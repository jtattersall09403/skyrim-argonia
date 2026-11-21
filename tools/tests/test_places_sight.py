"""The sight sheet names what the game names: a harvestable tree (Hanging Moss) by its name, a plain tree by its kind."""
from tools.places import sight


def test_a_harvestable_tree_is_named_and_a_plain_one_is_counted():
    bases = {"S:moss": {"type": "TREE", "name": "Hanging Moss", "model": "plants/florahangingmoss01.nif"},
             "S:willow": {"type": "TREE", "name": None, "model": "landscape/trees/willow01.nif"}}
    rows = [{"id": "p.a", "base": "S:moss", "pos": [0, 0, 0]}, {"id": "p.b", "base": "S:willow", "pos": [10, 0, 0]}]
    things, labels = sight._what(rows, bases, {}, 0.0, 0.0, None)
    assert ('a thing the game names "Hanging Moss"', 1) in labels
    assert not any("Hanging Moss" in t for t in things) and things


def test_woven_fences_are_called_so_not_walls():
    from tools.argonia_world.surroundings import kind_of
    assert kind_of("argonia/clutter/saxhleelfence02.nif alpafencewoven03")[1] == "woven fences"
    assert kind_of("architecture/whiterun/wrfence01.nif")[1] == "walls"
