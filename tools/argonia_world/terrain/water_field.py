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
SOFT = 2.0  # samples: the fields' blur (no crease at the cone's foot)


def cone(src: np.ndarray, amt: np.ndarray, grade: float) -> np.ndarray:
    f = G.majorant(np.where(src, amt, -1e9), grade)
    return np.maximum(f, 0.0)


def water_field(h, foot, vmin, vmax, touch, chz, tsamp):
    has = np.isfinite(vmin)
    drop = np.nan_to_num(vmax - vmin, nan=0.0)
    need = np.where(has, vmax + G.FREEBOARD_M, -np.inf)
    src = has & (touch | (drop > G.RIFFLE_M)) & ~chz & ~foot
    lift = np.where(src, np.maximum(need - h, 0.0), 0.0)
    lf = G.blur(cone(src & (lift > 0), lift, LIFT_GRADE), SOFT)
    h1 = h + lf
    # the bed under raster water, deepening inward by the type's measured profile
    din, _ = G.chamfer(~foot, 32)
    din = np.where(foot, np.where(np.isfinite(din), din, 32), 0)
    dp = np.zeros(h.shape)
    for i, n in enumerate(G.TYPES):
        dp[tsamp == i] = G.DEPTH_M[n]
    bed = vmin - np.clip(G.bed_depth(tsamp, din), G.FREEBOARD_M, np.maximum(dp, G.FREEBOARD_M + 0.2))
    cut = np.where(foot, np.maximum(h1 - bed, 0.0), 0.0)
    cf = G.blur(cone(foot & (cut > 0), cut, CARVE_GRADE), SOFT)
    h2 = h1 - np.where(src, 0.0, cf)
    # the footprint is the ground's contour: under the cell's lowest water is wet
    wet = has & (foot | (h2 < vmin - G.FREEBOARD_M))
    # no ground within the freeboard of its water (the checks' band): moved to the nearer side
    gap = has & ~wet & (h2 < vmax + G.FREEBOARD_M)
    mid = np.where(has, (vmin + vmax) / 2, 0)
    h2 = np.where(gap & (h2 < mid) & ~src, vmin - G.FREEBOARD_M - 0.01, np.where(gap, vmax + G.FREEBOARD_M, h2))
    wet = has & (foot | (h2 < vmin - G.FREEBOARD_M))
    lo = np.full(h.shape, -np.inf)
    hi = np.full(h.shape, np.inf)
    lo[src] = need[src]
    hi[wet] = np.minimum(vmin[wet] - G.FREEBOARD_M, np.where(foot[wet], bed[wet], np.inf))
    role = np.zeros(h.shape, np.uint8)
    role[wet] = 1
    role[has & ~wet] = 3
    lo[has & ~wet] = np.maximum(lo[has & ~wet], vmax[has & ~wet] + G.FREEBOARD_M)
    return h2, role, lo, hi, {"lift": lf, "carve": cf, "src": src}
