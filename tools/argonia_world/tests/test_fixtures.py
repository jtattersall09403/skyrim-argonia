"""L1: the studio fixtures build from a small fake piece index (no game data)."""
from __future__ import annotations

import ast
import inspect

import pytest

from tools.argonia_world import fixtures as fx
from tools.argonia_world import skyrim_units as su
from tools.argonia_world.pieces import Index, Resolver

MESHES = [fx.FLOOR, *fx.WALL.values(), fx.DOOR, fx.LADDER, fx.BACKDROP]


class FakeAlloc:
    def __init__(self):
        self.ids: dict[str, int] = {}

    def form_key(self, edid, record_type=None, entity_key=None):
        return f"{self.ids.setdefault(edid, 0x800 + len(self.ids)):06X}:Argonia.esm"


@pytest.fixture(scope="module")
def built():
    rows = [{"mesh": m, "plugin": "Skyrim.esm", "formKey": f"{0x100 + i:06X}:Skyrim.esm",
             "type": "Door" if m in (fx.DOOR, fx.LADDER) else "Static", "edid": f"E{i}"} for i, m in enumerate(MESHES)]
    res = Resolver(Index({"plugins": ["Skyrim.esm"], "records": rows, "meshes": MESHES}))
    lay = fx.layer(FakeAlloc(), res)
    return lay, {r["edid"]: r for r in lay.records}


def test_two_studio_only_cells(built):
    lay, by = built
    assert lay.name == "place:fixtures"
    for edid in (fx.PROVING_GROUND, fx.BOOTH):
        c = by[edid]
        assert {"IsInteriorCell", "CantTravelFromHere"} <= set(c["flags"])
        assert c["name"] and c["name"].isascii()
    assert "HasWater" in by[fx.PROVING_GROUND]["flags"] and by[fx.PROVING_GROUND]["water"]
    assert by[fx.PROVING_GROUND]["waterHeight"] == su.rounded(su.metres_to_units(fx.WATER_LEVEL_M), 2)


def test_every_ref_has_a_resolved_base(built):
    lay, by = built
    known = {r["formKey"] for r in lay.records} | {f"{0x100 + i:06X}:Skyrim.esm" for i in range(len(MESHES))} \
        | {su.ENGINE_MARKER_HEADING}
    for c in (by[fx.PROVING_GROUND], by[fx.BOOTH]):
        assert c["refs"]
        for r in c["refs"]:
            assert r["base"] in known, r["edid"]
        assert len({r["formKey"] for r in c["refs"]}) == len(c["refs"])


def test_every_station_has_a_persistent_marker(built):
    _, by = built
    refs = {r["edid"]: r for r in by[fx.PROVING_GROUND]["refs"]}
    for station in fx.STATIONS:
        m = refs[fx.marker_edid(station)]
        assert m["persistent"] and m["base"] == su.ENGINE_MARKER_HEADING
    for want in ("Start", "WallRockDry", "WallRockWet", "WallMasonryDry", "WallMasonryWet", "WallTimberDry",
                 "WallTimberWet", "Ladder", "DoorA", "DoorB", "WaterAnkle", "WaterWaist", "WaterSwim", "WaterDeep",
                 "DuelPlayer", "DuelOpponent"):
        assert want in fx.STATIONS
    b = {r["edid"]: r for r in by[fx.BOOTH]["refs"]}[fx.BOOTH_MARKER]
    assert b["persistent"]


def test_door_pair_teleports_to_each_other(built):
    _, by = built
    refs = {r["edid"]: r for r in by[fx.PROVING_GROUND]["refs"]}
    a, b = refs["ARG_PG_DoorA"], refs["ARG_PG_DoorB"]
    assert a["teleport"]["door"] == b["formKey"] and b["teleport"]["door"] == a["formKey"]


def test_duel_ring_is_12m_and_far_marker_15m(built):
    d = {k: fx.STATIONS[k] for k in ("DuelPlayer", "DuelOpponent", "DuelFar")}
    dist = lambda p, q: ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5
    assert dist(d["DuelPlayer"], d["DuelOpponent"]) <= 12
    assert dist(d["DuelFar"], d["DuelOpponent"]) == 15


def test_units_only_through_skyrim_units():
    src = inspect.getsource(fx)
    assert "70.03" not in src and "4096" not in src
    for node in ast.walk(ast.parse(src)):
        assert not (isinstance(node, ast.Constant) and node.value == 70.03)
