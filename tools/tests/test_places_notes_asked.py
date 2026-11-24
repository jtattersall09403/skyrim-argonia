"""An unsent note is answered only on the owner's own instruction, which the note keeps (tools/places/notes.py done)."""
import pytest

from tools.places import notes as N


def test_an_unsent_note_is_refused_unless_the_owner_asked(tmp_path):
    (tmp_path / "p" / "edits").mkdir(parents=True)
    n = N.add("p", {"text": "tilt this plank"}, tmp_path)
    with pytest.raises(ValueError, match="asked"):
        N.done("p", n["id"], "done it", tmp_path)
    r = N.done("p", n["id"], "Tilted: select it and use Tilt.", tmp_path, asked="#96")
    got = N.read("p", tmp_path)[0]
    assert got["done"] and got["asked"] == "#96" and got["reply"].startswith("Tilted") and N.state(got) == "done"
    assert r["id"] == n["id"]
