"""The quest form (tools/questform): the schema, each structural rule on a broken copy of the example, the compiler."""
import json
from pathlib import Path

import pytest

from tools.questform import compile as qc
from tools.questform import rules, validate

EXAMPLE = Path(__file__).resolve().parents[1] / "questform" / "examples" / "opening.json"


def example():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def stage(f, n):
    return next(s for s in f["stages"] if s["number"] == n)


def line(f, i):
    return next(ln for ln in f["lines"] if ln["id"] == i)


def failed_rules(f):
    return {r for r, _ in rules.check(f)}


def test_example_passes():
    assert rules.check(example()) == []


def no_journal(f):
    stage(f, 20)["journal"] = ""


def target_off(f):
    next(r for r in f["refs"] if r["id"] == "npc.example.contact")["enabled"] = False


def switch_beside_speaker(f):
    stage(f, 20)["results"].append({"do": "switch_off", "ref": "npc.example.roll-man"})


def switch_on_a_death(f):
    stage(f, 90)["results"].append({"do": "switch_off", "ref": "door.example.hold"})


def kill_a_bystander(f):
    f["triggers"].append({"id": "death.roll-man", "kind": "death", "ref": "npc.example.roll-man",
                          "prerequisite": 10, "sets": 20})


def ungated_hand_in(f):
    line(f, "contact.yes")["results"].append({"do": "take_item", "item": "item.example.letter", "count": 1})


def offer_outlives_ending(f):
    line(f, "contact.ask")["last_stage"] = 40


def speaks_first_alone(f):
    f["lines"] = [ln for ln in f["lines"] if ln["id"] != "roll-man.roll"]


def too_many_results(f):
    stage(f, 40)["results"] += [{"do": "give_gold", "amount": 1}] * rules.MAX_STAGE_RESULTS


def minor_with_message(f):
    f["quest"]["kind"] = "minor"


@pytest.mark.parametrize("breaks, rule", [
    (no_journal, "journal-text"),
    (minor_with_message, "main-message"),
    (too_many_results, "result-limits"),
    (target_off, "objective-target-on"),
    (switch_beside_speaker, "away"),
    (switch_on_a_death, "switch-cause"),
    (kill_a_bystander, "death-hostile"),
    (ungated_hand_in, "hand-in"),
    (offer_outlives_ending, "line-window"),
    (speaks_first_alone, "speaks-first-has-line"),
])
def test_each_broken_copy_fails_exactly_its_rule(breaks, rule):
    f = example()
    breaks(f)
    assert failed_rules(f) == {rule}
    assert rule in rules.RULES


def test_vocabularies_are_closed():
    f = example()
    stage(f, 40)["results"].append({"do": "move_player", "ref": "door.example.hold"})
    line(f, "contact.work")["conditions"].append({"is": "time_of_day", "value": "night"})
    got = rules.check(f)
    assert {r for r, _ in got} == {"vocabulary"} and len(got) == 2
    assert any("unknown word 'move_player'" in m for _, m in got)


def test_nothing_else_may_appear():
    f = example()
    f["scenes"] = []
    f["refs"][0]["package"] = "walk"
    got = validate.errors(f)
    assert len(got) == 2 and all("is not a field of the form" in e for e in got)


def test_unreachable_stage_and_dead_end():
    f = example()
    f["stages"].append({"number": 50, "shown": False, "journal": None, "ending": "none", "results": []})
    assert failed_rules(f) == {"way-out", "reachable"}


def test_lines_and_refs_must_exist():
    f = example()
    line(f, "contact.ask")["answers"].append("contact.maybe")
    f["objectives"][0]["targets"].append("npc.example.nobody")
    assert failed_rules(f) == {"refs-exist"}


def test_compiles_a_record_once_its_people_are_placed():
    from tools.argonia_world import db
    w = db.load()
    qid = "quest.local.lq25"
    w.delete("quest_placement", quest_id=qid)
    c = qc.Compiler(w, qid)
    c.compile()
    assert {t for t, _, _ in c.refused} == {"placement"}
    for i, r in enumerate(sorted(c.used_refs)):
        w.insert("quest_placement", {"quest_id": qid, "ord": i, "ref": r, "enabled": True,
                                     "kind": "person" if r.startswith(("npc", "creature")) else "thing",
                                     "base_kind": "existing_base", "base": "000001:Example.esp", "place": "p",
                                     "rule": "navmesh", "cell": f"cell{i}", "x": 0.0, "y": 0.0, "z": 0.0,
                                     "interior": True})
    form, refused = qc.compile_quest(w, qid)
    assert refused == [] and form is not None
    assert validate.errors(form) == []
    assert form["quest"]["editor_id"] == "ARG_LQ25"


