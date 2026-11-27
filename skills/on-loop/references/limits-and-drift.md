# Limits, stop rules, drift and traps

Read at tick steps 1 and 7. Every default is a line in the charter the user can change in words; the loop cannot.
At a limit it does one of three things:

```
 QUIET   start no new item; keep open PRs green; answer review comments; quiet beat (60 minutes)
 PARK    leave one item alone, queued with diagnostics; move to the next
 STOP    wind down (wind-down.md). Only the user restarts it.
```

| # | Limit | Default | At the limit |
| --- | --- | --- | --- |
| 1 | **Lifetime** | the charter's 7 days from the start | renewal asked on day 5 and day 6; with no renewal, STOP at the end |
| 2 | **Silence** | no message from the user for 24 hours | QUIET at 24 hours, STOP at 72 |
| 3 | **Fix rounds on one item** | 3 (doc-only and tracking edits made after the final verdict do not count) | PARK the item with the failing output and the last verdict ("Fix rounds, and parking after a failed verdict" below) |
| 4 | **The same failure** | the same check or error 3 times on one item; 5 times across items | PARK; at 5, STOP |
| 5 | **No progress** | 3 **attempted** work beats in a row with no commit, no PR change and no decision | STOP, with what it was trying. A beat does not count when it yielded to the user, was held by disk or load, waited on the user or CI, or while a builder runs inside its budget |
| 6 | **Parked items** | 3 parked in a row | STOP (the roadmap or the environment is wrong) |
| 7 | **Roadmap exhausted** | done, or every remaining item has an allowed blocker reason (tick.md step 13); an item merely not yet started is not blocked | QUIET; draft "what could come next" as a proposal for the user's yes; never invent work |
| 8 | **Usage limit reached** | Claude Code reports a usage limit | carry on at the next tick after the reset; no gauge, no guess |
| 9 | **Disk** | free space under the project's install floor, or 5 GiB when it has none | no installs or builds; bookkeeping only for the tick (reported once at start, once at clear); queue the cleanup (never delete to make room; only dependency folders and build output it produced in its own worktree may go) |
| 10 | **Load and memory** | the 5-minute load average above the charter's load line (default about 70% of the cores, shown as a number), or memory pressure reported | the tick takes no heavy step (no build, test run, install or subagent): bookkeeping only (ledger, review replies, state line, todo list), reported once at start, once after about 4 held beats in a row and once at clear; let the running job finish ("Holding for load" below) |
| 11 | **Stray processes** | every job it starts has a budget of about twice its normal run | stop it by PID (a polite signal, then forced) at the budget; after every agent's report, and before each report of its own, list the processes whose working directory is in its worktrees (PID, parent, age, CPU, working directory only) and stop its own strays |
| 12 | **Context** | a compaction, or a restart | invoke the skill again; re-read the state from the files; todo-sync's recovery if the list looks short; for a restart, `checkpoint` |
| 13 | **Items in flight** | the charter's line, default 2; one heavy job at a time | wait |

There is no cap on how many decisions or pull requests wait for the user, no depth limit on stacking, no usage gauge
and no active hours: the loop works whenever its session is open and idle. The loop never stops itself because work
or review is piling up, or because usage ran out; it stops only for the bounds the user set (lifetime, silence) or
those that say the loop itself is lost (no progress, the same failure, parked items), and it says why.

**Drift** is held down by: one step of one item per tick; every branch, commit and PR naming its item; the boundary
written before the first commit; the roadmap re-read on every tick with its commit recorded; no drive-by refactor,
upgrade or cleanup (a good idea becomes a proposal); a second opinion on "done"; a fresh start at each renewal.

**The drift table** goes in every full report. A non-zero row means stop and ask: start no new step on the
affected item, queue a class C entry naming the row and what was found, and carry on with other items.

```text
 commits not tied to a roadmap item                           0
 files changed outside the item's stated boundary             0   (a justified one is a logged decision)
 items worked out of roadmap order without a logged reason    0
 roadmap changed since the last re-plan (by anyone)           no  (yes: re-read, re-plan, record the new commit)
 tests deleted, skipped or loosened                           0   (a changed expectation is a class B entry)
```

