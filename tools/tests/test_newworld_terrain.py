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


def test_weathering_drains_keeps_marsh_flat_and_settles_places():
    from tools.newworld import terrain_erode as te
    n = 160
    rng = np.random.default_rng(3)
    water = np.zeros((n, n), bool)
    water[:, :10] = True
    relief = (tr.noise((n, n), 12, 5) * 6 + 30).astype(np.float32)
    relief[water] = 0
    F = {"floor": np.full((n, n), 5.0), "summit": np.full((n, n), 80.0), "rough": np.full((n, n), 3.0),
         "w_mesa": np.zeros((n, n))}
    out = te.weather(relief, water, F, 7)
    land = ~water
    assert out[land].min() >= min(te.DRY_M, relief[land].min()) - 1e-4     # no new water
    from skimage.morphology import reconstruction
    outlet = water.copy()
    outlet[0, :] = outlet[-1, :] = outlet[:, 0] = outlet[:, -1] = True
    before = reconstruction(np.where(outlet, relief, relief.max() + 1), relief, method="erosion")
    assert (before - relief)[land].max() > 0.5                              # (the noise had hollows to drain)
    assert np.abs(out - relief)[land].max() > 0.3                          # rain and drainage cut the hills
    low = dict(F, summit=np.full((n, n), 15.0))                             # low ground: every hollow drains
    raw = (relief - 25).clip(1, None).astype(np.float32)
    lo = te.weather(raw, water, low, 7)
    depth = lambda z: (reconstruction(np.where(outlet, z, z.max() + 1), z, method="erosion") - z)[land].max()
    assert depth(lo) <= te.LOW_HOLLOW_M * te.LOW_FILL + 0.05 < depth(raw)   # low ground: only shallow dips
    del rng
    r = out.copy()
    done = te.settle_places(r, [(80.0, 90.0, "town")], te.M)
    assert done and done[0]["slope_p98_deg"] <= te.BUILD_MAX_SLOPE_DEG + 0.5
    assert done[0]["relief_m"] > 0.05                                       # not bulldozed flat


def test_smooth_coast_keeps_thin_streams_and_rounds_square_corners():
    from scipy import ndimage as ndi
    from tools.newworld import terrain_coast as tc
    water = np.zeros((80, 80), bool)
    water[:, :20] = True                       # sea on the west
    water[40, 20:70] = True                    # a 1 px stream into it
    water[5:25, 20:40] = True                  # a square bay with sharp corners
    g = ts.Grid(rows=120, cols=120, p0x=0.0, p0y=0.0)
    sd, thin, force = tc.signed_distance(water, 3)
    s = tc.sample(sd, thin, g, 3, force=force)
    ws = s < 0
    lab, _ = ndi.label(ws)
    i, j = g.ij(np.array([65.5, 10.0]), np.array([40.5, 40.5]))
    a = lab[int(round(i[0])), int(round(j[0]))]
    b = lab[int(round(i[1])), int(round(j[1]))]
    assert a > 0 and a == b                    # the stream reaches the sea in one body
    ci, cj = g.ij(np.array([39.5]), np.array([24.5]))   # the bay's outer south-east corner pixel
    assert s[int(round(ci[0])), int(round(cj[0]))] > -1.0   # rounded: no longer deep inside the water
    agr = tc.agreement(ws, g, water)
    assert agr["blocks4"] > 0.97


def test_contour_coast_smooths_steps_and_keeps_streams():
    from scipy import ndimage as ndi
    from tools.newworld import terrain_coast as tc
    water = np.zeros((80, 80), bool)
    water[:, :20] = True                       # sea on the west
    water[40, 20:70] = True                    # a 1 px stream into it
    for k in range(5):                         # a bay whose east shore steps 4 px at a time
        water[5 + 4 * k:9 + 4 * k, 20:28 + 4 * k] = True
    g = ts.Grid(rows=120, cols=120, p0x=0.0, p0y=0.0)
    s = tc.sample_contour(water, g, 3)
    ws = s < 0
    lab, _ = ndi.label(ws)
    i, j = g.ij(np.array([65.5, 10.0]), np.array([40.5, 40.5]))
    assert lab[int(round(i[0])), int(round(j[0]))] > 0
    assert lab[int(round(i[0])), int(round(j[0]))] == lab[int(round(i[1])), int(round(j[1]))]
    assert tc.agreement(ws, g, water)["blocks4"] > 0.97
    # the stepped shore is one slope: the shore column per row grows smoothly, no 4 px jumps
    rows = np.arange(int(8 / g.k), int(24 / g.k))
    edge = np.array([np.flatnonzero(~ws[r, int(20 / g.k):])[0] for r in rows], float)
    assert np.abs(np.diff(edge)).max() <= 2.5


def test_smooth_line_keeps_a_circle_size():
    from tools.newworld import terrain_coast as tc
    t = np.linspace(0, 2 * np.pi, 200, endpoint=False)
    c = np.stack([30 * np.sin(t), 30 * np.cos(t)], 1)
    r = np.hypot(*tc.smooth_line(c).T)
    assert abs(r.mean() - 30) < 0.3


def test_droplets_cut_and_stay_off_the_water():
    from tools.newworld import terrain_droplets as td
    n = 64
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    h = (xx * 0.5 + tr.noise((n, n), 8, 2) * 0.5).astype(np.float32)
    stop = np.zeros((n, n), bool)
    stop[:, :3] = True
    k = np.ones((n, n), np.float32)
    k[:, 50:] = 0
    out = td.erode(h, k, stop, 400, 5)
    assert (out - h)[:, 4:46].min() < -0.01                  # it erodes
    assert np.abs(out - h)[:, 54:].max() == 0                 # not where erodibility is 0


def test_pad_follows_the_slope_without_a_rim():
    water = np.zeros((62, 62), bool)
    g = _grid()
    yy = np.arange(g.rows)[:, None] * np.ones((1, g.cols))
    h = (yy * 4.0 + 500).astype(np.float32)               # a gentle even slope
    before = h.copy()
    ts.flat_pad(h, np.zeros(h.shape, bool), g, 48.0, 48.0, 25.0)
    assert np.abs(h - before).max() < 0.6 * ts.U         # a plane on the land's lie: almost nothing cut or filled
    del water


def test_shore_access_leaves_dry_ground_alone():
    g = _grid()
    h = np.full((g.rows, g.cols), 30 * ts.U, np.float32)
    before = h.copy()
    ts.shore_access(h, np.zeros(h.shape, bool), g, 48.0, 48.0, 30.0)
    assert np.array_equal(h, before)
