# Lens: Performance and data at scale

Pasted in full into the brief of the reviewer that holds this seat.

## Seat this lens when

The target adds or changes a query, a loop over stored data, a list or search page, a cache, a fan-out, a batch, or a hot path, or states a size or load it must handle.

## Check

1. What is the size of each collection the plan touches, by the repo's own numbers? If no file states it, say `needs data:` rather than guess.
2. Is every query bounded and indexed for its filters and sort? A LIMIT bounds the rows returned, not the rows scanned.
3. Does any step do work per item that could be done once (N+1 queries, a call per row, a file read per request)?
4. What happens at ten times today's load: which resource runs out first (connections, memory, a rate limit, a lock)?
5. Is a cache keyed, bounded and invalidated correctly, and what happens on a cold cache?
6. Does a change in how many items flow through a step break a downstream limit (batch size, payload size, API quota)?

## Typical blocking-grade findings

- An unbounded or unindexed scan on a table the repo says is large, on a user-facing path.
- A fan-out that exceeds a stated downstream limit in normal use.

## Usually not blocking

- Micro-optimisation with no measured or stated load behind it.

## Where to look

Schema and index definitions, query code, any stated sizes in docs or comments, and past performance incidents.
