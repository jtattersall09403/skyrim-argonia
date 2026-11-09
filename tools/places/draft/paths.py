"""Streets and paths: the source's own streets recovered and laid on our land, connected, reaching every door and
the landing.

Recovery: the nodes are the source's door fronts and the landing's shore end; the network joining them is the
minimum spanning tree over walking distances on the source's navmesh, with the source's preferred-path triangles
(its own streets) costing PREFERRED_DISCOUNT of the rest; without a navmesh the distances are straight lines. Each
edge's route is mapped onto our land through the fit and its ends are pinned to our door fronts.
"""
from __future__ import annotations

import base64
import heapq
import json
import math
import re
from pathlib import Path

from tools.places.draft import geom

PREFERRED = 0x40
WATER = 0x200
PREFERRED_DISCOUNT = 0.5
STREET_WIDTH = 256.0
PATH_WIDTH = 160.0
SIMPLIFY = 64.0
END_FREE = 256.0      # a street may leave a doorway or a landing through what crowds it


class NavGraph:
    def __init__(self, navmeshes: list[dict], prefer: set | None = None):
        """prefer: grid keys (x // 128, y // 128) of the source's painted streets and walkways."""
        self.cent: list[tuple[float, float]] = []
        self.flags: list[int] = []
        self.adj: list[list[int]] = []
        edge_of: dict[tuple, list[int]] = {}
        for nm in navmeshes:
            verts = nm.get("verts") or []
            for t in nm.get("tris") or []:
                a, b, c = t[0], t[1], t[2]
                if max(a, b, c) >= len(verts):
                    continue
                pa, pb, pc = verts[a], verts[b], verts[c]
                i = len(self.cent)
                self.cent.append(((pa[0] + pb[0] + pc[0]) / 3, (pa[1] + pb[1] + pc[1]) / 3))
                self.flags.append(int(t[3]) if len(t) > 3 else 0)
                self.adj.append([])
                for e in ((a, b), (b, c), (c, a)):
                    k = tuple(sorted((tuple(round(v) for v in verts[e[0]][:2]), tuple(round(v) for v in verts[e[1]][:2]))))
                    edge_of.setdefault(k, []).append(i)
        prefer = prefer or set()
        self.pref = [bool(f & PREFERRED) or (int(c[0] // 128), int(c[1] // 128)) in prefer
                     for c, f in zip(self.cent, self.flags)]
        for tris in edge_of.values():
            for i in tris:
                for j in tris:
                    if i != j:
                        self.adj[i].append(j)

    def __bool__(self):
        return bool(self.cent)

    def nearest(self, p) -> int:
        return min(range(len(self.cent)), key=lambda i: geom.dist(self.cent[i], p))

    def route(self, a, b) -> tuple[float, list[tuple[float, float]]]:
        s, t = self.nearest(a), self.nearest(b)
        dist = {s: 0.0}
        prev: dict[int, int] = {}
        pq = [(0.0, s)]
        while pq:
            d, i = heapq.heappop(pq)
            if i == t:
                break
            if d > dist.get(i, math.inf):
                continue
            for j in self.adj[i]:
                w = geom.dist(self.cent[i], self.cent[j])
                if self.pref[j]:
                    w *= PREFERRED_DISCOUNT
                nd = d + w
                if nd < dist.get(j, math.inf):
                    dist[j] = nd
                    prev[j] = i
                    heapq.heappush(pq, (nd, j))
        if t not in dist:
            return geom.dist(a, b) * 3, [tuple(a), tuple(b)]
        pts, i = [], t
        while i != s:
            pts.append(self.cent[i])
            i = prev[i]
        pts.append(self.cent[s])
        pts.reverse()
        return dist[t], [tuple(a)] + pts + [tuple(b)]


def simplify(pts: list, tol: float = SIMPLIFY) -> list:
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    L = geom.dist(a, b) or 1e-9
    best, k = -1.0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        d = abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / L
        if d > best:
            best, k = d, i
    if best <= tol:
        return [a, b]
    return simplify(pts[:k + 1], tol)[:-1] + simplify(pts[k:], tol)


def network(nodes: dict[str, tuple[float, float]], nav: NavGraph) -> list[tuple[str, str, list]]:
    """MST over the nodes (Prim), each edge with its source route."""
    names = sorted(nodes)
    if len(names) < 2:
        return []
    routes: dict[tuple[str, str], tuple[float, list]] = {}

    def rt(a, b):
        k = (a, b) if a < b else (b, a)
        if k not in routes:
            if nav:
                routes[k] = nav.route(nodes[k[0]], nodes[k[1]])
            else:
                routes[k] = (geom.dist(nodes[k[0]], nodes[k[1]]), [nodes[k[0]], nodes[k[1]]])
        return routes[k]

    # candidate edges: each node to its 6 nearest by straight line keeps the routing cheap
    near = {a: sorted((b for b in names if b != a), key=lambda b: geom.dist(nodes[a], nodes[b]))[:6] for a in names}
    seen = {names[0]}
    edges = []
    while len(seen) < len(names):
        best = None
        for a in sorted(seen):
            for b in near[a]:
                if b in seen:
                    continue
                d = rt(a, b)[0]
                if best is None or (d, a, b) < best[0]:
                    best = ((d, a, b), a, b)
        if best is None:   # the 6-nearest graph is split: join the closest pair across the split
            a, b = min(((a, b) for a in seen for b in names if b not in seen),
                       key=lambda p: geom.dist(nodes[p[0]], nodes[p[1]]))
        else:
            _, a, b = best
        seen.add(b)
        k = (a, b) if a < b else (b, a)
        edges.append((k[0], k[1], rt(a, b)[1] if (a, b) == k else list(reversed(rt(a, b)[1]))))
    return edges


def seg_dist(p, a, b) -> float:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def dist_to_paths(p, paths: list[dict]) -> float:
    best = math.inf
    for pa in paths:
        pts = pa["points"]
        for a, b in zip(pts, pts[1:]):
            best = min(best, seg_dist(p, a, b) - pa.get("width", STREET_WIDTH) / 2)
    return max(best, 0.0)


def connected(paths: list[dict], join: float = 32.0) -> bool:
    """One network: every path touches another within `join` units."""
    if len(paths) <= 1:
        return True
    seen, stack = {0}, [0]
    while stack:
        i = stack.pop()
        for j, q in enumerate(paths):
            if j in seen:
                continue
            if any(dist_to_paths(p, [paths[i]]) <= join for p in q["points"]) or \
               any(dist_to_paths(p, [q]) <= join for p in paths[i]["points"]):
                seen.add(j)
                stack.append(j)
    return len(seen) == len(paths)


# --- recovering the source's streets ---------------------------------------------------------------------------

ROAD_TEX = re.compile(r"road|path|street|cobble|trail", re.I)
WALKWAY = re.compile(r"dock|boardwalk|bridge|walkway|steps|stair|road|plank|pier|jetty", re.I)
QUADS = {"BottomLeft": (0, 0), "BottomRight": (0, 16), "TopLeft": (16, 0), "TopRight": (16, 16)}
PAINTED = 0.5


def road_points(space_dir: Path) -> list[tuple[float, float]]:
    """Land vertices the source painted with a road or path texture (opacity >= PAINTED), as world points."""
    tj = space_dir / "terrain.json"
    if not tj.exists():
        return []
    t = json.loads(tj.read_text())
    ltex = t.get("ltex") or {}
    road = {k for k, v in ltex.items() if ROAD_TEX.search(f"{v.get('edid', '')} {v.get('diffuse', '')}")}
    out = set()
    for c in t["cells"]:
        cx, cy = c["cell"]
        for lay in c.get("layers") or []:
            if lay.get("tex") not in road or lay.get("quad") not in QUADS:
                continue
            r0, c0 = QUADS[lay["quad"]]
            alpha = base64.b64decode(lay["alpha"]) if lay.get("alpha") else bytes([255]) * 289
            for i, a in enumerate(alpha[:289]):
                if a / 255 >= PAINTED:
                    row, col = r0 + i // 17, c0 + i % 17
                    out.add((cx * 4096 + col * 128.0, cy * 4096 + row * 128.0))
    return sorted(out)


def width_from_paint(route: list, paint_grid: set, default: float) -> float:
    """A street's width from the source's paint along it: painted area round the route over its length."""
    if not paint_grid or len(route) < 2:
        return default
    hits = n = 0
    for a, b in zip(route, route[1:]):
        steps = max(1, int(geom.dist(a, b) // 128))
        for k in range(steps):
            x = a[0] + (b[0] - a[0]) * k / steps
            y = a[1] + (b[1] - a[1]) * k / steps
            n += 1
            hits += sum((round(x / 128) + i, round(y / 128) + j) in paint_grid for i in range(-2, 3) for j in range(-2, 3))
    if not n or hits / n < 1.0:
        return default
    return float(max(128.0, min(512.0, round(hits / n * 128 / 5 / 32) * 32)))


# --- laying a street on our ground -----------------------------------------------------------------------------

def astar(g, a, b, blocked, max_slope: float, guide: list, step: float = 128.0, pad: float = 1536.0):
    """A street from a to b on our ground: 8-neighbour search on a `step` grid round the guide line; a step is dearer
    the steeper it climbs and the further it strays from the guide; `blocked(x, y)` cells (water without a
    walkway, building footprints) and climbs steeper than max_slope degrees are never taken."""
    xs = [p[0] for p in guide] + [a[0], b[0]]
    ys = [p[1] for p in guide] + [a[1], b[1]]
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    start = (round(a[0] / step), round(a[1] / step))
    goal = (round(b[0] / step), round(b[1] / step))
    tan_max = math.tan(math.radians(max_slope))

    def stray(i, j):
        p = (i * step, j * step)
        return min(seg_dist(p, u, v) for u, v in zip(guide, guide[1:])) if len(guide) > 1 else 0.0
    hcache: dict = {}

    def h(i, j):
        if (i, j) not in hcache:
            hcache[(i, j)] = g.height(i * step, j * step)
        return hcache[(i, j)]
    openq = [(0.0, start)]
    cost = {start: 0.0}
    prev: dict = {}
    while openq:
        _, cur = heapq.heappop(openq)
        if cur == goal:
            break
        if len(cost) > 200000:
            return None
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if not di and not dj:
                    continue
                nx, ny = cur[0] + di, cur[1] + dj
                px, py = nx * step, ny * step
                if not (x0 <= px <= x1 and y0 <= py <= y1):
                    continue
                near_end = min(math.dist((nx, ny), start), math.dist((nx, ny), goal)) * step <= END_FREE
                if not near_end and blocked(px, py):
                    continue
                ha, hb = h(*cur), h(nx, ny)
                if ha is None or hb is None:
                    continue
                d = step * math.hypot(di, dj)
                rise = abs(hb - ha) / d
                if rise > tan_max and not near_end:
                    continue
                c = cost[cur] + d * (1 + 4 * (rise / max(tan_max, 1e-3)) ** 2) + 0.5 * d * stray(nx, ny) / 256.0
                if c < cost.get((nx, ny), math.inf):
                    cost[(nx, ny)] = c
                    prev[(nx, ny)] = cur
                    heapq.heappush(openq, (c + math.dist((nx, ny), goal) * step, (nx, ny)))
    if goal not in prev and goal != start:
        return None
    pts, k = [], goal
    while k != start:
        pts.append((k[0] * step, k[1] * step))
        k = prev[k]
    pts.append((start[0] * step, start[1] * step))
    pts.reverse()
    return [tuple(a)] + pts[1:-1] + [tuple(b)]


def route_slope(g, pts) -> float:
    """The steepest climb along a route, in degrees, sampled every 128 units."""
    worst = 0.0
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(geom.dist(a, b) // 128))
        prev = g.height(*a)
        for k in range(1, n + 1):
            q = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
            hq = g.height(*q)
            if prev is not None and hq is not None:
                worst = max(worst, math.degrees(math.atan(abs(hq - prev) / (geom.dist(a, b) / n or 1))))
            prev = hq
    return worst
