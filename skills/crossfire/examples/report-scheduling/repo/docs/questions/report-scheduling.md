# Question: should the nightly usage report move from cron to the job queue?

## Why we are asking

The usage report runs from cron on `app-1` only (`ops/crontab`). Twice this quarter `app-1` was being replaced
at 02:00 and the report did not go out; admins noticed the next morning. The job queue survives a server
restart, and the repo's rule 1 says background work that must survive a restart belongs there.

## What is on the table

- O1. Keep cron on `app-1`, and add a check that alerts when the report did not run.
- O2. Move the report to the job queue: `queue.schedule('usage-report', '0 2 * * *', {})`, with a worker that
  calls the existing `run()` from `jobs/usage-report.js` unchanged.
- O3. Move it to the queue as one job per workspace: a scheduled job enqueues about 3,000 small jobs, one per
  workspace, each sending that workspace's emails.

## What matters

- Every admin gets exactly one report a night.
- It goes out even when a server is replaced.
- Small effort: this is not a priority project.
