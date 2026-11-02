"""The water applied to the ground as smooth fields, not per-cell clamps (1.15 ground, session 10).

The ground stays continuous (prior + relief + erosion). A cell's water plane covers whatever ground lies under its
level, so the footprint is the ground's own contour (Skyrim.esm: the ground just climbs from the water, no plate,
probes/vanilla_shore_profile.py). The ground is changed only where the one-level-per-cell rule needs it, and only by
fields that fall off smoothly with distance:
- lift: where a cell's plane is clipped at its edge over lower ground (a vertex shared with a dry cell or a lower
  level, outside a step's channel), that vertex must stand above the upper water; the shortfall spreads out as a
  cone at LIFT_GRADE, softened, so the bank climbs to the cell line from both sides;
- carve: the raster's water (rivers, the solve's bodies) must lie under its bed; the excess spreads as a cone at
  CARVE_GRADE, so the ground slopes down into the channel.
No vertex is clamped to a constant over a cell or band; lo/hi are returned only at the vertices the rule names, for
the slope limit."""
import math

import numpy as np

from tools.argonia_world.terrain import generate as G

LIFT_GRADE = 0.6  # m per sample (18 deg): a raised bank's fall-off to the ground beside it
CARVE_GRADE = 0.6  # m per sample: the ground's fall into raster water down to the bed
SOFT = 3.0  # samples: the fields' blur (no crease at the cone's foot)
APEX = 4.0  # samples: the lift's rounded apex
SMAX = 0.6  # m: the smooth maximum's width where the lift meets the ground


def cone(src: np.ndarray, amt: np.ndarray, grade: float) -> np.ndarray:
    f = G.majorant(np.where(src, amt, -1e9), grade)
    return np.maximum(f, 0.0)


def lift_to(h, src, need, grade, far=48):
    """The lift as a rounded cone: the bank's surface falls from `need` at the nearest `src` vertex at `grade`, its
    apex rounded over APEX samples (a hyperbolic cone, so a raised cell line is a rounded ridge, never a crease),
    joined to the ground by a smooth maximum (exact at the source: never below `need` there)."""
    d, nv = G.chamfer(src, far, np.where(src, need, np.nan))
    ok = np.isfinite(d)
    t = np.where(ok, nv - grade * (np.sqrt(np.where(ok, d, 0.0) ** 2 + APEX ** 2) - APEX), -np.inf)
    a = np.where(ok, t, h)
    sm = (h + a + np.sqrt((h - a) ** 2 + SMAX ** 2)) / 2 - SMAX / 2
    return np.where(ok, np.maximum(sm, h), h) - h


def water_field(h, foot, vmin, vmax, touch, chz, tsamp):
    has = np.isfinite(vmin)
    drop = np.nan_to_num(vmax - vmin, nan=0.0)
    need = np.where(has, vmax + G.FREEBOARD_M, -np.inf)
    # a vertex a dry cell or a lower level shares: the upper plane covers it, so it is bank, not water
    src = has & (touch | (drop > G.RIFFLE_M)) & ~chz
    foot = foot & ~src
    # 1. carve: the raster water under its bed, deepening inward by the type's measured profile
    din, _ = G.chamfer(~foot, 32)
    din = np.where(foot, np.where(np.isfinite(din), din, 32), 0)
    dp = np.zeros(h.shape)
    for i, n in enumerate(G.TYPES):
        dp[tsamp == i] = G.DEPTH_M[n]
    bed = vmin - np.clip(G.bed_depth(tsamp, din), G.FREEBOARD_M, np.maximum(dp, G.FREEBOARD_M + 0.2))
    cut = np.where(foot, np.maximum(h - bed, 0.0), 0.0)
    cf = G.blur(cone(foot & (cut > 0), cut, CARVE_GRADE), SOFT)
    h1 = h - cf
    # 2. lift: the clipped edges above the upper water, the bank climbing to them from both sides
    lf = lift_to(h1, src, need, LIFT_GRADE)
    h1 = h1 + lf
    # 3. under-level ground not joined to the raster water (a hollow past the basin's pass, a low corner of the
    # cell): the cell's plane would draw a square pool over it, so it is lifted above the water the same way
    under = has & (h1 < vmin - G.FREEBOARD_M) & ~chz
    iso = under & ~G.reach(foot & under, under)
    if iso.any():
        lf2 = lift_to(h1, iso, need, LIFT_GRADE)
        h1 = h1 + lf2
        lf = lf + lf2
        src = src | iso
    h2 = h1
    # the footprint is the ground's contour: under the cell's lowest water is wet
    wet = has & ~src & (h2 < vmin - G.FREEBOARD_M)
    # no ground within the freeboard of its water (the checks' band): moved to the nearer side
    gap = has & ~wet & (h2 < vmax + G.FREEBOARD_M)
    mid = np.where(has, (vmin + vmax) / 2, 0)
    h2 = np.where(gap & (h2 < mid) & ~src, vmin - G.FREEBOARD_M - 0.01, np.where(gap, vmax + G.FREEBOARD_M, h2))
    wet = has & ~src & (h2 < vmin - G.FREEBOARD_M)
    lo = np.full(h.shape, -np.inf)
    hi = np.full(h.shape, np.inf)
    lo[src] = need[src]
    hi[wet] = vmin[wet] - G.FREEBOARD_M
    role = np.zeros(h.shape, np.uint8)
    role[wet] = 1
    role[has & ~wet] = 3
    lo[has & ~wet] = np.maximum(lo[has & ~wet], vmax[has & ~wet] + G.FREEBOARD_M)
    return h2, role, lo, hi, {"lift": lf, "carve": cf, "src": src, "iso": iso}