def test_an_objective_may_name_several_targets():
    """A record objective's `target` "a, b" is one marker on each (the form's targets list)."""
    from tools.argonia_world import db
    w = db.load()
    qid = "quest.local.lq25"
    two = "npc.hist-heartland.helstrom.lq25-crew-poler, npc.hist-heartland.helstrom.boat-captain"
    c = qc.Compiler(w, qid)
    obj = next(o for s in c.rec["stages"] for o in s.get("objectives") or [])
    obj["target"] = two
    form = c.compile()
    assert {"npc.hist-heartland.helstrom.lq25-crew-poler", "npc.hist-heartland.helstrom.boat-captain"} <= set(c.used_refs)
    if form is not None:
        assert form["objectives"][0]["targets"] == [t.strip() for t in two.split(",")]


# -- a lock, an owner, a carried thing, a container's contents, Skyrim's skill names --------------------------------

def chest(**kw):
    return {"id": "thing.example.chest", "kind": "thing", "enabled": True,
            "placement": {"base": {"kind": "existing_base", "id": "09424C:Skyrim.esm"},
                          "anchor": {"near": "0A0020:Example.esp", "rule": "surface"}},
            "at": {"cell": "0A0100:Example.esp", "interior": False, "x": 1050.0, "y": 2000.0, "z": 50.0}, **kw}


def carried(holder="npc.example.contact", **kw):
    return {"id": "thing.example.pouch", "kind": "thing", "enabled": True,
            "placement": {"base": {"kind": "item", "id": "00000A:Skyrim.esm"}, "carried_by": holder}, **kw}


def with_refs(*refs, door=None, contact=None):
    f = example()
    f["refs"] += list(refs)
    for ref, change in (("door.example.hold", door), ("npc.example.contact", contact)):
        if change:
            next(r for r in f["refs"] if r["id"] == ref).update(change)
    return f


LOCKED_OWNED = {"lock": {"level": "key", "key": "10BEFF:Skyrim.esm"}, "owner": "npc.example.contact",
                "contents": [{"item": "00000F:Skyrim.esm", "count": 50}, {"item": "item.example.letter", "count": 1}]}


def test_the_new_fields_pass():
    assert rules.check(with_refs(chest(**LOCKED_OWNED), carried(), door={"lock": {"level": "master"}})) == []
    assert rules.check(with_refs(chest(owner="faction.example"))) == []
    assert rules.check(with_refs(chest(contents=[]))) == []


@pytest.mark.parametrize("make, rule", [
    (lambda: with_refs(door={"lock": {"level": "impossible"}}), "schema"),
    (lambda: with_refs(chest(contents=[{"item": "x", "count": 0}])), "schema"),
    (lambda: with_refs(chest(lock={"level": "key", "key": "npc.example.contact"})), "lock"),
    (lambda: with_refs(contact={"lock": {"level": "novice"}}), "lock"),
    (lambda: with_refs(chest(owner="door.example.hold")), "owner"),
    (lambda: with_refs(door={"owner": "npc.example.contact"}), "owner"),
    (lambda: with_refs(chest(contents=[{"item": "npc.example.contact", "count": 1}])), "contents"),
    (lambda: with_refs(door={"contents": []}), "contents"),
    (lambda: with_refs(carried("door.example.hold")), "placement"),
    (lambda: with_refs(carried() | {"placement": {**carried()["placement"], "container": "thing.example.chest"}}, chest()), "placement"),
    (lambda: with_refs(carried("npc.example.nobody")), "refs-exist"),
])
def test_each_broken_new_field_fails_its_rule(make, rule):
    f = make()
    assert rule in failed_rules(f), rules.check(f)


def test_skills_are_skyrims_names_only():
    f = example()
    line(f, "contact.work")["conditions"].append({"is": "skill_at_least", "skill": "Speech", "value": 5})
    line(f, "contact.work")["prompt"] += " (Persuade)"
    assert rules.check(f) == []
    line(f, "contact.work")["conditions"][-1]["skill"] = "speechcraft"
    assert rules.check(f)


# -- a check the player can see coming: its label on the prompt -------------------------------------------------------

def _checked(f, *conds, prompt="I was told you have work."):
    line(f, "contact.work")["conditions"] = list(conds)
    line(f, "contact.work")["prompt"] = prompt
    return f


SPEECH = {"is": "skill_at_least", "skill": "Speech", "value": 25}
ALCHEMY = {"is": "skill_at_least", "skill": "Alchemy", "value": 25}
GOLD = {"is": "gold_at_least", "gold": 20}


