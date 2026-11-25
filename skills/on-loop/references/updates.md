# Reports: posture, the table and the full report

Read at tick step 12 and for "status" / "report". The table's rows, the seven-section report and the rules are in
[shared-with-away-loop.md](shared-with-away-loop.md); this file is what the on-loop adds. The user may be in the
same session, so the volume follows where they are. Posture comes from the time of the user's last message, written
into the state line from `date`; it never guesses presence from the clock.

```
 last message from the user      posture   a tick replies with
 under 15 minutes ago            PRESENT   one gauge line
 15 minutes to 2 hours ago       NEARBY    the status table, new information only
 over 2 hours ago                AWAY      the table; the full report every 2 hours and at each milestone
 an away mark ("I'm going to     AWAY      the same, until the user's next message after the
 sleep", "I'm stepping away")               one that set it clears the mark
 any time, on request            -         "status": the table · "report": the full report · "review": the digest
```

The gauge line is the smallest update and the first line of every larger one:

```text
on-loop · R3 Export v2: step 2 of 4 · decisions 5 pending (2 flagged) · PRs 3 open · day 2 of 7 · next beat ~14:37
```

Every time in a report (its heading, the state line, "next beat") comes from `date` run in the command that writes
it; never typed or estimated. **New information only:** a tick report never restates an unchanged queue item or
limit. An item reappears only when it changes, or in the 2-hour full report. A load or disk figure over its line is
reported once when it starts and once when it clears, with "bookkeeping only" while it holds.

A tick with nothing new says so in one line. **What a tick never does:** restate earlier ticks, post a table when
nothing changed, open a question panel, or print a diagram nobody asked for while the user is present. A tick that
yields (step 3) says nothing.

The status table is the shared five rows plus **Limits** (only when something is within 20% of a bound: which, and
what happens at it). The full report is the shared seven sections with two additions: after "Since the last full
report", **Decisions** (a count by class and status, the flagged ones a line each); after "Time to completion",
**Drift and budget** (the drift table, every limit with its current value). It is given about every 2 hours by
elapsed time from `last full report` while the posture is AWAY, at each milestone (an item, a phase or the roadmap
finished), and on request. Save it as `YYYY-MM-DD-HHMM-status.md` in the project's progress folder, if the project
keeps one, committed on the loop's log branch; a saved report is never edited. Nothing is sent outside the
session: no notification, no channel.
