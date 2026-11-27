"""File a chat-save archive into its private GitHub backup repo, from the Mac.

Usage:
  python3 file_chat.py ZIP [DOWNLOADED_FILE ...] [--raw PATH ...] [--repo PATH] [--direct]
                       [--dry-run] [--no-remote-check]
  python3 file_chat.py --inbox [DIR] [--direct] [--dry-run] [--no-remote-check]

The chat hands over a ZIP and this script files it.
In order; every step before the push stops the run with GitHub unchanged:
  1. Reads the ZIP and verifies every byte (chatarchive.verify). A failing archive is never filed, nor one holding a
     file GitHub would refuse (over 100 MB) or a name git treats specially (.git, .gitattributes, .gitmodules,
     .gitignore).
  2. Adds files you downloaded by hand: each name starts with the file id the save listed as missing
     (f000002.png, f000002-sketch.png). Their bytes are hashed; the manifest, the views and the checksums are rebuilt
     and verified again.
  3. Adds --raw material (a saved web page: the .html file and its _files folder) under raw/, byte for byte, leaving
     out Finder's .DS_Store files.
  4. Picks the repo: --repo, else $CHAT_SAVE_REPO_CHATGPT or $CHAT_SAVE_REPO_CLAUDE, else
     <the folder holding this repo's checkout>/<platform>-chat-history. It must have no commit hooks, its origin
     must be a GitHub repo, and gh must confirm that repo is private.
  5. Picks the folder: chats/<title-slug>--<key>/<revision>/, reusing the chat's folder from an earlier save. The
     same save filed again is a no-op, after the filed copy is verified from the fetched objects; the same save with
     missing files now added updates its folder.
  6. Writes the folder to a temporary directory and reads it back, so nothing that would not survive a checkout is
     pushed. Then builds one commit in a temporary git index, without touching your checkout: the revision folder,
     plus the chat's README.md the first time.
  7. Pushes it: to the branch chat-save/<slug>-<revision> with a pull request (the default), or straight to the
     default branch (--direct). A re-run reuses that branch and never takes anything away from it: nothing is
     pushed when it already holds this save with as many files or more, and otherwise the new commit goes on top of
     it, as a fast-forward.
  8. Checks GitHub: the branch must point at the commit, and a fresh sparse clone of just that folder must pass
     verification with the same bytes. A failure here says PUSHED, because GitHub already holds the commit.
Exit 0: filed, or already filed. 1: refused or failed, with the reason. 2: wrong usage.

--inbox files a folder of saves, each by the steps above (the same code), one pull request per save. DIR defaults to
~/chat-backups/inbox and must exist (a missing inbox is refused with the mkdir command; it is never created). The
folder must be named inbox and sit inside a folder that is not your home folder or the disk root, because filed/ and
the lock live beside it; a folder that is your home folder or the disk root is refused as too broad. Items are
processed in name order:
  - a *.zip at the top level is one save;
  - a folder at the top level is one chat: exactly one ZIP, files whose names start with a file id (f000002.png), and
    optionally a saved web page (X.html, filed as --raw, or X.html with its X_files folder; an X_files folder needs
    its X.html). Anything else in it refuses that folder and names the file; symbolic links are refused;
  - *.crdownload, *.download and *.part (a download in progress), at the top level or in a chat folder, skip that
    item;
  - any other file, a hidden item or a symbolic link is "left alone", and .DS_Store is ignored.
Suffixes match in any letter case. A save that is filed (or already filed) is moved, never deleted or overwritten, to
filed/ beside the inbox (a name clash gets " (2)", " (3)", ...). A partial save (files still missing) is filed but
stays in the inbox: a top-level ZIP moves into a new folder inbox/<zip name>/ (inbox/<zip name> (2)/ if that exists),
a chat folder stays; add the missing downloads there and run again. A refusal or failure in one item is reported and
the batch goes on; a summary line per item is printed at the end, even after an unexpected error. --direct and
--no-remote-check apply to every save. --dry-run writes nothing at all (no move, no folder, no lock file) and says what
it would do. --inbox cannot be combined with a ZIP, downloads, --raw or --repo (each platform's repo comes from the
environment variables or the default folder). One run at a time: a lock file .file-chat-inbox.lock beside the inbox
holds the PID of the run; a lock whose process is gone is replaced, a live one refuses the run.
Exit 0: every save filed, partial or already filed; skipped and left-alone items do not fail the run; also an empty
inbox, and a dry run that planned without a refusal. 1: any item refused or failed, or the inbox missing, not a
folder, not named inbox, too broad or locked. 2: wrong usage.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "chat-restore" / "scripts"))
import chatarchive as ca  # noqa: E402  (imported after the path insert, so it works with python3 -I too)

MAX_FILE_BYTES = 95 * 1024 * 1024  # GitHub refuses files over 100 MB
TIMEOUT = 600
COMMIT_HOOKS = ("pre-commit", "prepare-commit-msg", "commit-msg", "post-commit")
GIT_SPECIAL = {".git", ".gitattributes", ".gitmodules", ".gitignore"}
CREDENTIALS_IN_URL = re.compile(r"(\w+://)[^/@\s]+@")
IN_PROGRESS = (".crdownload", ".download", ".part")
FILE_ID = re.compile(r"f\d{6}(?:[-._ ].*)?$")
LOCK_NAME = ".file-chat-inbox.lock"
DEFAULT_INBOX = Path("~/chat-backups/inbox")
GITHUB_URL = re.compile(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/\s]+)/([^/\s]+?)"
                        r"(?:\.git)?/?$")


class Refusal(Exception):
    pass


def scrub(text):
    """Never echo a credential that a remote URL might carry."""
    return CREDENTIALS_IN_URL.sub(r"\1***@", text)


def run(args, cwd=None, env=None, data=None):
    try:
        done = subprocess.run(args, cwd=cwd, env=env, input=data, capture_output=True, timeout=TIMEOUT)
    except FileNotFoundError:
        raise Refusal(f"{args[0]} is not installed") from None
    except subprocess.TimeoutExpired:
        raise Refusal(f"{args[0]} {args[1] if len(args) > 1 else ''} took longer than {TIMEOUT} s and was stopped") \
            from None
    if done.returncode != 0:
        message = scrub(done.stderr.decode("utf-8", "replace").strip() or done.stdout.decode("utf-8", "replace"))
        shown = " ".join(a for a in args[:4] if not a.startswith(("http", "file:", "git@", "ssh:")))
        raise Refusal(f"`{shown}` failed: {message[:800]}")
    return done.stdout


def git(repo, *args, env=None, data=None):
    return run(["git", "-C", str(repo), *args], env=env, data=data)


def bullets(items):
    return "\n".join(f"  - {item}" for item in items)


def git_special(name):
    return any(part.lower().rstrip(". ") in GIT_SPECIAL for part in name.split("/"))


# ── 1–3: the archive ──────────────────────────────────────────────────────────────────────────────────────────────

def check_fileable(members):
    for name, data in sorted(members.items()):
        if len(data) > MAX_FILE_BYTES:
            raise Refusal(f"{name} is {len(data) // (1024 * 1024)} MB; GitHub refuses files over 100 MB, so this save "
                          "cannot be filed as is. Keep the ZIP somewhere safe")
        if git_special(name):
            raise Refusal(f"{name}: git treats this name specially, so file-chat will not commit it")


def load_archive(zip_path):
    members, problems, _ = ca.read_archive(zip_path)
    if problems:
        raise Refusal("the archive cannot be read, so nothing was filed:\n" + bullets(problems))
    report = ca.verify(members)
    if report["problems"]:
        raise Refusal("the archive failed verification, so nothing was filed:\n" + bullets(report["problems"]))
    if report["layout"] != "chat-save format 2":
        raise Refusal(f"file-chat files chat-save format 2 archives only; this one is: {report['layout']}")
    check_fileable(members)
    return members, json.loads(members["manifest.json"].decode("utf-8"))


def bind_downloads(members, manifest, paths):
    files = {entry["file_id"]: entry for entry in manifest["files"]}
    bound = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        match = re.match(r"(f\d{6})(?:[-._ ].*)?$", path.name)
        if not match:
            raise Refusal(f"{path.name}: a downloaded file's name must start with the file id the save listed as "
                          "missing (for example f000002.png); pass a saved web page with --raw")
        fid = match.group(1)
        entry = files.get(fid)
        if entry is None:
            raise Refusal(f"{path.name}: this save has no file {fid}")
        if fid in bound:
            raise Refusal(f"{fid} was given twice")
        if entry["status"] != "missing":
            raise Refusal(f"{path.name}: {fid} was already captured in the chat, so there is nothing to add")
        if path.is_symlink() or not path.is_file():
            raise Refusal(f"{path}: not a regular file")
        data = path.read_bytes()
        member = f"files/{fid}-{ca.safe_name(entry['name'])}"
        members[member] = data
        entry.update({"status": "captured", "path": member, "size": len(data), "sha256": ca.sha256(data),
                      "bytes_from": "user_download"})
        entry.pop("missing_reason", None)
        entry.pop("how_to_get", None)
        bound.append(fid)
    return bound


def add_raw(members, manifest, paths):
    added, skipped = [], []
    listed = manifest.setdefault("raw", [])
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        name = unicodedata.normalize("NFC", path.name)  # git on a Mac stores paths composed (NFC)
        name = name if not ca.member_name_problem(name) else ca.safe_name(name)
        base = f"raw/{name}"
        if any(m == base or m.startswith(base + "/") for m in members):
            raise Refusal(f"{base} is already in the archive")
        if path.is_symlink():
            raise Refusal(f"{path}: symbolic links are not copied")
        if path.is_file():
            items = [(base, path)]
        elif path.is_dir():
            items = []
            for item in sorted(path.rglob("*")):
                relative = unicodedata.normalize("NFC", item.relative_to(path).as_posix())
                if item.name in ca.IGNORED_NAMES or relative.startswith("__MACOSX"):
                    if item.is_file():
                        skipped.append(f"{base}/{relative}")
                    continue
                if item.is_symlink():
                    raise Refusal(f"{item}: symbolic links are not copied")
                if item.is_file():
                    items.append((f"{base}/{relative}", item))
        else:
            raise Refusal(f"{path}: no such file or folder")
        for member, item in items:
            problem = ca.member_name_problem(member)
            if problem:
                raise Refusal(f"{item}: its path {problem}")
            members[member] = item.read_bytes()
        listed.append({"path": base, "added_by": "user", "note": "added on the Mac with --raw"})
        added.append(base)
    if not listed:
        manifest.pop("raw")
    return added, skipped


def rebuild(members, manifest):
    """After adding files or raw material: recount, re-render, re-hash and verify again."""
    messages = [json.loads(line) for line in ca.text_lines(members["transcript.jsonl"])]
    coverage = manifest["coverage"]
    missing = sum(1 for f in manifest["files"] if f["status"] == "missing")
    coverage["files_missing"] = missing
    coverage["files_captured"] = len(manifest["files"]) - missing
    coverage["status"] = ca.coverage_status(coverage["first_message_confirmed_by_user"] is True,
                                            coverage.get("gaps"), missing)
    manifest["content_sha256"] = ca.content_hash(manifest["source"], messages, manifest["files"], coverage,
                                                 ca.raw_digests(members))
    members["manifest.json"] = ca.manifest_bytes(manifest)
    members["transcript.md"] = ca.render_transcript_md(manifest, messages)
    members["START-HERE.md"] = ca.render_start_here(manifest, messages, members["brief.md"])
    members[ca.CHECKSUMS] = ca.checksums_text(members)
    report = ca.verify(members)
    if report["problems"]:
        raise Refusal("after adding files the archive no longer verifies; nothing was filed:\n"
                      + bullets(report["problems"]))
    check_fileable(members)


def roundtrip_check(members):
    """Write the folder out and read it back the way a checkout will be read, before anything is pushed."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, data in members.items():
            target = Path(tmp, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        back, problems, _ = ca.read_folder(tmp)
    if problems or back != members:
        differing = sorted(set(back) ^ set(members)) or sorted(n for n in members if back.get(n) != members[n])
        raise Refusal("the save would not read back the same from a checkout, so nothing was pushed:\n"
                      + bullets(problems or [f"differs: {name}" for name in differing[:10]]))


# ── 4–5: the repo and the folder ──────────────────────────────────────────────────────────────────────────────────

def checkout_parent():
    """The folder that holds this repo's main checkout (a worktree resolves to its main checkout)."""
    try:
        common = Path(git(HERE, "rev-parse", "--path-format=absolute", "--git-common-dir").decode().strip())
        return common.parent.parent
    except Refusal:
        return HERE.parents[2]


def resolve_repo(arg, platform):
    if arg:
        repo = Path(arg).expanduser()
    elif os.environ.get(f"CHAT_SAVE_REPO_{platform.upper()}"):
        repo = Path(os.environ[f"CHAT_SAVE_REPO_{platform.upper()}"]).expanduser()
    else:
        repo = checkout_parent() / f"{platform}-chat-history"
    if not (repo / ".git").exists():
        raise Refusal(f"{repo} is not a clone of your {ca.PLATFORMS[platform]} backup repo; clone it there or pass "
                      "--repo")
    return repo.resolve()


def check_repo(repo):
    """Return (url, slug, default_branch, base) after refusing anything that would send the save the wrong way."""
    hooks_dir = Path(git(repo, "rev-parse", "--git-path", "hooks").decode().strip())
    if not hooks_dir.is_absolute():
        hooks_dir = repo / hooks_dir
    active = [hook for hook in COMMIT_HOOKS if (hooks_dir / hook).is_file()]
    if active:
        raise Refusal(f"{repo} has commit hooks ({', '.join(active)}). file-chat writes its commit without running "
                      "them, so it stops here rather than skip them; file this save by hand or remove the hooks")
    url = git(repo, "config", "--get", "remote.origin.url").decode().strip()
    match = GITHUB_URL.match(url)
    if not match:
        raise Refusal(f"{repo}'s origin ({scrub(url)}) is not a GitHub repo; file-chat only files into a private "
                      "GitHub repo")
    slug = f"{match.group(1)}/{match.group(2)}"
    push_url = subprocess.run(["git", "-C", str(repo), "config", "--get", "remote.origin.pushurl"],
                              capture_output=True, text=True, timeout=TIMEOUT).stdout.strip()
    if push_url and push_url != url:
        raise Refusal(f"{repo}'s origin pushes to a different address than it fetches from; file-chat only files when "
                      "both are the same private GitHub repo")
    try:
        info = json.loads(run(["gh", "repo", "view", slug, "--json", "isPrivate,nameWithOwner"]).decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        info = {}
    if info.get("isPrivate") is not True:
        raise Refusal(f"{slug} is not confirmed private by GitHub, so nothing was filed; file-chat only files into a "
                      "private repo")
    git(repo, "fetch", "--quiet", "origin")
    head = git(repo, "ls-remote", "--symref", "origin", "HEAD").decode()
    branch_match = re.search(r"ref: refs/heads/(\S+)\s+HEAD", head)
    if not branch_match:
        raise Refusal(f"cannot tell {slug}'s default branch; a new repo needs one commit first (GitHub's "
                      "\"Add a README\" does it)")
    branch = branch_match.group(1)
    base = git(repo, "rev-parse", f"refs/remotes/origin/{branch}").decode().strip()
    return url, info.get("nameWithOwner", slug), branch, base


def read_tree_manifests(repo, base):
    names = [n for n in git(repo, "ls-tree", "-r", "-z", "--name-only", base, "--", "chats").decode("utf-8")
             .split("\0") if n]
    found = {}
    for name in names:
        parts = name.split("/")
        if len(parts) == 4 and parts[3] == "manifest.json":
            try:
                found[(parts[1], parts[2])] = json.loads(git(repo, "show", f"{base}:{name}").decode("utf-8"))
            except (Refusal, json.JSONDecodeError, UnicodeDecodeError):
                continue
    return found


def same_chat(a, b):
    if a.get("platform") != b.get("platform"):
        return False
    if a.get("chat_id") or b.get("chat_id"):
        return a.get("chat_id") == b.get("chat_id")
    return a.get("title") == b.get("title")


def compare_saves(old, old_jsonl, new, new_jsonl):
    """How a filed save relates to this run's archive with the same revision id:
    "completion" (this run adds files), "covered" (the filed copy already has as much or more) or "different"."""
    if old_jsonl != new_jsonl:
        return "different", "its messages differ"
    old_files = {f["file_id"]: f for f in old.get("files", [])}
    new_files = {f["file_id"]: f for f in new["files"]}
    if old_files.keys() != new_files.keys():
        return "different", "its list of files differs"
    old_more, new_more = [], []
    for fid, before in old_files.items():
        after = new_files[fid]
        if before["status"] == "captured" and after["status"] == "captured":
            if before.get("sha256") != after.get("sha256"):
                return "different", f"{fid} has different bytes"
        elif before["status"] == "captured":
            old_more.append(fid)
        elif after["status"] == "captured":
            new_more.append(fid)
    old_raw = {item.get("path") for item in old.get("raw", [])}
    new_raw = {item.get("path") for item in new.get("raw", [])}
    old_more += sorted(old_raw - new_raw)
    new_more += sorted(new_raw - old_raw)
    if old_more and new_more:
        return "different", (f"the filed copy has {', '.join(old_more)}, which this run lacks; pass every download "
                             "and --raw item together")
    return ("completion", "") if new_more else ("covered", "")


def place(repo, base, manifest, members):
    """Return (chat_folder, plan, filed): plan is "new", "update", or a sentence saying it is already filed, and
    filed is then that folder's path, so the caller can check the filed copy."""
    existing = read_tree_manifests(repo, base)
    source, revision = manifest["source"], manifest["revision"]
    folders = sorted({folder for (folder, _), m in existing.items() if same_chat(m.get("source", {}), source)})
    if folders:
        folder = folders[0]
    else:
        key = ca.sha256(f"{source['platform']}:{source.get('chat_id') or source['title']}".encode())[:6]
        folder = f"{ca.slugify(source['title'])}--{key}"
    for (other_folder, other_revision), other in existing.items():
        if other_folder == folder and other.get("content_sha256") == manifest["content_sha256"]:
            return (folder, f"already filed as chats/{folder}/{other_revision}/ (identical content)",
                    f"chats/{folder}/{other_revision}")
    if (folder, revision) in existing:
        old_jsonl = git(repo, "show", f"{base}:chats/{folder}/{revision}/transcript.jsonl")
        relation, why = compare_saves(existing[(folder, revision)], old_jsonl, manifest, members["transcript.jsonl"])
        if relation == "completion":
            return folder, "update", None
        if relation == "covered":
            return (folder, f"already filed as chats/{folder}/{revision}/ (the filed copy has as many files or more)",
                    f"chats/{folder}/{revision}")
        raise Refusal(f"chats/{folder}/{revision}/ already holds a different archive with this revision id ({why}); "
                      "a filed save is never overwritten")
    return folder, "new", None


def check_filed(repo, commit, folder_path):
    """Verify a copy already filed, from the objects git fetched, so "already filed" is never taken on trust."""
    names = [n for n in git(repo, "ls-tree", "-r", "-z", "--name-only", commit, "--", folder_path).decode("utf-8")
             .split("\0") if n]
    members = {name[len(folder_path) + 1:]: git(repo, "cat-file", "blob", f"{commit}:{name}") for name in names}
    report = ca.verify(members)
    if report["problems"]:
        raise Refusal(f"{folder_path}/ is filed, but the filed copy does NOT verify, so do not trust it:\n"
                      + bullets(report["problems"]))
    return members


def chat_readme(source):
    """chats/<folder>/README.md, written once with the chat's first save and never changed, so it cannot conflict."""
    platform = ca.PLATFORMS.get(source["platform"], source["platform"])
    return (f"# {ca.md_escape(source['title'])}\n\n{platform} chat, saved with chat-save. Each folder here is one save, "
            "named by when it was packed (UTC), so the newest sorts last. To continue the chat, open the newest "
            "save's START-HERE.md.\n").encode("utf-8")


def tree_has(repo, commit, path):
    return subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit}:{path}"], capture_output=True,
                          timeout=TIMEOUT).returncode == 0


