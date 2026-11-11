#!/usr/bin/env python3
"""The one tidy of the build machine's disk and the private bucket (docs/machine-moves.md, "Tidying is automatic").

Run through tooling/disk.sh:  tidy [--dry-run] [--disk-only] [--bucket] [--quiet]   |   landed <worktree>

Deletes, never archives. Safe to interrupt and to run twice: every step re-reads the state it acts on, and a
thing is removed only when a named rule proves nothing needs it. A lane worktree goes only when nothing works in
it, nothing in it changed for IDLE_H hours and every file it would still change on main is already there.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAIN = Path(__file__).resolve().parent.parent  # the tree this file is in; main_tree() finds the main one
HOME = Path(os.environ.get("HOME", "/home/ubuntu"))
BUCKET = os.environ.get("ARGONIA_BUCKET", "argonia-private-050977237313")
REF = os.environ.get("TIDY_REF", "origin/main")
IDLE_H = float(os.environ.get("IDLE_H", "3"))          # a worktree untouched this long is idle
LOUD_H = float(os.environ.get("TIDY_LOUD_H", "24"))    # a kept worktree older than this is shouted at session start
JOB_DAYS = float(os.environ.get("TIDY_JOB_DAYS", "2"))  # job logs and scratch older than this go
SESSION_DAYS = float(os.environ.get("TIDY_SESSION_DAYS", "3"))  # a session whose transcript is this old has ended
EVICT_GB = float(os.environ.get("TIDY_EVICT_GB", "1"))  # cached mod archives go once they hold this much
FLOOR_GB = float(os.environ.get("DISK_FLOOR_GB", "15"))  # job_guard.sh run tidies the disk first under this
BUCKET_EVERY_H = float(os.environ.get("TIDY_BUCKET_EVERY_H", "24"))
STATE = Path(os.environ.get("TIDY_STATE", HOME / ".argonia/state"))
JOBS = Path(os.environ.get("JOBS_DIR", HOME / ".argonia/jobs"))

LANE_BRANCH = "worktree-"  # the Agent tool names a lane's branch worktree-<its worktree>

# Trees a tool writes whole from its sources (record YAML whose file names carry form ids, the read-back list, the
# story database). A lane's copy counts as landed when main changed the tree after the lane last wrote in it: main's
# tree then comes from a later run of the same generator. Place files are not here: they are edited by hand.
GENERATED = ("plugin/Argonia", "docs/research/skyrim/argonia-esp-records.md", "newworld/story/data/db")


os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")  # reading a worktree must not rewrite its index


def git(cwd, *args, check=True, env=None, text=True, input=None):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=text, env=env, input=input)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip() if text else r.stderr!r}")
    return r


# ---------------------------------------------------------------------------------------------- worktrees

def snapshot(wt: Path) -> str:
    """A commit of the worktree exactly as it stands (commits, edits, untracked files), made through a
    scratch index: the worktree, its index and its branch are not touched."""
    idx = git(wt, "rev-parse", "--git-path", "index").stdout.strip()
    idx = Path(idx) if os.path.isabs(idx) else wt / idx
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "index"
        if idx.exists():
            shutil.copy(idx, scratch)
        env = {**os.environ, "GIT_INDEX_FILE": str(scratch)}
        git(wt, "add", "-A", env=env)
        tree = git(wt, "write-tree", env=env).stdout.strip()
    env = {**os.environ, "GIT_AUTHOR_NAME": "tidy", "GIT_AUTHOR_EMAIL": "tidy@local",
           "GIT_COMMITTER_NAME": "tidy", "GIT_COMMITTER_EMAIL": "tidy@local"}
    return git(wt, "commit-tree", tree, "-p", "HEAD", "-m", "tidy snapshot", env=env).stdout.strip()


def _blob(repo, rev, path):
    r = git(repo, "rev-parse", "-q", "--verify", f"{rev}:{path}", check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def _merge_keeps(repo, ours, base, theirs, tmp) -> bool:
    """True when merging the lane's change (base -> theirs) into `ours` leaves `ours` as it is."""
    names = []
    for i, b in enumerate((ours, base, theirs)):
        p = Path(tmp) / f"m{i}"
        p.write_bytes(git(repo, "cat-file", "blob", b, text=False).stdout if b else b"")
        names.append(str(p))
    r = subprocess.run(["git", "merge-file", "-p", *names], capture_output=True)
    return r.returncode == 0 and r.stdout == Path(names[0]).read_bytes()


def _generated(path):
    return next((g for g in GENERATED if path == g or path.startswith(g + "/")), None)


