"""A studio save applied to a place's files (docs/design/place-studio.md, Edits).

`apply(place_files, ops)` is pure and deterministic: it returns new place files and never changes its input. The
studio's load uses it in memory; finalise uses it to disk (`load_place`, `apply_save`, `write_place`). An op whose
`before` does not match the files is a conflict (`EditConflict`), never applied. Rows are kept in a canonical
order (by id, or by cell, or by base and position), so independent ops give the same files in any order.

Place files in memory:
    {"place": {...place.json...},
     "spaces": {space_id: {"refs": [row...], "space": {...} | None}},
     "clear": [...], "land": [...], "paths": [...], "people": [...]}
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

OPS = ("ref.add", "ref.remove", "ref.move", "veg.clear", "veg.restore", "land.patch",
       "path.add", "path.remove", "path.edit", "person.add", "person.remove", "person.edit")
CALLS = ("fault", "taste")
MOVE_FIELDS = ("pos", "rot", "scale", "seat")
TOL = 1e-3  # game units and radians; a before that differs by less than this matches


class EditError(ValueError):
    """A save or op that is malformed."""


class EditConflict(EditError):
    """An op whose before does not match the place files."""


# ---------- comparison and canonical order ----------

def same(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= TOL
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def _r1(v):
    return math.floor(v * 10 + 0.5) / 10   # JavaScript's Math.round(v * 10) / 10, so both sides key alike


def _veg_key(it):
    return (it["base"], tuple(_r1(v) for v in it["pos"]))


def canonical(files: dict) -> dict:
    out = copy.deepcopy(files)
    out.setdefault("place", {})
    out.setdefault("spaces", {})
    for sp in out["spaces"].values():
        sp.setdefault("refs", [])
        sp.setdefault("space", None)
        sp["refs"].sort(key=lambda r: r["id"])
    for k in ("clear", "land", "paths", "people"):
        out.setdefault(k, [])
    out["clear"].sort(key=_veg_key)
    out["land"].sort(key=lambda r: tuple(r["cell"]))
    for row in out["land"]:
        row["verts"].sort()
    out["paths"].sort(key=lambda r: r["id"])
    out["people"].sort(key=lambda r: r["id"])
    return out


# ---------- validation ----------

def _need(op, *keys):
    for k in keys:
        if k not in op:
            raise EditError(f"op {op.get('n')} ({op.get('op')}): missing '{k}'")


def check_op(op: dict) -> None:
    if not isinstance(op, dict):
        raise EditError(f"an op must be an object, got {type(op).__name__}")
    _need(op, "n", "op")
    kind = op["op"]
    if kind not in OPS:
        raise EditError(f"op {op['n']}: unknown op '{kind}'")
    if op.get("call", "fault") not in CALLS:
        raise EditError(f"op {op['n']}: call must be fault or taste, got {op.get('call')!r}")
    if kind.startswith(("ref.", "veg.", "land.")):
        _need(op, "space")
    if kind == "ref.add":
        _need(op, "ref")
        if "space_copy_of" in op and op["space"] == "exterior":
            raise EditError(f"op {op['n']} (ref.add): space_copy_of names an interior, not the exterior")
        for k in ("id", "base", "pos", "rot", "scale"):
            if k not in op["ref"]:
                raise EditError(f"op {op['n']} (ref.add): the ref has no '{k}'")
    elif kind == "ref.remove":
        _need(op, "id", "before")
    elif kind == "ref.move":
        _need(op, "id", "before", "after")
        if set(op["before"]) != set(op["after"]) or not set(op["after"]) <= set(MOVE_FIELDS) or not op["after"]:
            raise EditError(f"op {op['n']} (ref.move): before and after must name the same fields of {MOVE_FIELDS}")
    elif kind in ("veg.clear", "veg.restore"):
        _need(op, "items")
        for it in op["items"]:
            if "base" not in it or len(it.get("pos", [])) != 3:
                raise EditError(f"op {op['n']} ({kind}): each item needs base and a three-number pos")
    elif kind == "land.patch":
        _need(op, "cell", "verts")
        for v in op["verts"]:
            if len(v) != 4 or not all(0 <= int(x) <= 32 for x in v[:2]):
                raise EditError(f"op {op['n']} (land.patch): each vert is [row, col, before_dz, after_dz], row and col 0..32")
    elif kind.startswith(("path.", "person.")):
        _need(op, kind.split(".")[0])
        if "id" not in op[kind.split(".")[0]]:
            raise EditError(f"op {op['n']} ({kind}): the row has no id")
        if kind.endswith(".edit"):
            _need(op, "before")


def check_save(save: dict, place_id: str | None = None) -> None:
    """The schema check for edits/<save_id>.json."""
    if not isinstance(save, dict):
        raise EditError("a save must be a JSON object")
    for k in ("save_id", "place_id", "ops"):
        if k not in save:
            raise EditError(f"the save has no '{k}'")
    if place_id and save["place_id"] != place_id:
        raise EditError(f"the save is for place '{save['place_id']}', not '{place_id}'")
    if not isinstance(save["ops"], list):
        raise EditError("ops must be a list")
    last = None
    for op in save["ops"]:
        check_op(op)
        if last is not None and op["n"] <= last:
            raise EditError(f"op numbers must increase: {op['n']} follows {last}")
        last = op["n"]


# ---------- apply ----------

def _space(files, op):
    sp = files["spaces"].setdefault(op["space"], {"refs": [], "space": None})
    return sp["refs"]


def _find(rows, rid):
    for i, r in enumerate(rows):
        if r["id"] == rid:
            return i
    return None


def _conflict(op, msg):
    raise EditConflict(f"op {op['n']} ({op['op']}): {msg}")


def _apply_one(files, op):
    kind = op["op"]
    if kind == "ref.add":
        new_space = op["space"] not in files["spaces"]
        rows = _space(files, op)
        if _find(rows, op["ref"]["id"]) is not None:
            _conflict(op, f"ref {op['ref']['id']} already exists")
        rows.append(copy.deepcopy(op["ref"]))
        sp = files["spaces"][op["space"]]
        if op.get("space_copy_of"):
            if not new_space and (sp["space"] or len(rows) > 1):
                _conflict(op, f"space {op['space']} already exists; a copied room needs a new space id")
            sp["space"] = {"space_id": op["space"], "copy_of": op["space_copy_of"],
                           "name": op.get("space_name") or op["space"]}
            for sid, other in files["spaces"].items():
                for r in other["refs"]:
                    if (r.get("door") or {}).get("to_space") == op["space"]:
                        sp["space"].update(door_from=r["id"], parent=sid)
        to = (op["ref"].get("door") or {}).get("to_space")
        target = (files["spaces"].get(to) or {}).get("space")
        if target is not None and target.get("copy_of") and not target.get("door_from"):
            target.update(door_from=op["ref"]["id"], parent=op["space"])
    elif kind == "ref.remove":
        rows = _space(files, op)
        i = _find(rows, op["id"])
        if i is None:
            _conflict(op, f"ref {op['id']} is not in {op['space']}")
        if not same(rows[i], op["before"]):
            _conflict(op, f"ref {op['id']} differs from the save's before")
        rows.pop(i)
        if op.get("space_drop") and not rows:
            del files["spaces"][op["space"]]
    elif kind == "ref.move":
        rows = _space(files, op)
        i = _find(rows, op["id"])
        if i is None:
            _conflict(op, f"ref {op['id']} is not in {op['space']}")
        for k, v in op["before"].items():
            if not same(rows[i].get(k), v):
                _conflict(op, f"ref {op['id']} {k} is {rows[i].get(k)}, the save expected {v}")
        rows[i].update(copy.deepcopy(op["after"]))
    elif kind == "veg.clear":
        have = {_veg_key(c) for c in files["clear"]}
        for it in op["items"]:
            if _veg_key(it) in have:
                _conflict(op, f"plant {it['base']} at {it['pos']} is already cleared")
            files["clear"].append(dict(copy.deepcopy(it), by=it.get("by", "owner")))
            have.add(_veg_key(it))
    elif kind == "veg.restore":
        for it in op["items"]:
            idx = [i for i, c in enumerate(files["clear"]) if _veg_key(c) == _veg_key(it)]
            if not idx:
                _conflict(op, f"plant {it['base']} at {it['pos']} is not cleared")
            files["clear"].pop(idx[0])
    elif kind == "land.patch":
        cell = list(op["cell"])
        row = next((r for r in files["land"] if list(r["cell"]) == cell), None)
        if row is None:
            row = {"cell": cell, "verts": [], "why": op.get("note", "")}
            files["land"].append(row)
        cur = {(v[0], v[1]): v[2] for v in row["verts"]}
        for r, c, b, a in op["verts"]:
            if not same(cur.get((r, c), 0.0), b):
                _conflict(op, f"cell {cell} vertex {r},{c} is {cur.get((r, c), 0.0)}, the save expected {b}")
            if a == 0:
                cur.pop((r, c), None)
            else:
                cur[(r, c)] = a
        row["verts"] = [[r, c, dz] for (r, c), dz in sorted(cur.items())]
        if not row["verts"] and not row.get("textures"):
            files["land"].remove(row)
    else:
        table, verb = kind.split(".")
        rows = files["paths" if table == "path" else "people"]
        row = op[table]
        i = _find(rows, row["id"])
        if verb == "add":
            if i is not None:
                _conflict(op, f"{table} {row['id']} already exists")
            rows.append(copy.deepcopy(row))
        else:
            if i is None:
                _conflict(op, f"{table} {row['id']} does not exist")
            expect = op["before"] if verb == "edit" else op.get("before", row)
            if not same(rows[i], expect):
                _conflict(op, f"{table} {row['id']} differs from the save's before")
            if verb == "remove":
                rows.pop(i)
            else:
                rows[i] = copy.deepcopy(row)


def apply(place_files: dict, ops: list) -> dict:
    """Apply ops in order to a copy of the place files; raise EditConflict at the first op that does not fit."""
    for op in ops:
        check_op(op)
    files = canonical(place_files)
    for op in ops:
        _apply_one(files, op)
    _check_doors(files, ops)
    return canonical(files)


def _check_doors(files, ops):
    """Every door added into one of the place's own spaces is paired: its to_ref is there and leads back."""
    for op in ops:
        if op["op"] != "ref.add" or not (op["ref"].get("door") or {}).get("to_space"):
            continue
        d = op["ref"]["door"]
        if d["to_space"] not in files["spaces"] or files["spaces"][d["to_space"]]["space"] is None:
            continue   # leads into a room the place does not copy (the source's own, or the world's)
        rows = files["spaces"][d["to_space"]]["refs"]
        i = _find(rows, d.get("to_ref"))
        back = (rows[i].get("door") or {}) if i is not None else {}
        if i is not None and back.get("to_space") == op["space"] and back.get("to_ref") == op["ref"]["id"]:
            continue
        # a door copied unchanged from the source (no row in refs.jsonl) cannot be checked here
        if i is None and not any(o["op"] == "ref.add" and o["space"] == d["to_space"] for o in ops):
            continue
        _conflict(op, f"door {op['ref']['id']} leads to {d['to_space']}/{d.get('to_ref')}, which does not lead back")


