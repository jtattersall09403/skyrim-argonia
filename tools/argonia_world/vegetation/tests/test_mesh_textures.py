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


ALT = {"meshes": {"meshes/a/fern.nif": {"row": "bmv", "laid": "bmv", "slots": [[0, "textures/a/fern.dds"]]}},
       "forms": {"1:Black Marsh.esm": [["Fern", "textures/a/ferny.dds", None]],
                 "2:Black Marsh.esm": [["Moss", "textures/a/moss.dds", "textures/a/moss_n.dds"]],
                 "3:Black Marsh.esm": [["Ok", "textures/a/fern.dds", "textures/vurt_amanita3_n.dds"]]},
       "sources": {"textures/a/fern.dds": "bmv", "textures/a/ferny.dds": None, "textures/a/moss.dds": "bmv",
                   "textures/a/moss_n.dds": None, "textures/vurt_amanita3_n.dds": None}}


def test_mods_gap_is_red_until_overridden(monkeypatch):
    monkeypatch.setattr(mt, "ALT_DROPPED", {})
    monkeypatch.setattr(mt, "ALT_UNFIXABLE", {})
    fs = [form(k, r"a\fern.nif", "bmv") for k in ("1:Black Marsh.esm", "2:Black Marsh.esm", "3:Black Marsh.esm")]
    bad = mt.problems(fs, ALT, {"mods": []})
    assert any(b.startswith("1:") and "MODS slot 0 textures/a/ferny.dds" in b for b in bad)  # a missing TXST diffuse
    assert any(b.startswith("2:") and "MODS slot 1" in b for b in bad)  # an unwaived TXST normal
    assert not any(b.startswith("3:") for b in bad)  # resolved diffuse, waived normal
    assert mt.untextured_forms(ALT) == {"1:Black Marsh.esm"}
    monkeypatch.setattr(mt, "ALT_DROPPED", {"1:Black Marsh.esm": "x", "2:Black Marsh.esm": "y"})
    assert mt.problems(fs, ALT, {"mods": []}) == [] and mt.untextured_forms(ALT) == set()  # the override resolves it


def test_unfixable_is_dropped_and_red_when_placed(monkeypatch):
    monkeypatch.setattr(mt, "ALT_DROPPED", {})
    monkeypatch.setattr(mt, "ALT_UNFIXABLE", {"3:Black Marsh.esm": "a glow in the NIF"})
    assert "3:Black Marsh.esm" in mt.untextured_forms(ALT)
    assert mt.alt_problems(["3:Black Marsh.esm"], ALT) == ["3:Black Marsh.esm: placed, but a glow in the NIF"]


def test_override_readback(monkeypatch):
    monkeypatch.setattr(mt, "ALT_DROPPED", {"1:Black Marsh.esm": "x", "2:Black Marsh.esm": "y", "4:Black Marsh.esm": "z"})
    bad = mt.override_problems({"1:Black Marsh.esm": [], "2:Black Marsh.esm": [["Moss", "t", None]]})
    assert bad == ["4:Black Marsh.esm: no record read", "2:Black Marsh.esm: 1 MODS sets still draw (no override, or MODS kept)"]


def test_committed_overrides_are_unique_and_disjoint():
    assert not set(mt.ALT_DROPPED) & set(mt.ALT_UNFIXABLE)
    assert all(k.endswith(".esm") or k.endswith(".esp") for k in mt.ALT_DROPPED)