# ── 6–8: commit, push, check ──────────────────────────────────────────────────────────────────────────────────────

def build_tree(repo, base, writes, removes):
    """The tree of base plus the writes, built in a temporary index: the checkout and its index are never touched."""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        git(repo, "read-tree", base, env=env)
        for path in removes:
            git(repo, "update-index", "--force-remove", "--", path, env=env)
        for path, data in sorted(writes.items()):
            blob = git(repo, "hash-object", "-w", "--stdin", data=data).decode().strip()
            git(repo, "update-index", "--add", "--cacheinfo", "100644", blob, path, env=env)
        return git(repo, "write-tree", env=env).decode().strip()


def remote_tip(repo, branch):
    found = git(repo, "ls-remote", "origin", f"refs/heads/{branch}").decode().split()
    return found[0] if found else None


def open_pull_request(repo, slug, base_branch, branch, title, body):
    found = run(["gh", "pr", "list", "--repo", slug, "--head", branch, "--state", "open", "--json", "url",
                 "--jq", ".[0].url // empty"], cwd=repo).decode().strip()
    if found:
        return found
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
        handle.write(body)
        body_path = handle.name
    try:
        output = run(["gh", "pr", "create", "--repo", slug, "--base", base_branch, "--head", branch, "--title", title,
                      "--body-file", body_path], cwd=repo).decode().strip()
    finally:
        os.unlink(body_path)
    return output.splitlines()[-1] if output else "(gh printed no address)"


