"""A piece's real shape, from its model's MESH, for every tool that measures, checks, places, seats or avoids.

One structure per model, computed once from its triangles and cached on disk by the converted model's content key
(out/places/shapes/v<VERSION>/<key>.npz, an index.json beside it): a SURFACE CLOUD (points laid over every triangle
at most SPACING apart, plus every vertex, each with its face's normal), kept on disk thinned to one point per VOX
cube, and the model-frame COLUMNS read from the full cloud (lowest, highest, highest and lowest walked height per
COL square). An untilted piece (any yaw, any uniform scale) reads its grid from the turned columns; a tilted one
from the cloud in its pose. Every derived number below is read in the world:

- a 16-unit world grid of the UNDERSIDE (lowest surface) and the TOP (highest surface) over the plan, and the
  occupancy that is the piece's true plan outline;
- FEET: connected local minima of the underside (a house's posts, a stair's foot, a bridge's two ends);
- WALK: the top-facing surfaces (normal within ~30 degrees of up) big enough to stand on, as a height field;
- ENDS of a walked span: its walk field's two extremes along its long axis, as end lines (middle, width, height);
- a body's floor, wall footprint and EAVES (the lowest underside outside the walls);
- a tree's ROOT COLLAR (where the trunk's section stops shrinking going up), trunk lean and crown extent;
- a hanging thing's hang point (its top).

Error bounds, on the real models: heights in the grid are exact to SPACING (8 units) along a face (coarser for a huge
model capped at MAX_POINTS: the spacing is in its cache); an untilted piece's cells are placed to COL * 0.71 = 6
units in plan; numbers read from the thinned cloud (a tilted piece's grid, end lines, a tree's collar) to VOX * 1.73
= 10 units. The golden fixture's registered meshes keep their full cloud: exact to the 2-unit tolerance. A model with no readable mesh is listed by name in `unread()` and measured by its box's 12 triangles,
marked `mesh=False` on its Posed; never silently.

The box (`p["lo"]`, `p["hi"]`) is used only as a first reject before two shapes are compared."""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np

VERSION = 5
SPACING = 8.0
MAX_POINTS = 400_000
CELL = 16.0
WALK_NZ = 0.85         # a face this near level (cos of ~32 degrees) is walked on
WALK_MIN_CELLS = 3     # a walked surface this many 16-unit cells or larger is one a person stands on
STEP = 32.0            # a person steps up this much
ROOT = Path(__file__).resolve().parents[2]

REAL = True           # read the converted models; a test sets it False to measure only registered meshes and boxes
_REG: dict[str, np.ndarray] = {}      # fixture or hand-given meshes: model -> tris (n, 3, 3)
_MODEL: dict[str, "Model"] = {}
_UNREAD: dict[str, str] = {}


def cache_dir() -> Path:
    base = Path(os.environ.get("PLACES_OUT", ROOT / "out" / "places"))
    return base / "shapes" / f"v{VERSION}"


def register(model: str, verts, tris) -> None:
    """A mesh given as vertex and triangle lists (the golden fixture's tiny meshes)."""
    V = np.asarray(verts, float).reshape(-1, 3)
    T = np.asarray(tris, int).reshape(-1, 3)
    _REG[str(model).lower()] = V[T]
    _MODEL.pop(str(model).lower(), None)


def unread() -> dict[str, str]:
    """Every model that could not be read as a mesh this run, with why: measured by its box, and said so."""
    return dict(_UNREAD)


# ---------- the model ----------
COL = 8.0              # the model-frame column size of the untilted fast path
VOX = 6.0              # the thinned cloud's cube, for tilted pieces


class Model:
    """A model's surface cloud in its own frame: points (n, 3) float32, normals (n, 3) float32, spacing; and its
    COLUMNS (k, 5): each COL-unit model-frame column's middle x, y, lowest z, highest z and highest walked z (nan when
    nothing walkable). An untilted piece (any yaw, any uniform scale) reads its fields from the turned columns (plan
    error at most COL * 0.71 = 6 units); a tilted one from the cloud itself."""
    def __init__(self, P, N, spacing: float, mesh: bool, cols: np.ndarray | None = None, load=None, hull=None):
        self._P, self._N, self.spacing, self.mesh, self._load = P, N, spacing, mesh, load
        self.cols = columns(P, N) if cols is None else cols
        self.hull = _plan_hull(P) if hull is None else hull

    @property
    def D(self) -> tuple[np.ndarray, np.ndarray]:
        """The cloud thinned to one point per VOX-unit cube (3D error at most VOX * 1.73 = 10 units): what a tilted
        piece's fields are read from."""
        if getattr(self, "_D", None) is None and getattr(self, "_Dload", None):
            self._D = self._Dload()
        if getattr(self, "_D", None) is None:
            P = self.P
            if not len(P):
                self._D = (P, self.N)
            else:
                k = np.floor(P / VOX).astype(np.int64)
                k -= k.min(0)
                span = k.max(0) + 1
                _, idx = np.unique((k[:, 0] * span[1] + k[:, 1]) * span[2] + k[:, 2], return_index=True)
                self._D = (P[idx], self.N[idx])
        return self._D

    def _get(self):
        if self._P is None:
            self._P, self._N = self._load()

    @property
    def P(self) -> np.ndarray:
        self._get()
        return self._P

    @property
    def N(self) -> np.ndarray:
        self._get()
        return self._N


def columns(P: np.ndarray, N: np.ndarray) -> np.ndarray:
    if not len(P):
        return np.zeros((0, 5), np.float32)
    I = np.floor(P[:, 0] / COL).astype(np.int64)
    J = np.floor(P[:, 1] / COL).astype(np.int64)
    key = (I - I.min()) * (int(J.max() - J.min()) + 1) + (J - J.min())
    o = np.argsort(key, kind="stable")
    k, z, up = key[o], P[o, 2], N[o, 2] >= WALK_NZ
    st = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    zmin = np.minimum.reduceat(z, st)
    zmax = np.maximum.reduceat(z, st)
    wz = np.where(up, z, -np.inf)
    wmax = np.maximum.reduceat(wz, st)
    wmax = np.where(np.isfinite(wmax), wmax, np.nan)
    wmin = np.minimum.reduceat(np.where(up, z, np.inf), st)
    wmin = np.where(np.isfinite(wmin), wmin, np.nan)
    ii, jj = I[o][st], J[o][st]
    return np.stack([(ii + 0.5) * COL, (jj + 0.5) * COL, zmin, zmax, wmax, wmin], 1).astype(np.float32)


