"""Build a chat-save archive (format 2) from a working folder, then reopen it and check every byte.

Usage:  python3 pack.py WORK_DIR [--out DIR]

WORK_DIR holds what the chat wrote while saving (SKILL.md says how):
    meta.json        platform, title, chat id (or the chat's link), cutoff, the first-message check, gaps, the
                     exchanges left out on purpose, parent revision
    messages.jsonl   one message per line {"n", "role", "text", "files", "evidence"}; a long message may be split
                     into pieces that carry "part" and "parts", joined here in order
    files.json       one entry per file occurrence: "captured" with a "source" path to the real bytes (inside the
                     working folder or the chat's own file folders), or "missing" with the reason and how to get it
    brief.md         the continuation brief

It writes chat-save-<platform>-<title>-<revision>[-partial].zip into --out (default: WORK_DIR's parent folder),
reopens the ZIP, verifies it with chatarchive, and prints a summary to show the user.
Exit 0: built and verified. 1: the input has problems (each printed with what to fix), or the reopened ZIP failed its
check (the ZIP is deleted, so no unverified archive is left behind). 2: wrong usage.
"""
import argparse
import datetime
import json
import stat
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chatarchive as ca  # noqa: E402  (imported after the path insert, so it works with python3 -I too)

META_KEYS = ("platform", "title", "chat_id", "project", "cutoff_before_text", "first_message_confirmed_by_user",
             "gaps", "left_out", "parent_revision")
MESSAGE_KEYS = {"n", "role", "text", "files", "evidence", "part", "parts"}
# Where a captured file may come from: the working folder, or the folders where the chat apps keep a chat's files.
SANDBOX_ROOTS = (Path("/mnt/data"), Path("/mnt/user-data"))
# GitHub refuses files over 100 MB, so file_chat.py refuses an archive holding one; pack.py only warns.
LARGE_FILE = 95 * 1024 * 1024


class InputProblems(Exception):
    def __init__(self, problems):
        super().__init__("\n".join(problems))
        self.problems = problems


def _whole_number(value):
    return isinstance(value, int) and not isinstance(value, bool)


def chat_id_from(value):
    """The chat's id, from the id itself or from a pasted link such as https://chatgpt.com/c/<id>."""
    if value is None:
        return None
    text = str(value).strip().split("?", 1)[0].split("#", 1)[0].rstrip("/")
    return text.rsplit("/", 1)[-1] or None


def _sentences(meta, key, problems):
    items = meta.get(key)
    if items is None:
        return []
    if not isinstance(items, list):
        problems.append(f"meta.json: {key} must be a list of sentences (an empty list when there are none)")
        return []
    cleaned = []
    for item in items:
        text = ca.one_line(item) if isinstance(item, str) else item
        problem = ca.line_problem(text, f"meta.json: an entry in {key}", ca.SENTENCE_LIMIT)
        if problem:
            problems.append(problem)
        else:
            cleaned.append(text)
    return cleaned


def load_meta(work, problems):
    path = work / "meta.json"
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append("meta.json is missing (step 6 of SKILL.md)")
        return {}
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        problems.append(f"meta.json is not valid JSON: {error}")
        return {}
    if not isinstance(meta, dict):
        problems.append("meta.json must hold one JSON object")
        return {}
    for key in META_KEYS:
        meta.setdefault(key, None)
    if meta["platform"] not in ca.PLATFORMS:
        problems.append(f"meta.json: platform must be \"chatgpt\" or \"claude\", not {meta['platform']!r}")
    title = ca.one_line(meta["title"]) if isinstance(meta["title"], str) else meta["title"]
    problem = ca.line_problem(title, "meta.json: title (the chat's title, as the user gave it)", ca.TITLE_LIMIT)
    if problem:
        problems.append(problem)
    meta["title"] = title
    meta["chat_id"] = chat_id_from(meta["chat_id"])
    if meta["chat_id"] is not None and not ca.CHAT_ID.fullmatch(meta["chat_id"]):
        problems.append("meta.json: chat_id must be the id from the chat's link (letters, digits, - and _), or null")
    for key in ("project", "parent_revision"):
        if meta[key] is not None:
            meta[key] = ca.one_line(meta[key]) if isinstance(meta[key], str) else meta[key]
            problem = ca.line_problem(meta[key], f"meta.json: {key}", ca.TITLE_LIMIT)
            if problem:
                problems.append(problem)
    if not isinstance(meta["cutoff_before_text"], str) or not meta["cutoff_before_text"].strip():
        problems.append("meta.json: cutoff_before_text must quote the user's save request")
    if not isinstance(meta["first_message_confirmed_by_user"], bool):
        problems.append("meta.json: first_message_confirmed_by_user must be true or false (step 2)")
    meta["gaps"] = _sentences(meta, "gaps", problems)
    meta["left_out"] = _sentences(meta, "left_out", problems)
    return meta


