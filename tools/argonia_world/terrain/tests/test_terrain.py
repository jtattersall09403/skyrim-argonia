"""L1 on a synthetic 4x4-cell province with a 1-cell apron: VHGT round trip, the limiter, seams, layers."""
import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import build, paint, quantize
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
    base, layers = paint.quadrant_layers(w)
    got = paint.composite(base, layers, 4)
    assert np.abs(got - w / w.sum(axis=2, keepdims=True)).max() < 0.02


def test_seed_covers_every_class_once():
    assert len({c.id for c in SEED}) == len(SEED) == 37
