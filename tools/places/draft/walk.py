"""The walkable network of a drafted place, by the build's own navmesh, and the joins the draft lays across it.

`network` builds the place (`build <place_id>` into out/places/draft_check, cached by the place files' key, so an
unchanged draft is not rebuilt) and loads it exactly as `check` does; `islands` lists each door's exterior navmesh
that is not on the place's main walkable network; `join` lays walkway pieces from each such island to the nearest
point of the network at a walkable height and reseats, until no door is on an island (or no join is possible).
`draft check` and `check` read the same network, so what `join` makes walkable the build's check finds walkable.
"""
from __future__ import annotations

import json
import re
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

from tools.places.draft import io, overlap
from tools.places.draft import paths as paths_mod

CHECK_OUT = io.ROOT / "out" / "places" / "draft_check"
LEVEL = 48.0         # units of height a join may leave between its two ends (a step the navmesh climbs)
JOIN_ROUNDS = 6
TRIES = 200        # joins tried per island, shortest first, for one no house or ship stands across


def build(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT) -> list[str]:
    """`build <place_id> --keep-going` into `out`: the build's problems, or the failure."""
    p = subprocess.run([sys.executable, "-m", "tools.places", "build", place_id, "--keep-going", "--places-dir", str(places),
                        "--out", str(out)], cwd=io.ROOT, capture_output=True, text=True)
    lines = [x.strip() for x in (p.stdout + p.stderr).splitlines() if x.strip()]
    bad = [f"build: {x}" for x in lines if x.startswith(f"{place_id}: ")]
    if p.returncode != 0:
        bad += [f"build failed ({p.returncode}): {x}" for x in lines[-10:]]
    return bad


def network(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT) -> tuple[dict | None, list[str]]:
    """The built place as `check` loads it (its context dict), and the build's problems."""
    bad = build(place_id, places, out)
    if any(b.startswith("build failed") for b in bad):
        return None, bad
    from tools.places import check as C
    ctx = C.load(place_id, out)
    ctx["place_dir"] = places / place_id
    return ctx, bad


def islands(ctx: dict, W: "Walkable") -> dict:
    """{door id: (its island, the island's triangle centres)} for each door of ours whose exterior navmesh is off the
    main network."""
    from tools.places import check as C
    m = C.mine(ctx)
    out: dict = {}
    for n in W.navs:
        if getattr(n, "world", False):
            continue
        for ti, d in n.doors:
            c = W.comp[W.off[n.fk] + ti]
            row = m["rows"].get(d)
            if not W.main[W.off[n.fk] + ti] and row is not None and row["id"] not in out:
                out[row["id"]] = (int(c), W.cent[W.comp == c])
    return out


ON_TOL = 48.0          # plan units: a point within this of its triangle stands on it
RISE, CLIMB = 1.0, 32.0  # a walked line climbs or drops no steeper than 45 degrees, plus a step (the navmesh's)
WATER_EDGE = 8.0       # over water with no deck: a dry triangle this near in plan, no lower than this under the water
PICK_TOL, Z_TOL = 96.0, 128.0   # the build's own lookup of a stop's triangle (check.STOP_PLAN_TOL, STOP_Z_TOL)
BUCKET = 512.0
STEP = 64.0            # units between the samples of a street tested against the network (paths.smooth's spacing)
SNAP = 384.0           # an end off the network (a doorway) is taken to the nearest network point this near
ROUTE_CAP = 200_000    # triangles a re-lay's search may open
MEND_LEAD = 8          # samples of the line on the network re-laid with a stretch off it, either side
MEND_GAP = 2048.0      # a stretch on the network shorter than this between two off it is re-laid with them (a line
#                        off the network either side of a short stretch is seldom at the right level in between)


