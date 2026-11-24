#!/usr/bin/env python3
"""List todo lists nobody has touched for a while, so the user can choose which to close out.

Looks at <config>/todo-sync/<initiative>/<session-id>.md and <config>/todos/<initiative>/<session-id>.md and
prints, oldest first, every list whose modification time is more than N days ago: the date it last changed,
which folder it is in, the initiative, the session id, and an approximate count of open checkboxes.

It only reads. It never deletes, moves or opens anything but those lists; closing one is the user's call,
made after seeing its open items.

Usage: list-old-lists.py [--days N] [config-folder]
  --days N        how old a list must be, in days (default 14)
  config-folder   default: $CLAUDE_CONFIG_DIR or ~/.claude
Exits 0 if it ran (whether or not it found lists), 1 for a bad argument, 2 if a folder could not be read.
"""
import datetime
import os
import re
import sys
import time

DEFAULT_DAYS = 14
# The old `todos` folder is read here only until the skill stops looking there for a session's own list;
# both go out together.
FOLDERS = (('todo-sync', 'todo-sync'), ('todos', 'todos (old folder)'))
SESSION_LIST = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.md', re.IGNORECASE)
OPEN_BOX = re.compile(r'^ *- \[ \]')


class BadArgument(Exception):
    pass


def parse(argv):
    days, config = DEFAULT_DAYS, None
    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg == '--days' or arg.startswith('--days='):
            value = arg.partition('=')[2] if '=' in arg else (args.pop(0) if args else '')
            if not re.fullmatch(r'[0-9]+', value):
                raise BadArgument(f'--days needs a whole number of days, got {value!r}')
            days = int(value)
        elif arg.startswith('-'):
            raise BadArgument(f'unknown option {arg}')
        elif config is None:
            config = arg
        else:
            raise BadArgument('only one config folder may be given')
    return days, config or os.environ.get('CLAUDE_CONFIG_DIR') or os.path.expanduser('~/.claude')


def open_items(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            return sum(1 for line in f if OPEN_BOX.match(line))
    except OSError:
        return None


def scan(config, cutoff, unreadable):
    found = []
    for folder, label in FOLDERS:
        root = os.path.join(config, folder)
        if not os.path.isdir(root):
            continue
        try:
            with os.scandir(root) as it:
                initiatives = sorted((e for e in it if e.is_dir(follow_symlinks=False)), key=lambda e: e.name)
        except OSError as e:
            unreadable.append(f'{root} -> unreadable ({e.strerror})')
            continue
        for top in initiatives:
            try:
                with os.scandir(top.path) as it:
                    files = [e for e in it if SESSION_LIST.fullmatch(e.name) and e.is_file(follow_symlinks=False)]
            except OSError as e:
                unreadable.append(f'{top.path} -> unreadable ({e.strerror})')
                continue
            for e in files:
                try:
                    mtime = e.stat(follow_symlinks=False).st_mtime
                except OSError as err:
                    unreadable.append(f'{e.path} -> unreadable ({err.strerror})')
                    continue
                if mtime < cutoff:
                    found.append((mtime, label, top.name, e.name[:-3], open_items(e.path)))
    return sorted(found)


def main(argv):
    try:
        days, config = parse(argv)
    except BadArgument as e:
        print(f'list-old-lists.py: {e}', file=sys.stderr)
        print('usage: list-old-lists.py [--days N] [config-folder]', file=sys.stderr)
        return 1
    unreadable = []
    found = scan(config, time.time() - days * 86400, unreadable)
    for mtime, label, initiative, session, count in found:
        date = datetime.date.fromtimestamp(mtime).isoformat()
        shown = '?' if count is None else str(count)
        print(f'{date}  {label}  {initiative}  {session}  open: about {shown}')
    noun = 'list' if len(found) == 1 else 'lists'
    print(f'{len(found)} {noun} untouched for more than {days} days; open counts are approximate '
          f'(lines starting "- [ ]")')
    for line in unreadable:
        print(line)
    if unreadable:
        n = len(unreadable)
        print(f'{n} {"folder or file" if n == 1 else "folders or files"} could not be read; the list is incomplete')
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
