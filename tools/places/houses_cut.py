"""Can the game's people walk through a house or a tent? The walking mesh the build made, held against each house and
tent of the place, from their real collision triangles.

The engine walks a person between two stops by its own pathfinding on the navmesh, so the way between any two stops
crosses a house or tent only if the mesh has triangles inside it. For each exterior house or tent (a row of kind
`building`, or one whose record names a tent, yurt or pavilion) its walls are the collision triangles standing in a
walker's height over its lowest point (24 to 180 units); their plan's convex hull, less a walker's radius, is its
footprint. A walking-mesh triangle whose middle lies in that footprint at the house's floor (from 40 under to 120
over its lowest point) is a way through it. A house whose floor is meant to be walked outside (a deck, a market
roof on posts: `walk` on the row, or no walls standing in a walker's height) has no footprint, and a house or tent
someone is meant to walk into (a bed, a stop, a drawn point or a door's arrival inside it) keeps its floor: its walls
hold the way. The build cuts every other footprint from the mesh as a `block` walking zone (`blocks`), so the probe
finds none after a build.

    python -m tools.places houses_cut <place_id> [--nav out/places/nav/<place_id>.json] [--places-dir ...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

TENT = re.compile(r"tent|yurt|pavilion|lean-?to", re.I)
WALKED = re.compile(r"dock|boardwalk|bridge|walkway|steps|stair|road|plank|pier|jetty|platform|deck|ramp", re.I)   # walked on, never round
BAND = (24.0, 180.0)
FLOOR = (-40.0, 120.0)
RADIUS = 24.0


def hull(pts: np.ndarray) -> np.ndarray:
    """The convex hull of plan points, counter-clockwise."""
    P = sorted(set(map(tuple, np.round(pts, 2))))
    if len(P) < 3:
        return np.array(P)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(P):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return np.array(lo[:-1] + hi[:-1])


def inside(poly: np.ndarray, pts: np.ndarray, margin: float) -> np.ndarray:
    """Which plan points lie in a counter-clockwise convex polygon by more than `margin`."""
    ok = np.ones(len(pts), bool)
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        e = b - a
        n = np.array([-e[1], e[0]]) / (np.hypot(*e) or 1.0)     # inward normal of a counter-clockwise edge
        ok &= (pts - a) @ n > margin
    return ok


def footprint(row: dict, tris_local: np.ndarray):
    """(plan hull, floor z) of a house from its collision triangles, or None when nothing stands in a walker's way."""
    from tools.places import xform
    m = np.array(xform.matrix(row["pos"], row.get("rot") or [0, 0, 0], row.get("scale", 1.0)))
    v = tris_local.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
    z0 = float(v[:, 2].min())
    t = v.reshape(-1, 3, 3)
    lo, hi = t[:, :, 2].min(axis=1) - z0, t[:, :, 2].max(axis=1) - z0
    walls = t[(hi > BAND[0]) & (lo < BAND[1])]
    if not len(walls):
        return None
    h = hull(walls[:, :, :2].reshape(-1, 2))
    return (h, z0) if len(h) >= 3 else None


def lived_in(files: dict) -> list[list[float]]:
    """The spots the place's people must reach (beds, stops, work, patrol and drawn points) and the doors' arrivals:
    a house or tent holding one is walked into, so it keeps its floor."""
    rows = {r["id"]: r for r in (files["spaces"].get("exterior") or {}).get("refs") or []}
    pts = [r["door"]["arrival"] for r in rows.values() if (r.get("door") or {}).get("arrival")]
    for p in files.get("people") or []:
        for k in ("bed",):
            b = rows.get(p.get(k)) if isinstance(p.get(k), str) else None
            if b:
                pts.append(b["pos"])
        for st in (p.get("routine") or []) + ([{"at": p["work"]}] if isinstance(p.get("work"), dict) else []):
            at = st.get("at") or {}
            if (at.get("space") or "exterior") != "exterior":
                continue
            if at.get("ref") in rows:
                pts.append(rows[at["ref"]]["pos"])
            elif at.get("pos"):
                pts.append(at["pos"])
            pts += [q for q in st.get("route") or []]
        pat = p.get("patrol") or []
        for q in (pat.get("points") or []) if isinstance(pat, dict) else pat:
            if isinstance(q, list):
                pts.append(q)
    return [list(map(float, q[:2])) for q in pts if q]


