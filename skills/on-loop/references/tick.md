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
   than two beats passed with no tick, say so in the first report after (a gap is reported, not hidden). A tick
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
   unanswered)? End the tick with no output.
4. **Health:** disk free, load, memory, the project's heavy-work lock, other sessions, and the user's own branches
   and worktrees (`git worktree list`, branches, open PRs). Note anything out of bounds. **Over a line (load or
   disk): this tick takes no heavy step** (no build, test run, install or subagent) and does bookkeeping only: the
   ledger, replies to review threads, the state line, the todo list. Report it once when it starts and once when it
   clears, not at every tick ([limits-and-drift.md](limits-and-drift.md) rows 9 and 10).
5. **Verdicts.** Apply any keep, change or veto the user gave since the last tick ([review-and-veto.md](review-and-veto.md)).
6. **Act on what finished.** For each subagent that reported, take its next step: a fix round, an independent
   reviewer with a scope that does not overlap, or one final verdict per item. Read the diff of every fix yourself;
   a builder's report is a claim, not proof. Check every PR the loop opened: CI, new reviews and **unresolved review
   threads**. **Reply to every review comment on the loop's own PRs, from anyone**: a fix is class A, declining
   with the reason is class B. Then resolve the thread. A PR is not "merge-ready" while a thread is open. A reply in
   the user's name outside its own PRs' review threads (an issue, someone else's PR) is class C: draft it, queue it.
   When the user merges a PR whose body lists decisions, mark those entries `accepted (merged <date>)`. When a PR it
   made is merged, list the branch and worktree clean-up for the user, with the exact commands; never run it.
7. **Roadmap changed?** Re-read the roadmap from the repo and compare its commit with the one recorded. If anyone
   changed it, say what changed, re-plan before picking, and record the new commit.
8. **Pick** the next item:
   1. finish what is in flight before starting anything (the charter's in-flight line, default two items: a pacing
      limit, never a cap on PRs waiting for the user);
   2. then the roadmap's own order or priority, never the loop's taste;
   3. skip items that are not ready, that wait on an unanswered question or a queued decision, or that are claimed (an
      assignee, another branch or PR touching it, the user saying "I'm on that"). **An unmerged PR does not block**:
      the next item may stack on it;
   4. skip items whose files the user or another session is changing right now;
   5. ties: the item that unblocks the most others, then the smallest.

   Every skip is written down with its reason. **Prefer independent work:** each item on its own branch off the
   default branch with its own PR. Stack when the work needs it: no limit on depth, and stacked PRs are fine to
   review. If a step cannot proceed (it waits on a decision), move in this order: (1) another ready item; (2) other
   work on the same item that does not depend on the pending choice; (3) prepare what is queued (options, a
   throwaway spike); (4) only when none exist, wait and name the one decision whose review unblocks it.
9. **Work** one step in the loop's own worktree, by a subagent when heavy. Subagents are never asked to spawn their
   own; say so in each brief, with the time budget and "never print a secret or another process's command line".
   **Branches follow the project's own naming convention with a `loop` suffix** (`feature/export-v2-loop`). The
   loop works only in worktrees and branches it created. It never switches, resets or stashes in the main checkout
   and never touches a branch, worktree, stash or process it did not make. Before the first commit write the item's
   boundary; compare the diff with it at the end of each step. Every branch, commit and PR names its roadmap item.
   Open PRs ready for review, never as drafts, unless a spike. Changes to the roadmap's status go through a PR on a
   loop branch (a status only, with evidence).
10. **Decide** each fork by the classes, and **record** it: fill [ledger-entry.md](ledger-entry.md)'s template exactly,
    heading included, with the entry's time from `date` run in the command that writes it (never typed or
    estimated). The ledger entry is pushed, then the todo list. No new step until the ledger is pushed.
11. **Done means** the item's check passes and a reviewer that did not build it agrees. The builder never grades its
    own work (single-threaded: see the charter).
12. **Report** by posture ([updates.md](updates.md)), new information only: an unchanged queue item or limit is not
    restated; it reappears when it changes or in the 2-hour full report.
13. **Speed.** Work left: the work beat (15 minutes). Everything waits on the user or on CI: the quiet beat (60
    minutes), by the re-arm in SKILL.md section 5, plus a background watcher that exits on the CI or PR state
    (never a foreground `sleep`). When work is available again, switch back.
14. **Update the state line and the claim:** last beat (in both), counters, last full report, every time from `date`
    in the writing command. Every write of the claim reads it first, writes the new content to a temp file beside it
    and renames that into place; it never opens the claim for writing in place. If writing it is refused, say so in
    one line and continue single-session: no claim.

**A tick stuck behind a permission panel** runs nothing until the user answers it; the gap rule then reports the
missed beats. The start gate's read and write check is there to surface that panel while the user is present.

**A tick never asks a modal question.** An `AskUserQuestion` stays open until answered, and a tick due meanwhile
waits and runs right after the turn ends (measured; see "What was tested, and what was not" in this skill's README.md), so a panel on a tick would only freeze the loop. Questions
(verdicts, renewal) are asked only in a turn the user started, with the digest read first.
