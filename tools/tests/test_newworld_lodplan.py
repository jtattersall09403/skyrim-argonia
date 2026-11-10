"""Which placed bases get LOD and how (tools/newworld/world/lodplan.py), on Skyrim's and DynDOLOD's measured rules."""
from tools.newworld.world import lodplan


def base(sig, obnd, model="argonia\\trees\\x.nif", copied=True, plugin="King of the Murkmire.esp", edid="X"):
    return {"sig": sig, "obnd": obnd, "model": model, "copied": copied, "plugin": plugin, "edid": edid}


BIG = [-300, -300, -20, 300, 300, 900]  # magnitude ~1150, Z2 900
SMALL = [-40, -40, 0, 40, 40, 60]


def test_our_edid_follows_foreigncopy():
    assert lodplan.our_edid(base("TREE", BIG, edid="ArgoniaTreeKapok01")) == "ANW_KotM_ArgoniaTreeKapok01"
    assert lodplan.our_edid(base("TREE", BIG, copied=False, plugin="Black Marsh.esm", edid="01Willow")) == "01Willow"


def test_large_trees_get_billboards_whatever_their_record_or_path():
    # TexGen's own filter drops a base without "tree" in its model path; ours forces it (the walk-5 fault)
    assert lodplan.classify(base("TREE", BIG, model="landscape\\plants\\fern.nif"), 10, "understorey", set())[0] == "tree"
    assert lodplan.classify(base("STAT", BIG), 10, "canopy_tree", set())[0] == "tree"
    # a master's STAT tree cannot carry our flag: its full model in object LOD
    assert lodplan.classify(base("STAT", BIG, copied=False, plugin="Black Marsh.esm"), 10, "canopy_tree", set())[0] == "object"


def test_large_rocks_and_logs_get_object_lod_small_things_none():
    assert lodplan.classify(base("STAT", BIG), 5, "boulder", set())[0] == "object"
    assert lodplan.classify(base("STAT", BIG, model="m\\rock.nif"), 5, "boulder", {"m\\rock.nif"})[0] == "own"
    assert lodplan.classify(base("STAT", SMALL), 5, "boulder", set())[0] == "none"
    assert lodplan.classify(base("FLOR", BIG), 5, "herb", set())[0] == "none"
    assert lodplan.classify(base("STAT", BIG), 0, "boulder", set())[0] == "none"  # not placed
