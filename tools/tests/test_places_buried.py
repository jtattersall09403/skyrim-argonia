"""The one physical buried rule (tools/places/look/geom.py `is_buried`), shared by `look probe` and `draft check`."""
from tools.places.look import geom


def test_a_house_sunk_by_hand_with_its_body_showing_is_not_buried():
    # a 400-high house sunk 215 (source stood 284 over a hollow): most of it still shows over even the lowest ground
    assert not geom.is_buried(-215.0, 185.0, 0.0)


def test_a_house_wholly_under_the_lowest_ground_is_buried():
    assert geom.is_buried(-500.0, -200.0, 0.0)         # wholly under
    assert not geom.is_buried(-300.0, 100.0, 0.0)      # its top still shows


def test_stilt_posts_and_rock_feet_in_the_ground_are_fine():
    assert not geom.is_buried(-120.0, 380.0, 0.0)      # posts 120 in, a house on top
    assert not geom.is_buried(-100.0, 300.0, -60.0)    # a rock sunk to its feet on a slope


def test_a_door_half_under_the_ground_is_buried_though_its_house_is_not():
    assert geom.is_buried(-100.0, 100.0, 5.0, part=True) is True
    assert not geom.is_buried(-100.0, 100.0, 5.0)      # the same box as a whole piece shows
    assert geom.is_part({"kind": "door"}) and geom.is_part({"edid": "MudWindow01"}) and not geom.is_part({"edid": "Rock01"})


def test_a_plant_needs_most_of_it_under():
    assert not geom.is_buried(-10.0, 20.0, 0.0, plant=True)
    assert geom.is_buried(-40.0, 10.0, 0.0, plant=True)
