# Wind down

On "stop the loop", "pause the loop", a STOP in limits-and-drift.md, or the end of the charter.

1. **Delete every recorded job** (`CronDelete` for the id in the marker) and any listed task whose prompt starts
   with "On-loop tick"; `CronList` shows none. Leave other loops running: they have their own owners.
2. Write the marker at once: ENDED with the reason (stop, a limit, the charter's end), or, for a pause,
   `PAUSED — on-loop — charter valid until <date> — reason user`.
3. **Running subagents:** let each finish at its next safe point or stop it (TaskStop, or the tool that started it); a report that arrives
   after wind-down is recorded in the ledger and the final report, and takes no next step.
4. Stop its own background processes by PID. Re-check PRs and CI from the sources.
5. Give the final report: the full status report, the decisions (counts and flagged ones), what is waiting for review,
   and why it stopped. For an end with decisions still pending, the report says where they wait (the ledger PR, by
   its full link) and that, once the todo list is closed, "review" no longer reaches the loop.
   For a pause, keep the charter, the state and the claim so "resume the loop" is one phrase;
   for an end, release the claim and carry every open item into the normal list, dropping nothing (`todo-sync`).
   Release the claim as SKILL.md section 1 says.
6. **Open branches are the user's.** The log branch stays, with its PR if one is open. The branches and worktrees of PRs that
   already merged or closed were cleaned up when that happened (tick step 6); if any were not, do it now under the
   same check. The branches and worktrees of PRs still open stay until the user decides: list them with the exact
   commands to remove them (`git worktree remove <path>`, `git branch -d <branch>`,
   `git push origin --delete <branch>`) and run none.
