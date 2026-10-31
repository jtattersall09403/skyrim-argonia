#!/usr/bin/env python3
"""The records can't go stale (owner, 2026-10-31): `make check` fails when PROGRESS, the part READMEs, the chunk
briefs and the check ledgers disagree, or when PROGRESS cites something the repo no longer has.

  python3 tools/check_records.py            exit 0, or 1 with one line per problem

Checks:
 1. every chunk in a docs/phases/*/README.md table has one PROGRESS row with the same status word (todo,
    in progress, done, blocked, dropped); a PROGRESS row names a README chunk (or a sub-row such as "2.W5 wave 1");
 2. a chunk brief's `**Status.**` line, when it has one, carries the same word;
 3. a chunk marked done has no `owed` row under its `## <id>` heading in any docs/phases/*/checks.md ledger
    (skipped, with a note, while no ledger exists);
 4. a row that isn't todo cites evidence: a commit, a report path or a lane report;
 5. PROGRESS cites nothing the repo no longer has: a commit git doesn't know, a lane with no lane report, a path that
    doesn't exist, a machine not in infra/gpu-box/machines.conf, a bare `game-N` batch older than the newest lane-game
    report (cite the report instead), "[from batch]", or a retired thing (STALE below).
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
WORDS = ("in progress", "todo", "done", "blocked", "dropped")
# Retired things a row must not cite, with why (each from an owner ruling or a machine move).
STALE = {
    r"\bg4dn\b": "the g4dn is retired (lane-g6-move); the play machine is argonia-play in machines.conf",
    r"(?i)\b(CK|Creation Kit)\b[^|]{0,20}\bLOD\b|LOD by the Creation Kit": "LOD is xLODGen's (owner 2026-10-30)",
    r"\[from batch\]": "a pointer to a batch that has run; cite the report or the ledger row",
}
HEX = re.compile(r"(?<![\w/.-])([0-9a-f]{7,40})(?![\w-])")


def status_word(cell: str) -> str | None:
    c = cell.strip().lower()
    return next((w for w in WORDS if c.startswith(w)), None)


def table_rows(text: str):
    """(header cells, row cells) for every markdown table row below a header row."""
    head = None
    for line in text.splitlines():
        if not line.startswith("|"):
            head = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if head is None:
            head = cells
        elif not set("".join(cells)) <= set("-: "):
            yield head, cells


def readme_chunks(root: pathlib.Path) -> dict[str, list[tuple[str, str, pathlib.Path | None]]]:
    """chunk id -> [(status word or '', README, brief path)] from every part README's chunk table."""
    out: dict = {}
    for readme in sorted((root / "docs/phases").glob("*/README.md")):
        for head, cells in table_rows(readme.read_text()):
            if head[:2] != ["Id", "Chunk"]:
                continue
            st = cells[head.index("Status")] if "Status" in head and len(cells) > head.index("Status") else ""
            m = re.search(r"\]\(([^)]+\.md)\)", cells[1])
            brief = (readme.parent / m.group(1)).resolve() if m else None
            out.setdefault(cells[0], []).append((st, str(readme.relative_to(root)), brief))
    return out


def progress_rows(root: pathlib.Path) -> list[tuple[str, str]]:
    rows = []
    for head, cells in table_rows((root / "docs/PROGRESS.md").read_text()):
        if head[:2] == ["Part", "Chunk"] and len(cells) >= 4:
            rows.append((cells[1], cells[3]))
    return rows


def ledgers(root: pathlib.Path) -> dict[str, list[str]] | None:
    """chunk id -> the Check cell of each owed row, over every checks.md; None while no ledger exists."""
    files = sorted((root / "docs/phases").glob("*/checks.md"))
    if not files:
        return None
    owed: dict = {}
    for f in files:
        cur = None
        for line in f.read_text().splitlines():
            h = re.match(r"##\s+(\S+)", line)
            if h:
                cur = h.group(1)
                owed.setdefault(cur, [])
            elif cur and line.startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 4 and cells[3].lower() == "owed":
                    owed[cur].append(cells[0])
    return owed