def _text(repo, blob):
    """A blob's text lower-cased, every run of white space one space: a re-wrapped paragraph compares equal."""
    return b" ".join(git(repo, "cat-file", "blob", blob, text=False).stdout.lower().split()) if blob else b""


def _added_phrases(repo, base, theirs, ctx=4):
    """The runs of words the lane added to a file (base -> theirs), lower-cased, one per clause. A run
    shorter than `ctx` words is given as two phrases, padded with the words before it and with the words after
    it: either may stand on main."""
    empty = git(repo, "hash-object", "-w", "-t", "blob", "--stdin", input="").stdout.strip()
    raw = git(repo, "diff", "--word-diff=porcelain", base or empty, theirs, text=False).stdout
    out, words = [], []  # words: (word, added) of one hunk

    def flush():
        i = 0
        while i < len(words):
            if not words[i][1]:
                i += 1
                continue
            j = i
            while j < len(words) and words[j][1]:
                j += 1
                if words[j - 1][0][-1:] in b".;:":
                    break  # a run ends with its clause: main may have landed the clauses apart
            run, need = [w for w, _ in words[i:j]], max(0, ctx - (j - i))
            before = [w for w, _ in words[max(0, i - need):i]] + run
            after = run + [w for w, _ in words[j:j + need]]
            out.append({b" ".join(before), b" ".join(after)} if need else {b" ".join(run)})
            i = j
        words.clear()

    body = False
    for ln in raw.split(b"\n"):
        if ln.startswith(b"@@"):
            body = True
            flush()
        elif body and ln[:1] in (b" ", b"+"):
            words.extend((w, ln[:1] == b"+") for w in ln[1:].lower().split())
    flush()
    return out


def unlanded(main: Path, wt: Path, ref: str = REF) -> list[tuple[str, str]]:
    """The files of a worktree whose content is not on `ref`, each with the reason. Empty: all landed.

    By content, never by commit id: the worktree as it stands (commits, edits, untracked files) is merged into
    `ref`, and a file the merge would not change is landed. A file it would change is still landed when
    - `ref`'s history since the fork held the lane's version, or took the lane's change, and then moved on;
    - every run of words the lane added stood in the file on `ref` at some point since the fork (the change
      landed among other edits, or was re-wrapped);
    - it lies in a generated tree that `ref` regenerated after the lane last wrote in it."""
    return unlanded_commit(main, snapshot(wt), ref, wt)


def unlanded_commit(main: Path, snap: str, ref: str = REF, wt: Path | None = None) -> list[tuple[str, str]]:
    """unlanded() for one commit: a worktree's snapshot, or the tip of a lane branch that has no worktree."""
    base = git(main, "merge-base", ref, snap).stdout.strip()
    mt = git(main, "merge-tree", "--write-tree", "--no-messages", "--name-only", ref, snap, check=False)
    if mt.returncode not in (0, 1):
        raise RuntimeError(f"merge-tree: {mt.stderr.strip()}")
    tree = mt.stdout.split("\n", 1)[0].strip()
    diff = git(main, "diff", "--name-only", "--no-renames", "-z", ref, tree).stdout
    files = [x for x in diff.split("\0") if x]
    # generated trees first, one decision per tree
    stale = {}
    for g in {_generated(f) for f in files} - {None}:
        t_main = git(main, "log", "-1", "--format=%ct", f"{base}..{ref}", "--", g).stdout.strip()
        t_lane = git(main, "log", "-1", "--format=%ct", f"{base}..{snap}^" if wt else f"{base}..{snap}", "--", g).stdout.strip()
        dirty = git(wt, "status", "--porcelain", "-z", "--no-renames", "-uall", "--", g).stdout if wt else ""
        mtimes = [(wt / e[3:]).lstat().st_mtime for e in dirty.split("\0") if e and (wt / e[3:]).exists()]
        stale[g] = bool(t_main) and int(t_main) > max([float(t_lane or 0), *mtimes])
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            if stale.get(_generated(f)):
                continue
            why = _file_unlanded(main, ref, base, snap, f, tmp)
            if why:
                out.append((f, why))
    return out


