# crossfire: review a plan before you build it

> A design review that runs before you build: independent reviewers, every blocker reproduced by a verifier,
> and a decision with a checklist you re-run.

`/crossfire` puts a plan, a design doc, a pull request or an open decision in front of a small panel of independent,
read-only reviewers before anyone builds it. Each reviewer looks through one lens (a checklist for one area, such as
security) or one stance (a fixed point of view, such as the advocate) and must back every finding with evidence. The
others then cross-examine those findings anonymously. A fresh verifier tries to refute every finding that could
block, and one chair writes a one-page decision. A fixed rule, not a model, turns that into the outcome: **PASS**,
**REVISE**, **STOP** (questions only you can answer), **ESCALATE** or **INCOMPLETE**, with a numbered list of
conditions that the next run checks by id.

How to use it day to day is in the [playbook](PLAYBOOK.md). Four examples (five real runs), each explained in its
own README, are in [examples](examples/README.md). How the evals work is in [evals/README.md](evals/README.md).

## Install

As a plugin, from the `agents` marketplace:

```
/plugin marketplace add sharvilk/agents
/plugin install crossfire@agents
```

crossfire needs no other skill. Start a new session afterwards so the skill is loaded.

Without the plugin system, copy the skill's folder, `skills/crossfire/`, to `~/.claude/skills/crossfire/` (or to
`$CLAUDE_CONFIG_DIR/skills/crossfire/` if you set that variable). Also copy its two agent files, `crossfire-reviewer.md`
and `crossfire-verifier.md`, from the folder's `agents/` to `~/.claude/agents/`: they are recommended rather than
required, because without them the reviewers' read-only limit is only in their prompt. There is no package or build
step.
[Install details](#install-details) shows what goes where.

## Quick start

In a session inside the repo the plan belongs to, type:

```
/crossfire docs/plans/reset.md
```

If another command already uses the name `/crossfire`, type `/crossfire:crossfire docs/plans/reset.md`. The run
takes about 8 to 33 minutes. You get a gate (PASS, REVISE, STOP, ESCALATE or INCOMPLETE) and a one-page summary
beside the plan; [At a glance](#at-a-glance) shows what comes back. To check the install, type `/crossfire` with no
target: it should stop with one line asking for one.

## Terms

- **Orchestrator:** your main Claude Code session. It follows [SKILL.md](SKILL.md), starts the agents and is the only
  one that writes files.
- **Seat:** one reviewer's place on the panel: a lens, the advocate or the pre-mortem.
- **Lens:** a checklist for one area (security, privacy, testing and so on), seated only when the target triggers it.
- **Stance:** a fixed point of view instead of a checklist: the advocate (the strongest honest case for the plan) or
  the pre-mortem ("it shipped and failed; how?").
- **Chair:** the one agent that merges the findings into a recommendation and a table of conditions.
- **Verifier:** a fresh agent whose job is to refute one finding by reproducing its evidence; unsure means refuted,
  and evidence it cannot reach (a private service, a page it may not fetch) becomes a question for you.
- **First view:** the orchestrator's own opinion of the target, told to you in three lines before any reviewer
  starts. No agent ever sees it.
- **Blocker:** a finding that is critical or major, protects something the plan must honour (an ask, a done item,
  a repo rule or a user scenario), and that a verifier reproduced.
- **Condition:** a numbered item in the summary, with a check someone can run. A **should-fix** is a non-blocking
  condition worth doing; a **follow-up** is one moved out of scope, with a reason.
- **Gate:** the fixed rule that turns the verification results into the outcome. [The gate](#the-gate) gives it.
- **Planted defect, answer key:** the eval projects are made up, with flaws put into their plans on purpose; the
  answer key lists them, and the scorer checks a run against it.

## Table of contents

- [Install](#install)
- [Quick start](#quick-start)
- [Terms](#terms)
- [What makes it different](#what-makes-it-different)
- [At a glance](#at-a-glance)
- [Why it exists](#why-it-exists)
- [How a run works](#how-a-run-works)
- [The stages, one by one](#the-stages-one-by-one)
- [Walkthrough: one finding, end to end](#walkthrough-one-finding-end-to-end)
- [Depth: how big the panel is](#depth-how-big-the-panel-is)
- [Seats and models](#seats-and-models)
- [Lenses](#lenses)
- [Stances](#stances)
- [Findings: shape, evidence, severity and what blocks](#findings-shape-evidence-severity-and-what-blocks)
- [Who sees what](#who-sees-what)
- [The gate](#the-gate)
- [Rounds](#rounds)
- [What it reads, writes and needs](#what-it-reads-writes-and-needs)
- [What you see: every outcome and error](#what-you-see-every-outcome-and-error)
- [Test results](#test-results)
- [Evals](#evals)
- [Limits](#limits)
- [Files](#files)
- [Install details](#install-details)
- [Background](#background)

## What makes it different

No single piece is new. The combination is, and each piece answers a known way AI review goes wrong:

| What other tools usually do | What crossfire does instead | Why it matters |
| --- | --- | --- |
| review the **code diff**, after it is written (code-review tools, pull-request bots) | reviews the **plan, before any code exists** | a design flaw costs least to fix before it is built |
| collect **opinions** from several models and blend them (multi-model consensus tools, LLM councils) | every finding must cite **evidence**, and every finding that could block is handed to a **verifier whose job is to refute it**; unsure means refuted | fewer confident, wrong findings for someone to act on |
| end in **a report or a score** | ends in **a decision**: PASS, REVISE, STOP, ESCALATE or INCOMPLETE, decided by a fixed rule, not a model | you know what to do next |
| list problems once | turns each problem into a **condition with a runnable check**, which the **next round re-checks by id** | review becomes a loop that closes, not a document that ages |
| **guess** when a fact is missing | **stops and asks you**, with at most three questions first | in three of four eval runs it stopped on a real gap instead of inventing an answer |
| run the same panel on every change | **sizes the panel to the risk**: quick for a copy change, deep for authentication or data | cost tracks what is at stake |
| let reviewers see each other, and agree | reviewers draft **blind**, cross-examine **anonymously**, and the chair never learns who wrote what | agreement comes from separate reviewers opening the same file, not from reading each other |
| show what the panel said | records your main session's (the orchestrator's) **first view before any reviewer starts**, and says what the panel changed | you can see whether the panel was worth running |
| ask you to trust it | ships its own **evals**: made-up projects with planted defects (flaws put in on purpose), an answer-key scorer, and the measured results | its claims can be checked and re-run |

It runs inside Claude Code with no API keys, no MCP servers and no accounts.

The full comparison, tool by tool, with diagrams and examples from real runs, is in [COMPARISON.md](COMPARISON.md).

**Who it is for:** anyone who lets Claude, or another agent, write plans. The clearest use is to check your agent's
plan before it writes the code.

**What it costs you** (measured on the [examples](examples/README.md): small made-up projects, at list
price, with the main session on Opus; a larger repo may cost more):
- **Money and time:** $3–17 and 8–33 minutes a run, with about 90% of the cost on Opus.
- **Reach:** Claude Code only, and one model family.
- **Evidence:** a small eval set so far, and the current version is not yet run end to end (see
  [Not yet measured](#not-yet-measured)).

## At a glance

```
 you type                              you get back, for example (in the session, at most 12 lines)
 ─────────────────────────────────     ───────────────────────────────────────────────────────
 /crossfire docs/plans/reset.md        Gate: REVISE. C1 and C2 are verified blockers.
                                       Recommendation: build it once tokens stay out of the
   (optional) quick | standard | deep    access log (C1) and used tokens stop working (C2).
   (optional) whether                  Questions: none.
   (optional) +privacy                 Summary: docs/plans/reset.crossfire.md

                                       and on disk:
                                         docs/plans/reset.crossfire.md   the one-page decision
                                         .crossfire/reset/r1-…/          every draft, verdict, file
```

`whether` asks the panel to judge whether to do it at all, not only how; `+privacy` forces the privacy lens onto the
panel. The reply in the session is at most 12 lines; the full summary is the file it names. That file is one screen
of prose above a conditions table. Each condition has an id, a severity, whether it blocks, what it protects, a
check someone can run, a status and the findings it came from. You fix what blocks, run `/crossfire` again on the
same target, and the next round checks those conditions by id.

It is manual only: it starts when you type `/crossfire`, never by itself, and it has no background process. It
commits, pushes and posts nothing: you decide what to keep.

## Why it exists

An agent that writes a plan and then reviews it shares its own blind spots. Asking one more agent for "a review"
mostly returns the same blind spots, at greater length. Multi-agent review is the usual answer, and the published
evidence says where it goes wrong:

- **One model in many roles is not many reviewers.** Giving a model a persona does not make it more accurate, and
  agents that debate drift from correct answers towards agreement with their peers. Even separate models make
  correlated errors: one study found nine judges carried about two votes' worth of information. A majority of
  simulated voices is not a majority of independent reviewers.
- **Unproven findings cost more than missed ones.** A finding with no file, count or command behind it reads as
  confidently as one with evidence, and someone acts on it. Model reviewers also judge correct code non-compliant
  surprisingly often.
- **Size has to be chosen, or it grows.** A panel that runs every reviewer on every change spends the same on a copy
  edit as on a payments change, and the report gets longer than anyone reads.
- **Scores are not decisions.** Model judges change their verdict when the order of the answers changes, prefer
  longer answers and favour their own, and an average of their ratings tells the owner nothing to do.

The sources are in [Evidence behind the design](#evidence-behind-the-design).

crossfire keeps what works in multi-agent review (independent first drafts, anonymous peer review, assigned
stances, a gate with a cap) and closes those gaps: separate agents each hold one lens or stance, every blocker is
verified, the depth is picked from the risk, and conditions with runnable checks replace scores and votes (see the
table in [What makes it different](#what-makes-it-different)).

## How a run works

The orchestrator follows [SKILL.md](SKILL.md), starts the agents, and is the only one that writes files. Every other
box below is a separate agent that reads and reports.

```
/crossfire <plan | PR | question> [quick | standard | deep] [whether] [+lens]

 0 FRAME     orchestrator, no agents; nothing is written to disk until step 7
             pin the target (path@sha + its text, PR head, question) ── unreadable? stop, one line
             frame: decision · mode · asks A1.. · done D1.. · options O1.. · repo rules
             · past failures
             first view: three lines, told to you before any reviewer starts
                    │
 1 SEAT      depth from risk ── lenses the target triggers ── advocate + pre-mortem ── models
                    │
 2 DRAFT     ┌────────────┬────────────┬────────────┬────────────┐   one message, in parallel,
             │ lens       │ lens       │ advocate   │ pre-mortem │   read-only, blind to each other,
             │ (sonnet)   │ (sonnet)   │ (sonnet)   │ (opus)     │   ≤ 7 findings, ≤ 600 words
             └─────┬──────┴─────┬──────┴─────┬──────┴─────┬──────┘
                   └────────────┴──────┬─────┴────────────┘
 3 LABEL     one global label F1.. per finding, in random order; the orchestrator keeps who wrote it
                                       │
 4 CROSS     shuffled per reader, own excluded, authors hidden, on sonnet
             standard: the advocate examines · deep: every seat · quick: skipped
                                       │
 5 VERIFY    duplicates merged into groups, then fresh verifiers (opus): ≤ 2 / 4 / 8 by depth
             VERIFIED at major+ keeps it · REFUTED drops it · NEEDS DATA makes it a question
                                       │
 6 DECIDE    one chair (opus), blind to authors and to the first view:
             recommendation · conditions (with the labels they came from) · questions · disputes
                                       │
 7 GATE      reconcile the chair's table with the verification results, then a fixed rule
             ──▶ INCOMPLETE | ESCALATE | STOP | PASS | REVISE
             writes the run folder and <target>.crossfire.md
```

## The stages, one by one

**0. Frame.** The orchestrator pins exactly what is being reviewed:
- a file: its path, the commit, whether it has uncommitted changes, and its full text (saved later as
  `target.md`, which the next round diffs against);
- a pull request: its head SHA, after checking that the checkout is at that commit;
- a question: the repo's commit, with the question's text as the target.

A target nobody can open stops the run before any agent starts: a panel that reviews a missing file produces
confident findings about nothing.

The frame quotes the target and your instructions, never the orchestrator's opinion:
- the decision, in one sentence, and the mode (`how`: build what was asked; `whether`: "don't" is a valid answer);
- the asks, numbered `A1`, `A2`…;
- the done items, numbered `D1`…, marked `(inferred)` when the target had none;
- in whether-mode, the options `O1`…, always including "keep things as they are", with the one you said you lean to
  marked `(leading)` and your words quoted;
- the repo's own rules from `AGENTS.md`, `CLAUDE.md` and `CONTRIBUTING`, quoted;
- where the repo keeps records of past incidents, if it does;
- the target's size: over about 600 lines, reviewers get a section list instead of the full text.

The orchestrator then tells you its own first view, in three lines, before any reviewer starts. Saying it to you
puts it on record, so it cannot drift towards the panel's answer; no agent ever sees it.

**1. Seat.** A seat is one reviewer's place on the panel: a lens, the advocate or the pre-mortem. Depth comes from risk (see [Depth](#depth-how-big-the-panel-is)). Lenses are seated only when the
target triggers them (at standard and deep depth, architecture and testing first when they apply), and the lenses
left out are listed with a reason, so "not checked" is visible rather than
silent. The orchestrator tells you the depth, the seats and why, and continues without waiting.

**2. Draft.** Every reviewer starts in one message, so they run at the same time and none can see another. Each
gets the frame, its seat's checklist and the finding contract pasted in full. Pasting guarantees the text reaches
every reviewer (a reviewer only told to read a rubric file often does not; see [Prior art](#prior-art)); it cannot
guarantee the reviewer applies it. Reviewers open repo files themselves and cite them.

A reply that breaks the contract gets one re-ask; a reviewer that errors gets one retry; after that the seat is
"not run". Two things are swept out of the replies: the advocate's "Keep:" list, which goes to the chair as an
unattributed list, and any out-of-seat blocker a reviewer noted, which becomes a finding if it has evidence.

**3. Label.** Every finding gets one global label, `F1`, `F2`…, in a random order across seats; from round 2 the
label carries the round (`r2-F3`). Every later stage and the summary's `From` column use the labels, so any
condition traces back to its findings, while the mapping to seats and models stays with the orchestrator.

**4. Cross-examine.** Findings are listed with the authors stripped, shuffled in a different order for each reader,
and each reader's own findings are left out. Each finding gets "agree", "dispute with evidence" or "can't tell",
and the reader names at most three blocking-grade problems everyone missed. Disputing without evidence counts as
"can't tell". Cross-examiners run on `sonnet`.

**5. Verify.** Every finding that could block (critical or major, and protecting something), and every disputed
one, goes to a fresh verifier on the strongest model, whose job is to show it is wrong. Findings that state the
same problem are merged into a group first and verified once. Verifiers are capped by depth (2, 4, 8), with
related groups batched, so nothing is dropped for cost. Each verifier answers one line per label:

| Verdict | Effect |
| --- | --- |
| `VERIFIED critical` or `VERIFIED major` | stays blocking-grade |
| `VERIFIED minor` or `VERIFIED nit` | becomes advisory, at the verifier's severity |
| `REFUTED` | dropped; unsure means refuted |
| `NEEDS DATA` | becomes a question for you; this includes evidence the verifier cannot reach, which it names |

**6. Decide.** One chair merges duplicates, turns findings into conditions with runnable checks, moves overreach
to follow-ups with a reason, lists the questions only you can answer and the disputes the evidence could not
settle, and writes a two- or three-sentence recommendation. It never learns who wrote what, and never sees the
orchestrator's first view.

**7. Gate and write.** The orchestrator first checks the chair's table against the verification results: every
verified blocker must be a blocking row, and every blocking row must trace to one. It corrects any mismatch and says
so. Then it applies [the rule](#the-gate) to the verification results, never to the chair's wording. It writes the
whole run folder in one go, then the summary beside the target, comparing the chair's recommendation with its own
first view to say what the panel changed. Last, it tells you the gate, the recommendation, the blocking conditions,
the questions and the summary's path.

## Walkthrough: one finding, end to end

This follows one real finding through the [password-reset example](examples/password-reset/README.md). The plan
puts the reset token in a URL (`GET /reset?token=…`), and the repo's access log records full URLs. The run used the first
version of the skill. The stages are the same today, but four things have been added since: findings are merged by
root cause before verification, verifiers are capped by depth, the chair's table is reconciled with the verdicts,
and nothing is written to disk until the run ends. That version also saved one file per reply, so its counts differ
from a run today.

```
 plan:24, plan:45                          src/http/logging.js:7
 "/reset?token=<token>"                    url: req.originalUrl  ("kept for 90 days", line 1)
            │                                         │
            └────────────────────┬────────────────────┘
                                 ▼
 2 DRAFT   six of seven reviewers, each on its own, wrote it as a finding:
             pre-mortem, security, privacy, architecture  → critical
             advocate, reliability                        → major
                                 │
 3 LABEL   F33, F34, F29, F40, F2, F23  (random labels; nobody downstream knows the seat)
                                 │
 4 CROSS   F40: agree 6 · dispute 0 · can't tell 0   F2, F23: 5 disputed "major" as too low
                                 │
 5 VERIFY  two batches of three (F2 + F23 + F40, and F33 + F34 + F29)  →  two Opus verifiers
           (the current version merges by root cause first, so all six would be one group)
           both reproduced logging.js:7 and plan:24/45, and found no redaction anywhere in the repo;
           one corrected "never expire" (a nightly job removes rows after 30 days)
           verdict: VERIFIED critical  →  blocks
                                 │
 6 DECIDE  C1 | critical | yes | protects AGENTS.md:8 "Never write … tokens … to logs"
           check: a test sends GET /reset?token=X through accessLog and asserts X is not logged
                                 │
 7 GATE    C1 is one of five verified blockers; three more findings needed facts only the owner had
           → STOP (the questions come first), with C1 to C5 listed to fix before round 2
```

The architecture reviewer's finding, as the contract shapes it:

```
### Reset token in the URL is written to the access log
- claim: GET /reset?token=<token> is logged in full, so live tokens are stored in the log store for
  90 days.
- evidence: src/http/logging.js logs `url: req.originalUrl` and its header says "kept for 90 days".
  Plan link: https://app.quillbox.example/reset?token=<token>. AGENTS.md:8 says "Never write …".
- severity: critical
- protects: AGENTS.md:8 "Never write passwords, tokens…"; D2 "The old password stops working…"
- condition: the access log redacts the token parameter, or the token travels in the URL fragment or
  a POST body. Check by requesting /reset?token=x and reading the log line.
- refute: log shipping that strips query strings. logging.js shows none.
```

Six independent findings of one problem, verified in two batches, is the panel working as intended:
agreement that comes from separate reviewers opening the same file, not from reading each other.

The same run shows the other side of verification. A reliability finding said tokens are stored in plaintext.
Its verifier reproduced the evidence but rated it minor: a database leak is not normal use, and the repo already
stores session ids raw. So it became an advisory follow-up rather than a blocker. That is the one defect deliberately planted in this made-up project (see [Terms](#terms)) that
the run did not block on, and why the security lens now says a credential readable from a database, replica or
backup is blocking-grade (see [Test results](#test-results)).

## Depth: how big the panel is

The orchestrator picks the depth from what the target touches and says why. You can override it with `quick`,
`standard` or `deep`.

```
                     does the target touch authentication, permissions, money,
                     deleting or migrating stored data, personal data,
                     a public contract, or production infrastructure?
                          │ yes                                │ no
                          ▼                                    ▼
                        DEEP                    is it only docs, copy or configuration
              advocate + pre-mortem             text, with no new runtime code and
              + up to 5 lenses                  no data change?
              every seat cross-examines            │ yes                  │ no
              up to 8 verifiers                    ▼                      ▼
                                                 QUICK                 STANDARD
                                       pre-mortem + 2 lenses    advocate + pre-mortem
                                       no cross-examination     + up to 3 lenses
                                       up to 2 verifiers        the advocate cross-examines
                                                                up to 4 verifiers
```

| Depth | Seats | Cross-examination | Most agent calls |
| --- | --- | --- | --- |
| quick | pre-mortem + 2 lenses | none | 3 drafts, 2 verifiers, 1 chair = 6 |
| standard | advocate + pre-mortem + 3 lenses | the advocate | 5 drafts, 1 cross, 4 verifiers, 1 chair = 11 |
| deep | advocate + pre-mortem + 5 lenses | every seat | 7 drafts, 7 cross, 8 verifiers, 1 chair = 23 |

The counts are ceilings, never targets: a standard run whose target triggers only two lenses seats two. Findings
that state the same problem are merged before verification, and when there are more groups than verifiers, related
groups are batched, so nothing is dropped to save cost.

## Seats and models

| Role | Model | Why |
| --- | --- | --- |
| lenses, advocate | `sonnet` | the work; at deep depth one lens runs on `fable` (another Claude model), for a second model's view |
| pre-mortem | `opus` | the seat most likely to find what no checklist names |
| cross-examiners | `sonnet` | weighing evidence that is already written down |
| verifiers, chair | `opus` | the verdicts: confirming or refuting a finding runs on the strongest model, because a wrong verdict costs more than the extra spend |

`fable` is another Claude model, used for a second model's view. When an alias is unavailable, the seat falls back
as [the errors table](#what-you-see-every-outcome-and-error) says.

## Lenses

A lens is a checklist with a trigger, not a persona: no names, no voices, no doctrines. Each file says when to seat
it, what to check, what is typically blocking-grade, what usually is not, and where to look.

| Lens | Seated when the target touches | File |
| --- | --- | --- |
| Architecture and placement | a new or moved component, table, interface or dependency | [architecture.md](references/lenses/architecture.md) |
| Security | auth, tokens, permissions, untrusted input, secrets, anything an attacker can call | [security.md](references/lenses/security.md) |
| Privacy and data handling | personal data, or anything said to users about their data | [privacy.md](references/lenses/privacy.md) |
| Reliability and operations | jobs, queues, migrations, deploys, external calls, retries, caches | [reliability.md](references/lenses/reliability.md) |
| Performance and data at scale | queries, loops over stored data, lists, caches, fan-out, stated load | [performance.md](references/lenses/performance.md) |
| Cost | paid services, model or API calls, growing storage, scheduled jobs, egress | [cost.md](references/lenses/cost.md) |
| Product, UX, copy and accessibility | anything a user sees, reads, clicks or receives | [product.md](references/lenses/product.md) |
| Testing | behaviour that should be checked automatically, judged by the repo's own rules | [testing.md](references/lenses/testing.md) |
| Infrastructure and cloud | cloud resources, permissions, networking, pipelines, environment config | [infrastructure.md](references/lenses/infrastructure.md) |

The testing lens judges against the repo's own testing rules, never a universal standard: a method the repo does
not use is a suggestion, not a blocker. You can force a lens onto the panel with `+<lens>`, for example `+privacy`.

## Stances

Two seats take a stance instead of a lens ([stances.md](references/stances.md)):

- **Advocate** (standard and deep). It makes the strongest honest case for the plan: what is right and must not
  change (its "Keep:" list), and what must be true for the plan to work. In cross-examination it disputes findings
  that are wrong or overstated. It is the run's counterweight to reviewers who, asked to find problems, find them
  in sound plans too. In the walkthrough above, the advocate itself was one of the reviewers who found the leak.
- **Pre-mortem** (every depth). "It shipped six months ago and failed; how?" Each failure is a chain from a normal
  day, tied to a line of the plan and evidence in the repo.

Both carry the same guardrail: a stance decides what you look for first, never what is true.

## Findings: shape, evidence, severity and what blocks

Every finding has the same shape ([contract.md](references/contract.md)): claim, evidence, severity, protects,
condition (as a runnable check), what would refute it, and, in whether-mode, the option it applies to. A reply is
a one-sentence verdict, at most seven findings, and a "Not reviewed" line, in at most 600 words.

Evidence is one of:
1. a file and line, with a short quote;
2. a read-only command and what it printed;
3. a count, and how it was counted;
4. a dated link to a library's or service's own documentation;
5. the target's own words, contradicting another of its words or an ask.

"This looks wrong" is not evidence, and a claim about production that no file states is written `needs data:`.

| Severity | Meaning |
| --- | --- |
| critical | On a normal path: data lost or corrupted, a secret or personal data exposed, money wrong, or the service down. |
| major | A key happy path or important error path broken; a stated ask missing or contradicted; a repo rule broken. |
| minor | It works, but worse. |
| nit | Wording, naming, formatting. |

A finding's life, from draft to condition:

```
 drafted ──▶ labelled ──▶ cross-examined ──▶ blocking-grade?
                                                (critical or major, and protects something)
                                 │ no                       │ yes, or disputed
                                 ▼                          ▼
                             advisory                   verifier
        (goes to the chair as is)       ┌───────────┬───────┴───┬───────────┐
                                        ▼           ▼           ▼           ▼
                                    VERIFIED    VERIFIED      REFUTED   NEEDS DATA
                                    major+      minor/nit     (dropped) (a question)
                                        │           │
                                        ▼           ▼
                                    blocking      advisory
                                    condition     condition
```

A finding **blocks** only when it is critical or major, its `protects` names an ask, a done item, a repo rule or a
user scenario, and a verifier reproduced it at that severity. Blocking is reserved for:
- a credible failure in normal use;
- a missing or contradictory requirement;
- a broken key happy path;
- an important error or recovery path that fails.

Theoretical states, speculative hardening and polish are minor at most.

## Who sees what

```
  ┌──────────────────────── orchestrator (your session) ─────────────────────────┐
  │ sees everything · tells you its first view before any reviewer starts        │
  │ holds the label → seat → model map · writes files only at the end            │
  └───────┬───────────────────┬────────────────────┬───────────────────┬─────────┘
          │ frame + seat      │ others' findings,  │ findings or       │ all findings with
          │ + contract        │ labels only,       │ groups, labels    │ verdicts and tallies,
          ▼                   ▼ shuffled           ▼ only              ▼ labels only
     reviewers          cross-examiners        verifiers             chair
   ═══════════════════════ wall: no agent sees who wrote what, ════════════════════════
   ═══════════════════════ the first view, or the .crossfire/ folder ══════════════════
```

| Agent | Sees | Never sees |
| --- | --- | --- |
| Reviewer (draft) | the target, the frame, its own seat text, the contract | other reviewers' work; the orchestrator's first view |
| Cross-examiner | other seats' findings, under their labels, shuffled | who wrote them; its own seat's findings; the first view |
| Verifier | the findings it checks, with any cross-examination lines | who wrote them; the first view |
| Chair | every finding with its verification result and tally, and the Keep list | who wrote what, on which model; the first view |
| Orchestrator | everything | nothing hidden; it tells you its first view before any reviewer starts |

No file naming who wrote what exists until the run ends, and every agent is told never to open `.crossfire/` or a
`*.crossfire.md` file, where earlier rounds' records live. Hiding names removes the label, not the writing style,
so a model may still recognise its own prose. The research says removing labels helps; it does not say it is
enough.

## The gate

The orchestrator applies this rule itself, from the verification results, after reconciling the chair's table. The
first line that matches is the outcome ([gate.md](references/gate.md)):

```
 did a reviewer, cross-examiner or verifier fail twice,
 or a reply stay malformed? ───────────── yes ──▶ INCOMPLETE  never a pass; lists what did not run
          │                                                    and the verified blockers so far
          │ no
          ▼
 round 3 with a verified blocker still open, or the
 last fix caused 2+ new verified blockers, or a
 fixed blocker came back? ────────────── yes ──▶ ESCALATE    you choose: revise, clarify,
          │ no                                                 narrow, defer, cancel
          ▼                                                    (escalation never approves)
 a blocking-grade finding that needs a fact only you
 have (NEEDS DATA), or, in whether-mode, a choice the
 frame records as yours? ─────────────── yes ──▶ STOP        3 questions first, any others after;
          │ no                                                 verified blockers listed to fix too
          ▼
 no verified blocker? ────────────────── yes ──▶ PASS        conditions stay listed as
          │ no                                                 should-fix or follow-up
          ▼
        REVISE   fix the verified blockers, then run /crossfire again for round N+1
```

- Escalation comes before STOP, so a third round cannot turn into a fourth by asking a question.
- STOP outranks REVISE, so a STOP summary also lists any verified blockers; fix them along with answering the
  questions.
- In how-mode, only you can narrow the scope. The panel reviews how to build what you asked for, and never answers
  a blocker by cutting an ask.
- In whether-mode, "don't do it" and "keep things as they are" are valid recommendations.
- A should-fix is a non-blocking condition worth doing; a follow-up is one the chair moved out of scope, with a reason.

When the run itself shows signs of overreaching (a second round raising new blockers with no new user-visible risk,
or more conditions than the plan has steps), the summary says so in one line under the verdict.

The chair moves a condition to a follow-up, with the reason in its row, when it overreaches:
- it tests states the real system cannot produce;
- it adds an abstraction only so a test can exist;
- it hardens against a threat the stated environment does not have;
- its check would cost more than the feature, for a risk normal use does not reach.

## Rounds

Running `/crossfire` again on the same target starts the next round.

```
 round 1 ──▶ REVISE or STOP ──▶ you change the plan (answer, fix, or mark "won't do: <reason>")
                                     │
                                     ▼
 round 2 ── diff vs round 1's target.md ── same seats, same depth, fresh agents ── each reports
            "Cn: met" or "Cn: not met" for its open conditions, plus new risks the change caused
                                     │
                                     ▼
            a verifier must agree a blocker is met before it is marked "fixed in round 2"
                                     │
                     ┌───────────────┼─────────────────┐
                     ▼               ▼                 ▼
                   PASS         REVISE / STOP      round 3 with a verified blocker
                                (round 3)          still open ──▶ ESCALATE (no round 4)
```

1. The orchestrator finds the last round: the summary beside a target file, or the newest run folder for a PR or a question.
2. The orchestrator diffs the target against the last round's saved copy (`target.md`), so an uncommitted plan edited in place
   still shows its changes. A PR is diffed against its last head SHA. If the last round has no saved copy, it
   diffs against the commit that round pinned; if that commit is gone, it treats every section as changed and
   says so.
3. The orchestrator reuses the frame, the depth and every lens you forced with `+lens`, seats fresh agents in the
   same seats, and adds a seat for any `+lens` given on the re-run. Each is briefed with the open conditions, the
   changed sections and your won't-do list.
4. A blocker a reviewer says is met goes to a verifier before it is marked fixed; unsure means not met. A blocker
   verified in an earlier round counts as a verified blocker until then.
5. The chair gets the previous Conditions table and keeps every row, so the record shows what each round caught.

A condition you mark `won't do: <reason>` is closed; reviewers are told not to raise it again unless the change made
it worse. Re-running an INCOMPLETE round keeps its number and runs only the parts that failed. Critique-and-revise
loops get most of their gain in the first three or four rounds, which is why round 3 escalates instead of going round again.

## What it reads, writes and needs

**Reads:**
- the target (a file, `gh pr view` and `gh pr diff`, or the question);
- the repository it runs in: the files the target touches, `git log`, and the instruction files;
- the repo's incident or postmortem records, if it keeps them;
- the web, only for the official documentation of a library or service the target uses.

Its instructions keep it away from production systems, dashboards and databases, and it has no credentials for
them beyond what your session has. Anything that needs them becomes a question for you.

**Writes**, only at the end of the run:

```
 <repo root>/
 ├── docs/plans/reset.md
 ├── docs/plans/reset.crossfire.md     the summary: verdict, conditions, questions, disputes,
 │                                     not checked, what the panel changed, run line
 │                                     (summary.md in the run folder
 │                                     for a PR or a question)
 └── .crossfire/                       excluded through .git/info/exclude (local, never committed)
     └── reset/
         └── r1-20261112-1214/
             ├── frame.md              the decision, asks, done items, options, repo rules
             ├── prior.md              the orchestrator's first view, as told to you
             ├── target.md             the target as reviewed; the next round diffs against it
             ├── seats.md              seat → model → labels, merge groups, verifier batches
             ├── drafts.md             every reviewer's reply, one section each
             ├── cross.md              every cross-examination
             ├── verify.md             every verifier's verdicts
             └── chair.md              the chair's reply
```

The orchestrator adds the `.crossfire/` line to `.git/info/exclude` if it is missing and says so. It commits,
pushes and posts nothing: you decide what to keep. Web searches and page fetches leave the machine, which is why
reviewers are told never to put code or anything private in them.

**Needs:**
- Claude Code with subagents and the `sonnet` and `opus` model aliases (`fable`, another Claude model, is used for
  one lens at deep depth; if it is unavailable the seat falls back to `sonnet`);
- the two agent definitions, recommended but not required: without them the run uses general-purpose agents with the
  same briefs, and the summary says the read-only limit was in the prompt only (see [Install](#install));
- `gh`, signed in, only for PR targets.

No API keys, no MCP servers, no accounts. Besides the model provider Claude Code already uses, the network traffic is
reviewers' web searches and page fetches for library documentation, and `gh` calls to GitHub for a PR target.

**Alerts:** none. It runs only when you type it, and stops when it reports.

## What you see: every outcome and error

| Situation | What you see |
| --- | --- |
| No target, or a target nobody can open | One line naming what is missing; no agents start |
| A PR target without `gh` signed in | One line, and an offer to review a local branch diff instead |
| A PR target while the checkout is on another commit | One line asking you to check out the PR's branch (`gh pr checkout <number>`), so reviewers read the PR's files |
| The agent definitions are not installed | The run uses general-purpose agents with the same briefs, and the summary's Run line says the read-only limit was in the prompt only |
| A reviewer or cross-examiner errors | One retry; if it fails again, it is "not run" and the gate is **INCOMPLETE** |
| A reply breaks the contract | One re-ask naming the problem; if it is still malformed, **INCOMPLETE** |
| A verifier fails twice | **INCOMPLETE**, naming the findings left unchecked |
| The chair's table disagrees with the verification results | The orchestrator corrects the table and says what it corrected in the Run line |
| Web search is unavailable | Reviewers continue; what they could not check appears under "Not checked" |
| No `AGENTS.md`, `CLAUDE.md` or `CONTRIBUTING` | The frame says "none found"; the testing lens judges by the existing tests |
| The target is over about 600 lines | Reviewers get its section list and path, and open it themselves |
| A finding turns on a fact only you have | **STOP**, with the three questions that matter most first, and any others after |
| A verified blocker | **REVISE**, with the condition and its check |
| Round 3 with a blocker still open | **ESCALATE**, with five choices (revise, clarify, narrow, defer, cancel) |
| The chair fails twice | The orchestrator writes the summary from the verification results, marked "chair did not run" |
| A model alias (`fable`, `opus`) is unavailable | The seat runs on the next model down (`fable` → `sonnet`; `opus` → the strongest available), and the Run line says so |
| An agent sends a second reply nobody asked for | The reply to the orchestrator's own brief is used; the other is saved in the stage file, marked unrequested, and not used |
| Nothing blocks | **PASS**, with any should-fix conditions and follow-ups listed |

## Test results

Everything below was measured, on the dates given.

### End-to-end runs

Each run was a fresh, headless Claude Code session on a small made-up project with defects planted in its plan
(the self-review excepted). The runs were made on 2026-11-12. Their summaries were scored with the current
[score.py](evals/score.py) on 2026-11-20. Each example's README records what its run found; the raw files the
runs wrote are not published.

| Case | Depth | Gate (expected?) | Planted defects | Blocking rows the key did not list | Time | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| [Password reset](examples/password-reset/README.md) | deep (picked) | STOP (yes) | 4 of 5 blocked; the 5th found but advisory | 1: no test for `GET /reset`, against the repo's rule (real) | 32.6 min | $16.55 |
| [Report scheduling](examples/report-scheduling/README.md) | standard, whether | STOP (yes) | 2 of 2 | 2: a replaced server re-sends to everyone done; no alert on the dead-letter queue (both real) | 20.1 min | $8.18 |
| [Help page, round 1](examples/help-page-copy/README.md) | quick (picked) | STOP (yes, after the key was changed) | none planted | 0 | 9.5 min | $3.93 |
| [Help page, round 2](examples/help-page-copy/README.md) | quick | PASS (yes) | none planted | 0 | 8.0 min | $3.09 |
| [Self-review of this README](examples/self-review/README.md) | standard | REVISE (not an eval case) | — | 4 verified blockers, all fixed | 28.6 min | $11.42 |

| Case | Skill version | Agent calls |
| --- | --- | --- |
| Password reset | first | 31 |
| Report scheduling | first | 14 |
| Help page, round 1 | first | 9 |
| Help page, round 2 | second | 4 |
| Self-review of this README | second | 11 |

First version: before the merge by root cause, the verifier cap and the reconciliation of the chair's table with the
verification results. Second version: with them.

What the runs show:
- **It finds what was planted.** All 7 planted defects were found, and 6 met the answer key. The 7th, plaintext
  token storage, had to block and did not: its verifier rated it minor, as the
  [walkthrough](#walkthrough-one-finding-end-to-end) shows.
- **What it adds beyond the key is real.** Every blocking row the key did not plant was a genuine problem in the
  example: a missing required test, a re-send after a server is replaced, a missing alert. The password-reset run
  also asked three questions it could not settle from the repo (a possible XSS through the echoed token, scripts
  reading the token from the URL, and the token in queue job data), and listed sessions that survive a reset as a
  minor condition.
- **It stops rather than guesses.** Three of four eval runs ended at STOP, each on facts the example did not
  contain (what renders a page, whether a queue schedule registers once). Round 2 of the help page answered its
  questions in the plan, and the run passed with nothing blocking.
- **It sizes itself, in the three runs where it chose.** The picker chose deep for the authentication change,
  standard for the scheduling question and quick for the copy change.
- **The summaries stay short.** The words above the Conditions table were 208, 265, 122 and 101 (counted from the
  run files, which are not published).
- **It corrects its own key.** The password-reset panel pointed out that "tokens never expire" was not quite right:
  a nightly job removes rows after 30 days, so the real defect is reuse after the password changes.

Costs are the list-price figures each session reported (`total_cost_usd`), not a bill:
- **Opus takes most of it:** 86–97% of every run (the published records give 86%, 96% and 95%; the rest is from
  the run files, which are not published), spent by the orchestrator (your main session, which ran on Opus in these
  runs, judging by each session's model usage), the pre-mortem, the verifiers and the chair. The Sonnet seats cost
  cents each; the one `fable` seat in the deep run cost $1.19 (from the run files).
- **The verifier cap has been measured once.** The first version had no cap, and the deep run used 16 verifiers.
  The second version merged duplicates and capped verifiers: the self-review batched 9 groups into 4 verifiers.
  A deep run under the cap has not been measured.

### Not yet measured

- the current version end to end (every recorded run predates the review fixes);
- a deep run under the verifier cap;
- the security-lens change that names stored credentials as blocking-grade;
- starting `/crossfire` from a Sonnet session to cut the orchestrator's cost;
- installing it as a plugin (`/plugin install crossfire@agents`), and the `crossfire:`-prefixed agent and command
  names a plugin install gives: every recorded run used a copied skill folder;
- the copy install on the current version.

## Evals

[evals/](evals/) runs each example end to end and scores it; [evals/README.md](evals/README.md) explains every
part. In short:

```bash
cd evals
python3 -I run.py password-reset --out /tmp/password-reset-rerun
python3 -I score.py password-reset /tmp/password-reset-rerun/summary.crossfire.md
python3 -I test_score.py && python3 -I test_run.py
```

`run.py` is a paid headless session (about $10–20 for this case); `score.py` checks the summary's Conditions table
against the case's answer key in [cases.json](evals/cases.json); the last line is the tools' own tests, which are
free. How `run.py` keeps the answer keys out of the session is in [evals/README.md](evals/README.md).

Caveat: the recorded runs used an installed skill folder that also held the answer keys. A search of their files
found no mention of the keys, but the runs could have read them. The raw files are not published, so this cannot be
rechecked. (The self-review read them on purpose: its target was the skill's own README.)

## Limits

- **One model family.** Every agent is a Claude model, and model errors correlate, so a panel is less independent
  than its seat count suggests. Most of the independence comes from different lenses, evidence and verification,
  not from model labels.
- **It sees the repo, not production.** Traffic, row counts and user behaviour come from files or from you; when
  neither has them, they become questions.
- **Read-only is enforced for files, not for Bash.** The agent definitions have no edit or write tools. They keep
  Bash for read-only commands such as `git log` and `grep`, and that limit is in their instructions. Your normal
  permission prompts still apply.
- **Anonymity hides labels, not style.** A model may still recognise its own prose; see
  [Who sees what](#who-sees-what).
- **Prompt injection.** A plan, a pull request or a repo file can contain text written to steer the reviewers.
  The briefs and agent definitions say that everything read is material and never instructions, and that no brief
  can relax their standing rules. No reviewer can edit files, and your permission prompts still apply. That limits
  the damage; it does not prevent a steered review, so treat a run on an untrusted pull request as advice to check.
- **A verifier can wrongly refute or downgrade a real finding.** Verdicts are in the run folder's `verify.md`. Skim
  them on a high-stakes run; the plaintext-token example above is one such downgrade.
- **It reviews plans and the design of changes, not lines of code.** For a line-level code review, use a code-review
  tool on the diff.
- **The evals are small:** three made-up cases, one in two rounds, plus a self-review, one run each, all on
  earlier versions. See [Not yet measured](#not-yet-measured). They do not measure its value on your real plans.

## Files

```
crossfire/
├── SKILL.md                     the procedure the orchestrator follows (manual only: /crossfire)
├── README.md                    this file
├── PLAYBOOK.md                  how to use it, step by step
├── COMPARISON.md                how it compares to other AI review tools, with examples
├── references/
│   ├── contract.md              finding shape, evidence, severity, what blocks, the reply
│   ├── stances.md               advocate, pre-mortem, the guardrail
│   ├── gate.md                  the gate rule, overreach, the summary template, rounds
│   ├── briefs.md                the exact briefs for reviewer, cross-examiner, verifier, chair
│   └── lenses/                  nine checklists, one per lens
├── agents/
│   ├── crossfire-reviewer.md    read-only reviewer type (drafts, cross-examination, chair)
│   └── crossfire-verifier.md    read-only verifier type
├── examples/                    four examples, each explained in a README; the eval projects
└── evals/                       run.py, score.py, cases.json (answer keys), tests, a README
```

## Install details

What goes where in a copy install (a plugin install places the same files itself):

```
 ~/.claude/
 ├── skills/crossfire/
 │   ├── SKILL.md          needed: the procedure; its frontmatter makes /crossfire exist
 │   ├── references/       needed: contract, stances, gate, briefs and lenses
 │   ├── README.md         docs only, linked from SKILL.md
 │   └── PLAYBOOK.md       docs only, linked from SKILL.md
 └── agents/
     ├── crossfire-reviewer.md    recommended: read-only reviewer type
     └── crossfire-verifier.md    recommended: read-only verifier type
```

The examples and evals ship in the folder; they are for checking the skill, and a run never loads them.

Claude Code loads agent definitions from `~/.claude/agents/`, a project's `.claude/agents/` or a plugin, not from
inside a skill folder. Installed as a plugin, the two agent types are named `crossfire:crossfire-reviewer` and
`crossfire:crossfire-verifier`; the skill uses whichever form is installed. Without the agent definitions the skill
still runs, on general-purpose agents (see [What you see](#what-you-see-every-outcome-and-error)), but then the
read-only limit is in the prompt only. After editing either agent file in a copy install, copy it to
`~/.claude/agents/` again and start a new session.

The skill is manual only (`disable-model-invocation: true`), so it never starts by itself.

## Background

Why the design is what it is, and what it borrows. None of this is needed to use the skill.

### Evidence behind the design

| Design choice | Evidence | Source |
| --- | --- | --- |
| Lenses, not personas | Personas in system prompts did not improve accuracy on objective tasks | Zheng et al., [When "A Helpful Assistant" Is Not Really Helpful](https://arxiv.org/abs/2311.10054), 2023 |
| Reviewers draft blind; no debate | In debate, models often move from correct to incorrect answers to agree with peers | Wynn et al., [Talk Isn't Always Cheap](https://arxiv.org/abs/2509.05396), 2025 |
| Reviewers draft blind; no debate | Majority voting accounts for most of what debate gains | Choi et al., [Debate or Vote](https://arxiv.org/abs/2508.17536), 2025 |
| No scores; shuffle and anonymise what judges read | Swapping the order of answers flips model judges' rankings | Wang et al., [Large Language Models are not Fair Evaluators](https://arxiv.org/abs/2305.17926), 2023 |
| No scores; shuffle and anonymise what judges read | Model judges show position, verbosity and self-enhancement biases | Zheng et al., [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685), 2023 |
| Do not count models as independent votes | Errors correlate across 350+ models, even across providers | Kim et al., [Correlated Errors in Large Language Models](https://arxiv.org/abs/2506.07962), ICML 2025 |
| A panel is not a jury: a majority of models is not a majority of independent experts | Nine judges carried about two independent votes' worth of information | Kohli, [Nine Judges, Two Effective Votes](https://arxiv.org/abs/2605.29800), 2026 preprint |
| Mixing models helps only in some setups | Sampling the best single model beat mixing models on several benchmarks | Li et al., [Rethinking Mixture-of-Agents](https://arxiv.org/abs/2502.00674), 2025 |
| A good selector matters more than diverse writers | A diverse team with a judge selecting beat a single model (win rate 0.81), a same-model team scored near chance, and judge selection beat blending the answers | Maryanskyy et al., [When Agents Disagree](https://arxiv.org/abs/2603.20324), 2026 |
| Debate is not free accuracy | Multi-agent debate often fails to beat simpler baselines | Zhang et al., [Stop Overvaluing Multi-Agent Debate](https://arxiv.org/abs/2502.08788), 2025 |
| Verify against ground truth | Hybrid model and static-analysis techniques removed 94–98% of false alarms, with high recall, on an industrial dataset | Du et al., [Reducing False Positives in Static Bug Detection with LLMs](https://arxiv.org/abs/2601.18844), 2026 |
| An advocate against over-rejection | Model reviewers often judge correct code non-compliant | Jin and Chen, [Are LLMs Reliable Code Reviewers?](https://arxiv.org/abs/2603.00539), 2026 |
| Three rounds, then escalate | Most of the gain from repair loops comes in the first three or four iterations (crossfire escalates at round 3) | Kiecker et al., [Is Three the Magic Number?](https://arxiv.org/abs/2607.05197), 2026 |

The evidence on assigned stances, on pre-mortem prompting and on severity inflation is thin. The design uses them
sparingly and says so: two stance seats, a guardrail, and a verifier that can drop anything.

### Prior art

crossfire borrows ideas, not text, from three public projects, read at the commits named:

| Project | Took | Left |
| --- | --- | --- |
| [LLM Council](https://github.com/karpathy/llm-council) @ `92e1fcc` (no licence file) | independent first drafts in parallel; anonymous peer review; every raw output kept for inspection; one failed model does not sink the run | ranking whole answers by average position; one fixed A/B/C order for every judge; a final writer who sees model names but not which label is which |
| [PAL MCP consensus](https://github.com/BeehiveInnovations/pal-mcp-server) @ `7afc7c1` (Apache-2.0) | strict blinding of each model from the others and from the caller's notes; stance seats with a guardrail that a stance never bends the facts; a reply shape that starts with the verdict and has a length cap | calling models one at a time; run state shared between callers; a confidence of "high" reported whatever happened; 1–10 confidence scores |
| [metaswarm](https://github.com/dsifry/metaswarm) design-review gate @ `4bbb10a` (MIT) | blocking only when severity is high and the finding names what it protects; reviewers report and the orchestrator decides; escalation never approves; stopping to ask when fixes cause new blockers; overreach signals; evals with planted defects | six reviewers on the strongest model every round for up to ten rounds; full re-review each round; severities left undefined; a task-tracker dependency |

metaswarm's reviewer-rubric eval reports that when the orchestrator's prompt did not name the rubric, only 1 of 73
of its design reviewers opened the rubric file in one session
([the eval](https://github.com/dsifry/metaswarm/tree/4bbb10abd301b9ec9d63371e296049cbc6043baa/evals/reviewer-rubric)).
That is why crossfire pastes each seat's checklist into its brief. Anonymous peer review follows the LLM Council
project; aiming it at individual findings rather than at ranking whole answers is crossfire's change.

### Reviews of the skill itself

- **crossfire on its own README** (the self-review under [Test results](#test-results)): four verified blockers, all
  about how the README backed its own claims (the false-alarm example had never passed; rounds had never run; the
  examples exceeded the verifier caps; the cost section was empty). All four were fixed.
- **Two adversarial review rounds.** Three Sonnet reviewers, one each for the procedure, the eval code and the docs,
  then one Opus verifier who checked every fix. The first round found 5 Highs. The main ones were an identity leak
  through the run folder, a chair table that was never reconciled, rounds that missed edits to an uncommitted plan,
  an eval allowlist that could write outside its folder, and a round 2 that could be scored on round 1's summary.
  The verifier pass found 2 more Highs: a step-number slip, and README text installed into the eval repo. Every High
  and Medium was fixed. The reviewers' notes were working files and are
  not kept in the repository.

### Future: other model families

Reviewers from other model families are not supported. A model from another family (GPT through the Codex CLI,
Gemini through the Gemini CLI, or an API) could join a deep run as one extra reviewer seat on the same contract. It
would report like any seat; it would never verify, chair or gate. Turning it on would need:

- the run's summary naming the provider and how long it keeps what it is sent;
- a target and repo that you or your organisation allow sending to that provider;
- nothing secret or personal in the brief;
- an eval run showing it catches something the Claude-only panel misses, enough to justify the cost and the extra
  data exposure.

### Tests of the eval tools

29 tests pass (run on 2026-11-24, from the skill's evals folder): `python3 -I test_score.py` has 22 and
`python3 -I test_run.py` has 7. Each of 20 deliberate breaks of `score.py` and `run.py` made at least one fail.

<details>
<summary>The 20 deliberate breaks</summary>

Each break was made by hand in a temporary copy, the matching suite was run, and the copy was discarded, so any of
them can be repeated. The 11 breaks to `score.py`, and the round-2 and commit-date setup of `run.py`, were run on
2026-11-20. The runner has since changed (it now stages a plugin instead of copying files into the case's repo), so
its staging was re-checked on 2026-11-24 with 7 breaks (the "examples or answer keys staged" break was tried two
ways) and two added tests.

| File | Break | Caught |
| --- | --- | --- |
| score.py | phrases match anywhere, not at the start of a word | yes |
| score.py | phrases counted in every column, not only Finding and Protects | yes |
| score.py | a table without a separator row accepted | yes |
| score.py | the gate read from anywhere, not the Verdict section | yes |
| score.py | a second table in the section read as rows | yes |
| score.py | "yesterday" counted as blocking | yes |
| score.py | one phrase group enough to match a defect | yes |
| score.py | `must_block` ignored | yes |
| score.py | unreadable input crashes instead of exiting 2 | yes |
| score.py | a string `all_of` group accepted | yes |
| score.py | a summary with no Conditions section scored as empty | yes |
| run.py | commit dates not fixed (2026-11-20) | yes |
| run.py | the round-2 seed not recorded (2026-11-20) | yes |
| run.py | the README staged into the skill folder (2026-11-24) | yes |
| run.py | `examples/` staged, or `evals/` with `cases.json` staged (2026-11-24) | yes |
| run.py | the staging folder made inside the case's repo (2026-11-24) | yes |
| run.py | a `.claude/` folder written into the case's repo (2026-11-24) | yes |
| run.py | `--plugin-dir` dropped from the session command (2026-11-24) | yes |
| run.py | the plugin manifest's name changed (2026-11-24) | yes |
| run.py | the two agent files not staged (2026-11-24) | yes |

</details>
