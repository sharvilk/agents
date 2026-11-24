# AGENTS.md: Quillbox

Quillbox is a notes web app: Node 22, Express, MySQL 8, and a managed job queue for background work.

## Rules

1. Background work that must survive a server restart runs on the job queue, not in a request.
2. Every email goes through `src/mail/send.js`.
3. Rows are never removed: to retire one, set its `deleted_at`.