def _file_unlanded(main, ref, base, snap, f, tmp):
    v, b = _blob(main, snap, f), _blob(main, base, f)
    # every version the file had on main since the fork, newest first
    hist = git(main, "log", "--format=%H", "-n", "200", f"{base}..{ref}", "--", f).stdout.split()
    blobs = [_blob(main, c, f) for c in hist]
    for h in blobs:
        if h == v:
            return None  # main held exactly this version (or this deletion), then moved on
        if h and v and _merge_keeps(main, h, b, v, tmp):
            return None  # main took this change, then moved on
    if v is None:
        return "deleted here, still on main"
    texts = [_text(main, h) for h in dict.fromkeys([*blobs, b]) if h]  # the fork's version stood on main too
    added = _added_phrases(main, b, v)
    missing = [ph for ph in added if not any(p in t for p in ph for t in texts)]
    if added and not missing:
        return None  # every run of words the lane added stood on main, then was reworded round it
    n = len(missing)
    if _blob(main, ref, f) is None:
        return f"not on main ({n} passages main never held)"
    return f"{n} added passages main never held"


def main_tree(start: Path = MAIN) -> Path:
    """The main working tree, also when this file runs from a lane's worktree."""
    common = git(start, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return Path(common).parent


def worktrees(main: Path) -> list[dict]:
    """Every lane worktree: {path, branch, lock}. The main tree and lane_commit's scratch trees are not lanes."""
    out, cur = [], {}
    for ln in git(main, "worktree", "list", "--porcelain").stdout.split("\n") + [""]:
        if ln.startswith("worktree "):
            cur = {"path": Path(ln[9:]), "branch": None, "lock": None}
        elif ln.startswith("branch "):
            cur["branch"] = ln[7:].removeprefix("refs/heads/")
        elif ln.startswith("locked"):
            cur["lock"] = ln[7:] or "locked"
        elif not ln and cur:
            if cur["path"] != main and not cur["path"].parent.name.startswith(("lane_commit.", "lane_cs.", "lane_land.")):
                out.append(cur)
            cur = {}
    return out


def _alive(pid: int, start: str | None = None) -> bool:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return False
    return start is None or stat.rsplit(")", 1)[1].split()[19] == start


def lock_live(lock: str | None) -> bool:
    """A worktree's lock holds while the session that took it lives ("... (pid N start T)"); a lock whose
    process is gone is a dead session's. A lock that names no process is someone's deliberate hold."""
    if not lock:
        return False
    import re
    m = re.search(r"\(pid (\d+)(?: start (\d+))?\)", lock)
    return _alive(int(m[1]), m[2]) if m else True


def job_waits(jobs: Path, name: str) -> bool:
    """A job whose whole command is a sleep only waits (the lead's idle hold): it reads and writes no file."""
    try:
        argv = [a for a in (jobs / f"{name}.cmd").read_bytes().split(b"\0") if a]
    except OSError:
        return False
    return bool(argv) and os.path.basename(argv[0]) == b"sleep"


def job_cwds(jobs: Path = None, waits: bool = True) -> list[tuple[str, Path]]:
    """(name, cwd) of every job_guard job that is queued or running; waits=False leaves out a job that only
    waits (job_waits): it holds its folder in place and blocks no change to the files there."""
    jobs = jobs or JOBS
    out = []
    for st in jobs.glob("*.state"):
        name = st.name[:-6]
        try:
            if st.read_text().strip() not in ("queued", "running"):
                continue
            pid = int((jobs / f"{name}.pid").read_text().strip() or 0)
            if not _alive(pid):   # a dead job (killed, or its machine stopped) holds nothing, whatever its state file says
                continue
            if not waits and job_waits(jobs, name):
                continue
            out.append((name, Path((jobs / f"{name}.cwd").read_text().strip())))
        except (OSError, ValueError):
            continue
    return out


def _inside(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def busy(wt: Path, lock: str | None = None) -> str | None:
    """Why a worktree is in use: its session's lock, a process standing in it, or a job started from it."""
    if lock_live(lock):
        return "its lane's session is live"
    for p in Path("/proc").glob("[0-9]*"):
        try:
            if _inside(Path(os.readlink(p / "cwd")), wt):
                return f"process {p.name} works in it"
        except OSError:
            continue
    for name, cwd in job_cwds():
        if _inside(cwd, wt):
            return f"job {name} runs from it"
    return None


def idle_hours(wt: Path) -> float:
    """Hours since anything in the worktree last changed: its files, its HEAD, its last commit. Never the
    index or the reflog: reading a status rewrites the one, a fetch's housekeeping the other."""
    newest = float(git(wt, "log", "-1", "--format=%ct", "HEAD", check=False).stdout.strip() or 0)
    gd = git(wt, "rev-parse", "--path-format=absolute", "--git-dir", check=False).stdout.strip()
    try:
        newest = max(newest, (Path(gd) / "HEAD").stat().st_mtime)
    except OSError:
        pass
    for root, dirs, files in os.walk(wt):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".pytest_cache", ".ruff_cache")]
        for n in (*files, *dirs):
            try:
                newest = max(newest, os.lstat(os.path.join(root, n)).st_mtime)
            except OSError:
                pass
    return (time.time() - newest) / 3600


