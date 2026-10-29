"""L1/L2 tests for the units module, the FormID allocator, the piece resolver and layer composition (0.4 §a)."""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.formids import Allocator, check_append_only
from tools.argonia_world.intermediate import Layer, compose
from tools.argonia_world.pieces import Index, Resolver, stat_edid

ROOT = Path(__file__).resolve().parents[3]
INDEX = {
    "plugins": ["Skyrim.esm", "BM.esp"],
    "records": [
        {"mesh": "meshes/a/floor.nif", "plugin": "BM.esp", "formKey": "000900:BM.esp", "type": "Static", "edid": "BMFloor"},
        {"mesh": "meshes/a/floor.nif", "plugin": "Skyrim.esm", "formKey": "080157:Skyrim.esm", "type": "Static", "edid": "FloorIce"},
        {"mesh": "meshes/a/floor.nif", "plugin": "Skyrim.esm", "formKey": "03CB89:Skyrim.esm", "type": "Static", "edid": "Floor"},
        {"mesh": "meshes/a/door.nif", "plugin": "Skyrim.esm", "formKey": "000123:Skyrim.esm", "type": "Door", "edid": "Door"},
    ],
    "meshes": ["meshes/a/bare.nif"],
}


# --- units ---------------------------------------------------------------------------------------------------
def test_units_round_trip_and_cells():
    assert su.units_to_metres(su.metres_to_units(12.5)) == pytest.approx(12.5)
    assert su.metres_to_units(1.828) == pytest.approx(su.VERTEX_SPACING_UNITS, abs=0.05)
    assert su.cell_of(-1, 4095) == (-1, 0) and su.cell_of(4096, -4097) == (1, -2)
    assert su.cell_origin(-2, 3) == (-2 * su.CELL_UNITS, 3 * su.CELL_UNITS)


def test_yaw_is_radians_clockwise_from_north_normalised():
    assert su.yaw_to_rot(90) == (0.0, 0.0, pytest.approx(math.pi / 2))
    assert su.yaw_to_rot(-90)[2] == pytest.approx(3 * math.pi / 2)
    assert su.rounded(-0.00001) == 0.0 and str(su.rounded(-0.00001)) == "0.0"


def test_unit_facts_live_only_in_the_units_module():
    pat = re.compile(r"\b(70\.03|4096|0x800)\b")
    hits = [p for p in (ROOT / "tools").rglob("*.py")
            if p.name != "skyrim_units.py" and "tests" not in p.parts and pat.search(p.read_text(encoding="utf-8"))]
    assert hits == []


# --- FormIDs -------------------------------------------------------------------------------------------------
def test_allocator_is_stable_and_append_only(tmp_path):
    t = tmp_path / "formids.json"
    a = Allocator(t)
    assert a.form_key("ARG_A") == "000800:Argonia.esm" and a.get("ARG_B") == 0x801 and a.get("ARG_A") == 0x800
    assert a.save() and not a.save()
    b = Allocator(t)
    assert b.ids == {"ARG_A": 0x800, "ARG_B": 0x801} and b.get("ARG_C") == 0x802
    assert check_append_only(a.ids, b.ids) == []
    with pytest.raises(KeyError):
        Allocator(t, frozen=True).get("ARG_NEW")
    with pytest.raises(ValueError):
        a.get("MQ101")


def test_append_only_refuses_removal_change_and_reuse():
    old = {"ARG_A": 0x800, "ARG_B": 0x801}
    assert any("removed" in e for e in check_append_only(old, {"ARG_A": 0x800}))
    assert any("changed" in e for e in check_append_only(old, {"ARG_A": 0x900, "ARG_B": 0x801}))
    assert any("reuses" in e for e in check_append_only({"ARG_A": 0x800, "ARG_B": 0x801},
                                                         {"ARG_A": 0x800, "ARG_B": 0x801, "ARG_C": 0x7FF}))


def test_committed_table_is_valid():
    assert subprocess.run([sys.executable, "-m", "tools.argonia_world.formids", "check"], cwd=ROOT, check=False).returncode == 0


