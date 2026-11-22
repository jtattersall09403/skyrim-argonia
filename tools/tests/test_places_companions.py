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
