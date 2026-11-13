"""The designed-against-built comparison (tools/questform/diff.py) on the example opening with seeded differences."""
import copy
import json
from pathlib import Path

import pytest

from tools.questform import diff as D
from tools.questform.__main__ import main

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = json.loads((REPO / "tools/questform/examples/opening.json").read_text())
PLACES = {"place.example.sample-house": {"cells": ["0A0200:Example.esp"]}}


def built_from(designed):
    """The example as the plugin reader gives it back: the same form, each ref at its position."""
    return copy.deepcopy(designed)


def no_at(form, *ids):
    f = copy.deepcopy(form)
    for r in f["refs"]:
        if r["id"] in ids:
            del r["at"]
    return f


def run(designed, built, positions=None):
    res = D.Resolver(positions=positions or {"0A0020:Example.esp": {"cell": "0A0100:Example.esp", "interior": False,
                                                                      "x": 1100.0, "y": 2000.0, "z": 50.0}},
                     places=PLACES, use_db=False)
    return D.diff_form(designed, built, res)


def test_the_built_example_matches_its_design():
    assert run(EXAMPLE, built_from(EXAMPLE)) == []


def test_anchor_satisfied_within_the_named_distance():
    d = no_at(EXAMPLE, "npc.example.roll-man")
    b = built_from(EXAMPLE)
    man = next(r for r in b["refs"] if r["id"] == "npc.example.roll-man")
    man["at"]["x"] = 1100.0 + D.NEAR_UNITS - 1
    assert run(d, b) == []
    man["at"]["x"] = 1100.0 + D.NEAR_UNITS + 50
    out = run(d, b)
    assert len(out) == 1 and "ref npc.example.roll-man.placement.anchor" in out[0] and "near is 1024" in out[0]


def test_place_anchor_by_cell():
    b = built_from(EXAMPLE)
    next(r for r in b["refs"] if r["id"] == "npc.example.contact")["at"]["cell"] = "0A0300:Example.esp"
    out = run(no_at(EXAMPLE, "npc.example.contact"), b)
    assert len(out) == 1 and "not one of place.example.sample-house's cells" in out[0]


SEEDS = [
    (lambda f: f["stages"][1].__setitem__("journal", "Something else."), "stage 20.journal"),
    (lambda f: f["stages"][3].__setitem__("results", []), "stage 40.results"),
    (lambda f: f["objectives"][1].__setitem__("targets", ["npc.example.roll-man"]), "objective 20.targets"),
    (lambda f: f["lines"][2].__setitem__("text", "Different words."), "line contact.work.text"),
    (lambda f: f["lines"][2].__setitem__("conditions", [{"is": "gold_at_least", "gold": 5}]),
     "line contact.work.conditions"),
    (lambda f: f["lines"].pop(5), "line contact.no: designed only"),
    (lambda f: f["must_live"][0].__setitem__("main_message", False), "who-must-live npc.example.contact.main_message"),
    (lambda f: f["refs"][1]["at"].__setitem__("x", 1500.0), "ref door.example.hold.at"),
    (lambda f: f["refs"][0].__setitem__("hostile", True), "ref npc.example.roll-man.hostile"),
    (lambda f: f["triggers"].append({"id": "t", "kind": "use", "ref": "door.example.hold", "prerequisite": 10,
                                     "sets": 20}), "trigger t: built only"),
    (lambda f: f["quest"].__setitem__("kind", "minor"), "quest.kind"),
    (lambda f: f["refs"][1].__setitem__("lock", {"level": "novice"}), "ref door.example.hold.lock"),
    (lambda f: f["must_live"][0].__setitem__("from", 20), "who-must-live npc.example.contact.from"),
]


def test_an_anchor_the_census_cannot_place_is_measured_from_the_designs_spot():
    """A static anchor (no position known) compares the built spot with the design's `at`; with no `at` either, the
    anchor is not compared."""
    d = copy.deepcopy(EXAMPLE)
    man = next(r for r in d["refs"] if r["id"] == "npc.example.roll-man")
    man["placement"]["anchor"]["near"] = "0FFFFF:Static.esp"
    b = built_from(d)
    assert run(d, b) == []
    next(r for r in b["refs"] if r["id"] == "npc.example.roll-man")["at"]["x"] += 300
    assert run(d, b) == []
    next(r for r in b["refs"] if r["id"] == "npc.example.roll-man")["at"]["x"] += D.NEAR_UNITS
    assert len(run(d, b)) == 1
    del man["at"]
    assert run(d, b) == []


