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
