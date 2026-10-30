"""L1: the placement's rules on hand-made cells (no game data, no world database)."""
import math

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import place
from tools.argonia_world.vegetation.place import CellInputs, Rule

V = su.LAND_VERTS


def rule(**kw):
    base = dict(form_key="000001:Skyrim.esm", density_per_ha=60.0, clustering=1, radius_m=0.0, min_slope=0,
                max_slope=40, min_height=None, max_height=None, water_min=-99.0, water_max=0.35, conform=False,
                scale=(0.8, 1.2))
    base.update(kw)
    return Rule(**base)


def cell(H=None, L=None, T=None, roads=(), feet=(), cx=0, cy=0):
    H = np.full((V, V), 10.0) if H is None else H
    return CellInputs(cx, cy, H, np.zeros((V, V)) if L is None else L, np.zeros((V, V)) if T is None else T,
                      np.zeros((V, V), bool), south_row=1000, west_col=1000, roads=list(roads), footprints=list(feet))


def test_density_is_calibrated_per_hectare():
    for r in (rule(density_per_ha=60.0), rule(density_per_ha=7.3, clustering=4, radius_m=8.0),
              rule(density_per_ha=0.6, clustering=2, radius_m=12.0)):
        n = sum(place.candidates(r, cx, 0)["u"].size for cx in range(400))
        want = r.density_per_ha * place.CELL_HA * 400
        assert abs(n - want) / want < 0.06, (r, n, want)


def test_deterministic_by_cell_and_form():
    a = place.place_cell(cell(cx=3, cy=-2), [rule(), rule(form_key="000002:Skyrim.esm", clustering=5, radius_m=6.0)])
    b = place.place_cell(cell(cx=3, cy=-2), [rule(), rule(form_key="000002:Skyrim.esm", clustering=5, radius_m=6.0)])
    assert all(np.array_equal(a[k], b[k]) for k in a)
    c = place.place_cell(cell(cx=4, cy=-2), [rule()])
    assert not np.array_equal(a["u"][:5], c["u"][:5])


def test_ground_spacing_scale_and_bounds():
    j = np.arange(V)[None, :] * 0.3
    H = np.repeat(j, V, axis=0) + 5.0  # a plane rising east, 9.3 degrees
    p = place.place_cell(cell(H=H), [rule(density_per_ha=200.0, clustering=4, radius_m=5.0)])
    assert p["u"].size > 20
    za, zb, gx, gy, *_ = place.ground_at(H, p["u"], p["v"])
    assert np.allclose(za, zb) and np.allclose(p["z"], za)
    assert np.allclose(place.slope_deg(gx, gy), math.degrees(math.atan(0.3 / place.STEP_M)))
    assert ((p["scale"] >= 0.8) & (p["scale"] <= 1.2)).all()
    assert ((p["u"] >= 0) & (p["u"] < su.CELL_UNITS) & (p["v"] >= 0) & (p["v"] < su.CELL_UNITS)).all()
    d = np.hypot(p["u"][:, None] - p["u"][None], p["v"][:, None] - p["v"][None]) + np.eye(p["u"].size) * 1e9
    assert d.min() >= su.metres_to_units(place.MIN_SPACING_M)


def test_slope_and_height_bands():
    j = np.arange(V)[None, :] * 1.5
    steep = np.repeat(j, V, axis=0)  # 39 degrees
    assert place.place_cell(cell(H=steep), [rule(max_slope=30)])["u"].size == 0
    assert place.place_cell(cell(H=steep), [rule(min_slope=35, max_slope=45)])["u"].size > 0
    assert place.place_cell(cell(), [rule(max_height=5.0)])["u"].size == 0
    assert place.place_cell(cell(), [rule(min_height=5.0, max_height=20.0)])["u"].size > 0


def test_water_posture():
    dry = rule(water_min=None, water_max=None)
    wading = rule(form_key="000002:Skyrim.esm", water_min=-6.0, water_max=1.4)
    aquatic = rule(form_key="000003:Skyrim.esm", water_min=0.6, water_max=3.5)
    wet = cell(L=np.full((V, V), 11.0))  # 1 m of water over ground at 10
    assert place.place_cell(wet, [dry])["u"].size == 0
    assert place.place_cell(wet, [wading])["u"].size > 0
    assert place.place_cell(wet, [aquatic])["u"].size > 0
    deep = cell(L=np.full((V, V), 14.0))  # 4 m: past both
    assert place.place_cell(deep, [wading, aquatic])["u"].size == 0
    high = cell(T=np.full((V, V), 2.0))  # dry, 8 m above the table
    assert place.place_cell(high, [wading])["u"].size == 0
    assert place.place_cell(high, [dry])["u"].size > 0
    assert place.place_cell(high, [aquatic])["u"].size == 0


def test_road_and_place_exclusion():
    seg = np.array([[[1000.0, 1000.0], [1000.0 - 32, 1032.0]]])  # corner to corner, rows decrease northwards
    half = 3.0 / su.PROVINCE_SAMPLE_M
    p = place.place_cell(cell(roads=[(half, seg)]), [rule(density_per_ha=300.0)])
    pr, pc = 1000 - p["v"] / su.VERTEX_SPACING_UNITS, 1000 + p["u"] / su.VERTEX_SPACING_UNITS
    assert (place.seg_dist(pr, pc, seg) >= half + place.ROAD_MARGIN_M / su.PROVINCE_SAMPLE_M).all()
    foot = (980.0, 1000.0, 1000.0, 1016.0)  # the cell's south-west quarter, in grid rows/cols
    q = place.place_cell(cell(feet=[foot]), [rule(density_per_ha=300.0)])
    qr, qc = 1000 - q["v"] / su.VERTEX_SPACING_UNITS, 1000 + q["u"] / su.VERTEX_SPACING_UNITS
    assert q["u"].size and not ((qr >= 980) & (qc <= 1016)).any()


def test_budget_threshold_holds_the_cap():
    t = np.random.default_rng(1).random(900)
    k = place.keep_value(place.threshold(t, 400))
    assert (t < k).sum() <= 400 and (t < k).sum() >= 398
    assert place.threshold(t[:300], 400) == 1.0


def test_formid_slots_clear_the_other_ranges():
    lo = place.ref_id(*su.PROVINCE_CELL_SW, 0)
    hi = place.ref_id(su.PROVINCE_CELL_SW[0] + su.PROVINCE_CELLS - 1, su.PROVINCE_CELL_SW[1] + su.PROVINCE_CELLS - 1,
                      place.SLOT - 1)
    assert lo > 0x600000 + 262 ** 2  # past the NAVMs (tools/navmesh/stitch.py)
    assert hi <= su.FORMID_LAST
    assert place.CAP <= place.SLOT


def test_vanilla_keep_brings_a_region_into_vanillas_range():
    counts = list(range(0, 275))
    k = place.vanilla_keep(counts)
    assert np.percentile(counts, 95) * k <= place.VANILLA_P95 + 1e-9 and max(counts) * k <= place.VANILLA_MAX
    assert place.vanilla_keep([3, 10, 20]) == 1.0
