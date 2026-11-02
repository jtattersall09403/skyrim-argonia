"""L1 on a synthetic 4x4-cell province with a 1-cell apron: VHGT round trip, the limiter, seams, layers."""
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import build, material, quantize
from tools.argonia_world.terrain.grid import Sources
from tools.argonia_world.terrain.landcover import SEED, table


def src():
    n, pad = 4 * 32, 32
    yy, xx = np.mgrid[0:n + 1, 0:n + 1]
    g = (20 * np.sin(xx / 9.0) + 10 * np.cos(yy / 7.0) + 30).astype(np.float32)
    g[:, 70:] += 60.0  # a cliff: 60 m in one sample overflows the signed byte
    ap = np.zeros((n + 1 + 2 * pad,) * 2, np.float32)
    cover = ((xx // 16 + yy // 16) % 5).astype(np.int16) + 16
    return Sources(ground=g, apron=ap, cover=cover, tint=None, pad=pad)


def test_encode_decode_round_trip():
    c = np.cumsum(np.cumsum(np.random.default_rng(1).integers(-60, 60, (33, 33)), axis=1), axis=0) // 33
    off, d = quantize.encode(c)
    assert np.array_equal(quantize.decode(off, d), c)


def test_limit_fits_a_byte_and_keeps_smooth_ground():
    s = np.zeros((10, 10), np.int64); s[:, 5:] = 1000
    lim = quantize.limit(s)
    assert quantize.overflow_pairs(lim) == 0 and np.abs(lim - s).max() <= (1000 - quantize.L) // 2 + 1


def test_build_seams_heights_and_layers(tmp_path):
    s = src()
    st = build.build(s, table(), tmp_path, cells=(-63, -63, -58, -58))
    cells = {(c["x"], c["y"]): c for c in build.read_cells(tmp_path)}
    assert st.province_cells == 16 and st.overflow_pairs > 0
    rec = {k: quantize.decode(c["offset"], build.unpack(c)["vhgt"]) for k, c in cells.items()}
    for (x, y), h in rec.items():
        if (x + 1, y) in rec:
            assert np.array_equal(h[:, -1], rec[(x + 1, y)][:, 0])
        if (x, y + 1) in rec:
            assert np.array_equal(h[-1], rec[(x, y + 1)][0])
    h = rec[(-62, -62)] * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE  # SW province cell: grid rows n-32..n
    truth = s.ground[-33:, :33][::-1]
    assert np.abs(h - truth).max() < 0.06
    assert max(st.layers_hist) <= su.LAND_QUADRANT_LAYERS


def test_layers_composite_to_the_weights():
    w = np.random.default_rng(2).random((17, 17, 4))
    base, layers = material.quadrant_layers(w / w.sum(axis=2, keepdims=True), [0, 1, 2, 3])
    got = material.composite(base, layers, 4)
    assert np.abs(got - w / w.sum(axis=2, keepdims=True)).max() < 0.02


def test_seed_covers_every_class_once():
    assert len({c.id for c in SEED}) == len(SEED) == 37


def test_limit_spreads_a_cliff_locally():
    s = np.zeros((12, 20), np.int64); s[:, 10:] = 1000
    lim = quantize.limit(s)
    assert quantize.overflow_pairs(lim) == 0
    moved = np.abs(lim - s).max(axis=0)
    assert moved[:5].max() == 0 and moved[15:].max() == 0  # 5 samples from the cliff on either side: untouched
    assert np.abs(lim - s).max() <= (1000 - quantize.L) // 2 + 1
    rng = np.random.default_rng(3)  # rough ground with cliffs: never worse than the L-infinity midpoint
    h = np.cumsum(rng.integers(-40, 41, (40, 40)), axis=1) + np.where(rng.random((40, 40)) < 0.05, 600, 0)
    m = (quantize._minorant(h) + quantize._majorant(h)) // 2
    f = quantize.limit(h)
    assert quantize.overflow_pairs(f) == 0 and (np.abs(f - h) <= np.abs(m - h)).all()


def test_the_database_holds_the_seed_classes():
    from tools.argonia_world import db
    assert table(db.open()) == {c.id: c for c in SEED}


def test_game_heights_equal_the_cells(tmp_path):
    s = src()
    build.build(s, table(), tmp_path, cells=(-62, -62, -61, -61))
    c = {(c["x"], c["y"]): c for c in build.read_cells(tmp_path)}[(-61, -62)]
    north, south = s.cell_rows(-62)
    a, b = s.cell_cols(-61)
    g = build.game_heights_m(s, north, south + 1, a, b + 1)[::-1]
    assert np.allclose(g, quantize.decode(c["offset"], build.unpack(c)["vhgt"]) * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE)


def test_build_replaces_land_only_after_writing_its_rows(tmp_path):
    s = src()
    build.build(s, table(), tmp_path, cells=(-63, -63, -58, -58))
    old = sorted(p.name for p in (tmp_path / "land").iterdir())
    try:
        build.build(s, table(), tmp_path, cells=(-63, -63, -58, 99999))  # refused before any row is written
    except ValueError:
        pass
    assert sorted(p.name for p in (tmp_path / "land").iterdir()) == old
    real = build.write_row

    def boom(*a, **k):
        raise RuntimeError("interrupted")
    build.write_row = boom
    try:
        build.build(s, table(), tmp_path, cells=(-63, -63, -58, -58))
    except RuntimeError:
        pass
    finally:
        build.write_row = real
    assert sorted(p.name for p in (tmp_path / "land").iterdir()) == old  # the old land is intact
    assert [p.name for p in tmp_path.iterdir()] == ["land"]  # no temp dir left behind
    build.build(s, table(), tmp_path, cells=(-63, -63, -60, -60))  # a new build swaps in whole
    assert len(list((tmp_path / "land").iterdir())) < len(old)
    assert [p.name for p in tmp_path.iterdir()] == ["land"]


def test_partial_builds_default_to_their_own_dir():
    import argparse

    from tools.argonia_world.terrain import __main__ as M
    ns = lambda **k: argparse.Namespace(**{"out": None, "sample": False, "cells": None, **k})  # noqa: E731
    assert M.default_out(ns()) == M.OUT
    assert M.default_out(ns(sample=True)) == M.SAMPLE_OUT / "sample"
    assert M.default_out(ns(cells="-5,6,7,8")) == M.SAMPLE_OUT / "cells--5,6,7,8"
    assert M.default_out(ns(sample=True, out="x")) == Path("x")
    assert M.OUT not in M.default_out(ns(sample=True)).parents
