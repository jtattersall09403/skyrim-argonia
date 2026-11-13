"""The paper game (tools/playtest): the example opening played to its end through `playtest do`, every condition and
result word of the quest form handled, the harness errors, deaths and fights, talk, stalls."""
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


def test_a_command_without_think_is_refused(tmp_path):
    folder, _ = new_session(tmp_path)
    assert S.do(folder, "look", think="")[0] == 2
    assert S.do(folder, "look", think=None)[0] == 2
    assert [r["command"] for r in S.transcript(folder)] == ["(new game)", "look", "look"]      # each refusal has a row
    assert S.transcript(folder)[1]["result"].startswith("Refused")


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
    "change_regard": {"ref": CONTACT, "by": 3}, "switch_on": {"ref": CONTACT}, "switch_off": {"ref": CONTACT},
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
            "set_rank": st["factions"].get("f") == 2, "change_regard": st["regard"].get(CONTACT) == 3,
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
    assert f"[Message box] {G.MESSAGES['main']}" in out
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
    assert g.do("pick barge hold door fail") == "You have no lockpicks."
    g.s["items"][G.LOCKPICK] = 2
    assert "breaks" in g.do("pick barge hold door fail") and g.s["items"][G.LOCKPICK] == 1
    assert "You pick the lock" in g.do("pick barge hold door win")
    assert g.do("use barge hold door") == "You open Barge Hold Door."


def test_a_skill_check_speaks_the_first_line_that_holds():
    """One entry per prompt; saying it speaks the first line whose conditions hold: the check when the sheet meets
    it, else the record's own fallback words. No threshold is shown."""
    f = form()
    f["lines"][2]["conditions"] = [{"is": "skill_at_least", "skill": "Speech", "value": 40}]
    f["lines"].insert(3, {**f["lines"][2], "id": "contact.work.fail", "text": "Words will not do it.", "written": True,
                          "conditions": [], "results": []})
    g = game(f)
    g.do("go sample-contact")
    out = g.do("talk sample-contact")
    assert out.count("I was told you have work.") == 1 and "Persuade" not in out
    out = g.do("say 1")
    assert 'Sample-Contact: "Words will not do it."' in out and "needed" not in out
    g.s["sheet"]["skills"]["Speech"] = 50
    assert "I found Sample-Contact" in g.do("say 1")


def test_the_story_vocabularys_skill_names_read_as_skyrims():
    """A form holds Skyrim's skill names only (the compiler maps the records' older words); the sheet still reads
    an older word asked of it as Skyrim's skill."""
    g = game()
    assert g._skill("Security") == g.s["sheet"]["skills"]["Lockpicking"]
    assert g._skill("Speechcraft") == g.s["sheet"]["skills"]["Speech"]


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
    g.s["quests"][Q]["done"].append(30)
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


def test_counts_are_filled_on_every_path(tmp_path):
    folder, _ = new_session(tmp_path)
    S.do(folder, "look", think="I look around")
    run = S.write_run(folder, {"cost_usd": 0.1, "minutes": 1.0})      # the runner's path
    assert run["counts"] == {"commands": 1, "stalls": 0, "harness_errors": 0}


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


# -- containers, locks, theft, books, windows, who people are, names, the walker -----------------------------------

AT = {"cell": "0A0100:Example.esp", "interior": False, "x": 1000.0, "y": 2000.0, "z": 0.0}
JQ = "quest.test.jar"


