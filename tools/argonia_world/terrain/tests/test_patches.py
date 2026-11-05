"""L2 (lane 1.15-r4-claywater): a terrain_patch pad is flat at its ground's mean inside its disc and eases back; a
bowl sits depth_m under its cell's water; a pad's ltex rules its disc. On synthetic rows over a sloped ground."""
import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import patches

S = su.PROVINCE_SAMPLE_M


def _ground():
    yy, xx = np.mgrid[0:60, 0:60]
    return (10.0 + 0.2 * xx * S).astype(np.float32)  # a 20 % slope east


def _rows(**kw):
    r = {"id": "p", "kind": "pad", "x_m": 30 * S, "y_m": 30 * S, "radius_m": 4.0, "blend_m": 3.0, "rise_m": None,
         "depth_m": None, "ltex_edid": "LDirtPath01"}
    r.update(kw)
    return [r]


def test_pad_is_flat_at_its_mean_and_blends_out():
    g = _ground()
    p = patches.Patches.from_rows(_rows(), g, 0, lambda x, y: None)
    out = g.astype(np.float64).copy()
    p.apply(out, 0, 0)
    yy, xx = np.mgrid[0:60, 0:60]
    d = np.hypot(yy - 30, xx - 30) * S
    inside = out[d <= 4.0]
    assert np.ptp(inside) < 1e-6 and abs(inside.mean() - g[30, 30]) < 0.3
    far = d > 4.0 + p.items[0].blend_m + S  # the blend widens to the seat gradient on a slope (pad-seat)
    assert np.allclose(out[far], g[far])


def test_bowl_sits_under_the_water():
    g = _ground()
    p = patches.Patches.from_rows(_rows(kind="bowl", depth_m=2.5, blend_m=None, ltex_edid=None), g, 0,
                                  lambda x, y: g[30, 30] + 1.0)
    out = g.astype(np.float64).copy()
    p.apply(out, 0, 0)
    assert abs(out[30, 30] - (g[30, 30] + 1.0 - 2.5)) < 1e-3
    assert (out <= g + 1e-9).all()  # a bowl never raises


def test_pad_paints_its_disc():
    g = _ground()
    p = patches.Patches.from_rows(_rows(), g, 0, lambda x, y: None)
    w = np.zeros((60, 60, 3), np.float32)
    w[..., 0] = 1.0
    p.paint(w, 0, 0, {"LDirtPath01": 2})
    assert w[30, 30, 2] == 1.0 and w[30, 30, 0] == 0.0 and w[0, 0, 0] == 1.0


def test_pad_paint_fades_over_its_blend():
    """Lane 1.15-r6-claywater-pads-look: a binary disc read as a hard-edged slab; the paint eases out over blend_m
    (partial weight on a radius out to blend_m), and the weights still sum to 1."""
    g = _ground()
    p = patches.Patches.from_rows(_rows(), g, 0, lambda x, y: None)
    w = np.zeros((60, 60, 3), np.float32)
    w[..., 0] = 1.0
    p.paint(w, 0, 0, {"LDirtPath01": 2})
    line = w[30, 30:, 2]
    assert ((line > 0.02) & (line < 0.98)).sum() >= 1 and line[int((4.0 + max(p.items[0].blend_m, 2 * S)) / S) + 1:].max() == 0.0
    assert np.all(np.diff(line) <= 1e-6) and np.allclose(w.sum(axis=2), 1.0)


def test_old_key_only_rows_are_never_applied():
    p = patches.Patches.from_rows([{"id": "patch.bed-cut.x", "kind": None}], _ground(), 0, lambda x, y: None)
    assert len(p) == 0


def test_pad_stands_its_freeboard_over_the_wettest_cell_under_its_disc():
    """Lane 1.15-r6-claywater-water: Claywater's common stood 0.52 m over its river and the quest-board marker 0.08 m
    on the bank's slope. A pad by the water clears the highest cell water its disc touches by PAD_FREEBOARD_M; a pad
    already higher keeps its mean; a pad over dry cells keeps its mean."""
    g = _ground()
    mean = patches.Patches.from_rows(_rows(), g, 0, lambda x, y: None).items[0].level
    wet = lambda x, y: mean if x > 30 * S + 3.0 else None  # only the rim east of the centre is in a wet cell
    assert patches.Patches.from_rows(_rows(), g, 0, wet).items[0].level == round(mean + patches.PAD_FREEBOARD_M, 3)
    low = lambda x, y: mean - 5.0
    assert patches.Patches.from_rows(_rows(), g, 0, low).items[0].level == mean


