"""The crime faction's jail (tools/places/draft/jail.py, people.jail_plan) and the primitives of copied refs
(tools/places/draft/primitives.py, build.collision_box, navmesh placed.collide) on small rows, no game data."""
import math

import numpy as np
import pytest

from tools.navmesh import placed
from tools.places import build as B
from tools.places import people
from tools.places.draft import jail, primitives

WALL = {"key": "K:000001", "edid": "ImpJailWall01", "type": "Static", "bounds": [[-4, 0, 0], [4, 260, 255]], "model": "x/jail.nif"}
BED = {"key": "K:000002", "edid": "CommonBed01", "type": "Furniture", "bounds": [[-40, -90, 0], [40, 90, 60]], "model": "x/bed.nif"}
DOOR = {"key": "K:000003", "edid": "ImpDoor01", "type": "Door", "bounds": [[-40, -5, 0], [40, 5, 200]], "model": "x/door.nif"}
BASES = {b["key"]: b for b in (WALL, BED, DOOR)}


def ref(i, base, kind, x, y, **kw):
    return {"id": f"X.esm:{i:06X}", "src": f"X.esm:{i:06X}", "base": base["key"], "kind": kind, "pos": [x, y, 0.0],
            "rot": [0.0, 0.0, 0.0], **kw}


def bars():
    """Two jail walls end to end along x = 0, y 0 to 520: the pen is the side away from the way in (x > 0)."""
    return [ref(1, WALL, "static", 0.0, 0.0), ref(2, WALL, "static", 0.0, 260.0)]


def test_a_room_with_bars_and_no_bed_gets_a_bedroll_behind_them_and_the_chests_by_the_way_in():
    got = jail.plan_jail("t", "cell", bars(), BASES, [800.0, 260.0, 0.0])
    assert got["bed_row"] and got["bed_row"]["base"] == jail.BEDROLL
    assert got["bed_row"]["pos"][0] < 0 and got["marker"][0] < 0  # behind the bars
    assert jail.MARKER_OFF[0] - 1 <= math.dist(got["marker"][:2], got["bed_row"]["pos"][:2]) <= jail.MARKER_OFF[1] + 1
    assert all(c[0] > 0 for c in got["chests"]) and math.dist(got["chests"][0], got["chests"][1]) >= 96


def test_a_bed_by_a_door_that_locks_is_the_cell():
    things = [ref(5, BED, "furniture", 2000.0, 0.0), ref(6, BED, "furniture", 300.0, 300.0),
              ref(7, DOOR, "door", 300.0, 100.0, lock={"level": "Adept"})]
    got = jail.plan_jail("t", "cell", things, BASES, [1000.0, 1000.0, 0.0])
    assert got["bed"]["id"] == "X.esm:000006" and got["door"]["id"] == "X.esm:000007" and got["bed_row"] is None
    assert "locks" in got["how"]


def test_a_room_with_neither_bed_nor_bars_has_no_cell():
    with pytest.raises(ValueError):
        jail.plan_jail("t", "cell", [ref(7, DOOR, "door", 0.0, 0.0)], BASES, [500.0, 0.0, 0.0])


def test_the_jail_is_known_by_its_source_cells_editor_id():
    spaces = {"exterior": {"refs": []}, "01Hall": {"space": {"copy_of": "s/01Hall"}, "refs": []},
              "01BlackRoseJail": {"space": {"copy_of": "s/01BlackRoseJail"}, "refs": []}}

    class Src:
        spaces = {}
    sid, how = jail.find_jail(spaces, Src(), BASES)
    assert sid == "01BlackRoseJail" and "editor id" in how


def test_the_faction_names_its_jail_rows_and_a_missing_row_is_a_problem():
    rows = {i: {"id": i, "fk": f"P.esp:{n:06X}"} for n, i in enumerate(("t.ext", "t.in", "t.stol", "t.plcn"), 1)}
    P = {"place": {"factions": [{"id": "t.crime", "kind": "crime", "jail": {
        "exterior": "t.ext", "marker": "t.in", "stolen": "t.stol", "inventory": "t.plcn", "space": "jail"}}]}}
    got = people.jail_plan(P, rows, "t")
    assert got["exterior"] == got["wait"] == "P.esp:000001" and got["stolen"] == "P.esp:000003"
    assert got["outfit"] == people.JAIL_OUTFIT and all(r.get("persistent") for r in rows.values())
    B.PROBLEMS.clear()
    del rows["t.plcn"]
    assert people.jail_plan(P, rows, "t") is None and B.PROBLEMS
    B.PROBLEMS.clear()
    assert people.jail_plan({"place": {"factions": [{"kind": "crime", "jail": None}]}}, rows, "t") is None


def test_classes_of_primitives():
    marker = {"key": "Skyrim.esm:000021", "edid": "CollisionMarker", "type": "Static"}
    trig = {"key": "Skyrim.esm:048AC0", "edid": "defaultActivateSelfTRIG", "type": "Activator"}
    room = {"key": "Skyrim.esm:00001F", "edid": "RoomMarker", "type": "Static"}
    box = {"type": "Box", "bounds": [10, 10, 10]}
    assert primitives.classify({"id": "a", "base": marker["key"], "primitive": box}, marker, set()) == ("collision", None)
    assert primitives.classify({"id": "b", "base": room["key"], "primitive": box}, room, set()) == ("room", None)
    cls, why = primitives.classify({"id": "c", "base": trig["key"], "primitive": box, "scripts": ["defaultActivateSelf"]}, trig, set())
    assert cls == "trigger" and "reaches nothing" in why
    assert primitives.classify({"id": "c", "base": trig["key"], "primitive": box, "scripts": ["x"]}, trig, {"c"}) == ("trigger", None)
    assert primitives.followed([{"activate_parents": ["c"]}, {"linked": [{"ref": "d"}]}, {"enable_parent": {"ref": "e"}}]) == {"c", "d", "e"}


def test_a_collision_markers_box_is_a_solid_of_the_navmesh_and_nothing_else_is():
    r = {"base": "Skyrim.esm:000021", "primitive": {"type": "Box", "bounds": [100.0, 0.0, 50.0]}}
    assert B.collision_box(r) == [100.0, 0.5, 50.0]  # a plane keeps a sliver of thickness
    assert B.collision_box({**r, "base": "Skyrim.esm:000034"}) is None and B.collision_box({"base": "Skyrim.esm:000021"}) is None
    tris, tally = placed.collide([{"base": "000021:Skyrim.esm", "pos": [1000.0, 0.0, 0.0], "rot": [0.0, 0.0, math.pi / 2],
                                   "scale": 1.0, "box": [100.0, 10.0, 50.0]}], B.ROOT / "no-such-data", {}, resolver=object())
    assert tally["primitive"] == 1 and len(tris) == 12
    v = tris.reshape(-1, 3)
    assert np.allclose([v[:, 0].min(), v[:, 0].max(), v[:, 1].min(), v[:, 1].max(), v[:, 2].min(), v[:, 2].max()],
                       [990.0, 1010.0, -100.0, 100.0, -50.0, 50.0])  # turned a quarter: its long side runs along y
