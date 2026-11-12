"""Hanging things of a place: rope lanterns on its Hist and the trees round it, from each tree's own limbs.

The hang points of a tree are measured from its mesh (tools/newworld/dressing/hang_points.py: limb undersides 2.5 to
7 m up, thick enough, with clear air below and a lantern's width from the trunk). A carrier is an exterior tree row
whose base names Hist, or a tree within NEAR of one. Each carrier takes a count drawn from the source mod's own
counts per carrier (King of the Murkmire: the `hanging-hist-lanterns` row of newworld/sources/dressing/kinds.json),
seeded by the tree's row id, one lantern per hang point. A lantern hangs from the point by its rope's top, posed by
the tree's rotation and scale, with a free yaw and no tilt; it is seated `on` the tree (its dz the drop from the
tree's z) so it follows the tree's height. It is refused with less than BELOW_MIN of air over the ground or inside
another solid row's bounds (rows within PART of the carrier are parts of the same tree).

    python -m tools.places.draft.hang <place_id>      the dry run: what the `hang` stage would add, nothing written
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys

import numpy as np

KINDS = "newworld/sources/dressing/kinds.json"
KIND = "hanging-hist-lanterns"
LANTERNS = ("King of the Murkmire.esp:1A845D", "King of the Murkmire.esp:2F01D6")   # DLC2DarkElfLantern05Rope, 04Rope
NEAR = 1536.0          # units: a tree this close to a Hist carries too
PART = 300.0           # units: rows this close to the carrier are parts of the same tree
BELOW_MIN = 60.0       # units of air under a lantern's bottom
SOLID = ("building", "static", "clutter", "furniture", "container", "door", "rock", "tree", "activator")  # rows with a body


def per_carrier(root) -> list[int]:
    return json.loads((root / KINDS).read_text())["kinds"][KIND]["per_carrier"]


def carriers(ext: list[dict], bases: dict) -> list[dict]:
    """Tree rows that carry: a Hist, and the trees within NEAR of one."""
    trees = [r for r in ext if (bases.get(r["base"]) or {}).get("kind") == "tree"]
    hist = [r for r in trees if "Hist" in ((bases.get(r["base"]) or {}).get("edid") or "")]
    return [r for r in trees if r in hist or any(math.dist(r["pos"][:2], h["pos"][:2]) <= NEAR for h in hist)]


def inside(p, r: dict, bases: dict) -> bool:
    """Is point p inside row r's bounds (its box turned by its yaw and scaled)?"""
    b = (bases.get(r["base"]) or {}).get("bounds")
    if not b:
        return False
    s = float(r.get("scale", 1.0))
    a = -float((r.get("rot") or [0, 0, 0])[2])
    dx, dy, dz = p[0] - r["pos"][0], p[1] - r["pos"][1], p[2] - r["pos"][2]
    lx, ly = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
    return all(b[0][i] * s <= v <= b[1][i] * s for i, v in enumerate((lx, ly, dz)))


def plan(place_id: str, ext: list[dict], bases: dict, ground, points_of, shape_of, counts: list[int]) -> list[dict]:
    """The lantern rows for a place's exterior. points_of(model) -> hang points; shape_of(base) -> {anchor, drop};
    ground(x, y) -> the ground's height."""
    from tools.newworld.dressing.hang_points import hang_world
    out = []
    for t in sorted(carriers(ext, bases), key=lambda r: r["id"]):
        pts = points_of(bases[t["base"]]["model"])
        if not pts:
            continue
        rng = np.random.default_rng(int(hashlib.sha256(f"{t['id']}/hang".encode()).hexdigest()[:12], 16))
        want = int(counts[int(rng.integers(len(counts)))])
        tree = {"x": t["pos"][0], "y": t["pos"][1], "z": t["pos"][2], "rx": (t.get("rot") or [0, 0, 0])[0],
                "ry": (t.get("rot") or [0, 0, 0])[1], "rz": (t.get("rot") or [0, 0, 0])[2], "scale": float(t.get("scale", 1.0))}
        others = [r for r in ext if r is not t and r.get("kind") in SOLID and math.dist(r["pos"][:2], t["pos"][:2]) > PART]
        n = 0
        for hn in rng.permutation(len(pts)):
            if n == want:
                break
            base = LANTERNS[int(rng.integers(len(LANTERNS)))]
            rz = float(rng.uniform(0, 2 * math.pi))
            sh = shape_of(base)
            w = hang_world(tree, pts[int(hn)])
            bottom = w[2] - sh["drop"]
            if bottom - ground(w[0], w[1]) < BELOW_MIN:
                continue
            if any(inside(w, r, bases) or inside((w[0], w[1], bottom), r, bases) for r in others):
                continue
            ax, ay, az = sh["anchor"]
            x = w[0] - (ax * math.cos(rz) - ay * math.sin(rz))
            y = w[1] - (ax * math.sin(rz) + ay * math.cos(rz))
            z = w[2] - az
            out.append({"id": f"{place_id}.hang.{t['id'].split('.', 1)[-1]}.{n}", "base": base, "kind": "clutter",
                        "pos": [round(x, 2), round(y, 2), round(z, 2)], "rot": [0.0, 0.0, round(rz, 5)], "scale": 1.0,
                        "layer": "place", "flags": [], "src": None,
                        "seat": {"mode": "on", "on": t["id"], "dz": round(z - t["pos"][2], 2)},
                        "why": f"a rope lantern on hang point {int(hn)} of {bases[t['base']].get('edid')}"})
            n += 1
    return out


