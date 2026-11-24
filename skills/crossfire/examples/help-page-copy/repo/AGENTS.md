# AGENTS.md: Quillbox

Quillbox is a notes web app: Node 22, Express, MySQL 8.

## Rules

1. Help copy is plain English, second person, present tense, and only describes what the code does today.
2. Configuration defaults live in `config/defaults.json`; nothing reads colours from code.
3. Every HTTP handler has a test in `tests/http/` that runs against the in-memory database.
