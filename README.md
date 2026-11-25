# agents

The AI-agent kit I use and share. It starts with skills for Claude Code: plain folders you can browse, read and
copy. More kinds will join as they are ready: commands, prompts, and guides to ways of working with agents. Each
skill's own README is its front page.

## Skills

| Skill | What it does |
| --- | --- |
| [`todo-sync`](skills/todo-sync/README.md) | Keeps each session's todo list complete in its own file, and rebuilds it from the transcript when it goes missing. |
| [`checkpoint`](skills/checkpoint/README.md) | Brings a session to a safe stopping point before a restart, records where it stands, and resumes from that record. |
| [`away-loop`](skills/away-loop/README.md) | Keeps a session working, visibly, while you are away for hours, and gives one summary when you return. |
| [`crossfire`](skills/crossfire/README.md) | Reviews a plan, design doc, pull request or open decision before you build it, with independent read-only reviewers and a fixed gate. |
| [`on-loop`](skills/on-loop/README.md) | Keeps a session working a project's roadmap while you come and go, and logs each decision it makes for you to keep, change or veto. |

## Use with Claude Code

Each skill installs as a Claude Code plugin. Add the marketplace once, then install what you want:

```
/plugin marketplace add sharvilk/agents
/plugin install todo-sync@agents
```

Swap `todo-sync` for any skill in the table. Installing `checkpoint`, `away-loop` or `on-loop` also installs
`todo-sync`, which they need. Start a new session afterwards so the skill is loaded.

A skill runs with your permissions, so read it before you install it. Each skill's README says what it reads,
writes and runs.

**Without the plugin system**, copy the skill's folder, `skills/<name>/`, to `~/.claude/skills/<name>/` (or to
`$CLAUDE_CONFIG_DIR/skills/<name>/` if you set that variable). `checkpoint`, `away-loop` and `on-loop` need
`todo-sync` copied too. `crossfire` also uses its two agent files, copied from `skills/crossfire/agents/` to
`~/.claude/agents/`: they are recommended, because they make its reviewers read-only.

**To update**, open `/plugin`, go to Installed and choose "Update now", or run `claude plugin update <name>@agents`
in a shell. Auto-update is off by default for a third-party marketplace; turn it on from `/plugin` under
Marketplaces.

**To remove a skill**, run `/plugin uninstall <name>@agents`. Uninstalling `checkpoint`, `away-loop` or `on-loop`
leaves `todo-sync` installed, since it came in as their dependency; `claude plugin prune` removes dependencies that
no installed plugin needs any more ([plugin dependencies](https://code.claude.com/docs/en/plugins/dependencies.md)).

## Use with other agents

The skills are written for Claude Code and use its features: scheduled jobs in `away-loop` and `on-loop`,
subagents and agent files in `crossfire`, and the variables that give the session id and the skill's own folder
(`${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`) in `todo-sync` and `checkpoint`. The instructions are plain
Markdown that another agent can read, but those parts need that agent's own equivalents.

## Layout

```
 skills/
 ├── todo-sync/
 ├── checkpoint/
 ├── away-loop/
 ├── crossfire/          its two reviewer agents are in crossfire/agents/
 └── on-loop/
 .claude-plugin/marketplace.json     the only packaging file; Claude Code installs from it
```

## Contributing

This repo is generated from a private source and is never edited by hand. A fix or a change is made at the source,
exported, and arrives here as a pull request.

Issues are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). A pull request is read as a proposal and re-made at the
source, with credit. To report a vulnerability privately, see [SECURITY.md](SECURITY.md). Everyone taking part
follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[Apache-2.0](LICENSE).
