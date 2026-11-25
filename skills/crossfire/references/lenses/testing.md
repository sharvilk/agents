# Lens: Testing

Pasted in full into the brief of the reviewer that holds this seat.

## Seat this lens when

The target changes behaviour that should be checked automatically; at standard and deep depth it is seated first when this matches, and never seated when it does not. Judge against the repo's own testing rules, never a universal standard.

## Check

1. What do the repo's instructions require for this kind of change (unit, integration, end-to-end, a dry run)? Quote them.
2. For each done item, is there a check that would fail if it broke? Name the check or the missing one.
3. Is the riskiest path tested for real, or only its safe preview (a dry run, a plan, a mock of the very thing at risk)?
4. Are the tests deterministic: no wall-clock sleeps, no shared state, no network the CI cannot reach?
5. Does each fixed bug the plan mentions get a test that fails without the fix?

## Typical blocking-grade findings

- A done item with no check at all, where a regression would reach users.
- The repo's own required test type missing for this kind of change.

## Usually not blocking

- A testing method the repo does not use or require (another framework, mutation testing, a coverage target) unless a finding names the logic it would protect.

## Where to look

The repo's testing docs and instructions, the existing tests nearest the code the plan touches, and the CI configuration.
