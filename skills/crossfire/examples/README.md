# crossfire examples

Four examples of `/crossfire`, five real runs in all (the help page has two rounds). Each is explained in its own
README: what the project was, what was asked, what the panel found, how it scored, what it cost, and what it taught
us. Three are made-up projects with defects planted on purpose, which double as the [eval](../evals/README.md)
cases. The fourth is crossfire reviewing its own README.

## Table of contents

- [The examples](#the-examples)
- [Versions](#versions)
- [What these runs changed in the skill](#what-these-runs-changed-in-the-skill)
- [What is kept here](#what-is-kept-here)

## The examples

| Example | What it shows | Depth | Gate | Planted defects | Agent calls | Time | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Password reset](password-reset/README.md) | a deep review finding security and data defects | deep (picked) | STOP | 4 of 5 blocked; the 5th found but advisory | 31 | 32.6 min | $16.55 |
| [Report scheduling](report-scheduling/README.md) | a whether-decision among three options | standard (picked) | STOP | 2 of 2 | 14 | 20.1 min | $8.18 |
| [Help page copy](help-page-copy/README.md), round 1 | stopping on missing facts instead of guessing | quick (picked) | STOP | none planted | 9 | 9.5 min | $3.93 |
| [Help page copy](help-page-copy/README.md), round 2 | a second round passing once the owner answers | quick | PASS | none planted | 4 | 8.0 min | $3.09 |
| [Self-review](self-review/README.md) | crossfire holding its own README to its claims | standard | REVISE | not an eval case | 11 | 28.6 min | $11.42 |

All runs were made on 2026-11-12, in fresh headless sessions. Costs are the list price each session reported, not a
bill. Each run is one sample, not an average.

## Versions

Each example README names the version of the skill that made its run, and links here:
- **First version** (password reset, report scheduling, help page round 1): writes one file per reply, has no merge
  step and no verifier cap.
- **Second version** (help page round 2, the self-review): merges duplicates before verification, caps verifiers by
  depth, and writes one file per stage.
- **Current version:** the second, plus the fixes from the skill's own reviews. It writes nothing to disk until the
  run ends; a `From` column traces each condition to its findings; the chair's table is reconciled with the
  verdicts; and rounds diff against a saved copy of the target. No run has used it end to end yet.

## What these runs changed in the skill

What each problem the runs exposed means for the skill today:

| Run showed | The skill now |
| --- | --- |
| Help page: four findings named the same missing renderer, and five Opus verifiers ran on a two-line change | merges findings that share a root cause before verification and verifies each once |
| Password reset: 16 Opus verifiers for 47 findings; most of the $16.55 was Opus | caps verifiers at 2, 4 or 8 by depth, batching related findings and never dropping any |
| Password reset: 149 orchestrator turns, with one file written per reply and per finding | writes one file per stage, all at the end of the run |
| Help page and report: the chair wrote conditional text in cells a script reads | fixes each cell of the chair's table to one value in the chair's brief |
| Password reset: plaintext token storage verified at minor | names stored credentials readable from a database, replica or backup as blocking-grade in the security lens (not yet re-run) |
| Help page: the final step listed running processes, which was not permitted and checked nothing | confirms every agent returned, and lists no processes |
| Self-review: four blockers in the README's own claims | corrected each claim in the README; see [the self-review](self-review/README.md) |

## What is kept here

Each example folder holds its README and, for the eval cases, the made-up project the run reviewed (`repo/`, and
`round2/` for the help page's second round). Those projects are the evals' inputs: [run.py](../evals/run.py) copies
them into a fresh repository for each run.

The raw files each run wrote (every draft, cross-examination, verification and summary) are not kept, to keep this
folder readable, and they are not published. Each example's README records what its run found. A new run
writes its own under `<example>/output/`, which git ignores.
