"""Tests for run.py's setup, which needs only git (no Claude session). Run: python3 -I test_run.py"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import run  # noqa: E402

CASES = json.loads((HERE / "cases.json").read_text())


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60, env=run.GIT_ENV)


class Prepare(unittest.TestCase):
    def prepare(self, case_id):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        return work, run.prepare(case_id, CASES[case_id], work)

    def stage(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        plugin = Path(tmp.name) / "plugin"
        run.stage_plugin(plugin)
        return plugin

    def test_stages_a_minimal_plugin_with_the_runtime_skill_and_agents_but_never_the_answer_keys(self):
        plugin = self.stage()
        files = sorted(str(f.relative_to(plugin)) for f in plugin.rglob("*") if f.is_file())
        self.assertEqual(json.loads((plugin / ".claude-plugin" / "plugin.json").read_text()), {"name": "crossfire"})
        self.assertTrue((plugin / "skills" / "crossfire" / "SKILL.md").is_file())
        self.assertTrue((plugin / "skills" / "crossfire" / "references").is_dir())
        self.assertTrue((plugin / "agents" / "crossfire-reviewer.md").is_file())
        self.assertTrue((plugin / "agents" / "crossfire-verifier.md").is_file())
        self.assertEqual(sorted(p.name for p in plugin.iterdir()), [".claude-plugin", "agents", "skills"])
        self.assertEqual(sorted(p.name for p in (plugin / "skills" / "crossfire").iterdir()), ["SKILL.md", "references"])
        for banned in ("README.md", "PLAYBOOK.md", "COMPARISON.md", "cases.json"):
            self.assertNotIn(banned, [Path(f).name for f in files])
        self.assertFalse(any(part in ("evals", "examples") for f in files for part in Path(f).parts))
        installed = [f for f in plugin.rglob("*") if f.is_file()]
        clues = ["must_block", "planted", "answer key", "cases.json", "examples/"]
        for case in CASES.values():
            clues.append(case["target"])
            for defect in case["defects"]:
                clues.append(defect["id"])
        leaked = sorted({f"{f.name}: {clue}" for f in installed for clue in clues
                         if clue.lower() in f.read_text(errors="ignore").lower()})
        self.assertEqual(leaked, [])

    def test_the_plugin_is_outside_the_case_repo_and_the_repo_holds_no_skill(self):
        plugin = self.stage()
        work, _ = self.prepare("help-page-copy")
        self.assertNotIn(work, plugin.parents)
        self.assertFalse((work / ".claude").exists())

    def test_the_workspaces_are_separate_folders_and_the_repo_gets_no_claude_folder(self):
        work, plugin, _ = run.make_workspaces("help-page-copy", CASES["help-page-copy"])
        self.addCleanup(shutil.rmtree, work)
        self.addCleanup(shutil.rmtree, plugin)
        self.assertNotIn(work, plugin.parents)
        self.assertNotIn(plugin, work.parents)
        self.assertNotEqual(work, plugin)
        self.assertTrue((plugin / ".claude-plugin" / "plugin.json").is_file())
        self.assertFalse((work / ".claude").exists())
        self.assertFalse((work / ".claude-plugin").exists())
        self.assertEqual(git(work, "status", "--porcelain").stdout, "")

    def test_the_session_command_loads_the_staged_plugin_with_project_settings_only(self):
        command = run.session_command("/crossfire x", Path("/some/plugin"), "opus", 25)
        self.assertEqual(command[command.index("--plugin-dir") + 1], "/some/plugin")
        self.assertEqual(command[command.index("--setting-sources") + 1], "project")
        self.assertIn("--strict-mcp-config", command)
        self.assertEqual(command[:3], ["claude", "-p", "/crossfire x"])

    def test_one_commit_and_the_run_folder_is_ignored(self):
        work, seeded = self.prepare("help-page-copy")
        self.assertIsNone(seeded)
        self.assertEqual(git(work, "rev-list", "--count", "HEAD").stdout.strip(), "1")
        self.assertEqual(git(work, "check-ignore", "-q", ".crossfire/x").returncode, 0)
        self.assertEqual(git(work, "status", "--porcelain").stdout, "")

    def test_the_same_files_give_the_same_commit(self):
        first, _ = self.prepare("password-reset")
        second, _ = self.prepare("password-reset")
        self.assertEqual(git(first, "rev-parse", "HEAD").stdout, git(second, "rev-parse", "HEAD").stdout)

    def test_a_second_round_seeds_the_first_rounds_summary_and_overlays_the_answers(self):
        case = CASES["help-page-copy-round2"]
        base_name = case["round_of"]
        examples = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, examples)
        base = examples / base_name
        shutil.copytree(HERE.parent / "examples" / base_name / "repo", base / "repo")
        shutil.copytree(HERE.parent / "examples" / base_name / case["overlay"], base / case["overlay"])
        (base / "output" / "run" / "help-copy" / "r1").mkdir(parents=True)
        (base / "output" / "run" / "help-copy" / "r1" / "chair.md").write_text("round 1 chair\n")
        (base / "output" / "summary.crossfire.md").write_text("**Gate: STOP.** round 1\n")
        real = run.EXAMPLES
        run.EXAMPLES = examples
        self.addCleanup(setattr, run, "EXAMPLES", real)
        work, seeded = self.prepare("help-page-copy-round2")
        self.assertEqual(seeded, b"**Gate: STOP.** round 1\n")
        self.assertEqual((work / case["summary"]).read_bytes(), seeded)
        self.assertEqual(git(work, "rev-list", "--count", "HEAD").stdout.strip(), "2")
        self.assertTrue((work / "src" / "help" / "banner.js").exists())
        self.assertTrue((work / ".crossfire" / "help-copy" / "r1" / "chair.md").exists())
        self.assertEqual(git(work, "ls-files", ".crossfire").stdout, "")

if __name__ == "__main__":
    unittest.main()
