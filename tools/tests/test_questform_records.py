"""The quest form compiled from the eleven built quests' records (tools/questform): each rule of compiling that the
walk 6 lanes found broken, proved on the records that broke it, and the rules over a set of forms."""
import copy

import pytest

from tools.argonia_world import db
from tools.questform import compile as qc
from tools.questform import rules

ELEVEN = ["quest.main.mq01", "quest.main.mq03", "quest.main.mq04", "quest.main.mq05",
          "quest.tg.tg01", "quest.tg.tg02", "quest.local.lq25", "quest.local.lq30"]   # BC01 to BC03: being rewritten
DIVES = "npc.pirate-freeholds.opening-work-camp.n1-2"


@pytest.fixture(scope="module")
def world():
    return db.load()


@pytest.fixture(scope="module")
def forms(world):
    out = {}
    for q in ELEVEN:
        form, refused = qc.compile_quest(world, q)
        assert refused == [], (q, refused)
        out[q] = form
    return out


def lines_of(form, topic, stage=None):
    return [ln for ln in form["lines"] if ln["id"].startswith(topic + "@")
            and (stage is None or ln["first_stage"] <= stage <= ln["last_stage"])]


def ref(form, rid):
    return next(r for r in form["refs"] if r["id"] == rid)


# -- the eleven fit, alone and as a set ---------------------------------------------------------------------------
def test_the_eleven_compile_and_pass_alone_and_as_a_set(forms):
    for q, f in forms.items():
        assert rules.check(f) == [], q
    assert rules.check_set(list(forms.values())) == []


# -- 1. a check's failure has its own text -------------------------------------------------------------------------
def test_a_failed_check_says_its_own_words_and_a_gated_line_has_no_ungated_twin(forms):
    persuade = lines_of(forms["quest.main.mq03"], "topic.mq03-persuade", 10)
    passed = [ln for ln in persuade if ln["results"]]
    failed = [ln for ln in persuade if not ln["results"]]
    assert len(passed) == 1 and len(failed) == 1
    assert {"is": "skill_at_least", "skill": "Speech", "value": 25} in passed[0]["conditions"]
    assert failed[0]["conditions"] == [] and failed[0]["text"].startswith("Words cost nothing")
    assert failed[0]["text"] != passed[0]["text"] and failed[0]["prompt"] == passed[0]["prompt"]


def test_a_hand_in_with_no_other_check_falls_back_without_the_thing(forms):
    """A line whose only check is a thing held: its fallback is said without it (else it could never be said)."""
    ret = lines_of(forms["quest.tg.tg01"], "topic.tg01-return", 30)
    fallback = [ln for ln in ret if not ln["results"]]
    assert len(fallback) == 1 and not any(c["is"] == "item_count_at_least" for c in fallback[0]["conditions"])
    assert not [f for f in rules.check(forms["quest.tg.tg01"]) if f[0] == "line-said"]


def test_a_variant_the_form_does_not_carry_is_refused(world):
    c = qc.Compiler(world, "quest.tg.tg01")
    written = qc.written_lines("tg01")
    written["topic.tg01-after"]["infos"].append({"variant": "again", "lines": ["Back again."]})
    c._written = lambda code: written
    c.compile()
    assert any(t == "variant" and "topic.tg01-after" in w for t, w, _ in c.refused)


def test_a_fallback_that_could_never_be_said_is_refused(world):
    c = qc.Compiler(world, "quest.tg.tg01")
    for t in c.rec["topics"]:
        if t["id"] == "topic.tg01-his-habits":
            t["when"] = {"npcAlive": "npc.mercantile-coast.soulrest.tg01-thief"}
            t["fallback"] = "Not now."
    c.compile()
    assert any(t == "unsaid line" and "topic.tg01-his-habits" in w for t, w, _ in c.refused)


def test_an_objective_is_closed_when_a_fail_forward_moves_the_quest(forms):
    f = forms["quest.main.mq01"]
    first = next(o for o in f["objectives"] if o["shown_at"] == [10])
    assert 21 in first["completed_at"] and 20 in first["completed_at"]



def test_a_hand_in_fallback_keeps_holding_the_thing(forms):
    read = lines_of(forms["quest.main.mq03"], "topic.mq03-read-sap", 12)
    fallback = [ln for ln in read if not ln["results"]]
    assert fallback and all({"is": "item_count_at_least", "item": "thing.mq03.sap-jar", "count": 1}
                            in ln["conditions"] for ln in fallback)


