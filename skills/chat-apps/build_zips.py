"""Make the upload ZIPs for ChatGPT and claude.ai: chat-save.zip and chat-restore.zip.

Usage:  python3 build_zips.py [--out DIR]        (default: dist/ beside this script, which git ignores)

Each ZIP holds one folder named like the skill (claude.ai requires that), with SKILL.md, scripts/ and references/,
and nothing else: no tests, no caches. The ZIPs are rebuilt from the folders here on every run, so they never drift
from the source, and the same source gives the same bytes. Exit 0 on success, 1 if a skill folder is incomplete.
"""
import argparse
import hashlib
import stat
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = ("chat-save", "chat-restore")
INCLUDE = ("SKILL.md", "scripts", "references")


def skill_members(skill):
    folder = HERE / skill
    members = {}
    for item in sorted(folder.rglob("*")):
        relative = item.relative_to(folder)
        if not item.is_file() or "__pycache__" in relative.parts or item.suffix == ".pyc":
            continue
        if relative.parts[0] not in INCLUDE or item.name == ".DS_Store":
            continue
        members[f"{skill}/{relative.as_posix()}"] = item.read_bytes()
    return members


def write_zip(path, members):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, members[name])


def main(argv):
    parser = argparse.ArgumentParser(description="Build the chat-save and chat-restore upload ZIPs.")
    parser.add_argument("--out", type=Path, default=HERE / "dist", help="where to write the ZIPs")
    args = parser.parse_args(argv[1:])
    args.out.mkdir(parents=True, exist_ok=True)
    for skill in SKILLS:
        members = skill_members(skill)
        if f"{skill}/SKILL.md" not in members:
            print(f"build-zips: {skill}/SKILL.md is missing")
            return 1
        path = args.out / f"{skill}.zip"
        write_zip(path, members)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{path}  {len(members)} files  sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
