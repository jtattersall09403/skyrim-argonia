"""The province-wide checks over a built navmesh (beside checks.py's per-record L1), on the records as written.

    coverage   every navmesh cell (world.navmesh_cells) with dry ground (a LAND sample above the water level) has a
               NAVM; the cells that do not are listed
    seams      cross-cell edge pairs: every open edge on a seam between two NAVMs whose neighbour has an open edge
               with the same two ends (both within SEAM_DZ in height) is linked; linked = pairs, mismatched = the rest
    components the triangle graph (neighbours and edge links) over the whole province; the largest component's
               share of the walkable plan area; every other component sorted by the landmass it stands on (connected
               dry-or-shallow ground, depth within WATER_MAX_DEPTH, across the navmesh cells): an island of its own
               (no other component on that landmass is larger) or cut off on a landmass the main component holds
               (cliffs, steep ground)
    paths      PAIRS settlement pairs (cities and towns, each to its nearest unpaired one), A* over triangle centroids
               from the triangle under each place's nearest walkable point; a failure names whether the two stand on
               different landmasses
"""
from __future__ import annotations

import heapq
import math
from collections import defaultdict

import numpy as np
from scipy import ndimage

from tools.navmesh import nvnm, params, stitch
from tools.navmesh import world as su

PAIRS = 20
SNAP_UNITS = 2048.0  # a place's point moves to the nearest triangle centroid within this (half a cell)


class Province:
    """Every triangle of the province as one graph: index = cell offset + triangle."""

    def __init__(self, out):
        self.cells, self.off = {}, {}
        cent, area, flags, cellid = [], [], [], []
        edges = []
        n_tri = 0
        raw = list(stitch.read_navm(out))
        for x, y, fk, n in raw:
            self.cells[(x, y)] = int(fk.split(":")[0], 16)
            self.off[self.cells[(x, y)]] = n_tri
            n_tri += len(n.tris)
        self.by_local = {v: k for k, v in self.cells.items()}
        for x, y, fk, n in raw:
            o = self.off[self.cells[(x, y)]]
            v = n.verts.astype(np.float64)
            tv = n.tris["v"].astype(np.int64)
            cent.append(v[tv].mean(axis=1))
            a, b, c = v[tv[:, 0]], v[tv[:, 1]], v[tv[:, 2]]
            area.append(np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])) / 2 / su.UNITS_PER_METRE ** 2)
            flags.append(n.tris["flags"].astype(np.int64))
            cellid.append(np.full(len(tv), self.cells[(x, y)], np.int64))
            e = n.tris["e"].astype(np.int64)
            fl = n.tris["flags"].astype(np.int64)
            for k in range(3):
                linked = (fl & nvnm.EDGE_LINK[k]) != 0
                inner = (~linked) & (e[:, k] >= 0)
                ti = np.nonzero(inner)[0]
                edges.append(np.stack([o + ti, o + e[ti, k]], 1))
                for t in np.nonzero(linked)[0]:
                    lk = n.links[int(e[t, k])]
                    other = int(lk["navm"]) & 0xFFFFFF
                    if other in self.off:
                        edges.append(np.array([[o + t, self.off[other] + int(lk["tri"])]]))
        self.n = n_tri
        self.cent = np.concatenate(cent) if cent else np.zeros((0, 3))
        self.area = np.concatenate(area) if area else np.zeros(0)
        self.flags = np.concatenate(flags) if flags else np.zeros(0, np.int64)
        self.cell = np.concatenate(cellid) if cellid else np.zeros(0, np.int64)
        ed = np.concatenate(edges) if edges else np.zeros((0, 2), np.int64)
        # CSR adjacency
        order = np.argsort(ed[:, 0], kind="stable")
        self.nbr = ed[order, 1]
        self.start = np.searchsorted(ed[order, 0], np.arange(n_tri + 1))
        self.labels = self._components()

    def _components(self) -> np.ndarray:
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        rows = np.repeat(np.arange(self.n), np.diff(self.start))
        m = coo_matrix((np.ones(len(rows), np.int8), (rows, self.nbr)), shape=(self.n, self.n))
        _, lab = connected_components(m, directed=False)
        return lab

    def nearest(self, p, reach: float = SNAP_UNITS) -> int | None:
        d = np.hypot(self.cent[:, 0] - p[0], self.cent[:, 1] - p[1])
        i = int(np.argmin(d)) if len(d) else -1
        return i if i >= 0 and d[i] <= reach else None

    def astar(self, a: int, b: int) -> tuple[list[int] | None, int]:
        """The triangle path from a to b and the number of nodes expanded."""
        goal = self.cent[b]
        cent, start, nbr = self.cent, self.start, self.nbr
        dist = {a: 0.0}
        prev: dict[int, int] = {}
        heap = [(float(np.linalg.norm(cent[a] - goal)), 0.0, a)]
        expanded = 0
        while heap:
            _, g, u = heapq.heappop(heap)
            if u == b:
                path = [u]
                while u in prev:
                    u = prev[u]
                    path.append(u)
                return path[::-1], expanded
            if g > dist.get(u, math.inf):
                continue
            expanded += 1
            cu = cent[u]
            for w in nbr[start[u]:start[u + 1]]:
                w = int(w)
                cw = cent[w]
                g2 = g + math.dist(cu, cw)
                if g2 < dist.get(w, math.inf):
                    dist[w], prev[w] = g2, u
                    heapq.heappush(heap, (g2 + math.dist(cw, goal), g2, w))
        return None, expanded