def houses(rows: list[dict], bases: dict, tris_of, keep: list | None = None) -> list[dict]:
    """Each exterior house or tent no one is meant to walk into: [{id, base, edid, hull, z0}]."""
    keep = np.asarray(keep or [], float).reshape(-1, 2)
    out = []
    for r in rows:
        b = bases.get(r.get("base")) or {}
        if r.get("walk") is not None or r.get("removed") or r.get("layer") == "world":
            continue
        name = f"{b.get('edid') or ''} {b.get('model') or ''}"
        if (r.get("kind") != "building" and not TENT.search(name)) or WALKED.search(name):
            continue
        t = tris_of(b.get("model")) if b.get("model") else None
        if t is None or not len(t):
            continue
        fp = footprint(r, np.asarray(t, float))
        if fp is None:
            continue
        h, z0 = fp
        if len(keep) and inside(h, keep, -RADIUS).any():
            continue
        out.append({"id": r["id"], "base": r.get("base"), "edid": b.get("edid"), "hull": h, "z0": z0})
    return out


def blocks(rows: list[dict], bases: dict, tris_of, keep: list | None = None) -> list[dict]:
    """The build's `block` walking zones (walknav) that cut each house's and tent's footprint from the walking mesh, so
    the game's pathfinding can never take a person through one."""
    out = []
    for h in houses(rows, bases, tris_of, keep):
        c = h["hull"].mean(axis=0)
        ring = [c + (p - c) * max(0.0, 1 - RADIUS / max(1e-6, float(np.hypot(*(p - c))))) for p in h["hull"]]
        out.append({"id": f"{h['id']}.house", "kind": "block", "space": "exterior", "by": "build",
                    "outline": [[round(float(p[0]), 1), round(float(p[1]), 1), round(h["z0"], 1)] for p in ring],
                    "note": f"no way through {h['edid'] or h['base']}: its footprint, from its collision walls"})
    return out


def cut(place_id: str, nav: dict, rows: list[dict], bases: dict, tris_of, keep: list | None = None) -> list[dict]:
    """Every house or tent with walking-mesh triangles inside it: [{id, base, tris}] (empty: none is walked through)."""
    m = nav["spaces"]["exterior"]
    V = np.asarray(m["verts"], float).reshape(-1, 3)
    T = np.asarray(m["tris"], int).reshape(-1, 3)
    C = V[T].mean(axis=1)
    out = []
    for hs in houses(rows, bases, tris_of, keep):
        h, z0 = hs["hull"], hs["z0"]
        near = (C[:, 2] > z0 + FLOOR[0]) & (C[:, 2] < z0 + FLOOR[1])
        n = int((inside(h, C[near, :2], RADIUS)).sum())
        if n:
            out.append({"id": hs["id"], "base": hs["base"], "edid": hs["edid"], "tris": n})
    return out


def main(argv: list[str]) -> int:
    from tools.places import edits
    from tools.places.draft import io
    from tools.places.seat import _collision_tris
    ap = argparse.ArgumentParser(prog="python -m tools.places houses_cut")
    ap.add_argument("place_id")
    ap.add_argument("--nav")
    ap.add_argument("--places-dir", default=str(io.PLACES))
    a = ap.parse_args(argv)
    files = edits.load_place(Path(a.places_dir) / a.place_id)
    nav = json.loads(Path(a.nav or (io.BUNDLES.parent / "nav" / f"{a.place_id}.json")).read_text())
    rows = [r for r in (files["spaces"].get("exterior") or {}).get("refs") or [] if r.get("layer") != "world"]
    src = io.load(f"src.{files['place']['source_id']}", io.BUNDLES)
    grd = io.load(f"ground.{a.place_id}", io.BUNDLES)
    bases = io.place_bases(src, grd, files["place"])
    bases.update(io.catalogue_bases({r["base"] for r in rows if r.get("base")} - set(bases)))
    got = cut(a.place_id, nav, rows, bases, _collision_tris, lived_in(files))
    houses = sum(1 for r in rows if r.get("kind") == "building" or TENT.search(str((bases.get(r.get("base")) or {}).get("model") or "")))
    print(f"houses_cut {a.place_id}: {houses} houses and tents, {len(got)} with walking-mesh triangles inside")
    for g in got:
        print(f"  {g['id']} ({g['edid']}): {g['tris']} triangles inside")
    return 1 if got else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
