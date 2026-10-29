"""The writing skills' brief tools read the right rows: place_brief.py gives a person the facts carried at their npc
socket; brief.py reads a quest with an empty list (no clues) as empty."""
import runpy
import sys
from pathlib import Path

import pytest

from tools.argonia_world import db

SKILLS = Path(__file__).resolve().parents[3] / ".claude" / "skills"


@pytest.fixture
def w(monkeypatch):
    world = db.open()
    monkeypatch.setattr(db, "open", lambda *a, **k: world)
    yield world
    world.con.rollback()


def run(script, monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", [script, *argv])
    with pytest.raises(SystemExit) as e:
        runpy.run_path(str(SKILLS / script), run_name="__main__")
    return e.value.code


def test_place_brief_has_the_facts_at_the_persons_socket(w, monkeypatch, tmp_path):
    person = "npc.imperial-fringe.bog-iron-workings.n1"
    want = w.values("SELECT id FROM fact WHERE carrier_built_uid = 'socket.bog-iron-workings.npc-n1'")
    assert want
    assert run("dialogue-write/place_brief.py", monkeypatch, "--person", person, "--out", str(tmp_path / "b.md")) == 0
    text = (tmp_path / "b.md").read_text()
    carried = text.split("## Facts this person carries")[1].split("## Topics")[0]
    assert all(f"`{f}`" in carried for f in want)


def test_quest_brief_reads_a_quest_with_no_clues(w, monkeypatch, tmp_path):
    w.delete("quest_clue", quest_id="quest.local.lh38")
    w.delete("quest_conclusion", quest_id="quest.local.lh38")
    assert run("quest-write/brief.py", monkeypatch, "quest.local.lh38", str(tmp_path)) == 0
    assert (tmp_path / "lh38-journal.md").exists()
