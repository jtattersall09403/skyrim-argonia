"""A base's alternate textures (its model's MODS): the catalogue's `alt_tex`, the converter's variant of the model
per swap, and the draft bundle carrying the field to the studio (docs/design/place-studio.md, Assets)."""
import json
from pathlib import Path

import numpy as np
import pytest

from tools.places import assets, draft_bundle
from tools.places.assets import nifglb

CAT = Path(__file__).resolve().parents[2] / "out" / "places" / "catalogue" / "bases.jsonl"
DEAD = "King of the Murkmire.esp:52D306"     # HistTree01Dead: the living Hist's model, its crown swapped to nothing
LIVING = "King of the Murkmire.esp:035B34"   # HistTree01
HIST = "argonia/trees/hist trees/histtree01.nif"


def shape(name, tex=("bark.dds", "bark_n.dds")):
    p = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], np.float32)
    return {"name": name, "tris": 1, "P": p, "N": None, "UV": np.zeros((3, 2), np.float32), "C": None,
            "I": np.array([0, 1, 2], np.uint32), "m": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0], "block": "BSTriShape",
            "tex": list(tex), "shader": {}}


def test_a_swap_retextures_its_shape_and_a_missing_set_draws_purple():
    shapes = [shape("trunk"), shape("crown:1", ("leaf.dds", "leaf_n.dds")), shape("crown:2", ("leaf.dds", ""))]
    swap = [{"shape": "trunk", "index": 0, "textures": {"diffuse": "deadbark.dds", "normal": "deadbark_n.dds"}},
            {"shape": "crown:1", "index": 1, "textures": None}]
    out = nifglb.swapped(shapes, swap)
    assert [s["name"] for s in out] == ["trunk", "crown:1", "crown:2"]
    assert out[1].get("missing") and not out[2].get("missing")       # the game's missing texture: shown, not hidden
    assert out[0]["tex"][:2] == ["deadbark.dds", "deadbark_n.dds"] and shapes[0]["tex"][0] == "bark.dds"
    assert nifglb.swapped(shapes, None) is shapes


def test_two_shapes_of_one_name_are_told_apart_by_the_swaps_index():
    shapes = [shape("leaf"), shape("leaf")]
    for i, s in enumerate(shapes):
        s["order"] = i
    out = nifglb.swapped(shapes, [{"shape": "leaf", "index": 1, "textures": None}])
    assert [bool(s.get("missing")) for s in out] == [False, True]


def test_the_converter_keeps_one_variant_per_swap(monkeypatch):
    """Bases sharing a model: no swap is the model's own file; a swap is its own file under the swap's identity, the
    same for two bases with the same swap, another for a different swap."""
    if not CAT.exists() or not assets.resolver().read(assets.norm(HIST, "meshes")):
        pytest.skip("needs the catalogue and King of the Murkmire's Hist model")
    gone = [{"shape": "cedartree1:1", "index": 3, "txst": "Skyrim.esm:000028", "edid": None, "textures": None}]
    other = [{"shape": "cedartree1:1", "index": 3, "txst": "X:1", "edid": "T",
              "textures": {"diffuse": "textures/landscape/dirt01.dds", "normal": None}}]
    rows = {"A:1": {"model": HIST, "alt_tex": gone}, "B:1": {"model": HIST, "alt_tex": gone},
            "C:1": {"model": HIST, "alt_tex": other}, "D:1": {"model": HIST}}
    monkeypatch.setattr(draft_bundle, "catalogue", lambda path=None: rows)
    plain, a, b, c, d = (assets.mesh_info(HIST, 1, None, k) for k in (None, "A:1", "B:1", "C:1", "D:1"))
    assert a["glb"] == b["glb"] != plain["glb"] != c["glb"] != a["glb"] and d["glb"] == plain["glb"]
    assert a["shapes"] == plain["shapes"] == c["shapes"]
    from tools.places.assets import glb
    j, _ = glb.read(Path(a["glb"]).read_bytes())
    assert sum(m["name"] == nifglb.MISSING for m in j["materials"]) == 1   # the crown shape's purple
    assert "textures/landscape/dirt01.dds" in c["textures"]


def test_the_catalogue_lists_a_bases_alternate_textures():
    if not CAT.exists():
        pytest.skip("no catalogue")
    rows = {}
    for line in CAT.open(encoding="utf-8"):
        if "HistTree01" in line:
            r = json.loads(line)
            rows[r["key"]] = r
    if DEAD not in rows or "alt_tex" not in rows[DEAD]:
        pytest.skip("the catalogue predates alt_tex: python -m tools.places assets catalogue")
    alt = rows[DEAD]["alt_tex"]
    assert {a["shape"] for a in alt} == {"cedartree1:1", "cedartree1:2"}
    assert all(a["textures"] is None and a["txst"] == "Skyrim.esm:000028" for a in alt)   # a set no plugin holds
    assert "alt_tex" not in rows[LIVING]


def test_our_plugin_clears_a_dead_hists_crown_and_the_studio_draws_it_so(monkeypatch):
    """The dead Hists the places use point their crown at a texture set no plugin holds (purple in game): our plugin's
    copy points it at the clear set, the studio draws the replaced base as the copy, and the build swaps the ref."""
    from tools.places import own_bases
    gone = [{"shape": "cedartree1:1", "index": 3, "txst": "Skyrim.esm:000028", "edid": None, "textures": None}]
    alt = own_bases.alt_tex(DEAD, gone)
    assert alt[0]["txst"] == own_bases.CLEAR_TXST and alt[0]["textures"]["diffuse"] == "textures/sky/alpha.dds"
    assert own_bases.alt_tex("Other.esp:000001", gone) == gone
    refs = [{"id": "r", "base": DEAD}]
    rows = own_bases.plan_own(refs, lambda name: f"Argonia.esp:{abs(hash(name)) % 0xFFFFFF:06X}", "jal-veesa")
    assert [r["kind"] for r in rows] == ["txst", "static"] and rows[1]["copy"] == DEAD and rows[1]["clear"] == rows[0]["fk"]
    assert refs[0]["base"] == rows[1]["fk"]
    if CAT.exists() and assets.resolver().read(assets.norm(HIST, "meshes")):
        monkeypatch.setattr(draft_bundle, "catalogue", lambda path=None: {DEAD: {"model": HIST, "alt_tex": gone}})
        cut = assets.mesh_info(HIST, 1, None, DEAD)
        assert "textures/sky/alpha.dds" in cut["textures"]


def test_the_clear_texture_is_clear_under_the_crowns_alpha_test():
    from tools.places import own_bases
    from tools.places.assets import dds
    raw = assets.resolver().read(own_bases.TEXTURE_SETS[own_bases.CLEAR_TXST]["diffuse"])
    if not raw:
        pytest.skip("the game's textures are not here")
    assert np.asarray(dds.decode(raw).convert("RGBA"))[..., 3].max() < 45   # the lowest crown threshold of the five
