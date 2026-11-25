# crossfire evals

The tools that check whether `/crossfire` does what it claims: run it end to end on a made-up project whose plan
has defects planted in it, then score its summary against an answer key. The results so far are in the skill's
README, under [Test results](../README.md#test-results).

## Table of contents

- [What is here](#what-is-here)
- [How a run works](#how-a-run-works)
- [Run one](#run-one)
- [The answer keys: cases.json](#the-answer-keys-casesjson)
- [How a summary is scored](#how-a-summary-is-scored)
- [The tools' own tests](#the-tools-own-tests)
- [Add a case](#add-a-case)
- [Errors and what you see](#errors-and-what-you-see)
- [Cost](#cost)
- [Limits](#limits)

## What is here

| File | What it does |
| --- | --- |
| [run.py](run.py) | Runs one case end to end in a fresh, headless Claude Code session, then scores it. Costs money. |
| [score.py](score.py) | Scores a summary file against a case's answer key. Free, no network. |
| [cases.json](cases.json) | The answer keys: each case's target, arguments, expected gate and planted defects. |
| [test_score.py](test_score.py) | 22 tests of the scorer. |
| [test_run.py](test_run.py) | 7 tests of the runner's setup and command line, which need only git. |
| `.gitignore` | Keeps Python's `__pycache__/` out of git. |

The made-up projects themselves live in [../examples/](../examples/README.md), one folder per case, each with a
`repo/` (the project as the run sees it) and a README describing the recorded run. A new run writes its output to
the case's `output/` folder, which git ignores.

## How a run works

```
 python3 -I run.py <case>
        │
        ▼
 1 PREPARE   copy examples/<case>/repo ──▶ a new temporary folder
             git init + one commit, with fixed dates and no global or system git config
             (round-2 cases: add round 1's summary and run folder, commit, lay the owner's
             answers on top, commit)
             exclude .crossfire/ from git
        │
        ▼
 2 STAGE     a minimal plugin in a second temporary folder, outside that repo:
               .claude-plugin/plugin.json   {"name": "crossfire"}
               skills/crossfire/            SKILL.md and references/
               agents/                      crossfire-reviewer.md and crossfire-verifier.md
             (never README, PLAYBOOK, examples or evals: they describe the planted defects)
        │
        ▼
 3 RUN       claude -p "/crossfire <target> <args>"
               --plugin-dir <staged plugin>   the skill loads as a plugin, from the folder above
               --setting-sources project      none of your instructions, hooks or installed plugins
               --strict-mcp-config            and none of your own MCP servers
               --model opus                   the main session's model, pinned (change with --model)
               --max-budget-usd 25            a spend cap (change with --max-budget-usd)
               --permission-mode acceptEdits  file edits inside the folder only
               --allowedTools Read Grep Glob Agent WebSearch WebFetch Bash(<read commands>)
             time limit 40 min (--timeout-min); on timeout or Ctrl-C, TERM then KILL the whole
             process group
        │
        ▼
 4 COLLECT   copy to examples/<case>/output (or --out DIR):
               summary.crossfire.md   only if the run wrote a new one
               run/                   the run folder: frame, drafts, cross, verify, chair…
               metrics.json           time, cost, turns and models, from the session's own report
               score.json             score.py's result, or why it could not score
             both temporary folders (the case repo and the staged plugin, `crossfire-plugin-*`) are
             kept and their paths printed; the runner deletes neither, so remove them yourself
             when you are done
```

The Bash allowlist is a prefix list, not a sandbox: named git subcommands (`log`, `show`, `diff`, `status`,
`rev-parse`, `ls-files`, `check-ignore`), `ls`, `wc`, `grep`, `cat` and `head`. A git flag such as `--output` could
still write outside the folder, and the read commands can read anything your user can. Anything else is denied, and
reviewers fall back to Read, Grep and Glob.

The run is hermetic: the answer keys are neither staged nor loaded by the session. That does not make them
unreadable: the checkout stays readable by the agents' read tools, as the skill's README says.

## Run one

```bash
cd <the skill folder>/evals
python3 -I run.py password-reset --out /tmp/password-reset-rerun
```

It refuses to overwrite an existing output folder, so pass `--out` when the case already has a recorded one. It
prints a JSON summary at the end: the output folder, both temporary folders, the exit code, whether it timed out,
whether a new summary was written, the time and the cost. It exits 0 only when the session finished and wrote a new
summary.

A second-round case (`help-page-copy-round2`) needs a first-round output in `examples/help-page-copy/output/`, so
run `help-page-copy` first; its own default output folder is `output-round2/`.

## The answer keys: cases.json

```
"password-reset": {
  "target": "docs/plans/password-reset.md",        the path /crossfire is given, in the case's repo
  "args": "",                                      anything after the target: a depth, "whether",
                                                   "+lens"
  "summary": "docs/plans/password-reset.crossfire.md", where the run writes its summary
  "expect_gate": ["REVISE", "STOP"],                 the gates that count as right
  "max_blockers": null,                              a ceiling on blocking rows; 0 for a clean case
  "defects": [
    {
      "id": "token-in-access-log",
      "must_block": true,                            the row must say Blocks = yes to count
      "all_of": [["access log", "logged", "logging", "logs", "log line", "log store"],
                 ["token", "query string", "originalurl", "url"]]
    }
  ]
}
```

A second-round case adds `"round_of": "<base case>"` and `"overlay": "<folder in the base case>"`; its repo is the
base case's repo plus that folder.

| Case | Target | What it tests |
| --- | --- | --- |
| `password-reset` | a reset-password plan with five planted security and data defects | that a deep run finds and blocks on each |
| `help-page-copy` | a two-line copy and config change, missing facts the plan relies on | that a quick run stops and asks rather than guesses (see the note below) |
| `help-page-copy-round2` | the same change with the owner's answers added | that round 2 passes, with nothing blocking |
| `report-scheduling` | a whether-decision among three options, with two planted traps | that whether-mode surfaces both and recommends an option |

Two notes on these keys:
- `help-page-copy` expects STOP in round 1 and PASS in round 2, because the example lacks facts the plan relies
  on. The key was first written to expect PASS in one round and was set to its current value after round 1's
  result was seen, so its "expected gate" is not a prediction.
- `report-scheduling` accepts REVISE, STOP or PASS, so its gate check says nothing; the case is about the two
  defects being surfaced.

## How a summary is scored

[score.py](score.py) reads the summary's `## Verdict` and `## Conditions` sections:

1. **The gate** is the `**Gate: …**` line in the Verdict section.
2. **The table** is the first Markdown table in the Conditions section. It must have a separator row under the
   header, and columns named `ID`, `Sev`, `Blocks` and `Finding`. Reading stops at the first line that is not a table
   row, so a second table is ignored. An escaped `\|` stays inside its cell.
3. **A defect is caught** when one row matches it: for every group in `all_of`, at least one phrase appears in that
   row's Finding or Protects cell, case-insensitively, at the start of a word ("url" matches "URLs", not "curl").
   A `must_block` defect also needs that row's Blocks cell to start with "yes".

It prints:

| Field | Meaning |
| --- | --- |
| `gate`, `gate_expected` | the gate, and whether it is in `expect_gate` |
| `caught`, `missed` | planted defect ids |
| `blocking_rows` | rows whose Blocks cell is "yes" |
| `over_max_blockers` | more blocking rows than `max_blockers` allows |
| `blocking_rows_not_planted` | blocking rows that match no planted defect: read them, as some are real problems |
| `rows`, `words_above_table` | the table's size, and the length of the prose above it |

Exit codes: 0 after printing a score, whatever it is (this measures, it does not gate); 2 when it cannot score.

## The tools' own tests

```bash
python3 -I test_score.py     # 22 tests
python3 -I test_run.py       # 7 tests
```

`test_score.py` covers parsing (a missing gate, section, table, separator or column; a second table; escaped
pipes; Windows line endings), matching (word starts, the matched columns, every group, `must_block`), the counts,
and every exit code.

`test_run.py` runs the setup step for real, with git only, and builds the session's command line without running
it. It checks:
- the staged plugin has the manifest, `SKILL.md`, `references/` and the two agent files, and nothing else: no
  README, playbook, examples or evals;
- no staged file mentions any case's target, defect ids or answer keys;
- the staged plugin and the case's repo are separate folders, and the repo holds no `.claude/`;
- the command line loads the staged plugin with `--plugin-dir`, with project-only settings and `--strict-mcp-config`;
- the run folder is ignored by git;
- the same files give the same commit;
- a second round seeds a first round's summary and the owner's answers (from a stand-in first round, so the test
  needs no paid run).

All 22 `test_score.py` tests and all 7 `test_run.py` tests pass (29 in all; run on 2026-11-24). The deliberate breaks
made to `score.py` and `run.py`, and when each was run, are listed in the skill's README, under
[Tests of the eval tools](../README.md#tests-of-the-eval-tools).

<details>
<summary>Earlier test run</summary>

On 2026-11-20, 26 tests passed, before the runner staged a plugin.

</details>

## Add a case

1. Make `../examples/<case>/repo/`: a small made-up project with an `AGENTS.md` of house rules, the plan or
   question, and the few source files the plan's defects depend on. Defects in code the reviewers can open and cite
   test the evidence rules; defects only in the plan's prose do not.
2. Add the case to `cases.json`. Pick phrases a reviewer would actually use, several per group, and run the scorer
   against a hand-written row to check they match only what they should.
3. Run `python3 -I test_run.py`: it fails if any file of the staged plugin mentions the new case's target or
   defect ids.
4. Run `python3 -I run.py <case>`, read the summary and the run folder, and write the example's README: the
   project, what was planted, what the run found and cost, and what it taught. Add a row to
   `../examples/README.md`.

Keep the cases made up. Nothing from a real project goes in an example.

## Errors and what you see

| Situation | What happens |
| --- | --- |
| Unknown case id | `run.py` prints the known ids and exits 1; `score.py` says the case is missing and exits 2 |
| The output folder already exists | `run.py` refuses before spending anything, and says to move it or pass `--out` |
| A second round with no first-round output yet | `run.py` refuses before spending anything |
| `claude` is not on `PATH` | `run.py` refuses before spending anything |
| The session times out | the process group is stopped, whatever it wrote is collected, and `run.py` exits 1 |
| The session hits the spend cap or errors | `metrics.json` records the exit code and the session's error flag; `run.py` exits 1 if the session's exit code was not 0, it timed out, or it wrote no new summary |
| The run wrote no new summary | `score.json` says so, and `run.py` exits 1 |
| The summary has no gate line, Conditions section, separator row or required column | `score.py` exits 2, naming what is missing |
| The summary is not UTF-8, or `cases.json` is malformed | `score.py` exits 2 |

## Cost

Each `run.py` call is a paid session. The recorded runs cost $3.09 to $16.55, at list price, as each session
reported; the deep case is the most expensive. `score.py` and the tests cost nothing.

## Limits

- Phrase matching is crude. It misses a defect described in words the key does not list, and can credit a row that
  uses the phrases while saying something else. Read the rows when a number surprises you.
- One run per case is a sample, not an average. Model output varies between runs.
- The recorded runs were made before the hermetic runner and the review fixes; see the skill README's
  [Not yet measured](../README.md#not-yet-measured).