def landmasses(ras, cells: set) -> tuple[np.ndarray, callable]:
    """Connected ground an agent could cover by walking and wading (depth within WATER_MAX_DEPTH) over the navmesh
    cells' samples; returns the label raster and a lookup (x, y) -> label (0 = none)."""
    g = ras.g
    h = np.asarray(ras.h)
    ok = h > g["water"] - params.WATER_MAX_DEPTH
    inside = np.zeros(h.shape, bool)
    for (x, y) in cells:
        c0 = int(round((x * su.CELL_UNITS - g["x0"]) / g["step"]))
        r0 = int(round((g["ytop"] - (y + 1) * su.CELL_UNITS) / g["step"]))
        inside[r0:r0 + su.LAND_VERTS, c0:c0 + su.LAND_VERTS] = True
    lab, _ = ndimage.label(ok & inside)

    def at(x, y):
        c = int(round((x - g["x0"]) / g["step"]))
        r = int(round((g["ytop"] - y) / g["step"]))
        if 0 <= r < lab.shape[0] and 0 <= c < lab.shape[1]:
            return int(lab[r, c])
        return 0
    return lab, at


def pairs(places: list[dict], k: int = PAIRS) -> list[tuple[dict, dict]]:
    """Cities and towns first, then villages, then the rest: each to its nearest place not yet used, until k pairs."""
    rank = {"city": 0, "town": 1, "village": 2}
    pool = sorted(places, key=lambda p: (rank.get(p["kind"], 3), p["id"]))  # then every other dry place
    used, out = set(), []
    for p in pool:
        if len(out) >= k:
            break
        if p["id"] in used:
            continue
        cand = [q for q in pool if q["id"] != p["id"] and q["id"] not in used]
        if not cand:
            break
        q = min(cand, key=lambda q: math.hypot(q["x"] - p["x"], q["y"] - p["y"]))
        used.update((p["id"], q["id"]))
        out.append((p, q))
    return out


