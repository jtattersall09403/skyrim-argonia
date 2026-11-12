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