def _join_parts(n, entries, problems):
    """A long message written in pieces: every piece carries part (1, 2, …) and parts (the total)."""
    pieces = {}
    total = None
    for line, record in entries:
        part, parts = record.get("part"), record.get("parts")
        if not _whole_number(part) or not _whole_number(parts) or not 1 <= part <= parts:
            problems.append(f"messages.jsonl line {line}: message {n} appears more than once; split a long message "
                            "with \"part\" and \"parts\" on every piece, or give each message its own n")
            return None
        if total is None:
            total = parts
        if parts != total or part in pieces:
            problems.append(f"messages.jsonl line {line}: message {n} has inconsistent or repeated parts")
            return None
        pieces[part] = record
    if sorted(pieces) != list(range(1, total + 1)):
        absent = sorted(set(range(1, total + 1)) - set(pieces))
        problems.append(f"message {n}: part(s) {absent} of {total} are missing")
        return None
    first = pieces[1]
    for key in ("role", "files", "evidence"):
        if any(pieces[p].get(key, first.get(key)) != first.get(key) for p in pieces):
            problems.append(f"message {n}: every part must have the same {key}")
            return None
    texts = [pieces[p].get("text") for p in range(1, total + 1)]
    if not all(isinstance(t, str) for t in texts):
        problems.append(f"message {n}: every part needs its text")
        return None
    joined = dict(first)
    joined["text"] = "".join(texts)
    return joined


def load_messages(work, problems, notes):
    path = work / "messages.jsonl"
    try:
        lines = path.read_text(encoding="utf-8").split("\n")  # never splitlines(): it splits on U+2028 too
    except FileNotFoundError:
        problems.append("messages.jsonl is missing (step 3 of SKILL.md)")
        return []
    except UnicodeDecodeError:
        problems.append("messages.jsonl is not UTF-8")
        return []
    groups = {}
    ignored = set()
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            problems.append(f"messages.jsonl line {line_number} is not valid JSON ({error.msg}); write each line "
                            "with json.dumps")
            continue
        if not isinstance(record, dict):
            problems.append(f"messages.jsonl line {line_number} must be one JSON object")
            continue
        n = record.get("n")
        if not _whole_number(n) or n < 1:
            problems.append(f"messages.jsonl line {line_number}: n must be a whole number from 1")
            continue
        ignored |= set(record) - MESSAGE_KEYS
        groups.setdefault(n, []).append((line_number, record))
    if ignored:
        notes.append(f"ignored unknown keys in messages.jsonl: {', '.join(sorted(ignored))}")
    messages = []
    for n in sorted(groups):
        entries = groups[n]
        if len(entries) == 1 and "part" not in entries[0][1]:
            record = entries[0][1]
        else:
            record = _join_parts(n, entries, problems)
            if record is None:
                continue
        message = {
            "n": n,
            "role": record.get("role"),
            "text": record.get("text"),
            "files": record.get("files", []),
            "evidence": record.get("evidence", "model_copy"),
        }
        if message["role"] not in ca.ROLES:
            problems.append(f"message {n}: role must be one of {', '.join(ca.ROLES)}, not {message['role']!r}")
        if not isinstance(message["text"], str):
            problems.append(f"message {n}: text must be a string (\"\" for an image-only turn)")
        else:
            try:
                message["text"].encode("utf-8")
            except UnicodeEncodeError:
                problems.append(f"message {n}: text holds a broken Unicode character (a lone surrogate); copy it again")
        if not isinstance(message["files"], list) or not all(isinstance(f, str) for f in message["files"]):
            problems.append(f"message {n}: files must be a list of file ids such as [\"f000001\"]")
        elif len(set(message["files"])) != len(message["files"]):
            problems.append(f"message {n}: lists the same file id twice")
        if message["evidence"] != "model_copy":
            problems.append(f"message {n}: evidence must be \"model_copy\": a chat re-types what it sees, so it can "
                            "never claim an exact copy")
        messages.append(message)
    numbers = [m["n"] for m in messages]
    if not messages and not problems:
        problems.append("messages.jsonl has no messages")
    elif numbers and numbers != list(range(1, len(numbers) + 1)):
        expected = next(i for i, n in enumerate(numbers, 1) if n != i)
        problems.append(f"message numbering must run 1, 2, 3… with no gaps; message {expected} is missing")
    return messages


