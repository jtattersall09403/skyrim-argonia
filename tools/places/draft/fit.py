"""Fit: where and how the source place sits on our land.

1. Global: one rigid turn and shift of the whole source onto our anchor, searched coarse then fine, scoring every
   cluster at once (water where the source had water and land where it had land, ground under each building no
   steeper than the source's own, nothing off our map). The landing counts LANDING_WEIGHT times: it must reach our
   real water.
2. Local: each cluster in turn (landing first, then buildings largest first) is shifted and turned a little from
   the global placement when that lowers its own cost, held back by the distance it moves, by how far its shift
   differs from its fitted neighbours' (so who neighbours whom and which way each faces stays) and by overlap
   with buildings already placed. Street clusters come last, held to the shifts of the clusters round them, so
   streets stay continuous.
3. Patches: a building whose ground is still steeper than the source's own or wet where the source was dry gets a
   land patch, the last resort, each with its reason.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from tools.places.draft import geom
from tools.places.draft.cluster import Cluster
from tools.places.seat import STEP, Ground, foot_points, foot_relief

LANDING_WEIGHT = 3.0
COARSE_SAMPLES = 6
W_WET, W_SLOPE, W_OFF = 10.0, 1.0, 50.0
W_MOVE, W_TURN, W_NEIGH, W_OVERLAP = 0.6, 0.4, 0.8, 6.0
RELIEF_SLACK, RELIEF_MIN = 48.0, 64.0


def relief_allowed(src_relief: float, seat: dict) -> float | None:
    """How far the ground under a building may rise: the source's own rise and some slack, or as deep as the source
    sank it; None when it does not stand on the ground (bridges, piers, things on other things)."""
    if seat.get("mode") != "ground":
        return None
    return max(src_relief + RELIEF_SLACK, RELIEF_MIN, -float(seat.get("dz", 0.0)))
LOCAL_SHIFTS = [-384.0, -256.0, -128.0, 0.0, 128.0, 256.0, 384.0]
LOCAL_TURNS = [math.radians(a) for a in (-15, -7.5, 0, 7.5, 15)]
LANDING_SHIFTS = [-1024.0, -768.0, -512.0, -256.0, 0.0, 256.0, 512.0, 768.0, 1024.0]


@dataclass
class Fit:
    pivot: tuple[float, float]
    anchor: tuple[float, float]
    xf: geom.Xf
    per: dict[str, geom.Xf] = field(default_factory=dict)
    local: dict[str, dict] = field(default_factory=dict)       # cluster -> {dx, dy, drot, cost_before, cost_after}
    patches: list[dict] = field(default_factory=list)
    cost: float = 0.0

    def warp(self, x: float, y: float) -> tuple[float, float]:
        """A source point not in a cluster: the global map plus the inverse-distance mean of nearby local moves."""
        gx, gy = self.xf.pt(x, y)
        num_x = num_y = den = 0.0
        for cid, c in self._centres.items():
            d2 = (x - c[0]) ** 2 + (y - c[1]) ** 2 + 256.0 ** 2
            px, py = self.per[cid].pt(x, y)
            num_x += (px - gx) / d2
            num_y += (py - gy) / d2
            den += 1 / d2
        return (gx + num_x / den, gy + num_y / den) if den else (gx, gy)

    _centres: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"pivot": [round(v, 1) for v in self.pivot], "anchor": [round(v, 1) for v in self.anchor],
                "rot_deg": round(math.degrees(self.xf.rot) % 360, 2), "cost": round(self.cost, 3),
                "clusters": {cid: {**self.per[cid].as_dict(), **self.local.get(cid, {})} for cid in sorted(self.per)}}


class Scorer:
    def __init__(self, clusters: list[Cluster], src: Ground, ours: Ground):
        self.src, self.ours = src, ours
        self.clusters = clusters
        self.src_relief = {(c.id, f[0]): foot_relief(src, f[1], f[2], f[3], f[4]) for c in clusters for f in c.feet}
        # the landing must reach our water whatever the town's size: a quarter of all the clusters' weight
        self.landing_weight = max(LANDING_WEIGHT, 0.25 * len(clusters))

    def cost(self, c: Cluster, xf: geom.Xf, coarse: bool = False) -> float:
        g = self.ours
        wet = c.wet[::4] if coarse and len(c.wet) > 16 else c.wet
        miss = off = 0
        for px, py, w in wet:
            qx, qy = xf.pt(px, py)
            if not g.has(qx, qy):
                off += 1
            elif g.wet(qx, qy) != w:
                miss += 1
        n = max(len(wet), 1)
        cost = W_WET * miss / n + W_OFF * off / n
        if c.kind != "landing":
            for fid, x, y, rz, f in c.feet:
                qx, qy = xf.pt(x, y)
                rel = foot_relief(g, qx, qy, xf.yaw(rz), f)
                allow = max(self.src_relief[(c.id, fid)] + RELIEF_SLACK, RELIEF_MIN)
                cost += W_SLOPE * max(0.0, rel - allow) / 128.0
        return cost * (self.landing_weight if c.kind == "landing" else 1.0)

    def total(self, xf: geom.Xf, coarse: bool = False) -> float:
        if not coarse:
            return sum(self.cost(c, xf) for c in self.clusters)
        if not hasattr(self, "_pool"):
            pool, heads = [], []
            for c in self.clusters:
                wl = self.landing_weight if c.kind == "landing" else 1.0
                take = c.wet[::max(1, len(c.wet) // COARSE_SAMPLES)][:COARSE_SAMPLES]
                pool.extend((px, py, w, wl / max(len(take), 1)) for px, py, w in take)
                if c.feet:
                    f = max(c.feet, key=lambda f: f[4][0] * f[4][1])
                    heads.append((f, self.src_relief[(c.id, f[0])]))
            self._pool, self._heads = pool, heads
        g = self.ours
        cost = 0.0
        for px, py, w, wt in self._pool:
            qx, qy = xf.pt(px, py)
            if not g.has(qx, qy):
                cost += W_OFF * wt
            elif g.wet(qx, qy) != w:
                cost += W_WET * wt
        for (fid, x, y, rz, f), srel in self._heads:
            qx, qy = xf.pt(x, y)
            rel = foot_relief(g, qx, qy, xf.yaw(rz), f)
            cost += W_SLOPE * max(0.0, rel - max(srel + RELIEF_SLACK, RELIEF_MIN)) / 128.0
        return cost


def _pivot(clusters: list[Cluster]) -> tuple[float, float]:
    pts = [c.centre for c in clusters if c.kind != "street"] or [c.centre for c in clusters]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def global_fit(sc: Scorer, pivot, anchor, rot_deg: float | None, search: float) -> geom.Xf:
    rots = [math.radians(rot_deg)] if rot_deg is not None else [math.radians(a) for a in range(0, 360, 15)]
    best = None
    step = max(search / 4, 256.0)
    n = int(search // step)
    for r in rots:
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                xf = geom.Xf(pivot, (anchor[0] + i * step, anchor[1] + j * step), r)
                k = (round(sc.total(xf, coarse=True), 6), abs(i) + abs(j), r)
                if best is None or k < best[0]:
                    best = (k, xf)
    xf = best[1]
    # refine: half the step at a time, turns of a few degrees
    fine_rots = [0.0] if rot_deg is not None else [math.radians(a) for a in (-5, -2.5, 0, 2.5, 5)]
    while step > STEP / 2:
        step /= 2
        cur = (round(sc.total(xf), 6), xf)
        for dr in fine_rots:
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    cand = geom.Xf(pivot, (xf.to[0] + i * step, xf.to[1] + j * step), xf.rot + dr)
                    k = round(sc.total(cand), 6)
                    if k < cur[0]:
                        cur = (k, cand)
        xf = cur[1]
    return xf


def _overlap(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    d = math.hypot(a[0] - b[0], a[1] - b[1])
    return max(0.0, a[2] + b[2] - d) / 128.0


def local_fit(sc: Scorer, clusters: list[Cluster], xf: geom.Xf, bases_radius: dict[str, float]) -> Fit:
    fit = Fit(xf.pivot, xf.to, xf)
    fit._centres = {c.id: c.centre for c in clusters}
    order = sorted(clusters, key=lambda c: (c.kind != "landing", c.kind != "building",
                                            -sum(f[4][0] * f[4][1] for f in c.feet), c.id))
    shifts: dict[str, tuple[float, float]] = {}
    circles: list[tuple[float, float, float]] = []
    for c in order:
        before = sc.cost(c, xf)
        about = xf.pt(*c.centre)
        rng = LANDING_SHIFTS if c.kind == "landing" else LOCAL_SHIFTS
        neigh = [(shifts[o.id], geom.dist(c.centre, o.centre)) for o in clusters
                 if o.id in shifts and geom.dist(c.centre, o.centre) < 2048]
        best = None
        for dr in LOCAL_TURNS:
            for dx in rng:
                for dy in rng:
                    cand = xf.then(dx, dy, dr, about)
                    k = sc.cost(c, cand)
                    k += W_MOVE * (dx * dx + dy * dy) / 256.0 ** 2 + W_TURN * (dr / math.radians(15)) ** 2
                    if neigh:
                        wsum = sum(1 / (d + 256) for _, d in neigh)
                        mx = sum(s[0] / (d + 256) for s, d in neigh) / wsum
                        my = sum(s[1] / (d + 256) for s, d in neigh) / wsum
                        k += W_NEIGH * ((dx - mx) ** 2 + (dy - my) ** 2) / 256.0 ** 2
                    if c.kind == "building":
                        mine = [(*cand.pt(f[1], f[2]), math.hypot(*f[4])) for f in c.feet[:1]]
                        k += W_OVERLAP * sum(_overlap(m, o) for m in mine for o in circles)
                    key = (round(k, 6), abs(dx) + abs(dy), abs(dr))
                    if best is None or key < best[0]:
                        best = (key, cand, dx, dy, dr)
        _, cand, dx, dy, dr = best
        fit.per[c.id] = cand
        shifts[c.id] = (dx, dy)
        if c.kind == "building":
            circles.extend((*cand.pt(f[1], f[2]), math.hypot(*f[4])) for f in c.feet[:1])
        fit.local[c.id] = {"dx": dx, "dy": dy, "drot_deg": round(math.degrees(dr), 2),
                           "cost_before": round(before, 3), "cost_after": round(sc.cost(c, cand), 3)}
    fit.cost = round(sum(sc.cost(c, fit.per[c.id]) for c in clusters), 3)
    return fit


def patch_verts(ours: Ground, x: float, y: float, rz: float, f, target: float) -> dict:
    """Vertex offsets that bring the land under a footprint (and a vertex beyond) to `target`, blended out over
    the next vertex and a half: {(cx, cy): [[row, col, dz]...]} (an edge vertex is written to both cells)."""
    half = math.hypot(*f) + 2 * STEP
    verts: dict[tuple[int, int], list] = {}
    gx0, gx1 = math.floor((x - half) / STEP), math.ceil((x + half) / STEP)
    gy0, gy1 = math.floor((y - half) / STEP), math.ceil((y + half) / STEP)
    c, s = math.cos(rz), math.sin(rz)
    for gx in range(gx0, gx1 + 1):
        for gy in range(gy0, gy1 + 1):
            dx, dy = gx * STEP - x, gy * STEP - y
            u, v = abs(dx * c - dy * s), abs(dx * s + dy * c)
            out = max(u - f[0], v - f[1], 0.0)
            if out > 2 * STEP:
                continue
            blend = 1.0 if out <= STEP else max(0.0, 1 - (out - STEP) / STEP)
            h = ours.vertex(gx, gy)
            if h is None or blend <= 0:
                continue
            dz = round((target - h) * blend, 1)
            if abs(dz) < 1:
                continue
            cx, col = divmod(gx, 32)
            cy, row = divmod(gy, 32)
            verts.setdefault((cx, cy), []).append([row, col, dz])
            if col == 0:
                verts.setdefault((cx - 1, cy), []).append([row, 32, dz])
            if row == 0:
                verts.setdefault((cx, cy - 1), []).append([32, col, dz])
            if col == 0 and row == 0:
                verts.setdefault((cx - 1, cy - 1), []).append([32, 32, dz])
    return verts


def patch_for(ours: Ground, src: Ground, r_src: dict, x: float, y: float, rz: float, f, kind: str,
              src_relief: float | None, which: str = "both", seat: dict | None = None) -> tuple[float, str] | None:
    """The land patch one placed thing still needs after the fit, as (target height, reason), or None.

    - a building on ground steeper than the source's own: level to the median under it;
    - a thing on our dry land that stood in the source's water: lowered to the source's depth under the surface;
    - a thing in our water that stood on the source's dry land: raised to the source's height above the water.
    """
    sx, sy = r_src["pos"][0], r_src["pos"][1]
    sw, ow = src.wet(sx, sy, 16), ours.wet(x, y, 16)
    w = ours.water(x, y)
    if sw != ow and w is not None and which in ("wet", "both") and (seat or {}).get("mode") != "above":
        sh, swl = src.height(sx, sy), src.water(sx, sy)
        if sw:
            depth = max(48.0, (swl - sh) if swl is not None and sh is not None else 48.0)
            return w - depth, "stood in the source's water; our land here is dry"
        above = max(32.0, (sh - swl) if swl is not None and sh is not None else 32.0)
        return w + above, "stood on the source's dry land; our water is here"
    if kind == "building" and f and src_relief is not None and which in ("relief", "both"):
        allow = relief_allowed(src_relief, seat or {"mode": "ground"})
        rel = foot_relief(ours, x, y, rz, f)
        if allow is not None and rel > allow:
            hs = sorted(h for h in (ours.height(px, py) for px, py in foot_points(x, y, rz, f, 5)) if h is not None)
            return hs[len(hs) // 2], f"ground under it rises {rel:.0f} units against the source's {src_relief:.0f}"
    return None