def cloud(tris: np.ndarray, spacing: float = SPACING) -> tuple[np.ndarray, np.ndarray, float]:
    """Points over every triangle at most `spacing` apart, with the face normal; spacing grows to keep MAX_POINTS."""
    tris = np.asarray(tris, float).reshape(-1, 3, 3)
    if not len(tris):
        return np.zeros((0, 3), np.float32), np.zeros((0, 3), np.float32), spacing
    e = np.stack([np.linalg.norm(tris[:, 1] - tris[:, 0], axis=1), np.linalg.norm(tris[:, 2] - tris[:, 1], axis=1),
                  np.linalg.norm(tris[:, 0] - tris[:, 2], axis=1)], 1).max(1)
    while True:
        n = np.maximum(1, np.ceil(e / spacing)).astype(int)
        total = int(((n + 1) * (n + 2) // 2).sum())
        if total <= MAX_POINTS:
            break
        spacing *= 1.5
    nrm = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.where(ln > 1e-12, nrm / np.maximum(ln, 1e-12), 0.0)
    Ps, Ns = [], []
    for k in np.unique(n):
        idx = np.nonzero(n == k)[0]
        ij = np.array([(i, j) for i in range(k + 1) for j in range(k + 1 - i)], float) / k
        w = np.stack([1 - ij[:, 0] - ij[:, 1], ij[:, 0], ij[:, 1]], 1)          # (m, 3) barycentric
        T = tris[idx]                                                          # (t, 3, 3)
        Ps.append(np.einsum("mk,tkd->tmd", w, T).reshape(-1, 3))
        Ns.append(np.repeat(nrm[idx], len(w), axis=0))
    return np.concatenate(Ps).astype(np.float32), np.concatenate(Ns).astype(np.float32), spacing


def box_tris(lo, hi) -> np.ndarray:
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    c = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
    f = [(0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3), (0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5),
         (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6)]
    return c[np.array(f)]


_INDEX: dict | None = None


def _index() -> dict:
    """model -> converted model key, kept beside the cache so a warm run skips the archive lookup; an entry whose
    cached shape is gone is looked up again (`shape.py --fresh` forgets them all)."""
    global _INDEX
    if _INDEX is None:
        import json
        try:
            _INDEX = json.loads((cache_dir() / "index.json").read_text())
        except (OSError, ValueError):
            _INDEX = {}
    return _INDEX


def _save_index() -> None:
    import json
    f = cache_dir() / "index.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(_index()))
    os.replace(tmp, f)


def _glb_key(model: str) -> tuple[str | None, str | None]:
    k = _index().get(model)
    if k and (cache_dir() / f"{k}.npz").exists():
        return k, None
    got = _glb_key_fresh(model)
    if got[0]:
        _index()[model] = got[0]
        _save_index()
    return got


def _glb_key_fresh(model: str) -> tuple[str | None, str | None]:
    try:
        from tools.places import assets
        info = assets.mesh_info(model)
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"[:200]
    if not info.get("tris") or info.get("placeholder"):
        return None, str(info.get("why") or info.get("reason") or "no readable mesh (the converter's stand-in box)")
    return Path(info["glb"]).name.split(".")[0], None


def model(name: str | None, lo=None, hi=None) -> Model:
    """The model's cloud: from the registered mesh, the disk cache, or its converted model's triangles (cached)."""
    k = str(name or "").lower()
    if k in _MODEL:
        return _MODEL[k]
    m = None
    if k in _REG:
        P, N, s = cloud(_REG[k])
        m = Model(P, N, s, True)
    elif k and not REAL:
        why = "real models off (a test)"
    elif k:
        key, why = _glb_key(k)
        if key:
            f = cache_dir() / f"{key}.npz"
            if f.exists():
                z = np.load(f)
                m = Model(None, None, float(z["s"]), True, z["C"],
                          load=lambda z=z: (z["DP"], z["DN"].astype(np.float32) / 127.0), hull=z["H"])
                m._D = None
                m._Dload = m._load
            else:
                from tools.places.look import outline
                T = outline.model_tris(k)
                if T is not None and len(T):
                    P, N, s = cloud(T)
                    f.parent.mkdir(parents=True, exist_ok=True)
                    tmp = f.with_suffix(f".{os.getpid()}.tmp.npz")
                    m = Model(P, N, s, True)
                    DP, DN = m.D
                    np.savez_compressed(tmp, s=np.float32(s), C=m.cols, DP=DP, DN=np.round(DN * 127).astype(np.int8), H=m.hull)
                    os.replace(tmp, f)
                else:
                    why = "the converted model has no triangles"
    if m is None and k:
        _UNREAD[k] = why or "unreadable"
    if m is None:
        if lo is None:
            m = Model(np.zeros((0, 3), np.float32), np.zeros((0, 3), np.float32), SPACING, False)
            return m
        P, N, s = cloud(box_tris(lo, hi), 32.0)
        m = Model(P, N, s, False)
        return m                       # a box stand-in is per piece's bounds: not cached under the model's name
    _MODEL[k] = m
    return m


# ---------- a piece in its pose ----------
class Posed:
    """A piece's shape in the world. Grid cells are world-aligned CELL squares keyed (i, j) = floor(x / CELL)."""
    def __init__(self, p: dict):
        self.M = M = np.asarray(p["m"], float)
        self._mod = mod = model(p.get("model"), p.get("lo"), p.get("hi"))
        self.mesh = mod.mesh
        self.spacing = mod.spacing
        A = M[:3, :3]
        sc = max(np.cbrt(abs(np.linalg.det(A))), 1e-9)
        self.tilted = abs(A[2, 2] / sc - 1.0) > 1e-4 or abs(A[2, 0]) > 1e-4 * sc or abs(A[2, 1]) > 1e-4 * sc
        self._P = None
        if not len(mod.cols):
            self._empty()
        elif self.tilted:
            DP, DN = mod.D
            A = M[:3, :3]
            P = DP.astype(float) @ A.T + M[:3, 3]
            nz = (DN @ (A / sc).T)[:, 2]
            wz = np.where(nz >= WALK_NZ, P[:, 2], np.nan)
            self._grid(P[:, 0], P[:, 1], P[:, 2], P[:, 2], wz, wz)
        else:
            C = mod.cols.astype(float)
            xy = C[:, :2] @ A[:2, :2].T + M[:2, 3]
            zz = C[:, 2:6] * A[2, 2] + M[2, 3]
            self._grid(xy[:, 0], xy[:, 1], zz[:, 0], zz[:, 1], zz[:, 2], zz[:, 3])
            H = mod.hull.astype(float) @ A[:2, :2].T + M[:2, 3]       # the plan's exact extent, from its hull
            if len(H):
                self.lo[:2], self.hi[:2] = H.min(0), H.max(0)
            if A[2, 2] < 0:
                self.lo[2], self.hi[2] = self.hi[2], self.lo[2]

    @property
    def P(self) -> np.ndarray:
        """The surface cloud in the world (computed when first asked)."""
        if self._P is None:
            mod, M = self._mod, self.M
            self._P = mod.P.astype(float) @ M[:3, :3].T + M[:3, 3] if len(mod.cols) else np.zeros((0, 3))
        return self._P

    @property
    def N(self) -> np.ndarray:
        A = self.M[:3, :3]
        return self._mod.N @ (A / max(np.cbrt(abs(np.linalg.det(A))), 1e-9)).T

    def _empty(self):
        self.i0 = self.j0 = 0
        self.under = self.top = self.walk = self.walk_low = np.full((0, 0), np.nan)
        self.lo = self.hi = np.zeros(3)

    def _grid(self, x, y, zlo, zhi, zwalk, zwalk_low):
        self.lo = np.array([x.min(), y.min(), zlo.min()])
        self.hi = np.array([x.max(), y.max(), zhi.max()])
        I = np.floor(x / CELL).astype(np.int64)
        J = np.floor(y / CELL).astype(np.int64)
        self.i0, self.j0 = int(I.min()), int(J.min())
        ni, nj = int(I.max()) - self.i0 + 1, int(J.max()) - self.j0 + 1
        flat = (I - self.i0) * nj + (J - self.j0)
        o = np.argsort(flat, kind="stable")
        k = flat[o]
        st = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
        cells = k[st]

        def field(v, red):
            out = np.full(ni * nj, np.nan)
            out[cells] = red.reduceat(v[o], st)
            return out.reshape(ni, nj)
        self.under, self.top = field(zlo, np.minimum), field(zhi, np.maximum)
        w = field(np.where(np.isnan(zwalk), -np.inf, zwalk), np.maximum)
        w[~np.isfinite(w)] = np.nan
        self.walk = _keep_big(w, WALK_MIN_CELLS)
        wl = field(np.where(np.isnan(zwalk_low), np.inf, zwalk_low), np.minimum)
        wl[~np.isfinite(wl)] = np.nan
        self.walk_low = wl

    @property
    def occ(self) -> np.ndarray:
        return ~np.isnan(self.under)

    def cell_xy(self, ii, jj):
        return (self.i0 + np.asarray(ii) + 0.5) * CELL, (self.j0 + np.asarray(jj) + 0.5) * CELL

    def low(self) -> float:
        return float(self.lo[2])

    def top_z(self) -> float:
        return float(self.hi[2])

    def cells(self, field: str = "under"):
        """(x, y, z) of every occupied cell of a field."""
        F = getattr(self, field)
        ii, jj = np.nonzero(~np.isnan(F))
        x, y = self.cell_xy(ii, jj)
        return np.stack([x, y, F[ii, jj]], 1) if len(ii) else np.zeros((0, 3))

    def at(self, x: float, y: float, field: str = "under") -> float | None:
        F = getattr(self, field)
        i, j = int(math.floor(x / CELL)) - self.i0, int(math.floor(y / CELL)) - self.j0
        if 0 <= i < F.shape[0] and 0 <= j < F.shape[1] and not np.isnan(F[i, j]):
            return float(F[i, j])
        return None

    def surface_near(self, x: float, y: float, z: float, r: float, dz: float) -> float | None:
        """The height of this mesh's top or walked surface within r of (x, y) in plan and dz of z, nearest z; None
        when it has none there (what an end line rests on)."""
        best = None
        i0, i1 = int(math.floor((x - r) / CELL)) - self.i0, int(math.floor((x + r) / CELL)) - self.i0 + 1
        j0, j1 = int(math.floor((y - r) / CELL)) - self.j0, int(math.floor((y + r) / CELL)) - self.j0 + 1
        i0, j0 = max(i0, 0), max(j0, 0)
        if i0 >= self.under.shape[0] or j0 >= self.under.shape[1] or i1 <= 0 or j1 <= 0:
            return None
        for F in (self.top, self.walk, self.walk_low):
            w = F[i0:i1, j0:j1]
            m = ~np.isnan(w) & (np.abs(w - z) <= dz)
            if m.any():
                v = w[m][np.argmin(np.abs(w[m] - z))]
                if best is None or abs(v - z) < abs(best - z):
                    best = float(v)
        return best

    def outline(self) -> list[list[float]]:
        """The true plan outline as the occupied cells' convex hull (for the drawing); occupancy is `occ`."""
        pts = self.cells("under")[:, :2]
        return [[round(float(a), 1), round(float(b), 1)] for a, b in _hull(pts)] if len(pts) else []

    # ground against the mesh
    def clearance(self, ground, band: float = 48.0) -> dict | None:
        """The mesh's underside against the ground under its own cells: `over` the least underside-over-ground of its
        cells within `band` of its lowest point and of every other cell (taken at every second cell: the ground's
        grid is 128), negative: in the ground; `gmin`/`gmax` the lowest and highest ground under the footprint;
        `at` where the least is."""
        U = self.under
        if not U.size:
            return None
        occ = ~np.isnan(U)
        ii, jj = np.nonzero(occ & ((U <= self.low() + band)
                                   | ((np.arange(U.shape[0])[:, None] % 2 == 0) & (np.arange(U.shape[1])[None, :] % 2 == 0))))
        xs, ys = self.cell_xy(ii, jj)
        zs = U[ii, jj]
        best = None
        gs = []
        for x, y, z in zip(xs.tolist(), ys.tolist(), zs.tolist()):
            g = ground.height(x, y)
            if g is None:
                continue
            gs.append(g)
            if best is None or z - g < best[0]:
                best = (z - g, x, y, z, g)
        if best is None:
            return None
        return {"over": round(float(best[0]), 1), "at": [round(float(best[1]), 1), round(float(best[2]), 1)],
                "z": round(float(best[3]), 1), "ground": round(float(best[4]), 1),
                "gmin": round(float(min(gs)), 1), "gmax": round(float(max(gs)), 1)}

    def sunk_share(self, ground) -> float:
        """How much of the piece is in the ground, cell by cell over its plan (every second cell): the mean share of
        each cell's height span [underside, top] under the ground there. A plant mostly in the ground scores high; a
        stem reaching down under fronds that stand in the air does not."""
        U, T = self.under, self.top
        if not U.size:
            return 0.0
        ii, jj = np.nonzero(~np.isnan(U))
        sel = ((ii + jj) % 2 == 0) if len(ii) > 8 else np.ones(len(ii), bool)
        ii, jj = ii[sel], jj[sel]
        xs, ys = self.cell_xy(ii, jj)
        got = []
        for x, y, u, t in zip(xs.tolist(), ys.tolist(), U[ii, jj].tolist(), T[ii, jj].tolist()):
            g = ground.height(x, y)
            if g is None:
                continue
            got.append(min(max((g - u) / (t - u), 0.0), 1.0) if t > u else float(t < g))
        return float(np.mean(got)) if got else 0.0

    # derived parts
    def feet(self, band: float = 48.0, radius: int = 2) -> list[dict]:
        """Where the mesh comes lowest: connected cells that are local minima of the underside (within 2 cells), each
        foot with its middle, height and size in cells, lowest first."""
        U = self.under
        if not U.size:
            return []
        V = np.where(np.isnan(U), np.inf, U)
        pad = np.pad(V, radius, constant_values=np.inf)
        mn = np.full_like(V, np.inf)
        for di in range(2 * radius + 1):
            for dj in range(2 * radius + 1):
                mn = np.minimum(mn, pad[di:di + V.shape[0], dj:dj + V.shape[1]])
        m = np.isfinite(V) & (V <= mn + 2.0)
        lab = _label(m)
        out = []
        for k in range(1, int(lab.max()) + 1 if lab.size else 1):
            ii, jj = np.nonzero(lab == k)
            if not len(ii):
                continue
            x, y = self.cell_xy(ii, jj)
            z = V[ii, jj]
            out.append({"at": [round(float(x.mean()), 1), round(float(y.mean()), 1)], "z": round(float(z.min()), 1),
                        "cells": int(len(ii))})
        out.sort(key=lambda f: f["z"])
        return out

    def walk_cells(self) -> np.ndarray:
        return self.cells("walk")

    def ends(self) -> list[dict] | None:
        """A walked span's two end lines, from its DECK: the one walked surface running its length (`_deck`: rails,
        rope tops, post caps and end frames standing above or beyond the planks are not it). The ends are the deck's
        extremes along its axis (the walk's long axis, or its climb where it rises CLIMB a unit: a flight wider than
        it is long); each end line's middle (x, y, z: the median deck height at
        the end edge, the last plank's), its width across, the outward axis, `under`: the underside of its deck there
        (the lowest point within a cell of the end and DECK_DEPTH under the walk) and `reach`/`reach_at`: the lowest
        point of anything of it within LEG_REACH (its own legs' feet) and where it is. Lowest first: a stair's FOOT,
        then its HEAD."""
        P, nz = self.P, self.N[:, 2]
        W = P[nz >= WALK_NZ]
        walked = len(W) >= 3
        if not walked:
            W = P
        if len(W) < 3:
            return None
        xy = W[:, :2]
        c = xy.mean(0)
        _, _, vt = np.linalg.svd(xy - c, full_matrices=False)
        ax = vt[0]
        if walked:                     # a flight climbs along its axis even when it is wider than it is long
            g = np.linalg.lstsq(np.c_[xy - c, np.ones(len(xy))], W[:, 2], rcond=None)[0][:2]
            if np.hypot(*g) >= CLIMB:
                ax = g / np.hypot(*g)
        across = np.array([-ax[1], ax[0]])
        t = (xy - c) @ ax
        sd = (xy - c) @ across
        if walked:
            keep = _deck(W[:, 2], t, sd)
            W, t, sd = W[keep], t[keep], sd[keep]
        tall = (P[:, :2] - c) @ ax
        out = []
        for sgn, ext in ((-1, t.min()), (1, t.max())):
            sel = np.abs(t - ext) <= END_EDGE
            edge = np.abs(t - ext) <= CELL
            side = sd[edge]
            mid = c + ax * ext + across * (side.max() + side.min()) / 2
            near = P[np.abs(tall - ext) <= CELL]
            legs = P[np.abs(tall - ext) <= LEG_REACH]
            zw = float(np.median(W[sel, 2]))
            deck = near[(near[:, 2] <= zw + 1.0) & (near[:, 2] >= zw - DECK_DEPTH)] if len(near) else near
            foot = legs[np.argmin(legs[:, 2])] if len(legs) else None
            out.append({"at": [round(float(mid[0]), 1), round(float(mid[1]), 1), round(zw, 1)],
                        "width": round(float(side.max() - side.min()), 1),
                        "out": [round(float(sgn * ax[0]), 4), round(float(sgn * ax[1]), 4)],
                        "under": round(float(deck[:, 2].min()), 1) if len(deck) else None,
                        "reach": None if foot is None else round(float(foot[2]), 1),
                        "reach_at": None if foot is None else [round(float(foot[0]), 1), round(float(foot[1]), 1)]})
        out.sort(key=lambda e: e["at"][2])
        return out

    def body(self) -> dict:
        """A building body: its ROOF cells (underside in the upper 40% of its height), its WALL footprint (the other
        occupied cells: walls, floor, legs), its FLOOR (the most common lowest walked surface over the wall cells,
        above its legs), and its EAVES (the lowest underside of the roof cells outside the walls, grown by a cell:
        the roof where it overhangs); eaves None when the roof does not overhang."""
        U = self.under
        if not U.size:
            return {}
        low, top = self.low(), self.top_z()
        occ = ~np.isnan(U)
        roof = occ & (U >= low + 0.6 * (top - low))
        wall = occ & ~roof
        over = roof & ~_dilate(wall, 1)
        eaves = float(np.nanmin(U[over])) if over.any() else None
        W = self.walk_low[wall]
        W = W[~np.isnan(W)]
        W = W[W > low + 1.0] if (W > low + 1.0).any() else W
        floor = None
        if len(W):
            v, n = np.unique(np.round(W / 2.0) * 2.0, return_counts=True)
            floor = float(v[np.argmax(n)])
        ii, jj = np.nonzero(wall)
        x, y = self.cell_xy(ii, jj)
        return {"floor": floor, "eaves": None if eaves is None else round(eaves, 1),
                "footprint": [[round(float(a), 1), round(float(b), 1)] for a, b in _hull(np.stack([x, y], 1))] if len(ii) else []}

    def tree(self, slab: float = 8.0, fine: float = 4.0) -> dict:
        """A tree or plant: its ROOT COLLAR (going up from its lowest point, the height where the section's area
        stops shrinking: where root flare becomes trunk), its root tips (feet), its trunk lean (the slice middles'
        line from the collar up), crown extent (the plan extent of its upper half) and top."""
        P = self.P
        if not len(P):
            return {}
        low, top = float(P[:, 2].min()), float(P[:, 2].max())
        h = top - low
        zs = np.arange(low, low + min(h * 0.6, 600.0), slab)
        areas, mids = [], []
        for z in zs:
            s = P[(P[:, 2] >= z) & (P[:, 2] < z + slab)]
            if not len(s):
                areas.append(0.0); mids.append(None); continue  # noqa: E702
            k = np.unique(np.floor(s[:, :2] / fine).astype(int), axis=0)
            areas.append(len(k) * fine * fine)
            mids.append(s[:, :2].mean(0))
        areas = np.array(areas)
        collar = low
        if len(areas) > 2:
            sm = np.convolve(areas, np.ones(3) / 3, mode="same")
            peak = int(np.argmax(sm[: max(2, len(sm) // 2)]))
            collar_i = peak
            for i in range(peak + 1, len(sm) - 1):
                collar_i = i
                if sm[i + 1] >= sm[i] * 0.97:
                    break
            collar = float(zs[collar_i])
        trunk = [(z, m) for z, m in zip(zs, mids) if m is not None and z >= collar]
        lean = None
        if len(trunk) >= 3:
            Z = np.array([z for z, _ in trunk])
            XY = np.array([m for _, m in trunk])
            dx = np.polyfit(Z, XY[:, 0], 1)[0]
            dy = np.polyfit(Z, XY[:, 1], 1)[0]
            lean = round(math.degrees(math.atan(math.hypot(dx, dy))), 1)
        up = P[P[:, 2] >= low + h / 2]
        crown = [[round(float(v), 1) for v in up[:, :2].min(0)], [round(float(v), 1) for v in up[:, :2].max(0)]] if len(up) else None
        return {"collar": round(collar, 1), "low": round(low, 1), "top": round(top, 1), "lean": lean, "crown": crown,
                "roots": self.feet()[:8]}

    def hang_point(self) -> list[float]:
        T = self.top
        z = float(np.nanmax(T))
        ii, jj = np.nonzero(T >= z - 1.0)
        x, y = self.cell_xy(ii, jj)
        return [round(float(x.mean()), 1), round(float(y.mean()), 1), round(z, 1)]


_POSED: dict = {}


def posed(p: dict) -> Posed:
    """The piece's Posed, cached by model and pose for the run."""
    k = (str(p.get("model") or "").lower(), tuple(np.round(np.asarray(p["m"], float).ravel(), 3)),
         tuple(p.get("lo") or ()), tuple(p.get("hi") or ()))
    s = _POSED.get(k)
    if s is None:
        s = _POSED[k] = Posed(p)
    return s


# ---------- two shapes ----------
def _shared(a: Posed, b: Posed):
    """The two grids' overlapping window as (a slice, b slice) or None."""
    i0, j0 = max(a.i0, b.i0), max(a.j0, b.j0)
    i1 = min(a.i0 + a.under.shape[0], b.i0 + b.under.shape[0])
    j1 = min(a.j0 + a.under.shape[1], b.j0 + b.under.shape[1])
    if i0 >= i1 or j0 >= j1:
        return None
    return ((slice(i0 - a.i0, i1 - a.i0), slice(j0 - a.j0, j1 - a.j0)),
            (slice(i0 - b.i0, i1 - b.i0), slice(j0 - b.j0, j1 - b.j0)))


def boxes_apart(a: Posed, b: Posed, gap: float = 0.0) -> bool:
    """The first reject: the two shapes' world boxes do not come within gap."""
    return bool(((a.lo - gap) > b.hi).any() or ((b.lo - gap) > a.hi).any())


def rests_on(a: Posed, b: Posed, tol: float = 24.0, reach: float = 160.0, a_band: float = 48.0) -> bool:
    """Does a's underside (its cells within a_band of its lowest point: where it comes down) rest on b? In a shared
    cell, one of b's surfaces meets it: b's top within tol under a's underside to `reach` over it (a post rising
    through a deck holds it), or one of b's walked surfaces (its highest or lowest: a floor inside a hut, a deck under
    a roof) within tol under to a step over it; b must have substance under that height there."""
    if boxes_apart(a, b, tol):
        return False
    w = _shared(a, b)
    if w is None:
        return False
    sa, sb = w
    au, bu = a.under[sa], b.under[sb]
    m0 = ~np.isnan(au) & (au <= a.low() + a_band) & ~np.isnan(bu)
    if not m0.any():
        return False
    bt = b.top[sb]
    if (m0 & (bt >= au - tol) & (bt <= au + reach)).any():
        return True
    for F in (b.walk[sb], b.walk_low[sb]):
        if (m0 & ~np.isnan(F) & (F >= au - tol) & (F <= au + STEP)).any():
            return True
    return False


def overlap(a: Posed, b: Posed, margin: float = 0.0) -> dict | None:
    """Two meshes' shared occupancy: cells both occupy whose height spans [under, top] cross by more than margin.
    None when they do not. A spreading root under a deck between its posts, an egg beside a cliff and a deck round a
    trunk share no cell at a height both fill; a house inside a house does (their walls' spans cross)."""
    if boxes_apart(a, b):
        return None
    w = _shared(a, b)
    if w is None:
        return None
    sa, sb = w
    au, at_, bu, bt = a.under[sa], a.top[sa], b.under[sb], b.top[sb]
    both = ~np.isnan(au) & ~np.isnan(bu)
    if not both.any():
        return None
    depth = np.minimum(at_, bt) - np.maximum(au, bu)
    m = both & (depth > margin)
    if not m.any():
        return None
    return {"cells": int(m.sum()), "area": round(float(m.sum() * CELL * CELL)), "depth": round(float(np.nanmax(np.where(m, depth, np.nan))), 1)}


# ---------- connections ----------
MEET_ALONG = 16.0      # an end within this of a surface along its axis meets it
MEET_BACK = 64.0       # a surface reaching this far back under the end still counts (an end resting on a deck's lip)
LOOK_AHEAD = 192.0     # how far past an end a surface it should meet is looked for
SINK = 48.0            # an end's underside this far in the ground is buried
DECK_DEPTH = 64.0      # a walked span's deck is at most this thick under its walk: lower parts are its own legs
LEG_REACH = 64.0       # its own legs within this of an end (along the span) hold that end
DECK_TOL = STEP + 4    # a deck rises at most this from one CELL slice to the next (a stair's riser; a rail is higher)
DECK_GAP = 2           # this many empty CELL slices (gaps between planks) are crossed when following a deck
CLIMB = 0.25           # a walk whose height rises this much a unit (a flight) takes its climb as its axis
END_EDGE = CELL       # an end line's height is the median of the deck within this of its end edge (its last plank)


def walk_points(s: Posed) -> np.ndarray:
    P = s.P
    return P[s.N[:, 2] >= WALK_NZ] if len(P) else P


def legs_held(e: dict, others: list, ground) -> bool:
    """Does the span's own mesh stand on legs under this end: is the lowest point of it within LEG_REACH of the end
    (`reach`, at `reach_at`: a post's foot) within STEP over the ground (or in it), on another mesh (its top or a
    walked surface within STEP of the foot, a cell round: a rock, a deck) or set into one all round (a cell round
    it, the foot between its underside and its top: a post in a rock, not a post beside another post)?"""
    r, at = e.get("reach"), e.get("reach_at")
    if r is None:
        return False
    x, y = at if at else e["at"][:2]
    g = ground.height(x, y) if ground is not None else None
    if g is not None and r - g <= STEP:
        return True
    for _, o in others:
        if o.lo[0] > x + CELL or o.hi[0] < x - CELL or o.lo[1] > y + CELL or o.hi[1] < y - CELL \
                or o.lo[2] > r + STEP or o.hi[2] < r - STEP:
            continue
        inside = 0
        for dx in (-CELL, 0.0, CELL):
            for dy in (-CELL, 0.0, CELL):
                if o.surface_near(x + dx, y + dy, r, 0.0, STEP) is not None:
                    return True               # the foot on its top or a walked surface of it
                u, tp = o.at(x + dx, y + dy, "under"), o.at(x + dx, y + dy, "top")
                inside += u is not None and u - STEP <= r <= tp
        if inside == 9:
            return True                       # set into it, all round (a post in a rock; not beside another post)
    return False


def end_meets(e: dict, others: list, ground) -> dict:
    """What one end line meets: the walked surface of another piece just past (or under) it, else the ground. Gives
    `along` (the gap past the end to the surface; negative: the surface runs under the end that far), `dz` (the
    surface's height less the end's), the ground at the end and the end's underside over it, and the verdict:
    meets <id> | rests on ground | on its own legs (legs_held) | buried end by N | short of <id> by N | step to <id> of N |
    mid-air by N."""
    x, y, z = e["at"]
    ox, oy = e["out"]
    half = e["width"] / 2 + CELL
    best = None
    for pid, o in others:
        if (o.lo[0] > x + LOOK_AHEAD + half or o.hi[0] < x - LOOK_AHEAD - half or o.lo[1] > y + LOOK_AHEAD + half
                or o.hi[1] < y - LOOK_AHEAD - half or o.lo[2] > z + 96 or o.hi[2] < z - 96):
            continue                                       # the first reject: its box is nowhere near the end
        W = walk_points(o)
        if not len(W):
            continue
        d = W[:, :2] - [x, y]
        along = d @ [ox, oy]
        side = np.abs(d @ [-oy, ox])
        m = (side <= half) & (along >= -MEET_BACK) & (along <= LOOK_AHEAD) & (np.abs(W[:, 2] - z) <= 96)
        if not m.any():
            continue
        a, zz = along[m], W[m, 2]
        gap = float(a.min())
        near = np.abs(a - max(gap, 0.0)) <= CELL
        if not near.any():
            near = np.abs(a - gap) <= CELL
        dz = float(zz[near][np.argmin(np.abs(zz[near] - z))]) - z
        score = max(gap, 0.0) + abs(dz)
        if best is None or score < best[0]:
            best = (score, pid, gap, dz)
    g = ground.height(x + ox * 4, y + oy * 4) if ground is not None else None
    under = e.get("under")
    under = z if under is None else under
    over = None if g is None else round(float(under - g), 1)
    row = {"at": e["at"], "width": e["width"], "ground": None if g is None else round(float(g), 1), "over_ground": over,
           "meets": None, "along": None, "dz": None}
    if best is not None:
        row.update(meets=best[1], along=round(best[2], 1), dz=round(best[3], 1))
    if best is not None and best[2] <= MEET_ALONG and abs(best[3]) <= STEP:
        v = f"meets {best[1]}"
    elif over is not None and -SINK <= over <= STEP:
        v = "rests on ground"
    elif over is not None and over > STEP and legs_held(e, others, ground):
        v = "on its own legs"
    elif over is not None and over < -SINK:
        v = f"buried end by {-over:.0f}"
    elif best is not None and best[2] > MEET_ALONG and abs(best[3]) <= STEP:
        v = f"short of {best[1]} by {best[2]:.0f}"
    elif best is not None:
        v = f"step to {best[1]} of {best[3]:.0f}"
    else:
        v = f"mid-air by {over:.0f}" if over is not None else "mid-air"
    row["verdict"] = v
    return row


CLEAR_WALK = 64.0      # a walk keeping this clear width beside what stands on it is not blocked
FLOOR_SHARE = 0.5      # a span this much under a body resting on it is that body's floor


def cover(s: Posed, o: Posed) -> dict | None:
    """What o covers of span s's walk at walking height (o's underside at most a person's height over the walk):
    `share` of the walk's cells covered; in the band along the span where it covers, `width` the share of the walk's
    width covered and `clear` the widest clear run left beside it (the walk's side extent less the covered one, either
    side); `across`: under CLEAR_WALK left there and open walk on both sides of the band along the span (a wall cut
    across the walked line). None when o covers none of it."""
    w = _shared(s, o)
    if w is None:
        return None
    sa, sb = w
    walk = ~np.isnan(s.walk)
    Wf, ou = s.walk[sa], o.under[sb]
    cov = np.zeros_like(walk)
    cov[sa] = ~np.isnan(Wf) & ~np.isnan(ou) & (ou <= Wf + 160.0)
    if not cov.any() or walk.sum() < 2:
        return None
    ii, jj = np.nonzero(walk)
    x, y = s.cell_xy(ii, jj)
    xy = np.stack([x, y], 1)
    c = xy.mean(0)
    ax = np.linalg.svd(xy - c, full_matrices=False)[2][0]
    t = (xy - c) @ ax
    sd = (xy - c) @ np.array([-ax[1], ax[0]])
    k = cov[ii, jj]
    t0, t1 = t[k].min(), t[k].max()
    band = (t >= t0 - CELL / 2) & (t <= t1 + CELL / 2)
    smin, smax = sd[band].min(), sd[band].max()
    cmin, cmax = sd[k].min(), sd[k].max()
    clear = max(cmin - smin, smax - cmax, 0.0)
    before, after = int((~k & (t < t0 - CELL)).sum()), int((~k & (t > t1 + CELL)).sum())
    return {"share": float(k.mean()), "width": float(min((cmax - cmin + CELL) / (smax - smin + CELL), 1.0)),
            "clear": float(clear), "across": bool(clear < CLEAR_WALK and before >= 2 and after >= 2)}


def joints(spans: list, pieces: list, ground, unit_of=None, walls=None, structures=None, name_of=None) -> list[dict]:
    """One row per end of every walked span (spans: [(id, Posed)]): what it meets and the verdict (end_meets); then,
    per span and piece of another unit: `spans overlap <id>` (another span overlapping it along its length);
    `crossed by wall <id>` (a wall or body cutting across its walked line, under CLEAR_WALK left, with open walk on
    both sides: `cover`); `runs into wall <id>` (one not resting on it blocking its walk at one end: a dead end);
    `floor of <id>` (a body resting on it, its floor within a STEP of the deck's ends, over FLOOR_SHARE of the walk or not
    cutting across the walked line: the house's floor, the rest a porch; not a fault);
    `stands on: <id>` (a piece resting on its walk leaving under CLEAR_WALK clear beside it) or `carries <id>` (one
    leaving that clear: not a fault), each saying what stands there, its share of the walk's width and the clear left.
    unit_of: piece id -> unit id; walls: ids of building bodies and wall parts; structures: the ids whose standing on
    a span is named (bodies, decks, steps, spans, walls; None: every piece); name_of: id -> what it is, for the row."""
    unit_of = unit_of or {}
    walls = walls or set()
    name_of = name_of or {}
    out = []
    span_ids = {i for i, _ in spans}
    for sid, s in spans:
        others = [(i, o) for i, o in pieces if i != sid]
        ends = s.ends() or []
        deck = [e["at"][2] for e in ends]
        for k, e in enumerate(ends):
            out.append({"span": sid, "unit": unit_of.get(sid), "end": "foot" if k == 0 else "head",
                        **end_meets(e, others, ground)})
        for i, o in others:
            if boxes_apart(s, o, STEP):
                continue
            same = unit_of.get(i) is not None and unit_of.get(i) == unit_of.get(sid)
            if same:
                continue
            row = {"span": sid, "unit": unit_of.get(sid), "end": "-", "on": i}
            if i in span_ids:
                ov = overlap(s, o, 8.0)
                if ov and i > sid and ov["cells"] >= 0.25 * min(int(s.occ.sum()), int(o.occ.sum())):
                    out.append({**row, "verdict": f"spans overlap {i}", "area": ov["area"]})
                continue
            if structures is not None and i not in structures and i not in walls:
                continue
            what = name_of.get(i)
            held = rests_on(o, s)
            cv = cover(s, o)
            if i in walls:
                ov = overlap(s, o, 8.0)
                fl = o.body().get("floor") if held and cv is not None else None
                floor = (fl is not None and bool(deck) and min(deck) - STEP <= fl <= max(deck) + STEP and cv["share"] >= 0.1
                         and (cv["share"] >= FLOOR_SHARE or not cv["across"]))
                cut = ov is not None and ov["cells"] >= 2 and cv is not None and cv["clear"] < CLEAR_WALK and not floor
                if cut and (cv["across"] or not held):
                    v = "crossed by wall" if cv["across"] else "runs into wall"
                    out.append({**row, "verdict": f"{v} {i}" + (f" ({what})" if what else ""), "area": ov["area"]})
                    continue
                if floor:
                    out.append({**row, "verdict": f"floor of {i}" + (f" ({what}, {cv['share'] * 100:.0f}% under it)"
                                                                      if what else f" ({cv['share'] * 100:.0f}% under it)"),
                                "share": round(cv["share"], 2)})
                    continue
            if not held:
                continue
            width, clear = (cv["width"], cv["clear"]) if cv else (0.0, None)
            blocked = clear is not None and clear < CLEAR_WALK
            note = ", ".join(x for x in (what, f"{width * 100:.0f}% of the walk's width",
                                         f"{clear:.0f} clear" if clear is not None else "") if x)
            out.append({**row, "verdict": f"{'stands on:' if blocked else 'carries'} {i} ({note})",
                        "width": round(width, 2), "clear": None if clear is None else round(clear)})
    return out


# ---------- helpers ----------
def _deck(z: np.ndarray, t: np.ndarray, sd: np.ndarray) -> np.ndarray:
    """Which walked points are the span's deck: the one walked surface running its length. Seeded in the middle third
    at the height level that spans the most 16-unit cells across, then followed slice by slice (CELL along the axis)
    out to both ends, each slice taking the points within DECK_TOL of the last deck height (a sagging deck rises to its
    ends, a stair climbs a riser a slice) that span at least a quarter of the seed's cells across; up to DECK_GAP
    empty slices (the gaps between planks) are crossed. Rails, rope tops and post caps above the deck and beams under
    it are left out; where nothing is found, every point is kept."""
    b = np.floor((t - t.min()) / CELL).astype(int)
    nb = int(b.max()) + 1
    sc = np.floor(sd / CELL).astype(int)
    q = np.round(z / 8.0).astype(int)
    seed = None
    for k in range(nb // 3, max(nb - nb // 3, nb // 3 + 1)):
        ik = np.flatnonzero(b == k)
        for v in np.unique(q[ik]):
            m = ik[np.abs(q[ik] - v) <= 1]
            n = len(np.unique(sc[m]))
            if seed is None or n > seed[0]:
                seed = (n, k, float(np.median(z[m])))
    if seed is None:
        return np.ones(len(z), bool)
    need = max(1, seed[0] // 4)
    keep = np.zeros(len(z), bool)
    for step in (1, -1):
        zprev, k, gap = seed[2], seed[1], 0
        while 0 <= k < nb:
            ik = np.flatnonzero(b == k)
            m = ik[np.abs(z[ik] - zprev) <= DECK_TOL]
            if len(m) and len(np.unique(sc[m])) >= need:
                keep[m] = True
                zprev, gap = float(np.median(z[m])), 0
            else:
                gap += 1
                if gap > DECK_GAP:
                    break
            k += step
    return keep if keep.sum() >= 3 else np.ones(len(z), bool)


def _label(m: np.ndarray) -> np.ndarray:
    """4-connected labels of a boolean grid."""
    from scipy import ndimage
    return ndimage.label(m)[0] if m.size else np.zeros(m.shape, int)


def _keep_big(F: np.ndarray, n: int) -> np.ndarray:
    m = ~np.isnan(F)
    if not m.any():
        return F
    lab = _label(m)
    cnt = np.bincount(lab.ravel())
    small = cnt < n
    small[0] = False
    out = F.copy()
    out[small[lab]] = np.nan
    return out


def _dilate(m: np.ndarray, r: int) -> np.ndarray:
    pad = np.pad(m, r)
    out = np.zeros_like(m)
    for di in range(2 * r + 1):
        for dj in range(2 * r + 1):
            out |= pad[di:di + m.shape[0], dj:dj + m.shape[1]]
    return out


def _plan_hull(P: np.ndarray) -> np.ndarray:
    """The cloud's plan as its convex hull's corners (exact: the cloud holds every vertex)."""
    if P is None or len(P) < 3:
        return np.zeros((0, 2), np.float32)
    try:
        from scipy.spatial import ConvexHull
        xy = np.asarray(P[:, :2], float)
        return xy[ConvexHull(xy).vertices].astype(np.float32)
    except Exception:  # noqa: BLE001  a degenerate (flat-in-plan) cloud: its extreme points
        xy = np.asarray(P[:, :2], float)
        return xy[[xy[:, 0].argmin(), xy[:, 0].argmax(), xy[:, 1].argmin(), xy[:, 1].argmax()]].astype(np.float32)


def _hull(pts: np.ndarray) -> list:
    pts = sorted(set(map(tuple, np.round(np.asarray(pts, float), 3))))
    if len(pts) <= 2:
        return pts
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])  # noqa: E704
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def warm(models, workers: int = 0) -> dict:
    """Build the cache for these models; returns {built, cached, unread, seconds}."""
    import time
    t = time.time()
    got = {"built": 0, "cached": 0, "unread": 0}
    for m in models:
        k = str(m).lower()
        key, _ = _glb_key(k)
        if key and (cache_dir() / f"{key}.npz").exists():
            got["cached"] += 1
        before = k in _UNREAD
        mod = model(k)
        if not mod.mesh and not before:
            got["unread"] += 1
        elif key and mod.mesh:
            got["built"] += 1
    got["built"] -= got["cached"]
    got["seconds"] = round(time.time() - t, 1)
    return got


def main(argv: list[str]) -> int:
    """python -m tools.places.shape <place>... : build the shape cache for every model the places draw."""
    import json
    from tools.places.look.scene import Scene
    for pl in argv:
        sc = Scene(pl)
        ms = sorted({str(p.get("model") or "").lower() for p in sc.pieces if p.get("model")})
        print(pl, len(ms), "models", json.dumps(warm(ms)))
    if _UNREAD:
        print("unread:", json.dumps(_UNREAD, indent=1))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
