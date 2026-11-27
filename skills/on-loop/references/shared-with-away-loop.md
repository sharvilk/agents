# Parts shared with away-loop

Each skill installs on its own, so the blocks below are **copies** of text in the `away-loop` skill's `SKILL.md`, set
between a "copied from" comment line and an "end of copy" comment line, and kept word for word. What the on-loop changes
is written after each block, outside the copy. When `away-loop` changes a copied block, change it here in the same
change, and the other way round. Nothing checks yet that the copies match: the first drift between them is fixed by
hand, and a second earns a check that diffs these blocks.

| Block | Copied from `away-loop/SKILL.md` |
| --- | --- |
| The re-arm sequence | Part 2 ("each tick"), step 0, the second and third bullets |
| The scheduling check | Part 1 ("start"), step 2 |
| The stale-tick rule | Part 2, step 0, the first bullet |
| The status table | Part 2, step 8, the table |
| The full status report | the section "The full status report", without its heading |
| The wake-up trap | "Traps", the bullet "A wake-up is a heartbeat, not a deadline" |

Nothing else is copied from the away-loop. The general practice of a long unattended run (future timestamps, outages,
sleeping in the foreground, trusting a confident subagent) is not part of either loop. This loop's own limits on disk
and load are in [limits-and-drift.md](limits-and-drift.md), and a refused permission is a queue item, never worked
around (SKILL.md section 2).

## The re-arm sequence

<!-- copied from away-loop/SKILL.md: Part 2, step 0, second and third bullets -->
- Recurring jobs expire after a fixed time, firing once more and then deleting themselves: 7 days after
  creation on Claude Code versions before 2.1.330, 30 days from 2.1.330 on. Re-arm after 6 days, which is safe
  for both. If the recorded creation time is more than 6 days ago, re-arm in this order: create the new recurring job with the same tick
  prompt; record its id and creation time in the todo file at once; delete the old job with `CronDelete`; run
  `CronList` and confirm exactly one recurring away-loop job remains.
- If `CronCreate` fails (scheduler off, permission refused, a task limit), keep the old job. Write "wake-up
  ends when the old job expires (7 or 30 days after <old creation>, by version); could not re-arm" in the status table and in "Waiting for you". Never claim
  the loop continues past that time.
<!-- end of copy -->

Changed for the on-loop (details in tick.md, step 2): the sequence is also used to **switch speed** (work beat to
quiet beat) and **at a renewal**; and it is **never used to outlive the charter** (7 days, the user's renewal needed).
The charter's length is a decision of the user and does not follow the job's expiry. The on-loop writes the
could-not-re-arm message in its report, not in a status table. In it, "away-loop job" reads "on-loop job", and the
parenthetical "(7 or 30 days after <old creation>, by version)" is left out.

## The scheduling check

<!-- copied from away-loop/SKILL.md: Part 1, step 2 -->
2. **Check that scheduling exists, before the user leaves.** If `CronCreate` is not in the tool list, or the call
   in step 4 is refused (the scheduler can be turned off with `CLAUDE_CODE_DISABLE_CRON=1`), say so plainly: this
   session cannot wake itself, so nothing will run while the user is away. Never pretend the loop is armed. Offer
   what is possible: work until the current step is done, then stop with a summary. Do not continue with steps 3
   to 5 as if a wake-up existed. A task already in `CronList` is not evidence that the scheduler works: arm the
   loop only when `CronCreate` has succeeded.
<!-- end of copy -->

No change for the on-loop, except that "step 4" there is this skill's Arm step 1 (`CronCreate`), and the steps it
says not to continue with are the arming steps that follow it.

## The stale-tick rule

<!-- copied from away-loop/SKILL.md: Part 2, step 0, first bullet -->
- If this session's todo file has no Away plan, or the plan is marked consumed, this tick is stale (for
  example a job restored with a resumed session: Claude Code's scheduled-tasks documentation says resume restores tasks that have not expired).
  Delete this job with `CronDelete`, say so in one line, and stop.
<!-- end of copy -->

Changed: "no Away plan, or the plan is marked consumed" becomes "no marker, or the marker says ENDED or PAUSED"; a
marker that says ARMED while its job is missing gets one line and an offer to re-arm, never a silent delete or
re-create; the prefix is "On-loop tick" (away-loop's is "Away-loop tick").

## The status table

<!-- copied from away-loop/SKILL.md: Part 2, step 8, the table -->
| | |
|---|---|
| Finished | what completed, with full PR links |
| Started | what began, and why it was next |
| Decisions | what you decided and why, in a line each |
| Running | agents and background jobs still going |
| Blockers | what stops progress, and what would unblock it |
<!-- end of copy -->

Changed: Started also names the roadmap item; Decisions give id, class and one line, flagged ones marked; one more
row, **Limits**, shown only when something is within 20% of a bound.

## The full status report

<!-- copied from away-loop/SKILL.md: The full status report, without its heading -->
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
<!-- end of copy -->

Changed: after section 4, **Decisions** (counts by class and status, flagged ones a line each); after section 5,
**Drift and budget** (the drift table and every limit's current value). The cadence is required in every posture (see
updates.md). Times follow SKILL.md step 10. The on-loop commits a saved report on its log branch, not "the project's
normal branch for docs" (as updates.md says), and "the last half hour" reads "the last beat".

## The wake-up trap

<!-- copied from away-loop/SKILL.md: Traps, the bullet "A wake-up is a heartbeat, not a deadline" -->
- **A wake-up is a heartbeat, not a deadline.** A recurring job can run up to half its period late. It lives in
  the session: it fires only while Claude Code is running and idle, so it stops when the session exits, and while the
  machine sleeps Claude Code is not running, so nothing fires. It also expires, 7 days after creation on versions before 2.1.330 and 30 days from it (see
  "Part 2: each tick", step 0).
<!-- end of copy -->

In the on-loop, the step that pointer names is [tick.md](tick.md) step 2.

Kept as it is. The traps new to the on-loop are in limits-and-drift.md.
