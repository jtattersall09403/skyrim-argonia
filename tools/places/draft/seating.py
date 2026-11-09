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

from tools.places.draft import geom
from tools.places.seat import Ground, foot_ground, reference_z

GROUND_BAND = 96.0
SURFACE_BAND = 48.0
CONTACT = 24.0
SUPPORT_KINDS = {"building", "static", "furniture", "container", "activator", "other"}
NEVER_ON = {"building", "tree", "rock"}


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
    if gz is not None and z - gz <= GROUND_BAND:
        return {**out, "mode": "ground", "dz": round(z - gz, 2)}
    return {**out, "mode": "above", "dz": round(z - (h if h is not None else z), 2)}
