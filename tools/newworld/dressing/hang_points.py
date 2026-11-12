"""Hang points of each placed tree kind: where a rope lantern can hang from a limb, in the mesh's own frame.

    python -m tools.newworld.dressing.hang_points run   [--out out/newworld/plugin]   rewrite stale bases only
    python -m tools.newworld.dressing.hang_points check [--out out/newworld/plugin]

Reads each placed tree base's mesh once (refs/flora/bases.json: TREE and tree-class STAT bases), as the game finds
it on the New World card (the assets resolver), and keeps its wood: the shapes that are not leaf cards (a leaf card
is textured as leaves, twigs, fronds, moss or vines, or is two-sided or vertex-alpha and not textured as bark). A hang point is the underside of a
near-horizontal limb (a wood triangle facing down, normal z <= -NZ) that:
- stands HEIGHT (2.5 to 7 m) above the mesh's ground point (its frame's z = 0);
- is THICK enough to carry a rope (the wood straight above it is at least THICK units deep);
- has clear air below: no triangle of the mesh, wood or leaf, within DROP units under it, nor under four points
  CLEAR units round it (the lantern's width);
- stands at least the trunk's radius plus CLEAR from the trunk's axis (the wood below 1 m).
The best KEEP points (thickest limb first), at least SPACING apart, are kept. A base whose limbs give none gets none.

Output: newworld/sources/dressing/hang_points.json, a committed source keyed by base (plugin:edid) with its mesh's
digest; `run` measures only bases whose digest changed or that are new, so it reruns cheaply.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "newworld/sources/dressing/hang_points.json"
PLUGIN = REPO / "out/newworld/plugin"

TREE_CLASSES = ("canopy_tree", "understorey")
HEIGHT = (175.0, 490.0)          # units above the mesh's ground point (2.5 to 7 m)
NZ = 0.6                         # an underside faces down at least this much
THICK = 8.0                      # units of wood above the point (a limb a rope can carry)
DROP = 160.0                     # the longest lantern and its swing room
CLEAR = 30.0                     # the lantern's half-width and a margin
SPACING = 60.0
KEEP = 6
LEAF = re.compile(r"leaf|leaves|frond|moss|vine|ivy|canopy|card|branchlod|hanging|grass|fern|lichen|spanish|twig|branch", re.I)
WOOD = re.compile(r"bark|wood|trunk|root|limb", re.I)


def is_leaf(shape: dict) -> bool:
    """A leaf card: textured as leaves, or two-sided and not textured as bark (a bark shell may be two-sided)."""
    sh = shape.get("shader") or {}
    tex = (shape.get("tex") or [""])[0] or ""
    if LEAF.search(tex):
        return True
    if WOOD.search(tex):
        return False
    return bool(sh.get("two_sided") or sh.get("vertex_alpha"))


def posed(shape: dict) -> tuple[np.ndarray, np.ndarray]:
    m = np.array(shape["m"], float).reshape(3, 4)
    return np.asarray(shape["P"], float) @ m[:, :3].T + m[:, 3], np.asarray(shape["I"], np.int64)


def tri_arrays(shapes: list[dict]) -> np.ndarray:
    """(n, 3, 3) triangles of the given shapes in the mesh frame."""
    ts = []
    for s in shapes:
        P, I = posed(s)
        if len(I):
            ts.append(P[I])
    return np.concatenate(ts) if ts else np.zeros((0, 3, 3))


def vertical_hits(tris: np.ndarray, x: float, y: float) -> np.ndarray:
    """z of every triangle the vertical line through (x, y) crosses."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    v0, v1 = b[:, :2] - a[:, :2], c[:, :2] - a[:, :2]
    p = np.array([x, y]) - a[:, :2]
    den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
    ok = np.abs(den) > 1e-9
    den = np.where(ok, den, 1.0)
    u = (p[:, 0] * v1[:, 1] - v1[:, 0] * p[:, 1]) / den
    v = (v0[:, 0] * p[:, 1] - p[:, 0] * v0[:, 1]) / den
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
    z = a[:, 2] + u * (b[:, 2] - a[:, 2]) + v * (c[:, 2] - a[:, 2])
    return z[hit]


