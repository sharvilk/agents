# Parts shared with away-loop

Origin: the `away-loop` skill. These blocks are copied from it, with the changes named below, so that the two skills
behave alike where they should. **They exist twice.** When `away-loop` changes one of them, check this file in the
same change, and the other way round. If the two ever drift a second time, that earns a check that diffs these
blocks. (The first drift would be a fix; the second is a gate.)

## The re-arm sequence (away-loop, Part 2, step 0)

Recurring jobs expire after a fixed time, firing once more and then deleting themselves: 7 days after creation on
Claude Code versions before 2.1.330, 30 days from 2.1.330 on (jobs created on the older versions keep the 7). Re-arm
after 6 days, which is safe for both. In this order:

1. create the new recurring job with the same tick prompt;
2. record its id, creation time and speed in the todo file at once;
3. delete the old job with `CronDelete`;
4. `CronList` and confirm exactly one recurring job of this loop remains.

If `CronCreate` fails (scheduler off, permission refused, a task limit), keep the old job, write "wake-up ends when
the old job expires; could not re-arm" in the report and in "Waiting for you", and never claim the loop continues
past that time.

Changed for the on-loop (details in tick.md, step 2): the sequence is also used to **switch speed** (work beat to quiet beat) and **at a
renewal**; and it is **never used to outlive the charter** (7 days, the user's renewal needed). The charter's length
is a decision of the user and does not follow the job's expiry.

## The scheduling check (away-loop, Part 1, step 2)

If `CronCreate` is not in the tool list, or the call is refused (`CLAUDE_CODE_DISABLE_CRON=1` turns the scheduler
off), say so plainly: this session cannot wake itself. Never pretend the loop is armed. A task already in
`CronList` is not evidence the scheduler works. Offer one bounded run. No change for the on-loop.

## The stale-tick rule

A tick that finds no plan, or a plan marked consumed (for example a job restored with a resumed session), deletes
its own job, says so in one line and stops. Changed: "no marker, or the marker says ENDED or PAUSED"; a marker that says ARMED while its job is missing gets
one line and an offer to re-arm, never a silent delete or re-create; the prefix is "On-loop tick" (away-loop's is
"Away-loop tick").

## The status table (away-loop, Part 2, step 8)

| | |
|---|---|
| Finished | what completed, with full PR links |
| Started | what began, and why it was next |
| Decisions | what was decided and why, a line each |
| Running | agents and background jobs still going |
| Blockers | what stops progress, and what would unblock it |

Changed: Started also names the roadmap item; Decisions give id, class and one line, flagged ones marked; one more
row, **Limits**, shown only when something is within 20% of a bound.

## The full status report (away-loop, "The full status report")

Seven sections, in this order:

1. the state in one line, and where we are (a figure of the phases with a "WE ARE HERE" marker, EXPECTED);
2. the build: a table of the milestone's parts with a column per step, and a progress bar per milestone (MEASURED);
3. the merge queue: a figure of the open PRs and how they stack, each marked with its check state, then every full
   link;
4. since the last full report: the work and its state, with full links;
5. time to completion: the measured pace, the pace the target needs, an optimistic and a realistic date (pace is
   DERIVED from a MEASURED count; the ranges are JUDGMENT); name the bottleneck;
6. what is left before the next milestone, in order;
7. what is needed from the user, in priority order, each with the exact words that unblock it.

Changed: after section 4, **Decisions** (counts by class and status, flagged ones a line each); after section 5,
**Drift and budget** (the drift table and every limit's current value).

Rules, unchanged: nothing else goes in; diagrams are ASCII, before the prose, labelled MEASURED, DERIVED or
EXPECTED; every count comes from the repo or GitHub at the time of writing; every PR and doc is a full link; the
cadence is elapsed time (about every 2 hours from `last full report`), because ticks start cold and missed ticks
collapse into one fire; save it as `YYYY-MM-DD-HHMM-status.md` in the project's progress folder, a snapshot never
edited.

## The traps (away-loop, "Traps")

- Future timestamps in docs: run `date +%Y-%m-%dT%H:%M%z` and write the time it is.
- "Merge-ready" with open review threads.
- Disk runs out quietly: check before each install, set a stop line. The on-loop may remove the dependency folders
  and build output it installed or produced in its own worktree right after the checks (its own change,
  regenerable); a shared cache or anything outside its worktree it only lists for the user.
- External outages look like your bug: check the provider's status page; trigger a fresh pipeline on the head after
  a recovery.
- A permission denial is a queue item: do not route around it.
- Never `sleep` in the foreground to wait.
- Subagents report confidently wrong things: check with git or a read-only probe, with a control that must succeed.
- A wake-up is a heartbeat, not a deadline: up to half its period late; fires only while Claude Code is running and
  idle; expires.

Changed for the on-loop: all kept, named here once. "Never while away" becomes the class D list in the skill's
section 2, extended with publishing, spending, default branches, the loop's own limits and deleting or weakening a
test. The traps new to the on-loop are in limits-and-drift.md.