def _inside_allowed_roots(path, work):
    real = path.resolve()
    for root in (work, *SANDBOX_ROOTS):
        try:
            real.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def load_files(work, messages, problems):
    path = work / "files.json"
    if not path.exists():
        listed = sorted({fid for m in messages for fid in m.get("files", []) if isinstance(fid, str)})
        if listed:
            problems.append(f"files.json is missing, but messages list {', '.join(listed)} (step 4 of SKILL.md)")
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        problems.append(f"files.json is not valid JSON: {error}")
        return []
    if not isinstance(data, list):
        problems.append("files.json must hold a list of file entries")
        return []
    count = len(messages)
    entries, seen = [], set()
    for index, entry in enumerate(data, 1):
        where = f"files.json entry {index}"
        if not isinstance(entry, dict):
            problems.append(f"{where} must be an object")
            continue
        fid = entry.get("file_id")
        if not isinstance(fid, str) or not ca.FILE_ID.fullmatch(fid):
            problems.append(f"{where}: file_id must look like f000001")
            continue
        if fid in seen:
            problems.append(f"{where}: {fid} is used twice; each occurrence gets its own id")
            continue
        seen.add(fid)
        kind = entry.get("kind")
        name = ca.one_line(entry["name"]) if isinstance(entry.get("name"), str) else entry.get("name")
        if kind not in ca.KINDS:
            problems.append(f"{fid}: kind must be one of {', '.join(ca.KINDS)}")
        problem = ca.line_problem(name, f"{fid}: name (the file's name as shown in the chat)", ca.NAME_LIMIT)
        if problem:
            problems.append(problem)
        message = entry.get("message")
        if message is not None:
            if not _whole_number(message) or not 1 <= message <= count:
                problems.append(f"{fid}: message must be the number of the message it appears in (1–{count}), "
                                "or null for a file not tied to a message")
            elif fid not in messages[message - 1].get("files", []):
                problems.append(f"{fid} says message {message}, but that message's files do not list it; add it there")
        status = entry.get("status")
        record = {"file_id": fid, "kind": kind, "name": name, "message": message, "status": status}
        if status == "captured":
            source = entry.get("source")
            bytes_from = entry.get("bytes_from", "chat_files")
            if bytes_from not in ("chat_files", "model_copy"):
                problems.append(f"{fid}: bytes_from must be \"chat_files\" (a real file) or \"model_copy\" (text you "
                                "wrote out, such as a canvas or an artifact)")
            source_path = Path(source) if isinstance(source, str) and source.strip() else None
            if source_path is not None and not source_path.is_absolute():
                source_path = work / source_path
            if source_path is None or not source_path.is_file() or source_path.is_symlink():
                problems.append(f"{fid}: status is captured, but source {source!r} is not a file; give the path to the "
                                "real bytes, or mark it missing")
            elif not _inside_allowed_roots(source_path, work):
                problems.append(f"{fid}: source {source!r} is outside the working folder and the chat's file folders "
                                "(/mnt/data, /mnt/user-data); copy the file into the working folder first")
            else:
                record["bytes"] = source_path.read_bytes()
                record["bytes_from"] = bytes_from
        elif status == "missing":
            suffix = Path(name).suffix if isinstance(name, str) else ""
            defaults = {
                "missing_reason": "not reachable from the chat",
                "how_to_get": (f"Download it from message {message} and name it {fid}{suffix}" if message is not None
                               else f"Download it from the chat or project and name it {fid}{suffix}"),
            }
            for key, default in defaults.items():
                value = entry.get(key)
                value = ca.one_line(value) if isinstance(value, str) and value.strip() else default
                problem = ca.line_problem(value, f"{fid}: {key}", ca.SENTENCE_LIMIT)
                if problem:
                    problems.append(problem)
                record[key] = value
        else:
            problems.append(f"{fid}: status must be \"captured\" or \"missing\"")
        entries.append(record)
    for message in messages:
        for fid in message.get("files", []) if isinstance(message.get("files"), list) else []:
            if fid not in seen:
                problems.append(f"message {message['n']} lists {fid}, which files.json does not have")
            else:
                placed = next(e for e in entries if e["file_id"] == fid)["message"]
                if placed != message["n"]:
                    problems.append(f"message {message['n']} lists {fid}, but files.json places it at message {placed}")
    return entries


