---
name: todo-sync
description: Keep each session's TODO list complete and current in its own file — nothing leaves the list unless it is done or the user agreed to drop it. Use at the start of a session, after any compaction, before rewriting the list, when the user says "check the todos" / "did you lose anything" / "go back in your history", when your part of an initiative wraps up, when the user says "close this initiative", "we're done with <initiative>", "wrap up this initiative", "close out my todo list" or "clean up old todo lists", and before reporting work complete. A subagent keeps no list; it reports open items to its parent.
---

# todo-sync

**A todo list whose heading is `## Loop state: ARMED` or `## Loop state: PAUSED` is never deleted, in any session's file.**

- That holds for "wrap up", "close out", "close this initiative" and "clean up old todo lists" alike: show that
  heading and skip that list.
- Skipping applies to deletion only: for this session's own list, todo-sync still closes its own part.
- **If this session's own list has such a heading owned by another skill:** "wrap up" or "close out" closes your part
  as below but never deletes the list and never removes that skill's blocks (the heading, its `Answers:` and `Owns:`
  lines, and every section the `Owns:` line names). Reorganize-before-prune and recovery keep those blocks whole.
- The owning skill ends its loop and writes ENDED; only then may the list be closed out.

The list is a commitment, not a scratchpad. An item that disappears reads as "done", so nothing leaves
the list without being confirmed.

## The rule

**Never remove an item without confirming it.** An item leaves the open list only when it is done, with
evidence (a PR, a commit, a verification), or when the user agreed to drop it. Dropped items move to a
Dropped section with the reason; they never vanish. Add freely. Rename, regroup and restructure freely.

**Reorganize-before-prune.** When rewriting the list, copy every open item across *first*, verbatim, then
trim done ones. Diff the new list against the old before saving — if anything open disappeared, restore
it. That diff is the safety net, so don't make backup copies of the file.

**Keep the detail.** If an item carries specifics — per-part lists, file paths, PR numbers, IDs,
sub-bullets — those travel with it. Collapsing five named follow-ups into "part follow-ups" loses the
work just as effectively as deleting them.

## Where the list lives

Each top-level session keeps its own list, one file per session, in the list folder:

`~/.claude/todo-sync/<initiative>/<session-id>.md`

- When `CLAUDE_CONFIG_DIR` is set, the list folder is `$CLAUDE_CONFIG_DIR/todo-sync/` instead: it sits in the
  same config folder as the session's transcript. Find the absolute path once, with
  `echo "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todo-sync"`, and give the file tools that path.
- `<session-id>` is this session's id: `${CLAUDE_SESSION_ID}`. If the value is empty or not a UUID, take the directory
  just above `scratchpad` in your scratchpad path, when the session has one; otherwise ask.
- `<initiative>` is short `kebab-case`. Reuse the existing folder if there is one.
- **A list started before the list folder existed stays where it is.** Earlier versions of this skill kept lists in
  `<config>/todos/<initiative>/<session-id>.md`, where `<config>` is `~/.claude` or `$CLAUDE_CONFIG_DIR`. If this
  session's list is there and not in the list folder, keep reading and writing it there until the session ends: don't
  move or copy it. New lists always go in the list folder. Never open, move or report other sessions' files in
  `todos/` unless the user names one or asks to clean up old lists (below). Before you create a list, and again after each
  compaction, look for your own in both places by its id. Put your session id (above) in place of `<session-id>` in
  the command. A subagent doesn't run this: the id is its parent's.

  ```bash
  find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todo-sync" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todos" -mindepth 2 -maxdepth 2 -name '<session-id>.md' 2>/dev/null
  ```

  It exits 1 when a folder does not exist yet; what it prints is the answer. If it finds the list in both, the
  list folder's copy is your list, even when the two sit under different initiative folders. Copy into it any open
  item that is only in the other copy before your next write, tell the user, and ask whether to delete the other
  copy; until they say so, repeat this at each session start and after each compaction.
- **A subagent keeps no list file.** It shares its parent's session id and scratchpad, so "its" file
  would be the parent's. It puts its open items in its report to the parent instead; if it needs a working
  list during a long task, it keeps one in the scratchpad (or a temporary folder when the session has none),
  named for its task, never in the list folder.
- **Write only your own file, and don't copy other sessions' lists into it.** The other files in the
  folder are other agents' work.
- Continuing another session's work in a new chat? Ask the user which session's file it is, and take it
  over only when the user says that session won't be resumed for this work: two sessions writing one
  file overwrite each other. Otherwise start your own list, copy nothing into it, and point to the other.
