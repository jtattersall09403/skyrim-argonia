"""Infer each source ref's seat rule by measuring how it sat in the source (never copying a raw height).

In order:
- interiors and things whose source cell had no land: `free`;
- standing on another thing (its origin inside that thing's footprint, its bottom at that thing's top, clear of
  the ground): `on`, dz from the supporter's origin;
- over the source's water: a thing floating at the surface is `water`; a structure reaching down into it
  (piers, stilt houses) is `stilts`; dz from the surface;
- otherwise `ground` when its origin is within GROUND_BAND of the lowest ground under its footprint (dz kept, so
  sunk foundations stay sunk), or `above` (hung, raised) with dz from the ground at its origin.
"""
from __future__ import annotations

import math

from tools.places.draft import geom
from tools.places.seat import Ground, foot_ground, foot_high, reference_z

GROUND_BAND = 96.0
SURFACE_BAND = 48.0
CONTACT = 24.0
SUPPORT_KINDS = {"building", "static", "furniture", "container", "activator", "other"}
NEVER_ON = {"building", "tree", "rock"}
RAISED_KINDS = {"building", "static"}


def find_support(r: dict, near: list[dict], bases: dict, g: Ground) -> dict | None:
    x, y = r["pos"][0], r["pos"][1]
    bot = geom.bottom(r, bases)
    h = g.height(x, y)
    if h is not None and bot < h + CONTACT:
        return None
    best = None
    for s in near:
        if s["id"] == r["id"] or s.get("kind") not in SUPPORT_KINDS or not geom.bounds(s, bases):
            continue
        if not geom.contains_xy(s, bases, x, y):
            continue
        top, sbot = geom.top(s, bases), geom.bottom(s, bases)
        if sbot - CONTACT <= bot <= top + CONTACT and s["pos"][2] < r["pos"][2] + CONTACT:
            # a building's floor is anywhere between its bottom and top; a small thing's top is its surface
            score = abs(bot - top) if s.get("kind") != "building" else 0.5 * CONTACT
            if best is None or (score, -geom.radius(s, bases)) < best[0]:
                best = ((score, -geom.radius(s, bases)), s)
    return best[1] if best else None


def infer(r: dict, near: list[dict], bases: dict, g: Ground | None, interior: bool) -> dict:
    """The seat rule of source ref r (in the source's own frame and ground)."""
    if interior or g is None or not g.has(r["pos"][0], r["pos"][1]):
        return {"mode": "free"}
    x, y, z = r["pos"]
    rz = r.get("rot", [0, 0, 0])[2]
    f = geom.foot(r, bases)
    out: dict = {}
    if f:
        out["foot"] = f
    if r.get("kind") not in NEVER_ON:
        s = find_support(r, near, bases, g)
        if s is not None:
            return {**out, "mode": "on", "on": s["id"], "dz": round(z - s["pos"][2], 2)}
    w, h = g.water(x, y), g.height(x, y)
    if w is not None and h is not None and h < w - 8:
        if abs(z - w) <= SURFACE_BAND and not f:
            return {**out, "mode": "water", "dz": round(z - w, 2)}
        if geom.bottom(r, bases) < w and r.get("kind") in ("building", "static", "other"):
            return {**out, "mode": "stilts", "dz": round(z - reference_z(g, "stilts", x, y, rz, f), 2)}
    gz = foot_ground(g, x, y, rz, f)
    b = geom.bounds(r, bases)
    if f and b and r.get("kind") in RAISED_KINDS:
        top_ground = foot_high(g, x, y, rz, f)
        if top_ground is not None and z + b[0][2] - top_ground > CONTACT:
            # its underside clears the ground everywhere (a raised floor or platform): keep that clearance
            return {**out, "mode": "clear", "dz": round(z - top_ground, 2)}
    if gz is not None and z - gz <= GROUND_BAND:
        return {**out, "mode": "ground", "dz": round(z - gz, 2)}
    return {**out, "mode": "above", "dz": round(z - (h if h is not None else z), 2)}