def remove_worktree(main: Path, w: dict, log) -> None:
    """Remove a worktree whose content is proved landed, with its branch (local and on origin). The proof is
    marked first, so an interrupted removal finishes on the next run instead of reading as deleted files."""
    wt, br = w["path"], w["branch"]
    gd = git(wt, "rev-parse", "--path-format=absolute", "--git-dir", check=False).stdout.strip()
    if gd:
        (Path(gd) / "tidy-landed").write_text(time.strftime("%FT%TZ", time.gmtime()))
    if w["lock"]:
        git(main, "worktree", "unlock", str(wt), check=False)
    git(main, "worktree", "remove", "--force", str(wt), check=False)
    if wt.exists():
        shutil.rmtree(wt, ignore_errors=True)
    git(main, "worktree", "prune")
    if br and br not in ("main", "master"):
        git(main, "branch", "-D", br, check=False)
        if git(main, "rev-parse", "-q", "--verify", f"refs/remotes/origin/{br}", check=False).returncode == 0:
            git(main, "push", "-q", "origin", "--delete", br, check=False)
    log(f"removed worktree {wt.name} and its branch: everything in it is on main")


def tidy_worktrees(main: Path, dry: bool, quiet: bool, log, ref: str = REF) -> list[str]:
    """Returns the lines worth a reader's attention (removed, or kept with unlanded work)."""
    said = []

    def say(s, always=True):
        if always or not quiet:
            log(s)
        if always:
            said.append(s)

    for w in worktrees(main):
        wt = w["path"]
        if not wt.is_dir():
            continue
        gd = git(wt, "rev-parse", "--path-format=absolute", "--git-dir", check=False).stdout.strip()
        if gd and (Path(gd) / "tidy-landed").exists() and not lock_live(w["lock"]):
            say(f"would finish removing {wt.name}" if dry else f"finishing the removal of {wt.name}")
            if not dry:
                remove_worktree(main, w, lambda s: None)
            continue
        why = busy(wt, w["lock"])
        if why:
            say(f"keep {wt.name}: in use ({why})", always=False)
            continue
        idle = idle_hours(wt)
        if idle < IDLE_H:
            say(f"keep {wt.name}: changed {idle:.1f} h ago (idle after {IDLE_H:g} h)", always=False)
            continue
        try:
            left = unlanded(main, wt, ref)
        except RuntimeError as e:
            say(f"keep {wt.name}: could not be read ({e})")
            continue
        if left:
            age = f"{idle / 24:.1f} days" if idle >= 48 else f"{idle:.0f} h"
            head = "; ".join(f"{f} ({why})" for f, why in left[:3]) + (f"; and {len(left) - 3} more" if len(left) > 3 else "")
            loud = f"ABANDONED WORK, idle {age}: decide it (land it with tooling/lane_land.sh, or delete it). " if idle >= LOUD_H else ""
            say(f"{loud}keep {wt.name} (idle {age}): {len(left)} files not on main: {head}")
        elif dry:
            say(f"would remove worktree {wt.name} and branch {w['branch']} (idle {idle:.0f} h, everything in it is on main)")
        else:
            remove_worktree(main, w, say)
    if not dry:
        git(main, "worktree", "prune", check=False)
    # lane branches whose worktree is gone already: the same rule on the branch's tip
    held = {w["branch"] for w in worktrees(main)}
    refs = git(main, "for-each-ref", "--format=%(refname:short) %(committerdate:unix)", "refs/heads/").stdout.split("\n")
    for br, t in (ln.split() for ln in refs if ln.strip()):
        idle = (time.time() - int(t)) / 3600
        if not br.startswith(LANE_BRANCH) or br in held or idle < IDLE_H:
            continue
        left = unlanded_commit(main, br, ref)
        if left:
            age = f"{idle / 24:.1f} days" if idle >= 48 else f"{idle:.0f} h"
            head = "; ".join(f"{f} ({why})" for f, why in left[:3]) + (f"; and {len(left) - 3} more" if len(left) > 3 else "")
            loud = "ABANDONED WORK: decide it (land it, or delete the branch). " if idle >= LOUD_H else ""
            say(f"{loud}keep branch {br} (no worktree, last commit {age} ago): {len(left)} files not on main: {head}")
        elif dry:
            say(f"would delete branch {br} (no worktree, everything on it is on main)")
        else:
            git(main, "branch", "-D", br, check=False)
            if git(main, "rev-parse", "-q", "--verify", f"refs/remotes/origin/{br}", check=False).returncode == 0:
                git(main, "push", "-q", "origin", "--delete", br, check=False)
            say(f"deleted branch {br}: no worktree, everything on it is on main")
    return said


