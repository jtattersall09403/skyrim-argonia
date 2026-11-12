"""Seat a placed thing on the ground by its own mesh: the clearance of its lowest vertex over the ground beneath it.

A base whose measured sink lifts it off the ground (a source that set it on a raised bed, a platform or water) floats
here; a `seat` edit row lowers every thing of that base by its clearance, so its lowest vertex sits `embed_m` into the
ground, keeping each thing's identity, form id, x, y, rotation and scale. The mesh is read as the game finds it on the
New World card (tools/places/assets/resolve.py) and its drawable vertices are posed by each thing's rotation and scale.

    python -m tools.newworld.place.seat audit [--json OUT]   every base's floating things (lowest vertex > 0.5 m clear)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

import numpy as np

from tools.newworld.place import place as P

FLOAT_M = 0.5      # a thing whose lowest vertex is this clear of the ground floats
SAMPLE = 500       # vertices kept a mesh: its 100 lowest and a seeded sample of the rest


def rot_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Skyrim's reference rotation (extrinsic X, then Y, then Z)."""
    cx, sx, cy, sy, cz, sz = np.cos(rx), np.sin(rx), np.cos(ry), np.sin(ry), np.cos(rz), np.sin(rz)
    return (np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
            @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))


def mesh_points(model: str, resolver=None) -> np.ndarray | None:
    """A model's drawable vertices in its own frame (None: no mesh the game would find)."""
    from tools.places.assets import nifglb
    from tools.places.assets.resolve import default, norm
    data = (resolver or default()).read(norm(model, "meshes"))
    if data is None:
        return None
    shapes = nifglb.drawable(nifglb.dump(data))
    if not shapes:
        return None
    p = np.concatenate([s["P"] @ np.array(s["m"], float).reshape(3, 4)[:, :3].T + np.array(s["m"], float).reshape(3, 4)[:, 3]
                        for s in shapes])
    if len(p) > SAMPLE + 100:
        keep = np.r_[np.argsort(p[:, 2])[:100], np.random.default_rng(0).choice(len(p), SAMPLE, replace=False)]
        p = p[np.unique(keep)]
    return p


def clearance(points: np.ndarray, pos, rot, scale: float, ground) -> float:
    """Units the posed mesh's lowest vertex stands above the ground beneath it (negative: into it).
    `ground(xs, ys)` -> the lower of the two triangulations' heights at each point."""
    q = points @ rot_matrix(*rot).T * float(scale) + np.asarray(pos, float)
    return float((q[:, 2] - ground(q[:, 0], q[:, 1])).min())


class Seater:
    """seat(o, embed_m) -> the thing's z with its lowest vertex `embed_m` into the ground (never raised)."""

    def __init__(self, world=None, resolver=None):
        self.W, self.R, self._pts = world, resolver, {}

    def ground(self, xs, ys):
        if self.W is None:
            self.W = P.World()
        t1, t2 = self.W.tri_grounds(np.asarray(xs, float), np.asarray(ys, float))
        return np.minimum(t1, t2)

    def points(self, model: str):
        if model not in self._pts:
            self._pts[model] = mesh_points(model, self.R)
        return self._pts[model]

    def seat(self, o: dict, embed_m: float) -> float | None:
        p = self.points(o["model"])
        if p is None:
            return None
        gap = clearance(p, o["pos"], o["rot"], o["scale"], self.ground) + embed_m * P.UPM
        return round(float(o["pos"][2]) - gap, 1) if gap > 0 else None


def audit(refs_dir=None) -> dict:
    """Per base: things, floating things and their median clearance (m), ranked by floating things."""
    s, agg = Seater(), defaultdict(lambda: {"refs": 0, "floating": 0, "clear": []})
    d = refs_dir or P.REFS
    for f in sorted(d.glob("cy*.jsonl")):
        for ln in f.read_text().splitlines():
            o = json.loads(ln)
            a = agg[o["base"]]
            a["refs"] += 1
            p = s.points(o["model"])
            if p is None:
                continue
            c = clearance(p, o["pos"], o["rot"], o["scale"], s.ground) / P.UPM
            if c > FLOAT_M:
                a["floating"] += 1
                a["clear"].append(c)
    rows = [{"base": b, "refs": a["refs"], "floating": a["floating"],
             "median_m": round(float(np.median(a["clear"])), 2) if a["clear"] else 0.0} for b, a in agg.items()]
    rows.sort(key=lambda r: -r["floating"])
    return {"refs": sum(r["refs"] for r in rows), "floating": sum(r["floating"] for r in rows), "bases": rows}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["audit"])
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    rep = audit()
    print(f"seat audit: {rep['refs']} things, {rep['floating']} floating (lowest vertex > {FLOAT_M} m clear)")
    for r in rep["bases"][:40]:
        if r["floating"]:
            print(f"  {r['floating']:>6}/{r['refs']:<6} {r['median_m']:>5} m  {r['base']}")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(rep, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