def remote_check(repo, url, branch, commit, folder_path, expected):
    tip = remote_tip(repo, branch)
    if tip != commit:
        raise Refusal(f"GitHub's {branch} does not point at the commit {commit[:12]}")
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "check"
        try:
            run(["git", "clone", "--quiet", "--depth", "1", "--branch", branch, "--filter=blob:none", "--no-checkout",
                 url, str(clone)])
            git(clone, "sparse-checkout", "set", "--no-cone", f"/{folder_path}/")
            git(clone, "checkout", "--quiet", branch)
        except Refusal:
            shutil.rmtree(clone, ignore_errors=True)  # a server without partial clone: take the whole branch
            run(["git", "clone", "--quiet", "--depth", "1", "--branch", branch, url, str(clone)])
        members, problems, _ = ca.read_folder(clone / folder_path)
        report = ca.verify(members) if not problems else {"problems": problems}
        if report["problems"]:
            raise Refusal("the copy fetched back from GitHub does not verify:\n" + bullets(report["problems"]))
        if members != expected:
            raise Refusal("the copy fetched back from GitHub differs from what was filed")
    return len(members)


def update_checkout(repo, branch):
    """After a direct push, bring a clean checkout of the default branch up to date; otherwise leave it alone."""
    try:
        clean = not git(repo, "status", "--porcelain").strip()
        on_branch = subprocess.run(["git", "-C", str(repo), "symbolic-ref", "--quiet", "--short", "HEAD"],
                                   capture_output=True, text=True, timeout=TIMEOUT).stdout.strip() == branch
        if clean and on_branch:
            git(repo, "fetch", "--quiet", "origin")
            git(repo, "merge", "--quiet", "--ff-only", f"refs/remotes/origin/{branch}")
            return None
    except Refusal:
        pass
    return f"your checkout of {repo} was left as it is; pull {branch} when convenient"