def inverse(op: dict) -> dict:
    """The op that undoes op."""
    inv = copy.deepcopy(op)
    kind = op["op"]
    if kind == "ref.add":
        inv.update(op="ref.remove", id=op["ref"]["id"], before=op["ref"])
        del inv["ref"]
        if op.get("space_copy_of"):
            inv["space_drop"] = True
    elif kind == "ref.remove":
        inv.update(op="ref.add", ref=op["before"])
        del inv["id"], inv["before"]
        inv.pop("space_drop", None)
    elif kind == "ref.move":
        inv.update(before=op["after"], after=op["before"])
    elif kind == "veg.clear":
        inv["op"] = "veg.restore"
    elif kind == "veg.restore":
        inv["op"] = "veg.clear"
    elif kind == "land.patch":
        inv["verts"] = [[r, c, a, b] for r, c, b, a in op["verts"]]
    else:
        table, verb = kind.split(".")
        if verb == "add":
            inv.update(op=f"{table}.remove", before=op[table])
        elif verb == "remove":
            inv.update(op=f"{table}.add", **{table: op.get("before", op[table])})
            inv.pop("before", None)
        else:
            inv.update(before=op[table], **{table: op["before"]})
    return inv


def invert(ops: list) -> list:
    return [inverse(op) for op in reversed(ops)]


