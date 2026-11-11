"""What of a placed thing stands in an actor's way, on the navmesh's own voxel grid.

The grid is the world's: column (i, j) covers x in [i cs, (i + 1) cs) and y in [j cs, (j + 1) cs). ArgoniaNav's cells
start on multiples of the voxel width, so its heightfield columns are these columns.

A thing blocks a column when its solid reaches into the band a body fills over the ground at the column's centre:
above the climb (lower is stepped over) and below the agent's height (higher is walked under). That is the rule
measured on Skyrim's own navmesh (vanilla.py, docs/research/nw-02-walk5-navmesh.md), and it is all the navmesh needs
of a placed thing: the collision is reduced to it here, once, and ArgoniaNav is handed blocked columns, never
triangles. The flora placer reads the same columns to keep a road's walking width clear (tools/newworld/place).

The solid of a collision mesh is its faces and what they enclose:
    faces    a face blocks every column it passes over where its height there (the face cut to the column's square)
             meets the band
    inside   a column whose centre the faces cross is solid between the crossings, bottom to top in pairs (in, out);
             with an odd count the lowest crossing is the top of a body open underneath (a rock's collision has no
             underside) and the column is solid from below up to it

    columns(tris, h, x0, ytop, step, cs, climb, height) -> (hit (H, W) uint8, i0, j0, faces in the band)
    runs(mask, i0, j0) -> (n, 3) int32 rows (j, first i, last i) of the set columns
"""
from __future__ import annotations

import math

import numpy as np

try:
    from numba import njit
except ImportError:  # numba (the venv has it) only makes it fast; the rule is the same without it

    def njit(*a, **k):
        return (lambda f: f) if not (a and callable(a[0])) else a[0]


@njit(cache=True)
def ground_at(h, x0, ytop, step, x, y):
    """The ground under a plan point: the mean of the quad's two triangulations (ArgoniaNav's Ground)."""
    rows, cols = h.shape
    c = (x - x0) / step
    r = (ytop - y) / step
    c0 = min(max(int(math.floor(c)), 0), cols - 2)
    r0 = min(max(int(math.floor(r)), 0), rows - 2)
    u = c - c0
    v = r - r0
    a = h[r0, c0]
    b = h[r0, c0 + 1]
    cc = h[r0 + 1, c0]
    d = h[r0 + 1, c0 + 1]
    z1 = a + u * (b - a) + v * (d - b) if u >= v else a + v * (cc - a) + u * (d - cc)
    z2 = a + u * (b - a) + v * (cc - a) if u + v <= 1 else d + (1 - u) * (cc - d) + (1 - v) * (b - d)
    return (z1 + z2) / 2


@njit(cache=True)
def _clip_z(t, xa, xb, ya, yb, P, Q):
    """The height range of triangle t over the square [xa, xb] x [ya, yb]: (it reaches the square, low, high)."""
    n = 3
    for k in range(3):
        P[k, 0] = t[k, 0]
        P[k, 1] = t[k, 1]
        P[k, 2] = t[k, 2]
    for k in range(4):
        axis = 0 if k < 2 else 1
        val = xa if k == 0 else (xb if k == 1 else (ya if k == 2 else yb))
        sgn = 1.0 if k % 2 == 0 else -1.0
        m = 0
        for a in range(n):
            b = a + 1 if a + 1 < n else 0
            da = sgn * (P[a, axis] - val)
            db = sgn * (P[b, axis] - val)
            if da >= 0:
                Q[m, 0] = P[a, 0]
                Q[m, 1] = P[a, 1]
                Q[m, 2] = P[a, 2]
                m += 1
            if (da > 0 and db < 0) or (da < 0 and db > 0):
                s = da / (da - db)
                Q[m, 0] = P[a, 0] + s * (P[b, 0] - P[a, 0])
                Q[m, 1] = P[a, 1] + s * (P[b, 1] - P[a, 1])
                Q[m, 2] = P[a, 2] + s * (P[b, 2] - P[a, 2])
                m += 1
        n = m
        if n == 0:
            return False, 0.0, 0.0
        for a in range(n):
            P[a, 0] = Q[a, 0]
            P[a, 1] = Q[a, 1]
            P[a, 2] = Q[a, 2]
    zlo = P[0, 2]
    zhi = P[0, 2]
    for a in range(1, n):
        zlo = min(zlo, P[a, 2])
        zhi = max(zhi, P[a, 2])
    return True, zlo, zhi


