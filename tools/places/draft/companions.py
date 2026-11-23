"""A thing its source makes of several models stays one thing: a ship's hull and its masts and rigging, a building's
body and its roof, set by the source at one pose (their origins within COMPANION units and turned alike). Where the
place has both models of such a pair near each other, the second stands where the first puts it, at the source's
offset turned with the first; a piece set apart by hand (an offset turned the wrong way, one piece moved without the
other) is a fault. A piece carried from the source is judged with its own partner there; a piece placed by hand with
the nearest of the second model. A kit's modular pieces set together at many poses (a scaffold's base and its
floor) are many things, never a pair. `draft check` calls `faults` with the place's sources (its own and each copied
room's).
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


def _rows(src_refs: list[dict]) -> list[dict]:
    return [r for r in src_refs if r.get("kind") in KINDS and r.get("base")]


def _want(a: dict, off: tuple) -> tuple:
    """Where a's second model stands, at the source's offset turned with a."""
    dx, dy, dz, _ = off
    ta = (a.get("rot") or [0, 0, 0])[2]
    wx, wy = _turn(dx, dy, -ta)
    return (a["pos"][0] + wx, a["pos"][1] + wy, a["pos"][2] + dz)


def pairs(src_refs: list[dict]) -> dict:
    """{(base a, base b): (dx, dy, dz, dturn) of b in a's own frame} over a source's pieces set together."""
    out = {}
    rows = _rows(src_refs)
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
            out.setdefault((a["base"], b["base"]), (dx, dy, b["pos"][2] - a["pos"][2], tb - ta))
    # a kit's modular pieces (a scaffold's base and its floor) are set together at many poses: a pair is one thing
    # only where the source never sets the two near each other at another pose
    return {k: v for k, v in out.items() if _always(k, v, rows)}


def _always(key: tuple, off: tuple, rows: list[dict]) -> bool:
    ba, bb = key
    bs = [r for r in rows if r["base"] == bb]
    for a in (r for r in rows if r["base"] == ba):
        near = [b for b in bs if math.dist(a["pos"][:2], b["pos"][:2]) <= NEAR]
        if not near:
            continue
        want = _want(a, off)
        if not any(math.dist(b["pos"], want) <= TOL for b in near):
            return False
    return True


def partners(src_refs: list[dict], known: dict | None = None) -> dict:
    """{a's source id: b's source id}: each first model of a pair with its own second model, as the source sets them."""
    rows = _rows(src_refs)
    known = pairs(src_refs) if known is None else known
    out = {}
    for (ba, bb), off in known.items():
        bs = [r for r in rows if r["base"] == bb]
        for a in (r for r in rows if r["base"] == ba):
            want = _want(a, off)
            got = [b for b in bs if math.dist(b["pos"], want) <= TOL]
            if got:
                out[a["id"]] = got[0]["id"]
    return out


def faults(refs: list[dict], src_ref_lists: list[list[dict]]) -> list[str]:
    known: dict = {}
    mate: dict = {}
    for rows in src_ref_lists:
        got = pairs(rows)
        for k, v in got.items():
            known.setdefault(k, v)
        mate.update(partners(rows, got))
    if not known:
        return []
    by_base: dict = {}
    by_src: dict = {}
    for r in refs:
        if not r.get("removed"):
            by_base.setdefault(r.get("base"), []).append(r)
            if r.get("src"):
                by_src.setdefault(r["src"], []).append(r)
    bad = []
    for (ba, bb), (dx, dy, dz, dt) in sorted(known.items()):
        for a in by_base.get(ba, []):
            if a.get("src") in mate:    # carried from the source: its own partner, where the place still holds it
                near = [b for b in by_src.get(mate[a["src"]], []) if b.get("base") == bb]
            elif a.get("src"):          # a source piece the source set without that model: nothing to keep with it
                continue
            else:                       # placed by hand: the nearest of the second model
                near = [b for b in by_base.get(bb, []) if math.dist(a["pos"][:2], b["pos"][:2]) <= NEAR]
            if not near:
                continue
            ta = (a.get("rot") or [0, 0, 0])[2]
            want = _want(a, (dx, dy, dz, dt))
            b = min(near, key=lambda b: math.dist(b["pos"], want))
            off = math.dist(b["pos"], want)
            tb = (b.get("rot") or [0, 0, 0])[2]
            turn_off = abs(math.remainder(tb - ta - dt, math.tau))
            if (off > TOL or turn_off > TURN_TOL * 5) and not any(b["id"] in x for x in bad):
                bad.append(f"{b['id']} stands {off:.0f} units (turned {math.degrees(turn_off):.0f} degrees) off where "
                           f"{a['id']} puts it: its source sets the two models as one thing; move them as one")
    return bad
