"""A new place's repeated interior: further doors into one source interior take another held one of like size."""
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.places.draft import interiors  # noqa: E402


def sp(n, exits=("exterior",), name="", interior=True):
    refs = [{"id": f"r{i}"} for i in range(n)] + [{"id": f"d{j}", "door": {"to_space": t, "to_ref": "x"}} for j, t in enumerate(exits)]
    return NS(refs=refs, meta={"name": name}, interior=interior)


def door(i, t):
    return {"id": i, "door": {"to_space": t, "to_ref": "x"}}


def test_further_doors_take_unused_interiors_of_like_size():
    src = NS(spaces={"exterior": sp(0, ()), "A": sp(20), "B": sp(24), "C": sp(60), "D": sp(18, ("exterior", "A")),
                     "Mine": sp(20, name="Old Mine"), "Hut": sp(22)})
    by_target = {"A": [door("d1", "A"), door("d2", "A"), door("d3", "A")]}
    got = interiors.variant_targets(src, by_target, {"A": False})
    # A itself is reached by D (D is a spare with its own way out); Mine is a site; C is too big; nearest in size first
    assert got == {"d2": "D", "d3": "Hut"}


def test_a_building_with_several_doors_and_a_source_without_spares_repeat():
    src = NS(spaces={"exterior": sp(0, ()), "A": sp(20)})
    assert interiors.variant_targets(src, {"A": [door("d1", "A"), door("d2", "A")]}, {"A": False}) == {}
    src.spaces["B"] = sp(20)
    assert interiors.variant_targets(src, {"A": [door("d1", "A"), door("d2", "A")]}, {"A": True}) == {}
