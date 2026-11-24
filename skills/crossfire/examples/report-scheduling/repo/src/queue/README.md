# Job queue

A managed queue. Each job is delivered at least once: a job that does not finish within its visibility timeout
is handed to another worker. The default visibility timeout is 5 minutes and can be set per job type up to
12 hours. A failed job is retried up to 5 times, then moved to the dead-letter queue.

Schedules: `queue.schedule(name, cron, payload)` enqueues a job on a cron expression.
