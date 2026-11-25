# Lens: Architecture and placement

Pasted in full into the brief of the reviewer that holds this seat.

## Seat this lens when

The target adds or moves a component, a module, a service, a table, a public interface, or a dependency between parts of the system; at standard and deep depth it is seated first when this matches, unless the change is confined to one existing function. It is never seated when this does not match.

## Check

1. Does each new piece live where the repo already keeps that kind of thing? Find the nearest existing example and compare.
2. Does the plan duplicate something that already exists (a helper, a client, a table, a queue)? Search for it before saying no.
3. Does the plan create a second source of truth for any state? Who writes it, who reads it, and what happens when they disagree?
4. Are the boundaries clean: does a low-level piece now import a high-level one, or does one component reach into another's storage?
5. Is the public contract (API shape, event schema, file format, CLI flags) stated, and is it compatible with what callers do today?
6. Is every new dependency (library, service) justified by something the existing stack cannot do?
7. Is the plan more general than its asks need: layers, plugins or configuration for cases nobody named?

## Typical blocking-grade findings

- A second writer for state the repo already owns, with no rule for which wins.
- A contract change that breaks existing callers, with no migration for them.
- A repo rule about structure broken (quote the rule).

## Usually not blocking

- Naming, file layout preferences, a different but equally valid pattern.

## Where to look

The repo's own instructions (AGENTS.md, CLAUDE.md, CONTRIBUTING), its architecture docs, the nearest existing example of the same kind of component, and its import graph (grep the imports).
