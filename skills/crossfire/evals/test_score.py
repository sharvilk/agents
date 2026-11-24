"""Tests for score.py. Run: python3 -I test_score.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import score  # noqa: E402

CASE = {
    "expect_gate": ["REVISE"],
    "max_blockers": 1,
    "defects": [
        {"id": "leak", "must_block": True, "all_of": [["log"], ["token"]]},
        {"id": "slow", "must_block": False, "all_of": [["unbounded", "full scan"]]},
    ],
}

HEAD = "| ID | Sev | Blocks | Finding | Protects | Check | Status |\n| --- | --- | --- | --- | --- | --- | --- |\n"
LEAK = "| C1 | major | yes | the token lands in the access log | A1 | grep | open |\n"


def summary(rows, gate="REVISE", before=""):
    return (f"# crossfire: x\n\n{before}## Verdict\n\n**Gate: {gate}.** because.\n\nDo it.\n\n"
            f"## Conditions\n\n{HEAD}{rows}\n## Run\n\nx\n")


class Parse(unittest.TestCase):
    def test_refuses_a_summary_without_a_gate_line(self):
        with self.assertRaises(score.Unscorable):
            score.parse_summary(summary(LEAK).replace("**Gate: REVISE.**", "Gate is revise"))

    def test_reads_the_gate_from_the_verdict_not_earlier_prose(self):
        parsed = score.parse_summary(summary(LEAK, gate="STOP", before="Last time: **Gate: PASS.**\n\n"))
        self.assertEqual(parsed["gate"], "STOP")

    def test_refuses_a_summary_with_no_conditions_heading(self):
        with self.assertRaises(score.Unscorable):
            score.parse_summary("# crossfire: x\n\n**Gate: PASS.** fine.\n\n## Run\n\nx\n")

    def test_refuses_a_conditions_section_without_a_table(self):
        with self.assertRaises(score.Unscorable):
            score.parse_summary("**Gate: PASS.** fine.\n\n## Conditions\n\nNone.\n")

    def test_refuses_a_table_without_a_separator_row(self):
        text = summary(LEAK).replace("| --- | --- | --- | --- | --- | --- | --- |\n", "")
        with self.assertRaises(score.Unscorable):
            score.parse_summary(text)

    def test_refuses_a_table_missing_a_column(self):
        text = "**Gate: PASS.** x\n\n## Conditions\n\n| ID | Sev | Finding |\n| --- | --- | --- |\n| C1 | nit | x |\n"
        with self.assertRaises(score.Unscorable):
            score.parse_summary(text)

    def test_refuses_a_row_with_the_wrong_cell_count(self):
        with self.assertRaises(score.Unscorable):
            score.parse_summary(summary("| C1 | major | yes | split | here | A1 | grep | open |\n"))

    def test_reads_only_the_first_table_in_the_section(self):
        second = "\nAnother table:\n\n| A | B | C | D | E | F | G |\n| --- | --- | --- | --- | --- | --- | --- |\n"
        parsed = score.parse_summary(summary(LEAK + second))
        self.assertEqual([row["id"] for row in parsed["rows"]], ["C1"])

    def test_an_escaped_pipe_stays_inside_its_cell(self):
        parsed = score.parse_summary(summary("| C1 | major | yes | the token lands in a \\| b log | A1 | grep | open |\n"))
        self.assertEqual(len(parsed["rows"]), 1)

    def test_windows_line_endings_parse(self):
        parsed = score.parse_summary(summary(LEAK).replace("\n", "\r\n"))
        self.assertEqual(parsed["gate"], "REVISE")
        self.assertEqual(len(parsed["rows"]), 1)

    def test_counts_the_words_above_the_table(self):
        parsed = score.parse_summary(summary(LEAK))
        self.assertEqual(parsed["words_above_table"], len("# crossfire: x ## Verdict **Gate: REVISE.** because. Do it.".split()))


class Score(unittest.TestCase):
    def run_case(self, text, case=CASE):
        return score.score(case, score.parse_summary(text))

    def test_catches_every_planted_defect(self):
        result = self.run_case(summary(LEAK + "| C2 | minor | no | a full scan on users | D1 | explain | follow-up: low |\n"))
        self.assertEqual(result["caught"], ["leak", "slow"])
        self.assertEqual(result["missed"], [])
        self.assertTrue(result["gate_expected"])
        self.assertEqual(result["blocking_rows_not_planted"], [])

    def test_a_must_block_defect_in_a_non_blocking_row_is_missed(self):
        result = self.run_case(summary(LEAK.replace("| yes |", "| no |")))
        self.assertEqual(result["missed"], ["leak", "slow"])

    def test_a_row_must_match_every_phrase_group(self):
        result = self.run_case(summary("| C1 | major | yes | the access log is noisy | A1 | grep | open |\n"))
        self.assertEqual(result["missed"], ["leak", "slow"])

    def test_phrases_match_at_the_start_of_a_word_only(self):
        case = {"expect_gate": ["REVISE"], "defects": [
            {"id": "url", "all_of": [["url"]]}, {"id": "ttl", "all_of": [["ttl"]]}]}
        text = summary("| C1 | minor | no | run curl to settle it | A1 | x | open |\n"
                       "| C2 | minor | no | the URLs and the TTL | A1 | x | open |\n")
        result = self.run_case(text, case)
        self.assertEqual(result["caught"], ["url", "ttl"])
        text_without = summary("| C1 | minor | no | run curl to settle it | A1 | x | open |\n")
        self.assertEqual(self.run_case(text_without, case)["missed"], ["url", "ttl"])

    def test_phrases_in_the_check_or_status_cells_do_not_count(self):
        result = self.run_case(summary("| C1 | major | yes | a problem | A1 | grep the log for the token | open |\n"))
        self.assertEqual(result["missed"], ["leak", "slow"])

    def test_phrases_in_the_protects_cell_count(self):
        result = self.run_case(summary("| C1 | major | yes | the access log | A1 never log a token | x | open |\n"))
        self.assertEqual(result["caught"], ["leak"])

    def test_blocks_accepts_yes_in_any_case_and_nothing_else(self):
        self.assertTrue(score.blocks({"blocks": "Yes"}))
        self.assertTrue(score.blocks({"blocks": "yes (verified)"}))
        self.assertFalse(score.blocks({"blocks": "yesterday"}))
        self.assertFalse(score.blocks({"blocks": "no"}))

    def test_counts_blocking_rows_the_key_did_not_plant(self):
        result = self.run_case(summary(LEAK + "| C2 | major | yes | sessions survive a reset | A2 | test | open |\n"))
        self.assertEqual(result["blocking_rows_not_planted"], ["C2"])
        self.assertTrue(result["over_max_blockers"])

    def test_max_blockers_zero_and_unset(self):
        clean = {"expect_gate": ["PASS"], "max_blockers": 0, "defects": []}
        self.assertTrue(self.run_case(summary(LEAK, gate="PASS"), clean)["over_max_blockers"])
        self.assertFalse(self.run_case(summary(LEAK.replace("| yes |", "| no |"), gate="PASS"), clean)["over_max_blockers"])
        unset = {"expect_gate": ["PASS"], "max_blockers": None, "defects": []}
        self.assertFalse(self.run_case(summary(LEAK, gate="PASS"), unset)["over_max_blockers"])

    def test_any_of_several_expected_gates(self):
        case = dict(CASE, expect_gate=["STOP", "REVISE"])
        self.assertTrue(self.run_case(summary(LEAK, gate="STOP"), case)["gate_expected"])
        self.assertFalse(self.run_case(summary(LEAK, gate="PASS"), case)["gate_expected"])


class CommandLine(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-I", str(HERE / "score.py"), *map(str, args)],
                              capture_output=True, text=True, timeout=30)

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = Path(tmp, "cases.json")
            stringy = {"expect_gate": ["PASS"], "defects": [{"id": "d", "all_of": ["log", "token"]}]}
            cases.write_text(json.dumps({"c": CASE, "broken": {"defects": []}, "stringy": stringy}))
            good = Path(tmp, "good.md")
            good.write_text(summary(LEAK))
            bad = Path(tmp, "bad.md")
            bad.write_text("no gate here\n")
            binary = Path(tmp, "binary.md")
            binary.write_bytes(b"\xff\xfe\x00not utf-8")
            junk = Path(tmp, "junk.json")
            junk.write_text("{not json")
            self.assertEqual(self.run_cli("c", good, cases).returncode, 0)
            self.assertEqual(self.run_cli("c", bad, cases).returncode, 2)
            self.assertEqual(self.run_cli("c", binary, cases).returncode, 2)
            self.assertEqual(self.run_cli("nope", good, cases).returncode, 2)
            self.assertEqual(self.run_cli("broken", good, cases).returncode, 2)
            self.assertEqual(self.run_cli("stringy", good, cases).returncode, 2)
            self.assertEqual(self.run_cli("c", good, junk).returncode, 2)
            self.assertEqual(self.run_cli("c").returncode, 2)


if __name__ == "__main__":
    unittest.main()
