---
name: away-loop
description: Keep a session working, visibly, while the user is away for hours (overnight, travel, a long meeting). It schedules a 30-minute wake-up, works the open items in order, decides minor things and logs them, queues what only the user can decide, posts a short status table on each tick and a full status report with diagrams every couple of hours and at each milestone, and stops when the user is back with one summary. Use when the user says "I'm going to sleep", "keep working while I'm away", "proceed while I sleep", "work overnight", "I'm stepping away for a few hours", or asks the session to carry on without them. Also use when the user returns ("I'm back", "good morning", "back online") to stop the loop and give the summary.
---

# Away loop

**If this session's todo list has a `## Loop state:` heading that is ARMED or PAUSED (owned by another skill), never arm, and do not stop that loop.**

- A phrase on the heading's `Answers:` line goes to that loop and only changes its posture.
- While the heading is ARMED, every arming phrase of this skill's goes to that loop too, whether or not the line
  lists it, in any wording: invoke the owner skill the heading names and let it answer, so it knows the user is
  away. Never arm.
- While the heading is PAUSED, an arming phrase does not arm and gets one line whether or not it is listed: say in
  one line which loop owns the session and how to stop or resume it, then stop.
- This skill's other phrases stay yours as usual.

A consumed away plan is not a loop.

The user is gone for hours, and the work should not stall at the first thing that needs them. This skill
turns "keep going while I'm away" into a procedure. A wake-up every 30 minutes keeps the session moving.
Each tick does the next unblocked step, decides what the agent may decide, and queues what it may not.
The loop stops the moment the user is back, and they get one summary instead of scrolling through the night.

```
 start ──► plan in the todo file ──► schedule the wake-up ──► tell the user the plan
   │
 tick (every 30 min) ──► plan consumed? ──yes──► delete own job, stop
   │ no
   ▼
   job older than 6 days? ──yes──► create new job ► record it ► delete old job ► CronList: one job
   │ no                          (CronCreate fails: keep the old job, say when the wake-up ends)
   ▼
   machine + agents + PRs ──► next unblocked step ──► log decisions, queue the rest ──► status table
                                (about every 2 hours, or at a milestone: the full report instead)
 stop (the user is back, or the end time) ──► delete every recorded job, check CronList ──► summary
```

The plan and the queue live in the session's todo-sync list, so this skill needs the `todo-sync` skill installed.
That skill says where the list is: wherever this skill says "the todo file", find it the way `todo-sync` does, and
never assume a path. If `todo-sync` is not available, say so before the user leaves, and keep the plan in a file
the user names, or in the project's own planning doc; "the todo file" then means that file. The `checkpoint` skill
is optional. When the user is about to restart or quit, use `checkpoint` instead of carrying on.

Scheduled tasks are scoped to the session: they belong to the session that created them, and Claude Code restores
them when that session is resumed (unless they expired). The rules below are this skill's defaults. A project's own
rules for review, merging, heavy work or reports override them.

## Part 1: start

Write every time with `date +%Y-%m-%dT%H:%M%z`, so a later tick can compare it with another.

1. **Write the plan into the session's todo file** (the list `todo-sync` keeps for this session; it knows where
   that is, including a list started before its folder existed), at the top, in three sections:
   - **Away plan:** a header line with the start time, the wake-up ids and times, `last full report: <time>`
     (the start time at first) and `held: 0`; then the open items in the order they will be worked, each with its branch, PR,
     file or command, and its next step. Highest value first; items that need a reviewer or CI to finish go before
     items that need many installs.
   - **Decisions made while away:** empty for now. Each entry gets the time, the decision and the reason.
   - **Waiting for you:** empty for now. It holds every item that needs the user.
2. **Check that scheduling exists, before the user leaves.** If `CronCreate` is not in the tool list, or the call
   in step 4 is refused (the scheduler can be turned off with `CLAUDE_CODE_DISABLE_CRON=1`), say so plainly: this
   session cannot wake itself, so nothing will run while the user is away. Never pretend the loop is armed. Offer
   what is possible: work until the current step is done, then stop with a summary. Do not continue with steps 3
   to 5 as if a wake-up existed. A task already in `CronList` is not evidence that the scheduler works: arm the
   loop only when `CronCreate` has succeeded.
3. **Check the existing wake-ups** (`CronList`; a session holds up to 50 tasks). If an away-loop job (prompt
   starting "Away-loop") already exists for this session's plan, adopt it: record its id and creation time, and
   do not create another. If it belongs to a plan already marked consumed, delete it. Pick minutes that no other
   wake-up uses and that are not :00 or :30, which other jobs favour: for example the cron expression
   `3,33 * * * *` for the 30-minute tick.
4. **Schedule the wake-up:** `CronCreate`, recurring, with the tick prompt below. If it is refused or fails, go
   back to the message in step 2 and stop here. If it succeeds, record its id and creation time in the todo file
   at once. If the user gave a return time, also schedule a one-shot at that time with the return prompt below,
   pinned to a minute that is not :00 or :30 (Claude Code's scheduled-tasks documentation says one-shots on those minutes can fire
   up to 90 seconds early), and record its id and time too.