@pytest.mark.parametrize("conds, prompt, ok", [
    ((SPEECH,), "I was told you have work. (Persuade)", True),
    ((SPEECH,), "(Intimidate) I was told you have work.", True),
    ((ALCHEMY,), "(Alchemy) I was told you have work.", True),
    ((SPEECH, GOLD), "I was told you have work. (Persuade) (20 gold)", True),
    ((), "I was told you have work. (from the docks)", True),          # brackets that are no label
    ((SPEECH,), "I was told you have work.", False),                   # no label
    ((SPEECH,), "I was told you have work. (Speech 25)", False),       # a threshold shown
    ((ALCHEMY,), "I was told you have work. (Persuade)", False),       # another check's label
    ((GOLD,), "I was told you have work. (30 gold)", False),           # another amount
    ((), "I was told you have work. (Persuade)", False),               # a label with no check
])
def test_a_check_is_labelled_on_its_prompt_as_skyrim_does(conds, prompt, ok):
    f = _checked(example(), *conds, prompt=prompt)
    assert (failed_rules(f) == set()) is ok and failed_rules(f) <= {"check-label"}


def test_a_fallback_shares_its_checks_label():
    f = _checked(example(), SPEECH, prompt="I was told you have work. (Persuade)")
    f["lines"].insert(3, {**line(f, "contact.work"), "id": "contact.work.fail", "conditions": [], "results": [],
                          "text": "Not for you."})
    assert rules.check(f) == []


def test_the_compiler_appends_a_missing_label_and_keeps_one_written():
    assert rules.labelled("Hear me out.", [("skill", "Speech")]) == "Hear me out. (Persuade)"
    assert rules.labelled("(Persuade) Hear me out.", [("skill", "Speech")]) == "(Persuade) Hear me out."
    assert rules.labelled("Buy it.", [("skill", "Restoration"), ("gold", 50)]) == "Buy it. (Restoration) (50 gold)"
    assert rules.labelled("Swing.", [("skill", "OneHanded")]) == "Swing. (One-handed)"


# -- a trigger that would come late: until --------------------------------------------------------------------------

def _late_death(f, until=None):
    """The roll-man's death as a step that replaces speaking to him: stage 25, open from stage 10."""
    f["stages"].insert(2, {"number": 25, "shown": True, "ending": "none", "results": [],
                           "journal": "The man with the roll is dead. I'm to find Sample-Contact in Lilmoth."})
    f["objectives"][0]["completed_at"].append(25)
    f["objectives"][1]["shown_at"].append(25)
    line(f, "contact.work")["last_stage"] = 25
    t = {"id": "death.roll-man", "kind": "death", "ref": "npc.example.roll-man", "prerequisite": 10, "sets": 25,
         "choice": True}
    f["triggers"].append(t | ({"until": until} if until is not None else {}))
    return f


def test_a_trigger_the_quest_can_pass_while_it_is_open_needs_until():
    late = rules.check(_late_death(example()))
    assert [r for r, _ in late] == ["late-trigger"] and "once the quest is at stage 30" in late[0][1]
    assert rules.check(_late_death(example(), until=20)) == []
    assert rules.late_triggers(rules.Form(_late_death(example(), until=20))) == {}
    assert failed_rules(_late_death(example(), until=10)) == {"late-trigger", "reachable"}    # never open


def test_a_trigger_whose_stage_still_comes_next_needs_no_until():
    f = _late_death(example())
    f["triggers"][0]["sets"] = 20                   # the death sets the step it replaces: always next
    f["stages"] = [s for s in f["stages"] if s["number"] != 25]
    f["objectives"][0]["completed_at"].remove(25)
    f["objectives"][1]["shown_at"].remove(25)
    line(f, "contact.work")["last_stage"] = 20
    assert rules.check(f) == []


# -- a key is not a theft: what a giver lets the player have ----------------------------------------------------------

def test_give_ownership_names_an_owned_thing_with_a_reference():
    f = with_refs(chest(owner="npc.example.contact"))
    stage(f, 30)["results"].append({"do": "give_ownership", "ref": "thing.example.chest"})
    assert "owner" not in failed_rules(f) and "created" not in failed_rules(f)
    f = with_refs(chest())
    stage(f, 30)["results"].append({"do": "give_ownership", "ref": "thing.example.chest"})
    assert "owner" in failed_rules(f)
    made = carried(owner="npc.example.contact") | {
        "placement": {"base": carried()["placement"]["base"], "container": "thing.example.chest"}}
    f = with_refs(chest(owner="npc.example.contact"), made)
    stage(f, 30)["results"].append({"do": "give_ownership", "ref": made["id"]})
    assert "created" in failed_rules(f)