class Walkable:
    """The built exterior navmesh (ours and the world's round the place) as one index: each triangle's walked
    component and whether it is the town's main network (the largest component over doors, as `check` finds it);
    triangles bucketed in plan for point lookup (a street's or a patrol's point is never found on water deeper than a
    ford, `check.walked`), and their neighbours for routing on the mesh. The levels one may stand
    at over a plan point (`levels`): a walkway piece's deck, `deck(x, y)`, by the mesh's own height there within
    check.DECK_TOL; our ground, `zref(x, y)`, within Z_TOL of a triangle's mean height, where it is dry or under
    water no deeper than check.WADE (`wet(x, y)` gives the water's level); over deeper water with no deck, only a
    dry triangle above the water, right under the point. A 3-d point carries its own height. A
    point's triangle is the one the build's check picks (`check.NavIndex.at`: within PICK_TOL in plan and the level's
    height band, nearest in plan, then in height), so what is on the network here is there."""

    def __init__(self, ctx: dict, zref=None, deck=None, wet=None, comp: dict | None = None):
        from tools.places import check as C
        water = C.water_level(ctx) if "facts" in ctx else None
        comp = comp if comp is not None else C.components(ctx["navs"], C.door_pairs(ctx))
        main = Counter(comp.values()).most_common(1)[0][0]
        self.zref, self.deck, self.wet = zref, deck, wet
        self.navs = [n for n in ctx["navs"].values() if n.space == "exterior" and len(n.tri)]
        self.off, tri, ids, o = {}, [], {}, 0
        cid = []
        for n in self.navs:
            self.off[n.fk] = o
            o += len(n.tri)
            tri.append(n.verts[n.tri])
            cid += [ids.setdefault(comp[(n.fk, i)], len(ids)) for i in range(len(n.tri))]
        self.T = np.concatenate(tri) if tri else np.zeros((0, 3, 3))
        self.dry = np.concatenate([C.walked(n, water) for n in self.navs]) if tri else np.zeros(0, bool)
        self.comp = np.asarray(cid, int)
        self.main = self.comp == ids.get(main, -1)
        self.cent = self.T.mean(axis=1)
        lo = np.floor((self.T[:, :, :2].min(axis=1) - PICK_TOL) / BUCKET).astype(int)
        hi = np.floor((self.T[:, :, :2].max(axis=1) + PICK_TOL) / BUCKET).astype(int)
        span = hi - lo
        keys, idx = [], []
        for di in range(int(span[:, 0].max(initial=0)) + 1):
            for dj in range(int(span[:, 1].max(initial=0)) + 1):
                m = (span[:, 0] >= di) & (span[:, 1] >= dj)
                keys.append(((lo[m, 0] + di).astype(np.int64) << 32) + (lo[m, 1] + dj).astype(np.int64))
                idx.append(np.nonzero(m)[0])
        keys = np.concatenate(keys) if keys else np.zeros(0, np.int64)
        idx = np.concatenate(idx) if idx else np.zeros(0, int)
        order = np.argsort(keys, kind="stable")
        keys, idx = keys[order], idx[order]
        u, start = np.unique(keys, return_index=True)
        ends = np.append(start[1:], len(keys))
        self.bucket = {int(k): idx[s:e] for k, s, e in zip(u, start, ends)}
        self._nbr = None

    def levels(self, p) -> list[tuple]:
        """Where one may stand at p, deck first: [(height, lowest, highest, by the mesh's height at p (else by the
        triangle's mean), plan reach)]; empty over open water with nothing to stand on."""
        from tools.places import check as C
        DECK_TOL = C.DECK_TOL
        x, y = float(p[0]), float(p[1])
        d = self.deck(x, y) if self.deck else None
        if len(p) > 2:
            z = float(p[2])
            if d is not None and abs(d - z) <= DECK_TOL:
                return [(z, z - DECK_TOL, z + DECK_TOL, True, math.inf)]
            return [(z, z - Z_TOL, z + Z_TOL, False, math.inf)]
        out = [(d, d - DECK_TOL, d + DECK_TOL, True, math.inf)] if d is not None else []
        w = self.wet(x, y) if self.wet else None
        if w is None:
            g = self.zref(x, y) if self.zref else None
            out.append((g, g - Z_TOL, g + Z_TOL, False, math.inf) if g is not None else (None, -math.inf, math.inf, False, math.inf))
        elif d is None:
            g = self.zref(x, y) if self.zref else None
            if g is not None and w - g <= C.WADE:     # waded: on the bed, as on the ground
                out.append((g, g - Z_TOL, g + Z_TOL, False, math.inf))
            else:                                     # too deep: only something dry right over it
                out.append((w, w - WATER_EDGE, math.inf, True, WATER_EDGE))
        return out

    def why(self, p) -> str:
        """Why p is off the network, in words, for a check's line."""
        lv = self.levels(p)
        if lv and lv[0][3] and lv[0][4] == math.inf and len(p) < 3:
            return f" (no dry triangle of the town's network within {lv[0][2] - lv[0][0]:.0f} of the deck at z {lv[0][0]:.0f})"
        if lv and lv[-1][2] == math.inf:
            return " (over open water: no deck and no dry triangle over it)"
        return ""

    def _cands(self, p, tol: float):
        """(triangle indices, plan distance, the mesh's height at p) of the dry triangles within `tol` of p in plan."""
        i, j = math.floor(p[0] / BUCKET), math.floor(p[1] / BUCKET)
        c = self.bucket.get((i << 32) + j)
        if c is None:
            return np.zeros(0, int), np.zeros(0), np.zeros(0)
        c = c[self.dry[c]]
        t = self.T[c]
        a, b, cc = t[:, 0, :2], t[:, 1, :2], t[:, 2, :2]
        q = np.asarray(p[:2], float)

        def cross(u, v):
            return (q[0] - v[:, 0]) * (u[:, 1] - v[:, 1]) - (u[:, 0] - v[:, 0]) * (q[1] - v[:, 1])
        d1, d2, d3 = cross(a, b), cross(b, cc), cross(cc, a)
        inside = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))

        def seg(u, v):
            w = v - u
            L = np.maximum((w * w).sum(axis=1), 1e-9)
            s = np.clip(((q - u) * w).sum(axis=1) / L, 0.0, 1.0)
            return np.linalg.norm(q - (u + w * s[:, None]), axis=1)
        dp = np.where(inside, 0.0, np.minimum(np.minimum(seg(a, b), seg(b, cc)), seg(cc, a)))
        # the triangle's plane at p (its centre's height for one seen edge on)
        e1, e2 = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
        nrm = np.cross(e1, e2)
        flat = np.abs(nrm[:, 2]) > 1e-6
        z = np.where(flat, t[:, 0, 2] - (nrm[:, 0] * (q[0] - t[:, 0, 0]) + nrm[:, 1] * (q[1] - t[:, 0, 1]))
                     / np.where(flat, nrm[:, 2], 1.0), self.cent[c, 2])
        z = np.clip(z, t[:, :, 2].min(axis=1), t[:, :, 2].max(axis=1))
        keep = dp <= tol
        return c[keep], dp[keep], z[keep]

    def _at(self, c, dp, z, lv, tol):
        """The candidates a level takes: (indices into c, their score)."""
        h, lo, hi, plane, reach = lv
        m = (z if plane else self.cent[c, 2])
        k = np.flatnonzero((m >= lo) & (m <= hi) & (dp <= min(tol, reach)))
        return k, dp[k] + (np.abs(m[k] - h) * 0.01 if h is not None else 0.0)

    def near(self, p, tol: float = PICK_TOL) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(triangle indices, plan distance, the mesh's height at p) of the dry triangles within `tol` of p in plan at
        a level one may stand at there."""
        c, dp, z = self._cands(p, tol)
        keep = np.zeros(len(c), bool)
        for lv in self.levels(p):
            keep[self._at(c, dp, z, lv, tol)[0]] = True
        return c[keep], dp[keep], z[keep]

    def pick(self, p) -> tuple[int, float]:
        """(triangle, plan distance) the build's check finds p on, else (-1, inf): at the first level (deck first)
        whose nearest triangle is of the main network, else the first level's nearest."""
        return self.found(p)[:2]

    def found(self, p) -> tuple[int, float, float | None]:
        """`pick`, with the mesh's height at p on that triangle."""
        c, dp, z = self._cands(p, PICK_TOL)
        first = None
        for lv in self.levels(p):
            k, score = self._at(c, dp, z, lv, PICK_TOL)
            if not len(k):
                continue
            best = k[int(np.argmin(score))]
            got = (int(c[best]), float(dp[best]), float(z[best]))
            if self.main[got[0]] and got[1] <= min(ON_TOL, lv[4]):
                return got
            first = first or got
        return first or (-1, float("inf"), None)

    def stands(self, p) -> tuple[np.ndarray, np.ndarray]:
        """(triangles, the mesh's height at p on each) of the main network's triangles p may stand on: within ON_TOL
        in plan, at any of its levels (a deck's, the ground's under it)."""
        c, dp, z = self._cands(p, ON_TOL)
        keep = np.zeros(len(c), bool)
        for lv in self.levels(p):
            keep[self._at(c, dp, z, lv, ON_TOL)[0]] = True
        keep &= self.main[c]
        return c[keep], z[keep]

    def walked(self, pts: list, z0: float | None = None) -> list[tuple[int, float] | None]:
        """A line's points walked in order: for each, (the triangle it stands on, the mesh's height there), or None
        where the line leaves the main network. A point is taken at the level one reaches it by from the point
        before, the nearest in height of those it may stand on (`stands`), never by a drop or a climb steeper than a
        walked slope (a step off a deck's edge onto the ground under it); the first point (or the next after a
        break) at `z0` when given, else as a stop is found (`found`: the deck first)."""
        out, prev = [], None
        for q in pts:
            c, z = self.stands(q)
            got = None
            if len(c) and prev is not None:
                dz = np.abs(z - prev[1])
                k = int(np.argmin(dz))
                if dz[k] <= RISE * math.dist(q[:2], prev[0][:2]) + CLIMB:
                    got = (int(c[k]), float(z[k]))
            elif len(c) and z0 is not None:
                k = int(np.argmin(np.abs(z - z0)))
                got = (int(c[k]), float(z[k])) if abs(z[k] - z0) <= CLIMB else None
            elif len(c):
                t, d, zt = self.found(q)
                k = int(np.argmin(np.abs(z - zt))) if t >= 0 and self.main[t] and d <= ON_TOL else int(np.argmax(z))
                got = (int(c[k]), float(z[k]))
            out.append(got)
            prev, z0 = ((q, got[1]) if got else None), None
        return out

    def line_ok(self, pts: list, z0: float | None = None) -> list[bool]:
        """For each of a line's points in order: whether it stands on the main network as the line is walked
        (`walked`)."""
        return [w is not None for w in self.walked(pts, z0)]

    def on(self, p, tol: float = ON_TOL) -> bool:
        """Whether p stands on the town's main network: the triangle it is found on is of it, within `tol` in plan."""
        t, d = self.pick(p)
        return t >= 0 and bool(self.main[t]) and d <= tol

    def snap(self, p, reach: float = SNAP):
        """The nearest point of the main network to p within `reach` in plan (p itself when it is on it), else None."""
        if self.on(p):
            return tuple(p[:2])
        for r in np.arange(STEP / 2, reach + 1, STEP / 2):
            for k in range(16):
                q = (p[0] + r * math.cos(k * math.pi / 8), p[1] + r * math.sin(k * math.pi / 8))
                if self.on(q, tol=8.0):
                    return q
        return None

    def neighbours(self) -> list[list[int]]:
        """Each triangle's neighbours over shared edges and edge links between meshes."""
        if self._nbr is None:
            nb = [[] for _ in range(len(self.T))]
            for n in self.navs:
                o = self.off[n.fk]
                for i in range(len(n.tri)):
                    for k in range(3):
                        e = int(n.edge[i][k])
                        if n.flags[i] & (1 << k):
                            if 0 <= e < len(n.links):
                                _, tgt, tt = n.links[e]
                                if tgt in self.off:
                                    nb[o + i].append(self.off[tgt] + tt)
                                    nb[self.off[tgt] + tt].append(o + i)
                        elif e >= 0:
                            nb[o + i].append(o + e)
            self._nbr = nb
        return self._nbr

    def reaches(self, a, b, za: float, zb: float) -> bool:
        """Whether the straight line a -> b, walked from a at height za (`walked`), stays on the main network all
        along and comes to b at height zb."""
        n = max(1, math.ceil(math.dist(a[:2], b[:2]) / (STEP / 2)))
        w = self.walked([(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)], za)
        return all(x is not None for x in w) and abs(w[-1][1] - zb) <= CLIMB

    def _portal(self, u: int, v: int) -> tuple[float, float, float]:
        """The middle of the edge two neighbouring triangles share (the middle between their centres when their
        corners do not meet, across an edge link)."""
        A, B = self.T[u], self.T[v]
        same = [p for p in A if (np.abs(B - p).max(axis=1) < 1.0).any()]
        m = (same[0] + same[1]) / 2 if len(same) >= 2 else (self.cent[u] + self.cent[v]) / 2
        return float(m[0]), float(m[1]), float(m[2])

    def route(self, a, b, za: float | None = None, zb: float | None = None) -> list | None:
        """The way the mesh walks from a to b (each on the main network, at heights za and zb when given): a search
        over the triangles; the line through the middles of the edges it crosses (so every point of it is on the
        mesh, at the level walked), pulled straight wherever the straight line walks the same way (`reaches`), then
        eased with paths.smooth when the eased line still does. Plan points, a and b included."""
        import heapq
        wa, wb = self.walked([a], za)[0], self.walked([b], zb)[0]
        if wa is None or wb is None:
            return None
        (s, za), (g, zb) = wa, wb
        nb, C = self.neighbours(), self.cent
        dist, prev, heap, opened = {s: 0.0}, {}, [(0.0, s)], 0
        while heap:
            _, u = heapq.heappop(heap)
            if u == g:
                break
            opened += 1
            if opened > ROUTE_CAP:
                return None
            for v in nb[u]:
                if not self.main[v] or not self.dry[v]:   # never through water deeper than a ford
                    continue
                d = dist[u] + float(np.linalg.norm(C[u] - C[v]))
                if d < dist.get(v, float("inf")):
                    dist[v], prev[v] = d, u
                    heapq.heappush(heap, (d + float(np.linalg.norm(C[v, :2] - C[g, :2])), v))
        if g not in dist:
            return None
        chain, u = [g], g
        while u != s:
            u = prev[u]
            chain.append(u)
        chain.reverse()
        pts = [(a[0], a[1], za)] + [self._portal(u, v) for u, v in zip(chain, chain[1:])] + [(b[0], b[1], zb)]
        pulled, i = [pts[0]], 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self.reaches(pts[i], pts[j], pts[i][2], pts[j][2]):
                j -= 1
            pulled.append(pts[j])
            i = j
        line = [q[:2] for q in pulled]
        eased = paths_mod.smooth(line, lambda x, y: not self.on((x, y)))
        w = self.walked([q for _, q in samples(eased)], za)
        return eased if all(x is not None for x in w) and abs(w[-1][1] - zb) <= CLIMB else line


def samples(pts: list, step: float = STEP) -> list[tuple[int, tuple]]:
    """A street's points every `step` units along it: [(the segment it lies on, (x, y))], its own points included."""
    out = []
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        n = max(1, math.ceil(math.dist(a[:2], b[:2]) / step))
        out += [(i, (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)) for k in range(n)]
    if pts:
        out.append((max(0, len(pts) - 2), tuple(pts[-1][:2])))
    return out


def off_network(paths: list[dict], folk: list[dict], W: Walkable) -> tuple[list[tuple], list[tuple]]:
    """([(street id, point)], [(person id, patrol point)]) of the street samples and patrol points off the main
    network."""
    st = []
    for p in paths:
        S = [q for _, q in samples(p["points"])]
        st += [(p["id"], q) for q, ok in zip(S, W.line_ok(S)) if not ok]
    pa = [(p["id"], q) for p in folk for q in (p.get("patrol") or {}).get("points") or [] if not W.on(q)]
    return st, pa


def mend(path: dict, W: Walkable, passes: int = 3) -> int | None:
    """Re-lay each stretch of a street off the main network along the way the mesh walks between the stretch's last
    and next points on it (an end off it, at a doorway, is first taken to the nearest network point; stretches less
    than MEND_GAP apart are one), and again over
    the new line while that leaves fewer points off (a gap finer than the sampling shows only on the new line). The
    stretches re-laid, or None when one has no way on the mesh (the street is then left as it was)."""
    before, total = list(path["points"]), 0

    def off() -> int:
        return W.line_ok([q for _, q in samples(path["points"])]).count(False)
    best = (off(), before)
    for _ in range(passes):
        if not best[0]:
            break
        n = _mend(path, W)
        if n is None:
            path["points"] = before
            return None
        left = off()
        if left >= best[0]:
            break
        best, total = (left, list(path["points"])), total + n
    path["points"] = best[1]
    return total


def _mend(path: dict, W: Walkable) -> int | None:
    pts = [tuple(q[:2]) for q in path["points"]]
    if len(pts) < 2:
        return 0
    S = samples(pts)
    at = W.walked([q for _, q in S])
    if all(x is not None for x in at):
        return 0
    for e in (0, len(S) - 1):
        if at[e] is None:
            q = W.snap(S[e][1])
            if q is None:
                return None
            S[e], at[e] = (S[e][0], q), W.walked([q])[0]
            pts[0 if e == 0 else -1] = q
    runs: list[list[int]] = []     # [first, last] sample of each stretch off the network
    for k, x in enumerate(at):
        if x is None:
            if runs and k - runs[-1][1] <= MEND_GAP / STEP:
                runs[-1][1] = k     # a short stretch on it between two off it is re-laid with them
            else:
                runs.append([k, k])
    out, cursor = [], 0
    for k0, k1 in runs:
        # from a little before to a little after, so the new line meets the old one in its stride
        a, b = max(0, k0 - 1 - MEND_LEAD), min(len(S) - 1, k1 + 1 + MEND_LEAD)
        way = W.route(S[a][1], S[b][1], at[a][1], at[b][1])
        if way is None:
            return None
        out += pts[cursor:S[a][0] + 1] + [S[a][1]] + list(way[1:-1]) + [S[b][1]]
        cursor = S[b][0] + 1
    n = len(runs)
    out += pts[cursor:]
    clean = [out[0]]
    for q in out[1:]:
        if math.dist(q, clean[-1]) > 1.0:
            clean.append(q)
    path["points"] = [[round(float(q[0]), 1), round(float(q[1]), 1)] for q in clean]
    return n


def dry(pts: np.ndarray, G) -> np.ndarray:
    """The triangle centres one walks on out of the water (a seabed under our water is no street)."""
    keep = []
    for p in pts:
        w = G.water(float(p[0]), float(p[1]))
        keep.append(w is None or p[2] >= w - 8)
    return pts[np.asarray(keep, bool)] if len(pts) else pts


def pairs(isl: np.ndarray, net: np.ndarray) -> list[tuple[float, np.ndarray, np.ndarray]]:
    """Level joins from an island to the network (ends within LEVEL of each other), shortest first: [(plan length, from, to)], one per
    island point (its nearest such network point)."""
    out = []
    for p in isl:
        d = np.linalg.norm(net[:, :2] - p[:2], axis=1)
        ok = np.abs(net[:, 2] - p[2]) <= LEVEL  # flat pieces: a join never climbs more than a step
        if ok.any():
            j = int(np.argmin(np.where(ok, d, np.inf)))
            out.append((float(d[j]), p, net[j]))
    return sorted(out, key=lambda t: t[0])


def walk_base(rows: list[dict], bases: dict) -> str | None:
    """The walkway piece the place's own joins and bridges use: the commonest the draft already laid, else the
    commonest walkway piece of the place."""
    laid = Counter(r["base"] for r in rows if not r.get("src") and r.get("kind") == "building" and r.get("why"))
    if laid:
        return sorted(laid, key=lambda b: (-laid[b], b))[0]
    ways = Counter(r["base"] for r in rows if r.get("kind") == "building"
                   and paths_mod.WALKWAY.search(str((bases.get(r["base"]) or {}).get("model", ""))))
    return sorted(ways, key=lambda b: (-ways[b], b))[0] if ways else None


def piece_length(bases: dict, base: str) -> float:
    bb = bases[base]["bounds"]
    return max(64.0, bb[1][1] - bb[0][1] - 16)


def lay(place_id: str, door_id: str, a, b, base: str, rows: list[dict], bases: dict, G,
        carrier: str | None = None) -> list[dict]:
    """Walkway pieces end to end from a to b ([x, y, z] each), their decks (the top surface of the mesh, geom.walk) on
    the line between the two heights. A piece rests on the `carrier`, the thing the door stands on (a ship's deck:
    the join is its gangway), and says so in its seat, so the build's overlap rule lets it (`check.rests`)."""
    from tools.places.draft import geom
    top = geom.walk(bases[base]) or 0.0
    length = piece_length(bases, base)
    near = [r for r in rows if r.get("kind") in overlap.SOLID and math.dist(r["pos"][:2], a[:2]) < math.dist(a[:2], b[:2]) + 4096]
    run = math.dist(a[:2], b[:2])
    n = max(1, math.ceil(run / length))
    yaw = math.atan2(b[0] - a[0], b[1] - a[1]) % (2 * math.pi)
    out = []
    for j in range(n):
        t = (j + 0.5) / n if run > length else 0.5
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        deck = float(a[2] + (b[2] - a[2]) * t)
        cand = {"id": io.mint(place_id, "join", door_id, str(j)), "base": base, "kind": "building",
                "pos": [round(x, 2), round(y, 2), round(deck - top, 2)], "rot": [0.0, 0.0, round(yaw, 5)], "scale": 1.0,
                "layer": "place", "flags": [], "src": None, "walk": top,
                "seat": {"mode": "free", **({"carrier": carrier} if carrier else {})},
                "why": f"joins door {door_id}'s walkable island to the town's network"}
        hit = overlap.hits(cand, near, bases)
        ways = [o for o in hit if paths_mod.WALKWAY.search(str((bases.get(o["base"]) or {}).get("model", "")))]
        if len(hit) > 1 or (hit and not ways):
            continue  # a door, a house or two pieces stand there: the join leaves that piece out
        if ways:
            cand["seat"]["on"] = ways[0]["id"]  # it rests on the walkway it continues
        out.append(cand)
    return out


def cut(place_id: str, door_ids: list[str], rows: list[dict], pdir: Path, log=print) -> int:
    """A door left on an island no level join reaches (a ship's hatch with no way aboard in the source) leads
    nowhere one can walk to: its room is left out with it, with the reason in the ledger, unless someone lives or
    works in that room (then it stays, and `draft check` lists the island). Returns the rooms left out."""
    import shutil
    used = set()
    for p in io.read_jsonl(pdir / "people.jsonl") if (pdir / "people.jsonl").exists() else []:
        used.add(p.get("home"))
        for k in ("bed", "work"):
            used.add((p.get(k) or {}).get("space"))
        used.update(s.get("space") for s in p.get("stops") or [] if isinstance(s, dict))
    by_id = {r["id"]: r for r in rows}
    gone, ledger = set(), []
    for did in door_ids:
        sid = ((by_id.get(did) or {}).get("door") or {}).get("to_space")
        sdir = pdir / "spaces" / str(sid)
        if not sid or sid == "exterior" or sid in used or not sdir.is_dir():
            continue
        sp = json.loads((sdir / "space.json").read_text())
        if sp.get("door_from") != did:
            continue   # a room with another way in stays
        why = (f"its only door {did} stands on a walkable island with no way to the town (the source gives no "
               f"way aboard) and nobody lives or works in it")
        gone.add(did)
        ledger.append({"src": by_id[did].get("src") or did, "space": "exterior", "status": "dropped", "why": why})
        ledger.append({"src": "*", "space": sid, "status": "dropped", "why": why})
        shutil.rmtree(sdir)
        log(f"join {place_id}: left out room {sid} and its door {did}: no way to it")
    if gone:
        dropped = {r["space"] for r in ledger if r["src"] == "*"}
        srcs = {r["src"] for r in ledger if r["src"] != "*"}
        # the links that led to a door left out go with it, and the walkway pieces laid to carry them
        pj, carried = pdir / "paths.jsonl", ()
        if pj.exists():
            paths = io.read_jsonl(pj)
            dead = [p for p in paths if p.get("from") in srcs or p.get("to") in srcs]
            if dead:
                carried = tuple(f"carries street {p['id'].rsplit('.', 1)[-1]} " for p in dead)
                io.write_jsonl(pj, [p for p in paths if p not in dead])
        io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl",
                       [r for r in rows if r["id"] not in gone and not str(r.get("why", "")).startswith(carried or ("\0",))])
        old = [r for r in io.read_jsonl(pdir / "ledger.jsonl") if r.get("space") not in dropped
               and not (r.get("space") == "exterior" and r.get("src") in srcs)]
        io.write_jsonl(pdir / "ledger.jsonl", old + ledger)
    return len(gone)


