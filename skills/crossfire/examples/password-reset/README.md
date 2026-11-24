# Example: password reset

A deep review of a plan with five planted security and data defects. It is the eval case `password-reset`; how the
evals work is in [../../evals/README.md](../../evals/README.md).

## Table of contents

- [The project](#the-project)
- [The plan and what was planted](#the-plan-and-what-was-planted)
- [The run](#the-run)
- [What crossfire returned](#what-crossfire-returned)
- [Scored against the answer key](#scored-against-the-answer-key)
- [What we learned](#what-we-learned)

## The project

[repo/](repo/) is a made-up notes app, "Quillbox" (Node, Express, MySQL), with just enough code for reviewers to
cite:

| File | Why it is there |
| --- | --- |
| [AGENTS.md](repo/AGENTS.md) | the house rules: soft delete only, never log tokens, every email through one mailer, every handler tested |
| [docs/plans/password-reset.md](repo/docs/plans/password-reset.md) | the plan under review |
| [src/http/logging.js](repo/src/http/logging.js) | an access log that writes each request's full URL and is kept 90 days |
| [src/db/schema.sql](repo/src/db/schema.sql) | the users and sessions tables (2.1 million users) |
| [src/http/login.js](repo/src/http/login.js), [tests/http/login.test.js](repo/tests/http/login.test.js) | login, which deliberately gives one answer for a wrong password and an unknown email |
| [src/mail/send.js](repo/src/mail/send.js) | the mailer, which queues and retries |

## The plan and what was planted

The plan adds a "Forgot your password?" flow: a form that emails a reset link, a table of reset tokens, a page that
takes the token and sets a new password, and a nightly clean-up job. Five defects were planted, each meant to
block:

| Planted defect | Where |
| --- | --- |
| The form says "No account uses that email", so anyone can find out who has an account | plan, "Requesting a reset" |
| The token travels in the URL, and the access log records full URLs, against the rule never to log tokens | plan link + `logging.js:7` + `AGENTS.md` rule 2 |
| Tokens are stored exactly as generated, so anyone who can read the table can reset any password | plan, "Storing tokens" |
| Tokens are never invalidated after use | plan, "Storing tokens" and "Using the link" |
| A nightly `DELETE` breaks the soft-delete rule | plan, "Cleaning up" + `AGENTS.md` rule 1 |

## The run

`/crossfire docs/plans/password-reset.md`, depth left to the picker, on 2026-11-12, with the first version of the
skill.

```
 depth: DEEP (the plan adds authentication: reset tokens, signing users in)
 seats: advocate (sonnet) · pre-mortem (opus) · security (sonnet) · privacy (fable)
        · reliability (sonnet) · testing (sonnet) · architecture (sonnet)
 not seated: product (covered by security and privacy), performance (no stated load),
             cost (no paid service), infrastructure (no cloud change)
 agent calls: 31 = 7 drafts + 7 cross-examinations + 16 verifiers + 1 chair
 time 32.6 min · cost $16.55 (list price, as the session reported) · 86% of it on Opus
```

## What crossfire returned

**Gate: STOP.** Three conditions that could block turned on facts only the owner had. Five verified blockers had to
be fixed whatever the answers.

> The plan cannot be built as written. Every clicked reset link writes a live reset token to a log store kept for
> 90 days, which breaks rule 2.

| ID | Severity | Blocks | Finding | Status |
| --- | --- | --- | --- | --- |
| C1 | critical | yes | `GET /reset?token=…` is logged in full by `logging.js:7` into a 90-day store | open |
| C2 | major | yes | a used token, and the user's other open tokens, keep working after the reset | open |
| C3 | major | yes | the nightly `DELETE` breaks rule 1; tokens need `deleted_at` | open |
| C4 | major | yes | `/forgot` answers differently for known and unknown emails, unlike login | open |
| C5 | major | yes | `GET /reset` has no test, against rule 4 | open |
| C6 | major, if the page does not escape it | no | the raw token is echoed into a hidden input: a possible reflected XSS | question |
| C7 | major, if third-party scripts load | no | scripts on the reset page can read the token from the URL | question |
| C8 | major, if the worker logs job data | no | the link, token included, sits in queue job data | question |
| C9 | minor | no | nothing measures the ask "the email arrives within a minute" | question |
| C10 | minor | no | existing sessions survive a reset; no test signs in afterwards | open |
| C11 | minor | no | tokens stored in plaintext | follow-up |
| C12 | minor | no | no rate limit on `/forgot` | follow-up |
| C13 | minor | no | deploy order for the new table, and other advisories | follow-up |

The three questions it asked:
1. What renders the reset page, does it escape attribute values, and does it load third-party scripts?
2. What does the mail worker do with job data, how long does it keep jobs, and how long from queue to send?
3. Is "this email has an account" already public (for example, at sign-up)? If so, C4 becomes "won't do".

**What the panel changed.** The orchestrator's first view, given before any reviewer started, was "do not build;
expect REVISE", for the token design, the disclosure, the `DELETE` and sessions surviving a reset. The core held.
The panel:
- downgraded plaintext storage to a follow-up;
- corrected "never expires" (rows go after 30 days; the defect is reuse after the password changes);
- showed that sessions surviving a reset do not break a done item, because login checks the current password;
- added the three questions (C6 to C8), which turned REVISE into STOP.

How one of these findings went through every stage is traced in the skill's README, under
[Walkthrough: one finding, end to end](../../README.md#walkthrough-one-finding-end-to-end).

## Scored against the answer key

| Planted defect | Result |
| --- | --- |
| account disclosure | caught, blocking (C4) |
| token in the access log | caught, blocking (C1) |
| token never invalidated | caught, blocking (C2) |
| hard `DELETE` against the rule | caught, blocking (C3) |
| plaintext storage | found, but not blocking (C11) |

Gate STOP, as expected. One blocking row was not planted: C5, a missing test the repo's rules require, which is a
real gap.

## What we learned

- **The panel finds what matters, and more.** Four of five planted defects blocked, and the run raised real
  problems nobody planted.
- **A verifier can downgrade a real finding.** Plaintext token storage was verified at minor, because a database
  leak is not normal use and the repo already stores session ids raw. Read literally, the "normal use only" rule
  allowed that. The security lens now says a credential readable from a database, replica or backup is
  blocking-grade. That change has not been re-run.
- **Cost needed limits.** 16 Opus verifiers ran for 47 findings, and the orchestrator took 149 turns. The skill now
  merges duplicate findings before verifying, caps verifiers by depth (8 at deep), and writes one file per stage.
