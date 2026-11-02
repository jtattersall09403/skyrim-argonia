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
TROUGH_BAND = {2.0: (0.03, 0.13), 4.0: (0.18, 0.45)}  # p25..p75 at 2 m and 4 m out
GRADE_MAX = 0.219  # vanilla's steepest road grade
GRADE_P95 = 0.164
GRADE_BASE_M = 8.0  # the grade's baseline (vanilla measured over +-4 m)
SMOOTH_M = 6.0  # the centreline smoothed along over +-this
WALL_M = 0.3  # a step across a road's edge past the land's own: a wall (the planner's rule, round 4)
CROSS_KEEP = 0.4  # the share of the land's cross fall a road keeps (the wall check's slope window)
BLEND_M = 6.0  # the road's ground blends back to the land over this beyond its core (vanilla's fold flattens by 8 m)


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
    zs = grade_limit(zs, MPP, GRADE_MAX * 0.85)  # headroom for the trough and the 8 m baseline
    return zs - 0.5 * trough(core_m)


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
    n = runs_n = 0
    taper_n = max(1, int(round(BLEND_M / MPP)))
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
            t = zc[ii] + trough(d_m) + CROSS_KEEP * (h[rr, cc] - zg[ii])
            if lo is not None:
                t = np.minimum(np.maximum(t, lo[rr, cc]), np.maximum(hi[rr, cc], lo[rr, cc]))
            keep = w > 0
            if water is not None:
                keep &= ~water[rr, cc]
            rr, cc, w, t = rr[keep], cc[keep], w[keep], t[keep]
            num[rr, cc] += w * t
            den[rr, cc] += w
            np.maximum.at(wgt, (rr, cc), w)
            n += int((d_m <= core_m).sum())
            runs_n += 1
    m = wgt > 0
    h[m] = h[m] * (1 - wgt[m]) + num[m] / den[m] * wgt[m]
    return {"roads": len(roads), "dry_runs": runs_n, "core_samples": n, "shaped_samples": int(m.sum())}


def profile(h: np.ndarray, roads: list[tuple[np.ndarray, float]], wet=None) -> dict:
    """Measure every road on ground h: the folded cross profile at 2 and 4 m (median, share in the vanilla band),
    the grade along (p50/p95/max, the count of centreline points steeper than GRADE_MAX), and the centreline
    points under water (wet: the wet level raster, NaN dry); a point on the wet raster is a crossing, not road grade.
    The trough fold is measured on roads (core >= 4 m), vanilla's class; tracks report their own median."""
    fold = {2.0: [], 4.0: []}
    track_fold = []
    grades, steep, wet_pts, total, crossings, cross_pts, walls = [], 0, 0, 0, 0, 0, 0
    # how many roads' corridors reach each sample: a wall test whose outside sample lies in another road's corridor
    # reads that road's trough (a track beside a road, a junction), not a wall
    reach = np.zeros(h.shape, np.int8)
    for pts, _core in roads:
        rr, cc, _d, _i = _nearest(h.shape, _dense(pts)[0], _core + BLEND_M / MPP)
        reach[rr, cc] += 1
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
        # a wall: a step across the road's edge more than WALL_M beyond the land's own step just outside it
        for sg in (1.0, -1.0):
            zz = [bilinear(h, p[:, 0] + sg * nrm[:, 0] * (_core + o), p[:, 1] + sg * nrm[:, 1] * (_core + o))
                  for o in (-0.5, 0.5, 1.5)]
            ox = p[:, 0] + sg * nrm[:, 0] * (_core + 0.5)
            oy = p[:, 1] + sg * nrm[:, 1] * (_core + 0.5)
            alone = reach[np.clip(np.rint(oy).astype(int), 0, h.shape[0] - 1),
                          np.clip(np.rint(ox).astype(int), 0, h.shape[1] - 1)] <= 1
            walls += int(((np.abs(zz[1] - zz[0]) > WALL_M + np.abs(zz[2] - zz[1])) & alone).sum())
        half = GRADE_BASE_M / 2 / MPP
        za = bilinear(h, p[:, 0] + v[:, 0] * half, p[:, 1] + v[:, 1] * half)
        zb = bilinear(h, p[:, 0] - v[:, 0] * half, p[:, 1] - v[:, 1] * half)
        g = np.abs(za - zb) / GRADE_BASE_M
        e = int(np.ceil(half / 2.0))  # the baseline never reaches past the road's ends
        g[:e] = g[-e:] = 0.0
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

    from tools.argonia_world import db
    from tools.argonia_world.terrain import cellwater
    from tools.argonia_world.terrain.grid import generated_ground

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("ground", nargs="?")
    a = ap.parse_args(argv)
    w = db.open()
    h = np.load(a.ground or generated_ground(), mmap_mode="r")
    wet, _ = cellwater.wet_raster(w)
    res = profile(np.asarray(h, np.float64), load_roads(w), wet)
    fails = []
    if res["steeper_than_max"]:
        fails.append(f"{res['steeper_than_max']} dry road points steeper than {GRADE_MAX}")
    if res["walls"]:
        fails.append(f"{res['walls']} walls at a road edge (a step over {WALL_M} m past the land's own)")
    for o, (lo, hi) in TROUGH_BAND.items():
        m = res[f"fold_{o:.0f}m_median"]
        if not lo <= m <= hi:
            fails.append(f"fold at {o:.0f} m median {m} outside vanilla's {lo}..{hi}")
    res["fails"] = fails
    print(json.dumps(res, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
