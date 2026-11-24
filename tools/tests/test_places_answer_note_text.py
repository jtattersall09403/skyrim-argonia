"""An answer committed over the owner's open session carries his note's words (look/verbs.py owner_note_text), from
his autosave first, then his saves, so the studio shows him what was answered."""
import json

from tools.places import notes as N
from tools.places.look import verbs


def test_the_note_text_comes_from_his_autosave_then_his_saves(tmp_path, monkeypatch):
    auto = tmp_path / "autosave"
    auto.mkdir()
    monkeypatch.setattr(N, "AUTOSAVES", auto)
    pdir = tmp_path / "p"
    (pdir / "edits").mkdir(parents=True)
    (auto / "p.json").write_text(json.dumps({"ops": [], "notes": [{"id": "g8", "text": "house door in bad position"}]}))
    (pdir / "edits" / "s.json").write_text(json.dumps({"ops": [], "notes": [{"id": "g2", "text": "rigging in the way"}]}))
    assert verbs.owner_note_text("p", "g8", pdir) == "house door in bad position"
    assert verbs.owner_note_text("p", "g2", pdir) == "rigging in the way"
    assert verbs.owner_note_text("p", "g9", pdir) == ""
