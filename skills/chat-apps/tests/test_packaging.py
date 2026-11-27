"""Tests for the upload ZIPs (build_zips.py) and the skill texts.
Run from the chat-skills folder:  python3 -I tests/test_packaging.py"""
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support as s  # noqa: E402

GUARD = "Stop if this is Claude Code or Codex"
EXPECTED = {
    "chat-save": {"chat-save/SKILL.md", "chat-save/scripts/pack.py", "chat-save/scripts/chatarchive.py",
                  "chat-save/references/format.md"},
    "chat-restore": {"chat-restore/SKILL.md", "chat-restore/scripts/verify.py", "chat-restore/scripts/chatarchive.py",
                     "chat-restore/references/format.md", "chat-restore/references/legacy-layouts.md"},
}


def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


class Zips(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def build(self, out):
        done = s.run_py(s.BUILD_ZIPS, "--out", out)
        self.assertEqual(done.returncode, 0, done.stdout)
        return {skill: Path(out) / f"{skill}.zip" for skill in EXPECTED}

    def test_each_zip_holds_exactly_its_skill_folder(self):
        for skill, path in self.build(self.tmp / "dist").items():
            names = set(zipfile.ZipFile(path).namelist())
            self.assertEqual(names, EXPECTED[skill], f"{skill}.zip holds {sorted(names)}")

    def test_the_same_source_gives_the_same_bytes(self):
        first = self.build(self.tmp / "a")
        second = self.build(self.tmp / "b")
        for skill in EXPECTED:
            self.assertEqual(first[skill].read_bytes(), second[skill].read_bytes())

    def test_an_unzipped_skill_runs_on_its_own(self):
        zips = self.build(self.tmp / "dist")
        for skill, path in zips.items():
            zipfile.ZipFile(path).extractall(self.tmp / "installed")
        installed = self.tmp / "installed"
        done = s.run_py(installed / "chat-save" / "scripts" / "pack.py", s.make_work(self.tmp), "--out",
                        self.tmp / "saved", "--now", s.NOW)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        archive = next((self.tmp / "saved").glob("*.zip"))
        check = s.run_py(installed / "chat-restore" / "scripts" / "verify.py", archive)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


class SkillTexts(unittest.TestCase):
    def test_frontmatter_follows_the_skill_rules(self):
        for skill in EXPECTED:
            fields = frontmatter((s.ROOT / skill / "SKILL.md").read_text())
            self.assertEqual(fields.get("name"), skill)
            self.assertRegex(fields["name"], r"^[a-z0-9-]{1,64}$")
            self.assertLessEqual(len(fields.get("description", "")), 1024)
            self.assertIn("never Claude Code or Codex", fields["description"])

    def test_each_skill_starts_by_stopping_in_claude_code_or_codex(self):
        for skill in EXPECTED:
            body = (s.ROOT / skill / "SKILL.md").read_text()
            first_step = body.index("## 0.")
            self.assertLess(first_step, body.index("## 1."))
            self.assertIn(GUARD, body[first_step:body.index("## 1.")])

    def test_save_never_claims_exactness_or_asks_for_a_token(self):
        body = (s.ROOT / "chat-save" / "SKILL.md").read_text()
        self.assertIn("**Evidence** is always `model_copy`", body)
        self.assertIn("pack.py refuses anything else", body)
        self.assertIn("never ask for a\ntoken", body)

    def test_the_skill_texts_stay_short_enough_to_follow(self):
        for skill in EXPECTED:
            self.assertLess(len((s.ROOT / skill / "SKILL.md").read_bytes()), 10_000, skill)


if __name__ == "__main__":
    unittest.main()