def jar_form():
    """A keeper with the key, her owned locked lockbox holding a jar and a note, lockpicks and her cup about."""
    def thing(i, **kw):
        return {"id": i, "kind": "thing", "enabled": True, "at": dict(AT), **kw,
                "placement": kw.get("placement") or {"base": {"kind": "existing_base", "id": "000001:Skyrim.esm"}}}
    return {
        "version": 1,
        "quest": {"id": JQ, "editor_id": "ARG_TestJar", "name": "The Jar", "kind": "main",
                  "start": {"by": "game", "stage": 10}},
        "names": {"item.jar": "Sap Jar"},
        "stages": [{"number": 10, "shown": True, "journal": "Get the jar.", "ending": "none", "results": []},
                   {"number": 20, "shown": True, "journal": "I have the jar.", "ending": "none", "results": []},
                   {"number": 90, "shown": True, "journal": "She has the jar.", "ending": "completed",
                    "results": [{"do": "take_item", "item": "item.jar", "count": 1}]},
                   {"number": 95, "shown": True, "journal": "She is dead.", "ending": "failed", "results": []}],
        "objectives": [{"number": 10, "text": "Bring the jar to the keeper.", "shown_at": [10],
                        "completed_at": [90], "targets": ["npc.keeper"]}],
        "refs": [
            {"id": "npc.keeper", "kind": "person", "enabled": True, "name": "Nesh-Deeka", "at": dict(AT),
             "placement": {"base": {"kind": "template_person", "id": "160E6A:Black Marsh.esm"}}},
            thing("thing.key", name="Lockbox Key", placement={"base": {"kind": "existing_base",
                                                                      "id": "000002:Skyrim.esm"},
                                                             "carried_by": "npc.keeper"}),
            thing("thing.box", name="Lockbox", owner="npc.keeper", lock={"level": "novice", "key": "thing.key"},
                  contents=[{"item": "item.jar", "count": 1}]),
            thing("thing.note", name="Torn Note", text="The cutters come at dusk.",
                  placement={"base": {"kind": "existing_base", "id": "000003:Skyrim.esm"}, "container": "thing.box"}),
            thing("thing.picks", name="Lockpick", placement={"base": {"kind": "existing_base", "id": G.LOCKPICK}}),
            thing("thing.cup", name="Clay Cup", owner="npc.keeper"),
            {"id": "door.vault", "kind": "door", "enabled": True, "name": "Vault Door", "at": dict(AT),
             "lock": {"level": "key"}, "placement": {"existing": "0A0030:Example.esp"}}],
        "lines": [{"id": "keeper.jar", "speaker": "npc.keeper", "kind": "topic", "prompt": "Here is the jar.",
                   "text": "Good.", "written": True,
                   "conditions": [{"is": "item_count_at_least", "item": "item.jar", "count": 1}],
                   "results": [{"do": "set_stage", "stage": 90}], "first_stage": 10, "last_stage": 20,
                   "answers": []}],
        "triggers": [{"id": "take.jar", "kind": "take", "ref": "item.jar", "prerequisite": 10, "sets": 20}],
        "must_live": [{"ref": "npc.keeper", "fail_stage": 95, "main_message": True}]}


def jar_world(*forms):
    from tools.playtest import world as W
    names, *_ = W.from_forms(list(forms))
    return {"names": names, "places": {"0A0100:Example.esp": {"name": "Barge Pier", "interior": False}},
            "talkers": [], "doors": {}, "people": {"npc.keeper": {"race": "argonian", "sex": "female"}}}


def jar_game(f=None):
    f = f or jar_form()
    g = G.Game([f], jar_world(f))
    g.begin(at="npc.keeper")
    return g


def test_a_container_lists_its_contents_and_cannot_be_taken():
    g = jar_game()
    look = g.look()
    assert "Lockbox (locked, Novice; owned)" in look and "Sap Jar" not in look and "Torn Note" not in look
    assert g.do("take lockbox") == "You cannot carry Lockbox. Use it to open it."
    assert g.do("take torn note") == "Torn Note is in Lockbox: open it first."
    g.s["locked"]["thing.box"] = False
    assert "not yours: opening it is stealing" in g.do("use lockbox")
    out = g.do("use lockbox unseen")
    assert "Nobody sees you." in out and "Lockbox holds: Torn Note; Sap Jar." in out
    out = g.do("take sap jar")
    assert "Added: Sap Jar" in out and "I have the jar." in out            # counted by the form's item id
    assert g.s["items"]["item.jar"] == 1 and g.s["contents"]["thing.box"]["item.jar"] == 0
    assert g.do("take sap jar") == "There is no 'sap jar' near you."
    g.do("take torn note")
    assert g.s["items"]["thing.note"] == 1
    g.do("talk nesh-deeka")
    assert "Quest completed: The Jar" in g.do("say here is the jar.")


def test_a_ref_two_forms_share_takes_what_either_says():
    plain = second_form()
    box = dict(jar_form()["refs"][2])
    plain["refs"].append({k: v for k, v in box.items() if k not in ("lock", "owner", "contents")})
    g = G.Game([plain, jar_form()], {**jar_world(jar_form()), "names": {**jar_world(jar_form())["names"],
                                                                         **json.loads(NAMES.read_text())["names"]}})
    assert g.ents["thing.box"]["lock"]["level"] == "novice" and g.ents["thing.box"]["contents"]