def find_points(wood: np.ndarray, every: np.ndarray) -> list[list[float]]:
    """Hang points from wood triangles and all triangles (each (n, 3, 3) in the mesh frame)."""
    if not len(wood):
        return []
    low = wood.reshape(-1, 3)
    low = low[low[:, 2] < 70.0]
    if not len(low):
        return []
    axis = low[:, :2].mean(0)
    radius = float(np.percentile(np.linalg.norm(low[:, :2] - axis, axis=1), 90))
    n = np.cross(wood[:, 1] - wood[:, 0], wood[:, 2] - wood[:, 0])
    ln = np.linalg.norm(n, axis=1)
    keep = ln > 1e-6
    nz = np.where(keep, n[:, 2] / np.where(keep, ln, 1), 0)
    cen = wood.mean(1)
    cand = keep & (nz <= -NZ) & (cen[:, 2] >= HEIGHT[0]) & (cen[:, 2] <= HEIGHT[1])
    cand &= np.linalg.norm(cen[:, :2] - axis, axis=1) >= radius + CLEAR
    idx = np.nonzero(cand)[0]
    if len(idx) > 600:
        idx = np.sort(np.random.default_rng(0).choice(idx, 600, replace=False))
    wlo, whi = wood[:, :, :2].min(1), wood[:, :, :2].max(1)
    alo, ahi = every[:, :, :2].min(1), every[:, :, :2].max(1)
    found = []
    for i in idx:
        x, y, z = (float(v) for v in cen[i])
        near = (wlo[:, 0] <= x) & (whi[:, 0] >= x) & (wlo[:, 1] <= y) & (whi[:, 1] >= y)
        above = vertical_hits(wood[near], x, y)
        above = above[above > z + 0.5]
        if not len(above) or above.min() - z < THICK:
            continue
        thick = float(above.min() - z)
        clear = True
        for dx, dy in ((0, 0), (CLEAR, 0), (-CLEAR, 0), (0, CLEAR), (0, -CLEAR)):
            px, py = x + dx, y + dy
            sel = (alo[:, 0] <= px) & (ahi[:, 0] >= px) & (alo[:, 1] <= py) & (ahi[:, 1] >= py)
            below = vertical_hits(every[sel], px, py)
            if ((below < z - 0.5) & (below > z - DROP)).any():
                clear = False
                break
        if clear:
            found.append((thick, x, y, z))
    found.sort(key=lambda t: (-t[0], t[3], t[1], t[2]))
    out: list = []
    for thick, x, y, z in found:
        if all((x - p[0]) ** 2 + (y - p[1]) ** 2 + (z - p[2]) ** 2 >= SPACING ** 2 for p in out):
            out.append([round(x, 1), round(y, 1), round(z, 1), round(thick, 1)])
        if len(out) == KEEP:
            break
    return out


def measure(data: bytes) -> list[list[float]]:
    from tools.places.assets import nifglb
    shapes = nifglb.drawable(nifglb.dump(data))
    wood = [s for s in shapes if not is_leaf(s)]
    return find_points(tri_arrays(wood), tri_arrays(shapes))


def tree_bases(out: Path) -> dict:
    """plugin:edid -> model of each placed tree base."""
    bases = json.loads((out / "refs/flora/bases.json").read_text())["bases"]
    return {b["ref"]: b["model"] for b in bases if b.get("cls") in TREE_CLASSES and b.get("model")}


def load() -> dict:
    return json.loads(OUT.read_text())["bases"] if OUT.exists() else {}


def run(out: Path) -> dict:
    from tools.places.assets.resolve import default, norm
    R = default()
    have = load()
    res = {}
    for ref, model in sorted(tree_bases(out).items()):
        data = R.read(norm(model, "meshes"))
        if data is None:
            continue
        dg = hashlib.sha256(data).hexdigest()[:16]
        if ref in have and have[ref]["digest"] == dg:
            res[ref] = have[ref]
            continue
        res[ref] = {"model": model, "digest": dg, "points": measure(data)}
    doc = {"about": __doc__.split("\n")[0] + " Each point: [x, y, z, limb depth] in units, mesh frame.",
           "bases": res}
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    with_pts = sum(1 for v in res.values() if v["points"])
    print(f"hang points: {with_pts} of {len(res)} tree kinds have points")
    return res


def check(out: Path) -> int:
    have, want = load(), tree_bases(out)
    faults = [f"{r}: not measured" for r in sorted(want) if r not in have]
    faults += [f"{r}: model changed" for r in sorted(want) if r in have and have[r]["model"] != want[r]]
    for r, v in have.items():
        for p in v["points"]:
            if not HEIGHT[0] <= p[2] <= HEIGHT[1] or p[3] < THICK:
                faults.append(f"{r}: point {p} out of bounds")
    print(f"hang points check: {sum(1 for v in have.values() if v['points'])} of {len(have)} kinds with points; "
          f"faults {len(faults)}")
    for f in faults[:20]:
        print("  " + f)
    return 1 if faults else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("run", "check"))
    ap.add_argument("--out", type=Path, default=PLUGIN)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        run(a.out)
        return 0
    return check(a.out)


if __name__ == "__main__":
    sys.exit(main())
