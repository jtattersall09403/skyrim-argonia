"""A draft stage running beside hands: a look session's commit, an agent's edit, a quest spot written while it runs.

A stage reads the place files when it starts and writes its own rows. Every file write inside `beside_hands` is
merged by row (key: the row's id, ref, or whole text) against what the file holds when the write lands: a row the
stage changed, added or removed is written; a row the hands changed is kept as the hands left it; a file the stage
never writes is never touched. A failed stage puts back only its own rows.
"""
from __future__ import annotations

import contextlib
import json
from pathlib import Path

_active: "Guard | None" = None
SKIP_PARTS = ("edits",)


def _key(r) -> str:
    if isinstance(r, dict):
        if r.get("id") is not None:
            return str(r["id"])
        if r.get("ref") is not None:
            return str(r["ref"])
        if "status" in r:
            return f"{r.get('space')}|{r.get('src')}|{r.get('copy')}"
    return json.dumps(r, sort_keys=True)


def _keyed(rows: list) -> dict:
    out, seen = {}, {}
    for r in rows:
        k = _key(r)
        seen[k] = seen.get(k, 0) + 1
        out[(k, seen[k])] = r
    return out


def merge(base: list, mine: list, disk: list) -> list:
    """`disk` with the stage's delta from `base` to `mine` laid on it: a row the stage changed, added or removed is
    taken, unless the hands changed that row too (the hands' row stands)."""
    b, m, d = _keyed(base), _keyed(mine), _keyed(disk)
    out, used = [], set()
    for k, row in d.items():
        used.add(k)
        if k in b and k not in m:
            if row == b[k]:
                continue                                   # the stage removed it, nobody else touched it
        elif k in m and k in b and m[k] != b[k] and row == b[k]:
            row = m[k]                                     # the stage changed it, nobody else did
        out.append(row)
    for k, row in m.items():
        if k not in used and k not in b:                   # the stage added it (a row the hands removed stays removed)
            out.append(row)
    return out


def merge_dict(base: dict, mine: dict, disk: dict) -> dict:
    out = dict(disk)
    for k in set(base) | set(mine):
        if k not in mine:
            if k in disk and disk[k] == base.get(k):
                out.pop(k)
        elif mine[k] != base.get(k) and (k not in disk or disk[k] == base.get(k)):
            out[k] = mine[k]
    return out


def _dump_rows(rows: list) -> str:
    return "".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows)


def _parse(p: Path, text: str):
    if p.suffix == ".json":
        return json.loads(text) if text.strip() else {}
    return [json.loads(x) for x in text.splitlines() if x.strip()]


