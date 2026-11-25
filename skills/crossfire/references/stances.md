# Stance seats

Two seats in a crossfire run take a stance instead of a lens. The orchestrator pastes the matching section, and the
guardrail, into that seat's brief.

## Table of contents

- [The guardrail](#the-guardrail)
- [Advocate](#advocate)
- [Pre-mortem](#pre-mortem)
- [Why these two, and why not more](#why-these-two-and-why-not-more)

## The guardrail

Pasted into both stance briefs, word for word:

> Your stance decides what you look for first. It never decides what is true. If the plan has a serious flaw, say
> so plainly, even as its advocate. If a part of the plan is sound, say so plainly, even in the pre-mortem. A
> stance that bends the facts makes the whole run worse than no run.

## Advocate

Seated at standard and deep depth. In whether-mode it argues for the option the frame marks as leading (the owner's stated leaning), or for the
change over "keep things as they are" when no option is marked.

Brief text:

> You are the advocate. Make the strongest honest case for the plan as written.
>
> 1. Name what is right and must not change: the decisions a reviewer might be tempted to undo, and why undoing
>    them would be worse. List them in a "Keep:" section after your findings, one line each with its evidence.
>    They go to the chair as a list, not as findings.
> 2. Name what must be true for the plan to work: the assumptions it rests on. Check each one you can against the
>    repo. An assumption you find false is a real finding, at its real severity.
> 3. Later you will see the other reviewers' findings. Your job there is to dispute the ones that are wrong or
>    overstated, with evidence, and to agree with the ones that hold.

The advocate exists because reviewers that are asked to find problems tend to find problems, including in sound
plans. It is the run's counterweight, not its cheerleader.

## Pre-mortem

Seated at every depth.

Brief text:

> It is six months after this plan shipped exactly as written, and it failed. Users were hurt, data went wrong,
> or the team had to roll it back. Write down the most likely ways that happened, most likely first.
>
> For each one: the chain of events from a normal day to the failure, the line of the plan (or the missing line)
> that let it happen, and the evidence in the repo that makes the chain credible. A chain you cannot tie to the
> plan or the repo is a guess; leave it out or mark it `needs data:`.

The pre-mortem runs on `opus`, because it is the seat most likely to find what no checklist names.

## Why these two, and why not more

The evidence on assigned stances is thin and points both ways: a strongly critical stance can sharpen a
reviewer's judgement, and forcing an agent to defend a stance can make it rigid. So the run seats exactly two
stances, gives each a job a lens does not do (protect what is right; imagine the failure), and holds both to the
guardrail. Every other seat is a lens: a checklist, not a persona.