def apply_save(place_files: dict, save: dict) -> dict:
    """Apply a whole save once: place.json lists every save applied, and a second apply is rejected."""
    check_save(save, place_files.get("place", {}).get("place_id"))
    done = place_files.get("place", {}).get("saves_applied", [])
    if save["save_id"] in done:
        raise EditConflict(f"save {save['save_id']} is already applied to {save['place_id']}")
    out = apply(place_files, save["ops"])
    out["place"]["saves_applied"] = done + [save["save_id"]]
    prefs = [preference(op, save["save_id"]) for op in save["ops"] if op.get("call", "fault") == "taste"]
    if prefs:
        out["place"]["preferences"] = out["place"].get("preferences", []) + prefs
    return out


def preference(op: dict, save_id: str) -> dict:
    """A taste op as that place's preference row in place.json."""
    what = op.get("id") or (op.get("ref") or op.get("path") or op.get("person") or {}).get("id") or op.get("cell")
    return {"save": save_id, "n": op["n"], "op": op["op"], "what": what, "note": op.get("note", "")}


# ---------- disk ----------

def _jsonl(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _write_jsonl(p: Path, rows: list) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows))


def load_place(root: Path) -> dict:
    root = Path(root)
    files = {"place": json.loads((root / "place.json").read_text()) if (root / "place.json").exists() else {},
             "spaces": {}}
    for sp in sorted((root / "spaces").glob("*")) if (root / "spaces").exists() else []:
        sj = sp / "space.json"
        files["spaces"][sp.name] = {"refs": _jsonl(sp / "refs.jsonl"),
                                    "space": json.loads(sj.read_text()) if sj.exists() else None}
    for k in ("clear", "land", "paths", "people"):
        files[k] = _jsonl(root / f"{k}.jsonl")
    return canonical(files)


