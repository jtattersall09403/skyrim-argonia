"""The walk's promises (tools/newworld/ecology/place.py check_promises, newworld/sources/ecology/walk_spots.json): a
spot fails when a promised kind stands beyond reach or the spot lands where nothing lives."""
import json

from tools.newworld.ecology import place

REPO = place.REPO


def test_a_promise_beyond_reach_or_a_spot_in_the_margin_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(place, "promises", lambda: (200 * 70.0, {"S": ["crab", "otter"], "M": ["crab"]}))
    monkeypatch.setattr(place, "landings", lambda out: {"S": (100.0, 100.0), "M": (9000.0, 100.0)})
    cells = {(0, 0): {"danger_band_id": "D1"}, (1, 0): {"margin": 1}}
    faults: list = []
    res = place.check_promises(tmp_path, cells, [("crab", 150.0, 100.0), ("otter", 100.0 + 300 * 70, 100.0)], faults)
    assert res["S"] == {"crab": 1, "otter": 300}
    assert any("S: no otter" in f for f in faults) and any("M: lands in a cell with no band" in f for f in faults)
    assert not any("S: no crab" in f for f in faults)


def test_every_promised_kind_is_a_kind_of_its_spots_world():
    spots = json.loads((REPO / "newworld/sources/ecology/walk_spots.json").read_text())["spots"]
    bind = json.loads((REPO / "newworld/sources/ecology/bindings.json").read_text())
    for name, kinds in spots.items():
        for k in kinds:
            assert k == "people" or bind["kinds"].get(k, {}).get("records") or bind["critter_kinds"].get(k, {}).get("critter"), (name, k)
