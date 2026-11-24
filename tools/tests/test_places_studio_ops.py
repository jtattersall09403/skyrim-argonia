"""The studio's newer edits replayed by edits.apply, as a save would carry them: a way drawn into a stop (a person.edit
whose stop has a `route`), a world tree taken into the place and lowered (veg.clear, ref.add with `world`, ref.move
of its seat), and a door raised on its seat; each replays and its inverse gives the place back."""
import copy
import json
from pathlib import Path

from tools.places.edits import apply, invert

PLACE = json.loads((Path(__file__).parent / "places_edits" / "place.json").read_text())


def ops_of(files):
    p0 = files["people"][0]
    p1 = copy.deepcopy(p0)
    p1["routine"].append({"start": 20, "hours": 4, "kind": "wander", "radius": 256,
                          "at": {"space": "exterior", "pos": [1500.0, 2500.0, 50.0], "radius": 256},
                          "route": [[1200.0, 2100.0, 50.0], [1400.0, 2400.0, 50.0]]})
    tree = {"id": "fix.TREE", "base": "Black Marsh.esm:0A0099", "kind": "tree", "pos": [3000.0, 3000.0, 40.0], "rot": [0, 0, 0.5],
            "scale": 1.0, "layer": "place", "flags": [], "seat": {"mode": "ground", "dz": -20.0},
            "world": {"base": "Black Marsh.esm:0A0099", "pos": [3000.0, 3000.0, 40.0]}}
    door = next(r for r in files["spaces"]["exterior"]["refs"] if r.get("seat"))
    before = {k: copy.deepcopy(door[k]) for k in ("pos", "rot", "scale", "seat") if k in door}
    after = copy.deepcopy(before)
    after["seat"]["dz"] = after["seat"].get("dz", 0) + 30.0
    after["pos"] = [after["pos"][0], after["pos"][1], after["pos"][2] + 30.0]
    ops = [{"op": "person.edit", "person": p1, "before": p0},
           {"op": "veg.clear", "items": [{"base": tree["base"], "pos": tree["pos"]}]},
           {"op": "ref.add", "ref": tree},
           {"op": "ref.move", "id": tree["id"], "before": {k: tree[k] for k in ("pos", "rot", "scale", "seat")},
            "after": {"pos": [3000.0, 3000.0, 26.0], "rot": [0, 0, 0.5], "scale": 1.0, "seat": {"mode": "ground", "dz": -34.0}}},
           {"op": "ref.move", "id": door["id"], "before": before, "after": after}]
    for n, o in enumerate(ops, 1):
        o.setdefault("space", "exterior")
        o["n"] = n
    return ops


def test_new_ops_replay_and_undo():
    ops = ops_of(PLACE)
    out = apply(PLACE, ops)
    p = next(x for x in out["people"] if x["id"] == "fix.p1")
    assert p["routine"][-1]["route"] == [[1200.0, 2100.0, 50.0], [1400.0, 2400.0, 50.0]]
    t = next(r for r in out["spaces"]["exterior"]["refs"] if r["id"] == "fix.TREE")
    assert t["pos"][2] == 26.0 and t["seat"]["dz"] == -34.0 and t["world"]["pos"] == [3000.0, 3000.0, 40.0]
    assert any(c["base"] == "Black Marsh.esm:0A0099" for c in out["clear"])
    back = apply(out, invert(ops))
    assert json.dumps(back, sort_keys=True) == json.dumps(PLACE, sort_keys=True)
