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
import numpy as np

from tools.argonia_world.terrain import generate as G

LIFT_GRADE = 0.6  # m per sample (18 deg): a raised bank's fall-off to the ground beside it
CARVE_GRADE = 0.6  # m per sample: the ground's fall into raster water down to the bed
TYPE_BLEND = 16.0  # samples (half a cell): the bed depth by type blends over this, never steps at a cell line
SOFT = 3.0  # samples: the fields' blur (no crease at the cone's foot)
HOLLOW_GRADE = 0.08  # m per sample: a raised hollow's lift fades this slowly, so its own relief survives
# a dry gully (raster water the solve gave no level: water/solve.py dry reaches) is a bed with no level, cut this
# far into its own ground at its middle by the blackwater bed profile (Skyrim.esm's dressed dry beds are shallow)
GULLY_M = 1.0
HOLLOW_PAD = 0.4  # m: a raised hollow's floor stands this far over the bank line (the blur takes some)
# Skyrim.esm's ground over a lake's level by distance from its shore line (vertices = our samples), the median of the
# 15 largest inland levels (probes/vanilla_shore_profile.py)
SHORE_D = (0.0, 1.0, 5.0, 10.0, 20.0)
SHORE_UP = (0.0, 0.23, 2.7, 6.4, 13.0)
BAND = 3  # samples: a clipped line's crest half-width, so the cell line is no ridge (trial: lattice 2.55 -> 1.40 at 3,
# 1.49 at 9); the upper water stops short of the line as Skyrim.esm's does (probes/vanilla_level_edges.py)


def shore_rise(d):
    """The vanilla shore profile: metres over the water at `d` samples in from the shore line."""
    return np.interp(d, SHORE_D, SHORE_UP)


def cone(src: np.ndarray, amt: np.ndarray, grade: float) -> np.ndarray:
    f = G.majorant(np.where(src, amt, -1e9), grade)
    return np.maximum(f, 0.0)


def lift_to(h, src, need, grade, band=0):
    """The lift as a field of amounts: each `src` vertex's shortfall under `need` spreads as a cone falling at `grade`
    (the upper envelope of all the cones), added to the ground, so the ground keeps its own shape under it and is
    exact at the source (never below `need` there). An amount, not a height: a height cone from a high source
    buried every cliff beside it in a 31 deg apron (session 12: 1.7 M samples raised over 50 m), and the chamfer's
    48-sample radius cut it into walls (session 11). With `band`, the source widens to a crest that many samples
    each side, carrying its need."""
    if band > 0:
        d, nv = G.chamfer(src, int(band), np.where(src, need, np.nan))
        src, need = np.isfinite(d), np.where(np.isfinite(d), nv, -np.inf)
    amt = np.where(src, np.maximum(need - h, 0.0), 0.0)
    return cone(src & (amt > 0), amt, grade)


