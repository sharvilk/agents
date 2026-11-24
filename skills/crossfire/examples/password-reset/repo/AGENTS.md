# AGENTS.md: Quillbox

Quillbox is a notes web app: Node 22, Express, MySQL 8.

## Rules

1. Rows are never removed: to retire one, set its `deleted_at`. Nothing in the app deletes rows.
2. Never write passwords, tokens, one-time codes or session ids to logs, analytics or error reports.
3. Every email goes through `src/mail/send.js`, which queues it and retries a failed send up to 3 times.
4. Every HTTP handler has a test in `tests/http/` that runs against the in-memory database.
5. Secrets come from the environment, never from code or config files.