def faults(ext: list[dict], bases: dict, points_of, shape_of, tol: float = 3.5) -> list[str]:
    """A lantern row whose rope's top is not within tol (5 cm) of a hang point of the tree it is seated on: a tree
    that changed, moved or was swapped under it leaves it in the air."""
    from tools.newworld.dressing.hang_points import hang_world
    by = {r["id"]: r for r in ext}
    out = []
    for r in ext:
        if r.get("base") not in LANTERNS or (r.get("seat") or {}).get("mode") != "on":
            continue
        t = by.get(r["seat"]["on"])
        if t is None:
            out.append(f"{r['id']}: its tree {r['seat']['on']} is gone")
            continue
        sh = shape_of(r["base"])
        a = float(r["rot"][2])
        ax, ay, az = sh["anchor"]
        top = np.array([r["pos"][0] + ax * math.cos(a) - ay * math.sin(a), r["pos"][1] + ax * math.sin(a) + ay * math.cos(a),
                        r["pos"][2] + az])
        rot = t.get("rot") or [0, 0, 0]
        tree = {"x": t["pos"][0], "y": t["pos"][1], "z": t["pos"][2], "rx": rot[0], "ry": rot[1], "rz": rot[2],
                "scale": float(t.get("scale", 1.0))}
        pts = points_of((bases.get(t["base"]) or {}).get("model"))
        if not pts or min(float(np.linalg.norm(top - hang_world(tree, p))) for p in pts) > tol:
            out.append(f"{r['id']}: not on a limb of {t['id']}")
    return out


def apply(st, log=print) -> None:
    """The `hang` stage: the place's lantern rows made again from its standing trees; place.json's `hang` lists them.
    A lantern row the owner's studio save touched is the owner's (the stage runner keeps it)."""
    rows, bases = want(st)
    old = {a["id"] for a in (st.place.get("hang") or {}).get("added") or []}
    keep = {r["id"] for r in rows}
    st.ext[:] = [r for r in st.ext if r["id"] not in old or r["id"] in keep]
    have = {r["id"]: r for r in st.ext}
    for r in rows:
        if r["id"] in have:
            have[r["id"]].update({k: r[k] for k in ("base", "pos", "rot", "seat", "why")})
        else:
            st.ext.append(r)
    st.place["hang"] = {"added": [{"id": r["id"], "base": r["base"], "on": r["seat"]["on"]} for r in rows]}
    st.bases.update({k: bases[k] for k in LANTERNS if k in bases})
    log(f"draft hang {st.place_id}: {len(rows)} lanterns on {len({r['seat']['on'] for r in rows})} trees")


def for_place(place_id: str) -> tuple[list[dict], dict]:
    from tools.places.draft.stages import Standing
    return want(Standing(place_id))


def want(st) -> tuple[list[dict], dict]:
    """The `hang` stage's rows for a standing place, and its bases (the lanterns' included)."""
    return rows_for(st.place_id, st.ext, st.bases, st.G)


def measurers(bases: dict):
    """(points_of(model) -> the model's hang points, shape_of(base) -> a lantern's anchor and drop), each read once."""
    from tools.newworld.dressing.hang_points import lantern_shape, measure
    from tools.places.assets.resolve import default, norm
    R, pts, shp = default(), {}, {}

    def points_of(model):
        if model not in pts:
            data = R.read(norm(model, "meshes")) if model else None
            pts[model] = measure(data) if data else []
        return pts[model]

    def shape_of(base):
        if base not in shp:
            shp[base] = lantern_shape(bases[base]["model"])
        return shp[base]

    return points_of, shape_of


def rows_for(place_id: str, ext: list[dict], bases: dict, G) -> tuple[list[dict], dict]:
    """Lantern rows for a place's exterior rows on its ground G, and the bases with the lanterns'."""
    from pathlib import Path

    from tools.places.draft.io import catalogue_bases
    bases = dict(bases)
    bases.update(catalogue_bases(set(LANTERNS) - set(bases)))
    if any(k not in bases for k in LANTERNS):      # a catalogue without the lanterns hangs none
        return [], bases
    points_of, shape_of = measurers(bases)

    def ground(x, y):
        h = G.height(x, y)
        return float(h) if h is not None else -1e9

    root = Path(__file__).resolve().parents[3]
    return plan(place_id, ext, bases, ground, points_of, shape_of, per_carrier(root)), bases


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("place_id")
    a = ap.parse_args(argv)
    rows, bases = for_place(a.place_id)
    by = {}
    for r in rows:
        by.setdefault(r["seat"]["on"], []).append(r)
    print(f"hang {a.place_id} (dry run): {len(rows)} lanterns on {len(by)} trees")
    for on, rs in sorted(by.items()):
        print(f"  {on}: {len(rs)} at {[round(r['pos'][2] - 0) for r in rs]}  ({rs[0]['why'].split(' of ')[-1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
