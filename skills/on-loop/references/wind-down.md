# Wind down

On "stop the loop", "pause the loop", a STOP in limits-and-drift.md, or the end of the charter.

1. **Delete every recorded job** (`CronDelete` for the id in the marker) and any listed task whose prompt starts
   with "On-loop tick"; `CronList` shows none. Leave other loops running: they have their own owners.
2. Write the marker at once: ENDED with the reason (stop, a limit, the charter's end), or, for a pause,
   `PAUSED — on-loop — charter valid until <date> — reason user`.
3. **Running subagents:** let each finish at its next safe point or stop it by its handle; a report that arrives
   after wind-down is recorded in the ledger and the final report, and takes no next step.
4. Stop its own background processes by PID. Re-check PRs and CI from the sources.
5. Give the final report: the full status report, the decisions (counts and flagged ones), what is waiting for review,
   and why it stopped. For a pause, keep the charter, the state and the claim so "resume the loop" is one phrase;
   for an end, release the claim (read it, write `released <time>` to a temp file beside it, rename that into place; nothing deletes it) and carry every open item into the normal list, dropping nothing (`todo-sync`).
6. **Clean-up is the user's.** The log branch and its PR stay open. The loop's finished branches and worktrees stay
   until the user decides: list them with the exact commands to remove them (`git worktree remove <path>`,
   `git branch -d <branch>`, `git push origin --delete <branch>`) and run none. Only its own scratch files in the
   session scratchpad may it remove, and the dependency folders and build output it produced in its own worktree.
