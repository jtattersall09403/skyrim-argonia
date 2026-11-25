#!/usr/bin/env python3
"""Bring the main tree (the tree the studio serves) level with origin/main, clearing only provably stale leftovers.

    tooling/level_main.sh [--tree DIR] [--report | --check | --line] [--auto] [--json] [--quiet]

  (no mode)  fetch, clear the stale leftovers, fast-forward to origin/main
  --report   fetch and say what a level would do; changes nothing
  --check    no fetch, no change: exit 1 when the tree holds stale leftovers a level would clear (the gate's check)
  --line     one line: whether the served tree is level (the session-start output)
  --auto     an automatic caller (lane_land, lane_commit, job end, the studio): a running job from the main tree
             defers the level to that job's end (job_guard runs it); a level that cannot be done tells an agent
             (state/agent-wake-pending) and posts or updates one owner-inbox issue, closed once the tree is level
  --json     a last line of JSON: {code, head, origin, behind, places_behind, stale, cleared, real, deferred}

A dirty file is a stale leftover, cleared, only when it is provably a copy of committed work: its content equals the
committed version at HEAD, at origin/main or any earlier committed version of that path (a tracked file: put back to
HEAD), or it is an untracked file (or a deletion) identical to what is landing. Anything else is real unlanded work:
never overwritten, named with when and by whom it was last written. Never touched: every place's `edits/` folder (the
owner's saves and notes), `.claude/settings*.json`, ignored files (out/, where the owner's autosave lives) and
anything outside the repository.

Exit: 0 level and clean; 3 level, real unlanded work left in the tree (named); 1 behind and could not level (real work
collides with what landed, or the tree has commits of its own); 4 deferred to a running job's end; 5 a passing git
lock (another command in the tree), tried again by the next caller.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path(os.environ.get("HOME", str(Path.home())))
STATE = HOME / ".argonia" / "state"
JOBS = Path(os.environ.get("JOBS_DIR", HOME / ".argonia/jobs"))
PENDING = "level-pending"          # in the job spool: the main tree to level when the job running from it ends
NEVER = (re.compile(r"^newworld/places/[^/]+/edits/"), re.compile(r"^\.claude/settings[^/]*\.json$"),
         re.compile(r"^\.claude/worktrees/"))


def git(tree: Path, *args: str, check: bool = True, binary: bool = False):
    r = subprocess.run(["git", "-C", str(tree), *args], capture_output=True, text=not binary)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args[:3])}: {(r.stderr if not binary else r.stderr.decode()).strip()}")
    return r


def out(tree: Path, *args: str) -> str:
    return git(tree, *args).stdout.strip()


def main_tree(start: Path) -> Path:
    common = Path(out(start, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return common.parent


def never(path: str) -> bool:
    return any(p.search(path) for p in NEVER)


def blob_at(tree: Path, ref: str, path: str) -> str | None:
    r = git(tree, "rev-parse", "-q", "--verify", f"{ref}:{path}", check=False)
    return r.stdout.strip() or None


def history_blobs(tree: Path, path: str, refs: list[str]) -> set[str]:
    """Every blob the path has had in the commits reachable from refs."""
    commits = git(tree, "rev-list", *refs, "--", path, check=False).stdout.split()
    if not commits:
        return set()
    r = subprocess.run(["git", "-C", str(tree), "cat-file", "--batch-check=%(objectname) %(objecttype)"],
                       input="".join(f"{c}:{path}\n" for c in commits), capture_output=True, text=True)
    return {ln.split()[0] for ln in r.stdout.splitlines() if ln.endswith(" blob")}


def status(tree: Path) -> list[tuple[str, str]]:
    """(xy, path) of every changed or untracked file, ignored ones left out."""
    raw = git(tree, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames").stdout
    items = raw.split("\0")
    return [(e[:2], e[3:]) for e in items if len(e) > 3]


def who_wrote(tree: Path, path: str) -> str:
    """When the file was last written and what was running from the main tree then (a job, or an agent's session)."""
    try:
        mt = (tree / path).stat().st_mtime
    except OSError:
        mt = None
    when = datetime.fromtimestamp(mt, timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if mt else "deleted"
    by = []
    if mt:
        for cwd in JOBS.glob("*.cwd"):
            try:
                c = Path(cwd.read_text().strip())
            except OSError:
                continue
            if not (c == tree or tree in c.parents) or (tree / ".claude/worktrees") in [c, *c.parents]:
                continue
            n = cwd.name[:-4]
            start = (JOBS / f"{n}.cmd").stat().st_mtime if (JOBS / f"{n}.cmd").exists() else 0
            rc = JOBS / f"{n}.rc"
            end = rc.stat().st_mtime if rc.exists() else time.time()
            if start - 5 <= mt <= end + 5:
                by.append(f"job {n}")
    return f"last written {when} by {', '.join(by) if by else 'an agent session working in the main tree (no job)'}"


def running_jobs(tree: Path) -> list[str]:
    sys.path.insert(0, str(HERE))
    sys.dont_write_bytecode = True
    import tidy
    tidy.JOBS = JOBS
    wts = tree / ".claude" / "worktrees"
    return [n for n, c in tidy.job_cwds(JOBS, waits=False) if tidy._inside(c, tree) and not tidy._inside(c, wts)]


def classify(tree: Path, target: str) -> tuple[list[dict], list[dict]]:
    """(stale, real): each dirty path judged against the committed versions."""
    stale, real = [], []
    refs = ["HEAD", target]
    for xy, p in status(tree):
        if never(p):
            continue
        f = tree / p
        landing = blob_at(tree, target, p)
        head = blob_at(tree, "HEAD", p)
        row = {"path": p, "xy": xy}
        if xy == "??":
            ok = f.is_file() and landing is not None and out(tree, "hash-object", "--", p) == landing
            row["fix"] = "delete"   # the fast-forward writes the landing copy, identical
        elif not f.exists() and not f.is_symlink():
            ok = landing is None    # a deletion is stale when what lands deletes it too
            row["fix"] = "head"
        elif f.is_dir():
            ok = False
        else:
            blob = out(tree, "hash-object", "--", p)
            ok = blob in {head, landing} - {None} or blob in history_blobs(tree, p, refs)
            row["fix"] = "head" if head else "unstage"
        (stale if ok else real).append(row)
    return stale, real


def clear(tree: Path, rows: list[dict]) -> None:
    for r in rows:
        p, f = r["path"], tree / r["path"]
        if r["xy"][0] not in " ?":   # staged: the index entry back to HEAD's (or out of the index)
            git(tree, "reset", "-q", "--", p, check=False)
        if r["fix"] == "delete" or r["fix"] == "unstage":
            if f.is_file() or f.is_symlink():
                f.unlink()
            continue
        mode = out(tree, "ls-tree", "HEAD", "--", p).split()[0]
        data = git(tree, "cat-file", "blob", f"HEAD:{p}", binary=True).stdout
        if f.is_symlink() or mode == "120000":
            if f.exists() or f.is_symlink():
                f.unlink()
            if mode == "120000":
                os.symlink(data.decode(), f)
                continue
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(f".{f.name}.level.tmp")
        tmp.write_bytes(data)
        os.chmod(tmp, 0o755 if mode == "100755" else 0o644)
        os.replace(tmp, f)
        git(tree, "update-index", "-q", "--refresh", check=False)


def places_of(paths: list[str]) -> list[str]:
    return sorted({p.split("/")[2] for p in paths if p.startswith("newworld/places/") and p.count("/") >= 3})


def notify(tree: Path, res: dict, real_lines: list[str]) -> None:
    """Tell an agent (agent-wake-pending) and post or update the one owner-inbox issue; once only per state."""
    STATE.mkdir(parents=True, exist_ok=True)
    mark = STATE / "level-main-issue.json"
    try:
        held = json.loads(mark.read_text())
    except (OSError, ValueError):
        held = {}
    key = "|".join(sorted(r["path"] for r in res["collide"])) + f"@{res['origin'][:12]}"
    if held.get("key") == key:
        return
    places = res["places_behind"]
    with open(STATE / "agent-wake-pending", "a") as w:
        w.write(f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ} level_main: the studio's tree {tree} is behind "
                f"origin/main ({', '.join(places) or 'no place'}): unlanded files collide; land or delete them, then "
                f"tooling/level_main.sh\n")
    body = ("The studio is not showing the latest version of "
            + (", ".join(places) if places else "some of the project's files")
            + ". Finished changes have landed, but the studio's folder holds unfinished files that an agent has not "
              "landed yet, and they stand in the way of the update. Nothing of yours is affected: your saves and your "
              "unsaved work are kept. An agent has been told and will land or clear these files; the studio updates by "
              "itself once they are gone. You do not need to do anything.\n\nThe files in the way:\n"
            + "\n".join(f"- {ln}" for ln in real_lines[:20]) + "\n")
    inbox = os.environ.get("LEVEL_MAIN_INBOX") or f"{sys.executable} {HERE / 'owner_inbox.py'}"
    bf = STATE / "level-main-issue.body"
    bf.write_text(body)
    cmd = inbox.split()
    if held.get("number"):
        cmd += ["--comment", str(held["number"]), "--body-file", str(bf)]
        num = held["number"]
    else:
        cmd += ["--post", "check", "--title", "The studio is behind: unfinished files in the way", "--body-file", str(bf)]
        num = None
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        m = re.search(r"/issues/(\d+)", r.stdout)
        num = num or (int(m.group(1)) if m else None)
        mark.write_text(json.dumps({"key": key, "number": num}))
    else:
        print(f"level_main: the owner-inbox post failed: {r.stderr.strip()[-300:]}", file=sys.stderr)


def resolved(tree: Path) -> None:
    """The tree is level: close the issue a failed level posted, if any."""
    mark = STATE / "level-main-issue.json"
    try:
        held = json.loads(mark.read_text())
    except (OSError, ValueError):
        return
    if held.get("number"):
        inbox = os.environ.get("LEVEL_MAIN_INBOX") or f"{sys.executable} {HERE / 'owner_inbox.py'}"
        r = subprocess.run(inbox.split() + ["--close", str(held["number"]), "--commit", out(tree, "rev-parse", "HEAD")],
                           capture_output=True, text=True)
        if r.returncode:
            return
    mark.unlink(missing_ok=True)


def level(tree: Path, mode: str, auto: bool) -> dict:
    res = {"code": 0, "tree": str(tree), "stale": [], "cleared": [], "real": [], "collide": [], "deferred": "",
           "places_behind": [], "behind": 0}
    branch = git(tree, "symbolic-ref", "-q", "--short", "HEAD", check=False).stdout.strip()
    no_origin = git(tree, "rev-parse", "-q", "--verify", "origin/main", check=False).returncode
    if mode == "check" and (branch != "main" or no_origin):
        return res   # nothing to judge stale against: not the studio's tree
    if branch != "main":
        res.update(code=1, why=f"the main tree is not on main ({branch or 'detached'})")
        return res
    if mode not in ("check", "line-nofetch"):
        if git(tree, "fetch", "-q", "origin", check=False).returncode:
            res["fetch_failed"] = True
    target = "origin/main"
    head, origin = out(tree, "rev-parse", "HEAD"), out(tree, "rev-parse", target)
    res.update(head=head, origin=origin)
    res["behind"] = int(out(tree, "rev-list", "--count", f"HEAD..{target}"))
    ahead = int(out(tree, "rev-list", "--count", f"{target}..HEAD"))
    incoming = set(out(tree, "diff", "--name-only", "--no-renames", "HEAD", target).splitlines()) if res["behind"] else set()
    res["places_behind"] = places_of(sorted(incoming))
    stale, real = classify(tree, target)
    res["stale"] = [r["path"] for r in stale]
    res["real"] = [r["path"] for r in real]
    res["collide"] = [r for r in real if r["path"] in incoming]
    res["real_lines"] = [f"{r['path']} ({who_wrote(tree, r['path'])})" for r in real]
    if ahead:
        res.update(code=1, why=f"the main tree has {ahead} commit(s) not on origin/main")
        return res
    if mode in ("report", "check", "line", "line-nofetch"):
        res["code"] = (1 if res["behind"] or stale else 3 if real else 0) if mode != "check" else (1 if stale else 0)
        return res
    if auto and (jobs := running_jobs(tree)) and (res["behind"] or stale):
        JOBS.mkdir(parents=True, exist_ok=True)
        (JOBS / PENDING).write_text(str(tree) + "\n")
        res.update(code=4, deferred=", ".join(jobs))
        return res
    clear(tree, stale)
    res["cleared"] = res["stale"]
    hook = os.environ.get("LEVEL_MAIN_TEST_HOOK")   # the tests write the owner's autosave here, mid-level
    if hook:
        subprocess.run(hook, shell=True, check=False)
    if res["behind"]:
        if res["collide"]:
            res.update(code=1, why="real unlanded work collides with what landed")
            return res
        m = git(tree, "merge", "-q", "--ff-only", target, check=False)
        if m.returncode:
            busy = "index.lock" in m.stderr or "Unable to create" in m.stderr
            res.update(code=5 if busy else 1, why=m.stderr.strip()[-400:])
            return res
    res["code"] = 3 if real else 0
    res["head"] = out(tree, "rev-parse", "HEAD")
    if (JOBS / PENDING).exists() and (JOBS / PENDING).read_text().strip() == str(tree):
        (JOBS / PENDING).unlink(missing_ok=True)
    return res


def say(res: dict, mode: str, quiet: bool) -> None:
    short = res.get("head", "")[:9]
    if mode in ("line", "line-nofetch"):
        if res["code"] == 1 and res.get("why"):
            print(f"served tree: NOT level: {res['why']}")
        elif res["behind"] or res["stale"]:
            print(f"served tree: NOT level: {res['behind']} commit(s) behind origin/main, {len(res['stale'])} stale "
                  f"leftover(s); tooling/level_main.sh levels it")
        else:
            print(f"served tree: level with origin/main ({short})"
                  + (f"; {len(res['real'])} unlanded file(s) in it" if res["real"] else ""))
        return
    lines = []
    if mode == "check":
        if res["stale"]:
            lines.append(f"level_main: the main tree holds {len(res['stale'])} stale leftover(s), copies of committed "
                         f"work: run tooling/level_main.sh to clear them (it overwrites nothing else)")
            lines += [f"  stale: {p}" for p in res["stale"][:20]]
        print("\n".join(lines) if lines else "level_main: no stale leftovers in the main tree")
        return
    verb = "would clear" if mode == "report" else "cleared"
    if res["stale"]:
        lines.append(f"{verb} {len(res['stale'])} stale leftover(s): " + ", ".join(res["stale"][:12])
                     + (" ..." if len(res["stale"]) > 12 else ""))
    for ln in res.get("real_lines", []):
        lines.append(f"left (real unlanded work): {ln}")
    c = res["code"]
    if mode == "report":
        if res.get("why"):
            lines.append(f"main tree NOT level: {res['why']}")
        elif res["behind"] or res["stale"]:
            lines.append(f"main tree is {res['behind']} commit(s) behind origin/main"
                         + (f" (places {', '.join(res['places_behind'])})" if res["places_behind"] else "")
                         + ("; real work in the way: " + ", ".join(r["path"] for r in res["collide"]) if res["collide"]
                            else "; a level would fast-forward it"))
        else:
            lines.append("main tree is level with origin/main")
        lines.append("report only: nothing changed")
    elif c == 4:
        lines.append(f"main tree left as is: job {res['deferred']} runs from it; it is levelled when that job ends")
    elif c == 1:
        lines.append(f"main tree NOT level: {res.get('why', '')}; behind origin/main by {res['behind']}"
                     + (f" (places {', '.join(res['places_behind'])})" if res["places_behind"] else ""))
        lines += [f"  in the way: {r['path']}" for r in res["collide"]]
    elif c == 5:
        lines.append("main tree not moved this time: another git command holds its lock; the next caller levels it")
    else:
        lines.append(f"main tree is level with origin/main at {short}")
    if not quiet or c not in (0,):
        print("\n".join(lines))


def run(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tree")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--report", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--line", action="store_true")
    g.add_argument("--pending", action="store_true", help="job_guard at a job's end: level only if a level waits")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if a.pending:
        pf = JOBS / PENDING
        if not pf.exists():
            return 0
        tree = Path(pf.read_text().strip())
        a.auto = True
    else:
        tree = main_tree(Path(a.tree).resolve() if a.tree else HERE)
    mode = "report" if a.report else "check" if a.check else ("line-nofetch" if a.no_fetch else "line") if a.line else "level"
    if a.check and os.environ.get("STUDIO_OWNER_SAVE") == "1":
        return 0   # the owner's save never waits on an agent's leftovers
    lock = (tree / ".git" / "argonia-level.lock")
    with open(lock, "a+") as lf:
        if mode == "level":
            fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            res = level(tree, mode, a.auto)
        except RuntimeError as e:
            res = {"code": 0 if mode == "check" else 1, "why": str(e), "stale": [], "real": [], "collide": [], "behind": 0, "places_behind": []}
    say(res, mode, a.quiet)
    if mode == "level" and a.auto:
        if res["code"] == 1:
            notify(tree, res, res.get("real_lines") or [res.get("why", "")])
        elif res["code"] in (0, 3):
            resolved(tree)
    if a.json:
        print(json.dumps({k: res.get(k) for k in ("code", "head", "origin", "behind", "places_behind", "stale",
                                                  "cleared", "real", "deferred", "why")}))
    return res["code"]


if __name__ == "__main__":
    sys.exit(run())
