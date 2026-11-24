# The finding contract

Every reviewer in a crossfire run reports in this shape, and every later stage reads it. The orchestrator pastes
this file into each reviewer's brief; it does not ask the reviewer to open it, because reviewers told to "read the
rubric" mostly don't.

## Table of contents

- [A finding](#a-finding)
- [Evidence](#evidence)
- [Severity](#severity)
- [Protects](#protects)
- [What blocks](#what-blocks)
- [The reply](#the-reply)

## A finding

```
### <short title>
- claim:     one sentence, stating what is wrong or missing
- evidence:  what shows it (see Evidence); "needs data: <the fact you would need>" when only the owner has it
- severity:  critical | major | minor | nit
- protects:  the ask, done item, repo rule or user scenario this protects, quoted with its id; "none" otherwise
- condition: the fix, stated as a check someone can run or read ("the reset handler returns 404 for an unknown
             email and for a known one alike: compare the two responses")
- refute:    the evidence that would show this finding is wrong
- option:    (whether-mode only) which option it applies to
```

Keep each field to one or two lines. A finding that needs a paragraph is two findings, or none.

## Evidence

Acceptable, in order of strength:

1. **A location**: `path:line` with a short quote of the line, from the target or the repo.
2. **A command and its output**: a read-only command (`git log`, `grep -c`, `wc -l`) and what it printed.
3. **A count**: how many places, rows, calls, and how it was counted.
4. **A dated source**: a link to a library's or service's own documentation, with the date you read it.
5. **The target's own words**: a quote from the plan or question that contradicts another quote, or an ask.

Not evidence:

- "This looks wrong", "I believe", "in my experience", "best practice says".
- A claim about the codebase you did not open a file for.
- A claim about production (row counts, traffic, latency) that no file states. Write `needs data:` instead.

## Severity

Judged by what happens to users, data or money if the plan ships as written and the finding is true.

| Severity | Meaning |
| --- | --- |
| critical | On a normal path: data is lost or corrupted, a secret or personal data is exposed, money is wrong, or the service goes down. |
| major | A key happy path or an important error or recovery path is broken; a stated ask is missing or contradicted; a repo rule is broken. |
| minor | It works, but worse: slower, harder to change, harder to operate, a confusing message. |
| nit | Wording, naming, formatting. |

Rare edge cases are not critical because the outcome would be bad. Ask how a user gets there in normal use; if
they can't, it is minor at most, however bad the outcome.

## Protects

Name the thing the finding defends, with its id from the frame:

- an ask: `A2 "users can reset a forgotten password from the login page"`;
- a done item: `D3 "reset links stop working after one use"`;
- a repo rule: `AGENTS.md:14 "never log request bodies or tokens"`;
- a user scenario, written out: `a user requests two resets and clicks the first email's link`.

A finding that protects nothing is advisory, whatever its severity.

## What blocks

A finding blocks only if all three hold:

1. its severity is critical or major;
2. its `protects` names an ask, done item, repo rule or user scenario;
3. a fresh verifier reproduced its evidence and agreed it is critical or major. A verifier that rates it minor or
   nit makes it advisory.

Block only for:

- a credible failure in normal use;
- a missing or contradictory requirement;
- a broken key happy path;
- an important error or recovery path that fails.

Do not block for:

- states the real system cannot produce;
- exhaustive permutations of races or corruption that normal use does not reach;
- speculative abstraction, or hardening against a threat the stated environment does not have;
- polish that safe normal use does not need.

Those go in as minor findings, so they are still visible.

## The reply

```
Verdict: <one sentence: the plan's biggest problem, or why it holds up>

<findings, most severe first, at most 7>

Not reviewed: <anything in your lens you could not check, and why; "nothing" if none>
```

The advocate adds a `Keep:` section after its findings. In a later round, every reviewer starts with one line per
open condition in its seat: `Cn: met` or `Cn: not met`, with evidence.

At most 600 words in total. Fewer, better-evidenced findings beat many weak ones; a reply with no findings is a
valid reply when the plan holds up through your lens.