@pytest.mark.parametrize("seed,want", SEEDS, ids=[w for _, w in SEEDS])
def test_each_seeded_difference_is_named(seed, want):
    b = built_from(EXAMPLE)
    seed(b)
    out = run(EXAMPLE, b)
    assert len(out) == 1 and want in out[0], out


def test_lines_pair_by_what_they_are_when_ids_differ():
    b = built_from(EXAMPLE)
    for ln in b["lines"]:
        ln["id"] = "INFO_" + ln["id"]
    for ln in b["lines"]:
        ln["answers"] = ["INFO_" + a for a in ln["answers"]]
    assert run(EXAMPLE, b) == []


def test_the_command_exits_non_zero_on_a_difference(tmp_path, capsys):
    (tmp_path / "d").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "d" / "q.json").write_text(json.dumps(EXAMPLE))
    b = copy.deepcopy(EXAMPLE)
    (tmp_path / "b" / "q.json").write_text(json.dumps(b))
    assert main(["diff", str(tmp_path / "d"), str(tmp_path / "b")]) == 0
    b["stages"][0]["journal"] = "Changed."
    (tmp_path / "b" / "q.json").write_text(json.dumps(b))
    assert main(["diff", str(tmp_path / "d"), str(tmp_path / "b")]) == 1
    assert "stage 10.journal" in capsys.readouterr().out


def _ref(f, rid):
    return next(r for r in f["refs"] if r["id"] == rid)


def test_a_reordered_results_list_is_named():
    d = copy.deepcopy(EXAMPLE)
    d["stages"][3]["results"] = [{"do": "give_gold", "amount": 5}, {"do": "give_gold", "amount": 7}]
    b = copy.deepcopy(d)
    b["stages"][3]["results"].reverse()
    out = run(d, b)
    assert len(out) == 1 and "stage 40.results" in out[0]


def test_a_dropped_duplicate_result_is_named():
    d = copy.deepcopy(EXAMPLE)
    d["stages"][3]["results"] = [{"do": "give_gold", "amount": 5}, {"do": "give_gold", "amount": 5}]
    b = copy.deepcopy(d)
    b["stages"][3]["results"].pop()
    out = run(d, b)
    assert len(out) == 1 and "stage 40.results" in out[0]


def test_a_line_results_reorder_is_named():
    d = copy.deepcopy(EXAMPLE)
    d["lines"][2]["results"] = [{"do": "give_gold", "amount": 5}, {"do": "give_gold", "amount": 7}]
    b = copy.deepcopy(d)
    b["lines"][2]["results"].reverse()
    out = run(d, b)
    assert len(out) == 1 and "results" in out[0]


def test_a_person_built_far_from_its_designed_spot_is_named():
    b = built_from(EXAMPLE)
    _ref(b, "npc.example.roll-man")["at"]["x"] += 7000
    out = run(EXAMPLE, b)
    assert len(out) == 1 and "ref npc.example.roll-man.at" in out[0]
    _ref(b, "npc.example.roll-man")["at"]["x"] -= 7000 - D.PLACED_UNITS + 1
    assert run(EXAMPLE, b) == []


def test_a_person_built_in_another_interior_is_named():
    b = built_from(EXAMPLE)
    _ref(b, "npc.example.contact")["at"]["cell"] = "0A0300:Example.esp"
    out = run(EXAMPLE, b)
    assert len(out) == 1 and "ref npc.example.contact.at" in out[0] and "0A0300" in out[0]


def test_a_built_existing_placement_against_a_designed_new_one_is_named():
    b = built_from(EXAMPLE)
    _ref(b, "npc.example.roll-man")["placement"] = {"existing": "0B0001:Argonia.esp"}
    out = run(EXAMPLE, b)
    assert len(out) == 1 and "ref npc.example.roll-man.placement.base" in out[0]


def test_a_must_live_message_difference_is_named():
    d = copy.deepcopy(EXAMPLE)
    d["must_live"][0]["message"] = "Gone."
    b = copy.deepcopy(d)
    b["must_live"][0]["message"] = "Other."
    out = run(d, b)
    assert len(out) == 1 and "who-must-live npc.example.contact.message" in out[0]


def test_a_triggers_until_is_compared():
    d = copy.deepcopy(EXAMPLE)
    d["triggers"].append({"id": "t", "kind": "use", "ref": "door.example.hold", "prerequisite": 10, "sets": 20,
                          "until": 20})
    b = built_from(d)
    assert run(d, b) == []
    del b["triggers"][0]["until"]
    out = run(d, b)
    assert len(out) == 1 and "trigger t.until: designed 20, built null" in out[0]