def missing_ids(manifest):
    return [entry["file_id"] for entry in manifest["files"] if entry["status"] == "missing"]


def file_one(zip_path, downloads, raw_paths, repo_arg, direct, dry_run, no_remote_check):
    """File one save and print the detailed result. Returns a namespace: outcome ("filed", "already" or "dry-run"),
    title, slug, pr_url, messages, files and missing (the file ids still missing from the filed copy).
    Raises Refusal when the save is refused or the filing fails."""
    notes = []
    members, manifest = load_archive(zip_path)
    bound = bind_downloads(members, manifest, downloads)
    raw, skipped = add_raw(members, manifest, raw_paths)
    notes += [f"left out {name} (a Finder file)" for name in skipped]
    if bound or raw:
        rebuild(members, manifest)
    source, revision = manifest["source"], manifest["revision"]
    coverage = manifest["coverage"]
    result = SimpleNamespace(outcome="filed", title=source["title"], slug=None, pr_url=None,
                             messages=coverage["messages"], files=coverage["files_captured"],
                             missing=missing_ids(manifest))
    repo = resolve_repo(repo_arg, source["platform"])
    url, slug, default_branch, base = check_repo(repo)
    result.slug = slug
    folder, plan, filed = place(repo, base, manifest, members)
    folder_path = f"chats/{folder}/{revision}"
    status = coverage["status"].upper()
    if plan not in ("new", "update"):
        filed_members = check_filed(repo, base, filed)
        print(f"file-chat: nothing to do: {source['title']} is {plan} in {slug}; the filed copy verifies "
              f"({len(filed_members)} files)")
        result.outcome = "already"
        result.missing = missing_ids(json.loads(filed_members["manifest.json"].decode("utf-8")))
        return result
    roundtrip_check(members)
    how = f"straight to {default_branch}" if direct else "by pull request"
    if dry_run:
        print(f"file-chat: dry run; would file {source['title']} ({status}) → {folder_path}/ in {slug} (private), "
              f"{len(members)} files, {plan}, {how}")
        result.outcome = "dry-run"
        return result
    writes = {f"{folder_path}/{name}": data for name, data in members.items()}
    if not tree_has(repo, base, f"chats/{folder}/README.md"):
        writes[f"chats/{folder}/README.md"] = chat_readme(source)
    removes = []
    if plan == "update":
        old = [n for n in git(repo, "ls-tree", "-r", "-z", "--name-only", base, "--", folder_path)
               .decode("utf-8").split("\0") if n]
        removes = [path for path in old if path not in writes]
    tree = build_tree(repo, base, writes, removes)
    title = f"Save {ca.PLATFORMS[source['platform']]} chat: {source['title']} ({revision})"
    if direct:
        branch, parent = default_branch, base
    else:
        branch = f"chat-save/{ca.slugify(source['title'], 32)}-{revision}"
        parent = remote_tip(repo, branch) or base
    pushed, held = True, None
    if parent != base:
        # The branch is from an earlier run: never let this run take anything away from it.
        git(repo, "fetch", "--quiet", "origin", f"refs/heads/{branch}")
        _, on_branch, filed_on_branch = place(repo, parent, manifest, members)
        if on_branch not in ("new", "update"):
            held_members = check_filed(repo, parent, filed_on_branch)  # the branch already holds as much or more
            held = len(held_members)
            result.missing = missing_ids(json.loads(held_members["manifest.json"].decode("utf-8")))
            commit, pushed = parent, False
        elif git(repo, "rev-parse", f"{parent}^{{tree}}").decode().strip() == tree:
            commit, pushed = parent, False  # this exact folder is already on the branch from an earlier run
    if pushed:
        commit = git(repo, "commit-tree", tree, "-p", parent, "-m", title).decode().strip()
        try:
            git(repo, "push", "--quiet", "origin", f"{commit}:refs/heads/{branch}")
        except Refusal as refusal:
            raise Refusal(f"the commit was made but not pushed, so GitHub is unchanged. If {branch} moved since "
                          f"the fetch, run file-chat again: {refusal}") from None
    try:
        checked = None if no_remote_check or held else remote_check(repo, url, branch, commit, folder_path, members)
    except Refusal as refusal:
        raise Refusal(f"PUSHED {commit[:12]} to {branch}, but the check of what GitHub holds FAILED; do not "
                      f"trust this save until it passes: {refusal}") from None
    pr_url = None
    if not direct:
        body = (f"Saved {ca.PLATFORMS[source['platform']]} chat `{ca.one_line(source['title'])}`, revision "
                f"`{revision}`.\n\n"
                f"- Status: {coverage['status']}; {coverage['messages']} messages; files "
                f"{coverage['files_captured']} captured, {coverage['files_missing']} missing\n"
                f"- Folder: `{folder_path}/`\n"
                "- file-chat verified every file before the commit"
                + (", and a fresh copy fetched back from GitHub passed the same check.\n" if checked else ".\n"))
        done = "checked" if checked else "pushed"
        try:
            pr_url = open_pull_request(repo, slug, default_branch, branch, title, body)
        except Refusal as refusal:
            raise Refusal(f"{done} {branch} ({commit[:12]}), but opening the pull request failed; open it on GitHub "
                          f"from that branch, or run file-chat again: {refusal}") from None
    else:
        note = update_checkout(repo, default_branch)
        if note:
            notes.append(note)
    result.pr_url = pr_url
    added = f" ({len(bound)} file(s) added from your downloads)" if bound else ""
    print(f"file-chat: filed {source['title']} ({ca.PLATFORMS[source['platform']]})")
    print(f"  repo      {slug} (private)")
    print(f"  folder    {folder_path}/")
    print(f"  status    {status}{added}")
    where = " (pushed straight to the default branch)" if direct else ""
    print(f"  commit    {commit[:12]} on {branch}" + (where if pushed else " (already there from an earlier run)"))
    if pr_url:
        print(f"  pr        {pr_url}  (merge it to keep the save on {default_branch})")
    if held:
        print(f"  github    {branch} already holds this save with as many files or more; its copy verifies "
              f"({held} files). Nothing was pushed")
    elif checked:
        print(f"  github    {branch} points at the commit; a fresh copy of the folder passed every check "
              f"({checked} files)")
    else:
        print("  github    not re-read (--no-remote-check)")
    for note in notes:
        print(f"  note      {note}")
    return result