def check(root: pathlib.Path = REPO) -> tuple[list[str], list[str]]:
    errs, notes = [], []
    chunks, prog = readme_chunks(root), progress_rows(root)
    seen: dict[str, int] = {}
    for cid, st in prog:
        seen[cid] = seen.get(cid, 0) + 1
    for cid, places in chunks.items():
        n = seen.get(cid, 0)
        if n != 1:
            errs.append(f"PROGRESS: chunk {cid} has {n} rows (one wanted)")
            continue
        pw = status_word(dict(prog)[cid])
        for st, readme, brief in places:
            if status_word(st) != pw:
                errs.append(f"{readme}: {cid} is {status_word(st) or 'without a status'!r}, PROGRESS says {pw!r}")
            if brief and brief.exists():
                m = re.search(r"^\*\*Status[^*]*\*\*\s*(.*)$", brief.read_text(), re.M)
                if m and status_word(m.group(1)) != pw:
                    errs.append(f"{brief.relative_to(root)}: Status {status_word(m.group(1))!r}, PROGRESS {pw!r}")
    for cid, st in prog:
        base = cid.split(" ")[0]
        if base not in chunks and not re.match(r"4\.[235]-", cid):
            errs.append(f"PROGRESS: {cid} is in no part README's chunk table")
        if status_word(st) is None:
            errs.append(f"PROGRESS: {cid} status {st[:30]!r} starts with none of {', '.join(WORDS)}")

    led = ledgers(root)
    if led is None:
        notes.append("no docs/phases/*/checks.md ledger yet: the done-has-no-owed check is skipped")
    else:
        for cid, st in prog:
            if status_word(st) == "done" and led.get(cid):
                errs.append(f"PROGRESS: {cid} is done but its ledger owes: {'; '.join(led[cid])[:120]}")

    research = {p.stem for p in (root / "docs/research").rglob("lane-*.md")}
    games = [int(m.group(1)) for s in research for m in [re.match(r"lane-game-(\d+)$", s)] if m]
    newest = max(games, default=0)
    machines = {line.split()[0] for line in (root / "infra/gpu-box/machines.conf").read_text().splitlines()
                if line.strip() and not line.startswith("#")} if (root / "infra/gpu-box/machines.conf").exists() else set()
    hashes: dict[str, str] = {}
    for cid, st in prog:
        where = f"PROGRESS {cid}"
        if status_word(st) not in ("todo", None) and not (HEX.search(st) or re.search(r"\.md\b|lane-", st)):
            errs.append(f"{where}: cites no evidence (a commit, a report or a lane)")
        for pat, why in STALE.items():
            if re.search(pat, st):
                errs.append(f"{where}: {re.search(pat, st).group(0)!r}: {why}")
        for m in re.finditer(r"(?<![\w-])game-(\d+)(?![\w.])", st):
            if int(m.group(1)) < newest:
                errs.append(f"{where}: bare game-{m.group(1)} is older than game-{newest}; cite lane-game-{m.group(1)}.md")
        for m in re.finditer(r"\blane-([\w.-]+?)(?:\.md)?(?=[\s,;:)]|$)", st):
            if f"lane-{m.group(1)}" not in research:
                errs.append(f"{where}: lane-{m.group(1)} has no report in docs/research")
        for m in re.finditer(r"(?<![\w/])((?:docs|tools|tooling|infra|tests|installer|data)/[\w./-]+\w)", st):
            if not (root / m.group(1)).exists():
                errs.append(f"{where}: {m.group(1)} does not exist")
        for m in re.finditer(r"\bargonia-play[\w-]*", st):
            if m.group(0) not in machines:
                errs.append(f"{where}: machine {m.group(0)} is not in machines.conf")
        for m in HEX.finditer(st):
            if re.search(r"[a-f]", m.group(1)) and re.search(r"\d", m.group(1)):
                hashes[m.group(1)] = where
    if hashes:
        r = subprocess.run(["git", "-C", str(root), "cat-file", "--batch-check"], capture_output=True, text=True,
                           input="".join(f"{h}^{{commit}}\n" for h in hashes))
        for h, line in zip(hashes, r.stdout.splitlines()):
            if " commit " not in line:
                errs.append(f"{hashes[h]}: commit {h} is unknown to git")
    return errs, notes


def main() -> int:
    errs, notes = check()
    for n in notes:
        print(f"note: {n}")
    for e in errs:
        print(e)
    print(f"records: {len(errs)} problem(s)" if errs else "records: PROGRESS, READMEs, briefs and ledgers agree")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
