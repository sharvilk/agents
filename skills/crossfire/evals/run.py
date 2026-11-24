#!/usr/bin/env python3
"""Run one crossfire example end to end in a fresh, headless Claude Code session, and score it.

    python3 -I run.py <case-id> [--out DIR] [--timeout-min 40] [--max-budget-usd 25] [--model opus]

1. Copies examples/<case>/repo to a new temporary folder and makes it a git repository with one commit, using fixed
   dates and no global or system git config, so the same files always give the same commit id.
2. Stages a minimal plugin in its own temporary folder, outside the case's repo: `.claude-plugin/plugin.json`,
   `skills/crossfire/SKILL.md` and `references/`, and the two agent files in `agents/`. It never holds the README,
   the playbook, the examples or the evals, which describe the planted defects. `.crossfire/` is excluded from git
   in the case's repo.
3. Runs `claude -p "/crossfire <target> <args>"` with `--plugin-dir <the staged plugin>`, `--setting-sources project`
   and `--strict-mcp-config`, so only the skill from this checkout loads, as a plugin, and none of your own
   instructions, hooks, MCP servers or installed plugins. File edits are
   accepted inside the folder; Bash is limited to a prefix allowlist of read commands (named git subcommands, ls,
   wc, grep, cat, head). That allowlist is not a sandbox: a git flag such as `--output` could still write a file
   elsewhere, and read commands can read any file your user can.
4. Copies the summary and run folder to DIR (default examples/<case>/output), writes metrics.json from the session's
   own report, and score.json from score.py.

A case with `round_of` is a second round: the copy starts from the base case's repo plus the base case's summary and
run folder, commits, lays the case's `overlay` folder (the owner's changes) on top, and commits again. If the run
leaves the first round's summary unchanged, it is not scored as this round's.

It refuses to overwrite an existing DIR and stops the session at the time limit or on Ctrl-C (TERM, then KILL, to the
whole process group). It keeps both temporary folders, the case repo copy and the staged plugin (`crossfire-plugin-*`),
prints their paths, and deletes neither: remove them yourself when you are done. Exit 0 only when the session finished
and wrote a new summary.

"Hermetic" here means the answer keys are neither staged nor loaded by the session. It does not mean they are
unreadable: the checkout stays readable by the agents' read tools.
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
EXAMPLES = SKILL / "examples"
RUNTIME = ["SKILL.md", "references"]
AGENTS = ["crossfire-reviewer.md", "crossfire-verifier.md"]
READ_ONLY_BASH = ["git log", "git show", "git diff", "git status", "git rev-parse", "git ls-files", "git check-ignore",
                  "ls", "wc", "grep", "cat", "head"]
TOOLS = ["Read", "Grep", "Glob", "Agent", "WebSearch", "WebFetch"] + [f"Bash({c}:*)" for c in READ_ONLY_BASH]
FIXED_DATE = "2026-11-01T09:00:00+00:00"
GIT_ENV = {**os.environ, "GIT_AUTHOR_DATE": FIXED_DATE, "GIT_COMMITTER_DATE": FIXED_DATE,
           "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=crossfire eval", "-c", "user.email=eval@example.invalid",
                           "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}", *args],
                          cwd=cwd, check=True, capture_output=True, text=True, timeout=60, env=GIT_ENV)


def stop(proc):
    """TERM the session's whole process group, wait briefly, then KILL whatever is left."""
    for sig, wait in ((signal.SIGTERM, 15), (signal.SIGKILL, 5)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=wait)
        except subprocess.TimeoutExpired:
            continue
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def prepare(case_id, case, work):
    base = case.get("round_of", case_id)
    shutil.copytree(EXAMPLES / base / "repo", work, dirs_exist_ok=True)
    git(work, "init", "-q")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "fixture")
    seeded = None
    if base != case_id:
        previous = EXAMPLES / base / "output"
        shutil.copy(previous / "summary.crossfire.md", work / case["summary"])
        shutil.copytree(previous / "run", work / ".crossfire")
        shutil.copytree(EXAMPLES / base / case["overlay"], work, dirs_exist_ok=True)
        git(work, "add", "-A", "--", ".", ":(exclude).crossfire")
        git(work, "commit", "-q", "-m", "answers to round 1")
        seeded = (work / case["summary"]).read_bytes()
    exclude = Path(git(work, "rev-parse", "--git-path", "info/exclude").stdout.strip())
    exclude = exclude if exclude.is_absolute() else work / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as handle:
        handle.write(".crossfire/\n")
    return seeded


def stage_plugin(plugin):
    """Lay out the minimal plugin the session loads with --plugin-dir: runtime files only, never answer keys."""
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "crossfire"}, indent=2) + "\n")
    skill = plugin / "skills" / "crossfire"
    skill.mkdir(parents=True)
    for name in RUNTIME:
        source = SKILL / name
        (shutil.copytree if source.is_dir() else shutil.copy)(source, skill / name)
    (plugin / "agents").mkdir()
    for name in AGENTS:
        shutil.copy(SKILL / "agents" / name, plugin / "agents" / name)


