#!/usr/bin/env python3
"""The gate for what a change reaches (CLAUDE.md "run only what the change reaches", decision 0021's amendment).

  tooling/check_reach.py --since <sha|ref>     changed paths since <sha> (committed, staged, unstaged, untracked)
  tooling/check_reach.py --since auto --record the last green gate's sha in ~/.argonia/round/gate-green (full gate
                                               when it is unknown or older than a day); a green run on a clean tree
                                               writes HEAD there
  tooling/check_reach.py --plan --since <sha>  print the plan, run nothing

A declared map (RULES) gives each path glob the gate steps that read it (`make check`'s PARTS, `unit` split into the
pytest directories beside the changed files). A path no rule names runs the whole gate: the conservative default.
Prints what ran and what was skipped and why. The full gate stays `make check`; a red is re-proved by its one test.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROUND = Path(os.environ.get("ARGONIA_ROUND_DIR", Path.home() / ".argonia" / "round"))
GREEN = ROUND / "gate-green"
MAX_AGE = 24 * 3600
PARTS = ["guard", "lint", "unit", "budget", "links", "records", "ledger", "world", "roads-census", "trees-census", "edges-census", "plugin-check", "skse", "immersion", "ui"]

# (glob, steps). `**` crosses directories, `*` does not. First match wins, so narrow rules come first.
# "unit" means the pytest directories beside the file; "unit:all" the whole unit step.
RULES: list[tuple[str, list[str]]] = [
    # docs and prose
    ("CLAUDE.md", ["budget", "links", "records"]),
    ("docs/phases/**/checks.md", ["links", "records", "ledger"]),
    ("docs/**", ["links", "records"]),
    ("**/*.md", ["links"]),
    # the world database and what builds from it
    ("world/db/build_ref.jsonl", ["world"]),
    ("out/terrain/ground.stamp", ["roads-census", "edges-census"]),  # a land rebuild: the census reads the new ground
    ("world/**", ["world", "plugin-check", "immersion", "unit"]),
    ("data/**", ["world"]),
    ("tools/argonia_world/skyrim_units.py", ["lint", "unit:all", "world", "plugin-check"]),
    ("tools/argonia_world/db.py", ["lint", "unit:all", "world", "plugin-check"]),
    ("tools/argonia_world/checks.py", ["lint", "unit", "world"]),
    ("tools/argonia_world/water/**", ["lint", "unit", "world", "roads-census", "edges-census"]),
    ("tools/argonia_world/vegetation/**", ["lint", "unit", "world"]),
    ("tools/argonia_world/routes/**", ["lint", "unit", "world", "roads-census"]),
    ("tools/argonia_world/terrain/**", ["lint", "unit", "world", "roads-census", "edges-census"]),
    ("tools/argonia_world/**/tests/**", ["lint", "unit"]),
    ("tools/argonia_world/**", ["lint", "unit", "world", "plugin-check"]),
    ("plugin/**", ["plugin-check"]),
    ("tools/ArgoniaGen/**", ["lint", "unit", "plugin-check"]),
    # test-ledger and records tools
    ("tools/check_ledger.py", ["lint", "unit", "ledger"]),
    ("tools/check_records.py", ["lint", "unit", "records"]),
    ("tools/doc_index.py", ["lint", "unit", "records"]),
    ("tooling/check_links.py", ["lint", "unit", "links"]),
    ("tests/journeys/**", ["ledger", "unit"]),
    ("tests/scenes/**", ["ledger"]),
    ("tooling/guards/**", ["guard", "lint", "unit"]),
    ("tooling/check_reach.py", ["lint", "unit"]),
    # code with tests beside it
    ("tools/immersion/**", ["lint", "unit", "immersion"]),
    ("tools/schema_gen/**", ["lint", "unit", "ui"]),
    ("ui/**", ["ui", "unit"]),
    ("skse/**", ["skse"]),
    ("infra/cloudflare/**", ["unit:all"]),
    ("infra/stream-client/**", ["unit:all"]),
    ("tools/navmesh/**/*.cs", []),  # built by `make navmesh`, not in the gate
    ("tests/*.py", ["lint", "unit"]),
    ("tools/**/*.py", ["lint", "unit"]),
    ("tooling/**/*.py", ["lint", "unit"]),
    ("tooling/**/*.sh", ["unit"]),
    ("infra/**/*.sh", ["unit"]),
    ("infra/**/*.ps1", []),
    ("Makefile", ["__all__"]),
]


def glob_re(g: str) -> re.Pattern:
    out, i = "", 0
    while i < len(g):
        if g.startswith("**/", i):
            out += "(?:.*/)?"; i += 3
        elif g.startswith("**", i):
            out += ".*"; i += 2
        elif g[i] == "*":
            out += "[^/]*"; i += 1
        else:
            out += re.escape(g[i]); i += 1
    return re.compile("^" + out + "$")


COMPILED = [(glob_re(g), g, s) for g, s in RULES]


def match(path: str):
    for rx, g, steps in COMPILED:
        if rx.match(path):
            return g, steps
    return None


def test_targets(path: str) -> list[str]:
    """The pytest targets beside a changed file: itself if a test, else the nearest tests/ dir or test_*.py siblings."""
    p = Path(path)
    if p.name.startswith("test_") or p.name.endswith("_test.py"):
        return [path] if p.suffix == ".py" else []
    d = p.parent
    while str(d) not in (".", ""):
        if (REPO / d / "tests").is_dir():
            return [f"{d}/tests"]
        sib = sorted(x.name for x in (REPO / d).glob("test_*.py"))
        if sib:
            return [f"{d}/{n}" for n in sib]
        d = d.parent
    return []


def changed_paths(since: str) -> list[str]:
    def git(*a):
        return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.split("\n")
    names = set(git("diff", "--name-only", since)) | set(git("ls-files", "-o", "--exclude-standard"))
    return sorted(n for n in names if n)


def plan(paths: list[str]):
    """-> (steps reached with the paths that reach them, pytest targets, run_all reason or None, node?, notes)."""
    reached: dict[str, list[str]] = {}
    targets: set[str] = set()
    unit_all = False
    for path in paths:
        m = match(path)
        if m is None or "__all__" in m[1]:
            return {}, set(), f"unmapped path {path}: the whole gate", False
        g, steps = m
        for s in steps:
            if s == "unit:all":
                unit_all = True
                s = "unit"
            reached.setdefault(s, []).append(path)
            if s == "unit":
                targets.update(test_targets(path))
    if unit_all:
        targets = {"__all__"}
    return reached, targets, None, False


def sh(cmd: list[str]) -> tuple[int, float]:
    t = time.time()
    return subprocess.run(cmd, cwd=REPO).returncode, time.time() - t


# The heavy parts start first so the pool overlaps them (the memory watcher's 3 GB-per-process cap: 3 at once).
# plugin-check alone takes out/.plugin.lock (make plugin-check); no other part does, so no part shares a worker.
HEAVY = ["unit", "plugin-check", "skse"]


def queue_order(steps: list[str]) -> list[str]:
    """Reached steps, heavy first, the rest in PARTS order."""
    return [s for s in HEAVY if s in steps] + [s for s in PARTS if s in steps and s not in HEAVY]


def run_part(s: str, targets: set[str], paths: list[str]) -> tuple[int, float, str]:
    """One part with its output captured whole: (rc, seconds, text)."""
    t = time.time()
    if s == "unit":
        cmd_unit = run_unit_cmds(targets)
        out, rc = "", 0
        for cmd in cmd_unit:
            r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
            out += r.stdout + r.stderr
            if r.returncode not in (0, 5) and cmd[0] != "make":
                rc = 1
            elif cmd[0] == "make" and r.returncode:
                rc = r.returncode
        return rc, time.time() - t, out
    r = subprocess.run(["make", "--no-print-directory", s], cwd=REPO, capture_output=True, text=True)
    return r.returncode, time.time() - t, r.stdout + r.stderr


def part_stamp(step: str, paths: list[str], targets: set[str], key: str) -> str:
    """The inputs of one part: its name, the caller's key (the pre-batch's build key), and the content of every changed
    path that reaches it (plus the pytest targets for unit). A moved input is a new stamp, so the part reruns."""
    import hashlib
    h = hashlib.sha256(f"{step}\0{key}\0".encode())
    for p in sorted(paths):
        m = match(p)
        if m and (step in m[1] or (step == "unit" and "unit:all" in m[1])):
            f = REPO / p
            h.update(p.encode() + b"\0" + (hashlib.sha256(f.read_bytes()).digest() if f.is_file() else b"-"))
    if step == "unit":
        h.update("\0".join(sorted(targets)).encode())
    return h.hexdigest()[:12]


def resumable(runner, state: Path | None, stamp_of):
    """Wrap a part runner: a part whose "<name> <stamp> OK" line is in `state` is skipped; a green part is recorded the
    moment it ends (a spot reclaim keeps it); a red part is never recorded, so it reruns."""
    import threading
    lock = threading.Lock()

    def run(s):
        if state is None:
            return runner(s)
        st = stamp_of(s)
        line = f"{s} {st} OK"
        try:
            done = line in state.read_text().splitlines()
        except OSError:
            done = False
        if done:
            return 0, 0.0, f"gate part {s} OK (done earlier for {st})"
        r = runner(s)
        if r[0] == 0:
            with lock:
                state.parent.mkdir(parents=True, exist_ok=True)
                with state.open("a") as f:
                    f.write(line + "\n")
        return r
    return run


def run_pool(steps: list[str], jobs: int, runner, emit=print) -> dict[str, int]:
    """Run steps with `jobs` workers in queue_order; each part's text is emitted whole, in PARTS order, once it and
    every earlier part has ended. -> {step: rc}."""
    from concurrent.futures import ThreadPoolExecutor
    order = [s for s in PARTS if s in steps]
    done: dict[str, tuple[int, float, str]] = {}
    results: dict[str, int] = {}
    nxt = 0
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        futs = {ex.submit(runner, s): s for s in queue_order(steps)}
        from concurrent.futures import as_completed
        for f in as_completed(futs):
            done[futs[f]] = f.result()
            while nxt < len(order) and order[nxt] in done:
                s = order[nxt]
                r, secs, text = done[s]
                if text.strip():
                    emit(text.rstrip("\n"))
                emit(f"reach: {s} {'GREEN' if r == 0 else 'RED'} in {secs:.0f} s")
                results[s] = r
                nxt += 1
    return results


def run_unit_cmds(targets: set[str]) -> list[list[str]]:
    py = Path.home() / ".argonia/venv/bin/python"
    py = str(py) if py.exists() else "python3"
    if "__all__" in targets:
        return [["make", "--no-print-directory", "unit"]]
    ex = sorted(t for t in targets if (REPO / t).exists())
    return [[py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--ignore=tooling/tests/test_word_budget.py", *ex]] if ex else []


def run_unit(targets: set[str], paths: list[str]) -> int:
    py = Path.home() / ".argonia/venv/bin/python"
    py = str(py) if py.exists() else "python3"
    rc = 0
    if "__all__" in targets:
        r, _ = sh(["make", "--no-print-directory", "unit"])
        return r
    ex = sorted(t for t in targets if (REPO / t).exists())
    if ex:
        r, _ = sh([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--ignore=tooling/tests/test_word_budget.py", *ex])
        if r not in (0, 5):
            rc = 1
    return rc


def last_green():
    try:
        sha, ts = GREEN.read_text().split()
        return sha, time.time() - float(ts)
    except Exception:
        return None, None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="origin/main")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--jobs", type=int, default=3, help="parts run at once (default 3; 1 is the serial run)")
    ap.add_argument("--state", default=os.environ.get("ARGONIA_GATE_STATE"), help="file of green parts (name, input stamp): a rerun skips them")
    ap.add_argument("--key", default=os.environ.get("ARGONIA_GATE_KEY", ""), help="the caller's inputs key, folded into every part stamp")
    ap.add_argument("--record", action="store_true", help="a green run on a clean tree records HEAD as the last green gate")
    a = ap.parse_args(argv)
    since, why_full = a.since, None
    if since == "auto":
        sha, age = last_green()
        if sha is None or age > MAX_AGE:
            why_full = "no green gate recorded in the last day"
        else:
            since = sha
    if why_full is None:
        if subprocess.run(["git", "rev-parse", "--verify", "-q", since + "^{commit}"], cwd=REPO, capture_output=True).returncode:
            why_full = f"{since} is not a commit here"
    paths = [] if why_full else changed_paths(since)
    reached, targets, why_full2, _ = ({}, set(), None, False) if why_full else plan(paths)
    why_full = why_full or why_full2
    if why_full:
        print(f"reach: {why_full}")
        if a.plan:
            return 0
        return finish(run_gate(list(PARTS), {"__all__"}, [], a, full_key(a.key)), a)
    print(f"reach: {len(paths)} changed path(s) since {since}")
    if not paths:
        print("reach: nothing changed; every step skipped")
        return 0
    for s in PARTS:
        if s in reached:
            ex = ", ".join(reached[s][:3]) + (f" (+{len(reached[s]) - 3})" if len(reached[s]) > 3 else "")
            print(f"  RUN  {s}: read by {ex}" + (f" -> {' '.join(sorted(targets))}" if s == "unit" else ""))
        else:
            print(f"  skip {s}: no changed path reads it")
    if a.plan:
        return 0
    steps = [x for x in PARTS if x in reached]
    return finish(run_gate(steps, targets, paths, a, a.key), a)


def full_key(key: str) -> str:
    """A full run's stamp key: the caller's key plus HEAD, marked full, so a part green in a full run is not taken for a
    green part of a narrower run and a resume of the full run skips only parts green at this commit."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    return f"{key}|full|{head}"


def run_gate(steps: list[str], targets: set[str], paths: list[str], a, key: str) -> int:
    """Every step through the per-part loop with state recording: no monolithic `make check` (it restarts from zero on a
    spot reclaim). The full run is all of PARTS, the same set `make check` runs. -> 0 green, 1 red."""
    t0 = time.time()
    run = resumable(lambda x: run_part(x, targets, paths), Path(a.state) if a.state else None,
                    lambda x: part_stamp(x, paths, targets, key))
    res = run_pool(steps, a.jobs, run)
    red = [x for x in steps if res.get(x)]
    wall = time.time() - t0
    print((f"REACH RED: {' '.join(red)} ({wall:.0f} s wall, {a.jobs} jobs)") if red else f"REACH GREEN ({len(steps)} steps of {len(PARTS)}, {wall:.0f} s wall, {a.jobs} jobs)")
    return 1 if red else 0


def finish(rc: int, a) -> int:
    if rc == 0 and a.record:
        clean = not subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        if clean:
            ROUND.mkdir(parents=True, exist_ok=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
            GREEN.write_text(f"{head} {time.time():.0f}\n")
            print(f"reach: recorded {head[:8]} as the last green gate")
    return rc


if __name__ == "__main__":
    sys.exit(main())