def test_two_people_of_one_name_are_told_apart_by_number():
    f = jar_form()
    twin = dict(f["refs"][0], id="npc.twin")
    f["refs"].append(twin)
    g = jar_game(f)
    assert "People: Nesh-Deeka 1 (an Argonian woman); Nesh-Deeka 2 (a person)" in g.look()
    assert g.do("talk nesh-deeka") == "Which one? Nesh-Deeka 1, Nesh-Deeka 2"
    assert g.do("talk nesh-deeka 2").startswith("Nesh-Deeka looks at you")


def test_a_hand_in_never_accepts_a_thing_never_held():
    g = jar_game()
    assert "Here is the jar." not in g.do("talk nesh-deeka")


def test_locks_levels_keys_and_lockpicks():
    g = jar_game()
    assert g.do("use lockbox") == "Lockbox is locked (Novice)."
    assert g.do("pick lockbox win") == "You have no lockpicks."
    assert g.do("take lockpick") == "Added: Lockpick" and g.s["items"][G.LOCKPICK] == 1
    assert "picking its lock is a crime" in g.do("pick lockbox win")
    out = g.do("pick lockbox win seen")
    assert "You are seen. Nesh-Deeka or a guard confronts you" in out and "Lockbox holds:" in out
    assert g.s["crimes"] == [{"what": "pick Lockbox", "owner": "npc.keeper", "seen": True}]
    assert g.do("use vault door") == "Vault Door is locked (needs a key). It opens only with its key."
    assert g.do("pick vault door win") == "The lock of Vault Door cannot be picked: it opens only with its key."
    f = jar_form()
    f["refs"][2]["lock"]["level"] = "master"
    g = jar_game(f)
    g.s["items"][G.LOCKPICK] = 1
    assert "is beyond your Lockpicking (25)" in g.do("pick lockbox win")
    assert "Your lockpick breaks" in g.do("pick lockbox fail unseen") and G.LOCKPICK not in g.s["items"]


def test_the_key_opens_its_lock_and_pickpocketing_takes_it():
    g = jar_game()
    assert g.do("take lockbox key") == "Nesh-Deeka carries Lockbox Key."
    out = g.do("pickpocket nesh-deeka")
    assert out == "Nesh-Deeka carries: Lockbox Key. Take one with: take <thing> unseen, or take <thing> seen."
    assert "Taking from Nesh-Deeka is pickpocketing." in g.do("take lockbox key")
    g.do("pickpocket nesh-deeka")
    assert g.do("take lockbox key unseen") == "Nobody sees you.\nAdded: Lockbox Key"
    out = g.do("use lockbox unseen")
    assert out.startswith("You unlock Lockbox with Lockbox Key.") and "Sap Jar" in out
    assert g.do("pickpocket nesh-deeka") == "You find nothing on Nesh-Deeka worth taking."


def test_owned_things_and_a_dead_persons_body():
    g = jar_game()
    assert "Clay Cup is not yours: taking it is stealing." in g.do("take clay cup")
    assert "a guard confronts you" in g.do("take clay cup seen") and g.s["items"]["thing.cup"] == 1
    assert "Quest failed: The Jar" in g.do("fight nesh-deeka win")
    assert g.do("pickpocket nesh-deeka").startswith("Nesh-Deeka is dead")
    assert g.do("use nesh-deeka") == "You search the body of Nesh-Deeka. It carries: Lockbox Key."
    assert g.do("take lockbox key") == "Added: Lockbox Key"


def test_a_readable_thing_shows_its_text():
    g = jar_game()
    g.s["locked"]["thing.box"] = False
    g.do("use lockbox unseen")
    g.do("take torn note")
    assert g.do("use torn note") == "You read Torn Note:\nThe cutters come at dusk."


def test_who_must_live_only_within_its_window():
    f = jar_form()
    f["must_live"][0].update({"from": 20, "to": 20, "main_message": False})
    g = jar_game(f)
    out = g.do("fight nesh-deeka win")
    assert "Quest failed" not in out and g.s["quests"][JQ]["ended"] is None
    f["must_live"][0]["from"] = 10
    assert "Quest failed: The Jar" in jar_game(f).do("fight nesh-deeka win")


def test_a_person_is_named_with_race_and_sex():
    g = jar_game()
    assert "Nesh-Deeka (an Argonian woman)" in g.look()
    assert g.do("talk nesh-deeka").startswith("Nesh-Deeka, an Argonian woman.")
    g.world["people"]["npc.keeper"] = {"race": "DarkElfRace", "sex": "male"}
    assert g.who("npc.keeper") == "a Dark Elf man"
    del g.world["people"]["npc.keeper"]
    assert g.who("npc.keeper") is None and "Nesh-Deeka (a person)" in g.look()


