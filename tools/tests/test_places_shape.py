"""shape.py against known answers: the tiny meshes of fixtures/truth_meshes.json (boxes and rings, no game asset),
each read in a known pose, with the numbers the mesh gives and the box would get wrong."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from tools.places import shape, xform

FIX = json.loads((Path(__file__).parent / "fixtures" / "truth_meshes.json").read_text())
C = FIX["cases"]
TOL = 2.0


class Flat:
    def __init__(self, h=0.0):
        self.h = h

    def height(self, x, y):
        return self.h

    def water(self, x, y):
        return None


@pytest.fixture(autouse=True, scope="module")
def meshes():
    for name, m in FIX["meshes"].items():
        shape.register(name, m["v"], m["t"])
    shape._POSED.clear()


def piece(pid, model, pos, rot=(0, 0, 0), scale=1.0):
    return {"id": pid, "model": model, "m": xform.matrix(list(pos), list(rot), scale)}


def posed(*a, **k):
    return shape.Posed(piece(*a, **k))


def test_an_l_deck_on_inset_posts_has_three_feet_and_an_l_shaped_plan():
    c = C["ldeck"]
    s = posed("d", c["model"], (1000, 1000, 300))
    feet = [f for f in s.feet() if f["z"] <= 300 + c["feet_z"] + TOL]
    assert len(feet) == c["feet"] and all(abs(f["z"] - (300 + c["feet_z"])) <= TOL for f in feet)
    box_cells = (400 / 16 + 1) ** 2
    assert s.occ.sum() < 0.6 * box_cells            # the L, not the square its box draws
    assert (~np.isnan(s.walk)).sum() >= c["walk_cells_min"]
    assert abs(s.low() - (300 + c["low"])) <= TOL


def test_the_deck_turned_keeps_its_feet():
    s = posed("d", C["ldeck"]["model"], (0, 0, 0), rot=(0, 0, 1.0))
    assert len([f for f in s.feet() if f["z"] <= -258]) == 3


def test_a_house_on_legs_gives_its_eaves_floor_and_four_feet():
    c = C["legshouse"]
    s = posed("h", c["model"], (0, 0, 500))
    b = s.body()
    assert abs(b["eaves"] - (500 + c["eaves"])) <= TOL
    assert abs(b["floor"] - (500 + c["floor"])) <= TOL
    feet = [f for f in s.feet() if f["z"] <= 500 + c["feet_z"] + TOL]
    assert len(feet) == c["feet"]


def test_a_leaning_tree_has_its_collar_above_its_root_tips_and_its_lean():
    c = C["leantree"]
    t = posed("t", c["model"], (0, 0, 100)).tree()
    assert abs(t["low"] - (100 + c["low"])) <= TOL
    assert abs(t["collar"] - (100 + c["collar"])) <= c["collar_tol"]
    assert abs(t["lean"] - c["lean"]) <= c["lean_tol"]


def test_an_egg_under_the_cliffs_overhang_or_beside_it_is_clear_one_inside_is_not():
    c = C["cliff_egg"]
    cliff = posed("c", c["cliff"], (0, 0, 0))
    for k, inside in (("egg_under_overhang", False), ("egg_beside", False), ("egg_inside", True)):
        egg = posed(k, "fx/egg.nif", c[k])
        assert (shape.overlap(cliff, egg) is not None) == inside, k


def test_a_root_under_a_deck_between_its_posts_does_not_overlap_it():
    deck = posed("d", C["ldeck"]["model"], (0, 0, 0))
    root = posed("r", "fx/root.nif", (200, 200, -60))
    assert not shape.boxes_apart(deck, root)             # the boxes cross: the box alone would flag it
    assert shape.overlap(deck, root) is None
    assert shape.overlap(deck, posed("r2", "fx/root.nif", (200, 50, -10))) is not None


def test_a_house_inside_a_house_overlaps():
    a = posed("a", C["legshouse"]["model"], (0, 0, 0))
    b = posed("b", C["legshouse"]["model"], (20, 0, 0))
    assert shape.overlap(a, b) is not None


def test_a_stair_resting_and_one_40_in_the_air():
    c = C["stairs"]
    g = Flat(0.0)
    ok = posed("s1", c["model"], (0, 0, 0))
    foot, head = ok.ends()
    assert abs(foot["at"][2] - c["foot_z"]) <= TOL and abs(head["at"][2] - c["head_z"]) <= TOL
    r = shape.end_meets(foot, [], g)
    assert r["verdict"] == "rests on ground" and abs(r["over_ground"]) <= TOL
    up = posed("s2", c["model"], (0, 0, c["midair"]))
    r = shape.end_meets(up.ends()[0], [], g)
    assert r["verdict"].startswith("mid-air") and abs(r["over_ground"] - c["midair"]) <= TOL


def test_a_bridge_meets_one_deck_and_falls_30_short_of_the_other():
    c = C["bridge"]
    g = Flat(-1000.0)
    plank = posed("p", c["plank"], (0, 0, 90))                 # deck top 100, from x 0 to 400
    a = posed("A", c["slab"], (-100, 0, 100))                  # its edge at x 0: meets
    b = posed("B", c["slab"], (400 + c["short"] + 100, 0, 100))  # its edge 30 past the plank's end
    rows = shape.joints([("p", plank)], [("p", plank), ("A", a), ("B", b)], g)
    ends = {r["meets"]: r for r in rows if r["end"] != "-"}
    assert ends["A"]["verdict"] == "meets A" and abs(ends["A"]["along"]) <= TOL
    assert ends["B"]["verdict"].startswith("short of B") and abs(ends["B"]["along"] - c["short"]) <= TOL


def test_a_house_standing_on_a_boardwalk_is_named():
    bw = posed("bw", "fx/boardwalk.nif", (0, 0, 0))
    hut = posed("hut", "fx/hut.nif", (300, 0, 0))
    rows = shape.joints([("bw", bw)], [("bw", bw), ("hut", hut)], Flat(-500), unit_of={"bw": "walk", "hut": "house"})
    assert any(r["verdict"] == "stands on: hut" for r in rows)
    assert shape.rests_on(hut, bw)


def test_a_tilted_plank_and_an_upside_down_one_read_their_real_lowest_point():
    t = posed("t", "fx/plank.nif", (0, 0, 100), rot=(0.0, math.radians(30), 0.0))
    P = shape.box_tris([0, -40, 0], [400, 40, 10]).reshape(-1, 3)
    M = np.asarray(t.M)
    W = P @ M[:3, :3].T + M[:3, 3]                              # the turned corners: not the untilted box's
    assert t.tilted and abs(t.low() - W[:, 2].min()) <= TOL and abs(t.top_z() - W[:, 2].max()) <= TOL
    assert abs(abs(W[:, 2] - 100).max() - (400 * 0.5 + 10 * math.cos(math.radians(30)))) <= TOL
    u = posed("u", "fx/hut.nif", (0, 0, 300), rot=(math.pi, 0, 0))
    assert abs(u.low() - 100) <= TOL and abs(u.top_z() - 300) <= TOL


def test_ground_clearance_under_the_mesh_footprint_not_the_box():
    s = posed("d", C["ldeck"]["model"], (0, 0, 300))

    class Slope(Flat):
        def height(self, x, y):
            return 0.1 * x
    c = s.clearance(Slope())
    # the post at x 350 (to 360) is the lowest foot over the highest ground: 40 - 36
    assert abs(c["over"] - (300 - 260 - 36)) <= TOL


def test_a_model_that_cannot_be_read_is_named_and_measured_by_its_box():
    p = {"id": "x", "model": "fx/nosuch.nif", "m": xform.matrix([0, 0, 0], [0, 0, 0], 1), "lo": [-10, -10, 0], "hi": [10, 10, 30]}
    s = shape.Posed(p)
    assert not s.mesh and abs(s.top_z() - 30) <= TOL and "fx/nosuch.nif" in shape.unread()
