"""A road's ground and its measured profile (1.15 round 4, owner play test 3 finding 21: "roads poorly implemented:
just flat texture"). Golden rule 0034: the numbers are Skyrim.esm's, measured on the Whiterun-Riverwood road
(cells 1..9, -13..0; terrain/probes/vanilla_roads.py + vanilla_roads_measure.py; the record is
docs/research/2026-11-03/lane-1.15-r4-roads.md):

- across, the road is the low line of a shallow trough, never a crown or a ditch: the ground beside it rises, folded
  over both sides, by the median TROUGH_M at 0..8 m (p25..p75 at 2 m 0.03..0.13 m, at 4 m 0.18..0.45 m);
- along, the grade is p50 0.053, p95 0.164, max 0.219 (rise over run, 8 m baseline);
- the paint: a dirt core across the flat width, blending to the land's own texture over ~4 m each side
  (LDirt02 + the default dirt 0.70 at the centre, 0.62 at 5 m, 0.53 at 8 m) - material.py's road blend;
- the statics: no edge posts or stones at a spacing; Road* surface meshes on 2.2 km of the road and RoadChunk
  stones scattered on it (lateral p50 2.8 m, 15 per 100 m where present); rocks and fences are the land's (10 m off).

`shape(h, roads)` lays each road into the ground: the centreline height is the ground smoothed along (SMOOTH_M),
held to GRADE_MAX by a forward and a backward pass, set half the core's trough into the ground; every sample within
the core (half flat width + shoulder) takes centre + TROUGH(d), blended back to the ground over BLEND_M.
`profile(h, roads)` measures the same on any ground (the L1 check, routes.profile).
"""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su

MPP = su.PROVINCE_SAMPLE_M
TROUGH_AT_M = np.arange(0.0, 9.0)
TROUGH_M = np.array([0.0, 0.02, 0.09, 0.19, 0.29, 0.40, 0.55, 0.69, 0.83])  # vanilla's fold, median
# the shaped fold comes out shallower than its target (the 1 m caps on a side slope, the bank fades, the blend and
# the slope limit after): the target is deepened by this so the measured fold meets vanilla's medians (check: fold_*)
TROUGH_GAIN = 1.35
TROUGH_BAND = {2.0: (0.03, 0.13), 4.0: (0.18, 0.45)}  # p25..p75 at 2 m and 4 m out
GRADE_MAX = 0.219  # vanilla's steepest road grade
GRADE_P95 = 0.164
GRADE_BASE_M = 8.0  # the grade's baseline (vanilla measured over +-4 m)
SMOOTH_M = 6.0  # the centreline smoothed along over +-this
WALL_M = 0.3  # a step across a road's edge past the land's own: a wall (the planner's rule, round 4)
MAX_CUT_M = 1.0  # a road is never cut or filled more than this from the land (L3 reader: a 3 m cut wall)
CROSS_KEEP = 0.4  # the share of the land's cross fall a road keeps (the wall check's slope window)
SITE_REACH = 1.5  # a place's shaped ground in the census: its site eased out to SITE_BLEND radii (generate.py)
ROAD_RAISED = "road-raised-u8.npy"  # generate: the samples dry_corridor raised (the census's bank grade)
ROAD_WATER = "road-water-u8.npy"  # generate writes the road pass's water mask beside the ground (the check's census)
DELTA_LIP = 0.2  # the road's change between neighbour samples, at most (m): its walls stay under WALL_M
# Skyrim.esm's own roads (vanilla/measure.py q12, 2026-11-04: the LAND under Tamriel's 1571 road-surface meshes,
# the same 8 m grade and the census's edge-wall test): 23.4 % of points steeper than GRADE_MAX, 6.8 % of side points
# a wall, 9.6 % within 16 m of water. GRADE_MAX (the r4 Whiterun box's max) is the shaping target, not the bar
VANILLA_ROADS = {"steep_share": 0.2342, "walls_per_side_point": 0.0681}
LAT_EDGE_M = 0.1  # the cut or fill at a road's edge, at most (m), growing LAT_RATE_M a sample toward the centre: the
LAT_RATE_M = 0.15  # bench's cut bank stays under WALL_M past the land's own step (the lateral cap, r6)
FADE_ITER = 40  # the blend's harmonic fade: Jacobi sweeps (the band is ~5 samples wide; 40 sweeps settle it)
BLEND_M = 9.0  # the road's ground blends back to the land over this beyond its core (vanilla's fold flattens by 8 m)


def trough(d_m):
    return np.interp(d_m, TROUGH_AT_M, TROUGH_M)


def _dense(pts: np.ndarray, step: float = 1.0):
    """(k, 2) polyline in samples -> (m, 2) at `step` samples, with the cumulative length of each point."""
    seg = np.diff(pts, axis=0)
    ln = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(ln)])
    t = np.linspace(0.0, cum[-1], max(2, int(np.ceil(cum[-1] / step)) + 1))
    return np.stack([np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])], 1), t