# ── the inbox: a batch of saves ───────────────────────────────────────────────────────────────────────────────────

class Skipped(Exception):
    pass


def in_progress(name):
    return name.lower().endswith(IN_PROGRESS)


def inspect_folder(folder):
    """One chat's folder: returns (zip, downloads, raw). Raises Skipped for a download still in progress and
    Refusal for anything that is not part of a save."""
    entries = sorted((e for e in folder.iterdir() if e.name != ".DS_Store"), key=lambda e: e.name)
    for entry in entries:
        if in_progress(entry.name):
            raise Skipped(f"download still in progress ({entry.name})")
    lower_names = {e.name.lower() for e in entries}
    zips, downloads, raw = [], [], []
    for entry in entries:
        lower = entry.name.lower()
        if entry.is_symlink():
            raise Refusal(f"{entry.name}: symbolic links are not filed")
        if entry.is_file() and lower.endswith(".zip"):
            zips.append(entry)
        elif entry.is_file() and FILE_ID.match(entry.name):
            downloads.append(entry)
        elif entry.is_file() and lower.endswith(".html"):
            raw.append(entry)
        elif entry.is_dir() and lower.endswith("_files") and f"{lower[:-len('_files')]}.html" in lower_names:
            raw.append(entry)
        else:
            raise Refusal(f"{entry.name}: not part of a save. A chat's folder holds one ZIP, downloads named from "
                          "their file id (f000002.png) and a saved web page (X.html, with its X_files folder); move "
                          "this out or rename it")
    if not zips:
        raise Refusal("no ZIP in this folder; put the chat-save ZIP in it")
    if len(zips) > 1:
        raise Refusal(f"{zips[1].name}: a second ZIP; a chat's folder holds exactly one, so move one of them out")
    return zips[0], downloads, raw


