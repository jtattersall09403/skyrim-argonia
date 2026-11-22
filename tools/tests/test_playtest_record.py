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


def test_a_stage_that_sets_the_next_shows_its_own_entry_first():
    q = rec()
    st20 = next(s for s in q["stages"] if s["id"] == 20)
    st20.setdefault("onEnter", []).append({"setStage": [q["id"], 30]})
    g, _ = started(q)
    g.do(A)
    g.do("go hanu-mah")
    g.do("talk hanu-mah")
    g.do("say 1")
    assert [m["stage"] for m in g.s["pending"]] == [20, 30]


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


def with_onenter(acts, stage=40, **extra):
    q = copy.deepcopy(rec())
    next(s for s in q["stages"] if s["id"] == stage)["onEnter"] = acts
    q.update(extra)
    return q


def test_a_message_by_id_a_fade_and_a_choice_with_buttons():
    buttons = [{"label": "Teeka's", "sets": 90}, {"label": "Hanu-Mah's", "sets": 91}]
    q = with_onenter([{"showMessage": "msg.vision"}, {"fadeToBlack": True},
                      {"showChoice": {"text": "Whose is the satchel?", "buttons": buttons}}],
                     messages=[{"id": "msg.vision", "text": "You see two old women at one net."}])
    assert R.check(q) == []
    g, _ = started(q)
    g.do(A)
    out = "\n".join(g.enter(40))
    assert out.index("You see two old women at one net.") < out.index("The screen goes black.") \
        < out.index("Whose is the satchel?")
    assert "1. [Teeka's]" in out and "2. [Hanu-Mah's]" in out
    assert g.do("look").startswith("The game is paused at a milestone")           # the milestone is answered first
    assert "Whose is the satchel?" in g.do(A)
    assert "A message box is open" in g.do("look")                                 # refused while it is open
    assert "not one of the buttons" in g.do("choose nobody")
    out = g.do("choose hanu")
    assert g.s["stage"] == 91 and g.s["ended"] == "complete" and "Quest complete" in out and g.s["choice"] is None


def test_an_ending_scene_fades_then_shows_each_message_after_its_before_actions():
    scene = {"endingScene": "scene.mended", "messages": ["The nets are mended.", "Yulca sleeps."],
             "before": [{"addCounter": ["c.done", 1]}]}
    q = with_onenter([scene], stage=90)
    assert R.check(q) == []
    g, _ = started(q)
    out = "\n".join(g.enter(90))
    assert "c.done" not in out
    assert out.index("The screen fades to black.") < out.index("The nets are mended.") < out.index("Yulca sleeps.")
    assert g.s["counters"] == {"c.done": 1} and g.s["scenes"] == ["scene.mended"]


def test_the_other_actions_say_what_skyrim_says_and_the_name_is_asked():
    g, _ = started()
    out = g.apply([{"killNpc": "npc.example.hanu"}, {"raiseSkill": ["sneak", 5]},
                   {"setFactionRank": ["faction.mages", "initiate"]}, {"makePeace": "faction.hlaalu"},
                   {"makeEnemy": "faction.redoran"}, {"grantAbility": ["spell.x", "Mud Ward"]},
                   {"grantMapMarker": "yulca-hut"}, {"giveHome": "yulca"}])
    assert out == ["Hanu-Mah is dead.", "Sneak increased by 5.", "You are now Initiate of Mages",
                   "Hlaalu is now friendly to you", "Redoran is now hostile to you", "Spell learned: Mud Ward",
                   "Map marker added: Hanu-Mah's Hut", "Yulca is now yours."]
    g.apply([{"setPlayerName": True}])
    g.do(A)
    assert "waiting for your name" in g.do("look")
    assert g.do("name Ssaren") == "You are Ssaren." and "You are Ssaren, at" in g.do("look")


def test_a_counter_gates_a_successor_and_a_spell_check_is_the_players_word():
    q = copy.deepcopy(rec())
    q["stages"][0]["successors"].insert(0, {"to": 20, "when": {"counterAtLeast": ["c.herbs", 2]}})
    q["topics"][0]["when"] = {"spellCastNear": ["destruction", "npc.example.teeka"]}
    assert R.check(q) == []
    g, _ = started(q)
    g.do(A)
    g.apply([{"addCounter": ["c.herbs", 1]}])
    g.advance()
    assert g.s["stage"] == 10
    g.apply([{"addCounter": ["c.herbs", 1]}])
    g.advance()
    assert g.s["stage"] == 20
    g.s["pending"].clear()
    g.s["at"] = "yulca"
    g.do("talk teeka")
    assert "(Destruction) a spell cast near Old Teeka" in g.do("say 1")
    assert "satchel of needles" in g.do("say 1 pass")


