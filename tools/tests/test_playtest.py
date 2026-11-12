"""The paper game (tools/playtest): the example opening played to its end through `playtest do`, every condition and
result word of the quest form handled, the harness errors, deaths and fights, talk, stalls and the index."""
import json
from pathlib import Path

import pytest

from tools.playtest import game as G
from tools.playtest import session as S

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "tools/questform/examples/opening.json"
NAMES = REPO / "tools/playtest/examples/opening.names.json"
SCHEMA = json.loads((REPO / "tools/questform/schema.json").read_text())


def form():
    return json.loads(EXAMPLE.read_text())


def world(extra_names=None, talkers=()):
    n = json.loads(NAMES.read_text())
    return {"names": {**n["names"], **(extra_names or {})}, "places": n["places"], "talkers": list(talkers),
            "doors": {}}


def game(f=None, **kw):
    g = G.Game([f or form()], world(**kw))
    g.begin(at="door.example.hold")
    return g


def new_session(tmp_path, *forms):
    paths = []
    for i, f in enumerate(forms):
        p = tmp_path / f"form{i}.json"
        p.write_text(json.dumps(f))
        paths.append(str(p))
    return S.new(paths or [str(EXAMPLE)], names=[str(NAMES)], at="door.example.hold", use_db=False,
                 root=tmp_path / "runs")


def test_example_played_to_its_ending_through_do(tmp_path):
    folder, screen = new_session(tmp_path)
    assert "Gang Boss walks up to you and speaks." in screen
    assert "New objective: Find Sample-Contact in Lilmoth." in screen
    steps = [("map", "Marker 1: Sample-Contact (a person)"), ("go marker 1", "Sample House, Lilmoth"),
             ("talk Sample-Contact", "1. I was told you have work."),
             ("say I was told you have work.", "[not yet written; the gist:] Work for those"),
             ("say 1", "1. I will serve."), ("say I will serve.", "Quest completed: Off the Pier"),
             ("journal", "Sample-Contact took me in. I serve the Reed now.")]
    for cmd, want in steps:
        code, out = S.do(folder, cmd, think=f"I do {cmd} because it seems the next step")
        assert code == 0 and want in out, (cmd, out)
    rows = S.transcript(folder)
    assert [r["command"] for r in rows][0] == "(new game)" and len(rows) == len(steps) + 1
    assert rows[-1]["summary"]["stages"] == {"quest.example.opening": 40}
    assert S.end(folder, take="It was short and clear.")[0] == 0
    assert S.end(folder, answers="1. Serve the Reed.")[0] == 0
    run = json.loads((folder / "run.json").read_text())
    assert run["ended"] == "all quests ended (quest.example.opening completed)" and run["counts"] == {"commands": 7, "stalls": 0, "harness_errors": 0}
    assert (folder / "take.md").read_text().startswith("It was short")
    idx = json.loads(S.index(tmp_path / "runs").read_text())
    assert idx["runs"][0]["quest"] == "quest.example.opening"


def test_a_command_without_think_is_refused(tmp_path):
    folder, _ = new_session(tmp_path)
    assert S.do(folder, "look", think="")[0] == 2
    assert S.do(folder, "look", think=None)[0] == 2
    assert len(S.transcript(folder)) == 1


def test_command_limit(tmp_path):
    folder, _ = new_session(tmp_path)
    sess = json.loads((folder / "session.json").read_text())
    sess["max_commands"] = 1
    (folder / "session.json").write_text(json.dumps(sess))
    assert S.do(folder, "look", "first look")[0] == 0
    code, out = S.do(folder, "look", "again")
    assert code == 2 and "give your take" in out


# -- the vocabularies ---------------------------------------------------------------------------------------------

def schema_words(kind):
    key = "is" if kind == "condition" else "do"
    words = set()
    for ref in SCHEMA["$defs"][kind]["oneOf"]:
        d = SCHEMA["$defs"][ref["$ref"].split("/")[-1]]["properties"][key]
        words |= set(d.get("enum", [])) | ({d["const"]} if "const" in d else set())
    return words


