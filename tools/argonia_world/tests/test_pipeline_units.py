"""L1/L2 tests for the units module, the FormID allocator, the piece resolver and layer composition (0.4 §a)."""
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.formids import Allocator, check_append_only
from tools.argonia_world.intermediate import Layer, compose
from tools.argonia_world.pieces import Index, Resolver, stat_edid

ROOT = Path(__file__).resolve().parents[3]
INDEX = {
    "plugins": ["Skyrim.esm", "Black Marsh.esm"],
    "records": [
        {"mesh": "meshes/a/floor.nif", "plugin": "Black Marsh.esm", "formKey": "000900:Black Marsh.esm", "type": "Static", "edid": "BMFloor"},
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
class FakeWorld:
    """The two db.World calls the allocator makes, over a list (the real table is tested by db.py's own tests)."""

    def __init__(self):
        self.table, self.saved = [], 0

    def rows(self, table, plugin):
        return [SimpleNamespace(**r) for r in self.table if r["plugin"] == plugin]

    def insert(self, table, **row):
        self.table.append(row)

    def save(self, tables):
        self.saved += 1


def test_allocator_is_stable_and_append_only():
    w = FakeWorld()
    a = Allocator(w)
    assert a.form_key("ARG_A", "GLOB") == "000800:Argonia.esm" and a.get("ARG_B") == 0x801 and a.get("ARG_A") == 0x800
    assert a.save() and not a.save() and w.saved == 1
    assert w.table[0] == {"editor_id": "ARG_A", "plugin": "Argonia.esm", "form_id": 0x800, "record_type": "GLOB",
                          "entity_key": None}
    b = Allocator(w)
    assert b.ids == {"ARG_A": 0x800, "ARG_B": 0x801} and b.get("ARG_C") == 0x802
    assert check_append_only(a.ids, b.ids) == []
    with pytest.raises(KeyError):
        Allocator(w, frozen=True).get("ARG_NEW")
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
def test_resolver_prefers_the_later_plugin_then_lowest_formid():
    res = Resolver(Index(INDEX), {"vanilla:a/floor": "meshes/a/floor.nif"})
    [r] = res.resolve("Meshes\\A\\Floor.NIF")
    assert (r.kind, r.form_key) == ("base", "000900:Black Marsh.esm")  # a Black Marsh mod before vanilla (0006 §8)
    vanilla = Resolver(Index({**INDEX, "records": INDEX["records"][1:]}))
    assert vanilla.resolve("meshes/a/floor.nif")[0].form_key == "03CB89:Skyrim.esm"  # not the ice variant


def test_resolver_never_lets_a_dlc_variant_win_unless_a_kit_names_it():
    # 1.7's Claywater walls: Dragonborn (later in load order) re-uses vanilla's mesh for its volcanic-ash swap.
    wall = "meshes/architecture/farmhouse/stonewall/stonewall01.nif"
    rows = [{"mesh": wall, "plugin": "Skyrim.esm", "formKey": "00099B:Skyrim.esm", "type": "Static", "edid": "Stonewall01"},
            {"mesh": wall, "plugin": "Skyrim.esm", "formKey": "06F15F:Skyrim.esm", "type": "Static", "edid": "Stonewall01Snow"},
            {"mesh": wall, "plugin": "Dragonborn.esm", "formKey": "03C39F:Dragonborn.esm", "type": "Static",
             "edid": "DLC2Stonewall01VolcanicAsh"},
            {"mesh": "meshes/dlc02/a/hut.nif", "plugin": "Dragonborn.esm", "formKey": "000777:Dragonborn.esm",
             "type": "Static", "edid": "DLC2Hut"},
            {"mesh": "meshes/dlc02/a/hut.nif", "plugin": "Sailable Ship.esm", "formKey": "000888:Sailable Ship.esm",
             "type": "Static", "edid": "ShipHut"},
            {"mesh": "meshes/landscape/rocks/rockl01.nif", "plugin": "DepthsOfSkyrim.esp", "formKey": "000901:DepthsOfSkyrim.esp",
             "type": "Static", "edid": "TBPRockL01Moss"},
            {"mesh": "meshes/landscape/rocks/rockl01.nif", "plugin": "King of the Murkmire.esp",
             "formKey": "000902:King of the Murkmire.esp", "type": "Static", "edid": "ArgoniaRockL01"},
            {"mesh": "meshes/landscape/rocks/rockl01.nif", "plugin": "Tropical Skyrim.esp",
             "formKey": "000903:Tropical Skyrim.esp", "type": "Static", "edid": "TropRockL01"}]
    order = ["Skyrim.esm", "Dragonborn.esm", "Sailable Ship.esm", "Tropical Skyrim.esp", "King of the Murkmire.esp",
             "DepthsOfSkyrim.esp"]
    res = Resolver(Index({"plugins": order, "records": rows, "meshes": []}))
    assert res.resolve(wall)[0].edid == "Stonewall01"  # vanilla, not the ash swap nor the snow variant
    assert res.resolve("meshes/dlc02/a/hut.nif")[0].edid == "DLC2Hut"  # the DLC's own folder names it
    assert res.resolve("meshes/landscape/rocks/rockl01.nif")[0].edid == "ArgoniaRockL01"  # Black Marsh, then Tropical
    no_bm = Resolver(Index({"plugins": order, "records": rows[-1:] + rows[-3:-2], "meshes": []}))
    assert no_bm.resolve("meshes/landscape/rocks/rockl01.nif")[0].edid == "TropRockL01"  # Tropical before other mods


def test_resolver_new_stat_composite_and_unresolved():
    res = Resolver(Index(INDEX), composites={"composite:x": ["meshes/a/door.nif", "meshes/a/bare.nif"]})
    kinds = [r.kind for r in res.resolve("composite:x")]
    loop = Resolver(Index(INDEX), composites={"composite:a": ["composite:b"], "composite:b": ["composite:a"]})
    assert loop.resolve("composite:a")[0].why == "composite contains itself"
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


def test_asset_ids_follow_the_registry_rule():
    from tools.argonia_world.pieces import asset_mesh
    assert asset_mesh("vanilla:architecture/riften/rtstables01") == "meshes/architecture/riften/rtstables01.nif"
    assert asset_mesh("composite:farmhouse/x") == "" and asset_mesh("nocolon") == ""


def test_sheet_layer_reads_the_world():
    from tools.argonia_world import db
    from tools.argonia_world.intermediate import sheet_layer
    w = db.open()
    lay = sheet_layer(Allocator(w, frozen=True), w, {"race": "argonian", "class": "marsh-guide", "birthsign": "serpent"})
    clas = next(r for r in lay.records if r["type"] == "CLAS")
    assert clas["skillWeights"]["Archery"] == 3 and sum(clas["skillWeights"].values()) > 0
    with pytest.raises(ValueError):
        sheet_layer(Allocator(w, frozen=True), w, {"race": "no-such-race", "class": "marsh-guide", "birthsign": "serpent"})