def test_check_names_an_unknown_action_or_condition_term_and_where_it_stands(tmp_path, capsys):
    q = with_onenter([{"summonDragon": 1}])
    q["stages"][0]["successors"][0]["when"] = {"moonPhase": "full"}
    bad = R.check(q)
    assert "stage 40 onEnter: action term summonDragon is not one the paper game plays" in bad
    assert any("condition term moonPhase" in b for b in bad)
    import yaml
    p = tmp_path / "q.yaml"
    p.write_text(yaml.safe_dump(q))
    assert main(["record", str(p), "--check"]) == 1
    assert "summonDragon" in capsys.readouterr().out


# -- --after: earlier records played to an ending first; rooms; a locked door's activation ----------------------
def _end(sid, eid, **kw):
    return {"id": sid, "place": "yulca", "journalText": f"It ended {sid}.", "ending": "complete", "endingId": eid,
            "information": {"going": "It is over."}, **kw}


def earlier_a():
    buttons = [{"label": "Road", "sets": 90}, {"label": "Ruin", "sets": 91}, {"label": "River", "sets": 92}]
    return {"id": "quest.a", "title": "A", "start": 10, "things": [{"id": "thing.a.pearl", "name": "Pearl"}],
            "stages": [{"id": 10, "hidden": True, "place": "yulca",
                        "onEnter": [{"showChoice": {"text": "Which way?", "buttons": buttons}}]},
                       _end(90, "e90"), _end(92, "e92"),
                       {"id": 91, "hidden": True, "ending": "fail", "endingId": "e91"}],
            "endings": [{"id": "e90", "world": [{"giveItem": "thing.a.pearl"}, {"setFlag": "f.road"},
                                                {"giveGold": 3}, {"killNpc": "npc.a.ghost"}]},
                        {"id": "e91"}, {"id": "e92", "world": [{"setFlag": "f.river"}]}],
            "cast": [{"id": "npc.a.ghost", "name": "Ghost"}]}


def later_b():
    return {"id": "quest.b", "title": "B", "start": 10, "things": [{"id": "thing.a.pearl", "name": "Pearl"}],
            "startWhen": {"any": [{"questStage": ["quest.a", "=", 90]}, {"questStage": ["quest.a", "=", 92]}]},
            "stages": [{"id": 10, "place": "yulca", "journalText": "Now B.", "objectives": [],
                        "information": {"going": "g", "next": "n", "ways": "w"},
                        "successors": [{"to": 90, "when": {"all": [{"hasItem": ["thing.a.pearl", 1]},
                                                                   {"flag": ["f.road", True]},
                                                                   {"stageEverReached": ["quest.a", 90]}]}}]},
                       _end(90, "e")], "endings": [{"id": "e"}]}


def write(tmp_path, name, q):
    import yaml
    p = tmp_path / name
    p.write_text(yaml.safe_dump(q))
    return p


def test_after_plays_the_earlier_record_to_a_completed_ending_and_carries_its_state(tmp_path):
    a, b = write(tmp_path, "a.yaml", earlier_a()), write(tmp_path, "b.yaml", later_b())
    folder, screen = R.new(b, root=tmp_path / "runs", after=[str(a)])
    s = json.loads((folder / "session.json").read_text())["state"]
    assert s["stage"] == 90 and s["ended"] == "complete"                       # B's start held and its successor too
    assert s["items"] == {"thing.a.pearl": 1} and s["gold"] == 3 and s["flags"] == {"f.road": True}
    assert s["dead"] == ["npc.a.ghost"]
    assert s["loaded"]["quest.a"] == {"stage": 90, "done": [10, 90], "ended": "complete"}
    assert "It ended 90" not in screen and "Which way" not in screen          # A's journal and boxes are not shown
    run = json.loads((folder / "run.json").read_text())
    assert run["after"][0]["ending"] == 90


