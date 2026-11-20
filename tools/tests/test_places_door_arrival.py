"""A load door's arrival: one using the inner door lands where the outer door's own `arrival` stands (the drafting and
the hands keep it on the deck the door opens onto), never at a stale `to_pos` the inner door still holds."""
from tools.places import build


def _pair(arrival):
    out = {"id": "p.out", "fk": "P:000001", "space": "exterior", "pos": [0.0, 0.0, 655.0], "rot": [0.0, 0.0, 0.0],
           "door": {"to_space": "Hut", "to_ref": "p.in", "to_pos": [10.0, 0.0, 0.0], "to_rot": [0.0, 0.0, 0.0],
                    **({"arrival": arrival} if arrival else {})}}
    inn = {"id": "p.in", "fk": "P:000002", "space": "Hut", "pos": [10.0, 0.0, 0.0], "rot": [0.0, 0.0, 0.0],
           "door": {"to_space": "exterior", "to_ref": "p.out", "to_pos": [-30.0, 70.0, 870.6], "to_rot": [0.0, 0.0, 5.9]}}
    build.pair_doors({"refs": [out, inn], "by_id": {"p.out": out, "p.in": inn}})
    return out, inn


def test_the_outer_doors_arrival_wins_over_a_stale_to_pos():
    _, inn = _pair([-30.0, 70.0, 575.0])
    assert inn["teleport"]["pos"] == [-30.0, 70.0, 575.0]
    assert inn["teleport"]["rot"] == [0.0, 0.0, 5.9]


def test_without_an_arrival_the_to_pos_stands():
    out, inn = _pair(None)
    assert inn["teleport"]["pos"] == [-30.0, 70.0, 870.6]
    assert out["teleport"]["pos"] == [10.0, 0.0, 0.0]
