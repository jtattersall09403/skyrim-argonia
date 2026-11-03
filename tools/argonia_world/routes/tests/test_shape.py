"""routes/shape.py: a road laid into synthetic ground meets Skyrim.esm's measured profile (L2)."""
import numpy as np

from tools.argonia_world.routes import shape as S


def _ground(n=200, rise=0.0, bumps=0.0):
    y, x = np.mgrid[0:n + 1, 0:n + 1].astype(np.float64)
    return x * rise * S.MPP + bumps * np.sin(x / 3.0) * np.cos(y / 5.0)


def _road(n=200):
    return [(np.array([[10.0, n / 2], [n - 10.0, n / 2]]), 4.5 / S.MPP)]  # a 5 m road with 2 m shoulders


def test_flat_marsh_takes_the_trough():
    h = _ground(bumps=0.6)
    S.shape(h, _road())
    r = S.profile(h, _road())
    for o, (lo, hi) in S.TROUGH_BAND.items():
        assert lo <= r[f"fold_{o:.0f}m_median"] <= hi, r


def test_steep_road_held_to_the_grade():
    h = _ground(rise=0.15, bumps=3.0)  # a 15 % slope along the road, bumpy past the vanilla max
    before = S.profile(h, _road())
    S.shape(h, _road())
    after = S.profile(h, _road())
    assert before["steeper_than_max"] > 0
    assert after["steeper_than_max"] < before["steeper_than_max"] / 2, (before, after)


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


def test_the_fade_follows_the_bank():
    """A road running along a stream: no wall at the edge on the water's side (the untouched bed beside it)."""
    h = _ground(bumps=0.6)
    water = np.zeros(h.shape, bool)
    water[100 + 4:100 + 7, :] = True  # a stream just past the road's left edge
    h[water] -= 1.0
    roads = _road()
    S.shape(h, roads, water)
    c = S.census(h, None, None, None, water, roads, None)
    assert c["walls"]["other"] == 0, c["walls"]


def test_census_lists_walls_by_water_as_crossings():
    h = _ground()
    water = np.zeros(h.shape, bool)
    water[103:107, :] = True  # a channel beside the road, its bank at the road's edge
    h[water] -= 2.0  # a wall the road did not make: the bank
    c = S.census(h, None, None, None, water, _road(), None)
    assert c["walls"]["crossing"] > 0 and c["walls"]["other"] == 0, c["walls"]
