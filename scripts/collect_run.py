#!/usr/bin/env python3
"""Snapshot a run's session logs, spec, plan and commit list into runs/<id>/.

Usage: scripts/collect_run.py <run-id> [<run-id> ...]   (or --all)

Safe to re-run while a session is still going; it overwrites the snapshot.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def expand(p):
    return Path(p).expanduser() if p else None


def git(checkout, *args):
    return subprocess.run(
        ["git", "-C", str(checkout), *args], capture_output=True, text=True
    )


def copy_sessions(run, out):
    dest = out / "sessions"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for i, s in enumerate(run["sessions"]):
        src = expand(s["path"])
        if not src.exists():
            print(f"  missing session: {src}")
            continue
        if src.is_dir():
            shutil.copytree(src, dest / s["role"])
        else:
            name = src.name if s["role"] == "main" else f"{s['role']}-{i}-{src.name}"
            shutil.copy2(src, dest / name)
        print(f"  session: {src.name}")


def copy_doc(run, key, out):
    rel = run.get(key)
    if not rel:
        return
    checkout = expand(run.get("worktree") or run["checkout"])
    ref = run.get("implementationBranch") or run["branch"]
    res = git(checkout, "show", f"{ref}:{rel}")
    if res.returncode == 0:
        text = res.stdout
    elif (checkout / rel).exists():
        text = (checkout / rel).read_text()
    else:
        print(f"  missing {key}: {rel}")
        return
    (out / f"{key}.md").write_text(text)
    print(f"  {key}: {rel}")


def write_commits(run, out):
    checkout = expand(run.get("worktree") or run["checkout"])
    ref = run.get("implementationBranch") or run["branch"]
    res = git(checkout, "log", "--reverse", "--format=%h %ad %s", "--date=iso", f"main..{ref}")
    if res.returncode == 0:
        (out / "commits.txt").write_text(res.stdout)
        print(f"  commits: {len(res.stdout.splitlines())}")


def collect(run):
    print(run["id"])
    if not run.get("checkout") or not run.get("branch"):
        print("  skipped: no checkout/branch recorded yet")
        return
    out = ROOT / "runs" / run["id"]
    out.mkdir(parents=True, exist_ok=True)
    copy_sessions(run, out)
    copy_doc(run, "spec", out)
    copy_doc(run, "plan", out)
    write_commits(run, out)


def main():
    runs = json.loads((ROOT / "data" / "runs.json").read_text())["runs"]
    wanted = sys.argv[1:]
    if not wanted:
        sys.exit(__doc__)
    for run in runs:
        if "--all" in wanted or run["id"] in wanted:
            collect(run)


if __name__ == "__main__":
    main()