5. **Tell the user, in a few lines** (only after step 4 succeeded):
   - what will run;
   - what stays theirs (see "Never while away");
   - when the summary comes, and when the full reports come (about every 2 hours, and at each milestone);
   - that the loop stops on their first message;
   - that ticks fire only while Claude Code is running and idle: while the machine sleeps or the app is closed,
     Claude Code is not running, so nothing fires until it runs again.

The tick prompt, stored with the wake-up. Its first words, "Away-loop tick", are how the agent tells a tick from
the user's own first message; a message that starts with them is a tick, and anything else means the user is back:

```text
Away-loop tick (the user is away; they asked to keep working). Follow the away-loop skill, Part 2: read the
Away plan, Decisions and Waiting sections of this session's todo file; act on finished agents and checks;
start the next unblocked step; decide minor things and log them; queue the rest; keep the repo record
current; reply with one status table, no repetition of earlier ticks. When about 2 hours have passed since
"last full report", and whenever a milestone or phase completes, give the full status report instead
(Part 2, "The full status report").
```

The return prompt, stored with the one-shot:

```text
Away-loop return: if the loop is still running, stop it and write the summary (the away-loop skill, Part 3); if
it already stopped, do nothing.
```

## Part 2: each tick

0. **Check the plan, then re-arm if the job is old.**
   - If this session's todo file has no Away plan, or the plan is marked consumed, this tick is stale (for
     example a job restored with a resumed session: Claude Code's scheduled-tasks documentation says resume restores tasks that have not expired).
     Delete this job with `CronDelete`, say so in one line, and stop.
   - Recurring jobs expire after a fixed time, firing once more and then deleting themselves: 7 days after
     creation on Claude Code versions before 2.1.330, 30 days from 2.1.330 on. Re-arm after 6 days, which is safe
     for both. If the recorded creation time is more than 6 days ago, re-arm in this order: create the new recurring job with the same tick
     prompt; record its id and creation time in the todo file at once; delete the old job with `CronDelete`; run
     `CronList` and confirm exactly one recurring away-loop job remains.
   - If `CronCreate` fails (scheduler off, permission refused, a task limit), keep the old job. Write "wake-up
     ends when the old job expires (7 or 30 days after <old creation>, by version); could not re-arm" in the status table and in "Waiting for you". Never claim
     the loop continues past that time.
1. **Hold heavy work while the machine is loaded.** The load line is the 5-minute load average against about 70%
   of the machine's cores, rounded and shown as a number (7 on a 10-core machine). Read the load, free disk and
   memory pressure together, on their own, with the result seen before any builder, install or other heavy step
   starts. Over the line, or with memory pressure reported, or while another job holds the project's heavy-work lock
   (if it has one), the tick does bookkeeping only (no builder, build, test run or install), and a running job
   finishes. Keep `held: <n>` in the Away plan header: add 1 for each tick held, reset it to 0 when the load
   clears. At `held: 4`, say so once: the load, the line and the options (wait, stop other work, raise the line);
   then one "held" line per tick until it clears. Never go silent. Installs also wait while free disk is under 5
   GiB, or the project's own floor. A project's own written rules on heavy work win; otherwise only the user's
   words change the line.
2. **Act on what finished.** For each subagent that reported, take its next step: a fix round, or, by default, one
   final verdict per phase.
3. **Check every PR this session opened:** CI state and new reviews. Each new comment gets a fix or a reasoned
   reply, then its thread is resolved; one only the user can answer is queued for them.
