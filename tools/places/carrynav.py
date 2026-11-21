"""A wholesale place's walking mesh from its source's own: the carried triangles (tools/places/draft/srcnav.py) cut
into our cells and joined to the generated mesh round them (docs/design/place-studio.md, Navmesh).

The plan is split into two regions, in plan only (every level of a deck and the ground under it falls on one side):

- CARRIED: inside the footprint (a polygon of DISK_SIDES round the anchor at the footprint radius), less every ZONE;
- GENERATED: everywhere else in the touched cells, and inside each zone. A zone is a convex polygon where the source's
  mesh no longer holds: a source piece deleted or moved (its true plan outline at the source pose, grown by MARGIN), a
  piece we added (its outline, grown), the new pose of a moved piece, and each carried triangle dropped as too steep
  once its ground vertices followed our ground (the triangle itself).

Each carried triangle is clipped to its cells and to the carried region; each generated triangle of a touched cell to
the generated region; then, per cell, the pieces are welded into one mesh (one vertex per spot), every T-junction on
an open edge is split at the vertex lying on it (the carried and generated sides meet along the region's boundary
with shared vertices; a cell's border edges are split where its neighbour has vertices, so join_seams pairs them edge
for edge), and neighbours are read from shared edges. Clipping never makes a sliver at a near miss: before cutting,
every vertex within SNAP of a boundary line is moved onto it (a cell line, the footprint, a zone).

Flags: a carried triangle keeps the source's PREFERRED and NO_LARGE_CREATURES; WATER follows OUR water (its middle
under our water level); door, edge-link and cover bits are cleared (finish_navmesh sets the doors from our pairs, and
join_seams the links). Pure numpy: no game data here."""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np

CELL = 4096.0
DISK_SIDES = 96
MARGIN = 64.0           # a zone is a changed piece's outline grown by this (two agent radii: the gap a mesh leaves round it)
SNAP = 8.0              # a vertex this near a boundary line is put on it before a cut: no sliver at a near miss
WELD_XY = 1.0           # two vertices this near in plan ...
WELD_Z = 48.0           # ... and this near in height are one: the carried and generated sides of a boundary differ by
#                         up to a climb and a detail error (32 + 16): the source mesh and Recast read a stair or a bank apart
ON_EDGE = 0.75          # a vertex this near an open edge in plan lies on it (a T-junction to split)
MIN_AREA = 0.5          # a triangle smaller in plan (units^2) is degenerate and dropped
SLIVER = 16.0           # reported: triangles under this plan area (units^2) left after the cut
MAX_SLOPE_DEG = 45.0    # tools.navmesh.params.MAX_SLOPE_DEG: Skyrim's walkable angle

# nvnm triangle flags (tools/navmesh/nvnm.py)
EDGE_BITS, DOOR, WATER, PREFERRED, NO_LARGE = 0x0007, 0x0400, 0x0200, 0x0040, 0x0010
KEEP_SRC = PREFERRED | NO_LARGE


# ---- convex polygons in plan, carrying height ------------------------------------------------------------------------

def ccw(poly2d) -> list:
    """The polygon's points counter-clockwise."""
    a = sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly2d, poly2d[1:] + poly2d[:1]))
    return list(poly2d) if a >= 0 else list(reversed(poly2d))


def planes(poly2d) -> list[tuple[float, float, float]]:
    """A convex counter-clockwise polygon's edges as half-planes a*x + b*y + c >= 0 (inside), unit normals."""
    out = []
    for p, q in zip(poly2d, poly2d[1:] + poly2d[:1]):
        a, b = -(q[1] - p[1]), q[0] - p[0]
        L = math.hypot(a, b)
        if L < 1e-9:
            continue
        out.append((a / L, b / L, -(a * p[0] + b * p[1]) / L))
    return out


def disk(centre, r: float, n: int = DISK_SIDES) -> list:
    return [(centre[0] + r * math.cos(2 * math.pi * i / n), centre[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def cell_box(c) -> list:
    x0, y0 = c[0] * CELL, c[1] * CELL
    return [(x0, y0), (x0 + CELL, y0), (x0 + CELL, y0 + CELL), (x0, y0 + CELL)]


def grow(poly2d, d: float = MARGIN) -> list:
    """The convex hull of the polygon grown by d (each corner by an octagon)."""
    pts = [(p[0] + d * math.cos(k * math.pi / 4), p[1] + d * math.sin(k * math.pi / 4)) for p in poly2d for k in range(8)]
    return hull(pts)


def hull(pts) -> list:
    pts = sorted(set((round(float(p[0]), 3), round(float(p[1]), 3)) for p in pts))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
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


def _side(h, p) -> float:
    return h[0] * p[0] + h[1] * p[1] + h[2]


def _cut(p, q, h) -> tuple:
    if p > q:                       # the same point whichever way round the edge is walked (shared edges agree)
        p, q = q, p
    dp, dq = _side(h, p), _side(h, q)
    t = dp / (dp - dq)
    return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]), p[2] + t * (q[2] - p[2]))