def water_field(h, foot, vmin, vmax, touch, chz, tsamp, gully=None):
    has = np.isfinite(vmin)
    drop = np.nan_to_num(vmax - vmin, nan=0.0)
    need = np.where(has, vmax + G.FREEBOARD_M, -np.inf)
    # a vertex a dry cell or a lower level shares: the upper plane covers it, so it is bank, not water
    src = has & (touch | (drop > G.RIFFLE_M)) & ~chz
    foot = foot & ~src
    # 1. carve: the raster water under its bed, deepening inward by the type's measured profile
    din, _ = G.chamfer(~foot, 32)
    din = np.where(foot, np.where(np.isfinite(din), din, 32), 0)
    # the bed's depth by type, blended across the cell lines (session 16: the type is per cell, so a fresh cell in a
    # blackwater marsh at one level cut its bed 3.0 m down beside 1.1 m, the marsh's staircase pool; Skyrim.esm's bed
    # is one continuous bowl under one plane, probes/vanilla_shore_profile.py)
    depth = np.zeros(h.shape)
    wsum = np.zeros(h.shape)
    for i, n in enumerate(G.TYPES):
        m = tsamp == i
        if not m.any():
            continue
        wi = G.blur(m.astype(np.float64), TYPE_BLEND)
        cap = max(G.DEPTH_M[n], G.FREEBOARD_M + 0.2)
        depth += wi * np.clip(G.bed_depth(np.full(h.shape, i), din), G.FREEBOARD_M, cap)
        wsum += wi
    bed = vmin - depth / np.maximum(wsum, 1e-9)
    cut = np.where(foot, np.maximum(h - bed, 0.0), 0.0)
    cf = G.blur(cone(foot & (cut > 0), cut, CARVE_GRADE), SOFT)
    h1 = h - cf
    if gully is not None and gully.any():
        dg, _ = G.chamfer(~gully, 32)
        dg = np.where(gully, np.where(np.isfinite(dg), dg, 32), 0)
        gcut = np.where(gully, np.minimum(G.bed_depth(np.full(h.shape, G.TYPES.index("blackwater")), dg), GULLY_M), 0.0)
        h1 = h1 - G.blur(gcut, SOFT)
    # 2. lift: the clipped edges above the upper water, the bank climbing to them from both sides
    lf = lift_to(h1, src, need, LIFT_GRADE, band=BAND)
    h1 = h1 + lf
    # 3. under-level ground not joined to the raster water (a hollow past the basin's pass, a low corner of the
    # cell): the cell's plane would draw a square pool over it, so it is lifted above the water the same way
    under = has & (h1 < vmin - G.FREEBOARD_M) & ~chz
    iso = under & ~G.reach(foot & under, under)
    if iso.any():
        # the hollow is raised whole, keeping its own slope (a bowl standing above the water, never a plate at the
        # level): the deepest shortfall spreads at HOLLOW_GRADE and is blurred; the small rest is lifted as above
        # (the slow fade only inside the hollow; past its rim the lift falls at LIFT_GRADE like any bank)
        inner = np.where(iso, cone(iso, np.where(iso, need - h1, 0.0) + HOLLOW_PAD, HOLLOW_GRADE), -1e9)
        lf2 = G.blur(np.maximum(G.majorant(inner, LIFT_GRADE), 0.0), SOFT)
        lf2 = lf2 + lift_to(h1 + lf2, iso & (h1 + lf2 < need), need, LIFT_GRADE)
        h1 = h1 + lf2
        lf = lf + lf2
        src = src | iso
    h2 = h1
    # the footprint is the ground's contour: under the cell's lowest water is wet
    wet = has & ~src & (h2 < vmin - G.FREEBOARD_M)
    # no ground within the freeboard of its water (the checks' band): moved to the nearer side. A monotone remap
    # over GAP_RUN m (session 14) kept the band's relief but carried the per-vertex level's step at each cell line
    # into the ground (lattice 1.38 -> 1.66, over the 1.5 gate); the snap moves 0.2-0.5 % of a window, the plates
    # it draws measured at 0.0-0.5 % (probes/clamp_census.py)
    gap = has & ~wet & (h2 < vmax + G.FREEBOARD_M)
    mid = np.where(has, (vmin + vmax) / 2, 0)
    gdn = gap & (h2 < mid) & ~src
    h2 = np.where(gdn, vmin - G.FREEBOARD_M - 0.01, np.where(gap, vmax + G.FREEBOARD_M, h2))
    wet = has & ~src & (h2 < vmin - G.FREEBOARD_M)
    lo = np.full(h.shape, -np.inf)
    hi = np.full(h.shape, np.inf)
    lo[src] = need[src]
    hi[wet] = vmin[wet] - G.FREEBOARD_M
    role = np.zeros(h.shape, np.uint8)
    role[wet] = 1
    role[has & ~wet] = 3
    lo[has & ~wet] = np.maximum(lo[has & ~wet], vmax[has & ~wet] + G.FREEBOARD_M)
    return h2, role, lo, hi, {"lift": lf, "carve": cf, "src": src, "iso": iso, "gap_up": gap & ~gdn, "gap_dn": gdn}
