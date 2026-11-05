"""L1 (lane 1.15-r6-shores-slope): the land falls through the waterline as Skyrim.esm's does, no shelf at the level.

Synthetic 3 x 3 cells: a basin under a flat plate standing 0.1 m over the water (the round-6 shelf), the east column
a dry cell. Skyrim.esm's measure (probes/vanilla_shore_profile.py): the 10th percentile of the ground over a lake's
level is 0 only at one vertex out and climbs 0.23 / 0.46 / 1.00 / 2.31 m at 2 / 3 / 5 / 10, so no vanilla shore
holds a shelf within 0.1 m of the level past one vertex (1.83 m): N = 1 sample."""
import numpy as np

from tools.argonia_world.terrain import generate as G
from tools.argonia_world.terrain import water_field as W
from tools.argonia_world.terrain.cellwater import Q

LV = 10.0


def _scene(wtype="fresh"):
    n = 3 * Q + 1
    level = np.full((3, 3), LV)
    level[:, 2] = np.nan  # the east column dry
    i = np.arange(n)
    lo_c, hi_c = np.clip((i - 1) // Q, 0, 2), np.clip(i // Q, 0, 2)
    st = np.stack([level[a][:, b] for a in (lo_c, hi_c) for b in (lo_c, hi_c)])
    with np.errstate(all="ignore"):
        vmin, vmax = np.nanmin(st, 0), np.nanmax(st, 0)
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - 48, xx - 40)
    h = np.where(r < 30, LV - 2.0 + (r / 30) ** 2 * 1.5, LV + 0.1)  # a bowl under a plate 0.1 m over the water
    h = h.astype(np.float64)
    foot = r < 26
    touch = np.zeros((n, n), bool)
    touch[:, 2 * Q] = True  # the vertices the dry column shares
    touch[0, :] = touch[-1, :] = touch[:, 0] = False
    chz = np.zeros((n, n), bool)
    tsamp = np.full((n, n), G.TYPES.index(wtype), np.int8)
    tsamp[:, 2 * Q + 1:] = -1
    return h, foot, vmin, vmax, touch, chz, tsamp


def _run(wtype="fresh"):
    h, foot, vmin, vmax, touch, chz, tsamp = _scene(wtype)
    h2, role, lo, hi, d = W.water_field(h, foot, vmin, vmax, touch, chz, tsamp)
    return h2, role, vmin


def test_no_shelf_at_the_level_past_one_sample():
    h2, role, vmin = _run()
    wet = role == 1
    dist, _ = G.chamfer(wet, 40)
    dry = ~wet & np.isfinite(vmin) & np.isfinite(dist)
    near = dry & (h2 - LV < G.FREEBOARD_M + 0.1)
    assert wet.any()
    assert not (near & (dist > 1.5)).any(), int((near & (dist > 1.5)).sum())


def test_shore_rises_at_vanillas_grade():
    h2, role, vmin = _run()
    wet = role == 1
    dist, _ = G.chamfer(wet, 40)
    for d, want in ((5, 1.00), (10, 2.31), (15, 3.43)):
        m = (np.abs(dist - d) < 0.5) & ~wet & np.isfinite(vmin)
        assert m.any()
        assert np.percentile(h2[m] - LV, 10) >= want + G.FREEBOARD_M - 0.1, d


def test_marsh_rises_at_half():
    h2, role, vmin = _run("blackwater")
    wet = role == 1
    dist, _ = G.chamfer(wet, 40)
    m = (np.abs(dist - 10) < 0.5) & ~wet & np.isfinite(vmin)
    z = np.percentile(h2[m] - LV, 10)
    assert 2.31 * W.MARSH_FLOOR + G.FREEBOARD_M - 0.05 <= z < 2.31 + G.FREEBOARD_M


def test_water_stops_short_of_a_dry_cells_edge():
    # the basin reaches the dry column's line: the water ends inside the cell, not one sample from the line
    h, foot, vmin, vmax, touch, chz, tsamp = _scene()
    h = np.where(np.arange(h.shape[1])[None, :] < 2 * Q + 1, np.minimum(h, LV - 1.0), h)
    foot = np.zeros_like(foot)
    foot[:, :2 * Q - 12] = True
    h2, role, lo, hi, d = W.water_field(h, foot, vmin, vmax, touch, chz, tsamp)
    rows = slice(Q // 2, 2 * Q)
    wet_cols = np.where((role[rows] == 1).any(axis=0))[0]
    assert 2 * Q - wet_cols.max() >= 4, 2 * Q - wet_cols.max()
    assert (h2[rows, 2 * Q] >= LV + G.FREEBOARD_M + W.EDGE_UP - 1e-6).all()