def bilinear(h: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """h at (col x, row y) samples."""
    n = h.shape[0] - 1
    x, y = np.clip(x, 0, n - 1e-6), np.clip(y, 0, n - 1e-6)
    c, r = np.floor(x).astype(int), np.floor(y).astype(int)
    fc, fr = x - c, y - r
    return (h[r, c] * (1 - fc) * (1 - fr) + h[r, c + 1] * fc * (1 - fr) + h[r + 1, c] * (1 - fc) * fr
            + h[r + 1, c + 1] * fc * fr)


def grade_limit(z: np.ndarray, ds_m: float, g: float) -> np.ndarray:
    """The tightest profile under z's mean that keeps every step within g x ds: a forward and a backward pass of
    min/max cones, averaged (the cut and the fill share the change)."""
    lip = g * ds_m
    up = z.copy()
    for i in range(1, len(up)):  # an upper envelope: never rises faster than the lip from behind
        up[i] = min(up[i], up[i - 1] + lip)
    for i in range(len(up) - 2, -1, -1):
        up[i] = min(up[i], up[i + 1] + lip)
    lo = z.copy()
    for i in range(1, len(lo)):
        lo[i] = max(lo[i], lo[i - 1] - lip)
    for i in range(len(lo) - 2, -1, -1):
        lo[i] = max(lo[i], lo[i + 1] - lip)
    out = 0.5 * (up + lo)
    for _ in range(3):  # the mean of two lipschitz profiles is lipschitz; this only guards rounding
        d = np.clip(np.diff(out), -lip, lip)
        out = out[0] + np.concatenate([[0.0], np.cumsum(d)])
    return out


def _runs(m: np.ndarray) -> list[tuple[int, int]]:
    """[start, end) of each run of True."""
    d = np.diff(np.concatenate([[0], m.astype(np.int8), [0]]))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def centreline(h: np.ndarray, p: np.ndarray, core_m: float) -> np.ndarray:
    """The road's centre height at each dense point of one dry run: the ground smoothed along over +-SMOOTH_M,
    grade-limited, set half the core's trough into the ground."""
    z = bilinear(h, p[:, 0], p[:, 1])
    k = max(1, int(round(SMOOTH_M / MPP)))
    zp = np.concatenate([np.full(k, z[0]), z, np.full(k, z[-1])])
    c = np.cumsum(np.concatenate([[0.0], zp]))
    zs = (c[2 * k + 1:] - c[:-2 * k - 1]) / (2 * k + 1)
    return grade_within(zs, z, MPP, GRADE_MAX * 0.85) - 0.5 * TROUGH_GAIN * trough(core_m)  # headroom: trough, 8 m baseline


def cone_env(b: np.ndarray, lip: float, op) -> np.ndarray:
    """The lip-Lipschitz envelope of b: min over j of b_j + lip |i - j| (op=min) or max of b_j - lip |i - j|."""
    sg = 1.0 if op is min else -1.0
    e = b.copy()
    for i in range(1, len(e)):
        e[i] = op(e[i], e[i - 1] + sg * lip)
    for i in range(len(e) - 2, -1, -1):
        e[i] = op(e[i], e[i + 1] + sg * lip)
    return e


def grade_within(zs: np.ndarray, z: np.ndarray, ds_m: float, g: float) -> np.ndarray:
    """The grade-limited profile of zs held within MAX_CUT_M of the land z and still within g: the band
    [z - cut, z + cut] narrowed to its g-Lipschitz envelopes (lo' = max cone of the floor, hi' = min cone of the
    roof), so clipping the limited profile into it keeps the grade (a min/max of g-Lipschitz profiles is one).
    Where the land itself is too steep for any such profile (lo' > hi': a slope longer than the cut can take) the
    road takes the band's middle there, and the point is a re-route's (routes/build.py), never a deeper cut."""
    lip = g * ds_m
    lo = cone_env(z - MAX_CUT_M, lip, max)
    hi = cone_env(z + MAX_CUT_M, lip, min)
    out = np.clip(grade_limit(zs, ds_m, g), np.minimum(lo, hi), np.maximum(lo, hi))
    bad = lo > hi
    out[bad] = 0.5 * (lo[bad] + hi[bad])
    return np.clip(out, z - MAX_CUT_M, z + MAX_CUT_M)


def _nearest(shape, p: np.ndarray, reach: float):
    """For every grid sample within `reach` samples of the dense polyline p: (rows, cols, distance in samples, index
    of the nearest dense point)."""
    n = shape[0] - 1
    r = int(np.ceil(reach))
    oy, ox = np.mgrid[-r:r + 1, -r:r + 1]
    best: dict[int, tuple[float, int]] = {}
    rr_all, cc_all, dd_all, ii_all = [], [], [], []
    for i0 in range(0, len(p), 512):
        q = p[i0:i0 + 512]
        rr = (np.rint(q[:, 1])[:, None] + oy.ravel()[None]).astype(np.int64)
        cc = (np.rint(q[:, 0])[:, None] + ox.ravel()[None]).astype(np.int64)
        dd = np.hypot(cc - q[:, 0:1], rr - q[:, 1:2])
        ii = np.broadcast_to(np.arange(i0, i0 + len(q))[:, None], dd.shape)
        ok = (dd <= reach) & (rr >= 0) & (rr <= n) & (cc >= 0) & (cc <= n)
        rr_all.append(rr[ok]); cc_all.append(cc[ok]); dd_all.append(dd[ok]); ii_all.append(ii[ok])
    del best
    rr, cc, dd, ii = (np.concatenate(a) for a in (rr_all, cc_all, dd_all, ii_all))
    if not len(rr):
        return rr, cc, dd, ii
    key = rr * (n + 1) + cc
    o = np.lexsort((dd, key))
    key, rr, cc, dd, ii = key[o], rr[o], cc[o], dd[o], ii[o]
    first = np.concatenate([[True], key[1:] != key[:-1]])
    return rr[first], cc[first], dd[first], ii[first]


def shape(h: np.ndarray, roads: list[tuple[np.ndarray, float]], water: np.ndarray | None = None,
          lo: np.ndarray | None = None, hi: np.ndarray | None = None) -> dict:
    """Lay every road ((k, 2) polyline in (col, row) samples, core half width in samples) into h in place.

    The road yields to water (`water`: a bed, gully, channel or wet-raster sample): the centreline is cut into dry
    runs at every water point, each run shaped on its own, its weight tapering to 0 over BLEND_M toward a bank, and
    no water sample is shaped; so a crossing keeps the water's graded bed and banks. With lo/hi (generate's cones)
    the target is held inside them before the blend, so the clip after never cuts a wall into the road."""
    num = np.zeros(h.shape)  # sum of weight x target: where two roads reach a sample, their targets blend by weight
    den = np.zeros(h.shape)
    wgt = np.zeros(h.shape)
    core_m_ = np.zeros(h.shape, bool)  # the road's own surface (within its core half width)
    n = runs_n = 0
    taper_n = max(1, int(round(BLEND_M / MPP)))
    bank_w = None
    if water is not None:  # the fade follows the bank: a road sample's weight eases to 0 at the water beside it,
        # so a road running along a bank or a crossing's wing never stands a step over the untouched water sample
        from tools.argonia_world.terrain.generate import chamfer
        dw, _ = chamfer(water, int(np.ceil(BLEND_M / MPP)) + 1)
        bank_w = np.clip(np.where(np.isfinite(dw), dw * MPP / BLEND_M, 1.0), 0.0, 1.0)
        bank_w = bank_w * bank_w * (3 - 2 * bank_w)
    for pts, core in roads:
        core_m = core * MPP
        p, _s = _dense(pts)
        if water is not None:
            wp = water[np.clip(np.rint(p[:, 1]).astype(int), 0, h.shape[0] - 1),
                       np.clip(np.rint(p[:, 0]).astype(int), 0, h.shape[1] - 1)]
        else:
            wp = np.zeros(len(p), bool)
        for a0, a1 in _runs(~wp):
            if a1 - a0 < 3:
                continue
            q = p[a0:a1]
            zc = centreline(h, q, core_m)
            # taper toward a bank: full weight taper_n points in from a water end, none at it (a road end is full)
            idx = np.arange(a1 - a0, dtype=np.float64)
            tap = np.ones(a1 - a0)
            if a0 > 0:
                tap = np.minimum(tap, idx / taper_n)
            if a1 < len(p):
                tap = np.minimum(tap, (a1 - a0 - 1 - idx) / taper_n)
            tap = np.clip(tap, 0.0, 1.0)
            rr, cc, dd, ii = _nearest(h.shape, q, core + BLEND_M / MPP)
            d_m = dd * MPP
            w = np.clip(1.0 - (d_m - core_m) / BLEND_M, 0.0, 1.0)
            w = w * w * (3 - 2 * w) * tap[ii]
            # across a slope the road keeps CROSS_KEEP of the land's own fall (a bench, cut uphill and filled
            # downhill, never a flat shelf with a fill wall on its low side); on the flat this is ~0
            zg = bilinear(h, q[:, 0], q[:, 1])
            # the lateral cap (r6): the bench (the land's cross fall the road gives up) is at most LAT_EDGE_M at the
            # core's edge, growing LAT_RATE_M a sample inward, so its cut bank never stands a wall over WALL_M (gen0:
            # a 0.4 keep on a 0.5 side slope cut 0.7 m at the edge, 52 walls the road made); the along-road evening
            # (zc - zg) is not capped by it
            cap = np.minimum(MAX_CUT_M, LAT_EDGE_M + LAT_RATE_M * np.maximum(core_m - d_m, 0.0) / MPP)
            cross = h[rr, cc] - zg[ii]
            t = zc[ii] + TROUGH_GAIN * trough(d_m) + cross + np.clip((CROSS_KEEP - 1.0) * cross, -cap, cap)
            t = np.clip(t, h[rr, cc] - MAX_CUT_M, h[rr, cc] + MAX_CUT_M)  # never a cut or fill over 1 m
            if bank_w is not None:
                w = w * bank_w[rr, cc]
            if lo is not None:
                t = np.minimum(np.maximum(t, lo[rr, cc]), np.maximum(hi[rr, cc], lo[rr, cc]))
            keep = w > 0
            if water is not None:
                keep &= ~water[rr, cc]
            rr, cc, w, t = rr[keep], cc[keep], w[keep], t[keep]
            num[rr, cc] += w * t
            den[rr, cc] += w
            np.maximum.at(wgt, (rr, cc), w)
            core_m_[rr, cc] |= d_m[keep] <= core_m
            n += int((d_m <= core_m).sum())
            runs_n += 1
    m = wgt > 0
    # the road's change is held inside DELTA_LIP cones from every sample it may not move (0 on water and off the
    # corridors; a site's pin and a bank's freeboard by their bounds), so no shaped sample stands a step over an
    # untouched neighbour: the fade follows the bank. Inside the road the change is free (it evens the land's steps)
    dz = np.zeros(h.shape)
    dz[m] = (num[m] / den[m] - h[m]) * wgt[m]
    free = m.copy() if water is None else m & ~water
    lod = np.where(free, -np.inf, 0.0)
    hid = np.where(free, np.inf, 0.0)
    if lo is not None:
        lod = np.where(free & np.isfinite(lo), np.maximum(lo - h, -1e6), lod)
        hid = np.where(free & np.isfinite(hi), np.minimum(hi - h, 1e6), hid)
    from tools.argonia_world.terrain.generate import majorant, minorant
    a, b = majorant(np.maximum(lod, -1e6), DELTA_LIP), minorant(np.minimum(hid, 1e6), DELTA_LIP)
    dz = np.minimum(np.maximum(dz, a), np.maximum(b, a))
    # the lateral cap (r6): beyond the core the road's change fades out harmonically (each blend sample the mean of
    # its neighbours, the core and the frozen samples held), so a cut or fill never stands a step at the road's edge
    # (gen0: 52 walls the road made, a 1 m cut faded by a smoothstep over 3 samples); the cones still bound it
    band = m & ~core_m_
    if water is not None:
        band &= ~water
    if band.any():
        ys, xs = np.nonzero(band)
        y0, y1, x0, x1 = max(ys.min() - 1, 0), ys.max() + 2, max(xs.min() - 1, 0), xs.max() + 2
        sub, bs = dz[y0:y1, x0:x1].copy(), band[y0:y1, x0:x1]
        for _ in range(FADE_ITER):
            p_ = np.pad(sub, 1, mode="edge")
            avg = (p_[:-2, 1:-1] + p_[2:, 1:-1] + p_[1:-1, :-2] + p_[1:-1, 2:]) / 4
            sub = np.where(bs, avg, sub)
        dz[y0:y1, x0:x1] = sub
        dz = np.minimum(np.maximum(dz, a), np.maximum(b, a))
    h += dz
    return {"roads": len(roads), "dry_runs": runs_n, "core_samples": n, "shaped_samples": int(m.sum())}


CAUSEWAY_SHOULDER_M = 6.0  # the corridor held dry: the road's core plus this each side (the pass's fade)
CAUSEWAY_M = 0.5  # the corridor's ground stands this far above its cell's highest water (planner, 2026-11-04 20:15)
FORD_M = 0.3  # a reach crossing's bed under its level, at most (Skyrim.esm's road fords: p50 0.16 m, max 1.23 m)
STEP_M = 0.5  # a vertex whose cells' levels differ by more is a step (water/solve.py RIFFLE_M)
# Skyrim.esm's roadside embankment (0034; probes/vanilla_road_banks.py on Tamriel cells -20..20 x -25..10, 578 road
# meshes, 257 sides where the road stands above the land): the fall over the 8 m beside the road edge, p50 0.077,
# p95 0.304, p99 0.429, max 0.580 (m per m). A causeway's bank is held to the p99 per road.
BANK_BAND_M = 8.0
BANK_BAR = 0.429
BANK_BAR_SOURCE = "Skyrim.esm roadside fall over 8 m beside the edge, p99 (probes/vanilla_road_banks.py)"
FORD_GAP = 2  # samples between a ford and the causeway left to the ground (the ramp from the top to the bed)


def corridor(shape_, roads, extra_m: float = CAUSEWAY_SHOULDER_M) -> np.ndarray:
    """The samples within each road's core half width plus `extra_m`."""
    m = np.zeros(shape_, bool)
    for pts, core in roads:
        rr, cc, _d, _i = _nearest(shape_, _dense(pts)[0], core + extra_m / MPP)
        m[rr, cc] = True
    return m


def dry_corridor(roads, lo, hi, role, vmin, vmax, reach, keep=None) -> dict:
    """A road is never under water (lane 1.15-r6-roads-dry): in each road's corridor the ground's lower bound
    stands CAUSEWAY_M over the cell's highest water and the sample leaves the footprint (role 3, no upper bound), the
    bank falling from it at GRADE_MAX until it meets the water's own bed (a footprint sample the bank needs above the
    water becomes bank too: the causeway widens with the depth); where the corridor crosses a reach (`reach`, a river
    or stream) the wet samples are a ford, the bed held FORD_M under the level. `keep` (a step's channel) is never
    touched: the step chain stays. lo, hi, role change in place; returns the masks and counts."""
    from tools.argonia_world.terrain.generate import chamfer, majorant
    has = np.isfinite(vmin)
    keep = np.zeros(lo.shape, bool) if keep is None else keep
    cor = corridor(lo.shape, roads) & has
    rd, _ = chamfer(reach, FORD_GAP + 2)
    # the ford: the reach's wet samples and the ring the causeway leaves beside it (lane fix 2: the ring kept the
    # field's carved bed, fords to 4.1 m)
    near_f = cor & np.isfinite(rd) & (rd <= FORD_GAP) & ~reach
    cw = cor & ~reach & ~near_f & ~keep
    ford = cor & (role == 1) & (reach | near_f) & ~keep
    top = np.where(cw, vmax + CAUSEWAY_M, -np.inf)
    cone = majorant(np.where(cw, top, -1e9), GRADE_MAX * MPP)
    cone = np.where(cone > -1e8, cone, -np.inf)
    free = ~keep & ~ford & ~near_f & ~reach
    from tools.argonia_world.terrain.generate import FREEBOARD_M
    flip = free & has & (role == 1) & (cone > vmin - FREEBOARD_M)
    bank = (cw | flip)
    lo0 = lo.copy()
    lo[free] = np.maximum(lo[free], cone[free])
    lo[flip] = np.maximum(lo[flip], vmax[flip] + FREEBOARD_M)
    hi[bank] = np.inf
    role[bank & has] = 3
    lo[ford] = vmin[ford] - FORD_M
    hi[ford] = np.minimum(hi[ford], vmin[ford] - FORD_M)
    # a step's channel under a road: its bed no deeper than FORD_M under the vertex's lowest water (the chain kept:
    # the bed stays under its level, only a deeper end is lifted)
    sc = cor & keep & np.isfinite(hi)
    cap = vmin - FORD_M
    deep = sc & (hi < cap)
    lo[deep] = cap[deep]
    hi[deep] = cap[deep]
    raised = (lo > lo0) | bank
    return {"causeway": cw, "bank": bank, "ford": ford | deep, "raised": raised,
            "stats": {"causeway_samples": int(cw.sum()), "flipped_samples": int((flip & ~cw).sum()),
                      "ford_samples": int(ford.sum()),
                      "step_channel_capped": int(deep.sum())}}


def _at(a: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return a[np.clip(np.rint(y).astype(int), 0, a.shape[0] - 1), np.clip(np.rint(x).astype(int), 0, a.shape[1] - 1)]


def frame(pts: np.ndarray, step: float = 2.0):
    """The dense centreline at `step` samples, its unit tangent and its left normal."""
    p, _s = _dense(pts, step)
    v = np.gradient(p, axis=0)
    v /= np.maximum(np.hypot(v[:, 0], v[:, 1]), 1e-9)[:, None]
    return p, v, np.stack([-v[:, 1], v[:, 0]], 1)


def corridor_reach(shape, roads) -> np.ndarray:
    """How many roads' corridors reach each sample: a wall test whose outside sample lies in another road's corridor
    reads that road's trough (a track beside a road, a junction), not a wall."""
    reach = np.zeros(shape, np.int8)
    for pts, core in roads:
        rr, cc, _d, _i = _nearest(shape, _dense(pts)[0], core + BLEND_M / MPP)
        reach[rr, cc] += 1
    return reach


def edge_walls(h, p, nrm, core, sg, reach) -> np.ndarray:
    """A wall at each point on side sg: a step across the road's edge more than WALL_M beyond the land's own step
    just outside it (outside samples in another road's corridor skipped)."""
    zz = [bilinear(h, p[:, 0] + sg * nrm[:, 0] * (core + o), p[:, 1] + sg * nrm[:, 1] * (core + o))
          for o in (-0.5, 0.5, 1.5)]
    alone = _at(reach, p[:, 0] + sg * nrm[:, 0] * (core + 0.5), p[:, 1] + sg * nrm[:, 1] * (core + 0.5)) <= 1
    return (np.abs(zz[1] - zz[0]) > WALL_M + np.abs(zz[2] - zz[1])) & alone


def grade_along(h, p, v) -> np.ndarray:
    """|rise| / run over the GRADE_BASE_M baseline at each point (0 within half a baseline of the ends)."""
    half = GRADE_BASE_M / 2 / MPP
    za = bilinear(h, p[:, 0] + v[:, 0] * half, p[:, 1] + v[:, 1] * half)
    zb = bilinear(h, p[:, 0] - v[:, 0] * half, p[:, 1] - v[:, 1] * half)
    g = np.abs(za - zb) / GRADE_BASE_M
    e = int(np.ceil(half / 2.0))
    g[:e] = g[-e:] = 0.0
    return g


def census(h, h_pre, lo, hi, water, roads, wet, sites=()) -> dict:
    """Every wall and every dry over-steep point on ground h, tagged by cause from the data (first that holds):
    crossing - within the taper (core + BLEND_M) of a water point on the centreline, or a water sample or a water's
    bank/bed cone holding the ground (h at lo or hi) within 2 samples of the edge (steep: of the centreline); pinned - a site core's
    pin (lo == hi) or a place's site disc within 2 samples; land - the same test on the ground before the roads (h_pre) already fails there (a step in the
    land, or the land's own grade); other."""
    reach = corridor_reach(h.shape, roads)
    if lo is not None:
        pin = np.isfinite(lo) & np.isfinite(hi) & (np.abs(hi - lo) < 0.05)  # a site core's pin (lo == hi)
        bank = ((np.abs(h - lo) < 0.01) | (np.abs(h - hi) < 0.01)) & ~pin  # a water's bank or bed cone binding h
    else:  # the check on a written ground: no cones, the water mask and the sites only
        pin, bank = np.zeros(h.shape, bool), np.zeros(h.shape, bool)
    for st in sites:  # a place's shaped ground (its site out to the blend): the place's to grade, not the road's
        cy, cx, r = st["y_m"] / MPP, st["x_m"] / MPP, st["radius_m"] / MPP * SITE_REACH
        r0, r1 = int(max(cy - r, 0)), int(min(cy + r + 1, h.shape[0]))
        c0, c1 = int(max(cx - r, 0)), int(min(cx + r + 1, h.shape[1]))
        yy, xx = np.mgrid[r0:r1, c0:c1]
        pin[r0:r1, c0:c1] |= np.hypot(yy - cy, xx - cx) <= r
    pin2, bank2 = pin.copy(), bank | water
    for ax in (0, 1):
        for d in (-2, -1, 1, 2):
            pin2 |= np.roll(pin, d, ax)
            bank2 |= np.roll(bank | water, d, ax)
    made = {"walls": 0, "steep": 0}  # not in the ground before the roads (h_pre): what the road itself made
    walls = {"crossing": 0, "pinned": 0, "land": 0, "other": 0}
    steep = {"crossing": 0, "pinned": 0, "land": 0, "other": 0}
    where = {"walls": [], "steep": []}
    for ri, (pts, core) in enumerate(roads):
        p, v, nrm = frame(pts)
        if len(p) < 5:
            continue
        wp = _at(water, p[:, 0], p[:, 1])
        # along-road distance (samples) to the nearest water point on the centreline
        idx = np.nonzero(wp)[0]
        pos = np.arange(len(p)) * 2.0
        dw = np.full(len(p), np.inf) if not len(idx) else np.min(np.abs(pos[:, None] - pos[idx][None]), 1) \
            if len(idx) * len(p) < 5e7 else np.full(len(p), np.inf)
        near_w = dw <= core + BLEND_M / MPP
        for sg in (1.0, -1.0):
            wl = edge_walls(h, p, nrm, core, sg, reach)
            wl0 = edge_walls(h_pre, p, nrm, core, sg, reach) if h_pre is not None else np.zeros(len(p), bool)
            ex, ey = p[:, 0] + sg * nrm[:, 0] * (core + 0.5), p[:, 1] + sg * nrm[:, 1] * (core + 0.5)
            wet_e = np.zeros(len(p), bool)
            for o in (-1.5, -0.5, 0.5, 1.5, 2.5):
                wet_e |= _at(water, p[:, 0] + sg * nrm[:, 0] * (core + o), p[:, 1] + sg * nrm[:, 1] * (core + o))
            wet_e |= _at(bank2, ex, ey)
            pe = _at(pin2, ex, ey) | _at(pin2, p[:, 0] + sg * nrm[:, 0] * (core - 0.5), p[:, 1] + sg * nrm[:, 1] * (core - 0.5))
            made["walls"] += int((wl & ~wl0).sum()) if h_pre is not None else 0
            for i in np.nonzero(wl)[0]:
                c = "crossing" if near_w[i] or wet_e[i] else "pinned" if pe[i] else "land" if wl0[i] else "other"
                walls[c] += 1
                where["walls"].append((ri, int(i), c, round(float(p[i, 0] * MPP)), round(float(p[i, 1] * MPP)),
                                       bool(not wl0[i]), sg))
        g = grade_along(h, p, v)
        g0 = grade_along(h_pre, p, v) if h_pre is not None else np.zeros(len(p))
        rl = np.isfinite(_at(wet, p[:, 0], p[:, 1])) if wet is not None else np.zeros(len(p), bool)
        pc = _at(pin2, p[:, 0], p[:, 1])
        near_w = near_w | _at(bank2, p[:, 0], p[:, 1])
        made["steep"] += int(((g > GRADE_MAX + 1e-6) & ~rl & (g0 <= GRADE_MAX)).sum()) if h_pre is not None else 0
        for i in np.nonzero((g > GRADE_MAX + 1e-6) & ~rl)[0]:
            c = "crossing" if near_w[i] else "pinned" if pc[i] else "land" if g0[i] > GRADE_MAX else "other"
            steep[c] += 1
            where["steep"].append((ri, int(i), c, round(float(p[i, 0] * MPP)), round(float(p[i, 1] * MPP)), round(float(g0[i]), 3)))
    return {"walls": walls, "steep": steep, "made_by_road": made, "where": where}


def profile(h: np.ndarray, roads: list[tuple[np.ndarray, float]], wet=None) -> dict:
    """Measure every road on ground h: the folded cross profile at 2 and 4 m (median, share in the vanilla band),
    the grade along (p50/p95/max, the count of centreline points steeper than GRADE_MAX), and the centreline
    points under water (wet: the wet level raster, NaN dry); a point on the wet raster is a crossing, not road grade.
    The trough fold is measured on roads (core >= 4 m), vanilla's class; tracks report their own median."""
    fold = {2.0: [], 4.0: []}
    track_fold = []
    grades, steep, wet_pts, total, crossings, cross_pts, walls = [], 0, 0, 0, 0, 0, 0
    reach = corridor_reach(h.shape, roads)
    for pts, _core in roads:
        p, _s = _dense(pts, 2.0)
        if len(p) < 5:
            continue
        v = np.gradient(p, axis=0)
        v /= np.maximum(np.hypot(v[:, 0], v[:, 1]), 1e-9)[:, None]
        nrm = np.stack([-v[:, 1], v[:, 0]], 1)
        z0 = bilinear(h, p[:, 0], p[:, 1])
        for o in fold:
            a = bilinear(h, p[:, 0] + nrm[:, 0] * o / MPP, p[:, 1] + nrm[:, 1] * o / MPP)
            b = bilinear(h, p[:, 0] - nrm[:, 0] * o / MPP, p[:, 1] - nrm[:, 1] * o / MPP)
            (fold[o] if _core * MPP >= 4.0 else track_fold if o == 4.0 else []).append((a + b) / 2 - z0)
        for sg in (1.0, -1.0):
            walls += int(edge_walls(h, p, nrm, _core, sg, reach).sum())
        g = grade_along(h, p, v)
        if wet is not None:  # a point on the wet raster (a water's footprint) is a crossing, not road grade:
            # `crossings` counts its runs, each a place that wants a bridge or a ford
            lv = wet[np.clip(np.rint(p[:, 1]).astype(int), 0, wet.shape[0] - 1),
                     np.clip(np.rint(p[:, 0]).astype(int), 0, wet.shape[1] - 1)]
            rl = np.isfinite(lv)
            wet_pts += int((rl & (lv > z0)).sum())
            cross_pts += int(rl.sum())
            crossings += int((rl[1:] & ~rl[:-1]).sum() + rl[0])
            dry = ~rl
        else:
            dry = np.ones(len(p), bool)
        g = g[dry]
        grades.append(g)
        steep += int((g > GRADE_MAX + 1e-6).sum())
        total += len(p)
    g = np.concatenate(grades)
    out = {"points": total, "grade_p50": round(float(np.percentile(g, 50)), 3),
           "grade_p95": round(float(np.percentile(g, 95)), 3), "grade_max": round(float(g.max()), 3),
           "steeper_than_max": steep, "under_water": wet_pts, "crossings": crossings, "crossing_points": cross_pts, "walls": walls}
    if track_fold:
        out["track_fold_4m_median"] = round(float(np.median(np.concatenate(track_fold))), 3)
    for o, a in fold.items():
        a = np.concatenate(a)
        lo, hi = TROUGH_BAND[o]
        out[f"fold_{o:.0f}m_median"] = round(float(np.median(a)), 3)
        out[f"fold_{o:.0f}m_in_band"] = round(float(((a >= lo - 0.05) & (a <= hi + 0.05)).mean()), 3)
    return out


def load_roads(w) -> list[tuple[np.ndarray, float]]:
    """The roads as generate.Inputs reads them: ((k, 2) (col, row) samples, core half width in samples)."""
    pts: dict[str, list] = {}
    for p in w.query("SELECT route_id, x_m, y_m FROM road_point ORDER BY route_id, ord"):
        pts.setdefault(p["route_id"], []).append((p["x_m"] / MPP, p["y_m"] / MPP))
    return [(np.asarray(pts[r["route_id"]]), (r["flat_width_m"] / 2 + r["shoulder_m"]) / MPP)
            for r in w.query("SELECT route_id, flat_width_m, shoulder_m FROM road ORDER BY route_id")
            if len(pts.get(r["route_id"], [])) >= 2]


def main(argv=None) -> int:
    """`check [GROUND.npy]`: L1 - the road profile on the generated ground (default the shared out/terrain one).
    Fails on any dry road point steeper than GRADE_MAX or a fold median outside the vanilla band."""
    import argparse
    import json
    from pathlib import Path

    from tools.argonia_world import db
    from tools.argonia_world.terrain import cellwater
    from tools.argonia_world.terrain.grid import generated_ground

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "census"])
    ap.add_argument("ground", nargs="?")
    ap.add_argument("--dump", help="census: generate's ARGONIA_ROAD_DUMP (.npz): the road pass replayed on it")
    a = ap.parse_args(argv)
    w = db.open()
    if a.cmd == "census":
        return census_main(w, a) if a.dump else wet_main(w, a)
    gp = Path(a.ground or generated_ground())
    h = np.asarray(np.load(gp, mmap_mode="r"), np.float64)
    wet, _ = cellwater.wet_raster(w)
    roads = load_roads(w)
    res = profile(h, roads, wet)
    fails = []
    # the census: walls and steep points beside a water crossing (owed to bridges) or on a place's site (owed to
    # the places lane) are listed, not failed; every other one fails (generate writes the road pass's water mask)
    wm = gp.with_name(ROAD_WATER)
    water = np.load(wm) > 0 if wm.exists() else np.isfinite(wet)
    sp = gp.with_name("entrance-sites.json")
    c = census(h, None, None, None, water, roads, wet, json.loads(sp.read_text()) if sp.exists() else ())
    res["walls_by_cause"], res["steep_by_cause"] = c["walls"], c["steep"]
    res["owed_sample_m"] = {k: [x[2:5] for x in c["where"][k] if x[2] in ("crossing", "pinned")][::25]
                            for k in ("walls", "steep")}  # (cause, x, y) every 25th: the full list is census()'s
    res["own_sample_m"] = {k: [x[2:5] for x in c["where"][k] if x[2] not in ("crossing", "pinned")][:40]
                           for k in ("walls", "steep")}
    # the bar is Skyrim.esm's own roads (q12, VANILLA_ROADS): shares over every road point, all causes counted
    n_pts = res["points"]
    ws, ss = sum(c["walls"].values()) / max(1, 2 * n_pts), sum(c["steep"].values()) / max(1, n_pts)
    res["walls_per_side_point"], res["steep_share"], res["vanilla_roads"] = round(ws, 4), round(ss, 4), VANILLA_ROADS
    if ss > VANILLA_ROADS["steep_share"]:
        fails.append(f"steep share {ss:.4f} of road points over Skyrim.esm's {VANILLA_ROADS['steep_share']}")
    if ws > VANILLA_ROADS["walls_per_side_point"]:
        fails.append(f"walls {ws:.4f} a side point over Skyrim.esm's {VANILLA_ROADS['walls_per_side_point']}")
    for o, (lo, hi) in TROUGH_BAND.items():
        m = res[f"fold_{o:.0f}m_median"]
        if not lo <= m <= hi:
            fails.append(f"fold at {o:.0f} m median {m} outside vanilla's {lo}..{hi}")
    res["fails"] = fails
    print(json.dumps(res, indent=1))
    return 1 if fails else 0