def rehome(place_id: str, W: "Walkable", bases: dict, src, pdir: Path, log=print) -> int:
    """A person whose bed outdoors (a camp bed) stands where the town's walkable network does not reach (a tent shut
    in by blocks) sleeps instead in a free bed of a home: the first room, by name, with a bed nobody has (never the
    inn's, whose beds are let); with none free, the last resident (residents only fill the beds left over) gives up
    theirs. Returns the people moved."""
    from tools.places import check as C
    from tools.places.draft import interiors
    rows = {r["id"]: r for r in io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")}

    def reached(pos) -> bool:   # within the build's own reach of a stop (a bed cuts the mesh round itself)
        return W.on(pos, tol=C.STOP_PLAN_TOL)
    ppl = io.read_jsonl(pdir / "people.jsonl")
    inns = {(p.get("work") or {}).get("space") for p in ppl
            if any((g.get("give_kind_id") or g.get("kind")) == "inn-room" for g in p.get("services") or [])}
    taken = Counter(((p.get("bed") or {}).get("space"), (p.get("bed") or {}).get("ref")) for p in ppl)
    free = []
    for sdir in sorted((pdir / "spaces").iterdir()):
        sp = json.loads((sdir / "space.json").read_text()) if (sdir / "space.json").exists() else None
        if not sp or sp["space_id"] == "exterior" or sp.get("parent") != "exterior" or sp["space_id"] in inns:
            continue
        src_space = str(sp.get("copy_of") or "").split("/")[-1]
        if src_space not in src.spaces:
            continue
        for b in interiors.beds_in(src.spaces[src_space].refs, bases, sp.get("room"), sp.get("copy_of")):
            free += [(sp["space_id"], b["ref"])] * max(0, b["sleeps"] - taken[(sp["space_id"], b["ref"])])
    moved = 0
    for p in ppl:
        bed = p.get("bed") or {}
        r = rows.get(bed.get("ref")) if bed.get("space") == "exterior" else None
        if r is None or reached(r["pos"]):
            continue
        if not free:   # residents only fill the beds left over: the last of them gives up a bed
            res = sorted((q for q in ppl if q.get("role") == "resident" and not q.get("_gone")
                          and (q.get("bed") or {}).get("space") not in (None, "exterior", *inns)), key=lambda q: q["id"])
            if not res:
                continue
            res[-1]["_gone"] = True
            free.append((res[-1]["bed"]["space"], res[-1]["bed"]["ref"]))
            log(f"join {place_id}: resident {res[-1]['id']} left out: a guard needs the bed")
        sid, ref = free.pop(0)
        log(f"join {place_id}: {p['id']} sleeps in {sid}: the camp bed {r['id']} is off the town's walkable network")
        p["bed"] = {**bed, "space": sid, "ref": ref}
        p["home"] = sid
        for st in p.get("routine") or []:
            if st.get("at") == bed:
                st["at"] = p["bed"]
        moved += 1
    if moved:
        io.write_jsonl(pdir / "people.jsonl", [q for q in ppl if not q.get("_gone")])
    return moved


ARRIVAL_LEVEL = 64.0    # units: a door's arrival stands on mesh within this of its own height (the deck it lands on)
ARRIVAL_ON = 16.0       # an arrival further than this over or under the mesh is put at the mesh's height (the detail mesh's error)
ARRIVAL_REACH = 288.0   # how far from where it was an arrival is moved to stand on the mesh


def arrivals(place_id: str, pdir: Path, W: Walkable, bases: dict, log=print) -> int:
    """Every door's arrival outside stands on the town's main walkable network of the built mesh, at its own level
    (on the deck or the ground it lands one on): one over or under the mesh there (on steps since raised) is put at
    the mesh's height; one off it is moved to the nearest point that is on it, on the
    same side of its door, outside every placed thing's body, at the mesh's height there. The partner door's `to_pos`
    and the door's `arrival` move together. Returns the arrivals moved."""
    from tools.places.draft import geom

    def level(q, z):   # the mesh's height at q on the main network at level z, else None
        c, dp, zz = W.near((q[0], q[1], z), tol=ON_TOL)
        m = W.main[c] & (np.abs(zz - z) <= ARRIVAL_LEVEL)
        return float(zz[m][np.argmin(dp[m])]) if m.any() else None
    ext = pdir / "spaces" / "exterior" / "refs.jsonl"
    rows = io.read_jsonl(ext)
    by_id = {r["id"]: r for r in rows}
    moved, inner_dirty = 0, {}
    for d in rows:
        a = (d.get("door") or {}).get("arrival")
        sid = (d.get("door") or {}).get("to_space")
        if d.get("kind") != "door" or not a or not sid or len(a) < 3:
            continue
        at = level(a, a[2])
        if at is None:      # the ground it stood on has since moved under it: the level nearest its own, where it is
            c, zz = W.stands(a[:2])
            near_z = float(zz[np.argmin(np.abs(zz - a[2]))]) if len(c) else None
            at = near_z if near_z is not None and abs(near_z - a[2]) <= Z_TOL else None
        if at is not None and abs(at - a[2]) <= ARRIVAL_ON:
            continue
        sup = by_id.get((d.get("seat") or {}).get("on"))
        near = [r for r in rows if r.get("kind") in geom.SOLID_KINDS and r is not d and r is not sup
                and math.dist(r["pos"][:2], a[:2]) < 2048]
        side = (a[0] - d["pos"][0], a[1] - d["pos"][1])
        got = [a[0], a[1], round(at, 2)] if at is not None else None   # where it is, at the mesh's own height
        for r_ in np.arange(8.0, ARRIVAL_REACH + 1, 8.0) if got is None else ():
            for k in range(32):
                q = (a[0] + r_ * math.cos(k * math.pi / 16), a[1] + r_ * math.sin(k * math.pi / 16))
                if (q[0] - d["pos"][0]) * side[0] + (q[1] - d["pos"][1]) * side[1] <= 0:
                    continue   # never behind its door
                z = level(q, a[2])
                if z is not None and not any(geom.stands_in(o, bases, (q[0], q[1], z)) for o in near):
                    got = [round(float(q[0]), 2), round(float(q[1]), 2), round(z, 2)]
                    break
            if got:
                break
        if got is None:
            log(f"join {place_id}: door {d['id']}: its arrival {[round(v) for v in a]} is off the walkable mesh, "
                f"with no point of it within {ARRIVAL_REACH:.0f} units")
            continue
        sp = pdir / "spaces" / sid / "refs.jsonl"
        inner = inner_dirty.get(sid) or (io.read_jsonl(sp) if sp.exists() else [])
        back = next((o for o in inner if (o.get("door") or {}).get("to_ref") == d["id"]), None)
        if back is None:
            continue
        yaw = math.atan2(got[0] - d["pos"][0], got[1] - d["pos"][1]) % (2 * math.pi)
        back["door"] = {**back["door"], "to_pos": got, "to_rot": [0.0, 0.0, round(yaw, 5)]}
        d["door"] = {**d["door"], "arrival": got}
        inner_dirty[sid] = inner
        moved += 1
        log(f"join {place_id}: door {d['id']}: arrival moved {math.dist(a[:2], got[:2]):.0f} units onto the walkable "
            f"mesh, z {a[2]:.0f} -> {got[2]:.0f}")
    if moved:
        io.write_jsonl(ext, rows)
        for sid, inner in inner_dirty.items():
            io.write_jsonl(pdir / "spaces" / sid / "refs.jsonl", inner)
    return moved


def stops(place_id: str, pdir: Path, W: Walkable, log=print) -> int:
    """A person's work stop outdoors named by a thing (the Hist a handler tends) whose spot the town's network does
    not reach, as the build looks a stop up, becomes the nearest point of the network beside it. Returns the stops
    moved."""
    from tools.places import check as C
    fj = pdir / "people.jsonl"
    folk = io.read_jsonl(fj) if fj.exists() else []
    rows = {r["id"]: r for r in io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")}
    n = 0
    for p in folk:
        w = p.get("work") or {}
        r = rows.get(w.get("ref")) if w.get("space") == "exterior" else None
        if r is None or W.on(r["pos"], tol=C.STOP_PLAN_TOL):
            continue
        q = W.snap(r["pos"][:2])
        if q is None:
            log(f"join {place_id}: {p['id']}: the work stop at {w['ref']} is off the walkable network, with no point "
                f"of it within {SNAP:.0f} units")
            continue
        new = {"space": "exterior", "pos": [round(float(q[0]), 1), round(float(q[1]), 1)], "radius": w.get("radius", 384)}
        for st in p.get("routine") or []:
            if st.get("at") == w:
                st["at"] = new
        p["work"], n = new, n + 1
        log(f"join {place_id}: {p['id']}: works beside {w['ref']}, at the nearest point of the walkable network")
    if n:
        io.write_jsonl(fj, folk)
    return n


def streets(place_id: str, pdir: Path, W: Walkable, world: list[dict] | None = None, log=print, bases: dict | None = None) -> int:
    """Every street lies on the town's main walkable network of the built mesh: a stretch off it is re-laid along the
    way the mesh walks (`mend`), said in the street's `laid`, and the world's plants (`world`, the ground bundle's)
    the new line reaches are cleared by the draft's own measure, and those whose body lies across it (`bases`: the
    ground bundle's, for their meshes); then each guard's patrol is taken again from the
    streets, every point on the network. Returns the changes (stretches re-laid and patrols changed)."""
    from tools.places.draft import people
    pj, fj = pdir / "paths.jsonl", pdir / "people.jsonl"
    paths = io.read_jsonl(pj) if pj.exists() else []
    n = 0
    for p in paths:
        got = mend(p, W)
        if got is None:
            log(f"join {place_id}: street {p['id']} has a stretch off the walkable network with no way round on it")
        elif got:
            n += got
            p["laid"] = f"{str(p.get('laid') or 'routed').split('; ')[0]}; re-laid on the built walkable network"
            log(f"join {place_id}: street {p['id']}: {got} stretch(es) re-laid on the built walkable network")
    if n:
        io.write_jsonl(pj, paths)
        cj, place = pdir / "clear.jsonl", json.loads((pdir / "place.json").read_text())
        if world and place.get("clearance"):
            from tools.places.draft import clear as clearmod
            rows = io.read_jsonl(cj) if cj.exists() else []
            relaid = [p for p in paths if "re-laid" in str(p.get("laid"))]
            more = clearmod.along(world, place["clearance"], relaid, {r.get("ref") for r in rows})
            from tools.places.draft import bodies
            solid = bodies.load(bases) if bases is not None else None
            if solid is not None:
                more += clearmod.across(world, {r.get("ref") for r in rows + more}, relaid, [], solid)
            if more:
                io.write_jsonl(cj, sorted(rows + more, key=lambda x: (x["pos"][0], x["pos"][1], x["base"])))
                log(f"join {place_id}: {len(more)} world plants cleared off the re-laid streets")
    folk = io.read_jsonl(fj) if fj.exists() else []
    guards = {io.mint(place_id, "person", "guard", str(k)): k for k in range(len(folk))}
    beats, changed = people.beats(paths), 0
    for g in folk:
        if g.get("role") != "guard" or g["id"] not in guards or not isinstance(g.get("patrol"), dict):
            continue
        pts = people.patrol(beats, guards[g["id"]], W.on)
        if not pts or pts == g["patrol"].get("points"):
            continue
        old = g.get("work")
        g["patrol"]["points"] = pts
        g["work"] = {**(old or {}), "space": "exterior", "pos": pts[0]}
        for st in g.get("routine") or []:
            if st.get("at") == old:
                st["at"] = g["work"]
        changed += 1
    if changed:
        io.write_jsonl(fj, folk)
        log(f"join {place_id}: {changed} guards' patrols taken again from the streets, on the walkable network")
    return n + changed


def finish(place_id: str, places: Path, bases: dict, log=print) -> int:
    """What the draft settles on the place files before the build, each a rule that leaves a file it already holds
    for as it was: the source's steps hung flush on their decks (`flush_steps`), the promises a resident keeps given
    to a resident (`people.give_to_residents`), and each person's name from the people source
    (`people.apply_identities`). Returns the rows changed."""
    from tools.places import identities
    from tools.places.draft import people
    from tools.places.draft.run import place_record
    pdir = places / place_id
    ext, fj = pdir / "spaces" / "exterior" / "refs.jsonl", pdir / "people.jsonl"
    rows = io.read_jsonl(ext)
    n = flush_steps(rows, bases, log)
    if n:
        io.write_jsonl(ext, rows)
    folk = io.read_jsonl(fj) if fj.exists() else []
    before = json.dumps(folk, sort_keys=True)
    place = json.loads((pdir / "place.json").read_text())
    who = identities.read(place_id, places)
    hist = next(iter(((place.get("stations") or {}).get("found") or {}).get("shrine") or []), None)
    for pid in people.give_to_residents(folk, place_record(place_id)[1], who, hist,
                                         people.routes_of(place_id)):
        log(f"join {place_id}: {pid} keeps a promise of the place beside their own life")
    people.apply_identities(folk, who)
    if json.dumps(folk, sort_keys=True) != before:
        was = {p["id"]: json.dumps(p, sort_keys=True) for p in json.loads(before)}
        n += sum(1 for p in folk if was.get(p["id"]) != json.dumps(p, sort_keys=True))
        io.write_jsonl(fj, folk)
    return n


def join(place_id: str, places: Path = io.PLACES, out: Path = CHECK_OUT, log=print) -> int:
    """Settle the place files (`finish`), build the place and read its walkable network; in each build round move the sleepers it does not reach
    (`rehome`), join every door's island to it by level walkway pieces, and once no island is left (or none can be
    joined) lay every street and patrol on it (`streets`); a round that changed what the mesh is built from (pieces,
    streets) builds again. Returns the changes made."""
    from tools.places import check as C
    pdir = places / place_id
    place = json.loads((pdir / "place.json").read_text())
    src = io.load(f"src.{place['source_id']}")
    grd = io.load(f"ground.{place_id}")
    bases = io.place_bases(src, grd, place)
    from tools.places.seat import Ground
    G = Ground.load(grd.path)
    G.apply_patches(io.read_jsonl(pdir / "land.jsonl") if (pdir / "land.jsonl").exists() else [])
    done = finish(place_id, places, bases, log)

    def settle():
        """The place files as they ship: reseated and in canonical order, so the build each round makes is the one
        `draft check` and the real build find unchanged."""
        from tools.places import edits
        from tools.places.seat import reseat_place
        reseat_place(place_id, places=places)
        edits.write_place(pdir, edits.load_place(pdir))
    settle()
    for _ in range(JOIN_ROUNDS):
        ctx, bad = network(place_id, places, out)
        if ctx is None:
            log(f"join {place_id}: the build failed: {bad[-1:]}")
            return done
        surf = C.surfaces(ctx)
        W = Walkable(ctx, *surf)
        # people moved to a reached bed change nothing the mesh is built from: no build round of their own
        moved = rehome(place_id, W, bases, src, pdir, log)
        # a deck that carries a door or a street and that the town reaches only by swimming (a pier above its
        # bank): one flight of the source's own steps brings it down; level pieces (below) only where heights agree
        Wd = Walkable(ctx, *surf, comp=C.components(ctx["navs"], C.door_pairs(ctx), C.water_level(ctx)))
        rows = io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")
        paths = io.read_jsonl(pdir / "paths.jsonl") if (pdir / "paths.jsonl").exists() else []
        have, new = {r["id"] for r in rows}, []
        # a street's deck that ends against a bank standing over it: one flight up the bank, before anything else
        # is judged cut off (what such a deck carries is an island only for want of it)
        up = bank_stairs(place_id, paths, Wd, rows, bases, steps_bases(rows, bases, G), G, log)
        for r in up:
            log(f"join {place_id}: {r['why']}: a flight of {r['base']} at {[round(v) for v in r['pos']]}, "
                f"hung on {r['seat']['on']}")
        if up:
            done += len(up) + moved
            io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", rows + up)
            settle()
            continue   # the flights are the network once built
        for key, (c, want) in sorted(deck_islands(ctx, Wd, paths).items()):
            got = [r for r in stairs(place_id, key, c, Wd, rows + new, bases, steps_bases(rows, bases, G), G, want)
                   if r["id"] not in have]
            if got:
                new += got
                have |= {r["id"] for r in got}
                log(f"join {place_id}: {key}: its deck joined to the town by a flight of {got[0]['base']} at "
                    f"{[round(v) for v in got[0]['pos']]}, hung on {got[0]['seat']['on']}")
            else:
                log(f"join {place_id}: {key}: its deck reaches the town only by swimming and no flight of steps fits")
        if new:
            done += len(new) + moved
            io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", rows + new)
            settle()
            continue   # the flights are the network once built
        isl = islands(ctx, W)
        if isl:
            rows = io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")
            base = walk_base(rows, bases)
            if base is None:
                log(f"join {place_id}: no walkway piece to join islands with")
                return done
            have = {r["id"] for r in rows}
            net = dry(W.cent[W.main], G)
            new, joined = [], set()
            # every island in one round, each by its shortest clear level join to the network
            for door_id, (c, pts) in sorted(isl.items()):
                if c in joined:
                    continue
                for d, a, b in pairs(dry(pts, G), net)[:TRIES]:
                    n = max(1, math.ceil(math.dist(a[:2], b[:2]) / piece_length(bases, base)))
                    carrier = ((next((r for r in rows if r["id"] == door_id), None) or {}).get("seat") or {}).get("on")
                    got = [r for r in lay(place_id, door_id, list(a), list(b), base, rows + new, bases, G, carrier)
                           if r["id"] not in have]
                    if len(got) == n:
                        new += got
                        have |= {r["id"] for r in got}
                        joined.add(c)
                        log(f"join {place_id}: door {door_id}: {n} pieces over {d:.0f} units, z {a[2]:.0f} -> {b[2]:.0f}")
                        break
            if new:
                done += len(new) + moved
                io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", rows + new)
                settle()
                continue   # the joined islands are the network once built
            log(f"join {place_id}: no island ({', '.join(sorted(isl))}) has a clear walkable way to the network")
            moved += cut(place_id, sorted(isl), rows, pdir, log)
        world = [r for r in (grd.exterior.refs if grd.exterior else []) if r.get("layer", "world") == "world"]
        got = arrivals(place_id, pdir, W, bases, log) + stops(place_id, pdir, W, log) + streets(place_id, pdir, W, world, log, bases)
        done += got + moved
        if got or moved:
            settle()
        if not got:
            break
        # the streets mark the mesh's road triangles: the next round proves the new lines on the mesh built with them
    return done


STEP_FLUSH = 64.0      # a flight whose top tread stands no further than this off its deck's height is hung flush on it
STEP_ABUT = 32.0       # plan units between a flight's top end and the deck edge it leaves that still abut
TREAD_MEET = 16.0      # a tread within this over the ground has met it (half the navmesh's climb)
BURY = 64.0            # flights are told apart by how much of their run the bank buries, in steps of this
STEPS = re.compile(r"step|stair", re.I)


def is_steps(r: dict, bases: dict) -> bool:
    return r.get("kind") == "building" and bool(STEPS.search(str((bases.get(r["base"]) or {}).get("model", ""))))


def steps_bases(rows: list[dict], bases: dict, G) -> list[str]:
    """The source's own steps pieces, the ones that bring a deck down to the water or a bank first: the place's steps
    and stair pieces standing over the water, commonest first, then the rest of its steps and stairs."""
    out: list[str] = []
    for pick in ([r for r in rows if is_steps(r, bases) and G.wet(r["pos"][0], r["pos"][1])],
                 [r for r in rows if is_steps(r, bases)]):
        got = Counter(r["base"] for r in pick)
        out += [b for b in sorted(got, key=lambda b: (-got[b], b)) if b not in out]
    return out


def flight(base: dict) -> dict | None:
    """A steps piece's walked profile along its run (the longer side of its box), read from its collision's treads:
    {axis, v (the middle across), top, foot (the run's two ends), us, zs (tread height every 16 units along it, top
    end first)}."""
    from tools.places import check as C
    from tools.places.seat import top_at
    bb = base.get("bounds")
    if not bb:
        return None
    up = C._up_faces(base.get("model"), [*bb[0], *bb[1]])
    if not len(up):
        return None
    axis = 0 if bb[1][0] - bb[0][0] >= bb[1][1] - bb[0][1] else 1
    v = (bb[0][1 - axis] + bb[1][1 - axis]) / 2
    prof = []
    for u in np.arange(bb[0][axis], bb[1][axis] + 1, 16.0):
        z = top_at(up, *((u, v) if axis == 0 else (v, u)))
        if z is not None:
            prof.append((float(u), z))
    if len(prof) < 2 or prof[0][1] == prof[-1][1]:
        return None
    ends = [float(bb[0][axis]), float(bb[1][axis])]
    if prof[0][1] < prof[-1][1]:
        prof.reverse()
        ends.reverse()
    return {"axis": axis, "v": v, "top": ends[0], "foot": ends[1], "us": [u for u, _ in prof], "zs": [z for _, z in prof]}


def to_world(r: dict, lx: float, ly: float) -> tuple[float, float]:
    """A point of a placed thing's own plan frame in the world (its yaw and scale; local +x is (cos rz, -sin rz))."""
    rz, s = (r.get("rot") or [0, 0, 0])[2], float(r.get("scale") or 1.0)
    c, sn = math.cos(rz), math.sin(rz)
    return r["pos"][0] + (lx * c + ly * sn) * s, r["pos"][1] + (-lx * sn + ly * c) * s


def to_local(r: dict, x: float, y: float) -> tuple[float, float]:
    rz, s = (r.get("rot") or [0, 0, 0])[2], float(r.get("scale") or 1.0)
    c, sn = math.cos(rz), math.sin(rz)
    dx, dy = x - r["pos"][0], y - r["pos"][1]
    return (dx * c - dy * sn) / s, (dx * sn + dy * c) / s


_RECT: dict = {}


def deck_rect(base: dict) -> tuple[float, tuple[float, float, float, float]] | None:
    """A level walkway piece's deck in its own frame: (its height over the origin, (x0, y0, x1, y1) of the upward
    faces of its collision at that height); None for a piece with no level deck (a flight of steps, a ramp)."""
    from tools.places import check as C
    from tools.places.draft import geom
    m = str(base.get("model") or "").lower()
    if m not in _RECT:
        got, w, bb = None, geom.walk(base), base.get("bounds")
        if w is not None and bb and not STEPS.search(m):
            up = C._up_faces(m, [*bb[0], *bb[1]])
            up = up[np.abs(up[:, :, 2] - w).max(axis=1) <= C.ON_TOP] if len(up) else up
            if len(up):
                lo, hi = up[:, :, :2].min(axis=(0, 1)), up[:, :, :2].max(axis=(0, 1))
                got = (float(w), (float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])))
        _RECT[m] = got
    return _RECT[m]