def area2(poly) -> float:
    return sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))


def clip(poly, h):
    """The part of a convex polygon (points (x, y, z)) on the inside of half-plane h; None when nothing is."""
    if poly is None:
        return None
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp, dq = _side(h, p), _side(h, q)
        if dp >= 0:
            out.append(p)
        if (dp > 0 and dq < 0) or (dp < 0 and dq > 0):
            out.append(_cut(p, q, h))
    ded = []
    for p in out:
        if not ded or (abs(p[0] - ded[-1][0]) > 1e-6 or abs(p[1] - ded[-1][1]) > 1e-6):
            ded.append(p)
    if len(ded) > 1 and abs(ded[0][0] - ded[-1][0]) <= 1e-6 and abs(ded[0][1] - ded[-1][1]) <= 1e-6:
        ded.pop()
    if len(ded) < 3 or abs(area2(ded)) < 2 * 1e-3:
        return None
    return ded


def intersect(poly, hs):
    for h in hs:
        poly = clip(poly, h)
        if poly is None:
            return None
    return poly


def minus(poly, hs) -> list:
    """A convex polygon less a convex region (its half-planes): convex pieces, disjoint."""
    if intersect(poly, hs) is None:     # untouched: whole (never cut along a far edge's line)
        return [poly]
    pieces, rest = [], poly
    for h in hs:
        o = clip(rest, (-h[0], -h[1], -h[2]))
        if o is not None:
            pieces.append(o)
        rest = clip(rest, h)
        if rest is None:
            break
    return pieces


def _bbox(poly) -> tuple:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _overlap(a, b) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


class Region:
    """The carried region: inside `outer` (convex), outside every zone (convex)."""

    def __init__(self, outer, zones=()):
        self.outer = ccw(list(outer))
        self.outer_h = planes(self.outer)
        self.zones = [ccw(list(z)) for z in zones if len(z) >= 3]
        self.zone_h = [planes(z) for z in self.zones]
        self.zone_box = [_bbox(z) for z in self.zones]

    def segments(self) -> list:
        segs = []
        for poly in [self.outer] + self.zones:
            segs += list(zip(poly, poly[1:] + poly[:1]))
        return segs

    def carried(self, poly) -> list:
        p = intersect(poly, self.outer_h)
        if p is None:
            return []
        pieces = [p]
        for h, bb in zip(self.zone_h, self.zone_box):
            nxt = []
            for q in pieces:
                nxt += minus(q, h) if _overlap(_bbox(q), bb) else [q]
            pieces = nxt
        return pieces

    def generated(self, poly) -> list:
        out = minus(poly, self.outer_h)
        inside = intersect(poly, self.outer_h)
        if inside is None:
            return out
        bbi = _bbox(inside)
        for k, (h, bb) in enumerate(zip(self.zone_h, self.zone_box)):
            if not _overlap(bbi, bb):
                continue
            q = intersect(inside, h)
            if q is None:
                continue
            pieces = [q]
            for j in range(k):          # a spot two zones share is generated once
                if _overlap(_bbox(q), self.zone_box[j]):
                    pieces = [r for p in pieces for r in minus(p, self.zone_h[j])]
            out += pieces
        if self.cover is not None:      # a hole in the source's mesh where our ground is walkable: generated
            free = [inside]
            for h, bb in zip(self.zone_h, self.zone_box):
                free = [r for p in free for r in (minus(p, h) if _overlap(_bbox(p), bb) else [p])]
            zlo, zhi = min(q[2] for q in inside) - COVER_DZ, max(q[2] for q in inside) + COVER_DZ
            for i in self._covering(bbi):
                h, bb, lo, hi = self.cover[i]
                if hi < zlo or lo > zhi:    # a deck far over the ground (or the ground far under it) covers nothing
                    continue
                free = [r for p in free for r in (minus(p, h) if _overlap(_bbox(p), bb) else [p])]
                if not free:
                    break
            # the cut splits what is left into wedges: judged together, a hole is a share of the triangle; a strip
            # along the source's edge is a scrap of it, kept only where it is thick
            share = sum(abs(area2(p)) for p in free) / max(abs(area2(inside)), 1e-9)
            out += [p for p in free if share >= HOLE_SHARE or thick(p)]
        return out

    cover = None

    def set_cover(self, tris) -> None:
        """The carried triangles: where none lies at a generated triangle's level (within COVER_DZ) inside the footprint,
        out of every zone, the generated mesh fills (a spot the source left unwalked that our ground makes walkable: a
        bank the edge band raised, dry ground under a walkway over the source's water)."""
        self.cover = []
        grid: dict = defaultdict(list)
        for t in tris:
            p = ccw([(q[0], q[1]) for q in t])
            if abs(area2(p)) < 1e-6:
                continue
            bb = _bbox(p)
            i = len(self.cover)
            self.cover.append((planes(p), bb, min(q[2] for q in t), max(q[2] for q in t)))
            for gx in range(math.floor(bb[0] / 256), math.floor(bb[2] / 256) + 1):
                for gy in range(math.floor(bb[1] / 256), math.floor(bb[3] / 256) + 1):
                    grid[(gx, gy)].append(i)
        self._grid = grid

    def _covering(self, bb) -> list:
        got = set()
        for gx in range(math.floor(bb[0] / 256), math.floor(bb[2] / 256) + 1):
            for gy in range(math.floor(bb[1] / 256), math.floor(bb[3] / 256) + 1):
                got.update(self._grid.get((gx, gy), ()))
        return sorted(got)


