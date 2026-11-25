# on-loop: keep a session working your roadmap, and review what it decided

A Claude Code skill for the hours you are around but busy. You have a roadmap. The on-loop keeps working it, item
after item, in a session that stays open. It decides the small and reversible choices itself, builds on its own
branches, and writes every decision into a log with a diagram, a worked example and the exact undo, so that you
can keep, change or veto each one later. It never merges, publishes, deletes or deploys: your merge is the last
gate on every decision. A message from you never stops it.

It is the sibling of `away-loop`: away-loop for the hours you are gone and only the approved plan, on-loop while
you come and go and the whole roadmap is in scope.

## Table of contents

- [Why it exists, and how it differs from away-loop](#why-it-exists-and-how-it-differs-from-away-loop)
- [How it works](#how-it-works)
  - [Starting it: four gates](#starting-it-four-gates)
  - [What a tick does](#what-a-tick-does)
  - [Where it runs, and the heartbeat](#where-it-runs-and-the-heartbeat)
  - [What it may decide](#what-it-may-decide)
  - [The decision log and the review](#the-decision-log-and-the-review)
  - [How loud it is](#how-loud-it-is)
  - [Limits and when it stops](#limits-and-when-it-stops)
  - [Why there are no caps](#why-there-are-no-caps)
  - [The loop-state marker](#the-loop-state-marker)
  - [Which skill answers which phrase](#which-skill-answers-which-phrase)
  - [Working with the other skills](#working-with-the-other-skills)
- [What it stores, and where](#what-it-stores-and-where)
- [Install](#install)
- [Examples](#examples)
- [Errors and what you see](#errors-and-what-you-see)
- [Limits](#limits)
- [Unverified behaviour](#unverified-behaviour)
- [Names considered](#names-considered)
- [Prior art](#prior-art)
- [Files](#files)

Figures are labelled MEASURED (read from a file, a docs page or a command), DERIVED (worked out from measured
facts) or EXPECTED (a design choice or a prediction: the skill is new, and nothing here describes a run).

## Why it exists, and how it differs from away-loop

A session today has two speeds. With you present it stops at every fork and waits. With `away-loop` it keeps going,
but only on the plan you already approved, only with minor decisions, and only until your first message. Between the
two there is a gap: you are around but busy, the project has a roadmap, and most forks inside a roadmap item are
choices you would rather review afterwards than be asked about one by one. The on-loop fills it.

```
 Figure 1 (DERIVED from away-loop's SKILL.md): where each skill sits

                          WHAT GETS WORKED ON
                 the approved plan only            the roadmap, item after item
               ┌──────────────────────────────┬──────────────────────────────────────┐
  you AWAY     │  away-loop                   │                                      │
  (hours)      │  minor decisions only        │                                      │
               │  stops on your first message │        on-loop                       │
               ├──────────────────────────────┤        decides inside each item,     │
  you AROUND   │  a normal session            │        logs every decision for       │
  (in and out) │  it stops and asks           │        your later review and veto,   │
               │                              │        keeps going when you speak    │
               └──────────────────────────────┴──────────────────────────────────────┘
```

The big shift is when it checks with you:

```
 Figure 2 (DERIVED): the oversight model moves from "ask first" to "review after", inside a hard fence

   ask first (a normal session)   fork ──► STOP, ask you ──► answer ──► build
   review after (the on-loop)     fork ──► decide ──► build on a branch ──► log ──► you review ──► keep / change / veto
   never (both)                   merge · delete · publish · deploy · spend · settings · push to the default branch

   The fence that makes "review after" safe: nothing the loop does leaves a branch it created or an open pull
   request without you. Your merge is the last gate on every decision.
```

| | away-loop (MEASURED, its SKILL.md) | on-loop (EXPECTED) |
| --- | --- | --- |
| When | you are away for hours | any time; you come and go |
| Starts on | "I'm going to sleep", "keep working while I'm away" | an explicit ask to work the roadmap continuously, then a typed yes to a written charter |
| Works on | "the open items", meaning the approved plan | the roadmap, picking the next ready item itself |
| No plan | does not arise | the roadmap gate: it drafts one, asks, and does not start without it |
| Decides | minor design choices, wording, test shape, the order of work, a severity | the same, plus reversible design choices inside a roadmap item (class B) |
| Big decisions | queued | queued, with options and a recommendation ready |
| Decision record | a line in the todo list: time, decision, reason | a ledger in the repo: decision, options, diagram, example, what it touched, how to undo it, review status |
| A message from you | stops the loop ("first message back") | does not stop it; answered first, then the loop carries on |
| Review | one summary on your return | a digest in batches, a verdict per decision, and a defined action for each verdict |
| Length | hours; re-arms itself past the job's expiry | a charter of 7 days; ends unless you renew it |
| Stops on | the first message, or the end time | the limits below, or the words "stop the loop" |
| Stays yours | merges, deletes, production writes, settings, big decisions | the same, plus publishing, spending, default branches and the loop's own limits |

### A separate skill, not a mode of away-loop

Their stop rules are opposites: away-loop stops on your first message, the on-loop must keep going through your
messages. One skill holding both would depend on a "which mode am I in?" flag that could be misremembered after a
compaction, and a wrong read either kills a week-long loop or keeps an overnight one running after "I'm back".
Keeping them separate also means broader authority is always something you switch on deliberately, with its own
charter: away-loop promises "It does not widen what the user approved", and "keep working while I'm away" should
never slide into roadmap-wide authority because the same skill happens to be loaded. Away-loop stays small and
every away tick pays only for the text it uses. A change to one does not reach sessions that loaded the other.

The cost is duplication: the re-arm sequence, the report sections and the traps exist twice. They live in one file,
[references/shared-with-away-loop.md](references/shared-with-away-loop.md), that names away-loop as the origin, so a
change to one is a reminder to change the other; if the two ever drift twice, that earns a check that diffs the
shared blocks. Later, once the on-loop has run a while, away-loop may turn out to be the on-loop with its autonomy
set to `minor` and its stop set to "first message". Folding them is a decision for after real use.

## How it works

The procedure is [SKILL.md](SKILL.md), a core that is kept short because Claude Code keeps only the first 5,000
tokens of an invoked skill through a compaction: it holds the loop-state marker, the never list, the phrases, the
class rule and the tick outline, in that order, and points at one file in [references/](references/) per topic,
each read by the step that needs it. The agent starts it by its description only when you say "start the on-loop",
"work the roadmap continuously" or "always-on mode"; looser phrasing ("keep going") never starts it. It also loads
when a scheduled message starts with "On-loop tick" (the tick prompt tells the agent to invoke the skill); while
its marker is ARMED or PAUSED, for the phrases on the marker's `Answers:` line ("stop the loop", "pause the loop",
"resume the loop", "renew the loop", "review", "status"); and, while a marker in any state (ARMED, PAUSED or ENDED)
has ledger entries pending, for "review" and "keep/veto/change <ids>". After a compaction the agent invokes the skill again.

```
 Figure 3 (EXPECTED): the on-loop, end to end

 START (you ask in the explicit words)
   │
   ├─ gate 1  ROADMAP      none, or not approved ──► draft one from the repo ──► show it ──► WAIT for you
   ├─ gate 2  CHARTER      scope, autonomy, limits, end date ──► show it ──► WAIT for a typed yes in a later message
   ├─ gate 3  SCHEDULING   CronCreate missing or refused ──► say so plainly, offer one bounded run, do not arm
   ├─ gate 4  CLAIM        another on-loop already holds this repo ──► say whose, stop
   ▼
 ARM   CronCreate FIRST ► only on success: write the marker (ARMED, job id) and the state into the todo list, then
       the claim ► tell you what runs, what stays yours, the limits, and the ways to stop it
       (CronCreate failed ► write nothing, or ENDED with the reason ► tell you)

 TICK  (the heartbeat fires while the session is idle, or a background agent or watcher reports)
   0  marker       none, ENDED or PAUSED ──► delete own job, one line, stop · ARMED: CronList confirms the job
   1  stop rules   lifetime · silence · no progress · same failure · parked items ──► WIND DOWN; more than two beats missed ──► say so
   2  renewal      day 5 and 6 of 7 ──► ask in the report; never re-arm past the charter without your word
   3  yield        is a request you typed still in progress? ──► end the tick with no output
   4  health       disk · load · memory · other sessions · your own branches and worktrees
   5  verdicts     apply any keep / change / veto you gave since the last tick
   6  finished     act on agents, CI and review threads that completed; reply to every comment on its own PRs
   7  roadmap      re-read it; changed since the charter? say what, re-plan
   8  pick         next roadmap item that is ready, not waiting on a decision and unclaimed (an unmerged PR does not block)
   9  work         ONE step of ONE item, in the loop's own worktree, by a subagent when it is heavy
  10  decide       each fork ──► class A: decide, log · B: decide, log in full, flag · C: prepare, queue · D: never; record it
  11  done         the check passes and a reviewer that did not build it agrees
  12  report       by posture: one line (you present) · table (nearby) · full report (2 hours, milestone)
  13  speed        work left ──► work beat (15 min) · everything waiting ──► quiet beat (60 min) + a watcher
  14  state        last beat, counters and the claim's last beat refreshed

 A MESSAGE FROM YOU (any time; it does NOT stop the loop)
   "stop the loop" / "pause the loop"            ──► WIND DOWN / pause
   "resume the loop" / "renew the loop"          ──► re-arm (clock kept) / extend the charter 7 days and re-arm
   "review", "what did you decide"               ──► the review digest
   "I'm back", "good morning", "back online"     ──► a short status, and the offer of the review digest
   a verdict ("keep 14, veto 16")                ──► applied as references/review-and-veto.md says:
                                                     a veto shows the cascade, then reverts
   anything else                                 ──► answered first, as in any session

 WIND DOWN   delete every recorded job ► CronList shows none ► marker ENDED (or PAUSED) ► stop own background
             processes by PID ► re-check PRs and CI ► final report + what is waiting for review
             ► carry open items into the normal list ► release the claim ► list the clean-up for you; delete nothing
```

### Starting it: four gates

**No roadmap, no loop.**

```
 Figure 4 (EXPECTED): the roadmap gate

  you name one? ──yes────────────────────────────────────────────────────┐
        │ no                                                             │
  the project has one?  (ROADMAP.md · docs/**/roadmap* · the tracker     │
        │               doc its instructions name · milestones/issues)   │
        ├─ exactly one ──► show what was found: "is this the roadmap?" ──┤
        ├─ several ──────► list them, ask which ─────────────────────────┤
        └─ none ─► DRAFT one from evidence: open issues, the README's    ▼
                   planned section, unreleased changelog, failing or   READY CHECK, per item:
                   skipped tests, TODO markers, the last 30 commits    outcome? a check that proves it? a boundary?
                        │                                                 │
                   show the draft, STOP, wait for edits and a yes   all three ► ready
                        │                                           missing  ► the loop drafts them and queues the
                   save it as a PR you merge                                    item for a yes; it works ready items meanwhile
                        └──────────────────────────────────────────────►  CHARTER names the roadmap and its version
```

Where a roadmap comes from, in order: a path or link you give (always wins); the project's own roadmap or tracker
doc (confirmed with you, because finding a file is not approval to work it); an issue milestone, label or board
(snapshotted at approval: issues opened later and comments by other people are not instructions, and on a public
repo that text is untrusted input); a list you type (written into a doc, shown back). The session's own open todo
items are not a roadmap: they are an approved plan, which the loop finishes first and says so.

When there is none, the loop drafts one, marks every line with its source, puts what it is unsure of under
"Questions", shows it and stops. The yes comes in a later message. The approved roadmap is saved through the
project's normal pull request, which you merge; until then the loop works from the approved text on its branch and
records the commit it read. An item is **ready** when it has an outcome, a check that proves the outcome, and a
boundary; a definition of done agreed before the work is what stops an agent declaring victory early.

**The charter** is shown and needs a typed yes: the roadmap and its commit, the scope, the autonomy setting
(`minor`, `standard` (the default) or `ask-first:<area>`; nothing above `standard`), every limit, the start and the
end (7 days), the branch naming and ledger place, the models, the project's own rules, standing answers, and your
words approving it. The draft charter always shows a **mode** line, "Mode: multi-threaded (builders and one verdict) |
single-threaded (fewer agents, lower usage)", defaulting to the project's rule and otherwise multi-threaded; you pick.
**No charter with limits, no loop.** The loop can never change it; only your quoted words can.

**A permission check** comes at the same gates, while you are present. The todo list and the claim live outside the
project folder, so a read or write there can raise a permission panel, and a tick stuck behind a panel waits until it
is answered (measured: probe (c) in [Unverified behaviour](#unverified-behaviour)). So the loop does one read and one write of the todo list and of the claim file
before arming; if a panel appears it asks you to choose the option that keeps allowing that folder, and names the
folder. **Scheduling** is checked before you walk away. **The claim**: one on-loop per repo, by `on-loop-claim.json` in the repo's
shared git folder, never committed, holding the session id, the charter's end date, the job id, the start time and
the last beat (refreshed every tick). A claim carrying this session's own charter end date (a session resumed after a
checkpoint) is adopted and gets the new session id; any other is reported with whose it is. A claim whose last beat
is over 2 hours old is reported as stale and taking it over needs your word. Every write of the claim reads it first, writes the new content to a temp file beside it and renames that into place, never opening the claim for writing in place (an in-place open empties it if the write fails). Releasing the claim rewrites the file as `released <time>`: a released or expired claim is free, and nothing deletes it. Renew, resume and every re-arm update its charter end date, job id and session id. If the write is refused, the loop says so in one line and continues single-session, with no claim and no claim check. One loop per session: if away-loop is armed, it stops first.

### What a tick does

The numbered steps are in Figure 3. The points that matter:

- **One step of one item per tick.** Ticks start cold, so the tick prompt (starting "On-loop tick") tells the agent
  to read the charter, state, roadmap view and queues from the todo list before it acts.
- **Wake kinds.** A message that starts "On-loop tick" is a tick. A notice from the loop's own agent or watcher is
  tick work and never counts as a message from you, so it cannot defeat the silence limit. Every message you type
  writes `last user message` first.
- **The loop yields.** A tick fires only between your turns, and a tick due while a question panel is open waits
  and runs right after the turn ends (measured: probe (c) in [Unverified behaviour](#unverified-behaviour)); if a request of yours is still running, the tick ends with no
  output.
- **Picking.** Finish what is in flight; then the roadmap's own order, never the loop's taste; skip items that are
  not ready, waiting on a queued decision or an unanswered question, claimed, or touching files you or another session is changing; ties go to the item that
  unblocks the most, then the smallest. An unmerged PR does not block: the next item may stack on it. Every skip is
  written down; an item never disappears.
- **Independent work first.** Each item on its own branch off the default branch with its own PR. When work truly
  needs stacking it stacks, with no limit on depth, and stacked PRs are fine to review.
- **"Done" is the check plus a second opinion.** A reviewer that did not build the item agrees. The builder never
  grades its own work.
- **Branches.** They follow the project's own naming convention plus a `loop` suffix (`feature/export-v2-loop`
  where the project uses `feature/`). The loop works only in worktrees and branches it created, marked by the
  suffix, and never touches the main checkout, another session's work, or another agent's branches and PRs.
- **Drift is held down** by naming the roadmap item on every branch, commit and PR; writing each item's boundary
  before the first commit and comparing the diff at the end of each step; re-reading the roadmap on every tick; no
  drive-by refactor or cleanup (a good idea becomes a proposal); and a fresh session recommended at each renewal.
- **A tick never asks a modal question**, because a question panel stays open until answered and would freeze the
  loop. Ticks queue; questions are asked only in a turn you started.

When the roadmap changes under it (you edited it), it re-reads, says what changed and re-plans. The loop may change
an item's **status** in the roadmap, with evidence, through a pull request on a loop branch; never its text, order or
check. A loop that can rewrite its own goals has no goals.

### Where it runs, and the heartbeat

Any session. The default is **the project's own everyday session**: you arm it in that project's session and go
work on other projects elsewhere; you can drop back in at any time and your message is answered first. Two other
answers were considered and rejected: a **dedicated session only**, where it refuses to arm in a session in which your
own work is in flight (stricter than the goal needs), and **always your working session**, where it runs where you
work and so mostly waits, since ticks fire only while you are idle.

```
 Figure 5 (EXPECTED): the loop works project A on its own while you work on B and C

 ┌ window: project A ───────────────────┐   ┌ window: project B ─────┐   ┌ window: project C ─────┐
 │ your everyday session for A          │   │ you work here          │   │ you work here          │
 │ on-loop armed: a tick every 15 min   │   │ (or B's own on-loop,   │   │                        │
 │ works in its own worktrees, *-loop   │   │  on B's own roadmap)   │   │                        │
 │ you drop in any time: "status",      │   └────────────────────────┘   └────────────────────────┘
 │ "review", or any normal request      │
 └──────────────────────────────────────┘
```

| | A session you mostly leave alone | A session you are actively working in |
| --- | --- | --- |
| Ticks | every 15 min | only while you are idle; while you work they mostly wait |
| The conversation | its status lines and reports | mixed in with your own work (one line per tick while you are present) |
| Context window | filled by the loop's work; it compacts and recovers from its files | shared, so compactions come sooner |
| The repo | its own worktrees and `*-loop` branches | the same, and each tick checks your branches to stay out of your way |

Two limits apply either way: one loop per session and one per repo; and your usage limit is shared by all your
sessions, so several loops use it faster. When Claude Code reports a usage limit, the loop carries on at the next
tick after the reset; it has no gauge for plan usage. (An earlier design went quiet after a limit until told to
continue; it was dropped because it stopped on a second limit within 24 hours. Carrying on at the next tick is Claude
Code's own default.)

**The heartbeat is a recurring `CronCreate` job at two speeds**, woken early by its own background work:

```
 Figure 6 (EXPECTED): one heartbeat, two speeds, plus events

  work beat    7,22,37,52 * * * *   every 15 min (runs 0 to 7.5 min late)   while an item can move
  quiet beat   17 * * * *           every 60 min (runs 0 to 30 min late)    while everything waits on you or CI
  events       a background agent reports · a watcher on PR/CI state exits  ──► the session wakes by itself

  switching speed = the re-arm sequence:
     create the new job ► record its id and time ► delete the old job ► CronList shows exactly one
```

The mechanisms considered (the facts are MEASURED from Claude Code's scheduled-tasks, goal, hooks and agent-view
docs, read on 2026-11-24):

| Mechanism | For an always-on loop | Against |
| --- | --- | --- |
| **Recurring `CronCreate` job** (chosen; away-loop's way) | fires "between your turns, not while Claude is mid-response", so it never cuts into your request; restored on `--resume`; visible in `CronList`; expires, which bounds a forgotten loop | fixed cadence; up to half the gap late; "Tasks only fire while Claude Code is running and idle"; no catch-up for missed fires |
| **Self-paced `/loop`** (`ScheduleWakeup`) | adapts its pace by itself | not restored on resume; it can stop silently when one iteration ends without scheduling the next; `Esc` on an empty prompt cancels it |
| **`/goal`, or a Stop hook** (the Ralph plugin's way) | never waits | never idle, so scheduled tasks never fire and usage burns; the `/goal` evaluator cannot read files, so it cannot judge a roadmap; a Stop hook is a settings change, and Claude Code overrides it after eight blocks in a row ([hooks](https://code.claude.com/docs/en/hooks.md)) |
| **A background session** (`/bg`) | not an engine but a place to run one: it survives a closed terminal, and plain `CronCreate` jobs keep firing on time there (probed) | shutting down still stops it |
| **Cloud or Desktop scheduled tasks** | durable, outside any session | a fresh clone each run, 1-hour minimum, so the loop's state and your chat are not there; a different product |

Why the chosen one: it is the mechanism away-loop already uses, so its start check, re-arm order and stale-tick rule
carry over; it yields to you by construction; it is the only option restored after a resume; and its expiry
becomes a feature (renewal) rather than a fight. The 15-minute beat reads the conversation from cache; the
60-minute quiet beat may miss it (DERIVED from the prompt-caching docs), so quiet mode leans on a watcher that costs
nothing while it waits, and the silence limit ends a loop nobody is reading. The skill must be one Claude may invoke
by itself, because "a scheduled fire only runs skills that Claude is allowed to invoke on its own"; so starting it
is guarded by the charter's typed yes, not by the frontmatter.

**Job expiry and the charter are different things.** A recurring job expires 7 days after creation on Claude Code
versions before 2.1.330 and 30 days from 2.1.330 on (the job fires one last time and deletes itself). The skill
re-arms after 6 days, which is safe for both, at each renewal and when it changes speed. The charter stays 7 days
whatever the job's expiry: that is how long a forgotten loop may run without you saying yes again, and it is a
decision, not a platform limit.

### What it may decide

```
 Figure 7 (EXPECTED): four classes, sorted by three questions

   1. UNDO      can one revert on a branch nobody else builds on take it back?
   2. REACH     does it stay inside this roadmap item and inside this repo?
   3. SURPRISE  would you be surprised to hear it was settled without you?

   on the never list ───────────────────────────────────────────────►  D  NEVER      queue the ask; do not do it
   undo NO, or reach NO, or one of the five big kinds ──────────────►  C  QUEUE      prepare options + a recommendation
   undo YES, reach YES, a real fork (2+ workable designs) ──────────►  B  DECIDE,    full entry: diagram + example
                                                                          FLAG
   undo YES, reach YES, the docs or the code already imply the answer ►  A  DECIDE,    short entry
                                                                          LOG
   not sure which class ────────────────────────────────────────────►  one class UP (A to B, B to C)
```

The five big kinds are architecture, security boundaries, public contracts, scope, and anything that costs money.

| Class | Example decisions |
| --- | --- |
| **A: decide, log** | the name of an internal function, file or test · where a new test goes and what shape it has · the order of two steps inside an item · the wording of an error message · which existing helper to reuse · fixing a check its own change caused · the severity of a review finding · a comment or README paragraph the item requires · bumping a timeout in its own test |
| **B: decide, flag** | an internal data structure or module boundary the roadmap leaves open · which of two algorithms, when both pass the check · how an edge case behaves when the spec is silent · the layout of a new config section nothing outside the repo reads · **changing what an existing test expects, with the reason** · splitting one item into two PRs · declining a reviewer's suggestion, with the reason · skipping an item because it is blocked · **adding a dependency, inside the guardrails below** |
| **C: queue, prepared** | anything in a public contract: a CLI flag, an exported API, a file format, a schema · a new service, queue, database or table, or a major version of a dependency · anything touching auth, secrets, permissions or what data leaves the machine · changing the scope, order or check of a roadmap item, or adding one · a migration of stored data · changing CI, release or build configuration · a licence question · a reply in your name outside its own PRs' review threads (an issue, someone else's PR) · anything two project documents disagree about |
| **D: never** | merging or approving a PR · pushing to the default or a release branch · force-pushing · `--no-verify` · any delete (files outside its change, branches, worktrees, stashes, resources, data), **its own branches and worktrees included**, at wind-down, on a veto and after a merge: it lists the clean-up with the exact commands for you · enabling auto-merge or a merge queue · closing or reopening PRs or issues · changing repository settings or memory · publishing, releasing, tagging, deploying · spending money · writes to production · changing settings, `CLAUDE.md`, `AGENTS.md`, hooks or this skill's files · changing its own charter or limits · network, VPN or system settings · touching another session's worktree, branch or processes · printing secrets · deleting, skipping or weakening a test to make a check pass · working around a refused permission |

- **Class C** includes everything short of deciding: the options, what each costs, a recommendation, and what it
  would do next under each. It may build **one clearly labelled throwaway spike branch** per queued item (never
  merged) to make options concrete.
- **Class D** holds not with a blanket go and not when it would unblock everything. The loop queues the exact
  words you would say ("merge 37") and moves to other work.
- **A refused action is a queue item**: when the permission system says no, it writes down what it wanted and why,
  and does not look for another route.
- **The never list is the skill's own default**, so it holds for a stranger with no other rules; a project's rules
  make it stricter, never looser.
- **Dependencies are class B with guardrails**, because everything happens on the loop's own branches and a veto
  removes the dependency before anything merges. The guardrails: prefer the standard library or an existing
  dependency; a permissive licence only; a maintained package with a recent release; no known advisories; the
  version pinned and the lockfile updated; no install script it cannot explain; one dependency per entry, with the
  reason and the alternative it rejected. Any guardrail that fails makes it class C.
- **A changed test expectation** is a flagged decision with the reason. Deleting, skipping or loosening a test is
  never allowed.
- **Nothing is ever deleted by the loop.** A veto reverts with new commits; at wind-down and after one of its PRs
  merges it lists the branches and worktrees to remove, with the exact commands, and you run them. Only its own
  scratch files in the session scratchpad, and the dependency folders and build output it produced in its own
  worktree, are its to remove.
- **Autonomy** is one setting: `minor` (queue class B like C; first runs), `standard` (the default), or
  `ask-first:<area>` (queue class B for the named area). Class C and D are not reachable by any setting.

Examples: A: name a new test after the existing pattern; follow the house style for an error message. B: put new
CSV columns at the end rather than grouping them by meaning; pick one of two workable designs for a helper. C: a
new dependency with a major version, an API other code relies on, a security boundary, an item's scope, anything
that costs money. D: merge, delete (its own branches and worktrees too), publish, deploy, spend, change settings, push to the default branch, force-push.

### The decision log and the review

```
 Figure 8 (EXPECTED): one ledger in the repo, an index in the todo list, a pointer in each PR

   the repo, on the loop's log branch (one rolling PR)          the session's todo list            each work PR's body
   ┌─────────────────────────────────────────────────┐         ┌──────────────────────────┐       ┌──────────────────────┐
   │ <decisions folder>/2026-11-24.md                │◄────────│ ## Decisions to review   │       │ Decisions in this PR │
   │  ## D-014 · 2026-11-24T14:07+0000 · B · pending │  points │ D-014 B pending  <link>  │       │ D-014 <one line>     │
   │  ## D-015 · 2026-11-24T14:31+0000 · A · pending │         │ D-015 A pending  <link>  │◄──────│ D-015 <one line>     │
   │  the full entries: the source of truth          │         │ ## Waiting for you  C-3  │       │ <links to the ledger>│
   └─────────────────────────────────────────────────┘         └──────────────────────────┘       └──────────────────────┘
```

The ledger is a committed doc in the repo, with only an index in the todo list. In the repo it can be read by you
in any session or on GitHub, by other agents and by a later session; every entry and every verdict is a commit;
entries carry diagrams without bloating what every tick reads. Only the index is in the todo list, because
todo-sync's list "is not a handoff". It lives in the project's own decision-log or progress folder when it has one,
else the loop proposes one the first time and asks. Entries go on one long-lived log branch with one open PR,
pushed after every entry so a crash loses nothing; you merge that PR whenever you like, and the loop never does.
The fallback, when a project wants no such branch, is a git-ignored folder in the main checkout, with the loss risk
said out loud. The entry format is in [references/ledger-entry.md](references/ledger-entry.md).

One flagged entry, shortened:

```
 D-014 · B · pending: new export columns go at the end; existing columns keep their order
   roadmap item   R3 "Export v2"
   options        1 append at the end (chosen): spreadsheets and the 14 export tests keep working
                  2 group by meaning: nicer to read, but breaks anyone reading columns by position
   example        1042,2026-11-02,Acme,120.00  ──►  1042,2026-11-02,Acme,120.00,21.60,EUR
   undo           git revert <sha> on feature/export-v2-loop; nothing depends on it; ~10 min to redo as option 2
   review         (empty until you answer)
```

A class A entry is short: the heading, the decision, why it came up, what it depends on and the undo line. A flagged decision made while you are present is
**announced at once, in one line**, so "tell me later" never becomes "surprise me later"; the diagram waits for the
review.

```
 Figure 9 (EXPECTED): from a pile of entries to verdicts, without a wall of text

  TRIGGER  "review" · "what did you decide" · (after "I'm back" the status offers it) · the first message after 2+ hours
     │      (after 2+ hours the loop only offers: "7 to review, 2 flagged. Say 'review' when you want them.")
     ▼
  RE-CHECK the sources: PR and CI state now, not as of the entry
     ▼
  DIGEST   1. flagged (B) first, roots before the entries built on them, each in full: decision, diagram, example, undo
           2. minor (A) as one table, a line each
           3. waiting for you (C), each with its options and the words that unblock it
     ▼
  YOU READ.  Nothing is asked in the same step.
     ▼
  VERDICTS when you say you have read it: free text ("keep 14 15, veto 16, change 17: sort by date")
           or question panels, at most 4 per panel, the recommended answer first
     ▼
  APPLY    keep ► accepted            change ► redo            veto ► undo            discuss ► parked
```

| Verdict | The loop does | Recorded as |
| --- | --- | --- |
| **Keep** | nothing more | `accepted`, with the date and your words |
| **Keep all minor** | accepts every class A entry shown | each one `accepted` |
| **Change: how** | **redoes the work on the same branch** as new commits; a new entry (`D-031 supersedes D-014`) carries your choice; checks run again; anything built on the old choice is re-checked and listed | old entry `changed → D-031` |
| **Veto** | **shows what depends on the decision, then reverts it**; your veto is the go. `git revert`, newest first, a new commit and never a reset or force-push, checks re-run, pushed. If the whole PR was the decision it says so and leaves closing the PR to you | `vetoed`, with what was reverted |
| **Veto, already merged** | opens a revert PR for you to merge and adds the redo to the roadmap view | `vetoed (merged): follow-up <link>` |
| **Discuss** | parks the item and everything built on it; picks other work | `discussing` |

Rules that keep the review honest: **silence is never consent**, so an entry stays `pending` until you answer;
**merging a PR accepts the decisions listed in its body** (your own act, the one implicit path); **a veto teaches
once**: the loop proposes one standing answer for the charter ("when the spec is silent on ordering, ask"), added
only on your yes and never written into `CLAUDE.md`, memory or settings; roots come first in the digest so that a
veto of an early entry is seen before the later ones built on it; the digest is rebuilt from the ledger, never from
the conversation; flagged entries cannot be bulk-kept, only class A can; and a reviewer subagent checks the class of
each flagged entry. Every review comment on the loop's own PRs is answered, whoever wrote it: a fix (class A) or a reasoned reply
(declining, class B), then the thread resolved. A reply in your name outside its own PRs' review threads (an issue, someone else's PR) is class C and is drafted for you.

The shape of an entry is the well-known decision record (context, options, outcome, consequences); the four
additions are a diagram, a worked example, the exact undo, and what depends on it.

### How loud it is

Borrowed from away-loop whole: the per-tick table, the full report about every 2 hours measured by elapsed time (not
tick count, because ticks start cold and missed ticks collapse into one fire), the milestone report, new
information only, full links, and saved reports as snapshots never edited. What is new is that you may be in the
same session, so the volume follows where you are.

```
 Figure 10 (EXPECTED): how loud a tick is, by how recently you typed

   last message from you             posture     a tick replies with
   under 15 minutes ago              PRESENT     one gauge line; nothing if a request of yours is still running
   15 minutes to 2 hours ago         NEARBY      the status table, new information only
   over 2 hours ago                  AWAY        the status table; the full report every 2 hours and at each milestone
   an away mark ("I'm going to sleep")                  AWAY        the same, until your next message clears the mark
   any time, on request              -           "status": the table · "report": the full report · "review": the digest
```

The loop knows the posture because it writes the time (from `date`) of each message you type into the state line;
it never guesses presence from the clock. The gauge line is the smallest update and the first line of every larger
one:

```
on-loop · R3 Export v2: step 2 of 4 · decisions 5 pending (2 flagged) · PRs 3 open · day 2 of 7 · next beat ~14:37
```

The **status table** is away-loop's five rows (Finished, Started, Decisions, Running, Blockers) plus **Limits**,
shown only when something is within 20% of a bound. The **full report** is away-loop's seven sections in the same
order (state and where we are; the build; the merge queue; since the last full report; time to completion; what is
left; what is needed from you) with two additions: **Decisions** after the fourth section, and **Drift and budget**
after the fifth. Milestones (an item, a phase, the roadmap finished) always get the full report. Reports are shown
in the chat and saved as `YYYY-MM-DD-HHMM-status.md` in the project's progress folder, if it keeps one, committed on
the log branch. Outside the session there is nothing in version 1: no notification, no channel.

What a tick never does: restate earlier ticks, post a table when nothing changed, open a question panel, or print a
diagram nobody asked for while you are present.

### Limits and when it stops

Because it cannot keep going always, every prior loop without a hard bound is a warning (AutoGPT, an early open-ended
agent, became known for loops without a halt condition; a first-party loop plugin says "Always rely on `--max-iterations` as
your primary safety mechanism"; one open-source loop refuses to start unless a run count, a cost or a duration is
set). The on-loop takes that rule: **no charter with limits, no loop.**

```
 Figure 11 (EXPECTED): three outcomes at a limit

   QUIET   start no new item; keep open PRs green; answer review comments; heartbeat drops to 60 min
   PARK    leave one item alone, queue it with diagnostics, move to the next
   STOP    wind down: delete the jobs, stop own processes, final report, charter ended. Only you restart it.
```

| # | Limit | Default | At the limit | Why this number |
| --- | --- | --- | --- | --- |
| 1 | **Lifetime** | the charter's 7 days from the start | renewal asked on day 5 and day 6 in the reports; with no renewal, STOP at the end | a forgotten loop must end; a renewal re-reads the roadmap and the charter. Independent of the job's expiry |
| 2 | **Silence** | no message from you for 24 hours | QUIET at 24 hours, STOP at 72 | always-on assumes someone is reading. A weekend fits; a forgotten loop does not |
| 3 | **Fix rounds on one item** | 3 | PARK the item with the failing output | a third failed fix usually means a wrong assumption, not a typo |
| 4 | **The same failure** | the same check or error 3 times on one item; 5 times across items | PARK; at 5, STOP | one open-source loop's circuit breaker uses 3 no-progress and 5 same-error loops |
| 5 | **No progress** | 3 attempted work beats in a row with no commit, no PR change and no decision | STOP, with what it was trying. A beat that yielded to you, was held by disk or load, waited on you or CI, or ran while a builder was inside its budget does not count | a loop that only talks burns tokens |
| 6 | **Parked items** | 3 parked in a row | STOP | the roadmap or the environment is wrong, not the items |
| 7 | **Roadmap exhausted** | done, or every remaining item blocked or not ready | QUIET; it proposes what could come next for your yes | it never invents work. A built-in maintenance prompt falls back to "cleanup passes"; the on-loop does not, because idle cleanup is where drift and cost come from |
| 8 | **Usage limit reached** | Claude Code reports a usage limit | carries on at the next tick after the reset (Claude Code's default) | it reacts to the notice only; no gauge |
| 9 | **Disk** | free space under the project's install floor, or 5 GiB when it has none | no installs or builds; queue the cleanup (the loop never deletes to make room) | quiet disk exhaustion |
| 10 | **Load and memory** | load above half the cores, or memory pressure reported | no new heavy job; let the running one finish | the machine check |
| 11 | **Stray processes** | every job it starts has a budget of about twice its normal run | stop it by PID (polite signal, then forced) at the budget; list its own strays before each report | a job can outlive its agent by hours |
| 12 | **Context** | a compaction, or a restart | re-read the state from the files; run todo-sync's recovery if the list looks short; for a restart, `checkpoint` | nothing lives only in the chat |
| 13 | **Items in flight** | the charter's line, default 2; one heavy job at a time | wait | the machine and review focus: a pacing line, not a cap on PRs waiting for you |

**It never stops itself because work or review is piling up, or because usage ran out.** It stops only for the
bounds you set (lifetime, silence) and for the ones that say the loop itself is lost (no progress, the same failure,
parked items), and it says why. Every default is a line in the charter you can change in words; the loop cannot.

**Drift**, in every full report; any non-zero row is a stop-and-ask:

```
 Figure 12 (EXPECTED): the drift table

   check                                                        this report
   commits not tied to a roadmap item                           0
   files changed outside the item's stated boundary             0   (a justified one is a logged decision)
   items worked out of roadmap order without a logged reason    0
   roadmap changed since the last re-plan (by anyone)           no  (yes: re-read, re-plan, say so; the row resets after the re-plan)
   tests deleted, skipped or loosened                           0   (a changed expectation is a class B entry)
```

**Your own work and other sessions.** The loop works only in worktrees and branches it created. Before picking an
item it lists the repo's worktrees, branches and open PRs; if you or another session have changes in the same files
it takes a different item or queues this one. Your word wins at once: "I'm taking R4" releases the item (it pushes
what it has, records where it stopped and leaves the branch). A project's heavy-work lock is honoured. There is no
active-hours window: it works whenever its session is open and idle, and the posture rules keep it quiet while you
type.

**Models.** The project's own model rule where it has one; otherwise the cheaper model for builders and reviewers
and one strong verdict per item.

**The ways to stop it:** say "stop the loop" (or "pause the loop", which keeps the charter and deletes the
jobs); exit the session and choose "Exit and stop tasks"; for a session sent to the background, `claude stop <id>`;
quit Claude Code. `Esc` and `Ctrl+C` do not stop a
fixed-interval job, and the arming message says so.

### Why there are no caps

The loop has **no cap on decisions, no cap on PRs and no depth limit**. It prefers independent work (each item on its
own branch off the default branch, with its own PR) and stacks PRs freely when the work needs it; a veto shows its
cascade before it reverts. When a step cannot proceed, for example because it waits on a decision of yours, the loop
works down this list:

```
 WHAT THE LOOP DOES WHEN A STEP IS BLOCKED (EXPECTED)
   1  another ready roadmap item          independent work is unlimited
   2  the same item, other work           tests, docs, the half of the item that doesn't depend on the choice
   3  prepare what's queued               options and a throwaway spike for a decision waiting on you
   4  only if none of these exist         wait, and tell you the ONE decision whose review unblocks it
```

The cost, stated honestly: after a long stretch the review list can be long. The digest shows flagged decisions first
and roots first, so you start with what matters.

**Considered and dropped.** An earlier design had a cap on unreviewed decisions (12, of which 4 flagged), a cap on PRs
waiting for your merge (5), and a depth rule (stacks at most 2 deep). Both caps limit how much work piles up before
you have looked at it. Neither guards against damage: the loop works only on its own branches and nothing merges
without you. What they limit is redo work and review load.

```
 Without the review cap (EXPECTED)                       With it
 D-1 flagged ─► 6 commits built on it                    after 4 flagged (12 total) waiting: QUIET —
 D-2 flagged ─► 9 commits                                it tends open PRs and answers reviews, starts
 … D-15                                                  nothing new, until you review
 you come back: 40 decisions to read;                    a veto undoes a small amount
 veto D-1 ─► revert through 30 commits
```

```
 Without the PR cap (EXPECTED)                           With it
 it can't merge, so PRs wait for you:                    5 waiting, stacks at most 2 deep: QUIET
 PR-1 ◄─ PR-2 ◄─ PR-3 ◄─ PR-4  (each built on the last)
 "change" in PR-1 ─► rebase PR-2, 3, 4
 or PRs off main that conflict with each other
```

The real risk in both is depth, work built on work you have not reviewed; the count mostly controls how much there
is to read at once. Three options were weighed:

| Option | What it keeps | Outcome |
| --- | --- | --- |
| Depth rule only | nothing builds on more than one unreviewed flagged decision, and PR stacks stay at most 2 deep; no count cap, so it keeps working on independent items for as long as it has them | dropped too (below) |
| Keep both caps (12/4 decisions, 5 PRs) | shorter reviews, less to rebase | dropped |
| No caps at all | it never goes quiet for review load; a veto can mean a longer revert chain, which the cascade shows first | **what ships** |

The depth rule does not count how much is waiting for you; it only stops the loop from building on top of choices
you have not seen yet:

- **One level is fine.** A step may build on one unreviewed flagged decision, such as a function's shape you have not
  approved yet.
- **Two levels are not.** If the next step would build on a decision that itself rests on another unreviewed one, the
  loop moves to a different item instead; with no other item, it waits for you to review that one decision.
- **PRs work the same way.** PR-2 may sit on top of unmerged PR-1, but PR-3 may not sit on PR-2.

```
 ALLOWED: side by side, as many as it has                 THE TOWER THE DEPTH RULE WOULD HAVE STOPPED
   main                                                   main
    ├─ R1 branch: D-1 flagged, unreviewed                  └─ R1 branch: D-1 flagged, unreviewed
    ├─ R2 branch: D-2 flagged, unreviewed                       └─ next step builds on D-1 and makes D-5 (flagged)
    ├─ R3 branch: D-3 flagged, unreviewed                            └─ a step building on D-5   x stopped here
    └─ R4, R5, … every independent item it can do
```

The depth rule was dropped as well, so the tower is allowed now, because a lot of work needs to be built as stacked PRs, and reviewing stacked PRs is fine;
building items separately is still preferred where possible, and the loop is encouraged to.

### The loop-state marker

One heading line in the session's todo list tells every skill whether the loop is live. It is written by the on-loop
and read by todo-sync, checkpoint, away-loop and the on-loop itself:

```
 Figure 6a (EXPECTED): the marker, and what each state means

 ## Loop state: ARMED — on-loop — charter valid until 2026-12-01T09:00+0000 — job 5c0e91a2
 Answers: "stop the loop", "pause the loop", "renew the loop", "review", "status", "report", "resume", "I'm back", "good morning", "back online", ...
 Owns: "On-loop charter", "On-loop state", "Roadmap view", "Decisions to review", "Waiting for you"

   ARMED   a job exists. Answers: lists every phrase the loop answers.
   PAUSED  no job; the charter and its clock stay. The heading ends "reason checkpoint" (checkpoint deleted the job
           for a restart or a quit) or "reason user" (you paused it). Answers: resume the loop / resume / stop / renew /
           review / status / report / I'm taking, and keep/veto/change <ids> while entries are pending.
   ENDED   no job; the heading says why. Answers: only "review" and keep/veto/change <ids> while entries are pending.
```

- **Arm order:** `CronCreate` first; only on success the marker (ARMED, with the job id) and then the claim. On a
  failure nothing is written, or ENDED with the reason, and you are told.
- **"stop the loop"** deletes the job and writes ENDED. **"pause the loop"** deletes it and writes PAUSED, reason user.
  **"resume the loop"** (or "start the on-loop" over its own PAUSED marker, or a bare "resume" with no resume block; it says in one line that it is resuming, no question)
  re-creates the job, writes ARMED and updates the claim; the charter's clock keeps running. **"renew the
  loop"** extends the charter by its length (7 days) from now and re-arms; from a pause you started, it extends the
  charter and stays paused.
- **Confirming the job:** on any message routed to the loop, and at each tick's step 0, `CronList` confirms the job.
  If it is missing while the marker says ARMED, the loop says so in one line and offers to re-arm; it never re-arms
  silently (it never deletes or re-creates the job on its own either), and never after you stopped it. Limit: a job that
  disappears is noticed only at the next tick it should have run, or at the next phrase routed to the loop.
- **A resumed session** (`--resume`): the marker decides. A restored job under an ENDED or PAUSED marker is deleted.
- **A consumed away-loop plan** never reads as an armed on-loop: away-loop's own plan heading is its state, and the
  marker is the on-loop's.
- The other skills' guards are worded generically against this heading ("a `Loop state` heading owned by another
  skill") and act on its `Answers:` line, so those three skills never name this one and each works without it.

### Which skill answers which phrase

Several skills react to everyday phrases, and some phrases mean different things to different skills. **The
session's state decides who answers, not the words.** The overlaps, taken from each skill's description:

| Phrase | todo-sync | checkpoint | away-loop | on-loop |
| --- | --- | --- | --- | --- |
| "I'm back", "good morning", "back online" | | resume after a restart | stop and summarise | the review offer, when there is no resume block |
| "continue", "resume", "carry on", "keep going" | | resume after a restart | (it is what arms it: "carry on without me") | one line, when there is no resume block |
| "I'm going to sleep", "I'm stepping away" | | | arms | already running: becomes AWAY |
| "stop ..." | | "stop everything safely" | any message stops it | only "stop the loop" |
| "wrap up", "close out" | closes this session's part; never deletes a live loop's list or blocks | | | |
| "status", "report", "review" | | | | its own commands |
| a restart or a quit | | deletes loop jobs first, then resumes them | | re-armed by checkpoint's resume |
| after a compaction | recovers the list first | | re-reads its plan | invoke the skill again, re-read the marker and charter |

The routing, by state:

| Phrase | Nothing armed | away-loop armed | on-loop ARMED | on-loop PAUSED | on-loop ENDED, entries pending |
| --- | --- | --- | --- | --- | --- |
| "I'm back", "good morning", "back online" | checkpoint resumes, if a resume block exists | away-loop stops and summarises | resume block: checkpoint resumes, re-arming only a loop it paused (`reason checkpoint`); none: a short status and the review digest offer | resume block: checkpoint resumes and re-arms a `reason checkpoint` pause, nothing for `reason user`; none: not answered by the loop | not answered by the loop |
| "continue", "carry on", "keep going" | checkpoint resumes, if a resume block exists | (already working) | resume block: as above; none: the on-loop says it is already working | resume block: as above; none: not on its `Answers:` line | not answered by the loop |
| "resume the loop" | nothing to resume | (already working) | already working | the on-loop resumes (charter clock kept) | nothing to resume |
| a bare "resume", with a "Resume here" block | checkpoint resumes | (already working) | checkpoint resumes | checkpoint re-arms a `reason checkpoint` pause only, nothing for `reason user` | not answered by the loop |
| a bare "resume", no resume block | nothing to resume | (already working) | the on-loop: already working | the on-loop resumes (charter clock kept) | nothing to resume |
| "I'm going to sleep", "keep working while I'm away", "proceed while I sleep", "work overnight", "I'm stepping away" | away-loop arms | (already armed) | the on-loop stays armed; its posture becomes AWAY | away-loop does not arm: one line says the on-loop owns the session and how to resume or stop it | away-loop arms |
| "review", "keep/veto/change <ids>" | no skill | no skill | the on-loop | the on-loop | the on-loop |
| every other checkpoint trigger ("checkpoint", "save progress", "I'm going to restart", "before I restart", "before I quit", "stop everything safely", "is it safe to restart") | checkpoint | checkpoint | checkpoint | checkpoint | checkpoint |
| "stop the loop", "pause the loop" | nothing to stop | away-loop answers | stop / pause | stop (pause: already paused) | nothing to stop |
| other "stop ..." | no skill | away-loop stops | not a stop: answered | not a stop: answered | no skill |
| "wrap up", "close out", "close this initiative", "clean up old todo lists" | todo-sync closes this session's part | todo-sync, after away-loop has stopped | todo-sync closes its part; it never deletes the list or the loop's blocks; the loop keeps running | same: the list is shown and skipped, never deleted | todo-sync closes it out; the pending entries stay in the ledger in the repo |
| a restart or a quit | checkpoint | checkpoint deletes the loop's jobs first and resumes them after | checkpoint deletes the loop's job first (marker PAUSED, `reason checkpoint`) and resumes it after | nothing to delete; a `reason user` pause stays paused | checkpoint |
| after a compaction | todo-sync recovers the list first | away-loop re-reads its plan | the on-loop skill is invoked again and re-reads its marker and charter | same | the on-loop is invoked for a pending verdict |

Every checkpoint trigger stays checkpoint's in every state. Each skill ships on its own, so each carries a short
guard for the rows that concern it: todo-sync, checkpoint and away-loop each have one paragraph, worded against the
marker and not by name.

### Working with the other skills

```
 Figure 13 (EXPECTED): what the on-loop reuses, and the hand-offs

   todo-sync  (REQUIRED)    holds the charter, the loop state, the roadmap view, the decisions index and
                            "Waiting for you". The on-loop asks todo-sync where the list is; it never assumes a path.
                            After a compaction: todo-sync's recovery first, then the tick.

   checkpoint (optional)    restart or quit ──► you run /checkpoint ──► the on-loop deletes its jobs FIRST, so no
                            tick fires mid-checkpoint ──► the marker becomes PAUSED, reason checkpoint, and the
                            resume block's first item is "resume the loop (owner on-loop, charter valid until
                            <date>)" ──► after "continue": the on-loop's "resume the loop" step re-arms it, clock
                            NOT reset. A
                            break (no restart, no quit) leaves job and marker alone; a user-paused loop gets no item

   away-loop  (separate)    one loop per session.
                            on-loop armed + "I'm going to sleep" ──► stays the on-loop; posture AWAY; same authority
                            away-loop armed + "work the roadmap"  ──► away-loop stops and summarises first, then the gates
                            nothing armed + "I'm going to sleep"  ──► away-loop, as today

   crossfire  (manual)      the loop cannot run it: it is manual-only, and a scheduled fire runs only skills Claude
                            may invoke itself. A design-heavy class C item is queued with the exact words:
                            "run /crossfire <path>".
```

| Reused from | What | Changed for the on-loop |
| --- | --- | --- |
| away-loop | the scheduling check before promising anything; "never pretend the loop is armed" | none |
| away-loop | the re-arm order (create, record, delete, list shows exactly one) | also used to switch speed and at renewal; never used to outlive the charter unasked |
| away-loop | the stale-tick rule | "no marker, or the marker says ENDED or PAUSED"; a missing job under ARMED gets one line and an offer to re-arm |
| away-loop | the tick prefix that tells a tick from a typed message | a different prefix |
| away-loop | the status table and seven-section full report, elapsed-time cadence, saved snapshots | one more row, two more sections; posture decides which is shown |
| away-loop | the three todo-list sections (plan, decisions, waiting) | plan becomes the roadmap view; decisions become an index into the ledger |
| away-loop | every trap | all kept |
| away-loop | "Never while away" | kept and extended (class D) |
| todo-sync | nothing leaves the list unconfirmed; reorganize before prune; keep the detail | roadmap items and skipped items follow it |
| checkpoint | the scan of machine, worktrees and processes; the resume block | the block names the loop and its charter |

## What it stores, and where

| What | Where | Written by |
| --- | --- | --- |
| The loop-state marker (ARMED, PAUSED or ENDED, with its `Answers:` and `Owns:` lines) | the top of the session's todo list | the agent |
| The charter, the loop state (job id and creation time, speed, last beat, last message from you, counters), the roadmap view, the decisions index, "Waiting for you" | the top of the session's todo list, which `todo-sync` keeps | the agent |
| The decision ledger: one file per day, entries appended | the repo, in the project's decision-log or progress folder (or one the loop proposes), on the loop's log branch with one rolling PR | the agent; you merge the PR |
| Saved full reports | the project's progress folder, if it keeps one, as `YYYY-MM-DD-HHMM-status.md`, on the log branch | the agent |
| The claim (session id, charter end date, job id, start time, last beat; released as `released <time>`, never deleted) | a file in the repo's shared git folder, never committed | the agent |
| The loop's work | its own worktrees and branches named by the project's convention plus a `loop` suffix | the agent |

The roadmap itself stays where it is; the loop changes only an item's status, through a pull request on a loop branch.
The todo list is not a handoff: everything another session or you must read is in the repo.

## Install

As a plugin, from the `agents` marketplace:

```
/plugin marketplace add sharvilk/agents
/plugin install on-loop@agents
```

That also installs `todo-sync`, because the plugin declares it as a dependency.

Or copy the `on-loop` and `todo-sync` folders to `~/.claude/skills/` (or `$CLAUDE_CONFIG_DIR/skills/` if you set
that variable). Nothing needs registering: Claude Code finds
each skill by the `name` and `description` at the top of its `SKILL.md`. To check it loaded, ask for it by name
("start the on-loop"); with no roadmap it will draft one and stop, which is the safe first answer.

`away-loop` and `checkpoint` are optional. If you installed `todo-sync`, `checkpoint` or `away-loop` before the
on-loop, update them (`claude plugin update todo-sync@agents`, and the same for the others), so each carries the
guard that leaves a running loop alone ([Working with the other skills](#working-with-the-other-skills)).

It has no script, so there is nothing else to run or install.

## Examples

**The charter** at the top of the session's todo list:

```md
## Loop state: ARMED — on-loop — charter valid until 2026-12-01T09:00+0000 — job 5c0e91a2
Answers: "stop the loop", "pause the loop", "renew the loop", "review", "status", "report", "resume", "I'm back", "good morning", "back online", "continue", "carry on", "keep going", "I'm going to sleep", "keep working while I'm away", "proceed while I sleep", "work overnight", "I'm stepping away", "I'm stepping away for a few hours", "I'm taking <item>", "keep/veto/change <ids>"
Owns: "On-loop charter", "On-loop state", "Roadmap view", "Decisions to review", "Waiting for you"

## On-loop charter
Roadmap: docs/roadmap.md at 4be21a0. Scope: R1 to R6. Autonomy: standard. Models: project rule (cheap builders, one strong verdict).
Single-threaded: no.
Limits: lifetime 7 days · silence quiet 24 h, stop 72 h · fix rounds 3 · same failure 3/5 · no progress 3 beats · parked 3 · in flight 2.
Branches: feature/<item>-loop. Ledger: docs/decisions/, log branch docs/decision-log-loop, PR <link>.
Approved: "yes, start it" on 2026-11-24.
Standing answers: none yet.

## On-loop state
job 5c0e91a2 created 2026-11-24T09:03+0000, speed work · last beat 2026-11-24T14:07+0000 · last user message 2026-11-24T13:41+0000 · away mark none · last full report 2026-11-24T12:05+0000
counters: fix rounds R3: 0 · same failure none · beats without progress 0 · parked in a row 0
roadmap commit read: 4be21a0 · claim: held
```

**An arming message**, after the charter is approved:

```
On-loop armed.
Works: R1 to R6 of docs/roadmap.md, one step at a time, on feature/*-loop branches.
Yours: it never merges, publishes, deletes or deploys; those stay yours.
Decisions: logged in docs/decisions/ for your review.
Limits: 7 days (renew on day 5 or 6), quiet after 24 h of silence, stop after 72 h, and the bounds in the charter.
Ticks: fire only while Claude Code is running and idle (a closed app, an exited session or a sleeping machine means
none); a tick due while the agent is busy or a question panel is open waits and runs right after the turn ends.
Beat: 7, 22, 37 and 52 minutes past each hour; hourly when everything waits on you or CI.
Mode: multi-threaded.
Stop it: say "stop the loop"; "pause the loop" keeps the charter and "resume the loop" brings it back.
/bg keeps the jobs running (a backgrounded session fires on time).
"Exit and stop tasks" on /exit stops them.
`claude stop <id>` stops a background session.
Esc or Ctrl+C does not stop a fixed-interval job.
```

**A gauge line** while you are working in the session:

```
on-loop · R3 Export v2: step 2 of 4 · decisions 5 pending (2 flagged) · PRs 3 open · day 2 of 7 · next beat ~14:37
```

**A flagged announcement**, whatever the posture:

```
D-014 (flagged): appended the new export columns instead of regrouping; entry in the log.
```

**A status table** on a tick, when you have been away 40 minutes:

| | |
|---|---|
| Finished | PR 61 CI is green; two review comments fixed and resolved |
| Started | R4 "Import dates", because R3 waits on your merge |
| Decisions | D-016 (A) test placed beside the import tests; D-017 (B, flagged) empty dates are rejected, not defaulted |
| Running | one reviewer on R3, budget 20 minutes |
| Blockers | R5 needs a CLI flag, a public contract: queued as C-3, unblocked by "C-3: add --format" |

**A review:**

```
you:  review
loop: 7 to review, 2 flagged. Flagged first.
      D-014 · B · pending: new export columns go at the end ... (decision, diagram, example, undo)
      D-017 · B · pending: empty dates are rejected ...
      Minor (A): a table, one line each (D-015, D-016, ...)
      Waiting for you: C-3 (a CLI flag): options and a recommendation
you:  (reads) ready
loop: verdicts? free text is fine ("keep 14, veto 17, change 18: sort by date, keep all minor").
you:  keep 14, veto 17, keep all minor
loop: D-017 is built on by D-019 (a test) and commit 9c1e..; reverting both on feature/import-dates-loop, newest first,
      checks re-run, pushed. D-014 and the five minor entries accepted. Standing answer proposed: "when the spec is
      silent on empty input, ask". Add it?
```

**Stopping:**

```
you:  stop the loop
loop: jobs deleted (CronList shows none); strays: none; PRs re-checked. Final report ... 5 decisions waiting for
      review, 2 PRs waiting for your merge. Marker ENDED; open items are in the normal list.
      Clean-up for you to run (nothing was deleted): git worktree remove ../export-v2-loop, git branch -d feature/export-v2-loop
```

## Errors and what you see

| What happens | What you see | What to do |
| --- | --- | --- |
| `todo-sync` is not available | before arming: it says so and does not arm, because its state could vanish in a compaction | install `todo-sync` |
| `CronCreate` is not in the tool list, scheduling is off (`CLAUDE_CODE_DISABLE_CRON=1`) or the call is refused | the session cannot wake itself, so nothing will run while you are away; it never says a wake-up exists, and offers one bounded run | enable scheduling and ask again, or accept the shorter run |
| No roadmap, or an unapproved one | a draft with each line's source and a "Questions" list; it stops | read it, edit it, say yes in a later message |
| An item has no outcome, check or boundary | the proposed ones, queued for your yes; it works the ready items meanwhile | say yes or edit them |
| Another on-loop holds the repo | whose claim it is; it stops | stop that loop, or take over a stale claim with your word |
| A claim older than 2 hours | reported as stale | say whether to take it over |
| The loop's job fires in a resumed session whose charter ended or is gone | the tick deletes its own job and says so in one line | nothing |
| The job is older than 6 days, at a renewal, or on a speed change | a new job is created and recorded first, then the old one is deleted, then `CronList` confirms exactly one | nothing |
| That re-arm fails (scheduler off, permission refused, a task limit) | the old job stays; the report and "Waiting for you" say "wake-up ends when the old job expires; could not re-arm" | allow scheduling and renew before then |
| The charter reaches day 5 and 6 | renewal asked for in the report | say "renew the loop", or let it end |
| The charter ends, or you do not renew | wind down and the final report; the loop stops | say "start the on-loop" again |
| 24 hours without a message from you | QUIET: no new items, open PRs tended | send a message |
| 72 hours without a message | STOP, with a final report | restart it |
| The roadmap is exhausted, or everything left is blocked | QUIET; a proposal of what could come next | approve some of it, or stop |
| A roadmap file was edited under it | "roadmap changed: ..." and a re-plan | confirm or revert |
| A fix round fails 3 times on an item | the item is PARKED with the failing output | look at it, or say what to try |
| The same failure 3 times on one item, or 5 across items | PARK, then STOP | read the report |
| 3 work beats with no progress | STOP, with what it was trying | read the report |
| 3 parked items in a row | STOP: the roadmap or the environment looks wrong | read the report |
| A refused permission | the action goes into "Waiting for you" with what it was for; no route around it | allow it, or do it yourself |
| An action that is class C or D | queued with options and the exact words that unblock it, never done | say the words |
| Disk or load out of bounds | no installs or builds or heavy jobs; the cleanup is queued for you | free the space yourself |
| Claude Code reports a usage limit | the loop carries on at the next tick after the reset | nothing |
| A dependency fails a guardrail | it becomes class C: queued with the options | decide |
| A merged PR's decisions | marked `accepted (merged <date>)` | nothing |
| You veto a decision that other work builds on | the cascade is stated as its own line ("cascade: none" if empty) before any revert runs, then the loop reverts newest first in the same turn: the veto is the go, so it does not wait | read it; reply if the cascade is wrong |
| A tick is stuck behind a permission panel | nothing runs until you answer it; the gap rule then reports the missed beats | answer it, choosing the option that keeps allowing that folder |
| Load or disk is over its line | the tick takes no heavy step (no build, test run, install or subagent), does bookkeeping only, and says so once when it starts and once when it clears | free the space or wait |
| A veto of a decision already merged | a revert PR for you to merge, and a redo on the roadmap view | merge it |
| A tick fires while you are mid-request | no output | nothing |
| The session exits, the app closes or the machine sleeps | no ticks until Claude Code runs again; the next tick's report names the gap | nothing, or re-arm |
| A restart or quit | `checkpoint` deletes the loop's job first and marks it PAUSED, reason checkpoint; the resume block says "resume the loop"; after "continue" the on-loop's resume step re-arms it and the clock is not reset. A break leaves job and marker alone; a loop you paused yourself gets no re-arm item | run `checkpoint` |
| The tick finds the marker missing a job (the app was exited with "Exit and stop tasks", or the job was deleted) | one line: the loop's job is gone, with an offer to re-arm; it never re-arms silently | say yes to re-arm, or leave it |
| A session is resumed and a job comes back under an ENDED or PAUSED marker | the tick deletes the job and says so | nothing |
| `CronCreate` fails while arming | nothing is written, or ENDED with the reason; no claim; you are told | fix scheduling, start again |
| You say "pause the loop" | the job is deleted, the marker is PAUSED, the charter and its clock stay | "resume the loop" |
| You say "resume the loop" past the charter's end, or "renew the loop" | resume past the end offers a renewal; a renewal re-reads the roadmap, shows charter changes, extends 7 days and re-arms (from a pause you started, it stays paused) | say "renew the loop" |
| A drift row is above zero | a stop-and-ask: no new step on the affected item, a class C entry names the row, other items carry on | answer the entry |
| The project bars subagents | the loop works single-threaded and marks each PR and entry "checked by the builder only"; your review is the second opinion | review them |
| A job was stopped at its budget | the report names the job and the budget; its PID was stopped politely, then forced | nothing |
| You say a loose phrase such as "keep going" with no loop | it asks whether you want the on-loop and waits for the start phrase | say "start the on-loop" |
| Several roadmap files are found | it lists them and asks which | name one |
| The project wants no log branch | the ledger goes in a git-ignored folder in the main checkout, and the risk of losing it is said aloud | accept, or allow a branch |
| A ledger push fails | the entry stays in the working tree, the tick reports it and retries next tick; the loop starts no new step until it is pushed | fix access |
| One of its PRs is merged, or the loop winds down | the branches and worktrees to remove are listed with the exact commands; none is run | run them yourself |
| You ask to stop while a subagent runs | the job is deleted first; the subagent finishes or is stopped; its late report is recorded and takes no next step | nothing |
| away-loop is armed and you say "start the on-loop" | away-loop stops and gives its summary first, then the gates | nothing |

## Limits

- **Ticks fire only while Claude Code is running and idle.** A closed app or an exited session means no ticks, and
  while the machine sleeps nothing fires. A tick due while the agent is busy fires once when it becomes idle.
  A session you are typing in mostly waits.
- **A tick can run late**: up to half its period (up to 30 minutes on the quiet beat's 60, 7.5 on the work beat's 15). The minutes avoid :00 and :30 and differ from away-loop's `3,33`.
- **The job expires** (7 days before Claude Code 2.1.330, 30 from it); the skill re-arms after 6 days. **The charter
  is 7 days** regardless and needs your renewal.
- **Full reports follow elapsed time**, about every 2 hours from `last full report`.
- **It is a procedure, not a lock.** The agent follows it because the skill says so, and Claude Code's own
  permission checks sit under it (they already refuse a merge you did not ask for). The never list is a default.
  A hook that mechanically refuses merges, default-branch pushes, force-pushes, `--no-verify` and publishes would be
  a global settings change that could also block your own merges in that session, so version 1 ships none; one is
  added later only if real use shows a slip, on your go.
- **No usage gauge.** It reads no plan usage; it reacts to Claude Code's usage-limit notice.
- **No notification outside the session** in version 1.
- **No script in version 1**; the ledger is plain Markdown and counts come from `grep`.
- **Review is yours.** Merging a PR accepts the decisions it lists; nothing else counts as consent.
- **It needs the `todo-sync` skill.**
- **Start small.** Try it first on a project whose roadmap is short and clear, and review its first log before you
  leave it running for long.

### Risks and their mitigations

| # | Risk | Mitigation |
| --- | --- | --- |
| 1 | Review debt becomes rubber-stamping | flagged entries cannot be bulk-kept; roots first; digest rebuilt from the ledger |
| 2 | A veto cascades | the cascade is stated before any revert, which follows in the same turn; reverts are new commits, newest first; independent work preferred |
| 3 | A decision is misclassified | three written questions; one class up when unsure; concrete examples in each class; a reviewer subagent checks flagged entries |
| 4 | Drift | one step of one item per tick; every commit names its item; boundary first; the drift table must read zero; no idle cleanup |
| 5 | It declares victory early | done means the check plus a reviewer that did not build it; "merge-ready" requires resolved threads |
| 6 | Runaway cost | no charter without limits; quiet beat plus a watcher; no-progress, same-failure and parked stops; silence limit |
| 7 | It collides with your work | own worktrees and branches; overlap check before picking; your claim wins at once; never touches the main checkout |
| 8 | Two loops on one repo | one loop per session; one on-loop per repo by a claim file; others' branches read-only |
| 9 | Noise | posture: one line when present, nothing while your request runs |
| 10 | The loop dies quietly | the arming message says when ticks fire and do not; reports carry the last beat's time; a stale claim is reported |
| 11 | A stale tick after a resume | the stale-tick rule deletes the job |
| 12 | Context rot over days | all state in files; heavy work in subagents; a fresh session at each renewal |
| 13 | An unapproved roadmap | finding is not approval; the charter records your yes and the roadmap's commit |
| 14 | Injected instructions | issue-sourced roadmaps are snapshotted; text from others and the web is data; class C covers anything leaving the repo |
| 15 | It widens its own limits | changing the charter is class D; only your quoted words change a limit |
| 16 | Started by accident | explicit phrases only; nothing arms before the charter is answered with a typed yes in a later message |
| 17 | Trigger collision with the other skills | state decides, by the routing table; a guard line in each skill |
| 18 | The ledger is lost or wrong | push after every entry; only the heading line (status), the "Built on it since" line and the "Review" line change; counts come from `grep` |
| 19 | A project forbids what the loop assumes | the project's rules are read into the charter and override the defaults; single-threaded where subagents are barred |
| 20 | Leftover processes | budgets, stop by PID, strays listed before each report |
| 21 | The shared parts exist twice | one references file naming its origin; a second drift earns a diff check |
| 22 | Overstated guarantees | this README says "a procedure, not a lock" |
| 23 | Unverified platform behaviour | the probes below; the skill promises only what was probed |

## Unverified behaviour

Three behaviours of Claude Code were probed read-only on 2026-11-24 (Claude Code 2.1.322, in a throwaway session
with one-shot `CronCreate` jobs; MEASURED). The skill's procedure uses the results.

| Probe | Result (MEASURED) | Where the skill uses it |
| --- | --- | --- |
| (a) Do `CronCreate` wake-up jobs keep firing after the session is put in the background (`/bg`)? | **Yes, on time.** Two jobs set for 15:31 and 15:32 wrote their lines at 15:31:02 and 15:32:02 after `/bg`; `claude agents` listed the session as background and `claude stop <id>` stopped it | the arming message says a backgrounded session keeps its jobs; the ways to stop include `claude stop <id>` |
| (b) Does a skill's hook register when a scheduled tick invokes the skill? | **Moot in version 1**: there is no hook, so nothing depends on it | nothing |
| (c) Does a tick fire, or wait, while a question panel is open? | **It waits and is not lost.** A job due at 15:27 with a panel open had not run at 15:28:43, and ran at 15:28:54, three seconds after the turn ended | a tick never opens a panel; a late tick after a panel is expected; the gap rule (tick step 1) reports more than two missed beats |

The probes ran read-only in a throwaway session on Claude Code 2.1.322 with model Sonnet 5.5 in auto mode, in a throwaway signed-in config folder and an empty scratch project, using only one-shot `CronCreate` jobs that each appended a timestamp to a log file; the figures above are the measured results, unchanged.

**Seen in a trial run (2026-11-24),** in a throwaway session: a scheduled prompt's instruction to invoke the skill
works when a tick fires (the tick prompt, in the core's section 5, says "Invoke the on-loop skill"): the Skill call was
seen at each tick, and after `/compact` the pane showed "Skills restored". **Not verified:** the claim that no tool
keeps a reviewable ledger of its own decisions rests on one search, and the name screen below covers npm and GitHub
repo names only.

## Names considered

The id people type and install is `on-loop`, beside `away-loop` (away / on). The brand is the same: something
simple in the `<word>-loop` family rather than a coined word. A pun on "human in the loop": "human **on** the loop"
is the established term for oversight by review and veto rather than by approval, and "on" also says always-on.

The twelve candidates screened on 2026-11-24 (MEASURED: the npm registry's answer for the bare name and a GitHub
repo-name search; no trademark, domain or web search was done):

| # | Name | Kind | Rationale | Screen |
| --- | --- | --- | --- | --- |
| 1 | Onro | coined | "on" with a coined ending: the loop that stays on | npm free; GitHub only a robotics company's repos |
| 2 | Tendro | coined | from "tend": it tends the roadmap while you do something else | npm free; unrelated repos |
| 3 | Pursuo | coined | from "pursue": it keeps pursuing the roadmap | npm free; no repo by that name; the cleanest screen |
| 4 | Steado | coined | from "steady": steady progress, no drama | npm free |
| 5 | Onwardo | coined | from "onward": always the next item | npm free |
| 6 | Advanco | coined | from "advance" | npm free; also a company name |
| 7 | Decido | coined | from "decide": it decides and shows its working | npm free; a small R package; a real word in Spanish and Italian |
| 8 | Carrio | coined | from "carry on" | npm free; "carry on" is a trigger of `checkpoint`, a small confusion risk |
| 9 | Definite Loop | brand twist | on "infinite loop": it keeps going but has written limits | npm free; classroom exercises only |
| 10 | On the Loop (`on-loop`) | brand twist | on "human in the loop" | `on-the-loop` and `onloop` free on npm |
| 11 | LoopedOn | brand twist | a looped-in pun | npm free |
| 12 | `roadmap-loop` | plain | matches the family and says what it works on | npm free, GitHub clean |

Dropped on the screen: Persisto, Perpetuo, Continuo and GitGoing (taken on npm; Continuo is also a music term),
Proceedo (already a product name), Recursor (a well-known DNS tool), and `always-on` (a crowded generic term). `on-loop`
was chosen for plainness: it pairs with `away-loop` and says what it does. The name you see and the id you type are
the same.

## Prior art

Borrow rule: ideas from anyone; text or code only from permissive licences, with credit. Nothing needs to be copied
verbatim; the borrowings are patterns.

| Project or feature | What it does | What was borrowed | Licence |
| --- | --- | --- | --- |
| **away-loop** | an overnight loop on the approved plan | the whole operating frame: heartbeat, re-arm, stale tick, table, full report, traps, never list | Apache-2.0 (this repo) |
| **Claude Code scheduled tasks** (`CronCreate`, `/loop`), [docs](https://code.claude.com/docs/en/scheduled-tasks.md) | session-scoped recurring prompts; idle-only; expire | the engine; the expiry as a bound; off-peak minutes | product feature |
| **Claude Code `/loop` built-in prompt and `loop.md`** | "continue unfinished work, tend the PR, run cleanup passes" | the order: unfinished work, then the PR, then new work. Not the idle cleanup passes | product feature |
| **Claude Code `/goal`**, [docs](https://code.claude.com/docs/en/goal.md) | a separate small model judges a completion condition after each turn | completion decided by a fresh model rather than the one doing the work: the reviewer-decides-done rule; its stop on "no tool use for several turns" as the no-progress rule | product feature |
| **Claude Code skill hooks**, [docs](https://code.claude.com/docs/en/hooks.md) | a skill registers `PreToolUse` hooks when invoked | the possible later mechanical lock on class D | product feature |
| **Claude Code cloud scheduled tasks**, [docs](https://code.claude.com/docs/en/routines.md) | cloud runs on a schedule; `claude/`-prefixed branches | the branch marker as a fence; branch protection as the real lock on default branches | product feature |
| **Ralph technique** (Geoffrey Huntley), [post](https://ghuntley.com/ralph/) | a shell loop re-feeding one prompt | "one item per loop"; state in files; tests as backpressure; search before assuming something is missing. His own caveat (greenfield, expect broken builds) is why this adds PR fences and review | post: ideas only |
| **`ralph-loop` plugin** (Anthropic), [repo](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-loop) | Ralph inside one session through a Stop hook | an iteration bound as "your primary safety mechanism"; proof that a plugin can ship a hook. Not the Stop-hook engine | Apache-2.0 |
| **frankbria/ralph-claude-code**, [repo](https://github.com/frankbria/ralph-claude-code) | Ralph with exit detection and rate limiting | the circuit-breaker numbers (3 no-progress, 5 same-error); the two-signal exit; a readiness score for imported issues; handling the 5-hour limit as its own state | MIT |
| **AnandChowdhary/continuous-claude**, [repo](https://github.com/AnandChowdhary/continuous-claude) | a loop that opens PRs, waits for checks, merges | it will not start without a bound (runs, cost or duration); a shared notes file between iterations; a reviewer pass per iteration; a stall threshold that pauses for a human. Not its auto-merge | MIT |
| **snarktank/ralph**, [repo](https://github.com/snarktank/ralph) | Ralph over a `prd.json` of stories | "highest priority story where passes: false"; items small enough for one context; an append-only learnings file; "CI must stay green" | MIT |
| **mikeyobrien/ralph-orchestrator**, [repo](https://github.com/mikeyobrien/ralph-orchestrator) | Ralph with roles, gates and a human channel | gates that reject incomplete work; the human can steer mid-loop without stopping it | MIT |
| **Anthropic, Effective harnesses for long-running agents**, [post](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | an initializer plus a coding agent across many sessions | every session starts by reading the log and the progress file; the feature list is editable only by status; one feature at a time; never remove or edit tests | article: ideas only |
| **Anthropic, Harness design for long-running application development**, [post](https://www.anthropic.com/engineering/harness-design-long-running-apps) | planner, generator, evaluator | a separate skeptical evaluator; "done" agreed before the work; add structure only when needed | article: ideas only |
| **Anthropic, Measuring AI agent autonomy in practice**, [post](https://www.anthropic.com/research/measuring-agent-autonomy) | usage data on autonomy | experienced users auto-approve more and interrupt more: oversight by monitoring and intervening is this design's model; "only 0.8% of actions appear to be irreversible", so fence those few hard | article: ideas only |
| **Cursor, Scaling long-running autonomous coding**, [post](https://cursor.com/blog/scaling-agents) | many agents for weeks | "periodic fresh starts to combat drift and tunnel vision"; a judge decides whether to continue each cycle | article: ideas only |
| **GitHub Copilot cloud agent**, [docs](https://docs.github.com/en/copilot/responsible-use/copilot-cloud-agent) | an agent that works behind a PR | it "can only push to a single branch"; its work arrives as a pull request; "You should review all outputs generated by the agent thoroughly prior to merging" | product docs: ideas only |
| **OpenAI Codex approvals**, [docs](https://learn.chatgpt.com/docs/agent-approvals-security) | approval presets and a sandbox | named autonomy presets instead of a free-form dial; a reviewer agent in front of the human | product docs: ideas only |
| **OpenHands security analyzer**, [docs](https://docs.openhands.dev/sdk/guides/security) | risk-labelled actions | low, medium, high plus unknown, with unknown confirmed by default: the "one class up when unsure" rule | repo MIT; docs: ideas only |
| **Devin 2.1 confidence**, [post](https://cognition.com/blog/devin-2-1) | a confidence rating; waits when unsure | a confidence field on each entry; low confidence raising the class | product blog: ideas only |
| **AutoGPT**, [Wikipedia](https://en.wikipedia.org/wiki/AutoGPT) | the 2023 open-ended agent | the negative lessons: loops without a halt condition, goal drift, bills. Set a success condition, a halt condition and a budget before starting | nothing to copy |
| **MADR**, [repo](https://github.com/adr/madr) | a decision-record template | the entry's spine: context, options, outcome, consequences | MIT or CC0-1.0 |

What does not seem to exist, from one search: a loop whose first-class output is a reviewable ledger of its own
decisions, each with a diagram, an example and an undo, with defined veto handling. The nearby tools either block
before acting (approval inboxes) or act and leave the reader to the diff. That is a hypothesis from a thin search,
not a proven gap.

## Files

| File | What it is |
| --- | --- |
| [SKILL.md](SKILL.md) | the procedure's core, short enough to survive a compaction: the loop-state marker, the never list, the phrases, the class rule, the tick outline and where each step reads more |
| README.md | this page |
| [references/start-and-charter.md](references/start-and-charter.md) | the four gates, the charter, arming and the todo-file template |
| [references/tick.md](references/tick.md) | every tick step in detail, the pick rule, the re-arm and the beats |
| [references/decisions-and-ledger.md](references/decisions-and-ledger.md) | the class examples, the dependency guardrails and the ledger |
| [references/review-and-veto.md](references/review-and-veto.md) | the digest, the verdicts, the veto and its cascade |
| [references/updates.md](references/updates.md) | postures, the gauge line, the table and the full report |
| [references/limits-and-drift.md](references/limits-and-drift.md) | the limits, drift, traps and what it does not do |
| [references/wind-down.md](references/wind-down.md) | stopping, pausing and ending, with the clean-up listing |
| [references/routing.md](references/routing.md) | the phrase routing and the hand-offs |
| [references/ledger-entry.md](references/ledger-entry.md) | the decision-ledger entry template, with a class B and a class A example and what the review line becomes |
| [references/shared-with-away-loop.md](references/shared-with-away-loop.md) | the parts copied from away-loop (re-arm sequence, scheduling check, stale-tick rule, status table, full report, traps), with what changed for this skill |

It has no script, so it has no tests and no test record.
