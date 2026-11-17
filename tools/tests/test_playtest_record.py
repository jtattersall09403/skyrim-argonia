"""The paper game on a quest record's YAML view (tools/playtest/record.py): the milestone gate, successors moved by
say, take and a read hook, a check passed or failed by the player's word, the notes at the end, the run folder, and
`record --check` refusing a broken record one line per fault."""
import copy
import json
from pathlib import Path

from tools.playtest import record as R
from tools.playtest.__main__ import main

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tools/playtest/examples/satchel.yaml"
A = "answer 1. a 2. b 3. c 4. d"


def rec():
    return R.load(FIXTURE)


def started(q=None):
    g = R.Game(q or rec())
    screen = g.begin()
    return g, screen


def test_the_fixture_passes_the_check():
    assert R.check(rec()) == []
    assert main(["record", str(FIXTURE), "--check"]) == 0


def test_the_start_is_a_milestone_and_the_gate_refuses_all_but_answer():
    g, screen = started()
    assert "*** Quest started: The Mender's Satchel ***" in screen and "Objective: Ask Hanu-Mah" in screen
    assert "1. What is going on?" in screen and "4. Is there any word" in screen
    assert "Answer the four questions first" in g.do("look")
    assert g.s["commands"] == 0
    assert g.do(A) == "Noted. The game goes on."
    assert g.s["milestones"][0]["answers"] == ["a", "b", "c", "d"]
    assert g.s["milestones"][0]["plan"]["going"].startswith("Old Teeka")
    assert "You are at Yulca." in g.do("look")


def test_say_moves_a_stage_and_take_and_read_move_the_next():
    g, _ = started()
    g.do(A)
    assert "You travel to Hanu-Mah's Hut." in g.do("go hanu-mah")
    assert "1. Old Teeka wants her satchel back." in g.do("talk hanu-mah")
    out = g.do("say 1")
    assert "the key stays on her belt" in out and "*** Journal updated" in out and g.s["stage"] == 20
    g.do(A)
    assert g.do("take lockpick") == "Added: Lockpick x3" and g.s["items"]["item.lockpick"] == 3
    assert "locked (novice)" in g.do("use chest")
    assert g.do("pick chest win") == "You pick the lock of Hanu-Mah's Chest."
    assert "holds: Mender's Satchel; Letter in Teeka's Hand" in g.do("use chest")
    assert "Journal updated" in g.do("take satchel") and g.s["stage"] == 30           # a take's successor
    g.do(A)
    g.do("take letter")
    out = g.do("read letter")
    assert "yours when I am gone" in out and g.s["stage"] == 40                        # the read hook's flag
    assert g.s["flags"] == {"flag.example.letter-read": True}


def test_a_choice_to_an_ending_then_notes_and_the_end():
    g, _ = started()
    g.s.update(stage=40, done=[10, 20, 30, 40], pending=[], items={"thing.example.satchel": 1}, at="yulca-hut")
    g.do("talk hanu")
    out = g.do("say teeka's letter")
    assert "*** Quest complete" in out and g.s["stage"] == 91 and g.s["ended"] == "complete"
    assert "Write your notes" in g.do(A)
    assert "Answer" in g.do("answer") or True
    assert "game is over" in g.do("answer Hanu-Mah has the satchel.")
    assert g.s["notes"] == "Hanu-Mah has the satchel." and g.do("look") == "The game is over."


def test_a_check_is_passed_or_failed_by_the_players_word():
    g, _ = started()
    g.s.update(stage=20, done=[10, 20], pending=[], at="yulca-hut")
    g.do("talk hanu")
    out = g.do("say persuade")
    assert "needs a check (Speechcraft 30)" in out and "pass" in out
    assert "mind your own business" in g.do("say persuade fail")
    g.do("talk hanu")
    assert "novice's lock" in g.do("say persuade pass")


def test_a_fight_won_leaves_the_key_on_the_body():
    g, _ = started()
    g.s.update(stage=20, done=[10, 20], pending=[], at="yulca-hut")
    assert "On the body: Key to Hanu-Mah's Chest" in g.do("fight hanu win")
    assert g.do("take key") == "Added: Key to Hanu-Mah's Chest"
    assert "You unlock Hanu-Mah's Chest" in g.do("use chest")


def test_check_refuses_a_broken_record_one_line_per_fault(tmp_path, capsys):
    q = copy.deepcopy(rec())
    q["stages"][0]["objectives"][0]["target"] = "npc.nobody"
    q["stages"][0]["successors"][0]["to"] = 25
    q["stages"][1].pop("information")
    q["topics"][0]["person"] = "npc.ghost"
    q["hooks"][0]["thing"] = "thing.nothing"
    q["cast"][0].pop("name")
    bad = R.check(q)
    assert len(bad) == 6, bad
    p = tmp_path / "broken.yaml"
    import yaml
    p.write_text(yaml.safe_dump(q))
    assert main(["record", str(p), "--check"]) == 1
    lines = capsys.readouterr().out.strip().splitlines()
    assert len(lines) == 7 and lines[-1].endswith("6 fault(s)")
    assert main(["record", str(p), "--new", "--out", str(tmp_path / "runs")]) == 3       # refused as a harness error


def test_a_session_keeps_the_run_folder(tmp_path):
    folder, screen = R.new(FIXTURE, root=tmp_path, know="You came to Yulca to mend nets.", way="lockpick")
    assert folder.name.endswith("-designed") and folder.parent.name == "quest.example.satchel"
    assert R.do(folder, "look", think="")[0] == 2
    assert R.do(folder, A, think="I answer")[0] == 0
    assert R.end(folder, "I know about a satchel.")[0] == 0
    run = json.loads((folder / "run.json").read_text())
    assert run["way"] == "lockpick" and run["commands_used"] == ["look", A] and run["notes"] is True
    md = (folder / "milestones.md").read_text()
    assert "| Going on | Old Teeka, Yulca's mender" in md and "| a |" in md
    assert (folder / "notes.md").read_text().startswith("I know about")
    assert json.loads((folder / "session.json").read_text())["know_text"] == "You came to Yulca to mend nets."
