# Lens: Cost

Pasted in full into the brief of the reviewer that holds this seat.

## Seat this lens when

The target adds a paid service, a model or API call, storage that grows with use, a scheduled job, or egress, or changes how often something billable runs.

## Check

1. What does one use cost, and what multiplies it (per user, per request, per item, per retry)? Show the arithmetic from stated prices and sizes.
2. Is there a ceiling: a budget, a rate limit, a cap on retries or on stored data?
3. Is there a cheaper way to meet the same ask that the plan did not consider (a smaller model, a batch, a cache, an existing service)?
4. Does storage or log volume grow without a retention rule?

## Typical blocking-grade findings

- Spend that grows without a ceiling in normal use, on a path anyone can trigger.
- A stated budget the arithmetic exceeds.

## Usually not blocking

- Savings below what the change costs to build, with no growth path.

## Where to look

Pricing pages of the services named (dated), configuration for limits and retention, and any stated budget.
