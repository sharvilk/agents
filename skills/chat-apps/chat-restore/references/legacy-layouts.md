# Older layouts

Archives made before format 2 can still be restored. verify.py checks them by their checksums only, so read their
manifests yourself and cite message numbers and paths as they appear.

| Layout | How to recognise it | Where the messages and files are |
| --- | --- | --- |
| Draft format 1 | `manifest.json` with `schema_version: 1`; `CHECKSUMS.sha256` lists every other file | `batches` in the manifest list `transcript/batch-NNNN.jsonl` files (lines with `message_id`, `capture_number`, `role`, `text`, `file_ids`, `text_evidence`) and their Markdown views; `files` map ids to `originals/<file_id>/…` |
| Document pilot | A manifest without a schema version, with `transcript_ranges`, `cutoff`, `files` and `original_attachments`; `checksums.sha256` (lower case) lists every other file | Markdown transcripts named in `transcript_ranges[].file` with `first_message` and `last_message`. A file name can claim a longer range than it holds: trust the headings inside and the declared range, not the name |
| Image pilot | A manifest naming `image-chat-full-backup-v1` and pointing at `image-manifest.json`; `checksums.sha256` lists every other file | Markdown transcripts listed in the manifest's `transcripts`; images under `images/uploaded/` and `images/generated/`, mapped to messages in `image-manifest.json`. Use the outer manifest for what the combined backup holds |

In all of them, several generated images can belong to one message: call one final only when the transcript says
so, or the user does.
