# A tick in detail

Read at each tick. A tick does ONE step of ONE item, then reports. The marker, the beats and the phrases are in
SKILL.md. In order:

**Wake kinds.** A message starting "On-loop tick" is a tick. A notice from the loop's own agent or watcher (a report,
a CI or PR state change) is step 6 work: it never counts as a message from the user and never writes `last user
message`. Anything else is the user, and the first thing done for it is to write that time.

0. **Marker and job.** Read the marker. ENDED, PAUSED or no marker: this tick is stale (a job restored with a
   resumed session): delete this job with `CronDelete`, say so in one line, stop. ARMED: `CronList` and confirm the
   job in the marker exists; if not, say so in one line, offer to re-arm, stop. Never re-arm on one's own.
1. **Stop rules** ([limits-and-drift.md](limits-and-drift.md)): lifetime, silence, no progress, same failure, parked
   items. A stop means [wind-down.md](wind-down.md). **Gap rule:** compare the time now with `last beat`; if more
   than two beats at the current speed passed with no tick (30 minutes on the work beat, 2 hours on the quiet
   beat), say so in the first report after (a gap is reported, not hidden). A tick
   that was due while a question panel was open, or while the user's turn ran, fires right after the turn ends; that
   is a late tick, not a lost one.
2. **Job age and renewal.**
   - Recurring jobs expire after a fixed time, firing once more and deleting themselves: 7 days after creation
     before Claude Code 2.1.330, 30 days from 2.1.330 on. The charter is 7 days either way. The loop never outlives
     its charter without the user's word.
   - **Renewal:** on day 5 and day 6 of the charter, ask for renewal in the report. The user says "renew the loop":
     re-read the roadmap, show any change to the charter, record the new end time (7 days from the renewal), rewrite
     the marker's date, and re-arm (the beats, the one tick prompt and the order are in SKILL.md section 5). Recommend a fresh session at a renewal
     (`checkpoint`, then resume).
   - **Re-arm** when the recorded creation time is more than 6 days ago, at a renewal, and to change speed, as
     SKILL.md section 5 says (create, record, delete the old job, `CronList` shows exactly one on-loop job, update
     the claim). If `CronCreate` fails, keep the old job and write "wake-up ends when the old job
     expires; could not re-arm" in the report and in "Waiting for you". Never re-arm an ended charter, or past its
     end without the user's word.
3. **Yield.** Is a request the user typed still in progress (work for them still running, or a question to them
   unanswered)? End the tick with one held line ([updates.md](updates.md)), and update `last beat`, so consecutive yields do not later read as a gap.
4. **Health:** disk free, load (read in its own command, and its result seen before any builder or heavy step
   starts), memory, the project's heavy-work lock, other sessions, and the user's own branches and worktrees
   (`git worktree list`, branches, open PRs). Note anything out of bounds. **Over a line (load or disk): this tick
   takes no heavy step** (no build, test run, install or subagent) and does bookkeeping only: the ledger, replies to
   review threads, the state line, the todo list. Report it once when it starts and once when it clears, not at every
   tick; after about 4 held beats in a row (the `held beats` counter) say so once more ([limits-and-drift.md](limits-and-drift.md) rows 9 and 10,
   "Holding for load").
