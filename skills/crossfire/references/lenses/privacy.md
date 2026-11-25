# Lens: Privacy and data handling

Pasted in full into the brief of the reviewer that holds this seat.

## Seat this lens when

The target collects, stores, shows, shares, exports, retains or deletes personal data, or says anything to users about how their data is handled.

## Check

1. What personal data does the plan add, and is each field needed for an ask? Name the ask.
2. Where does it flow: logs, analytics, third parties, backups, exports, caches? Check the code paths, not the plan's summary.
3. Is it kept only as long as needed, and does deletion reach every copy?
4. Does every promise to users (a privacy notice, consent text, UI copy) stay true after this change? Quote the promise and the line that breaks it.
5. Can one user see another user's data through any new view, export, search or shared link?
6. Does deletion follow the repo's rule (soft delete, retention periods)?

## Typical blocking-grade findings

- A user-facing promise the change makes false.
- Personal data sent to a new third party or log with no ask behind it.
- One user's data visible to another.

## Usually not blocking

- Field-level minimisation that no ask or rule requires; theoretical re-identification with no realistic path.

## Where to look

User-facing copy and notices in the repo, analytics and logging calls, the data model, and the repo's data rules.
