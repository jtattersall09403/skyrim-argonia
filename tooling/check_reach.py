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
PARTS = ["guard", "lint", "unit", "budget", "links", "records", "ledger", "world", "roads-census", "plugin-check", "skse", "immersion", "ui"]

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
    ("out/terrain/ground.stamp", ["roads-census"]),  # a land rebuild: the census reads the new ground
    ("world/**", ["world", "plugin-check", "immersion", "unit"]),
    ("data/**", ["world"]),
    ("tools/argonia_world/skyrim_units.py", ["lint", "unit:all", "world", "plugin-check"]),
    ("tools/argonia_world/db.py", ["lint", "unit:all", "world", "plugin-check"]),
    ("tools/argonia_world/checks.py", ["lint", "unit", "world"]),
    ("tools/argonia_world/water/**", ["lint", "unit", "world", "roads-census"]),
    ("tools/argonia_world/vegetation/**", ["lint", "unit", "world"]),
    ("tools/argonia_world/routes/**", ["lint", "unit", "world", "roads-census"]),
    ("tools/argonia_world/terrain/**", ["lint", "unit", "world", "roads-census"]),
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
        rc = subprocess.run(["make", "--no-print-directory", "check"], cwd=REPO).returncode
        return finish(rc, a)
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
    red = []
    t0 = time.time()
    for s in PARTS:
        if s not in reached:
            continue
        t = time.time()
        r = run_unit(targets, paths) if s == "unit" else sh(["make", "--no-print-directory", s])[0]
        print(f"reach: {s} {'GREEN' if r == 0 else 'RED'} in {time.time() - t:.0f} s")
        if r:
            red.append(s)
    print(("REACH RED: " + " ".join(red)) if red else f"REACH GREEN ({len(reached)} steps of {len(PARTS)}, {time.time() - t0:.0f} s)")
    return finish(1 if red else 0, a)


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