CONTACT, DOOR, Q = "npc.example.contact", "door.example.hold", "quest.example.opening"
COND_ARGS = {
    "stage_is": {"quest": Q, "stage": 10}, "stage_at_least": {"quest": Q, "stage": 10},
    "stage_done": {"quest": Q, "stage": 10}, "number_compare": {"number": "n", "op": ">=", "value": 0},
    "in_faction": {"faction": "f"}, "rank_at_least": {"faction": "f", "rank": 0},
    "item_count_at_least": {"item": "item.x", "count": 1}, "gold_at_least": {"gold": 1},
    "skill_at_least": {"skill": "Speech", "value": 10}, "alive": {"ref": CONTACT}, "dead": {"ref": CONTACT},
    "speaker_is": {"ref": CONTACT}, "regard_at_least": {"ref": CONTACT, "value": 0},
    "race_is": {"value": "Argonian"}, "sex_is": {"value": "male"}, "spoken_before": {}, "not_spoken_before": {},
}
RESULT_ARGS = {
    "set_stage": {"stage": 20}, "give_item": {"item": "item.x", "count": 2}, "take_item": {"item": "item.x", "count": 1},
    "give_gold": {"amount": 5}, "take_gold": {"amount": 5}, "set_number": {"number": "n", "value": 3},
    "add_number": {"number": "n", "value": 1}, "join_faction": {"faction": "f"}, "set_rank": {"faction": "f", "rank": 2},
    "change_regard": {"ref": CONTACT, "by": 5}, "switch_on": {"ref": CONTACT}, "switch_off": {"ref": CONTACT},
    "lock_door": {"ref": DOOR}, "unlock_door": {"ref": DOOR}, "show_message": {"text": "A box."},
    "speaker_hostile": {}, "start_quest": {"quest": Q, "stage": 20},
}


def test_every_schema_word_is_handled():
    assert schema_words("condition") == set(G.CONDITIONS) == set(COND_ARGS)
    assert schema_words("result") == set(G.RESULTS) == set(RESULT_ARGS)


@pytest.mark.parametrize("word", sorted(COND_ARGS))
def test_each_condition_evaluates(word):
    g = game(extra_names={"item.x": "Ring"})
    assert g.holds(Q, [{"is": word, **COND_ARGS[word]}], CONTACT) in (True, False)


EXPECT = {"give_item": "Added: Ring x2", "show_message": "[Message box] A box.", "speaker_hostile": "attacks you!",
          "set_stage": "New objective: Find Sample-Contact", "start_quest": "New objective: Find Sample-Contact"}


@pytest.mark.parametrize("word", sorted(RESULT_ARGS))
def test_each_result_is_said_from_a_line(word):
    f = form()
    f["lines"].append({"id": "probe", "speaker": "npc.example.roll-man", "kind": "topic", "prompt": "Probe",
                       "text": "Probe.", "written": True, "conditions": [], "results": [{"do": word,
                                                                                         **RESULT_ARGS[word]}],
                       "first_stage": 10, "last_stage": 40, "answers": []})
    f["lines"][0]["first_stage"] = f["lines"][1]["first_stage"] = 30      # keep the speaks-first line quiet
    f["lines"][0]["last_stage"] = f["lines"][1]["last_stage"] = 30
    f["objectives"][0]["targets"] = ["npc.example.roll-man"]
    g = game(f, extra_names={"item.x": "Ring"})
    g.do("talk gang boss")
    out = g.do("say probe")
    assert 'Gang Boss: "Probe."' in out
    if word in EXPECT:
        assert EXPECT[word] in out
    st = g.s
    assert {"give_gold": st["gold"] == 5, "take_gold": st["gold"] == 0, "set_number": st["numbers"].get("n") == 3,
            "add_number": st["numbers"].get("n") == 1, "join_faction": "f" in st["factions"],
            "set_rank": st["factions"].get("f") == 2, "change_regard": st["regard"].get(CONTACT) == 5,
            "switch_on": st["switched"].get(CONTACT) is True, "switch_off": st["switched"].get(CONTACT) is False,
            "lock_door": st["locked"].get(DOOR) is True, "unlock_door": st["locked"].get(DOOR) is False}.get(word, True)


def test_an_unknown_word_is_a_named_harness_error():
    g = game()
    with pytest.raises(G.HarnessError, match="'teleport'"):
        g.holds(Q, [{"is": "teleport"}], None)
    with pytest.raises(G.HarnessError, match="'teleport'"):
        g._apply(Q, [{"do": "teleport"}], None)
    f = form()
    f["stages"][0]["results"].append({"do": "teleport"})
    with pytest.raises(G.HarnessError, match="teleport"):
        G.Game([f], world())


