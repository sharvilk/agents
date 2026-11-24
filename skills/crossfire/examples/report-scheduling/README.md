# Example: report scheduling

A whether-mode review: should a nightly report move from cron on one server to a managed job queue? Two traps were
planted. It is the eval case `report-scheduling`; how the evals work is in
[../../evals/README.md](../../evals/README.md).

## Table of contents

- [The project](#the-project)
- [The question and what was planted](#the-question-and-what-was-planted)
- [The run](#the-run)
- [What crossfire returned](#what-crossfire-returned)
- [Scored against the answer key](#scored-against-the-answer-key)
- [What we learned](#what-we-learned)

## The project

[repo/](repo/) is the same made-up notes app, here with a nightly usage report:

| File | Why it is there |
| --- | --- |
| [AGENTS.md](repo/AGENTS.md) | the house rules: background work that must survive a restart runs on the queue; every email through the mailer |
| [docs/questions/report-scheduling.md](repo/docs/questions/report-scheduling.md) | the question under review, with three options |
| [ops/crontab](repo/ops/crontab) | the report runs from cron on one server only |
| [jobs/usage-report.js](repo/jobs/usage-report.js) | the report: one email per workspace admin, about 3,000 workspaces, about 12 minutes a run |
| [src/queue/README.md](repo/src/queue/README.md) | the queue: delivers at least once; a job not finished within 5 minutes goes to another worker |
| [src/mail/send.js](repo/src/mail/send.js) | the mailer, which queues and retries |

## The question and what was planted

The report was skipped twice when its one server was replaced at 02:00. The options:
- **O1:** keep cron, and add an alert when the report does not run;
- **O2:** move the report to the queue as one scheduled job that calls the existing code unchanged;
- **O3:** a scheduled job that enqueues one job per workspace.

What matters: every admin gets exactly one report a night, it survives a server being replaced, and the effort is
small. Two traps were planted for any option that uses the queue:

| Planted trap | Why it matters |
| --- | --- |
| The queue delivers at least once, and the job keeps no record of what it sent | a redelivery emails admins twice |
| The 12-minute job runs under a 5-minute visibility timeout | O2 as written hands the job to a second and third worker every night |

## The run

`/crossfire docs/questions/report-scheduling.md whether`, on 2026-11-12, with the first version of the skill.

```
 depth: STANDARD (picked: the options would add runtime code, a queue worker or a fan-out job)
 seats: advocate (sonnet) · pre-mortem (opus) · reliability, architecture, testing (sonnet)
 not seated: performance, infrastructure, cost, product, privacy, security (each with a reason)
 agent calls: 14 = 5 drafts + 1 cross-examination (the advocate) + 7 verifiers + 1 chair
 time 20.1 min · cost $8.18 (list price, as the session reported) · 96% of it on Opus
```

## What crossfire returned

**Gate: STOP**, on a fact only the owner had, with three verified blockers against O2 as written.

The recommendation was **O2, with conditions**: the smallest change that meets the asks, once the job's timeout is
raised, a sent record stops repeats, and dead letters raise an alert. O1 still loses the report when the server is
replaced; O3 costs more and needs the same record. The summary drew the failure:

```
O2 as written, one night
02:00  worker A: run() from workspace 1 ──────────────────────── ~02:12 done
02:05            timeout → worker B: run() from workspace 1 ──────────▶
02:10                      timeout → worker C: run() from workspace 1 ────▶
       result: admins early in the loop get 2-3 copies, every night        (C1)
```

| ID | Severity | Blocks | Finding | Status |
| --- | --- | --- | --- | --- |
| C1 | major | yes | the 12-minute run outlasts the 5-minute timeout; set it to about an hour | open |
| C2 | major | yes | no record of who was sent the report, so a server replaced mid-run re-sends to everyone already done | open |
| C3 | major | yes | nothing alerts on the dead-letter queue, so admins notice first, as today | open |
| C4 | major, depending on Q1 | no | nothing shows `queue.schedule` registers only once | question |
| C5 | minor | no | a retry after midnight UTC reports the wrong day | open |
| C6 | minor | no | a finished job does not mean the emails went out | open |
| C7 | minor | no | the mailer's own retries can repeat an email, under every option | follow-up |
| C8 | minor | no | no tests or CI, so none of these checks runs again | follow-up |

The three questions it asked:
1. Does `queue.schedule` keep one schedule when called from several servers, and in which timezone?
2. Is a rare second copy acceptable on a night a server is replaced? The ask says no.
3. Does the queue already alert on dead letters, outside this repo?

**What the panel changed.** The orchestrator's first view leaned to O3. The panel moved it to O2 with reasons: a
redelivered fan-out job re-queues every workspace, so O3 needs the same record and costs more. It also added the
dead-letter alert, the schedule question, the wrong-day retry and the case for keeping the timeout short.

## Scored against the answer key

| Planted trap | Result |
| --- | --- |
| duplicate sends under at-least-once delivery | caught (C1, C2) |
| visibility timeout shorter than the run | caught (C1) |

The case's key accepts any gate, since it is about the traps being surfaced. Two blocking rows were not in the key,
and both are real: the re-send after a server is replaced (C2) and the missing alert (C3).

## What we learned

- **Whether-mode works.** It compared all three options, recommended one with conditions, and said why the others
  lost.
- **The sealed first view earns its place.** It shows the panel changed the recommendation, not just restated it.
- **It found what was not planted.** The wrong-day retry after midnight and the missing alert were real.
- **The chair needed a stricter format.** It wrote "if Q1 is one per process" in a cell a script reads. The chair's
  brief now fixes each cell to one value.
