"""L2: the generator's pieces on small grids: the slope limit inside the bounds, the chamfer, the blur."""
import math

import numpy as np

from tools.argonia_world.terrain import generate as G


def test_limit_holds_slope_and_bounds():
    h = np.zeros((40, 40))
    h[:, 20:] = 50.0  # a 50 m cliff
    lo = np.full(h.shape, -np.inf)
    hi = np.full(h.shape, np.inf)
    hi[:, :5] = -1.0  # a wet strip must stay under -1
    f, moved = G.limit(h, lo, hi, 6.8)
    assert np.abs(np.diff(f, axis=1)).max() <= 6.8 + 1e-9
    assert (f[:, :5] <= -1.0 + 1e-9).all()
    assert moved[:, 19].all()


def test_chamfer_distance_and_value():
    src = np.zeros((9, 9), bool)
    src[4, 4] = True
    d, v = G.chamfer(src, 10, np.where(src, 7.0, np.nan))
    assert d[4, 8] == 4 and math.isclose(d[0, 0], 4 * math.sqrt(2))
    assert (v == 7.0).all()


def test_blur_keeps_constant_and_mean():
    a = np.full((50, 60), 3.0)
    assert np.allclose(G.blur(a, 5), 3.0)
    r = np.random.default_rng(0).standard_normal((64, 64))
    assert G.blur(r, 4).std() < r.std() / 3


def test_relief_rows_cite():
    class W:
        def query(self, q):
            return [{"id": "dunmer-north.rootland", "region_id": "dunmer-north", "eco_class_id": "rootland"}]
    (row,) = G.relief_rows(W())
    assert row["summit_m"] == 96.0 and "shadowfen.md" in row["why"]


def test_reach_keeps_only_joined_low_ground():
    from tools.argonia_world.terrain.generate import reach
    allowed = np.zeros((7, 9), bool)
    allowed[1:4, 1:5] = True      # an L joined to the seed
    allowed[3:6, 3] = True
    allowed[5, 7] = True          # an isolated low patch (a padding cell's hollow)
    seed = np.zeros_like(allowed)
    seed[1, 1] = True
    got = reach(seed, allowed)
    assert got[5, 3] and got[1, 4] and not got[5, 7]
    assert got.sum() == 12 + 2


def test_write_is_atomic_an_interrupted_write_leaves_the_old_file(tmp_path):
    f = tmp_path / "ground-f32.npy"
    np.save(f, np.ones(4, np.float32))

    def dies(fh):
        fh.write(b"half a fie")
        raise KeyboardInterrupt

    try:
        G.atomic(f, dies)
    except KeyboardInterrupt:
        pass
    assert np.load(f).tolist() == [1.0] * 4
    assert [p.name for p in tmp_path.iterdir()] == ["ground-f32.npy"]  # no tmp-<pid> left behind
    G.atomic(f, lambda fh: np.save(fh, np.zeros(4, np.float32)))
    assert np.load(f).tolist() == [0.0] * 4
