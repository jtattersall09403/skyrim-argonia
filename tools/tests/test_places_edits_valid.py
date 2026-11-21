"""tools/places/edits_valid.py: the whole check of a commit that touches only a place's edits/ folder."""
import json

from tools.places import edits_valid


def _save(tmp_path, place="p1", name="s1", **over):
    d = tmp_path / place / "edits"
    d.mkdir(parents=True, exist_ok=True)
    body = {"save_id": name, "place_id": place, "ops": [], "notes": [], "final": False}
    body.update(over)
    f = d / f"{name}.json"
    f.write_text(json.dumps(body))
    return f


def test_a_good_save_and_notes_pass(tmp_path):
    f = _save(tmp_path)
    n = f.with_name("notes.jsonl")
    n.write_text(json.dumps({"id": "n1", "text": "move the barrel"}) + "\n")
    assert edits_valid.check_file(f) is None and edits_valid.check_file(n) is None


def test_a_broken_save_or_note_is_named(tmp_path):
    assert "ops" in edits_valid.check_file(_save(tmp_path, name="a", ops="x"))
    assert "place" in edits_valid.check_file(_save(tmp_path, name="b", place_id="other"))
    bad = tmp_path / "p1" / "edits" / "notes.jsonl"
    bad.write_text("{not json\n")
    assert edits_valid.check_file(bad)
    bad.write_text(json.dumps({"id": "n1"}) + "\n")
    assert "line 1" in edits_valid.check_file(bad)


def test_a_variants_save_and_a_deleted_file_pass(tmp_path):
    assert edits_valid.check_file(_save(tmp_path, place="p1@v", name="s2", place_id="p1")) is None
    assert edits_valid.check_file(tmp_path / "p1" / "edits" / "gone.json") is None