class Guard:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.known: dict[Path, str | None] = {}     # the text the file held when the stage last read or wrote it
        self.view: dict[Path, object] = {}          # the rows as the stage itself last held them
        self.hand: dict[Path, set] = {}             # the keys of rows the hands changed
        self.wrote: set[Path] = set()
        for p in self.root.rglob("*"):
            if p.is_file() and p.suffix in (".json", ".jsonl") and not set(SKIP_PARTS) & set(p.relative_to(self.root).parts):
                text = p.read_text(encoding="utf-8")
                self.known[p.resolve()] = text
                try:
                    self.view[p.resolve()] = _parse(p, text)
                except ValueError:
                    pass

    def mine(self, p: Path) -> bool:
        p = Path(p).resolve()
        return self.root in p.parents and not set(SKIP_PARTS) & set(p.relative_to(self.root).parts) and p.suffix in (".json", ".jsonl")

    def write(self, p: Path, obj, dump) -> None:
        """Write `obj` (the stage's whole file) to p, keeping what the hands changed since the stage last saw it."""
        rp = Path(p).resolve()
        have = rp.read_text(encoding="utf-8") if rp.exists() else None
        known = self.known.get(rp)
        if rp not in self.view or have == known or (have is None and known is None):
            text = dump(obj)
        else:
            try:
                disk = _parse(rp, have) if have is not None else ([] if isinstance(obj, list) else {})
            except ValueError:
                disk = None
            base = self.view[rp]
            if disk is None or isinstance(disk, dict) != isinstance(obj, dict):
                text = dump(obj)
            else:
                if isinstance(obj, dict):
                    got = merge_dict(base, obj, disk)
                    self.hand.setdefault(rp, set()).update(k for k in set(disk) | set(base) if disk.get(k) != base.get(k))
                else:
                    got = merge(base, obj, disk)
                    self.hand.setdefault(rp, set()).update(k for (k, _), r in _keyed(disk).items()
                                                           if _keyed(base).get((k, _)) != r)
                    self.hand[rp].update(k for (k, _) in _keyed(base) if (k, _) not in _keyed(disk))
                text = dump(got)
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(text, encoding="utf-8")
        self.known[rp], self.view[rp] = text, obj
        self.wrote.add(rp)

    def settle(self) -> dict[str, set | None]:
        """What the stage's ownership proof leaves out: {relative file: the hands' row keys, or None for a whole file
        the stage never wrote}; read once the stage has finished."""
        out: dict[str, set | None] = {}
        for p in self.root.rglob("*"):
            if not (p.is_file() and p.suffix in (".json", ".jsonl")) or set(SKIP_PARTS) & set(p.relative_to(self.root).parts):
                continue
            rp, rel = p.resolve(), str(p.relative_to(self.root))
            text = p.read_text(encoding="utf-8")
            if rp not in self.wrote:
                if text != self.known.get(rp):
                    out[rel] = None
                continue
            if text != self.known.get(rp):    # the hands wrote after the stage's last write
                try:
                    now, was = _parse(p, text), self.view[rp]
                    self.hand.setdefault(rp, set()).update(
                        {k for (k, n), r in _keyed(now).items() if _keyed(was).get((k, n)) != r}
                        if isinstance(now, list) else {k for k in now if now.get(k) != was.get(k)})
                except ValueError:
                    out[rel] = None
                    continue
            if self.hand.get(rp):
                out[rel] = self.hand[rp]
        return out

    def revert(self, snap: dict[str, str]) -> None:
        """A failed stage: its own rows go back to the snapshot, the hands' rows stay."""
        for rel, old in snap.items():      # a file the stage removed (a room taken out) comes back
            if not (self.root / rel).exists():
                (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
                (self.root / rel).write_text(old, encoding="utf-8")
        for rp in sorted(self.wrote):
            rel = str(rp.relative_to(self.root))
            old = snap.get(rel)
            if old is None:
                if rp.exists() and rp.read_text(encoding="utf-8") == self.known.get(rp):
                    rp.unlink()
                continue
            have = rp.read_text(encoding="utf-8") if rp.exists() else ""
            try:
                disk, back, base = _parse(rp, have) if have else None, _parse(rp, old), self.view[rp]
            except ValueError:
                rp.write_text(old, encoding="utf-8")
                continue
            if disk is None or have == self.known.get(rp) and not self.hand.get(rp):
                rp.write_text(old, encoding="utf-8")
            elif isinstance(disk, dict):
                rp.write_text(json.dumps(merge_dict(base, back, disk), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            else:
                rp.write_text(_dump_rows(merge(base, back, disk)), encoding="utf-8")


@contextlib.contextmanager
def beside_hands(root: Path):
    """Inside it every file write under `root` made through `write_rows` / `write_json` keeps the hands' rows."""
    global _active
    prev, _active = _active, Guard(root)
    try:
        yield _active
    finally:
        _active = prev


def write_rows(p: Path, rows: list) -> None:
    if _active is not None and _active.mine(p):
        _active.write(p, rows, _dump_rows)
        return
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(_dump_rows(rows))


def write_json(p: Path, obj: dict) -> None:
    dump = lambda o: json.dumps(o, indent=1, ensure_ascii=False) + "\n"      # noqa: E731
    if _active is not None and _active.mine(p):
        _active.write(p, obj, dump)
        return
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(dump(obj))