def carry(rows: list[dict], was: dict[str, float]) -> int:
    """A piece laid free and carried by others (a flight or gangway the streets stage hung on a deck: its seat's
    `carrier`) moves up or down with its first carrier that moved, so a re-seated deck keeps its flight. `was`: each
    row's height before the re-seat. Returns the number of rows moved."""
    by_id = {r["id"]: r for r in rows}
    moved = 0
    for r in rows:
        s = r.get("seat") or {}
        c = s.get("carrier")
        if s.get("mode") != "free" or not c:
            continue
        for cid in (c if isinstance(c, list) else [c]):
            sup = by_id.get(cid)
            if sup is not None and cid in was and abs(sup["pos"][2] - was[cid]) > 1e-3:
                r["pos"][2] = round(r["pos"][2] + sup["pos"][2] - was[cid], 3)
                moved += 1
                break
    return moved


# --- one walked structure, one height ---
LEVEL_MODES = {"ground", "clear", "above"}
LEVEL_STEP = 48.0       # deck heights (or a flight's foot and a deck) this close meet as one walked surface
LEVEL_CONTACT = 16.0    # record boxes this close in plan touch


def _plan_box(r: dict, b) -> tuple[float, float, float, float]:
    x, y = r["pos"][0], r["pos"][1]
    rz = (r.get("rot") or [0, 0, 0])[2]
    c, s = math.cos(rz), math.sin(rz)
    pts = [(x + u * c + v * s, y - u * s + v * c) for u in (b[0][0], b[1][0]) for v in (b[0][1], b[1][1])]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def levels(rows: list[dict], by_src: dict[str, dict], bases: dict, g: Ground) -> int:
    """Seat each floor-plate level that has its own flight as one body. The source's floor plates and flights (by
    their top) that touch in plan and meet in height are one level (a keep's yard and its stairs). Where a level
    holds a flight, its pieces keep their source heights relative to each other, so a flight's top still meets its
    yard and the yard stays level: the level stands by the flight whose own seat rule (its foot on our ground) moves
    the level's pieces least from their own rules at worst, and every other piece of it is seated `on` that flight at
    its source offset. A piece a building or a door stands on (a house's porch) belongs to its building and keeps its
    rule, as do pieces seated on the water or on another thing. Returns the number of rows re-seated."""
    from tools.places.draft.paths import FLIGHT, is_plate
    from tools.places.seat import seat_z
    held = {(x.get("seat") or {}).get("on") for x in rows if x.get("kind") in ("building", "door")}
    mem = []
    for row in rows:
        r = by_src.get(row.get("src"))
        if r is None or row.get("base") != r.get("base") or row.get("primitive") or row["id"] in held:
            continue
        if (row.get("seat") or {}).get("mode") not in LEVEL_MODES:
            continue
        base = bases.get(r.get("base")) or {}
        flight = bool(FLIGHT.search(str(base.get("model") or "")))
        w, b = geom.walk(base), geom.bounds(r, bases)
        if w is None or not b or not (flight or is_plate(base)):
            continue
        mem.append((row, r, r["pos"][2] + w, _plan_box(r, b), flight))
    par = list(range(len(mem)))

    def find(i: int) -> int:
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i, (_, _, di, a, _) in enumerate(mem):
        for j in range(i + 1, len(mem)):
            _, _, dj, o, _ = mem[j]
            if a[0] - LEVEL_CONTACT > o[2] or o[0] - LEVEL_CONTACT > a[2] or a[1] - LEVEL_CONTACT > o[3] \
                    or o[1] - LEVEL_CONTACT > a[3]:
                continue
            if abs(di - dj) <= LEVEL_STEP:
                par[find(i)] = find(j)
    groups: dict[int, list[int]] = {}
    for i in range(len(mem)):
        groups.setdefault(find(i), []).append(i)
    changed = 0
    for members in groups.values():
        flights = [i for i in members if mem[i][4]]
        if len(members) < 2 or not flights:
            continue
        own = {i: seat_z(mem[i][0], g) - mem[i][1]["pos"][2] for i in members}
        root = min(flights, key=lambda f: (max(abs(own[f] - own[i]) for i in members), mem[f][0]["id"]))
        rrow, rsrc = mem[root][0], mem[root][1]
        for i in members:
            if i == root:
                continue
            row, r = mem[i][0], mem[i][1]
            seat = {"foot": row["seat"]["foot"]} if row["seat"].get("foot") else {}
            seat.update({"mode": "on", "on": rrow["id"], "dz": round(r["pos"][2] - rsrc["pos"][2], 2)})
            if seat != row["seat"]:
                row["seat"] = seat
                changed += 1
    return changed
