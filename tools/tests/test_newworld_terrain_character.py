"""Relief character (terrain_forms), the ground past the map (terrain_beyond), held ground (terrain_held), the scope
past the picture (tiles) and the character measure (terrain_character), on small synthetic grids."""
import json

import numpy as np
import pytest

from tools.newworld import frame as f
from tools.newworld import terrain_beyond as tb
from tools.newworld import terrain_character as tch
from tools.newworld import terrain_forms as tf
from tools.newworld import terrain_held as th
from tools.newworld import terrain_shape as ts


def _crop(i0=0, j0=0, n=200, seed=7):
    z = np.zeros((n, n), np.float32)
    return tf.Crop(i0=i0, j0=j0, shape=(n, n), ox=0.0, oy=0.0, m=128 / 70, rel=z + 3.0, dw=z + 50.0,
                   dsea=z + 1e4, droad=z + 1e6, span=z + 20.0, seed=seed)


def test_forms_anchored_to_the_world():
    """Two overlapping windows lay the same ground where they overlap: features are fixed by world position."""
    a = tf.root_hummocks(_crop(0, 0), "after")
    b = tf.root_hummocks(_crop(50, 70), "after")
    assert np.allclose(a[50:, 70:], b[:150, :130], atol=1e-4)
    for name in ("ring-mounds", "ravined-mounds", "cuesta"):          # the forms that read noise, too
        fa = sum(x for x in (tf.CHARACTERS[name](_crop(0, 0), s) for s in ("before", "after")) if x is not None)
        fb = sum(x for x in (tf.CHARACTERS[name](_crop(50, 70), s) for s in ("before", "after")) if x is not None)
        assert np.allclose(fa[50:, 70:], fb[:150, :130], atol=2e-3), name
    assert a.max() > 0.3                        # hummocks stand up to about a metre


@pytest.mark.parametrize("name", sorted(tf.CHARACTERS))
def test_every_character_runs_and_is_bounded(name):
    for stage in ("before", "after"):
        add = tf.CHARACTERS[name](_crop(), stage)
        if add is not None:
            assert add.shape == (200, 200) and np.isfinite(add).all()
            assert np.abs(add).max() < 40.0


def test_characters_differ():
    """Each character's fine shape differs from every other's (not one noise at another amplitude)."""
    sig = {}
    for name, fn in tf.CHARACTERS.items():
        c = _crop()
        c.dw = np.tile(np.linspace(0, 300, 200, dtype=np.float32), (200, 1))
        c.dsea = c.dw * 2
        add = sum(x for x in (fn(c, "before"), fn(c, "after")) if x is not None)
        if np.isscalar(add) or not np.abs(add).max():
            continue
        sig[name] = add / (np.abs(add).max())
    names = sorted(sig)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert np.abs(sig[a] - sig[b]).mean() > 0.01, (a, b)


