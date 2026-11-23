"""A thing its source makes of several models stays one thing: a ship's hull and its masts and rigging, a building's
body and its roof, set by the source at one pose (their origins within COMPANION units and turned alike). Where the
place has both models of such a pair near each other, the second stands where the first puts it, at the source's
offset turned with the first; a piece set apart by hand (an offset turned the wrong way, one piece moved without the
other) is a fault. `draft check` calls `faults` with the place's sources (its own and each copied room's).
"""
from __future__ import annotations

import math

COMPANION = 100.0      # two source pieces this near, turned alike, are one thing in two models
TURN_TOL = 0.01        # radians
NEAR = 400.0           # in the place, the second model this near the first is its companion
TOL = 8.0              # how far the second may stand off where the first puts it
KINDS = {"building", "static"}


def _turn(dx, dy, t):
    c, s = math.cos(t), math.sin(t)
    return dx * c - dy * s, dx * s + dy * c


def _instances(src_refs: list[dict]) -> dict:
    """{(base a, base b): [(a id, b id, (dx, dy, dz, dturn))]} for every two source pieces set together."""
    out: dict = {}
    rows = [r for r in src_refs if r.get("kind") in KINDS and r.get("base")]
    for a in rows:
        for b in rows:
            if a is b or a["base"] == b["base"]:
                continue
            if math.dist(a["pos"][:2], b["pos"][:2]) > COMPANION:
                continue
            ta, tb = (a.get("rot") or [0, 0, 0])[2], (b.get("rot") or [0, 0, 0])[2]
            if abs(math.remainder(ta - tb, math.tau)) > TURN_TOL:
                continue
            # a ref's z turn runs clockwise: its own frame is the world turned by +turn
            dx, dy = _turn(b["pos"][0] - a["pos"][0], b["pos"][1] - a["pos"][1], ta)
            out.setdefault((a["base"], b["base"]), []).append((a["id"], b["id"], (dx, dy, b["pos"][2] - a["pos"][2], tb - ta)))
    return out


def _same(u, v) -> bool:
    return math.dist(u[:3], v[:3]) <= TOL and abs(math.remainder(u[3] - v[3], math.tau)) <= TURN_TOL * 5


def pairs(src_refs: list[dict]) -> dict:
    """{(base a, base b): (dx, dy, dz, dturn) of b in a's own frame} over the source's things made of two models: a
    pair set at one offset wherever the source sets it, and every a of the source with its b. A modular kit (a
    scaffold's legs and decks, stacked at many offsets, or a leg standing alone) is many things, never a pair."""
    out = {}
    counts: dict = {}
    for r in src_refs:
        if r.get("kind") in KINDS and r.get("base"):
            counts[r["base"]] = counts.get(r["base"], 0) + 1
    for (ba, bb), inst in _instances(src_refs).items():
        offs = [o for _, _, o in inst]
        if any(not _same(o, offs[0]) for o in offs) or len({a for a, _, _ in inst}) != counts.get(ba, 0):
            continue
        out[(ba, bb)] = offs[0]
    return out


def partners(src_refs: list[dict]) -> dict:
    """{a's source id: b's source id} for every pair `pairs` keeps: the two models of one thing in the source."""
    keep = pairs(src_refs)
    return {a: b for k, inst in _instances(src_refs).items() if k in keep for a, b, _ in inst}


def faults(refs: list[dict], src_ref_lists: list[list[dict]]) -> list[str]:
    known: dict = {}
    mate: dict = {}
    for rows in src_ref_lists:
        for k, v in pairs(rows).items():
            known.setdefault(k, v)
        mate.update(partners(rows))
    if not known:
        return []
    live = [r for r in refs if not r.get("removed")]
    by_base: dict = {}
    by_src: dict = {}
    for r in live:
        by_base.setdefault(r.get("base"), []).append(r)
        if r.get("src"):
            by_src.setdefault(r["src"], []).append(r)
    bad = []
    for (ba, bb), (dx, dy, dz, dt) in sorted(known.items()):
        for a in by_base.get(ba, []):
            if a.get("src") in mate:    # carried from the source: its own partner, where the place still holds it
                near = [b for b in by_src.get(mate[a["src"]], []) if b.get("base") == bb]
            elif a.get("src"):          # a source piece the source set alone: nothing to keep with it
                continue
            else:                       # placed by hand: the nearest of the second model
                near = [b for b in by_base.get(bb, []) if math.dist(a["pos"][:2], b["pos"][:2]) <= NEAR]
            if not near:
                continue
            ta = (a.get("rot") or [0, 0, 0])[2]
            wx, wy = _turn(dx, dy, -ta)
            want = (a["pos"][0] + wx, a["pos"][1] + wy, a["pos"][2] + dz)
            b = min(near, key=lambda b: math.dist(b["pos"], want))
            off = math.dist(b["pos"], want)
            tb = (b.get("rot") or [0, 0, 0])[2]
            turn_off = abs(math.remainder(tb - ta - dt, math.tau))
            if (off > TOL or turn_off > TURN_TOL * 5) and not any(b["id"] in x for x in bad):
                bad.append(f"{b['id']} stands {off:.0f} units (turned {math.degrees(turn_off):.0f} degrees) off where "
                           f"{a['id']} puts it: its source sets the two models as one thing; move them as one")
    return bad
