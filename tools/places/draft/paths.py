"""Streets and paths: the source's own streets recovered and laid on our land, connected, reaching every door and
the landing.

Recovery: the nodes are the source's door fronts and the landing's shore end; the network joining them is the
minimum spanning tree over walking distances on the source's navmesh, with the source's preferred-path triangles
(its own streets) costing PREFERRED_DISCOUNT of the rest; without a navmesh the distances are straight lines. Each
edge's route is mapped onto our land through the fit and its ends are pinned to our door fronts.
"""
from __future__ import annotations

import heapq
import math

from tools.places.draft import geom

PREFERRED = 0x40
WATER = 0x200
PREFERRED_DISCOUNT = 0.5
STREET_WIDTH = 256.0
PATH_WIDTH = 160.0
SIMPLIFY = 64.0


class NavGraph:
    def __init__(self, navmeshes: list[dict]):
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
                if self.flags[j] & PREFERRED:
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