def test_the_world_database_says_who_a_person_is():
    from tools.playtest import world as W
    snap = W.from_db([templated()])
    assert snap["people"]["npc.nesh-deeka"] == {"race": "argonian", "sex": "female"}


def test_a_forms_name_wins_and_the_names_file_ids_are_listed(tmp_path):
    from tools.playtest import world as W
    f = tmp_path / "n.json"
    f.write_text(json.dumps({"names": {"npc.nesh-deeka": "From The File", "item.x": "Ring", "item.unused": "Cup"},
                             "places": {}}))
    form_ = templated(name="Nesh-Deeka")
    form_["refs"].append({"id": "thing.x", "kind": "thing", "enabled": True,
                          "placement": {"base": {"kind": "item", "id": "item.x"}}})
    snap = W.snapshot([form_], [f], use_db=False)
    assert snap["names"]["npc.nesh-deeka"] == "Nesh-Deeka" and snap["names"]["item.x"] == "Ring"
    assert snap["from_names_file"] == ["item.x"]
    folder, _ = new_session(tmp_path)
    assert set(S.write_run(folder)["names_from_file"]) == {
        "npc.example.roll-man", "door.example.hold", "npc.example.contact", "0A0100:Example.esp",
        "0A0200:Example.esp"}


def second_form():
    """The example opening, begun when the jar quest completes."""
    f = form()
    f["quest"].update(id="quest.test.after", editor_id="ARG_TestAfter", name="After the Jar",
                      start={"by": "quest_stage", "quest": JQ, "quest_stage": 90, "stage": 10})
    return f


def test_reach_reports_each_ending_and_where_paths_stop():
    from tools.playtest import walk
    rows = walk.reach([jar_form()], world=jar_world(jar_form()))
    ends = {s["stage"]: s["by"]["able"] for s in rows[0]["stages"]}
    assert ends[95] == ["fight Nesh-Deeka win"]
    assert ends[90] == ["take Lockpick", "pick Lockbox win", "take Sap Jar", "talk Nesh-Deeka", "say Here is the jar."]
    assert walk.unreached(rows) == []
    f = jar_form()
    f["refs"][2]["contents"] = []                       # the jar is gone: nothing reaches the ending
    rows = walk.reach([f], world=jar_world(f))
    assert "90 completed: NOT REACHED: able: no path reaches it; stages reached: 10" in walk.report(rows)
    assert any("ending 90 not reached" in b for b in walk.unreached(rows))


def test_the_reach_gate_holds_to_its_owed_list(tmp_path, monkeypatch):
    from tools.playtest import walk
    owed = tmp_path / "owed.json"
    owed.write_text(json.dumps({"quests": {"quest.a": "why"}}))
    monkeypatch.setattr(walk, "OWED", owed)
    assert walk.gate(["quest.a: no completed ending can be reached"]) == []
    assert walk.gate(["quest.b: no completed ending can be reached"]) == [
        "quest.b: no completed ending can be reached (and it is not on tools/playtest/reach_owed.json)",
        "quest.a now reaches a completed ending: take it off tools/playtest/reach_owed.json"]


# -- what a compiled form carries: places, texts, item ids, if_held, start_quest ------------------------------------

def compiled_jar_form():
    """The jar quest as the compiler writes it: the jar a unique thing of ours in the lockbox (its item id its ref
    id), the lockpicks a stock item by the story database's id, the note's words and the pier's name on the form."""
    f = jar_form()
    refs = {r["id"]: r for r in f["refs"]}
    refs["thing.box"]["contents"] = []
    refs["thing.note"].pop("text")
    refs["thing.picks"]["placement"] = {"base": {"kind": "item", "id": "item.lockpick"}}
    f["refs"].append({"id": "thing.jar", "kind": "thing", "enabled": True, "name": "Sap Jar",
                      "placement": {"base": {"kind": "item", "id": "thing.jar"}, "container": "thing.box"}})
    f["names"] = {"item.lockpick": "Lockpick"}
    f["texts"] = {"thing.note": "The cutters come at dusk."}
    f["places"] = {AT["cell"]: {"name": "Barge Pier", "interior": False}}
    for x in f["lines"][0]["conditions"] + f["stages"][2]["results"]:
        x["item"] = "thing.jar"
    f["triggers"] = [{"id": "take.thing.jar.10-20", "kind": "take", "ref": "thing.jar", "prerequisite": 10, "sets": 20},
                     {"id": "take.thing.jar.15-30", "kind": "take", "ref": "thing.jar", "prerequisite": 15, "sets": 30}]
    f["stages"].insert(2, {"number": 30, "shown": True, "journal": "Taken the other way.", "ending": "none",
                           "results": []})
    return f


