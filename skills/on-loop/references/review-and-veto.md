# The review, verdicts and veto

Read when the user asks for a review, gives a verdict, or at tick step 5.

Triggers: "review" and "what did you decide" in any state (ARMED, PAUSED, or ENDED) while entries are pending; "I'm
back" (with the marker ARMED and no resume block), which gets a short status and the offer, never the digest unasked;
or the user's first message after 2 hours or more (then only the offer: "7 to review, 2 flagged. Say 'review' when you want
them."). The order is fixed: the digest first, and verdicts only after the user says they have read it.

1. **Re-check the sources:** PR and CI state now, not as of the entry. Rebuild the digest from the ledger, never from
   the conversation.
2. **The digest, in chat:** flagged (B) entries first, roots before the entries built on them, each in full:
   decision, diagram, example, undo. Then minor (A) as one table, a line each. Then waiting for you (C), each with
   its options and the words that unblock it.
3. **The user reads. Nothing is asked in the same step.**
4. **Verdicts** when the user says they have read it: free text ("keep 14 15, veto 16, change 17: sort by date") or
   question panels of up to 4, the recommended answer first. Panels only in a turn the user started.

| Verdict | The loop does | Recorded as |
| --- | --- | --- |
| **Keep** | nothing more | `accepted`, with date and the user's words |
| **Keep all minor** | accepts every class A entry shown | each `accepted` |
| **Change: how** | **redo on the same branch** as new commits; a new entry (`D-031 supersedes D-014`) carries the user's choice; checks re-run; anything built on the old choice is re-checked and listed | old entry `changed → D-031` |
| **Veto** | state the cascade, then revert with `git revert`, newest first, as set out under "How a veto runs" below | `vetoed`; each entry reverted with it `reverted (with D-014)` |
| **Veto, already merged** | open a revert PR for the user to merge and add the redo to the roadmap view | `vetoed (merged): follow-up <link>` |
| **Discuss** | park the item and everything built on it; pick other work | `discussing` |

**How a veto runs:**

1. State the cascade as its own line in the message **before any revert command runs**: every entry and commit built
   on the vetoed one, from the entries' "Depends on" lines; "cascade: none" when empty.
2. Then revert in the same turn with `git revert`, newest first: new commits, never a reset, a rebase or a
   force-push, and **nothing is deleted**.
3. Re-run the checks and push.
4. The veto is the go, so there is no wait between the cascade line and the revert.
5. If the whole PR was the decision, say so and leave closing it to the user.

Branches stacked on a reverted or changed one are brought up to date by **merging, never rebasing**.

- **Silence is never consent.** An entry stays `pending` until the user answers.
- **Merging a work PR is consent for the decisions its body lists:** the one implicit path, and the user's own act.
  Merging the log PR is not (see [decisions-and-ledger.md](decisions-and-ledger.md)).
- **A change or a veto teaches once.** Propose one standing answer for the charter's "Standing answers", added only
  on the user's yes. Never write it into `CLAUDE.md`, memory or settings.
- **Flagged entries cannot be bulk-kept**; only class A can.