def test_a_lift_keeps_the_yards_relief_and_clears_the_water():
    """Lane 1.15-r6-claywater-pad-seat: Skyrim.esm never flattens a farmstead's yard (58 farmhouses on slopes: the LAND
    runs on at the slope's gradient beside the footprint). A lift raises the yard by the least that sets its dry
    ground's low edge PAD_FREEBOARD_M over the water, its relief kept; the river's bed in its disc is never counted; over dry
    cells it is no change at all."""
    g = _ground()
    lift = _rows(kind="lift", radius_m=8.0, blend_m=4.0, ltex_edid=None)
    dry = patches.Patches.from_rows(lift, g, 0, lambda x, y: None)
    out = g.astype(np.float64).copy()
    dry.apply(out, 0, 0)
    assert np.allclose(out, g)
    lv = float(g[30, 30]) - 0.2  # the water 0.2 m under the yard's centre: the yard rises 1.2 m
    wet = patches.Patches.from_rows(lift, g, 0, lambda x, y: lv)
    v = patches.disc_values(g, 30, 30, -1.0, 8.0)
    low = float(np.percentile(v[v > lv], patches.LIFT_LOW_PCT))
    assert abs(wet.items[0].level - (lv + patches.PAD_FREEBOARD_M - low)) < 1e-3
    out = g.astype(np.float64).copy()
    wet.apply(out, 0, 0)
    yy, xx = np.mgrid[0:60, 0:60]
    d = np.hypot(yy - 30, xx - 30) * S
    inside = d <= 8.0
    assert np.allclose(out[inside] - g[inside], wet.items[0].level)  # raised as a whole: the slope is kept
    far = d > 8.0 + wet.items[0].blend_m + S
    assert np.allclose(out[far], g[far])


def _edge_profiles(out, r_m):
    """The ground every 0.5 m from a pad's rim to 12 m out, on its four sides (bilinear)."""
    t = np.arange(0.0, 12.01, 0.5)
    prof = []
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        rr, cc = 30 + dy * (r_m + t) / S, 30 + dx * (r_m + t) / S
        i, j = np.floor(rr).astype(int), np.floor(cc).astype(int)
        fr, fc = rr - i, cc - j
        prof.append(out[i, j] * (1 - fr) * (1 - fc) + out[i, j + 1] * (1 - fr) * fc + out[i + 1, j] * fr * (1 - fc)
                    + out[i + 1, j + 1] * fr * fc)
    return np.array(prof)


def test_a_footprint_pad_sits_in_the_slope_with_no_plate_edge():
    """Lane 1.15-r6-claywater-pad-seat: a pad inside a lift is read on the lifted ground (the station house's pad
    stood 1.0 m proud of the common's plate), and its edge falls to the slope no steeper than SEAT_FALL_DEG (Skyrim.esm's
    farmhouse LAND 0-3 m out, p90) with the road-profile bar's second difference (0.487 m p95 at 0.5 m steps);
    beyond the blend the ground is the slope's own, no flat run longer than Skyrim's beside a footprint (p90 8.5 m)."""
    g = _ground()
    lv = float(g[30, 30]) - 0.2
    rows = _rows(kind="lift", id="a-yard", radius_m=10.0, blend_m=4.0, ltex_edid=None) + _rows(id="b-house")
    p = patches.Patches.from_rows(rows, g, 0, lambda x, y: lv)
    lift, pad = p.items
    assert lift.kind == "lift" and pad.kind == "pad"
    # read on the lifted ground, its own freeboard kept
    assert abs(pad.level - max(patches.pad_level(g, 30, 30, 4.0) + lift.level, lv + patches.PAD_FREEBOARD_M)) < 1e-3
    out = g.astype(np.float64).copy()
    p.apply(out, 0, 0)
    prof = _edge_profiles(out, 4.0)
    assert np.percentile(np.abs(np.diff(prof, 2, axis=1)), 95) < 0.487
    # on Skyrim's p50 farmstead slope (5 deg) the edge falls no steeper than SEAT_FALL_DEG with the slope included
    g5 = (10.0 + np.tan(np.radians(5.0)) * np.mgrid[0:60, 0:60][1] * S).astype(np.float32)
    lv5 = float(g5[30, 30]) - 0.2
    out5 = g5.astype(np.float64).copy()
    patches.Patches.from_rows(rows, g5, 0, lambda x, y: lv5).apply(out5, 0, 0)
    fall = np.abs(np.diff(_edge_profiles(out5, 4.0), axis=1)).max() / 0.5
    assert np.degrees(np.arctan(fall)) <= patches.SEAT_FALL_DEG + 0.5
    flat = [(np.abs(z - z[0]) < 0.15).argmin() * 0.5 for z in prof]
    assert max(flat) <= 8.5


def test_a_steep_pad_edge_widens_its_blend_to_the_seat_gradient():
    g = _ground()
    p = patches.Patches.from_rows(_rows(blend_m=0.5, rise_m=2.0), g, 0, lambda x, y: None)
    need = 2.0 / np.tan(np.radians(patches.SEAT_FALL_DEG))
    assert p.items[0].blend_m >= need - 0.5