COVER_DZ = 64.0        # a carried triangle covers a generated one within this in height (two climbs)
HOLE_SHARE = 0.3       # a generated triangle a third or more of which no carried triangle covers lies in a hole: kept
HOLE_THICK = 16.0      # a scrap of a mostly covered one is kept when at least this thick (2 area / perimeter): the
#                        strips between the source's edge and Recast's along a wall are not holes


def thick(poly) -> bool:
    P = sum(math.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(poly, poly[1:] + poly[:1]))
    return P > 0 and abs(area2(poly)) / P >= HOLE_THICK


# ---- snapping, welding, T-junctions ------------------------------------------------------------------------------------

def snap(V: np.ndarray, segs, fixed: np.ndarray | None = None, tol: float = SNAP) -> int:
    """Move every vertex within tol of a boundary segment onto it (onto its end when within tol of that), in place;
    `fixed` vertices are never moved. Returns how many moved."""
    if not len(V) or not segs:
        return 0
    moved = np.zeros(len(V), bool)
    free = np.ones(len(V), bool) if fixed is None else ~fixed
    for a, b in segs:
        a = np.asarray(a[:2], float)
        b = np.asarray(b[:2], float)
        d = b - a
        L2 = float(d @ d)
        if L2 < 1e-12:
            continue
        lo, hi = np.minimum(a, b) - tol, np.maximum(a, b) + tol
        near = free & (V[:, 0] >= lo[0]) & (V[:, 0] <= hi[0]) & (V[:, 1] >= lo[1]) & (V[:, 1] <= hi[1])
        if not near.any():
            continue
        idx = np.flatnonzero(near)
        P = V[idx, :2]
        for e in (a, b):
            de = np.hypot(P[:, 0] - e[0], P[:, 1] - e[1])
            on = (de <= tol) & (de > 0)
            V[idx[on], 0], V[idx[on], 1] = e[0], e[1]
            moved[idx[on]] = True
        P = V[idx, :2]
        t = ((P - a) @ d) / L2
        proj = a + np.clip(t, 0, 1)[:, None] * d
        dist = np.hypot(*(P - proj).T)
        on = (t > 0) & (t < 1) & (dist <= tol) & (dist > 0)
        V[idx[on], 0], V[idx[on], 1] = proj[on, 0], proj[on, 1]
        moved[idx[on]] = True
    return int(moved.sum())


def snap_cell_lines(V: np.ndarray, tol: float = SNAP) -> int:
    n = 0
    for ax in (0, 1):
        line = np.round(V[:, ax] / CELL) * CELL
        on = (np.abs(V[:, ax] - line) <= tol) & (V[:, ax] != line)
        V[on, ax] = line[on]
        n += int(on.sum())
    return n


