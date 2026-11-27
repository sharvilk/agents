# Documenting projects: docs as the system of record

This guide is for you if you build software with other people or with agents, and decisions keep getting lost in
chats. It sets one rule, that the repository is the record, and shows what to write down, where it goes, and how to
keep it true. It also covers what to do when a project is public and its plans are not.

## Table of contents

- [The rule](#the-rule)
- [1. Capture a conclusion in the same change](#1-capture-a-conclusion-in-the-same-change)
- [2. Know what to write down and what to leave in the chat](#2-know-what-to-write-down-and-what-to-leave-in-the-chat)
- [3. Give every fact one owner](#3-give-every-fact-one-owner)
- [4. Put how it works beside the code](#4-put-how-it-works-beside-the-code)
- [5. Keep comments about behaviour](#5-keep-comments-about-behaviour)
- [6. Keep one progress narrative](#6-keep-one-progress-narrative)
- [7. Separate what you saw from what you infer](#7-separate-what-you-saw-from-what-you-infer)
- [8. Point only at what the reader can open](#8-point-only-at-what-the-reader-can-open)
- [9. Move and correct documents completely](#9-move-and-correct-documents-completely)
- [Checklist](#checklist)

## The rule

The git repository that owns a project is its record. Chats, review threads, terminal transcripts, notes and talks
are ways of working together. They are not documentation.

A conclusion is unfinished until it is in a tracked file, proposed through the project's normal review. A chat may
link to the file for convenience. The file and its history are the authority.

```
 conversation / review / incident / experiment
                   |
                   v
          did it settle something?
            /               \
          no                 yes
          |                   |
   leave it in the chat       v
                       pick the repo and file that own it
                              |
                              v
              update that file and its indexes
                              |
                              v
                 check, commit, review
                              |
                              v
                   git is the authority
```

Keeping a transcript is still worth it: it holds the reasoning and the dead ends. Keep it as a backup of the
conversation, never as the place the decision lives.

## 1. Capture a conclusion in the same change

1. **Name what you learned or decided**, why it matters, and what is still unknown.
2. **Pick the owner**: the one repo and file that should hold it. Never make a second source of truth.
3. **Update it in the same pull request as the work**: the canonical doc, the roadmap, the API reference, the
   instructions the work touched.
4. **Check what depends on it**: links, indexes, tests, templates, ignore rules.
5. **Commit and review it.** Don't call it documented while it exists only in a local file or a chat.

## 2. Know what to write down and what to leave in the chat

| Write it down | Leave it out |
| --- | --- |
| Requirements, outcomes, non-goals | Step-by-step narration of what you ran |
| Architecture, data, security and compatibility decisions | Secrets, tokens, keys, environment dumps |
| Rejected options, with the reason and what would reopen them | Raw private material you only analysed |
| Public interfaces: commands, options, settings, errors | Personal paths, process ids, task titles |
| Benchmark method, results, corrections and limits | Unfiltered logs, screenshots, transcripts |
| Incidents and the requirements they produced | Guesses that changed no decision |
| Roadmap changes, open work, deferrals | |
| Policies for dependencies, releases, migrations | |

Write the conclusion with enough provenance to review it. Don't paste a whole chat when a decision, its reason, an
observation and its uncertainty say it.

## 3. Give every fact one owner

Duplicated state is how documents drift. Pick one place per kind of knowledge and link to it from everywhere else.

| Knowledge | Where it lives |
| --- | --- |
| What the project is, and how to start | the root `README.md` |
| State of each item, phases, deferred work | one roadmap file. Never a second tracker. |
| How the project got here, and what is still open | one progress narrative (rule 6) |
| Design and user documentation | the docs folder, in a layout the project declares |
| Public interface | one API reference, beside the code, updated with it |
| How a module or script works | a README beside it (rule 4) |
| Private strategy and raw evidence | a private location, never the public repo |
| Instructions for agents | one instructions file, with the real rules written in it |

Embed the rules in the project's own instruction file instead of linking to a shared document. An agent should see
the rule without following a link.

## 4. Put how it works beside the code

Planning documents (requirements, specs, trackers) say why and when. They get renumbered and go stale. Someone new to
a module, a person or an agent, needs how it works, next to the code.

Every module, and every script or tool someone runs, has a README beside it. One README may cover a folder of
scripts. A user guide somewhere else does not replace it. Write it for a newcomer, and let it be long:

- what it does, and how its pieces connect, in an ASCII diagram;
- what it stores and where;
- worked examples;
- every error it can raise, and what a user sees for each;
- the alerts that watch it.

Write it and update it in the same pull request as the code.

> What happened to me: an agent I was running shipped a backup script with a user guide on how to make and open an
> archive, and no README on how the script works inside. It had taken a README to be something only a module needs,
> and the user guide to be enough.

> What happened to me: one module's README cited spec sections and decision numbers a dozen times. Understanding the
> code meant reading the plans. Stating the substance in the README made it stand alone.

## 5. Keep comments about behaviour

- A comment says what the code does, briefly, and why when that is not obvious. An entry point may carry a short
  diagram or example.
- Don't put tracker ids, planning-document links, ticket or pull-request numbers in source. They rot when the tracker
  renumbers, and in a public repo they point at something readers cannot reach. The reason for a change goes in the
  decision record or the module README, in the same change.
- A comment is not the decision log. Before you say who uses a component, check where decisions are recorded.

> What happened to me: an agent I was running called a component unused because a code comment said so. The decision
> log recorded a consumer. The comment was stale.

## 6. Keep one progress narrative

A tracker answers "what state is each item in?". A returning maintainer asks something else: "how did this get here,
and what is still open?" Only a narrative can answer, and its best part is the reversals: the thing built and then
removed, the design that was refuted, the assumption a real user disproved. A list of statuses cannot say why, and
why is what stops people redoing the work.

Keep one narrative for any project that will run longer than a few weeks. It must:

- run from the beginning to now, with each era present because it changed the direction, not because it shipped;
- say what each era settled, so the reader learns the constraint and not only the commit;
- keep the reversals, and what they cost to learn;
- separate work that is blocked on a decision from work that is only queued;
- carry a freshness header: version, revision, and the date it was last reviewed.

**It is not a second tracker.** The tracker owns item state, and the narrative links to it. Where they disagree,
the tracker wins. Update the narrative in the same change that alters direction: a behaviour change, a release, a
finished phase, a decision landing.

Choose any form you like, with two conditions. A reader needs no build step or running service to read it, and it
must be cheap enough to get updated. A narrative nobody refreshes is worse than none, because it is trusted and
wrong. If it has diagrams, have something check them. A diagram fails silently.

## 7. Separate what you saw from what you infer

- Record observation, inference, decision and public claim as four different things. A measurement is not yet a
  cause, a requirement or a marketing claim.
- Say which statements you checked in the code and which you read in a document. Never present an inference about
  what the code does as a fact.
- Words like "faster", "saved" or "reduced" need comparison evidence and a nearby link to its limits. An incident
  seen before the fix is problem evidence, not a before-and-after result.
- Give a substantial document a status (draft, proposed, accepted, superseded), its scope, what it establishes and
  what it does not, and the document that replaces it.
- Before you describe or build a component, find the one document that describes where the whole effort is going
  (its end state, the phases, what each covers) and say where the component sits in it. Keep one such document per
  effort, with the same status legend everywhere.
- Mark an interim or minimal version of something as interim at the top, and say where the full version is
  described.

An evidence record for an incident or benchmark holds: purpose and authorization, environment and time window, how
you collected and attributed, sanitised results, confounders and limits, what it does and does not establish, the
requirements that came out of it, its privacy and publication boundary, and its correction history. For a family of
incidents, keep an indexed folder with stable, sortable names:

```
 docs/evidence/incidents/
 ├── README.md                                      scope, naming, how to add one
 ├── 001-2026-03-04-SLOW-STARTUP-AFTER-UPGRADE.md   the sequence number never changes
 └── 002-2026-03-19-SLOW-STARTUP-ON-LOW-DISK.md     the date is when it was observed
```

Name the observed shape, not an assumed cause.

## 8. Point only at what the reader can open

A public document carries no pointer into a private tree. That means no link, and no bare citation either: an
internal decision, phase or finding number resolves to nothing for the reader. It is worse than saying less, because
it implies evidence you then withhold. **State the substance in place** and drop the reference.

Three details people miss:

- **Code comments count.** A doc comment reaches users when they hover in an editor, and ships inside published type
  declarations and source maps. Check the published source, not only the Markdown.
- **Removing a reference is editing a sentence.** A citation sits inside a parenthesis, a list or a range. Delete the
  id and the sentence loses its operand: it still parses and renders, and no longer says anything. Rewrite the
  sentence whole, then confirm the id is gone.
- **A reference the reader can open is fine**: a numbered rule the public set itself lists, a section of a public
  document, an issue or pull request on the same repo. So is a look-alike that only resembles an internal id, such
  as a product's own name that happens to look like a code.

Keep the boundary closed with habits:

- Check a repo's visibility before you commit documentation to it: `gh repo view <owner>/<repo> --json visibility`.
- Keep the list of private names a scanner searches for out of the repo it guards, and scan every tracked file, not
  only what ships. The guard can be the leak.
- A changelog is public documentation too.
- When you sweep, fix the highest harm first: published source, then documents that instruct a reader, then
  annotations. Search every spelling of a pattern (`Phase 3` and `Phase-3`).

Write a [gate](writing-gates.md) for this as soon as it goes wrong a second time.

## 9. Move and correct documents completely

A move is finished only when every consumer has moved with it. Search the repo for the old path and update:

- Markdown links and indexes;
- instruction files and templates;
- literal paths in build manifests;
- tests and fixtures;
- ignore and privacy paths;
- examples, sites and generated or public copies.

Then check the local links, run `git diff --check`, run the full gate if code or checked paths changed, and wait for
green CI.

Never rewrite history silently. When a parser, a method or a conclusion proves wrong, keep the correction and narrow
every claim that depended on it. A decision changes through a new decision that supersedes it, so the old reason
survives.

## Checklist

- [ ] The conclusion is in a tracked file in the repo that owns it, not only in a chat.
- [ ] It is in the same pull request as the work.
- [ ] There is one owner for each fact, and nothing is duplicated.
- [ ] Each module and script has a README that explains how it works, with diagrams, examples and every error.
- [ ] Comments say what the code does, with no tracker ids or ticket numbers.
- [ ] The progress narrative is updated, has a freshness date, and does not restate item status.
- [ ] Observation, inference and claim are labelled, with limits stated.
- [ ] No public document points at something its reader cannot open, and the published source is checked.
- [ ] Anything moved took its links, tests, manifests and indexes along.
- [ ] No secrets, personal paths or raw private material are in the commit.
