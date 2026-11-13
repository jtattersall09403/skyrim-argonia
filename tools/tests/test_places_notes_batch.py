"""The owner's plain notes are written, then sent as one batch, then done (tools/places/notes.py), and a sent batch
runs one agent that closes each note with a reply (tools/places/notes_batch.py, with a stand-in agent)."""
import json
import sys

import pytest

from tools.places import notes, notes_batch


def test_a_note_is_written_then_sent_then_done(tmp_path):
    """Unsent notes are the owner's to change or delete; Send sends every one of them as one batch; only a sent note
    is answered; a note from before batches counts as sent."""
    for t in ("one", "two", "three"):
        notes.add("x", {"text": t}, tmp_path)
    assert [notes.state(n) for n in notes.read("x", tmp_path)] == ["unsent"] * 3
    assert notes.edit("x", "n2", " two, better ", tmp_path)["text"] == "two, better"
    assert notes.delete("x", "n3", tmp_path)["deleted"]
    with pytest.raises(ValueError, match="not been sent"):
        notes.done("x", "n1", "too soon", tmp_path)
    out = notes.send("x", tmp_path)
    assert out["batch"] == "b1" and [n["id"] for n in out["sent"]] == ["n1", "n2"]
    assert all(n["sent"] and n["sent_at"] and n["batch"] == "b1" for n in notes.read("x", tmp_path))
    with pytest.raises(ValueError, match="sent to the agent"):
        notes.edit("x", "n1", "changed my mind", tmp_path)
    with pytest.raises(ValueError, match="sent to the agent"):
        notes.delete("x", "n2", tmp_path)
    with pytest.raises(ValueError, match="no unsent notes"):
        notes.send("x", tmp_path)
    notes.add("x", {"text": "four"}, tmp_path)
    assert [n["id"] for n in notes.send("x", tmp_path)["sent"]] == ["n3"], "a deleted note was never sent: its id is free"
    assert notes.read("x", tmp_path)[-1]["batch"] == "b2"
    assert notes.state(notes.done("x", "n1", "done", tmp_path)) == "done"
    assert notes.state({"id": "n9", "text": "old", "done": False}) == "sent", "a note from before batches"


def test_the_listing_shows_only_sent_open_notes(tmp_path, capsys):
    notes.add("x", {"text": "sent and open"}, tmp_path)
    notes.add("x", {"text": "answered"}, tmp_path)
    notes.send("x", tmp_path)
    notes.done("x", "n2", "ok", tmp_path)
    notes.add("x", {"text": "still the owner's"}, tmp_path)
    (tmp_path / "x" / "edits" / "a.json").write_text(json.dumps({"save_id": "a", "ops": [
        {"n": 1, "op": "ref.move", "space": "exterior", "id": "r1", "note_group": "g1",
         "before": {"pos": [0, 0, 0]}, "after": {"pos": [700, 0, 0]}}],
        "notes": [{"id": "g1", "text": "read at finalise", "at": "t"}]}))

    def listed(*args):
        notes.main([*args, "--places", str(tmp_path)])
        return capsys.readouterr().out
    out = listed()
    assert "sent and open" in out and "answered" not in out and "still the owner's" not in out
    assert "read at finalise" not in out, "notes on changes are read at finalise, not at a session start"
    assert "still the owner's" in listed("x", "--unsent")
    assert "read at finalise" in listed("x", "--changes")
    out = listed("x", "--all")
    assert all(w in out for w in ("sent and open", "answered", "still the owner's", "read at finalise"))
    notes.main(["done", "x", "n1", "--reply", "moved it", "--places", str(tmp_path)])
    capsys.readouterr()
    assert "no open notes" in listed()


STAND_IN = """import sys
from pathlib import Path
from tools.places import notes
place, places = sys.argv[1], Path(sys.argv[2])
assert "narrow change" in Path(sys.argv[3]).read_text()
for n in notes.read(place, places):
    if notes.state(n) == "sent":
        notes.done(place, n["id"], "done: " + n["text"], places)
print('{"total_cost_usd": 0.01, "num_turns": 3, "result": "ok"}')
"""


def test_a_sent_batch_runs_one_agent_that_closes_each_note(tmp_path, monkeypatch):
    places, out = tmp_path / "places", tmp_path / "runs"
    for t in ("raise the jetty", "is the shrine meant to be ruined?", "more reeds"):
        notes.add("x", {"text": t}, places)
    notes.send("x", places)
    notes.add("x", {"text": "not sent"}, places)
    agent = tmp_path / "agent.py"
    agent.write_text(STAND_IN)
    monkeypatch.setenv("PYTHONPATH", str(notes_batch.CODE_REPO))
    monkeypatch.setattr(notes_batch, "agent_cmd",
                        lambda place, text, pf, b, t: [sys.executable, str(agent), place, str(places), str(pf)])
    assert notes_batch.run("x", places, out) == 0
    rows = notes.read("x", places)
    assert [notes.state(n) for n in rows] == ["done", "done", "done", "unsent"], "the unsent note is never answered"
    assert rows[1]["reply"] == "done: is the shrine meant to be ruined?"
    assert "not sent" not in next(out.glob("x.*.prompt.md")).read_text(), "the agent never sees an unsent note"
    rec = json.loads(next(out.glob("x.*.json")).read_text())
    assert rec["notes"] == ["n1", "n2", "n3"] and rec["still_open"] == [] and rec["cost_usd"] == 0.01
    assert notes_batch.run("x", places, out) == 0, "nothing left: the next run does nothing"
    # an agent that leaves a note open: the run says so
    notes.send("x", places)
    monkeypatch.setattr(notes_batch, "agent_cmd", lambda *a: [sys.executable, "-c", "print('{}')"])
    assert notes_batch.run("x", places, out) == 1


def test_the_override_command_gets_the_place_and_the_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTES_AGENT_CMD", "echo hello")
    assert notes_batch.agent_cmd("x", "p", tmp_path / "p.md", 10, 80) == ["echo", "hello", "x", str(tmp_path / "p.md")]


def test_the_batch_prompt(tmp_path, monkeypatch):
    monkeypatch.delenv("NOTES_AGENT_CMD", raising=False)
    notes.add("x", {"text": "raise the jetty"}, tmp_path)
    notes.send("x", tmp_path)
    p = notes_batch.prompt("x", tmp_path, notes_batch.open_notes("x", tmp_path))
    assert "raise the jetty" in p and "notes done x <note id>" in p and f"--places {tmp_path}" in p
    assert "never redraft" in p and "never regenerate over the owner's studio edits" in p
    assert "question for the owner" in p and "commit nothing" in p
    ours = notes_batch.prompt("helstrom", notes.PLACES, [])
    assert "tooling/lane_commit.sh" in ours and "--places" not in ours
    cmd = notes_batch.agent_cmd("x", "p", tmp_path / "p.md", 10, 80)
    assert cmd[:2] == ["claude", "-p"] and "--max-budget-usd" in cmd and "acceptEdits" in cmd