class Mesh:
    """One cell's triangles while they are assembled: welded vertices, triangles with flags."""

    def __init__(self):
        self.V: list[list[float]] = []
        self.T: list[list[int]] = []
        self.F: list[int] = []
        self.tag: list[int] = []
        self._ix: dict = defaultdict(list)

    def vert(self, p) -> int:
        k = (round(p[0] / WELD_XY), round(p[1] / WELD_XY))
        best, bd = -1, WELD_Z
        for kk in ((k[0] + dx, k[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            for i in self._ix.get(kk, ()):
                v = self.V[i]
                if abs(v[0] - p[0]) <= WELD_XY and abs(v[1] - p[1]) <= WELD_XY and abs(v[2] - p[2]) <= bd:
                    best, bd = i, abs(v[2] - p[2])
        if best >= 0:
            return best
        self.V.append([float(p[0]), float(p[1]), float(p[2])])
        self._ix[k].append(len(self.V) - 1)
        return len(self.V) - 1

    def add_poly(self, poly, flags: int, tag: int = 0) -> None:
        ids = []
        for p in poly:
            i = self.vert(p)
            if not ids or ids[-1] != i:
                ids.append(i)
        if len(ids) > 1 and ids[0] == ids[-1]:
            ids.pop()
        if len(ids) < 3:
            return
        if len(ids) == 3 or not self._flat_corner(ids):
            tris = [[ids[0], ids[j], ids[j + 1]] for j in range(1, len(ids) - 1)]      # a convex polygon: a fan
        else:                                  # a corner on a straight run: a fan from the middle (no flat triangle)
            c = np.mean([self.V[i] for i in ids], axis=0)
            self.V.append([float(c[0]), float(c[1]), float(c[2])])
            ci = len(self.V) - 1
            tris = [[ci, ids[j], ids[(j + 1) % len(ids)]] for j in range(len(ids))]
        for t in tris:
            if len(set(t)) == 3:
                self.T.append(t)
                self.F.append(int(flags))
                self.tag.append(tag)

    def _flat_corner(self, ids) -> bool:
        n = len(ids)
        for j in range(n):
            a, b, c = self.V[ids[j - 1]], self.V[ids[j]], self.V[ids[(j + 1) % n]]
            ux, uy, vx, vy = b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]
            if abs(ux * vy - uy * vx) <= 0.02 * math.hypot(ux, uy) * math.hypot(vx, vy):
                return True
        return False

    def plan_area(self, t) -> float:
        a, b, c = (self.V[i] for i in t)
        return 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))

    def edges(self) -> dict:
        use: dict = defaultdict(list)
        for ti, t in enumerate(self.T):
            for k in range(3):
                use[(min(t[k], t[(k + 1) % 3]), max(t[k], t[(k + 1) % 3]))].append((ti, k))
        return use


def collapse_short(m: Mesh, length: float = SNAP, cell=None) -> int:
    """Merge the two ends of every edge shorter than `length` in plan (and within WELD_Z in height) where no triangle
    round the end that goes would flip or fall under MIN_AREA: the short edges a cut leaves where a boundary's corner
    passes near a triangle's edge. A vertex on the cell's border never moves (the cell beside it must find it).
    Returns how many vertices went."""
    def fixed(i):
        if cell is None:
            return False
        v = m.V[i]
        x0, y0 = cell[0] * CELL, cell[1] * CELL
        return abs(v[0] - x0) < 0.5 or abs(v[0] - x0 - CELL) < 0.5 or abs(v[1] - y0) < 0.5 or abs(v[1] - y0 - CELL) < 0.5

    def area(t):
        a, b, c = (m.V[i] for i in t)
        return 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    gone = 0
    for _ in range(4):
        around: dict = defaultdict(set)
        for ti, t in enumerate(m.T):
            for i in t:
                around[i].add(ti)
        dead: set = set()
        moved: set = set()
        for (u, w) in list(m.edges()):
            if u in moved or w in moved:
                continue
            a, b = m.V[u], m.V[w]
            if math.hypot(a[0] - b[0], a[1] - b[1]) >= length or abs(a[2] - b[2]) > WELD_Z:
                continue
            fu, fw = fixed(u), fixed(w)
            if fu and fw:
                continue
            keep, drop = (w, u) if fw else (u, w)
            # the link condition: the two ends' common neighbours are only the corners opposite the edge (else the
            # merge folds two triangles onto one)
            live_u = [m.T[ti] for ti in around[u] if ti not in dead]
            live_w = [m.T[ti] for ti in around[w] if ti not in dead]
            nu = {i for t in live_u for i in t} - {u}
            nw = {i for t in live_w for i in t} - {w}
            opp = {i for t in live_u if w in t for i in t} - {u, w}
            if (nu & nw) - opp:
                continue
            ok = True
            for ti in around[drop]:
                if ti in dead:
                    continue
                t = m.T[ti]
                if keep in t:
                    continue
                nt = [keep if i == drop else i for i in t]
                if area(nt) < MIN_AREA or (area(nt) > 0) != (area(t) > 0):
                    ok = False
                    break
            if not ok:
                continue
            for ti in list(around[drop]):
                if ti in dead:
                    continue
                t = m.T[ti]
                if keep in t:
                    dead.add(ti)
                    continue
                m.T[ti] = [keep if i == drop else i for i in t]
                around[keep].add(ti)
            moved |= {u, w}
            gone += 1
        if not moved:
            break
        keep_t = [ti for ti in range(len(m.T)) if ti not in dead]
        m.T = [m.T[i] for i in keep_t]
        m.F = [m.F[i] for i in keep_t]
        m.tag = [m.tag[i] for i in keep_t]
    return gone


