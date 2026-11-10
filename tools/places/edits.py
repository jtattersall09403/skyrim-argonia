"""A studio save applied to a place's files (docs/design/place-studio.md, Edits).

`apply(place_files, ops)` is pure and deterministic: it returns new place files and never changes its input. The
studio's load uses it in memory; finalise uses it to disk (`load_place`, `apply_save`, `write_place`). An op whose
`before` does not match the files is a conflict (`EditConflict`), never applied. Rows are kept in a canonical
order (by id, or by cell, or by base and position), so independent ops give the same files in any order.

Place files in memory:
    {"place": {...place.json...},
     "spaces": {space_id: {"refs": [row...], "space": {...} | None}},
     "clear": [...], "land": [...], "paths": [...], "people": [...],
     "identities": the people source (newworld/sources/people/<place_id>.json) | None,
     "stock": the stock source (newworld/sources/stock/places/<place_id>.json) | None}
The last two are the database's sources for who the place's people are and what the place holds (Stock). The
content ops (`identity.edit`, `stock.*`) apply to them, and `write_place` writes them back only when they changed.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

OWNER_TIER = "OWNER_STATED"   # the statement tier of the owner's own words (newworld/sources/key.json statement_tier)
CONTENT_OPS = ("identity.edit", "stock.container.set", "stock.container.remove", "stock.loose.add", "stock.loose.remove",
               "stock.loose.edit", "stock.possessions.set", "stock.trader.set", "stock.delivery.set")
OPS = ("ref.add", "ref.remove", "ref.move", "veg.clear", "veg.restore", "land.patch",
       "path.add", "path.remove", "path.edit", "person.add", "person.remove", "person.edit") + CONTENT_OPS
# A content op's row: the op's payload key, the source it lives in, its list there, the fields that name it (a
# delivery has none: it is found by its whole row)
CONTENT = {"identity": ("person", "identities", "people", ("id",)),
           "stock.container": ("container", "stock", "containers", ("space", "ref")),
           "stock.loose": ("loose", "stock", "loose", ("id",)),
           "stock.possessions": ("possessions", "stock", "possessions", ("person",)),
           "stock.trader": ("trader", "stock", "traders", ("person",)),
           "stock.delivery": ("delivery", "stock", "deliveries", ())}
# the order a source's rows are kept in, so independent ops give the same source in any order
SOURCE_ORDER = {"identities": {"households": ("id",), "people": ("id",)},
                "stock": {"containers": ("space", "ref"), "loose": ("id",), "possessions": ("person",),
                          "traders": ("person",), "deliveries": ("give_seq", "by", "person", "ref", "status", "why")}}
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
    for k in SOURCE_ORDER:   # the people and stock sources, when the files carry them
        if out.get(k) is not None:
            out[k] = canonical_source(k, out[k])
    return out


def _order(fields):
    return lambda r: tuple((0, r[f]) if isinstance(r.get(f), (int, float)) else (1, str(r.get(f) or "")) for f in fields)


def canonical_source(kind: str, doc: dict) -> dict:
    """A people or stock source with its rows in their kept order."""
    doc = copy.deepcopy(doc)
    for k, fields in SOURCE_ORDER[kind].items():
        if isinstance(doc.get(k), list):
            doc[k].sort(key=_order(fields))
    return doc


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
            if not isinstance(it, dict) or "base" not in it or not isinstance(it.get("pos"), list) or len(it["pos"]) != 3:
                raise EditError(f"op {op['n']} ({kind}): each item needs base and a three-number pos")
    elif kind == "land.patch":
        _need(op, "cell", "verts")
        for v in op["verts"]:
            num = isinstance(v, list) and len(v) == 4 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v)
            if not num or not all(x == int(x) and 0 <= x <= 32 for x in v[:2]):
                raise EditError(f"op {op['n']} (land.patch): each vert is [row, col, before_dz, after_dz], row and col 0..32")
    elif kind in CONTENT_OPS:
        _check_content(op)
    elif kind.startswith(("path.", "person.")):
        _need(op, kind.split(".")[0])
        if "id" not in op[kind.split(".")[0]]:
            raise EditError(f"op {op['n']} ({kind}): the row has no id")
        if kind.endswith(".edit"):
            _need(op, "before")


def _content(kind: str):
    return CONTENT[kind.rsplit(".", 1)[0]]


def _check_content(op: dict) -> None:
    """The row and its before: identity.edit and stock.loose.edit carry both; `.add` and `.remove` the row; a
    container's `.set` the row and before only when it replaces one; a possessions', trader's or delivery's `.set`
    either may be null (an added or a removed row), never both."""
    kind = op["op"]
    field, _, _, keys = _content(kind)
    verb = kind.rsplit(".", 1)[1]
    _need(op, field)
    nullable = kind in ("stock.possessions.set", "stock.trader.set", "stock.delivery.set")
    if verb == "edit" or kind in ("stock.possessions.set", "stock.trader.set"):
        _need(op, "before")
    row, before = op[field], op.get("before")
    if (row is None and not nullable) or (row is None and before is None):
        raise EditError(f"op {op['n']} ({kind}): '{field}' must be a row")
    for r in (row, before):
        if r is None:
            continue
        if not isinstance(r, dict):
            raise EditError(f"op {op['n']} ({kind}): '{field}' and before are rows (objects)")
        for k in keys or ("give_seq",):
            if k not in r:
                raise EditError(f"op {op['n']} ({kind}): the row has no '{k}'")
    if keys and row is not None and before is not None and any(row.get(k) != before.get(k) for k in keys):
        raise EditError(f"op {op['n']} ({kind}): the row and its before name different {'/'.join(keys)}")


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


SOURCE_KEYS = ("base", "pos", "rot", "scale")  # what a before is checked against on a copied space's implicit ref


def _implicit(files, op, rid):
    """The source row of a copied space's ref that has no row of its own (the room as copied), or None."""
    info = (files["spaces"].get(op["space"]) or {}).get("space") or {}
    if not info.get("copy_of") or files.get("_source") is None:
        return None
    rows = files["_source"](op["space"], info)
    if any(r.get("src") == rid and r["id"] != rid for r in files["spaces"][op["space"]]["refs"]):
        return None   # that source ref already has a row of its own, under its own id
    r = rows.get(rid)
    return copy.deepcopy(r) if r is not None else None


