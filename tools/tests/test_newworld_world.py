"""The new world's LAND shards: quantise, limit, encode round trip, seams, grid maths."""
import json

import numpy as np

from tools.newworld.world import land
from tools.newworld.world import quantize
from tools.newworld.world import units as su


def test_limit_removes_overflow_and_encode_round_trips():
    rng = np.random.default_rng(1)
    steps = rng.integers(-50, 50, (65, 65)).astype(np.int64)
    steps[:, 33:] += 1000  # a cliff no signed byte can hold
    assert quantize.overflow_pairs(steps) > 0
    lim = quantize.limit(steps)
    assert quantize.overflow_pairs(lim) == 0
    cell = lim[:33, :33][::-1]
    off, d = quantize.encode(cell)
    assert np.array_equal(quantize.decode(off, d), cell)


def test_grid_and_rows(tmp_path):
    b = {"id": "t", "width": 65, "height": 33, "origin_world_x": -8192.0, "origin_world_y": 4096.0,
         "water_level_units": 0.0, "sample_units": 128.0}
    (tmp_path / "build.json").write_text(json.dumps(b))
    g = su.load_grid(tmp_path / "build.json")
    assert (g.cells_x, g.cells_y, g.cx0, g.cy_top, g.cy_bottom) == (2, 1, -2, 0, 0)
    h = np.arange(33 * 65, dtype=np.float32).reshape(33, 65) % 7 * 8
    lim = np.rint(h / 8).astype(np.int32)
    data = land.row_bytes(g, lim, land.normals(lim), 0)
    assert len(data) == 2 * land.CELL_BYTES
    dec = []
    for i in range(2):
        o = i * land.CELL_BYTES
        off = np.frombuffer(data[o:o + 4], np.float32)[0]
        d = np.frombuffer(data[o + 4:o + 4 + 1089], np.int8).reshape(33, 33)
        dec.append(quantize.decode(off, d))
    assert np.array_equal(dec[0][:, 32], dec[1][:, 0])  # the shared edge: no seam
    assert np.array_equal(dec[0][::-1], lim[:, :33])
