"""Check a chat-save archive and print what it holds.

Usage:  python3 verify.py PATH        (a chat-save ZIP, or an unzipped archive folder)

It checks that every member is listed in CHECKSUMS.sha256 with a matching SHA-256, that the paths are safe, the
messages are numbered 1, 2, 3… and every file link is consistent, and that the readable views match the record.
Two older layouts (the first drafts and the pilots) are recognised and checked by their checksums only.
Exit 0 when every check passes, 1 when any fails, 2 on wrong usage.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chatarchive  # noqa: E402  (imported after the path insert, so it works with python3 -I too)

if __name__ == "__main__":
    sys.exit(chatarchive.main(sys.argv))
