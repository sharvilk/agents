# Example: crossfire reviewing its own README

crossfire run on this skill's own [README](../../README.md), as it stood midway through writing it, to see whether
the panel would catch problems in the skill's own documentation. It is not an eval case: there is no answer key.

## Table of contents

- [The run](#the-run)
- [What crossfire returned](#what-crossfire-returned)
- [How each condition was fixed](#how-each-condition-was-fixed)
- [What we learned](#what-we-learned)

## The run

`/crossfire README.md`, on 2026-11-12, with the second version of the skill. It ran in a temporary copy of the
repository the skill was written in, so the panel had that repository's own rules for writing a skill to hold the
README to.

```
 depth: STANDARD
 seats: advocate (sonnet) · pre-mortem (opus) · architecture, testing, security (sonnet)
 agent calls: 11 = 5 drafts + 1 cross-examination + 4 verifiers + 1 chair
               (9 merged groups batched into 4 verifiers: the cost controls added after the first runs)
 time 28.6 min · cost $11.42 (list price, as the session reported) · 95% of it on Opus
```

Every reviewer and verifier had Bash denied by the headless run's permission rules, and worked from Read, Grep and
Glob instead.

## What crossfire returned

**Gate: REVISE**, with four verified blockers. All four were about how the README backed its own claims:

| ID | Severity | Blocks | Finding |
| --- | --- | --- | --- |
| C1 | major | yes | the false-alarm example had never reached PASS, yet the README called it the control |
| C2 | major | yes | rounds had never run, and nothing said how a re-run of a PR or a question finds its last round |
| C3 | major | yes | the examples had used more verifiers than the depth table allows |
| C4 | major | yes | the Cost and time section was an empty placeholder |

Nine minor findings and nits came with them. Among them:
- the eval runner allowed any git command, though the README said read-only;
- STOP outranks REVISE, but the playbook's STOP advice did not say to fix verified blockers too;
- no fallback when a model alias is unavailable;
- no mention of prompt-injection risk;
- a compiled Python cache file in the tree.

**What the panel changed.** The orchestrator's first view expected REVISE on two things: the empty cost section and
the example file layout. The panel confirmed the first, downgraded the second to minor, and found three blockers the
first view had not expected (C1 to C3).

## How each condition was fixed

| Condition | Fix |
| --- | --- |
| C1 | round 2 of the help-page example was run, and passed; the docs now describe it as two rounds |
| C2 | round 2 ran; the procedure now says where the last round is for each kind of target |
| C3 | the docs say which runs used the first version, which had no verifier cap |
| C4 | the README now has the measured cost of every run, in its Test results |
| minors | named git subcommands only; the playbook's STOP row; a model-alias fallback; prompt injection in Limits; the cache ignored |

## What we learned

- **It holds its own docs to their claims.** Every blocker was a place where the README said more than the evidence
  showed.
- **The cost controls worked.** Merging and the verifier cap kept a standard run to 11 agent calls.
