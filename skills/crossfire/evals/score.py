#!/usr/bin/env python3
"""Score a crossfire summary against a case's answer key.

    python3 -I score.py <case-id> <summary.md> [cases.json]

For each planted defect in cases.json, a defect counts as caught when one row of the summary's Conditions table
has, in its Finding or Protects cell, at least one phrase from every group in its `all_of`. Phrases match
case-insensitively at the start of a word ("url" matches "URL" and "urls", not "curl"). A `must_block` defect only
counts when that row's Blocks cell is "yes". It also reports the gate, the number of blocking rows, the blocking rows
that match no planted defect (to read by hand: some are real problems the key did not plant), and the words above
the Conditions table.

Exit 0 after printing the score, whatever it is: this measures, it does not gate. Exit 2 when it cannot score: the
summary has no gate line, no Conditions table, a table without a separator row or the expected columns, or is not
UTF-8; or cases.json is malformed or lacks the case. A scorer that cannot read its input must not print a score.

Known limits: phrase matching misses a defect described in words the key does not list, and can credit a row that
uses the phrases while saying something else. Read the rows when a number surprises you.
"""
import json
import re
import sys
from pathlib import Path

GATE = re.compile(r"\*\*Gate:\s*(INCOMPLETE|STOP|PASS|ESCALATE|REVISE)\b")
COLUMNS = ("id", "sev", "blocks", "finding")
MATCHED_COLUMNS = ("finding", "protects")
PIPE = re.compile(r"(?<!\\)\|")
SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
YES = re.compile(r"yes\b", re.I)


class Unscorable(Exception):
    pass


def cells(line):
    """Split a table row on unescaped pipes, so `a \\| b` inside a cell stays one cell."""
    return [cell.strip() for cell in PIPE.split(line.strip().strip("|"))]


def section(text, heading):
    match = re.search(rf"^## {heading}\s*$", text, re.M)
    if not match:
        return None, None
    body = text[match.end():]
    end = re.search(r"^## ", body, re.M)
    return match, body[: end.start()] if end else body


def parse_summary(text):
    verdict, verdict_body = section(text, "Verdict")
    gate = GATE.search(verdict_body if verdict else text)
    if not gate:
        raise Unscorable("no '**Gate: ...**' line" + (" in the Verdict section" if verdict else ""))
    heading, body = section(text, "Conditions")
    if not heading:
        raise Unscorable("no '## Conditions' section")
    lines = [line.strip() for line in body.splitlines()]
    start = next((i for i, line in enumerate(lines) if line.startswith("|")), None)
    if start is None:
        raise Unscorable("the Conditions section has no table")
    table = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        table.append(line)
    if len(table) < 2 or not SEPARATOR.match(table[1]):
        raise Unscorable("the Conditions table has no separator row under its header")
    header = [cell.lower() for cell in cells(table[0])]
    if not all(column in header for column in COLUMNS):
        raise Unscorable(f"the Conditions table lacks a column of {COLUMNS}: has {header}")
    rows = []
    for line in table[2:]:
        row = cells(line)
        if len(row) != len(header):
            raise Unscorable(f"a row has {len(row)} cells, the header has {len(header)}: {line}")
        rows.append(dict(zip(header, row)))
    return {"gate": gate.group(1), "rows": rows, "words_above_table": len(text[: heading.start()].split())}


def blocks(row):
    return bool(YES.match(row["blocks"].strip()))


def phrase(text, words):
    return re.search(r"\b" + re.escape(words.lower()), text) is not None


def matches(row, defect):
    text = " ".join(row.get(column, "") for column in MATCHED_COLUMNS).lower()
    return all(any(phrase(text, words) for words in group) for group in defect["all_of"])


def score(case, parsed):
    caught, missed = [], []
    matched_rows = set()
    for defect in case["defects"]:
        hits = [i for i, row in enumerate(parsed["rows"])
                if matches(row, defect) and (blocks(row) or not defect.get("must_block"))]
        (caught if hits else missed).append(defect["id"])
        matched_rows.update(hits)
    blocking = [i for i, row in enumerate(parsed["rows"]) if blocks(row)]
    unplanted = [parsed["rows"][i]["id"] for i in blocking if i not in matched_rows]
    max_blockers = case.get("max_blockers")
    return {
        "gate": parsed["gate"],
        "gate_expected": parsed["gate"] in case["expect_gate"],
        "caught": caught,
        "missed": missed,
        "blocking_rows": len(blocking),
        "over_max_blockers": max_blockers is not None and len(blocking) > max_blockers,
        "blocking_rows_not_planted": unplanted,
        "rows": len(parsed["rows"]),
        "words_above_table": parsed["words_above_table"],
    }


def main(argv):
    if len(argv) not in (3, 4):
        print("usage: python3 -I score.py <case-id> <summary.md> [cases.json]", file=sys.stderr)
        return 2
    case_id, summary_path = argv[1], Path(argv[2])
    cases_path = Path(argv[3]) if len(argv) == 4 else Path(__file__).with_name("cases.json")
    try:
        cases = json.loads(cases_path.read_text())
        case = cases[case_id]
        for defect in case["defects"]:
            if not all(isinstance(group, list) for group in defect["all_of"]):
                raise Unscorable(f"defect {defect['id']}: every all_of group must be a list of phrases")
        parsed = parse_summary(summary_path.read_text(encoding="utf-8"))
        result = score(case, parsed)
    except KeyError as err:
        print(f"cannot score: case {case_id!r} or its field {err} is missing from {cases_path}", file=sys.stderr)
        return 2
    except (Unscorable, OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as err:
        print(f"cannot score {summary_path}: {err}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
