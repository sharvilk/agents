"""Tests for `file_chat.py --inbox`, driven end to end like test_file_chat.py: two local bare repos stand in for the
ChatGPT and Claude backup repos, a fake `gh` is first on PATH, HOME is a temporary folder and no credentials exist.
The inbox and the filed folder are always inside the temporary folder; no test passes or defaults to a real path.
Run from the chat-skills folder:  python3 -I tests/test_inbox.py"""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support as s  # noqa: E402
from test_file_chat import FAKE_GH as BASE_GH  # noqa: E402

# The fake gh answers with the repo it was asked about, so each platform's pull request names its own repo.
FAKE_GH = (BASE_GH.replace('"nameWithOwner":"example/backup"}\'', '"nameWithOwner":"\'"$3"\'"}\'')
           .replace("example/backup/pull/7", '$4/pull/7'))
assert FAKE_GH != BASE_GH and '"$3"' in FAKE_GH and "$4/pull/7" in FAKE_GH

URLS = {"chatgpt": "https://github.com/example/backup.git", "claude": "https://github.com/example/backup-claude.git"}


class Inbox(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        self.gh_log = self.tmp / "gh.log"
        self.env = s.clean_env(self.tmp / "home", {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
            "GH_LOG": str(self.gh_log),
        })
        self.remotes, self.clones = {}, {}
        config = ""
        for platform, url in URLS.items():
            remote = self.tmp / f"remote-{platform}.git"
            self.remotes[platform] = remote
            config += f'[url "file://{remote}"]\n\tinsteadOf = {url}\n'
        Path(self.env["GIT_CONFIG_GLOBAL"]).write_text(config)
        for platform, url in URLS.items():
            remote = self.remotes[platform]
            self.git("init", "--quiet", "--bare", "-b", "main", str(remote))
            self.git("-C", str(remote), "config", "uploadpack.allowFilter", "true")
            self.git("-C", str(remote), "config", "uploadpack.allowAnySHA1InWant", "true")
            seed = self.tmp / f"seed-{platform}"
            self.git("init", "--quiet", "-b", "main", str(seed))
            (seed / "README.md").write_text("# backup\n")
            self.git("-C", str(seed), "add", "README.md")
            self.git("-C", str(seed), "commit", "--quiet", "-m", "init")
            self.git("-C", str(seed), "push", "--quiet", f"file://{remote}", "main")
            self.clones[platform] = self.tmp / f"clone-{platform}"
            self.git("clone", "--quiet", url, str(self.clones[platform]))
        self.env["CHAT_SAVE_REPO_CHATGPT"] = str(self.clones["chatgpt"])
        self.env["CHAT_SAVE_REPO_CLAUDE"] = str(self.clones["claude"])
        self.base = self.tmp / "chat-backups"
        self.inbox = self.base / "inbox"
        self.filed = self.base / "filed"
        self.inbox.mkdir(parents=True)
        self.packs = 0

    def git(self, *args):
        return subprocess.run(["git", *args], capture_output=True, text=True, env=self.env, check=True,
                              timeout=60).stdout

    def branches(self, platform="chatgpt"):
        return self.git("-C", str(self.remotes[platform]), "branch", "--list", "chat-save/*").split()

    def tip(self, platform, ref):
        return self.git("-C", str(self.remotes[platform]), "rev-parse", ref).strip()

    def tree(self, platform, ref):
        out = self.git("-C", str(self.remotes[platform]), "ls-tree", "-r", "-z", "--name-only", ref)
        return [n for n in out.split("\0") if n]

    def manifest(self, platform, ref):
        path = [f for f in self.tree(platform, ref) if f.endswith("/manifest.json")][0]
        return json.loads(self.git("-C", str(self.remotes[platform]), "show", f"{ref}:{path}"))

    def build(self, platform="chatgpt", partial=False, title=None):
        """A ZIP for a fresh copy of the synthetic chat, saved under a platform; partial lists f000002 as missing."""
        work = self.tmp / f"work{self.packs}"
        shutil.copytree(s.FIXTURE, work)
        meta = json.loads((work / "meta.json").read_text())
        meta["platform"] = platform
        meta["title"] = title or meta["title"]
        (work / "meta.json").write_text(json.dumps(meta))
        if partial:
            files = json.loads((work / "files.json").read_text())
            files[1].update(status="missing", missing_reason="not exposed")
            files[1].pop("source")
            (work / "files.json").write_text(json.dumps(files))
        out = self.tmp / f"out{self.packs}"
        self.packs += 1
        done, zip_path = s.pack(work, out)
        self.assertEqual(done.returncode, 0, done.stdout)
        return zip_path

    def put(self, zip_path, where=None, name=None):
        folder = where or self.inbox
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / (name or zip_path.name)
        shutil.copy(zip_path, target)
        return target

    def png(self, folder, name="f000002.png"):
        path = folder / name
        path.write_bytes((s.FIXTURE / "uploads" / "fixture.png").read_bytes())
        return path

    def inbox_run(self, *args, inbox=None, env=None):
        return s.run_py(s.FILE_CHAT, "--inbox", inbox or self.inbox, *args, env=env or self.env)

    def snapshot(self, folder):
        """{relative path: sha256 or None for a folder} of everything under folder."""
        found = {}
        for path in sorted(Path(folder).rglob("*")):
            relative = path.relative_to(folder).as_posix()
            found[relative] = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        return found

    def pr_creates(self):
        """The repo slug of every `gh pr create` the fake gh saw."""
        return [line.split()[3] for line in self.gh_log.read_text().splitlines() if line.startswith("pr create ")]

    def names(self, folder):
        return sorted(p.name for p in folder.iterdir()) if folder.exists() else []

    # ── filing a batch ────────────────────────────────────────────────────────────────────────────────────────────

    def test_two_saves_from_two_platforms_file_into_their_own_repos_and_move_to_filed(self):
        gpt = self.put(self.build("chatgpt"))
        claude = self.put(self.build("claude"))
        heads = {p: self.tip(p, "main") for p in URLS}
        done = self.inbox_run()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(len(self.branches("chatgpt")), 1)
        self.assertEqual(len(self.branches("claude")), 1)
        for platform in URLS:
            self.assertEqual(self.tip(platform, "main"), heads[platform])
        self.assertEqual(self.names(self.inbox), [])
        self.assertEqual(self.names(self.filed), sorted([gpt.name, claude.name]))
        self.assertIn(f"filed   {gpt.name} → example/backup https://github.com/example/backup/pull/7  ", done.stdout)
        self.assertIn(f"filed   {claude.name} → example/backup", done.stdout)
        self.assertFalse((self.base / ".file-chat-inbox.lock").exists())

    def test_a_chat_folder_files_with_its_download_and_moves_whole(self):
        folder = self.inbox / "Logo ideas"
        self.put(self.build(partial=True), folder)
        self.png(folder, "f000002-sketch.png")
        (folder / ".DS_Store").write_bytes(b"finder")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        branch = self.branches()[0]
        manifest = self.manifest("chatgpt", branch)
        self.assertEqual(manifest["coverage"]["status"], "complete")
        self.assertEqual(manifest["files"][1]["bytes_from"], "user_download")
        self.assertEqual(self.names(self.inbox), [])
        self.assertEqual(self.names(self.filed), ["Logo ideas"])
        self.assertTrue((self.filed / "Logo ideas" / "f000002-sketch.png").is_file())
        self.assertIn("filed   Logo ideas → example/backup", done.stdout)

    def test_a_saved_web_page_in_a_chat_folder_is_filed_as_raw_material(self):
        folder = self.inbox / "Synthetic pilot"
        self.put(self.build(), folder)
        (folder / "Synthetic pilot.html").write_text("<html>page</html>")
        (folder / "Synthetic pilot_files").mkdir()
        (folder / "Synthetic pilot_files" / "a.png").write_bytes(b"\x89PNG a")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        files = self.tree("chatgpt", self.branches()[0])
        self.assertTrue(any(f.endswith("/raw/Synthetic pilot.html") for f in files))
        self.assertTrue(any(f.endswith("/raw/Synthetic pilot_files/a.png") for f in files))
        self.assertEqual(self.names(self.filed), ["Synthetic pilot"])

    def test_a_partial_top_level_zip_moves_into_its_own_folder_and_a_rerun_completes_it(self):
        zip_path = self.put(self.build(partial=True))
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        branch = self.branches()[0]
        first_tip = self.tip("chatgpt", branch)
        folder = self.inbox / zip_path.stem
        self.assertEqual(self.names(self.inbox), [zip_path.stem])
        self.assertEqual(self.names(folder), [zip_path.name])
        self.assertEqual(self.names(self.filed), [])
        self.assertIn(f"partial {zip_path.name} → https://github.com/example/backup/pull/7  missing f000002; "
                      f"drop it into inbox/{zip_path.stem}/ and re-run", done.stdout)
        self.png(folder)
        again = self.inbox_run("--no-remote-check")
        self.assertEqual(again.returncode, 0, again.stdout)
        self.assertEqual(self.branches(), [branch])
        self.assertEqual(self.git("-C", str(self.remotes["chatgpt"]), "rev-parse", f"{branch}~1").strip(), first_tip)
        self.assertEqual(self.manifest("chatgpt", branch)["coverage"]["status"], "complete")
        self.assertEqual(self.names(self.inbox), [])
        self.assertEqual(self.names(self.filed), [zip_path.stem])

    def test_a_partial_chat_folder_stays_where_it_is(self):
        folder = self.inbox / "chat"
        self.put(self.build(partial=True), folder)
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.names(self.inbox), ["chat"])
        self.assertIn("missing f000002; drop it into inbox/chat/ and re-run", done.stdout)
        self.assertEqual(self.names(self.filed), [])

    def test_the_same_save_again_is_already_filed_and_moves_with_a_suffix(self):
        original = self.build()
        first = self.put(original)
        self.assertEqual(self.inbox_run("--direct", "--no-remote-check").returncode, 0)
        self.put(original)
        head = self.tip("chatgpt", "main")
        done = self.inbox_run("--direct", "--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn(f"already filed {first.name}", done.stdout)
        self.assertEqual(self.tip("chatgpt", "main"), head)
        self.assertEqual(self.names(self.filed), sorted([first.name, f"{first.stem} (2).zip"]))

    # ── refusals, skips, left alone ───────────────────────────────────────────────────────────────────────────────

    def test_a_corrupt_zip_is_refused_and_stays_while_the_others_are_filed(self):
        (self.inbox / "a-corrupt.zip").write_bytes(b"this is not a zip")
        good = self.put(self.build())
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("refused a-corrupt.zip:", done.stdout)
        self.assertEqual(self.names(self.inbox), ["a-corrupt.zip"])
        self.assertEqual(self.names(self.filed), [good.name])
        self.assertEqual(len(self.branches()), 1)

    def test_a_stray_file_is_left_alone_and_never_touched(self):
        (self.inbox / "notes.txt").write_text("keep me")
        (self.inbox / ".hidden").write_text("x")
        (self.inbox / ".DS_Store").write_bytes(b"finder")
        good = self.put(self.build())
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("left alone notes.txt: not a save", done.stdout)
        self.assertIn("left alone .hidden: not a save", done.stdout)
        self.assertNotIn(".DS_Store", done.stdout)
        self.assertEqual((self.inbox / "notes.txt").read_text(), "keep me")
        self.assertEqual(self.names(self.filed), [good.name])

    def test_a_folder_with_two_zips_or_an_unrelated_file_is_refused_naming_it(self):
        two = self.inbox / "two"
        self.put(self.build(), two)
        self.put(self.build(title="Other chat"), two, name="zz-second.zip")
        odd = self.inbox / "odd"
        self.put(self.build(), odd)
        (odd / "holiday.jpg").write_bytes(b"x")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("refused two: zz-second.zip: a second ZIP", done.stdout)
        self.assertIn("refused odd: holiday.jpg: not part of a save", done.stdout)
        self.assertEqual(self.names(self.inbox), ["odd", "two"])
        self.assertEqual(self.branches(), [])

    def test_a_folder_without_a_zip_is_refused(self):
        (self.inbox / "empty").mkdir()
        done = self.inbox_run()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("refused empty: no ZIP in this folder", done.stdout)

    def test_a_download_in_progress_is_skipped_at_the_top_and_in_a_chat_folder(self):
        (self.inbox / "chat-save-x.zip.crdownload").write_bytes(b"half")
        folder = self.inbox / "chat"
        self.put(self.build(), folder)
        (folder / "f000002.png.part").write_bytes(b"half")
        done = self.inbox_run()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("skipped chat-save-x.zip.crdownload: download still in progress", done.stdout)
        self.assertIn("skipped chat: download still in progress", done.stdout)
        self.assertEqual(self.names(self.inbox), ["chat", "chat-save-x.zip.crdownload"])
        self.assertEqual(self.branches(), [])

    # ── options, usage, safety ────────────────────────────────────────────────────────────────────────────────────

    def test_dry_run_moves_nothing_and_pushes_nothing(self):
        gpt = self.put(self.build())
        folder = self.inbox / "chat"
        self.put(self.build("claude", title="Other chat"), folder)
        before = {p.name for p in self.inbox.iterdir()}
        done = self.inbox_run("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn(f"dry run {gpt.name} → example/backup: would be filed", done.stdout)
        self.assertEqual({p.name for p in self.inbox.iterdir()}, before)
        self.assertFalse(self.filed.exists())
        self.assertEqual(self.branches("chatgpt") + self.branches("claude"), [])
        self.assertFalse((self.base / ".file-chat-inbox.lock").exists())

    def test_the_inbox_cannot_be_combined_with_a_zip_downloads_raw_or_repo(self):
        zip_path = self.build()
        for extra in (["--repo", self.clones["chatgpt"]], [zip_path], ["--raw", self.tmp], [self.tmp / "f000002.png"]):
            done = s.run_py(s.FILE_CHAT, "--inbox", self.inbox, *extra, env=self.env)
            self.assertEqual(done.returncode, 2, (extra, done.stdout))
            self.assertIn("cannot be combined", done.stdout)
        self.assertEqual(self.branches(), [])

    def test_a_missing_inbox_is_refused_with_the_mkdir_command_and_not_created(self):
        missing = self.tmp / "no such" / "inbox"
        done = self.inbox_run(inbox=missing)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn(f"mkdir -p '{missing}'", done.stdout)
        self.assertFalse(missing.parent.exists())

    def test_an_empty_inbox_says_so(self):
        (self.inbox / ".DS_Store").write_bytes(b"finder")
        done = self.inbox_run()
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("is empty; nothing to file", done.stdout)

    def test_a_name_clash_in_filed_is_suffixed_and_nothing_is_overwritten(self):
        zip_path = self.put(self.build())
        self.filed.mkdir()
        (self.filed / zip_path.name).write_text("an older file")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual((self.filed / zip_path.name).read_text(), "an older file")
        self.assertTrue((self.filed / f"{zip_path.stem} (2).zip").is_file())
        self.assertEqual(self.names(self.inbox), [])

    def test_a_held_lock_refuses_the_run_and_is_left_in_place(self):
        zip_path = self.put(self.build())
        lock = self.base / ".file-chat-inbox.lock"
        lock.write_text(f"{os.getpid()}\n")
        done = self.inbox_run()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn(str(lock.resolve()), done.stdout)
        self.assertIn(f"PID {os.getpid()}", done.stdout)
        self.assertIn(f"rm {shlex.quote(str(lock.resolve()))}", done.stdout)
        self.assertTrue(lock.exists())
        self.assertEqual(self.names(self.inbox), [zip_path.name])
        self.assertEqual(self.branches(), [])

    def test_the_default_inbox_is_under_the_home_folder(self):
        home = Path(self.env["HOME"])
        inbox = home / "chat-backups" / "inbox"
        zip_path = self.put(self.build(), inbox)
        done = s.run_py(s.FILE_CHAT, "--inbox", "--no-remote-check", env=self.env)
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.names(home / "chat-backups" / "filed"), [zip_path.name])

    def test_a_folder_that_is_too_broad_to_be_an_inbox_is_refused(self):
        home = Path(self.env["HOME"])
        (home / "keep.zip").write_bytes(b"x")
        done = s.run_py(s.FILE_CHAT, "--inbox", home, env=self.env)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("too broad to be an inbox", done.stdout)
        self.assertTrue((home / "keep.zip").is_file())


    # ── dry run, failures, robustness ─────────────────────────────────────────────────────────────────────────────

    def test_a_dry_run_changes_nothing_in_the_inbox_its_parent_or_the_lock(self):
        complete = self.build(title="Complete chat")
        self.put(complete)
        partial_folder = self.inbox / "partial chat"
        self.put(self.build(partial=True, title="Partial chat"), partial_folder)
        self.assertEqual(self.inbox_run("--direct", "--no-remote-check").returncode, 0)
        self.put(complete)
        self.put(self.build(partial=True, title="Fresh partial"))
        before = self.snapshot(self.base)
        done = self.inbox_run("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.snapshot(self.base), before)
        self.assertFalse((self.base / ".file-chat-inbox.lock").exists())
        self.assertIn(f"dry run {complete.name}: already filed; would move to filed/", done.stdout)
        self.assertIn("dry run partial chat: already filed; missing f000002; would stay in the inbox", done.stdout)
        self.assertRegex(done.stdout, r"dry run chat-save-[^\n]*\.zip → example/backup: would be filed")

    def test_a_dry_run_on_an_inbox_without_filed_creates_no_folder(self):
        zip_path = self.put(self.build(partial=True))
        before = self.snapshot(self.base)
        done = self.inbox_run("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.snapshot(self.base), before)
        self.assertFalse(self.filed.exists())
        self.assertFalse((self.inbox / zip_path.stem).exists())

    def test_a_move_that_fails_after_filing_is_reported_and_the_batch_goes_on(self):
        self.filed.write_text("not a folder")
        gpt = self.put(self.build("chatgpt"))
        claude = self.put(self.build("claude"))
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn(f"failed  {gpt.name}: filed, but it could not be moved", done.stdout)
        self.assertIn(f"failed  {claude.name}: filed, but it could not be moved", done.stdout)
        self.assertEqual(len(self.branches("chatgpt")) + len(self.branches("claude")), 2)
        self.assertEqual(self.names(self.inbox), sorted([gpt.name, claude.name]))
        self.assertEqual(self.filed.read_text(), "not a folder")
        self.assertIn("inbox summary", done.stdout)

    def test_an_unexpected_error_in_one_item_is_reported_and_the_next_is_filed(self):
        spec = importlib.util.spec_from_file_location("file_chat_under_test", s.FILE_CHAT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        first = self.put(self.build("chatgpt"), name="a-first.zip")
        second = self.put(self.build("claude"), name="b-second.zip")
        real = module.file_one
        calls = []

        def flaky(zip_path, *rest):
            calls.append(zip_path.name)
            if zip_path.name == "a-first.zip":
                raise KeyError("boom")
            return real(zip_path, *rest)

        module.file_one = flaky
        out = io.StringIO()
        with unittest.mock.patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(out):
            code = module.main(["file_chat.py", "--inbox", str(self.inbox), "--no-remote-check"])
        self.assertEqual(code, 1, out.getvalue())
        self.assertEqual(calls, ["a-first.zip", "b-second.zip"])
        self.assertIn("failed  a-first.zip: KeyError: 'boom'", out.getvalue())
        self.assertIn("filed   b-second.zip → example/backup-claude", out.getvalue())
        self.assertIn("inbox summary", out.getvalue())
        self.assertEqual(self.names(self.inbox), [first.name])
        self.assertEqual(self.names(self.filed), [second.name])
        self.assertFalse((self.base / ".file-chat-inbox.lock").exists())

    def test_a_partial_top_level_zip_never_reuses_an_existing_folder_of_its_name(self):
        zip_path = self.put(self.build(partial=True))
        old = self.inbox / zip_path.stem
        old.mkdir()
        (old / zip_path.name).write_bytes(b"an older, different file")
        before = self.snapshot(old)
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertEqual(self.snapshot(old), before)
        newer = self.inbox / f"{zip_path.stem} (2)"
        self.assertEqual(self.names(newer), [zip_path.name])
        self.assertEqual(self.names(self.inbox), sorted([zip_path.stem, newer.name]))
        self.assertIn(f"drop it into inbox/{zip_path.stem} (2)/ and re-run", done.stdout)

    def test_a_save_already_filed_and_still_missing_a_file_stays_with_the_hint(self):
        folder = self.inbox / "chat"
        self.put(self.build(partial=True), folder)
        self.assertEqual(self.inbox_run("--direct", "--no-remote-check").returncode, 0)
        again = self.inbox_run("--direct", "--no-remote-check")
        self.assertEqual(again.returncode, 0, again.stdout)
        self.assertIn("already filed chat  missing f000002; drop it into inbox/chat/ and re-run", again.stdout)
        self.assertEqual(self.names(self.inbox), ["chat"])
        self.assertEqual(self.names(self.filed), [])

    def test_a_folder_name_with_a_dot_gets_a_suffix_at_the_end_when_it_clashes(self):
        first = self.inbox / "v1.2 notes"
        self.put(self.build(), first)
        self.assertEqual(self.inbox_run("--no-remote-check").returncode, 0)
        before = self.snapshot(self.filed / "v1.2 notes")
        self.put(self.build(title="A second chat"), self.inbox / "v1.2 notes")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.names(self.filed), ["v1.2 notes", "v1.2 notes (2)"])
        self.assertEqual(self.snapshot(self.filed / "v1.2 notes"), before)

    def test_one_pull_request_per_save_each_to_its_own_repo(self):
        self.put(self.build("chatgpt"))
        self.put(self.build("claude"))
        self.put(self.build("claude", title="Another claude chat"))
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(sorted(self.pr_creates()),
                         ["example/backup", "example/backup-claude", "example/backup-claude"])

    # ── symlinks, hidden, case ────────────────────────────────────────────────────────────────────────────────────

    def test_a_symlink_in_the_inbox_is_left_alone_and_its_target_untouched(self):
        outside = self.tmp / "outside"
        self.put(self.build(), outside)
        (self.inbox / "linked").symlink_to(outside, target_is_directory=True)
        before = self.snapshot(outside)
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("left alone linked: not a save", done.stdout)
        self.assertEqual(self.snapshot(outside), before)
        self.assertEqual(self.branches(), [])

    def test_a_symlink_inside_a_chat_folder_refuses_that_folder(self):
        folder = self.inbox / "chat"
        self.put(self.build(partial=True), folder)
        (self.tmp / "elsewhere").mkdir()
        target = self.png(self.tmp / "elsewhere", "target.png")
        (folder / "f000002.png").symlink_to(target)
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("refused chat: f000002.png: symbolic links are not filed", done.stdout)
        self.assertEqual(self.branches(), [])
        self.assertTrue(target.is_file())

    def test_a_hidden_folder_is_left_alone(self):
        self.put(self.build(), self.inbox / ".hidden")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("left alone .hidden: not a save", done.stdout)
        self.assertEqual(self.branches(), [])
        self.assertEqual(len(self.names(self.inbox / ".hidden")), 1)

    def test_a_files_folder_without_its_page_is_refused(self):
        folder = self.inbox / "chat"
        self.put(self.build(), folder)
        (folder / "x_files").mkdir()
        (folder / "x_files" / "a.png").write_bytes(b"a")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("refused chat: x_files: not part of a save", done.stdout)

    def test_suffixes_match_in_any_letter_case(self):
        upper = self.put(self.build(), name="Chat.ZIP")
        (self.inbox / "other.ZIP.CRDOWNLOAD").write_bytes(b"half")
        folder = self.inbox / "page chat"
        self.put(self.build(title="Page chat"), folder, name="Save.Zip")
        (folder / "X.HTML").write_text("<html>page</html>")
        (folder / "X_FILES").mkdir()
        (folder / "X_FILES" / "a.png").write_bytes(b"a")
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("skipped other.ZIP.CRDOWNLOAD: download still in progress", done.stdout)
        self.assertEqual(self.names(self.filed), sorted([upper.name, "page chat"]))
        files = [f for b in self.branches() for f in self.tree("chatgpt", b)]
        self.assertTrue(any(f.endswith("/raw/X.HTML") for f in files), files)
        self.assertTrue(any(f.endswith("/raw/X_FILES/a.png") for f in files), files)

    def test_a_refused_zip_shows_the_first_detail_in_the_summary(self):
        (self.inbox / "a-corrupt.zip").write_bytes(b"this is not a zip")
        done = self.inbox_run("--no-remote-check")
        line = [l for l in done.stdout.splitlines() if l.startswith("  refused a-corrupt.zip")][0]
        self.assertRegex(line, r"refused a-corrupt\.zip: the archive cannot be read, so nothing was filed — \S")
        self.assertFalse(line.endswith(":"))

    # ── usage and the inbox rules ─────────────────────────────────────────────────────────────────────────────────

    def test_a_zip_given_as_the_inbox_is_a_usage_error(self):
        zip_path = self.build()
        for value in (zip_path, self.tmp / "missing.ZIP"):
            done = s.run_py(s.FILE_CHAT, "--inbox", value, env=self.env)
            self.assertEqual(done.returncode, 2, done.stdout)
            self.assertIn("cannot be combined", done.stdout)
        done = s.run_py(s.FILE_CHAT, "--inbox", zip_path, self.png(self.tmp), env=self.env)
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertEqual(self.branches(), [])

    def test_a_regular_file_as_the_inbox_is_refused_and_untouched(self):
        path = self.tmp / "notes.txt"
        path.write_text("keep")
        done = s.run_py(s.FILE_CHAT, "--inbox", path, env=self.env)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("is not a folder", done.stdout)
        self.assertEqual(path.read_text(), "keep")

    def test_the_inbox_must_be_named_inbox_and_not_sit_in_home_or_the_root(self):
        home = Path(self.env["HOME"])
        for where in (self.tmp / "elsewhere", home / "chat-backups" / "filed", home / "chat-backups"):
            self.put(self.build(), where if where.name != "chat-backups" else where / "inbox")
        before = self.snapshot(home)
        for chosen in (self.tmp / "elsewhere", home / "chat-backups", home / "chat-backups" / "filed"):
            done = s.run_py(s.FILE_CHAT, "--inbox", chosen, env=self.env)
            self.assertEqual(done.returncode, 1, (chosen, done.stdout))
            self.assertIn("must be a folder named exactly inbox", done.stdout)
        self.assertEqual(self.snapshot(home), before)
        (home / "inbox").mkdir()
        done = s.run_py(s.FILE_CHAT, "--inbox", home / "inbox", env=self.env)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("must be a folder named exactly inbox", done.stdout)
        self.assertEqual(self.names(home), sorted(["chat-backups", "empty.gitconfig", "inbox"]))
        self.assertEqual(len(self.names(self.tmp / "elsewhere")), 1)

    def test_the_disk_root_is_refused_before_anything_is_read(self):
        done = s.run_py(s.FILE_CHAT, "--inbox", "/", env=self.env)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("too broad to be an inbox", done.stdout)
        self.assertNotIn("file-chat: inbox summary", done.stdout)

    # ── the lock ──────────────────────────────────────────────────────────────────────────────────────────────────

    def test_a_lock_left_by_a_process_that_is_gone_is_replaced(self):
        child = subprocess.Popen(["true"])
        child.wait()
        lock = self.base / ".file-chat-inbox.lock"
        lock.write_text(f"{child.pid}\n")
        zip_path = self.put(self.build())
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn(f"replacing a stale lock left by process {child.pid}", done.stdout)
        self.assertEqual(self.names(self.filed), [zip_path.name])
        self.assertFalse(lock.exists())

    def test_a_lock_without_a_process_number_is_refused_with_the_rm_command(self):
        lock = self.base / ".file-chat-inbox.lock"
        lock.write_text("garbage")
        zip_path = self.put(self.build())
        done = self.inbox_run()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn(f"rm {shlex.quote(str(lock.resolve()))}", done.stdout)
        self.assertEqual(lock.read_text(), "garbage")
        self.assertEqual(self.names(self.inbox), [zip_path.name])

    def test_a_lock_that_cannot_be_created_is_refused_without_a_traceback(self):
        self.base.chmod(0o555)
        self.addCleanup(self.base.chmod, 0o755)
        if os.access(self.base, os.W_OK):
            self.skipTest("this account can write to a read-only folder")
        done = self.inbox_run()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("cannot create the lock", done.stdout)
        self.assertNotIn("Traceback", done.stdout + done.stderr)

    def test_the_lock_is_removed_after_a_run_with_a_refused_item(self):
        (self.inbox / "a-corrupt.zip").write_bytes(b"this is not a zip")
        done = self.inbox_run()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertFalse((self.base / ".file-chat-inbox.lock").exists())


    def test_a_dry_run_leaves_an_already_filed_partial_top_level_zip_where_it_is(self):
        original = self.build(partial=True)
        zip_path = self.put(original)
        self.assertEqual(self.inbox_run("--direct", "--no-remote-check").returncode, 0)
        self.assertEqual(self.names(self.inbox), [zip_path.stem])
        self.put(original)
        before = self.snapshot(self.base)
        done = self.inbox_run("--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.snapshot(self.base), before)
        self.assertIn(f"dry run {zip_path.name}: already filed; missing f000002; would move into "
                      f"inbox/{zip_path.stem} (2)/", done.stdout)
        self.assertFalse((self.base / ".file-chat-inbox.lock").exists())

    def test_an_unreadable_chat_folder_is_reported_and_the_rest_is_filed(self):
        if os.geteuid() == 0:
            self.skipTest("root can read any folder")
        locked = self.inbox / "locked chat"
        locked.mkdir()
        locked.chmod(0o000)
        self.addCleanup(locked.chmod, 0o755)
        if os.access(locked, os.R_OK):
            self.skipTest("chmod has no effect here")
        good = self.put(self.build())
        done = self.inbox_run("--no-remote-check")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertRegex(done.stdout, r"failed  locked chat: \[Errno 13\]")
        self.assertEqual(self.names(self.filed), [good.name])

    def test_an_unreadable_inbox_is_refused_without_a_traceback_and_the_lock_is_removed(self):
        if os.geteuid() == 0:
            self.skipTest("root can read any folder")
        self.inbox.chmod(0o000)
        self.addCleanup(self.inbox.chmod, 0o755)
        if os.access(self.inbox, os.R_OK):
            self.skipTest("chmod has no effect here")
        done = self.inbox_run()
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("cannot read the inbox", done.stdout)
        self.assertNotIn("Traceback", done.stdout + done.stderr)
        self.assertFalse((self.base / ".file-chat-inbox.lock").exists())

    def test_a_lock_holding_a_number_no_process_can_have_is_refused_with_the_rm_command(self):
        lock = self.base / ".file-chat-inbox.lock"
        for number in ("99999999999", "2147483648", "0", "-5"):
            lock.write_text(number)
            done = self.inbox_run()
            self.assertEqual(done.returncode, 1, (number, done.stdout))
            self.assertIn(f"rm {shlex.quote(str(lock.resolve()))}", done.stdout)
            self.assertNotIn("Traceback", done.stdout + done.stderr)
            self.assertEqual(lock.read_text(), number)

    def test_a_linked_inbox_is_used_by_its_target_and_the_target_must_be_named_inbox(self):
        target = self.tmp / "cloud" / "inbox"
        zip_path = self.put(self.build(), target)
        link = self.tmp / "link-inbox"
        link.symlink_to(target, target_is_directory=True)
        done = self.inbox_run("--no-remote-check", inbox=link)
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.names(self.tmp / "cloud" / "filed"), [zip_path.name])
        self.assertEqual(self.names(self.tmp / "cloud"), ["filed", "inbox"])
        bad = self.tmp / "cloud" / "chats"
        bad.mkdir()
        wrong = self.tmp / "link-chats"
        wrong.symlink_to(bad, target_is_directory=True)
        refused = self.inbox_run(inbox=wrong)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn(f"{wrong} is a link to {bad.resolve()}, which is not", refused.stdout)

    def test_an_inbox_name_in_other_letter_case_is_refused_naming_the_rule(self):
        upper = self.base / "Inbox"
        upper.mkdir(exist_ok=True)
        done = self.inbox_run(inbox=upper)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("named exactly inbox (in lower case)", done.stdout)


if __name__ == "__main__":
    unittest.main()