@pytest.mark.parametrize("word, skill", [("Speechcraft", "Speech"), ("mercantile", "Speech"), ("security", "Lockpicking"),
                                         ("sneak", "Sneak"), ("pickpocket", "Pickpocket"), ("marksman", "Archery"),
                                         ("short-blade", "OneHanded"), ("spear", "TwoHanded"), ("skill.Heavy Armor", "HeavyArmor"),
                                         ("OneHanded", "OneHanded"), ("armorer", "Smithing")])
def test_a_records_skill_names_map_to_skyrims(word, skill):
    assert qc.skill_of(word) == skill
    assert skill in validate.SCHEMA["$defs"]["skill"]["enum"]


def test_an_unknown_skill_is_refused_and_a_known_one_is_mapped():
    from tools.argonia_world import db
    c = qc.Compiler(db.load(), "quest.local.lq25")
    assert c.gate({"skillAtLeast": ["speechcraft", 25]}, "x") == [{"is": "skill_at_least", "skill": "Speech", "value": 25}]
    assert c.gate({"skillAtLeast": ["mysticism", 25]}, "x") == []
    assert [t for t, _, _ in c.refused] == ["skillAtLeast"]


def test_the_compiler_names_what_the_player_sees():
    from tools.argonia_world import db
    w = db.load()
    c = qc.Compiler(w, "quest.local.lq25")
    person = {"id": "p", "kind": "person"}
    c._name(person, {"form_key": "00AC8E:Black Marsh.esm", "base": None})
    assert person["name"] == "Reads-The-Shallows"
    thing = {"id": "t", "kind": "thing"}
    c._name(thing, {"form_key": None, "base": "item.alto-wine"})
    assert thing["name"] == "Alto Wine"
    door = dict(w.query("SELECT d.id FROM bmv_door d JOIN bmv_door t ON t.id = d.target JOIN bmv_cell c ON c.id = t.cell "
                        "WHERE c.name IS NOT NULL LIMIT 1")[0])
    o = {"id": "d", "kind": "door"}
    c._name(o, {"form_key": door["id"], "base": None})
    assert o["name"] and o["destination"]
    form = {"refs": [{"id": "r", "placement": {"base": {"kind": "item", "id": "item.alto-wine"}}}], "stages": [],
            "lines": [{"results": [{"do": "give_item", "item": "item.alto-wine", "count": 1}], "conditions": []}]}
    assert c.item_names(form) == ({"item.alto-wine": "Alto Wine"}, {})


# -- the builder's refusals and the engine's facts, as rules (code review C1) --------------------------------------

def _set_lower(f):
    line(f, "contact.ask")["results"] = [{"do": "set_stage", "stage": 20}]


def _two_deaths(f):
    f["triggers"] = [{"id": f"death.c.{p}", "kind": "death", "ref": "npc.example.contact", "prerequisite": p,
                      "sets": 40, "choice": True} for p in (20, 30)]


def _two_speak_first(f):
    f["lines"].append({**line(f, "roll-man.first"), "id": "roll-man.first.2"})


def _orphan_answer(f):
    line(f, "contact.ask")["answers"] = ["contact.yes"]


def _no_prompt(f):
    line(f, "contact.work")["prompt"] = None


def _door_speaks(f):
    line(f, "contact.after")["speaker"] = "door.example.hold"


def _hostile_existing(f):
    next(r for r in f["refs"] if r["id"] == "door.example.hold")["hostile"] = True


def _shadowed(f):
    f["lines"].insert(3, {**line(f, "contact.work"), "id": "contact.work.2", "text": "Never said."})


def _regard(f):
    line(f, "contact.work")["results"].append({"do": "change_regard", "ref": "npc.example.contact", "by": 10})


def _left(f):
    f["objectives"][1]["completed_at"] = []


@pytest.mark.parametrize("breaks,rule", [(_set_lower, "stage-order"), (_two_deaths, "trigger"),
                                         (_two_speak_first, "speaks-first"), (_orphan_answer, "answer"),
                                         (_no_prompt, "prompt"), (_door_speaks, "speaker"),
                                         (_hostile_existing, "hostile"), (_shadowed, "line-said"),
                                         (_regard, "regard-range"), (_left, "objective-left")])
def test_each_builder_and_engine_rule(breaks, rule):
    f = example()
    breaks(f)
    assert rule in failed_rules(f)


def test_the_row_limit_counts_rows_as_the_builder_does():
    f = example()
    n = rules.built_rows(rules.Form(f))
    # the start check 1; results 1; objectives completed 3 and shown 3; SetActive 1; each ending: closing, Stop
    assert n == 1 + 1 + 6 + 1 + 2 + 2
    stage(f, 20)["results"] = [{"do": "give_gold", "amount": 1}] * (rules.MAX_STAGE_RESULTS - n + 1)
    assert "result-limits" in failed_rules(f)