def test_a_quest_this_run_did_not_load_is_a_harness_error():
    f = form()
    f["lines"][2]["conditions"] = [{"is": "stage_done", "quest": "quest.other", "stage": 10}]
    with pytest.raises(G.HarnessError, match="quest.other"):
        G.Game([f], world())


def test_a_name_nobody_gives_is_a_harness_error():
    w = world()
    del w["names"]["npc.example.contact"]
    with pytest.raises(G.HarnessError, match="npc.example.contact"):
        G.Game([form()], w)


# -- deaths, fights, things ---------------------------------------------------------------------------------------

def test_a_must_live_death_fails_the_quest_and_shows_the_message():
    g = game()
    g.do("go sample-contact")
    assert g.do("fight sample-contact lose") == "You died. You load your last save."
    assert g._alive(CONTACT)
    out = g.do("fight sample-contact win")
    assert "Sample-Contact is dead." in out and "Quest failed: Off the Pier" in out
    assert f"[Message box] {G.MAIN_MESSAGE}" in out
    assert "Sample-Contact is dead. Nobody else" in g.journal()
    assert g.do("talk sample-contact") == "Sample-Contact is dead."


def fetch_form():
    f = form()
    f["refs"].append({"id": "thing.ring", "kind": "thing", "enabled": True,
                      "placement": {"base": {"kind": "item", "id": "item.ring"},
                                    "anchor": {"near": "0A0020:Example.esp", "rule": "surface"}},
                      "at": {"cell": "0A0100:Example.esp", "interior": False, "x": 1200.0, "y": 2000.0, "z": 50.0}})
    f["refs"].append({"id": "npc.bandit", "kind": "person", "enabled": True, "hostile": True,
                      "placement": {"existing": "0B0001:Example.esp"},
                      "at": {"cell": "0A0100:Example.esp", "interior": False, "x": 1300.0, "y": 2000.0, "z": 50.0}})
    f["triggers"] = [{"id": "take.ring", "kind": "take", "ref": "thing.ring", "prerequisite": 20, "sets": 30},
                     {"id": "death.bandit", "kind": "death", "ref": "npc.bandit", "prerequisite": 30, "sets": 40}]
    return f


def test_take_and_death_triggers_move_the_quest():
    g = game(fetch_form(), extra_names={"thing.ring": "Silver Ring", "npc.bandit": "Bandit", "item.ring": "Silver Ring"})
    assert "Bandit (hostile)" in g.look() and "Silver Ring" in g.look()
    out = g.do("take silver ring")
    assert "Added: Silver Ring" in out and "I found Sample-Contact" in out
    assert g.s["items"] == {"item.ring": 1}
    assert g.do("talk bandit") == "Bandit attacks you rather than talk."
    assert "Quest completed" in g.do("fight bandit win")


def test_locks_and_doors():
    g = game()
    g.s["locked"][DOOR] = True
    assert "Doors: Barge Hold Door (locked)" in g.look()
    assert g.do("use barge hold door") == "Barge Hold Door is locked."
    assert "breaks" in g.do("pick barge hold door fail")
    assert "You pick the lock" in g.do("pick barge hold door win")
    assert g.do("use barge hold door") == "You open Barge Hold Door."


def test_persuade_checks_the_sheet():
    f = form()
    f["lines"][2]["conditions"] = [{"is": "skill_at_least", "skill": "Speech", "value": 40}]
    g = game(f)
    g.do("go sample-contact")
    assert "(Persuade) I was told you have work." in g.do("talk sample-contact")
    assert "not persuaded. (Your Speech is 15; this needed 40.)" in g.do("persuade 1")
    g.s["sheet"]["skills"]["Speech"] = 50
    assert "I found Sample-Contact" in g.do("say 1")


def test_the_story_vocabularys_skill_names_read_as_skyrims():
    """A form holds Skyrim's skill names only (the compiler maps the records' older words); the sheet still reads
    an older word asked of it as Skyrim's skill."""
    f = form()
    f["lines"][2]["conditions"] = [{"is": "skill_at_least", "skill": "Speech", "value": 40}]
    g = game(f)
    g.do("go sample-contact")
    assert "(Persuade) I was told you have work." in g.do("talk sample-contact")
    assert "this needed 40" in g.do("persuade 1")
    assert g._skill("Security") == g.s["sheet"]["skills"]["Lockpicking"]