# --------------------------------------------------------------------------------------------- the disk

def _size(p: Path) -> int:
    if p.is_symlink() or p.is_file():
        return p.lstat().st_size
    n = 0
    for root, _, files in os.walk(p):
        for f in files:
            try:
                n += os.lstat(os.path.join(root, f)).st_size
            except OSError:
                pass
    return n


def _newest(p: Path) -> float:
    try:
        t = p.lstat().st_mtime
    except OSError:
        return time.time()
    if p.is_dir() and not p.is_symlink():
        for root, dirs, files in os.walk(p):
            for n in (*files, *dirs):
                try:
                    t = max(t, os.lstat(os.path.join(root, n)).st_mtime)
                except OSError:
                    pass
    return t


def _rm(p: Path):
    if p.is_dir() and not p.is_symlink():
        shutil.rmtree(p, ignore_errors=True)
    else:
        p.unlink(missing_ok=True)


def stale_jobs(jobs: Path, now: float, days: float = JOB_DAYS) -> list[tuple[str, list[Path]]]:
    """The spool files of each job that ended more than `days` ago. A queued or running job, a job whose
    process lives, the counters, the locks and the slots are never listed."""
    groups: dict[str, list[Path]] = {}
    exts = ("log.interrupted", "boot", "cmd", "cwd", "env", "log", "pid", "rc", "seq", "state", "unit", "gpu", "lane",
            "machine", "started")
    for f in jobs.iterdir():
        if f.name.startswith(".") or not f.is_file():
            continue
        if f.name.startswith("RESUMED-"):
            groups.setdefault(f.name, []).append(f)
            continue
        ext = next((e for e in exts if f.name.endswith("." + e)), None)
        if ext:
            groups.setdefault(f.name[: -len(ext) - 1], []).append(f)
    out = []
    for name, files in sorted(groups.items()):
        if now - max(f.stat().st_mtime for f in files) < days * 86400:
            continue
        if not name.startswith("RESUMED-"):
            state = (jobs / f"{name}.state").read_text().strip() if (jobs / f"{name}.state").exists() else ""
            try:
                pid = int((jobs / f"{name}.pid").read_text().strip())
            except (OSError, ValueError):
                pid = 0
            if _alive(pid) or (state in ("queued", "running") and not (jobs / f"{name}.rc").exists()):
                continue  # live, or cut off and owed a relaunch by job_resume.sh
        out.append((name, files))
    return out


def session_procs() -> set[str]:
    """The session ids live processes carry (CLAUDE_CODE_SESSION_ID in the environment of every shell, job and
    subagent a session starts)."""
    out = set()
    for p in Path("/proc").glob("[0-9]*"):
        try:
            env = (p / "environ").read_bytes()
        except OSError:
            continue
        i = env.find(b"CLAUDE_CODE_SESSION_ID=")
        if i >= 0 and (i == 0 or env[i - 1] == 0):
            out.add(env[i + 23:].split(b"\0", 1)[0].decode(errors="replace"))
    return out


def session_live(sid: str, now: float, procs: set[str], days: float = SESSION_DAYS, projects: Path = None) -> str | None:
    """Why a session counts as live, or None: a process of it runs, or its transcript (its own file or any file
    of its folder, under whichever project holds it) was written within `days`. A session that waits on a long
    job or on its owner writes nothing for hours and is still live: only days of silence end it."""
    if sid in procs:
        return "a process of the session runs"
    projects = projects or HOME / ".claude/projects"
    newest = 0.0
    for t in (*projects.glob(f"*/{sid}.jsonl"), *projects.glob(f"*/{sid}")):
        newest = max(newest, _newest(t))
    if now - newest < days * 86400:
        return f"its transcript was written under {days:g} days ago"
    return None