def _matches_source(files, op, row):
    """True when a copy ref's override row is the source ref unchanged (so the row is dropped)."""
    if not row.get("src") or row["id"] != row["src"] or row.get("removed"):
        return False
    info = (files["spaces"].get(op["space"]) or {}).get("space") or {}
    if not info.get("copy_of") or files.get("_source") is None:
        return False
    s = files["_source"](op["space"], info).get(row["src"])
    return s is not None and same(row, s)


def _conflict(op, msg):
    raise EditConflict(f"op {op['n']} ({op['op']}): {msg}")


def _apply_one(files, op):
    kind = op["op"]
    if kind == "ref.add":
        new_space = op["space"] not in files["spaces"]
        rows = _space(files, op)
        i = _find(rows, op["ref"]["id"])
        if i is not None and not rows[i].get("removed"):
            _conflict(op, f"ref {op['ref']['id']} already exists")
        if i is not None:   # a copy ref removed by an override row comes back
            rows.pop(i)
        if not _matches_source(files, op, op["ref"]):
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
        if i is not None and rows[i].get("removed"):
            i = None
        if i is None:
            src = _implicit(files, op, op["id"])
            if src is None:
                _conflict(op, f"ref {op['id']} is not in {op['space']}")
            for k in SOURCE_KEYS:
                if k in op["before"] and not same(src.get(k), op["before"][k]):
                    _conflict(op, f"ref {op['id']} {k} is {src.get(k)}, the save expected {op['before'][k]}")
            rows.append({"id": op["id"], "src": op["id"], "removed": True})
        else:
            if not same(rows[i], op["before"]):
                _conflict(op, f"ref {op['id']} differs from the save's before")
            row = rows.pop(i)
            info = files["spaces"][op["space"]].get("space") or {}
            if row.get("src") and info.get("copy_of") and files.get("_source") is not None \
                    and row["src"] in files["_source"](op["space"], info):
                rows.append({"id": row["id"], "src": row["src"], "removed": True})   # else the source ref returns
        if op.get("space_drop") and not rows:
            del files["spaces"][op["space"]]
    elif kind == "ref.move":
        rows = _space(files, op)
        i = _find(rows, op["id"])
        if i is not None and rows[i].get("removed"):
            _conflict(op, f"ref {op['id']} is removed from {op['space']}")
        if i is None:
            src = _implicit(files, op, op["id"])
            if src is None:
                _conflict(op, f"ref {op['id']} is not in {op['space']}")
            rows.append(src)
            i = len(rows) - 1
        for k, v in op["before"].items():
            if not same(rows[i].get(k), v):
                _conflict(op, f"ref {op['id']} {k} is {rows[i].get(k)}, the save expected {v}")
        rows[i].update(copy.deepcopy(op["after"]))
        if _matches_source(files, op, rows[i]):
            rows.pop(i)   # back to its source pose: the override goes
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
    elif kind in CONTENT_OPS:
        _apply_content(files, op)
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