def test_a_skill_check_with_no_fallback_is_refused(world):
    c = qc.Compiler(world, "quest.main.mq04")
    c._written = lambda code: {}             # no written lines (no `fail` info) and no fallback gist
    for t in c.rec["topics"]:
        t.pop("fallback", None)
    c.compile()
    assert any(t == "fallback" and "topic.mq04-persuade" in w for t, w, _ in c.refused)


def test_a_topic_gate_gates_a_line_that_moves_nothing(forms):
    give = lines_of(forms["quest.main.mq03"], "topic.mq03-give-jar")
    assert give and all({"is": "item_count_at_least", "item": "thing.mq03.sap-jar", "count": 1} in ln["conditions"]
                        for ln in give)


# -- 2. nothing placed is dropped -----------------------------------------------------------------------------------
def test_every_placement_row_is_a_ref(world, forms):
    for q, f in forms.items():
        rows = {r["ref"] for r in world.query("SELECT ref FROM quest_placement WHERE quest_id = ?", q)}
        assert {r["id"] for r in f["refs"]} == rows, q
    assert {"creature.mq05.wasp-1", "creature.mq05.wasp-2"} <= {r["id"] for r in forms["quest.main.mq05"]["refs"]}
    assert {"thing.mq04.gum-box", "thing.mq04.gum-pot"} <= {r["id"] for r in forms["quest.main.mq04"]["refs"]}


# -- 3. locks, owners, carried things, names and levels from the record ---------------------------------------------
def test_locks_owners_carried_things_names_and_levels(forms):
    mq03 = forms["quest.main.mq03"]
    box = ref(mq03, "thing.mq03.sack")
    assert box["lock"] == {"level": "novice", "key": "thing.mq03.sack-key"} and box["owner"] == DIVES
    assert box["name"] == "Dives-Without-A-Rope's Lockbox"
    assert ref(mq03, "thing.mq03.sack-key")["placement"]["carried_by"] == DIVES
    assert ref(mq03, "thing.mq03.sap-jar")["placement"]["base"]["kind"] == "template_item"
    assert ref(mq03, "thing.mq03.sap-jar")["name"] == "Cutters' Jar of Sap"
    assert ref(mq03, "thing.mq03.lockpicks")["count"] == 5
    assert mq03["names"]["thing.mq03.page"] == "Nesh-Deeka's Page" and "dry voice" in mq03["texts"]["thing.mq03.page"]
    assert ref(forms["quest.main.mq04"], "thing.mq04.gum-box")["lock"] == {"level": "novice"}
    tg01 = forms["quest.tg.tg01"]
    assert ref(tg01, "thing.tg01.strongbox")["owner"] == "npc.mercantile-coast.soulrest.tg01-thief"
    assert ref(tg01, "item.tg01.strongbox-key")["placement"]["carried_by"] == "npc.mercantile-coast.soulrest.tg01-thief"
    assert ref(forms["quest.tg.tg02"], "thing.tg02.lockbox")["lock"] == {"level": "novice"}
    croc = ref(forms["quest.local.lq25"], "creature-at.hist-heartland.helstrom.lq25-river-beast")
    assert (croc["name"], croc["level"]) == ("Crocodile", 1)
    for f in forms.values():      # the paper game needs no names file: every ref has the name the player sees
        assert all(r.get("name") for r in f["refs"] if r["kind"] != "marker"), f["quest"]["id"]


def test_a_new_item_without_a_name_and_a_level_on_a_thing_are_refused(forms):
    f = copy.deepcopy(forms["quest.main.mq03"])
    del ref(f, "thing.mq03.sap-jar")["name"]
    ref(f, "thing.mq03.sack")["level"] = 3
    assert {r for r, _ in rules.check(f)} == {"placement"}


# -- 4. items by one id ----------------------------------------------------------------------------------------------
def test_a_hand_in_and_a_take_name_one_item(forms):
    mq03 = forms["quest.main.mq03"]
    held = {c["item"] for ln in mq03["lines"] for c in ln["conditions"] if c["is"] == "item_count_at_least"}
    assert held == {"thing.mq03.sap-jar"}
    lq25 = forms["quest.local.lq25"]
    assert {c["item"] for ln in lq25["lines"] for c in ln["conditions"] if "item" in c} == {"thing.lq25.bait"}