def test_apply_respects_weights_and_dry_floor():
    H = W = 64
    rel = np.full((H, W), 2.0, np.float32)
    wc = np.zeros((H // 8 + 2, W // 8 + 2), np.float32)
    wc[:, : 5] = 1.0                            # the region covers the west
    spec = {"r": {"character": "knob-and-kettle"}}
    done = tf.apply(rel, "after", spec, {"r": wc}, 8, ox=0.0, oy=0.0, m=128 / 70, dw=np.full((H, W), 100.0, np.float32),
                    coast_t=np.full((H, W), 0.9, np.float32), road_ij=np.zeros((0, 2)), span=np.full((H, W), 10.0))
    assert "r" in done
    assert rel.min() >= tf.DRY_M - 1e-6        # a kettle never digs under the dry floor
    assert np.allclose(rel[:, 50:], 2.0)       # nothing outside the region


def test_overrides():
    p = tf.overrides({"x": {"base": 0.3, "ramp_m": 4, "form": "ridge"}}, "x", {"ramp": 40, "form": "hills"})
    assert p == {"ramp": 4.0, "form": "ridge", "base": 0.3}
    assert tf.overrides({}, "y", {"ramp": 40})["base"] == 1.0


def test_spec_names_real_characters_and_cites_research():
    spec = tf.load()
    for rid, s in spec.items():
        assert s["character"] in tf.CHARACTERS, rid
        assert s["reads"].split(":")[0].endswith(".json"), rid


def test_beyond_carries_the_edge_out():
    """West edge land runs on west, south edge sea runs on south; the picture's inside is unchanged."""
    n = 400
    water = np.zeros((n, n), bool)
    water[240:, :] = True                       # sea in the south half
    foreign = np.zeros((n, n), bool)
    foreign[:120, :] = True
    ext, fext, pad = tb.extend(water, foreign, pad=80)
    inner = slice(pad + tb.INSET_PX, pad + n - tb.INSET_PX)
    assert (ext[inner, inner] == water[tb.INSET_PX:n - tb.INSET_PX, tb.INSET_PX:n - tb.INSET_PX]).all()
    assert not ext[pad + 150, 5]                # far west, in the land's rows: land
    assert ext[pad + 330, 5]                    # far west, in the sea's rows: sea
    assert ext[-3, pad + 200]                   # far south: sea
    assert fext[pad + 150, 5]                    # land past the map is foreign land
    corr = tb.corrected(ext, pad, water.shape)
    assert corr.shape == water.shape


def test_held_ground_identical_inside(tmp_path, monkeypatch):
    rec = {"terrain_build": "T0", "cells": [[0, -1]]}
    old = np.full((80, 80), 400.0, np.float32)
    p = {"h": old, "x0": -32 * 128.0, "y0": 32 * 128.0}
    monkeypatch.setattr(th, "MARGIN_M", 10.0)
    monkeypatch.setattr(th, "BLEND_M", 30.0)
    monkeypatch.setattr(th, "rows", lambda: {"p": rec})
    monkeypatch.setattr(th, "patch", lambda pid, r: p)
    grid = ts.Grid(rows=120, cols=120, p0x=0.0, p0y=0.0, ox=-40 * 128.0, oy=40 * 128.0)
    h = np.full((120, 120), 1000.0, np.float32)
    ws = np.zeros(h.shape, bool)
    th.apply(h, grid, ws)
    res = th.check(h, grid)
    assert res["p"]["max_diff_units"] == 0.0 and th.ok(res)
    w = th.weight(rec, p)
    ring = (w > 0) & (w < 1)
    assert ring.any()
    sub = h[8:88, 8:88]
    assert np.all(np.mod(sub[ring], 8.0) == 0)               # the blend is on LAND's step
    assert sub[ring].min() >= 400 and sub[ring].max() <= 1000


def test_held_rows_need_every_built_place(tmp_path, monkeypatch):
    (tmp_path / "places" / "newplace").mkdir(parents=True)
    monkeypatch.setattr(th, "PLACES", tmp_path / "places")
    monkeypatch.setattr(th, "HELD", tmp_path / "held.json")
    (tmp_path / "held.json").write_text(json.dumps({"places": {}}))
    with pytest.raises(SystemExit):
        th.rows()


def test_scope_reaches_past_the_picture():
    from tools.newworld import tiles
    xs, ys = f.cell_range()
    b = tiles.beyond_cells()
    assert (xs.start - tiles.BEYOND_CELLS, ys.start) in b and (xs.stop - 1, ys.stop - 1) not in b
    assert len(b) == (len(xs) + 2 * tiles.BEYOND_CELLS) * (len(ys) + 2 * tiles.BEYOND_CELLS) - len(xs) * len(ys)


def _ground(kind, amp=1.0, n=420):
    """Synthetic ground of one landform at one amplitude (metres), on a 2 m base."""
    c = _crop(n=n)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32) * (128 / 70)
    if kind == "mounds":
        add = tf._blobs(c, 90, 0.7, 5, 20, 30, 2.0, 3.0)
    elif kind == "kettles":
        add = -tf._blobs(c, 90, 0.7, 5, 20, 30, 2.0, 3.0)
    elif kind == "ridges":
        add = 2.5 * np.maximum(np.cos(2 * np.pi * xx / 90), 0) ** 3
    else:                                   # benches: flats between a few steep risers
        add = 2.5 * np.floor(xx / 180) + 0 * yy
    return (6.0 + amp * add).astype(np.float32)


def test_character_measure_reads_landform_not_only_amplitude():
    """Two landforms of one amplitude lie further apart than one landform at two amplitudes; a flat sheet and
    hummocky ground are far apart."""
    m = np.zeros((420, 420), bool)
    m[40:-40, 40:-40] = True
    rows = {k: tch.measure(_ground(k), m) for k in ("mounds", "kettles", "ridges", "benches")}
    rows["mounds x1.5"] = tch.measure(_ground("mounds", 1.5), m)
    d = tch.distances(rows, tch.scale_of({}))
    same = d["mounds"]["mounds x1.5"]
    for other in ("kettles", "ridges", "benches"):
        assert d["mounds"][other] > 1.5 * same, (other, d["mounds"][other], same)
    assert rows["mounds"]["skew"] > 0.5 > -0.5 > rows["kettles"]["skew"]
    assert rows["ridges"]["line"] > rows["mounds"]["line"] + 0.2
    assert rows["ridges"]["grain"] > rows["mounds"]["grain"] + 0.3
    assert rows["benches"]["flat"] > rows["mounds"]["flat"]
    rng = np.random.default_rng(1)
    flat = np.full((420, 420), 2.0, np.float32) + 0.01 * rng.standard_normal((420, 420)).astype(np.float32)
    hum = flat + tf.root_hummocks(_crop(n=420), "after")
    a, b = tch.measure(flat, m), tch.measure(hum, m)
    assert b["flat"] < a["flat"] and b["fine"] > a["fine"]
    assert tch.distances({"a": a, "b": b}, tch.scale_of({}))["a"]["b"] > 1.0
    assert tch.measure(flat, np.zeros_like(m)) is None                 # too little ground is no measure


def test_character_judge_fails_on_alike_neighbours():
    c = {"neighbour_pairs": {"a|b": 1.0, "a|c": 4.0}, "nearest": {"a": 1.0, "b": 1.0, "c": 4.0},
         "skyrim_min_neighbour": 1.6, "skyrim_mean_neighbour": 2.9, "skyrim_nearest": {"x": 0.9}, "mean_neighbour": 2.5}
    j = tch.judge(c)
    assert not j["ok"] and list(j["neighbours_too_alike"]) == ["a|b"]
    c["neighbour_pairs"] = {"a|b": 2.0, "a|c": 4.0}
    c["mean_neighbour"] = 3.0
    assert tch.judge(c)["ok"]


def test_noise_is_anchored_to_the_base_window():
    """A grid wider than its base window lays the window's noise where the window alone would."""
    from tools.newworld import terrain_relief as tr
    base, wide = (200, 260), (328, 388)
    alone = tr.noise(base, 40.0, 11)
    tr.anchor(wide, 64, 64, base)
    try:
        z = tr.noise(wide, 40.0, 11)
    finally:
        tr.unanchor(wide)
    inner = z[64:264, 64:324]
    assert np.abs(inner - alone).max() < 1e-3
    assert z[:40].std() > 0.3 and z[:, -40:].std() > 0.3               # and real noise beyond it
    assert not np.allclose(tr.noise(wide, 40.0, 11)[64:264, 64:324], alone, atol=1e-3)     # unregistered: its own


def test_rounding_pattern_and_droplets_are_anchored():
    from tools.newworld import terrain_droplets as td
    from tools.newworld import terrain_relief as tr
    base = np.linspace(0, 300, 96 * 128, dtype=np.float32).reshape(96, 128)      # gently leaning ground
    wide = np.pad(base, 64, mode="edge")
    alone = ts.quantise(base)
    tr.anchor(wide.shape, 64, 64, base.shape)
    try:
        q = ts.quantise(wide)
    finally:
        tr.unanchor(wide.shape)
    assert (q[64 + 4:64 + 92, 64 + 4:64 + 124] == alone[4:92, 4:124]).mean() > 0.99
    cand = np.ones((96, 128), bool)
    a = td.starts_of(cand, 0.5, 5)
    big = np.ones((224, 256), bool)
    b = td.starts_of(big, 0.5, 5, origin=(64, 64))
    inb = (b[:, 0] >= 64) & (b[:, 0] < 128) & (b[:, 1] >= 64) & (b[:, 1] < 192)   # the base's first row of blocks
    ina = a[:, 0] < 64
    assert np.allclose(np.sort(b[inb] - 64, axis=0), np.sort(a[ina], axis=0))
    cand2 = cand.copy()
    cand2[70:, 70:] = False                                             # a change in one block
    c = td.starts_of(cand2, 0.5, 5)
    assert np.allclose(c[(c[:, 0] < 64) & (c[:, 1] < 64)], a[(a[:, 0] < 64) & (a[:, 1] < 64)])   # moves no other


def test_cell_land_share_off_the_picture():
    water = np.zeros((400, 400), bool)
    water[240:, :] = True
    ext, pad = tb.extend_water(water, pad=80)
    assert tb.cell_land_share(ext, pad, (-60, 100, -20, 140)) == 1.0     # west of the picture, in the land's rows
    assert tb.cell_land_share(ext, pad, (-60, 320, -20, 360)) == 0.0     # west of it, in the sea's rows
    with pytest.raises(SystemExit):
        tb.cell_land_share(ext, pad, (-200, 100, -160, 140))             # past the carried map: loud


def test_grid_past_the_carried_map_stops_the_build():
    g = ts.Grid(rows=10, cols=10, p0x=-5.0, p0y=3.0)
    with pytest.raises(SystemExit):
        tb.covers(g, (100, 100))
    tb.covers(ts.Grid(rows=10, cols=10, p0x=5.0, p0y=3.0), (100, 100))


def test_held_patch_is_keyed_by_its_box_and_checks_the_source(tmp_path, monkeypatch):
    import hashlib
    src = tmp_path / "src"
    src.mkdir()
    h = np.arange(200 * 200, dtype=np.float32).reshape(200, 200)
    np.save(src / "heightmap.npy", h)
    sha = hashlib.sha256((src / "heightmap.npy").read_bytes()).hexdigest()
    b = {"id": "T0", "origin_world_x": -100 * 128.0, "origin_world_y": 100 * 128.0, "sha256": sha}
    (src / "build.json").write_text(json.dumps(b))
    monkeypatch.setattr(th, "STORE", tmp_path / "store")
    monkeypatch.setattr(th, "MARGIN_M", 10.0)
    monkeypatch.setattr(th, "BLEND_M", 10.0)
    monkeypatch.setattr(th, "_source", lambda stamp: (src / "heightmap.npy", src / "build.json", None))
    one = th.patch("p", {"terrain_build": "T0", "cells": [[0, -1]]})
    two = th.patch("p", {"terrain_build": "T0", "cells": [[0, -1], [1, -1]]})       # the row grew: a new patch
    assert two["h"].shape[1] > one["h"].shape[1]
    assert len(list((tmp_path / "store").glob("p.T0.*.npz"))) == 2
    (src / "build.json").write_text(json.dumps(b | {"sha256": "0" * 64}))            # a wrong or broken source
    with pytest.raises(SystemExit):
        th.patch("p", {"terrain_build": "T0", "cells": [[2, -1]]})


def test_clearance_keeps_the_waterline_and_clears_the_plane():
    from tools.newworld import terrain_clearance as tcl
    n = 120
    sd = np.tile(np.linspace(-30, 30, n, dtype=np.float32), (n, 1))      # water west, land east
    ws = sd < 0
    h = np.where(ws, -10.0, 10.0).astype(np.float32)                       # hugging the plane both sides
    tcl.apply(h, sd, ws)
    assert ((h > 0) == ~ws).all()                                          # the waterline did not move
    far = np.abs(sd) > max(tcl.LAND_REACH_M, tcl.BED_REACH_M)
    assert (np.abs(h[far]) > 64).all()
    assert tcl.shares(h)["full"]["pm64"] < 0.3


def test_held_zone_lifts_land_by_one_constant(monkeypatch):
    rec = {"terrain_build": "T0", "cells": [[0, -1]]}
    old = np.full((80, 80), 16.0, np.float32)                              # land hugging the plane
    old[:, :20] = -16.0                                                    # water on the west
    p = {"h": old, "x0": -32 * 128.0, "y0": 32 * 128.0}
    monkeypatch.setattr(th, "MARGIN_M", 40.0)
    monkeypatch.setattr(th, "BLEND_M", 20.0)
    monkeypatch.setattr(th, "rows", lambda: {"p": rec})
    monkeypatch.setattr(th, "patch", lambda pid, r: p)
    L = th.lift(rec, p)
    assert L > 0 and L % 8 == 0 and 16 + L >= 77
    grid = ts.Grid(rows=120, cols=120, p0x=0.0, p0y=0.0, ox=-40 * 128.0, oy=40 * 128.0)
    h = np.full((120, 120), 200.0, np.float32)
    h[:, :28] = -80.0
    th.apply(h, grid, h < 0)
    res = th.check(h, grid)
    assert th.ok(res) and res["p"]["lift_units"] == L


def test_build_inputs_are_digested(tmp_path, monkeypatch):
    """build.json names its inputs by digest; a changed or missing input shows."""
    from tools.newworld import terrain as T
    for name in ("scope_cells.json", "cell_region.json", "region_relief.json", "terrain_held.json"):
        (tmp_path / name).write_text("{}")
    monkeypatch.setattr(f, "OUT", tmp_path)
    monkeypatch.setattr(tf, "SPEC", tmp_path / "region_relief.json")
    monkeypatch.setattr(th, "HELD", tmp_path / "terrain_held.json")
    from tools.newworld import water_held as wh
    monkeypatch.setattr(wh, "OVERRIDES", tmp_path / "water_overrides.json")
    monkeypatch.setattr(wh, "PNG", tmp_path / "water_owner_bodies.png")
    (tmp_path / "water_overrides.json").write_text("{}")
    a = T.input_digests()
    assert set(a) == {"scope_cells.json", "cell_region.json", "region_relief.json", "terrain_held.json",
                      "water_overrides.json", "water_owner_bodies.png"}
    assert a["water_owner_bodies.png"] is None          # the owner's water: an edit taken in shows in the check
    (tmp_path / "water_overrides.json").write_text('{"wb-1-2": {}}')
    assert T.input_digests()["water_overrides.json"] != a["water_overrides.json"]
    (tmp_path / "region_relief.json").write_text('{"regions": {}}')
    b = T.input_digests()
    assert b["region_relief.json"] != a["region_relief.json"] and b["scope_cells.json"] == a["scope_cells.json"]
    (tmp_path / "terrain_held.json").unlink()
    assert T.input_digests()["terrain_held.json"] is None
