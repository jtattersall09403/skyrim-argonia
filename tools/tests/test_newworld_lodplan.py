"""Which placed bases get LOD and how (tools/newworld/world/lodplan.py), on Skyrim's and DynDOLOD's measured rules."""
import collections

from tools.newworld.world import lodplan


def base(sig, obnd, model="argonia\\trees\\x.nif", copied=True, plugin="King of the Murkmire.esp", edid="X"):
    return {"sig": sig, "obnd": obnd, "model": model, "copied": copied, "plugin": plugin, "edid": edid}


BIG = [-300, -300, -20, 300, 300, 900]  # magnitude ~1150, Z2 900
HUGE = [-900, -900, -50, 900, 900, 900]  # magnitude ~1560
SMALL = [-40, -40, 0, 40, 40, 60]


def test_our_edid_follows_foreigncopy():
    assert lodplan.our_edid(base("TREE", BIG, edid="ArgoniaTreeKapok01")) == "ANW_KotM_ArgoniaTreeKapok01"
    assert lodplan.our_edid(base("TREE", BIG, copied=False, plugin="Black Marsh.esm", edid="01Willow")) == "01Willow"


def test_large_trees_get_billboards_whatever_their_record_path_or_plugin():
    # TexGen's own filter drops a base without "tree" in its model path; ours forces it (the walk-5 fault)
    assert lodplan.classify(base("TREE", BIG, model="landscape\\plants\\fern.nif"), 10, "understorey", set())[0] == "tree"
    assert lodplan.classify(base("STAT", BIG), 10, "canopy_tree", set())[0] == "tree"
    # a master's static tree too: our override of it carries the flag
    assert lodplan.classify(base("STAT", BIG, copied=False, plugin="Black Marsh.esm"), 10, "canopy_tree", set())[0] == "tree"


def test_rocks_and_logs_follow_skyrims_rules():
    assert lodplan.classify(base("STAT", HUGE), 5, "boulder", set())[0] == "object"
    assert lodplan.classify(base("STAT", BIG), 5, "boulder", set())[0] == "none"  # under 1,500: as Skyrim's RockL
    assert lodplan.classify(base("STAT", HUGE, model="Landscape\\Rocks\\RockL01.nif"), 5, "boulder", set())[0] == "none"
    assert lodplan.classify(base("STAT", HUGE), 5, "road_rock_pile", set())[0] == "none"
    assert lodplan.classify(base("STAT", BIG), 5, "log", set())[0] == "object"
    assert lodplan.classify(base("STAT", BIG, model="m\\rock.nif"), 5, "boulder", {"m\\rock.nif"})[0] == "own"
    assert lodplan.classify(base("STAT", SMALL), 5, "boulder", set())[0] == "none"
    assert lodplan.classify(base("FLOR", BIG), 5, "herb", set())[0] == "none"
    assert lodplan.classify(base("STAT", BIG), 0, "boulder", set())[0] == "none"  # not placed


def test_a_lod_model_of_the_same_shape_is_found_where_dyndolod_looks():
    have = {"meshes\\lod\\rocks\\bigrock01_lod_0.nif"}
    read = lambda p: b"x" if p.lower() in have or ("meshes\\" + p.lower()) in have else None  # noqa: E731
    assert lodplan.lod_model("landscape\\rocks\\bigrock01.nif", read) == "lod\\rocks\\bigrock01_lod_0.nif"
    assert lodplan.lod_model("landscape\\rocks\\other.nif", read) is None


def test_full_models_are_refused_past_tamriels_per_block_budget():
    def row(src, model, refs, mag, lod8=False):
        return {"mech": "object", "source": src, "model": model, "refs": refs, "magnitude": mag, "lod8": lod8, "why": ""}
    rows = [row("a", "big.nif", 2, 3000), row("b", "log.nif", 100, 900)]
    blocks = {"a": {4: collections.Counter({(0, 0): 2}), 8: collections.Counter({(0, 0): 2})},
              "b": {4: collections.Counter({(0, 0): 100}), 8: collections.Counter({(0, 0): 100})}}
    lodplan.budget(rows, blocks, {"big.nif": 1000, "log.nif": 4562})  # 456,200 triangles in one block: refused
    assert rows[0]["mech"] == "object" and rows[1]["mech"] == "none" and "past Tamriel's" in rows[1]["why"]
    assert rows[0]["block_peak"][4] == 2000 <= lodplan.BUDGET[4]
    assert rows[1]["heavy"] and not rows[0].get("heavy")  # the refused model is owed a LOD model


