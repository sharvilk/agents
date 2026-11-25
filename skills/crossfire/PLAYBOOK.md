# crossfire playbook

How to use `/crossfire` day to day: when to reach for it, how to prepare a target, how to run it, how to read what it
gives back, and what to do with each outcome. How it works inside is in the [README](README.md); real runs are in
[examples](examples/README.md).

## Table of contents

- [When to use it](#when-to-use-it)
- [Before you run: make the target reviewable](#before-you-run-make-the-target-reviewable)
- [Run it](#run-it)
- [Read the result](#read-the-result)
- [Act on the gate](#act-on-the-gate)
- [Run the next round](#run-the-next-round)
- [When you disagree with a finding](#when-you-disagree-with-a-finding)
- [Keep it cheap](#keep-it-cheap)
- [Troubleshooting](#troubleshooting)
- [Worked examples](#worked-examples)

## When to use it

Use it **before building**, when a mistake found later is expensive:

- a plan or design doc for a feature, a migration, a new job or service, an auth or payments change;
- a pull request whose design you want challenged, not its formatting;
- an open decision: "should we move X to Y?", "which of these three approaches?" (whether-mode).

Skip it for:

- a line-by-line code review of a diff: use a code-review tool, which is built for that;
- a typo fix or a one-line change: the cheapest depth still starts several agents;
- a question with a known answer: ask it directly;
- a plan with no asks and no done items yet: write those first (next section), or the panel reviews its own guesses.

## Before you run: make the target reviewable

The panel can only protect what the target states. Five minutes here saves a round. A plan reviews best with:

```markdown
## Asks
- A1. <what the user or owner asked for, in their words>
- A2. ...

## Done when
- D1. <an observable result someone can check>
- D2. ...

## Design
<what will be built, where it lives, what it changes>

## Not in this change
- <what is deliberately left out, and why>
```

- **Asks** are what blocking findings protect. A finding that protects nothing cannot block.
- **Done items** become the checks in the conditions list.
- **"Not in this change"** stops reviewers from blocking on things you already decided to leave out. It does not
  stop them from saying that leaving something out breaks an ask.
- For a whether-question, list the options, including "keep things as they are", and what matters for the
  choice.

Commit the target first if you can, so the run pins a commit and the next round can diff against it. An uncommitted
target is reviewed as it is on disk, and the summary says so.

## Run it

| You want | Type |
| --- | --- |
| Review a plan, depth picked for you | `/crossfire docs/plans/password-reset.md` |
| Force a depth | `/crossfire docs/plans/password-reset.md deep` |
| Add a lens the picker left out | `/crossfire docs/plans/export.md +privacy` |
| Review a pull request's design | `/crossfire 1234` or `/crossfire https://github.com/owner/repo/pull/1234` |
| Decide whether to do something | `/crossfire docs/questions/report-scheduling.md whether` |
| Ask a question with no file | `/crossfire "should the nightly report move from cron to the job queue?"` |

Run it from a session inside the repository the target belongs to, so reviewers can open its files.

Once it has read the target, the orchestrator tells you, in up to four lines, the depth, the seats and why, and
its own first view. Then the panel runs. In the recorded examples, quick runs took 8–10 minutes, standard runs
20–29 and the deep run 33; the [examples](examples/README.md) have the times and costs.

## Read the result

The orchestrator ends with up to 12 lines: the gate, the recommendation, the blocking conditions, the questions, and
the summary's path. The summary file has these sections, in this order:

1. **Verdict.** The gate line, in bold, names the conditions behind it. Then two or three sentences of
   recommendation. Read this first; it is written for a busy reader.
2. **Conditions.** One row per condition:

   | Column | What it tells you |
   | --- | --- |
   | Sev | critical, major, minor or nit |
   | Blocks | `yes` only if it is critical or major, protects something, and a verifier reproduced it |
   | Finding | the claim and where the evidence is |
   | Protects | the ask, done item, repo rule or user scenario it defends |
   | Check | how you, or the next round, will know it is met |
   | Status | open, fixed in round N, follow-up (with a reason), won't do (with your reason), question |
   | From | the finding labels it came from, to look up in the run folder's `drafts.md` and `verify.md` |

3. **Questions only you can answer.** Facts or choices the panel could not settle from the repo. These hold the run
   at STOP.
4. **Disputes the evidence could not settle.** Both sides, each with its evidence. You decide.
5. **Not checked.** Lenses not seated and why, and anything a reviewer could not reach. This is how you know what
   the PASS did not cover.
6. **What the panel changed.** The orchestrator's first view, told to you before any reviewer started, against
   the outcome. "Nothing" here means the panel confirmed what was already thought, and on a small change that is a
   sign to run it at a lower depth next time.
7. **Run.** Who sat where on which model, how many findings were verified or refuted, the agent count, and the
   path to the raw files.

The raw files (`.crossfire/…`) hold every draft, cross-examination, verification and the chair's reply. Open them
when a condition surprises you, or to see what a verifier refuted.

## Act on the gate

| Gate | What it means | What you do |
| --- | --- | --- |
| **INCOMPLETE** | A reviewer, cross-examiner or verifier did not run | Read which part failed and run again. It is never a pass |
| **ESCALATE** | Round 3 with a blocker open, a fix that caused new blockers, or a blocker that came back | Choose: revise differently, clarify the requirement, narrow the scope, defer, or cancel. Escalation never approves on its own |
| **STOP** | A blocking-grade finding needs a fact or decision only you have | Answer the questions: add the facts to the plan, or state your decision there. STOP outranks REVISE, so also fix every condition with Blocks = `yes`. Then run again. "Keep going" is not an answer; the run will ask again |
| **PASS** | Nothing verified blocks | Build. Treat the should-fix conditions as part of the work, and file the follow-ups where you keep follow-ups |
| **REVISE** | At least one verified blocker | Change the plan to meet each blocking condition's check, commit, and run `/crossfire` again on the same target |

## Run the next round

After changing the target for REVISE or STOP:

1. Commit the change if you can, so the run pins a commit. An uncommitted target is reviewed as it is on disk.
2. Run `/crossfire <same target>` with no other arguments. The summary beside the target tells the orchestrator
   which round this is.
3. The new round checks the open conditions and the changed sections. It does not review the whole target again.

Each condition keeps its row: `fixed in round 2` stays visible, so the record shows what the review caught. A third
round with a blocker still open escalates rather than going round again.

## When you disagree with a finding

- **The evidence is wrong.** Add the correcting fact to the target, for example "the users table has an index on
  email (`schema.sql:4`)", and re-run. The next round's verifier sees it.
- **The finding is right but you accept the risk.** Set its Status to `won't do: <your reason>` in the summary and
  re-run. The round respects a recorded decision, and the record shows who decided and why.
- **The finding overreaches.** Say so in the target's "Not in this change" with the reason. The chair moves
  overreaching conditions to follow-ups and gives the reason in the row.
- **You want a second look at a refuted finding.** Open the run folder's `verify.md`. Verifiers default to
  refuted when unsure, so a real problem can be dropped. Run again with `+<lens>` to put a fresh lens on it.

## Keep it cheap

- Let the depth picker choose. Force `deep` only for auth, money, data deletion or migration, personal data, public
  contracts and production infrastructure.
- Fix the target before re-running, not during. Each round re-seats the panel.
- Write the asks and done items. A vague target makes every reviewer guess, and guesses come back as findings to
  verify.
- Do not re-run to "see if it passes this time". The verifier, not luck, decides what blocks.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `/crossfire` does nothing, or is unknown | The skill is not installed where Claude Code looks | Install the plugin, or copy the folder to `~/.claude/skills/crossfire/` and its two agent files to `~/.claude/agents/` ([Install](README.md#install)); then start a new session |
| The Run line says the read-only limit was in the prompt only | The agent definitions are not in `~/.claude/agents/` | Copy `crossfire-reviewer.md` and `crossfire-verifier.md` from the skill's agents folder there, and start a new session |
| It stops at once with one line | The target is missing or unreadable | Check the path from the repo root, or the PR number and `gh auth status` |
| Every run is STOP | The plan lacks facts reviewers need (sizes, traffic, who uses it) | Put the facts in the plan. That is the run working, not failing |
| Many minor findings, nothing blocks | The plan holds up, and the reviewers still reported minor points up to their limit of findings | Read the Verdict and the blocking column; skim the rest |
| A run takes much longer than the examples | A large target, deep depth, or many blocking-grade findings to verify | Check the depth line; split a very large plan into parts |
| INCOMPLETE | A reviewer or verifier errored twice, often a provider hiccup | Run again; if one seat keeps failing, its draft file shows why |

## Worked examples

Real runs, each explained in its own README: the project, what was asked, what the panel found and what it cost.

- [Password reset](examples/password-reset/README.md): a deep review, since the plan touches authentication, of a
  plan with five planted security and data defects.
- [Help page copy](examples/help-page-copy/README.md): a quick-depth review of a small change. Round 1 stops on
  two questions the example could not answer; round 2 adds the answers and passes.
- [Report scheduling](examples/report-scheduling/README.md): a whether-mode decision among three options.
- [Self-review](examples/self-review/README.md): crossfire reviewing its own README, at standard depth: REVISE,
  with four verified blockers, each of which was then fixed in the README.
