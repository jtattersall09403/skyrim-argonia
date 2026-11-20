"""No obviously wrong thing stands in a draft (owner, 2026-11-19, #80): a piece whose model did not resolve or a bare
collision box standing where a building should be seen; a piece floating over the ground or water under it with
nothing under it that carries it; a bridge or walkway without support at both ends. `draft check` calls `faults`.

The measure is the piece's own record box, scaled and turned by its yaw (a tilted piece is skipped: its box's
underside is not its lowest point). A piece is carried when another solid's (or a tree's or rock's) box holds a point of
it in plan (widened by CARRY_PAD) and reaches from at least the piece's underside (within FLOAT_TOL) down to below
its top: it rests on that thing, hangs from it or is set into it (a lantern on a wall, a hive in a tree). A disabled piece (parked
under the world by its source) is never seen, so never judged.
"""
from __future__ import annotations

import math
import re

from tools.places.draft import geom

FLOAT_TOL = 32.0      # units: an underside this far over what is under it rests on it
CARRY_PAD = 48.0      # units: a carrier's box widened in plan by this much (a post beside a deck's edge holds it)
TILT = 0.2            # radians of pitch or roll beyond which the record box's underside is not the piece's
SOLID = {"building", "static", "furniture", "container", "door", "activator"}
CARRIERS = SOLID | {"tree", "rock", "clutter"}   # what a piece may rest on, hang from or be set into (a hive in a tree,
# a lantern on its lamp post)
WALKWAY = re.compile(r"bridge|walkway|boardwalk|dock|pier|plank", re.I)
COLLISION_BASES = {"Skyrim.esm:000021"}   # CollisionMarker: a box with no visible model
UNRESOLVED = "has no model that resolves: a stand-in where a thing should be seen"
BOX = "is a bare collision box standing on its own: a stand-in where a building should be seen"
FLOATS = "floats over what is under it"
BRIDGE = "is a bridge or walkway without support at"


def _box(r: dict, bases: dict):
    b = geom.bounds(r, bases)
    if not b:
        return None
    lo, hi = b
    return lo, hi


def _world(r: dict, u: float, v: float) -> tuple[float, float]:
    rz = (r.get("rot") or [0, 0, 0])[2]
    c, s = math.cos(rz), math.sin(rz)
    return r["pos"][0] + u * c + v * s, r["pos"][1] - u * s + v * c


def _local(r: dict, x: float, y: float) -> tuple[float, float]:
    rz = (r.get("rot") or [0, 0, 0])[2]
    c, s = math.cos(rz), math.sin(rz)
    dx, dy = x - r["pos"][0], y - r["pos"][1]
    return dx * c - dy * s, dx * s + dy * c


def _surface(G, x: float, y: float) -> float | None:
    h, w = G.height(x, y), G.water(x, y)
    if h is None:
        return None
    return max(h, w) if w is not None else h


def _seen(r: dict) -> bool:
    return "initially_disabled" not in (r.get("flags") or []) and not r.get("removed")


def faults(refs: list[dict], bases: dict, G) -> list[str]:
    """Every obviously wrong piece of the exterior rows `refs` over the ground `G`, one line each."""
    bad: list[str] = []
    by_id = {r["id"]: r for r in refs}
    solids = []
    for r in refs:
        if not _seen(r):
            continue
        base = bases.get(r.get("base"))
        if r.get("base") in COLLISION_BASES or (r.get("primitive") and not (base or {}).get("model")):
            on = (r.get("seat") or {}).get("on")
            if (r.get("seat") or {}).get("mode") != "on" or on not in by_id:
                bad.append(f"{r['id']} ({r.get('base')}) {BOX}")
            continue
        if r.get("kind") not in CARRIERS:
            continue
        if r.get("kind") in SOLID and (not base or not base.get("model")):
            bad.append(f"{r['id']} ({r.get('base')}, {r.get('kind')}) {UNRESOLVED}")
            continue
        box = _box(r, bases)
        if box:
            solids.append((r, box))

    def carried(r, x, y, under_z, over_z):
        for o, (lo, hi) in solids:
            if o is r:
                continue
            top, bottom = o["pos"][2] + hi[2], o["pos"][2] + lo[2]
            if top < under_z - FLOAT_TOL or bottom > over_z:
                continue
            u, v = _local(o, x, y)
            if lo[0] - CARRY_PAD <= u <= hi[0] + CARRY_PAD and lo[1] - CARRY_PAD <= v <= hi[1] + CARRY_PAD:
                return True
        return False

    for r, (lo, hi) in solids:
        if r.get("kind") not in SOLID:
            continue
        over = r["pos"][2] + hi[2]
        rot = r.get("rot") or [0, 0, 0]
        if abs(math.sin(rot[0])) > math.sin(TILT) or abs(math.sin(rot[1])) > math.sin(TILT):
            continue
        under = r["pos"][2] + lo[2]
        name = (bases.get(r["base"]) or {}).get("edid") or r["base"]
        model = str((bases.get(r["base"]) or {}).get("model") or "")
        if WALKWAY.search(model) or WALKWAY.search(str(name)):
            long_u = (hi[0] - lo[0]) >= (hi[1] - lo[1])
            mid = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
            ends = []
            for k in (0, 1):
                e = ((lo[0], hi[0])[k], mid[1]) if long_u else (mid[0], (lo[1], hi[1])[k])
                ends.append(_world(r, *e))
            loose = []
            for k, (x, y) in enumerate(ends):
                s = _surface(G, x, y)
                if s is not None and s >= under - FLOAT_TOL:
                    continue
                if carried(r, x, y, under, over):
                    continue
                loose.append(k)
            if loose:
                bad.append(f"{r['id']} ({name}) {BRIDGE} {'both ends' if len(loose) == 2 else 'one end'} "
                           f"(underside z {under:.0f})")
            continue
        pts = [_world(r, u, v) for u in (lo[0], (lo[0] + hi[0]) / 2, hi[0]) for v in (lo[1], (lo[1] + hi[1]) / 2, hi[1])]
        surf = [s for s in (_surface(G, x, y) for x, y in pts) if s is not None]
        if not surf or under - max(surf) <= FLOAT_TOL:
            continue
        if any(carried(r, x, y, under, over) for x, y in pts):
            continue
        bad.append(f"{r['id']} ({name}) {FLOATS}: underside {under - max(surf):.0f} over the ground or water "
                   f"with nothing under it")
    return bad