@njit(cache=True)
def columns(tris, h, x0, ytop, step, cs, climb, height):
    """The columns one thing blocks. `tris` (n, 3, 3) float64 world units, `h` the ground raster (row 0 north, its
    first sample at (x0, ytop), `step` apart). Returns the columns of the thing's plan box as (H, W) uint8 (row j0
    first, south to north; column i0 first), i0, j0, and how many of its faces lie in the band of some column."""
    n = tris.shape[0]
    xmin = tris[0, 0, 0]
    xmax = xmin
    ymin = tris[0, 0, 1]
    ymax = ymin
    for t in range(n):
        for k in range(3):
            xmin = min(xmin, tris[t, k, 0])
            xmax = max(xmax, tris[t, k, 0])
            ymin = min(ymin, tris[t, k, 1])
            ymax = max(ymax, tris[t, k, 1])
    i0 = int(math.floor(xmin / cs))
    j0 = int(math.floor(ymin / cs))
    W = int(math.floor(xmax / cs)) - i0 + 1
    H = int(math.floor(ymax / cs)) - j0 + 1
    g = np.empty((H, W))
    gmin = np.inf
    gmax = -np.inf
    for j in range(H):
        for i in range(W):
            g[j, i] = ground_at(h, x0, ytop, step, (i0 + i + 0.5) * cs, (j0 + j + 0.5) * cs)
            gmin = min(gmin, g[j, i])
            gmax = max(gmax, g[j, i])
    hit = np.zeros((H, W), np.uint8)
    P = np.empty((12, 3))
    Q = np.empty((12, 3))
    band = 0
    for t in range(n):
        ax, ay, az = tris[t, 0, 0], tris[t, 0, 1], tris[t, 0, 2]
        bx, by, bz = tris[t, 1, 0], tris[t, 1, 1], tris[t, 1, 2]
        cx, cy, cz = tris[t, 2, 0], tris[t, 2, 1], tris[t, 2, 2]
        tz0 = min(az, min(bz, cz))
        tz1 = max(az, max(bz, cz))
        if tz1 <= gmin + climb or tz0 >= gmax + height:
            continue
        band += 1
        ia = int(math.floor(min(ax, min(bx, cx)) / cs)) - i0
        ib = int(math.floor(max(ax, max(bx, cx)) / cs)) - i0
        ja = int(math.floor(min(ay, min(by, cy)) / cs)) - j0
        jb = int(math.floor(max(ay, max(by, cy)) / cs)) - j0
        den = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)  # twice the plan area, signed
        level = abs(den) > 1e-6
        zx = zy = e = 0.0
        sg = 1.0 if den > 0 else -1.0
        if level:
            zx = ((bz - az) * (cy - ay) - (cz - az) * (by - ay)) / den
            zy = ((cz - az) * (bx - ax) - (bz - az) * (cx - ax)) / den
            e = (abs(zx) + abs(zy)) * cs / 2
        for j in range(ja, jb + 1):
            ya = (j0 + j) * cs
            for i in range(ia, ib + 1):
                if hit[j, i]:
                    continue
                lo = g[j, i] + climb
                hi = g[j, i] + height
                if tz1 <= lo or tz0 >= hi:
                    continue
                xa = (i0 + i) * cs
                if level:
                    zc = az + zx * (xa + cs / 2 - ax) + zy * (ya + cs / 2 - ay)
                    if zc + e <= lo or zc - e >= hi:
                        continue  # the face's plane over the whole square misses the band
                    out = False  # the square's corner furthest inside each edge is outside it: the face misses the square
                    for k in range(3):
                        px, py = tris[t, k, 0], tris[t, k, 1]
                        qx, qy = tris[t, (k + 1) % 3, 0], tris[t, (k + 1) % 3, 1]
                        ex = sg * (qx - px)
                        ey = sg * (qy - py)
                        x = xa if ey > 0 else xa + cs
                        y = ya + cs if ex > 0 else ya
                        if ex * (y - py) - ey * (x - px) < 0:
                            out = True
                            break
                    if out:
                        continue
                ok, zl, zh = _clip_z(tris[t], xa, xa + cs, ya, ya + cs, P, Q)
                if ok and zh > lo and zl < hi:
                    hit[j, i] = 1
    # inside: the crossings of each open column's centre line, counted, then gathered and sorted
    cnt = np.zeros(H * W + 1, np.int64)
    zs = np.empty(0)
    fill = cnt
    for step_ in range(2):
        if step_ == 1:
            for k in range(H * W):
                cnt[k + 1] += cnt[k]
            zs = np.empty(cnt[H * W])
            fill = cnt[:H * W].copy()  # cnt[k] is now where column k's crossings start, cnt[k + 1] where they end
        for t in range(n):
            ax, ay, az = tris[t, 0, 0], tris[t, 0, 1], tris[t, 0, 2]
            bx, by, bz = tris[t, 1, 0], tris[t, 1, 1], tris[t, 1, 2]
            cx, cy, cz = tris[t, 2, 0], tris[t, 2, 1], tris[t, 2, 2]
            d = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(d) < 1e-6:
                continue  # an upright face crosses no column's centre line
            ia = max(0, int(math.ceil(min(ax, min(bx, cx)) / cs - 0.5)) - i0)
            ib = min(W - 1, int(math.floor(max(ax, max(bx, cx)) / cs - 0.5)) - i0)
            ja = max(0, int(math.ceil(min(ay, min(by, cy)) / cs - 0.5)) - j0)
            jb = min(H - 1, int(math.floor(max(ay, max(by, cy)) / cs - 0.5)) - j0)
            for j in range(ja, jb + 1):
                py = (j0 + j + 0.5) * cs
                for i in range(ia, ib + 1):
                    if hit[j, i]:
                        continue
                    px = (i0 + i + 0.5) * cs
                    l1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / d
                    l2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / d
                    l3 = 1 - l1 - l2
                    # a centre on a face's edge is taken by two of its three edges only, so two faces sharing it seldom both count
                    if l1 < 0 or l2 < 0 or l3 <= 0:
                        continue
                    k = j * W + i
                    if step_ == 0:
                        cnt[k + 1] += 1
                    else:
                        zs[fill[k]] = l1 * az + l2 * bz + l3 * cz
                        fill[k] += 1
    for j in range(H):
        for i in range(W):
            k = j * W + i
            a, b = cnt[k], cnt[k + 1]
            if hit[j, i] or b <= a:
                continue
            s = np.sort(zs[a:b])
            lo = g[j, i] + climb
            hi = g[j, i] + height
            q = 0
            if (b - a) % 2 == 1:
                if s[0] > lo:
                    hit[j, i] = 1
                q = 1
            while q + 1 < b - a and not hit[j, i]:
                if s[q + 1] > lo and s[q] < hi:
                    hit[j, i] = 1
                q += 2
    return hit, i0, j0, band


