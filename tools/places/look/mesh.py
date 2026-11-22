"""The built walkable mesh for the look tool: the navmesh the place's build wrote (navexport's per-space export),
split into islands (triangles joined across an edge), what stands on each island (door arrivals, street points),
whether a walk joins two points and, where it does not, where the mesh breaks between them.

Pure numbers here (tested on a small fixture mesh); verbs.py draws them and names the things."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

CLIMB = 32.0       # the navmesh's climb: a height step over this between two edges is a step no one walks
ON_TOL = 48.0      # a point this far over or under a triangle under it stands on it
GAP_K = 16         # the nearest points of the other island each edge point is weighed against
GAP_OPEN = 24.0    # two islands' edges further apart than this across the plan: a missing strip of triangles


class Mesh:
    def __init__(self, verts, tris, nb, kind=None, doors=None):
        self.V = np.asarray(verts, float).reshape(-1, 3)
        self.T = np.asarray(tris, int).reshape(-1, 3)
        self.nb = np.asarray(nb, int).reshape(-1, 3)
        self.kind = np.asarray(kind if kind is not None else [0] * len(self.T), int)
        self.doors = [(int(t), str(r)) for t, r in (doors or [])]
        self.C = self.V[self.T].mean(axis=1) if len(self.T) else np.zeros((0, 3))
        self.lab, self.count = _islands(self.nb)
        self.main = int(np.argmax(self.count)) if len(self.count) else -1

    def tri_at(self, x: float, y: float, z: float | None = None, tol: float = ON_TOL) -> tuple[int, float | None]:
        """The triangle under (x, y) whose height there is nearest z (any when z is None), and its height; (-1, None)
        when no triangle is under the point within tol of z."""
        if not len(self.T):
            return -1, None
        a, b, c = self.V[self.T[:, 0]], self.V[self.T[:, 1]], self.V[self.T[:, 2]]
        lo = np.minimum(np.minimum(a, b), c)
        hi = np.maximum(np.maximum(a, b), c)
        m = np.where((lo[:, 0] <= x) & (x <= hi[:, 0]) & (lo[:, 1] <= y) & (y <= hi[:, 1]))[0]
        best, bz = -1, None
        for i in m:
            h = _height_in(a[i], b[i], c[i], x, y)
            if h is None:
                continue
            if z is not None and abs(h - z) > tol:
                continue
            if best < 0 or (z is not None and abs(h - z) < abs(bz - z)) or (z is None and h > bz):
                best, bz = int(i), h
        return best, bz

    def island_of(self, x: float, y: float, z: float | None = None) -> int:
        t, _ = self.tri_at(x, y, z)
        return int(self.lab[t]) if t >= 0 else -1

    def door_islands(self) -> dict[str, int]:
        return {r: int(self.lab[t]) for t, r in self.doors if 0 <= t < len(self.T)}

    def boundary(self, island: int) -> np.ndarray:
        """The island's open edges, as segments (n, 2, 3)."""
        segs = []
        for i in np.where(self.lab == island)[0]:
            for k in range(3):
                if self.nb[i, k] < 0:
                    segs.append((self.V[self.T[i, k]], self.V[self.T[i, (k + 1) % 3]]))
        return np.asarray(segs, float).reshape(-1, 2, 3)

    def gap(self, ia: int, ib: int, near=None) -> dict | None:
        """Where islands ia and ib come nearest: the two open-edge points, the gap across the plan and the height
        step, and what kind of break it is: a height step (edges meet across the plan, too far apart in height), a
        missing strip (no triangles between edges apart across the plan). `near` (x, y): the break nearest it among
        those within 64 units of the closest."""
        A, B = self.boundary(ia), self.boundary(ib)
        if not len(A) or not len(B):
            return None
        pa, pb = _sample(A), _sample(B)
        # each of A's points against its nearest of B's in plan (a kd-tree: an island's edge is a million points and
        # every pair would not fit in memory); the cost adds half the height step
        from scipy.spatial import cKDTree
        k = min(GAP_K, len(pb))
        dist, idx = cKDTree(pb[:, :2]).query(pa[:, :2], k=k)
        dist, idx = dist.reshape(len(pa), k), idx.reshape(len(pa), k)
        cost = dist + 0.5 * np.abs(pa[:, None, 2] - pb[idx, 2])
        if near is not None:
            best = float(cost.min())
            mid = (pa[:, None, :2] + pb[idx, :2]) / 2
            far = np.hypot(mid[..., 0] - near[0], mid[..., 1] - near[1])
            cost = np.where(cost <= best + 64, far, np.inf)
        i, c = np.unravel_index(int(np.argmin(cost)), cost.shape)
        a, b = pa[i], pb[idx[i, c]]
        across, step = float(math.dist(a[:2], b[:2])), float(abs(a[2] - b[2]))
        what = "missing strip" if across > GAP_OPEN else "height step" if step > CLIMB else "seam unjoined"
        return {"from": [round(float(v)) for v in a], "to": [round(float(v)) for v in b],
                "at": [round(float(v)) for v in (a + b) / 2], "across": round(across), "step": round(step), "kind": what}


