"""The ground paint's rules: the road ramp, the six-slot cap, the materials and provinces, the engine view."""
import json
import os
from pathlib import Path

import numpy as np

from tools.newworld import landcover as lc
from tools.newworld.world import roadpaint as rp
from tools.newworld.world import texcheck as tc
from tools.newworld.world import texture as tx

REPO = Path(__file__).resolve().parents[2]


STUDIO_FIXTURE = REPO / "tools/places/studio/web/test/road_rule.json"


def road_rule_fixture() -> dict:
    """The road rule's numbers at fixed inputs, for the studio's path_paint.js to be tested against (node reads the
    file; this module proves the file is what the Python rule gives)."""
    pts = [[0, 0], [-838680, -835251], [12345, -67890], [-344064, -385024], [5000, 77777]]
    mix = [float(tx.road_mix(np.array([int(np.floor(-y / 128 + 0.5))]), np.array([int(np.floor(x / 128 + 0.5))]))[0]) for x, y in pts]
    cases = []
    for scale in sorted(set(rp.SCALE.values())):
        for e in (-4.0, -2.0, -0.45, 0.0, 1.0, 3.05, 5.0, 8.0, 9.0):
            for m in (-1.2, 0.0, 0.3, 2.0):
                p, a, b, v = (float(x) for x in rp.road_weights(e, scale, m))
                ov, ob, oa = (float(x) for x in rp.layer_opacities(e, scale, m))
                cases.append({"e": e, "scale": scale, "mix": m, "weights": [p, a, b, v], "opacities": [ov, ob, oa]})
    r6 = lambda o: json.loads(json.dumps(o), parse_float=lambda x: round(float(x), 6))
    return r6({"road_mix": [{"x": x, "y": y, "value": v} for (x, y), v in zip(pts, mix)], "cases": cases,
               "road_sets": {k: list(v) for k, v in rp.ROAD_SETS.items()}})


def test_the_studio_fixture_is_what_the_rule_gives():
    want = road_rule_fixture()
    if os.environ.get("ARGONIA_WRITE_FIXTURES"):
        STUDIO_FIXTURE.write_text(json.dumps(want, indent=1) + "\n")
    assert json.loads(STUDIO_FIXTURE.read_text()) == want


def test_the_road_is_no_steeper_than_skyrims_mean_ramp_and_is_gone_at_its_reach():
    for scale in (rp.SCALE["major"], rp.SCALE["minor"]):
        e = np.arange(-6, 12, rp.VERTEX_M / 4)  # any vertex placement across the edge
        for shift in np.linspace(0, rp.VERTEX_M, 5):
            for mix in (-2.0, 0.0, 2.0):
                here = rp.road_weights(e + shift, scale, mix)
                there = rp.road_weights(e + shift + rp.VERTEX_M, scale, mix)
                assert np.abs(here[0] - there[0]).max() <= 0.31       # the road's weight (texcheck road_step_p99)
                for a, b in zip(here[1:], there[1:]):                  # each of its materials (texcheck road_join_max)
                    assert np.abs(a - b).max() <= 0.31
        assert rp.pull(rp.reach_m(scale), scale) == 0 and rp.pull(-3, scale) >= 0.97


def test_no_grass_reaches_a_spine_and_every_set_carries_the_common_track():
    assert tx.MATERIALS[rp.COMMON_TRACK][1] == []
    for s in rp.ROAD_SETS.values():
        assert rp.COMMON_TRACK in s[:2]
    for cls in ("major", "minor"):   # within 1.5 m of a spine (texcheck's spine) the road holds 0.97 or more
        assert rp.pull(1.5 - rp.HALF_M[cls], rp.SCALE[cls]) >= 0.97


def test_the_core_falls_away_over_three_vertices_or_more_and_the_weights_sum_to_the_pull():
    assert (rp.CORE_OUT - rp.CORE_IN) >= 3 * rp.VERTEX_M
    p, a, b, v = rp.road_weights(np.array([-3.0, 0.0, 3.0]), 1.0, np.array([0.0, 2.0, -2.0]))
    assert np.allclose(a + b + v, p) and (v >= 0).all()
    m = rp.track_mix(np.array([-9.0, 9.0]))
    assert m.min() >= rp.TRACK_MIN - 1e-9 and m.max() <= 1 - rp.TRACK_MIN + 1e-9