4. **Start the next unblocked step** from the Away plan, with at most two install-heavy builders at once. Every builder brief ends
   with the time budget (about twice the step's normal run), "never start subagents" and four lines: commit only when the gate itself passes; never
   disguise code to get past a check; stop every process you started; never print a secret or another process's
   command line.
5. **Decide what you may decide:** minor design choices, wording, test shape, the order of work, a severity.
   Log each one in "Decisions made while away", with its time and the reason.
6. **Queue what you may not decide.** Get it ready first: open the PR, or write the options with a
   recommendation. Then add it to "Waiting for you" and move on.
7. **Keep the repo record current:** the project's tracker or roadmap, through its normal branch.
8. **Reply with one status table**, new information only:

   | | |
   |---|---|
   | Finished | what completed, with full PR links |
   | Started | what began, and why it was next |
   | Decisions | what you decided and why, in a line each |
   | Running | agents and background jobs still going |
   | Blockers | what stops progress, and what would unblock it |

   A tick with nothing new says so in one line; it does not restate the night.

   Ticks start cold and missed ticks collapse into one fire, so a tick count is unreliable. When about 2 hours have
   passed since the time on the `last full report` line in the Away plan header, whenever a milestone or phase
   completes, and whenever the user asks, give the full status report below instead of the table, and update that
   line.

### The full status report

The table says what moved in the last half hour. The full report says where the whole initiative stands, so the
user can catch up in one read and decide what to unblock. It has seven sections, in this order:

1. **The state in one line**, then **where we are:** a figure of the initiative's phases with a "WE ARE HERE"
   marker and the target date (EXPECTED).
2. **The build:** a table of the current milestone's parts, one row each, with a column per step the project's
   cycle has (built, reviewed, fixed, checked, PR, checks passed, merged), then one progress bar per milestone with its
   count (MEASURED from the repository).
3. **The merge queue:** a figure of the open PRs and how they stack, each marked with its check state, then the full
   link of every PR in it.
4. **Since the last full report:** a table of the work and its state, with full links. Merges, decisions taken
   with the user, and anything that went wrong and how it was handled.
5. **Time to completion:** a figure with the measured pace, the pace the target needs, what is ahead of or behind
   it, and an optimistic and a realistic date. Pace is DERIVED from a MEASURED count; the ranges are JUDGMENT.
   Name the bottleneck.
6. **What is left** before the next milestone, in order.
7. **What is needed from the user,** in priority order, each with the exact words that unblock it ("merge 37 48",
   "clean the cache"), and what each unblocks.

The rules that make it trustworthy:
- **Nothing else goes in.** No restating of earlier ticks, and no item without a link or a number behind it.
- **Diagrams are ASCII**, placed before the prose they explain, and every one is labelled MEASURED, DERIVED or
  EXPECTED. The labels mean: MEASURED, counted from the repository or GitHub now; DERIVED, calculated from measured
  numbers; EXPECTED, a forecast. A range you chose is labelled JUDGMENT.
- **Every count comes from the repository or GitHub at the time of writing**, never from memory of an earlier tick.
  Run `date +%Y-%m-%dT%H:%M%z` for the time on the heading.
- **Every PR and doc is a full clickable link**, never a bare `#N`.
- **Save it where the user can find it later:** if the project keeps a progress folder, write the
  report there as `YYYY-MM-DD-HHMM-status.md`, so a listing sorts by time.
  Commit it on the project's normal branch for docs and push it. A saved report is a snapshot and is never edited.
  If the project has no such folder, offer to start one the first time.

### Never while away

By default these stay the user's, however blanket the go sounds (a project's own rules may be stricter). Queue
them, do not do them:
- merging a PR, unless the user named that exact PR;
- any delete: files, branches the user did not create, resources, data;
- writes to production systems or databases;
- changes to settings, `CLAUDE.md` or `AGENTS.md`;
- big decisions: architecture, security boundaries, public contracts, scope.

## Part 3: stop

The loop ends on the user's **first message back**, or at the end time if one was set.

1. **Delete the wake-ups** first. Run `CronList`, delete every recorded id (the recurring job and the one-shot)
   with `CronDelete`, and also delete any listed task whose prompt starts with "Away-loop". Then list again and
   confirm none remain. Leave other loops running: release watches and project wake-ups have their own owners.
2. **Re-check the sources before summarising.** PR states, CI and production move while the user sleeps; the todo
   file describes the moment it was written.
3. **Give one summary**, in this order (after a run of more than about 4 hours, or one that crossed a
   milestone, give it as the full status report, with these items inside its sections):
   1. what changed in production or the shared systems (anomalies with numbers, resolved or open);
   2. what needs the user, in priority order, each with the exact next action;
   3. the PRs opened or moved, as a table with full links and state;
   4. the decisions taken while away, so the user can overturn any of them;
   5. drafts waiting to be sent;
   6. what is next.
4. **Mark the Away plan consumed** in the todo file (a job that fires later then finds it and deletes itself). Carry every open item into the normal list, and drop
   nothing (`todo-sync`).

## Traps

- **A permission denial is a queue item.** When the harness or its classifier refuses an action, do not route
  around it. Put it in "Waiting for you" with what it was for.
- **A wake-up is a heartbeat, not a deadline.** A recurring job can run up to half its period late. It lives in
  the session: it fires only while Claude Code is running and idle, so it stops when the session exits, and while the
  machine sleeps Claude Code is not running, so nothing fires. It also expires, 7 days after creation on versions before 2.1.330 and 30 days from it (see
  "Part 2: each tick", step 0).

## When it cannot conclude

- **Everything left needs the user:** say so on the next tick, keep ticks to one line, and keep the summary ready.
- **The machine is over its line** (step 1): hold heavy work, let the running ones finish, and queue any cleanup
  the user must approve.
- **The session is about to end** (a restart, a context limit): run `checkpoint` so the next session can resume.
- **The user returns mid-tick:** finish the step in flight only if stopping halfway would leave a broken state.
  Otherwise stop and summarise.

## What it does not do

- It does not run while Claude Code is not running (the machine asleep, the app closed) or after the session exits.
- It does not wake a session that has no scheduling tools; it says so before the user leaves.
- It does not widen what the user approved. A blanket "do what you need to" does not reach merges, deletes or
  settings.
- It does not replace the project's own trackers. It points the user at them.
