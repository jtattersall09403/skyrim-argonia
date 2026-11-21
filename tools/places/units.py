"""A place's units: each a thing a builder would call one structure, derived from the source's own arrangement.

    python -m tools.places units <place> [--all] [--source] [--json]
    python -m tools.places units plan <place> [--margin 30] [--out plan.json]
    python -m tools.places units apply <place> [UNIT ...] [--why=...]   (the plan written as the agent's draft edits;
        a Hist unit is seated by its own rule: what lay on the source's ground on ours, the rest on its trunk)
    python -m tools.places units <place> --joints [--json]   one row per end of every stair, ramp, bridge, walkway
        and boardwalk piece: what its end line meets, the gap along and in height, the verdict (shape.joints)

A house unit is its building body with the platform or deck it stands on, the posts under them, the steps and
railings at its deck, the doors set in its walls (and the room they lead to) and what rests on, hangs on or is fixed
to it; a walkway, bridge or dock is a unit of its own whose joins name the units it rests on; a boat, a rack, a stall
is a small unit. A Hist is one unit: its trunk with its roots, glands, gland roots, flowers, vine floors, the gland
lights and chimes hung in its crown, and its sap pool, kept in the source's arrangement about the trunk. Other trees,
rocks, roots and ground cover belong to the ground (a plant standing on a deck excepted).
Membership comes from contact and support among the SOURCE's pieces at the source's positions (the look tool's
rules, tools/places/look/geom.py), carried to the draft by each row's `src`; draft rows with no source ref are
grouped the same way where they stand.

Each unit is measured against our ground (the place's heightfield and water as the look tool reads them): the floor
or deck against the highest ground under the footprint, each foot against the ground under it and its leg (how far
it reaches below the standing level in the source), the body against its own deck, each door's sill against its
floor and the ground before it, each join against the source's relative height. The plan gives every unit one
vertical offset, solved over the join graph, or a spot nearby where it fits, or the joins it must give up.
"""
from __future__ import annotations

import copy
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

from tools.places import shape
from tools.places.look import geom

MARGIN = 30.0          # a floor stands this far over the highest ground under its footprint
DECK_MARGIN = 60.0     # a stilt house's deck stays a deck: this far over the ground at its highest corner
BURY_MIN = 16.0        # a foot is buried at least this far
STEP = 16.0            # a join meets what it rests on within a step
GAP_TOL = 8.0          # a body's gap to its own deck may differ from the source's by this much
SILL_TOL = 16.0        # a door's sill against its floor may differ from the source's by this much
HIGH_DECK = 250.0      # a deck this far over the ground needs steps
GROUND_LEG = 96.0      # how far a body standing on the ground (no deck) may sink: its foundation
TOUCH = 16.0
SMALL_SINK = 48.0      # a small unit (a rack, a cart) may sink this far into the ground at its lowest corner's ground
# the word lists are the one classifier's (tools/places/classify.py)
from tools.places.classify import (BODY_WORDS, DECK_WORDS, GROUND_KINDS, RAIL_WORDS,  # noqa: E402
                                   SPAN_UNIT_WORDS as SPAN_WORDS, STEPS_RE, NOT_STRUCTURE, GROUND_CLASSES, kind_of, post as _post)
from tools.places.classify import LOOSE_KINDS as LOOSE  # noqa: E402
SPANS = ("walkway", "bridge", "dock")
HIST_TRUNK = re.compile(r"^(ArgoniaTreeHist\d|Hist(Tree|Trunk)\d)", re.I)   # a Hist's tree or trunk, living or dead
HIST_REACH = 256.0     # a root, gland, flower or vine floor of a Hist lies within this of its trunk's box
HIST_SNAP = 128.0      # a draft's added Hist stands for the source's when it stands this near the source's spot


FOOT_BAND = 48.0   # a mesh's feet within this of its lowest point are the feet it stands on


# ---------- pieces ----------
def _words(p: dict) -> str:
    return f"{p.get('edid') or ''} {p.get('model') or ''}".lower()


def ground_piece(p: dict) -> bool:
    """A tree, rock, root, plant or ground cover: it belongs to the ground, never to a building."""
    return p.get("kind") in GROUND_KINDS or kind_of(p) in GROUND_CLASSES


def pieces_of(rows: list[dict], bases: dict, bounds) -> list[dict]:
    """Rows as the look tool's pieces (geom.py): {id, base, kind, edid, model, m, lo, hi, door, src, row}."""
    from tools.places import xform
    out = []
    for r in rows:
        if not r.get("pos") or r.get("removed"):
            continue
        b = bases.get(r["base"]) or {}
        (lo, hi), ok = bounds(b)
        out.append({"id": r["id"], "base": r["base"], "kind": r.get("kind") or b.get("kind"), "edid": b.get("edid"),
                    "model": b.get("model"), "resolved": ok and bool(b), "cluster": r.get("cluster"),
                    "m": xform.matrix(r["pos"], r.get("rot") or [0, 0, 0], r.get("scale", 1)),
                    "lo": list(lo), "hi": list(hi), "door": r.get("door"), "src": r.get("src"), "row": r})
    return out


def footprint_bounds(out: Path):
    """The bounds rule of the look tool without its converter: the models' measured extents, else the base's."""
    try:
        fp = json.loads((out / "footprints.json").read_text())
    except (OSError, ValueError):
        fp = {}

    def bounds(b: dict):
        got = fp.get(str(b.get("model") or "").lower())
        return (got or b.get("bounds") or [[-32, -32, 0], [32, 32, 64]]), got is not None or bool(b.get("bounds"))
    return bounds


_DECK: dict = {}


def deck_top(p: dict, bases: dict | None) -> float:
    """The walked top of a deck piece (its collision's level deck), else the top of its box."""
    hi = float(geom.aabb(p)[1][2])
    if bases is None or p.get("kind") != "building":
        return hi
    b = bases.get(p["base"]) or {}
    k = str(b.get("model") or "").lower()
    if k not in _DECK:
        try:
            from tools.places.draft import walk
            _DECK[k] = walk.deck_rect(b)
        except Exception:  # noqa: BLE001  no collision to read: the box's top
            _DECK[k] = None
    d = _DECK[k]
    if d is None:
        return hi
    r = p["row"]
    return float(r["pos"][2]) + d[0] * float(r.get("scale") or 1.0)


# ---------- derivation ----------
def hist_trunk(p: dict) -> bool:
    return bool(HIST_TRUNK.match(str(p.get("edid") or "")))


def hist_role(p: dict) -> str | None:
    """A piece's part of a Hist, by its words: root (a HistRoot or a gland's roots), gland, floor (a mossy vine
    floor), sap (the Hist's sap water), hanging (a gland light, a flower, a chime); None when it is no part of one."""
    e, w = str(p.get("edid") or ""), _words(p)
    if hist_trunk(p):
        return None
    if "hist" in w and "sap" in w or e == "WaterPuddleHist":
        return "sap"
    if re.match(r"^HistRoot|^HistGland\d*Roots", e):
        return "root"
    if re.match(r"^HistGland\d", e):
        return "gland"
    if "mossyvinesfloor" in w:
        return "floor"
    if "hist" in w or "chime" in w:
        return "hanging"
    return None


def _role0(p: dict) -> str:
    w = _words(p)
    if ground_piece(p):
        return "ground"
    if p.get("kind") == "door":
        return "door"
    if p.get("kind") in LOOSE and not p.get("model"):
        return "loose"
    if kind_of(p) in NOT_STRUCTURE:
        return "fixture"   # a light, effect, marker, fixture or mound: never a body, deck, post, steps or span
    if STEPS_RE.search(w) and p.get("kind") in ("building", "static"):
        return "steps"
    if p.get("kind") == "building" and any(x in w for x in BODY_WORDS) and not any(x in w for x in DECK_WORDS + ("plank", "walkway", "bridge")):
        return "body"
    if p.get("kind") in ("building", "static") and any(x in w for x in SPAN_WORDS):
        return "span"
    return "thing"


def _uf(n):
    par = list(range(n))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    def union(a, b):
        par[find(a)] = find(b)
    return find, union


