"""Paths on built navmeshes, the way the engine walks them: triangle to triangle across shared edges and edge links.

    Graph(navms)            navms: (key, Nvnm) pairs; key is the NAVM's local FormID (links name it the same way)
    .locate(p, dz)          the triangle under the point (in plan, the nearest in height within dz), or None
    .path(a, b)             A* over triangle centroids from the triangle under a to the one under b: the list of
                            (key, triangle) or None when b cannot be reached
    .component_of(node)     every node reachable from node

The query runs on our records (decoded NVNM), not on Recast's own mesh, so it proves what the game is given:
adjacency from the NVNM edges, cell seams from the Portal edge links.
"""
from __future__ import annotations

import heapq
import math

import numpy as np

from tools.navmesh import nvnm


class Graph:
    def __init__(self, navms):
        self.n: dict[int, nvnm.Nvnm] = {}
        self.cent: dict[int, np.ndarray] = {}
        for key, n in navms:
            self.n[key] = n
            v = n.verts.astype(np.float64)
            self.cent[key] = v[n.tris["v"].astype(int)].mean(axis=1)

    def neighbours(self, node):
        key, ti = node
        n = self.n[key]
        fl = int(n.tris["flags"][ti])
        for k in range(3):
            e = int(n.tris["e"][ti][k])
            if fl & nvnm.EDGE_LINK[k]:
                lk = n.links[e]
                other = int(lk["navm"]) & 0xFFFFFF
                if other in self.n:
                    yield other, int(lk["tri"])
            elif e >= 0:
                yield key, e

    def locate(self, p, dz: float = 128.0):
        """The triangle whose plan shape holds p (0.5 unit slack) with the smallest height difference within dz."""
        best, bd = None, dz
        for key, n in self.n.items():
            if n.bounds is not None and len(n.bounds) == 6:
                lo, hi = n.bounds[:3], n.bounds[3:]
                if not (lo[0] - 1 <= p[0] <= hi[0] + 1 and lo[1] - 1 <= p[1] <= hi[1] + 1):
                    continue
            v = n.verts.astype(np.float64)
            tv = n.tris["v"].astype(int)
            a, b, c = v[tv[:, 0]], v[tv[:, 1]], v[tv[:, 2]]
            den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
            with np.errstate(divide="ignore", invalid="ignore"):
                l1 = ((b[:, 1] - c[:, 1]) * (p[0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (p[1] - c[:, 1])) / den
                l2 = ((c[:, 1] - a[:, 1]) * (p[0] - c[:, 0]) + (a[:, 0] - c[:, 0]) * (p[1] - c[:, 1])) / den
            l3 = 1 - l1 - l2
            eps = 0.5 / np.sqrt(np.abs(den) + 1e-9)
            inside = (l1 >= -eps) & (l2 >= -eps) & (l3 >= -eps) & (den != 0)
            for ti in np.nonzero(inside)[0]:
                z = l1[ti] * a[ti, 2] + l2[ti] * b[ti, 2] + l3[ti] * c[ti, 2]
                d = abs(z - p[2])
                if d <= bd:
                    best, bd = (key, int(ti)), d
        return best

    def path(self, a, b):
        if a is None or b is None:
            return None
        goal = self.cent[b[0]][b[1]]

        def h(node):
            return float(np.linalg.norm(self.cent[node[0]][node[1]] - goal))
        dist = {a: 0.0}
        prev = {}
        heap = [(h(a), 0.0, a)]
        while heap:
            _, g, node = heapq.heappop(heap)
            if node == b:
                out = [node]
                while node in prev:
                    node = prev[node]
                    out.append(node)
                return out[::-1]
            if g > dist.get(node, math.inf):
                continue
            c0 = self.cent[node[0]][node[1]]
            for nb in self.neighbours(node):
                g2 = g + float(np.linalg.norm(self.cent[nb[0]][nb[1]] - c0))
                if g2 < dist.get(nb, math.inf):
                    dist[nb], prev[nb] = g2, node
                    heapq.heappush(heap, (g2 + h(nb), g2, nb))
        return None

    def component_of(self, node) -> set:
        seen, stack = {node}, [node]
        while stack:
            for nb in self.neighbours(stack.pop()):
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return seen
