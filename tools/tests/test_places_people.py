"""tools/places/people.plan on small rows: where stops are seated, patrol chains, and rows it cannot read."""
import base64

import numpy as np
import pytest

from tools.places import build as B
from tools.places import people

P = "ArgoniaNWPlaces.esp"


class Ids:
    def __init__(self):
        self.n = {}

    def __call__(self, key):
        return f"{P}:{self.n.setdefault(key, 0x800 + len(self.n)):06X}"


def facts(patched=None):
    cell = {"x": 0, "y": 0, "offset": 100.0, "deltas": base64.b64encode(np.zeros((33, 33), np.int8).tobytes()).decode()}
    return {"by_cell": {(0, 0): cell}, "patched": patched or {}}


def plan(rows, patched=None):
    B.PROBLEMS.clear()
    out = people.plan({"place": {"place_id": "t"}, "people": rows}, {"refs": [], "by_id": {}}, Ids(), facts(patched), [])
    return out, list(B.PROBLEMS)


def guard(**kw):
    return {"id": "t.guard", "base_from": "Skyrim.esm:000001", "role": "guard",
            "routine": [{"start": 8, "hours": 4, "kind": "patrol"}, {"start": 20, "hours": 4, "kind": "patrol"}],
            "patrol": {"points": [[64, 128], [500, 500], [900, 200]], "loop": True}, **kw}


def test_a_stop_outside_is_seated_on_the_built_land_between_its_vertices():
    out, problems = plan([guard()], patched={(1, 1): 110})  # one vertex raised 10 steps by a land patch
    assert not problems
    first = next(m for m in out["markers"] if m["pos"][:2] == [64, 128])
    assert first["pos"][2] == pytest.approx(840.0)  # halfway from 800 (the world's) to 880 (the patched vertex)


def test_a_day_that_starts_on_patrol_is_placed_and_two_patrol_stops_walk_one_chain():
    out, problems = plan([guard()])
    assert not problems
    assert len({m["fk"] for m in out["markers"]}) == len(out["markers"]) == 4  # three patrol points and home
    chain = [m for m in out["markers"] if m.get("linked")]
    assert len(chain) == 3 and all(len(m["linked"]) == 1 for m in chain)
    actor = out["actors"][0]
    assert actor["pos"][:2] == [64.0, 128.0] and actor["linked"][0]["ref"] == chain[0]["fk"]
    kinds = [p["kind"] for p in out["packages"]]
    assert kinds == ["patrol", "patrol", "sandbox"] and all(p.get("target_linked") for p in out["packages"][:2])


def test_rows_the_builder_cannot_seat_or_read_are_problems_and_the_rest_are_planned():
    rows = [guard(),
            {"id": "t.off", "base_from": "Skyrim.esm:000001", "routine": [{"start": 8, "hours": 8, "kind": "work", "at": {"pos": [99999, 99999]}}]},
            {"id": "t.room", "base_from": "Skyrim.esm:000001", "routine": [{"start": 8, "hours": 8, "kind": "work", "at": {"space": "house", "pos": [10, 10]}}]},
            {"id": "t.bed", "base_from": "Skyrim.esm:000001", "bed": {"space": "house"}, "routine": []}]
    out, problems = plan(rows)
    assert [n["id"] for n in out["npcs"]] == ["t.guard"]
    assert len(problems) == 3
    assert "off the land" in problems[0] and "no height" in problems[1] and "t.bed" in problems[2]
