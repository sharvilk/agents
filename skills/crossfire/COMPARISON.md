# How crossfire compares to what's out there

> A design review that runs before you build: independent reviewers, every blocker reproduced by a verifier,
> and a decision with a checklist you re-run, not a long list of AI comments.

This page puts crossfire next to the tools people already use for AI review: where each one sits in the work, how
each one is built, what they share, where crossfire differs, and where it is weaker. The examples come from real
crossfire runs, described in [examples/](examples/README.md). The other tools are described from their own source
or documentation, read at the commits named under [Sources](#sources).

## Table of contents

- [Where each tool sits](#where-each-tool-sits)
- [Four shapes of AI review](#four-shapes-of-ai-review)
- [Side by side](#side-by-side)
- [What is not unique, and what is](#what-is-not-unique-and-what-is)
- [The tools, one by one](#the-tools-one-by-one)
- [Examples from real runs](#examples-from-real-runs)
- [Where crossfire is weaker](#where-crossfire-is-weaker)
- [Using them together](#using-them-together)
- [Who it is for](#who-it-is-for)
- [Sources](#sources)

## Where each tool sits

```
 idea ──▶ PLAN / DESIGN ──────────▶ CODE ──────▶ PULL REQUEST ──────────────▶ DEPLOY
              ▲                                       ▲
         crossfire                          Anthropic's code-review plugin
         metaswarm's design-review gate     Anthropic's pr-review-toolkit
         (inside its larger framework)      pull-request review bots

 any question, not tied to a stage:  PAL's consensus tool (several models, for/against stances)
                                     LLM Council (several models rank each other's answers)
```

Most AI review happens at the pull request, after the code exists. crossfire works one stage earlier, on the plan,
when a design mistake costs least to fix. Of the tools here, only metaswarm's design-review gate works at the same
stage, and it comes as part of a larger framework.

## Four shapes of AI review

```
 A  ONE REVIEWER      plan ──▶ [one agent] ──▶ a list of comments
                      (often the agent that wrote the plan: the same blind spots)

 B  CONSENSUS         question ──▶ [model 1] [model 2] [model 3] ──▶ blend ──▶ one answer
                      (PAL, LLM Council: diverse opinions; nothing has to be proven)

 C  DIFF REVIEW       diff ──▶ [narrow reviewers] ──▶ [check each finding] ──▶ pull-request comments
    WITH A CHECK      (Anthropic's code-review: checked findings, but after the code exists,
                      ending in comments)

 D  CROSSFIRE         plan ──▶ frame ──▶ [lenses + advocate + pre-mortem, blind]
                           ──▶ anonymous cross-examination ──▶ [a verifier per blocker]
                           ──▶ chair ──▶ FIXED GATE ──▶ conditions
                                                              │
                                  next round re-checks each by id ◀┘
```

Each shape answers a different question:
- **A** asks "what does one reviewer think?"
- **B** asks "what do several models think, blended?"
- **C** asks "which problems in this diff are real?"
- **D** asks "should this plan be built as written, and what exactly must change first?"

## Side by side

✓ = yes, ~ = partly, ✗ = no.

| | crossfire | metaswarm design gate | Anthropic code-review | PAL consensus | LLM Council | one agent |
| --- | --- | --- | --- | --- | --- | --- |
| Reviews the plan before code | ✓ | ✓ | ✗ (pull requests) | ~ (any proposal text) | ~ (any question) | ✓ |
| Findings must cite evidence (file:line, a command, a count) | ✓ | ✓ | ✓ (links lines in pull-request comments) | ~ (only files it is handed) | ✗ | ✗ |
| A separate agent tries to refute each blocking finding | ✓ | ✗ | ✓ (validates issues before reporting) | ✗ | ✗ | ✗ |
| Reviewers draft blind, then cross-examine anonymously | ✓ | ~ (blind, no cross-examination) | ~ (parallel, no cross-examination) | ~ (blind) | ✓ (ranks whole answers) | ✗ |
| Ends in a decision made by a fixed rule | ✓ (five outcomes) | ✓ | ✗ (comments) | ✗ (a summary) | ✗ (an answer) | ✗ |
| Stops and asks when a fact is missing | ✓ (STOP) | ✓ (its "clarify" stop) | ✗ | ✗ (a model can ask for files; the tool does not act on it) | ✗ | ✗ |
| Later rounds re-check conditions by id | ✓ | ~ (a fresh full review each round, tracking recurring themes) | ✗ | ✗ | ✗ | ✗ |
| Panel sized to the risk | ✓ (up to 3, 5 or 7 seats) | ~ (runs only on project-sized designs; then six reviewers, Opus by default, every round) | ~ (cheap checks first) | ~ (you choose the models) | ✗ (fixed list) | — |
| Records its own first view, to show what the panel changed | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Ships end-to-end evals with answer keys and measured cost | ✓ | ~ (tests whether reviewers apply their rubric) | ✗ | ✗ | ✗ | ✗ |
| Several model families | ✗ (Claude only) | ~ (the framework can use other models' CLIs; not shown for this gate) | ✗ | ✓ | ✓ | ✗ |
| What it takes to set up | install the plugin from its marketplace, or copy the files | the metaswarm framework (it recommends its own task tracker) | a plugin | an MCP server and provider API keys | a local web app and an API key | nothing |

The table compares the review step only. Several of these tools do far more around it: metaswarm is a whole
development workflow, and PAL is a toolbox of which consensus is one tool.

## What is not unique, and what is

No single feature in that table is unique to crossfire:
- Anthropic's code-review plugin also has a separate agent check each bug finding, and drops what it cannot
  confirm. It does so on pull requests, after the code exists.
- metaswarm's design-review gate also reviews designs before code, blocks only on findings that name what they
  protect, and stops to ask when it needs the owner. For project-sized work it runs six reviewers (on the strongest
  model by default) every round, with no separate verifier, inside its own framework.
- LLM Council also anonymises reviewers before they judge each other, but ranks whole answers rather than testing
  individual findings.

What is new is the combination, aimed at one moment:

```
   BEFORE CODE  +  EVIDENCE A VERIFIER REPRODUCES  +  A DECISION A RULE MAKES
        +  A LOOP THAT CLOSES BY ID  +  A PANEL SIZED TO THE RISK
        +  A RECORD OF WHAT THE PANEL CHANGED  +  EVALS YOU CAN RE-RUN
```

## The tools, one by one

### LLM Council

A small local web app. A question goes to several models at once through OpenRouter. Each model then ranks all the
answers, its own included, relabelled "Response A", "Response B" and so on, so no judge is told whose is whose. A
chairman model writes the final answer from all of it.

- **Shares with crossfire:** independent first drafts, and anonymous peer review.
- **Differs:**
  - It answers questions; it does not open a repository or cite files.
  - Every judge sees the answers in the same fixed order, and ranks its own answer too.
  - The chairman is shown the model names, with the answers in the same order as their labels, but is never told
    which label belongs to which model.
  - It ends in one answer, not a decision with conditions.
- **Status:** its author calls it a weekend hack and does not plan to maintain it. It has no licence.

### PAL's consensus tool

One tool in the PAL MCP server. The calling agent writes a proposal, then the tool sends it to several models, one at
a time. Each model can be told to argue for, against, or neutral, with a guardrail that a stance must not bend the
facts. Each model sees only the original proposal, never another model's answer or the caller's notes. The calling
agent writes the final synthesis.

- **Shares with crossfire:** strict blinding between reviewers; stance seats with a guardrail; a reply that starts
  with a verdict and has a length limit.
- **Differs:**
  - Real model diversity: models from different families.
  - Each reply follows a set shape (a verdict, an analysis, a 1–10 confidence and takeaways), which the tool does not
    check, and it reports a confidence of "high" however the run went, even when a model call failed.
  - It has no verification step and no gate: the calling agent decides what agreement means.
  - Models see only the files and images the caller attaches. The prompt lets a model ask for more files, but the
    tool does not act on that request.
- **Licence:** Apache-2.0. It needs API keys for each model provider.

### metaswarm's design-review gate

Part of metaswarm, a larger development framework. When a project-sized design document is committed, six
reviewers run in parallel, on the strongest model by default: product, architect, designer, security, UX and
CTO. Smaller work skips the gate. A finding
blocks only when it is critical or major and names what it protects. An ordered rule decides each round: pass,
stop and ask the owner, escalate, or fix and review again, up to ten rounds. Escalation never approves.

- **Shares with crossfire:** review before code; a blocking rule tied to what a finding protects; stopping to ask
  the owner; escalation that never approves; evals with planted defects.
- **Differs:**
  - No separate agent tries to refute findings; reviewers report and the orchestrator decides.
  - The same six reviewers run every round, and each round is a full fresh review rather than a re-check of open
    items.
  - It defines which severities block (critical or major, naming what they protect), but not what separates critical
    from major, or minor from nit.
  - Its evals test whether a reviewer applies its rubric, not the whole gate end to end.
  - It is built into metaswarm's workflow, which recommends the framework's own task tracker. The framework can also
    call other models' command-line tools; this gate's reviewers are not shown using them.
- **Licence:** MIT.

### Anthropic's code-review plugin

A `/code-review` command for pull requests:
1. It skips closed, draft, trivial or already-reviewed pull requests.
2. It gathers the repository's `CLAUDE.md` files and summarises the change.
3. Four agents review in parallel: two check the change against `CLAUDE.md`, and two on the strongest model hunt for
   bugs.
4. Issues then go to separate subagents to be validated, and issues that are not validated are dropped. (The command
   names the bug reviewers' issues and gives a `CLAUDE.md` example too. Its README also describes scoring each
   issue from 0 to 100 and keeping those of 80 and above.)
5. It reports a short summary in the terminal, or posts inline pull-request comments that link to the exact lines.

- **Shares with crossfire:** parallel narrow reviewers, a check on each finding before it is reported, and evidence
  linked to code.
- **Differs:** it reviews a diff after the code is written, and ends in comments, not a decision or a loop.

### Anthropic's pr-review-toolkit

Six specialist agents for pull requests, used one at a time or together: code comments, tests, silent failures, type
design, general code review and simplification. Its `/review-pr` command gathers their results into critical,
important and suggested items with an action plan. It is a set of focused reviewers for code that exists, with no
gate and no separate verification step.

### Pull-request review bots

Hosted services that comment on pull requests. They work on diffs, after the code is written, and post findings as
review comments.

### Asking one agent to review

The default: "review my plan". One context, one point of view, often the same agent that wrote the plan. The answer
is a list of comments, with no evidence required, no check on each claim, and no decision.

## Examples from real runs

The first three come from crossfire runs on small made-up projects, each described in full in
[examples/](examples/README.md); the fourth puts their figures side by side.

### 1. Evidence, and a verifier who also cuts

[Password reset](examples/password-reset/README.md), deep depth: a plan for "forgot your password", in a repo
whose access log records full URLs.

```
 six of seven reviewers, each on its own:  "the reset token lands in the access log"
        │
 verifier (Opus) reproduces it: plan:24 puts the token in the URL ─┐
                                logging.js:7 logs req.originalUrl ─┴─▶ VERIFIED critical
        │
 C1 | critical | blocks | check: a test sends GET /reset?token=X, asserts X is not in the log
```

The verifier also cuts, and here it cut too far. Plaintext token storage was one of the planted defects and should
have blocked. A reliability reviewer raised it, and the verifier rated it minor, since a database leak is not normal
use, so it became a follow-up. crossfire's own record counts this as the run's one miss. The security lens now
treats stored credentials as blocking; that change has not been tested yet. What the design guarantees is that
every blocking claim is either reproduced or loses its block, with the reason written down, so a wrong call like
this one is visible and can be corrected.

### 2. It stops instead of guessing

[Help page copy](examples/help-page-copy/README.md), quick depth: a two-line change whose plan said the banner
should be teal "as the other help pages already do".

```
 round 1   plan: "make the banner teal, as the other help pages already do"
           repo: no file reads the banner setting, no palette, no other help pages
           ──▶ STOP: "What reads helpBannerColor? What is the brand teal?"
                         │
 owner     adds the banner code, the palette and the answers to the plan
                         │
 round 2   ──▶ C1 "fixed in round 2" (banner.js:7, palette.json:3) ──▶ PASS
```

crossfire turned the gap into two questions, and the next round closed them by id. A reviewer that does not stop
to ask would probably have trusted the plan's claim, but no single-reviewer run was made to compare.

### 3. It changes the decision, and shows that it did

[Report scheduling](examples/report-scheduling/README.md), a whether-decision: should a nightly report move from
cron to a job queue, and how?

```
 first view, told before any reviewer started: "lean to option 3: one job per workspace"
 panel, with evidence:                         "option 2: a redelivered fan-out job re-queues every
                                                workspace, so option 3 needs the same sent-record
                                                and costs more"

 option 2 as written, one night:
 02:00  worker A runs the report ─────────────────────── ~02:12
 02:05            timeout → worker B runs it again ───────────▶   admins get 2–3 copies
 02:10                      timeout → worker C runs it again ──▶   every night
```

Because the orchestrator writes its view down before any reviewer starts, the summary can say what the panel
changed. Here the panel changed the recommendation, with reasons, instead of restating the first view.

### 4. Sized to the risk

```
 copy change   QUICK   pre-mortem + 2 lenses, no cross-examination  4–9 agent calls  $3–4   8–10 min
 auth change   DEEP    7 reviewers, every one cross-examines        31 agent calls   $16.55 33 min
```

The deep run used 16 verifiers; the skill now caps them at 8 at deep depth, and a deep run under that cap has not
been measured.
Each figure is one sample per case, not an average.

## Where crossfire is weaker

- **One model family.** Every agent is a Claude model, and model errors correlate. PAL and LLM Council draw on
  several families.
- **Cost and time.** $3–17 and 8–33 minutes a run in the recorded examples, 86–97% of it on Opus (86%, 96% and 95% in the
  published records; the rest is from the run files, which are not published). A one-agent review is expected to cost much less, though that was not measured here.
- **Not for line-level code review.** Once code exists, a diff reviewer such as Anthropic's code-review plugin is the
  right tool.
- **Thin evidence so far.** Three made-up cases and a self-review, one sample per case, all on earlier versions of
  the skill.
- **Claude Code only.** It runs as a Claude Code skill, installed as a plugin or copied.
- **Prompt-level read-only for Bash.** Its agents have no file-editing tools, but their Bash use is limited by
  instruction, not by the tool list.

## Using them together

```
 plan ──▶ crossfire ──▶ build ──▶ pull request ──▶ Anthropic's code-review ──▶ merge
           (should we build this,                    / pr-review-toolkit
            and what must change first?)             (is this diff correct?)

 a decision where model diversity matters more than repository evidence
   ──▶ PAL consensus, as a second opinion
```

crossfire does not replace a diff reviewer. It moves the expensive mistakes earlier, so the diff reviewer sees fewer
of them.

## Who it is for

Anyone who lets Claude, or another agent, write plans, and wants that plan checked before it turns into code. The
clearest use is to run `/crossfire` on your agent's plan before it starts building.

## Sources

Read at these commits:

- [karpathy/llm-council @ 92e1fcc](https://github.com/karpathy/llm-council/tree/92e1fccb1bdcf1bab7221aa9ed90f9dc72529131):
  `backend/council.py`, `backend/openrouter.py`, `README.md`
- [BeehiveInnovations/pal-mcp-server @ 7afc7c1](https://github.com/BeehiveInnovations/pal-mcp-server/tree/7afc7c1cc96e23992c8f105f960132c657883bb1):
  `tools/consensus.py`, `systemprompts/consensus_prompt.py`, `docs/tools/consensus.md`
- [dsifry/metaswarm @ 4bbb10a](https://github.com/dsifry/metaswarm/tree/4bbb10abd301b9ec9d63371e296049cbc6043baa):
  `skills/design-review-gate/`, `lib/review-rule.js`, `evals/reviewer-rubric/`
- [anthropics/claude-plugins-official @ 1b9a8c7](https://github.com/anthropics/claude-plugins-official/tree/1b9a8c736db2330ce1812bcc41878a6e2e288e24/plugins):
  `plugins/code-review/` (the command and its README) and `plugins/pr-review-toolkit/`

crossfire's own figures come from the runs in [examples/](examples/README.md) and the results in the
[README](README.md#test-results).