**The user's own work wins at once.** Before picking, list the repo's worktrees, branches and open PRs; if the user or
another session has changes in the same files, take a different item or queue this one. A project's heavy-work lock
is honoured.

## Holding for load

The load line is a charter field. It is a number of cores read against the **5-minute** load average, so a short
spike (another repo's CI runner, the user's own sessions, this session) does not hold the loop for an afternoon.
The default is about 70% of the machine's cores, rounded and shown as a number (7 on a 10-core machine); only the
user's words change it.

- **Read the load alone.** One command, its result seen before any builder or heavy step starts; never in the same
  parallel batch as the start.
- **After about 4 held beats in a row (the `held beats` counter, reset when the load clears), say so once:** the 5-minute load, the busiest processes (PID, CPU and working
  directory only; "this session" when it is the session itself, since holding cannot help then), and the options:
  wait, stop the other work, or the user's words to raise the line. Then do not repeat that message until it clears; each held tick still posts its one held line.
- **A builder that started over the line:** stop it (TaskStop, or the tool that started it); confirm its worktree is clean and that
  no process of it is left. If anything is uncommitted, leave it in place and name it in the restart brief; the
  restarted builder decides with the gate (commit only when the gate itself passes). Queue the same brief; restart it at
  the first tick under the line.

## Fix rounds, and parking after a failed verdict

A fix round is one build-and-check pass after a failed check or a "not done" verdict; a code change is a round.
After the final verdict, edits that fix doc drift it found or add follow-ups to other roadmap rows change no
behaviour and are not rounds. When the third round ends with a verdict still "not done": push the branch and open no
new PR (if one exists, comment on it with the blockers and leave it open; no draft PRs), write a class C entry in
"Waiting for you" with the blockers verbatim, the options (finish by hand, change the item's scope, drop it) and the
exact words that unblock it, mark the item parked, with the reason, in the todo file's Roadmap view (the roadmap file itself changes only through a pull request, so none is opened for a parked item; a follow-up for a
parked dependency is different: see tick.md step 8), and move to the next item.

## Traps

The away-loop's one trap this loop depends on (a wake-up is a heartbeat, not a deadline) is in
[shared-with-away-loop.md](shared-with-away-loop.md). The traps of this loop:

- **A roadmap file is not an approved roadmap.** The charter records the yes and the commit.
- **Rubber-stamping.** "Keep all" on twenty entries: flagged entries cannot be bulk-kept; roots come first.
- **The loop widening itself.** "The limit is in the way" is not a reason; changing the charter is class D.
- **A stale tick after a resume.** Step 0 deletes the job.
- **Counting from memory.** Counts come from `grep` on the ledger and from GitHub.
- **Leftover processes.** A watcher or test run that outlives its tick or its builder: budget, PID, list before each report.
- **Reading a stop into other words.** Only "stop the loop" stops it.
- **Working a stale claim.** Report it; taking it over needs the user's word.

## When it cannot conclude

- **Everything left needs the user:** once the blocker table shows an allowed reason on every row, the quiet beat, the table in the first reply and then one-line ticks that point to it, the digest ready, naming the one decision whose
  review unblocks the most.
- **The machine is out of bounds:** stop starting builders, finish or pause the running ones, queue the cleanup.
- **The session is about to end** (a restart, a context limit): run `checkpoint` when installed; otherwise write the
  state into the todo file. A resumed session restores the job only if the marker allows it (SKILL.md section 1).
- **A class is unclear:** one class up. **A rule is unclear:** the stricter reading, and say so.
- **The list looks shorter than the work:** recover (todo-sync's recovery), never rewrite from memory.

## What it does not do

- It does not run while Claude Code is not running, or after the session exits; it says so before arming.
- It does not merge, publish, deploy, spend or change settings, and deletes only the worktrees and branches of its own merged or closed PRs.
- It ships no hook. One is added only if real use shows a slip, and then as a settings change on the user's go.
- It does not read plan usage, notify outside the session, invent roadmap work or rewrite the roadmap's text, order
  or checks, run `crossfire` (a separate skill) or any eval, or widen what the user approved.
- It does not replace the project's own trackers; it points the user at them.