def _words(x, out: dict) -> dict:
    """Every reason (`why`) and note text (`text`) in a row, at any depth, with the tier it is recorded at."""
    if isinstance(x, dict):
        if isinstance(x.get("why"), str):
            out[("why", x["why"])] = x.get("why_tier")
        if isinstance(x.get("text"), str) and "aspect" in x:
            out[("text", x["text"])] = x.get("tier")
        for k, v in x.items():
            if k not in ("why", "text"):
                _words(v, out)
    elif isinstance(x, list):
        for v in x:
            _words(v, out)
    return out


def owner_marks(row, before):
    """A content op's row with the owner's own words marked: every reason (`why`) or note text (`text`) the row holds
    that its before did not was written by the owner in the studio, so it is recorded at the owner's statement tier
    (`why_tier` beside a reason, a note's `tier`). A word the row keeps from its before keeps the tier it had there.
    Idempotent; js/stock.js ownerMarks is its mirror."""
    old = _words(before, {}) if before is not None else {}

    def walk(x):
        if isinstance(x, dict):
            for k, tk in (("why", "why_tier"), ("text", "tier")):
                if isinstance(x.get(k), str) and (k == "why" or "aspect" in x):
                    if (k, x[k]) not in old:
                        x[tk] = OWNER_TIER
                    elif old[(k, x[k])] and not x.get(tk):
                        x[tk] = old[(k, x[k])]
            for k, v in x.items():
                if k not in ("why", "text"):
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    row = copy.deepcopy(row)
    walk(row)
    return row


def mark_owner(ops: list) -> list:
    """The ops of a studio save with the owner's new words marked (owner_marks on each content op's row against its
    before): the studio marks them as it makes an op (js/stock.js opFor), and finalise marks a save again before it
    records it, so a save from any client goes in at the owner's tier. An op's inverse is never marked: undoing gives
    back the row as it was."""
    out, marked = [], {}    # a row as the save wrote it -> as marked, so a later op's before names the marked row
    key = lambda r: json.dumps(r, sort_keys=True)   # noqa: E731
    for op in ops:
        op = copy.deepcopy(op)
        if op.get("op") in CONTENT_OPS:
            field = _content(op["op"])[0]
            for k in ("before", field):
                if isinstance(op.get(k), dict) and key(op[k]) in marked:
                    op[k] = copy.deepcopy(marked[key(op[k])])
            if not op["op"].endswith(".remove") and op.get(field) is not None:
                was = key(op[field])
                op[field] = owner_marks(op[field], op.get("before"))
                marked[was] = op[field]
        out.append(op)
    return out