def wet_census(h, roads, ids, level, reach, step: float = 1.0, raised=None, rid=None, rnames=None, drop=None) -> dict:
    """Per road on ground h: metres under its cell's water (`level`, per sample, NaN dry) outside fords, the longest
    wet run, the fords (wet runs touching a reach: count, deepest), the causeway metres (dry over a cell with water)
    and the bank's steepest grade beside the causeway (core edge out to 30 m, where the ground falls to the water)."""
    out = {}
    for name, (pts, core) in zip(ids, roads):
        p, v, nrm = frame(pts, step)
        z, lv = bilinear(h, p[:, 0], p[:, 1]), _at(level, p[:, 0], p[:, 1])
        wet = np.isfinite(lv) & (z < lv)
        rch = np.zeros(len(p), bool)
        for o in np.arange(-core, core + 0.5, 1.0):
            rch |= _at(reach, p[:, 0] + nrm[:, 0] * o, p[:, 1] + nrm[:, 1] * o)
        ds = step * MPP
        fords, under, longest, deepest, steps_x = [], 0.0, 0.0, None, []
        for a0, a1 in _runs(wet):
            seg = slice(a0, a1)
            depth = float((lv[seg] - z[seg]).max())
            if drop is not None and (_at(drop, p[seg, 0], p[seg, 1]) > STEP_M).any():
                k = a0 + int(np.argmax(_at(drop, p[seg, 0], p[seg, 1])))
                steps_x.append({"drop_m": round(float(_at(drop, p[k:k + 1, 0], p[k:k + 1, 1])[0]), 2),
                                "at_m": [round(float(p[k, 0] * MPP)), round(float(p[k, 1] * MPP))]})
                continue  # a road over a step (a fall between two cells' levels): a bridge, never a ford
            if rch[max(a0 - 2, 0):a1 + 2].any():
                fords.append(round(depth, 2))
                if rid is not None and (deepest is None or depth > deepest["depth_m"]):
                    k = a0 + int(np.argmax(lv[seg] - z[seg]))
                    near = [int(_at(rid, p[k, 0] + nrm[k, 0] * o, p[k, 1] + nrm[k, 1] * o))
                            for o in np.arange(-core - 4, core + 4.5, 1.0)]
                    near = [x for x in near if x >= 0]
                    deepest = {"depth_m": round(depth, 2), "at_m": [round(float(p[k, 0] * MPP)), round(float(p[k, 1] * MPP))],
                               "reach": rnames[max(set(near), key=near.count)] if near and rnames else None}
            else:
                under += (a1 - a0) * ds
                longest = max(longest, (a1 - a0) * ds)
        cw = np.isfinite(lv) & ~wet & (z < lv + CAUSEWAY_M + 1.0)  # low dry ground over a cell's water
        # the bank: the fall from the core's edge over BANK_BAND_M beside it, on the sides where the road stands
        # above the land, where generate raised the ground (Skyrim.esm's bar, BANK_BAR)
        falls = []
        if cw.any():
            for sg in (-1, 1):
                xa, ya = p[cw, 0] + sg * nrm[cw, 0] * core, p[cw, 1] + sg * nrm[cw, 1] * core
                ob = core + BANK_BAND_M / MPP
                xb, yb = p[cw, 0] + sg * nrm[cw, 0] * ob, p[cw, 1] + sg * nrm[cw, 1] * ob
                fall = (bilinear(h, xa, ya) - bilinear(h, xb, yb)) / BANK_BAND_M
                m = fall > 0
                if raised is not None:
                    mid = core + BANK_BAND_M / MPP / 2
                    m &= _at(raised, p[cw, 0] + sg * nrm[cw, 0] * mid, p[cw, 1] + sg * nrm[cw, 1] * mid) > 0
                falls.append(fall[m])
        falls = np.concatenate(falls) if falls else np.zeros(0)
        g = float(falls.max()) if len(falls) else 0.0
        g99 = float(np.percentile(falls, 99)) if len(falls) else 0.0
        out[name] = {"length_m": round(len(p) * ds), "under_m": round(under), "longest_wet_m": round(longest),
                    "fords": len(fords), "ford_max_m": max(fords) if fords else 0.0,
                    "causeway_m": round(float(cw.sum()) * ds), "bank_max_grade": round(g, 3),
                    "bank_p99": round(g99, 3), "deepest_ford": deepest, "step_crossings": steps_x}
    return out