def stale_scratch(now: float, days: float = JOB_DAYS, tmp: Path = None, projects: Path = None,
                  procs: set[str] = None) -> list[tuple[Path, str]]:
    """Scratch nothing reads any more. A session's scratch folder under /tmp/claude-<uid>/<project>/<session> goes
    only when the session is not live (session_live) and nothing in it changed for `days`; our tools' own temp
    folders under /tmp when nothing in them changed for `days`. Never a folder a process stands in."""
    tmp, uid, out = tmp or Path(tempfile.gettempdir()), os.getuid(), []
    procs = session_procs() if procs is None else procs
    cand: list[tuple[Path, str]] = []
    for base in tmp.glob(f"claude-{uid}"):
        for d in base.iterdir():
            if d.is_dir() and not d.is_symlink() and d.name.startswith("-"):  # a project's folder: one per session
                cand += [(s, "a past session's scratch") for s in d.iterdir()
                         if not session_live(s.name, now, procs, projects=projects)]
            else:
                cand.append((d, "session scratch"))
    for pat, what in (("lane_commit.*", "lane_commit scratch"), ("lane_cs.*", "lane_commit build scratch"),
                      ("lane_land.*", "lane_land scratch"), ("studio-shots-*", "studio test stills"),
                      ("studio-fixture-*", "studio test fixture"), ("pytest-of-*/pytest-*", "pytest temp")):
        cand += [(p, what) for p in tmp.glob(pat)]
    cwds = set()
    for p in Path("/proc").glob("[0-9]*"):
        try:
            cwds.add(Path(os.readlink(p / "cwd")))
        except OSError:
            pass
    for p, what in cand:
        try:
            if p.lstat().st_uid != uid or now - _newest(p) < days * 86400:
                continue
        except OSError:
            continue
        if any(_inside(c, p) for c in cwds):
            continue
        out.append((p, what))
    return out


def tidy_disk(main: Path, dry: bool, log) -> int:
    now, freed = time.time(), 0
    verb = "would delete" if dry else "deleted"
    jobs = stale_jobs(JOBS, now) if JOBS.is_dir() else []
    if jobs:
        n = sum(sum(f.stat().st_size for f in fs) for _, fs in jobs)
        freed += n
        log(f"{verb} the spool of {len(jobs)} jobs ended over {JOB_DAYS:g} days ago ({n / 2**20:.0f} MB, {JOBS})")
        if not dry:
            for _, fs in jobs:
                for f in fs:
                    f.unlink(missing_ok=True)
    for p, what in stale_scratch(now):
        n = _size(p)
        freed += n
        log(f"{verb} {p} ({what}, untouched over {JOB_DAYS:g} days, {n / 2**20:.0f} MB)")
        if not dry:
            _rm(p)
    # cached mod archives the bucket's mods/ holds: stack.py evict checks each against the manifest's hash, uploads
    # what the bucket lacks, then deletes the local copy; a restage fetches it back. Archives no manifest row names
    # stay. Only once they are worth it (EVICT_GB) or the disk is under its floor: a small cache saves refetching.
    mods, stack = HOME / ".argonia/mods", main / "infra/gpu-box/stack.py"
    py = HOME / ".argonia/venv/bin/python"
    if mods.is_dir() and stack.exists() and py.exists():
        r = subprocess.run([str(py), "-c", "import sys,json; sys.path.insert(0, sys.argv[1]); import stack; "
                            "print(sum(stack.archive_path(m).stat().st_size for m in stack.manifest()['mods'] "
                            "if stack.archive_path(m).exists()))", str(stack.parent)], capture_output=True, text=True)
        n = int(r.stdout.strip() or 0) if r.returncode == 0 else 0
        if n > EVICT_GB * 2**30 or (n and free_gb() < FLOOR_GB):
            freed += n
            log(f"{verb} {n / 2**30:.1f} GB of cached mod archives the bucket's mods/ holds (stack.py evict; a restage fetches them back)")
            if not dry:
                subprocess.run([str(py), str(stack), "evict"], capture_output=True, text=True)
    return freed


# ------------------------------------------------------------------------------------------- the bucket

PRUNED = ("nw/terrain/", "nw/plugin/", "nw/lod/")  # the only prefixes anything is ever deleted from
GRACE_H = float(os.environ.get("TIDY_BUCKET_GRACE_H", "24"))  # nothing younger goes: a job may still be writing it