5. **Verdicts.** Apply any keep, change or veto the user gave since the last tick ([review-and-veto.md](review-and-veto.md)).
6. **Act on what finished.** For each subagent that reported, take its next step: a fix round, an independent
   reviewer with a scope that does not overlap, or one final verdict per item. Read the diff of every fix yourself;
   a builder's report is a claim, not proof. Check every PR the loop opened: CI, new reviews and unresolved review
   threads. **Reply to every review comment on the loop's own PRs, from anyone**: a fix is class A, declining
   with the reason is class B. A reply in the user's name outside its own PRs' review threads (an issue, someone
   else's PR) is class C: draft it, queue it. **After replying, resolve the thread**: an open
   thread is this step's work signal, so an unresolved one would be answered again, and a PR is not "merge-ready"
   while a thread is open.
   When the user merges a PR whose body lists decisions, mark those entries `accepted (merged <date>)` in the next
   ledger push, never in a PR of its own; an entry that was changed or vetoed keeps its status (`changed → D-…`, `vetoed`). When a PR it
   made is merged or closed, clean up: remove its worktree and delete its branch, locally and on GitHub, once the
   worktree has nothing uncommitted and nothing unpushed. If something is, list the clean-up with the exact commands
   for the user instead. **The ledger branch is the exception**: it is kept after its PR merges, brought up to date by
   merging the default branch, and the next day's ledger PR is opened from it.
7. **Roadmap changed?** Re-read the roadmap from the repo and compare its commit with the one recorded. If anyone
   changed it, say what changed, re-plan before picking, and record the new commit.
8. **Pick** the next item:
   1. finish what is in flight before starting anything (the charter's in-flight line, default two items: a pacing
      limit, never a cap on PRs waiting for the user);
   2. then the roadmap's own order or priority, never the loop's taste;
   3. skip items that are not ready, that wait on an unanswered question or a queued decision **that changes what gets
      built** (one that gates only the merge or a default does not), or that are claimed (an assignee, another branch
      or PR touching it, the user saying "I'm on that"). **An unmerged PR does not block**: the next item may stack on
      it; **a parked item's dependents are not blocked**, see "What does not block building" below;
   4. skip items whose files the user or another session is changing right now;
   5. ties: the item that unblocks the most others, then the smallest.

   Every skip is written down with its reason. **Prefer independent work:** each item on its own branch off the
   default branch with its own PR. Stack when the work needs it: no limit on depth, and stacked PRs are fine to
   review. If a step cannot proceed (it waits on a decision), move in this order: (1) another ready item; (2) other
   work on the same item that does not depend on the pending choice; (3) prepare what is queued (options, a
   throwaway spike); (4) only when none exist, wait and name the one decision whose review unblocks it.
   **What does not block building.** A blocker stops only the part of an item that needs it, never everything
   downstream of it. A parked item's dependents are not automatically blocked: look for the part of each dependent
   that does not need the parked part. Before skipping an item as blocked, find the part that does not need the
   blocker:
   - an unmerged dependency: stack on its branch (the loop never merges it); once the user merges it, prove the diff
     against the new base is only this item's own delta;
   - a parked dependency: build against what exists today behind a narrow adapter, touch none of the parked item's
     files, and record the adapter's follow-up in the PR body, in the ledger (a flagged class B entry with its exact
     undo) and in the todo file's Roadmap view; also propose the follow-up as a roadmap row in a PR of its own, which
     merges only on the user's go (the roadmap file changes only through a pull request);
   - an open decision that gates only the merge or a default: build with the default untouched, as a normal PR under
     the project's own PR standards (never marked SPIKE), put the merge gate in the PR body, and queue the exact words
     in "Waiting for you"; nothing merges without the user;
   - a large item: split it into phases and start the one that depends on nothing pending (a class B decision).
   An item is blocked only when what is left after this needs the blocker. A skip is written down with the part
   looked for and why it does not exist. If no item is ready, write the table (step 13) before concluding; a row with
   no allowed reason is the item to pick.
   **After merging the base into a branch** (never rebase), run the full gate. When two branches changed the same
   lines, resolve keeping both meanings, run the full gate and wait for CI on the new head.
9. **Work** one step in the loop's own worktree, by a subagent when heavy. **Every brief ends with** the time
   budget, "never start subagents" and these four lines (the brief footer): (1) commit only when the gate itself passes, on its exit
   status (`if <gate> > log 2>&1; then git commit ...; fi`), never `&& git commit` after a redirected run; (2) never
   disguise code to get past a check: a genuine exception is a named allowance in the check itself, as narrow as
   possible, tested both ways, and logged as a class B decision; (3) stop every process you started (tests that spawn
   processes stop them in `finally`); (4) never print a secret or another process's command line.
   **Branches follow the project's own naming convention with a `loop` suffix** (`feature/export-v2-loop`). The
   loop works only in worktrees and branches it created. It never switches, resets or stashes in the main checkout
   and never touches a branch, worktree, stash or process it did not make. Before the first commit write the item's
   boundary; compare the diff with it at the end of each step. Every branch, commit and PR names its roadmap item.
   Open PRs ready for review, never as drafts, unless a spike. Changes to the roadmap's status go through a PR on a
   loop branch (a status only, with evidence).
   **A live check with a side effect** (a real notification, a real external run) runs only as far as the charter's
   "live checks" line allows, and each allowance is spent once (the `live checks spent` counter). Record which build it used (the commit). If it ran
   before the final commits, the PR says what it proves and what it does not, and the check is not run again to
   cover them; one without an allowance is queued as class C.