def make_workspaces(case_id, case):
    """Make the case's repo copy and the staged plugin, in two separate temporary folders; return both and the seed."""
    work = Path(tempfile.mkdtemp(prefix=f"crossfire-{case_id}-"))
    seeded = prepare(case_id, case, work)
    plugin = Path(tempfile.mkdtemp(prefix="crossfire-plugin-"))
    stage_plugin(plugin)
    return work, plugin, seeded


def session_command(prompt, plugin, model, max_budget_usd):
    """The headless session's command line: the staged plugin, project-only settings, no user MCP servers."""
    return ["claude", "-p", prompt, "--output-format", "json", "--permission-mode", "acceptEdits",
            "--plugin-dir", str(plugin), "--setting-sources", "project", "--strict-mcp-config", "--model", model,
            "--max-budget-usd", str(max_budget_usd), "--allowedTools", *TOOLS]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("--out")
    parser.add_argument("--timeout-min", type=float, default=40)
    parser.add_argument("--max-budget-usd", type=float, default=25)
    parser.add_argument("--model", default="opus")
    args = parser.parse_args()

    cases = json.loads((HERE / "cases.json").read_text())
    if args.case not in cases:
        sys.exit(f"unknown case {args.case!r}; known: {', '.join(sorted(cases))}")
    case = cases[args.case]
    base = case.get("round_of", args.case)
    default_out = EXAMPLES / base / (f"output-{case['overlay']}" if "overlay" in case else "output")
    out = Path(args.out) if args.out else default_out
    if out.exists():
        sys.exit(f"{out} already exists; move it aside or pass --out")
    if base != args.case and not ((EXAMPLES / base / "output" / "summary.crossfire.md").exists()
                                  and (EXAMPLES / base / "output" / "run").exists()):
        sys.exit(f"a second round needs examples/{base}/output/summary.crossfire.md and run/ from the first")
    if not shutil.which("claude"):
        sys.exit("the claude CLI is not on PATH")

    work, plugin, seeded = make_workspaces(args.case, case)
    out.mkdir(parents=True)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))

    prompt = f"/crossfire {case['target']} {case['args']}".strip()
    command = session_command(prompt, plugin, args.model, args.max_budget_usd)
    print(f"running in {work} with the plugin staged in {plugin}: {prompt}", file=sys.stderr)
    started = time.monotonic()
    proc = subprocess.Popen(command, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=args.timeout_min * 60)
    except subprocess.TimeoutExpired:
        timed_out = True
        stop(proc)
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            stdout, stderr = "", "pipes still open after the process group was killed"

    except BaseException:
        stop(proc)
        raise
    elapsed = round(time.monotonic() - started)

    summary = work / case["summary"]
    fresh = summary.exists() and (seeded is None or summary.read_bytes() != seeded)
    if fresh:
        shutil.copy(summary, out / "summary.crossfire.md")
    if (work / ".crossfire").exists():
        shutil.copytree(work / ".crossfire", out / "run")
    try:
        session = json.loads(stdout)
    except json.JSONDecodeError:
        session = None
    if not isinstance(session, dict):
        session = {"unparsed_stdout_tail": (stdout or "")[-2000:]}
    metrics = {
        "case": args.case,
        "prompt": prompt,
        "model": args.model,
        "exit_code": proc.returncode,
        "timed_out": timed_out,
        "is_error": session.get("is_error"),
        "summary_written": fresh,
        "wall_seconds": elapsed,
        "total_cost_usd": session.get("total_cost_usd"),
        "num_turns": session.get("num_turns"),
        "duration_api_ms": session.get("duration_api_ms"),
        "usage": session.get("usage"),
        "model_usage": session.get("modelUsage"),
        "final_message": session.get("result"),
        "stderr_tail": (stderr or "")[-2000:],
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

    if fresh:
        scored = subprocess.run([sys.executable, "-I", str(HERE / "score.py"), args.case, str(summary)],
                                capture_output=True, text=True, timeout=60)
        result = scored.stdout if scored.returncode == 0 else json.dumps({"unscorable": scored.stderr.strip()})
    else:
        result = json.dumps({"unscorable": "the run wrote no new summary"})
    (out / "score.json").write_text(result.rstrip("\n") + "\n")
    print(json.dumps({"out": str(out), "work": str(work), "plugin": str(plugin), "exit_code": proc.returncode, "timed_out": timed_out,
                      "summary_written": fresh, "wall_seconds": elapsed,
                      "total_cost_usd": metrics["total_cost_usd"]}, indent=2))
    return 0 if proc.returncode == 0 and not timed_out and fresh else 1


if __name__ == "__main__":
    sys.exit(main())
