"""A thing its source makes of two models stays one thing (tools/places/draft/companions.py): Black Marsh & Valenwood's
Imperial ship is a hull and a masts-and-rigging model set at one pose. Where the hull puts them (the source's offset
turned with the hull, as tools/places/xform turns a ref) the masts pass; turned the other way, or moved on their own,
they stand off the hull, which is a fault."""
from __future__ import annotations

from tools.places.draft import companions

HULL, MASTS = "Black Marsh.esm:0D8483", "Black Marsh.esm:0D8484"
SOURCE = [{"id": "s.hull", "base": HULL, "kind": "building", "pos": [136656.0, -70515.4, 67.6], "rot": [0, 0, 3.800007]},
          {"id": "s.masts", "base": MASTS, "kind": "building", "pos": [136640.0, -70528.0, 0.0], "rot": [0, 0, 3.8000014]},
          {"id": "s.door", "base": "Skyrim.esm:x", "kind": "door", "pos": [136271.0, -70157.0, 83.0], "rot": [0, 0, 5.4]}]


def place(masts_pos):
    return [{"id": "hull", "base": HULL, "kind": "building", "pos": [-102250.0, -527900.0, 68.0], "rot": [0, 0, 4.71239]},
            {"id": "masts", "base": MASTS, "kind": "building", "pos": masts_pos, "rot": [0, 0, 4.71239]}]


def test_the_masts_where_the_hull_puts_them_pass():
    assert companions.faults(place([-102269.7, -527895.1, 0.4]), [SOURCE]) == []


def test_the_masts_turned_the_wrong_way_or_moved_alone_fail():
    bad = companions.faults(place([-102249.8, -527920.4, 0.4]), [SOURCE])
    assert bad and bad[0].startswith("masts stands 32 units")
    assert companions.faults(place([-102264.4, -527827.4, -63.5]), [SOURCE])   # moved on their own


def test_without_the_masts_nothing_is_asked():
    assert companions.faults(place([-102249.8, -527920.4, 0.4])[:1], [SOURCE]) == []


LEG, DECK = "K.esp:000001", "K.esp:000002"
KIT = [{"id": "s.leg1", "base": LEG, "kind": "static", "pos": [0, 0, 0], "rot": [0, 0, 0]},
       {"id": "s.deck1", "base": DECK, "kind": "static", "pos": [0, 0, 190], "rot": [0, 0, 0]},
       {"id": "s.leg2", "base": LEG, "kind": "static", "pos": [1000, 0, 0], "rot": [0, 0, 0]},
       {"id": "s.deck2", "base": DECK, "kind": "static", "pos": [1000, 0, 380], "rot": [0, 0, 0]},
       {"id": "s.leg3", "base": LEG, "kind": "static", "pos": [2000, 0, 0], "rot": [0, 0, 0]}]


def test_a_modular_kit_is_many_things_not_a_pair():
    """A scaffold's legs and decks stacked at many offsets (and a leg standing alone) make no pair to keep."""
    assert companions.pairs(KIT) == {}
    moved = [dict(r, id=r["id"][2:], src=r["id"]) for r in KIT]
    moved[1]["pos"] = [300, 0, 160]          # a deck sunk and shifted by hand
    assert companions.faults(moved, [KIT]) == []


def test_a_carried_pair_is_checked_against_its_own_partner():
    """A hull carried from the source is judged with its own masts."""
    s_hull, s_masts = SOURCE[0], SOURCE[1]
    carried = [dict(s_hull, id="hull", src="s.hull"), dict(s_masts, id="masts", src="s.masts")]
    assert companions.faults(carried, [SOURCE]) == []          # as the source sets them
    carried[1] = dict(carried[1], pos=[s_masts["pos"][0] + 40, s_masts["pos"][1] + 40, 0.0])
    assert companions.faults(carried, [SOURCE])                # the masts moved off their own hull


def test_a_kits_modular_pieces_set_together_at_many_poses_are_not_one_thing():
    """King of the Murkmire's cypress scaffold: a base under a floor at one spot, the same two at another pose nearby
    elsewhere in the source. The pair is a kit, not one thing: a deck laid by hand from it is no fault."""
    base, floor = "K:base", "K:floor"
    src = [{"id": "s1", "base": base, "kind": "static", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 1.0]},
           {"id": "s2", "base": floor, "kind": "static", "pos": [0.0, 0.0, 190.0], "rot": [0, 0, 1.0]},
           {"id": "s3", "base": base, "kind": "static", "pos": [5000.0, 0.0, 0.0], "rot": [0, 0, 0.0]},
           {"id": "s4", "base": floor, "kind": "static", "pos": [5100.0, 150.0, 190.0], "rot": [0, 0, 2.0]}]
    assert companions.pairs(src) == {}
    ours = [{"id": "b", "base": base, "kind": "static", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0.3]},
            {"id": "f", "base": floor, "kind": "static", "pos": [200.0, 0.0, 190.0], "rot": [0, 0, 1.9]}]
    assert companions.faults(ours, [src]) == []
    assert companions.pairs(SOURCE)                                  # a ship's hull and masts stay one thing


def test_a_carried_piece_keeps_the_turn_its_own_source_partner_has():
    """Two source decks on their legs at one offset, one turned a half round: carried as the source sets them, neither
    is a fault (each is judged at its own partner's pose)."""
    leg, deck = "K:leg", "K:deck"
    src = [{"id": "s1", "base": leg, "kind": "static", "pos": [0.0, 0.0, 0.0], "rot": [0, 0, 0.0]},
           {"id": "s2", "base": deck, "kind": "static", "pos": [0.0, 0.0, 190.0], "rot": [0, 0, 0.0]},
           {"id": "s3", "base": leg, "kind": "static", "pos": [3000.0, 0.0, 0.0], "rot": [0, 0, 0.0]},
           {"id": "s4", "base": deck, "kind": "static", "pos": [3000.0, 0.0, 190.0], "rot": [0, 0, 3.14159265]}]
    assert companions.pairs(src)
    carried = [dict(r, id="p" + r["id"], src=r["id"]) for r in src]
    assert companions.faults(carried, [src]) == []
    carried[3] = dict(carried[3], pos=[3040.0, 0.0, 190.0])
    assert companions.faults(carried, [src])