def test_the_three_layers_compose_to_the_road_weights():
    e = np.linspace(-4, 9, 40)
    ov, ob, oa = rp.layer_opacities(e, 0.8, 0.4)
    p, a, b, v = rp.road_weights(e, 0.8, 0.4)
    assert np.allclose(oa, a, atol=1e-9)
    assert np.allclose(ob * (1 - oa), b, atol=1e-9)
    assert np.allclose(ov * (1 - ob) * (1 - oa), v, atol=1e-9)


def test_a_quadrant_carries_six_textures_at_most_and_round_trips():
    assert tx.MAXL == 6 and tc.SLOTS == 6
    rng = np.random.default_rng(1)
    w = rng.random((289, tx.NM)).astype(np.float32)
    w[:, 6:] = 0
    w /= w.sum(1, keepdims=True)
    order = list(np.argsort(-w.sum(0))[:6])
    b = tx.quad_bytes(w, order)
    mats, comp = tx.decode_quad(b, 0)
    assert mats == order and np.abs(comp - w[:, order]).max() <= 3 / 255


def test_the_engine_view_hides_a_seventh_texture():
    # a quadrant written with seven textures (the old build): the seventh layer's weight is not shown
    maxl = 7
    qb = 1 + maxl + (maxl - 1) * 289
    a = np.zeros(qb, np.uint8)
    a[0] = 7
    a[1:8] = np.arange(7)
    al = a[1 + maxl:].reshape(maxl - 1, 289)
    al[:] = 0
    al[5] = 255  # the top layer covers everything
    dense, n, loss, lost = tc.decode_row(a.tobytes(), maxl, 8)
    assert n[0] == 7 and dense[0, :, 6].max() == 0 and dense[0, :, 0].min() == 1 and loss.max() == 1
    assert lost[0, :, 6].min() == 1


def test_steps_count_the_triangle_diagonal_per_vertex_spacing():
    g = np.zeros((17, 17, 1), np.float32)
    g[1, 0] = 1  # one vertex: its diagonal neighbour (0, 1) steps by 1 over 1.41 spacings
    s = np.abs(tc.steps(g))
    assert s.max() == 1 and s.shape[0] == 16 * 17 * 2 + 16 * 16
    assert abs(float(s[16 * 17 * 2:].max()) - 1 / np.sqrt(2)) < 1e-6


def test_a_quadrant_keeps_its_corner_grounds_then_the_common_track_then_the_heaviest_roads():
    hq = 2
    n = 17 + 2 * hq
    w = np.zeros((n, n, tx.NM), np.float32)
    ground = np.zeros_like(w)
    names = ["moss", "rock", "sand", "meadow"]
    for k, m in enumerate(names):   # four grounds, one heaviest at each corner
        ground[(hq, hq, hq + 16, hq + 16)[k], (hq, hq + 16, hq, hq + 16)[k], tx.MI[m]] = 1
        w[..., tx.MI[m]] = 0.1
    for m, v in (("gravel_track", 0.05), ("mud_track", 0.2), ("verge", 0.3)):
        w[..., tx.MI[m]] = v
    keep, _ = tx.quadrant_sets(w, ground, hq)
    kept = {tx.MAT[i] for i in np.flatnonzero(keep[0, 0])}
    assert kept == set(names) | {"gravel_track", "verge"}   # four corners, the common track, the heaviest other road


def test_the_road_distance_is_to_the_line_itself():
    segs = [(10.0, 10.0, 30.0, 30.0, 2), (10.0, 10.0, 10.0, 60.0, 1)]  # a diagonal path and a major road from one point
    d, cls = lc.road_field((80, 80), segs)
    assert abs(d[20, 21] - np.sqrt(0.5)) < 1e-4 and d[20, 20] == 0   # beside the diagonal: 0.71 samples, not 1
    assert cls[20, 21] == 2 and cls[10, 40] == 1 and cls[10, 10] == 1  # a major road wins the tie at the junction
    assert abs(d[70, 70] - np.hypot(40, 40)) < 1.0 and d[79, 0] >= lc.ROAD_EXACT