def unsplit_border(m: Mesh, cell, sides: dict) -> int:
    """On each border side of `cell` whose neighbour is not rebuilt (`sides`: (axis, line value) -> the neighbour's
    border vertices there), take back every vertex of ours the neighbour does not have: merged into the next vertex
    along the line where nothing flips. The neighbour's triangles and the links into them stay as they are, and our
    border then matches its edge for edge (a cut through a big generated triangle leaves such points on its edge).
    Returns how many went."""
    def area(t):
        a, b, c = (m.V[i] for i in t)
        return 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    gone = 0
    for (ax, line), pts in sides.items():
        theirs = {round(float(p[1 - ax]), 1) for p in pts}
        for _ in range(64):
            on = sorted((m.V[i][1 - ax], i) for i in {i for t in m.T for i in t} if abs(m.V[i][ax] - line) < 0.5)
            extra = [(u, i) for u, i in on if round(u, 1) not in theirs]
            if not extra:
                break
            around: dict = defaultdict(list)
            for ti, t in enumerate(m.T):
                for i in t:
                    around[i].append(ti)
            done = False
            for u, v in extra:
                k = [j for j, (_, i) in enumerate(on) if i == v][0]
                for j in (k - 1, k + 1):
                    if not 0 <= j < len(on):
                        continue
                    keep = on[j][1]
                    if not any(keep in m.T[ti] for ti in around[v]):
                        continue
                    ok = True
                    for ti in around[v]:
                        t = m.T[ti]
                        if keep in t:
                            continue
                        nt = [keep if i == v else i for i in t]
                        if area(nt) <= 0 or len(set(nt)) < 3:
                            ok = False
                            break
                    if not ok:
                        continue
                    dead = {ti for ti in around[v] if keep in m.T[ti]}
                    for ti in around[v]:
                        if ti not in dead:
                            m.T[ti] = [keep if i == v else i for i in m.T[ti]]
                    keep_t = [ti for ti in range(len(m.T)) if ti not in dead]
                    m.T = [m.T[i] for i in keep_t]
                    m.F = [m.F[i] for i in keep_t]
                    m.tag = [m.tag[i] for i in keep_t]
                    gone += 1
                    done = True
                    break
                if done:
                    break
            if not done:
                break
    return gone


def drop_flat(m: Mesh) -> int:
    """Remove every flat triangle: under MIN_AREA in plan, or a corner within ON_EDGE of the edge across from it (a
    needle a cut leaves along a near-tangent boundary). The hole it leaves is closed by splitting the neighbour's long
    edge at that corner (fix_t_junctions). Returns how many went."""
    keep = []
    for ti, t in enumerate(m.T):
        P = [m.V[i] for i in t]
        a2 = (P[1][0] - P[0][0]) * (P[2][1] - P[0][1]) - (P[2][0] - P[0][0]) * (P[1][1] - P[0][1])
        flat = abs(a2) < 2 * MIN_AREA
        if not flat:
            for k in range(3):
                p, q = P[k], P[(k + 1) % 3]
                L = math.hypot(q[0] - p[0], q[1] - p[1])
                if L > 0 and abs(a2) / L <= ON_EDGE:       # the third corner's distance to the line pq
                    flat = True
                    break
        if not flat:
            keep.append(ti)
    gone = len(m.T) - len(keep)
    m.T = [m.T[i] for i in keep]
    m.F = [m.F[i] for i in keep]
    m.tag = [m.tag[i] for i in keep]
    return gone


def _splits(m: Mesh, extra: list) -> dict:
    """{triangle: {edge k: [(t along the edge, vertex index or a point to add)]}}: every vertex of the mesh (or point
    of `extra`, a neighbour cell's border vertices) lying on an open edge's inside."""
    V = np.asarray(m.V, float) if m.V else np.zeros((0, 3))
    pts = [(i, V[i]) for i in range(len(V))] + [(None, np.asarray(p, float)) for p in extra]
    grid: dict = defaultdict(list)
    G = 64.0
    for i, p in pts:
        grid[(math.floor(p[0] / G), math.floor(p[1] / G))].append((i, p))
    out: dict = defaultdict(lambda: defaultdict(list))
    for (u, w), uses in m.edges().items():
        if len(uses) != 1:
            continue
        ti, k = uses[0]
        a, b = V[m.T[ti][k]], V[m.T[ti][(k + 1) % 3]]
        d = b[:2] - a[:2]
        L2 = float(d @ d)
        if L2 < 1e-9:
            continue
        x0, y0 = math.floor((min(a[0], b[0]) - ON_EDGE) / G), math.floor((min(a[1], b[1]) - ON_EDGE) / G)
        x1, y1 = math.floor((max(a[0], b[0]) + ON_EDGE) / G), math.floor((max(a[1], b[1]) + ON_EDGE) / G)
        seen = set()
        for gx in range(x0, x1 + 1):
            for gy in range(y0, y1 + 1):
                for i, p in grid.get((gx, gy), ()):
                    if i in (u, w) or (i is not None and i in seen):
                        continue
                    t = float((p[:2] - a[:2]) @ d) / L2
                    if not 1e-4 < t < 1 - 1e-4:
                        continue
                    q = a[:2] + t * d
                    if math.hypot(p[0] - q[0], p[1] - q[1]) > ON_EDGE:
                        continue
                    z = a[2] + t * (b[2] - a[2])
                    if abs(p[2] - z) > WELD_Z:
                        continue
                    if i is not None:
                        seen.add(i)
                        out[ti][k].append((t, i))
                    else:
                        out[ti][k].append((t, (float(q[0]), float(q[1]), float(z))))
    return out


