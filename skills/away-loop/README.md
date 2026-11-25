# away-loop: keep a session working while you are away

A Claude Code skill for the hours you are not at the keyboard: overnight, on a flight, in a long meeting. It writes
a plan into the session's todo list, schedules a wake-up every 30 minutes (using Claude Code's scheduled tasks; the
diagram below shows them as `CronCreate`, `CronList` and `CronDelete`), and on each wake-up (a "tick") does the next
step that is not blocked, decides what the agent may decide, and queues what only you can. It stops on your first
message back and gives you one summary.

## Install

As a plugin, from the `agents` marketplace:

```
/plugin marketplace add sharvilk/agents
/plugin install away-loop@agents
```

That also installs `todo-sync`, because the plugin declares it as a dependency.

Or copy the `away-loop` and `todo-sync` folders to `~/.claude/skills/` (or `$CLAUDE_CONFIG_DIR/skills/`). Nothing
needs registering: Claude Code finds each skill by the `name` and `description` at the top of its `SKILL.md`. Start
a new session afterwards. To check it loaded, ask for it by name ("use away-loop, I'm going to sleep"); that arms a real loop, so
say "I'm back" to stop it.

`checkpoint` is optional. When it is installed, the loop uses it for a restart or a quit instead of carrying on.

It has no script, so there is nothing else to run or install, and it has no tests.

## Quick start

Say "I'm going to sleep", "keep working while I'm away" or "work overnight". The agent writes the plan into the todo
list, schedules the wake-ups, and tells you in a few lines what will run and what stays yours. When you come back,
say "I'm back" (or any message): it stops the loop and gives you one summary.

## Table of contents

