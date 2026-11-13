"""The paper game against the engine (code review C1): each place the paper game was more forgiving than Skyrim, or
showed a wrong result, as a small made case on the example opening."""
import json
from pathlib import Path

import pytest

from tools.playtest import game as G
from tools.playtest import walk

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = REPO / "tools/questform/examples/opening.json"
NAMES = json.loads((REPO / "tools/playtest/examples/opening.names.json").read_text())
CONTACT, DOOR, BOSS, Q = "npc.example.contact", "door.example.hold", "npc.example.roll-man", "quest.example.opening"
HOUSE = {"cell": "0A0200:Example.esp", "interior": True, "x": 0.0, "y": 0.0, "z": 0.0}


def form():
    return json.loads(EXAMPLE.read_text())


def line(i, speaker=CONTACT, prompt="Probe", first=10, last=40, conditions=(), results=(), kind="topic", text=None):
    return {"id": i, "speaker": speaker, "kind": kind, "prompt": prompt, "text": text or f"Line {i}.", "written": True,
            "conditions": list(conditions), "results": list(results), "first_stage": first, "last_stage": last,
            "answers": []}


def game(f=None, doors=None, names=None, at=DOOR, begin=True):
    w = {"names": {**NAMES["names"], **(names or {})}, "places": NAMES["places"], "talkers": [],
         "doors": doors or {}}
    g = G.Game([f or form()], w)
    if begin:
        g.begin(at=at)
    return g


def done(g, q=Q):
    return g.s["quests"][q]["done"]


# -- H1: `not` turns a condition round ---------------------------------------------------------------------------

@pytest.mark.parametrize("cond", [{"is": "race_is", "value": "Argonian"}, {"is": "alive", "ref": CONTACT},
                                  {"is": "dead", "ref": CONTACT}, {"is": "gold_at_least", "gold": 1},
                                  {"is": "stage_done", "quest": Q, "stage": 10}])
def test_not_gives_the_opposite_answer(cond):
    g = game()
    assert g.holds(Q, [cond], None) != g.holds(Q, [{**cond, "not": True}], None)


# -- H2: a stage already done is never set again ------------------------------------------------------------------

def test_a_done_stage_is_not_set_again_nor_its_results_run():
    f = form()
    f["stages"][1]["results"] = [{"do": "give_gold", "amount": 100}]
    f["lines"].append(line("again", speaker=BOSS, first=10, last=30, results=[{"do": "set_stage", "stage": 20}]))
    g = game(f)
    g.do("talk gang boss")
    g.do("say probe")
    g.do("talk gang boss")
    out = g.do("say probe")
    assert g.s["gold"] == 100 and "Journal entry" not in out


def test_setting_a_done_stage_from_a_later_one_moves_nothing():
    f = form()
    f["lines"].append(line("back", first=30, last=30, results=[{"do": "set_stage", "stage": 20}]))
    g = game(f)
    g._set_stage(Q, 20, None)
    g._set_stage(Q, 30, None)
    g.do("go sample-contact")
    g.do("talk sample-contact")
    g.do("say probe")
    assert g.stage(Q) == 30 and "Will you take me in?" in g.do("talk sample-contact")


def test_a_start_quest_said_twice_does_not_restart_the_quest():
    f = form()
    f["lines"].append(line("again", speaker=BOSS, results=[{"do": "start_quest", "quest": Q, "stage": 10}]))
    g = game(f)
    g._set_stage(Q, 20, None)
    g.do("talk gang boss")
    g.do("say probe")
    assert g.stage(Q) == 20 and done(g) == [10, 20]


# -- H4: a trigger is open while its prerequisite is done and its stage is not -------------------------------------