def bucket_plan(objects: list[dict], refs: dict[str, dict[str, str]], now: float, grace_h: float = GRACE_H):
    """objects: [{key, size, mtime}]. refs: {prefix: {build id: why it is kept}}.
    Returns (delete, keep, other): builds as (prefix + id, bytes, [keys], why); other: {prefix: (count, bytes)}.
    A build under a pruned prefix is kept when a reference names it, when it is the newest there, or when any
    object of it is younger than the grace; every other build goes. Nothing outside PRUNED is ever deleted."""
    builds: dict[tuple[str, str], list[dict]] = {}
    other: dict[str, list[int]] = {}
    for o in objects:
        pre = next((p for p in PRUNED if o["key"].startswith(p)), None)
        if pre is None:
            top = "/".join(o["key"].split("/")[:2 if o["key"].startswith("nw/") else 1]) + "/"
            c = other.setdefault(top, [0, 0])
            c[0] += 1
            c[1] += o["size"]
            continue
        bid = o["key"][len(pre):].split("/")[0]
        bid = bid[:-4] if bid.endswith(".tar") else bid
        builds.setdefault((pre, bid), []).append(o)
    newest = {}
    for (pre, bid), objs in builds.items():
        t = max(o["mtime"] for o in objs)
        if pre not in newest or t > newest[pre][1]:
            newest[pre] = (bid, t)
    delete, keep = [], []
    for (pre, bid), objs in sorted(builds.items()):
        size, keys, t = sum(o["size"] for o in objs), [o["key"] for o in objs], max(o["mtime"] for o in objs)
        why = refs.get(pre, {}).get(bid)
        if not why and newest[pre][0] == bid:
            why = "the newest there"
        if not why and now - t < grace_h * 3600:
            why = f"written under {grace_h:g} h ago"
        if why:
            keep.append((pre + bid, size, keys, why))
        else:
            delete.append((pre + bid, size, keys, "no reference names it and a newer one exists"))
    return delete, keep, {k: tuple(v) for k, v in other.items()}


def _json(p: Path):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def bucket_refs(main: Path, objects: list[dict]) -> dict[str, dict[str, str]]:
    """What the repo, the build outputs and the play machine's records name, read from the main tree and from
    every lane worktree (a lane may have re-seated a place or built a world that has not landed yet)."""
    refs: dict[str, dict[str, str]] = {p: {} for p in PRUNED}
    trees = [main, *(w["path"] for w in worktrees(main))]
    for t in trees:
        tag = "" if t == main else f" (worktree {t.name})"
        b = _json(t / "out/newworld/terrain/build.json")
        if b and b.get("id"):
            refs["nw/terrain/"].setdefault(b["id"], f"the current terrain build, out/newworld/terrain/build.json{tag}")
        held = _json(t / "newworld/sources/terrain_held.json") or {}
        for place, row in (held.get("places") or {}).items():
            if row.get("terrain_build"):
                refs["nw/terrain/"].setdefault(row["terrain_build"], f"{place}'s held ground, newworld/sources/terrain_held.json{tag}")
        man = _json(t / "out/newworld/plugin/land/manifest.json") or {}
        key = (_json(t / "out/newworld/plugin/ArgoniaNewWorld.json") or {}).get("key", "")
        for bid in {man.get("build_id"), key.split(":")[0]} - {None, ""}:
            refs["nw/plugin/"].setdefault(bid, f"the current world file, out/newworld/plugin{tag}")
    # the world file on the play machine: lod.sh send records its hash and time in out/newworld/verify/play-esm.sha256;
    # it was sent from the build current then, so it is the newest world file uploaded up to that time
    sent = main / "out/newworld/verify/play-esm.sha256"
    if sent.exists():
        t_sent = sent.stat().st_mtime
        esms = [o for o in objects if o["key"].startswith("nw/plugin/") and o["key"].endswith(".esm") and o["mtime"] <= t_sent]
        if esms:
            bid = max(esms, key=lambda o: o["mtime"])["key"].split("/")[2]
            refs["nw/plugin/"].setdefault(bid, "the world file on the play machine (sent "
                                          + time.strftime("%F %H:%M", time.gmtime(t_sent)) + ", out/newworld/verify/play-esm.sha256)")
    # the LOD on the play machine: lod.sh run marks each finished step per input key; the key whose last step
    # (dyndolod) finished most recently is the LOD the machine holds
    for m in (HOME / ".argonia/lod-steps").glob("nw-*"):
        done = sorted(m.glob("*/dyndolod"), key=lambda p: p.stat().st_mtime)
        if done:
            refs["nw/lod/"].setdefault(done[-1].parent.name, f"the LOD on {m.name[3:]} (~/.argonia/lod-steps/{m.name})")
    # anything a manifest in the repo names
    for o in objects:
        pre = next((p for p in PRUNED if o["key"].startswith(p)), None)
        if pre:
            bid = o["key"][len(pre):].split("/")[0].removesuffix(".tar")
            if bid not in refs[pre]:
                r = git(main, "grep", "-l", "-F", bid, "--", "*.json", check=False)
                if r.stdout.strip():
                    refs[pre][bid] = f"named by {r.stdout.split()[0]}"
    return refs


