"""The designed-against-built comparison (docs/design/paper-playtest.md, docs/design/quest-form.md).

    python3 -m tools.questform diff <designed dir|file> <built dir|file>

Names every difference between a designed form (compiled from the quest record) and the form read back from the
built plugin, field by field, one line each; exits 1 on any. Stages, objectives, refs and who-must-live rows pair by
their number or id; lines and triggers pair by id, then by what they are (speaker, kind, prompt and window; kind,
subject and stages). A stage's and a line's `results` compare as ordered lists (the builder keeps the form's order, so
a reorder or a dropped duplicate is a difference). The lists that are sets in the game (a line's conditions, an
objective's shown_at, completed_at and targets) compare as sets.

A ref the design places by an anchor is built at a position the design may not have known exactly. When the designed
ref has an `at`, the built ref must stand in the same cell within PLACED_UNITS of it, horizontally (x, y): the
builder's 300-unit navmesh tolerance plus the 100-unit door step. Only when the design has no `at` is the anchor
itself tested: within NEAR_UNITS of the anchor reference (`near`), or in a cell of the anchor place, or within
PLACE_UNITS of the place's position (`place`). The anchor reference's position comes from a ref of the designed form
with that existing form key, else the world database (an actor, a door or a house shell), else none, and then the
anchor is not compared. A new placement's `base`, `container` and `carried_by` are always compared; a built existing
reference against a designed new placement is a difference. An existing ref's `at` (an actor's or a door's, from the
census) is compared within POS_UNITS.

Every field of the form is compared, the form-level `names` (each item the form names that is not one of its refs, by
the name the player sees) and a thing's `name` among them, so a name the build or the reader drops is a difference;
except the form-level `texts` and `places` and a person's, door's or marker's `name`, a ref's `destination` and `text`
(display strings the builder takes from the world and the form's `places` and `texts`, whose own refusals cover them).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

NEAR_UNITS = 1024.0       # a placement "near" a reference stands within this of it (about 15 m)
PLACE_UNITS = 8192.0      # a placement "at" a place stands within this of the place's position (two cells)
PLACED_UNITS = 400.0      # an anchored ref stands within this of its designed `at` (navmesh 300 plus the door step 100)
POS_UNITS = 1.0           # an existing ref's designed and built positions agree within this


def _load(p) -> dict[str, dict]:
    p = Path(p)
    files = sorted(p.glob("*.json")) if p.is_dir() else [p]
    out = {}
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(d, dict) and "quest" in d and "stages" in d:
            out[d["quest"]["id"]] = d
    return out


def _canon(v):
    return json.dumps(v, sort_keys=True)


def _set(v):
    return sorted({_canon(x) for x in v})


class Resolver:
    """Where an anchor's reference stands and which cells a place holds."""

    def __init__(self, positions: dict | None = None, places: dict | None = None, use_db: bool = True):
        self.positions = dict(positions or {})     # form key -> {cell, interior, x, y, z}
        self.places = dict(places or {})           # place id -> {"cells": [...], "x": .., "y": ..}
        self.use_db = use_db
        self._w = None

    def _db(self):
        if self._w is None and self.use_db:
            from tools.argonia_world import db
            self._w = db.open()
        return self._w

    def position(self, key):
        if key in self.positions:
            return self.positions[key]
        w = self._db()
        if w is None:
            return None
        for sql in ("SELECT p.cell, c.interior, p.x, p.y, p.z FROM bmv_placement p JOIN bmv_cell c ON c.id = p.cell "
                    "WHERE p.id = ?", "SELECT d.cell, c.interior, d.x, d.y, d.z FROM bmv_door d JOIN bmv_cell c "
                    "ON c.id = d.cell WHERE d.id = ?", "SELECT s.cell, c.interior, s.x, s.y, s.z FROM bmv_shell s "
                    "JOIN bmv_cell c ON c.id = s.cell WHERE s.id = ?"):
            got = w.query(sql, key)
            if got:
                return {**dict(got[0]), "interior": bool(got[0]["interior"])}
        return None

    def place(self, pid):
        if pid in self.places:
            return self.places[pid]
        w = self._db()
        if w is None:
            return None
        cells = [r["cell"] for r in w.query("SELECT cell FROM bmv_settlement_cell WHERE settlement = ?", pid)]
        if not cells and w.query("SELECT id FROM bmv_cell WHERE id = ?", pid):
            cells = [pid]
        mk = w.query("SELECT x, y FROM bmv_map_marker WHERE settlement = ?", pid)
        if not cells and not mk:
            return None
        return {"cells": cells, **({"x": mk[0]["x"], "y": mk[0]["y"]} if mk else {})}

    def anchor_ok(self, anchor, at, designed_at=None) -> str | None:
        """None when the built position satisfies the anchor, else why not. An anchor reference the census cannot
        place (a static it does not list) is measured from the design's own `at`, the spot the record gives; with
        neither, the anchor is not compared: the builder has already refused a spot it could not find."""
        if at is None:
            return "the built ref has no position"
        if "near" in anchor:
            ref = self.position(anchor["near"]) or designed_at
            if ref is None:
                return None
            if ref["interior"] or at["interior"]:
                return None if ref["cell"] == at["cell"] else f"built in cell {at['cell']}, the anchor reference " \
                                                              f"stands in {ref['cell']}"
            d = math.dist((ref["x"], ref["y"], ref["z"]), (at["x"], at["y"], at["z"]))
            return None if d <= NEAR_UNITS else f"built {d:.0f} units from {anchor['near']} (near is {NEAR_UNITS:.0f})"
        pl = self.place(anchor["place"])
        if pl is None:
            return f"the anchor place {anchor['place']} is not known"
        if at["cell"] in pl.get("cells", []):
            return None
        if "x" in pl and not at["interior"]:
            d = math.dist((pl["x"], pl["y"]), (at["x"], at["y"]))
            if d <= PLACE_UNITS:
                return None
            return f"built {d:.0f} units from {anchor['place']} (at a place is {PLACE_UNITS:.0f})"
        return f"built in cell {at['cell']}, not one of {anchor['place']}'s cells"