def compiled_jar_game(f=None):
    from tools.playtest import world as W
    f = f or compiled_jar_form()
    snap = W.snapshot([f], use_db=False)
    g = G.Game([f], {**snap, "people": {}})
    g.begin(at="npc.keeper")
    return g


def test_a_compiled_forms_places_texts_and_names_need_no_names_file():
    from tools.playtest import world as W
    snap = W.snapshot([compiled_jar_form()], use_db=False)
    assert snap["places"][AT["cell"]] == {"name": "Barge Pier", "interior": False}
    assert snap["texts"] == {"thing.note": "The cutters come at dusk."} and snap["from_names_file"] == []
    g = compiled_jar_game()
    assert "You are at Barge Pier." in g.look()
    g.s["locked"]["thing.box"] = False
    g.do("use lockbox unseen")
    g.do("take torn note")
    assert g.do("use torn note") == "You read Torn Note:\nThe cutters come at dusk."


def test_takes_and_hand_ins_match_by_the_forms_item_id_and_one_take_fires_once():
    g = compiled_jar_game()
    assert g.do("take lockpick") == "Added: Lockpick" and g.s["items"] == {G.LOCKPICK: 1}     # stock by one id
    g.do("pick lockbox win unseen")
    out = g.do("take sap jar")
    assert "I have the jar." in out and g.s["items"]["thing.jar"] == 1
    assert g.s["quests"][JQ]["done"] == [10, 20]       # 15-30 opened only by the stage the take itself set
    g.do("talk nesh-deeka")
    assert "Quest completed: The Jar" in g.do("say here is the jar.") and "thing.jar" not in g.s["items"]


def test_if_held_moves_a_stage_on_only_when_the_thing_is_held():
    f = compiled_jar_form()
    f["stages"][1]["results"] = [{"do": "set_stage", "stage": 30, "if_held": "thing.jar"}]
    g = compiled_jar_game(f)
    g._set_stage(JQ, 20, None)
    assert g.stage(JQ) == 20
    g = compiled_jar_game(f)
    g.s["items"]["thing.jar"] = 1
    g._set_stage(JQ, 20, None)
    assert g.stage(JQ) == 30


def test_a_quest_started_by_another_forms_result_waits_on_it():
    from tools.playtest import walk
    first, after = jar_form(), second_form()
    after["quest"]["start"] = {"by": "start_quest", "stage": 10}
    first["stages"][2]["results"].append({"do": "start_quest", "quest": "quest.test.after", "stage": 10})
    forms = {JQ: first, "quest.test.after": after}
    assert walk.waits_on(after, forms) == {JQ} and walk.order("quest.test.after", forms) == [JQ, "quest.test.after"]


def test_a_session_starts_after_earlier_quests_with_their_state(tmp_path):
    paths = []
    for i, f in enumerate((jar_form(), second_form())):
        p = tmp_path / f"f{i}.json"
        p.write_text(json.dumps(f))
        paths.append(str(p))
    folder, screen = S.new(paths, names=[str(NAMES)], use_db=False, root=tmp_path / "runs", after=[JQ],
                           at="door.example.hold")
    sess = json.loads((folder / "session.json").read_text())
    st = sess["state"]
    assert st["quests"][JQ]["ended"] == "completed" and "quest.test.after" in st["quests"]
    assert st["commands"] == 0 and st["items"] == {G.LOCKPICK: 1}          # the jar was handed in
    assert st["crimes"] == [{"what": "pick Lockbox", "owner": "npc.keeper", "seen": False}]
    assert sess["know_text"] == ('What you know so far, from your journal: From "The Jar": Get the jar. I have '
                                 'the jar. She has the jar.')
    assert sess["after_path"][-1]["command"] == "say Here is the jar."
    assert screen.startswith("Your game goes on.") and folder.parent.name == "quest.test.after"
    bad = jar_form()
    bad["refs"][2]["contents"] = []
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(G.HarnessError, match="no completed ending reached"):

        S.new([str(p)], use_db=False, root=tmp_path / "runs", after=[JQ])


