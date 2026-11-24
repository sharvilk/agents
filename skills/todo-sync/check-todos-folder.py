#!/usr/bin/env python3
"""List anything in the todo-sync list folder that is not a todo list.

<list-folder>/<initiative>/ may hold only <session-id>.md files. This reports everything else: a file
directly in the list folder, a backup copy of a list, a file named after a session that is not exactly
<session-id>.md, a file that is not .md, a symlink, or a subfolder. A subfolder is reported once with its
file count and never entered, so a subfolder of copied source costs one line, not thousands.

It only reads; moving or deleting what it finds is the user's call.

Usage: check-todos-folder.py [list-folder]
  default: <config>/todo-sync, where <config> is $CLAUDE_CONFIG_DIR or ~/.claude
Exits 0 if all is well, 1 if it found something, 2 if part of the folder was unreadable.
"""
import os
import re
import sys

# Finder's metadata file: never a list, and not worth a line.
IGNORED = {'.DS_Store'}

# The names agents give pre-rewrite copies, wherever they appear: <id>.md.presync-1003.bak,
# <id>.pre-sync-2026-10-01.md, <id>.bak.md, <id>.backup.md.
BACKUP_NAME = re.compile(r'\.bak|\.backup|pre-?sync', re.IGNORECASE)
# A list is exactly <session-id>.md; any other name that holds a session id is a copy or a side file
# (<id>.old.md, copy of <id>.md, <id>-notes.md). Notes with other names pass.
SESSION_ID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
BACKUP_COPY = ('backup copy of a list: tell the user; none are kept here, since the diff before saving and '
               'the transcript cover the list')
SESSION_SIDE_FILE = 'named after a session but not <session-id>.md: a copy or a side file; tell the user'


def config_dir():
    return os.environ.get('CLAUDE_CONFIG_DIR') or os.path.expanduser('~/.claude')


def count_files(folder, errors):
    # os.walk does not follow symlinks unless asked, so a symlink loop cannot hang the count;
    # onerror collects the folders it could not open instead of skipping them silently.
    return sum(len(files) for _, _, files in os.walk(folder, onerror=errors.append))


def entries(folder):
    with os.scandir(folder) as it:
        return sorted((e for e in it if e.name not in IGNORED), key=lambda e: e.name)


def initiatives(root, unreadable):
    """Yield (initiative, its entries) for each real subfolder of root; record the ones that cannot be read."""
    for top in entries(root):
        if top.is_symlink() or not top.is_dir(follow_symlinks=False):
            continue
        try:
            yield top.name, entries(top.path)
        except OSError as e:
            unreadable.append((top.name + '/', f'unreadable ({e.strerror})'))


def problems(root):
    found, unreadable = [], []
    for top in entries(root):
        if top.is_symlink():
            found.append((top.name, 'symlink in the list folder itself'))
        elif not top.is_dir(follow_symlinks=False):
            found.append((top.name, 'file in the list folder itself; lists go in <initiative>/'))
    for name, items in initiatives(root, unreadable):
        for item in items:
            rel = f'{name}/{item.name}'
            if item.is_symlink():
                found.append((rel, 'symlink'))
            elif item.is_dir(follow_symlinks=False):
                errors = []
                files = plural(count_files(item.path, errors), 'file', 'files')
                found.append((rel + '/', f"subfolder ({'at least ' if errors else ''}{files})"))
                if errors:
                    unreadable.append((rel + '/', f'partly unreadable ({errors[0].strerror})'))
            elif BACKUP_NAME.search(item.name):
                found.append((rel, BACKUP_COPY))
            elif (m := SESSION_ID.search(item.name)) and item.name != m.group(0) + '.md':
                found.append((rel, SESSION_SIDE_FILE))
            elif not item.name.endswith('.md'):
                found.append((rel, 'not a .md file'))
    return found, unreadable


def plural(n, one, many):
    return f'{n} {one if n == 1 else many}'


def main(argv):
    root = os.path.expanduser(argv[0]) if argv else os.path.join(config_dir(), 'todo-sync')
    if not os.path.lexists(root):
        print(f'OK - no list folder at {root} yet')
        return 0
    if not os.path.isdir(root) or os.path.islink(root):
        print(f'{root} -> not a real folder (a file or a symlink); lists go in a real folder')
        return 1
    try:
        found, unreadable = problems(root)
    except OSError as e:
        found, unreadable = [], [('', f'unreadable ({e.strerror})')]
    for rel, what in found + unreadable:
        print(f'{os.path.join(root, rel) if rel else root} -> {what}')
    if found:
        print(f"{plural(len(found), 'entry', 'entries')} in {root} "
              f"{'is not a todo list' if len(found) == 1 else 'are not todo lists'}", file=sys.stderr)
    if unreadable:
        print(f"{plural(len(unreadable), 'folder', 'folders')} could not be read; the check is incomplete",
              file=sys.stderr)
        return 2
    if found:
        return 1
    print(f'OK - {root} holds only todo lists')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