def write_place(root: Path, files: dict) -> None:
    root = Path(root)
    files = canonical(files)
    root.mkdir(parents=True, exist_ok=True)
    (root / "place.json").write_text(json.dumps(files["place"], indent=1, ensure_ascii=False) + "\n")
    for sid, sp in files["spaces"].items():
        _write_jsonl(root / "spaces" / sid / "refs.jsonl", sp["refs"])
        if sp.get("space") is not None:
            (root / "spaces" / sid / "space.json").write_text(json.dumps(sp["space"], indent=1, ensure_ascii=False) + "\n")
    for k in ("clear", "land", "paths", "people"):
        if files[k] or (root / f"{k}.jsonl").exists():
            _write_jsonl(root / f"{k}.jsonl", files[k])


def main(argv: list[str]) -> int:
    """python -m tools.places edits check <save.json> | apply <place_dir> <save.json> [--to <dir>]"""
    import sys
    if len(argv) >= 2 and argv[0] == "check":
        try:
            check_save(json.loads(Path(argv[1]).read_text()))
        except (EditError, json.JSONDecodeError) as e:
            print(f"bad save: {e}", file=sys.stderr)
            return 1
        print("ok")
        return 0
    if len(argv) >= 3 and argv[0] == "apply":
        to = Path(argv[argv.index("--to") + 1]) if "--to" in argv else Path(argv[1])
        try:
            out = apply_save(load_place(Path(argv[1])), json.loads(Path(argv[2]).read_text()))
        except EditError as e:
            print(f"not applied: {e}", file=sys.stderr)
            return 1
        write_place(to, out)
        print(f"applied to {to}")
        return 0
    print(main.__doc__, file=sys.stderr)
    return 2
