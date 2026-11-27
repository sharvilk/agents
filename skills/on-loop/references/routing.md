# Routing and hand-offs

The session's state decides who answers a phrase, not the words. No ordinary message stops the
loop: "stop the loop" ends it, "pause the loop" pauses it, and anything else, even a message with the word "stop" in
it, is answered first while the loop carries on. The full table, with every skill's column, is in this skill's
README ("Which skill answers which phrase"); this is the on-loop's side.

Read across: the phrase, then what happens in each session state.

| Phrase | Nothing armed | away-loop armed | on-loop ARMED | on-loop PAUSED | on-loop ENDED, entries pending |
| --- | --- | --- | --- | --- | --- |
| "I'm back", "good morning", "back online" | checkpoint resumes, if a resume block exists | away-loop stops and summarises | with a resume block, checkpoint resumes and re-arms only a loop it paused (`reason checkpoint`); with none, a short status and the review digest offer | with a resume block, checkpoint resumes and re-arms a `reason checkpoint` pause, nothing for `reason user`; with none, not answered by the loop | not answered by the loop |
| "continue", "carry on", "keep going" | checkpoint resumes, if a resume block exists | (already working) | with a resume block, as above; with none, the on-loop says it is already working, unless the last tick was quiet: then it re-runs the blocker table and acts | with a resume block, as above; with none, not on its `Answers:` line | not answered by the loop |
| "resume the loop" | nothing to resume | (already working) | already working, unless the last tick was quiet: then it re-runs the blocker table and acts | the on-loop resumes (charter clock kept) | nothing to resume |
| a bare "resume", with a "Resume here" block | checkpoint resumes | (already working) | checkpoint resumes | checkpoint re-arms a `reason checkpoint` pause only, nothing for `reason user` | not answered by the loop |
| a bare "resume", no resume block | nothing to resume | (already working) | the on-loop: already working, unless the last tick was quiet: then it re-runs the blocker table and acts | the on-loop resumes (charter clock kept) | nothing to resume |
| "I'm going to sleep", "keep working while I'm away", "proceed while I sleep", "work overnight", "I'm stepping away" | away-loop arms | (already armed) | the on-loop stays armed and sets its away mark, for these or any other words for leaving; its posture becomes AWAY and it says so in one line | away-loop does not arm: one line says the on-loop owns the session and how to resume or stop it | away-loop arms |
| "review", "keep/veto/change <ids>" | no skill | no skill | the on-loop | the on-loop | the on-loop |
| every other checkpoint trigger ("checkpoint", "save progress", "I'm going to restart", "before I restart", "before I quit", "stop everything safely", "is it safe to restart") | checkpoint | checkpoint | checkpoint | checkpoint | checkpoint |
| "stop the loop", "pause the loop" | nothing to stop | away-loop answers | stop / pause | stop (pause: already paused) | nothing to stop |
| other "stop ..." | no skill | away-loop stops | not a stop: answered | not a stop: answered | no skill |
| "wrap up", "close out", "close this initiative", "clean up old todo lists" | todo-sync closes this session's part | todo-sync, after away-loop has stopped | todo-sync closes its part; it never deletes the list or the loop's blocks; the loop keeps running | same: the list is shown and skipped, never deleted | todo-sync closes it out; the pending entries stay in the ledger in the repo |
| a restart or a quit | checkpoint | checkpoint deletes the loop's jobs first and resumes them after | checkpoint deletes the loop's job first (marker PAUSED, `reason checkpoint`) and resumes it after | nothing to delete; a `reason user` pause stays paused | checkpoint |
| after a compaction | todo-sync recovers the list first | away-loop re-reads its plan | the on-loop skill is invoked again and re-reads its marker and charter | same | the on-loop is invoked for a pending verdict |

Every checkpoint trigger stays checkpoint's in every state. PAUSED and ENDED: only the phrases on the marker's `Answers:` line (ENDED: "review" and verdicts while entries are pending). away-loop never arms while any `## Loop state:` heading is ARMED or PAUSED.

## Other skills

- **todo-sync (required).** Holds the marker, charter, state, roadmap view, decisions index and "Waiting for you".
  After a compaction, todo-sync's recovery first, then the skill again. Its close-out and its prune-and-recovery
  rules leave every block the marker's `Owns:` line names whole.
- **checkpoint (optional).** Restart or quit: the job is deleted first (no tick fires mid-checkpoint) and the marker
  becomes `PAUSED — on-loop — charter valid until <date> — reason checkpoint`; the resume block's first item is
  "resume the loop (owner on-loop, charter valid until <date>)". A break (no restart, no quit) leaves the job and
  marker alone. On "continue" with the resume block, checkpoint invokes this skill and runs its "resume the loop"
  step, but only for a marker it paused itself (`reason checkpoint`): the schedule is re-armed as in SKILL.md
  section 5, the claim is updated, `Answers:` is rewritten by this skill, and the charter's clock is **not** reset.
  A `reason user` pause gets no re-arm item.
- **away-loop (separate).** One loop per session. On-loop armed and "I'm going to sleep", in any wording: it stays the
  on-loop with an away mark, and says so in one line; away-loop hands every such phrase to it. away-loop armed and
  "start the on-loop": away-loop stops and summarises first, then the gates.
- **crossfire (manual).** The loop cannot run it. A design-heavy class C item is queued with the exact words: "run
  /crossfire <path>".