def run(out, cells: set, ras) -> dict:
    pv = Province(out)
    have = set(pv.cells)
    h = np.asarray(ras.h)
    g = ras.g
    # coverage: navmesh cells with any dry sample
    land_cells, missing = 0, []
    for (x, y) in sorted(cells):
        c0 = int(round((x * su.CELL_UNITS - g["x0"]) / g["step"]))
        r0 = int(round((g["ytop"] - (y + 1) * su.CELL_UNITS) / g["step"]))
        if (h[r0:r0 + su.LAND_VERTS, c0:c0 + su.LAND_VERTS] > g["water"]).any():
            land_cells += 1
            if (x, y) not in have:
                missing.append([x, y])
    extra = sorted([list(c) for c in have - cells])
    # seams: open seam edges in both neighbours with matching ends
    linked = mismatched = unmatched = 0
    ends_of: dict = {}
    unm_at: list = []
    mism_at = []
    edges_by = {}
    for x, y, fk, n in stitch.read_navm(out):
        m = stitch.Mesh(x, y, n.verts.astype(np.float64).tolist(), n.tris["v"].astype(int).tolist(), [0] * len(n.tris))
        fl = n.tris["flags"].astype(int)
        open_ = {}
        for side in "WESN":
            for key, (ti, k, z0, z1) in stitch.seam_edges(m, side).items():
                open_[(side, key)] = (bool(fl[ti] & nvnm.EDGE_LINK[k]), z0, z1)
        # seam_edges finds edges with one use inside the cell: linked ones count too (they are open in the mesh)
        edges_by[(x, y)] = open_
    for (x, y), es in edges_by.items():
        for (side, key), (lk, z0, z1) in es.items():
            if side not in "EN":
                continue  # each pair once, from its west or south cell
            dx, dy = stitch.STEP[side]
            other = edges_by.get((x + dx, y + dy))
            if other is None:
                continue
            o = other.get((stitch.OPP[side], key))
            if o is None:
                ends = ends_of.setdefault((x + dx, y + dy, stitch.OPP[side]),
                                          {p for (sd, kk) in other for p in kk if sd == stitch.OPP[side]})
                if key[0] in ends or key[1] in ends:
                    unmatched += 1
                    if len(unm_at) < 10:
                        unm_at.append([x, y, side, [list(map(float, k)) for k in key], [z0, z1]])  # the neighbour has an edge from one of these ends, but not this segment
                continue
            if lk and o[0]:
                linked += 1
            elif abs(z0 - o[1]) <= params.SEAM_DZ and abs(z1 - o[2]) <= params.SEAM_DZ:
                mismatched += 1
                if len(mism_at) < 10:
                    mism_at.append([x, y, side])
    # components and landmasses
    lab_r, at = landmasses(ras, cells)
    comp_area = np.bincount(pv.labels, weights=pv.area) if pv.n else np.zeros(0)
    total = float(comp_area.sum())
    main = int(np.argmax(comp_area)) if len(comp_area) else -1
    # each component's landmass: the most common landmass under its triangles' centroids
    comp_land: dict[int, int] = {}
    if pv.n:
        cc = np.clip(np.rint((pv.cent[:, 0] - g["x0"]) / g["step"]).astype(np.int64), 0, lab_r.shape[1] - 1)
        rr = np.clip(np.rint((g["ytop"] - pv.cent[:, 1]) / g["step"]).astype(np.int64), 0, lab_r.shape[0] - 1)
        lm = lab_r[rr, cc].astype(np.int64)
        for c in np.unique(pv.labels):
            sel = lm[pv.labels == c]
            sel = sel[sel > 0]
            comp_land[int(c)] = int(np.bincount(sel).argmax()) if len(sel) else 0
    main_land = comp_land.get(main, 0)
    land_best = defaultdict(lambda: (-1.0, -1))
    for c, lmk in comp_land.items():
        if comp_area[c] > land_best[lmk][0]:
            land_best[lmk] = (float(comp_area[c]), c)
    islands, cut = [], []
    for c in np.argsort(-comp_area):
        c = int(c)
        if c == main:
            continue
        lmk = comp_land.get(c, 0)
        cen = pv.cent[pv.labels == c][0]
        row = {"m2": round(float(comp_area[c]), 1), "at": [round(float(cen[0])), round(float(cen[1]))]}
        if lmk != main_land and land_best[lmk][1] == c:
            islands.append(row)
        else:
            cut.append(row)
    # paths
    pr = []
    inside = [p for p in su.settlements() if (int(p["x"] // su.CELL_UNITS), int(p["y"] // su.CELL_UNITS)) in cells]
    for p, q in pairs(inside):
        a, b = pv.nearest((p["x"], p["y"])), pv.nearest((q["x"], q["y"]))
        rec = {"from": p["id"], "to": q["id"], "straight_m": round(math.hypot(p["x"] - q["x"], p["y"] - q["y"]) / su.UNITS_PER_METRE)}
        la, lb = at(p["x"], p["y"]), at(q["x"], q["y"])
        if a is None or b is None:
            rec.update(ok=False, why=f"no navmesh within {SNAP_UNITS:g} units of {'the start' if a is None else 'the end'}")
        elif pv.labels[a] != pv.labels[b]:
            rec.update(ok=False, why="different components" + (" on different landmasses (water between)" if la != lb else " on one landmass"))
        else:
            path, nexp = pv.astar(a, b)
            if path is None:
                rec.update(ok=False, why="A* found no path")
            else:
                ln = sum(math.dist(pv.cent[i], pv.cent[j]) for i, j in zip(path, path[1:])) / su.UNITS_PER_METRE
                rec.update(ok=True, path_m=round(ln), triangles=len(path), expanded=nexp)
        pr.append(rec)
    return {
        "coverage": {"navmesh_cells": len(cells), "land_cells": land_cells, "navm": len(have), "land_cells_without_navm": len(missing),
                     "missing": missing[:20], "navm_outside_navmesh_cells": len(extra)},
        "seams": {"linked_pairs": linked, "mismatched": mismatched, "unmatched_segments": unmatched, "first_unmatched": unm_at, "first_mismatched": mism_at},
        "components": {"count": int(len(comp_area)), "main_m2": round(float(comp_area[main]), 1) if main >= 0 else 0,
                       "main_share": round(float(comp_area[main]) / total, 4) if total else None,
                       "islands": len(islands), "islands_m2": round(sum(r["m2"] for r in islands), 1),
                       "largest_islands": islands[:10],
                       "cut_off_on_a_main_landmass": len(cut), "cut_off_m2": round(sum(r["m2"] for r in cut), 1),
                       "largest_cut_off": cut[:10]},
        "paths": {"pairs": len(pr), "ok": sum(1 for r in pr if r.get("ok")), "list": pr},
    }
