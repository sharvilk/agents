"""Tests for list-old-lists.py. Each test builds its folders in a temporary directory and runs the script
there, with HOME and CLAUDE_CONFIG_DIR pointed at it, so the real config folder is never read.
Run: python3 -I test_list_old_lists.py"""
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / 'list-old-lists.py'
A = '0b9e7c1a-2f3d-4e5f-8a9b-0c1d2e3f4a5b'
B = 'f1e2d3c4-b5a6-4978-8695-a4b3c2d1e0f9'
C = '11111111-2222-4333-8444-555555555555'
DAY = 86400


class ListOld(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.config = self.home / 'config'

    def run_script(self, *args, env_config=True, home=None):
        env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_CONFIG_DIR'}
        env['HOME'] = str(home or self.home)
        if env_config:
            env['CLAUDE_CONFIG_DIR'] = str(self.config)
        done = subprocess.run([sys.executable, '-I', str(SCRIPT), *args], capture_output=True, text=True,
                              env=env, timeout=30)
        return done.returncode, done.stdout, done.stderr

    def make(self, folder, initiative, name, age_days, text='- [ ] item\n', config=None):
        path = (config or self.config) / folder / initiative / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        then = time.time() - age_days * DAY
        os.utime(path, (then, then))
        return path

    def lines(self, out):
        return out.splitlines()

    def test_nothing_old(self):
        self.make('todo-sync', 'billing', f'{A}.md', 1)
        self.make('todos', 'billing', f'{B}.md', 13)
        code, out, _ = self.run_script()
        self.assertEqual(code, 0)
        self.assertEqual(len(self.lines(out)), 1)
        self.assertIn('0 lists untouched for more than 14 days', out)

    def test_no_folders_at_all(self):
        code, out, _ = self.run_script()
        self.assertEqual(code, 0)
        self.assertIn('0 lists untouched', out)

    def test_an_old_list_in_each_folder(self):
        self.make('todo-sync', 'billing', f'{A}.md', 20)
        self.make('todos', 'search', f'{B}.md', 30)
        code, out, _ = self.run_script()
        self.assertEqual(code, 0)
        rows = self.lines(out)
        self.assertEqual(len(rows), 3)
        self.assertIn('todos (old folder)  search  ' + B, rows[0])
        self.assertIn('todo-sync  billing  ' + A, rows[1])
        self.assertNotIn('todos (old folder)', rows[1])
        self.assertIn('2 lists untouched for more than 14 days', rows[2])

    def test_row_has_date_folder_initiative_id_and_count(self):
        path = self.make('todo-sync', 'billing', f'{A}.md', 20)
        date = time.strftime('%Y-%m-%d', time.localtime(path.stat().st_mtime))
        code, out, _ = self.run_script()
        self.assertEqual(self.lines(out)[0], f'{date}  todo-sync  billing  {A}  open: about 1')

    def test_days_option(self):
        self.make('todo-sync', 'billing', f'{A}.md', 5)
        self.assertNotIn(A, self.run_script()[1])
        code, out, _ = self.run_script('--days', '3')
        self.assertEqual(code, 0)
        self.assertIn(A, out)
        self.assertIn('for more than 3 days', out)
        self.assertIn(A, self.run_script('--days=3')[1])
        self.assertIn(A, self.run_script('--days', '0')[1])
        self.assertNotIn(A, self.run_script('--days', '6')[1])

    def test_one_list_is_singular(self):
        self.make('todo-sync', 'billing', f'{A}.md', 20)
        self.assertIn('1 list untouched', self.run_script()[1])

    def test_a_non_uuid_md_is_ignored(self):
        self.make('todo-sync', 'billing', 'notes.md', 40)
        self.make('todo-sync', 'billing', f'{A}-notes.md', 40)
        self.make('todo-sync', 'billing', f'{A}.txt', 40)
        self.make('todo-sync', 'billing', f'x{A}.md', 40)
        code, out, _ = self.run_script()
        self.assertEqual(code, 0)
        self.assertEqual(len(self.lines(out)), 1)
        self.assertIn('0 lists', out)

    def test_a_subfolder_is_ignored(self):
        self.make('todo-sync', 'billing', f'{A}.md', 40)
        self.make('todo-sync', 'billing', f'{B}.md/inner.md', 40)
        old = time.time() - 40 * DAY
        os.utime(self.config / 'todo-sync' / 'billing' / f'{B}.md', (old, old))
        self.make('todo-sync', 'billing', f'sub/{C}.md', 40)
        code, out, _ = self.run_script()
        self.assertEqual(code, 0)
        self.assertIn('1 list untouched', out)
        self.assertNotIn(B, out)
        self.assertNotIn(C, out)

    def test_a_file_directly_in_a_list_folder_is_ignored(self):
        path = self.config / 'todo-sync' / f'{A}.md'
        path.parent.mkdir(parents=True)
        path.write_text('- [ ] x\n')
        old = time.time() - 40 * DAY
        os.utime(path, (old, old))
        self.assertIn('0 lists', self.run_script()[1])

    def test_a_symlinked_list_is_ignored(self):
        target = self.make('todo-sync', 'billing', f'{A}.md', 40)
        link = target.parent / f'{B}.md'
        link.symlink_to(target)
        out = self.run_script()[1]
        self.assertIn('1 list untouched', out)
        self.assertNotIn(B, out)

    def test_a_symlinked_initiative_folder_is_not_entered(self):
        real = self.make('todo-sync', 'billing', f'{A}.md', 40).parent
        (self.config / 'todo-sync' / 'linked').symlink_to(real)
        out = self.run_script()[1]
        self.assertIn('1 list untouched', out)
        self.assertNotIn('  linked  ', out)

    def test_checkbox_count(self):
        text = ('- [ ] one\n  - [ ] indented\n- [x] done\n- [X] done\n-[ ] no space\n* [ ] star\n'
                'text - [ ] mid-line\n- [  ] two spaces\n\t- [ ] tab\n    - [ ] four spaces\n')
        self.make('todo-sync', 'billing', f'{A}.md', 20, text)
        self.assertIn(f'{A}  open: about 3\n', self.run_script()[1])

    def test_a_list_without_checkboxes_counts_zero(self):
        self.make('todo-sync', 'billing', f'{A}.md', 20, '## Open\n- item\n')
        self.assertIn('open: about 0', self.run_script()[1])

    def test_a_list_that_is_not_utf8_still_counts(self):
        path = self.make('todo-sync', 'billing', f'{A}.md', 20)
        path.write_bytes(b'- [ ] caf\xe9\n- [ ] two\n')
        old = time.time() - 20 * DAY
        os.utime(path, (old, old))
        self.assertIn('open: about 2', self.run_script()[1])

    def test_oldest_first(self):
        self.make('todo-sync', 'zeta', f'{A}.md', 20)
        self.make('todos', 'alpha', f'{B}.md', 50)
        self.make('todo-sync', 'alpha', f'{C}.md', 35)
        rows = self.lines(self.run_script()[1])
        self.assertEqual([r.split('  ')[3] for r in rows[:3]], [B, C, A])

    def test_the_listing_changes_nothing(self):
        paths = [self.make('todo-sync', 'billing', f'{A}.md', 20), self.make('todos', 'x', f'{B}.md', 20)]
        before = [(p.read_text(), p.stat().st_mtime) for p in paths]
        tree = sorted(str(p) for p in self.config.rglob('*'))
        self.run_script()
        self.assertEqual([(p.read_text(), p.stat().st_mtime) for p in paths], before)
        self.assertEqual(sorted(str(p) for p in self.config.rglob('*')), tree)

    def test_a_bad_days_value_exits_1(self):
        for args in (['--days', 'x'], ['--days'], ['--days', '-1'], ['--days', '1.5'], ['--days='],
                     ['--days', '']):
            code, out, err = self.run_script(*args)
            self.assertEqual(code, 1, args)
            self.assertEqual(out, '', args)
            self.assertIn('--days needs a whole number', err)
            self.assertIn('usage: list-old-lists.py', err)

    def test_an_unknown_option_or_a_second_folder_exits_1(self):
        code, out, err = self.run_script('--bogus')
        self.assertEqual((code, out), (1, ''))
        self.assertIn('unknown option --bogus', err)
        code, out, err = self.run_script(str(self.config), str(self.config))
        self.assertEqual((code, out), (1, ''))
        self.assertIn('only one config folder', err)

    def test_an_unreadable_initiative_exits_2_and_prints_the_rest(self):
        if os.geteuid() == 0:
            self.skipTest('root can read anything')
        self.make('todo-sync', 'aaa', f'{A}.md', 20)
        locked = self.make('todo-sync', 'bbb', f'{B}.md', 20).parent
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o755)
        code, out, _ = self.run_script()
        self.assertEqual(code, 2)
        self.assertIn(A, out)
        self.assertNotIn(B, out)
        self.assertIn(f'{locked} -> unreadable', out)
        self.assertIn('1 folder or file could not be read; the list is incomplete', out)

    def test_an_unreadable_list_folder_exits_2(self):
        if os.geteuid() == 0:
            self.skipTest('root can read anything')
        self.make('todos', 'aaa', f'{A}.md', 20)
        root = self.config / 'todos'
        root.chmod(0)
        self.addCleanup(root.chmod, 0o755)
        code, out, _ = self.run_script()
        self.assertEqual(code, 2)
        self.assertIn(f'{root} -> unreadable', out)
        self.assertIn('0 lists untouched', out)

    def test_two_unreadable_folders_are_plural(self):
        if os.geteuid() == 0:
            self.skipTest('root can read anything')
        locked = [self.make('todo-sync', n, f'{A}.md', 20).parent for n in ('aaa', 'bbb')]
        for p in locked:
            p.chmod(0)
            self.addCleanup(p.chmod, 0o755)
        code, out, _ = self.run_script()
        self.assertEqual(code, 2)
        self.assertIn('2 folders or files could not be read', out)

    def test_a_folder_argument_is_used(self):
        other = self.home / 'other'
        self.make('todo-sync', 'billing', f'{A}.md', 20, config=other)
        self.make('todo-sync', 'search', f'{B}.md', 20)
        out = self.run_script(str(other))[1]
        self.assertIn(A, out)
        self.assertNotIn(B, out)
        out = self.run_script('--days', '3', str(other))[1]
        self.assertIn(A, out)
        out = self.run_script(str(other), '--days', '3')[1]
        self.assertIn(A, out)

    def test_the_default_folder_comes_from_claude_config_dir(self):
        self.make('todo-sync', 'billing', f'{A}.md', 20)
        self.make('todo-sync', 'search', f'{B}.md', 20, config=self.home / '.claude')
        out = self.run_script()[1]
        self.assertIn(A, out)
        self.assertNotIn(B, out)

    def test_the_default_folder_without_it_is_home_dot_claude(self):
        self.make('todo-sync', 'billing', f'{A}.md', 20)
        self.make('todo-sync', 'search', f'{B}.md', 20, config=self.home / '.claude')
        out = self.run_script(env_config=False)[1]
        self.assertIn(B, out)
        self.assertNotIn(A, out)

    def test_an_empty_claude_config_dir_falls_back_to_home(self):
        self.make('todo-sync', 'search', f'{B}.md', 20, config=self.home / '.claude')
        env = {k: v for k, v in os.environ.items()}
        env.update(HOME=str(self.home), CLAUDE_CONFIG_DIR='')
        done = subprocess.run([sys.executable, '-I', str(SCRIPT)], capture_output=True, text=True, env=env,
                              timeout=30)
        self.assertIn(B, done.stdout)


if __name__ == '__main__':
    unittest.main()
