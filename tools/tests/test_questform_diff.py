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
    """The example as a plugin reader would give it back: new placements read as existing refs at a position."""
    b = copy.deepcopy(designed)
    for r in b["refs"]:
        if "anchor" in r["placement"]:
            r["placement"] = {"existing": "0B" + r["id"][-4:] + ":Argonia.esp"}
    return b


def run(designed, built, positions=None):
    res = D.Resolver(positions=positions or {"0A0020:Example.esp": {"cell": "0A0100:Example.esp", "interior": False,
                                                                      "x": 1100.0, "y": 2000.0, "z": 50.0}},
                     places=PLACES, use_db=False)
    return D.diff_form(designed, built, res)


def test_the_built_example_matches_its_design():
    assert run(EXAMPLE, built_from(EXAMPLE)) == []


def test_anchor_satisfied_within_the_named_distance():
    b = built_from(EXAMPLE)
    man = next(r for r in b["refs"] if r["id"] == "npc.example.roll-man")
    man["at"]["x"] = 1100.0 + D.NEAR_UNITS - 1
    assert run(EXAMPLE, b) == []
    man["at"]["x"] = 1100.0 + D.NEAR_UNITS + 50
    out = run(EXAMPLE, b)
    assert len(out) == 1 and "ref npc.example.roll-man.placement.anchor" in out[0] and "near is 1024" in out[0]


def test_place_anchor_by_cell():
    b = built_from(EXAMPLE)
    next(r for r in b["refs"] if r["id"] == "npc.example.contact")["at"]["cell"] = "0A0300:Example.esp"
    out = run(EXAMPLE, b)
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
]


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
    b = copy.deepcopy(EXAMPLE)       # the anchor placements kept: the default resolver reads the designed form's refs
    for r in b["refs"]:
        if r["id"] == "npc.example.roll-man":
            r["placement"] = {"existing": "0B0001:Argonia.esp"}
    (tmp_path / "b" / "q.json").write_text(json.dumps(b))
    assert main(["diff", str(tmp_path / "d"), str(tmp_path / "b")]) == 0
    b["stages"][0]["journal"] = "Changed."
    (tmp_path / "b" / "q.json").write_text(json.dumps(b))
    assert main(["diff", str(tmp_path / "d"), str(tmp_path / "b")]) == 1
    assert "stage 10.journal" in capsys.readouterr().out
