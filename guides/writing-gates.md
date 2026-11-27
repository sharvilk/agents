# Writing your own gates

A gate is a check that runs by itself and fails loudly when a rule is broken: a test, a lint rule, a script in CI, a
pre-commit hook. This guide is for you if you build software, alone or with agents, and you keep fixing the same kind
of mistake by hand. It shows when to write a gate, how to write one you can trust, and how to keep it honest after
the day you wrote it.

## Table of contents

- [Why a gate beats a rule you remember](#why-a-gate-beats-a-rule-you-remember)
- [1. Treat a green CI as evidence about where it ran](#1-treat-a-green-ci-as-evidence-about-where-it-ran)
- [2. Write the gate when a mistake happens the second time](#2-write-the-gate-when-a-mistake-happens-the-second-time)
- [3. Write the detector before the fix](#3-write-the-detector-before-the-fix)
- [4. Test the gate in both directions](#4-test-the-gate-in-both-directions)
- [5. Rename a collision, don't loosen the gate](#5-rename-a-collision-dont-loosen-the-gate)
- [6. Check that the gate reads what it claims to read](#6-check-that-the-gate-reads-what-it-claims-to-read)
- [7. Test against the real tool, not a hand-made copy](#7-test-against-the-real-tool-not-a-hand-made-copy)
- [8. Set the stop rule before the first review round](#8-set-the-stop-rule-before-the-first-review-round)
- [9. Fix a repeated claim at its source](#9-fix-a-repeated-claim-at-its-source)
- [Checklist](#checklist)

## Why a gate beats a rule you remember

A rule nobody encoded is a habit. Habits regress silently, between the person who learned the lesson and the person
who arrives next. That person can be you in six months, or an agent that never saw the conversation.

```
 a rule in someone's head      a rule in a document        a rule in a gate
 ------------------------      --------------------        ----------------
 holds until they forget       holds until nobody reads    holds until someone
 or leave                      the document                deletes the check
                                                           (and the deletion shows in review)
```

## 1. Treat a green CI as evidence about where it ran

Green says the checks passed in the environment they ran in. Make sure that environment is the one that matters.

- **Run the gate on the platform you ship to.** A convenience runner (your own machine, another OS, another CPU) can
  hide defects for a project's whole life. Anything touching files, containers, file ownership, paths or process
  limits is a candidate. If the gate runs somewhere else too, still run it on the real target, and never read a pass
  elsewhere as a pass there.
- **Tie a deferral to its condition.** "Turn on the expensive job when it is free" is fine. Leaving it off after it
  became free is not. Name the moment it flips and act on it then.
- **Don't let a third party's throttle fail your gate.** Public registries limit the shared addresses CI runs from.
  A limit per second clears in moments: serialise and back off. A quota per day cannot be waited out: use another
  provider or authenticate. Absorb throttling, and still fail loudly when an artifact is truly missing.

> What happened to me: a library's tests ran on a self-hosted macOS runner for the whole pre-launch period and were
> always green. The first run on a hosted Linux runner failed on two latent defects. One was a container writing
> root-owned files into a mounted folder that the host user then could not delete. That cannot happen on a Mac, where the container tool
> remaps ownership, so no amount of local running would have found it.

## 2. Write the gate when a mistake happens the second time

The first time a thing goes wrong, fix it. The second time, stop being careful and write the check. A rule that has
failed twice will fail a third time, and the check costs less than the next cleanup.

> What happened to me: an agent I was running cleaned internal-document references out of a project's published code
> comments by hand. A year later 271 of them were back, 71 of them in published source.

## 3. Write the detector before the fix

When a defect has more than a handful of instances, write the gate first and fix second. A gate is a better
inventory than a search:

```
 sweep first, gate second                 gate first, fix second
 ------------------------                 ----------------------
 you search the files you thought of      the gate reads every file
 you declare it clean                     it lists every instance
 the gate, written later, finds more      you fix until it is green
 nobody knows when the next one appears   it keeps running after you stop
```

Writing it first forces you to define the pattern precisely while that is cheap. "Am I done?" stops being a
judgement and becomes a green check.

> What happened to me: in that same project an agent I was running swept first and wrote the gate second. On its
> first run, the gate failed on six files the sweep had just called clean. Every one used a hyphenated spelling the
> hand-written search did not cover. Three of the six were in published source.

You can ask an agent to work this way. A prompt that works: "Before you fix these, write the detector that finds
every instance. Then verify it both ways: mutate in a defect and watch it fail, then confirm the legitimate
look-alikes don't trip it. Fix only once the gate is green in both directions."

## 4. Test the gate in both directions

Most people test only half. A gate has two jobs, and each needs a test.

| Direction | You do this | You expect |
| --- | --- | --- |
| It catches | Put in the defect it exists for | It fails, and the message points at the defect |
| It leaves honest work alone | Run it on legitimate code that looks like the defect | It passes |

A gate that fires on honest work is worse than none. It trains everyone to route around it, and whoever is in a
hurry will loosen it.

When you test by editing real files:

1. **Back up each file just before each edit**, and restore from that backup. A backup folder kept across runs, with
   "copy only if missing", restores a stale file and silently reverts later edits.
2. After each restore, compare the file with its backup (`cmp`), and run `git status`.
3. Commit before each batch of mutations, so git can restore whatever a backup misses.
4. Write out the exact command, with its environment variables.

> What happened to me: an agent I was running reused one backup folder across mutation runs, and a restore undid
> three real edits of mine. In another run, a command that left out its mode variable started the full benchmark
> instead of the quick check.

## 5. Rename a collision, don't loosen the gate

When an honest case trips the gate, the easy move is to widen the pattern until it passes. Don't. A pattern widened
for one legitimate case stops catching the illegitimate ones.

- Change the local name instead.
- If an exemption is truly needed, make it an explicit list of named files with the reason written down.
- Never write a general escape ("anything in backticks", "anything in a comment"). The real defect satisfies it too.

## 6. Check that the gate reads what it claims to read

A checker that says it covers a surface it does not read is worse than no checker. It removes the suspicion that
would have found the gap.

- Assert the scope: the file list is not empty, it contains the surfaces that have gone wrong before, and it has not
  shrunk after a rename.
- When the gate describes itself in a document or an instruction, change that text in the same change that changes
  the gate's scope.
- Where a real engine can read the input (a browser, the real parser, the real tool), compare its reading with your
  static reader's and fail on any difference. Keep the static reader as the fast path. This ends a whole class of
  "the parser reads it differently" bugs, where patching the parser one case at a time does not.
- Some questions have no static answer. Whether text on a web page is visible depends on the whole style cascade,
  which no static reader resolves. Refuse the styling features the page does not use, and check what remains by
  rendering the page and comparing pixels.

## 7. Test against the real tool, not a hand-made copy

A fake proves your logic. It does not prove the environment.

> What happened to me: a release audit parsed the package manager's dependency paths in the format of an older
> version. An upgrade changed the format, and every advisory then parsed as "reaches no published package". Three real
> high-severity findings passed with every test green, including the both-direction checks, because the test inputs
> were written by hand. In another project a CI step assumed a tool was installed because a sibling script installs it.
> The CI image had none.

- Capture the tool's real output at the version CI runs, store it beside the test, and record the version. Cross-check
  the fixture against the tool's own totals.
- On a major upgrade, find every script that parses that tool's output and capture its fixtures again.
- Confirm the tool exists in the CI image. Run the real call once in the pull request's own pipeline.
- Fail closed: output the gate cannot classify is a failure, not a pass.

## 8. Set the stop rule before the first review round

A gate that checks code by its syntax can chase "airtight" for ever. Each round of fixes closes the last round's
bypasses and opens new ones. Decide before round one:

| Class | Meaning | What you do |
| --- | --- | --- |
| High | A defect written the way a developer plausibly would slips through, or realistic legitimate code fails | Fix it |
| Out of scope | Deliberate evasion, such as escaped names or computed keys | Leave it to types, runtime checks and review |

Count false positives as heavily as bypasses, and write the known limits into the gate itself.

> What happened to me: three rounds of verify-and-fix on a static-analysis gate each closed the previous bypasses
> and opened new ones. Tightening the rule traded missed cases for wrong failures: honest code was refused. My
> mistake was asking a syntax check for the guarantees only meaning can give.

You can use [crossfire](../skills/crossfire/README.md) to put an independent, read-only review on a gate before you
rely on it. Your own tests share your blind spots.

## 9. Fix a repeated claim at its source

When the same wrong sentence appears in many places, one of them is upstream: a list of invariants, an instruction
file, a spec everyone reads first. Correct that one and re-derive the rest. Fixing the copies and leaving the source
leaves a path for the error to come back.

## Checklist

- [ ] Run your gate on the platform you ship to, or know what its green does not prove.
- [ ] If this is the second time it has gone wrong, or there are many instances, write a gate, not a sweep.
- [ ] Write the detector before the fix, and make it read every file in scope.
- [ ] Mutate in the defect and watch it fail.
- [ ] Run it on honest look-alikes and watch it pass.
- [ ] Back up each mutated file just before each edit, and restore from that backup.
- [ ] Make any exemption a named list with a reason, not a general escape.
- [ ] Make the gate assert its own scope, and move any text describing it with it.
- [ ] Take fixtures from the real tool at the CI version, and make unclassifiable output fail.
- [ ] Write down what counts as High and what is out of scope.
