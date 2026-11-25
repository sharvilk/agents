---
name: checkpoint
description: Bring the session's work to a safe stopping point and record exactly where it stands, so nothing is lost when the machine restarts, the app quits or the user steps away, then give a quick summary. Use when the user types /checkpoint or says "save progress", "checkpoint", "I'm going to restart", "before I restart", "before I quit", "stop everything safely", "is it safe to restart". Also use at the start of work after a checkpoint, when the user says "continue", "resume", "carry on", "keep going" or "I'm back", or opens a session after a restart: then resume the recorded work and keep working, not only summarise it.
---

# Checkpoint

A restart keeps what is on disk and loses what is running. A checkpoint deals with the second half: it stops the
work in flight at a safe point, writes down where each piece stands and what comes next, makes sure everything
committed is pushed, and leaves no process behind. Then it says, in a few lines, whether it is safe to restart.

The resume block is written into the session's `todo-sync` list, so checkpoint needs the `todo-sync` skill installed
too.

**If this session's todo list has a `## Loop state:` heading that is ARMED or PAUSED and owned by another skill** (the heading names the owner): every phrase in this skill's description stays yours in every state ("checkpoint", "save progress", "I'm going to restart", "before I restart", "before I quit", "stop everything safely", "is it safe to restart"). For a restart or a quit with the marker ARMED, delete the loop's job first, rewrite the marker as `## Loop state: PAUSED — <owner> — charter valid until <date> — reason checkpoint`, and put "resume the loop (owner <owner>, charter valid until <date>)" first in the resume block. A break (no restart, no quit) leaves the loop's job and marker alone; when it leaves an ARMED loop running, its summary names the loop from the marker and says "pause the loop" pauses it. When a "Resume here" block for this session exists, "continue", "resume", "carry on", "keep going" and "I'm back" are yours first: resume, and re-arm only a loop whose marker is PAUSED with `reason checkpoint`, by invoking the owner skill named in the heading and running that skill's "resume the loop" step, which keeps the charter's clock. A marker PAUSED with `reason user` gets no re-arm item and is left alone. With no resume block, those phrases go to the loop when its `Answers:` line lists them.

```
 SURVIVES a restart (disk)                  LOST in a restart
 worktrees, commits, uncommitted edits      running subagents and their unreported progress
 notes, todo lists, session transcripts     background jobs: test runs, benches, watchers, servers
                                            the session scratchpad (a temporary folder, emptied at boot)
```