def _fields(where, a, b, keys, sets=()) -> list[str]:
    out = []
    for k in keys:
        x, y = a.get(k), b.get(k)
        if k in sets:
            x, y = _set(x or []), _set(y or [])
        if x != y:
            out.append(f"{where}.{k}: designed {_show(a.get(k))}, built {_show(b.get(k))}")
    return out


def _show(v) -> str:
    s = json.dumps(v, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= 160 else s[:157] + "..."


def _pair(designed, built, key, fallback):
    """Pairs by key, then the unpaired by fallback; (pairs, only designed, only built)."""
    bd = {key(x): x for x in built}
    pairs, left = [], []
    for d in designed:
        b = bd.pop(key(d), None)
        (pairs.append((d, b)) if b is not None else left.append(d))
    rest = {}
    for b in bd.values():
        rest.setdefault(fallback(b), []).append(b)
    only_d = []
    for d in left:
        cands = rest.get(fallback(d))
        (pairs.append((d, cands.pop(0))) if cands else only_d.append(d))
    only_b = [b for v in rest.values() for b in v]
    return pairs, only_d, only_b


def diff_form(d: dict, b: dict, res: Resolver) -> list[str]:
    q = d["quest"]["id"]
    out = [f"{q}: quest.{k}: designed {_show(d['quest'].get(k))}, built {_show(b['quest'].get(k))}"
           for k in ("id", "editor_id", "name", "kind", "start") if d["quest"].get(k) != b["quest"].get(k)]
    out += [f"{q}: version: designed {d.get('version')}, built {b.get('version')}"] * (d.get("version") != b.get("version"))
    dn, bn = d.get("names", {}), b.get("names", {})
    out += [f"{q}: names.{k}: designed {_show(dn.get(k))}, built {_show(bn.get(k))}"
            for k in sorted(set(dn) | set(bn)) if dn.get(k) != bn.get(k)]

    def keyed(what, dl, bl, key, fallback, fn):
        pairs, od, ob = _pair(dl, bl, key, fallback)
        r = [f"{q}: {what} {key(x)}: designed only" for x in od]
        r += [f"{q}: {what} {key(x)}: built only" for x in ob]
        for x, y in pairs:
            r += [f"{q}: {line}" for line in fn(f"{what} {key(x)}", x, y)]
        return r

    out += keyed("stage", d["stages"], b["stages"], lambda s: s["number"], lambda s: s["number"],
                 lambda w, x, y: _fields(w, x, y, ("shown", "journal", "ending", "results"), sets=()))
    out += keyed("objective", d["objectives"], b["objectives"], lambda o: o["number"], lambda o: o["number"],
                 lambda w, x, y: _fields(w, x, y, ("text", "shown_at", "completed_at", "targets"),
                                         sets=("shown_at", "completed_at", "targets")))

    def ref_fn(w, x, y):
        r = _fields(w, {**x, "hostile": bool(x.get("hostile"))}, {**y, "hostile": bool(y.get("hostile"))},
                    ("kind", "enabled", "hostile", "lock", "owner", "contents", "count", "level")
                    + (("name",) if x.get("kind") == "thing" else ()))
        px, py = x["placement"], y["placement"]
        if "anchor" in px:
            for k in ("base", "container", "carried_by"):
                if px.get(k) != py.get(k):
                    r.append(f"{w}.placement.{k}: designed {_show(px.get(k))}, built {_show(py.get(k))}")
            ax, ay = x.get("at"), y.get("at")
            if ax is None:
                why = res.anchor_ok(px["anchor"], ay, None)
                if why:
                    r.append(f"{w}.placement.anchor {_show(px['anchor'])} not satisfied: {why}")
            elif ay is None:
                r.append(f"{w}.at: designed {_show(ax)}, built none")
            elif ax["cell"] != ay["cell"]:
                r.append(f"{w}.at: designed in cell {ax['cell']}, built in {ay['cell']}")
            else:
                d = math.dist((ax["x"], ax["y"]), (ay["x"], ay["y"]))
                if d > PLACED_UNITS:
                    r.append(f"{w}.at: built {d:.0f} units from the designed spot (allowed {PLACED_UNITS:.0f})")
        else:
            r += _fields(w, x, y, ("placement",))
            ax, ay = x.get("at"), y.get("at")
            if (ax is None) != (ay is None) or (ax and (ax["cell"] != ay["cell"] or ax["interior"] != ay["interior"]
                                                       or math.dist((ax["x"], ax["y"], ax["z"]),
                                                                    (ay["x"], ay["y"], ay["z"])) > POS_UNITS)):
                r.append(f"{w}.at: designed {_show(ax)}, built {_show(ay)}")
        return r
    out += keyed("ref", d["refs"], b["refs"], lambda r: r["id"], lambda r: r["id"], ref_fn)

    def line_key(ln):
        return (ln["speaker"], ln["kind"], ln["prompt"], ln["first_stage"], ln["last_stage"])
    pairs, od, ob = _pair(d["lines"], b["lines"], lambda ln: ln["id"], line_key)
    ids = {x["id"]: y["id"] for x, y in pairs}
    out += [f"{q}: line {x['id']}: designed only" for x in od] + [f"{q}: line {x['id']}: built only" for x in ob]
    for x, y in pairs:
        x = {**x, "answers": [ids.get(a, a) for a in x["answers"]]}
        out += [f"{q}: {line}" for line in _fields(
            f"line {x['id']}", x, y, ("speaker", "kind", "prompt", "text", "written", "conditions", "results",
                                      "first_stage", "last_stage", "answers"), sets=("conditions",))]
    out += keyed("trigger", d["triggers"], b["triggers"], lambda t: t["id"],
                 lambda t: (t["kind"], t.get("ref") or t.get("quest"), t.get("quest_stage"), t["prerequisite"],
                            t["sets"]),
                 lambda w, x, y: _fields(w, {**x, "choice": bool(x.get("choice"))}, {**y, "choice": bool(y.get("choice"))},
                                         ("kind", "ref", "quest", "quest_stage", "prerequisite", "sets", "until",
                                          "choice")))
    out += keyed("who-must-live", d["must_live"], b["must_live"], lambda m: m["ref"], lambda m: m["ref"],
                 lambda w, x, y: _fields(w, x, y, ("fail_stage", "main_message", "message", "from", "to")))
    return out


def diff(designed, built, res: Resolver | None = None) -> list[str]:
    ds, bs = _load(designed), _load(built)
    if res is None:
        pos = {r["placement"]["existing"]: r["at"] for f in ds.values() for r in f["refs"]
               if "existing" in r["placement"] and r.get("at")}
        res = Resolver(positions=pos)
    out = [f"{q}: designed only (no built form)" for q in sorted(set(ds) - set(bs))]
    out += [f"{q}: built only (no designed form)" for q in sorted(set(bs) - set(ds))]
    for q in sorted(set(ds) & set(bs)):
        out += diff_form(ds[q], bs[q], res)
    return out


def main(designed, built) -> int:
    lines = diff(designed, built)
    for ln in lines:
        print(ln)
    n = len(_load(designed))
    print(f"questform diff: {n} designed form(s), {len(lines)} difference(s)")
    return 1 if lines else 0
