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
    assert np.allclose(a[50:, 70:], b[:150, :130], atol=1e-5)
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


def test_character_measure_tells_flat_from_hummocky():
    rng = np.random.default_rng(1)
    flat = np.full((300, 300), 2.0, np.float32) + 0.01 * rng.standard_normal((300, 300)).astype(np.float32)
    c = _crop(n=300)
    hum = flat + tf.root_hummocks(c, "after")
    m = np.ones(flat.shape, bool)
    a = tch.summarise(flat, tch.fields(flat), m)
    b = tch.summarise(hum, tch.fields(hum), m)
    assert b["r20"] > 5 * a["r20"] and b["flat"] < a["flat"]
    d = tch.distances({"a": a, "b": b}, tch.scale_of({}))
    assert d["a"]["b"] > 1.0


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
