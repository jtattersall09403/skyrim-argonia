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


def test_notes_take_odd_input_and_many_writers(tmp_path):
    """A position that is not three numbers is left out, never a crash; writers at once each get their own id."""
    import threading
    n = notes.add("x", {"text": "a", "things": [{"id": "a", "pos": [1, None, "z"]}, "junk"], "view": {"at": [1, 2, "up"]}},
                  tmp_path)
    assert n["things"] == [{"id": "a"}] and "view" not in n
    ts = [threading.Thread(target=notes.add, args=("x", {"text": f"t{i}"}, tmp_path)) for i in range(12)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    ids = [r["id"] for r in notes.read("x", tmp_path)]
    assert len(ids) == 13 and sorted(ids, key=lambda i: int(i[1:])) == [f"n{i}" for i in range(1, 14)]
    assert not list((tmp_path / "x" / "edits").glob(".*"))
