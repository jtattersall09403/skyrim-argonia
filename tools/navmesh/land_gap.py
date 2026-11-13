"""How far a navmesh lies from the ground under it (decision 0034): Skyrim's own, beside ours.

An actor walks on the navmesh and its feet are put on the havok ground (the LAND). Where the navmesh lies under the
LAND, a walker's body dips into the ground; where a corpse falls from such a place it can end under the land. For
every exterior cell with a navmesh and a LAND, the cell is sampled on a 64-unit grid; at each sample covered by a
navmesh triangle the gap is the triangle's height minus the LAND's (a height between the quad's two possible splits counts as
on the ground; outside them, the gap to the nearer). Reported for all ground and for rough ground (the quad's four
corners more than 64 units off their plane fit, Skyrim's broken ground): the share of samples lying more than 8 and
more than 16 units under the LAND, and percentiles.

    python -m tools.navmesh.land_gap [--esm PATH] [--world FORMID] [--cells x0,y0,x1,y1] [--every N]
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

from tools.navmesh import esm, nvnm

STEP = 64.0
UNDER = (8.0, 16.0)
ROUGH = 64.0


def land_heights(vhgt: bytes) -> np.ndarray:
    off = struct.unpack_from("<f", vhgt)[0]
    d = np.frombuffer(vhgt, np.int8, 1089, 4).reshape(33, 33).astype(np.float64)
    col0 = off + np.cumsum(d[:, 0])
    rows = col0[:, None] + np.concatenate([np.zeros((33, 1)), np.cumsum(d[:, 1:], axis=1)], axis=1)
    return rows * 8   # rows run south to north, columns west to east


def read(path: Path, world: int, box=None, every: int = 1):
    """(cell xy -> 33x33 LAND heights, cell xy -> navmesh triangles (n, 3, 3)) for the world's exterior cells."""
    cells, land, navm = {}, {}, {}
    label = struct.pack("<I", world)
    for r in esm.records(path, {b"CELL", b"LAND", b"NAVM"}, groups={b"WRLD"}):
        if (esm.GROUP_WORLD_CHILDREN, label) not in r.parents:
            continue
        sub = dict(esm.subrecords(r.data))
        if r.sig == b"CELL" and b"XCLC" in sub:
            cells[r.fid] = struct.unpack_from("<ii", sub[b"XCLC"])
        elif r.sig == b"LAND" and b"VHGT" in sub and r.cell in cells:
            xy = cells[r.cell]
            if (box is None or box[0] <= xy[0] <= box[2] and box[1] <= xy[1] <= box[3]) and (xy[0] + xy[1]) % every == 0:
                land[xy] = land_heights(sub[b"VHGT"])
        elif r.sig == b"NAVM":
            n = nvnm.decode(sub[b"NVNM"])
            if n.grid_xy is not None and len(n.tris):
                navm.setdefault(n.grid_xy, []).append(n.verts.astype(np.float64)[n.tris["v"].astype(int)])
    return land, {k: np.concatenate(v) for k, v in navm.items() if k in land}


def land_z(h: np.ndarray, u: float, v: float) -> tuple[float, float]:
    """The LAND's height at cell-local (u, v) in quads (0..32) under each of the quad's two splits (south-west to
    north-east, and south-east to north-west); the ground is one of them."""
    i, j = min(int(u), 31), min(int(v), 31)
    fu, fv = u - i, v - j
    a, b, c, d = h[j, i], h[j, i + 1], h[j + 1, i], h[j + 1, i + 1]   # sw, se, nw, ne
    s1 = a + (b - a) * fu + (d - b) * fv if fu >= fv else a + (d - c) * fu + (c - a) * fv
    s2 = a + (b - a) * fu + (c - a) * fv if fu + fv <= 1 else d + (c - d) * (1 - fu) + (b - d) * (1 - fv)
    return float(s1), float(s2)


def rough_quads(h: np.ndarray) -> np.ndarray:
    """A quad is rough when its corners leave their best plane by more than ROUGH (the twist of the quad)."""
    tw = np.abs(h[:-1, :-1] + h[1:, 1:] - h[:-1, 1:] - h[1:, :-1]) / 4
    return tw > ROUGH / 4


def gaps(land: dict, navm: dict) -> tuple[np.ndarray, np.ndarray]:
    """(gap navmesh minus LAND at every covered sample, whether its quad is rough)."""
    out, rough = [], []
    g = np.arange(STEP / 2, 4096, STEP)
    for (cx, cy), tris in navm.items():
        h = land[(cx, cy)]
        rq = rough_quads(h)
        px, py = np.meshgrid(cx * 4096 + g, cy * 4096 + g)
        px, py = px.ravel(), py.ravel()
        a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
        den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
        ok = den != 0
        a, b, c, den = a[ok], b[ok], c[ok], den[ok]
        for x, y in zip(px, py):
            l1 = ((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1])) / den
            l2 = ((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1])) / den
            l3 = 1 - l1 - l2
            ins = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
            if not ins.any():
                continue
            zs = l1[ins] * a[ins, 2] + l2[ins] * b[ins, 2] + l3[ins] * c[ins, 2]
            u, v = (x - cx * 4096) / 128, (y - cy * 4096) / 128
            l1z, l2z = land_z(h, u, v)
            lz = (l1z + l2z) / 2
            z = zs[np.argmin(np.abs(zs - lz))]
            lo, hi = min(l1z, l2z), max(l1z, l2z)
            lz = lo if z < lo else hi if z > hi else z     # within the two splits counts as on the ground       # the triangle nearest the ground (a bridge or ledge above is not it)
            if abs(z - lz) > 256:
                continue                             # a navmesh on a placed object, not on the ground
            out.append(z - lz)
            rough.append(bool(rq[min(int(v), 31), min(int(u), 31)]))
    return np.array(out), np.array(rough, bool)


def summary(gap: np.ndarray, rough: np.ndarray) -> dict:
    def one(x):
        if not len(x):
            return {"samples": 0}
        return {"samples": int(len(x)), "mean": round(float(x.mean()), 2),
                "p1_5_50_95": [round(float(v), 1) for v in np.percentile(x, (1, 5, 50, 95))],
                "under_8": round(float((x < -UNDER[0]).mean()), 4), "under_16": round(float((x < -UNDER[1]).mean()), 4)}
    return {"all": one(gap), "rough": one(gap[rough])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tools.navmesh.land_gap")
    ap.add_argument("--esm", required=True)
    ap.add_argument("--world", default="0x3C")
    ap.add_argument("--cells", help="x0,y0,x1,y1")
    ap.add_argument("--every", type=int, default=1, help="every Nth cell by (x + y) mod N")
    a = ap.parse_args(argv)
    box = tuple(int(v) for v in a.cells.split(",")) if a.cells else None
    land, navm = read(Path(a.esm), int(a.world, 0), box, a.every)
    res = summary(*gaps(land, navm))
    res["cells"] = len(navm)
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
