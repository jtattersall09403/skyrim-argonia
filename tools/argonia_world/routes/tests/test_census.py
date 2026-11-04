"""routes/census.py: the measures of a shaped road on synthetic ground (L2)."""
import numpy as np

from tools.argonia_world.routes import census as C
from tools.argonia_world.routes import shape as S
from tools.argonia_world.routes.tests.test_shape import _flooded, _ground, _road


def test_flat_marsh_takes_the_trough():
    h = _ground(bumps=0.6)
    S.shape(h, _road())
    r = C.profile(h, _road())
    for o, (lo, hi) in C.TROUGH_BAND.items():
        assert lo <= r[f"fold_{o:.0f}m_median"] <= hi, r


def test_steep_road_held_to_the_grade():
    h = _ground(rise=0.15, bumps=3.0)  # a 15 % slope along the road, bumpy past the vanilla max
    before = C.profile(h, _road())
    S.shape(h, _road())
    after = C.profile(h, _road())
    assert before["steeper_than_max"] > 0
    assert after["steeper_than_max"] < before["steeper_than_max"] / 2, (before, after)


def test_the_fade_follows_the_bank():
    """A road running along a stream: no wall at the edge on the water's side (the untouched bed beside it)."""
    h = _ground(bumps=0.6)
    water = np.zeros(h.shape, bool)
    water[100 + 4:100 + 7, :] = True  # a stream just past the road's left edge
    h[water] -= 1.0
    roads = _road()
    S.shape(h, roads, water)
    c = C.census(h, None, None, None, water, roads, None)
    assert c["walls"]["other"] == 0, c["walls"]


def test_census_lists_walls_by_water_as_crossings():
    h = _ground()
    water = np.zeros(h.shape, bool)
    water[103:107, :] = True  # a channel beside the road, its bank at the road's edge
    h[water] -= 2.0  # a wall the road did not make: the bank
    c = C.census(h, None, None, None, water, _road(), None)
    assert c["walls"]["crossing"] > 0 and c["walls"]["other"] == 0, c["walls"]


def test_flooded_footprint_becomes_a_causeway():
    from tools.argonia_world.terrain.generate import limit
    n = 120
    h, lo, hi, role, vl = _flooded(n)
    road = _road(n)
    reach = np.zeros(h.shape, bool)
    dc = S.dry_corridor(road, lo, hi, role, vl, vl, reach)
    assert dc["causeway"].any() and not dc["ford"].any()
    h = np.minimum(np.maximum(h, lo), hi)
    S.shape(h, road, ~dc["bank"] & (role == 1), lo, hi)
    f, _ = limit(np.minimum(np.maximum(h, lo), hi), lo, hi, 6.8)
    c = C.wet_census(f, road, ["r"], vl, reach)["r"]
    assert c["under_m"] == 0 and c["causeway_m"] > 150, c
    # the bank falls at no more than GRADE_MAX from the causeway to the bed (the waterline's freeboard step aside:
    # every shore's, no ground within 0.3 m of its water)
    col = f[:, n // 2]
    g = np.abs(np.diff(col)) / S.MPP
    g[(col[:-1] < 2.0) != (col[1:] < 2.0)] = 0.0
    assert g.max() <= S.GRADE_MAX + 0.02, g.max()
    assert col.min() < 2.0 - 0.3 and col[n // 2] >= 2.0 + S.CAUSEWAY_M - 0.01


def test_a_step_crossing_a_bridge_covers_is_not_a_candidate():
    res = {"r1": {"step_crossings": [{"drop_m": 1.0, "at_m": [100, 100]}, {"drop_m": 1.0, "at_m": [500, 500]}]},
           "r2": {"step_crossings": [{"drop_m": 1.0, "at_m": [100, 100]}]}, "r3": {"step_crossings": []}}
    bridges = [{"id": "bridge.x", "routes": ["r1"], "at_m": [102.0, 99.0, 0.0]}]
    left = C.bridge_candidates(res, bridges)
    assert left == {"r1": [{"drop_m": 1.0, "at_m": [500, 500]}], "r2": [{"drop_m": 1.0, "at_m": [100, 100]}]}
