# Lens: Reliability and operations

Pasted in full into the brief of the reviewer that holds this seat.

## Seat this lens when

The target adds a job, a queue, a migration, a deploy step, an external call, a retry, a cache, or anything that runs without a person watching.

## Check

1. What happens when each dependency the plan calls is slow, down or rate-limited? Is there a timeout, and what does the user see?
2. Is each job, handler and retry safe to run twice? What does a duplicate do to users (a second email, a double charge)?
3. Can a migration run on the real data size without locking or failing, and can it be rolled back? Is code deployed before or after it, and does each order work?
4. How would anyone know it broke: what is logged, what alerts, what does an operator run to check?
5. Does a failure stay contained, or can one bad record or one slow call stall everything behind it?
6. If the repo keeps records of past incidents, does the plan repeat a pattern one of them names?

## Typical blocking-grade findings

- A non-idempotent job or retry that sends, charges or writes twice in normal operation.
- A migration that fails or locks on the real data size, or that has no working deploy order.
- A failure that nobody would notice until users report it, on a path that handles money or data.

## Usually not blocking

- Extra dashboards, runbooks or chaos testing the asks do not need.

## Where to look

Job and queue code, retry and timeout settings, migrations and their history, logging and alerting setup, and any incident or postmortem records the repo keeps.