def test_value_noise_is_a_function_of_position_alone():
    r = np.arange(100, 140)[:, None] + np.zeros((1, 30), np.int64)
    c = np.arange(500, 530)[None, :] + np.zeros((40, 1), np.int64)
    whole = tx.vnoise(5, r, c, 8)
    part = tx.vnoise(5, r[10:20, 5:9], c[10:20, 5:9], 8)
    assert np.array_equal(whole[10:20, 5:9], part)
    big = tx.vnoise(5, np.arange(0, 4000)[:, None] + np.zeros((1, 50), np.int64), np.arange(50)[None] + np.zeros((4000, 1), np.int64), 8)
    assert 0.6 < big.std() < 1.4


def test_every_named_material_exists_and_roads_beaches_and_rock_grow_no_grass():
    names = set(tx.MATERIALS)
    for pal in tx.PALETTE.values():
        assert set(pal) <= names
    for p in tx.PROVINCES.values():
        for acc in p["accent"].values():
            assert set(acc) <= names
        assert set(p["grass"]) <= names and p["road"] in rp.ROAD_SETS
    assert set(rp.ROAD_MATERIALS) <= names and set(tx.AFF) <= names
    bare = set(rp.ROAD_MATERIALS) | {"sand", "wet_sand", "beach", "pale_sand", "rock", "rock2", "pale_rock", "red_rock", "grey_gravel",
                                     "black_gravel", "marsh_mud", "silt", "grey_mud"}
    for m in bare:
        assert tx.MATERIALS[m][1] == [], m
    rows = tx.material_rows()
    assert len({r["id"] for r in rows}) == tx.NM and all(r["diffuse"] for r in rows)
    for r in rows:
        if r["scope"]:
            base = r["id"].split("~")[0]
            assert r["grass"] and r["grass"] != tx.MATERIALS[base][1]


def test_every_land_region_of_the_research_has_a_province_and_no_province_names_a_stranger():
    regions = json.loads((REPO / "newworld/sources/flora/regions.json").read_text())["regions"]
    land = {r for r, v in regions.items() if not set(v["habitats"]) <= {"seabed_shallow", "seabed_mid", "seabed_deep"}}
    named = [r for p in tx.PROVINCES.values() for r in p["regions"]]
    assert len(named) == len(set(named)) and set(named) <= set(regions) and set(tx.REGIONS) <= set(named)
    assert all(r["look"] in tx.MATERIALS and set(r["grass"]) <= set(tx.MATERIALS) for r in tx.REGIONS.values())
    sea_edge = {"sea-of-mists", "topal-bay"}  # sea regions with a mangrove or beach fringe: painted by their edges
    assert land - sea_edge <= set(named)


def test_micro_relief_marks_humps_and_hollows():
    h = np.zeros((60, 60), np.float32)
    h[30, 30] = 700.0
    h[10, 10] = -700.0
    r = lc.micro_relief(h)
    assert r.dtype == np.int8 and r[30, 30] > 0 and r[10, 10] < 0


def test_a_signature_ground_is_brought_up_to_its_share_and_never_stacked_on_the_accent():
    v = tx.vec({"rock": .4, "moss": .4, "grey_gravel": .2 * 4 / 3.2})   # the accent already gives it 0.2 or more
    look = tx.MI["grey_gravel"]
    assert v[look] >= tx.SIG and np.array_equal(tx.signed(v, look), v)
    low = tx.vec({"rock": .5, "moss": .45, "grey_gravel": .05})
    out = tx.signed(low, look)
    assert abs(out[look] - tx.SIG) < 1e-6 and abs(out.sum() - 1) < 1e-6
    assert abs(out[tx.MI["rock"]] / out[tx.MI["moss"]] - .5 / .45) < 1e-5
    none = tx.signed(tx.vec({"rock": 1}), look)
    assert abs(none[look] - tx.SIG) < 1e-6 and abs(none[tx.MI["rock"]] - (1 - tx.SIG)) < 1e-6
    # no palette holds its signature twice over: the heaviest share of any classed habitat stays under 0.45
    legend = {"shape": [8, 8], "habitats": ["none"] + list(tx.PALETTE), "kinds": [], "regions": list(tx.REGIONS)}
    prov = tx.province_of(legend["regions"])
    for r, rn in enumerate(legend["regions"]):
        for h, cls in tx.HAB_CLASS.items():
            pal = (1 - tx.ACCENT) * tx.vec(tx.PALETTE[h]) + tx.ACCENT * tx.vec(tx.PROVINCES[tx.PROV[prov[r] - 1]]["accent"][cls])
            assert tx.signed(pal, tx.MI[tx.REGIONS[rn]["look"]]).max() < 0.45, (rn, h)