def runs(mask: np.ndarray, i0: int, j0: int) -> np.ndarray:
    """The set columns of a mask (row j0 first, column i0 first) as rows (j, first i, last i), in order."""
    m = np.zeros((mask.shape[0], mask.shape[1] + 2), np.int8)
    m[:, 1:-1] = mask != 0
    d = np.diff(m, axis=1)
    js, a = np.nonzero(d == 1)
    _, b = np.nonzero(d == -1)
    return np.stack([js + j0, a + i0, b - 1 + i0], 1).astype(np.int32)


def paint(mask: np.ndarray, i0: int, j0: int, rr: np.ndarray) -> None:
    """Set the columns of runs `rr` (rows j, first i, last i) that fall inside the mask (row j0, column i0 first)."""
    H, W = mask.shape
    rr = rr[(rr[:, 0] >= j0) & (rr[:, 0] < j0 + H) & (rr[:, 2] >= i0) & (rr[:, 1] < i0 + W)]
    if not len(rr):
        return
    d = np.zeros((H, W + 1), np.int32)
    np.add.at(d, (rr[:, 0] - j0, np.maximum(rr[:, 1] - i0, 0)), 1)
    np.add.at(d, (rr[:, 0] - j0, np.minimum(rr[:, 2] - i0 + 1, W)), -1)
    mask |= np.cumsum(d, axis=1)[:, :W] > 0