def test_every_command_counts_toward_the_limit_and_a_refusal_has_a_row(tmp_path):
    folder, _ = new_session(tmp_path)
    sess = json.loads((folder / "session.json").read_text())
    sess["max_commands"] = 3
    (folder / "session.json").write_text(json.dumps(sess))
    assert S.do(folder, "frobnicate", think="what happens")[0] == 0
    assert S.do(folder, "look", think="")[0] == 2                  # refused for a missing think: still counted
    assert S.do(folder, "look", think="I look")[0] == 0
    code, text = S.do(folder, "look", think="again")               # the limit
    assert code == 2 and "used all 3 commands" in text
    assert json.loads((folder / "session.json").read_text())["state"]["commands"] == 3
    rows = S.transcript(folder)
    assert [r["command"] for r in rows] == ["(new game)", "frobnicate", "look", "look", "look"]
    assert rows[2]["result"].startswith("Refused: every command needs --think")
    assert rows[4]["result"].startswith("You have used all 3 commands")
    assert S.write_run(folder)["counts"]["commands"] == 2


def _stream(n_tool_calls, extra=""):
    rows = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}}
            for _ in range(n_tool_calls)]
    rows.append({"type": "result", "result": extra or "done"})
    return "\n".join(json.dumps(r) for r in rows)


def test_the_probe_needs_five_tries_and_no_repo_text():
    from tools.playtest import runner
    assert runner.judge_probe(_stream(7))[0] is True
    ok, why = runner.judge_probe(_stream(4))
    assert ok is False and "4 tool calls" in why
    ok, why = runner.judge_probe(_stream(7, "Binding rules: ..."))
    assert ok is False and "repo" in why


def test_the_wrapper_passes_an_argument_through_as_one_literal():
    from tools.playtest import runner
    got = runner.wrapper_argv(["go $(cat /etc/hostname)"], "/s", py="py")
    assert got == ["py", "-m", "tools.playtest", "do", "/s", "go $(cat /etc/hostname)"]
    assert runner.wrapper_argv(["end", "--take", "x"], "/s", py="py")[3:] == ["end", "/s", "--ask-later", "--take", "x"]
    assert runner.wrapper_argv(["answers", "1. a", "2. b"], "/s", py="py")[-2:] == ["--answers", "1. a 2. b"]
    # `play 'end --take ...'` quoted whole is a take, its words split as text and never run
    assert runner.wrapper_argv(["end --take 'It was $(fun)'", "--think", "done"], "/s", py="py")[3:] == [
        "end", "/s", "--ask-later", "--take", "It was $(fun)", "--think", "done"]


def test_the_wrapper_script_is_python_without_a_shell(tmp_path):
    from tools.playtest import runner
    text = runner.wrapper(tmp_path).read_text()
    assert text.startswith("#!") and "/bin/sh" not in text and "os.execv" in text and '"$@"' not in text


def _fake(tmp_path, code, timeout=30):
    import sys

    from tools.playtest import runner
    return runner.run_claude([sys.executable, "-c", code], tmp_path / "s.jsonl", tmp_path, timeout=timeout)


def test_run_claude_says_why_it_stopped(tmp_path):
    ok = _fake(tmp_path, 'import json;print(json.dumps({"type":"result","subtype":"success","result":"fine"}))')
    assert ok["stopped"] == "result" and ok["subtype"] == "success"
    bad = _fake(tmp_path, 'import json;print(json.dumps({"type":"result","is_error":True,"result":"x"}))')
    assert bad["stopped"] == "error"
    api = _fake(tmp_path, 'import json;print(json.dumps({"type":"result","result":"API Error: 529"}))')
    assert api["stopped"] == "error"
    assert _fake(tmp_path, 'print("no json")')["stopped"] == "no result"
    assert _fake(tmp_path, "import time;time.sleep(60)", timeout=1)["stopped"] == "timeout"


def test_a_run_that_is_always_refused_keeps_its_last_attempt(tmp_path, monkeypatch):
    from tools.playtest import runner
    folders = []

    def attempt(*a):
        f = tmp_path / f"a{len(folders)}"
        f.mkdir()
        folders.append(f)
        return f, False

    monkeypatch.setattr(runner, "_attempt", attempt)
    got = runner.run([], "careful")
    assert got == folders[-1] and got.exists()
    assert len(folders) == runner.ATTEMPTS and not any(f.exists() for f in folders[:-1])