def test_naming_a_unique_things_base_is_refused(world, forms):
    f = copy.deepcopy(forms["quest.main.mq03"])
    for ln in f["lines"]:
        for c in ln["conditions"]:
            if c.get("item") == "thing.mq03.sap-jar":
                c["item"] = "03EADD:Skyrim.esm"
    assert "item-id" in {r for r, _ in rules.check(f)}
    c = qc.Compiler(world, "quest.main.mq03")
    assert c.item("03EADD:Skyrim.esm", "x") == "03EADD:Skyrim.esm"
    assert [t for t, _, _ in c.refused] == ["item id"]
    assert c.item("thing.mq03.lockpicks", "x") == "item.lockpick"       # a stock thing by its base


# -- 5. who-must-live windows ----------------------------------------------------------------------------------------
def test_who_must_live_holds_from_the_first_shown_stage(forms):
    for q in ("quest.local.lq25", "quest.local.lq30"):
        f = forms[q]
        first = min(s["number"] for s in f["stages"] if s["shown"])
        assert all(m["from"] == first for m in f["must_live"]), q
        start = [ln for ln in f["lines"] if ln["first_stage"] == 0 and ln["results"]]
        assert start and all({"is": "alive", "ref": m["ref"]} in ln["conditions"]
                             for ln in start for m in f["must_live"]), "a death before the start leaves it unable to start"
    keeper = next(m for m in forms["quest.tg.tg01"]["must_live"] if m["ref"].endswith("keeper-harbour-den"))
    assert (keeper["from"], keeper["to"]) == (10, 30)
    f = copy.deepcopy(forms["quest.local.lq25"])
    del f["must_live"][0]["from"]
    assert {r for r, _ in rules.check(f)} == {"must-live-window"}


# -- 6. a thing already held ------------------------------------------------------------------------------------------
def test_a_thing_already_held_moves_the_quest_as_its_stage_begins(forms):
    mq04 = forms["quest.main.mq04"]
    s30 = next(s for s in mq04["stages"] if s["number"] == 30)
    assert {"do": "set_stage", "stage": 40, "if_held": "thing.mq04.sap-jars"} in s30["results"]
    f = copy.deepcopy(mq04)
    next(s for s in f["stages"] if s["number"] == 30)["results"] = []
    assert {r for r, _ in rules.check(f)} == {"held-take"}


# -- 7. the chain holds -----------------------------------------------------------------------------------------------
def test_the_chain_holds(forms):
    assert forms["quest.main.mq04"]["quest"]["start"] == {"by": "quest_stage", "quest": "quest.main.mq03",
                                                         "quest_stage": 90, "stage": 10}
    assert forms["quest.main.mq05"]["quest"]["start"] == {"by": "start_quest", "stage": 10}
    s20 = [ln for ln in forms["quest.main.mq05"]["lines"] if {"do": "set_stage", "stage": 20} in ln["results"]]
    assert [ln["speaker"] for ln in s20] == ["npc.nesh-deeka"]


def test_the_set_refuses_a_double_start_and_a_missing_quest(forms):
    fs = copy.deepcopy(list(forms.values()))
    mq05 = next(f for f in fs if f["quest"]["id"] == "quest.main.mq05")
    mq05["quest"]["start"] = {"by": "quest_stage", "quest": "quest.main.mq04", "quest_stage": 92, "stage": 10}
    got = rules.check_set(fs)
    assert {r for r, _ in got} == {"set-start"} and len(got) == 3
    fs = [f for f in fs if f["quest"]["id"] != "quest.main.mq03"]
    assert any(r == "set-stages" and "quest.main.mq03" in m for r, m in rules.check_set(fs))
    two = [f for f in fs if f["quest"]["id"] == "quest.tg.tg01"]
    tg02 = copy.deepcopy(forms["quest.tg.tg02"])
    s = next(s for s in two[0]["stages"] if s["number"] == 30)
    s["results"].append({"do": "start_quest", "quest": "quest.tg.tg02", "stage": 10})
    assert any(r == "set-start" and "can fire in one play" in m for r, m in rules.check_set(two + [tg02]))


# -- 9. an ending may change nothing in the world -------------------------------------------------------------------
def test_an_ending_with_no_world_imports():
    from tools.argonia_world.quest_record import export, import_record
    w = db.load()
    q = export(w, "quest.local.lq25")
    q["endings"][-1].pop("world", None)
    assert import_record(w, q) == [] and w.errors() == []


