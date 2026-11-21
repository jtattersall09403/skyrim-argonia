"""The sight sheet names what the game names: a harvestable tree (Hanging Moss) by its name, a plain tree by its kind."""
from tools.places import sight


def test_a_harvestable_tree_is_named_and_a_plain_one_is_counted():
    bases = {"S:moss": {"type": "TREE", "name": "Hanging Moss", "model": "plants/florahangingmoss01.nif"},
             "S:willow": {"type": "TREE", "name": None, "model": "landscape/trees/willow01.nif"}}
    rows = [{"id": "p.a", "base": "S:moss", "pos": [0, 0, 0]}, {"id": "p.b", "base": "S:willow", "pos": [10, 0, 0]}]
    things, labels = sight._what(rows, bases, {}, 0.0, 0.0, None)
    assert ('a thing the game names "Hanging Moss"', 1) in labels
    assert not any("Hanging Moss" in t for t in things) and things
