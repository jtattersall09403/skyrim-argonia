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


def test_road_corridor_keeps_a_tree_trunk_off_the_lane():
    # round 6: a trunk is a body. The centre may sit outside half + margin and the trunk still stand on the lane.
    seg = np.array([[[1000.0, 1000.0], [1000.0 - 32, 1032.0]]])
    half = 3.0 / su.PROVINCE_SAMPLE_M
    big = rule(density_per_ha=300.0, tree=True, reach_m=3.0, scale=(1.0, 1.0))
    p = place.place_cell(cell(roads=[(half, seg)]), [big])
    pr, pc = 1000 - p["v"] / su.VERTEX_SPACING_UNITS, 1000 + p["u"] / su.VERTEX_SPACING_UNITS
    assert p["u"].size
    assert (place.seg_dist(pr, pc, seg) >= half + (place.ROAD_MARGIN_M + 3.0) / su.PROVINCE_SAMPLE_M).all()
    assert place.road_reach(rule(reach_m=9.0), [2.0])[0] == place.ROAD_REACH_CAP_M  # capped


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


def test_sink_fractions_are_skyrims_medians():
    """Decision 0034, audit section 5: boulders 0.5 of their height, cliff shells 0.7; none of ours was lower."""
    from tools.argonia_world.vegetation import lists
    assert (lists.SINK_BOULDER, lists.SINK_CLIFF) == (0.5, 0.7)
    assert lists.upright_share(lists.SINK_BOULDER) == lists.UPRIGHT_BOULDER == 0.25
    assert lists.upright_share(lists.SINK_CLIFF) == 0.0 and lists.upright_share(0.0) == 0.0


def test_a_quarter_of_boulders_stand_upright():
    H = np.zeros((V, V))
    H[:] = np.arange(V)[None, :] * 0.8  # a slope: a conformed rock tilts
    r = rule(density_per_ha=600.0, conform=True, upright=0.25, max_slope=60)
    n = flat = 0
    for cx in range(8):
        out = place.place_cell(cell(H=H, cx=cx), [r])
        flat += int(((out["rx"] == 0) & (out["ry"] == 0)).sum())
        n += out["rx"].size
    assert abs(flat / n - 0.25) < 0.05, flat / n
    out = place.place_cell(cell(H=H), [rule(density_per_ha=600.0, conform=True, max_slope=60)])
    assert (np.hypot(out["rx"], out["ry"]) > 0).all()  # no upright share: all conform


def test_tree_band_check_flags_a_thin_forest_and_passes_a_marsh():
    from tools.argonia_world.vegetation import checks
    eco = {"a": "flooded-forest", "b": "deep-sink-basin"}
    rep, errs = checks.tree_bands({"a": [3, 5, 4] * 4, "b": [15, 20, 19]}, eco, [1, 20], [300.0, 500.0])
    assert len(errs) == 1 and errs[0].startswith("a (forest)")
    assert rep["regions"]["b"]["band"] == "marsh" and rep["in_water_share"] == 0.05


def test_a_window_builds_the_same_twice():
    """Determinism: placing a window of cells twice (the second in reverse cell order, so no draw can lean on call
    order or shared state) gives identical stems, conforming rocks and clumps included."""
    rules = [rule(), rule(form_key="000002:Skyrim.esm", conform=True, upright=0.5, density_per_ha=20.0),
             rule(form_key="000003:Skyrim.esm", clustering=4, radius_m=8.0, density_per_ha=9.0)]
    H = 10.0 + np.add.outer(np.arange(V), np.arange(V)) * 0.05
    cells = [(cx, cy) for cx in range(-9, -7) for cy in range(1, 3)]
    a = {c: place.place_cell(cell(H=H, cx=c[0], cy=c[1]), rules) for c in cells}
    b = {c: place.place_cell(cell(H=H, cx=c[0], cy=c[1]), rules) for c in reversed(cells)}
    assert sum(len(a[c]["u"]) for c in cells) > 0
    for c in cells:
        for k in a[c]:
            assert np.array_equal(a[c][k], b[c][k]), (c, k)


def test_tree_keep_closes_the_band_deterministically():
    from tools.argonia_world.vegetation import build
    rng = np.random.default_rng(1)
    mk = lambda: {"thin": rng.random(300), "tree": np.ones(300, bool), "countable": True}
    placed = {(i, 0): mk() for i in range(12)}
    region = {c: "r.coastal-lagoon" for c in placed}
    tk, info = build.tree_keeps(placed, region, {"r.coastal-lagoon": 1.0}, {"r.coastal-lagoon": "coastal-lagoon"})
    assert info["r.coastal-lagoon"]["mean_after"] == 18.0 and tk["r.coastal-lagoon"] < 0.1
    p = placed[(0, 0)]
    assert (place.final_mask(p["thin"], p["tree"], 1.0, tk["r.coastal-lagoon"]) ==
            place.final_mask(p["thin"], p["tree"], 1.0, tk["r.coastal-lagoon"])).all()


def test_tree_score_is_position_seeded_and_in_range():
    from tools.argonia_world.vegetation import build
    r = np.array([[1234.5, 99.25], [1234.5, 99.25], [5.0, 7.0]])
    s = build.tree_score(r)
    assert s[0] == s[1] and s[0] != s[2] and ((0 <= s) & (s < 1)).all()