def unique_path(path, is_file):
    """path, or the same name with " (2)", " (3)", ... so that nothing is ever overwritten."""
    if not os.path.lexists(path):
        return path
    stem, suffix = (path.stem, path.suffix) if is_file else (path.name, "")
    number = 2
    while os.path.lexists(path.with_name(f"{stem} ({number}){suffix}")):
        number += 1
    return path.with_name(f"{stem} ({number}){suffix}")


def move_into(source, folder):
    """Move source into folder under its own name (suffixed on a clash); returns the new path."""
    folder.mkdir(exist_ok=True)
    target = unique_path(folder / source.name, source.is_file())
    shutil.move(str(source), str(target))
    return target


def one_line_reason(refusal):
    """The first line of a refusal; when that line only introduces a list ("...:"), the first item of the list too."""
    lines = [line.strip() for line in str(refusal).splitlines() if line.strip()]
    if not lines:
        return "failed"
    if lines[0].endswith(":") and len(lines) > 1:
        detail = lines[1][2:] if lines[1].startswith("- ") else lines[1]
        return f"{lines[0][:-1]} — {detail}"
    return lines[0]


def settle(entry, inbox, filed_dir, result, dry_run):
    """Move a filed item out of the way and return the summary line. A dry run only says what would move."""
    name = entry.name
    if result.outcome == "dry-run":
        part = f"; still missing {', '.join(result.missing)}" if result.missing else ""
        return f"dry run {name} → {result.slug}: would be filed, {result.messages} messages, {result.files} files{part}"
    if result.missing:
        if entry.is_file():
            if dry_run:
                where = unique_path(inbox / entry.stem, False).name
            else:
                folder = unique_path(inbox / entry.stem, False)
                folder.mkdir()
                shutil.move(str(entry), str(folder / entry.name))
                where = folder.name
        else:
            where = entry.name
        hint = (f"missing {', '.join(result.missing)}; drop it into {inbox.name}/{where}/ and re-run"
                if len(result.missing) == 1 else
                f"missing {', '.join(result.missing)}; drop them into {inbox.name}/{where}/ and re-run")
        if dry_run:
            move = f"would move into {inbox.name}/{where}/" if entry.is_file() else "would stay in the inbox"
            return f"dry run {name}: already filed; missing {', '.join(result.missing)}; {move}"
        if result.outcome == "already":
            return f"already filed {name}  {hint}"
        return f"partial {name} → {result.pr_url or result.slug}  {hint}"
    if dry_run:
        return f"dry run {name}: already filed; would move to {filed_dir.name}/"
    move_into(entry, filed_dir)
    if result.outcome == "already":
        return f"already filed {name}"
    where = f"{result.slug} {result.pr_url}" if result.pr_url else f"{result.slug} (straight to the default branch)"
    return f"filed   {name} → {where}  {result.messages} messages, {result.files} files"


