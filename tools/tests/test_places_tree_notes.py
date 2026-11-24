"""Notes about the world's trees carry the tree's type, where the world had it and its sink, and are listed grouped by
tree type against the placement rule's sink (tools/places/notes.py)."""
from tools.places import notes


def test_a_tree_note_keeps_its_world_place_and_sink(tmp_path):
    (tmp_path / "p" / "edits").mkdir(parents=True)
    n = notes.add("p", {"text": "too high", "things": [{"id": "world:X", "base": "Black Marsh.esm:0D864C", "kind": "tree",
                                                       "pos": [1, 2, 3], "world": {"base": "Black Marsh.esm:0D864C", "pos": [1, 2, 17]},
                                                       "sink_m": 0.31, "ground": 20}]}, tmp_path)
    t = n["things"][0]
    assert t["world"] == {"base": "Black Marsh.esm:0D864C", "pos": [1.0, 2.0, 17.0]} and t["sink_m"] == 0.31
    text = notes.tree_notes({"p": [n]})
    assert "tree type" in text and "rule sink 0.2-0.2 m" in text and "owner's sink 0.31 m" in text