def decks(rows: list[dict], bases: dict) -> list[tuple[dict, float, tuple]]:
    """The place's level deck pieces: [(row, its deck's height in the world, its deck's box in its own frame)]."""
    out = []
    for r in rows:
        d = deck_rect(bases.get(r["base"]) or {}) if r.get("kind") == "building" else None
        if d is not None:
            out.append((r, r["pos"][2] + d[0] * float(r.get("scale") or 1.0), d[1]))
    return out


def hang(fl: dict, d: dict, deck_z: float, a, o, scale: float = 1.0) -> tuple[list[float], list[float], dict]:
    """A flight hung on deck piece d the way Skyrim.esm's dock steps hang on their decks (DockStepsDown01 and 02:
    square to the deck, the top end against its edge, the top tread at the deck's height): its origin, rotation and
    seat, its top end's middle at plan point a, running down along the unit plan direction o."""
    s = 1.0 if fl["foot"] > fl["top"] else -1.0
    ax = (o[0] * s, o[1] * s)                      # the local run axis (+u) in the world
    if fl["axis"] == 1:                            # local +y along ax: local +x is ax turned a quarter clockwise
        ax = (ax[1], -ax[0])
    rz = math.atan2(-ax[1], ax[0]) % (2 * math.pi)   # local +x is (cos rz, -sin rz) in the world
    c, sn = math.cos(rz), math.sin(rz)
    lu, lv = (fl["top"], fl["v"]) if fl["axis"] == 0 else (fl["v"], fl["top"])
    z = deck_z - fl["zs"][0] * scale
    pos = [round(float(a[0] - (lu * c + lv * sn) * scale), 2), round(float(a[1] - (-lu * sn + lv * c) * scale), 2),
           round(float(z), 2)]
    return pos, [0.0, 0.0, round(float(rz), 5)], {"mode": "on", "on": d["id"], "dz": round(float(z - d["pos"][2]), 2)}