def take_lock(lock):
    """Create the lock holding this PID and return True; otherwise print why and return False. A lock left by a
    process that no longer exists is replaced."""
    rm = f"rm {shlex.quote(str(lock))}"
    try:
        descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError:
        try:
            pid = int(lock.read_text().strip())
            if pid <= 0 or pid > 2 ** 31 - 1:
                raise ValueError
        except (OSError, ValueError, OverflowError):
            print(f"file-chat: the lock {lock} exists and does not hold a process number. If no inbox run is active, "
                  f"remove it with:\n  {rm}")
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            print(f"file-chat: replacing a stale lock left by process {pid}")
            try:
                lock.unlink()
                descriptor = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except OSError as error:
                print(f"file-chat: cannot replace the lock {lock}: {error}")
                return False
        except OSError:
            descriptor = None  # alive, or not ours to signal
        else:
            descriptor = None
        if descriptor is None:
            print(f"file-chat: another inbox run holds the lock {lock} (PID {pid}); wait for it. Only if no run is "
                  f"active, remove it with:\n  {rm}")
            return False
    except OSError as error:
        print(f"file-chat: cannot create the lock {lock}: {error}")
        return False
    with os.fdopen(descriptor, "w") as handle:
        handle.write(f"{os.getpid()}\n")
    return True


