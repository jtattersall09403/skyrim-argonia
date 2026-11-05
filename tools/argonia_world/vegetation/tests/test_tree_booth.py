"""The tree-seat stand rule (lane 1.15-r6-tree-look): 6-10 m off the trunk's footprint, nothing over 1 m within 3 m
of the eye line to the base; a class stop with no plant over 1 m within 4 m of the eye."""
import math

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.vegetation import tree_booth as T

U = su.UNITS_PER_METRE


class Flat:
    """Flat dry ground at z 0; foliage as the journeys' Build tuples (x, y, z, radius, height, bushy, z0)."""

    def __init__(self, plants):
        self.plants = plants

    def ground_u(self, x, y):
        return 0.0

    def soaked(self, x, y):
        return False

    def foliage_near(self, x, y, reach_u):
        return [f for f in self.plants if math.hypot(f[0] - x, f[1] - y) <= reach_u + f[3]]


def shrub(x_m, y_m, h_m=2.0, r_m=0.8):
    return (x_m * U, y_m * U, 0.0, r_m * U, h_m * U, True, 0.0)


def tree(x_m, y_m):
    return (x_m * U, y_m * U, 0.0, 6 * U, 20 * U, False, 0.0)


SUBJ = {"x": 0.0, "y": 0.0, "z": 0.0, "seat": 0.0, "scale": 1.0}


def _dist_m(s):
    return math.hypot(s["x"], s["y"]) / U


def test_tree_stand_is_in_the_band_and_south_when_clear():
    s = T.tree_stand(Flat([]), SUBJ)
    assert s["key"] == (0, 0) and 6.0 <= _dist_m(s) <= 10.0
    assert s["y"] < 0 and abs(s["x"]) < 1.0   # south of the trunk, looking north at its base
    assert abs(s["h"]) < 1.0 or abs(s["h"] - 360) < 1.0


def test_a_shrub_on_the_south_line_turns_the_stand():
    s = T.tree_stand(Flat([shrub(0, -4)]), SUBJ)
    assert s["key"] == (0, 0) and 6.0 <= _dist_m(s) <= 10.0
    assert T.aim_hits(Flat([shrub(0, -4)]), (0.0, -8 * U, 120.0), (0.0, 0.0, 0.0)) == 1
    assert s["x"] != 0.0   # another bearing


def test_a_fern_under_a_metre_is_no_hit():
    assert T.aim_hits(Flat([shrub(0, -4, h_m=0.6)]), (0.0, -8 * U, 120.0), (0.0, 0.0, 0.0)) == 0


def test_the_stand_clears_the_trunks_footprint(monkeypatch):
    monkeypatch.setattr(T, "base_radius_u", lambda mod, model, seat: 10 * U)
    s = T.tree_stand(Flat([]), {**SUBJ, "mod": "m", "model": "a.nif"})
    assert 16.0 <= _dist_m(s) <= 20.0 and s["base_m"] == 10.0


def test_class_stand_keeps_the_eye_out_of_a_leaf_curtain():
    ox, oy = su.cell_origin(0, 0)
    plants = [shrub((ox + i * 8 * U) / U + 1.0, (oy + j * 8 * U) / U, h_m=3.0, r_m=1.0) for i in range(8) for j in range(8)
              if (i, j) != (3, 3)]
    plants += [tree((ox + 3 * 8 * U) / U, (oy + 3 * 8 * U) / U + 15.0)]
    s = T.class_stand(Flat(plants), {"cell": (0, 0)})
    assert s["curtain"] == 0 and T.curtain(Flat(plants), (s["x"], s["y"], 120.0)) == 0
    assert s["p"] == 0.0