def build(work, now):
    """Return (members, manifest, notes) or raise InputProblems."""
    problems, notes = [], []
    meta = load_meta(work, problems)
    messages = load_messages(work, problems, notes)
    files_in = load_files(work, messages, problems) if not problems else []
    try:
        brief = (work / "brief.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        brief = ""
        problems.append("brief.md is missing (step 5 of SKILL.md)")
    except UnicodeDecodeError:
        brief = ""
        problems.append("brief.md is not UTF-8")
    if not problems and not brief.strip():
        problems.append("brief.md is empty (step 5 of SKILL.md)")
    if problems:
        raise InputProblems(problems)

    members, files = {}, []
    for entry in files_in:
        record = {key: entry[key] for key in ("file_id", "kind", "name", "message", "status")}
        if entry["status"] == "captured":
            data = entry["bytes"]
            path = f"files/{entry['file_id']}-{ca.safe_name(entry['name'])}"
            members[path] = data
            record.update({"path": path, "size": len(data), "sha256": ca.sha256(data),
                           "bytes_from": entry["bytes_from"]})
            if len(data) > LARGE_FILE:
                notes.append(f"{entry['file_id']} is {len(data) // (1024 * 1024)} MB; GitHub refuses files over "
                             "100 MB, so file-chat will refuse this archive; keep the ZIP somewhere safe")
        else:
            record.update({"path": None, "size": None, "sha256": None, "bytes_from": None,
                           "missing_reason": entry["missing_reason"], "how_to_get": entry["how_to_get"]})
        files.append(record)

    missing = sum(1 for f in files if f["status"] == "missing")
    coverage = {
        "status": ca.coverage_status(meta["first_message_confirmed_by_user"], meta["gaps"], missing),
        "messages": len(messages),
        "first_message_confirmed_by_user": meta["first_message_confirmed_by_user"],
        "evidence": {e: sum(1 for m in messages if m["evidence"] == e) for e in ca.EVIDENCE},
        "files_captured": len(files) - missing,
        "files_missing": missing,
        "gaps": list(meta["gaps"]),
        "left_out": list(meta["left_out"]),
    }
    source = {"platform": meta["platform"], "title": meta["title"], "chat_id": meta["chat_id"],
              "project": meta["project"]}
    digest = ca.content_hash(source, messages, files, coverage)
    manifest = {
        "schema_version": ca.SCHEMA,
        "format": "chat-save",
        "revision": now.strftime("%Y%m%dT%H%M%SZ") + "-" + digest[:12],
        "content_sha256": digest,
        "parent_revision": meta["parent_revision"],
        "created_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "cutoff": {"before_text": meta["cutoff_before_text"],
                   "excluded": "the save request and everything after it"},
        "coverage": coverage,
        "messages": {"path": "transcript.jsonl", "view": "transcript.md", "count": len(messages)},
        "files": files,
        "restore_checks": list(ca.RESTORE_CHECKS),
    }
    members["manifest.json"] = ca.manifest_bytes(manifest)
    members["transcript.jsonl"] = ca.transcript_jsonl(messages)
    members["transcript.md"] = ca.render_transcript_md(manifest, messages)
    members["brief.md"] = (brief.rstrip("\n") + "\n").encode("utf-8")
    members["START-HERE.md"] = ca.render_start_here(manifest, messages, members["brief.md"])
    members[ca.CHECKSUMS] = ca.checksums_text(members)
    return members, manifest, notes


