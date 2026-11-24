# The gate and the summary

After the chair returns, the orchestrator applies this rule itself. The chair recommends; the rule decides. A
model never declares its own run passed.

## Table of contents

- [The rule](#the-rule)
- [Holding back overreach](#holding-back-overreach)
- [The summary file](#the-summary-file)
- [Rounds](#rounds)

## The rule

Read the lines in order. The first one that matches is the outcome.

```
1 INCOMPLETE  a reviewer, cross-examiner or verifier failed twice, or a reply stayed malformed
              after one re-ask
              → list what did not run, and the verified blockers found so far; never a pass
2 ESCALATE    a verified blocker is still open at round 3, or the last round's fix caused
              two or more new verified blockers, or a blocker marked fixed came back
              → the owner chooses: revise, clarify the requirement, narrow the scope,
                defer or cancel; escalation never approves
3 STOP        a blocking-grade finding came back NEEDS DATA from its verifier (or its evidence
              is "needs data:"), or, in whether-mode, the recommendation turns on a choice the
              frame records as the owner's
              → ask the 3 questions that matter most and list any others after them; "keep
                going" answers none of them. Verified blockers are listed too, and are fixed
                before the next round
4 PASS        no verified blocker
              → the remaining conditions stay listed as should-fix or follow-up
5 REVISE      otherwise
              → fix the verified blockers, then run crossfire again for round N+1
```

A blocking-grade finding is critical or major and names what it protects. A verified blocker is one of those that a
verifier reproduced. See [contract.md](contract.md#what-blocks).

Narrowing the scope is the owner's choice alone. In how-mode the panel reviews how to build what was asked; it never
answers a blocker by cutting an ask.

## Holding back overreach

The chair moves a condition to `follow-up`, with the reason in its row, when it:

- tests states the real system cannot produce;
- adds an abstraction, a layer or a framework only so that a test can exist;
- hardens against a threat the plan's stated environment does not have, with no credible normal-use scenario;
- would cost more to check than the feature costs to build, for a risk that normal use does not reach.

Signs the run itself is overreaching, which the summary reports when they appear:

- a second round raised new blockers that name no new user-visible risk;
- the conditions outgrew the plan: more conditions than the plan has steps.

## The summary file

Written by the orchestrator, beside the target: `<target-name>.crossfire.md` (a plan `docs/plan.md` gets
`docs/plan.crossfire.md`). A PR or a question has no file to sit beside, so its summary goes in the run folder as
`summary.md`. The orchestrator never commits it; the owner decides.

```markdown
# crossfire: <title of the target>

<target path>@<short sha> · round <N> · <depth> · <how | whether> · <YYYY-MM-DD>

## Verdict

**Gate: <INCOMPLETE | STOP | PASS | ESCALATE | REVISE>.** <one sentence: why, naming the condition ids>

<the chair's recommendation, two or three sentences; in whether-mode, the option it recommends and why>

## Conditions

| ID | Sev | Blocks | Finding | Protects | Check | Status | From |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | major | yes | <claim> (<evidence location>) | <id and quote> | <the check> | open | F3, F7 |
| C2 | minor | no | <claim> | <...> | <...> | follow-up: <reason> | F5 |

## Questions only you can answer

1. <question> (needed for C3)

## Disputes the evidence could not settle

- <finding>: <side A, with evidence> versus <side B, with evidence>.

## Not checked

- <lens or area>: <why>.

## What the panel changed

Before the panel: <the sealed first view, one line>. After: <what changed, or "nothing: the panel confirmed it">.

## Run

Reviewers: <lens or stance → model, one per line or comma-separated>. Cross-examination: <who>. Verified <n>,
refuted <n>, not verifiable <n>. Agent calls: <n>. Corrections made when reconciling the table: <none, or what>.
Raw files: `<run folder>`.
```

Status values: `open`, `fixed in round N`, `follow-up: <reason>`, `won't do: <owner's reason>`, `question`.

Keep the summary to one screen above the Conditions table. The detail lives in the run folder.

## Rounds

Round N+1 starts from the summary file:

1. Find the last round: for a file, the summary beside it; for a PR or a question, the newest folder under
   `.crossfire/<target-slug>/`.
2. Diff the target against the last round's `target.md` with `git diff --no-index`. A PR is diffed against its
   last round's head SHA. If the last round has no `target.md`, diff against the commit its summary pins. If that
   commit is gone (rebased or squashed), say so and treat every section as changed.
3. Reuse the frame. Re-seat the same lenses and stances, as fresh agents, never the earlier ones.
4. Each reviewer gets the round block: the open conditions with their ids and checks, the changed sections, and the
   won't-do list. For each open condition in its seat it reports `Cn: met` or `Cn: not met`, with evidence, and it
   reports new findings only for risks the change introduced, or blocking-grade risks the last round missed.
5. Verify every blocker a reviewer says is now met, inside the depth's verifier cap; a blocker is marked
   `fixed in round N` only when its verifier agrees, and unsure means not met. A blocker verified in an earlier
   round stays a verified blocker, in the reconcile and the gate, until then. Labels carry the round
   (`r2-F3`), so `From` cells from different rounds never collide.
6. The chair gets the previous Conditions table and keeps every row, updating statuses. Then decide and gate as
   before.

A condition the owner marked `won't do: <reason>` in the summary is closed. It does not count as an open blocker,
reviewers are told not to raise it again, and its row keeps the owner's reason. It reopens only if the change made
it worse, and the finding must show how.

A third round with a verified blocker still open is an escalation, not a fourth round. Re-running an INCOMPLETE
round keeps its number and runs only the parts that failed; it does not count towards the three.
