"""Tests for file_chat.py, driven end to end against a local bare repo standing in for GitHub.

Every run gets a temporary HOME, a temporary global git config and no system one, no credentials, and a fake `gh`
first on PATH. The clone's origin is a GitHub address that the temporary git config rewrites to the local bare repo,
so even with a refusal deleted the script could only write to the temporary repos.
Run from the chat-skills folder:  python3 -I tests/test_file_chat.py"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support as s  # noqa: E402
from support import chatarchive as ca  # noqa: E402

GITHUB_URL = "https://github.com/example/backup.git"
FAKE_GH = """#!/bin/sh
printf '%s\\n' "$*" >> "$GH_LOG"
case "$1 $2" in
  "repo view")
    if [ "$FAKE_GH_PRIVATE" = "false" ]; then echo '{"isPrivate":false,"nameWithOwner":"example/backup"}'
    else echo '{"isPrivate":true,"nameWithOwner":"example/backup"}'; fi ;;
  "pr list") exit 0 ;;
  "pr create")
    if [ -n "$FAKE_GH_FAIL_ONCE" ] && [ -f "$FAKE_GH_FAIL_ONCE" ]; then rm -f "$FAKE_GH_FAIL_ONCE"; echo boom >&2; exit 1; fi
    echo "https://github.com/example/backup/pull/7" ;;
  *) exit 1 ;;