def _islands(nb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = len(nb)
    lab = -np.ones(n, int)
    k = 0
    for s in range(n):
        if lab[s] >= 0:
            continue
        lab[s] = k
        st = [s]
        while st:
            t = st.pop()
            for o in nb[t]:
                if 0 <= o < n and lab[o] < 0:
                    lab[o] = k
                    st.append(int(o))
        k += 1
    return lab, (np.bincount(lab, minlength=k) if n else np.zeros(0, int))


def _height_in(a, b, c, x, y) -> float | None:
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-9:
        return None
    l1 = ((b[1] - c[1]) * (x - c[0]) + (c[0] - b[0]) * (y - c[1])) / d
    l2 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / d
    l3 = 1 - l1 - l2
    if min(l1, l2, l3) < -1e-6:
        return None
    return float(l1 * a[2] + l2 * b[2] + l3 * c[2])


def _sample(segs: np.ndarray, step: float = 16.0) -> np.ndarray:
    out = []
    for p, q in segs:
        n = max(1, int(math.dist(p, q) // step))
        for t in np.linspace(0, 1, n + 1):
            out.append(p + (q - p) * t)
    return np.asarray(out, float)


# ---------- where the export is ----------
def find(place: str, out: Path) -> tuple[Path | None, Path | None]:
    """(the export, the build dir it is of): the newest of the place's own build (out/draft_check/<place>, written
    by draft check) and the shared build (out), made again by navexport when its plugin is newer."""
    from tools.places import navexport
    got = []
    for o in (out / "draft_check" / place, out):
        try:
            p = navexport.current(place, o)
        except Exception:  # noqa: BLE001  an unbuilt or half-built tree is just not a candidate
            p = None
        if p is not None and p.exists():
            # the newer BUILD wins (its plan's time), never the newer export: an old shared build's mesh is exported
            # again whenever asked and would otherwise outrank a fresh draft-check build
            plan = o / "shards" / place / "plan.json"
            got.append((plan.stat().st_mtime if plan.exists() else p.stat().st_mtime, p, o))
    if not got:
        return None, None
    _, p, o = max(got)
    return p, o


def stale(place_dir: Path, build: Path, place: str) -> dict:
    """The build's plan against the place files: stale when a place file is newer than the plan the mesh is of."""
    plan = build / "shards" / place / "plan.json"
    if not plan.exists():
        return {"stale": True, "why": "no plan of the build"}
    t = plan.stat().st_mtime
    newer = sorted(str(f.relative_to(place_dir)) for f in place_dir.rglob("*.json*") if f.stat().st_mtime > t)
    return {"stale": bool(newer), "built": plan.stat().st_mtime, "newer_files": newer[:8]}


def load(path: Path, space: str = "exterior") -> Mesh | None:
    d = json.loads(path.read_text())
    s = (d.get("spaces") or {}).get(space)
    if not s:
        return None
    return Mesh(s["verts"], s["tris"], s["nb"], s.get("kind"), s.get("doors"))


def colour(i: int, main: int) -> tuple[int, int, int]:
    """An island's colour: the main network green, the rest by a golden-angle hue walk (red kept for off-mesh)."""
    if i == main:
        return (40, 200, 90)
    import colorsys
    h = (0.12 + i * 0.618034) % 1.0
    if h < 0.05 or h > 0.95:
        h = 0.55
    r, g, b = colorsys.hsv_to_rgb(h, 0.85, 1.0)
    return int(r * 255), int(g * 255), int(b * 255)
