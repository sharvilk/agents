# The ledger entry

The decision ledger is a committed Markdown file, one per day, entries appended, on the loop's log branch. The shape
is the well-known decision-record one (context, options, outcome, consequences; MADR, Markdown Architectural Decision Records, is the common template) with
four additions this loop needs: a diagram, a worked example, the exact undo, and what depends on it.

In a full entry, three parts change after writing: the heading line (the status), the **Built on it since** line and
the **Review** line. A class A entry changes only its heading line. Counting is a `grep` of the heading
(`grep -c '· pending$'`), never the agent's memory. Ids continue across charters and renewals (`D-001`, `D-002`, ...; the next is
the highest in the ledger plus one, found by a `grep`, never from memory); class C items are `C-1`, `C-2`, ... and
live in the todo file's "Waiting for you", with a link to their write-up.

## The heading line, exactly

Fill this and nothing else; no extra characters, no other separators. The time is the output of
`date +%Y-%m-%dT%H:%M%z` run in the same command that appends the entry, never typed or estimated:

```text
## D-014 · 2026-11-24T14:07+0000 · B · pending
```

That is `## `, the id, ` · `, the time, ` · `, the class (A or B), ` · `, the status, with a plain middle dot and no
trailing text.

## A class B entry (full)

````md
## D-014 · 2026-11-24T14:07+0000 · B · pending

**Decision.** New export columns are appended at the end; existing columns keep their order.
**Roadmap item.** R3 "Export v2" (link to the roadmap line)
**Why it came up.** R3 adds `tax` and `currency` to the CSV. The roadmap does not say where they go.
**Options.**
1. Append at the end (chosen): existing spreadsheets and the 14 export tests keep working.
2. Group by meaning (`amount, tax, currency, ...`): nicer to read; breaks every consumer that reads by position.

**Diagram** (DERIVED from the code on the branch):
```
 before     id | date | customer | amount
 chosen     id | date | customer | amount | tax | currency      <- column 4 is still `amount`
 option 2   id | date | customer | currency | amount | tax      <- column 4 is now `currency`: positional readers break
```
**Example.** `1042,2026-11-02,Acme,120.00` becomes `1042,2026-11-02,Acme,120.00,21.60,EUR`.
**Confidence.** High: the tests encode the old order.
**What it touched.** commit `<sha>` on `feature/export-v2-loop`; PR <full link>.
**Depends on.** none.   **Built on it since.** none.
**Undo.** `git revert <sha>` on that branch: clean, nothing else depends on it. About 10 minutes to redo as option 2.
**Review.** (empty until the user answers: verdict, date, their words)
````

## A class A entry (short)

A class A entry has these lines: the heading, Decision, Why it came up, Depends on and Undo. (A veto reads the
"Depends on" lines to find what to revert with it.)

````md
## D-015 · 2026-11-24T14:31+0000 · A · pending

**Decision.** The new test lives in `export.test` beside the existing column tests, named after their pattern.
**Why it came up.** The roadmap item adds columns; the convention puts column tests there.
**Depends on.** none.
**Undo.** `git revert <sha>`: one test file.
````

## What the Review line becomes

The user's verdict, the date and their words, and the heading changes to one of: `accepted`, `accepted (merged
<date>)`, `changed → D-031`, `vetoed`, `vetoed (merged): follow-up <link>`, `reverted (with D-014)` for an entry reverted in another's cascade,
`discussing`. A change is a **new**
entry (`D-031 · B · pending`, with "Supersedes D-014" under the Decision) made on the same branch as new commits.

## A dependency entry

One dependency per entry: the heading is class B; "Options" names the standard-library or existing-dependency
choices tried and why they fell short; add lines for the guardrails with their evidence: licence, latest release
date, advisories checked, pinned version, lockfile updated, install scripts (none, or what they do).
