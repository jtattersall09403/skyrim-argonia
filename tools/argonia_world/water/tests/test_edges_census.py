import numpy as np

from tools.argonia_world.terrain.cellwater import Step
from tools.argonia_world.water.edges_census import BURIED_MAX, FOOT_FAR_MAX, Q, census, red


def test_dry_neighbour_under_the_level_is_red():
    level = np.array([[10.0, np.nan]])
    g = np.full((Q + 1, 2 * Q + 1), 11.0)
    g[:, Q] = 9.0  # the shared line under the plane
    r = census(level, g, cx0=0, cy0=0)
    assert r["red_lines"] == 1 and r["other_hanging_m"] > 50


def test_bank_at_the_level_is_green():
    level = np.array([[10.0, np.nan]])
    assert census(level, np.full((Q + 1, 2 * Q + 1), 10.3), cx0=0, cy0=0)["red_lines"] == 0


def test_kept_step_channel_is_not_red():
    level = np.array([[10.0, 5.0]])
    g = np.full((Q + 1, 2 * Q + 1), 10.3)
    g[Q - 12:Q - 9, Q] = 7.0  # the channel notch, vertices 10..12 from the south
    r = census(level, g, [Step(0, 0, "e", 10.0, 5.0, 10, 12, "falls")], cx0=0, cy0=0)
    assert r["red_lines"] == 0 and r["step_hanging_m"] > 0


def test_foot_meets_the_lower_water_within_the_bar():
    level = np.array([[10.0, 5.0]])
    g = np.full((Q + 1, 2 * Q + 1), 10.3)
    g[:, Q + 4:] = 4.0  # the lower water from the fourth vertex past the line
    r = census(level, g, [Step(0, 0, "e", 10.0, 5.0, 10, 12, "falls")], cx0=0, cy0=0)
    assert r["foot_p10_50_90"][1] == 4 and r["foot_far"] == 0


def test_one_vertex_pit_is_no_foot():
    level = np.array([[10.0, 5.0]])
    g = np.full((Q + 1, 2 * Q + 1), 10.3)
    g[:, Q + 4] = 4.0  # round 6: a one-vertex pit at the channel's foot, the ground over the lower water past it
    r = census(level, g, [Step(0, 0, "e", 10.0, 5.0, 10, 12, "falls")], cx0=0, cy0=0)
    assert r["foot_far"] == 1 and r["foot_worst"][0]["foot"] == Q + 1


def test_buried_footprint_is_counted():
    level = np.array([[10.0, np.nan]])
    g = np.full((Q + 1, 2 * Q + 1), 12.0)
    foot = np.zeros(g.shape, bool)
    foot[:Q, :Q // 2] = True  # half the cell is raster water
    g[:Q, :Q // 4] = 9.0  # a quarter of it under the level: half its footprint
    r = census(level, g, foot=foot, cx0=0, cy0=0)
    assert r["wet_cells"] == 1 and r["buried_cells"] == 1
    g[:Q, :Q // 2] = 9.0
    assert census(level, g, foot=foot, cx0=0, cy0=0)["buried_cells"] == 0


def test_gate_holds_the_ceilings():
    base = {"red_lines": 0, "foot_far": FOOT_FAR_MAX, "buried_cells": BURIED_MAX}
    assert not red(base)
    assert red({**base, "buried_cells": BURIED_MAX + 1}) and red({**base, "red_lines": 1})