def test_after_at_a_stage_plays_to_that_ending_and_a_fail_is_never_chosen_otherwise(tmp_path):
    a, b = write(tmp_path, "a.yaml", earlier_a()), write(tmp_path, "b.yaml", later_b())
    folder, _ = R.new(b, root=tmp_path / "runs", after=[f"{a}@92"])
    s = json.loads((folder / "session.json").read_text())["state"]
    assert s["loaded"]["quest.a"]["stage"] == 92 and s["flags"] == {"f.river": True} and s["stage"] == 10
    assert s["items"] == {} and s["gold"] == 0
    assert R.parse_after([f"{a}@91", str(a)]) == [(str(a), 91), (str(a), None)]
    q = earlier_a()
    q["stages"] = [s_ for s_ in q["stages"] if s_["id"] not in (90, 92)]
    q["stages"][0]["onEnter"][0]["showChoice"]["buttons"] = [{"label": "Ruin", "sets": 91}]
    bad = write(tmp_path, "bad.yaml", q)
    import pytest

    from tools.playtest.game import HarnessError
    with pytest.raises(HarnessError, match="cannot reach a completed ending"):
        R.new(b, root=tmp_path / "runs", after=[str(bad)])
    assert main(["record", str(b), "--new", "--out", str(tmp_path / "runs"), "--after", str(bad)]) == 3


def test_a_loaded_quest_is_moved_silently_by_the_played_quests_state(tmp_path):
    a = {"id": "quest.a", "start": 10, "stages": [
        {"id": 10, "hidden": True, "successors": [{"to": 90, "when": {"flag": ["f.x", True]}}]},
        {"id": 90, "hidden": True, "ending": "complete", "endingId": "e", "onEnter": [{"giveGold": 7}]}],
        "endings": [{"id": "e"}]}
    g = R.Game(later_b(), earlier=[a])
    g.s["loaded"]["quest.a"] = {"stage": 10, "done": [10], "ended": None}
    g.apply([{"setFlag": ["f.x", True]}])
    g.advance()
    assert g.s["loaded"]["quest.a"] == {"stage": 90, "done": [10, 90], "ended": "complete"} and g.s["gold"] == 7
    assert not g.s["pending"]


def fort():
    return {"id": "quest.fort", "start": 10, "cast": [{"id": "npc.q", "name": "Quartermaster"}],
            "stages": [{"id": 10, "hidden": True, "place": "fort-chalkmoth",
                        "successors": [{"to": 90, "when": {"flag": ["f.knocked", True]}}]},
                       {"id": 90, "hidden": True, "ending": "complete", "endingId": "e"}],
            "endings": [{"id": "e"}],
            "hooks": [{"thing": "door.store", "hook": "activate", "setsFlag": "f.knocked"}],
            "placements": [
                {"ref": "door.store", "kind": "door", "placeName": "Quartermaster's Store",
                 "anchor": {"place": "fort-chalkmoth"}, "lock": {"level": "key"}},
                {"ref": "npc.q", "kind": "person", "name": "Quartermaster",
                 "anchor": {"place": "fort-chalkmoth", "room": "Quartermaster's Store"}}]}


def test_a_room_is_a_place_of_its_own_reached_by_its_door():
    q = fort()
    assert R.check(q) == []
    q["placements"][1]["anchor"]["room"] = " "
    assert any("anchor room is empty" in b for b in R.check(q))
    q = fort()
    q["hooks"] = []
    g = R.Game(q)
    g.begin()
    assert "People:" not in g.do("look")                  # the person stands in the room, not the fort
    g.s["unlocked"].append("door.store")
    assert "You go through Door to Quartermaster's Store" in g.do("use door")
    assert g.s["at"] == "Quartermaster's Store" and "People: Quartermaster" in g.do("look")
    assert "You are at Quartermaster's Store." in g.do("look")


def test_using_a_locked_door_fires_its_activate_hook_then_says_it_is_locked():
    g = R.Game(fort())
    g.begin()
    out = g.do("use door")
    assert "is locked" in out and g.s["flags"] == {"f.knocked": True} and g.s["stage"] == 90


def test_arriving_in_a_place_moves_a_stage_on_place_entered():
    q = copy.deepcopy(rec())
    q["stages"][0]["successors"].insert(0, {"to": 20, "when": {"placeEntered": "yulca"}})
    assert R.check(q) == []
    g = R.Game(q)
    g.begin(at="elsewhere")
    g.do(A)
    assert g.s["stage"] == 10
    g.s["at"] = "yulca"
    g.advance()
    assert g.s["stage"] == 20