# -- 8. place names and interiors in the form --------------------------------------------------------------------------
def test_every_place_the_player_meets_is_named_in_the_form(forms):
    for q, f in forms.items():
        cells = {r["at"]["cell"] for r in f["refs"] if r.get("at")}
        assert cells <= set(f["places"]) and all(p["name"] for p in f["places"].values()), q
    assert forms["quest.tg.tg01"]["places"]["16BF81:Black Marsh North.esp"]["name"] == "The Night-Reed Chapter, Lilmoth"
    assert forms["quest.main.mq04"]["places"]["03978F:Black Marsh.esm"]["name"] == "Low-Reed Village"
    house = forms["quest.main.mq03"]["places"]["0FE7F7:Black Marsh.esm"]
    assert house["interior"] and "entrance" in house
    assert forms["quest.main.mq05"]["places"]["1562F8:Black Marsh.esm"]["name"]   # a door into a persistent cell
    assert ref(forms["quest.main.mq05"], "thing.mq05.landing-door")["at"]["cell"] == "0AA665:Black Marsh.esm"


# -- 9. a death that would come late closes with the step it replaces ----------------------------------------------
def trigger(form, tid):
    return next(t for t in form["triggers"] if t["id"] == tid)


def test_a_death_that_would_come_late_closes_with_the_step_it_replaces(forms):
    assert trigger(forms["quest.main.mq01"],
                   "death.npc.mercantile-coast.lilmoth.broker-buys-the-months.10-21")["until"] == 20
    assert trigger(forms["quest.main.mq04"], "death.npc.mercantile-coast.low-reed-village.root-herald.10-21")["until"] == 20
    assert trigger(forms["quest.main.mq03"], f"death.{DIVES}.10-13")["until"] == 12   # her talk, sale or refusal
    with_until = {"quest.main.mq01", "quest.main.mq03", "quest.main.mq04"}
    for q, f in forms.items():
        assert rules.late_triggers(rules.Form(f)) == {}, q
        assert q in with_until or all("until" not in t for t in f["triggers"]), q


def test_a_record_states_until_where_it_cannot_be_derived():
    w = db.load()
    row = next(r for r in w.rows("quest_fail_forward", quest_id="quest.main.mq01") if r.to == 21)
    w.update("quest_fail_forward", row.quest_id, row.stages_ord, row.ord, until=30)
    form, refused = qc.compile_quest(w, "quest.main.mq01")
    assert refused == []
    assert trigger(form, "death.npc.mercantile-coast.lilmoth.broker-buys-the-months.10-21")["until"] == 30
    w.update("quest_fail_forward", row.quest_id, row.stages_ord, row.ord, until=90)       # still open at stage 30
    form, refused = qc.compile_quest(w, "quest.main.mq01")
    assert form is None and [t for t, _, _ in refused] == ["late trigger"]


# -- 10. a key is not a theft: the giver lets the player have what the box holds -----------------------------------
def test_a_box_whose_key_is_given_becomes_the_players(forms):
    for q, box, given in (("quest.main.mq03", "thing.mq03.sack", (15, 16)),
                          ("quest.tg.tg01", "thing.tg01.strongbox", (21, 22))):
        for s in forms[q]["stages"]:
            gives = {"do": "give_ownership", "ref": box} in s["results"]
            assert gives is (s["number"] in given), (q, s["number"])
        assert ref(forms[q], box)["owner"]                     # stolen on every other way


# -- 11. a check the player can see coming ------------------------------------------------------------------------
def test_every_check_shows_its_label_and_no_threshold(forms):
    assert lines_of(forms["quest.main.mq04"], "topic.mq04-persuade", 20)[0]["prompt"].endswith(
        "Tell me what happened to your tree. (Persuade)")
    assert lines_of(forms["quest.main.mq05"], "topic.mq05-tell-minder", 45)[0]["prompt"].endswith("(Persuade)")
    for q, f in forms.items():
        for ln in f["lines"]:
            assert not any(k == "threshold" for k, _, _ in rules.prompt_labels(ln["prompt"])), (q, ln["id"])
            for c in rules.checks(ln["conditions"]):
                assert c in {(k, v) for k, v, _ in rules.prompt_labels(ln["prompt"])}, (q, ln["id"])
