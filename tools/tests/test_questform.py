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
    assert rules.check(f) == []
    line(f, "contact.work")["conditions"][-1]["skill"] = "speechcraft"
    assert rules.check(f)


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