# --- pieces --------------------------------------------------------------------------------------------------
def test_resolver_prefers_load_order_then_lowest_formid():
    res = Resolver(Index(INDEX), {"vanilla:a/floor": "meshes/a/floor.nif"})
    [r] = res.resolve("Meshes\\A\\Floor.NIF")
    assert (r.kind, r.form_key) == ("base", "03CB89:Skyrim.esm")
    assert res.resolve("vanilla:a/floor")[0].form_key == "03CB89:Skyrim.esm"


def test_resolver_new_stat_composite_and_unresolved():
    res = Resolver(Index(INDEX), composites={"composite:x": ["meshes/a/door.nif", "meshes/a/bare.nif"]})
    kinds = [r.kind for r in res.resolve("composite:x")]
    assert kinds == ["base", "new-stat"]
    assert res.resolve("meshes/a/bare.nif")[0].edid == stat_edid("meshes/a/bare.nif") == "ARG_STAT_a_bare"
    assert [r.piece for r in res.unresolved(["meshes/a/door.nif", "bmv:no/such", "composite:none", "meshes/x.nif"])] \
        == ["bmv:no/such", "composite:none", "meshes/x.nif"]


def test_pieces_check_fails_on_a_deliberately_unknown_piece(tmp_path):
    (tmp_path / "index.json").write_text(json.dumps(INDEX))
    (tmp_path / "pieces.json").write_text(json.dumps({"place.test": ["meshes/a/floor.nif", "bmv:deliberately/unknown"]}))
    cmd = [sys.executable, "-m", "tools.argonia_world.pieces", "check", "--index", str(tmp_path / "index.json"),
           "--pieces", str(tmp_path / "pieces.json")]
    r = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
    assert r.returncode == 1 and "bmv:deliberately/unknown: unresolved" in r.stdout
    (tmp_path / "pieces.json").write_text(json.dumps({"place.test": ["meshes/a/floor.nif"]}))
    assert subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True).returncode == 0


# --- layers --------------------------------------------------------------------------------------------------
def _rec(edid, fid, **kw):
    return {"type": "STAT", "edid": edid, "formKey": f"{fid:06X}:Argonia.esm", **kw}


def test_regenerating_the_base_keeps_the_layer():
    place = Layer("place:p", [_rec("ARG_A", 0x800, model="meshes/edited.nif"), _rec("ARG_C", 0x802, model="c.nif")])
    first = compose([Layer("base", [_rec("ARG_A", 0x800, model="a.nif"), _rec("ARG_B", 0x801, model="b.nif")]), place])
    again = compose([Layer("base", [_rec("ARG_A", 0x800, model="a2.nif")]), place])  # the base regenerated, smaller
    assert [r["model"] for r in first] == ["meshes/edited.nif", "b.nif", "c.nif"]
    assert [(r["edid"], r["model"]) for r in again] == [("ARG_A", "meshes/edited.nif"), ("ARG_C", "c.nif")]
    assert again[0]["layer"] == "base"


def test_same_kind_layers_may_not_clash_but_a_patch_wins():
    a, b = Layer("place:a", [_rec("ARG_A", 0x800, model="x")]), Layer("place:b", [_rec("ARG_A", 0x800, model="y")])
    with pytest.raises(ValueError, match="set by both"):
        compose([a, b])
    assert compose([a, Layer("patch:fix", [_rec("ARG_A", 0x800, model="z")])])[0]["model"] == "z"


def test_records_sort_by_type_then_raw_formid():
    recs = compose([Layer("patch:q", [
        {"type": "QUST", "override": True, "edid": "Z", "formKey": "000001:Dawnguard.esm"},
        {"type": "QUST", "override": True, "edid": "Y", "formKey": "0FFFFF:Skyrim.esm"},
        {"type": "GLOB", "edid": "ARG_G", "formKey": "000800:Argonia.esm"}])], ["Skyrim.esm", "Dawnguard.esm"])
    assert [r["edid"] for r in recs] == ["ARG_G", "Y", "Z"]
