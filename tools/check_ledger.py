#!/usr/bin/env python3
"""The check ledgers (owner, 2026-10-31): every in-game check a brief owes is a row in its part's
docs/phases/<part>/checks.md, one table per chunk under `## <chunk id> <title>`:

    | Check | From | Level | Status | Evidence |

Status is owed, proven or dropped. Evidence tokens, any order, separated by spaces or `;`:
    journey:<id>[#<step prefix>]   a journey in tests/journeys (the prefix: only its steps named so)
    pass|fail out/batch/...        the run dir it passed or failed in (written by tools/run_batch.py)
    owner-brief:YYYY-MM-DD         a dated row in docs/owner-brief.md (required for dropped)
    <repo path>[:<line>]           a file in the repo (a lane report and its line)
    <sha>                          a commit (7-40 hex, at least one letter)

    python3 tools/check_ledger.py         # L1: every ledger valid; exit 1 naming each bad row

The checks: a valid Status; proven and dropped rows carry evidence that resolves (a proven journey row a pass run
or another resolving token; a dropped row an owner-brief date); every journey token names a journey; every journey
in tests/journeys/batches/all.yaml appears in some ledger. `update(summary)` is run_batch's end-of-run rewrite.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
STATUSES = ("owed", "proven", "dropped")
HEADER = ["Check", "From", "Level", "Status", "Evidence"]
JOURNEY = re.compile(r"journey:([A-Za-z0-9_.-]+)(?:#([A-Za-z0-9_.-]+))?")
RUN = re.compile(r"\b(pass|fail) (out/\S*\d{8}T\d{6}\S*)")
OWNER = re.compile(r"owner-brief:(\d{4}-\d{2}-\d{2})")
PATH = re.compile(r"(?<![\w/:.-])((?:docs|tests|tools|tooling|infra|skse|ui|data|world|installer)/[\w./-]+?)(?::(\d+))?(?=[\s;,)]|$)")
SHA = re.compile(r"(?<![\w/:#.-])(?=[0-9a-f]*[a-f])([0-9a-f]{7,40})(?![\w/-])")


def ledgers(repo: pathlib.Path = REPO) -> list[pathlib.Path]:
    return sorted((repo / "docs" / "phases").glob("*/checks.md"))


def cells(line: str) -> list[str] | None:
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return None
    return [c.strip() for c in s[1:-1].split("|")]


def rows(text: str):
    """(line index, chunk heading, cells) for every data row of a chunk table."""
    chunk, in_table = None, False
    for k, line in enumerate(text.splitlines()):
        if line.startswith("## "):
            chunk, in_table = line[3:].strip(), False
            continue
        c = cells(line)
        if c is None:
            in_table = False
            continue
        if c == HEADER:
            in_table = True
            continue
        if in_table and not all(set(x) <= set("-: ") for x in c):
            yield k, chunk, c


class Resolver:
    def __init__(self, repo: pathlib.Path):
        self.repo = repo
        self.journeys = {p.stem for p in (repo / "tests" / "journeys").glob("*.yaml")}
        ob = repo / "docs" / "owner-brief.md"
        self.owner_dates = set(re.findall(r"^\| (\d{4}-\d{2}-\d{2}) \|", ob.read_text(), re.M)) if ob.exists() else set()
        self._sha: dict = {}

    def sha(self, s: str) -> bool:
        if s not in self._sha:
            r = subprocess.run(["git", "-C", str(self.repo), "cat-file", "-e", f"{s}^{{commit}}"], capture_output=True)
            self._sha[s] = r.returncode == 0
        return self._sha[s]

    def path(self, p: str, line: str | None) -> bool:
        f = self.repo / p
        if not f.is_file():
            return False
        return line is None or int(line) <= len(f.read_text(errors="replace").splitlines())


def check_text(text: str, name: str, res: Resolver, seen: set) -> list[str]:
    errs = []
    n = 0
    for k, chunk, c in rows(text):
        n += 1
        where = f"{name}:{k + 1}"
        if chunk is None:
            errs.append(f"{where}: a row outside a `## <chunk>` section")
        if len(c) != 5:
            errs.append(f"{where}: {len(c)} columns, want 5 ({' | '.join(HEADER)})")
            continue
        check, _, level, status, ev = c
        if not check:
            errs.append(f"{where}: no Check")
        if not re.fullmatch(r"L[1-6](?:[-/]L?[1-6])?", level):
            errs.append(f"{where}: Level {level!r} (L1..L6)")
        if status not in STATUSES:
            errs.append(f"{where}: Status {status!r} (one of {', '.join(STATUSES)})")
            continue
        js = JOURNEY.findall(ev)
        for jid, _ in js:
            seen.add(jid)
            if jid not in res.journeys:
                errs.append(f"{where}: journey:{jid} is not in tests/journeys")
        runs = RUN.findall(ev)
        owners = OWNER.findall(ev)
        for d in owners:
            if d not in res.owner_dates:
                errs.append(f"{where}: owner-brief:{d} has no dated row in docs/owner-brief.md")
        stripped = OWNER.sub(" ", RUN.sub(" ", JOURNEY.sub(" ", ev)))
        paths = PATH.findall(stripped)
        for p, ln in paths:
            if not res.path(p, ln or None):
                errs.append(f"{where}: {p}{':' + ln if ln else ''} does not resolve")
        shas = SHA.findall(PATH.sub(" ", stripped))
        for s in shas:
            if not res.sha(s):
                errs.append(f"{where}: commit {s} does not exist")
        if status == "dropped" and not owners:
            errs.append(f"{where}: dropped needs owner-brief:<date>")
        if status == "proven" and not (js or paths or shas):
            errs.append(f"{where}: proven needs evidence (a journey with its pass run, a report path, or a commit)")
        if status == "proven" and js and not paths and not shas and not any(r[0] == "pass" for r in runs):
            errs.append(f"{where}: a proven journey row needs its `pass out/...` run")
    if n == 0:
        errs.append(f"{name}: no ledger rows")
    return errs


def batch_journeys(repo: pathlib.Path) -> list[str]:
    import yaml
    f = repo / "tests" / "journeys" / "batches" / "all.yaml"
    if not f.exists():
        return []
    out = []
    for it in yaml.safe_load(f.read_text()).get("items", []):
        if isinstance(it, str) and not it.startswith("scene:"):
            out.append(it.partition(":")[0])
        elif isinstance(it, dict) and "journey" in it:
            out.append(str(it["journey"]))
    return out


def check(repo: pathlib.Path = REPO) -> list[str]:
    res, seen, errs = Resolver(repo), set(), []
    files = ledgers(repo)
    if not files:
        return ["no docs/phases/*/checks.md ledger"]
    for f in files:
        errs += check_text(f.read_text(), str(f.relative_to(repo)), res, seen)
    for jid in batch_journeys(repo):
        if jid not in seen:
            errs.append(f"tests/journeys/batches/all.yaml: journey {jid} is in no ledger")
    return errs


def _steps(report_dir: pathlib.Path) -> list[dict]:
    try:
        return json.loads((report_dir / "report.json").read_text()).get("steps", [])
    except (OSError, ValueError):
        return []


def update_text(text: str, results: dict) -> tuple[str, int]:
    """results: journey id -> {passed, run (repo-relative dir), steps: [{name, passed}]}, the last run of each.
    Rewrites Status and Evidence of each owed or proven `journey:` row; dropped rows stay. Returns (text, rows changed)."""
    lines = text.splitlines(keepends=True)
    changed = 0
    for k, _, c in list(rows(text)):
        if len(c) != 5 or c[3] == "dropped":
            continue
        m = JOURNEY.search(c[4])
        if not m or m.group(1) not in results:
            continue
        jid, prefix = m.groups()
        r = results[jid]
        if prefix:
            st = [s for s in r.get("steps", []) if s.get("name", "").startswith(prefix)]
            if not st:
                continue  # the run never reached those steps
            ok = all(s.get("passed") for s in st)
        else:
            ok = bool(r["passed"])
        status = "proven" if ok else "owed"
        ev = f"{m.group(0)} {'pass' if ok else 'fail'} {r['run']}"
        if (c[3], c[4]) == (status, ev):
            continue
        new = c[:3] + [status, ev]
        eol = "\n" if lines[k].endswith("\n") else ""
        lines[k] = "| " + " | ".join(new) + " |" + eol
        changed += 1
    return "".join(lines), changed


def update(summary: dict, repo: pathlib.Path = REPO) -> int:
    """run_batch's end-of-run rewrite from its summary.json; the rows changed."""
    results = {}
    for i in summary.get("items", []):
        if i.get("kind", "journey") != "journey" or not i.get("report"):
            continue
        d = pathlib.Path(i["report"])
        s = d.as_posix()
        rel = s[s.index("out/"):] if "out/" in s else s  # out/ is per tree (a worktree links it), so repo-relative
        results[i["id"]] = {"passed": bool(i.get("passed")), "run": rel, "steps": _steps(d)}
    total = 0
    for f in ledgers(repo):
        new, n = update_text(f.read_text(), results)
        if n:
            f.write_text(new)
            total += n
    return total


def main(argv=None) -> int:
    errs = check()
    for e in errs:
        print(e)
    if errs:
        print(f"check_ledger: {len(errs)} bad")
        return 1
    n = sum(1 for f in ledgers() for _ in rows(f.read_text()))
    print(f"check_ledger: {n} rows in {len(ledgers())} ledgers OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
