"""The ground paint's rules: the road ramp, the six-slot cap, the materials and provinces, the engine view."""
import json
from pathlib import Path

import numpy as np

from tools.newworld import landcover as lc
from tools.newworld.world import roadpaint as rp
from tools.newworld.world import texcheck as tc
from tools.newworld.world import texture as tx

REPO = Path(__file__).resolve().parents[2]


def test_the_road_ramp_never_steps_more_than_half_between_two_vertices_and_is_gone_at_its_reach():
    for scale in (rp.SCALE["major"], rp.SCALE["minor"]):
        e = np.arange(-6, 12, rp.VERTEX_M / 4)  # any vertex placement across the edge
        for shift in np.linspace(0, rp.VERTEX_M, 5):
            a = rp.pull(e + shift, scale)
            b = rp.pull(e + shift + rp.VERTEX_M, scale)
            assert np.abs(a - b).max() <= 0.5
        assert rp.pull(rp.reach_m(scale), scale) == 0 and rp.pull(-3, scale) >= 0.97


def test_the_core_hands_to_the_verge_over_two_vertices_or_more():
    assert (rp.CORE_OUT - rp.CORE_IN) >= 2 * rp.VERTEX_M
    p, a, b, v = rp.road_weights(np.array([-3.0, 0.0, 3.0]), 1.0, np.array([0.0, 2.0, -2.0]))
    assert np.allclose(a + b + v, p)
    m = rp.track_mix(np.array([-9.0, 9.0]))
    assert m.min() >= rp.TRACK_MIN - 1e-9 and m.max() <= 1 - rp.TRACK_MIN + 1e-9


def test_the_three_layers_compose_to_the_road_weights():
    e = np.linspace(-4, 9, 40)
    ov, ob, oa = rp.layer_opacities(e, 0.6, 0.4)
    p, a, b, v = rp.road_weights(e, 0.6, 0.4)
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


def test_steps_count_the_triangle_diagonal():
    g = np.zeros((17, 17, 1), np.float32)
    g[1, 0] = 1  # one vertex: its diagonal neighbour (0, 1) steps by 1
    s = np.abs(tc.steps(g))
    assert s.max() == 1 and s.shape[0] == 16 * 17 * 2 + 16 * 16


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
