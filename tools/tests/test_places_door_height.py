"""A door's height set in the studio is kept by `seat` in every seat mode (tools/places/seat.py seat_all), and a door
seated on its hut stands on the hut's seated height, as the studio's seatZ shows it (test/seat_on.test.mjs)."""
import pytest

from tools.places.seat import Ground, seat_all


def flat(h=500.0):
    return Ground({(0, 0): [h] * (33 * 33)}, {}, None)


@pytest.mark.parametrize("mode", ["ground", "above", "stilts", "clear", "on", "free"])
def test_a_raised_door_keeps_its_height(mode):
    g = flat()
    hut = {"id": "hut", "pos": [1000.0, 1000.0, 300.0], "rot": [0, 0, 0], "seat": {"mode": "above", "dz": 10.0}}
    seat = {"mode": mode} if mode == "free" else {"mode": "on", "on": "hut", "dz": 40.0} if mode == "on" else {"mode": mode, "dz": 0.0}
    door = {"id": "door", "pos": [1000.0, 1100.0, 777.0], "rot": [0, 0, 0], "seat": seat}
    seat_all([hut, door], g)
    z0 = door["pos"][2]
    if mode != "free":                      # the studio raises a seated door by its seat's dz
        door["seat"]["dz"] = door["seat"].get("dz", 0.0) + 30.0
    else:
        door["pos"][2] += 30.0
    seat_all([hut, door], g)
    assert abs(door["pos"][2] - (z0 + 30.0)) < 1e-6
    if mode == "on":
        assert door["pos"][2] == hut["pos"][2] + 70.0 == 580.0
