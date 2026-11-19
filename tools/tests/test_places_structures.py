"""A source's major structures are kept only where the place record supports them (tools/places/draft/structures.py),
and a piece whose floor is taken out stands on our ground as it stood on that floor (seating.floor_gone)."""
from unittest import mock

from tools.places.draft import seating, structures

BASES = {
    "plaza": {"edid": "MorrImpKeepExtPlaza", "model": "keep/exterior/mwimparchplaza01.nif", "kind": "building"},
    "wall": {"edid": "MorrImpKeepExtWall01", "model": "keep/exterior/mwimparchwall01.nif", "kind": "building"},
    "dock": {"edid": "MorrImpKeepDockMid02", "model": "keep/dock/x.nif", "kind": "building"},
    "house": {"edid": "SOMRTownhouse2", "model": "houses/townhouse2.nif", "kind": "building"},
    "gatehouse": {"edid": "MorrImpGatehouse01B", "model": "imp/gatehouse01.nif", "kind": "building"},
    "door": {"edid": "DLC2RRDoorLoad01", "model": "door.nif", "kind": "door", "type": "Door"},
}
REFS = [{"id": k, "base": k} for k in BASES] + [{"id": "d2", "base": "wall", "door": {"to_space": "Room"}}]


def test_unsupported_structures_are_dropped_and_supported_kept():
    got = structures.judge(REFS, BASES, "a town of sedge-wardens; its harbour on the river")
    assert got["terrace"]["kept"] is False and got["terrace"]["refs"] == ["plaza"]
    assert got["walls"]["kept"] is False and got["walls"]["refs"] == ["wall"]   # a door is never a wall's piece
    assert got["harbour"]["kept"] is True
    assert "house" not in str(got) and "gatehouse" not in str(got)     # houses are no structure


def test_a_word_of_the_record_keeps_it_and_a_verb_does_not():
    assert structures.judge(REFS, BASES, "the walled town")["walls"]["kept"] is True
    assert structures.supported("keep", "the wardens keep the reed beds") is None
    assert structures.supported("keep", "a fort on the hill") == "fort"


def test_a_harbour_is_ordinary_on_the_water():
    got = structures.judge(REFS, BASES, "a fishing village by the lake")
    assert got["harbour"]["kept"] is True and "ordinary" in got["harbour"]["why"]


def test_a_record_that_rules_a_structure_out_drops_it():
    """Helstrom's look: "no stone and no outward wall, because the marsh is the wall"."""
    got = structures.judge(REFS, BASES, "houses of reed and mud, with no stone and no outward wall; a gate of reeds")
    assert got["walls"]["kept"] is False and "no outward wall" in got["walls"]["why"]


def test_a_buildings_own_wall_or_a_keeper_is_no_support():
    assert structures.supported("walls", "jars stacked by the longhouse wall; a back wall door") is None
    assert structures.supported("keep", "a keeper and two lanterns") is None


def test_a_palisade_of_clutter_pieces_is_a_wall_and_a_tower_house_is_a_home():
    assert structures.classify({"edid": "StockadeWallStraight01", "model": "stockadewallstraight01.nif",
                                "kind": "clutter"}) == "walls"
    assert structures.classify({"edid": "StockadeTower01", "model": "stockadetower01.nif", "kind": "clutter"}) == "walls"
    assert structures.classify({"edid": "Barrel01", "model": "barrel01.nif", "kind": "clutter"}) is None
    assert structures.classify({"edid": "01arghousebig", "model": "exttower.nif", "kind": "building"}) is None
    assert structures.classify({"edid": "01mosspost", "model": "byohbyohwrtowerpostsl01.nif", "kind": "building"}) is None


def test_floor_gone_seats_on_ground_at_its_height_over_the_floor():
    sup = {"id": "p", "base": "plaza", "pos": [0.0, 0.0, 100.0], "rot": [0, 0, 0]}
    r = {"id": "h", "base": "house", "kind": "building", "pos": [10.0, 0.0, 356.0]}
    # a floor 256 over the plaza's origin under the house, and a roof above it that is not its floor
    floor = [[-50, -50, 256], [50, -50, 256], [0, 50, 256]]
    roof = [[-50, -50, 600], [50, -50, 600], [0, 50, 600]]
    with mock.patch("tools.places.seat._collision_tris", return_value=[floor, roof]), \
            mock.patch("tools.places.draft.geom.foot", return_value=None):
        s = seating.floor_gone(r, sup, BASES, g=None)
    assert s == {"mode": "ground", "dz": 0.0}