def flush_steps(rows: list[dict], bases: dict, log=print) -> int:
    """A flight of the source's own steps whose top end abuts a deck's edge hangs on that deck: where the source set
    its top tread a little off the deck's height (within STEP_FLUSH; a step the navmesh does not climb), it is
    seated flush, `on` the deck piece, so deck and flight are one walked surface. Returns the flights reseated."""
    dk, n = decks(rows, bases), 0
    for r in rows:
        fl = flight(bases.get(r["base"]) or {}) if is_steps(r, bases) else None
        if fl is None:
            continue
        s = float(r.get("scale") or 1.0)
        top = to_world(r, *((fl["top"], fl["v"]) if fl["axis"] == 0 else (fl["v"], fl["top"])))
        tz = r["pos"][2] + fl["zs"][0] * s
        best = None
        for d, dz, (x0, y0, x1, y1) in dk:
            if d is r or abs(dz - tz) > STEP_FLUSH:
                continue
            lx, ly = to_local(d, *top)
            gap = math.hypot(max(x0 - lx, 0.0, lx - x1), max(y0 - ly, 0.0, ly - y1)) * float(d.get("scale") or 1.0)
            ox, oy = to_local(d, r["pos"][0], r["pos"][1])
            if gap <= STEP_ABUT and not (x0 <= ox <= x1 and y0 <= oy <= y1) and (best is None or gap < best[0]):
                best = (gap, d, dz)
        if best is None:
            continue
        _, d, dz = best
        z = round(dz - fl["zs"][0] * s, 2)
        seat = {**{k: v for k, v in (r.get("seat") or {}).items() if k == "foot"}, "mode": "on", "on": d["id"],
                "dz": round(z - d["pos"][2], 2)}
        if seat != r.get("seat"):
            log(f"steps {r['id']}: hung on deck {d['id']}, its top tread at the deck's height (it stood "
                f"{tz - dz:+.0f} off it)")
            r["seat"], r["pos"], n = seat, [r["pos"][0], r["pos"][1], z], n + 1
    return n