def fix_t_junctions(m: Mesh, extra: list = (), rounds: int = 64) -> int:
    """Split every open edge at each vertex lying on it (and at `extra` points: a neighbour cell's border vertices),
    one edge per triangle per round, the triangle (a, b, c) with points p1..pn along ab fanned from c into
    (a, p1, c), (p1, p2, c) ... (pn, b, c), until none is left. Returns how many splits were made."""
    total = 0
    for _ in range(rounds):
        sp = _splits(m, list(extra))
        if not sp:
            break
        newT, newF, newG = [], [], []
        for ti, t in enumerate(m.T):
            s = sp.get(ti)
            if not s:
                newT.append(t)
                newF.append(m.F[ti])
                newG.append(m.tag[ti])
                continue
            k = max(s, key=lambda kk: len(s[kk]))    # the edge with the most points: all of them at once
            a, b, c = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
            run = [a]
            for _, x in sorted(s[k], key=lambda r: r[0]):
                i = x if isinstance(x, int) else m.vert(x)
                if i not in t and i not in run:
                    run.append(i)
            run.append(b)
            if len(run) == 2:
                newT.append(t)
                newF.append(m.F[ti])
                newG.append(m.tag[ti])
                continue
            for q in range(len(run) - 1):          # a fan from the corner across the split edge
                newT.append([run[q], run[q + 1], c])
                newF.append(m.F[ti])
                newG.append(m.tag[ti])
            total += len(run) - 2
        m.T, m.F, m.tag = newT, newF, newG
    return total


def finish_cell(m: Mesh) -> dict:
    """Drop degenerate triangles (plan area under MIN_AREA), orient every triangle counter-clockwise in plan, read
    neighbours from shared edges. {verts (n,3), tris [(v0,v1,v2)], edges [(e0,e1,e2)], flags, tags, stats}."""
    keep = []
    dropped = 0
    for ti, t in enumerate(m.T):
        a = m.plan_area(t)
        if abs(a) < 1e-3:                   # zero area only: a small one dropped would open a hole
            dropped += 1
            continue
        keep.append((t if a > 0 else [t[0], t[2], t[1]], m.F[ti], m.tag[ti]))
    used = sorted({i for t, _, _ in keep for i in t})
    remap = {o: n for n, o in enumerate(used)}
    V = np.asarray([m.V[i] for i in used], np.float32).reshape(-1, 3)
    T = [[remap[i] for i in t] for t, _, _ in keep]
    use: dict = defaultdict(list)
    for ti, t in enumerate(T):
        for k in range(3):
            use[(min(t[k], t[(k + 1) % 3]), max(t[k], t[(k + 1) % 3]))].append((ti, k))
    E = [[-1, -1, -1] for _ in T]
    nonmanifold = 0
    for uses in use.values():
        if len(uses) == 2:
            (a, ka), (b, kb) = uses
            E[a][ka], E[b][kb] = b, a
        elif len(uses) > 2:
            nonmanifold += 1
    areas = [abs(0.5 * ((V[t[1]][0] - V[t[0]][0]) * (V[t[2]][1] - V[t[0]][1])
                        - (V[t[2]][0] - V[t[0]][0]) * (V[t[1]][1] - V[t[0]][1]))) for t in T]
    return {"verts": V, "tris": T, "edges": E, "flags": [f for _, f, _ in keep], "tags": [g for _, _, g in keep],
            "stats": {"tris": len(T), "degenerate_dropped": dropped, "nonmanifold_edges": nonmanifold,
                      "slivers": sum(1 for a in areas if a < SLIVER), "min_area": round(min(areas), 2) if areas else None,
                      "open_edges": sum(1 for u in use.values() if len(u) == 1)}}


def t_junctions(cell: dict) -> int:
    """How many vertices lie inside an open edge of a finished cell (zero once fixed)."""
    m = Mesh()
    m.V = [list(map(float, v)) for v in cell["verts"]]
    m.T = [list(t) for t in cell["tris"]]
    m.F = list(cell["flags"])
    m.tag = list(cell["tags"])
    return sum(len(v) for s in _splits(m, []).values() for v in s.values())


# ---- the carried triangles' own rules --------------------------------------------------------------------------------

def slope_deg(tri) -> float:
    a, b, c = (np.asarray(p, float) for p in tri)
    n = np.cross(b - a, c - a)
    L = float(np.linalg.norm(n))
    if L < 1e-9:
        return 90.0
    return math.degrees(math.acos(min(1.0, abs(float(n[2])) / L)))