- If the session has a todo tool (`TodoWrite`, or the task tools `TaskCreate`, `TaskUpdate` and `TaskList`), use
  it as your in-session view, but the file is your working list: update both in the same turn. Without one, the
  file is the list.

The file is not a handoff: anything another agent or a later session needs goes in the repo, in a committed
and pushed doc. A project's tracker in its repo is separate.

**The folder holds todo lists only.** `<initiative>/` contains `<session-id>.md` files and nothing else —
no scratch, working files, harnesses, copies of repo code, logs, JSON, backup copies, subfolders or
symlinks. A list folder used as a scratchpad can grow to thousands of files, copies of other
repositories' source and symlinks, and a git backup of the config folder that holds it can then fail on every
run. If you keep your config folder in git as a backup, ignore everything in the list folder
except the lists (`/todo-sync/*/*` with `!/todo-sync/*/*.md`), and note that a file git already tracks stays
tracked after you ignore it. A backup copy of a list adds nothing: the diff before saving and the transcript
already cover it.

Throwaway scratch goes in the session scratchpad, or a temporary folder when the session has none. Working
files needed across sessions or days go in a repo — a committed doc, or a gitignored folder in that project's
main checkout — never elsewhere in the config folder. Untracked is not ignored: add the folder to that
checkout's `.git/info/exclude`, which is never committed, and confirm with `git check-ignore <folder>`;
otherwise one `git add -A` commits it. Not a folder in a branch worktree: removing the worktree after its PR
merges deletes ignored files without a warning.

## What goes in the file

Only what you need to act on:

- **Open** — each with enough context to act on later: branch, PR, file, ID.
- **Waiting on the user** — decisions raised, not acted on.
- **Done** — with evidence.
- **Dropped** — with the reason.

Nothing else is persisted there. Save a general lesson to memory when you learn it. Methods, research and
handoff docs go to the project's docs, committed and pushed. Throwaway output goes to the scratchpad.

## At session start and after compaction

At session start, check the folder first:

```bash
python3 "${CLAUDE_SKILL_DIR}/check-todos-folder.py"
```

It lists, one line each, anything in the list folder that is not a todo list. It exits 1 if it found something,
or 2 if part of the folder could not be read. A subfolder is reported once, with its file count. Tell the user
what it lists; don't move or delete any of it — another agent may still be using it, and the user decides where
it goes.

Then read your own file (in the list folder, or in `todos/` for a list started before it) — not the whole folder. A
new session has no file yet: if its work continues an
earlier session's, ask which file (the takeover case above). If your list is missing, or looks shorter
than the work, recover before rebuilding: a fresh list written from memory silently ratifies whatever was
dropped.

## Recovering a lost list

Use every source you have; each holds what the others miss. Look in the transcript of the session that wrote the list. After a
new session starts, that is the earlier session. The transcript is
`<config>/projects/<project-folder>/<session-id>.jsonl`, where `<config>` is `~/.claude` or
`$CLAUDE_CONFIG_DIR`, and `<project-folder>` is the working directory's path with every character other than
letters and digits replaced by `-`. `ls <config>/projects/*/<session-id>.jsonl` finds it. Subagents' calls are in
`<project-folder>/<session-id>/subagents/agent-*.jsonl`. Each file is JSON Lines, one object per line.

1. **The list's own edits in the transcript.** Every Write, Edit or Bash call that changed the file is
   still in the transcript, including the ones from before compaction. Take the `tool_use` blocks whose
   input contains the file's name, `<session-id>.md` (paths appear as `~/…`, `$HOME/…` or absolute), and
   replay them in order: from the call that created the file, or, when the config folder is backed up in git, the calls after its
   newest backed-up version, on top of that version.

2. **The todo tool's calls**, if the session had one. Count them first:

   ```bash
   F=<config>/projects/<project-folder>/<session-id>.jsonl
   grep -c -e '"name":"TodoWrite"' -e '"name":"TaskCreate"' -e '"name":"TaskUpdate"' "$F"
   ```

   `TodoWrite` rewrites the whole list on every call. In Python: parse each call's `todos` array, **cluster
   the items by similarity** (≈0.70 ratio), and take each cluster's **latest** status. The task tools create
   and update one item at a time: a `TaskCreate` call's result, not its input, holds the new item's id, and each
   update names that id. Match them by id and take each item's latest status.

3. **The backup's history**, if you keep the config folder in git. The list has one version per backup
   commit that changed it; anything edited since the last commit is only in the transcript. For a list kept in
   the old folder, put `todos/<initiative>/<session-id>.md` in place of the path below:

   ```bash
   git -C <config> log -p -- todo-sync/<initiative>/<session-id>.md
   ```

