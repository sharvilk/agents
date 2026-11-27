# checkpoint: stop safely before a restart, and carry on after it

`/checkpoint` brings an agent session's work to a safe stopping point before the machine restarts, the app quits or
you step away, writes down exactly where everything stands, and tells you in a few lines whether it is safe to go.
When you come back and say "continue", the agent picks the work up from that record and keeps working.

## Install

As a plugin, from the `agents` marketplace:

```
/plugin marketplace add sharvilk/agents
/plugin install checkpoint@agents
```

That also installs `todo-sync`, because the plugin declares it as a dependency.

Or copy the `checkpoint` and `todo-sync` folders to `~/.claude/skills/` (or `$CLAUDE_CONFIG_DIR/skills/`). Nothing
needs registering: Claude Code finds each skill by the `name` and `description` at the top of its `SKILL.md`. Start a
new session afterwards so the skills are loaded. To check it loaded, type `/checkpoint` (or `/checkpoint:checkpoint`
if another command already uses that name) in a session.

**Use.** Type `/checkpoint`, or say "save progress" or "is it safe to restart". After the restart, say "continue"
(or "resume", "carry on", "I'm back"), in the same session or a new one.

## Table of contents

- [Why it exists](#why-it-exists)
- [What a restart keeps and loses](#what-a-restart-keeps-and-loses)
- [Working with a loop skill](#working-with-a-loop-skill)
- [The flow](#the-flow)
- [What you see](#what-you-see)
- [The scan](#the-scan)
- [Why there is no hook](#why-there-is-no-hook)
- [Errors and what you see](#errors-and-what-you-see)
- [Limits](#limits)
- [Tests](#tests)
- [Files](#files)

## Why it exists

A long session runs many things at once: subagents building and reviewing, test suites, benchmarks, CI watchers.
Stopping the machine in the middle loses whatever lived only in those running things, and a process an agent started
can outlive the agent: a benchmark's child process, for example, can keep a core busy for hours after its agent
reported done, and the machine slows until a person notices. Without this skill, the checks before a restart are done
by hand: stop every agent, read every worktree's state, sweep for leftover processes, write a resume plan. This skill
is that procedure, written down, with a script for the parts that should never depend on memory.

## What a restart keeps and loses

```
 KEPT (on disk)                              LOST
 ─────────────────────────────────           ────────────────────────────────────────────────
 worktrees, commits, uncommitted edits       running subagents, and whatever they had not reported
 todo lists, notes, session transcripts      background jobs: tests, benchmarks, watchers, servers
 the pushed branches and open PRs            the session scratchpad (temporary, emptied at boot)
```

So the checkpoint does not copy files. It stops running work at a safe point, records the state that lived in it,
pushes what is committed, rescues the scratchpad, and removes leftover processes.

## Working with a loop skill

Another skill can run a background loop and mark the session's todo list with a `## Loop state:` heading (ARMED or
PAUSED) that names the skill as its owner. Checkpoint then pauses that loop before a restart and re-arms it on resume.
In this repo, `on-loop` is the skill that writes that heading.

- Every checkpoint trigger stays checkpoint's, whatever the loop's state.
- A restart or a quit deletes the loop's job first and rewrites the marker as PAUSED with `reason checkpoint`. A break
  (you step away, but the machine and the app keep running) leaves the job and the marker alone.
- On resume, a "Resume here" block is resumed first. Only a marker PAUSED with `reason checkpoint` is re-armed, by
  invoking the owner skill and running its "resume the loop" step, which keeps the loop's charter clock. A marker
  PAUSED with `reason user` is left alone.
- With no resume block, the phrases on the heading's `Answers:` line go to that loop.

## The flow

```
  you: /checkpoint
        │
        ▼
  1 inventory ── checkpoint-scan.py: machine · worktrees · processes in the repos
        │        + what the agent knows: its subagents, its background jobs, its scratch files
        ▼
  2 safe point ── each subagent: "commit what is done, push, stop your processes, report",
        │         then stopped · each background job: stopped · a benchmark: stopped, "re-run"
        ▼
  3 push ──────── committed work on this session's feature branches
        │         (hooks run; never main, never forced)
        │         uncommitted edits stay on disk and are listed
        ▼
  4 rescue ────── scratchpad files that later work needs → a gitignored folder in the main checkout
        ▼
  5 record ────── the "Resume here" block at the top of the session's todo list
        ▼
  6 sweep ─────── the scan again; strays this session started are stopped; others are listed
        ▼
  7 summary ───── "safe to restart" (or why not), on one screen
        │
   … restart …
        │
  you: continue
        ▼
  resume ──────── find the block · re-check the machine · re-verify each item from git,
                  the PR and CI · one line on what resumes · then the work itself, in the
                  block's order
```

### Finding the block when you resume

The block sits in a session's todo list, `<config>/todo-sync/<initiative>/<session-id>.md`, where `<config>` is
`$CLAUDE_CONFIG_DIR` or `~/.claude`. A session that has its own list looks it up by its session id, never by a path
it remembers from the conversation, because a list can have moved. A new session cannot know which list is yours, so
it asks:

```
 same session                        new session (after a restart)
 ──────────────────────────          ────────────────────────────────────────────────────
 find <session-id>.md in             list every "## Resume here" block in both list folders
 the list folders                      │   session id (short) · initiative folder
        │                              │   checkpoint time and reason · first in-flight item
        ▼                              ▼
 continue from that block            ask you which one to continue (never the newest by
                                     itself: other sessions, even ones for unrelated work,
                                     keep lists here)
                                       │
                                       ▼
                                     your answer is the takeover: that session's list is now
                                     this session's, and that session should not be resumed
                                     elsewhere
                                       │
                                       ▼
                                     keep writing that file (not a copy) and carry on
```

Lists started before the list folder existed are found in `<config>/todos/` as well: the folder earlier versions of
todo-sync used. Both lookups cover it, and a new list is always written in `todo-sync/`.

When no block is found, the agent says so and asks what to continue.

## What you see

The summary at the end of a checkpoint:

```
Checkpoint (2026-10-21 12:45): safe to restart
machine     disk 6.8 GiB free · load 4.9 · swap 11.8 of 13.3 GB
running     0 processes of ours · agents stopped: 3
saved       9 worktrees clean and pushed · uncommitted: none · not mine: 2 worktrees of another
            session
in flight   export fix (PR for fix/csv-escape): figures committed → next: README and a test
            (brief in notes/brief-fix-round.md)
            import fix (PR for fix/import-dates): fix round pushed → next: verdict on its findings
waiting     the gate decision (recommendation: one more benchmark round)
resume      say "continue"; the plan is in ~/.claude/todo-sync/billing/<session-id>.md
```

And after you say "continue", one or two lines on what is resuming, then the work.

## The scan

`checkpoint-scan.py` is read only. Give it the main checkouts of the repos the session touched; it finds their
worktrees itself.

```bash
python3 ~/.claude/skills/checkpoint/checkpoint-scan.py ~/code/project-a ~/code/project-b
```

This path is for a copy install (with `$CLAUDE_CONFIG_DIR` set, the folder is `$CLAUDE_CONFIG_DIR/skills/checkpoint/`). A
plugin install keeps the script elsewhere; the agent runs it from the skill's own folder, so you never type the path.

```
## Machine
disk free   6.8 GiB
load        4.9 5.0 7.3  (11 cores)
swap        total = 13312.00M  used = 11786.75M  free = 1525.25M  (encrypted)

## Worktrees
/Users/me/code/project-a
  .                                              main                                           clean, pushed
  .worktrees/feature-x                           feature/x                                      3 uncommitted, 1 unpushed
  .worktrees/fix-y                               fix/y                                          clean, pushed

## Processes in these repos (PID, parent, age, CPU, resident, executable, cwd; never command lines)
  pid 65023   ppid 64785   age 08:55:16     cpu 100.0%      4 MB  node             /Users/me/code/project-a/.worktrees/feature-x
```

This is real output, and its worktree and process rows are wider than most screens, so it scrolls sideways.

- **Worktree notes**, one or more per row:
  - `n uncommitted`, `n unpushed`, `n behind its remote`;
  - `merge in progress` (or rebase, cherry, revert);
  - `no remote branch`, `no remote`, `n commit(s) on no remote`;
  - `git status failed` (the worktree's folder is gone or unreadable);
  - `clean, pushed`.
- **How the remote is chosen.** A detached worktree is not compared with a remote. A branch with no upstream setting is
  compared with `origin/<branch>` when that exists. When neither exists, the repo's remotes decide the note: none at
  all gives `no remote`; otherwise commits reachable from no remote-tracking branch give `n commit(s) on no remote`,
  and a branch with none of its own gives `no remote branch`. The repo's stash count is shown once, because every
  worktree shares one stash.
- **Processes:** every process whose working directory is inside the repos or their worktrees, except the scan itself
  and its own pipeline. It never prints a command line or an environment, which can carry secrets.
- **Exit codes:** 0 nothing to deal with; 1 something listed needs a decision (a dirty, unpushed or behind worktree, a
  half-done merge, a process, disk under 5 GiB); 2 a check could not run (a path that is not a git repo). A branch
  whose only note is `no remote branch` or `no remote` exits 0, because it holds nothing a remote lacks. A branch with
  commits on no remote exits 1. A 2 wins over a 1. An uncaught Python error prints one line on stderr and exits 2.
- It needs Python 3.8 or later and `git`, and uses the standard library only. It has been run with Python 3.14 on
  macOS only; 3.8 is the floor the code is written to, not a version it was tested on. On Linux
  it reads working directories through `lsof`, or `/proc` where `lsof` is missing; that path is untested.

## Why there is no hook

A hook that saves progress "on quit" would be the obvious design, and it does not work:

- `SessionEnd` cannot block or delay the exit, has a 1.5-second default budget (60 seconds at most), and runs a shell
  command only: it cannot write the resume block, judge what is in flight or stop subagents.
- Nothing documents it running when the editor window closes or the machine restarts, so a checkpoint that depends on
  it would fail silently exactly when it matters.

There is no `SessionStart` hook that prints the scan on every start: it would put the scan's output into every
session's context whether or not anything was interrupted, and the skill's resume step already runs the scan.

## Errors and what you see

| What happens | Exit | What you see | What to do |
| --- | --- | --- | --- |
| Nothing to deal with | 0 | the three sections, every worktree `clean, pushed` (or only `no remote branch` or `no remote`), and `none` under processes | nothing: it is safe to restart |
| A worktree is dirty, unpushed, behind its remote or in the middle of a merge, rebase, cherry-pick or revert | 1 | its notes on its row, for example `3 uncommitted, 1 unpushed` | commit and push, or leave it and say so in the resume block |
| A worktree's folder is gone or git cannot read it | 1 | `git status failed` on its row | remove the stale entry with `git worktree prune`, or restore the folder |
| A process has its working directory in the repos | 1 | one `pid … ppid … age … cpu … MB … <executable> <cwd>` row each | stop it if the session started it; otherwise it is listed and left alone |
| A branch has commits that exist on no remote | 1 | `2 commits on no remote` on its row | push the branch |
| A repo has no remote at all | 0 | `no remote` on its row | nothing, unless you meant to publish it |
| Every process found ended before it could be described | unchanged | `none (the ones found had already ended)`, printed only when each one is confirmed gone | nothing |
| A process was found but `ps` printed nothing for it and it is still running | 1 | `could not describe pid(s) 123, 456 (still running)` | look at those PIDs by hand; they are not confirmed gone |
| The `ps` call that describes the found processes fails or runs over 30 seconds | 2 | `ps failed: OSError; could not describe pid(s) 123 (still running)` (or `TimeoutExpired`; a process that ended meanwhile is left out) | run `ps -p <pid>` by hand |
| Any other uncaught Python error | 2 | on stderr `checkpoint-scan: unexpected error: <ExceptionType>: <message>` | report it with the message; the scan changed nothing |
| Disk free is under 5 GiB | 1 | `disk free   3.2 GiB  (under 5 GiB)` | free space before building or installing anything |
| A path is not a git repo, or does not exist | 2 | `<path>: not a git repo` in the worktrees section; the other paths are still scanned | give the main checkout of the repo |
| No path given, and the current folder is not in a git repo | 2 | nothing on stdout; on stderr `not inside a git repo: name the repo roots to scan` | name the repo roots |
| A `git`, `ps`, `lsof` or `sysctl` call fails or runs over 30 seconds | as above | treated as no output: a failed `git worktree list` reads as `not a git repo`, a failed `sysctl` leaves out the `swap` line, a failed `lsof` falls back to `/proc` and then to no processes. The `ps` call that describes found processes is the exception: see the `ps failed` row | run the command by hand to see why |

The skill itself raises no errors. When a step cannot conclude, it says so in the summary: a subagent that does not
answer is marked "state unknown", a failed push is recorded as unpushed with its error, and a process that will not
die is handed to you with its PID.

Nothing watches it in the background: the scan runs when you ask for a checkpoint and when a session resumes.

## Limits

- It runs when you ask for it. Nothing triggers it before an unplanned crash or power loss; the disk still keeps
  everything committed and uncommitted then, but running work is lost unrecorded.
- It cannot pause a benchmark or a long test: it stops it and records that it must be re-run.
- In auto mode, the permission check may refuse to stop a process. The checkpoint then hands you the PID and the exact
  command, and does not work around the refusal.
- It acts only on what its own session made. Other sessions' worktrees, branches and processes are listed and left
  alone.
- It writes into the todo list that the `todo-sync` skill keeps, so it needs that skill installed.
- On a machine with neither `lsof` nor `/proc`, the scan cannot read working directories and reports no processes.
- The process list leaves out the scan, the shells above it and the other processes its caller started in the same
  shell, which are the caller and not strays. A stray started from that same shell is therefore not listed.

## Tests

[test_checkpoint_scan.py](test_checkpoint_scan.py) builds every case in a temporary directory, with `HOME` pointed at
it, an empty global git config and no system git config, and a local bare repository as `origin`, so your own git
settings and hooks never apply and nothing touches the network. The process tests start a child with its working
directory inside a repo. The disk, swap and `/proc` cases load the script as a module and replace the machine's answers.

```bash
python3 -I test_checkpoint_scan.py      # from this folder; takes under a minute
```

52 tests pass (run on 2026-11-22, macOS, Python 3). Each of 43 deliberate breaks of the script made at least one test
fail, in these groups:

<details>
<summary>The 43 deliberate breaks</summary>

- Disk: the floor tested with `<=` instead of `<`; no warning set for low disk.
- Exit codes: the exit-2 check ranked below the exit-1 check; a path that is not a repo never failing the run; findings
  never exiting 1; the no-argument run outside a repo exiting 1; a listed process not exiting 1; the `ps` failure not
  setting exit 2; a live undescribed process not setting exit 1; `no remote` worrying; `no remote branch` alone exiting 1;
  the unexpected-error wrapper exiting 1 or removed.
- Worktree state: the uncommitted count capped at 1; each of merge, rebase, cherry-pick and revert not detected (four
  breaks); a relative git path not joined to the worktree; no comparison with `origin/<branch>` when there is no
  upstream; unpushed commits not reported; behind-remote not reported; a detached worktree compared with a remote; a repo
  named twice listed twice; the stash count always 1; the singular stash wording lost; the `--not --remotes` count
  ignored; a repo with no remote flagged as `no remote branch`; the commit count's singular wording lost.
- Processes: a path prefix matched without a separator; the scan and its shells listed; the caller's sibling processes
  listed; the ancestor walk stopping after the scan itself; the command line printed; processes outside the repos listed;
  the `lsof` output parsed without its PIDs; the `os.kill` existence check removed; `PermissionError` treated as ended;
  the `ps failed` reason left out; the `already ended` line printed while a process still runs.
- Other: swap read on every platform; no `none` line when nothing is found; `realpath` replaced by `abspath` for the
  roots.

</details>

The tests are skipped when the machine itself has under 5 GiB free, because the scan then exits 1 by design.

## Files

| File | What it is |
| --- | --- |
| [SKILL.md](SKILL.md) | the procedure the agent follows: the seven checkpoint steps, the resume steps, the resume block's shape, the traps, and what to do when a step cannot conclude |
| [checkpoint-scan.py](checkpoint-scan.py) | the read-only inventory: machine, worktrees, processes |
| [test_checkpoint_scan.py](test_checkpoint_scan.py) | its tests |
| README.md | this page |
