"""A thing seated `on` another that was raised in the studio (a bigger seat dz, the pos z the seat works out) is
where the seat pass leaves it: the seat moves 0 refs, in every seat mode."""
import pytest

from tools.places.seat import seat_all


class Flat:
    def has(self, x, y):
        return True

    def height(self, x, y):
        return 100.0

    def water(self, x, y):
        return 50.0


def _refs(dz):
    house = {"id": "h", "pos": [0, 0, 100.0], "rot": [0, 0, 0], "seat": {"mode": "ground", "dz": 0.0}}
    door = {"id": "d", "pos": [10, 0, 100.0 + dz], "rot": [0, 0, 0], "seat": {"mode": "on", "on": "h", "dz": dz}}
    return [door, house]


@pytest.mark.parametrize("dz", [90.1, 140.1, 20.0])
def test_a_raised_door_on_its_house_is_not_moved_by_the_seat_pass(dz):
    refs = _refs(dz)
    assert seat_all(refs, Flat()) == 0
    assert refs[0]["pos"][2] == 100.0 + dz


@pytest.mark.parametrize("mode,base", [("ground", 100.0), ("above", 100.0), ("water", 50.0), ("stilts", 100.0)])
def test_a_raised_thing_in_any_mode_keeps_its_dz(mode, base):
    r = {"id": "x", "pos": [0, 0, base + 30.0], "rot": [0, 0, 0], "seat": {"mode": mode, "dz": 30.0, "foot": [-10, -10, 10, 10]}}
    assert seat_all([r], Flat()) == 0
