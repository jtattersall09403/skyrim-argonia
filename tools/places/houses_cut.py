"""Can the game's people walk through a house or a tent? The walking mesh a build made, held against each house and
tent of the place, from their real collision triangles.

The engine walks a person between two stops by its own pathfinding on the navmesh, so a way between two stops crosses
a house or tent only if the mesh runs through it: in at one opening and out at another. A house or tent is a row of
kind `building`, or one whose record names a tent, yurt or pavilion, that encloses: its collision triangles standing
in a walker's height over its lowest point (24 to 180 units) stand on at least three quarters of the way round its
middle (a lone wall, a column, a bust or a rubble pile encloses nothing). Its footprint is the plan hull of those
walls less a walker's radius. The walking-mesh triangles whose middles lie in it at its floor (from 40 under to 120
over its lowest point) are its inside; the triangles outside it that share an edge with them are its openings, grouped
where they lie within a doorway's width (160 units). Two or more openings, or openings round more than half of it (the mesh running on under its walls),
make it a way through; one opening (a tent's front, a hut's door) is a room one walks into and back out of, which no
found way crosses.

    python -m tools.places houses_cut <place_id> [--nav out/places/nav/<place_id>.json] [--fix]

--fix adds a `block` walking zone over each way through (the place's walk.jsonl, `by: agent`), which the next build
cuts from the mesh (walknav), so the found ways go round it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

TENT = re.compile(r"tent|yurt|pavilion|lean-?to", re.I)
WALKED = re.compile(r"dock|boardwalk|bridge|walkway|steps|stair|road|plank|pier|jetty|platform|deck|ramp", re.I)
BAND = (24.0, 180.0)
FLOOR = (-40.0, 120.0)
RADIUS = 24.0
FOOT = 60.0           # a wall reaches down to within this of the lowest point (under it a walker passes or steps over)
ENCLOSES = 9          # of twelve thirty-degree sectors round its middle, the walls stand in at least this many
OPENING = 160.0       # ring triangles this near one another are one opening (a doorway is narrower than this)


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
        n = np.array([-e[1], e[0]]) / (np.hypot(*e) or 1.0)
        ok &= (pts - a) @ n > margin
    return ok


def sectors(pts: np.ndarray, centre) -> int:
    """How many of twelve thirty-degree sectors round `centre` the plan points stand in."""
    a = np.degrees(np.arctan2(pts[:, 1] - centre[1], pts[:, 0] - centre[0])) % 360
    return len(set((a // 30).astype(int).tolist()))


def footprint(row: dict, tris_local: np.ndarray):
    """(plan hull, floor z) of an enclosure from its collision triangles, or None when it encloses nothing."""
    from tools.places import xform
    m = np.array(xform.matrix(row["pos"], row.get("rot") or [0, 0, 0], row.get("scale", 1.0)))
    v = tris_local.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
    z0 = float(v[:, 2].min())
    t = v.reshape(-1, 3, 3)
    # a wall is a plan cell (32 units) its collision fills from a walker's feet (within FOOT of the lowest point) to
    # over its head (BAND[1]): a stilt house's raised floor, a low rubble pile or a roof on posts leaves none
    a, b = t[:, :, :], np.roll(t, -1, axis=1)
    f = np.linspace(0.0, 1.0, 9)[None, None, :, None]
    pts = (a[:, :, None, :] * (1 - f) + b[:, :, None, :] * f).reshape(-1, 3)
    cell = np.floor(pts[:, :2] / 32.0).astype(np.int64)
    key = cell[:, 0] * 1_000_003 + cell[:, 1]
    order = np.argsort(key)
    key, z, xy = key[order], pts[order, 2] - z0, pts[order, :2]
    starts = np.r_[0, np.nonzero(np.diff(key))[0] + 1]
    lo, hi = np.minimum.reduceat(z, starts), np.maximum.reduceat(z, starts)
    wall = (lo < FOOT) & (hi > BAND[1])
    if not wall.any():
        return None
    centres = np.array([xy[s:e].mean(axis=0) for s, e, w in zip(starts, np.r_[starts[1:], len(z)], wall) if w])
    h = hull(centres)
    if len(h) < 3 or sectors(centres, h.mean(axis=0)) < ENCLOSES:
        return None
    return h, z0


def houses(rows: list[dict], bases: dict, tris_of) -> list[dict]:
    """Each exterior house or tent that encloses: [{id, base, edid, hull, z0}]."""
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
        if fp is not None:
            out.append({"id": r["id"], "base": r.get("base"), "edid": b.get("edid"), "hull": fp[0], "z0": fp[1]})
    return out


def through(nav: dict, h: np.ndarray, z0: float) -> dict | None:
    """The way through one enclosure on a mesh {verts, tris, nb}: {inside, openings, round}, or None when there is
    none (no triangle inside it, or one opening on no more than half of it)."""
    V = np.asarray(nav["verts"], float).reshape(-1, 3)
    T = np.asarray(nav["tris"], int).reshape(-1, 3)
    NB = np.asarray(nav.get("nb") or [-1] * len(nav["tris"]), int).reshape(-1, 3)
    C = V[T].mean(axis=1)
    lo, hi = h.min(axis=0) - 256, h.max(axis=0) + 256
    near = np.nonzero((C[:, 0] > lo[0]) & (C[:, 0] < hi[0]) & (C[:, 1] > lo[1]) & (C[:, 1] < hi[1]))[0]
    level = near[(C[near, 2] > z0 + FLOOR[0]) & (C[near, 2] < z0 + FLOOR[1])]
    ins = set(level[inside(h, C[level, :2], RADIUS)].tolist())
    if not ins:
        return None
    ring = {int(n) for i in ins for n in NB[i] if n >= 0 and int(n) not in ins}
    if not ring:
        return None
    groups, left = [], set(ring)
    while left:                      # the openings: ring triangles grouped where they lie within a doorway's width
        g, todo = set(), [left.pop()]
        while todo:
            k = todo.pop()
            g.add(k)
            for n in [q for q in left if np.hypot(*(C[q, :2] - C[k, :2])) <= OPENING]:
                left.discard(n)
                todo.append(n)
        groups.append(g)
    rnd = sectors(C[sorted(ring), :2], h.mean(axis=0))
    if len(groups) < 2 and rnd <= 6:
        return None
    groups.sort(key=len, reverse=True)
    shapes = [V[T[sorted(g)]].reshape(-1, 3) for g in groups]
    return {"inside": len(ins), "openings": len(groups), "round": rnd,
            "doors": [{"hull": hull(s[:, :2]), "z": float(s[:, 2].mean())} for s in shapes]}


def cut(nav: dict, rows: list[dict], bases: dict, tris_of) -> list[dict]:
    """Every enclosure the mesh runs through: [{id, base, edid, hull, z0, inside, openings, round}]."""
    m = nav["spaces"]["exterior"]
    out = []
    for hs in houses(rows, bases, tris_of):
        t = through(m, hs["hull"], hs["z0"])
        if t:
            out.append({**hs, **t})
    return out


def lived_in(files: dict) -> list[list[float]]:
    """The spots the place's people must reach (beds, stops, work, patrol and drawn points) and the doors' arrivals: an
    enclosure holding one is walked into, so a block over it would shut someone out of it."""
    rows = {r["id"]: r for r in (files["spaces"].get("exterior") or {}).get("refs") or []}
    pts = [r["door"]["arrival"] for r in rows.values() if (r.get("door") or {}).get("arrival")]
    for p in files.get("people") or []:
        b = rows.get(p.get("bed")) if isinstance(p.get("bed"), str) else None
        if b:
            pts.append(b["pos"])
        for st in (p.get("routine") or []) + ([{"at": p["work"]}] if isinstance(p.get("work"), dict) else []):
            at = st.get("at") or {}
            if (at.get("space") or "exterior") != "exterior":
                continue
            pts.append(rows[at["ref"]]["pos"] if at.get("ref") in rows else at.get("pos"))
            pts += list(st.get("route") or [])
        pat = p.get("patrol") or []
        pts += [q for q in ((pat.get("points") or []) if isinstance(pat, dict) else pat) if isinstance(q, list)]
    return [list(map(float, q[:2])) for q in pts if q]


def door_rows(h: dict) -> list[dict]:
    """`block` zones over each opening of a lived-in enclosure but its widest: the mesh outside its other openings,
    grown by a walker's radius, so the one way in and out is its door."""
    out = []
    for k, d in enumerate(h["doors"][1:], 1):
        c = d["hull"].mean(axis=0)
        ring = [c + (p - c) * (1 + RADIUS / max(1e-6, float(np.hypot(*(p - c))))) for p in d["hull"]]
        out.append({"id": f"{h['id']}.closed-opening-{k}", "kind": "block", "space": "exterior", "by": "agent",
                    "outline": [[round(float(p[0]), 1), round(float(p[1]), 1), round(d["z"], 1)] for p in ring],
                    "note": f"closes an opening of {h['edid'] or h['base']} that is not its door, so no way runs through it"})
    return out