def thing_form(pre, sets, extra_stages=()):
    f = form()
    f["stages"][2:2] = [{"number": n, "shown": False, "journal": None, "ending": "none", "results": []}
                        for n in extra_stages]
    f["refs"].append({"id": "thing.ring", "kind": "thing", "enabled": True,
                      "placement": {"base": {"kind": "item", "id": "item.ring"},
                                    "anchor": {"near": "0A0020:Example.esp", "rule": "surface"}},
                      "at": {"cell": "0A0100:Example.esp", "interior": False, "x": 1200.0, "y": 2000.0, "z": 50.0}})
    f["triggers"] = [{"id": "take.ring", "kind": "take", "ref": "thing.ring", "prerequisite": pre, "sets": sets}]
    return f


def test_a_trigger_whose_prerequisite_was_skipped_never_fires():
    g = game(thing_form(15, 40, extra_stages=[15]), names={"thing.ring": "Ring", "item.ring": "Ring"})
    g._set_stage(Q, 20, None)
    g.do("take ring")
    assert 40 not in done(g)


def test_a_trigger_fires_late_when_its_stage_was_skipped():
    g = game(thing_form(10, 15, extra_stages=[15]), names={"thing.ring": "Ring", "item.ring": "Ring"})
    g._set_stage(Q, 20, None)
    g.do("take ring")
    assert 15 in done(g) and g.stage(Q) == 20


# -- H5, H6: locked doors --------------------------------------------------------------------------------------

def test_go_does_not_pass_a_locked_door():
    f = form()
    f["refs"][1]["lock"] = {"level": "key", "key": "item.key"}
    g = game(f, doors={DOOR: HOUSE}, names={"item.key": "Hold Key"})
    out = g.do("go sample-contact")
    assert "locked" in out and g.s["pos"]["cell"] != HOUSE["cell"]
    g.s["items"]["item.key"] = 1
    assert "Sample House" in g.do("go sample-contact")


def test_a_door_a_result_unlocks_starts_locked():
    f = form()
    f["stages"][2]["results"] = [{"do": "unlock_door", "ref": DOOR}]
    g = game(f, doors={DOOR: HOUSE})
    assert "opens only with its key" in g.do("use barge hold door")
    g._set_stage(Q, 20, None)
    g._set_stage(Q, 30, None)
    assert "You go through Barge Hold Door" in g.do("use barge hold door")


# -- H7, W1: answers by their window, one entry per prompt ---------------------------------------------------------

def test_answers_respect_their_window_and_are_not_duplicated():
    f = form()
    f["lines"][4]["first_stage"] = f["lines"][4]["last_stage"] = 20            # "I will serve." only at 20
    f["lines"].insert(5, {**f["lines"][5], "id": "contact.no.2"})               # a second "Not yet."
    f["lines"][3]["answers"] = ["contact.yes", "contact.no", "contact.no.2"]
    g = game(f)
    for n in (20, 30):
        g._set_stage(Q, n, None)
    g.do("go sample-contact")
    g.do("talk sample-contact")
    out = g.do("say will you take me in?")
    assert "I will serve." not in out and out.count("Not yet.") == 1


# -- H10: a death before the quest starts --------------------------------------------------------------------------

def test_a_must_live_person_dead_before_the_start_fails_the_quest_as_it_starts():
    g = game(begin=False)
    g.s["pos"] = dict(g._pos(DOOR))
    g.kill(CONTACT)
    out = "\n".join(g._set_stage(Q, 10, None))
    assert "Quest failed" in out and 90 in done(g)


# -- W2: stacks ---------------------------------------------------------------------------------------------------

def test_a_placed_stack_and_a_containers_row_are_taken_whole():
    f = thing_form(10, 20)
    f["refs"][-1]["placement"]["base"]["id"] = G.LOCKPICK
    f["refs"][-1]["count"] = 5
    f["triggers"] = []
    g = game(f, names={"thing.ring": "Lockpick"})
    assert "x5" in g.do("take lockpick") and g.s["items"][G.LOCKPICK] == 5


# -- W4: the faction quest's message -------------------------------------------------------------------------------

