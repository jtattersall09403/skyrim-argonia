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
# lane 1.15-r6-stepped-pools: Skyrim.esm's falls face drops ~2.0 m per vertex into the lower pool
# (probes/vanilla_hanging_edges.py: the channel face 6.2, 5.4, 4.0, 3.5, 3.4, 1.6 m over the lower water by vertex) and
# the lower thalweg is under the lower level by vertex 6 (p50); a step line's bank lift falls into the pool at this
# grade, and no lift raises the carved footprint (the raster water) by more than this per sample of distance from it:
# the bank lift and the hollow lift had filled the carved pool back in (lift p50 25 m at -50,46 against a 15 m
# shortfall; 1,654 buried cells, 183 kept steps with no lower water within 12 vertices)
FACE_GRADE = 2.0
WALL_GRADE = 6.0
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
# a stepped cell (a level a riffle over or under a neighbour's) floods its under-level ground only this far from its
# raster water: a stair of cell planes down a slope flooded each cell's whole low ground to the cell line, the
# straight-edged pools of -38_25 (probes/marsh_cells.py: raster 1.96 m under solved 10.66 m, pre-ground 3.9 m under
# the plane, 82 % wet against 39 % footprint). Skyrim.esm's ground stands 2.7 m over its water 5 samples from the shore
# (SHORE_UP), so a river's water keeps to its channel; past the band the ground is raised as a hollow
FLOOD_BAND = 6
# Skyrim.esm's shore floor (lane 1.15-r6-shores-slope, probes/vanilla_shore_profile.py, the 15 largest inland
# levels, dry vertices inside the water cells): the 10th percentile of the ground's rise over the level (m) by
# distance from the water (vertices). Nine in ten of vanilla's shore stands over this line: the ground falls through
# the waterline, never a plate at the level. Ours had a shelf at the freeboard (the floor plate base + floor, the gap
# snap, lo = level + freeboard): p10 0.30-0.50 m flat from 5 to 15 m out at the round-6 tarn and sea-far stands
FLOOR_D = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20)
FLOOR_UP = (0.0, 0.0, 0.23, 0.46, 0.71, 1.00, 1.31, 1.77, 2.31, 2.74, 3.43, 4.51)
FLOOR_FAR = 20  # samples: the floor reaches this far from the water, then fades back to the ground over as far again
# a water cell's edge on a dry cell: vanilla's upper water stops a median 9 vertices short of a closed edge
# (probes/vanilla_level_edges.py), so the edge stands the floor's 9-vertex rise over the water and the bank falls from
# it at EDGE_GRADE (vanilla's p10 grade); at LIFT_GRADE and the freeboard the waterline ran one sample inside the cell
# line, ruler-straight, with a stepped notch at each cell corner (round-6 sea-far s0/s5)
EDGE_UP = 2.06
MARSH_FLOOR = 0.5
EDGE_GRADE = 0.3
BAND = 3  # samples: a clipped line's crest half-width, so the cell line is no ridge (trial: lattice 2.55 -> 1.40 at 3,
# 1.49 at 9); the upper water stops short of the line as Skyrim.esm's does (probes/vanilla_level_edges.py)


def shore_rise(d):
    """The vanilla shore profile: metres over the water at `d` samples in from the shore line."""
    return np.interp(d, SHORE_D, SHORE_UP)


def shore_floor(d):
    """Skyrim.esm's shore floor: metres over the water at `d` samples from it (0 past FLOOR_FAR, faded over as far)."""
    up = np.interp(d, FLOOR_D, FLOOR_UP)
    fade = np.clip(1.0 - (d - FLOOR_FAR) / FLOOR_FAR, 0.0, 1.0)
    return np.where(np.isfinite(d), up * fade, 0.0)


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


def pool_room(foot: np.ndarray) -> np.ndarray:
    """The most any lift may raise a sample: 0 on the raster water, growing FACE_GRADE per sample away from it, so the
    carved pool keeps its bed and the bank rises from it as a falls face, never a fill."""
    return -G.majorant(np.where(foot, 0.0, -1e9), FACE_GRADE)


