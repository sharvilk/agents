"""Shared helpers for the chat-skills tests. Every test works in a temporary folder; nothing outside it is written."""
import os
import shutil
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "chat-save" / "scripts" / "pack.py"
VERIFY = ROOT / "chat-restore" / "scripts" / "verify.py"
FILE_CHAT = ROOT / "file_chat.py"
BUILD_ZIPS = ROOT / "build_zips.py"
FIXTURE = ROOT / "examples" / "synthetic-chat"
NOW = "20261123T120000Z"

sys.path.insert(0, str(ROOT / "chat-restore" / "scripts"))
import chatarchive  # noqa: E402,F401  (re-exported for the tests)


def run_py(script, *args, env=None, cwd=None, timeout=180):
    """Run a script the way the README does: python3 -I, captured output, a timeout."""
    return subprocess.run([sys.executable, "-I", str(script), *map(str, args)], capture_output=True, text=True,
                          env=env, cwd=cwd, timeout=timeout)


def make_work(tmp):
    """A fresh copy of the synthetic chat's working folder."""
    work = Path(tmp) / "work"
    shutil.copytree(FIXTURE, work)
    return work


def pack(work, out, now=NOW):
    done = run_py(PACK, work, "--out", out, "--now", now)
    zips = sorted(Path(out).glob("*.zip"))
    return done, (zips[-1] if zips else None)


def read_raw(zip_path):
    """[(name, data, external_attr)] exactly as stored, duplicates included."""
    with zipfile.ZipFile(zip_path) as archive:
        return [(info.filename, archive.read(info), info.external_attr) for info in archive.infolist()]


def write_raw(zip_path, entries):
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data, attr in entries:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = attr
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def regular():
    return (stat.S_IFREG | 0o644) << 16


def with_fresh_checksums(members):
    """Recompute CHECKSUMS.sha256 so a test reaches the checks behind it."""
    members = dict(members)
    members[chatarchive.CHECKSUMS] = chatarchive.checksums_text(members)
    return members


def write_members(zip_path, members):
    write_raw(zip_path, [(name, data, regular()) for name, data in sorted(members.items())])


def clean_env(home, extra=None):
    """An environment with no credentials: a temporary HOME, no global or system git config, a fixed identity."""
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    gitconfig = home / "empty.gitconfig"
    gitconfig.touch()
    env = {
        "HOME": str(home),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LANG": "en_US.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(gitconfig),
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
        "GIT_TERMINAL_PROMPT": "0",
    }
    env.update(extra or {})
    return env