Traps, each of which produces a wrong answer:

- **Keying on the exact string.** Items get reworded between calls, so a reworded item never inherits
  its own `completed` and looks dropped. Cluster first.
- **Naive call-to-call diffing.** Reports hundreds of false drops for the same reason.
- **Taking "ever completed" instead of the latest status.** A reopened item then looks done.
- **Trusting the cluster count as truth.** Items pruned as done without an explicit status change still
  look open. Expect to hand-review.
- **Globbing across `~/.claude/projects`.** The folder names start with `-`, so `grep … */*.jsonl` reads
  them as options and silently matches nothing. Use `./*/*.jsonl` or `--`.
- **Guessing the project folder from the repo path.** Every non-alphanumeric character becomes `-`, so
  `my_app` is `-Users-…-my-app`, not `…-my_app`. Find the transcript by its session id instead.

## When you cannot prove an item is done

Keep it. Put it in an **Unverified** section with a note on what is probably shipped and why, and ask the
user to confirm or drop each one. Judgement that isn't written down is judgement that gets lost.

State the uncertainty plainly. "I mined 50 calls, curated 11 verified drops, and 149 clusters I could not
confirm — listed under Unverified" is a real answer. "Yes, I have them all" is not, unless you can show it.

## Staying in sync

- **On completing work:** mark it done in the same turn, with its evidence — not at a later checkpoint.
- **On discovering work:** add it immediately, with enough context to act on later. Future-you will not
  remember what "fix the thing" meant.
- **Before reporting done:** re-read the list. Anything still open goes in the reply as remaining work.
- **On handing off:** every open item stays in your list. The handoff itself — context, decisions, how to
  continue — goes in a committed, pushed doc, and the list points to it.

## Closing out

Never delete a list that still has an open item the user has not accepted as done, dropped or moved. Delete your
own list only after step 2 below. Delete another session's list only when the user names it, after you have shown
them its open items.

**Moving an item** means it is already written in the place the user names: a committed doc, or the list of the
session that will carry the work, which that session writes, never you. Show the user where it is written; only
then does it count as moved.

**When your part of the initiative is finished** ("wrap up" or "close out" mean this, never the whole initiative):

1. Sort the lessons. General ones go to memory — update an existing entry rather than adding a
   near-duplicate. Methods go to the project's docs.
2. Confirm with the user that every open item in **your** list is done, dropped or moved.
3. Delete your own list, in whichever folder it is. The other files in the folder are other agents' lists: delete
   one only when the user names it, after you have shown its open items.
4. Remove the initiative's folder only once it is empty, with `rmdir`, which refuses a folder that still holds
   anything.

**When the user closes the whole initiative** ("close this initiative", "we're done with <initiative>"):

1. Find every list of the initiative, in both folders, with the initiative's name in place of `<initiative>`,
   inside the quotes. Use `find`, not a bare glob: in zsh a glob with no match aborts the command.

   ```bash
   find "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todo-sync/<initiative>" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/todos/<initiative>" -maxdepth 1 -name '*.md' 2>/dev/null
   ```

   If it prints nothing, check the name against a listing of the list folders before concluding there is nothing
   to close. A `.md` file whose name is not a session id is not a list: report it, and don't delete it.
2. Close out your own list as above.
3. For each other list, show the user its open items and ask whether that session is still running: a running
   session keeps writing its list. Delete it only when the user confirms, and only once each of its open items is
   done, dropped with a reason, or moved somewhere the user names. A blanket yes ("all of them") is not enough:
   show each list's open items first, and delete only the lists the user confirms one by one.
4. Remove each of the initiative's folders only once it is empty, with `rmdir`.

Never delete a list because it looks old.

## Cleaning up old lists

Many sessions end without closing out, so their lists stay. When the user asks ("clean up old todo lists"), run:

```bash
python3 "${CLAUDE_SKILL_DIR}/list-old-lists.py"
```

It only reads. It prints one line per list that has not changed for 14 days (`--days N` changes that), oldest
first: the date, the folder, the initiative, the session id and an approximate count of open checkboxes. Show the
user its table, and ask which lists to close.

For each list they pick, show its open items. A blanket yes ("all of them") is not enough: show every picked list's
open items first. Delete a list only when the user confirms that list, and only once each open item is done,
dropped with a reason, or moved somewhere the user names.

- **A list untouched for a while can still belong to a session the user means to resume.** The user decides, never
  you.
- **Never run the script on a schedule, and never delete on its output alone.**
- **The listing covers the old `todos/` folder too.** This is the one place the skill reports other sessions' files
  there, because the user asked.