- [Install](#install)
- [Quick start](#quick-start)
- [Why it exists](#why-it-exists)
- [How a tick works](#how-a-tick-works)
- [What it stores, and where](#what-it-stores-and-where)
- [Examples](#examples)
- [Errors and what you see](#errors-and-what-you-see)
- [Limits](#limits)
- [Working with a loop skill](#working-with-a-loop-skill)
- [Files](#files)

## Why it exists

Left alone, a session stops at the first thing that needs you, and the night is lost. Told "carry on", it can do
too much: merge, delete, change settings. This skill sits between the two. It keeps the work moving, writes down
every decision it took so you can overturn any of them, and never touches the short list of things that stay yours
(merges you did not name, deletes, production writes, settings, big decisions).

## How a tick works

```
 start ──► plan in the todo list ──► CronCreate (recurring, every 30 min) ──► tell you what runs
   │            (CronCreate refused or off: nothing is armed, and you are told)
 tick ──► plan missing or consumed? ──yes──► delete its own job, stop
   │ no
   ▼
 job older than 6 days? ──yes──► CronCreate the new job ► record it ► CronDelete the old one
   │ no                                                     ► CronList: exactly one
   │                          (CronCreate fails: keep the old job, say when the wake-up ends)
   ▼
 machine check ──► act on finished agents ──► check every PR the session opened ──► next step
   │                                                                                    │
   │                          log what it decided ◄──── queue what only you can decide ◄┘
   ▼
 one status table  (about every 2 hours, or at a milestone: the full status report instead)
   │
 stop (your first message back, or the end time) ──► CronDelete every recorded job
   │                                                  ──► CronList: none left
   │                                                  ──► re-check the sources ──► one summary
```

The procedure is [SKILL.md](SKILL.md). The agent loads it by its description when you say "I'm going to sleep" or
"keep working while I'm away", and again when you say "I'm back".

- **The tick prompt is stored with the job.** Each tick starts with no memory of earlier ticks, so the prompt tells it to read the plan, the
  decisions and the waiting list from the todo list before it acts.
- **Ticks add only what is new.** A tick with nothing new says so in one line.
- **About every 2 hours, and at each milestone, a tick posts a full status report instead of the table.** It has
  seven sections: the phases, the build, the merge queue, what changed, time to completion, what is left and what it
  needs from you.
- **The tick prompt starts with "Away-loop tick".** That prefix is how the agent tells a tick from your own first
  message. A tick that finds no plan, or a plan marked consumed (for example a job restored with a resumed
  session), deletes its own job and says so in one line.
- **The job lives in the session.** Scheduled tasks are scoped to the session. Claude Code runs them only while it
  is running and idle, and restores them, unless expired, when the session is resumed.

## What it stores, and where

| What | Where | Written by |
| --- | --- | --- |
| The plan, the decisions and the queue | the top of the session's todo list, which the `todo-sync` skill keeps | the agent |
| The wake-up's id and creation time, the return one-shot's id and time, and the time of the last full report | the same list | the agent |
| A full status report (optional) | the project's progress folder, if it keeps one, as `YYYY-MM-DD-HHMM-status.md` | the agent |

The todo list has three sections added by this skill (SKILL.md calls the list "the todo file": it is the same
thing):

- **Away plan:** the open items in the order they will be worked, each with its branch, PR, file or command, and its
  next step.
- **Decisions made while away:** one entry per decision, with the time, the decision and the reason.
- **Waiting for you:** every item that needs you, with what was prepared for it.

Where the list lives is `todo-sync`'s business, including a list started before its current folder existed. See its
README. A saved report is a snapshot and is never edited. If the project has no progress folder, the agent offers to
start one the first time.

## Examples

**An away plan** at the top of the session's todo list (the header is one line in the list; it is wrapped here to fit):

```md
## Away plan (started 2026-11-22T23:10+0000,
   wake-up 3f9a2c1d created 2026-11-22T23:12+0000,
   return one-shot 8b41e07a at 2026-11-23T07:33+0000,
   last full report: 2026-11-22T23:10+0000)
1. PR 37 (fix/csv-escape): wait for CI, then address review comments
2. Import dates (fix/import-dates): builder running; next, an independent review
3. README example for the export command (docs/export-readme)

## Decisions made while away
(none yet)

## Waiting for you
(none yet)
```

**A status table**, posted on a tick:

| | |
|---|---|
| Finished | PR 37 CI is green; one review comment fixed and its thread resolved |
| Started | review of the import-dates fix, because its builder reported |
| Decisions | 02:03 kept the old column order (the export tests depend on it) |
| Running | one reviewer on the import-dates fix |
| Blockers | PR 48 waits for a decision on refunded invoices (queued) |

**The return summary**, on your first message back:

```
Good morning. Summary of the night (2026-11-22 23:12 to 2026-11-23 07:40):
1. Production / shared systems: nothing changed.
2. Needs you: (a) merge 37 48 once you have read PR 48; (b) should exports include refunded
   invoices?
3. PRs: 37 green, ready for your merge; 48 open, one thread waiting on (b).
4. Decisions: 02:03 kept the old column order. Overturn it by saying so.
5. Drafts waiting: a reply to the reviewer on PR 48.
6. Next: the README example, after (a).
```

After a run of more than about 4 hours, the summary comes as the full status report, with these items inside its
sections.

## Errors and what you see

| What happens | What you see | What to do |
| --- | --- | --- |
| `CronCreate` is not in the tool list, or scheduling is turned off (`CLAUDE_CODE_DISABLE_CRON=1`) | before you leave: the session cannot wake itself, so nothing will run while you are away. It offers to work until the current step is done and then stop with a summary | enable scheduling and ask again, or accept the shorter run |
| The scheduling call is refused by a permission check | the same message. It never says a wake-up exists, and does not retry around it | allow the call, or accept the shorter run |
| The `todo-sync` skill is not available | before you leave: it says so, and keeps the plan in a file you name, or in the project's planning doc | install `todo-sync`, or name the file |
| The wake-up is older than 6 days | on that tick, a new recurring job with the same prompt is created and recorded first, then the old one is deleted, then `CronList` confirms exactly one | nothing |
| That re-arm fails (scheduler off, permission refused, a task limit) | the old job stays; the status table and "Waiting for you" say "wake-up ends when the old job expires (7 or 30 days after <old creation>, by version); could not re-arm" | allow scheduling and ask for a new loop before then |
| The job expired anyway (7 or 30 days passed, by version, so it fired one last time and deleted itself) | after that last tick, no more ticks; the todo list still holds the plan | ask the agent to arm a new loop |
| A job fires in a resumed session whose plan is gone or consumed | the tick deletes its own job and says so in one line | nothing |
| A tick cannot run its step (CI down, disk low, a refused action) | the status table names it under Blockers; a refused action goes in "Waiting for you" | read the queue when you return |
| Every pipeline fails the same way at once | the agent checks the provider's status page first and reports an outage instead of debugging | wait for the provider |
| You send a message while it works | the loop stops: it deletes the job, re-checks the sources and gives the summary | nothing |

## Limits

- **Ticks fire only while Claude Code is running and idle.** A closed app or an exited session means no ticks, and
  while the machine sleeps Claude Code is not running, so nothing fires. A tick due while the agent is busy fires
  once when it becomes idle, not once per missed interval.
- **A tick can run late.** A recurring job starts up to half its period late, so a 30-minute loop can run up to 15
  minutes late. The tick uses off-peak minutes, for example `3,33 * * * *`, and the return one-shot is pinned to a
  minute that is not :00 or :30, where one-shots can fire up to 90 seconds early.
- **Full reports follow elapsed time**, about every 2 hours from the `last full report` time in the plan header,
  because ticks start cold and missed ticks collapse into one fire.
- **A recurring job expires 7 days after creation on Claude Code versions before 2.1.330, and 30 days from 2.1.330
  on.** It fires one last time and then deletes itself. The skill re-arms it on the first tick after day 6 (safe for
  both limits), creating the new job before deleting the old one. A loop is meant for hours, so this matters only
  for a long absence.
- **It acts only within the session's own permissions.** It does not widen what you approved: merges you did not
  name, deletes, production writes, settings and big decisions are queued for you.
- **It is a procedure, not a lock.** The agent follows it because the skill says so. Its rules (open pull requests
  ready for review, never as drafts; one final verdict per phase; one install-heavy job at a time through the
  project's heavy-work lock; what stays yours) are defaults that a project's own rules override.
- **It needs the `todo-sync` skill** for the plan and the queue.

## Working with a loop skill

Another skill can run its own background loop and mark the session's todo list with a `## Loop state:` heading. While
that heading says ARMED or PAUSED, away-loop never arms and does not stop that loop. The phrases on the heading's
`Answers:` line go to that loop. For an arming phrase that is not on that line, away-loop says in one line which loop
owns the session and how to stop or resume it. In this repo, `on-loop` is the skill that writes that heading.

## Files

| File | What it is |
| --- | --- |
| [SKILL.md](SKILL.md) | the procedure the agent follows: start, each tick, stop, traps and what it does not do |
| README.md | this page |

