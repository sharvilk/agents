#!/usr/bin/env python3
"""Read-only inventory for a checkpoint: the machine, the processes left in your repos, and every worktree's git state.

A restart or a quit keeps what is on disk and loses what is running. This lists what a checkpoint has to deal with
before either: processes whose working directory is inside the repos you name (or their worktrees), each worktree's
uncommitted files, unpushed commits and half-done merges, the repo's stash entries, and the machine's disk, load and
swap. It never prints a process's command line or environment (they can carry secrets): only PID, parent, age, CPU,
resident memory, the executable's name and the working directory. It changes nothing; stopping a process or pushing a
branch is the caller's decision.

Usage: checkpoint-scan.py [repo-root ...]   (default: the git repo the current directory is in)
Exit: 0 nothing to deal with, 1 something listed needs a decision, 2 a check could not run.
"""
import os
import platform
import re
import shutil
import subprocess
import sys

DISK_FLOOR_GIB = 5.0


def run(args, cwd=None):
    try:
        out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout if out.returncode == 0 else None


def git(path, *args):
    return run(['git', '-C', path, *args])


def machine():
    lines, worry = [], False
    usage = shutil.disk_usage('/')
    free = usage.free / 2**30
    if free < DISK_FLOOR_GIB:
        worry = True
    lines.append(f'disk free   {free:.1f} GiB' + (f'  (under {DISK_FLOOR_GIB:.0f} GiB)' if free < DISK_FLOOR_GIB else ''))
    load = os.getloadavg()
    cores = os.cpu_count() or 1
    lines.append(f'load        {load[0]:.1f} {load[1]:.1f} {load[2]:.1f}  ({cores} cores)')
    if platform.system() == 'Darwin':
        swap = run(['sysctl', '-n', 'vm.swapusage'])
        if swap:
            lines.append('swap        ' + swap.strip())
    return lines, worry


def worktrees(root):
    out = git(root, 'worktree', 'list', '--porcelain')
    if out is None:
        return None
    trees, cur = [], {}
    for line in out.splitlines() + ['']:
        if not line:
            if cur:
                trees.append(cur)
            cur = {}
        elif line.startswith('worktree '):
            cur['path'] = line[len('worktree '):]
        elif line.startswith('branch '):
            cur['branch'] = line[len('branch refs/heads/'):]
        elif line == 'detached':
            cur['branch'] = '(detached)'
    return trees


def tree_state(path, branch):
    notes = []
    status = git(path, 'status', '--porcelain')
    if status is None:
        return ['git status failed'], True
    dirty = len([l for l in status.splitlines() if l.strip()])
    if dirty:
        notes.append(f'{dirty} uncommitted')
    for op in ('MERGE_HEAD', 'REBASE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD'):
        p = (git(path, 'rev-parse', '--git-path', op) or '').strip()
        if p and os.path.exists(os.path.join(path, p) if not os.path.isabs(p) else p):
            notes.append(f'{op.split("_")[0].lower()} in progress')
    if branch and not branch.startswith('('):
        counts = git(path, 'rev-list', '--left-right', '--count', '@{u}...HEAD')
        if counts is None and git(path, 'rev-parse', '--verify', '--quiet', f'refs/remotes/origin/{branch}') is not None:
            counts = git(path, 'rev-list', '--left-right', '--count', f'origin/{branch}...HEAD')
        if counts is None:
            remotes = git(path, 'remote')
            own = git(path, 'rev-list', '--count', 'HEAD', '--not', '--remotes')
            if remotes is not None and not remotes.strip():
                notes.append('no remote')
            elif own is not None and own.strip().isdigit() and int(own) > 0:
                notes.append(f'{int(own)} commit{"" if int(own) == 1 else "s"} on no remote')
            else:
                notes.append('no remote branch')
        else:
            behind, ahead = (int(x) for x in counts.split())
            if ahead:
                notes.append(f'{ahead} unpushed')
            if behind:
                notes.append(f'{behind} behind its remote')
    return notes, bool(notes)


def process_cwds():
    """{pid: cwd} for every process, from one lsof call (macOS and Linux) or /proc (Linux)."""
    out = run(['lsof', '-a', '-d', 'cwd', '-Fpn'])
    cwds = {}
    if out is not None:
        pid = None
        for line in out.splitlines():
            if line.startswith('p'):
                pid = int(line[1:])
            elif line.startswith('n') and pid is not None:
                cwds[pid] = line[1:]
        return cwds
    if os.path.isdir('/proc'):
        for name in os.listdir('/proc'):
            if name.isdigit():
                try:
                    cwds[int(name)] = os.readlink(f'/proc/{name}/cwd')
                except OSError:
                    pass
    return cwds


