# Deciding, and the decision ledger

Read at steps 8 to 10 of a tick. The classes and the never list are in SKILL.md.

```
 on the never list ──────────────────────────────────────────► D  NEVER    queue the ask; do not do it
 undo NO, or reach NO, or one of the big kinds ──────────────► C  QUEUE    prepare options + a recommendation
 undo YES, reach YES, a real fork (2+ workable designs) ─────► B  DECIDE, FLAG   full entry: diagram + example
 undo YES, reach YES, the docs or code already imply it ─────► A  DECIDE, LOG    short entry
 not sure which class ───────────────────────────────────────► one class UP (A to B, B to C)
```

- **A examples:** an internal name; where a new test goes; the order of two steps; the wording of an error message;
  which existing helper to reuse; fixing a check the loop's own change broke; a review finding's severity; a comment
  the item requires; a timeout in its own test; a fix made for a review comment.
- **B examples:** an internal data structure or module boundary the roadmap leaves open; which of two algorithms when
  both pass; how an edge case behaves when the spec is silent; the layout of a new config section nothing outside
  the repo reads; **changing what an existing test expects, with the reason** (deleting, skipping or loosening a test
  is never allowed); splitting one item into two PRs; declining a reviewer's suggestion, with the reason; skipping an
  item because it is blocked, and what it took instead; **adding a dependency**.
- **C examples:** anything in a public contract (a CLI flag, an exported API, a file format, a schema); a new service,
  queue, database or table, or a major version of a dependency; anything touching auth, secrets, permissions or what
  data leaves the machine; changing the scope, order or check of a roadmap item, or adding one; a migration of stored
  data; changing CI, release or build configuration; a licence question; a reply in the user's name outside its own
  PRs' review threads; anything two project documents disagree about. Build **one clearly labelled throwaway spike
  branch** per queued item at most (the PR title says "SPIKE"; never merged) when it makes the options concrete.
  When the user answers a queued item, record the answer in the ledger as a decision with their words, then build
  the chosen option as a new step on a loop branch; a spike is never promoted.
- **Autonomy `minor`** queues every class B like a C. **`ask-first:<area>`** does that for the named area only.
- When a project's rules say who may approve or review, those rules apply.

## Dependencies: class B with guardrails

All of it happens on the loop's own branches, so a veto removes it before anything merges. **Check every guardrail
before installing anything**, with read-only lookups (the registry's metadata, the lockfile, the package's manifest):
the standard library or an existing dependency was tried first; a permissive licence; a maintained package with a
recent release; no known advisories; no install script the loop cannot explain (inspect it; install with scripts
off where the tool allows). Only then install, pin the version and update the lockfile. One dependency per ledger
entry, with the reason and the alternative it rejected. A major version of an existing dependency is class C. Any
guardrail that fails makes it class C.

## The ledger

A committed Markdown doc in the repo, one file per day, entries appended, in the project's own decision-log or
progress folder when it has one; otherwise propose a folder the first time and ask. The entries go on **one
long-running log branch with one open pull request** (its name follows the project's convention plus the `loop`
suffix), pushed after every entry so a crash loses nothing. The user merges that PR when they like; the loop never
does. **The log PR's body lists no decisions, and merging it is no verdict on any entry:** entries stay `pending`
until the user answers. Fallback when the project wants no such branch: a git-ignored folder in the main checkout,
with the loss risk said out loud. Each work PR's body has a "Decisions in this PR" list with a line per entry and
links into the ledger. The todo list holds only an index: id, class, status, link, one line.

The entry format is in [ledger-entry.md](ledger-entry.md): write each entry by filling that file's template exactly,
heading line included (the exact line is shown there), with its time from `date` run in the same command that writes
it, never typed or estimated. Ids continue across charters and renewals: the next id is
the highest in the ledger plus one (a `grep`, never memory). Counting is a `grep` for `· pending$`. Class C items are
not decisions: they sit in "Waiting for you" as `C-n` with the same options-and-recommendation shape.

**No new step starts until the ledger is pushed.** A push that fails leaves the entry in the working tree; the tick
reports it and retries at the next tick, and starts no new step meanwhile.

A flagged (class B) decision made while the user is present is **announced at once, in one line**, whatever the
posture: "D-014 (flagged): appended the new export columns instead of regrouping; entry in the log." The diagram
waits for the review. A **reviewer subagent checks the class of each flagged entry** before it is announced.