10. **Decide** each fork by the classes, and **record** it: fill [ledger-entry.md](ledger-entry.md)'s template exactly,
    heading included, with the entry's time as SKILL.md step 10 says. The ledger entry is pushed, then the todo list. No new step until
    the ledger is pushed.
11. **Done means** the item's check passes and a reviewer that did not build it agrees. The builder never grades its
    own work (single-threaded: see the charter). One strong verdict per item is mandatory, even when the other
    reviewers agree; besides "is it done?" its brief asks who calls this and which roadmap row owns wiring it in,
    what changed in shared types since the branch was cut, and whether any code was changed only to get past a check.
    Every reviewer's brief asks that last question too.
12. **Report** by posture ([updates.md](updates.md)), new information only, and never less than one visible line: an
    unchanged queue item or limit is not restated; it reappears when it changes or in the 2-hour full report.
13. **Speed.** Work left: the work beat (15 minutes); an item with its own builder running counts as work left. **The
    quiet beat starts only after the blocker table.** Write a table with one row for every roadmap item that is not
    done (parked ones too): the item, the exact thing that blocks it, which allowed reason that is, and the words that
    unblock it. The allowed reasons, and only these:
    1. it needs a decision that changes what gets BUILT, not only what gets merged;
    2. it needs something that exists only after the user merges another item and that item's release, deploy or
       package publish runs; every other dependency is built ahead on a branch, and the loop never merges;
    3. a limit is in force: load, disk, silence, fix rounds, the same failure or parked items
       ([limits-and-drift.md](limits-and-drift.md)); during the silence limit every row reads "silence limit";
    4. the user has claimed it ("I'm taking R4"), or someone else is changing its files right now.
    A row with none of these is not blocked: go back to step 8 and pick it. If the tick has already done its one step,
    stay on the work beat so the next tick takes it. Only when every row has an allowed reason switch to the quiet
    beat, by the re-arm in SKILL.md section 5, post the table ([updates.md](updates.md), "The quiet report"), and add a
    background watcher that exits on the CI or PR state (never a foreground `sleep`). Every row with reason 1 or 2 has
    a matching "Waiting for you" entry with the exact words that unblock it; a row without one means the queue is
    incomplete, so write the entry first. On a quiet beat re-write the table each tick (step 8); when a row loses its
    reason, switch back to the work beat and take that item. "Waits on the user" never means "touches anything that
    waits on the user": a blocker stops only its own scope (step 8, "What does not block building").
14. **Update the state line and the claim:** last beat (in both), counters, last full report. The claim is written as
    SKILL.md section 1 says; if writing it is refused, say so in one line and continue single-session: no claim.

**A question about why the loop is quiet or stopped** ("isn't the loop supposed to keep going?", "why did it stop?"):
do not defend the quiet state and do not answer "already working". Re-run the blocker table now from the repo, the PRs
and CI as they are. A row with no allowed reason: say so in one line, switch the job back to the work beat and take
that item in this same turn (step 8 onwards). Every row blocked: show the table with the words that unblock each. The
same applies when a bare "keep going", "continue" or "carry on" arrives while the last tick was a quiet one.

**A tick stuck behind a permission panel** runs nothing until the user answers it; the gap rule then reports the
missed beats. The start gate's read and write check is there to surface that panel while the user is present.

**A tick never asks a modal question.** An `AskUserQuestion` stays open until answered, and a tick due meanwhile
waits and runs right after the turn ends (measured; see "What was tested, and what was not" in this skill's README.md), so a panel on a tick would only freeze the loop. Questions
(verdicts, renewal) are asked only in a turn the user started, with the digest read first.