def ancestors():
    """This script and the shells above it, which are the caller, not strays."""
    pids, pid = set(), os.getpid()
    for _ in range(12):
        pids.add(pid)
        out = run(['ps', '-o', 'ppid=', '-p', str(pid)])
        if not out or not out.strip().isdigit():
            break
        pid = int(out.strip())
        if pid <= 1:
            break
    return pids


def pid_exists(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def under(path, prefixes):
    return any(path == p or path.startswith(p.rstrip('/') + '/') for p in prefixes)


def main(argv):
    roots = [os.path.realpath(a) for a in argv] or []
    if not roots:
        top = run(['git', 'rev-parse', '--show-toplevel'])
        if not top:
            print('not inside a git repo: name the repo roots to scan', file=sys.stderr)
            return 2
        roots = [top.strip()]
    failed, worry = False, False

    print('## Machine')
    lines, w = machine()
    worry |= w
    print('\n'.join(lines))

    all_paths, seen = [], set()
    print('\n## Worktrees')
    for root in roots:
        trees = worktrees(root)
        if trees is None:
            print(f'{root}: not a git repo')
            failed = True
            continue
        main_tree = trees[0]['path'] if trees else root  # git lists the main checkout first
        if main_tree in seen:
            continue
        seen.add(main_tree)
        stashes = git(root, 'stash', 'list')
        n_stash = len(stashes.splitlines()) if stashes else 0
        print(f'{main_tree}' + (f'  ({n_stash} stash entr{"y" if n_stash == 1 else "ies"}; the stash is shared by every worktree)' if n_stash else ''))
        for t in trees:
            all_paths.append(t['path'])
            notes, w = tree_state(t['path'], t.get('branch'))
            worry |= w and notes not in (['no remote branch'], ['no remote'])
            label = os.path.relpath(t['path'], main_tree) if t['path'] != main_tree else '.'
            print(f'  {label:<46} {t.get("branch", "?"):<46} {", ".join(notes) if notes else "clean, pushed"}')

    print('\n## Processes in these repos (PID, parent, age, CPU, resident, executable, cwd; never command lines)')
    cwds = process_cwds()
    mine = ancestors()
    # The rest of the caller's own pipeline shares this script's parent shell; a stray lives under another shell.
    siblings = set()
    ps_all = run(['ps', '-A', '-o', 'pid=,ppid='])
    for line in (ps_all or '').splitlines():
        a = line.split()
        if len(a) == 2 and a[1].isdigit() and int(a[1]) == os.getppid():
            siblings.add(int(a[0]))
    hits = sorted(pid for pid, cwd in cwds.items()
                  if pid not in mine and pid not in siblings and under(cwd, all_paths + roots))
    if not hits:
        print('none')
    else:
        # ps exits non-zero when a listed process has already ended, so its output is read whatever the exit code.
        ps_error = None
        try:
            out = subprocess.run(['ps', '-o', 'pid=,ppid=,etime=,%cpu=,rss=,comm=', '-p', ','.join(map(str, hits))],
                                 capture_output=True, text=True, timeout=30).stdout
        except (OSError, subprocess.TimeoutExpired) as exc:
            out, ps_error = '', type(exc).__name__
        described = set()
        for line in out.splitlines():
            parts = line.split(None, 5)
            if len(parts) < 6 or not parts[0].isdigit():
                continue
            pid, ppid, etime, cpu, rss, comm = parts
            described.add(int(pid))
            print(f'  pid {pid:<7} ppid {ppid:<7} age {etime:<12} cpu {cpu:>5}%  {int(rss) // 1024:>5} MB  '
                  f'{os.path.basename(comm):<16} {cwds.get(int(pid), "?")}')
        if described:
            worry = True
        # A process ps did not describe has either ended or ps could not see it: tell the two apart.
        running = [pid for pid in hits if pid not in described and pid_exists(pid)]
        if running:
            reason = f'ps failed: {ps_error}; ' if ps_error else ''
            print(f'  {reason}could not describe pid(s) {", ".join(map(str, running))} (still running)')
            worry = True
        if ps_error:
            failed = True
        if not described and not running:
            print('none (the ones found had already ended)')
    return 2 if failed else (1 if worry else 0)


if __name__ == '__main__':
    try:
        code = main(sys.argv[1:])
    except Exception as exc:
        print(f'checkpoint-scan: unexpected error: {type(exc).__name__}: {exc}', file=sys.stderr)
        code = 2
    sys.exit(code)