def _coverage(tmp_path, plan_rows, billboards, export_rows):
    import json
    plugin, logs = tmp_path / "plugin", tmp_path / "logs"
    (plugin / "map").mkdir(parents=True)
    logs.mkdir()
    (plugin / "map" / "lodplan.json").write_text(json.dumps({"bases": plan_rows}))
    (logs / "DynDOLOD_SSE_BillboardsUsed_ArgoniaBlackMarsh.txt").write_text(
        "".join(f"{e} [TREE:0A000001] Billboard {'found' if ok else 'not found'} x\n" for e, ok in billboards))
    (logs / "LODGen_SSE_Export_ArgoniaBlackMarsh.txt").write_text(
        "".join("\t".join(["x"] * 9 + [e, "x", "x", "meshes\\" + full, lod4, "", "", "x"]) + "\n" for e, full, lod4 in export_rows))
    rc = lodplan.coverage(plugin, logs)
    return rc, json.loads((logs / "coverage.json").read_text())


def test_coverage_holds_each_base_to_the_mechanism_planned(tmp_path):
    def row(edid, mech, model, **kw):
        return {"edid": edid, "mech": mech, "model": model, "refs": 5, **kw}
    plan = [row("Palm", "tree", "t\\palm.nif"), row("Cliff", "object", "r\\cliff.nif"),
            row("Log", "lodmodel", "t\\log.nif", lod_model="lod\\t\\log_lod_0.nif"), row("Fern", "none", "p\\fern.nif")]
    good = [("Cliff", "r\\cliff.nif", "meshes\\r\\cliff.nif"), ("Log", "t\\log.nif", "meshes\\lod\\t\\log_lod_0.nif")]
    rc, doc = _coverage(tmp_path / "a", plan, [("Palm", True)], good)
    assert rc == 0 and doc["missing"] == [] and doc["rules"] == 2 and doc["rules_without_refs"] == []
    # a billboard not made, a rule that matched nothing, a derived model DynDOLOD did not draw from: each is a miss
    rc, doc = _coverage(tmp_path / "b", plan, [("Palm", False)], [("Log", "t\\log.nif", "meshes\\t\\log.nif")])
    assert rc == 1 and len(doc["missing"]) == 3 and doc["rules_without_refs"] == ["r\\cliff.nif"]


def test_a_base_with_a_texture_repair_is_planned_as_our_copy_of_it(tmp_path):
    import json
    plugin = tmp_path / "plugin"
    (plugin / "refs" / "flora").mkdir(parents=True)
    b = {"key": "11FE76:Black Marsh.esm", "ref": "Black Marsh.esm:01MANGROVE", "copied": False, "sig": "STAT", "edid": "01MANGROVE",
         "plugin": "Black Marsh.esm", "model": "landscape\\trees\\mangrove.nif", "obnd": BIG}
    rows = [dict(b, alt_textures=[{"shape": "s", "index": 1, "slots": ["a.dds"]}]),
            dict(b, ref="Black Marsh.esm:01MANGROVE2", edid="01MANGROVE2", key="11FE77:Black Marsh.esm")]
    (plugin / "refs" / "flora" / "bases.json").write_text(json.dumps({"build_id": "b", "key": "k", "bases": rows}))
    (plugin / "refs" / "flora" / "cy000.jsonl").write_text(
        "".join(json.dumps({"base": r["ref"], "cls": "canopy_tree", "x": 0, "y": 0}) + "\n" for r in rows))
    doc = lodplan.build(plugin, read=lambda p: None)
    got = {r["source"]: r for r in doc["bases"]}
    mine, masters = got["Black Marsh.esm:01MANGROVE"], got["Black Marsh.esm:01MANGROVE2"]
    # NewWorld.cs places the repaired base as ANW_BM_01MANGROVE: the flag and the billboard go to that record
    assert (mine["edid"], mine["plugin"], mine["key"], mine["mech"]) == ("ANW_BM_01MANGROVE", "ArgoniaNewWorld.esm", None, "tree")
    assert (masters["edid"], masters["plugin"], masters["key"], masters["mech"]) == ("01MANGROVE2", "Black Marsh.esm", "11FE77:Black Marsh.esm", "tree")