def test_talkers_show_their_topics_and_rumours_by_stage():
    talker = {"id": "0C0001:Example.esp", "name": "Reads-The-Shallows", "cell": "0A0100:Example.esp",
              "interior": False, "x": 1150.0, "y": 2050.0,
              "topics": [{"topic": "talk.greet-stranger", "prompt": "(greeting)", "lines": ["Stranger."], "gate": None},
                         {"topic": "talk.self", "prompt": "Yourself", "lines": ["I carry crops.", "For coin."],
                          "gate": None},
                         {"topic": "talk.rumours", "prompt": "Latest rumours", "lines": ["A boss wants rid of you."],
                          "gate": {"quest": "ARG_ExampleOpening", "first": 30, "last": None}}]}
    g = game(talkers=[talker])
    out = g.do("talk reads")
    assert 'Reads-The-Shallows: "Stranger."' in out and "Yourself" in out and "Latest rumours" not in out
    assert 'Reads-The-Shallows: "I carry crops. For coin."' in g.do("say yourself")
    g.s["quests"][Q]["stage"] = 30
    assert "Latest rumours" in g.do("talk reads")


def test_new_sheet_race_skills():
    sh = G.new_sheet("Argonian", "female", Speech=30)
    assert sh["skills"]["Lockpicking"] == 25 and sh["skills"]["Sneak"] == 20 and sh["skills"]["Speech"] == 30
    with pytest.raises(G.HarnessError):
        G.new_sheet("Argonian", "male", Flying=5)


def test_stalls():
    def r(cmd, think="go on", result=""):
        return {"command": cmd, "think": think, "result": result}
    rows = [r("look"), r("look"), r("journal"), r("map"), r("journal"), r("talk x", "I am stuck here"), r("map"),
            r("say 1", result="a"), r("say 1", result="b")]
    assert S.stalls(rows) == 3


def test_map_gives_distance_and_direction():
    g = game()
    m = g.map()
    assert "Marker 1: Sample-Contact (a person)" in m and "its door is at (40000, -30000)" in m
    assert "a walk of about 720 m to the south-east" in m
    assert g.summary()["markers"] == [CONTACT]


def test_the_world_database_gives_the_talkers_standing_where_a_quest_is():
    from tools.playtest import world as W
    f = form()
    c = next(r for r in f["refs"] if r["id"] == CONTACT)
    c["placement"] = {"existing": "02A1E9:Black Marsh.esm"}
    c["at"] = {"cell": "005A11:Black Marsh.esm", "interior": False, "x": 21606.0, "y": -11999.0, "z": 0.0}
    snap = W.snapshot([f], [NAMES])
    assert "Peeks-Under-Boats" in {t["name"] for t in snap["talkers"]}
    assert snap["places"]["005A11:Black Marsh.esm"]["name"] == "Lilmoth"
    del snap["names"][CONTACT]
    g = G.Game([f], snap)
    g.begin(at="door.example.hold")
    g.do("go peeks-under-boats")
    out = g.do("talk peeks-under-boats")
    assert "I was told you have work." in out and "Yourself" in out


# -- the chained run, the counts, our people's names, the final questions -----------------------------------------

def test_a_run_over_chained_quests_is_not_over_when_the_first_ends(tmp_path):
    from tools.playtest import runner
    assert "more may follow after a quest completes" in runner.brief("play", "careful", "")
    assert "active objective" in runner.brief("play", "careful", "")
    second = form()
    second["quest"]["id"] = "quest.example.second"
    second["quest"]["start"] = {"by": "quest_stage", "quest": Q, "quest_stage": 40, "stage": 10}
    sess = {"forms": [form(), second], "broken": None, "take": "t", "max_commands": 40}
    st = {"commands": 5, "quests": {Q: {"ended": "completed"}}}
    assert S.how_ended(sess, st) == f"stopped by the player ({Q} completed, quest.example.second not started)"
    st["quests"]["quest.example.second"] = {"ended": None}
    assert S.how_ended(sess, st).endswith(f"({Q} completed, quest.example.second active)")
    st["quests"]["quest.example.second"] = {"ended": "failed"}
    assert S.how_ended(sess, st) == f"all quests ended ({Q} completed, quest.example.second failed)"
    st["commands"] = 40
    st["quests"]["quest.example.second"] = {"ended": None}
    sess["take"] = None
    assert S.how_ended(sess, st).startswith("command limit")


