# todo-sync

A Claude Code skill that keeps each session's todo list complete. The list is a plain Markdown file, one per
session, and nothing leaves it unless it is done, with evidence, or you agreed to drop it. When a list goes missing
or comes back short, the skill rebuilds it from the session's own transcript.

## Table of contents

- [Why](#why)
- [How it works](#how-it-works)
- [What it stores, and where](#what-it-stores-and-where)
- [Install](#install)
- [Examples](#examples)
- [The folder check](#the-folder-check)
- [The old-list listing](#the-old-list-listing)
- [Errors and what you see](#errors-and-what-you-see)
- [Limits](#limits)
- [Files](#files)

## Why

A long session loses work in a quiet way. Compaction summarises the conversation, and an open item can fall out of
the summary. An agent rewriting its list collapses "fix the three named follow-ups" into "follow-ups". A new session
rebuilds a list from memory, and whatever memory missed is gone. Nothing errors: the item just reads as done.

todo-sync makes the list a commitment. It lives in a file outside the conversation, so compaction cannot touch
it. Every rewrite copies the open items first and diffs against the old list before saving. When the list is lost
anyway, the transcript still holds every edit the session made to it.

A todo list whose heading is `## Loop state: ARMED` or `PAUSED` is never deleted, in any session's file, including through "wrap up", "close out", "close this initiative" and "clean up old todo lists": todo-sync shows that heading and skips the list. Reorganizing or recovering a list keeps that skill's blocks whole.

## How it works

```
 Figure 1: one session's list (what the skill tells the agent to do)

  session starts ─────► check-todos-folder.py ───► anything that is not a list? ──► tell the user
        │
        ▼
  read its own file  ~/.claude/todo-sync/<initiative>/<session-id>.md
        │           (a list started before that folder existed: ~/.claude/todos/…, used where it is)
        │                   ▲
        │ work              │ write: open items copied first, then done ones trimmed,
        ▼                   │        then diffed against the old list
  complete / discover ──────┘
        │
  compaction or a new session ──► file missing or short? ──► recover from the transcript, the todo
                                                             tool's calls and the backup (if any)
        │
  part of the work finished ──► every open item done, dropped or moved? ──► delete its own file
        │
  user closes the whole initiative ──► find every list of it in both folders ──► own list closed out;
        │                                for each other list: show its open items, ask whether that
        │                                session still runs, delete only on the user's yes
        │
  user asks to clean up old lists ──► list-old-lists.py (read-only) ──► table ──► user picks lists ──►
                                      each pick: show open items, delete only on the user's yes
```

The skill is the procedure in [SKILL.md](SKILL.md). The agent loads it by its description: at the start of a
session, after compaction, before rewriting a list, when you ask "did you lose anything", and before it reports
work complete, and when you say "close this initiative", "we're done with <initiative>", "wrap up this initiative",
"close out my todo list" or "clean up old todo lists". A bare "wrap up" or "close out" closes only that session's
part, never the whole initiative, and no list is deleted without your yes for that list. The two scripts, [check-todos-folder.py](check-todos-folder.py) and
[list-old-lists.py](list-old-lists.py), only read.

- **One file per session.** Two sessions on the same work keep two files, so they never overwrite each other. A
  session continuing another's work takes over its file only when you say the other session won't resume.
- **Subagents keep no list.** A subagent shares its parent's session id, so its file would be the parent's. It
  reports its open items to the parent instead.
- **Closing is confirmed, list by list.** An agent deletes its own list once every open item is done, dropped or
  moved. When you close a whole initiative, it shows you each other session's open items and asks whether that
  session is still running, since a running session keeps writing its list; it deletes a list only on your yes. A
  list is never deleted because it looks old.
- **Cleanup is on demand.** Many sessions end without closing out. When you ask, the agent runs
  `list-old-lists.py`, shows you the table of lists untouched for 14 days or more, and closes the ones you pick,
  after showing each one's open items. Nothing runs it on a schedule, and nothing is deleted on its output alone.
- **The todo tool is a view.** When the session has `TodoWrite` or the task tools (`TaskCreate`, `TaskUpdate`,
  `TaskList`), the agent uses it for the panel, and keeps the file as the list.

## What it stores, and where

| What | Where | Written by |
| --- | --- | --- |
| One list per session | `~/.claude/todo-sync/<initiative>/<session-id>.md`, or `$CLAUDE_CONFIG_DIR/todo-sync/…` when that is set | the agent, through its file tools |
| A list started before that folder existed | `~/.claude/todos/<initiative>/<session-id>.md`, used where it is until its session ends, never moved | the agent, as above |
| Nothing else | | the folder check reports anything else found there |

`<initiative>` is a short kebab-case name for the piece of work, shared by every session on it. `<session-id>` is
the session's id, which the skill reads from `${CLAUDE_SESSION_ID}`.

A list has four sections: **Open** (each item with what is needed to act on it later: branch, PR, file, id),
**Waiting on the user**, **Done** (with evidence) and **Dropped** (with the reason).

**Why not `~/.claude/todos/`?** It is a legacy folder that current Claude Code no longer writes, and its cleanup
deletes files there once they are older than `cleanupPeriodDays`, 30 days by default. A list kept there disappears
after a month. Earlier versions of this skill kept lists there, so a session whose list is already there keeps using
it in place until it ends: the skill looks there only for the session's own id, and every new list goes to
`todo-sync/`.

**Backing it up.** The lists are plain files in your config folder. If you keep that folder in git, ignore everything
in the list folder except the lists, so a stray working file never reaches the backup:

```gitignore
/todo-sync/*/*
!/todo-sync/*/*.md
```

## Install

As a plugin, from the `agents` marketplace:

```
/plugin marketplace add sharvilk/agents
/plugin install todo-sync@agents
```

Or copy this folder to `~/.claude/skills/todo-sync/`. Nothing needs registering: Claude Code finds the skill by the
`name` and `description` at the top of `SKILL.md`. To check it loaded, ask for it by name ("use todo-sync to check
my list").

To make it the rule in every session, add a line to your `CLAUDE.md`:

```md
## Todo lists
Full procedure, including how to recover items lost to compaction, is the `todo-sync` skill.
```

The folder check needs Python 3.8 or later. It has been run on macOS only.

## Examples

**A list in use.** Session `0b9e7c1a-…` working on a billing export writes
`~/.claude/todo-sync/billing-export/0b9e7c1a-2f3d-4e5f-8a9b-0c1d2e3f4a5b.md`:

```md
# billing-export

## Open
- [ ] CSV export: escape commas in customer names (branch fix/csv-escape, PR 214, review pending)
- [ ] Follow-ups from review: (a) rename `toRow`, (b) test the empty-invoice case, (c) README example

## Waiting on the user
- Should exports include refunded invoices? Asked 2026-11-20.

## Done
- [x] Date column in ISO 8601 (merged in PR 209, verified with the March sample)

## Dropped
- PDF export: the user moved it to next quarter (2026-11-19).
```

On a rewrite, the three named follow-ups stay three named follow-ups. "PR 214, review pending" stays until the PR
merges.

**After compaction.** The agent reads its file, which compaction never touched, and carries on. If the file is
shorter than the work it remembers, it recovers before writing anything.

**Recovering a lost list.** The file was overwritten by a rewrite that dropped two items. The skill takes the
session's transcript, finds every Write, Edit or Bash call that touched `<session-id>.md`, and replays them in
order. It then reads the todo tool's calls and takes each item's latest status. With `TodoWrite`, which rewrites the
whole list each call, it groups reworded items by similarity first, so a renamed item keeps its status. Items it
cannot prove done go in an **Unverified** section for you to confirm.

**Closing an initiative.** You say "we're done with billing-export". The agent finds every list of it in both
folders and closes out its own as usual. For each other list it shows you the open items:

```
Other lists in billing-export:
  f1e2d3c4-b5a6-4978-8695-a4b3c2d1e0f9.md   2 open: "- [ ] README example", "- [ ] test the empty invoice"
Is that session still running? If not, are those two items done, dropped, or moved somewhere?
```

You answer "not running; the README one is done, drop the test", and it records the drop with your reason and then
deletes the list. Once `billing-export/` is empty, it removes the folder.

**Cleaning up old lists.** You say "clean up old todo lists". The agent runs the listing (see
[below](#the-old-list-listing)), shows you the table, and asks which to close. You pick, it shows each pick's open
items, and it deletes a list only when you confirm.

## The folder check

```bash
python3 ~/.claude/skills/todo-sync/check-todos-folder.py [list-folder]
```

By default it checks `<config>/todo-sync`, where `<config>` is `$CLAUDE_CONFIG_DIR` or `~/.claude`. It only reads,
and moves or deletes nothing. It reports, one line each:
- a file or symlink directly in the list folder (lists go in `<initiative>/`);
- in an initiative folder: a symlink, a subfolder (once, with its file count, never entered), a backup copy of a
  list (`.bak`, `.backup`, `presync` or `pre-sync` in the name), a file whose name holds a session id but is not
  exactly `<session-id>.md` (`<id>-notes.md`, `<id>.old.md`, `copy of <id>.md`), or a file that is not `.md`. A
  Markdown file with any other name passes.
- the list folder itself, when it is a file or a symlink rather than a real folder.

```
$ python3 check-todos-folder.py
/Users/me/.claude/todo-sync/billing-export/repo-copy/ -> subfolder (2413 files)
/Users/me/.claude/todo-sync/billing-export/results.json -> not a .md file
2 entries in /Users/me/.claude/todo-sync are not todo lists
$ echo $?
1
```

The agent shows you these and leaves them where they are: another session may still be using them, and where they
go is your call.

**Its tests:** [test_check_todos_folder.py](test_check_todos_folder.py) builds every case in a temporary folder, with
`HOME` and `CLAUDE_CONFIG_DIR` pointed at it, so it never reads your config folder:

```bash
python3 -I test_check_todos_folder.py      # from this folder
```

Run on 2026-11-21 with Python 3 on macOS: 19 tests passed. Each of twenty-two deliberate breaks of the script made
at least one test fail: another default folder; ignoring `CLAUDE_CONFIG_DIR`; no check for a file, or for a symlink,
directly in the list folder; a symlink in an initiative not reported; no check for files named after a session; the
session-id match anchored at the start; no backup-copy check; no `pre-sync` match; no check for files that are not
`.md`; `.DS_Store` not ignored; every hidden file ignored; a wrong subfolder file count; no "at least" on a count
that missed an unreadable folder; an unreadable initiative skipped silently; no "partly unreadable" report; an
unreadable list folder passing; an incomplete check exiting 1 rather than 2; the summary dropped when the check is
incomplete; the singular wording for two entries; a list folder that is a file passing; following a symlinked list
folder. The tests that make a folder unreadable are skipped when run as root, which can read anything.

## The old-list listing

```bash
python3 ~/.claude/skills/todo-sync/list-old-lists.py [--days N] [config-folder]
```

It lists every `<session-id>.md` directly inside an initiative folder of `<config>/todo-sync/` and
`<config>/todos/` whose modification time is more than N days ago (default 14), oldest first. `<config>` is the
folder argument, else `$CLAUDE_CONFIG_DIR`, else `~/.claude`. It only reads: it never deletes, moves or writes
anything. One line per list (date last changed, folder, initiative, session id, approximate count of open
checkboxes), then a summary line. Files whose names are not a session id and subfolders are ignored.

```
$ python3 list-old-lists.py
2026-09-30  todos (old folder)  search-index  f1e2d3c4-b5a6-4978-8695-a4b3c2d1e0f9  open: about 4
2026-10-18  todo-sync  billing-export  0b9e7c1a-2f3d-4e5f-8a9b-0c1d2e3f4a5b  open: about 2
2 lists untouched for more than 14 days; open counts are approximate (lines starting "- [ ]")
$ echo $?
0
```

An old list may belong to a session you mean to resume, so the table is a prompt for you to decide, not a list of
things to delete. The `todos` folder is read here only until the skill stops looking there for a session's own list;
both go out together.

**Its tests:** [test_list_old_lists.py](test_list_old_lists.py) builds every case in a temporary folder, with `HOME`
and `CLAUDE_CONFIG_DIR` pointed at it, so it never reads your config folder:

```bash
python3 -I test_list_old_lists.py      # from this folder
```

Run on 2026-11-24 with Python 3 on macOS: 25 tests passed. Each of 25 deliberate breaks of the script made at least
one test fail:
- the age comparison reversed; a different default for `--days`; days counted in hours; a negative `--days` accepted;
  `--days=N` not accepted;
- the `todo-sync` folder skipped; the `todos` folder skipped; `CLAUDE_CONFIG_DIR` ignored; a different default
  folder;
- names not required to be a session id; the session-id match not anchored; a subfolder named like a list counted; a
  symlinked initiative folder followed;
- the open-checkbox pattern matching any bracket, not allowing indentation, or matching mid-line;
- the sort reversed; the sort by session id;
- exit 3 for a bad argument; exit 1 for an unreadable folder; an unreadable folder reported with exit 0; exit 5 after
  a normal run;
- the singular wording for one list dropped;
- a write to a list's modification time; a file created in the list folder.

The tests that make a folder unreadable are skipped when run as root, which can read anything.

## Errors and what you see

| What happens | Exit | What you see | What to do |
| --- | --- | --- | --- |
| Everything in place | 0 | `OK - <folder> holds only todo lists`, or `OK - no list folder at <folder> yet` when it does not exist | nothing |
| Something in the list folder is not a list | 1 | one `<path> -> <what>` line each, then `<n> entries in <folder> are not todo lists` | move it: scratch to the session scratchpad, working files to a repo |
| The list folder is a file or a symlink | 1 | `<folder> -> not a real folder (a file or a symlink); lists go in a real folder` | replace it with a real folder |
| A folder cannot be read | 2 | `<folder> -> unreadable (<reason>)` for a whole folder, `<path>/ -> unreadable` or `partly unreadable` inside it (that subfolder's count then reads `at least <n> files`), then any summary lines above and `<n> folders could not be read; the check is incomplete` | fix its permissions and run it again; the report above it is incomplete |

**`list-old-lists.py`:**

| What happens | Exit | What you see | What to do |
| --- | --- | --- | --- |
| It ran, with or without old lists | 0 | the rows, then `<n> list(s) untouched for more than <N> days; open counts are approximate (lines starting "- [ ]")` | nothing |
| `--days` is missing, not a whole number, or negative | 1 | on stderr: `list-old-lists.py: --days needs a whole number of days, got '<value>'`, then `usage: list-old-lists.py [--days N] [config-folder]` | pass a whole number |
| An option it does not know | 1 | `list-old-lists.py: unknown option <option>`, then the usage line | remove the option |
| More than one folder given | 1 | `list-old-lists.py: only one config folder may be given`, then the usage line | give one |
| A folder or a list cannot be read | 2 | the rows it could read and the summary line, then `<path> -> unreadable (<reason>)` for each, then `<n> folder(s) or file(s) could not be read; the list is incomplete` | fix its permissions and run it again |
| A list's text cannot be read | 0 | `open: about ?` on that row | open the list yourself |

A config folder with no `todo-sync/` or `todos/` is not an error: it has nothing to list.

The skill itself raises no errors. When it cannot conclude, it says so: a list it cannot recover in full comes back
with an **Unverified** section, and a session that cannot tell its own id asks you.

Nothing watches it in the background. The check runs when a session starts.

## Limits

- **It is a procedure, not a lock.** The agent follows it because the skill says so. Nothing stops an agent that
  ignores the skill from overwriting a list.
- **Recovery needs the transcript.** Claude Code deletes transcripts older than `cleanupPeriodDays`. A list lost
  after that can come back only from a backup.
- **The folder check looks only at the list folder.** A list still in `~/.claude/todos/` is not checked.
- **Open counts in the old-list table are approximate.** It counts lines starting with `- [ ]` (after optional
  spaces); a list that marks open items another way shows `about 0`. The agent reads the list itself before
  anything is deleted.
- **Age is the file's modification time.** A copy, a restore or a backup tool that resets it makes an old list look
  recent, and a list touched by hand looks recent too.
- **Lists belong to one config folder.** A session run under a different `CLAUDE_CONFIG_DIR` keeps its lists
  there, and the folder check looks only at the current one.
- **Two sessions given the same file overwrite each other.** The skill avoids this by asking before a takeover; it
  cannot detect it afterwards.

## Files

| File | What it is |
| --- | --- |
| [SKILL.md](SKILL.md) | the procedure the agent follows |
| [check-todos-folder.py](check-todos-folder.py) | the read-only folder check run at session start |
| [test_check_todos_folder.py](test_check_todos_folder.py) | its tests |
| [list-old-lists.py](list-old-lists.py) | the read-only listing of old lists, run when you ask for a cleanup |
| [test_list_old_lists.py](test_list_old_lists.py) | its tests |
| README.md | this page |