def stairs(place_id: str, key: str, c: int, Wd: "Walkable", rows: list[dict], bases: dict, sbases: list[str],
           G, want: list, every: bool = False) -> list[dict]:
    """One flight of the source's own steps from an island's deck down to the town's dry network, hung the way
    Skyrim.esm hangs dock steps (`hang`): off a free edge of one of the island's deck pieces, square to it, running
    down until its treads meet our ground where the town's network walks (the bank may bury the rest of its run, as
    a flight set into a slope; never a tread under the ground before that), its body clear of every solid by the
    build's overlap rule. Of the flights that fit, the one the bank buries least, then the nearest to where the
    island's streets and doors are (`want`); `every`: all that fit, best first. [] when none fits."""
    cand = []
    near = [r for r in rows if r.get("kind") in overlap.SOLID]
    for d, dz, (x0, y0, x1, y1) in decks(rows, bases):
        t = Wd.found((d["pos"][0], d["pos"][1], dz))[0]
        if t < 0 or int(Wd.comp[t]) != c:
            continue
        for e, (mx, my, ox, oy) in enumerate((((x0 + x1) / 2, y1, 0, 1), ((x0 + x1) / 2, y0, 0, -1),
                                             (x1, (y0 + y1) / 2, 1, 0), (x0, (y0 + y1) / 2, -1, 0))):
            a = to_world(d, mx, my)
            far = to_world(d, mx + ox, my + oy)
            o = (far[0] - a[0], far[1] - a[1])
            L = math.hypot(*o)
            o = (o[0] / L, o[1] / L)
            h = Wd.deck(a[0] + o[0] * 2 * STEP_ABUT, a[1] + o[1] * 2 * STEP_ABUT) if Wd.deck else None
            if h is not None and abs(h - dz) <= TREAD_MEET:
                continue   # the deck goes on there: no edge to leave it by
            for sbase in sbases:
                fl = flight(bases[sbase])
                if fl is None:
                    continue
                pos, rot, seat = hang(fl, d, dz, a, o)
                landed = buried = None
                for u, z in zip(fl["us"], fl["zs"]):
                    run = abs(u - fl["top"])
                    x, y = a[0] + o[0] * run, a[1] + o[1] * run
                    g, tz = G.height(x, y), pos[2] + z
                    if g is None or g > tz + 8:
                        break      # the ground stands over a tread: the flight would run into a bank
                    if tz - g <= TREAD_MEET:
                        landed, buried = (x, y, g), abs(fl["foot"] - u)
                        break
                if landed is None:
                    continue
                t = Wd.found(landed)[0]
                if t < 0 or not Wd.main[t]:
                    continue       # it comes down in water too deep to wade, or on ground the town does not reach
                row = {"id": io.mint(place_id, "steps", d["id"], str(e)), "base": sbase, "kind": "building",
                       "pos": pos, "rot": rot, "scale": 1.0, "layer": "place", "flags": [], "src": None,
                       "walk": geom_walk(bases[sbase]), "seat": seat,
                       "why": f"brings {key}'s deck down to the town's network"}
                if overlap.hits(row, near, bases):
                    continue
                to = min((math.dist(landed[:2], q[:2]) for q in want), default=0.0)
                cand.append((round(buried / BURY), round(to), row["id"], row))
    cand.sort(key=lambda t: t[:3])
    return [t[3] for t in (cand if every else cand[:1])]