def _apply_content(files, op):
    """identity.edit and stock.*: a row of the people or stock source replaced, added or removed. A row with no
    before is added (a conflict when one of its name is there); every before must equal the source's row."""
    kind = op["op"]
    field, doc_key, table, keys = _content(kind)
    verb = kind.rsplit(".", 1)[1]
    doc = files.get(doc_key)
    if doc is None:
        _conflict(op, f"the place has no {'people' if doc_key == 'identities' else 'stock'} source")
    rows = doc.setdefault(table, [])
    if verb == "remove":
        row, before = None, op[field]
    else:
        row, before = op[field], (None if verb == "add" else op.get("before"))

    def find(r):
        if not keys:
            return next((i for i, x in enumerate(rows) if same(x, r)), None)
        return next((i for i, x in enumerate(rows) if all(x.get(k) == r.get(k) for k in keys)), None)
    named = row if row is not None else before
    what = f"{field} {'/'.join(str(named.get(k)) for k in keys or ('give_seq',))}"
    if before is None:
        if find(row) is not None:
            _conflict(op, f"{what} already exists")
        rows.append(copy.deepcopy(row))
        return
    i = find(before)
    if i is None:
        _conflict(op, f"{what} does not exist")
    if not same(rows[i], before):
        _conflict(op, f"{what} differs from the save's before")
    if row is None:
        rows.pop(i)
    else:
        rows[i] = copy.deepcopy(row)


def apply(place_files: dict, ops: list, source=None) -> dict:
    """Apply ops in order to a copy of the place files; raise EditConflict at the first op that does not fit.

    source(space_id, space_info) -> {source id: row}: a copied space's refs as copied from the source, which the
    place files list only when changed (Place files); a dict {space_id: [row...]} serves too. Without it only
    listed refs can be edited."""
    for op in ops:
        check_op(op)
    files = canonical(place_files)
    if isinstance(source, dict):
        given = {sid: {r["id"]: r for r in rows} for sid, rows in source.items()}
        source = lambda sid, info: given.get(sid, {})   # noqa: E731
    files["_source"] = _cached(source) if source else None
    for op in ops:
        _apply_one(files, op)
    _check_doors(files, ops)
    files.pop("_source")
    return canonical(files)


def _cached(source):
    memo = {}

    def get(sid, info):
        if sid not in memo:
            memo[sid] = source(sid, info)
        return memo[sid]
    return get


def bundle_source(bundles: Path | None = None):
    """The source resolver over the source bundles: a copied space's refs, by the draft bundle's own reading of the
    source cell and of the build's room rule (tools.places.draft_bundle.copy_space)."""
    from tools.places import draft_bundle

    def get(sid, info):
        src = (bundles or draft_bundle.BUNDLES) / f"src.{info['copy_of'].split('/', 1)[0]}"
        return {r["id"]: r for r in draft_bundle.copy_space(info, [], src)}
    return get


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
    elif kind in CONTENT_OPS:
        field = _content(kind)[0]
        base, verb = kind.rsplit(".", 1)
        if verb == "add":
            inv["op"] = f"{base}.remove"
        elif verb == "remove":
            inv["op"] = f"{base}.set" if base == "stock.container" else f"{base}.add"
            inv.pop("before", None)
        elif kind == "stock.container.set" and op.get("before") is None:
            inv["op"] = "stock.container.remove"
            inv.pop("before", None)
        else:
            inv.update({field: op.get("before"), "before": op[field]})
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


def apply_save(place_files: dict, save: dict, source=None) -> dict:
    """Apply a whole save once: place.json lists every save applied, and a second apply is rejected."""
    check_save(save, place_files.get("place", {}).get("place_id"))
    done = place_files.get("place", {}).get("saves_applied", [])
    if save["save_id"] in done:
        raise EditConflict(f"save {save['save_id']} is already applied to {save['place_id']}")
    out = apply(place_files, mark_owner(save["ops"]), source)   # the studio's edits are the owner's words
    out["place"]["saves_applied"] = done + [save["save_id"]]
    prefs = [preference(op, save["save_id"]) for op in save["ops"] if op.get("call", "fault") == "taste"]
    if prefs:
        out["place"]["preferences"] = out["place"].get("preferences", []) + prefs
    return out