def water_flag(flags: int, tri, water) -> int:
    """WATER as OUR water has it: set when the triangle's middle is under the water's level there."""
    f = int(flags) & ~WATER
    c = np.mean(np.asarray(tri, float), axis=0)
    w = water(float(c[0]), float(c[1])) if water else None
    return f | WATER if w is not None and c[2] < w else f


def build_cells(carried: list, generated: dict, region: Region, water=None, neighbours: dict | None = None) -> dict:
    """The touched cells' meshes, cut, joined and finished.

    carried    [(tri (3x3), flags, tag)]: the source's triangles in our coordinates (tag 0 the town, k a moved unit)
    generated  {cell: [(tri, flags)]}: the generator's triangles of every touched cell
    region     the carried region (Region)
    water      water(x, y) -> our level or None
    neighbours {cell: [(x, y, z)]}: the border vertices of the cells round them that are not rebuilt here

    Returns {cell: finish_cell dict} for every cell that holds a triangle."""
    segs = region.segments()
    CV = np.asarray([p for t, _, _ in carried for p in t], float).reshape(-1, 3)
    snapped = snap(CV, segs) + snap_cell_lines(CV)
    carried = [(CV[3 * i:3 * i + 3].tolist(), f, g) for i, (_, f, g) in enumerate(carried)]
    region.set_cover([t for t, _, g in carried if g == 0])
    gen = {}
    for c, rows in generated.items():
        GV = np.asarray([p for t, _ in rows for p in t], float).reshape(-1, 3)
        x0, y0 = c[0] * CELL, c[1] * CELL
        on_line = (np.abs(GV[:, 0] - x0) < 0.5) | (np.abs(GV[:, 0] - x0 - CELL) < 0.5) | \
                  (np.abs(GV[:, 1] - y0) < 0.5) | (np.abs(GV[:, 1] - y0 - CELL) < 0.5) if len(GV) else np.zeros(0, bool)
        snapped += snap(GV, segs, fixed=on_line)
        gen[c] = [(GV[3 * i:3 * i + 3].tolist(), f) for i, (_, f) in enumerate(rows)]
    meshes: dict = defaultdict(Mesh)
    for tri, flags, tag in carried:
        poly = [tuple(p) for p in tri]
        if area2(poly) < 0:
            poly = poly[::-1]
        f = water_flag(int(flags) & KEEP_SRC, tri, water)
        x0, y0, x1, y1 = _bbox(poly)
        for cx in range(math.floor(x0 / CELL), math.floor(x1 / CELL) + 1):
            for cy in range(math.floor(y0 / CELL), math.floor(y1 / CELL) + 1):
                q = intersect(poly, planes(cell_box((cx, cy))))
                if q is None:
                    continue
                # a moved unit's own triangles (tag > 0) stand where the unit now is, in its zone: cut by cells only
                for piece in (region.carried(q) if tag == 0 else [q]):
                    meshes[(cx, cy)].add_poly(piece, f, tag)
    for c, rows in gen.items():
        for tri, flags in rows:
            poly = [tuple(p) for p in tri]
            if area2(poly) < 0:
                poly = poly[::-1]
            for piece in region.generated(poly):
                meshes[c].add_poly(piece, int(flags) & ~(EDGE_BITS | DOOR) & 0xFFFF, -1)
    out = finish_cells(meshes, neighbours)
    for c in out:
        out[c]["stats"]["snapped"] = snapped
    return out


def finish_cells(meshes: dict, neighbours: dict | None = None) -> dict:
    """Cells of welded pieces finished as one mesh each: T-junctions split (a cell's border at the vertices of the cells
    beside it, rebuilt here or not: `neighbours`), short edges merged, flat triangles dropped, borders a neighbour does
    not split unsplit, neighbours read. Returns {cell: finish_cell dict} for every cell that holds a triangle."""
    # each cell's border vertices, so the cells beside it split their border edges at them
    border: dict = defaultdict(list)
    for c, m in meshes.items():
        for v in m.V:
            border[c].append(v)
    for c, pts in (neighbours or {}).items():
        border[c] += [list(p) for p in pts]
    out = {}
    splits = collapsed = unsplit = 0
    for c in sorted(meshes):
        m = meshes[c]
        x0, y0 = c[0] * CELL, c[1] * CELL
        extra = []
        for o in ((c[0] - 1, c[1]), (c[0] + 1, c[1]), (c[0], c[1] - 1), (c[0], c[1] + 1)):
            for v in border.get(o, ()):
                if (abs(v[0] - x0) < 0.5 or abs(v[0] - x0 - CELL) < 0.5) and y0 - 0.5 <= v[1] <= y0 + CELL + 0.5 or \
                   (abs(v[1] - y0) < 0.5 or abs(v[1] - y0 - CELL) < 0.5) and x0 - 0.5 <= v[0] <= x0 + CELL + 0.5:
                    extra.append(v)
        splits += fix_t_junctions(m, extra)
        collapsed += collapse_short(m, cell=c)
        for _ in range(8):                        # a flat triangle goes; its long edge's neighbour is split instead
            flats = drop_flat(m)
            splits += fix_t_junctions(m, extra)
            if not flats:
                break
        sides = {}
        for o, ax, line in (((c[0] - 1, c[1]), 0, x0), ((c[0] + 1, c[1]), 0, x0 + CELL),
                            ((c[0], c[1] - 1), 1, y0), ((c[0], c[1] + 1), 1, y0 + CELL)):
            if o in (neighbours or {}):
                sides[(ax, line)] = [p for p in neighbours[o] if abs(p[ax] - line) < 0.5]
        unsplit += unsplit_border(m, c, sides)
        got = finish_cell(m)
        if got["tris"]:
            out[c] = got
    for c in out:
        out[c]["stats"]["splits"] = splits
        out[c]["stats"]["collapsed"] = collapsed
        out[c]["stats"]["unsplit"] = unsplit
    return out


