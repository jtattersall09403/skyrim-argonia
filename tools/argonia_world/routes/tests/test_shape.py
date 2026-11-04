"""routes/shape.py: a road laid into synthetic ground meets Skyrim.esm's measured profile (L2)."""
import numpy as np

from tools.argonia_world.routes import shape as S


def _ground(n=200, rise=0.0, bumps=0.0):
    y, x = np.mgrid[0:n + 1, 0:n + 1].astype(np.float64)
    return x * rise * S.MPP + bumps * np.sin(x / 3.0) * np.cos(y / 5.0)


def _road(n=200):
    return [(np.array([[10.0, n / 2], [n - 10.0, n / 2]]), 4.5 / S.MPP)]  # a 5 m road with 2 m shoulders


def test_grade_limit_is_lipschitz():
    z = np.array([0, 5, 0, 10, 10, 2, 30], float)
    g = S.grade_limit(z, 1.0, 0.2)
    assert np.abs(np.diff(g)).max() <= 0.2 + 1e-9


def test_grade_within_never_cuts_past_the_cap():
    z = np.concatenate([np.zeros(20), np.linspace(0, 6, 10), np.full(20, 6.0)])  # a 6 m bank in 10 samples
    g = S.grade_within(z.copy(), z, 1.0, 0.2)
    assert np.abs(g - z).max() <= S.MAX_CUT_M + 1e-9
    gentle = np.linspace(0, 3, 50)
    assert np.abs(np.diff(S.grade_within(gentle + 0.3 * np.sin(np.arange(50)), gentle, 1.0, 0.2))).max() <= 0.2 + 1e-9


def _flooded(n=120, level=2.0, bed=-3.0):
    """A 5 m deep lake over the whole window, one level, a road across it."""
    h = np.full((n + 1, n + 1), bed)
    lo, hi = np.full(h.shape, -np.inf), np.full(h.shape, level - 0.3)
    role = np.ones(h.shape, np.uint8)
    vl = np.full(h.shape, level)
    return h, lo, hi, role, vl


def test_reach_crossing_is_a_ford():
    n = 120
    h, lo, hi, role, vl = _flooded(n)
    road = _road(n)
    reach = np.zeros(h.shape, bool)
    reach[:, 55:66] = True  # a stream across the road
    dc = S.dry_corridor(road, lo, hi, role, vl, vl, reach)
    assert dc["ford"].any()
    h = np.minimum(np.maximum(h, lo), hi)
    d = 2.0 - h[n // 2, 56:65]
    assert (d > 0).all() and d.max() <= S.FORD_M + 1e-6, d


def test_step_channel_under_a_road_is_capped_at_the_ford_depth():
    n = 120
    h, lo, hi, role, vl = _flooded(n)
    road = _road(n)
    chan = np.zeros(h.shape, bool)
    chan[:, 58:61] = True  # a step's channel across the road, its bed 2 m under the level
    hi[chan] = 0.0
    h[chan] = 0.0
    dc = S.dry_corridor(road, lo, hi, role, vl, vl, np.zeros(h.shape, bool), keep=chan)
    h = np.minimum(np.maximum(h, lo), hi)
    d = 2.0 - h[n // 2, 58:61]
    assert np.allclose(d, S.FORD_M), d
    assert h[5, 59] == 0.0  # off the corridor the channel keeps its bed
    assert dc["ford"][n // 2, 59]