def test_counts_are_filled_on_every_path_and_the_index_recomputes_them(tmp_path):
    folder, _ = new_session(tmp_path)
    S.do(folder, "look", think="I look around")
    run = S.write_run(folder, {"cost_usd": 0.1, "minutes": 1.0})      # the runner's path
    assert run["counts"] == {"commands": 1, "stalls": 0, "harness_errors": 0}
    p = folder / "run.json"
    kept = json.loads(p.read_text())
    kept["counts"] = {"commands": None, "stalls": None, "harness_errors": None}
    p.write_text(json.dumps(kept))
    idx = json.loads(S.index(tmp_path / "runs").read_text())
    assert idx["runs"][0]["counts"] == {"commands": 1, "stalls": 0, "harness_errors": 0}
    assert json.loads(p.read_text())["counts"]["commands"] == 1


def templated(**extra):
    return {"refs": [{"id": "npc.nesh-deeka", "kind": "person", "enabled": True, **extra,
                      "placement": {"base": {"kind": "template_person", "id": "160E6A:Black Marsh.esm"}}}]}


def test_a_refs_own_name_is_its_name_and_nothing_else(tmp_path, capsys):
    from tools.playtest import world as W
    f = tmp_path / "n.json"
    f.write_text(json.dumps({"names": {"npc.nesh-deeka": "From The File"}, "places": {}}))
    snap = W.snapshot([templated(name="Nesh-Deeka")], [f], use_db=False)
    assert snap["names"]["npc.nesh-deeka"] == "Nesh-Deeka" and capsys.readouterr().err == ""


def test_a_person_from_a_template_gets_the_casts_name_else_the_templates_with_a_warning(capsys):
    from tools.playtest import world as W
    snap = W.from_db([templated()])
    assert snap["names"]["npc.nesh-deeka"] == "Nesh-Deeka" and snap["fallback"] == []
    ref = templated()["refs"][0]
    ref["id"] = "npc.nobody-we-wrote"
    out = W.snapshot([{"refs": [ref]}])
    assert out["fallback"] == ["npc.nobody-we-wrote"]
    err = capsys.readouterr().err
    assert err.count("WARNING") == 1 and "npc.nobody-we-wrote" in err and "template" in err


def test_the_standing_questions_are_a_separate_numbered_final_turn(tmp_path):
    from tools.playtest import runner
    folder, _ = new_session(tmp_path)
    S.do(folder, "look", think="I look around")
    code, out = S.end(folder, take="A short take.", ask=True)
    assert code == 0 and "answer these" not in out
    asked = []
    text = runner.ask_questions(folder, "sys", "m", tmp_path, ask=lambda p: asked.append(p) or "1. Go on.\n2. Nobody.")
    assert "1. What do you think you are meant to do next?" in asked[0] and "A short take." in asked[0]
    assert "4. What would you tell the writer?" in asked[0] and "look" in asked[0]
    assert text.startswith("1. Go on.") and (folder / "answers.md").read_text().startswith("1. Go on.")


def test_speechcraft_is_the_sheets_speech():
    g = game()
    g.s["sheet"]["skills"]["Speech"] = 33
    assert g._skill("Speechcraft") == 33


def test_the_forms_name_their_items_doors_and_marked_places():
    """A form's `names`, a door's `destination` and a marker's `name` reach the player without a names file."""
    from tools.playtest import world as W
    f = {"names": {"item.ring": "Silver Ring"}, "refs": [
        {"id": "door.x", "kind": "door", "enabled": True, "destination": "Coast Ship", "placement": {}},
        {"id": "marker.x", "kind": "marker", "enabled": True, "name": "Low-Reed Village", "placement": {},
         "at": {"cell": "03978F:Black Marsh.esm", "interior": False, "x": 0.0, "y": 0.0, "z": 0.0}}]}
    snap = W.snapshot([f], use_db=False)
    assert snap["names"]["item.ring"] == "Silver Ring" and snap["names"]["door.x"] == "Door to Coast Ship"
    assert snap["places"]["03978F:Black Marsh.esm"] == {"name": "Low-Reed Village", "interior": False}