def preference(op: dict, save_id: str) -> dict:
    """A taste op as that place's preference row in place.json."""
    row = next((op[k] or op.get("before") for k in ("container", "loose", "possessions", "trader", "delivery")
                if k in op), None) or {}
    what = (op.get("id") or (op.get("ref") or op.get("path") or op.get("person") or {}).get("id") or op.get("cell")
            or (f"{row.get('space')}/{row['ref']}" if "container" in op else None)
            or row.get("id") or row.get("person") or (f"give {row['give_seq']}" if "give_seq" in row else None))
    return {"save": save_id, "n": op["n"], "op": op["op"], "what": what, "note": op.get("note", "")}


# ---------- disk ----------

def _jsonl(p: Path) -> list:
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def _write_jsonl(p: Path, rows: list) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows))


SOURCE_FILES = {"identities": "people/{pid}.json", "stock": "stock/places/{pid}.json"}


def source_paths(root: Path, files: dict, sources: Path | None = None) -> dict:
    """The place's people and stock sources: under `sources`, by default the newworld/sources folder beside the
    places folder (newworld/places/<id> -> newworld/sources)."""
    pid = (files.get("place") or {}).get("place_id") or Path(root).name
    base = Path(sources) if sources else Path(root).resolve().parent.parent / "sources"
    return {k: base / rel.format(pid=pid) for k, rel in SOURCE_FILES.items()}


def dump_stock(doc: dict) -> str:
    """The stock source as it is kept: one row per line under each list."""
    out = []
    for k, v in doc.items():
        if isinstance(v, list) and v and all(isinstance(r, dict) for r in v):
            body = ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in v)
            out.append(f" {json.dumps(k)}: [\n{body}\n ]")
        else:
            out.append(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}")
    return "{\n" + ",\n".join(out) + "\n}\n"


def load_place(root: Path, sources: Path | None = None) -> dict:
    """The place files, with the place's people and stock sources when they exist."""
    root = Path(root)
    files = {"place": json.loads((root / "place.json").read_text()) if (root / "place.json").exists() else {},
             "spaces": {}}
    for k, p in source_paths(root, files, sources).items():
        if p.exists():
            files[k] = json.loads(p.read_text(encoding="utf-8"))
    for sp in sorted((root / "spaces").glob("*")) if (root / "spaces").exists() else []:
        sj = sp / "space.json"
        files["spaces"][sp.name] = {"refs": _jsonl(sp / "refs.jsonl"),
                                    "space": json.loads(sj.read_text()) if sj.exists() else None}
    for k in ("clear", "land", "paths", "people"):
        files[k] = _jsonl(root / f"{k}.jsonl")
    return canonical(files)


def write_sources(root: Path, files: dict, sources: Path | None = None) -> list[Path]:
    """Write the people and stock sources whose rows changed (an unchanged source is never rewritten, so its order
    and layout stay as its author left them); returns the paths written."""
    written = []
    for k, p in source_paths(root, files, sources).items():
        doc = files.get(k)
        if doc is None:
            continue
        old = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        if old is not None and same(canonical_source(k, old), canonical_source(k, doc)):
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        text = dump_stock(doc) if k == "stock" else json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
        tmp = p.with_name(f".{p.name}.tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(p)
        written.append(p)
    return written


def write_place(root: Path, files: dict, sources: Path | None = None) -> None:
    root = Path(root)
    files = canonical(files)
    write_sources(root, files, sources)
    root.mkdir(parents=True, exist_ok=True)
    (root / "place.json").write_text(json.dumps(files["place"], indent=1, ensure_ascii=False) + "\n")
    # a space the files no longer have (a copied room taken out again) leaves no folder behind
    import shutil
    for old in sorted((root / "spaces").glob("*")) if (root / "spaces").exists() else []:
        if old.is_dir() and old.name not in files["spaces"]:
            shutil.rmtree(old)
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
            out = apply_save(load_place(Path(argv[1])), json.loads(Path(argv[2]).read_text()), bundle_source())
        except EditError as e:
            print(f"not applied: {e}", file=sys.stderr)
            return 1
        write_place(to, out)
        print(f"applied to {to}")
        return 0
    print(main.__doc__, file=sys.stderr)
    return 2
