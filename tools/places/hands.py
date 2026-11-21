"""A draft stage running beside hands: a look session's commit, an agent's edit, a quest spot written while it runs.

A stage reads the place files when it starts and writes its own rows. Every file write inside `beside_hands` is
merged by row (key: the row's id, ref, or whole text) against what the file holds when the write lands: a row the
stage changed, added or removed is written; a row the hands changed is kept as the hands left it; a file the stage
never writes is never touched. A failed stage puts back only its own rows.
"""
from __future__ import annotations

import contextlib
import copy
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


# ---------- a hand's placement is authoritative ----------
# Every draft stage (draft/stages.py `run`) ends with `keep_placed`: a row a committed agent edit (agent-edits/, listed
# in place.json `agent_saves_applied`) or an owner's finalised studio save (edits/, `final`) moved, turned, sank,
# dropped, added, un-dropped or edited stands as the hand left it, until a hand moves it again or `look release`
# gives it back to the stages (place.json `released`; an owner's row is never released by an agent).
TABLE_FILES = {"path": "paths.jsonl", "person": "people.jsonl", "quest": "quests.jsonl"}


def _place(pdir: Path) -> dict:
    try:
        return json.loads((pdir / "place.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _saves(pdir: Path) -> list[tuple[str, list, int]]:
    """(whose, ops, order) of every hand save of the place: the owner's finalised saves (order 0), then the agent's
    in the order place.json `agent_saves_applied` lists them (order 1 + its index there)."""
    out = []
    ed = pdir / "edits"
    for p in sorted(ed.glob("*.json")) if ed.is_dir() else []:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if s.get("final"):
            out.append((f"the owner's save {p.stem}", s.get("ops") or [], 0))
    for i, sid in enumerate(_place(pdir).get("agent_saves_applied") or []):
        p = pdir / "agent-edits" / f"{sid}.json"
        if p.exists():
            out.append((f"the agent's edit {sid}", json.loads(p.read_text(encoding="utf-8")).get("ops") or [], i + 1))
    return out


def _op_row(op: dict) -> tuple[str, str, set | None] | None:
    """(file, row key, the fields the hand set; None: the whole row and whether it stands) that an op holds."""
    kind = op.get("op", "")
    sp = f"spaces/{op.get('space', 'exterior')}/refs.jsonl"
    if kind == "ref.move":
        return sp, str(op["id"]), set(op.get("after") or {}) or None
    if kind == "ref.add":
        return sp, str(op["ref"]["id"]), None
    if kind == "ref.remove":
        return sp, str(op["id"]), None
    table, _, verb = kind.partition(".")
    if table in TABLE_FILES and isinstance(op.get(table), dict) and op[table].get("id") is not None:
        row, before = op[table], op.get("before")
        if verb == "edit" and isinstance(before, dict):
            return TABLE_FILES[table], str(row["id"]), {k for k in set(row) | set(before) if row.get(k) != before.get(k)}
        return TABLE_FILES[table], str(row["id"]), None
    return None


def placed(pdir: Path) -> dict[tuple[str, str], dict]:
    """{(file, row key): {fields, by, order}} of every row a hand placed and has not released: `fields` the fields
    the hands set (None: the whole row, and whether it stands at all), `by` whose hand last touched it."""
    pdir = Path(pdir)
    out: dict[tuple[str, str], dict] = {}
    for who, ops, order in _saves(pdir):
        for op in ops:
            got = _op_row(op)
            if got is None:
                continue
            rel, key, fields = got
            have = out.get((rel, key))
            if have is not None and have["order"] == 0 and order > 0:
                continue                     # an owner's row: the agent's stroke on it was left out at commit
            if have is not None:
                fields = None if have["fields"] is None or fields is None else have["fields"] | fields
            out[(rel, key)] = {"fields": fields, "by": who, "order": order}
    for r in _place(pdir).get("released") or []:
        k = (f"spaces/{r.get('space', 'exterior')}/refs.jsonl", str(r["id"]))
        if k in out and 0 < out[k]["order"] <= int(r.get("after", 0)):
            out.pop(k)                       # given back to the stages, and no hand has touched it since
    return out


def _would(old, new, fields) -> str:
    """What a stage would have done to a hand's row, in a few words."""
    import math
    if old is None:
        return "put it back (a hand dropped it)"
    if new is None:
        return "taken it out"
    said = []
    for f in sorted(fields if fields is not None else set(old) | set(new)):
        a, b = old.get(f), new.get(f)
        if a == b:
            continue
        if f == "pos" and isinstance(a, list) and isinstance(b, list) and len(a) == len(b) == 3:
            said.append(f"moved it {math.dist(a, b):.0f} units (dz {b[2] - a[2]:+.0f})")
        elif f == "rot":
            said.append("turned it")
        else:
            said.append(f"changed its {f}")
    return ", ".join(said) or "rewritten it"


def _in_order(rows: list, put: set, order: list) -> list:
    """`rows` with each row put back (key in `put`) where it stood in the standing file: after the row before it."""
    if not put:
        return rows
    back = {_key(r): r for r in rows if _key(r) in put}
    out = [r for r in rows if _key(r) not in put]
    for k in [k for k in order if k in back]:
        i = order.index(k)
        prev = next((order[j] for j in range(i - 1, -1, -1) if any(_key(r) == order[j] for r in out)), None)
        at = 0 if prev is None else next(n for n, r in enumerate(out) if _key(r) == prev) + 1
        out.insert(at, back[k])
    return out


def keep_placed(pdir: Path, before: dict[str, str], tag: str, log=print) -> list[str]:
    """After a stage: every row a hand placed (`placed`) stands as the standing files (`before`: rel -> text) had it,
    and a row carried `on` a row put back moves back with it. Logs and returns each row kept with what the stage
    would have done. Writes through `write_rows`, so the hands' writes beside the run are kept too."""
    pdir = Path(pdir)
    held: dict[str, dict] = {}
    for (rel, key), h in placed(pdir).items():
        held.setdefault(rel, {})[key] = h
    said = []
    for rel, rows_held in sorted(held.items()):
        p = pdir / rel
        old_rows = {_key(r): r for r in _parse(p, before[rel])} if rel in before and before[rel].strip() else {}
        if not p.exists() and not old_rows:
            continue
        rows: list = _parse(p, p.read_text(encoding="utf-8")) if p.exists() else []
        by = {_key(r): i for i, r in enumerate(rows)}
        shift: dict[str, list] = {}
        put: set = set()
        changed = False
        for key, h in sorted(rows_held.items()):
            old, cur = old_rows.get(key), (rows[by[key]] if key in by else None)
            fields = h["fields"]
            if fields is None:
                if old == cur:
                    continue
                what = _would(old, cur, None)
                if cur is None:
                    rows.append(copy.deepcopy(old))
                    put.add(key)
                else:
                    rows[by[key]] = copy.deepcopy(old)       # None: a dropped row stays dropped
            else:
                if old is None:
                    continue                                 # nothing of the hand's stands to keep
                off = set(fields) if cur is None else {f for f in fields if cur.get(f) != old.get(f)}
                if not off:
                    continue
                what = _would(old, cur, off)
                if cur is None:
                    rows.append(copy.deepcopy(old))
                    put.add(key)
                else:
                    new = dict(cur)
                    for f in off:
                        if f in old:
                            new[f] = copy.deepcopy(old[f])
                        else:
                            new.pop(f, None)
                    rows[by[key]] = new
            if old is not None and cur is not None and isinstance(old.get("pos"), list) and isinstance(cur.get("pos"), list) \
                    and len(old["pos"]) == len(cur["pos"]) == 3 and old["pos"] != cur["pos"]:
                shift[key] = [o - c for o, c in zip(old["pos"], cur["pos"])]
            changed = True
            line = f"{tag}: {key} ({rel}) is placed by hand ({h['by']}): kept as the hand left it; the stage would have {what}"
            log(line)
            said.append(line)
        live = _in_order([r for r in rows if r is not None], put, list(old_rows))
        seen = set(shift)
        while shift:                                         # what the stage carried on a row put back comes back too
            nxt = {}
            for r in live:
                on, k = (r.get("seat") or {}).get("on"), _key(r)
                if on not in shift or k in seen or k in rows_held or not isinstance(r.get("pos"), list) or len(r["pos"]) != 3:
                    continue
                was = (old_rows.get(k) or {}).get("pos")
                back = [round(a + b, 3) for a, b in zip(r["pos"], shift[on])]
                if was is not None and max(abs(a - b) for a, b in zip(back, was)) < 0.5:
                    r["pos"] = list(was)                     # the stage moved it only with the row a hand placed
                    nxt[k] = shift[on]
                    seen.add(k)
            shift = nxt
        if changed:
            write_rows(p, live)
    return said
