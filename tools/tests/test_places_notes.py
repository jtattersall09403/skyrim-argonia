"""The owner's studio notes (tools/places/notes.py): kept, numbered, answered and reopened."""
import pytest

from tools.places import notes


def test_notes_round_trip(tmp_path):
    n = notes.add("x", {"text": " hi ", "things": [{"id": "a", "pos": [1, 2, 3.14159], "kind": "building"}],
                        "view": {"space": "exterior", "at": [1, 2, 3]}}, tmp_path)
    assert n["id"] == "n1" and n["text"] == "hi" and n["things"][0]["pos"] == [1, 2, 3.1]
    assert notes.add("x", {"text": "two"}, tmp_path)["id"] == "n2"
    r = notes.done("x", "n1", "fixed", tmp_path)
    assert r["done"] and r["reply"] == "fixed"
    assert [x["done"] for x in notes.read("x", tmp_path)] == [True, False]
    r = notes.done("x", "n1", places=tmp_path, undo=True)
    assert not r["done"] and "done_at" not in r
    assert "about: " in notes.show("x", notes.read("x", tmp_path)[0])


def test_notes_refuse_nonsense(tmp_path):
    with pytest.raises(ValueError):
        notes.add("x", {"text": "  "}, tmp_path)
    with pytest.raises(ValueError):
        notes.add("../x", {"text": "a"}, tmp_path)
    with pytest.raises(ValueError):
        notes.done("x", "n9", places=tmp_path)