def bucket_listing(bucket: str = BUCKET) -> list[dict]:
    aws = shutil.which("aws") or str(HOME / ".local/bin/aws")
    r = subprocess.run([aws, "s3api", "list-objects-v2", "--bucket", bucket, "--output", "json",
                        "--query", "Contents[].[Key,Size,LastModified]"], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"bucket listing failed: {r.stderr.strip()[:200]}")
    import datetime
    return [{"key": k, "size": s, "mtime": datetime.datetime.fromisoformat(t).timestamp()}
            for k, s, t in (json.loads(r.stdout or "null") or [])]


def tidy_bucket(main: Path, dry: bool, quiet: bool, log, bucket: str = BUCKET) -> None:
    objects = bucket_listing(bucket)
    delete, keep, other = bucket_plan(objects, bucket_refs(main, objects), time.time())
    gb = lambda n: f"{n / 2**30:.2f} GB"  # noqa: E731
    for name, size, keys, why in delete:
        log(f"{'would delete' if dry else 'deleted'} s3://{bucket}/{name} ({len(keys)} objects, {gb(size)}): {why}")
        if not dry:
            aws = shutil.which("aws") or str(HOME / ".local/bin/aws")
            for k in keys:
                subprocess.run([aws, "s3", "rm", "--only-show-errors", f"s3://{bucket}/{k}"], check=True, timeout=600)
    if not quiet:
        for name, size, keys, why in keep:
            log(f"keep s3://{bucket}/{name} ({gb(size)}): {why}")
        for pre, (n, size) in sorted(other.items()):
            log(f"keep s3://{bucket}/{pre} ({n} objects, {gb(size)}): "
                + ("the mod cache, never touched" if pre == "mods/" else "no rule deletes here"))
        total = sum(o["size"] for o in objects) - (0 if dry else sum(s for _, s, _, _ in delete))
        log(f"bucket: {gb(total)}" + (f" ({gb(sum(s for _, s, _, _ in delete))} would go)" if dry and delete else ""))


# ---------------------------------------------------------------------------------------------- command

def free_gb() -> float:
    s = os.statvfs("/")
    return s.f_bavail * s.f_frsize / 2**30


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tidy")
    t.add_argument("--dry-run", action="store_true", help="print exactly what would go and why, and what is kept")
    t.add_argument("--quiet", action="store_true", help="only what was removed, and work kept that needs a decision")
    t.add_argument("--disk-only", action="store_true", help="worktrees and disk, never the bucket (the low-disk path)")
    t.add_argument("--bucket", action="store_true", help="the bucket pass now, whatever its once-a-day stamp says")
    for name in ("landed", "remove"):
        p = sub.add_parser(name)
        p.add_argument("worktree")
    a = ap.parse_args(argv)
    root = main_tree()
    if a.cmd in ("landed", "remove"):
        wt = Path(a.worktree).resolve()
        w = next((w for w in worktrees(root) if w["path"] == wt), None)
        if w is None:
            print(f"tidy: {wt} is not a lane worktree of {root}", file=sys.stderr)
            return 2
        git(root, "fetch", "-q", "origin", check=False)
        left = unlanded(root, wt)
        for f, why in left:
            print(f"{f}: {why}")
        if left:
            print(f"{wt.name}: {len(left)} files not on main; kept", file=sys.stderr)
            return 1
        if a.cmd == "remove":
            why = busy(wt, w["lock"])
            if why:
                print(f"{wt.name}: everything is on main, but it is in use ({why}); kept", file=sys.stderr)
                return 1
            remove_worktree(root, w, print)
        else:
            print(f"{wt.name}: everything in it is on main")
        return 0

    STATE.mkdir(parents=True, exist_ok=True)
    import fcntl
    lock = open(STATE / "tidy.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0  # another tidy is running: it does the work
    out = (lambda s: print(f"tidy: {s}", flush=True))
    before = free_gb()
    git(root, "fetch", "-q", "origin", check=False)
    tidy_worktrees(root, a.dry_run, a.quiet, out)
    tidy_disk(root, a.dry_run, out)
    stamp = STATE / "tidy-bucket.stamp"
    due = not stamp.exists() or time.time() - stamp.stat().st_mtime > BUCKET_EVERY_H * 3600
    if not a.disk_only and (a.bucket or a.dry_run or due):
        try:
            tidy_bucket(root, a.dry_run, a.quiet, out)
            if not a.dry_run:
                stamp.write_text(time.strftime("%FT%TZ", time.gmtime()))
        except (RuntimeError, subprocess.SubprocessError, OSError) as e:
            out(f"bucket pass skipped ({e}); it runs again next time")
    after = free_gb()
    if not a.quiet or after - before > 0.5:
        out(f"disk: {after:.1f} GB free" + (f" ({after - before:.1f} GB freed)" if after - before > 0.05 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
