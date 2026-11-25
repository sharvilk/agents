# Example: help page copy, in two rounds

A quick review of a two-line change. Round 1 stopped because the example lacked facts the plan relied on. Round 2
added the answers and passed. It is the eval cases `help-page-copy` and `help-page-copy-round2`; how the evals work
is in [../../evals/README.md](../../evals/README.md).

## Table of contents

- [The project](#the-project)
- [The plan](#the-plan)
- [Round 1](#round-1)
- [Round 2](#round-2)
- [Scored against the answer key](#scored-against-the-answer-key)
- [What we learned](#what-we-learned)

## The project

[repo/](repo/) is the same made-up notes app:

| File | Why it is there |
| --- | --- |
| [AGENTS.md](repo/AGENTS.md) | the house rules: help copy describes only what the code does; colours live in config |
| [docs/plans/help-copy.md](repo/docs/plans/help-copy.md) | the plan under review |
| [src/export/formats.js](repo/src/export/formats.js) | the export menu offers Markdown and PDF |
| [src/help/exporting.md](repo/src/help/exporting.md) | the help text, which mentions only Markdown |
| [config/defaults.json](repo/config/defaults.json) | the help banner's colour, "blue" |

## The plan

Two changes. The help text gains "or as a PDF", and the help banner's colour changes from blue to teal, "as the rest
of the help pages already do". Nothing was planted: this was meant as the clean control that should pass.

## Round 1

`/crossfire docs/plans/help-copy.md`, on 2026-11-12, with the [first version](../README.md#versions) of the skill.

```
 depth: QUICK (one sentence of copy and one config value; no code, no data)
 seats: pre-mortem (opus) · product (sonnet) · testing (sonnet)
 agent calls: 9 = 3 drafts + 5 verifiers + 1 chair      (no cross-examination at quick depth)
 time 9.5 min · cost $3.93 (list price, as the session reported)
```

**Gate: STOP.** The example was incomplete. Nothing in it read the banner setting, defined a brand teal, or showed
the "rest of the help pages". So the panel could not tell whether the colour change would work at all. It said to
build the copy change as written and hold the colour change.

| ID | Severity | Blocks | Finding | Status |
| --- | --- | --- | --- | --- |
| C1 | major | no | no file reads `helpBannerColor`, and nothing defines the brand teal | question |
| C2 | minor | no | "Done when" has no way to check either change; banner text contrast is undefined | open |
| C3 | minor | no | no test ties the help text to the export formats | follow-up |

The two questions it asked: what reads `helpBannerColor`, and does it accept "teal"? And what value do the other help
pages use for the brand teal?

The orchestrator's first view had predicted PASS with a should-fix. All three reviewers raised the missing
renderer, in four findings between them; four verifiers could not settle it from the repo and returned it as a
question, so the gate became STOP.

## Round 2

The owner answered in the plan. [round2/](round2/) holds exactly what was added:
- [banner.js](round2/src/help/banner.js), which reads the setting and maps it through the palette;
- [palette.json](round2/src/styles/palette.json), whose `teal` is `#0f766e` with white text;
- [help-pages.json](round2/config/help-pages.json), which shows the account and billing pages already teal;
- an "Answers to the review's questions" section in [the plan](round2/docs/plans/help-copy.md).

Then `/crossfire docs/plans/help-copy.md` ran again, with the [second version](../README.md#versions) of the skill.

```
 round 2, quick, same seats as fresh agents
 agent calls: 4 = 3 drafts + 1 chair      (nothing blocking-grade, so no verifier was needed)
 time 8.0 min · cost $3.09 (list price, as the session reported)
```

**Gate: PASS.**

| ID | Severity | Blocks | Finding | Status |
| --- | --- | --- | --- | --- |
| C1 | major | no | round 1's question, settled by `banner.js:7`, `palette.json:3` and `help-pages.json` | fixed in round 2 |
| C2 | minor | no | "Done when" still lacks runnable checks; contrast works out to about 5.47:1 by hand | open |
| C3 | minor | no | no test ties the help text to the export formats | follow-up |
| C4 | nit | no | the banner's own text does not mention PDF | question |

Round 1's commit did not exist in round 2's fresh copy, so the run said so and reviewed every section as changed. That
is the fallback the rounds procedure describes.

## Scored against the answer key

Round 1: STOP, no blocking rows. Round 2: PASS, no blocking rows. The key expects STOP in round 1 and PASS in
round 2, because round 1's stop was right. It was first written to expect PASS in one round and was set to its
current value after round 1's result was seen, so it is not a prediction.

## What we learned

- **It stops rather than guessing.** The plan's claim that other pages were already teal had nothing behind it, and
  the panel said so instead of assuming.
- **Rounds work end to end** ([second version](../README.md#versions)). The owner answered in the plan, the next
  round marked the condition fixed, and the gate passed.
- **Duplicate findings needed merging.** Four findings named the same missing renderer, and five Opus verifiers ran
  on a two-line change. The skill now merges duplicates before verifying, and caps verifiers at 2 at quick depth.
- **The chair's cells needed fixed values.** It wrote "major (minor if only the shade is off)" in one cell. The
  chair's brief now allows one value per cell.