So the checkpoint does not save files. It saves **state that lives only in running things and in your head**, and it
removes processes that would otherwise run on after you leave (a benchmark's child process, for example, can keep a core busy for hours after its agent reported done).

## Contents

- [Part 1: the checkpoint](#part-1-the-checkpoint)
- [Part 2: resuming](#part-2-resuming)
- [The resume block](#the-resume-block)
- [Traps](#traps)
- [When it cannot conclude](#when-it-cannot-conclude)
- [What it does not do](#what-it-does-not-do)

## Part 1: the checkpoint

Start no new work. Do the steps in order; each reads before it acts.

**1. Inventory (read only).** Run the scan over every repo this session touched (main checkouts; it finds their
worktrees itself):

```bash
python3 "${CLAUDE_SKILL_DIR}/checkpoint-scan.py" <repo-root> [<repo-root> ...]
```

It prints the machine (disk, load, and swap on macOS), each worktree's state (uncommitted files, unpushed commits, a half-done
merge or rebase, the stash count) and every process whose working directory is inside those repos: PID, parent, age,
CPU, memory, executable and cwd, never a command line or environment. Exit 0 means nothing to deal with; 1 means
something listed needs a decision; 2 means a check could not run. Add to it what only you know: the subagents and
background jobs this session started and has not seen finish, and the scratchpad files later work needs.

**2. Bring running work to a safe point.**
- **Each subagent still running:** send it "stop at the next safe point: commit what is finished on your feature
  branch and push it, leave the rest uncommitted, stop every process you started, and report your exact state and next
  step in at most ten lines". Give it a few minutes, then stop it (`TaskStop`) whether or not it answered, and record
  what it said or that it did not.
- **Each background job of your own** (a watcher, a CI poll, a server, a long test): stop it. CI keeps running on the
  remote; note what to read there later.
- **A timing run or benchmark** cannot be paused: stop it and record "re-run from the start".

**3. Push what is committed.** For each worktree **this session** worked in, push committed work on its feature
branch, through the hooks (never `--no-verify`, never to the default or a release branch, never a force-push).
Uncommitted edits stay where they are, since the disk survives; list them with their worktree. Commit them only if the
user asks or the disk itself is at risk, and then as a commit that says it is unfinished. Leave other sessions'
worktrees alone, even when the scan flags them: list them as "not mine".

**4. Rescue the scratchpad.** Anything in the session scratchpad (or the temporary folder used when the session has
none) that later work needs (a brief, a result file, a draft) moves to a gitignored folder in the project's **main
checkout** (never a branch worktree, whose removal deletes ignored files). If the project has no such folder, ask
where; do not edit a `.gitignore` to make one.

**5. Write the resume block** (below) into the session's todo list,
`<config>/todo-sync/<initiative>/<session-id>.md`, where `<config>` is `${CLAUDE_CONFIG_DIR:-$HOME/.claude}`, or in the
list's own place when `todo-sync` finds it elsewhere (a list started before that folder existed stays in
`<config>/todos/<initiative>/`), after reconciling the list with the `todo-sync` skill
(reorganize before prune; never drop an open item). Anything other agents or sessions must see also goes in the
project's tracker doc, through its normal PR.

**6. Sweep for strays.** Run the scan again. Every remaining process in these repos that this session started is
stopped: a polite signal (`kill <pid>`), then a forced one (`kill -9 <pid>`) if it is still there a few seconds later. A
process you did not start is not yours to stop: list it. If the permission check refuses a `kill`, give the user the
PID, its age, CPU and working directory and the exact command, and do not work around the refusal.

**7. Give the quick summary**, and stop:

```
Checkpoint (<date time>): safe to restart | NOT safe to restart: <why>
machine     disk <n> GiB free · load <n> · swap <n>
running     <n> processes of ours (0 is the goal) · agents stopped: <n>
saved       <n> worktrees clean and pushed · uncommitted: <worktree: n files> · not mine: <list>
in flight   <item>: <state> → next: <step>          (one line each, the few that matter)
waiting     <decisions only the user can make>
resume      say "continue" in this session or a new one; the plan is in <todo file path>
```

Keep it to what fits on one screen; the detail is in the resume block.

## Part 2: resuming

When the user says "continue", "resume", "carry on" or "I'm back", or opens a session after a restart:

1. **Find the block.**
   - **A session that has its own list** finds its block in that list, by the session id, never by a path remembered
     from the conversation, because a list can have moved. The list is in `<config>/todo-sync/<initiative>/`, or, for a
     list started before that folder existed, in `<config>/todos/<initiative>/`, where `<config>` is
     `${CLAUDE_CONFIG_DIR:-$HOME/.claude}` and the file is `<session-id>.md`, with the id from `${CLAUDE_SESSION_ID}`
     as `todo-sync` says. A lookup that works in zsh, where a glob with no match aborts the whole command, with your
     session id in place of `<session-id>`:
     `find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todo-sync" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todos" -mindepth 2 -maxdepth 2 -name '<session-id>.md' 2>/dev/null`
     It exits 1 when either folder does not exist yet; what it prints is the answer.
     - **It prints nothing:** this session has no list, so take the new-session path below.
     - **It prints two paths:** follow `todo-sync`'s rule for a list that is in both folders (the list folder's copy
       is the list), then look for the block in that copy. If the block is only in the other copy, tell the user and
       ask before resuming.
     - **The list is found but has no `## Resume here` block:** say so and ask what to continue.
     - **The id in the command still reads `<session-id>`, or is not a UUID:** recover the id first, as `todo-sync`
       says (the directory above `scratchpad` in the scratchpad path, otherwise ask the user).
   - **A new session** lists every `## Resume here` block in both folders, with a `find` rather than a bare glob, for
     the same zsh reason:
     `find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todo-sync" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todos" -mindepth 2 -maxdepth 2 -name '*.md' -exec grep -l '^## Resume here' {} + 2>/dev/null`
     From each file it prints, read the `## Resume here (...)` heading line, which holds the checkpoint time and
     reason, and the first numbered line after `In flight, in order:`. The session id is the file's name and the
     initiative is its folder. Show the user one line per file (short session id, initiative, time and reason, first
     in-flight item) and ask which one to continue. It never picks one by itself, not even the newest: other
     sessions, including ones the user runs for unrelated work, keep lists in the same folders. When the command
     prints nothing, say so and ask what to continue.
   - **The user's choice is the takeover** that `todo-sync` requires. The question says that the chosen session's
     list will be taken over, so that session should not be resumed elsewhere. The agent then keeps writing that
     file, as `todo-sync` says, rather than copying it.
2. **Re-check the machine and the strays** with the scan. If disk, load or a leftover process is out of bounds, deal
   with that first and say so in one line.
3. **Re-verify each item from its source**, because the block describes the moment it was written: the branch and its
   remote head, the PR's state and CI, what merged meanwhile. Trust the source over the block.
4. **Then keep working.** Say in one or two lines what you are resuming, and carry on with the in-flight items in
   the block's order: relaunch each stopped piece with a fresh brief (the old subagents are gone, and so is their
   context), re-run what was marked "re-run", read the CI results that came in. Do not stop at a summary or ask "shall
   I continue?": the user's "continue" is the go for the work that was already in flight. Decisions that were waiting on
   the user still wait: list them once, and do not act on them.
5. **Mark the block consumed** (rename its heading to `## Resumed <date time>`, or delete it once every item is back in
   the list's open section).

## The resume block

At the top of the todo file, newest first; one block at a time, replacing a consumed one:

```md
## Resume here (checkpoint <date time>, <reason: restart / quit / break>)
Machine at checkpoint: disk <n> GiB free, load <n>, swap <n>; strays stopped: <pids or none>.
In flight, in order:
1. <item> — <branch / PR / worktree> at <sha>. State: <done so far>. Next: <exact next step, with the brief's path>.
2. …
Lost in the stop and to redo: <a timing run to re-run, a watcher to restart, CI to read>.
Uncommitted, left on disk: <worktree: what and why>.
Waiting on the user: <decision> (recommendation: <x>).
Not mine (left alone): <worktrees or processes the scan showed that another session owns>.
```

Write each "Next" so a fresh session with none of this conversation could do it: the branch, the file, the command,
the brief.

## Traps

- **"The agent reported done" is not "its processes are gone".** A background job can outlive its agent by hours, and
  its parent is the agent's idle shell, not PID 1, so a search for orphans under PID 1 misses it. Match by working
  directory and age, which is what the scan does.
- **Pushing someone else's branch, or popping their stash.** The scan lists every worktree of the repo, other
  sessions' included, and the stash is shared by all of them. Act only on what this session made.
- **Committing half-finished work to make the tree "clean".** The disk survives a restart; a WIP commit on a PR branch
  runs CI and reads as done. Leave edits uncommitted unless the user asks or the disk is at risk.
- **A resume block that only this conversation can read.** "Continue the fix round" means nothing to a fresh session;
  name the branch, the commit, the file and the next command.
- **Resuming into a summary.** After a restart the user's "continue" means do the work. One line on what resumes,
  then the work.
- **Trusting the block after the restart.** CI finished, someone merged, a branch moved. Re-read each source first.

## When it cannot conclude

- **A subagent will not stop or does not answer:** stop it with `TaskStop` and record its last known state from its
  last report; mark the item "state unknown: re-check the branch".
- **A push fails** (a hook fails, the remote refuses, no network): leave the commit local, record it as unpushed with
  the error, and say "safe to restart" only if the user accepts that it is unpushed (the disk keeps it).
- **The disk is full or nearly so:** do not install or build to make a hook run; record what is uncommitted and stop.
- **A process will not die, or the permission check refuses the kill:** hand it to the user with the PID and the
  command; the checkpoint says "NOT safe to restart" only if that process holds unsaved work, and otherwise names it.

## What it does not do

- It does not run by itself before a restart or a quit: no hook can do this work. A `SessionEnd` hook cannot delay the
  exit, has a 1.5-second default budget, runs only a shell command (it cannot think, write the block or stop agents),
  and is not documented to run when the window closes or the machine restarts. The user runs `/checkpoint`.
- It does not pause anything: what was running is stopped, and the block says how to redo it.
- It does not decide for the user: decisions that were waiting stay waiting.