def joined_tags(out: dict) -> set:
    """The moved units' tags (> 0) whose triangles share an edge with a triangle of another tag in some cell."""
    got = set()
    for cell in out.values():
        tags = cell["tags"]
        for i, e in enumerate(cell["edges"]):
            if tags[i] > 0 and any(j >= 0 and tags[j] != tags[i] for j in e):
                got.add(tags[i])
    return got


def place_cells(carried: list, generated: dict, region: Region, water=None, neighbours=None, on_moved=None) -> tuple[dict, dict]:
    """build_cells with the moved units' rule: a moved unit's own triangles (tag k > 0) replace the generated triangles
    resting on its surface in its new place (`on_moved[k - 1](tri)`); a unit whose patch joins nothing else is meshed
    by the generator instead (its triangles dropped, the generated ones kept). Returns (cells, {moved_kept, moved_island})."""
    tags = sorted({g for _, _, g in carried if g > 0})
    island: set = set()

    def run(cells=None):
        use = [t for t in carried if t[2] not in island]
        live = [k for k in tags if k not in island]
        gen = generated if cells is None else {c: r for c, r in generated.items() if c in cells}
        if cells is not None:       # a trial of the moved units' cells alone: what lies over them
            use = [t for t in use if any((math.floor(p[0] / CELL), math.floor(p[1] / CELL)) in cells for p in t[0])]
        if on_moved and live:
            gen = {c: [(t, f) for t, f in rows if not any(on_moved[k - 1](t) for k in live)] for c, rows in gen.items()}
        return build_cells(use, gen, region, water, neighbours), live
    if tags:                        # which moved units join: tried on their own cells first
        cells = {(math.floor(p[0] / CELL), math.floor(p[1] / CELL)) for t, _, g in carried if g > 0 for p in t}
        cells |= {(c[0] + dx, c[1] + dy) for c in list(cells) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        while True:
            out, live = run(cells)
            lone = set(live) - joined_tags(out)
            if not lone:
                break
            island |= lone
    out, live = run()
    return out, {"moved_kept": len(live), "moved_island": len(island)}


def to_nvnm(cell: dict, template):
    """A finished cell as an Nvnm, its header (world, grid) from `template` (the generated mesh of that cell)."""
    from tools.navmesh import nvnm
    T = np.zeros(len(cell["tris"]), nvnm.TRI)
    if len(T):
        T["v"] = np.asarray(cell["tris"], np.uint16)
        T["e"] = np.asarray(cell["edges"], np.int16)
        T["flags"] = np.asarray(cell["flags"], np.uint16)
    return nvnm.Nvnm(world=template.world, grid_xy=template.grid_xy, cell=template.cell,
                     verts=np.asarray(cell["verts"], np.float32).reshape(-1, 3), tris=T)


def door_faults(navs: list[dict], S: dict, step: float = 64.0) -> list[str]:
    """Every exterior door has a door triangle, and its arrival stands over a triangle within a step (in plan and
    height together, as finish_navmesh measures)."""
    from tools.places.build import cell_of, tri_near
    by_cell = {tuple(n["cell"]): n for n in navs if n["space"] == "exterior"}
    by_fk = {r["fk"]: r for r in S["refs"]}
    out = []
    for r in S["refs"]:
        t = r.get("teleport")
        if not t or r.get("kind") == "marker" or r["space"] != "exterior":
            continue
        at = by_fk[t["to"]]["teleport"]["pos"]
        cx, cy = cell_of(at[0], at[1])
        best = min((tri_near(by_cell[c]["nv"], at)[1] for c in ((cx + dx, cy + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
                    if c in by_cell), default=float("inf"))
        if best > step:
            out.append(f"door {r['id']}: its arrival {[round(v) for v in at]} is {best:.0f} from the nearest triangle (over a step)")
    return out
