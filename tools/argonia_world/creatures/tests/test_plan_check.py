"""plan-check (lane 1.15-r6-creatures): the kinds the plan puts round a stand, counted as the engine draws them."""
from tools.argonia_world.creatures import plan_check as pc


def _sp(x, base, cls="c"):
    return {"kind": "spawn", "x": x, "y": 0.0, "base": base, "class": cls}


def test_one_list_of_four_drawn_many_times_expects_near_four():
    ent = {"L": ["a", "b", "c", "d"]}
    k = pc.kinds_near([_sp(i * 10.0, "L") for i in range(30)], ent, "c", {"a", "b", "c", "d"}, 0, 0)
    assert k["possible"] == 4 and k["spawns"] == 30 and k["own_spawns"] == 30
    assert 3.9 < k["expected"] <= 4 and k["p_ge"] > 0.9


def test_other_class_kinds_and_far_refs_do_not_count():
    ent = {"L": ["a", "x"], "M": ["y"]}
    refs = [_sp(0, "L"), _sp(0, "M", "other"), _sp(pc.RADIUS_U + 1, "L")]
    k = pc.kinds_near(refs, ent, "c", {"a", "b"}, 0, 0)
    assert k["spawns"] == 2 and k["own_spawns"] == 1 and k["possible"] == 1 and k["expected"] == 0.5 and k["p_ge"] == 0


def test_stops_reads_the_generated_stand_and_subject():
    t = ("- name: coastal-lagoon\n  # cell\n  # subject: 1 2 3\n  do:\n  - console: x\n"
         "  - console: player.setpos x 10\n  - console: player.setpos y -20\n")
    assert pc.stops(t) == [{"name": "coastal-lagoon", "subj": (1.0, 2.0, 3.0), "x": 10.0, "y": -20.0}]
