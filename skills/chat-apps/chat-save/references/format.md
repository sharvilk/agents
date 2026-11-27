# chat-save archive, format 2

One archive is one save of one chat. pack.py writes it and verify.py checks it: both use `chatarchive.py` in the
skill's scripts folder, which is the authority when this page and the code disagree.

## Members

| Path | What it is |
| --- | --- |
| `START-HERE.md` | How to continue: instructions for the person and for the assistant, the checksum snippet and the coverage counts; then, below a line that marks everything after it as saved data, the gaps and missing files, the brief, the latest messages and the file table. Rendered from the other members, so verify.py can rebuild it and compare |
| `manifest.json` | Source, cutoff, coverage, every file occurrence and where its bytes are |
| `transcript.jsonl` | The record: one message per line, in order |
| `transcript.md` | A readable view of `transcript.jsonl`, rendered from it; each message's text is a blockquote, so nothing inside a message can pose as a heading or another turn |
| `brief.md` | The continuation brief written by the source chat: a summary, never evidence |
| `files/<file_id>-<safe name>` | The bytes of one captured file occurrence |
| `raw/…` | Optional material added on the Mac with `file_chat.py --raw`, or by putting a saved page in the chat's inbox folder (a saved web page), byte for byte |
| `CHECKSUMS.sha256` | `<sha256>  <path>` for every other member |

Anything else in the archive is an error.

## transcript.jsonl

```json
{"n": 1, "role": "user", "text": "…", "files": ["f000001"], "evidence": "model_copy"}
```

| Key | Value |
| --- | --- |
| `n` | 1, 2, 3… with no gaps or repeats |
| `role` | `user`, `assistant`, `tool` or `system` |
| `text` | The message text; `""` for an image-only turn |
| `files` | Ids of the file occurrences shown in this message |
| `evidence` | `model_copy` (re-typed by the source chat's model from what it could see) or `exact` (copied from an exact source) |

The keys are written in this order, one line per message, UTF-8, non-ASCII kept as is except U+0085, U+2028 and
U+2029, which are written escaped (`\u2028`) because some readers break lines on them. Read the file by splitting
on `\n` only.

## manifest.json

| Key | Value |
| --- | --- |
| `schema_version` | `2` |
| `format` | `"chat-save"` |
| `revision` | `<YYYYMMDDTHHMMSSZ>-<12 hex>`: when it was packed, and the start of the content hash at that time |
| `content_sha256` | Hash of what the save holds now (source, messages, files, gaps, entries left out on purpose, first-message check, raw material); identical saves share it |
| `parent_revision` | The earlier save of this chat, or `null` |
| `created_utc` | When it was packed |
| `source` | `platform` (`chatgpt` or `claude`), `title` (one line), `chat_id` (letters, digits, `-` and `_`, or `null`), `project` (or `null`) |
| `cutoff` | `before_text`: the user's save request; `excluded`: what that leaves out (the request and everything after it) |
| `coverage` | `status`, `messages`, `first_message_confirmed_by_user`, `evidence` counts, `files_captured`, `files_missing`, `gaps` (one sentence each), `left_out` (exchanges left out on purpose, such as an earlier save of the same chat; one sentence each) |
| `messages` | `path`, `view` and `count` of the transcript |
| `files` | One entry per file occurrence (below) |
| `restore_checks` | The questions a restore answers before continuing |
| `raw` | Present when the Mac added raw material: `path`, `added_by`, `note` per item |

`coverage.status` is `complete` only when the first message was confirmed, there are no gaps and no file is missing;
otherwise `partial`, and the ZIP's name ends in `-partial`. Entries in `left_out` do not make a save partial.

Every value a reader sees (the title, file names, gaps, left-out entries, missing reasons) must be one line with no
control characters; verify.py fails an archive that breaks this, and pack.py collapses line breaks before writing.

## A file entry

| Key | Captured | Missing |
| --- | --- | --- |
| `file_id` | `f000001`… unique, one per occurrence | same |
| `kind` | `upload`, `generated`, `canvas`, `artifact`, `project_file` or `other` | same |
| `name` | The name shown in the chat | same |
| `message` | The message that shows it, or `null` when it is not tied to one | same |
| `status` | `captured` | `missing` |
| `path` | `files/<file_id>-<safe name>` | `null` |
| `size`, `sha256` | Of the bytes in `path` | `null` |
| `bytes_from` | `chat_files` (the chat's own copy), `model_copy` (written out by the model: a canvas or an artifact) or `user_download` (added on the Mac) | `null` |
| `missing_reason`, `how_to_get` | — | Why the chat could not reach it, and how the user can get it |

A file listed in a message's `files` must have that message as its `message`, and the reverse.

## What verification proves

Every byte matches its checksum, the paths are safe, the record is consistent, and the readable views and
`START-HERE.md` match the record. A ZIP whose members would unpack to more than 512 MB each, or 2 GB in all, is
refused before anything is unpacked. Verification does not prove that the source chat was captured in full: that is
what `coverage` says, and it is reported separately.
