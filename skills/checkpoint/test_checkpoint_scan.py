"""Tests for checkpoint-scan.py. Every repo is built in a temporary directory, with HOME pointed at it, an empty
global git config and no system git config, so your own git settings and hooks never apply. The remote is a local
bare repository; nothing touches the network.
Run: python3 -I test_checkpoint_scan.py"""
import contextlib
import importlib.util
import io
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent / 'checkpoint-scan.py'
SLEEPER_ARG = 'DISTINCTIVE-ARG-7781'
GIB = 2**30


def load_module():
    spec = importlib.util.spec_from_file_location('checkpoint_scan', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(os.path.realpath(tmp.name))
        (self.tmp / 'gitconfig').write_text('')
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith('GIT_') and k != 'CLAUDE_CONFIG_DIR'}
        self.env.update(HOME=str(self.tmp), GIT_CONFIG_GLOBAL=str(self.tmp / 'gitconfig'), GIT_CONFIG_NOSYSTEM='1')
        self.outside = self.tmp / 'outside'
        self.outside.mkdir()

    def git(self, repo, *args):
        done = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, env=self.env,
                              timeout=30)
        return done

    def git_ok(self, repo, *args):
        done = self.git(repo, *args)
        self.assertEqual(done.returncode, 0, f'git {args} failed: {done.stderr}')
        return done.stdout

    def commit(self, repo, name='file.txt', text=None, message='change'):
        path = Path(repo) / name
        path.write_text(text if text is not None else f'{message}\n')
        self.git_ok(repo, 'add', name)
        self.git_ok(repo, 'commit', '-q', '-m', message)

    def make_repo(self, name='project'):
        """A repo on branch main with one commit, pushed to a local bare origin."""
        origin = self.tmp / f'{name}-origin.git'
        subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(origin)], check=True, env=self.env)
        repo = self.tmp / 'work' / name
        repo.mkdir(parents=True)
        self.git_ok(repo, 'init', '-q', '-b', 'main')
        self.git_ok(repo, 'config', 'user.name', 'Test')
        self.git_ok(repo, 'config', 'user.email', 'test@example.invalid')
        self.git_ok(repo, 'config', 'commit.gpgsign', 'false')
        self.git_ok(repo, 'remote', 'add', 'origin', str(origin))
        (repo / '.git' / 'info' / 'exclude').write_text('.worktrees/\n')
        self.commit(repo, message='first')
        self.git_ok(repo, 'push', '-q', '-u', 'origin', 'main')
        return repo

    def scan(self, *roots, cwd=None, wrap=True):
        """Run the scan. It is run under a shell of its own, so that processes this test starts are not that shell's
        children, which the scan treats as part of the caller's pipeline."""
        args = [sys.executable, '-I', str(SCRIPT), *map(str, roots)]
        if wrap:
            args = ['sh', '-c', '"$@"; exit $?', 'sh', *args]
        done = subprocess.run(args, capture_output=True, text=True, env=self.env, cwd=str(cwd or self.outside),
                              timeout=60)
        return done.returncode, done.stdout, done.stderr

    def row(self, out, label):
        rows = [line for line in out.splitlines() if line.lstrip().startswith(label + ' ')]
        self.assertEqual(len(rows), 1, f'{label!r} not listed exactly once in:\n{out}')
        return rows[0]

    def spawn_sleeper(self, cwd):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)', SLEEPER_ARG],
                                 cwd=str(cwd), env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        def stop():
            if child.poll() is None:
                os.kill(child.pid, signal.SIGKILL)
            child.wait()
        self.addCleanup(stop)
        self.wait_for_cwd(child.pid, cwd)
        return child

    def wait_for_cwd(self, pid, cwd):
        """Wait until the process reports its new working directory (a fork can still show the parent's)."""
        module = load_module()
        for _ in range(100):
            if module.process_cwds().get(pid) == str(cwd):
                return
            time.sleep(0.05)
        self.fail('the child never showed its working directory')


