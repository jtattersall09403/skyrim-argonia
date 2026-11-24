"""What a unit's move carries and what it leaves (edits.py unit_carried; the studio's units.js spotsMoved and edits.js
unitCarried keep the same rule): its door's spur and its people's own spots go; a path that only starts near it, a
spot another person also stands at and a guard's post stay."""
from tools.places.edits import unit_carried


def person(pid, pos, role="resident"):
    return {"id": pid, "role": role, "routine": [{"start": 8, "hours": 8, "kind": "work", "at": {"space": "exterior", "pos": pos}}]}


def moved(p, pos):
    q = {**p, "routine": [dict(p["routine"][0], at={"space": "exterior", "pos": pos})]}
    return {"person": q, "before": p}


def test_a_unit_carries_its_own_and_leaves_the_rest():
    files = {"spaces": {"exterior": {"refs": [{"id": "door1", "door": {"to_space": "r"}}]}},
             "people": [person("a", [0, 0, 0]), person("b", [500, 0, 0]), person("c", [505, 0, 0]), person("g", [900, 0, 0], "guard")]}
    op = {"space": "exterior", "refs": [{"id": "door1", "before": {"pos": [0, 0, 0]}, "after": {"pos": [100, 0, 0]}}],
          "people": [moved(files["people"][0], [100, 0, 0]), moved(files["people"][1], [600, 0, 0]), moved(files["people"][3], [1000, 0, 0])],
          "paths": [{"before": {"id": "spur", "to": "door1", "points": [[0, -500], [0, -200], [0, 0]]},
                     "path": {"id": "spur", "to": "door1", "points": [[0, -500], [50, -200], [100, 0]]}},
                    {"before": {"id": "camp", "points": [[10, 10], [10, -900]]}, "path": {"id": "camp", "points": [[110, 10], [10, -900]]}}]}
    people = {m["person"]["id"]: m["person"]["routine"][0]["at"]["pos"] for m in unit_carried(files, op, "people")}
    assert people == {"a": [100, 0, 0]}            # b shares its spot with c; g is a guard: both stay
    paths = {m["path"]["id"]: m["path"]["points"] for m in unit_carried(files, op, "paths")}
    assert paths == {"spur": [[0, -500], [50, -200], [100, 0]]}   # the camp path only started near it: it stays