def write_zip(path, members):
    """Same members in, same bytes out: sorted names, a fixed date, regular-file permissions."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, members[name])


def summary(manifest, zip_path, zip_digest, members, notes):
    coverage = manifest["coverage"]
    source = manifest["source"]
    confirmed = "yes" if coverage["first_message_confirmed_by_user"] else "no"
    lines = [
        "chat-save: archive built and verified",
        f"  chat      {source['title']} ({ca.PLATFORMS[source['platform']]})",
        f"  revision  {manifest['revision']}",
        f"  status    {coverage['status'].upper()}",
        f"  messages  {coverage['messages']} (model copy); first message confirmed by you: {confirmed}",
        f"  files     {coverage['files_captured']} captured, {coverage['files_missing']} missing",
    ]
    for entry in manifest["files"]:
        if entry["status"] == "missing":
            lines.append(f"            {entry['file_id']} {entry['name']}: {entry['missing_reason']}. "
                         f"{entry['how_to_get']}.")
    lines += [f"  gap       {gap}" for gap in coverage["gaps"]]
    lines += [f"  left out  {item}" for item in coverage["left_out"]]
    lines += [
        f"  package   verified: {len(members)} members, every SHA-256 checked after reopening the ZIP",
        f"  zip       {zip_path}",
        f"  sha256    {zip_digest}",
        "  restore   not tested yet",
    ]
    lines += [f"  note      {n}" for n in notes]
    lines.append("next: download the ZIP, then move it into ~/chat-backups/inbox (create it once: mkdir -p "
                 "~/chat-backups/inbox). If I listed files to download, or you saved the chat page, make a folder "
                 "there and put the ZIP and those files in it. Then on your Mac run `python3 file_chat.py --inbox` "
                 "from the folder that holds file_chat.py.")
    return "\n".join(lines)


def main(argv):
    parser = argparse.ArgumentParser(description="Build and verify a chat-save archive.")
    parser.add_argument("work", type=Path, help="the working folder with meta.json, messages.jsonl, files.json, brief.md")
    parser.add_argument("--out", type=Path, help="where to write the ZIP (default: the working folder's parent)")
    parser.add_argument("--now", help=argparse.SUPPRESS)  # tests pin the clock: YYYYMMDDTHHMMSSZ
    args = parser.parse_args(argv[1:])
    work = args.work.resolve()
    if not work.is_dir():
        print(f"chat-save: {work} is not a folder")
        return 2
    now = (datetime.datetime.strptime(args.now, "%Y%m%dT%H%M%SZ") if args.now
           else datetime.datetime.now(datetime.timezone.utc))
    try:
        members, manifest, notes = build(work, now)
    except InputProblems as error:
        print("chat-save: the working files have problems; fix them and run pack.py again:")
        for problem in error.problems:
            print(f"  - {problem}")
        return 1
    out = (args.out or work.parent).resolve()
    out.mkdir(parents=True, exist_ok=True)
    suffix = "-partial" if manifest["coverage"]["status"] == "partial" else ""
    zip_path = out / (f"chat-save-{manifest['source']['platform']}-{ca.slugify(manifest['source']['title'])}-"
                      f"{manifest['revision']}{suffix}.zip")
    write_zip(zip_path, members)
    reread, read_problems, _ = ca.read_zip(zip_path)
    report = ca.verify(reread) if not read_problems else {"problems": read_problems}
    if report["problems"] or reread != members:
        zip_path.unlink(missing_ok=True)
        print("chat-save: the ZIP failed its check after reopening, so it was deleted:")
        for problem in report["problems"] or ["the reopened ZIP differs from what was written"]:
            print(f"  - {problem}")
        return 1
    print(summary(manifest, zip_path, ca.sha256(zip_path.read_bytes()), members, notes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
