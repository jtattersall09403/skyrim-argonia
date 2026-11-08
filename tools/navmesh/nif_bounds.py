"""The visible size of a NIF: the box round its shapes' vertices in the model's own space (SSE BSTriShape), with a
shape's bounding sphere where its vertices are not inline (skinned or dynamic shapes). Loading screens size and
centre their models from it (data/loading-screens.json, 1.12 lane loading); the collision box (nif.collision) is
not the visible model and some meshes have none.
    python -m tools.navmesh.nif_bounds <file.nif>...     prints lo, hi, size and centre per file
"""
from __future__ import annotations

import json
import struct
import sys

import numpy as np

from tools.navmesh.nif import Nif, _Reader

SHAPES = ("BSTriShape", "BSSubIndexTriShape", "BSMeshLODTriShape", "BSDynamicTriShape")


class _Bounds(_Reader):
    def __init__(self, nif: Nif):
        super().__init__(nif)
        self.pts: list[np.ndarray] = []

    def walk(self, i, parent, seen):
        if i < 0 or i in seen or i >= len(self.n.types):
            return
        seen.add(i)
        m, _coll, kids = self.av_object(i)
        world = parent @ m
        if self.n.types[i] in SHAPES:
            self.shape_points(i, world)
        for k in kids:
            if 0 <= k < len(self.n.types) and self._is_av(k):
                self.walk(k, world, seen)

    def shape_points(self, i, world):
        n, o = self.n, self.n.offsets[i]
        o += 4
        o += 4 + 4 * n.u32(o)
        o += 4 + (4 if n.bsver > 26 else 2) + 52 + 4  # controller, flags, transform, collision
        c, r = np.array(n.f(o, 3)), n.f(o + 12)
        o += 16 + 12  # sphere; skin, shader, alpha
        desc = struct.unpack_from("<Q", n.b, o)[0]
        o += 8
        o += 4 if n.bsver >= 130 else 2  # triangles
        nv = struct.unpack_from("<H", n.b, o)[0]
        size = n.u32(o + 2)
        o += 6
        stride = (desc & 0xF) * 4
        vflags = (desc >> 44) & 0xFFF
        if size and stride and nv and vflags & 0x001 and n.types[i] != "BSDynamicTriShape":
            v = np.array([n.f(o + k * stride, 3) for k in range(nv)])
        else:
            v = np.array([c + d for d in (np.eye(3) * r).tolist() + (np.eye(3) * -r).tolist()])
        self.pts.append(v @ world[:3, :3].T + world[:3, 3])


def bounds(data: bytes) -> dict:
    nif = Nif(data)
    r = _Bounds(nif)
    seen: set = set()
    for i in [i for i, _ in enumerate(nif.types) if r._is_av(i)]:
        r.walk(i, np.eye(4), seen)
    p = np.concatenate(r.pts)
    lo, hi = p.min(0), p.max(0)
    return {"lo": lo.round(1).tolist(), "hi": hi.round(1).tolist(), "size": (hi - lo).round(1).tolist(),
            "centre": ((hi + lo) / 2).round(1).tolist()}


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f, json.dumps(bounds(open(f, "rb").read())))