def block_row(h: dict) -> dict:
    c = h["hull"].mean(axis=0)
    ring = [c + (p - c) * max(0.0, 1 - RADIUS / max(1e-6, float(np.hypot(*(p - c))))) for p in h["hull"]]
    return {"id": f"{h['id']}.no-way-through", "kind": "block", "space": "exterior", "by": "agent",
            "outline": [[round(float(p[0]), 1), round(float(p[1]), 1), round(h["z0"], 1)] for p in ring],
            "note": f"no way through {h['edid'] or h['base']}: the mesh ran in at {h['openings']} openings; its footprint, from its collision walls"}


def main(argv: list[str]) -> int:
    from tools.places import edits
    from tools.places.draft import io
    from tools.places.seat import _collision_tris
    ap = argparse.ArgumentParser(prog="python -m tools.places houses_cut")
    ap.add_argument("place_id")
    ap.add_argument("--nav")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--places-dir", default=str(io.PLACES))
    a = ap.parse_args(argv)
    pdir = Path(a.places_dir) / a.place_id
    files = edits.load_place(pdir)
    nav = json.loads(Path(a.nav or (io.BUNDLES.parent / "nav" / f"{a.place_id}.json")).read_text())
    rows = [r for r in (files["spaces"].get("exterior") or {}).get("refs") or [] if r.get("layer") != "world"]
    src = io.load(f"src.{files['place']['source_id']}", io.BUNDLES)
    bases = dict(src.bases)
    bases.update(io.catalogue_bases({r["base"] for r in rows if r.get("base")} - set(bases)))
    hs = houses(rows, bases, _collision_tris)
    got = cut(nav, rows, bases, _collision_tris)
    print(f"houses_cut {a.place_id}: {len(hs)} houses and tents, {len(got)} with a way through")
    for g in got:
        print(f"  {g['id']} ({g['edid']}): {g['inside']} triangles inside, {g['openings']} openings round {g['round'] * 30} degrees")
    keep = np.asarray(lived_in(files), float).reshape(-1, 2)
    home = [g for g in got if len(keep) and inside(g["hull"], keep, -RADIUS).any()]
    for g in home:
        print(f"  {g['id']} is walked into (someone's bed, stop or door is in it): its widest opening stays its door, "
              f"the other {g['openings'] - 1} are closed")
    if a.fix and got:
        p = pdir / "walk.jsonl"
        have = {json.loads(ln)["id"] for ln in p.read_text().splitlines() if ln.strip()} if p.exists() else set()
        new = [block_row(g) for g in got if g not in home and f"{g['id']}.no-way-through" not in have]
        for g in home:     # someone walks into it: every opening but the widest is closed, so it is a room, not a way
            new += [r for r in door_rows(g) if r["id"] not in have]
        with open(p, "a", encoding="utf-8") as f:
            for r in new:
                f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        print(f"  {len(new)} block zones added to {p}")
    return 1 if got else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