def run_inbox(inbox, direct, dry_run, no_remote_check):
    inbox = inbox.expanduser()
    given = inbox
    if not inbox.exists():
        print(f"file-chat: the inbox {inbox} does not exist. Create it with:\n  mkdir -p {shlex.quote(str(inbox))}\n"
              "then move your chat-save ZIPs into it. file-chat never creates the inbox")
        return 1
    if not inbox.is_dir():
        print(f"file-chat: {inbox} is not a folder")
        return 1
    inbox = inbox.resolve()
    if inbox in (Path.home().resolve(), Path(inbox.anchor)):
        print(f"file-chat: {inbox} is too broad to be an inbox; use a folder of its own, such as "
              "~/chat-backups/inbox")
        return 1
    if inbox.name != "inbox" or inbox.parent in (Path.home().resolve(), Path(inbox.anchor)):
        subject = f"{given} is a link to {inbox}, which" if given.is_symlink() else f"{inbox}"
        print("file-chat: the inbox must be a folder named exactly inbox (in lower case), inside a folder that is not "
              f"your home folder or the disk root: {subject} is not. file-chat keeps filed/ and its lock beside the "
              "inbox, so use ~/chat-backups/inbox")
        return 1
    filed_dir = inbox.parent / "filed"
    if dry_run:
        return process_inbox(inbox, filed_dir, direct, dry_run, no_remote_check)
    lock = inbox.parent / LOCK_NAME
    if not take_lock(lock):
        return 1
    try:
        return process_inbox(inbox, filed_dir, direct, dry_run, no_remote_check)
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def process_inbox(inbox, filed_dir, direct, dry_run, no_remote_check):
    try:
        entries = sorted((e for e in inbox.iterdir() if e.name != ".DS_Store"), key=lambda e: e.name)
    except OSError as error:
        print(f"file-chat: cannot read the inbox {inbox}: {error}")
        return 1
    if not entries:
        print(f"file-chat: the inbox {inbox} is empty; nothing to file")
        return 0
    lines, failed = [], False
    try:
        for entry in entries:
            name = entry.name
            if in_progress(name):
                lines.append(f"skipped {name}: download still in progress")
                continue
            is_zip = entry.is_file() and name.lower().endswith(".zip")
            if entry.is_symlink() or name.startswith(".") or not (is_zip or entry.is_dir()):
                lines.append(f"left alone {name}: not a save")
                continue
            print(f"file-chat: {name}")
            try:
                if is_zip:
                    zip_path, downloads, raw = entry, [], []
                else:
                    zip_path, downloads, raw = inspect_folder(entry)
                result = file_one(zip_path, downloads, raw, None, direct, dry_run, no_remote_check)
                try:
                    lines.append(settle(entry, inbox, filed_dir, result, dry_run))
                except OSError as error:
                    failed = True
                    lines.append(f"failed  {name}: filed, but it could not be moved: {error}")
            except Skipped as skip:
                lines.append(f"skipped {name}: {skip}")
            except Refusal as refusal:
                print(f"file-chat: {refusal}")
                failed = True
                lines.append(f"refused {name}: {one_line_reason(refusal)}")
            except OSError as error:
                print(f"file-chat: {error}")
                failed = True
                lines.append(f"failed  {name}: {error}")
            except Exception as error:
                print(f"file-chat: {type(error).__name__}: {error}")
                failed = True
                lines.append(f"failed  {name}: {type(error).__name__}: {error}")
    finally:
        print("\nfile-chat: inbox summary")
        for line in lines:
            print(f"  {line}")
    return 1 if failed else 0


def main(argv):
    parser = argparse.ArgumentParser(description="File a chat-save archive into its private GitHub backup repo.")
    parser.add_argument("zip", nargs="?", type=Path, help="the chat-save ZIP the chat gave you")
    parser.add_argument("downloads", nargs="*", type=Path,
                        help="files you downloaded for ids the save listed as missing (f000002.png …)")
    parser.add_argument("--raw", action="append", default=[], type=Path,
                        help="extra material to keep byte for byte under raw/ (a saved web page and its folder)")
    parser.add_argument("--repo", help="your local clone of the backup repo (default: see the README)")
    parser.add_argument("--inbox", nargs="?", const=DEFAULT_INBOX, default=None, type=Path, metavar="DIR",
                        help=f"file every save in this folder (default {DEFAULT_INBOX}), one pull request each")
    parser.add_argument("--direct", action="store_true",
                        help="commit straight to the default branch instead of opening a pull request")
    parser.add_argument("--dry-run", action="store_true", help="check and show the plan; fetch, but write nothing")
    parser.add_argument("--no-remote-check", action="store_true",
                        help="skip re-reading the folder from GitHub after the push")
    args = parser.parse_intermixed_args(argv[1:])
    if args.inbox is not None:
        if str(args.inbox).lower().endswith(".zip"):
            args.zip = args.zip or args.inbox
        if args.zip or args.downloads or args.raw or args.repo:
            print("file-chat: --inbox files every save in the inbox, so it cannot be combined with a ZIP, downloaded "
                  "files, --raw or --repo (each platform's repo comes from $CHAT_SAVE_REPO_CHATGPT / "
                  "$CHAT_SAVE_REPO_CLAUDE or the default folder)")
            return 2
        return run_inbox(args.inbox, args.direct, args.dry_run, args.no_remote_check)
    if args.zip is None:
        print("file-chat: give a ZIP to file, or --inbox to file a folder of them")
        return 2
    if not args.zip.is_file():
        print(f"file-chat: {args.zip} is not a file")
        return 2
    try:
        file_one(args.zip, args.downloads, args.raw, args.repo, args.direct, args.dry_run, args.no_remote_check)
    except Refusal as refusal:
        print(f"file-chat: {refusal}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
