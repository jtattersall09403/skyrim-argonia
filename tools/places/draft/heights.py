"""The height a carried source point takes on our ground: one offset per district body, the ground followed between.

A source town on a hill cannot take one height on a flat site: its districts sat at different heights on the hill. A
wholesale place may name its districts in place.json `fit.districts`, `[{name, clusters: [source cluster ids],
offset: <units> | "auto", terrace?: false}]` (the cluster ids are the look tool's: `b04`, `s55`, `w06`, `landing`). Each district is one
rigid body: every piece of its clusters takes the district's offset (position and turn stay the one transform), and
the ground under it is the source's own terrace at that offset, capped and eased to ours (ground.carry with a
`field`; `terrace: false` keeps our ground about it, for a landing whose source ground was the sea bed). Everything
else follows the carried ground: a piece of another source cluster moves with its cluster by the
cluster's median rise over its own ground; a loose piece keeps its height over the source's ground. `"auto"` is the
median, over the district's buildings and doors, of our ground less the source's ground under each.

`wholesale` writes the resolved districts into place.json `wholesale.districts` `[{name, offset, at: [[x, y], ...]}]`
(`at`: the source positions of the district's pieces, thinned), the one home every later reader takes them from: the
carried walking mesh (srcnav), the rooms' arrivals and the walks.
"""
from __future__ import annotations

import math

import numpy as np

R_IN = 768.0      # units from a district's piece within which a point is the district's
R_OUT = 2048.0    # units at which the district's terrace has eased back to our ground
THIN = 192.0      # units: the grid the district's `at` points are thinned to


def _ease(d):
    t = np.clip((R_OUT - np.asarray(d, float)) / (R_OUT - R_IN), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def thin(pts, step: float = THIN) -> list[list[float]]:
    seen, out = set(), []
    for x, y in pts:
        k = (round(x / step), round(y / step))
        if k not in seen:
            seen.add(k)
            out.append([round(float(x), 1), round(float(y), 1)])
    return out


class Heights:
    """`districts`: [{name, offset, at}] (place.json `wholesale.districts`); `default`: the place's one offset, used
    where neither a district nor the grounds answer."""

    def __init__(self, districts: list[dict] | None, default: float = 0.0):
        from scipy.spatial import cKDTree
        self.default = float(default)
        pts, offs, flat = [], [], []
        for d in districts or ():
            for p in d.get("at") or ():
                (pts if d.get("terrace", True) else flat).append((float(p[0]), float(p[1])))
                if d.get("terrace", True):
                    offs.append(float(d["offset"]))
        self.offs = np.asarray(offs, float)
        self.tree = cKDTree(np.asarray(pts, float)) if pts else None
        self.flat = cKDTree(np.asarray(flat, float)) if flat else None
        self._all = [(float(p[0]), float(p[1]), float(d["offset"])) for d in districts or () for p in d.get("at") or ()]
        self.any = cKDTree(np.asarray([a[:2] for a in self._all], float)) if self._all else None

    def __bool__(self) -> bool:
        return self.any is not None

    def field(self, SX, SY):
        """(weight, offset) arrays at source positions: weight 1 within R_IN of a district's piece, eased to 0 at
        R_OUT; offset the nearest district's. A district laid without its terrace (`terrace: false`: a landing whose
        source ground was the sea bed) keeps our ground about it: the weight eases to 0 near its pieces."""
        SX, SY = np.asarray(SX, float), np.asarray(SY, float)
        if self.tree is None:
            return np.zeros(SX.shape), np.full(SX.shape, self.default)
        q = np.stack([SX.ravel(), SY.ravel()], axis=1)
        d, i = self.tree.query(q)
        w = _ease(d)
        if self.flat is not None:
            w = w * (1.0 - _ease(self.flat.query(q)[0]))
        return w.reshape(SX.shape), self.offs[i].reshape(SX.shape)

    def district(self, x: float, y: float) -> float | None:
        """The offset of the district whose piece lies within R_IN of source point (x, y), or None."""
        if self.any is None:
            return None
        d, i = self.any.query((float(x), float(y)))
        return self._all[i][2] if d <= R_IN else None

    def dz(self, x: float, y: float, z: float | None = None, src_ground=None, our_xy=None, our_ground=None) -> float:
        """The rise of a source point (x, y[, z]): its district's offset; else, a point on or near the source's ground
        or any point the grounds can answer for, our ground less the source's there (it follows the carried ground);
        else the default offset."""
        o = self.district(x, y)
        if o is not None:
            return o
        if src_ground is not None and our_ground is not None and our_xy is not None:
            g, h = src_ground(x, y), our_ground(*our_xy)
            if g is not None and h is not None:
                return float(h) - float(g)
        return self.default


def of_place(place: dict) -> Heights:
    w = place.get("wholesale") or {}
    return Heights(w.get("districts"), float(w.get("offset", 0.0) or 0.0))


def soft_cap(v, cap: float):
    """A change held within +-cap, softly: the terrace's top and bottom round off rather than flatten."""
    if not math.isfinite(cap) or cap >= 1e8:
        return v
    return cap * np.tanh(np.asarray(v, float) / cap)