esac
"""


class FileChat(unittest.TestCase):
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
        self.remote = self.tmp / "remote.git"
        Path(self.env["GIT_CONFIG_GLOBAL"]).write_text(f'[url "file://{self.remote}"]\n\tinsteadOf = {GITHUB_URL}\n')
        self.git("init", "--quiet", "--bare", "-b", "main", str(self.remote))
        self.git("-C", str(self.remote), "config", "uploadpack.allowFilter", "true")
        self.git("-C", str(self.remote), "config", "uploadpack.allowAnySHA1InWant", "true")
        seed = self.tmp / "seed"
        self.git("init", "--quiet", "-b", "main", str(seed))
        (seed / "README.md").write_text("# backup\n")
        self.git("-C", str(seed), "add", "README.md")
        self.git("-C", str(seed), "commit", "--quiet", "-m", "init")
        self.git("-C", str(seed), "push", "--quiet", f"file://{self.remote}", "main")
        self.clone = self.tmp / "clone"
        self.git("clone", "--quiet", GITHUB_URL, str(self.clone))
        self.work = s.make_work(self.tmp)

    def git(self, *args):
        return subprocess.run(["git", *args], capture_output=True, text=True, env=self.env, check=True,
                              timeout=60).stdout

    def remote_files(self, ref="main"):
        listing = self.git("-C", str(self.remote), "ls-tree", "-r", "-z", "--name-only", ref)
        return [name for name in listing.split("\0") if name]

    def remote_head(self, ref="main"):
        return self.git("-C", str(self.remote), "rev-parse", ref).strip()

    def chat_branches(self):
        return self.git("-C", str(self.remote), "branch", "--list", "chat-save/*").split()

    def build(self, change_files=None):
        if change_files:
            path = self.work / "files.json"
            files = json.loads(path.read_text())
            change_files(files)
            path.write_text(json.dumps(files))
        out = self.tmp / f"out{len(list(self.tmp.glob('out*')))}"
        done, zip_path = s.pack(self.work, out)
        self.assertEqual(done.returncode, 0, done.stdout)
        return zip_path

    def partial_zip(self):
        def missing(files):
            files[1].update(status="missing", missing_reason="not exposed")
            files[1].pop("source")
        return self.build(missing)

    def download(self, name="f000002.png", data=None):
        path = self.tmp / name
        path.write_bytes(data if data is not None else (s.FIXTURE / "uploads" / "fixture.png").read_bytes())
        return path

    def file(self, *args, env=None):
        return s.run_py(s.FILE_CHAT, *args, "--repo", str(self.clone), env=env or self.env)

    def manifest_on(self, ref="main"):
        path = [f for f in self.remote_files(ref) if f.endswith("/manifest.json")][0]
        return json.loads(self.git("-C", str(self.remote), "show", f"{ref}:{path}"))

    # ── filing ────────────────────────────────────────────────────────────────────────────────────────────────────

    def test_direct_files_the_save_and_checks_it_back(self):
        done = self.file(self.build(), "--direct")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("repo      example/backup (private)", done.stdout)
        self.assertIn("a fresh copy of the folder passed every check (8 files)", done.stdout)
        files = self.remote_files()
        folder = [f for f in files if f.endswith("/START-HERE.md")][0].rsplit("/", 1)[0]
        self.assertRegex(folder, r"^chats/synthetic-pilot--[0-9a-f]{6}/\d{8}T\d{6}Z-[0-9a-f]{12}$")
        self.assertIn(folder.rsplit("/", 1)[0] + "/README.md", files)
        self.assertTrue((self.clone / folder / "manifest.json").is_file(), "clean checkout was not fast-forwarded")

    def test_filing_the_same_save_again_changes_nothing(self):
        zip_path = self.build()
        self.assertEqual(self.file(zip_path, "--direct").returncode, 0)
        head = self.remote_head()
        again = self.file(zip_path, "--direct")
        self.assertEqual(again.returncode, 0, again.stdout)
        self.assertIn("nothing to do", again.stdout)
        self.assertEqual(self.remote_head(), head)

    def test_default_opens_a_pull_request_and_leaves_main_alone(self):
        head = self.remote_head()
        done = self.file(self.build())
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("https://github.com/example/backup/pull/7", done.stdout)
        self.assertEqual(self.remote_head(), head)
        branches = self.chat_branches()
        self.assertEqual(len(branches), 1)
        self.assertIn(f"pr create --repo example/backup --base main --head {branches[0]}", self.gh_log.read_text())

    def test_it_never_changes_the_checkout_when_it_opens_a_pull_request(self):
        before = self.git("-C", str(self.clone), "status", "--porcelain", "--branch")
        self.assertEqual(self.file(self.build()).returncode, 0)
        self.assertEqual(self.git("-C", str(self.clone), "status", "--porcelain", "--branch"), before)

    def test_a_rerun_after_a_failed_pull_request_reuses_the_pushed_branch(self):
        marker = self.tmp / "fail-once"
        marker.touch()
        zip_path = self.build()
        first = self.file(zip_path, env=dict(self.env, FAKE_GH_FAIL_ONCE=str(marker)))
        self.assertEqual(first.returncode, 1, first.stdout)
        self.assertIn("but opening the pull request failed", first.stdout)
        branch = self.chat_branches()[0]
        tip = self.remote_head(branch)
        second = self.file(zip_path)
        self.assertEqual(second.returncode, 0, second.stdout)
        self.assertIn("already there from an earlier run", second.stdout)
        self.assertIn("https://github.com/example/backup/pull/7", second.stdout)
        self.assertEqual(self.remote_head(branch), tip)

    def test_adding_a_download_while_the_pull_request_is_open_fast_forwards_its_branch(self):
        zip_path = self.partial_zip()
        self.assertEqual(self.file(zip_path).returncode, 0)
        branch = self.chat_branches()[0]
        first_tip = self.remote_head(branch)
        done = self.file(zip_path, self.download())
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.chat_branches(), [branch])
        self.assertEqual(self.git("-C", str(self.remote), "rev-parse", f"{branch}~1").strip(), first_tip)
        self.assertEqual(self.manifest_on(branch)["coverage"]["status"], "complete")

    # ── downloads, completion, raw material ───────────────────────────────────────────────────────────────────────

    def test_a_downloaded_file_completes_a_partial_save(self):
        done = self.file(self.partial_zip(), self.download(), "--direct")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("COMPLETE (1 file(s) added from your downloads)", done.stdout)
        manifest = self.manifest_on()
        self.assertEqual(manifest["files"][1]["bytes_from"], "user_download")
        self.assertEqual(manifest["coverage"]["status"], "complete")

    def test_a_later_download_updates_the_filed_save_in_place(self):
        zip_path = self.partial_zip()
        self.assertEqual(self.file(zip_path, "--direct").returncode, 0)
        done = self.file(zip_path, self.download("f000002-from-chat.png", b"\x89PNG later"), "--direct")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertEqual(self.manifest_on()["coverage"]["status"], "complete")
        self.assertEqual(len([f for f in self.remote_files() if f.endswith("/manifest.json")]), 1)

    def test_the_original_zip_after_a_completion_is_already_filed(self):
        zip_path = self.partial_zip()
        self.assertEqual(self.file(zip_path, self.download(), "--direct").returncode, 0)
        head = self.remote_head()
        again = self.file(zip_path, "--direct")
        self.assertEqual(again.returncode, 0, again.stdout)
        self.assertIn("the filed copy has as many files or more", again.stdout)
        self.assertEqual(self.remote_head(), head)

    def test_raw_material_is_kept_byte_for_byte_without_finder_files(self):
        page = self.tmp / "Synthetic pilot.html"
        page.write_text("<html>saved page</html>")
        assets = self.tmp / "Synthetic pilot_files"
        assets.mkdir()
        (assets / "image.png").write_bytes(b"\x89PNG asset")
        (assets / ".DS_Store").write_bytes(b"finder")
        done = self.file(self.build(), "--raw", page, "--raw", assets, "--direct")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("left out raw/Synthetic pilot_files/.DS_Store (a Finder file)", done.stdout)
        files = self.remote_files()
        self.assertTrue(any(f.endswith("/raw/Synthetic pilot.html") for f in files))
        self.assertTrue(any(f.endswith("/raw/Synthetic pilot_files/image.png") for f in files))
        self.assertFalse(any(f.endswith(".DS_Store") for f in files))

    def test_downloads_may_follow_the_options(self):
        page = self.tmp / "page.html"
        page.write_text("<html></html>")
        done = self.file(self.partial_zip(), "--raw", page, self.download(), "--direct")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("COMPLETE", done.stdout)

    def test_the_repo_comes_from_the_environment_when_not_given(self):
        env = dict(self.env, CHAT_SAVE_REPO_CHATGPT=str(self.clone))
        done = s.run_py(s.FILE_CHAT, self.build(), "--direct", env=env)
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_dry_run_writes_nothing(self):
        head = self.remote_head()
        done = self.file(self.build(), "--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("dry run", done.stdout)
        self.assertIn("in example/backup (private)", done.stdout)
        self.assertEqual(self.remote_head(), head)
        self.assertEqual(self.chat_branches(), [])

    def test_skipping_the_remote_check_says_so(self):
        done = self.file(self.build(), "--direct", "--no-remote-check")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("not re-read (--no-remote-check)", done.stdout)

    def test_in_pr_mode_the_original_zip_after_a_completion_takes_nothing_away(self):
        zip_path = self.partial_zip()
        self.assertEqual(self.file(zip_path).returncode, 0)
        self.assertEqual(self.file(zip_path, self.download()).returncode, 0)
        branch = self.chat_branches()[0]
        tip = self.remote_head(branch)
        again = self.file(zip_path)
        self.assertEqual(again.returncode, 0, again.stdout)
        self.assertIn("already holds this save with as many files or more", again.stdout)
        self.assertEqual(self.remote_head(branch), tip)
        self.assertTrue(any(f.endswith("/files/f000002-fixture.png") for f in self.remote_files(branch)))

    def test_in_pr_mode_a_different_download_for_the_same_file_is_refused(self):
        zip_path = self.partial_zip()
        self.assertEqual(self.file(zip_path).returncode, 0)
        self.assertEqual(self.file(zip_path, self.download()).returncode, 0)
        branch = self.chat_branches()[0]
        tip = self.remote_head(branch)
        other = self.download("f000002-other.png", b"\x89PNG different bytes")
        self.assert_refused(self.file(zip_path, other), "a filed save is never overwritten")
        self.assertEqual(self.remote_head(branch), tip)

    def test_a_saved_page_named_in_decomposed_unicode_is_filed_and_verifies(self):
        decomposed = unicodedata.normalize("NFD", "Café plan.html")
        page = self.tmp / decomposed
        page.write_text("<html>café</html>")
        done = self.file(self.build(), "--raw", page, "--direct")
        self.assertEqual(done.returncode, 0, done.stdout)
        composed = unicodedata.normalize("NFC", "Café plan.html")
        self.assertTrue(any(f.endswith(f"/raw/{composed}") for f in self.remote_files()), self.remote_files())

    def test_an_already_filed_copy_that_no_longer_verifies_is_reported(self):
        zip_path = self.build()
        self.assertEqual(self.file(zip_path, "--direct").returncode, 0)
        editor = self.tmp / "editor"
        self.git("clone", "--quiet", f"file://{self.remote}", str(editor))
        target = next(editor.glob("chats/*/*/files/f000001-fixture.md"))
        target.write_text("changed by hand\n")
        self.git("-C", str(editor), "commit", "--quiet", "-am", "edit a filed file by hand")
        self.git("-C", str(editor), "push", "--quiet", "origin", "main")
        again = self.file(zip_path, "--direct")
        self.assert_refused(again, "the filed copy does NOT verify")

    def test_refuses_a_push_address_that_differs_from_the_fetch_address(self):
        self.git("-C", str(self.clone), "config", "remote.origin.pushurl", "https://github.com/example/other.git")
        head = self.remote_head()
        self.assert_refused(self.file(self.build(), "--direct"), "pushes to a different address")
        self.assert_unchanged(head)

    def test_raw_names_that_collide_on_this_disk_are_refused_before_the_push(self):
        probe = self.tmp / "CaseProbe"
        probe.touch()
        if not (self.tmp / "caseprobe").exists():
            self.skipTest("this file system tells upper and lower case apart")
        first, second = self.tmp / "one", self.tmp / "two"
        first.mkdir()
        second.mkdir()
        (first / "Page.html").write_text("one")
        (second / "page.html").write_text("two")
        head = self.remote_head()
        done = self.file(self.build(), "--raw", first / "Page.html", "--raw", second / "page.html", "--direct")
        self.assert_refused(done, "would not read back the same from a checkout")
        self.assert_unchanged(head)

    def test_a_file_github_would_refuse_is_refused(self):
        spec = importlib.util.spec_from_file_location("file_chat_under_test", s.FILE_CHAT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.MAX_FILE_BYTES = 10
        with self.assertRaises(module.Refusal) as caught:
            module.check_fileable({"files/f000001-big.bin": b"x" * 20})
        self.assertIn("GitHub refuses files over 100 MB", str(caught.exception))

    # ── refusals: each leaves GitHub unchanged ────────────────────────────────────────────────────────────────────

    def assert_refused(self, done, expected):
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn(expected, done.stdout)

    def assert_unchanged(self, head):
        self.assertEqual(self.remote_head(), head)
        self.assertEqual(self.chat_branches(), [])

    def test_refuses_an_archive_that_fails_verification(self):
        bad = self.tmp / "bad.zip"
        entries = [(n, d.replace(b"cedar", b"pine!") if n.startswith("files/") and n.endswith(".md") else d, a)
                   for n, d, a in s.read_raw(self.build())]
        s.write_raw(bad, entries)
        head = self.remote_head()
        self.assert_refused(self.file(bad, "--direct"), "failed verification, so nothing was filed")
        self.assert_unchanged(head)

    def test_refuses_a_repo_github_does_not_confirm_private(self):
        head = self.remote_head()
        done = self.file(self.build(), env=dict(self.env, FAKE_GH_PRIVATE="false"))
        self.assert_refused(done, "is not confirmed private by GitHub, so nothing was filed")
        self.assert_unchanged(head)

    def test_refuses_an_origin_that_is_not_github(self):
        self.git("-C", str(self.clone), "remote", "set-url", "origin", f"file://{self.remote}")
        head = self.remote_head()
        self.assert_refused(self.file(self.build(), "--direct"), "is not a GitHub repo")
        self.assert_unchanged(head)

    def test_refuses_a_name_git_treats_specially(self):
        assets = self.tmp / "page_files"
        assets.mkdir()
        (assets / ".gitattributes").write_text("* -text\n")
        head = self.remote_head()
        self.assert_refused(self.file(self.build(), "--raw", assets, "--direct"), "git treats this name specially")
        self.assert_unchanged(head)

    def test_refuses_a_download_without_a_file_id(self):
        self.assert_refused(self.file(self.partial_zip(), self.download("sketch.png"), "--direct"),
                            "must start with the file id")

    def test_refuses_a_download_for_a_file_already_captured(self):
        self.assert_refused(self.file(self.partial_zip(), self.download("f000001.md", b"x"), "--direct"),
                            "was already captured")

    def test_refuses_a_repo_with_commit_hooks(self):
        hook = self.clone / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 0\n")
        hook.chmod(0o755)
        self.assert_refused(self.file(self.build(), "--direct"), "has commit hooks (pre-commit)")

    def test_refuses_a_folder_that_is_not_a_clone(self):
        done = s.run_py(s.FILE_CHAT, self.build(), "--repo", str(self.tmp / "nowhere"), env=self.env)
        self.assert_refused(done, "is not a clone of your ChatGPT backup repo")

    def test_never_overwrites_a_different_save_with_the_same_revision(self):
        zip_path = self.build()
        self.assertEqual(self.file(zip_path, "--direct").returncode, 0)
        members = {n: d for n, d, _ in s.read_raw(zip_path)}
        messages = [json.loads(line) for line in ca.text_lines(members["transcript.jsonl"])]
        messages[1]["text"] = "Pilot B acknowledged."
        manifest = json.loads(members["manifest.json"])
        manifest["content_sha256"] = ca.content_hash(manifest["source"], messages, manifest["files"],
                                                     manifest["coverage"])
        members.update({"manifest.json": ca.manifest_bytes(manifest),
                        "transcript.jsonl": ca.transcript_jsonl(messages),
                        "transcript.md": ca.render_transcript_md(manifest, messages)})
        members["START-HERE.md"] = ca.render_start_here(manifest, messages, members["brief.md"])
        forged = self.tmp / "same-revision.zip"
        s.write_members(forged, s.with_fresh_checksums(members))
        head = self.remote_head()
        self.assert_refused(self.file(forged, "--direct"), "a filed save is never overwritten")
        self.assertEqual(self.remote_head(), head)

    def test_a_rejected_push_says_github_is_unchanged(self):
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\necho 'rejected for the test' >&2\nexit 1\n")
        hook.chmod(0o755)
        head = self.remote_head()
        self.assert_refused(self.file(self.build(), "--direct"), "not pushed, so GitHub is unchanged")
        self.assertEqual(self.remote_head(), head)


if __name__ == "__main__":
    unittest.main()