def wet_main(w, a) -> int:
    """`census [GROUND.npy]`: every road's wet census on the generated ground (lane 1.15-r6-roads-dry). Fails on any
    metre under water outside a ford, a ford deeper than FORD_M, or a bank steeper than GRADE_MAX (the slope's
    lip-limit is the land's elsewhere, so the bank grade is reported against the bar)."""
    import json
    from pathlib import Path

    from tools.argonia_world.terrain import cellwater
    from tools.argonia_world.terrain.generate import Q
    from tools.argonia_world.terrain.grid import data_root, generated_ground
    gp = Path(a.ground or generated_ground())
    h = np.asarray(np.load(gp, mmap_mode="r"), np.float64)
    wl = cellwater.load(w).level
    level = np.pad(np.repeat(np.repeat(wl, Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge")[:h.shape[0], :h.shape[1]]
    rl, rid = cellwater.reach_raster(w, h.shape[0])
    rnames = [f"{r['id']} ({r['kind']}, {r['width_m']} m)"
              for r in w.query("SELECT id, kind, width_m FROM hydrology_reach ORDER BY id")]
    rp = gp.with_name(ROAD_RAISED)
    raised = np.load(rp) if rp.exists() else None
    zb = np.load(data_root() / "hydrology-graph-bodies.npz")
    reach = ~np.isnan(rl) & ~np.isfinite(zb["level"]) & ~zb["sea"]
    ids = [r["route_id"] for r in w.query("SELECT route_id FROM road ORDER BY route_id")]
    pts: dict[str, list] = {}
    for p in w.query("SELECT route_id, x_m, y_m FROM road_point ORDER BY route_id, ord"):
        pts.setdefault(p["route_id"], []).append(1)
    ids = [i for i in ids if len(pts.get(i, [])) >= 2]
    from tools.argonia_world.terrain.generate import vertex_levels
    vmin, vmax = vertex_levels(wl)
    drop = np.nan_to_num(vmax - vmin, nan=0.0)[:h.shape[0], :h.shape[1]]
    for _ in range(3):  # a step's channel runs a few samples into the lower cell: the drop carried to it
        drop = np.maximum.reduce([drop, np.roll(drop, 1, 0), np.roll(drop, -1, 0), np.roll(drop, 1, 1), np.roll(drop, -1, 1)])
    res = wet_census(h, load_roads(w), ids, level, reach, raised=raised, rid=rid, rnames=rnames, drop=drop)
    tot = {k: round(sum(r[k] for r in res.values()), 1) for k in ("length_m", "under_m", "causeway_m", "fords")}
    tot["roads_wet"] = sum(r["under_m"] > 0 for r in res.values())
    tot["ford_max_m"] = max([r["ford_max_m"] for r in res.values()] or [0])
    tot["bank_max_grade"] = max([r["bank_max_grade"] for r in res.values()] or [0])
    fails = [f"{k}: {r['under_m']} m under water" for k, r in res.items() if r["under_m"] > 0]
    fails += [f"{k}: ford {r['ford_max_m']} m" for k, r in res.items() if r["ford_max_m"] > FORD_M + 0.01]
    fails += [f"{k}: bank p99 {r['bank_p99']} over the bar {BANK_BAR}" for k, r in res.items()
              if raised is not None and r["bank_p99"] > BANK_BAR]
    tot["bridge_candidates"] = {k: r["step_crossings"] for k, r in res.items() if r["step_crossings"]}
    print(json.dumps({"total": tot, "roads": res, "fails": fails, "grade_max": GRADE_MAX,
                      "bank_bar": {"value": BANK_BAR, "band_m": BANK_BAND_M, "source": BANK_BAR_SOURCE},
                      "bank_measured_on": "raised" if raised is not None else "all low ground (no road-raised mask)"}, indent=1))
    return 1 if fails else 0


def census_main(w, a) -> int:
    """`census --dump D [GROUND_DIR]`: the road pass replayed on generate's dump (the ground before the roads, the
    cones and the water mask), then every wall and dry over-steep point by cause, with what the road itself made
    (not in the ground before it). The sites are GROUND_DIR's entrance-sites.json (default out/terrain)."""
    import json
    from pathlib import Path

    from tools.argonia_world.terrain import cellwater
    d = np.load(a.dump)
    h_pre = np.asarray(d["h"], np.float64)
    lo, hi, water = np.asarray(d["lo"], np.float64), np.asarray(d["hi"], np.float64), d["water"]
    h = h_pre.copy()
    roads = load_roads(w)
    shape(h, roads, water, lo, hi)
    h = np.minimum(np.maximum(h, lo), hi)
    wet, _ = cellwater.wet_raster(w)
    sp = Path(a.ground or "out/terrain") / "entrance-sites.json"
    c = census(h, h_pre, lo, hi, water, roads, wet, json.loads(sp.read_text()) if sp.exists() else ())
    pts_n = sum(len(frame(pts)[0]) for pts, _c in roads)
    vb = VANILLA_ROADS
    sh = {"points": pts_n, "walls_per_side_point": round(sum(c["walls"].values()) / (2 * pts_n), 4),
          "made_walls_per_side_point": round(c["made_by_road"]["walls"] / (2 * pts_n), 4),
          "steep_share": round(sum(c["steep"].values()) / pts_n, 4), "vanilla": vb}
    fails = []
    if sh["walls_per_side_point"] > vb["walls_per_side_point"]:
        fails.append(f"walls {sh['walls_per_side_point']} a side point over Skyrim.esm's {vb['walls_per_side_point']}")
    if sh["steep_share"] > vb["steep_share"]:
        fails.append(f"steep share {sh['steep_share']} over Skyrim.esm's {vb['steep_share']}")
    land = {}
    for ri, _i, cause, x, y, g0 in c["where"]["steep"]:
        if cause == "land":
            land.setdefault(ri, []).append((x, y, g0))
    made = {}
    for x in c["where"]["walls"]:
        if x[5]:
            made[x[2]] = made.get(x[2], 0) + 1
    res = {"bar": sh, "fails": fails, "walls": c["walls"], "steep": c["steep"], "made_by_road": c["made_by_road"],
           "made_walls_by_cause": made,
           "made_walls_m": [x[:5] for x in c["where"]["walls"] if x[5]][:60],
           "walls_total": sum(c["walls"].values()), "steep_total": sum(c["steep"].values()),
           "steep_land_by_road": {str(r): {"points": len(v), "land_grade_median": round(float(np.median([g for *_, g in v])), 3),
                                           "first_m": v[0][:2]} for r, v in sorted(land.items())}}
    print(json.dumps(res, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