@unittest.skipIf(shutil.disk_usage('/').free < 5 * GIB, 'the machine itself has under 5 GiB free')
class WorktreeState(Base):
    def test_a_clean_pushed_repo_exits_0(self):
        repo = self.make_repo()
        code, out, err = self.scan(repo)
        self.assertEqual((code, err), (0, ''), out)
        self.assertIn('clean, pushed', self.row(out, '.'))
        self.assertIn('main', self.row(out, '.'))
        self.assertTrue(out.rstrip().endswith('none'))

    def test_the_machine_section_is_present(self):
        repo = self.make_repo()
        _, out, _ = self.scan(repo)
        head, _, _ = out.partition('## Worktrees')
        self.assertTrue(head.startswith('## Machine\n'))
        self.assertRegex(head, r'(?m)^disk free   \d+\.\d GiB$')
        self.assertRegex(head, r'(?m)^load        \d+\.\d \d+\.\d \d+\.\d  \(\d+ cores\)$')
        if platform.system() == 'Darwin':
            self.assertRegex(head, r'(?m)^swap        ')
        self.assertIn('## Processes in these repos', out)

    def test_uncommitted_files_exit_1_and_are_counted(self):
        repo = self.make_repo()
        (repo / 'a.txt').write_text('a')
        (repo / 'b.txt').write_text('b')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        self.assertIn('2 uncommitted', self.row(out, '.'))
        self.assertNotIn('clean, pushed', out)

    def test_a_modified_tracked_file_counts(self):
        repo = self.make_repo()
        (repo / 'file.txt').write_text('edited\n')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        self.assertIn('1 uncommitted', self.row(out, '.'))

    def test_an_unpushed_commit_exits_1(self):
        repo = self.make_repo()
        self.commit(repo, 'two.txt', message='second')
        self.commit(repo, 'three.txt', message='third')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        self.assertIn('2 unpushed', self.row(out, '.'))
        self.assertNotIn('uncommitted', out)

    def test_a_branch_behind_its_remote_exits_1(self):
        repo = self.make_repo()
        other = self.tmp / 'other-clone'
        self.git_ok(self.tmp, 'clone', '-q', str(self.tmp / 'project-origin.git'), str(other))
        self.git_ok(other, 'config', 'user.name', 'Test')
        self.git_ok(other, 'config', 'user.email', 'test@example.invalid')
        self.commit(other, 'remote.txt', message='remote')
        self.git_ok(other, 'push', '-q', 'origin', 'main')
        self.git_ok(repo, 'fetch', '-q')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        self.assertIn('1 behind its remote', self.row(out, '.'))
        self.assertNotIn('unpushed', out)

    def test_a_branch_with_no_remote_branch_is_noted_and_alone_exits_0(self):
        repo = self.make_repo()
        self.git_ok(repo, 'checkout', '-q', '-b', 'local-only')
        code, out, _ = self.scan(repo)
        self.assertIn('no remote branch', self.row(out, '.'))
        self.assertEqual(code, 0, out)

    def test_a_branch_with_commits_on_no_remote_exits_1(self):
        repo = self.make_repo()
        self.git_ok(repo, 'checkout', '-q', '-b', 'local-only')
        self.commit(repo, 'own.txt', message='own')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1, out)
        self.assertIn('1 commit on no remote', self.row(out, '.'))
        self.commit(repo, 'own2.txt', message='own2')
        _, out, _ = self.scan(repo)
        self.assertIn('2 commits on no remote', self.row(out, '.'))

    def test_a_repo_with_no_remote_at_all_is_noted_and_exits_0(self):
        repo = self.make_repo()
        self.git_ok(repo, 'remote', 'remove', 'origin')
        code, out, _ = self.scan(repo)
        row = self.row(out, '.')
        self.assertIn('no remote', row)
        self.assertNotIn('no remote branch', row)
        self.assertNotIn('on no remote', row)
        self.assertEqual(code, 0, out)

    def test_a_root_given_through_a_symlink_lists_the_real_repo_processes(self):
        repo = self.make_repo()
        link = self.tmp / 'link-to-repo'
        link.symlink_to(repo)
        child = self.spawn_sleeper(repo)
        code, out, _ = self.scan(link)
        self.assertEqual(code, 1, out)
        self.assertIn(f'pid {child.pid} ', out)

    def test_a_root_that_is_a_symlink_to_a_plain_folder_still_matches_processes_in_it(self):
        plain = self.tmp / 'plain'
        plain.mkdir()
        link = self.tmp / 'link-to-plain'
        link.symlink_to(plain)
        child = self.spawn_sleeper(plain)
        code, out, _ = self.scan(link)
        self.assertEqual(code, 2, out)
        self.assertIn(f'{plain}: not a git repo', out)
        self.assertIn(f'pid {child.pid} ', out)

    def test_no_remote_branch_does_not_hide_other_problems(self):
        repo = self.make_repo()
        self.git_ok(repo, 'checkout', '-q', '-b', 'local-only')
        (repo / 'a.txt').write_text('a')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        row = self.row(out, '.')
        self.assertIn('1 uncommitted', row)
        self.assertIn('no remote branch', row)

    def test_a_branch_pushed_without_upstream_is_compared_with_origin(self):
        repo = self.make_repo()
        self.git_ok(repo, 'checkout', '-q', '-b', 'topic')
        self.commit(repo, 'topic.txt', message='topic')
        self.git_ok(repo, 'push', '-q', 'origin', 'topic')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 0, out)
        self.assertIn('clean, pushed', self.row(out, '.'))
        self.commit(repo, 'more.txt', message='more')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        self.assertIn('1 unpushed', self.row(out, '.'))

    def test_a_merge_left_half_done_by_a_conflict(self):
        repo = self.make_repo()
        self.git_ok(repo, 'checkout', '-q', '-b', 'side')
        self.commit(repo, 'file.txt', 'side\n', 'side')
        self.git_ok(repo, 'checkout', '-q', 'main')
        self.commit(repo, 'file.txt', 'main\n', 'main')
        self.git_ok(repo, 'push', '-q', 'origin', 'main')
        self.assertNotEqual(self.git(repo, 'merge', 'side').returncode, 0)
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        row = self.row(out, '.')
        self.assertIn('merge in progress', row)
        self.assertIn('1 uncommitted', row)

    def test_a_rebase_cherry_pick_and_revert_left_half_done(self):
        for op in ('rebase', 'cherry-pick', 'revert'):
            with self.subTest(op=op):
                repo = self.make_repo(f'repo-{op}')
                self.git_ok(repo, 'checkout', '-q', '-b', 'side')
                self.commit(repo, 'file.txt', 'side\n', 'side')
                self.git_ok(repo, 'checkout', '-q', 'main')
                self.commit(repo, 'file.txt', 'main\n', 'main')
                self.git_ok(repo, 'push', '-q', 'origin', 'main')
                if op == 'rebase':
                    self.git_ok(repo, 'checkout', '-q', 'side')
                    failed = self.git(repo, 'rebase', 'main')
                elif op == 'cherry-pick':
                    failed = self.git(repo, 'cherry-pick', 'side')
                else:
                    self.commit(repo, 'file.txt', 'later\n', 'later')
                    self.git_ok(repo, 'push', '-q', 'origin', 'main')
                    failed = self.git(repo, 'revert', 'HEAD~1', '--no-edit')
                self.assertNotEqual(failed.returncode, 0, failed.stdout)
                code, out, _ = self.scan(repo)
                self.assertEqual(code, 1)
                self.assertIn(f'{op.split("-")[0]} in progress', self.row(out, '.'))

    def test_a_merge_left_half_done_in_a_linked_worktree(self):
        repo = self.make_repo()
        self.git_ok(repo, 'branch', 'side')
        self.git_ok(repo, 'branch', 'work')
        linked = repo / '.worktrees' / 'work'
        self.git_ok(repo, 'worktree', 'add', '-q', str(linked), 'work')
        self.commit(linked, 'file.txt', 'work\n', 'work')
        self.git_ok(repo, 'checkout', '-q', 'side')
        self.commit(repo, 'file.txt', 'side\n', 'side')
        self.assertNotEqual(self.git(linked, 'merge', 'side').returncode, 0)
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        self.assertIn('merge in progress', self.row(out, '.worktrees/work'))
        self.assertNotIn('merge in progress', self.row(out, '.'))

    def test_the_stash_count_is_shown_once_per_repo(self):
        repo = self.make_repo()
        for n in (1, 2):
            (repo / 'file.txt').write_text(f'edit {n}\n')
            self.git_ok(repo, 'stash', 'push', '-q', '-m', f'stash {n}')
        self.git_ok(repo, 'worktree', 'add', '-q', '-b', 'other', str(repo / '.worktrees' / 'other'))
        _, out, _ = self.scan(repo)
        self.assertEqual(out.count('stash entr'), 1)
        self.assertIn(f'{repo}  (2 stash entries; the stash is shared by every worktree)', out)

    def test_a_single_stash_entry_reads_in_the_singular(self):
        repo = self.make_repo()
        (repo / 'file.txt').write_text('edit\n')
        self.git_ok(repo, 'stash', 'push', '-q')
        _, out, _ = self.scan(repo)
        self.assertIn('(1 stash entry;', out)

    def test_no_stash_prints_no_stash_note(self):
        repo = self.make_repo()
        _, out, _ = self.scan(repo)
        self.assertNotIn('stash', out)

    def test_a_linked_worktree_is_listed_with_its_own_state(self):
        repo = self.make_repo()
        linked = repo / '.worktrees' / 'feature'
        self.git_ok(repo, 'worktree', 'add', '-q', '-b', 'feature/x', str(linked))
        self.git_ok(linked, 'push', '-q', '-u', 'origin', 'feature/x')
        (linked / 'wip.txt').write_text('wip')
        self.commit(linked, 'done.txt', message='done')
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        row = self.row(out, '.worktrees/feature')
        self.assertIn('feature/x', row)
        self.assertIn('1 uncommitted', row)
        self.assertIn('1 unpushed', row)
        self.assertIn('clean, pushed', self.row(out, '.'))

    def test_a_detached_worktree_has_no_remote_notes(self):
        repo = self.make_repo()
        linked = repo / '.worktrees' / 'frozen'
        self.git_ok(repo, 'worktree', 'add', '-q', '--detach', str(linked))
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 0, out)
        row = self.row(out, '.worktrees/frozen')
        self.assertIn('(detached)', row)
        self.assertIn('clean, pushed', row)

    def test_naming_a_repo_and_its_worktree_lists_the_repo_once(self):
        repo = self.make_repo()
        linked = repo / '.worktrees' / 'feature'
        self.git_ok(repo, 'worktree', 'add', '-q', '-b', 'feature/y', str(linked))
        _, out, _ = self.scan(repo, linked, repo)
        self.assertEqual(out.count(str(repo) + '\n'), 1)
        self.assertEqual(out.count('.worktrees/feature'), 1)

    def test_two_repos_are_both_listed(self):
        a, b = self.make_repo('alpha'), self.make_repo('beta')
        (b / 'x.txt').write_text('x')
        code, out, _ = self.scan(a, b)
        self.assertEqual(code, 1)
        self.assertIn(str(a), out)
        self.assertIn(str(b), out)

    def test_a_worktree_whose_folder_is_gone_reports_a_failed_status(self):
        repo = self.make_repo()
        linked = repo / '.worktrees' / 'gone'
        self.git_ok(repo, 'worktree', 'add', '-q', '-b', 'gone', str(linked))
        shutil.rmtree(linked)
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 1)
        self.assertIn('git status failed', self.row(out, '.worktrees/gone'))

    def test_a_path_that_is_not_a_repo_exits_2(self):
        code, out, _ = self.scan(self.outside)
        self.assertEqual(code, 2)
        self.assertIn(f'{self.outside}: not a git repo', out)

    def test_a_bad_path_exits_2_even_when_another_repo_is_dirty(self):
        repo = self.make_repo()
        (repo / 'a.txt').write_text('a')
        code, out, _ = self.scan(repo, self.outside)
        self.assertEqual(code, 2)
        self.assertIn('1 uncommitted', out)
        self.assertIn('not a git repo', out)

    def test_a_missing_path_exits_2(self):
        code, out, _ = self.scan(self.tmp / 'does-not-exist')
        self.assertEqual(code, 2)
        self.assertIn('not a git repo', out)

    def test_no_argument_scans_the_repo_the_current_directory_is_in(self):
        repo = self.make_repo()
        sub = repo / 'sub'
        sub.mkdir()
        code, out, err = self.scan(cwd=sub)
        self.assertEqual((code, err), (0, ''), out)
        self.assertIn(str(repo), out)

    def test_no_argument_outside_a_repo_exits_2_on_stderr(self):
        code, out, err = self.scan(cwd=self.outside)
        self.assertEqual(code, 2)
        self.assertEqual(out, '')
        self.assertIn('not inside a git repo: name the repo roots to scan', err)


