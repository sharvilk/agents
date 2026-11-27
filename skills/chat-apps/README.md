# Chat skills: save a chat app conversation, file it in a private repo, continue it elsewhere

**For the ChatGPT and claude.ai chat apps only. Upload these skills to those apps; never copy them into
`~/.claude/skills/` or Codex.**

Two skills for the **ChatGPT and claude.ai chat apps**, and one script for your Mac. Together they save a chat (its
messages, uploaded files, generated images, canvases and artifacts) into a verified archive, keep that archive in a
private GitHub repo as readable files, and let a new chat in another account carry on from it.

**Who it is for.** Anyone who keeps real work in ChatGPT or claude.ai chats and wants a copy that does not depend on
one account, one app or one export button: for moving a project between accounts, keeping a record, or picking up
a long chat in a fresh one.

**Install in three steps** (details in [Install the skills](#install-the-skills)):

1. Clone this repository and, in this folder, run `python3 build_zips.py`. It writes `dist/chat-save.zip` and
   `dist/chat-restore.zip`.
2. In each chat app, upload the ZIPs as skills (the table in [Install the skills](#install-the-skills) names the
   menu and the plans).
3. In a chat, send "Save this chat". Then follow [Before the first filing](#before-the-first-filing) to set up the
   Mac script.

| Piece | Runs in | Does |
| --- | --- | --- |
| [chat-save](chat-save/SKILL.md) | a ChatGPT or claude.ai chat | Copies the chat it is in, the files it can reach and a continuation brief, then builds and checks a ZIP with its own [pack.py](chat-save/scripts/pack.py) |
| [file_chat.py](file_chat.py) | your Mac | Files every ZIP in your inbox folder (or one ZIP): verifies it, adds any files you downloaded by hand, confirms the repo is private, commits, pushes, opens a pull request, and re-reads the save from GitHub |
| [chat-restore](chat-restore/SKILL.md) | a new ChatGPT or claude.ai chat | Checks a saved archive with its own [verify.py](chat-restore/scripts/verify.py), reads it, confirms with you, and continues |

These skills are **not for Claude Code or Codex**. A coding agent's session is already a file on your disk, so
re-typing it from inside the agent would only make a lossy copy of a record you already hold exactly. Nothing here
copies the skills into a folder a coding agent loads skills from (see
[Why they must stay out of Claude Code and Codex](#why-they-must-stay-out-of-claude-code-and-codex)).

## Table of contents

- [How it works](#how-it-works)
- [Why they must stay out of Claude Code and Codex](#why-they-must-stay-out-of-claude-code-and-codex)
- [Install the skills](#install-the-skills)
- [Before the first filing](#before-the-first-filing)
- [Save a chat](#save-a-chat)
- [File a batch: the inbox](#file-a-batch-the-inbox)
- [File one ZIP on the Mac](#file-one-zip-on-the-mac)
- [Continue it in another account](#continue-it-in-another-account)
- [What is stored, and where](#what-is-stored-and-where)
- [What it guarantees, and what it does not](#what-it-guarantees-and-what-it-does-not)
- [Errors and what you see](#errors-and-what-you-see)
- [Tests](#tests)
- [Files here](#files-here)

## How it works

```
Figure 1 — save, file, restore

 THE CHAT YOU SAVE (ChatGPT or claude.ai)       YOUR MAC                               GITHUB (private repo)
 ┌──────────────────────────────────────┐
 │ you: "Save this chat" (chat-save)    │
 │ 0 stop if this is Claude Code/Codex  │
 │ 1 cutoff: just before your request   │
 │ 2 one question: first message, the   │
 │   chat's link, its title             │
 │ 3 copy messages, at most 4 at a time │──▶ chat-save-….zip ──▶ file_chat --inbox ──▶ chats/<chat>/<revision>/
 │ 4 copy the files it can reach; list  │    (inbox folder)     1 verify every byte        START-HERE.md
 │   the rest and how to get them       │    + files you        2 add your downloads       transcript.md
 │ 5 write the brief                    │      downloaded       3 repo private? hooks?     transcript.jsonl
 │ 6 meta.json                          │                       4 read back, commit        files/…
 │ 7 pack.py: ZIP, hashes, reopen,      │                       5 push: PR or --direct     manifest.json
 │   check                              │                       6 re-read from GitHub      CHECKSUMS.sha256
 └──────────────────────────────────────┘

 A NEW CHAT, ANY ACCOUNT, LATER
 personal ChatGPT (skills are listed for work and school plans only) ── attach the ZIP, or START-HERE.md alone, and send one line
 claude.ai (skills on every plan)      ── chat-restore + the ZIP, or the repo folder through Claude's GitHub connector
 either one                            ── checks it, reads the brief and the latest messages, quotes the first and
                                          last message and the final file, waits for your OK, then carries on
```

Three facts shape it:

1. **The chat packages the save; the Mac files it.**
   - ChatGPT's code sandbox "cannot make external web requests or API calls" (checked on 2026-11-25, OpenAI's
     [data analysis help page](https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt)).
   - OpenAI's help page says the GitHub app in ChatGPT "only lets you read from your repositories" (checked on
     2026-11-25, [Connecting GitHub to ChatGPT](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt)).
     In practice it wrote: tested on 2026-11-24 in a ChatGPT chat with the app linked to a
     personal GitHub account and the backup repo granted to it: it created blobs, a tree, a commit, a branch and a
     pull request, and PNGs of 32 KB to 1.2 MB arrived byte for byte. Its actions run in a separate JavaScript
     runtime that cannot see the sandbox's files: a file the sandbox writes reaches them only as base64 text the
     chat offers as a download, and only from the chat's next turn. That does not scale to a whole save: reading
     the text back spends the chat's own length. About 1.5 MB of files worked; a 3.7 MB save ended the chat with
     "You've reached the maximum length for this conversation". So the chat only packages the save, and the Mac
     files it.
   - claude.ai's GitHub integration reads file names and contents only (checked on 2026-11-25,
     [Claude's GitHub integration](https://claude.com/docs/connectors/github)); writing from claude.ai has not been
     tested.

   Pasting a GitHub token into a chat would leave it in that account's chat history, so the skill never asks for
   one. The chat hands over a ZIP and the Mac files it.
2. **A model can only re-type what it can see.** Inside a chat there is no exact export, so chat-save re-types the
   messages and marks every one `model_copy`. A very long chat may not fit the model's window; the first-message
   check catches that, and the gap is recorded. For those chats, also press Cmd+S on the chat page ("Webpage,
   Complete") and put the saved page in the chat's folder in the inbox: the full text is then kept as well. (The
   single-ZIP form of `file_chat.py` takes it with `--raw`; `--raw` does not exist with `--inbox`.)
3. **Not every file is reachable from inside a chat.** Older uploads leave the sandbox, and generated images are not
   always there as files. chat-save copies what it can reach, lists the rest with how to get each one, and
   `file_chat.py` adds the files you download (put them in the chat's folder in the inbox).

## Why they must stay out of Claude Code and Codex

```
Figure 2 — where an uploaded skill ends up

 you add a skill to …            it also loads in …
 claude.ai (Customize → Skills)  Claude Code signed in to the same account (Claude's skills help page: skills
                                 enabled in your Claude settings load in Claude Code; it needs Claude Code v2.1.273
                                 or later, and does not apply with an API key or a cloud provider). Synced copies
                                 were seen under ~/.claude/skills/synced/ (observed locally, not in the help page).
 ChatGPT (Plugins → Skills)      Codex, per OpenAI's build-skills page: "Standalone skills are available in the
                                 ChatGPT desktop app, Codex CLI, and IDE extension." (checked on 2026-11-25)
```

So a skill uploaded to a chat app can surface in the coding agents signed in to the same account. Nothing breaks.
But "save this chat" there would make a re-typed copy of a session that your machine already keeps
exactly. Three layers stop that:

1. **This folder is never copied** into `~/.claude/skills/`.
2. **Each skill's description says** it is for the chat apps only, never Claude Code or Codex.
3. **Each skill's first step stops** when it finds itself in Claude Code or Codex.

## Install the skills

Build the upload ZIPs from this folder. They are rebuilt from the source every time, never kept in git:

```bash
python3 build_zips.py
```

It prints the path, file count and SHA-256 of `dist/chat-save.zip` and `dist/chat-restore.zip`, beside the script.
Each ZIP holds one folder named like its skill (claude.ai requires that) with `SKILL.md`, `scripts/` and
`references/`.

| Where | Install | Then |
| --- | --- | --- |
| ChatGPT, Business, Enterprise, Healthcare or Edu (where you save) | Plugins in the sidebar → Skills → Create → Upload from your computer → `chat-save.zip`. OpenAI's help page does not say whether it takes a ZIP or a folder; the first install settles it. Skills there are "subject to workspace settings" | In the chat, type `@`, pick chat-save, send "Save this chat" |
| claude.ai, any plan (where you save) | Customize → Skills → + → Create skill → Upload a skill → `chat-save.zip`. It needs code execution turned on: in Settings → Capabilities on Free, Pro, Max and Ultra; on Team and Enterprise an owner turns it on in Organization settings → Plugins & skills (it is on by default on Team). A Team or Enterprise owner can turn off user-created skills; if they have, the skill can't be added there | Send "Save this chat" |
| claude.ai, any plan including Free (where you continue) | Same path → `chat-restore.zip` | Attach the archive, send "Restore this chat" |
| ChatGPT without skills, such as Free (where you continue) | Nothing: OpenAI's help page lists skills for eligible Business, Enterprise, Healthcare and Edu users, and no other plan | Attach the archive and send the line from its `START-HERE.md` |
| Claude Code, Codex | **Never** | — |

Plan facts are from the providers' own pages, checked on 2026-11-25 (they change, so check them before relying on
them): [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt),
[OpenAI's build-skills page](https://learn.chatgpt.com/docs/build-skills),
[Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude),
[GitHub in ChatGPT](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt),
[Claude's GitHub integration](https://claude.com/docs/connectors/github),
[ChatGPT data analysis](https://help.openai.com/en/articles/8437071-data-analysis-with-chatgpt),
[ChatGPT file uploads](https://help.openai.com/en/articles/8555545-file-uploads-faq).

## Before the first filing

`file_chat.py` needs, once:

1. **git and gh installed, with gh signed in to GitHub** (`gh auth login`). gh confirms the repo is private before
   every filing and opens the pull requests.
2. **A private GitHub repo per platform, with at least one commit.** Creating it with GitHub's "Add a README" option
   gives it that commit. An empty repo is refused, because it has no default branch to build on.
3. **A clone of each repo, found by one of these:**
   - `--repo PATH`;
   - `$CHAT_SAVE_REPO_CHATGPT` or `$CHAT_SAVE_REPO_CLAUDE`;
   - the folder named `<platform>-chat-history` beside this repository's checkout, where `<platform>` is `chatgpt` or
     `claude`, by the app the chat came from.

   Its origin must be the GitHub repo, and the clone must have no commit hooks.
4. **The inbox folder, once:** `mkdir -p ~/chat-backups/inbox`. Browsers save to `~/Downloads`; you move each ZIP
   from there into the inbox. The script never creates the inbox.

## Save a chat

In the chat: "Save this chat" (or "Save a new revision" later). The steps match [chat-save's SKILL.md](chat-save/SKILL.md):

0. **Stops** if it is running in Claude Code or Codex.
1. **Says what will happen** and freezes the cutoff just before your request. On a re-save, the earlier save
   exchanges are left out and listed as "left out on purpose", which does not make the save partial.
2. **Asks one question:**
   - is this quoted message the first one (scroll to the top and answer)?
   - the chat's link, whose id keeps every save of this chat together;
   - the chat's title.
3. **Copies the messages**, at most four at a time, into `messages.jsonl`, giving each file an id as it appears.
4. **Lists every file** in `files.json`. It copies the bytes it can reach (only from its working folder or the chat's
   own file folders), writes canvases and artifacts out as text, and marks the rest missing with how to get them.
5. **Writes `brief.md`:** the goal, the decisions with message numbers, the open questions, the current file
   versions.
6. **Writes `meta.json`.**
7. **Runs pack.py,** which builds the ZIP, hashes every member, reopens the ZIP, checks it and prints this:

```
chat-save: archive built and verified
  chat      Logo ideas (ChatGPT)
  revision  20261124T101200Z-3be1c2d4e5f6
  status    PARTIAL
  messages  52 (model copy); first message confirmed by you: yes
  files     8 captured, 1 missing
            f000009 logo-v3.png: generated image not available as a file in the sandbox. Download it from
            message 47 and name it f000009.png.
  package   verified: 14 members, every SHA-256 checked after reopening the ZIP
  zip       /mnt/data/chat-save-chatgpt-logo-ideas-20261124T101200Z-3be1c2d4e5f6-partial.zip
  sha256    9b4c…
  restore   not tested yet
next: download the ZIP, then move it into ~/chat-backups/inbox (create it once: mkdir -p ~/chat-backups/inbox). If I listed files to download, or you saved the chat page, make a folder there and put the ZIP and those files in it. Then on your Mac run `python3 file_chat.py --inbox` from the folder that holds file_chat.py.
```

Browsers save to `~/Downloads`, so download the ZIP and then move it into `~/chat-backups/inbox`. A file the save
lists as missing (named as it says), or a saved page of the chat, goes with the ZIP in a folder of its own there (see
[the inbox](#file-a-batch-the-inbox) for where each goes). If the chat cannot run code at all,
chat-save hands over its four working files instead, and `python3 chat-save/scripts/pack.py <folder>` builds the
same ZIP on the Mac.

## File a batch: the inbox

Move each chat's ZIP into one folder (`~/chat-backups/inbox`) and run one command. `file_chat.py` files every save in it, one pull request
each, and moves what it filed out of the way.

```
Figure 3 — chat to pull requests (expected)

 chat (ChatGPT / claude.ai)      your Mac                                              GitHub (private repos)
 ┌────────────────────┐   download   ~/chat-backups/inbox/           one command
 │ "Save this chat"   │ ───────────▶   a.zip              ─┐   python3 file_chat.py --inbox
 │ chat-save builds   │              Logo ideas/            ├────────────────────────────▶  one PR per save, in the
 │ a verified ZIP     │                (ZIP + f000003-…png) │   each item: verify, add          chat's platform repo
 └────────────────────┘              b.zip.crdownload ─ skipped (still downloading)             (chat-save/<slug>-<revision>)
                                      notes.txt        ─ left alone                                     │
                                                                                                         │
                                  ~/chat-backups/filed/  ◀── filed or already filed: MOVED here, never ─┘
                                                              deleted; a partial one stays in the inbox
```

**The CLI.**

```bash
mkdir -p ~/chat-backups/inbox
python3 file_chat.py --inbox            # the default inbox, ~/chat-backups/inbox
python3 file_chat.py --inbox ~/more/inbox  # another inbox; its filed folder is ~/more/filed
python3 file_chat.py --inbox --dry-run  # check everything; write, move and push nothing
```

- Run it from the folder that holds `file_chat.py`, or give the path to it.
- The inbox must exist: the script never creates it. It must be a folder named `inbox`, and its parent must not be
  your home folder or the disk root, because `filed/` (the inbox's sibling, created when the first item moves) and
  the lock file live in that parent. If the path you give is a symbolic link, its
  target is the inbox: the target itself must be named `inbox`, and `filed/` and the lock go beside the target, not
  beside the link (`~/chat-backups/inbox` linked to `~/Dropbox/inbox` keeps `filed/` in `~/Dropbox/`).
- `--direct`, `--dry-run` and `--no-remote-check` apply to every save in the batch.
- Each platform's repo comes from `$CHAT_SAVE_REPO_CHATGPT` / `$CHAT_SAVE_REPO_CLAUDE`, or the default folder (see
  [Before the first filing](#before-the-first-filing)). `--repo` is refused with `--inbox`: one path cannot be right
  for two platforms. A ZIP, downloaded files and `--raw` are refused too: `--raw` exists only in the single-ZIP form,
  and in the inbox a saved page in the chat's folder is filed the same way.

**What goes in the inbox**, processed in name order:

| Item | Meaning |
| --- | --- |
| `name.zip` at the top level | One save with nothing added |
| A folder at the top level | One chat: exactly one `.zip`, plus downloads whose names start with a file id (`f000003-sketch.png`), plus optionally a saved page: a lone `X.html`, or `X.html` with its `X_files/` folder (an `X_files/` folder needs its `X.html`), filed as `--raw`. Anything else in the folder refuses that folder. Every suffix matches in any letter case (`Chat.ZIP`, `X.HTML`) |
| `*.crdownload`, `*.download`, `*.part` (top level or in a chat folder) | A download in progress: skipped until it finishes |
| Any other file, a hidden file or folder, a symbolic link | Not a save: reported as left alone, never touched |
| `.DS_Store` | Ignored everywhere |

**A worked example.** The inbox holds two top-level ZIPs (one ChatGPT, one Claude), one chat folder with a ZIP and a
download, and one partial save whose missing file is not downloaded yet:

```
~/chat-backups/
├── inbox/
│   ├── chat-save-chatgpt-logo-ideas-20261124T101200Z-3be1c2d4e5f6.zip
│   ├── chat-save-claude-pricing-20261124T103000Z-77aa90c1d2e3.zip
│   ├── Garden plan/
│   │   ├── chat-save-chatgpt-garden-plan-20261124T104500Z-0a1b2c3d4e5f-partial.zip
│   │   └── f000003-sketch.png
│   └── chat-save-chatgpt-trip-20261124T105500Z-9f8e7d6c5b4a-partial.zip     (needs f000005)
└── filed/                                   (made at the first move)
```

After `python3 file_chat.py --inbox` (each save's detailed output comes first; this is the closing summary):

```
file-chat: inbox summary
  filed   chat-save-chatgpt-logo-ideas-20261124T101200Z-3be1c2d4e5f6.zip → <you>/<chatgpt repo> https://github.com/<you>/<chatgpt repo>/pull/12  52 messages, 9 files
  filed   chat-save-claude-pricing-20261124T103000Z-77aa90c1d2e3.zip → <you>/<claude repo> https://github.com/<you>/<claude repo>/pull/3  18 messages, 2 files
  filed   Garden plan → <you>/<chatgpt repo> https://github.com/<you>/<chatgpt repo>/pull/13  31 messages, 4 files
  partial chat-save-chatgpt-trip-20261124T105500Z-9f8e7d6c5b4a-partial.zip → https://github.com/<you>/<chatgpt repo>/pull/14  missing f000005; drop it into inbox/chat-save-chatgpt-trip-20261124T105500Z-9f8e7d6c5b4a-partial/ and re-run
```

```
~/chat-backups/
├── inbox/
│   └── chat-save-chatgpt-trip-20261124T105500Z-9f8e7d6c5b4a-partial/
│       └── chat-save-chatgpt-trip-20261124T105500Z-9f8e7d6c5b4a-partial.zip
└── filed/
    ├── chat-save-chatgpt-logo-ideas-20261124T101200Z-3be1c2d4e5f6.zip
    ├── chat-save-claude-pricing-20261124T103000Z-77aa90c1d2e3.zip
    └── Garden plan/
```

To finish the partial save, put `f000005.png` (named from its file id) into that folder and run the command again:
the same branch is updated, the pull request updates, and the folder moves to `filed/`.

**The summary lines:**

| Line | Meaning |
| --- | --- |
| `filed   <name> → <repo> <PR URL>  N messages, M files` | Filed and moved to `filed/` (with `--direct` there is no PR URL) |
| `partial <name> → <PR URL>  missing f000005; drop it into inbox/<folder>/ and re-run` | Filed, but files are still missing; it stays in the inbox (a top-level ZIP moves into a new folder named after it) |
| `already filed <name>` | The same save was filed before and its filed copy verifies; moved to `filed/`. If files are still missing it stays in the inbox, with the same hint as `partial` |
| `refused <name>: <reason>` | Not filed; it stays where it is, and the batch goes on. The reason is the refusal's first line, and when that line only introduces a list, the first item of the list too (`refused a.zip: the archive cannot be read, so nothing was filed — not a readable ZIP`) |
| `failed  <name>: <reason>` | A disk error, an unexpected error (shown as `<ExceptionType>: <message>`), or the save was filed but could not be moved; the batch goes on |
| `skipped <name>: download still in progress` | Try again when the download is finished |
| `left alone <name>: not a save` | Not touched |
| `dry run <name> → <repo>: would be filed, …` | `--dry-run`: nothing written, moved or pushed |
| `dry run <name>: already filed; would move to filed/` | `--dry-run`, a save that is already filed: it stays where it is |
| `dry run <name>: already filed; missing f000005; would move into inbox/<folder>/` (or `would stay in the inbox`) | `--dry-run`, already filed with files still missing |

**Moves.** A ZIP or chat folder is moved to `filed/`, never deleted and never overwritten: on a name clash the new
one is called `name (2)`, `name (3)`, and so on. The same ZIP downloaded twice therefore ends as `name.zip` and
`name (2).zip`. In `--dry-run`, nothing moves, no folder is made and no lock file is written.

**One run at a time.** A lock file `.file-chat-inbox.lock` beside the inbox (in `~/chat-backups/`) holds the run's PID
and is removed when the run ends, even after an error. A lock whose process no longer exists is replaced (the run
says so). `--dry-run` writes nothing, so it takes no lock and ignores one.

**Exit code.** 0 when every save was filed, partial or already filed (also for an empty inbox); 1 when any item was
refused or failed, or the inbox is missing, not a folder, not named `inbox`, too broad or locked; 2 for wrong
usage. Skipped and left-alone items do not fail the run. A dry run exits 0 unless an item would be refused (1) or
the usage is wrong (2).

**Errors and what you see**, besides the per-save ones in [Errors and what you see](#errors-and-what-you-see):

| You see | Why | Do |
| --- | --- | --- |
| `file-chat: the inbox <path> does not exist. Create it with:` `mkdir -p <path>` | The inbox is never created for you | Run that command, then download the ZIPs and move them into it |
| `file-chat: <path> is not a folder` | The inbox path is a file (exit 1) | Pass the folder |
| `file-chat: <path> is too broad to be an inbox; use a folder of its own` | The path is your home folder or the disk root | Use a dedicated folder such as `~/chat-backups/inbox` |
| `file-chat: the inbox must be a folder named exactly inbox (in lower case), inside a folder that is not your home folder or the disk root: <path> is not. …` | The folder is named something else (such as `~/chat-backups`, `~/Downloads` or `Inbox`), or its parent is your home folder or the root. When you gave a link, the message reads `<link> is a link to <target>, which is not`: the target must be the one named `inbox` | Use `~/chat-backups/inbox`, or a link to a folder named `inbox` |
| `file-chat: cannot read the inbox <path>: <error>` (exit 1) | The inbox exists but cannot be listed (permissions) | Fix its permissions |
| `file-chat: replacing a stale lock left by process <pid>` | An earlier run was killed and its process is gone; this run takes the lock over and goes on | Nothing |
| `file-chat: another inbox run holds the lock <path> (PID n); wait for it. Only if no run is active, remove it with:` `rm <path>` | A run with that PID is going | Wait; only if no run is active, run the `rm` command and try again |
| `file-chat: the lock <path> exists and does not hold a process number. If no inbox run is active, remove it with:` `rm <path>` | The lock file is damaged, or holds a number no process can have | If no run is active, run the `rm` command |
| `file-chat: cannot replace the lock <path>: <error>` or `file-chat: cannot create the lock <path>: <error>` | The folder beside the inbox is not writable, or the stale lock cannot be removed | Fix the permissions on that folder |
| `file-chat: --inbox files every save in the inbox, so it cannot be combined with a ZIP, downloaded files, --raw or --repo …` (exit 2) | Mixed the two forms | Drop the extra arguments, or use the single-ZIP form |
| `file-chat: give a ZIP to file, or --inbox to file a folder of them` (exit 2) | No ZIP and no `--inbox` | Give one of them |
| `file-chat: --inbox files every save in the inbox, so it cannot be combined with …` (exit 2), after `--inbox a.zip` | A ZIP's name came right after `--inbox`, which takes a folder | Use `python3 file_chat.py a.zip`, or `--inbox` alone |
| `file-chat: <zip> is not a file` (exit 2) | The single-ZIP form was given a path that is not a file | Fix the path |
| `file-chat: <name>` on a line of its own, followed by that save's output | Progress: the item being filed now | Nothing |
| `file-chat: nothing to do: <title> is already filed …; the filed copy verifies (N files)` | The same save was filed before (single-ZIP form, and per item in the inbox) | Nothing |
| `file-chat: dry run; would file <title> (…) → chats/…/ in <repo> (private), N files, new, by pull request` | `--dry-run` for a save that would be filed | Run again without `--dry-run` |
| `file-chat: the inbox <path> is empty; nothing to file` (exit 0) | Nothing there | Download a ZIP, then move it into the inbox |
| `refused <folder>: no ZIP in this folder` | A chat folder with no ZIP | Put the chat-save ZIP in it |
| `refused <folder>: <name>: a second ZIP; a chat's folder holds exactly one` | Two ZIPs in one folder | Move one out |
| `refused <folder>: <name>: not part of a save …` | A file that is no ZIP, no file-id download and no saved page (`X.html` with `X_files/`) | Move it out, or rename a download to start with its file id |
| `refused <folder>: <name>: symbolic links are not filed` | A link in a chat folder | Replace it with the real file |
| `skipped <name>: download still in progress` | A `.crdownload`, `.download` or `.part` item | Wait for the download, then run again |
| `failed  <name>: <ExceptionType>: <message>` | A bug or an unexpected condition in that item; the batch went on and the summary was still printed | Report it with the message; the save's file is untouched in the inbox |
| `failed  <name>: filed, but it could not be moved: …` | The pull request exists, but the move to `filed/` failed (permissions, disk) | Move it by hand; running again reports it as already filed |

## File one ZIP on the Mac

The inbox runs this same code once per save; use the single-ZIP form to file one ZIP from anywhere, or to pass `--repo` or
`--raw`.

```bash
python3 file_chat.py ~/Downloads/chat-save-chatgpt-logo-ideas-20261124T101200Z-3be1c2d4e5f6-partial.zip ~/Downloads/f000009.png
```

```
file-chat: filed Logo ideas (ChatGPT)
  repo      <you>/<platform>-chat-history (private)
  folder    chats/logo-ideas--5c1e9a/20261124T101200Z-3be1c2d4e5f6/
  status    COMPLETE (1 file(s) added from your downloads)
  commit    4f2a9e1c0b7d on chat-save/logo-ideas-20261124T101200Z-3be1c2d4e5f6
  pr        https://github.com/<you>/<platform>-chat-history/pull/12  (merge it to keep the save on main)
  github    chat-save/logo-ideas-… points at the commit; a fresh copy of the folder passed every check (15 files)
```

**What it does, in order.** Every step before the push stops the run with GitHub unchanged:

1. **Verifies the ZIP.** A ZIP that fails verification is never filed. Neither is one holding a file GitHub would
   refuse (over 100 MB), or a name git treats specially (`.git`, `.gitattributes`, `.gitmodules`, `.gitignore`).
2. **Adds downloaded files.** Each name must start with the file id the save listed as missing (`f000009.png`,
   `f000009-logo.png`). It hashes each one, then rebuilds and re-verifies the manifest, views and checksums.
3. **Adds `--raw PATH` material** (a saved page's `.html` file and its `_files` folder) under `raw/`, byte for byte.
   Finder's `.DS_Store` files are left out, and it says so. Names are stored in composed Unicode (NFC), the form git
   on a Mac stores, so a name with accents matches after a checkout.
4. **Checks the repo** found as described in [Before the first filing](#before-the-first-filing):
   - it has no commit hooks (pre-commit, prepare-commit-msg, commit-msg, post-commit), because file-chat writes its
     commit without running them;
   - its origin is a GitHub repo, and it pushes to the same address it fetches from;
   - gh confirms that repo is private.
5. **Finds the folder:** `chats/<title-slug>--<key>/<revision>/`, reusing the chat's folder from an earlier save
   (matched by chat id, or by title when there is none).
   - The same save filed again changes nothing. Before saying so, it verifies the filed copy from what it fetched,
     and says loudly if that copy no longer verifies.
   - The same save with missing files now added updates its folder.
   - The original ZIP filed again after that changes nothing, in either mode.
   - A different archive with the same revision id is refused, so a filed save is never overwritten.
6. **Reads back, then commits.** It writes the folder to a temporary directory and reads it back, so nothing that
   would not survive a checkout is pushed. Then it writes one commit on top of origin's default branch, in a
   temporary git index, so your checkout and its index are untouched. The commit holds the revision folder, plus the
   chat's `README.md` the first time.
7. **Pushes:**
   - **By default** (`--direct` instead commits straight to the default branch), to the branch `chat-save/<slug>-<revision>`,
     then `gh pr create` opens a pull request that you merge.
   - **A re-run reuses that branch and never takes anything away from it.** Nothing is pushed when the branch already
     holds this save with as many files or more (its copy is verified instead). Otherwise the new commit goes on top
     of it, as a fast-forward, and the open pull request updates. A different download for a file the branch already
     holds is refused, as on the default branch.
   - **With `--direct`,** straight to the default branch, as a fast-forward only. A clean checkout of that branch is
     then fast-forwarded too.
8. **Checks GitHub:**
   - the branch must point at the commit;
   - a fresh `--depth 1 --filter=blob:none` sparse clone of just that folder must pass verification with
     byte-identical files. A server without partial clone gets a plain shallow clone instead.

   A failure here starts with PUSHED, because GitHub already holds the commit.

Other options:
- `--dry-run` checks everything and prints the plan, writing nothing (it does fetch).
- `--no-remote-check` skips step 8 and says so in the output.
- Options and files can come in any order.

## Continue it in another account

1. **Get the archive:**
   - **The original ZIP.**
   - **The save's folder from the repo.** GitHub can't download a single folder, so on the Mac pull your clone of
     the backup repo, then zip the save folder's contents, for example
     `cd <your clone>/chats/<chat>/<revision> && zip -qr ~/Downloads/restore.zip .`.
   - **Claude's GitHub connector.** Add that folder to a Claude chat or project directly.
2. **Start a new chat:**
   - **claude.ai:** install chat-restore once, attach the archive, send "Restore this chat".
   - **ChatGPT Free:** attach the ZIP and send "Read START-HERE.md in the attached archive and follow it." Free
     allows 3 file uploads a day (checked on 2026-11-25, OpenAI's file uploads FAQ), and a ZIP is one. If the chat can't open ZIPs, attach `START-HERE.md` on its own: it
     carries the brief and the latest messages (about 6,000 tokens of messages, plus the brief). In a long chat
     message 1 is not among them; attach `transcript.md` as well when you need it.
3. **Check its answers.** Before going on, it:
   - quotes message 1 and the last message;
   - names the final file and the message that makes it final;
   - reports the coverage, and whether it could check the checksums.

   Compare them with what you remember, then say go.

It is a new chat that starts from the saved one. Neither app can put old chats back into a sidebar or restore their
branches, settings or memory.

## What is stored, and where

| Where | What |
| --- | --- |
| The chat's sandbox, while saving | The working folder (`meta.json`, `messages.jsonl`, `files.json`, `brief.md`) and the ZIP; gone when the sandbox resets |
| `~/Downloads` | Where the browser first saves the ZIP and any files you download; you move them into the inbox |
| `~/chat-backups/inbox` | The ZIPs and chat folders waiting to be filed; you create it once (`mkdir -p ~/chat-backups/inbox`); a partial save stays here |
| `~/chat-backups/inbox/<name>/` | A partial save's folder: its ZIP, and where you drop the files it still needs; made when a top-level partial ZIP is filed |
| `~/chat-backups/filed` (beside the inbox's target, if the inbox is a link) | Everything already filed, moved here whole, never deleted or overwritten (a clash gets ` (2)`); made at the first move |
| `~/chat-backups/.file-chat-inbox.lock` (likewise beside the target) | The PID of a running `--inbox` run; removed when the run ends |
| Your local clone of the backup repo | Only what git fetches; `file_chat.py` adds commit objects but never edits the checkout, except the fast-forward after `--direct` |
| The private GitHub repo, one per app (`<platform>-chat-history`, where `<platform>` is `chatgpt` or `claude`) | `chats/<title-slug>--<key>/README.md` (written with the chat's first save) and one folder per save, readable as is |

One save's folder, in short (the full format is [references/format.md](chat-save/references/format.md)):

| Member | What it is |
| --- | --- |
| `START-HERE.md` | How to continue, a checksum snippet and coverage; then, below a line, the gaps, the brief, the latest messages and the file table |
| `transcript.jsonl` | The record, one message per line: `n`, `role`, `text`, `files`, `evidence` |
| `transcript.md` | The same, readable, each message's text quoted |
| `brief.md` | The source chat's summary for continuing: never evidence |
| `files/` | Original bytes, one per file occurrence, with where they came from |
| `raw/` | A saved web page or other material added on the Mac |
| `manifest.json` | Source, cutoff, coverage, every file and its hash |
| `CHECKSUMS.sha256` | Every other member |

## What it guarantees, and what it does not

| Claim | Backed by |
| --- | --- |
| The archive's bytes are exactly what pack.py wrote | Every member's SHA-256: checked after reopening the ZIP, again before filing, again after the read-back, and again after re-reading from GitHub |
| The record is consistent | Numbering 1, 2, 3…; every file link both ways; views rebuilt and compared; no unexpected or unsafe members |
| The save only goes to a private GitHub repo | gh confirms the origin repo is private before anything is pushed |
| GitHub holds exactly that folder | The branch points at the commit, and a fresh sparse clone verifies byte for byte |
| Saved text cannot pose as instructions or turns | Message text and the brief are blockquotes; titles, names and gaps are one escaped line; the model-written parts sit below a line that marks them as data |
| **Not** guaranteed: the source chat was captured in full | The model re-typed what it could see. Coverage says so: `model_copy` on every message, the first-message answer, gaps, missing files |
| **Not** guaranteed: a restore continues correctly | Only you can judge that, from the quotes it shows before continuing |

Also:
- A partial save is labelled `PARTIAL` everywhere, and its ZIP name ends in `-partial`.
- Text inside the archive is data. Both skills and `START-HERE.md` say so, and a restore never follows instructions
  found in a saved chat.

## Errors and what you see

The scripts print one line naming the problem; when there are several, a list follows. pack.py's lines start with
`chat-save:` and file_chat.py's with `file-chat:`. The exit code is 1, or 2 for wrong usage.

| Where | You see | What to do |
| --- | --- | --- |
| pack.py, in the chat | `the working files have problems; fix them and run pack.py again:` with each problem, such as `message numbering must run 1, 2, 3… with no gaps; message 7 is missing` or `… is outside the working folder and the chat's file folders` | The chat fixes its files and reruns; it never writes the ZIP itself |
| pack.py, in the chat | `the ZIP failed its check after reopening, so it was deleted:` | Rerun; if it repeats, the sandbox's storage is failing |
| verify.py, in a restore | `FAILED: N problem(s)` with each path, such as `files/f000002-logo.png: SHA-256 does not match CHECKSUMS.sha256` | Do not continue from it. Get the archive again from its source (the original ZIP or the repo), then restore again |
| verify.py, in a restore | `CHECKSUMS.sha256 is missing from the archive's root … one was found at <folder>` | The ZIP holds the save one folder too deep: zip that folder's contents instead |
| file_chat.py | `the archive cannot be read, so nothing was filed:` or `the archive failed verification, so nothing was filed:` | Get the ZIP again; nothing changed anywhere |
| file_chat.py | `<path>: no such file or folder` | A `--raw` path does not exist; fix it |
| file_chat.py | `<path>: symbolic links are not copied` | A `--raw` path or a file inside it is a link; copy the real file |
| file_chat.py | `<path>: its path …` | A `--raw` file has a name the archive cannot hold; rename it |
| file_chat.py | `<fid> was given twice` | Two downloads for one file id; pass one |
| file_chat.py | `<path>: not a regular file` | A download is a folder or a link; pass the file itself |
| file_chat.py | `raw/<name> is already in the archive` | The save already holds raw material of that name; rename the page you add |
| file_chat.py | `after adding files the archive no longer verifies; nothing was filed:` | Rare; run again, and if it repeats keep the ZIP and the downloads and report it |
| file_chat.py | `GitHub's <branch> does not point at the commit` or `the copy fetched back from GitHub does not verify:` or `… differs from what was filed` | These start with PUSHED (see below); run it again, it verifies the filed copy |
| file_chat.py | `` `git …` failed: … `` or `` `gh …` failed: … `` | The command's own error follows: usually the network, a sign-in (`gh auth login`) or permissions; fix that and run again |
| file_chat.py | `git <command> took longer than 600 s and was stopped` | The network stalled; run it again |
| file_chat.py | `file-chat files chat-save format 2 archives only` | An older archive can be restored, not filed |
| file_chat.py | `… is N MB; GitHub refuses files over 100 MB, so this save cannot be filed as is` or `git treats this name specially` | Keep that ZIP somewhere safe; it cannot go in a GitHub repo as it is |
| file_chat.py | `a downloaded file's name must start with the file id …`, `this save has no file f000010`, `… was already captured in the chat` | Rename the download as the save's summary said, or drop it; pass a saved page with `--raw` |
| file_chat.py | `… is not a clone of your ChatGPT backup repo; clone it there or pass --repo` | Clone the repo, or point `--repo` at it |
| file_chat.py | `… has commit hooks (pre-commit) …` | It will not skip hooks; file by hand, or remove the hooks from that clone |
| file_chat.py | `… origin (…) is not a GitHub repo` or `… is not confirmed private by GitHub, so nothing was filed` | Point the clone at your private GitHub repo; check `gh auth login` |
| file_chat.py | `cannot tell …'s default branch; a new repo needs one commit first` | Add a README on GitHub, then file again |
| file_chat.py | `gh is not installed` or `git is not installed` | Install it (see [Before the first filing](#before-the-first-filing)) |
| file_chat.py | `the save would not read back the same from a checkout, so nothing was pushed:` | Usually two raw files whose names differ only in case; rename one and file again |
| file_chat.py | `… already holds a different archive with this revision id (…); a filed save is never overwritten` | Two different archives claim one revision; the message says why. If it says to pass every download together, do that |
| file_chat.py | `the commit was made but not pushed, so GitHub is unchanged.` | Usually the network or a sign-in; run it again |
| file_chat.py | `PUSHED <commit> to <branch>, but the check of what GitHub holds FAILED; do not trust this save until it passes:` | Run it again: it finds the save already filed and verifies that copy, saying whether it passes. If it fails again, compare the branch with the ZIP by hand |
| file_chat.py | `… is filed, but the filed copy does NOT verify, so do not trust it:` | Someone or something changed the filed folder; restore it from the ZIP, or file the ZIP again after removing that folder by hand |
| file_chat.py | `… origin pushes to a different address than it fetches from` | Remove the clone's separate push address (`remote.origin.pushurl`) |
| file_chat.py | `pushed <branch> (…), but opening the pull request failed;` or `checked <branch> …` | Run it again (it reuses the branch), or open the pull request on GitHub from that branch |
| file_chat.py | `note: your checkout of … was left as it is` | After `--direct` with a dirty checkout, or one on another branch: pull when convenient |
| build_zips.py | `build-zips: <skill>/SKILL.md is missing` | The skill folder is incomplete; restore it from git |

Nothing here runs in the background, so nothing raises alerts. A failure shows only in the output of the command you
ran.

## Tests

From this folder, with the standard library only:

```bash
python3 -I tests/test_archive.py      # pack.py and verify.py: 45 cases, a few seconds
python3 -I tests/test_file_chat.py    # file_chat.py end to end: 31 cases, under a minute
python3 -I tests/test_inbox.py        # file_chat.py --inbox end to end: 47 cases, about a minute
python3 -I tests/test_packaging.py    # the upload ZIPs and the skill texts: 7 cases
```

- **Archive tests** build the [synthetic chat](examples/synthetic-chat/) and break the result in every way the
  checks claim to catch:
  - a changed byte, a duplicate member, a path that climbs out, a symbolic link;
  - an unexpected or unreferenced member, edited views, false coverage, a wrong content hash;
  - a missing captured file, unlisted raw material, a malformed manifest (which must fail without a traceback);
  - an oversized member, refused before unpacking.

  Saved text tests:
  - line separators survive exactly;
  - a title cannot add instructions above the data line, and a message cannot pose as another turn;
  - every field a reader sees must be one line;
  - the brief and gaps sit below the data line.

  pack.py refuses a claim of exactness and a file from outside its folders.
  The older layouts, a ZIP with a top folder and members without file-type bits must pass.
- **file_chat tests** run against a local bare repo standing in for GitHub. Each run has a temporary `HOME`, a
  temporary git config, no credentials and a fake `gh` first on `PATH`. The clone's origin is a GitHub address that
  git rewrites to the local repo, so even with a refusal deleted, the script can only write to the temporary repos.
  They cover:
  - the pull request path and the direct path;
  - re-runs that reuse or fast-forward the branch, and never take a file away from it;
  - idempotence, downloads, completion in place, and the original ZIP after a completion, in both modes;
  - raw material without Finder files, names in decomposed Unicode, and options in any order;
  - a filed copy changed by hand is reported;
  - every refusal: not private, not GitHub, a different push address, special names, names that collide on the
    disk, files over 100 MB, hooks, a different save, a rejected push.
- **Inbox tests** use the same temporary setup with two repos (ChatGPT and Claude); the inbox and `filed/` are always
  inside the temporary folder. They cover:
  - two saves from two platforms, filed into their own repos and moved; a chat folder with a download, and with a
    saved page;
  - a partial ZIP moved into its own folder, then completed on the same branch and moved to `filed/`; a partial chat
    folder staying put; the same save again (already filed, moved with a suffix);
  - a corrupt ZIP refused while the rest are filed; a stray file left alone; two ZIPs or an unrelated file in a
    folder; a download in progress skipped;
  - `--dry-run` changing nothing in the inbox's parent (checked by hashing every file) for a fresh partial, an
    already filed complete and an already filed partial save, and leaving no lock; `--inbox` with `--repo`, a ZIP,
    downloads or `--raw`, or a `.zip` as the inbox; a missing, an empty and a regular-file inbox; the inbox-name
    rule (a folder not named `inbox`, the parent folder, a parent that is `HOME`, the disk root); a name clash in
    `filed/`, with a dotted folder name too; the default inbox under `HOME`;
  - the lock: held by a live process, damaged, holding an impossible number, stale and replaced, impossible to create,
    removed after a refusal; an unreadable inbox or chat folder; a linked inbox, and the inbox name in the wrong case;
  - a move that fails after filing and an unexpected error in one item: reported, the next item still filed, the
    summary printed, the lock removed; a partial ZIP never reusing an existing folder of its name;
  - exactly one pull request per save, each to its own platform's repo; symbolic links, hidden folders, an `X_files/`
    folder without its page, and upper-case suffixes; the refusal reason shown in the summary.
- **Packaging tests** install the built ZIPs into a temporary folder and run pack.py and verify.py from there,
  proving each skill is self-contained.

`chatarchive.py` and `references/format.md` exist in both skills, because each skill is uploaded on its own. A test
fails if the two copies differ: change one, copy it to the other.

## Files here

| File | Purpose |
| --- | --- |
| [chat-save/SKILL.md](chat-save/SKILL.md) | The save procedure the chat follows |
| [chat-save/scripts/pack.py](chat-save/scripts/pack.py) | Builds, reopens and verifies the ZIP from the working folder |
| [chat-save/scripts/chatarchive.py](chat-save/scripts/chatarchive.py) | Reads, checks and renders archives; identical in both skills |
| [chat-save/references/format.md](chat-save/references/format.md) | The archive format; identical in both skills |
| [chat-restore/SKILL.md](chat-restore/SKILL.md) | The restore procedure |
| [chat-restore/scripts/verify.py](chat-restore/scripts/verify.py) | Checks an archive, ZIP or folder |
| [chat-restore/references/legacy-layouts.md](chat-restore/references/legacy-layouts.md) | How to read the archives made before format 2 (restorable, not fileable) |
| [file_chat.py](file_chat.py) | Files archives in their backup repos: one ZIP, or an inbox folder of them |
| [build_zips.py](build_zips.py) | Builds the upload ZIPs |
| [examples/synthetic-chat/](examples/synthetic-chat/) | A made-up chat's working folder: the tests' fixture and a dry run for a first install |
| [tests/](tests/) | The tests above |
