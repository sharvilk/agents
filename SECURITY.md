# Security policy

## Supported versions

Each skill here installs as a Claude Code plugin, and every one is pre-1.0 (`0.x`). Security fixes land on the
latest version of a skill; there are no long-term support branches.

## Reporting a vulnerability

**Please report privately: do not open a public issue for a security problem.**

Use GitHub's **private vulnerability reporting**: on this repository, go to the **Security** tab, then **Report a
vulnerability**. This opens a private advisory visible only to the maintainer.

Please include what the issue is and the impact you foresee, steps to reproduce, the affected skill and its version,
and any suggested fix. I will acknowledge as soon as I reasonably can (this is a small, volunteer-maintained
project), work with you on a fix, and credit you unless you would rather stay anonymous. Please allow a reasonable
window for a fix before any public disclosure.

## Scope notes

A skill runs inside Claude Code with your permissions. Especially in scope:

- **What a skill tells the agent to run.** A skill's instructions or helper script that makes an agent delete,
  overwrite, publish or send something the user did not ask for.
- **Command lines.** The helper scripts take paths and names from the session. A way to inject into a command they
  run, for example through a folder or branch name, is in scope.
- **What a skill reads and writes.** A skill that reads or writes outside the folders its README names, or leaks
  what it reads, is in scope.

Out of scope: problems that need a deliberately hostile local setup (a modified plugin, a malicious Claude Code
build), and the behaviour of Claude Code itself; report those to Anthropic.