def test_a_faction_quests_death_shows_the_factions_message():
    f = form()
    f["quest"]["kind"] = "faction"
    g = game(f)
    out = "\n".join(g.kill(CONTACT))
    assert G.MESSAGES["faction"] in out and G.MESSAGES["main"] not in out


# -- W5: a greeting counts as having spoken ------------------------------------------------------------------------

def test_the_first_greeting_makes_spoken_before_true():
    f = form()
    f["lines"] += [line("hi.new", kind="greeting", prompt=None, text="Who are you?",
                        conditions=[{"is": "not_spoken_before"}]),
                   line("hi.again", kind="greeting", prompt=None, text="You again.",
                        conditions=[{"is": "spoken_before"}])]
    g = game(f)
    g.do("go sample-contact")
    assert "Who are you?" in g.do("talk sample-contact")
    assert "You again." in g.do("talk sample-contact")


# -- H13: regard is kept between -4 and 4 --------------------------------------------------------------------------

def test_regard_is_clamped():
    f = form()
    f["stages"][1]["results"] = [{"do": "change_regard", "ref": CONTACT, "by": 4},
                                 {"do": "change_regard", "ref": CONTACT, "by": 4}]
    g = game(f)
    g._set_stage(Q, 20, None)
    assert g.s["regard"][CONTACT] == 4


# -- W3: how a player knew where to go -----------------------------------------------------------------------------

def test_go_says_how_the_target_was_known():
    g = game()
    g.do("go gang boss")
    assert g.summary()["travel"] == "in sight"
    g.do("go sample-contact")
    assert g.summary()["travel"] == "marker"
    g.do("go gang boss")
    assert g.summary()["travel"] == "known place"
    g.s["quests"][Q]["shown"], g.s["visited"] = [], []
    g.do("go sample-contact")
    assert g.summary()["travel"] == "name only"


# -- L5: every command counts --------------------------------------------------------------------------------------

def test_an_unknown_command_counts():
    g = game()
    n = g.s["commands"]
    g.do("dance wildly")
    assert g.s["commands"] == n + 1


# -- the walker ----------------------------------------------------------------------------------------------------

def test_the_walker_reaches_a_person_named_dead_by_a_condition():
    """A player can kill anyone: a line that needs a person dead is reached though nothing marks him fightable."""
    f = form()
    f["lines"].append(line("dead", speaker=BOSS, first=20, last=20, conditions=[{"is": "dead", "ref": CONTACT}],
                           results=[{"do": "set_stage", "stage": 40}]))
    f["must_live"] = []
    f["stages"] = [s for s in f["stages"] if s["number"] != 90]
    f["lines"][4]["results"] = []                       # only the line that needs him dead completes it

    rows = walk.reach([f], world={"names": NAMES["names"], "places": NAMES["places"], "talkers": [], "doors": {}})
    assert not walk.unreached(rows)


def test_the_walker_takes_a_readable_thing():
    f = thing_form(20, 30)
    f["refs"][-1]["text"] = "A note."
    f["stages"][2]["results"] = []
    f["lines"][2]["results"] = []                       # only the take moves the quest on from 20
    w = {"names": {**NAMES["names"], "thing.ring": "Note", "item.ring": "Note"}, "places": NAMES["places"],
         "talkers": [], "doors": {}}
    rows = walk.reach([f], world=w)
    assert not [b for b in walk.unreached(rows)]


def test_reach_names_a_stage_no_path_reaches():
    f = form()
    f["stages"].insert(3, {"number": 35, "shown": False, "journal": None, "ending": "none", "results": []})
    f["triggers"] = [{"id": "quest_stage.x", "kind": "quest_stage", "quest": Q, "quest_stage": 99,
                      "prerequisite": 30, "sets": 35}]
    rows = walk.reach([f], world={"names": NAMES["names"], "places": NAMES["places"], "talkers": [], "doors": {}})
    assert any("stage 35" in b for b in walk.unreached(rows))