@unittest.skipIf(shutil.disk_usage('/').free < 5 * GIB, 'the machine itself has under 5 GiB free')
class Processes(Base):
    def test_a_child_with_its_cwd_in_the_repo_is_listed_without_its_command_line(self):
        repo = self.make_repo()
        child = self.spawn_sleeper(repo)
        code, out, err = self.scan(repo)
        self.assertEqual(code, 1)
        line = next((l for l in out.splitlines() if l.lstrip().startswith(f'pid {child.pid} ')), None)
        self.assertIsNotNone(line, out)
        self.assertIn(str(repo), line)
        self.assertIn(f'ppid {os.getpid()}', line)
        self.assertRegex(line, r'(?i)age \S+\s+cpu\s+[\d.]+%\s+\d+ MB\s+python')
        self.assertNotIn(SLEEPER_ARG, out + err)
        self.assertNotIn('time.sleep', out + err)

    def test_a_process_in_a_subfolder_or_a_linked_worktree_is_listed(self):
        repo = self.make_repo()
        (repo / 'deep' / 'er').mkdir(parents=True)
        linked = repo / '.worktrees' / 'feature'
        self.git_ok(repo, 'worktree', 'add', '-q', '-b', 'feature/z', str(linked))
        self.git_ok(linked, 'push', '-q', '-u', 'origin', 'feature/z')
        deep = self.spawn_sleeper(repo / 'deep' / 'er')
        in_tree = self.spawn_sleeper(linked)
        _, out, _ = self.scan(repo)
        self.assertIn(f'pid {deep.pid} ', out)
        self.assertIn(f'pid {in_tree.pid} ', out)

    def test_a_process_outside_the_repos_is_not_listed(self):
        repo = self.make_repo()
        elsewhere = self.spawn_sleeper(self.outside)
        lookalike = self.tmp / 'work' / 'project-other'
        lookalike.mkdir()
        beside = self.spawn_sleeper(lookalike)
        code, out, _ = self.scan(repo)
        self.assertEqual(code, 0, out)
        self.assertNotIn(f'pid {elsewhere.pid} ', out)
        self.assertNotIn(f'pid {beside.pid} ', out)

    def test_a_process_in_a_repo_given_by_a_linked_worktree_path_is_listed(self):
        repo = self.make_repo()
        linked = repo / '.worktrees' / 'feature'
        self.git_ok(repo, 'worktree', 'add', '-q', '-b', 'feature/w', str(linked))
        child = self.spawn_sleeper(repo)
        _, out, _ = self.scan(linked)
        self.assertIn(f'pid {child.pid} ', out)

    def test_the_scan_and_the_shells_above_it_are_not_listed(self):
        repo = self.make_repo()
        # The scan, its shell and this test process all have their working directory in the repo.
        previous = os.getcwd()
        os.chdir(repo)
        self.addCleanup(os.chdir, previous)
        code, out, _ = self.scan(repo, cwd=repo)
        self.assertEqual(code, 0, out)
        self.assertNotIn('pid ', out)

    def test_the_callers_own_pipeline_is_not_listed(self):
        repo = self.make_repo()
        marker = self.tmp / 'pid.txt'

        def stop_sibling():
            if marker.exists() and marker.read_text().strip().isdigit() and _alive(int(marker.read_text())):
                os.kill(int(marker.read_text()), signal.SIGKILL)
        self.addCleanup(stop_sibling)
        script = ('(cd "$1" && exec "$4" -c "import time; time.sleep(60)") >/dev/null 2>&1 & echo $! > "$2"; cd "$3"; '
                  '"$4" -I "$5" "$1"; echo "exit $?" > "$3/status.txt"')
        subprocess.run(['sh', '-c', script, 'sh', str(repo), str(marker), str(self.outside), sys.executable,
                        str(SCRIPT)], env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual((self.outside / 'status.txt').read_text().strip(), 'exit 0')

    def _scan_with_describe(self, repo, pid, behavior):
        """Run main() with only the describe call (the one asking for ppid and etime) replaced."""
        module = load_module()
        real = subprocess.run

        def fake(args, *a, **kw):
            if args and args[0] == 'ps' and any('etime' in str(x) for x in args):
                if isinstance(behavior, Exception):
                    raise behavior
                return subprocess.CompletedProcess(args, 1, stdout=behavior, stderr='')
            return real(args, *a, **kw)
        out = io.StringIO()
        with mock.patch.object(module, 'process_cwds', return_value={pid: str(repo)}), \
                mock.patch.object(module.subprocess, 'run', side_effect=fake), \
                mock.patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(out):
            code = module.main([str(repo)])
        return code, out.getvalue()

    def test_a_failed_describe_call_still_reports_a_live_process_and_exits_2(self):
        repo = self.make_repo()
        child = self.spawn_sleeper(repo)
        code, out = self._scan_with_describe(repo, child.pid, OSError('no ps'))
        self.assertEqual(code, 2, out)
        self.assertIn(f'ps failed: OSError; could not describe pid(s) {child.pid} (still running)', out)
        self.assertNotIn('had already ended', out)

    def test_a_timed_out_describe_call_exits_2(self):
        repo = self.make_repo()
        child = self.spawn_sleeper(repo)
        code, out = self._scan_with_describe(repo, child.pid, subprocess.TimeoutExpired('ps', 30))
        self.assertEqual(code, 2, out)
        self.assertIn('ps failed: TimeoutExpired', out)

    def test_an_empty_describe_result_for_a_live_process_still_reports_it_and_exits_1(self):
        repo = self.make_repo()
        child = self.spawn_sleeper(repo)
        code, out = self._scan_with_describe(repo, child.pid, '')
        self.assertEqual(code, 1, out)
        self.assertIn(f'could not describe pid(s) {child.pid} (still running)', out)
        self.assertNotIn('ps failed', out)
        self.assertNotIn('had already ended', out)

    def test_a_dead_process_is_still_reported_as_ended_with_exit_0(self):
        repo = self.make_repo()
        gone = subprocess.Popen([sys.executable, '-c', 'pass'])
        gone.wait()
        code, out = self._scan_with_describe(repo, gone.pid, '')
        self.assertEqual(code, 0, out)
        self.assertIn('none (the ones found had already ended)', out)
        self.assertNotIn('could not describe', out)

    def test_a_process_that_ended_before_it_could_be_described(self):
        module = load_module()
        repo = self.make_repo()
        gone = subprocess.Popen([sys.executable, '-c', 'pass'])
        gone.wait()
        out = io.StringIO()
        with mock.patch.object(module, 'process_cwds', return_value={gone.pid: str(repo)}), \
                mock.patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(out):
            code = module.main([str(repo)])
        self.assertEqual(code, 0)
        self.assertIn('none (the ones found had already ended)', out.getvalue())


def _alive(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class Crash(Base):
    def test_an_unexpected_python_error_exits_2_with_a_one_line_message(self):
        broken = self.tmp / 'broken-scan.py'
        broken.write_text(SCRIPT.read_text().replace('def main(argv):\n', 'def main(argv):\n    raise ValueError("boom")\n', 1))
        done = subprocess.run([sys.executable, '-I', str(broken)], capture_output=True, text=True, env=self.env,
                              cwd=str(self.outside), timeout=60)
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stderr.strip(), 'checkpoint-scan: unexpected error: ValueError: boom')
        self.assertNotIn('Traceback', done.stderr)


class Units(Base):
    """The parts of the script that cannot be driven from outside on this machine, with the machine mocked."""

    def setUp(self):
        super().setUp()
        self.module = load_module()

    def test_disk_under_5_gib_is_a_warning(self):
        usage = shutil.disk_usage('/')
        with mock.patch.object(shutil, 'disk_usage', return_value=usage._replace(free=GIB)):
            lines, worry = self.module.machine()
        self.assertTrue(worry)
        self.assertEqual(lines[0], 'disk free   1.0 GiB  (under 5 GiB)')

    def test_disk_of_exactly_5_gib_is_not(self):
        usage = shutil.disk_usage('/')
        with mock.patch.object(shutil, 'disk_usage', return_value=usage._replace(free=5 * GIB)):
            lines, worry = self.module.machine()
        self.assertFalse(worry)
        self.assertEqual(lines[0], 'disk free   5.0 GiB')

    def test_low_disk_alone_makes_a_clean_scan_exit_1(self):
        repo = self.make_repo()
        usage = shutil.disk_usage('/')
        for free, expected in ((GIB, 1), (50 * GIB, 0)):
            out = io.StringIO()
            with mock.patch.object(shutil, 'disk_usage', return_value=usage._replace(free=free)), \
                    mock.patch.object(self.module, 'process_cwds', return_value={}), \
                    mock.patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(out):
                code = self.module.main([str(repo)])
            self.assertEqual(code, expected, out.getvalue())

    def test_the_swap_line_is_read_on_macos_only(self):
        usage = shutil.disk_usage('/')
        fake = mock.Mock(side_effect=lambda args, cwd=None: 'total = 1.00M  used = 0.50M\n')
        with mock.patch.object(shutil, 'disk_usage', return_value=usage), \
                mock.patch.object(self.module, 'run', fake):
            with mock.patch.object(platform, 'system', return_value='Darwin'):
                darwin, _ = self.module.machine()
            with mock.patch.object(platform, 'system', return_value='Linux'):
                linux, _ = self.module.machine()
        self.assertEqual(darwin[-1], 'swap        total = 1.00M  used = 0.50M')
        self.assertFalse(any(l.startswith('swap') for l in linux))

    def test_cwds_are_read_from_lsof_output(self):
        listing = 'p12\nn/a/b\np13\nn/c d\n'
        with mock.patch.object(self.module, 'run', return_value=listing):
            self.assertEqual(self.module.process_cwds(), {12: '/a/b', 13: '/c d'})

    def test_cwds_fall_back_to_proc_without_lsof(self):
        links = {'/proc/21/cwd': '/x/y', '/proc/22/cwd': '/z'}

        def readlink(path):
            if path in links:
                return links[path]
            raise OSError('gone')
        with mock.patch.object(self.module, 'run', return_value=None), \
                mock.patch.object(os.path, 'isdir', return_value=True), \
                mock.patch.object(os, 'listdir', return_value=['21', 'self', '22', '23']), \
                mock.patch.object(os, 'readlink', side_effect=readlink):
            self.assertEqual(self.module.process_cwds(), {21: '/x/y', 22: '/z'})

    def test_no_cwds_without_lsof_or_proc(self):
        with mock.patch.object(self.module, 'run', return_value=None), \
                mock.patch.object(os.path, 'isdir', return_value=False):
            self.assertEqual(self.module.process_cwds(), {})

    def test_under_matches_whole_path_segments(self):
        under = self.module.under
        self.assertTrue(under('/r', ['/r']))
        self.assertTrue(under('/r/sub', ['/r']))
        self.assertTrue(under('/r/sub', ['/r/']))
        self.assertFalse(under('/r-other', ['/r']))
        self.assertFalse(under('/', ['/r']))

    def test_the_ancestor_walk_stops_at_init(self):
        answers = {str(os.getpid()): '500\n', '500': '1\n'}

        def fake(args, cwd=None):
            return answers.get(args[-1])
        with mock.patch.object(self.module, 'run', side_effect=fake):
            self.assertEqual(self.module.ancestors(), {os.getpid(), 500})

    def test_pid_exists_tells_ended_from_running_from_not_ours(self):
        for effect, expected in ((ProcessLookupError(), False), (PermissionError(), True), (None, True)):
            with mock.patch.object(os, 'kill', side_effect=effect):
                self.assertEqual(self.module.pid_exists(12345), expected, effect)

    def test_a_failed_command_gives_none(self):
        self.assertIsNone(self.module.run(['git', '-C', str(self.outside), 'status']))
        self.assertIsNone(self.module.run(['no-such-program-7781']))


if __name__ == '__main__':
    unittest.main()
