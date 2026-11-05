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
GRADE_MAX = 0.219  # vanilla's steepest road grade
SMOOTH_M = 6.0  # the centreline smoothed along over +-this
MAX_CUT_M = 1.0  # a road is never cut or filled more than this from the land (L3 reader: a 3 m cut wall)
CROSS_KEEP = 0.4  # the share of the land's cross fall a road keeps (the wall check's slope window)
ROAD_RAISED = "road-raised-u8.npy"  # generate: the samples dry_corridor raised (the census's bank grade)
ROAD_WATER = "road-water-u8.npy"  # generate writes the road pass's water mask beside the ground (the check's census)
DELTA_LIP = 0.2  # the road's change between neighbour samples, at most (m): its walls stay under WALL_M
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
SEAT_UNDER_SAMPLES = 1.5  # a seat runs this many samples under its deck at least: the 0.3 m seat is under one
# sample, so the bilinear ground at the deck's end mixed the free samples under the deck (gideon-step end 1: 4.4 m)
DECK_CLEAR_M = 1.0  # the ground under a deck between its seats stands at least this far under the deck's top
FORD_GAP = 2  # samples between a ford and the causeway left to the ground (the ramp from the top to the bed)


def bridge_crossings(w) -> list[dict]:
    """Each bridge end's seat at routes/infra.BRIDGES' crossings (the deck centred on the roads' axis there), its
    deck top z_m unset: generate sets it on the corridor (bridge_decks)."""
    import math

    from tools.argonia_world.routes import infra
    out = []
    for bid, (q, _reach, routes) in sorted(infra.BRIDGES.items()):
        lines = {r: [(p["x_m"], p["y_m"]) for p in w.query(
            "SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r)] for r in routes}
        if any(len(v) < 2 for v in lines.values()):
            continue
        x, y, hd = infra.axis([infra.nearest_on(lines[r], q) for r in routes])
        ux, uy = math.sin(math.radians(hd)), -math.cos(math.radians(hd))
        half = infra.BRIDGE_LEN_M / 2
        for k, sg in enumerate((-1, 1)):
            out.append({"bridge": f"bridge.{bid}", "end": k, "at_m": [round(x + sg * ux * half, 2), round(y + sg * uy * half, 2)],
                        "centre_m": [round(x, 2), round(y, 2)], "heading": round(hd, 2),
                        "yaw": round((hd + infra.BRIDGE_YAW_OFFSET) % 360, 2), "z_m": None,
                        "from_m": -infra.SEAT_M, "to_m": infra.APPROACH_M,
                        "half_width_m": round(infra.BRIDGE_HALF_W_M + 2.0, 2)})
    return out


def _seat_axis(q, ends):
    ex, ey = (float(v) / MPP for v in q["at_m"])
    other = [o for o in ends[q["bridge"]] if o is not q]
    if other:
        ox, oy = (float(v) / MPP for v in other[0]["at_m"])
        ux, uy = ex - ox, ey - oy
    else:
        th = np.radians(q["heading"])
        ux, uy = np.sin(th), -np.cos(th)
    ln = max(float(np.hypot(ux, uy)), 1e-9)
    return ex, ey, ux / ln, uy / ln


def deck_span(shape_, seats: list[dict]) -> np.ndarray:
    """The samples under each bridge's deck between its two seats (inside from_m of each end), the deck's half width
    plus the seat's margin across: dry_corridor leaves them to the water, so the step shows under the deck."""
    m = np.zeros(shape_, bool)
    ends: dict = {}
    for q in seats:
        ends.setdefault(q["bridge"], []).append(q)
    for qs in ends.values():
        if len(qs) != 2:
            continue
        (ax, ay), (bx, by) = ([float(v) / MPP for v in q["at_m"]] for q in qs)
        ln = max(float(np.hypot(bx - ax, by - ay)), 1e-9)
        ux, uy = (bx - ax) / ln, (by - ay) / ln
        inset = max(-qs[0]["from_m"] / MPP, SEAT_UNDER_SAMPLES)
        w_ = qs[0]["half_width_m"] / MPP
        r = int(np.ceil(ln / 2 + w_)) + 1
        cx, cy = (ax + bx) / 2, (ay + by) / 2
        r0, r1 = max(int(cy) - r, 0), min(int(cy) + r, shape_[0] - 1)
        c0, c1 = max(int(cx) - r, 0), min(int(cx) + r, shape_[1] - 1)
        yy, xx = np.mgrid[r0:r1 + 1, c0:c1 + 1].astype(np.float64)
        along = (xx - ax) * ux + (yy - ay) * uy
        across = np.abs(-(xx - ax) * uy + (yy - ay) * ux)
        m[r0:r1 + 1, c0:c1 + 1] |= (along > inset) & (along < ln - inset) & (across <= w_)
    return m


def bridge_decks(h, seats: list[dict]) -> list[dict]:
    """Each bridge's deck top: the road corridor's height at its two ends (h after dry_corridor's bounds), the higher
    one: the highest ground along each seat's axis (from under the deck to APPROACH_M beyond), so a seat only ever
    raises the road to the deck, never cuts the causeway down to it. Sets each seat's z_m; returns the decks
    (bridge-decks.json: id, deck top, centre, ends, heading, yaw)."""
    ends: dict = {}
    for q in seats:
        ends.setdefault(q["bridge"], []).append(q)
    out = []
    for bid, qs in ends.items():
        tops = []
        for q in qs:
            ex, ey, ux, uy = _seat_axis(q, ends)
            s_ = np.arange(q["from_m"], q["to_m"] + 0.01, 0.5) / MPP
            tops.append(float(bilinear(h, ex + ux * s_, ey + uy * s_).max()))
        top = round(max(tops), 2)
        for q in qs:
            q["z_m"] = top
        out.append({"id": bid, "deck_m": top, "ends_ground_m": [round(t, 2) for t in tops], "centre_m": qs[0]["centre_m"],
                    "ends_m": [q["at_m"] for q in qs], "heading": qs[0]["heading"], "yaw": qs[0]["yaw"]})
    return out


def bridge_seats(seats: list[dict], lo, hi, keep=None, corridor_m=None, h=None, keep_ch=None) -> dict:
    """Each bridge end's seat (bridge_crossings, decks by bridge_decks): the corridor raised to the deck's top z_m
    from from_m (under the deck) to to_m beyond the end, half_width_m across, and eased up to it at GRADE_MAX beyond
    (a lo cone, inside the road's corridor `corridor_m` when given). A seat never cuts: where the ground `h` already
    stands above the deck it is left; only a seat sample at or under the deck is pinned to it. Between the two seats
    the channel (`keep`) is never touched, so the step's water shows under the deck; the rest under the deck
    (outside the step's channel `keep_ch`) is held DECK_CLEAR_M under it. The deck is the higher end's corridor
    (bridge_decks), so the lower end's seat is a ramp up to it, as Skyrim.esm's roads climb to a level deck
    (Bridge01's ends 2.97 m over the land). lo, hi in place."""
    from tools.argonia_world.terrain.generate import chamfer
    keep = np.zeros(lo.shape, bool) if keep is None else keep
    ends: dict = {}
    for q in seats:
        ends.setdefault(q["bridge"], []).append(q)
    n_seat = 0
    held = np.zeros(lo.shape, bool)
    for q in seats:
        if q.get("z_m") is None:
            continue
        ex, ey, ux, uy = _seat_axis(q, ends)
        far = int(np.ceil(4 * MAX_CUT_M / (GRADE_MAX * MPP))) + 2  # the ease's reach in samples
        reach = (q["to_m"] + q["half_width_m"]) / MPP + far + 2
        r0, r1 = int(max(ey - reach, 0)), int(min(ey + reach, lo.shape[0] - 1))
        c0, c1 = int(max(ex - reach, 0)), int(min(ex + reach, lo.shape[1] - 1))
        sub = np.s_[r0:r1 + 1, c0:c1 + 1]
        yy, xx = np.mgrid[r0:r1 + 1, c0:c1 + 1].astype(np.float64)
        along = ((xx - ex) * ux + (yy - ey) * uy) * MPP
        across = np.abs(-(xx - ex) * uy + (yy - ey) * ux) * MPP
        box = (along >= min(q["from_m"], -SEAT_UNDER_SAMPLES * MPP)) & (along <= q["to_m"]) & \
            (across <= q["half_width_m"]) & ~keep[sub]
        z = q["z_m"]
        pin = box  # the deck is the seat axis's highest corridor ground: the whole seat is held at it
        lo[sub] = np.where(pin, z, lo[sub])
        hi[sub] = np.where(pin, z, hi[sub])
        held[sub] |= box
        n_seat += int(box.sum())
        # the ease: a lo cone from the seat falling GRADE_MAX a metre (8-neighbour chamfer distance); raise only
        d, _ = chamfer(box, far)
        m = np.isfinite(d) & (d > 0) & ~keep[sub] & ~held[sub]
        if corridor_m is not None:
            m &= corridor_m[sub]
        dz = GRADE_MAX * np.where(np.isfinite(d), d, 0.0) * MPP
        lo[sub] = np.where(m, np.maximum(lo[sub], z - dz), lo[sub])
        hi[sub] = np.where(m, np.maximum(hi[sub], lo[sub]), hi[sub])
    # under each deck between its seats: the ground held DECK_CLEAR_M under the deck's top (never through the deck;
    # the step's channel keeps its own bed)
    n_under = 0
    for qs in ends.values():
        if len(qs) != 2 or qs[0].get("z_m") is None:
            continue
        under = deck_span(lo.shape, qs) & ~keep_ch if keep_ch is not None else deck_span(lo.shape, qs)
        cap = qs[0]["z_m"] - DECK_CLEAR_M
        hi[under] = np.minimum(hi[under], cap)
        lo[under] = np.minimum(lo[under], hi[under])
        n_under += int(under.sum())
    return {"seated": held, "stats": {"seats": len(seats), "seat_samples": n_seat, "under_deck_samples": n_under}}


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
