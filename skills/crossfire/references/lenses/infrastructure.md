# Lens: Infrastructure and cloud

Pasted in full into the brief of the reviewer that holds this seat.

## Table of contents

- [Seat this lens when](#seat-this-lens-when)
- [Check](#check)
- [Typical blocking-grade findings](#typical-blocking-grade-findings)
- [Usually not blocking](#usually-not-blocking)
- [Where to look](#where-to-look)

## Seat this lens when

the target creates, changes or deletes cloud resources, infrastructure code, permissions, networking, DNS, deploy pipelines or environment configuration.

## Check

1. Is every resource created through the repo's infrastructure code and pipeline, or by hand? Which does the repo require?
2. Are permissions the least the job needs? Quote any wildcard actions or resources.
3. What does the change do to running traffic during deploy, and how is it rolled back?
4. Are secrets stored where the repo's rules say, and never in code, logs or plain configuration?
5. Are names, tags and environments consistent with the repo's conventions, and is production changed only by the path the repo allows?
6. Does anything get deleted or replaced on apply that holds data?

## Typical blocking-grade findings

- A resource with data that the change would delete or replace.
- A permission wider than the job needs on a production path.
- A deploy step with no rollback for a change to live traffic.

## Usually not blocking

- Tagging or naming drift with no operational effect.

## Where to look

Infrastructure code, pipeline configuration, the repo's infrastructure rules, and the plan output if the target includes one.
