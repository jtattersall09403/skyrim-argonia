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


def test_notes_list_shows_the_notes_on_changes(tmp_path):
    """`notes` shows each note on changes in an unfinalised save with exactly its changes, once across saves."""
    import json
    ops = [{"n": 1, "op": "ref.move", "space": "exterior", "call": "fault", "id": "r1", "note_group": "g1",
            "before": {"pos": [0, 0, 0]}, "after": {"pos": [700, 0, 0]}},
           {"n": 2, "op": "ref.move", "space": "exterior", "call": "fault", "id": "r2", "note_group": "g1",
            "before": {"pos": [0, 0, 0]}, "after": {"pos": [0, 140, 0]}},
           {"n": 3, "op": "ref.move", "space": "exterior", "call": "fault", "id": "r3",
            "before": {"pos": [0, 0, 0]}, "after": {"pos": [0, 0, 70]}}]
    save = {"save_id": "a", "place_id": "x", "ops": ops, "notes": [{"id": "g1", "text": "off the boardwalk", "at": "t"}]}
    (tmp_path / "x" / "edits").mkdir(parents=True)
    (tmp_path / "x" / "edits" / "a.json").write_text(json.dumps(save))
    auto = tmp_path / "auto"
    auto.mkdir()
    (auto / "x.json").write_text(json.dumps(save | {"save_id": "autosave"}))
    text = notes.change_notes("x", places=tmp_path, autosaves=auto)
    assert text.count('"off the boardwalk"') == 1 and "about 2 changes" in text
    assert "10.0 m east" in text and "2.0 m north" in text and "r3" not in text
    (tmp_path / "x" / "edits" / "a.json").write_text(json.dumps(save | {"final": True}))
    (auto / "x.json").unlink()
    assert notes.change_notes("x", places=tmp_path, autosaves=auto) == ""
    assert '"off the boardwalk"' in notes.change_notes("x", True, places=tmp_path, autosaves=auto)
