"""A place's units: each a thing a builder would call one structure, derived from the source's own arrangement.

    python -m tools.places units <place> [--all] [--source] [--json]
    python -m tools.places units plan <place> [--margin 30] [--out plan.json]

A house unit is its building body with the platform or deck it stands on, the posts under them, the steps and
railings at its deck, the doors set in its walls (and the room they lead to) and what rests on, hangs on or is fixed
to it; a walkway, bridge or dock is a unit of its own whose joins name the units it rests on; a boat, a rack, a stall
is a small unit. Trees, rocks, roots and ground cover belong to the ground (a plant standing on a deck excepted).
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

import json
import math
import re
import sys
from pathlib import Path

import numpy as np

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
BODY_WORDS = ("house", "hut", "shack", "tent", "hall", "home", "cabin", "shop", "stall", "tower", "yurt", "longhouse", "inn")
DECK_WORDS = ("platform", "deck", "floor", "dock", "pier", "boardwalk", "scaffold")
SPAN_WORDS = ("walkway", "bridge", "gangway", "plank", "boardwalk", "pier", "dock", "platform")
STEPS_RE = re.compile(r"stair|steps|ramp|ladder")
RAIL_WORDS = ("rail", "fence", "wall", "balust", "banister")
POST_WORDS = ("post", "pillar", "stilt", "pole", "pile", "column", "support")
GROUND_KINDS = {"tree", "rock", "plant", "groundcover", "flora", "grass", "landscape", "water"}
SPANS = ("walkway", "bridge", "dock")
LOOSE = {"light", "marker", "sound", "actor"}


# ---------- pieces ----------
def _words(p: dict) -> str:
    return f"{p.get('edid') or ''} {p.get('model') or ''}".lower()


def ground_piece(p: dict) -> bool:
    """A tree, rock, root, plant or ground cover: it belongs to the ground, never to a building."""
    return p.get("kind") in GROUND_KINDS or "root" in _words(p) or "/landscape/" in _words(p)


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
def _role0(p: dict) -> str:
    w = _words(p)
    if ground_piece(p):
        return "ground"
    if p.get("kind") == "door":
        return "door"
    if p.get("kind") in LOOSE and not p.get("model"):
        return "loose"
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
    unit_of: dict[str, int] = {}
    role: dict[str, str] = {}
    units: list[dict] = []
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
                    if p["id"] not in unit_of and any(x in _words(p) for x in POST_WORDS) and role0[p["id"]] == "thing" \
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
        if p["id"] in unit_of or role0[p["id"]] != "loose":
            continue
        x, y, z = p["m"][0][3], p["m"][1][3], p["m"][2][3]
        for q, u in list(unit_of.items()):
            lo, hi = boxes[q]
            if units[u]["kind"] != "thing" and lo[0] - 32 <= x <= hi[0] + 32 and lo[1] - 32 <= y <= hi[1] + 32 and lo[2] - 32 <= z <= hi[2] + 64:
                add(p["id"], u, "hanging" if p.get("kind") == "light" else "on")
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
        self.build(place_id, sc, pieces_of(src.exterior.refs, sc.bases, bounds), src.ground)

    @classmethod
    def of(cls, place_id: str, scene, src_pieces: list[dict], src_ground) -> "Place":
        """A place from parts: a scene-like object (pieces, refs, by_id, bases, ground, files) and the source's pieces."""
        pl = cls.__new__(cls)
        pl.build(place_id, scene, src_pieces, src_ground)
        return pl

    def build(self, place_id: str, sc, src_pieces: list[dict], src_ground) -> None:
        self.sc, self.place_id = sc, place_id
        self.src_pieces = src_pieces
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


def _rel_src(pl: Place, un: dict, did: str) -> str | None:
    p = pl.by.get(did)
    return p and p.get("src")


def measure(pl: Place, un: dict, dz: dict | None = None, shift=(0.0, 0.0)) -> dict:
    """One unit's numbers on our ground. dz: piece id -> extra height (a plan's reassembly and offset); shift: a
    plan move (dx, dy) of the whole unit."""
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
    for i in fp_ids:
        for x, y, _ in geom.bottom_points(P[i], 4):
            fp_pts.append((x, y))
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
        lo, hi = box(i)
        pts = geom.bottom_points(P[i], 2)
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
        ends = geom.end_points(P[i])
        e = min(ends, key=lambda q: q[2])
        lo, hi = box(i)
        z = float(lo[2])
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


def joins(pl: Place) -> list[dict]:
    """Every join of a walkway or dock with what it rests on: {walk, unit, piece, with, rel, rel_src, flag}. rel: the
    walkway piece's top over the unit's standing level now; rel_src: the same in the source."""
    out = []
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
            if rel is not None and rs is not None and abs(rel - rs) > STEP:
                flag = f"walkway end mismatched ({rel - rs:+.0f})"
            out.append({"walk": un["id"], "unit": tgt["id"], "piece": ws[0], "rel": _r(rel), "rel_src": _r(rs), "flag": flag})
    return out


def table(pl: Place, everything: bool = False) -> tuple[list[dict], str]:
    rows, js = [], joins(pl)
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
                     f"{_f(fg):>8} {gp:>11} {fd:>13} {roles}; {' '.join(m['joins']) or '-'}; {'; '.join(m['flags']) or 'ok'}")
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
    for v in un["pieces"].values():
        for i in v:
            p = pl.by.get(i)
            if not p or p["src"] not in pl.src_by:
                continue
            want = pl.src_by[p["src"]]["m"][2][3] + shift
            d = want - p["m"][2][3]
            if abs(d) > 0.5:
                out[i] = round(d, 1)
    return out


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
    """A tree or root moved up or down in a stroke of an agent's edit that also moved a building."""
    from tools.places.seat import PLACES
    pdir = (places or PLACES) / files["place"]["place_id"] / "agent-edits"
    rows = {r["id"]: r for r in files["spaces"]["exterior"]["refs"]}
    bad = []
    for f in sorted(pdir.glob("*.json")) if pdir.is_dir() else []:
        ops = (json.loads(f.read_text()).get("ops") or [])
        strokes: dict = {}
        for op in ops:
            if op.get("op") == "ref.move" and op.get("space", "exterior") == "exterior":
                strokes.setdefault(op.get("stroke"), []).append(op)
        for s, group in strokes.items():
            def kind(op):
                r = rows.get(op["id"]) or {}
                b = bases.get(r.get("base")) or {}
                return r.get("kind") or b.get("kind"), str(b.get("edid") or "").lower()
            if not any(kind(op)[0] == "building" for op in group):
                continue
            for op in group:
                k, ed = kind(op)
                if k == "tree" or "root" in ed:
                    dz = op["after"]["pos"][2] - op["before"]["pos"][2]
                    if abs(dz) > BURY_MIN:
                        bad.append(f"{op['id']} ({ed or k}) moved {dz:+.0f} off its seat on the ground by an edit of a "
                                   f"building ({f.name} stroke {s}): a tree or root is judged against the ground, not moved with a house")
    return bad


# ---------- CLI ----------
def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    opts = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else True) for a in argv if a.startswith("--")}
    if not args:
        print(__doc__.split("\n\n")[0])
        return 2
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
