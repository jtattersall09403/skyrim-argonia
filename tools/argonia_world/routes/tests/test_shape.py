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
