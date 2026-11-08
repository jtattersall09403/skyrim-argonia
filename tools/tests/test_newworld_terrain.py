"""The terrain shaping on small synthetic maps: water held, steps storable, roads graded, bodies labelled stably."""
import numpy as np

from tools.newworld import terrain_relief as tr
from tools.newworld import terrain_shape as ts
from tools.newworld import terrain_water as tw


def _grid(n=97):
    return ts.Grid(rows=n, cols=n, p0x=0.0, p0y=0.0)


def _map(n=62):
    water = np.zeros((n, n), bool)
    water[:, :8] = True                      # sea on the west
    water[30, 8:50] = True                   # a 1 px stream into it
    water[40:46, 20:26] = True               # a pond
    return water


def _terrain(water):
    g = _grid()
    ws = ts.sample_classes(g, water)
    relief = np.full(ws.shape, 20.0, np.float32)
    h, _, _ = ts.compose(ws, relief, np.full(ws.shape, 20.0), np.full(ws.shape, 0.2), np.full(ws.shape, 3.0), g.m)
    return g, ws, h


def test_water_guaranteed_and_land_format():
    water = _map()
    g, ws, h = _terrain(water)
    h = ts.quantise(h)
    ts.clamp_steps(h)
    fails = ts.guarantee(h, g, water)
    assert fails == []
    v, _, _ = ts.pixel_values(h, g, ts.px_box(g, water.shape))
    l, t, r, b = ts.px_box(g, water.shape)
    w = water[t:b, l:r]
    assert (v[w] < 0).all() and (v[~w] > 0).all()
    assert ts.land_format(h)["ok"]


def test_clamp_steps_fits_vhgt():
    h = np.zeros((33, 33), np.float32)
    h[16, 16] = 5000
    ts.clamp_steps(h)
    assert ts.land_format(h)["max_step_units"] <= ts.MAX_STEP


def test_road_grade_and_trough():
    water = np.zeros((62, 62), bool)
    g = _grid()
    yy = np.arange(g.rows)[:, None] * np.ones((1, g.cols))
    h = (yy * 30.0).astype(np.float32) + 100            # 30 units per 128: grade 0.23
    pts = [[30.0, 2.0], [30.0, 58.0]]
    pl = ts.plan_road(h, water, g, pts, 0.186)
    ts.stamp_roads(h, np.zeros(h.shape, bool), g, [(pl, "major")])
    res = ts.road_checks(h, g, [(pl, "major")], {"major": 0.186})
    assert res["grade_max"] <= 0.186 + 0.03
    assert res["trough4m_p50"] > 0.1


def test_entrance_faces_dry_ground():
    water = np.zeros((62, 62), bool)
    water[:, :20] = True
    g = _grid()
    ws = ts.sample_classes(g, water)
    h = np.where(ws, -100.0, 300.0).astype(np.float32)
    facing, dry = ts.choose_facing(h, ws, g, 48.0, 60.0)
    assert dry == 1.0 and not 225 <= facing <= 315       # not toward the western water
    ts.entrance(h, ws, g, 48.0, 60.0, facing)
    ok = ts.entrance_ok(h, ws, ts.slope_deg(h) > 55, g, 48.0, 60.0, facing)
    assert ok["dry"]


def test_water_bodies_stable_and_flowing():
    water = np.zeros((200, 200), bool)
    water[:, :60] = True
    water[100, 60:150] = True
    names = ["sea-a", "land-a"]
    code = np.ones(water.shape, np.int32)
    code[:, :60] = 0
    a, bodies = tw.label_bodies(water, code, names, {"sea-a": "sea", "land-a": "land"}, {}, 2.93)
    b2 = tw.label_bodies(water, code, names, {"sea-a": "sea", "land-a": "land"}, {}, 2.93)[1]
    assert [b["id"] for b in bodies] == [b["id"] for b in b2]
    tw.flow(a, bodies, {"stream": True, "ocean": False, "pond": False, "bay": False})
    streams = [b for b in bodies if b["water_kind_id"] == "stream"]
    assert streams and all(b["flows"] for b in streams)
    assert any(225 <= b.get("flow_deg", 0) <= 315 for b in streams)   # westward to the sea


def test_fallback_by_landform_word():
    class R:
        id, name, landform = "x-mesa", "Chixathe Mesa", None
        elevation_floor_m = elevation_summit_m = roughness_m = cliff_share = wetness = None
    p, src = tr.region_params(R)
    assert p["form"] == "mesa" and "fallback" in src
    R.elevation_summit_m = 99.0
    p, src = tr.region_params(R)
    assert p["summit"] == 99.0 and "db" in src
