"""mesh_textures: the L1 texture-coverage check and the untextured filter lists.usable applies."""
from tools.argonia_world.vegetation import mesh_textures as mt

MAN = {"meshes": {
    "meshes/a/tree.nif": {"row": "bmv", "laid": "bmv", "slots": [[0, "textures/a/bark.dds"], [1, "textures/a/bark_n.dds"]]},
    "meshes/a/bush.nif": {"row": "bmv", "laid": "bmv", "slots": [[0, "textures/a/leaf.dds"]]},
    "meshes/b/lily.nif": {"row": "kotm", "laid": "kotm", "slots": [[0, "textures/b/lily.dds"],
                                                                   [1, "textures/nor"]]},
}, "sources": {"textures/a/bark.dds": "bmv", "textures/a/bark_n.dds": None, "textures/a/leaf.dds": None,
               "textures/b/lily.dds": "kotm", "textures/nor": None}}
DEPS = {"mods": [{"id": "bmv", "keep": ["meshes/a/tree.nif"]}, {"id": "kotm"}]}


def form(k, model, mod):
    return {"form_key": k, "model": model, "mod": mod}


def test_untextured_is_a_missing_diffuse_only():
    assert mt.untextured(MAN) == {"meshes/a/bush.nif"}


def test_problems_name_each_gap():
    bad = mt.problems([form("1", r"a\Tree.nif", "bmv"), form("2", r"a\bush.nif", "bmv"),
                       form("3", r"b\lily.nif", "kotm"), form("4", r"c\gone.nif", "kotm")], MAN, DEPS)
    assert any("1 " in b and "bark_n" in b for b in bad)  # an unwaived normal
    assert any(b.startswith("2 ") and "keep" in b for b in bad) and any(b.startswith("2 ") and "slot 0" in b for b in bad)
    assert not any(b.startswith("3 ") for b in bad)  # its normal is waived
    assert any(b.startswith("4 ") and "manifest" in b for b in bad)


def test_norm():
    assert mt.norm("Textures\\Landscape\\X.DDS") == "textures/landscape/x.dds" == mt.norm("landscape\\x.dds")
    assert mt.norm("D:\\Steam\\Skyrim\\Data\\Textures\\a\\b.dds") == "textures/a/b.dds"
    assert mt.norm("textures\\\x08NOR") == "textures/nor"


def test_committed_manifest_covers_every_placed_form():
    import json
    from tools.argonia_world import db
    w = db.open()
    assert mt.problems(mt.placed_forms(w), mt.load(), json.loads(mt.DEPS.read_text(encoding="utf-8"))) == []
