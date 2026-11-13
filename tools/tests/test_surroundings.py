"""The surroundings sheet on known spots (raw facts measured from the built world, trimmed to 1,600 units)."""
import json
from pathlib import Path

from tools.argonia_world import surroundings as su

DATA = Path(__file__).parent / "data/surroundings"


def sheet(name: str) -> str:
    return su.sheet(json.loads((DATA / f"{name}.json").read_text()), name)


def test_the_broker_stands_on_a_ships_deck_not_a_pier():
    s = sheet("broker")
    assert "Underfoot [fixed]: the deck of a big ship" in s
    assert "a door to Ship" in s
    assert "Buys-The-Months" in s and "[moving]" in s and "sandbox" in s


def test_the_crocodile_is_in_shallow_water_with_no_plank_walkway_near():
    s = sheet("crocodile")
    assert "Underfoot [fixed]: shallow water" in s
    assert "plank walkway" not in s and "pier" not in s
    assert "Crocodile, a creature; hostile" in s


def test_the_viper_lies_on_bare_earth_with_no_roots():
    s = sheet("viper")
    assert "Underfoot [fixed]: bare earth" in s
    assert "root" not in s


def test_the_cell_men_stand_on_a_giant_trees_roots_and_no_camp():
    s = sheet("cell-man")
    assert "roots of the giant tree" in s
    assert "tent" not in s and "fire burning" not in s
    assert "No fire burns here" in s


def test_indoors_the_building_kit_is_the_room_and_the_floor_is_read():
    s = sheet("nesh-deeka")
    assert "Place [fixed]: indoors" in s
    assert "Underfoot [fixed]: a floor" in s
    assert "room: the walls" in s


def test_kinds_are_read_from_the_file_name_and_unknown_models_are_not_guessed():
    assert su.kind_of("Meshes/Dungeons/NordicRuins/RuinsCeilingRopeShort.nif x")[0] == "rope"
    assert su.kind_of("Meshes/Architecture/BYOH/BYOHWRtowerPostsL01.nif x")[0] == "wooden posts"
    assert su.kind_of("Meshes/Clutter/Something/zzq01.nif zzq01") is None


def test_words_for_distance_never_count():
    assert su.how_far(100) == "right here" and su.how_far(2000) == "a short walk" and su.how_far(9000) == "far"
    assert su.where(0, 1000) == "north, close by"
