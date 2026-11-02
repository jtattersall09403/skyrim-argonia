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


def _step_grid():
    """A synthetic two-cell step: water at 10 m on the left half, 4 m on the right, one channel row of vertices
    through the shared column (bed 9.8 m at the edge, as generate.py's join holds it), a cave mouth sited on it."""
    n = 160
    h = np.full((n, n), 12.0)
    lo = np.full(h.shape, -np.inf)
    hi = np.full(h.shape, np.inf)
    vmin = np.full(h.shape, np.nan)
    vmax = np.full(h.shape, np.nan)
    role = np.zeros(h.shape, np.int8)
    vmin[:, :80], vmax[:, :80] = 10.0, 10.0
    vmin[:, 80:], vmax[:, 80:] = 4.0, 4.0
    chan = np.zeros(h.shape, bool)
    chan[78:83, 76:84] = True  # the graded channel across the edge
    h[chan] = 9.8
    hi[chan] = 9.81
    role[chan] = 1
    foot = role == 1
    inp = type("I", (), {"sites": [{"place_id": "place.test.mouth", "x_m": 80 * G.MPP, "y_m": 80 * G.MPP, "radius_m": 3 * G.MPP,
                                    "entrance": "cave-mouth", "water_m": 1.0, "request": None}]})()
    return h, lo, hi, role, inp, vmin, vmax, foot, chan


def test_site_over_a_step_keeps_its_channel():
    """The pass that lost 8 of 203 steps (shape_sites: a mouth's disc reserved as ground above the water sharing it)
    leaves a step's channel at its bed."""
    h, lo, hi, role, inp, vmin, vmax, foot, chan = _step_grid()
    G.shape_sites(h, lo, hi, role, inp, vmin, vmax, foot, np.zeros(h.shape, bool), None, chan)
    assert (h[chan] <= 9.81 + 1e-9).all() and (hi[chan] <= 9.81 + 1e-9).all()
    # without the channel mask the same site buries it (the bug this guards)
    h, lo, hi, role, inp, vmin, vmax, foot, chan = _step_grid()
    G.shape_sites(h, lo, hi, role, inp, vmin, vmax, foot, np.zeros(h.shape, bool))
    assert (h[chan] > 9.81).any()