BANK_REACH = 768.0     # how far along its street past a deck's end the top of the bank over it is looked for
BANK_NEAR = 512.0      # a bank flight whose top end is within this of where a street reaches the bank's top serves it
BANK_WHY = "from its deck up the bank that stands over it"
BANK_STEP = 16.0       # the street is read, and the flight's top end tried, every this many units


def bank_stairs(place_id: str, paths: list[dict], Wd: "Walkable", rows: list[dict], bases: dict, sbases: list[str],
                G, log=lambda *_: None) -> list[dict]:
    """One flight of the source's own steps wherever a street leaves a deck for a bank that stands over it by more
    than a step the mesh climbs and the mesh does not walk from one to the other (a low bridge that ends against a
    steep bank): hung on the deck piece the street leaves, square to it (`hang`), its top tread at the height of the
    bank's top where the town's network walks, running down over the deck until its treads meet the deck, which hides
    the rest of its run; never a tread under the ground, its body clear of every solid but its deck. Of the flights
    that fit one end (off any edge of any of the deck's pieces there), the one the deck hides least, then the one
    whose top is nearest where the street reaches the bank's top. [] when no street needs one."""
    dk = decks(rows, bases)
    near = [r for r in rows if r.get("kind") in overlap.SOLID]
    have = {r["id"] for r in rows}

    def deck_at(q):
        for d, dz, (x0, y0, x1, y1) in dk:
            if math.dist(d["pos"][:2], q) > 1024:
                continue
            lx, ly = to_local(d, q[0], q[1])
            g = G.height(q[0], q[1])
            if x0 <= lx <= x1 and y0 <= ly <= y1 and g is not None and g <= dz + TREAD_MEET:
                return d, dz, (x0, y0, x1, y1)
        return None

    def top(q):     # the ground at q where the town's network walks it, else None
        g = G.height(q[0], q[1])
        if g is None:
            return None
        t, dp, z = Wd.found((q[0], q[1], g))
        return g if t >= 0 and Wd.main[t] and dp <= ON_TOL and abs(z - g) <= CLIMB else None

    def top_end(r):  # where a hung flight's top end stands
        fl = flight(bases.get(r["base"]) or {})
        return to_world(r, *((fl["top"], fl["v"]) if fl["axis"] == 0 else (fl["v"], fl["top"]))) if fl else r["pos"][:2]
    tops = [top_end(r) for r in rows if str(r.get("why") or "").endswith(BANK_WHY)]
    out: list[dict] = []
    for p in paths:
        S = [q for _, q in samples(p.get("points") or [], BANK_STEP)]
        on = [deck_at(q) for q in S]
        for i in range(len(S) - 1):
            for a, b, step in ((i, i + 1, 1), (i + 1, i, -1)):       # the street leaves a deck at a for the land at b
                if on[a] is None or on[b] is not None:
                    continue
                d, dz, (x0, y0, x1, y1) = on[a]
                reach = range(b, min(len(S), b + int(BANK_REACH / BANK_STEP)) if step > 0
                              else max(-1, b - int(BANK_REACH / BANK_STEP)), step)
                k = next((j for j in reach if on[j] is None and top(S[j]) is not None), None)
                if k is None or top(S[k]) - dz <= CLIMB:
                    continue       # the bank is no higher than a step over the deck: the mesh walks it
                if all(Wd.line_ok(S[min(a, k):max(a, k) + 1])):
                    continue       # walked already (a flight stands there)
                hosts = [h for h in dk if abs(h[1] - dz) <= TREAD_MEET and math.dist(h[0]["pos"][:2], S[a]) <= 1024]
                if any(math.dist(q, S[k]) <= BANK_NEAR for q in tops):
                    continue       # this end has its flight (the street is laid over it with the rest)
                cand = []
                for h, hz, (hx0, hy0, hx1, hy1) in hosts:        # the deck's pieces at this end, each edge of each
                    c0 = to_world(h, (hx0 + hx1) / 2, (hy0 + hy1) / 2)
                    for e, (ox, oy) in enumerate(((0, 1), (0, -1), (1, 0), (-1, 0))):
                        rid = io.mint(place_id, "steps", h["id"], "bank", str(e))
                        far = to_world(h, (hx0 + hx1) / 2 + ox, (hy0 + hy1) / 2 + oy)
                        o = (far[0] - c0[0], far[1] - c0[1])
                        L = math.hypot(*o)
                        o = (o[0] / L, o[1] / L)     # the way the flight runs down: from the bank back over the deck
                        if rid in have or o[0] * (S[a][0] - S[k][0]) + o[1] * (S[a][1] - S[k][1]) <= 0:
                            continue
                        for s in np.arange(0.0, BANK_REACH + 1.0, BANK_STEP):
                            A = (c0[0] - o[0] * s, c0[1] - o[1] * s)
                            g = top(A)
                            if g is None or g - hz <= CLIMB:
                                continue
                            for sbase in sbases:
                                fl = flight(bases[sbase])
                                if fl is None:
                                    continue
                                pos, rot, seat = hang(fl, h, g, A, o)
                                hidden = None
                                for u, z in zip(fl["us"], fl["zs"]):
                                    run = abs(u - fl["top"])
                                    x, y = A[0] + o[0] * run, A[1] + o[1] * run
                                    gg, tz = G.height(x, y), pos[2] + z
                                    if gg is None or gg > tz + 8:
                                        break      # the ground stands over a tread
                                    if tz - hz <= TREAD_MEET:
                                        lx, ly = to_local(h, x, y)
                                        if hx0 <= lx <= hx1 and hy0 <= ly <= hy1 and tz >= hz - TREAD_MEET:
                                            hidden = abs(fl["foot"] - u)
                                        break
                                if hidden is None:
                                    continue
                                row = {"id": rid, "base": sbase, "kind": "building", "pos": pos, "rot": rot,
                                       "scale": 1.0, "layer": "place", "flags": [], "src": None,
                                       "walk": geom_walk(bases[sbase]), "seat": seat,
                                       "why": f"brings street {p['id'].rsplit('.', 1)[-1]} {BANK_WHY}"}
                                if not overlap.hits(row, near, bases):
                                    cand.append((round(hidden / BURY), round(math.dist(A, S[k]) / STEP), float(s),
                                                 sbase, rid, row))
                if cand:
                    row = min(cand, key=lambda c: c[:5])[5]
                    out.append(row)
                    have.add(row["id"])
                    tops.append(top_end(row))
                else:
                    log(f"join {place_id}: street {p['id']} leaves the deck of {d['id']} for a bank "
                        f"{top(S[k]) - dz:.0f} over it and no flight of steps fits")
    return out


def deck_islands(ctx: dict, Wd: "Walkable", paths: list[dict]) -> dict:
    """{key: (component, where its doors and streets are)} for each island of `Wd` (built on what joins without
    swimming) that carries a door of ours or a street on a deck of ours: a pier or a ship the town reaches only by
    swimming. The key is the door's id, else the street's."""
    from tools.places import check as C
    out: dict = {}
    for door_id, (c, pts) in sorted(islands(ctx, Wd).items()):
        out.setdefault(c, (door_id, []))[1].append(tuple(pts.mean(axis=0)[:2]))
    for p in paths:
        for _, q in samples(p["points"]):
            t = Wd.found(q)[0]
            h = Wd.deck(q[0], q[1]) if Wd.deck else None
            if t >= 0 and not Wd.main[t] and h is not None and abs(h - Wd.cent[t, 2]) <= C.DECK_TOL:
                out.setdefault(int(Wd.comp[t]), (p["id"], []))[1].append(q)
    return {key: (c, pts) for c, (key, pts) in out.items()}


def geom_walk(base: dict) -> float | None:
    from tools.places.draft import geom
    return geom.walk(base)
