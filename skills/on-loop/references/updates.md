# Reports: posture, the table and the full report

Read at tick step 12 and for "status" / "report". The table's rows, the seven-section report and the rules are in
[shared-with-away-loop.md](shared-with-away-loop.md); this file is what the on-loop adds. The user may be in the
same session, so the volume follows where they are. Posture comes from the time of the user's last message, written
into the state line from `date`; it never guesses presence from the clock.

```
 last message from the user      posture   a tick replies with
 under 15 minutes ago            PRESENT   one gauge line (defined just below)
 15 minutes to 2 hours ago       NEARBY    the status table, new information only
 over 2 hours ago                AWAY      the table, and the full report at each milestone
 an away mark ("I'm going to     AWAY      the same, until the user's next message after the
 sleep", "I'm stepping away")               one that set it clears the mark
 any time, on request            -         "status": the table · "report": the full report
                                            "review": the digest
 in every posture                -         also the full report every 2 hours
```

The gauge line is the smallest update and the first line of every larger one:

```text
on-loop · R3 Export v2: step 2 of 4 · decisions 5 pending (2 flagged) · PRs 3 open · day 2 of 7 · next beat ~14:37
```

Times in a report follow SKILL.md step 10. **New information only:** a tick report never restates an unchanged queue
item or limit. An item reappears only when it changes, or in the 2-hour full report. A load or disk figure over its
line is reported once when it starts, once after about 4 held beats in a row and once when it clears, with
"bookkeeping only" while it holds.

**Every tick posts at least one visible line**, starting with the gauge's `on-loop ·` prefix: what it did, or why it
held (load, disk, a limit, waiting on the user or CI), including a tick that yields (step 3): "on-loop · held: your
request is still running". **What a tick never does:** restate earlier ticks, post a table when nothing changed, open
a question panel, or print a diagram nobody asked for while the user is present (the 2-hour and milestone full reports count as asked for).

## The quiet report

The tick that enters the quiet beat shows the blocker table once, in every posture (even with the user present, in
place of that tick's gauge line): every roadmap item not done, the exact blocker, its allowed reason (tick.md step 13)
and the words that unblock it.

    on-loop · quiet: 3 items, none can move · decisions 4 pending · next beat ~15:17
    item | blocked by                              | reason     | unblocked by
    R5   | its design choice changes what is built | decision   | your answer to Q2 ("use option B")
    R7   | needs R6 merged and its release run     | merge-only | "merge 41", then the release
    R9   | free disk under 5 GiB (installs wait)   | limit      | free some disk, or "set the disk line to 3"

A bare "quiet tick, nothing new" is not enough. The table is posted again when a row changes, in each 2-hour full
report and on "status". Other quiet ticks post one line: "on-loop · quiet: 3 items waiting (table unchanged since
14:17) · next beat ~16:17". This is a change, so it is not the "table when nothing changed" a tick never posts.

The status table is the shared five rows plus **Limits** (only when something is within 20% of a bound: which, and
what happens at it). The full report is the shared seven sections with two additions: after "Since the last full
report", **Decisions** (a count by class and status, the flagged ones a line each); after "Time to completion",
**Drift and budget** (the drift table, every limit with its current value). It is required, in every posture: about
every 2 hours by elapsed time from `last full report` (a quiet stretch gets a short one that says nothing changed),
at each milestone (an item, a phase or the roadmap finished), and on request. Save it as `YYYY-MM-DD-HHMM-status.md`
in the project's progress folder, if the project keeps one, committed on the loop's log branch; a saved report is
never edited. Nothing is sent outside the session: no notification, no channel.

## "Is the loop on?" ("status", "is it running", "did it stop")

The answer is built from `CronList` and the state line, never from memory, and shows: the job id; the last beat and
the next beat; and why a tick may be waiting. Ticks fire only while the session is idle, so a busy turn, an open
question panel or a permission panel makes a due tick wait and run right after; a tick that waited is late, not
lost. Reports stay in the chat.
