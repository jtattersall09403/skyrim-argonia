import numpy as np

from tools.argonia_world.terrain.cellwater import Step
from tools.argonia_world.water.edges_census import Q, census


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