def water_field(h, foot, vmin, vmax, touch, chz, tsamp, gully=None, exempt=None):
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
    # 2. lift: the clipped edges above the upper water, the bank climbing to them from both sides; an edge on a dry
    # cell stands the shore's 9-vertex rise over the water and falls at vanilla's grade, so the water stops short of it
    edge = src & touch
    lf = np.maximum(lift_to(h1, src & ~edge, need, LIFT_GRADE, band=BAND),
                    lift_to(h1, edge, need + EDGE_UP, EDGE_GRADE, band=BAND))
    # a clipped line keeps its need and falls from it at the face grade; the pool beyond keeps its bed
    # the cells beside a level step (a riffle or more under or over a neighbour): the hillside staircase. Only there
    # is the pool kept from the lifts; a flat marsh or a ford keeps its gentle banks (roads' bank bar)
    dd = drop > G.RIFFLE_M
    dd = dd[:-1, :-1] | dd[1:, 1:] | dd[:-1, 1:] | dd[1:, :-1]
    n_ = dd.shape[0] // G.Q
    stc = dd[:n_ * G.Q, :n_ * G.Q].reshape(n_, G.Q, n_, G.Q).any(axis=(1, 3))
    st_s = np.pad(np.repeat(np.repeat(stc, G.Q, 0), G.Q, 1), ((0, h.shape[0] - n_ * G.Q), (0, h.shape[1] - n_ * G.Q)),
                  mode="edge")
    room = np.maximum(pool_room(foot), cone(src & (lf > 0), np.where(src, lf, 0.0), WALL_GRADE))
    # a road's corridor and cone and a step bridge's seats keep the full lift (the causeway and the seat stand on it)
    keep_ = st_s if exempt is None else st_s & ~exempt
    room = np.where(keep_, room, np.inf)
    lf = np.minimum(lf, room)
    h1 = h1 + lf
    # 3. under-level ground not joined to the raster water (a hollow past the basin's pass, a low corner of the
    # cell): the cell's plane would draw a square pool over it, so it is lifted above the water the same way
    under = has & (h1 < vmin - G.FREEBOARD_M) & ~chz
    dfo, _ = G.chamfer(foot, FLOOD_BAND + 1)
    keep = under & ~(st_s & ~(np.nan_to_num(dfo, nan=99) <= FLOOD_BAND))
    iso = under & ~G.reach(foot & keep, keep)
    if iso.any():
        # the hollow is raised whole, keeping its own slope (a bowl standing above the water, never a plate at the
        # level): the deepest shortfall spreads at HOLLOW_GRADE and is blurred; the small rest is lifted as above
        # (the slow fade only inside the hollow; past its rim the lift falls at LIFT_GRADE like any bank)
        inner = np.where(iso, cone(iso, np.where(iso, need - h1, 0.0) + HOLLOW_PAD, HOLLOW_GRADE), -1e9)
        lf2 = G.blur(np.maximum(G.majorant(inner, LIFT_GRADE), 0.0), SOFT)
        lf2 = np.minimum(lf2, room)  # a raised hollow beside the pool does not fill it
        lf2 = lf2 + lift_to(h1 + lf2, iso & (h1 + lf2 < need), need, LIFT_GRADE)
        h1 = h1 + lf2
        lf = lf + lf2
        src = src | iso
    # 4. the shore floor: dry ground near the water stands at least Skyrim.esm's p10 rise over it (FLOOR_UP) plus the
    # freeboard, so the land falls continuously through the waterline: no shelf at the level for the plane to meet in a
    # straight line, nothing for the freeboard snap below to flatten. The level carries out over a dry cell's edge
    # (the nearest water's), so the ground beside a closed edge rises too
    wet0 = has & ~src & (h1 < vmin - G.FREEBOARD_M)
    dw, lvw = G.chamfer(wet0, 2 * FLOOR_FAR, np.where(wet0, vmax, np.nan))
    lvw = np.where(has, vmax, lvw)
    # a marsh's shore rises at half a lake's (SHORE_RISE_U: Morthal's 326 u at 10 vertices against Ilinalta's 648)
    marsh = np.isin(tsamp, [G.TYPES.index("brackish"), G.TYPES.index("blackwater")])
    up = shore_floor(dw) * np.where(marsh, MARSH_FLOOR, 1.0)
    fl = np.where(~wet0 & ~chz & np.isfinite(lvw), lvw + G.FREEBOARD_M + up, -np.inf)
    sf = G.blur(np.maximum(fl - h1, 0.0), 1.0)
    sf = np.where(np.isfinite(fl), np.maximum(sf, fl - h1), 0.0)
    sf = np.maximum(sf, 0.0)
    h1 = h1 + sf
    lf = lf + sf
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
    lo[fl > lo] = fl[fl > lo]
    return h2, role, lo, hi, {"floor": sf, "lift": lf, "carve": cf, "src": src, "iso": iso, "gap_up": gap & ~gdn, "gap_dn": gdn}