def derive(pieces: list[dict], ground=None, bases: dict | None = None, prefix: str = "") -> list[dict]:
    """The units of pieces at their own positions (a source's, where everything is right by construction).
    Returns [{id, kind, pieces: {role: [ids]}, interior, doors: [ids], joins: [{unit, piece, with}]}]."""
    if not pieces:
        return []
    boxes = {p["id"]: geom.aabb(p) for p in pieces}
    by = {p["id"]: p for p in pieces}
    role0 = {p["id"]: _role0(p) for p in pieces}
    solids = [p for p in pieces if geom.solid(p) and role0[p["id"]] != "ground"]
    B = geom.Boxes(solids, boxes)

    def gap(a, b):
        return geom.box_gap(*boxes[a], *boxes[b])

    def under(pid, tol=32.0):
        lo, hi = boxes[pid]
        pts = [((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)] + [(q[0], q[1]) for q in geom.bottom_points(by[pid])]
        got = set()
        for x, y in pts:
            got.update(B.ids[i] for i in B.under(x, y, float(lo[2]), tol))
        got.discard(pid)
        return sorted(got, key=lambda q: (-float(boxes[q][1][2]), q))   # the nearest under first, in one order

    unit_of: dict[str, int] = {}
    role: dict[str, str] = {}
    units: list[dict] = []
    for t in sorted((p for p in pieces if hist_trunk(p)), key=lambda p: p["id"]):
        units.append({"kind": "hist", "pieces": {}})
        unit_of[t["id"]], role[t["id"]] = len(units) - 1, "trunk"
    trunks = [i for i, r in role.items() if r == "trunk"]
    for p in pieces:
        r = hist_role(p)
        if r is None or p["id"] in unit_of or not trunks:
            continue
        d, t = min((gap(p["id"], t), t) for t in trunks)
        lo, hi = boxes[p["id"]]
        tlo, thi = boxes[t]
        if r == "hanging" and not ("hist" in _words(p) or (tlo <= lo).all() and (hi <= thi).all()):
            continue   # a chime or lantern counts only inside the crown's box
        if d <= HIST_REACH:
            unit_of[p["id"]], role[p["id"]] = unit_of[t], r
    # bodies: by their words, or a large building piece a door is set in; bodies standing in each other are one
    doors = [p["id"] for p in pieces if role0[p["id"]] == "door"]
    for p in pieces:
        if role0[p["id"]] in ("thing",) and p.get("kind") == "building":
            lo, hi = boxes[p["id"]]
            if (hi[0] - lo[0]) >= 300 and (hi[1] - lo[1]) >= 300 and not any(x in _words(p) for x in DECK_WORDS + SPAN_WORDS) \
                    and any(gap(d, p["id"]) <= TOUCH for d in doors):
                role0[p["id"]] = "body"
    bodies = [i for i, r in role0.items() if r == "body"]
    find, union = _uf(len(bodies))
    for a in range(len(bodies)):
        for b in range(a + 1, len(bodies)):
            if gap(bodies[a], bodies[b]) < -TOUCH:
                union(a, b)
    # a door's room joins the bodies its doors are set in (a house with two doors is one house)
    door_body = {}
    for d in doors:
        near = sorted((gap(d, b), b) for b in bodies)
        if near and near[0][0] <= 2 * TOUCH:
            door_body[d] = near[0][1]
    by_room: dict = {}
    for d, b in door_body.items():
        room = (by[d].get("door") or {}).get("to_space")
        if room:
            if room in by_room:
                union(bodies.index(b), bodies.index(by_room[room]))
            by_room[room] = b
    groups: dict = {}
    for i, b in enumerate(bodies):
        groups.setdefault(find(i), []).append(b)
    for g in groups.values():
        units.append({"kind": "house", "pieces": {}})
        for b in g:
            unit_of[b], role[b] = len(units) - 1, "body"

    def add(pid, u, r):
        unit_of[pid], role[pid] = u, r

    # decks: what the bodies stand on; posts: what the decks stand on (twice: a deck on beams on posts)
    for u in range(len(units)):
        if units[u]["kind"] != "house":
            continue
        mine = [b for b, k in unit_of.items() if k == u]
        for b in mine:
            blo = float(boxes[b][0][2])
            for s in under(b):   # a deck: a building piece of some size whose top is at the body's floor
                lo, hi = boxes[s]
                if s not in unit_of and role0[s] not in ("body", "door", "steps") and by[s].get("kind") == "building" \
                        and (hi[0] - lo[0]) * (hi[1] - lo[1]) >= 150 * 150 and float(hi[2]) <= blo + 48:
                    add(s, u, "deck")
        for _ in range(2):
            for d in [q for q, k in unit_of.items() if k == u and role[q] in ("deck", "posts")]:
                for s in under(d):
                    if s not in unit_of and role0[s] in ("thing", "span") and boxes[s][0][2] < boxes[d][0][2] - TOUCH:
                        add(s, u, "posts")
            for d in [q for q, k in unit_of.items() if k == u and role[q] == "deck"]:
                for p in pieces:
                    if p["id"] not in unit_of and _post(p) and role0[p["id"]] == "thing" \
                            and gap(p["id"], d) <= TOUCH and boxes[p["id"]][0][2] < boxes[d][0][2]:
                        add(p["id"], u, "posts")

    def grow(kinds):
        """Attach what rests on, hangs on or is fixed to a unit's pieces, until nothing more attaches."""
        for _ in range(6):
            moved = False
            for p in pieces:
                pid, r0 = p["id"], role0[p["id"]]
                if pid in unit_of or r0 == "loose":
                    continue
                if r0 == "ground" and p.get("kind") not in ("plant", "groundcover", "flora"):
                    continue
                lo, hi = boxes[pid]
                touch = [q for q in unit_of if units[unit_of[q]]["kind"] in kinds and gap(pid, q) <= TOUCH]
                if not touch:
                    continue
                if r0 == "door":
                    hit = [q for q in touch if role[q] == "body"] or touch
                    add(pid, unit_of[hit[0]], "door")
                elif r0 == "steps":
                    add(pid, unit_of[touch[0]], "steps")
                elif r0 == "ground":   # a plant standing on a deck
                    on = [q for q in under(pid, 24) if q in unit_of and role[q] == "deck"]
                    if not on:
                        continue
                    add(pid, unit_of[on[0]], "on")
                elif r0 == "span" and kinds == ("house",):
                    continue
                else:
                    on = [q for q in under(pid, 24) if q in unit_of]
                    if on:
                        rr = "railing" if any(x in _words(p) for x in RAIL_WORDS) else "on"
                        add(pid, unit_of[on[0]], rr)
                    elif geom.wall_fixed(p) or geom.hangs(p) or any(x in _words(p) for x in RAIL_WORDS) or "door" in _words(p):
                        rr = "railing" if any(x in _words(p) for x in RAIL_WORDS) else ("door" if "door" in _words(p) else "hanging")
                        add(pid, unit_of[touch[0]], rr)
                    else:
                        continue
                moved = True
            if not moved:
                return

    grow(("house",))
    # walkways, bridges and docks: the span pieces left, in touching runs, with steps and what rests on them
    spans = [p["id"] for p in pieces if role0[p["id"]] == "span" and p["id"] not in unit_of]
    def legged(pid):   # a dock piece stands on its own posts down to the ground; a walkway or bridge is slung
        lo, hi = boxes[pid]
        g = ground.height(float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2) if ground is not None else None
        return g is not None and float(lo[2]) <= g + geom.END_TOL and not re.search(r"walkway|bridge|plank|gangway", _words(by[pid]))
    leg = {s: legged(s) for s in spans}
    find2, union2 = _uf(len(spans))
    for a in range(len(spans)):
        for b in range(a + 1, len(spans)):
            if leg[spans[a]] == leg[spans[b]] and gap(spans[a], spans[b]) <= TOUCH:
                union2(a, b)
    runs: dict = {}
    for i, s in enumerate(spans):
        runs.setdefault(find2(i), []).append(s)
    for run in runs.values():
        words = " ".join(_words(by[s]) for s in run)
        units.append({"kind": "dock" if leg[run[0]] else ("bridge" if "bridge" in words else "walkway"), "pieces": {}})
        for s in run:
            add(s, len(units) - 1, "deck")
    grow(("house",) + SPANS)
    # small units: the touching runs of what is built and left (a boat, a rack, a stall); a lone thing alone
    rest = [p["id"] for p in pieces if p["id"] not in unit_of and role0[p["id"]] in ("thing", "steps", "span", "body")
            and p.get("model")]
    find3, union3 = _uf(len(rest))
    for a in range(len(rest)):
        for b in range(a + 1, len(rest)):
            if gap(rest[a], rest[b]) <= TOUCH:
                union3(a, b)
    smalls: dict = {}
    for i, s in enumerate(rest):
        smalls.setdefault(find3(i), []).append(s)
    for run in smalls.values():
        big = max(run, key=lambda q: float(np.prod(boxes[q][1] - boxes[q][0])))
        units.append({"kind": "boat" if geom.vessel(by[big]) else ("small" if len(run) > 1 or by[big].get("kind") == "building" else "thing"),
                      "pieces": {}})
        for s in run:
            add(s, len(units) - 1, "body" if s == big else "on")
    # lights and markers: the unit whose piece holds them
    for p in pieces:
        if p["id"] in unit_of or role0[p["id"]] not in ("loose", "fixture"):
            continue
        x, y, z = p["m"][0][3], p["m"][1][3], p["m"][2][3]
        for q, u in list(unit_of.items()):
            lo, hi = boxes[q]
            if units[u]["kind"] not in ("thing", "hist") and lo[0] - 32 <= x <= hi[0] + 32 and lo[1] - 32 <= y <= hi[1] + 32 and lo[2] - 32 <= z <= hi[2] + 64:
                add(p["id"], u, "hanging" if p.get("kind") == "light" or role0[p["id"]] == "fixture" else "on")
                break

    for pid, u in unit_of.items():
        units[u]["pieces"].setdefault(role[pid], []).append(pid)
    # joins: a walkway or dock touching a unit rests on it there
    for u, un in enumerate(units):
        un["joins"] = []
    for u, un in enumerate(units):
        if un["kind"] not in SPANS:
            continue
        seen = set()
        for s in un["pieces"].get("deck", []) + un["pieces"].get("steps", []):
            for q, v in unit_of.items():
                if v == u or v in seen or units[v]["kind"] in ("thing",) or role[q] not in ("deck", "body", "posts", "steps"):
                    continue
                if units[v]["kind"] in SPANS and (un["kind"] == "dock" or units[v]["kind"] != "dock"):
                    continue
                if gap(s, q) <= TOUCH:
                    seen.add(v)
                    un["joins"].append({"unit": v, "piece": s, "with": q})
        # ends on the ground: a span end within reach of the ground, touching no other piece of its own run
        if ground is not None:
            for s in un["pieces"].get("deck", []):
                for e in geom.end_points(by[s]):
                    g = ground.height(float(e[0]), float(e[1]))
                    mine = any(t != s and boxes[t][0][0] - TOUCH <= e[0] <= boxes[t][1][0] + TOUCH
                               and boxes[t][0][1] - TOUCH <= e[1] <= boxes[t][1][1] + TOUCH for t in un["pieces"]["deck"])
                    if g is not None and not mine and abs(float(e[2]) - g) <= geom.END_TOL \
                            and not any(j["piece"] == s for j in un["joins"]):
                        un["joins"].append({"unit": "ground", "piece": s, "at": [round(float(e[0])), round(float(e[1]))]})
                        break
    # names: a house by its room, the rest by kind and order west to east
    names, count = [], {}
    for un in units:
        if un["kind"] == "house":
            rooms = sorted({(by[d].get("door") or {}).get("to_space") for d in un["pieces"].get("door", [])} - {None})
            un["interior"] = rooms[0] if rooms else None
    order = sorted(range(len(units)), key=lambda i: (units[i]["kind"], _centre(units[i], boxes)))
    for i in order:
        un = units[i]
        if un["kind"] == "house" and un.get("interior") and f"house.{un['interior']}" not in names:
            nm = f"house.{un['interior']}"
        else:
            count[un["kind"]] = count.get(un["kind"], 0) + 1
            nm = f"{un['kind']}.{count[un['kind']]:02d}"
        un["id"] = prefix + nm
        names.append(nm)
    for un in units:
        for j in un["joins"]:
            if j["unit"] != "ground":
                j["unit"] = units[j["unit"]]["id"]
        un["doors"] = list(un["pieces"].get("door", []))
        un.setdefault("interior", None)
    return sorted(units, key=lambda un: un["id"])


def _centre(un, boxes):
    ids = [i for v in un["pieces"].values() for i in v] if un["pieces"] else []
    if not ids:
        return (0.0, 0.0)
    return (round(float(np.mean([boxes[i][0][0] for i in ids]))), round(float(np.mean([boxes[i][0][1] for i in ids]))))


# ---------- a place ----------
class Place:
    """A drafted place's units: derived on its source, carried to the draft by `src`; measured on the draft as the
    look tool seats and draws it (Scene: the place files with the land patches, seated)."""

    def __init__(self, place_id: str, scene=None):
        from tools.places.draft import io
        from tools.places.look.scene import Scene, data_out
        sc = scene or Scene(place_id)
        src = io.load(f"src.{sc.files['place']['source_id']}", data_out() / "bundles")
        bounds = lambda b: sc.bounds_of(b)  # noqa: E731  the look tool's own extents, so the numbers match its sections
        self.build(place_id, sc, pieces_of(src.exterior.refs, {**src.bases, **sc.bases}, bounds), src.ground)

    @classmethod
    def of(cls, place_id: str, scene, src_pieces: list[dict], src_ground) -> "Place":
        """A place from parts: a scene-like object (pieces, refs, by_id, bases, ground, files) and the source's pieces."""
        pl = cls.__new__(cls)
        pl.build(place_id, scene, src_pieces, src_ground)
        return pl

    def build(self, place_id: str, sc, src_pieces: list[dict], src_ground) -> None:
        self.sc, self.place_id = sc, place_id
        self.src_pieces, self.src_ground = src_pieces, src_ground
        self.src_by = {p["id"]: p for p in self.src_pieces}
        self.src_units = derive(self.src_pieces, src_ground, sc.bases)
        for p in sc.pieces:
            p["src"] = (sc.refs.get(p["id"]) or {}).get("src")
            p["row"] = sc.refs.get(p["id"])
        self.by = sc.by_id
        of_src: dict[str, list[str]] = {}
        for p in sc.pieces:
            if p["src"] in self.src_by:
                of_src.setdefault(p["src"], []).append(p["id"])
        self.units = []
        taken = set()
        for su in self.src_units:
            pcs = {r: [d for s in ids for d in of_src.get(s, [])] for r, ids in su["pieces"].items()}
            pcs = {r: v for r, v in pcs.items() if v}
            if not pcs:
                continue
            taken.update(i for v in pcs.values() for i in v)
            self.units.append(dict(su, pieces=pcs, doors=pcs.get("door", []), src_pieces=su["pieces"]))
        rest = [p for p in sc.pieces if p["id"] not in taken and p["src"] not in self.src_by]
        for un in self.units:   # a Hist the draft added where the source's stood (a swapped tree) is that Hist's trunk
            if un["kind"] == "hist":
                got = _stand_ins(self, un, rest)
                for r, ids in got.items():
                    un["pieces"].setdefault(r, []).extend(ids)
                rest = [p for p in rest if not any(p["id"] in v for v in got.values())]
        for un in derive(rest, sc.ground, sc.bases, prefix="added."):
            self.units.append(dict(un, src_pieces=None))
        self.by_unit = {u["id"]: u for u in self.units}

    def unit(self, name: str) -> dict:
        if name in self.by_unit:
            return self.by_unit[name]
        n = name.lower()
        hits = [u for u in self.units if u["id"].lower().startswith(n)] or \
            [u for u in self.units if u["id"].lower().endswith(n) or n in u["id"].lower()]
        if len(hits) == 1:
            return hits[0]
        raise KeyError(f"no unit {name!r}" + (f"; {len(hits)} match" if hits else "") + "; units: "
                       + " ".join(u["id"] for u in self.units if u["kind"] != "thing"))

    def unit_of_piece(self, pid: str) -> dict | None:
        for u in self.units:
            if any(pid in v for v in u["pieces"].values()):
                return u
        return None


def _stand_ins(pl: Place, un: dict, rest: list[dict]) -> dict:
    """For a source Hist whose trunk the draft does not carry: the draft's added Hist standing where the source's
    stood (the source's spot moved as the unit's carried pieces moved, within HIST_SNAP), and the sap pool on that
    trunk (a WaterPuddleHist within its box). {role: [ids]}."""
    if un["pieces"].get("trunk"):
        trunk = un["pieces"]["trunk"][0]
    else:
        st = [s for s in un["src_pieces"].get("trunk", []) if s in pl.src_by]
        moved = [np.array([pl.by[i]["m"][k][3] - pl.src_by[pl.by[i]["src"]]["m"][k][3] for k in range(2)])
                 for v in un["pieces"].values() for i in v if pl.by.get(i, {}).get("src") in pl.src_by]
        if not st or not moved:
            return {}
        d = np.median(np.array(moved), axis=0)
        sx, sy = pl.src_by[st[0]]["m"][0][3] + d[0], pl.src_by[st[0]]["m"][1][3] + d[1]
        near = sorted((math.hypot(p["m"][0][3] - sx, p["m"][1][3] - sy), p["id"]) for p in rest if hist_trunk(p))
        if not near or near[0][0] > HIST_SNAP:
            return {}
        trunk = near[0][1]
    out = {} if un["pieces"].get("trunk") else {"trunk": [trunk]}
    lo, hi = geom.aabb(pl.by[trunk])
    pools = [p["id"] for p in rest if hist_role(p) == "sap" and lo[0] <= p["m"][0][3] <= hi[0] and lo[1] <= p["m"][1][3] <= hi[1]]
    if pools:
        tx, ty = pl.by[trunk]["m"][0][3], pl.by[trunk]["m"][1][3]
        out["sap"] = [min(pools, key=lambda i: math.hypot(pl.by[i]["m"][0][3] - tx, pl.by[i]["m"][1][3] - ty))]
    return out


def measure_hist(pl: Place, un: dict) -> dict:
    """A Hist's numbers: each root, gland, floor and hanging piece against our ground and against the trunk. A piece
    that rested on the source's ground (its lowest point within GROUND_REST of it) must reach ours, by its lowest
    point; every other piece keeps its height on the trunk as the source has it, within STEP. A sap pool's surface is
    given with the highest ground inside its box."""
    G, roles = pl.sc.ground, un["pieces"]
    trunk = (roles.get("trunk") or [None])[0]
    sg = getattr(pl, "src_ground", None)
    st = [s for s in (un.get("src_pieces") or {}).get("trunk", []) if s in pl.src_by]
    tz = pl.by[trunk]["m"][2][3] if trunk in pl.by else None
    stz = pl.src_by[st[0]]["m"][2][3] if st else None
    out = {"id": un["id"], "kind": "hist", "n": sum(len(v) for v in roles.values()), "stand": _r(tz), "floor": None,
           "deck": None, "flags": [], "steps": [], "doors": [], "parts": []}
    gs, depths = [], []
    for r in ("root", "floor", "gland", "hanging"):
        for i in [i for i in roles.get(r, []) if i in pl.by]:
            p = pl.by[i]
            pts = geom.bottom_points(p, 3)
            lows = [(float(z) - g, g) for x, y, z in pts if (g := G.height(float(x), float(y))) is not None]
            if not lows:
                continue
            over, g = min(lows)
            gs.append(g)
            top = float(geom.aabb(p)[1][2])
            sp = pl.src_by.get(p.get("src"))
            src_over = rel = src_rel = None
            if sp is not None and sg is not None:
                sl = [float(z) - h for x, y, z in geom.bottom_points(sp, 3) if (h := sg.height(float(x), float(y))) is not None]
                src_over = min(sl) if sl else None
            if sp is not None and tz is not None and stz is not None:
                rel, src_rel = p["m"][2][3] - tz, sp["m"][2][3] - stz
            grounded = src_over is not None and src_over <= GROUND_REST and r != "hanging"
            part = {"piece": i, "role": r, "edid": p.get("edid"), "over": _r(over), "src_over": _r(src_over),
                    "on_trunk": _r(None if rel is None else rel - src_rel), "grounded": grounded}
            out["parts"].append(part)
            name = f"{r} {p.get('edid')} ...{i[-8:]}"
            if grounded:
                depths.append(-over)
                if over > STEP:
                    out["flags"].append(f"{name} hangs {over:.0f} over the ground")
                if top < max(h for _, h in lows):
                    out["flags"].append(f"{name} buried whole")
            elif r == "floor" and over is not None and -STEP <= over <= STEP:
                pass                    # a vine floor lying on our ground is seated, wherever the source's mound had it
            elif part["on_trunk"] is not None and abs(part["on_trunk"]) > STEP:
                out["flags"].append(f"{name} off its place on the trunk ({part['on_trunk']:+.0f})")
            elif part["on_trunk"] is None and over > STEP and r in ("root", "floor"):
                out["flags"].append(f"{name} hangs {over:.0f} over the ground")
    for i in roles.get("sap", []):
        p = pl.by.get(i)
        if p is None:
            continue
        lo, hi = geom.aabb(p)
        rim = [g for x in np.linspace(lo[0], hi[0], 7) for y in np.linspace(lo[1], hi[1], 7)
               if (g := G.height(float(x), float(y))) is not None]
        out["sap"] = {"piece": i, "surface": _r(p["m"][2][3]), "rim_max": _r(max(rim)) if rim else None}
    out["gmin"], out["gmax"] = (_r(min(gs)), _r(max(gs))) if gs else (None, None)
    out["min_depth"] = _r(min(depths)) if depths else None
    out["max_depth"] = _r(max(depths)) if depths else None
    out["feet"] = []
    return out


def hist_reassembly(pl: Place, un: dict) -> dict:
    """Per piece of a Hist, the height that seats it (measure_hist's rule): a piece that rested on the source's ground
    sunk until its lowest point is BURY_MIN into ours (a vine floor flush on it), never lifted; every other piece back at its height on the trunk as the source has it. {piece id: dz}."""
    out = {}
    for part in measure_hist(pl, un)["parts"]:
        if part["grounded"] and part["over"] is not None:   # its lowest point sunk into the ground, never lifted
            d = min(0.0, (0.0 if part["role"] == "floor" else -BURY_MIN) - part["over"])
        elif part["on_trunk"] is not None:
            d = -part["on_trunk"]
        else:
            continue
        if abs(d) > 0.5:
            out[part["piece"]] = round(d, 1)
    return out


def _rel_src(pl: Place, un: dict, did: str) -> str | None:
    p = pl.by.get(did)
    return p and p.get("src")


def measure(pl: Place, un: dict, dz: dict | None = None, shift=(0.0, 0.0)) -> dict:
    """One unit's numbers on our ground. dz: piece id -> extra height (a plan's reassembly and offset); shift: a
    plan move (dx, dy) of the whole unit."""
    if un["kind"] == "hist" and not dz and shift == (0.0, 0.0):
        return measure_hist(pl, un)
    sc, dz = pl.sc, dz or {}
    G = sc.ground
    roles = un["pieces"]
    P = {i: pl.by[i] for v in roles.values() for i in v if i in pl.by}

    def box(i):
        lo, hi = geom.aabb(P[i])
        d = np.array([shift[0], shift[1], dz.get(i, 0.0)])
        return lo + d, hi + d

    def gh(x, y):
        return G.height(x + shift[0], y + shift[1])
    body = [i for i in roles.get("body", []) if i in P]
    decks = [i for i in roles.get("deck", []) if i in P]
    house = un["kind"] == "house"
    tops = {i: deck_top(P[i], sc.bases) + dz.get(i, 0.0) for i in decks}
    floor = min(float(box(b)[0][2]) for b in body) if body and house else None
    sills = [float(box(i)[0][2]) for i in un.get("doors", []) if i in P]
    if house and not decks and sills:   # a house on the ground: its floor is where its doors stand
        floor = min(sills)
    deck = None
    if decks:
        if body and house:   # the deck a body stands on: the one under most of it
            own = own_deck([box(b) for b in body], {i: box(i) for i in decks})
            deck = tops[own]
        else:
            deck = max(tops.values())
    stand = floor if floor is not None else (deck if deck is not None else (float(box(body[0])[0][2]) if body else None))
    # footprint: the body and decks (a walkway: its decks)
    fp_ids = (body + decks) or list(P)
    fp_pts = []
    for i in fp_ids:   # the meshes' own footprint cells (every second one: the ground's grid is 128)
        fp_pts += [(float(x), float(y)) for x, y, _ in shape.posed(P[i]).cells("under")[::2]]
    gs = [g for g in (G.height(x + shift[0], y + shift[1]) for x, y in fp_pts) if g is not None]
    water = [w for w in (G.water(x + shift[0], y + shift[1]) for x, y in fp_pts[:: max(1, len(fp_pts) // 8)]) if w is not None]
    gmin, gmax = (min(gs), max(gs)) if gs else (None, None)
    out = {"id": un["id"], "kind": un["kind"], "n": sum(len(v) for v in roles.values()), "stand": _r(stand),
           "floor": _r(floor), "deck": _r(deck), "gmin": _r(gmin), "gmax": _r(gmax),
           "water": _r(max(water)) if water else None, "flags": []}
    # source numbers: the leg of each foot, the body's gap to its deck, each sill against the floor
    src_rel = _source_rel(pl, un)
    # feet: posts, else the decks' bottoms, else the body's; steps' feet separately
    feet = []
    # the pieces that reach the ground: posts and decks standing on legs; a body only when nothing else stands under it
    legged = [i for i in decks if float(box(i)[1][2] - box(i)[0][2]) >= 150]
    foot_ids = [i for i in roles.get("posts", []) if i in P] + legged
    if not foot_ids and un["kind"] not in ("walkway", "bridge"):
        foot_ids = body or [i for i in roles.get("on", []) if i in P][:1]
    for i in foot_ids:
        S = shape.posed(P[i])   # the mesh's feet: where it comes lowest (posts, legs, a body's bottom), not box corners
        pts = [(f["at"][0], f["at"][1], f["z"]) for f in S.feet() if f["z"] <= S.low() + FOOT_BAND][:8]
        for x, y, z in pts:
            z = float(z) + dz.get(i, 0.0)
            g = gh(float(x), float(y))
            leg = src_rel["leg"].get(i)
            if leg is None:
                leg = (max(GROUND_LEG, stand - z) if stand is not None else GROUND_LEG) if (i in body and not decks) \
                    else (stand - z if stand is not None else 0.0)
            feet.append({"piece": i, "at": [_r(x + shift[0]), _r(y + shift[1])], "z": _r(z), "ground": _r(g),
                         "depth": _r(g - z) if g is not None else None, "leg": _r(max(leg, GROUND_LEG if i in body and not decks else 0.0)),
                         # a body's own bottom with no foundation under its floor: it sits on the ground, flush
                         "flush": i in body and stand is not None and stand - z < BURY_MIN})
    out["feet"] = feet
    steps = []
    for i in [i for i in roles.get("steps", []) if i in P]:
        ends = geom.end_points(P[i])   # the mesh's foot line, at its underside
        e = min(ends, key=lambda q: q[2]) if len(ends) else geom.bottom_points(P[i])[0]
        lo, hi = box(i)
        z = float(e[2]) + dz.get(i, 0.0)
        g = gh(float(e[0]), float(e[1]))
        steps.append({"piece": i, "foot": _r(z), "ground": _r(g), "over": _r(z - g) if g is not None else None,
                      "height": _r(float(hi[2] - lo[2]))})
    out["steps"] = steps
    # body against its own deck
    gap = None
    if body and house and decks and deck is not None:
        gap = floor - deck
        out["body_gap"] = _r(gap)
        sg = src_rel.get("gap")
        out["body_gap_src"] = _r(sg)
        if sg is not None and abs(gap - sg) > GAP_TOL:
            out["flags"].append(f"body through its deck ({gap - sg:+.0f})" if gap < sg else f"body off its deck ({gap - sg:+.0f})")
    # doors
    drs = []
    for i in [i for i in un.get("doors", []) if i in P]:
        lo, hi = box(i)
        sill = float(lo[2])
        gb = _ground_before(P[i], G, sill, shift)
        d = {"piece": i, "sill": _r(sill), "on_floor": _r(sill - stand) if stand is not None else None,
             "src_on_floor": _r(src_rel["sill"].get(i)), "ground_before": gb}
        if d["on_floor"] is not None and d["src_on_floor"] is not None and abs(d["on_floor"] - d["src_on_floor"]) > SILL_TOL:
            out["flags"].append(f"door sill off its floor ({d['on_floor'] - d['src_on_floor']:+.0f})")
        if gb is not None and sill < gb - SILL_TOL and not (deck is not None and deck > gb):
            out["flags"].append(f"door sill under ground ({sill - gb:+.0f})")
        drs.append(d)
    out["doors"] = drs
    # flags of standing and feet
    if stand is not None and gmax is not None and stand < gmax and un["kind"] in ("house", "dock"):
        out["flags"].append(f"floor under the ground ({stand - gmax:+.0f})")
    for f in feet:
        if f["depth"] is None:
            continue
        if f["depth"] < (-STEP if f.get("flush") else 0) and un["kind"] not in ("walkway", "bridge"):
            out["flags"].append(f"foot not reaching the ground ({-f['depth']:.0f} over)")
            break
    for f in feet:
        if f["depth"] is not None and f["depth"] > f["leg"] + GAP_TOL:
            out["flags"].append(f"foot buried deeper than its leg ({f['depth']:.0f} > {f['leg']:.0f})")
            break
    if deck is not None and gmax is not None and deck - (gmin if gmin is not None else gmax) > HIGH_DECK and not steps \
            and un["kind"] == "house" and not any(j for u2 in pl.units for j in u2.get("joins", []) if j.get("unit") == un["id"]):
        out["flags"].append(f"deck {deck - gmin:.0f} over the ground with no steps")
    for s in steps:
        if s["over"] is not None and s["over"] > geom.END_TOL:
            out["flags"].append(f"steps not reaching the ground ({s['over']:.0f} over)")
            break
    out["max_depth"] = _r(max((f["depth"] for f in feet if f["depth"] is not None), default=None))
    out["min_depth"] = _r(min((f["depth"] for f in feet if f["depth"] is not None), default=None))
    return out


def _ground_before(p: dict, G, sill: float, shift=(0.0, 0.0)) -> float | None:
    """The ground where one comes out of a door: at its arrival point, else 100 units out on the side nearer the sill."""
    arr = (p.get("door") or {}).get("arrival")
    pts = [arr[:2]] if arr else [[float(v) for v in (np.asarray(p["m"], float) @ np.array([0, s, p["lo"][2], 1.0]))[:2]]
                                 for s in (-100.0, 100.0)]
    gs = [g for g in (G.height(x + shift[0], y + shift[1]) for x, y in pts) if g is not None]
    return _r(min(gs, key=lambda g: abs(g - sill))) if gs else None


def own_deck(body_boxes: list, deck_boxes: dict) -> str:
    """Of a house's decks, the one under most of its body in plan."""
    def over(a, b):
        return max(0.0, min(a[1][0], b[1][0]) - max(a[0][0], b[0][0])) * max(0.0, min(a[1][1], b[1][1]) - max(a[0][1], b[0][1]))
    return max(sorted(deck_boxes), key=lambda d: sum(over(bb, deck_boxes[d]) for bb in body_boxes))


def _r(v):
    return None if v is None else round(float(v), 1)


def _source_rel(pl: Place, un: dict) -> dict:
    """The unit's relative numbers in the source, keyed by the draft's piece ids: each foot's leg below the standing
    level, the body's gap to its deck, each door's sill against the floor."""
    key = ("_src_rel", un["id"])
    if key in pl.__dict__:
        return pl.__dict__[key]
    rel = {"leg": {}, "sill": {}, "gap": None, "stand": None}
    if un.get("src_pieces"):
        s_of = {i: pl.by[i]["src"] for v in un["pieces"].values() for i in v if i in pl.by}
        S = pl.src_by
        body = [s for s in un["src_pieces"].get("body", []) if s in S]
        decks = [s for s in un["src_pieces"].get("deck", []) if s in S]
        tops = [deck_top(S[s], pl.sc.bases) for s in decks]
        floor = min(float(geom.aabb(S[b])[0][2]) for b in body) if body and un["kind"] == "house" else None
        sills = [float(geom.aabb(S[s])[0][2]) for s in un["src_pieces"].get("door", []) if s in S]
        if floor is not None and not decks and sills:
            floor = min(sills)
        deck = None
        if tops and floor is not None:   # the same deck piece the draft's body stands on
            own = own_deck([geom.aabb(S[b]) for b in body], {d: geom.aabb(S[d]) for d in decks})
            deck = deck_top(S[own], pl.sc.bases)
        elif tops:
            deck = max(tops)
        stand = floor if floor is not None else deck
        rel["stand"] = stand
        if floor is not None and deck is not None:
            rel["gap"] = floor - deck
        for i, s in s_of.items():
            if s not in S or stand is None:
                continue
            rel["leg"][i] = stand - float(geom.aabb(S[s])[0][2])
            if S[s].get("kind") == "door":
                rel["sill"][i] = float(geom.aabb(S[s])[0][2]) - stand
    pl.__dict__[key] = rel
    return rel


def mismatched(rel: float | None, rs: float | None) -> bool:
    """A join's end is mismatched when it stands more than a step off the source's: a difference of a step itself
    (to float noise, a bridge one plank step off) is within a step."""
    return rel is not None and rs is not None and abs(rel - rs) > STEP + 0.5


def joins(pl: Place) -> list[dict]:
    """Every join of a walkway or dock with what it rests on: {walk, unit, piece, with, rel, rel_src, flag}. rel: the
    walkway piece's top over the unit's standing level now; rel_src: the same in the source."""
    out = []
    given = {(g["walk"], g["unit"]): g.get("why", "") for g in given_up(pl)}
    for un in pl.units:
        for j in un.get("joins", []):
            if j["unit"] == "ground":
                continue
            ws = [i for i in un["pieces"].get("deck", []) + un["pieces"].get("steps", []) if pl.by.get(i, {}).get("src") == j["piece"]] \
                if un.get("src_pieces") else ([j["piece"]] if j["piece"] in pl.by else [])
            tgt = pl.by_unit.get(j["unit"])
            if not ws or not tgt:
                continue
            m = measure(pl, tgt)
            top = deck_top(pl.by[ws[0]], pl.sc.bases)
            rel = None if m["stand"] is None else top - m["stand"]
            rs = None
            if un.get("src_pieces") and j["piece"] in pl.src_by:
                srel = _source_rel(pl, tgt)["stand"]
                if srel is not None:
                    rs = deck_top(pl.src_by[j["piece"]], pl.sc.bases) - srel
            flag = None
            if mismatched(rel, rs):
                flag = f"walkway end mismatched ({rel - rs:+.0f})"
            gone = given.get((un["id"], tgt["id"]), given.get((tgt["id"], un["id"])))
            if gone is not None:
                flag = None
            out.append({"walk": un["id"], "unit": tgt["id"], "piece": ws[0], "rel": _r(rel), "rel_src": _r(rs), "flag": flag,
                        **({"given_up": gone} if gone is not None else {})})
    return out


def given_up(pl: Place) -> list[dict]:
    """The joins the drafter gave up for a flight where two levels cannot agree (`draft.joins_given_up` of place.json:
    [{walk, unit, why}], either order): measured as ever, never flagged as a mismatched end."""
    files = getattr(pl.sc, "files", None) or {}
    return list(((files.get("place") or {}).get("draft") or {}).get("joins_given_up") or [])


def accepted(pl: Place) -> list[dict]:
    """The flags the drafter accepted because they copy the source's own arrangement (`draft.accepted` of place.json:
    [{unit, flag, why}]; `flag` is a prefix of the measured flag): shown as "accepted: why", never as a fault."""
    files = getattr(pl.sc, "files", None) or {}
    return list(((files.get("place") or {}).get("draft") or {}).get("accepted") or [])


def apply_accepted(unit_id: str, flags: list[str], acc: list[dict]) -> tuple[list[str], list[str]]:
    """Split a unit's flags into (faults, accepted notes) by the `draft.accepted` rows."""
    faults, notes = [], []
    for f in flags:
        a = next((a for a in acc if a.get("unit") == unit_id and f.startswith(a.get("flag", "\0"))), None)
        if a is None:
            faults.append(f)
        else:
            notes.append(f"accepted: {a.get('why', '')} ({f})")
    return faults, notes


def table(pl: Place, everything: bool = False) -> tuple[list[dict], str]:
    rows, js, acc = [], joins(pl), accepted(pl)
    for un in pl.units:
        if un["kind"] == "thing" and not everything:
            continue
        m = measure(pl, un)
        for j in js:
            if j["walk"] == un["id"] and j["flag"]:
                m["flags"].append(f"{j['flag']} at {j['unit']}")
        for j in un.get("joins", []):
            if j["unit"] == "ground":
                pass
        if un["kind"] in ("walkway", "bridge") and not un.get("joins"):
            m["flags"].append("walkway end unsupported (rests on nothing named)")
        m["flags"], m["accepted"] = apply_accepted(un["id"], m["flags"], acc)
        m["joins"] = [j["unit"] for j in un.get("joins", [])]
        m["roles"] = {r: len(v) for r, v in un["pieces"].items()}
        rows.append(m)
    lines = [f"units of {pl.place_id}: {len(rows)} shown ({sum(1 for r in rows if r['kind'] == 'house')} houses); "
             "heights in units (70 = 1 m); depth = how far a foot is in the ground (negative: over it)",
             f"{'unit':34} {'kind':7} {'n':>3} {'stand':>7} {'gmin':>7} {'gmax':>7} {'flr-gmax':>8} {'gap/src':>11} {'feet depth':>13} roles; joins; flags"]
    for m in rows:
        fg = None if m["stand"] is None or m["gmax"] is None else m["stand"] - m["gmax"]
        gp = "" if m.get("body_gap") is None else f"{m['body_gap']:.0f}/{m['body_gap_src'] if m['body_gap_src'] is None else round(m['body_gap_src'])}"
        fd = "" if m["min_depth"] is None else f"{m['min_depth']:.0f}..{m['max_depth']:.0f}"
        roles = ",".join(f"{k}{v}" for k, v in sorted(m["roles"].items()))
        lines.append(f"{m['id'][:34]:34} {m['kind']:7} {m['n']:>3} {_f(m['stand']):>7} {_f(m['gmin']):>7} {_f(m['gmax']):>7} "
                     f"{_f(fg):>8} {gp:>11} {fd:>13} {roles}; {' '.join(m['joins']) or '-'}; {'; '.join(m['flags'] + m['accepted']) or 'ok'}")
    return rows, "\n".join(lines)


def _f(v):
    return "-" if v is None else f"{v:.0f}"


# ---------- the plan ----------
def reassembly(pl: Place, un: dict) -> dict:
    """Per piece, the height that puts it back where it stands in the source relative to the unit's reference piece
    (its deck, else its body): {piece id: dz}. Empty for a unit with no source."""
    if not un.get("src_pieces"):
        return {}
    # the unit's own height change: the middle of its built pieces' changes (a piece pushed apart is the odd one out)
    core = [i for r in ("deck", "body", "posts") for i in un["pieces"].get(r, []) if i in pl.by and pl.by[i]["src"] in pl.src_by]
    if not core:
        return {}
    def moved(i):
        return pl.by[i]["m"][2][3] - pl.src_by[pl.by[i]["src"]]["m"][2][3]
    body = [i for i in core if i in un["pieces"].get("body", [])]
    decks = [i for i in core if i in un["pieces"].get("deck", [])]
    if body and decks and un["kind"] == "house":   # a house keeps where its own deck stands; its body goes back onto it
        own = own_deck([geom.aabb(pl.by[b]) for b in body], {d: geom.aabb(pl.by[d]) for d in decks})
        shift = float(moved(own))
    else:
        shift = float(np.median([moved(i) for i in core]))
    out = {}
    sg, G = getattr(pl, "src_ground", None), pl.sc.ground
    tops = [float(geom.aabb(pl.src_by[pl.by[i]["src"]])[1][2]) for i in un["pieces"].get("deck", [])
            if i in pl.by and pl.by[i]["src"] in pl.src_by]
    src_stand = max(tops) if tops else None
    lying: dict[str, float] = {}     # what lay on the source's ground: {id: how far its underside was over it}
    for r, v in un["pieces"].items():
        for i in v:
            p = pl.by.get(i)
            if p and p["src"] in pl.src_by and r in ("on", "hanging", "railing", "door"):
                over = _on_src_ground(pl.src_by[p["src"]], sg, src_stand if r in ("on", "door") else None)
                if over is not None:
                    lying[i] = over
    # a group under the deck (a fire pit with its firewood and smoke) keeps its own heights, its lowest on the ground
    up = [o for o in lying.values() if o > GROUND_REST]
    drop = min(up) if up else 0.0
    for r, v in un["pieces"].items():
        for i in v:
            p = pl.by.get(i)
            if not p or p["src"] not in pl.src_by:
                continue
            want = pl.src_by[p["src"]]["m"][2][3] + shift
            if i in lying:   # it lay on the source's ground by or under the house (a net, a fire pit): it lies on ours
                lo, hi = geom.aabb(p)
                g = G.height(float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2)
                if g is not None:
                    over = lying[i] - drop if lying[i] > GROUND_REST else lying[i]
                    want = p["m"][2][3] + (g + over - float(lo[2]))
            d = want - p["m"][2][3]
            if abs(d) > 0.5:
                out[i] = round(d, 1)
    return out


GROUND_REST = 64.0     # a piece of a unit whose underside was this close to the source's ground rested on the ground


def _on_src_ground(sp: dict, sg, stand: float | None = None) -> float | None:
    """How far over the source's ground a piece's underside was, when it belonged to that ground: it rested on it, or
    it stood wholly under the unit's standing level (a fire pit and its smoke under a stilt house, a door into the
    space under the deck); else None."""
    if sg is None:
        return None
    lo, hi = geom.aabb(sp)
    g = sg.height(float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2)
    if g is None:
        return None
    over = float(lo[2]) - g
    under = stand is not None and float(hi[2]) < stand - STEP * 3 and over < stand - g - STEP * 3
    return over if -GROUND_REST <= over <= GROUND_REST or under else None


def interval(m: dict, un: dict, margin: float, steps: bool = True) -> tuple[float, float, list[str]]:
    """The offsets a unit may take on the ground under it: (lo, hi, what binds)."""
    lo, hi, why = -math.inf, math.inf, []
    small = un["kind"] in ("small", "boat", "thing")
    if m["stand"] is not None and m["gmax"] is not None and un["kind"] in ("house", "dock"):
        need = margin
        if un["kind"] == "house" and m["deck"] is not None and m["gmin"] is not None and m["deck"] - m["gmin"] > 120:
            need = max(margin, DECK_MARGIN)   # a stilt house stays on stilts
        if un["kind"] == "house" and (m["deck"] is None or all(f.get("flush") for f in m["feet"])):
            need = 0.0   # a house on the ground: its floor meets the highest ground, its walls go into the lower
        v = m["gmax"] + need - m["stand"]
        if v > lo:
            lo, why = v, why + [f"floor {need:.0f} over the highest ground"]
    for f in m["feet"]:
        if f["ground"] is None or un["kind"] in ("walkway", "bridge", "boat"):
            continue
        if small:   # a rack, a cart, a stall: on the ground, sunk no more than a hand
            hi = min(hi, f["ground"] - f["z"])
            lo = max(lo, f["ground"] - SMALL_SINK - f["z"])
            continue
        h = f["ground"] + (STEP if f.get("flush") else -BURY_MIN) - f["z"]
        if h < hi:
            hi = h
        l_ = f["ground"] - f["leg"] - f["z"]
        if l_ > lo:
            lo = l_
    if un["kind"] in ("walkway", "bridge") and m["gmax"] is not None and m["stand"] is not None:
        lo = max(lo, m["gmax"] - m["stand"])
    if steps:
        for s in m["steps"]:
            if s["ground"] is None:
                continue
            hi = min(hi, s["ground"] + 8 - s["foot"])
            lo = max(lo, s["ground"] - max(s["height"] - 64.0, 0.0) - s["foot"])   # its top tread stays over the ground
    return lo, hi, why


SCAN = 2000.0          # how far from where it stands the plan looks for a spot a unit fits


def plan(pl: Place, margin: float = MARGIN, scan: float = SCAN, grid: float = 128.0) -> dict:
    """One offset per unit (or a spot, or the joins given up), solved over the join graph for the least total
    movement once each unit is put back together as its source has it."""
    from scipy.optimize import linprog
    units = [u for u in pl.units if u["kind"] != "thing"]
    res: dict[str, dict] = {}
    for un in units:
        ra = reassembly(pl, un)
        m = measure(pl, un, ra)
        lo, hi, why = interval(m, un, margin)
        steps_off = False
        if lo > hi + 0.5 and m["steps"]:
            lo2, hi2, _ = interval(m, un, margin, steps=False)
            if lo2 <= hi2 + 0.5:
                lo, hi, steps_off = lo2, hi2, True
        res[un["id"]] = {"unit": un["id"], "kind": un["kind"], "reassemble": ra, "lo": lo, "hi": hi,
                         "before": measure(pl, un)["flags"],
                         "relief": _r((m["gmax"] or 0) - (m["gmin"] or 0)) if m["gmax"] is not None else None,
                         "steps_relay": steps_off, "m": m, "why": why}
    # a unit no offset seats: a spot nearby where it does
    boxes = {u["id"]: _plan_box(pl, u) for u in units}
    for un in units:
        r = res[un["id"]]
        if r["lo"] <= r["hi"] + 0.5:
            continue
        r["fits"] = False
        blocked: dict = {}
        r["closest"] = {"dz": round((r["lo"] + r["hi"]) / 2, 1), "short": round(r["lo"] - r["hi"], 1)}
        spot = _scan(pl, un, r["reassemble"], margin, boxes, scan, grid, blocked)
        if blocked:
            r["blocked"] = {"spots": blocked["count"], "by": sorted(blocked["by"])}
        if spot:
            r["move"] = spot
            r["lo"], r["hi"] = spot["lo"], spot["hi"]
    # the solve: least |dz| over the units, every join within a step if it can be, else given up
    ids = [u["id"] for u in units if res[u["id"]]["lo"] <= res[u["id"]]["hi"] + 0.5]
    ix = {u: k for k, u in enumerate(ids)}
    J = []
    for j in joins(pl):
        if j["walk"] in ix and j["unit"] in ix and j["rel_src"] is not None and j["rel"] is not None \
                and not res[j["walk"]].get("move") and not res[j["unit"]].get("move"):
            ra_w = res[j["walk"]]["reassemble"].get(j["piece"], 0.0)
            c = j["rel_src"] - (j["rel"] + ra_w - (res[j["unit"]]["m"]["stand"] - measure(pl, pl.by_unit[j["unit"]])["stand"]))
            J.append((ix[j["walk"]], ix[j["unit"]], c, j))
    n, k = len(ids), len(J)
    if n:
        nv = 2 * n + k
        cost = np.concatenate([np.zeros(n), np.ones(n), np.full(k, 100.0)])
        A, b = [], []
        for i in range(n):
            row = np.zeros(nv)
            row[i], row[n + i] = 1, -1
            A.append(row), b.append(0)
            row = np.zeros(nv)
            row[i], row[n + i] = -1, -1
            A.append(row), b.append(0)
        for q, (w, u, c, _) in enumerate(J):
            row = np.zeros(nv)
            row[w], row[u], row[2 * n + q] = 1, -1, -1
            A.append(row), b.append(c + STEP)
            row = np.zeros(nv)
            row[w], row[u], row[2 * n + q] = -1, 1, -1
            A.append(row), b.append(-(c - STEP))
        bounds = [(max(res[u]["lo"], -5000), min(res[u]["hi"], 5000) if res[u]["hi"] >= res[u]["lo"] else res[u]["lo"]) for u in ids] \
            + [(0, None)] * (n + k)
        sol = linprog(cost, A_ub=np.array(A), b_ub=np.array(b), bounds=bounds, method="highs")
        x = sol.x if sol.success else np.zeros(nv)
        for u in ids:
            res[u]["dz"] = round(float(x[ix[u]]), 1)
        for q, (w, u, c, j) in enumerate(J):
            if x[2 * n + q] > 0.5:
                res[ids[w]].setdefault("give_up", []).append({"join": j["unit"], "miss": round(float(x[2 * n + q]), 1)})
    # residual flags after the plan
    for un in units:
        r = res[un["id"]]
        if "dz" not in r:
            r["give_up"] = [{"join": j} for j in _joined(pl, un)]
            continue
        mv = r.get("move") or {}
        extra = {i: r["reassemble"].get(i, 0.0) + r["dz"] for v in un["pieces"].values() for i in v}
        after = measure(pl, un, extra, (mv.get("dx", 0.0), mv.get("dy", 0.0)))
        r["after"] = after["flags"]
        r["stand_after"] = after["stand"]
    return {"place": pl.place_id, "margin": margin, "units": [_plain_plan(res[u["id"]]) for u in units]}


def _plain_plan(r: dict) -> dict:
    out = {k: r[k] for k in ("unit", "kind", "relief") if k in r}
    out["dz"] = r.get("dz")
    out["reassemble"] = {k: v for k, v in r["reassemble"].items() if abs(v) > GAP_TOL}
    for k in ("move", "give_up", "steps_relay", "after", "stand_after", "fits", "why", "closest", "blocked"):
        if r.get(k) not in (None, False, [], {}):
            out[k] = r[k]
    out["window"] = [_r(r["lo"]) if math.isfinite(r["lo"]) else None, _r(r["hi"]) if math.isfinite(r["hi"]) else None]
    out["before"] = r["before"]
    return out


def _plan_box(pl, un):
    ids = [i for r in ("body", "deck") for i in un["pieces"].get(r, []) if i in pl.by] or \
        [i for v in un["pieces"].values() for i in v if i in pl.by]
    bs = [geom.aabb(pl.by[i]) for i in ids]
    return [min(b[0][0] for b in bs), min(b[0][1] for b in bs), max(b[1][0] for b in bs), max(b[1][1] for b in bs)]


def _joined(pl, un) -> list[str]:
    """The units joined to this one, either way."""
    got = [j["unit"] for j in un.get("joins", []) if j["unit"] != "ground"]
    got += [u2["id"] for u2 in pl.units for j in u2.get("joins", []) if j.get("unit") == un["id"]]
    return sorted(set(got))


def _scan(pl, un, ra, margin, boxes, radius, grid, blocked: dict | None = None) -> dict | None:
    """The nearest spot within the place where one offset seats the unit, clear of every other unit's plan box.
    `blocked` collects the spots where it would fit but another unit stands: {count, by}."""
    bx = boxes[un["id"]]
    allb = list(boxes.values())
    lo_x, lo_y = min(b[0] for b in allb), min(b[1] for b in allb)
    hi_x, hi_y = max(b[2] for b in allb), max(b[3] for b in allb)
    cand = sorted(((dx, dy) for dx in np.arange(-radius, radius + 1, grid) for dy in np.arange(-radius, radius + 1, grid)
                   if 0 < math.hypot(dx, dy) <= radius), key=lambda d: math.hypot(*d))
    for dx, dy in cand:
        nb = [bx[0] + dx, bx[1] + dy, bx[2] + dx, bx[3] + dy]
        if nb[0] < lo_x or nb[1] < lo_y or nb[2] > hi_x or nb[3] > hi_y:
            continue
        m = measure(pl, un, ra, (float(dx), float(dy)))
        lo, hi, _ = interval(m, un, margin)
        if lo > hi + 0.5:
            continue
        hit = [k for k, o in boxes.items() if k != un["id"]
               and not (nb[2] + 64 < o[0] or o[2] + 64 < nb[0] or nb[3] + 64 < o[1] or o[3] + 64 < nb[1])]
        if hit:
            if blocked is not None:
                blocked["count"] = blocked.get("count", 0) + 1
                blocked.setdefault("by", set()).update(hit)
            continue
        return {"dx": float(dx), "dy": float(dy), "lo": lo, "hi": hi, "joins_lost": _joined(pl, un)}
    return None


def plan_text(p: dict) -> str:
    L = [f"layout plan for {p['place']} (floor margin {p['margin']:.0f}; a stilt deck {DECK_MARGIN:.0f} over its highest ground; "
         f"feet {BURY_MIN:.0f} in the ground, never deeper than their leg; joins within {STEP:.0f}).",
         "Each piece of a unit moves by its own `reassemble` (back to the source's level within its unit; the plan file lists"
         " them) plus the unit's dz; a MOVE shifts the whole unit in plan. `before` and `after` are the unit's flags.", ""]
    bad = []
    for u in p["units"]:
        head = f"{u['unit']:34} {u['kind']:7}"
        if u.get("dz") is None and not u.get("move"):
            bl = u.get("blocked")
            L.append(f"{head} CANNOT SEAT where it stands: the ground under it rises {u.get('relief')} and no one offset keeps "
                     f"its floor up and its feet down (short by {u['closest']['short']:.0f}; the nearest is dz "
                     f"{u['closest']['dz']:+.0f}, leaving that much unmet); "
                     + (f"it fits at {bl['spots']} spot(s) within {SCAN:.0f} but each is taken by {', '.join(bl['by'][:6])}; "
                        if bl else f"no spot within {SCAN:.0f} fits it; ")
                     + f"before: {'; '.join(u['before']) or 'ok'}; joins it would give up if moved: "
                     f"{', '.join(g['join'] for g in u.get('give_up', [])) or 'none'}")
            bad.append(u["unit"])
            continue
        s = f"{head} dz {u['dz']:+.0f}"
        if u.get("move"):
            mv = u["move"]
            s += f" MOVE {mv['dx']:+.0f},{mv['dy']:+.0f} (does not fit where it stands: relief {u.get('relief')}); joins lost {mv['joins_lost'] or 'none'}"
        if u.get("reassemble"):
            s += f"; reassemble {len(u['reassemble'])} piece(s) to the source's levels (largest {max(u['reassemble'].values(), key=abs):+.0f})"
        if u.get("steps_relay"):
            s += "; its steps cannot reach the ground at any offset: re-lay them (look steps)"
        if u.get("give_up"):
            s += f"; gives up join(s) {[(g['join'], g.get('miss')) for g in u['give_up']]}"
        s += f"; before: {'; '.join(u['before']) or 'ok'}; after: {'; '.join(u.get('after') or []) or 'ok'}"
        if u.get("after"):
            bad.append(u["unit"])
        L.append(s)
    L += ["", f"{len(p['units'])} units; {len(bad)} still flagged after the plan: {' '.join(bad) or 'none'}"]
    return "\n".join(L)


# ---------- the draft check's refusals ----------
def check_faults(place_id: str, places: Path | None = None, pl: Place | None = None) -> list[str]:
    """A house moved apart from its platform (its body's gap to its own deck differs from the source's by more than
    GAP_TOL), and a tree or root moved off its seat on the ground by an edit of a building."""
    bad = []
    if pl is None:
        try:
            pl = Place(place_id)
        except Exception as e:  # noqa: BLE001  no bundle or scene: the units cannot be read here
            return [f"units: cannot read the place's units ({type(e).__name__}: {str(e)[:80]})"]
    for un in pl.units:
        if un["kind"] != "house":
            continue
        m = measure(pl, un)
        if m.get("body_gap") is not None and m.get("body_gap_src") is not None and abs(m["body_gap"] - m["body_gap_src"]) > GAP_TOL:
            bad.append(f"{un['id']}: a house moved apart from its platform (body {m['body_gap']:.0f} over its deck, "
                       f"source {m['body_gap_src']:.0f})")
    bad += edit_faults(pl.sc.files, pl.sc.bases, places)
    return bad


def edit_faults(files: dict, bases: dict, places: Path | None = None) -> list[str]:
    """A tree or root left moved up or down by a stroke of an agent's edit that also moved a building (net of the
    strokes of the ground alone that put it back)."""
    rows = {r["id"]: r for r in files["spaces"]["exterior"]["refs"]}
    bad = []
    for i, dz in sorted(moved_by_buildings(files, bases, places).items()):
        r = rows.get(i) or {}
        b = bases.get(r.get("base")) or {}
        k, ed = r.get("kind") or b.get("kind"), str(b.get("edid") or "").lower()
        if (k == "tree" or "root" in ed) and abs(dz) > BURY_MIN:
            bad.append(f"{i} ({ed or k}) moved {dz:+.0f} off its seat on the ground by an edit of a building: a tree or "
                       f"root is judged against the ground, not moved with a house (units apply puts it back)")
    return bad


def moved_by_buildings(files: dict, bases: dict, places: Path | None = None) -> dict[str, float]:
    """{id: dz} of every tree, fern, rock or root a stroke of an agent's edit moved together with a building, net of
    the strokes of the ground alone that came after."""
    from tools.places.seat import PLACES
    pdir = (places or PLACES) / files["place"]["place_id"] / "agent-edits"
    rows = {r["id"]: r for r in files["spaces"]["exterior"]["refs"]}
    owed: dict[str, float] = {}
    for f in sorted(pdir.glob("*.json")) if pdir.is_dir() else []:
        strokes: dict = {}
        for op in json.loads(f.read_text()).get("ops") or []:
            if op.get("op") == "ref.move" and op.get("space", "exterior") == "exterior":
                strokes.setdefault(op.get("stroke"), []).append(op)
        for group in strokes.values():
            def piece(op):
                r = rows.get(op["id"]) or {}
                b = bases.get(r.get("base")) or {}
                return {"kind": r.get("kind") or b.get("kind"), "edid": b.get("edid"), "model": b.get("model")}
            building = any(piece(op)["kind"] == "building" for op in group)
            for op in group:
                if ground_piece(piece(op)) and (building or op["id"] in owed):
                    owed[op["id"]] = owed.get(op["id"], 0.0) + op["after"]["pos"][2] - op["before"]["pos"][2]
    return {i: dz for i, dz in owed.items() if abs(dz) > 0.5}


# ---------- applying the plan ----------
def apply_strokes(pl: Place, p: dict, names: list[str] | None = None, places: Path | None = None,
                  files: dict | None = None) -> tuple[list, list[str]]:
    """The plan `p` as strokes of ref moves on the place files: one stroke per unit named (default every unit the plan
    seats), each piece moved by its own reassembly plus the unit's dz (and the unit's move in plan), then one stroke
    of the ground alone putting back every tree, fern, rock and root an earlier edit of a building moved. Each moved
    piece's seat is pinned (seat.pin) so the seating stage finds it where it was put. Returns (strokes, report)."""
    from tools.places import edits
    from tools.places.look.verbs import _move_op
    from tools.places.seat import PLACES, pin, seat_z
    files = files or edits.load_place((places or PLACES) / pl.place_id)
    rows = {r["id"]: r for r in files["spaces"]["exterior"]["refs"]}
    seated = pl.sc.refs
    G = pl.sc.ground
    plan_by = {u["unit"]: u for u in p["units"]}
    want = names or [u["unit"] for u in p["units"] if u.get("dz") is not None and not u.get("after")]
    strokes, report = [], []
    for name in want:
        u, un = plan_by.get(name), pl.by_unit.get(name)
        if u is None or un is None:
            raise ValueError(f"{name}: no such unit in the plan of {pl.place_id}")
        if u.get("dz") is None or u.get("after"):
            report.append(f"{name}: not applied: the plan cannot seat it ({'; '.join(u.get('after') or []) or 'no offset'})")
            continue
        mv = u.get("move") or {}
        dx, dy = float(mv.get("dx", 0.0)), float(mv.get("dy", 0.0))
        ids = [i for v in un["pieces"].values() for i in v if i in rows and i in seated]
        new = {}
        for i in ids:
            d = float(u.get("reassemble", {}).get(i, 0.0)) + float(u["dz"])
            s = seated[i]["pos"]
            new[i] = dict(copy.deepcopy(rows[i]), pos=[round(s[0] + dx, 3), round(s[1] + dy, 3), round(s[2] + d, 3)])
        placed = {**seated, **new}
        stroke = []
        for i in ids:
            r = new[i]
            r["seat"] = pin(r, r["pos"][2], G, placed)
            if r.get("seat") is None:
                r.pop("seat", None)
            if math.dist(r["pos"], rows[i]["pos"]) > 0.05 or r.get("seat") != rows[i].get("seat"):
                stroke.append(_move_op(rows[i], {"pos": r["pos"], "rot": r.get("rot") or [0, 0, 0],
                                                 "scale": r.get("scale", 1), "seat": r.get("seat")}))
        if stroke:
            strokes.append(stroke)
        report.append(f"{name}: dz {float(u['dz']):+.0f}, {len(u.get('reassemble') or {})} piece(s) reassembled, "
                      f"{len(stroke)} row(s) written")
    ground = []
    built = {i for un in pl.units for v in un["pieces"].values() for i in v}   # a plant on a deck moves with its deck
    for i, dz in sorted(moved_by_buildings(files, pl.sc.bases, places).items()):
        if i not in rows or i not in seated or i in built:
            continue
        r = copy.deepcopy(rows[i])
        s = r.get("seat") or {}
        if s.get("mode", "free") == "free":
            r["pos"][2] = round(r["pos"][2] - dz, 3)
        else:
            r["seat"] = dict(s, dz=round(float(s.get("dz", 0.0)) - dz, 3))
            r["pos"][2] = seat_z(r, G, seated)
        ground.append(_move_op(rows[i], {"pos": r["pos"], "rot": r.get("rot") or [0, 0, 0], "scale": r.get("scale", 1),
                                          "seat": r.get("seat")}))
        report.append(f"{i}: back to its own seat on the ground ({-dz:+.0f})")
    if ground:
        strokes.append(ground)
    return strokes, report


def apply_cli(place_id: str, names: list[str], why: str | None = None) -> int:
    from tools.places.look.verbs import write_agent_save
    pl = Place(place_id)
    hists = [n for n in names if pl.by_unit.get(n, {}).get("kind") == "hist"]
    if hists:   # a Hist is seated by its own rule (hist_reassembly), never by the houses' offsets
        p = {"units": [{"unit": n, "dz": 0.0, "reassemble": hist_reassembly(pl, pl.by_unit[n])} for n in hists]}
        strokes, report = apply_strokes(pl, p, hists)
        names = [n for n in names if n not in hists]
        if names:
            more, rep = apply_strokes(pl, plan(pl), names)
            strokes, report = strokes + more, report + rep
    else:
        strokes, report = apply_strokes(pl, plan(pl), names or None)
    print("\n".join(report))
    if not strokes:
        print("nothing to write")
        return 0
    got = write_agent_save(place_id, strokes, why or f"units apply: {' '.join(names) or 'every unit the plan seats'}")
    print(f"wrote {got['ops']} op(s) in {got['strokes']} stroke(s): {got['save']}")
    for lf in got["left_for_owner"]:
        print(f"left for the owner: stroke {lf['stroke']} touches {lf['owner_rows']}")
    return 0


# ---------- joints ----------
JOINT_ROLES = ("steps", "walkway", "bridge", "dock")
JOINT_CLASSES = ("steps", "span")


def joint_rows(pl: Place) -> list[dict]:
    """Every walked span's ends and what stands on it, from the meshes (shape.joints): a span is a piece the classifier
    calls steps or span, or a deck piece of a walkway, bridge or dock unit."""
    from tools.places import classify, shape
    unit_of, role_of = {}, {}
    for u in pl.units:
        for r, ids in u["pieces"].items():
            for i in ids:
                unit_of[i], role_of[i] = u["id"], (u["kind"] if r == "deck" else r)
    solid = [p for p in pl.sc.pieces if p.get("model") and geom.solid(p) and not ground_piece(p)]
    spans = [p for p in solid if (classify.kind_of(p) in JOINT_CLASSES or role_of.get(p["id"]) in JOINT_ROLES)
             and not classify.has(p, ("wall",))]
    walls = {p["id"] for p in solid if role_of.get(p["id"]) == "body" or classify.kind_of(p) in ("building body", "wall part")}
    structures = walls | {p["id"] for p in solid if classify.kind_of(p) in ("deck", "steps", "span")}
    posed = [(p["id"], shape.posed(p)) for p in solid]
    by = dict(posed)
    rows = shape.joints([(p["id"], by[p["id"]]) for p in spans], posed, pl.sc.ground, unit_of, walls, structures)
    for r in rows:
        p = pl.by.get(r["span"]) or {}
        r["edid"] = p.get("edid")
    return rows


def joints_text(rows: list[dict]) -> str:
    out = [f"{'span':<34} {'edid':<28} {'end':<5} {'at (x, y, z)':<26} {'over gnd':>8} {'along':>6} {'dz':>6}  verdict"]
    for r in rows:
        at = r.get("at")
        out.append(f"{r['span'][-12:]:<34} {str(r.get('edid'))[:28]:<28} {r['end']:<5} "
                   f"{(', '.join(f'{v:.0f}' for v in at) if at else ''):<26} {_s(r.get('over_ground')):>8} "
                   f"{_s(r.get('along')):>6} {_s(r.get('dz')):>6}  {r['verdict']}")
    kinds: dict[str, int] = {}
    for r in rows:
        k = r["verdict"].split(" ")[0] if not r["verdict"].startswith(("rests", "stands", "spans", "crossed", "buried", "short", "step", "on its"))\
            else " ".join(r["verdict"].split(" ")[:2])
        kinds[k] = kinds.get(k, 0) + 1
    out.append("counts: " + ", ".join(f"{k} {n}" for k, n in sorted(kinds.items(), key=lambda kv: -kv[1])))
    return "\n".join(out)


def _s(v) -> str:
    return "" if v is None else f"{v:.0f}"


# ---------- CLI ----------
def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    opts = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else True) for a in argv if a.startswith("--")}
    if not args:
        print(__doc__.split("\n\n")[0])
        return 2
    if args[0] == "apply":
        return apply_cli(args[1], args[2:], opts.get("--why") if isinstance(opts.get("--why"), str) else None)
    if args[0] == "plan":
        pl = Place(args[1])
        p = plan(pl, float(opts.get("--margin", MARGIN)))
        from tools.places.look.scene import data_out
        out = Path(opts["--out"]) if isinstance(opts.get("--out"), str) else data_out() / "units" / f"{args[1]}.plan.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(p, indent=1, default=float) + "\n")
        print(plan_text(p))
        print(f"plan file: {out}")
        return 0
    pl = Place(args[0])
    if "--joints" in opts:
        rows = joint_rows(pl)
        print(json.dumps(rows, indent=1, default=float) if "--json" in opts else joints_text(rows))
        return 0
    if "--source" in opts:
        for u in pl.src_units:
            if u["kind"] != "thing" or "--all" in opts:
                print(u["id"], u["kind"], {r: len(v) for r, v in u["pieces"].items()}, "joins:", [j["unit"] for j in u["joins"]])
        return 0
    rows, txt = table(pl, "--all" in opts)
    print(json.dumps(rows, indent=1, default=float) if "--json" in opts else txt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
