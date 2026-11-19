"""A placement at a new-world place takes its spot from the place's quests.jsonl row (set in the studio's Quests
layer); with no row it has no `at` and the rules report it as not placed yet."""
import json
from pathlib import Path

from tools.questform import compile as qc
from tools.questform import rules
from tools.questform.diff import NW_WORLD

Q = "quest.main.mn04"


def _place(t: Path, rows: list[dict]) -> Path:
    d = t / "camp"
    d.mkdir(parents=True)
    (d / "quests.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (d / "formids.json").write_text(json.dumps({"space:longhouse-1": 0x11A2B}))
    return t


def test_a_row_present_is_the_forms_at(tmp_path):
    places = _place(tmp_path, [
        {"id": f"{Q}/thing.mn04.cage", "quest": Q, "ref": "thing.mn04.cage", "space": "exterior",
         "pos": [-57000.5, -605900, 1152], "rot": [0, 0, 1.57]},
        {"id": f"{Q}/npc.mn04.late", "quest": Q, "ref": "npc.mn04.late", "space": "longhouse-1",
         "pos": [10, 20, 3], "rot": [0, 0, 3.1]}])
    assert qc.NW_WORLD == NW_WORLD
    assert qc.spot_at(Q, "thing.mn04.cage", "camp", places) == {
        "cell": NW_WORLD, "interior": False, "x": -57000.5, "y": -605900.0, "z": 1152.0, "rz": 1.57}
    assert qc.spot_at(Q, "npc.mn04.late", "camp", places) == {
        "cell": "011A2B:ArgoniaNWPlaces.esp", "interior": True, "x": 10.0, "y": 20.0, "z": 3.0, "rz": 3.1}


def test_a_row_absent_is_not_placed_yet(tmp_path):
    places = _place(tmp_path, [{"id": f"{Q}/other", "quest": Q, "ref": "other", "space": "nowhere-built",
                                "pos": [1, 2, 3], "rot": [0, 0, 0]}])
    assert qc.spot_at(Q, "thing.mn04.cage", "camp", places) is None
    assert qc.spot_at(Q, "other", "camp", places) is None          # a room with no cell form id yet
    ref = {"id": "thing.mn04.cage", "kind": "thing", "enabled": True,
           "placement": {"base": {"kind": "item", "id": "x"}, "anchor": {"place": "camp", "rule": "surface"}}}
    fm = rules.Form({"quest": {"id": Q}, "stages": [], "refs": [ref], "lines": [], "triggers": []})
    out = rules._placement(fm)
    assert [r for r, _ in out] == ["not-placed"] and "not placed yet" in out[0][1]
    fm.f["refs"][0]["at"] = {"cell": NW_WORLD, "interior": False, "x": 0, "y": 0, "z": 0}
    assert rules._placement(fm) == []
