"""tools/places/assets: GLB writing, the NIF shape to glTF rules, DDS to WebP, the cache cap, resolution order,
the catalogue's derived fields. Synthetic inputs only: no game file is read."""
import io
import json
import os
import threading
import time

import numpy as np
import pytest
from PIL import Image

from tools.places.assets import cache, catalogue, dds, glb, nifglb, resolve


def shape(name="s", tris=None, verts=None, **kw):
    P = np.array(verts if verts is not None else [[0, 0, 0], [10, 0, 0], [0, 10, 0], [10, 10, 5]], np.float32)
    I = np.array(tris if tris is not None else [[0, 1, 2], [1, 3, 2]], np.uint32)
    s = {"name": name, "block": "BSTriShape", "verts": len(P), "tris": len(I), "hidden": False, "skinned": False,
         "m": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0], "P": P, "I": I, "N": np.tile([0, 0, 1.0], (len(P), 1)).astype(np.float32),
         "UV": np.zeros((len(P), 2), np.float32), "C": None, "tex": ["textures\\Foo\\Bar.dds", ""],
         "shader": {"type": "BSLightingShaderProperty", "two_sided": False, "vertex_colors": False, "vertex_alpha": False,
                    "flags2": 0, "uv_offset": [0, 0], "uv_scale": [1, 1]}}
    s.update(kw)
    return s


def test_glb_round_trip_keeps_matrix_material_and_uri():
    s = shape(m=[1, 0, 0, 5, 0, 1, 0, 6, 0, 0, 1, 7], alpha={"flags": 0x200 | 0xEC, "threshold": 128})
    s["shader"]["two_sided"] = True
    data, meta = nifglb.build({"shapes": [s]})
    j, b = glb.read(data)
    assert meta["tris"] == 2 and meta["textures"] == ["textures/foo/bar.dds"]
    assert j["images"][0]["uri"] == "/api/asset/tex?path=textures/foo/bar.dds&size=512"
    assert nifglb.uri_path(j["images"][0]["uri"]) == "textures/foo/bar.dds"
    mat = j["materials"][0]
    assert mat["alphaMode"] == "MASK" and abs(mat["alphaCutoff"] - 128 / 255) < 1e-3 and mat["doubleSided"]
    assert j["nodes"][0]["matrix"][12:15] == [5, 6, 7]  # translation in glTF's column-major slot
    assert glb.accessor(j, b, j["meshes"][0]["primitives"][0]["indices"]).tolist() == [0, 1, 2, 1, 3, 2]
    assert meta["bounds"] == [[5.0, 6.0, 7.0], [15.0, 16.0, 12.0]]


def test_tree_vertex_alpha_is_wind_not_opacity():
    C = np.array([[0.5, 0.5, 0.5, 0.0]] * 4, np.float32)
    s = shape(C=C)
    s["shader"].update(vertex_colors=True, vertex_alpha=True, flags2=nifglb.TREE_ANIM)
    j, b = glb.read(nifglb.build({"shapes": [s]})[0])
    col = glb.accessor(j, b, j["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"])
    assert np.allclose(col[:, 3], 1.0)
    s["shader"]["flags2"] = 0
    j, b = glb.read(nifglb.build({"shapes": [s]})[0])
    assert np.allclose(glb.accessor(j, b, j["meshes"][0]["primitives"][0]["attributes"]["COLOR_0"])[:, 3], 0.0)


def test_hidden_shapes_left_out_skinned_kept_and_garbage_texture_ignored():
    with pytest.raises(nifglb.MeshError):
        nifglb.build({"shapes": [shape(hidden=True)]})
    meta = nifglb.build({"shapes": [shape(skinned=True, tex=["\x08nor", "textures\\"])]})[1]
    assert meta["tris"] == 2 and meta["textures"] == []


def test_level_one_simplifies_heavy_mesh_only():
    n = 60
    xs, ys = np.meshgrid(np.arange(n), np.arange(n))
    P = np.stack([xs.ravel(), ys.ravel(), np.sin(xs.ravel() / 5.0) * 3], 1).astype(np.float32)
    T = []
    for y in range(n - 1):
        for x in range(n - 1):
            a = y * n + x
            T += [[a, a + 1, a + n], [a + 1, a + n + 1, a + n]]
    s = shape(verts=P, tris=T, N=None, UV=np.zeros((len(P), 2), np.float32))
    full = nifglb.build({"shapes": [s]}, 0)[1]
    light = nifglb.build({"shapes": [s]}, 1)[1]
    assert full["tris"] == len(T) > nifglb.LIGHT_TRIS
    assert light["tris"] <= max(nifglb.LIGHT_TRIS, len(T) // 4) * 1.05 and light["tris_full"] == len(T)
    small = shape()
    assert nifglb.build({"shapes": [small]}, 1)[1]["tris"] == 2


def test_placeholder_is_a_flagged_box_of_the_bounds():
    data, meta = nifglb.placeholder([[-10, -20, 0], [10, 20, 30]], "why")
    j, b = glb.read(data)
    P = glb.accessor(j, b, j["meshes"][0]["primitives"][0]["attributes"]["POSITION"])
    assert meta["placeholder"] and meta["why"] == "why" and j["extras"]["argonia"]["placeholder"]
    assert P.min(0).tolist() == [-10, -20, 0] and P.max(0).tolist() == [10, 20, 30]


def dds_bytes(im: Image.Image, fmt: str | None = None) -> bytes:
    out = io.BytesIO()
    im.save(out, "DDS", **({"pixel_format": fmt} if fmt else {}))
    return out.getvalue()


def test_dds_to_webp_halves_to_size_and_keeps_alpha():
    a = np.zeros((256, 128, 4), np.uint8)
    a[..., 0] = 200
    a[..., 3] = 255
    a[:64, :, 3] = 0
    raw = dds_bytes(Image.fromarray(a, "RGBA"))
    data, meta = dds.to_webp(raw, 100)
    im = Image.open(io.BytesIO(data))
    assert im.format == "WEBP" and im.size == (64, 128) and meta["alpha"] and im.mode == "RGBA"
    _, m2 = dds.to_webp(raw, 100, keep_alpha=False)
    assert not m2["alpha"]
    assert dds.clamp_size(300) == 512 and dds.clamp_size(5000) == 2048


def test_dds_bc_formats_decode():
    a = np.full((64, 64, 4), 128, np.uint8)
    for fmt in ("DXT1", "DXT5", "BC7"):
        try:
            raw = dds_bytes(Image.fromarray(a, "RGBA"), fmt)
        except (ValueError, OSError, KeyError):
            continue  # this Pillow cannot write that format; decoding is still covered by the game proofs
        data, meta = dds.to_webp(raw, 64)
        assert meta["w"] == 64 and data[:4] == b"RIFF"


def test_cache_evicts_least_recently_used(tmp_path, monkeypatch):
    monkeypatch.setenv("PLACES_OUT", str(tmp_path))
    now = time.time()
    for i in range(10):
        p = cache.path("mesh", f"{i:02x}" * 32, "l0.glb")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * 1000)
        os.utime(p, (now - 100 + i, now - 100 + i))
    cache.touch(cache.path("mesh", "00" * 32, "l0.glb"))  # the oldest is used again
    land = cache.root() / "land" / "Skyrim.esm_000001.webp"   # the land set is kept however old
    land.parent.mkdir(parents=True)
    land.write_bytes(b"x" * 400)
    os.utime(land, (now - 500, now - 500))
    r = cache.evict(cap=5400)
    assert r["removed"] == 6 and r["after"] <= 4900 and land.exists()
    left = {p.name[:2] for p in (tmp_path / "assets" / "mesh").rglob("*.glb")}
    assert left == {"00", "07", "08", "09"}


def test_concurrent_missing_mesh_converts_once(tmp_path, monkeypatch):
    monkeypatch.setenv("PLACES_OUT", str(tmp_path))
    import tools.places.assets as A

    class R:
        def read(self, k):
            return None

        def where(self, k):
            return None
    monkeypatch.setattr(A, "resolver", lambda: R())
    calls = []
    real = nifglb.placeholder
    monkeypatch.setattr(nifglb, "placeholder", lambda b, w: (calls.append(1), real(b, w))[1])
    out = []
    ts = [threading.Thread(target=lambda: out.append(A.mesh_info("x/y.nif", 0, [[0, 0, 0], [1, 1, 1]]))) for _ in range(6)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(calls) == 1 and len({o["glb"] for o in out}) == 1 and out[0]["placeholder"]


def test_resolution_loose_winner_case_insensitive_then_archive(tmp_path):
    stack, data, assets = tmp_path / "stack", tmp_path / "Data", tmp_path / "nw"
    f = stack / "MO2" / "mods" / "bmv" / "Meshes" / "Foo" / "Bar.NIF"
    f.parent.mkdir(parents=True)
    f.write_bytes(b"bmv")
    g = assets / "tropical-skyrim-sse" / "textures" / "a.dds"
    g.parent.mkdir(parents=True)
    g.write_bytes(b"ts")
    (stack / "MO2" / "profiles" / "NewWorld").mkdir(parents=True)
    (stack / "MO2" / "profiles" / "NewWorld" / "modlist.txt").write_text("+tropical-skyrim-sse\n+bmv\n")
    (stack / "installed-NewWorld.json").write_text(json.dumps({"files": {
        "meshes\\foo\\bar.nif": ["bmv", "x"], "textures\\a.dds": ["tropical-skyrim-sse", "y"]}}))
    data.mkdir()
    r = resolve.Resolver(stack, data, assets)
    assert r.read(resolve.norm("Foo/BAR.nif", "meshes")) == b"bmv" and r.where("meshes\\foo\\bar.nif") == "mod:bmv"
    assert r.read(resolve.norm("textures\\A.dds", "textures")) == b"ts"
    assert r.read("meshes\\none.nif") is None
    assert resolve.norm("Data\\Meshes\\X.nif", "meshes") == "meshes\\x.nif"


def test_resolution_ignores_case_along_the_whole_path_when_a_mod_holds_two_spellings_of_a_folder(tmp_path):
    # Tropical Skyrim holds both `Meshes/` and `meshes/`: a file under either is found by the lower-case data path
    stack, data, assets = tmp_path / "stack", tmp_path / "data", tmp_path / "nw"
    (assets / "ts" / "meshes" / "landscape" / "trees").mkdir(parents=True)
    (assets / "ts" / "meshes" / "landscape" / "trees" / "palm.nif").write_bytes(b"tree")
    (assets / "ts" / "Meshes" / "Landscape" / "Grass").mkdir(parents=True)
    (assets / "ts" / "Meshes" / "Landscape" / "Grass" / "FernGrass01.NIF").write_bytes(b"grass")
    (assets / "ts" / "Meshes" / "landscape" / "grass").mkdir(parents=True)
    (assets / "ts" / "Meshes" / "landscape" / "grass" / "reed.nif").write_bytes(b"reed")
    stack.mkdir()
    data.mkdir()
    (stack / "installed-NewWorld.json").write_text(json.dumps({"files": {
        "meshes\\landscape\\grass\\ferngrass01.nif": ["ts", "x"], "meshes\\landscape\\trees\\palm.nif": ["ts", "x"],
        "Meshes/Landscape/Grass/reed.nif": ["ts", "x"], "meshes\\landscape\\grass\\absent.nif": ["ts", "x"]}}))
    r = resolve.Resolver(stack, data, assets)
    assert r.read(resolve.norm("Landscape\\Grass\\FernGrass01.nif", "meshes")) == b"grass"
    assert r.read(resolve.norm("landscape\\trees\\palm.nif", "meshes")) == b"tree"
    assert r.read(resolve.norm("landscape/grass/REED.nif", "meshes")) == b"reed"
    assert r.loose_file("meshes\\landscape\\grass\\absent.nif") is None


def test_catalogue_fields():
    assert catalogue.is_nordic({"edid": "WRHouse01", "model": "architecture/whiterun/wrhouse01.nif"})
    assert catalogue.is_nordic({"edid": "TreePineForest01", "model": "landscape/trees/treepineforest01.nif"})
    assert not catalogue.is_nordic({"edid": "BMStiltHut01", "model": "bm/architecture/stilthut01.nif"})
    for edid, model in (("RockM02Ice", "landscape/rocks/rockm02.nif"), ("IcePileS04", "x.nif"),
                        ("CaveIHall1Way64L01ice", "x.nif"), ("X", "landscape/ice/x.nif")):
        assert catalogue.is_nordic({"edid": edid, "model": model}), edid
    for edid, model in (("LoadScreenDSApprentice01", "loadscreenart/loadscreendsapprentice01.nif"),
                        ("BMChalice01", "bm/clutter/chalice.nif"), ("FoodIceCream", "clutter/icecream.nif")):
        assert not catalogue.is_nordic({"edid": edid, "model": model}), edid
    assert catalogue.kind({"type": "STAT", "model": "landscape/rocks/rockcliff01.nif", "edid": "RockCliff01"}) == "rock"
    assert catalogue.kind({"type": "TREE", "model": "x.nif", "edid": "T"}) == "tree"
    assert catalogue.words("BMStiltHut01") == ["bm", "stilt", "hut"]
    t = catalogue.descriptor({"type": "STAT", "edid": "BMStiltHut01", "name": None, "model": "bm/stilthut01.nif",
                              "bounds": [[-140, -140, 0], [140, 140, 350]], "nordic": False}, "Black Marsh & Valenwood")
    assert "stilt hut" in t and "static object" in t and "Black Marsh" in t and "4.0 by 4.0 m" in t


def test_a_converted_source_is_not_read_again_and_a_passing_failure_is_not_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("PLACES_OUT", str(tmp_path))
    import tools.places.assets as A

    class R:
        reads = 0
        stamp = 1

        def ident(self, k):
            return ("loose", k, 3, self.stamp)

        def read(self, k):
            R.reads += 1
            return b"nif%d" % self.stamp

        def where(self, k):
            return "mod:x"
    r = R()
    monkeypatch.setattr(A, "resolver", lambda: r)
    monkeypatch.setattr(A, "_hashed", {})
    fails = [nifglb.NotNow("nifdump ran out of time"), nifglb.MeshError("not a NIF")]
    monkeypatch.setattr(nifglb, "dump", lambda raw, tmp=None: (_ for _ in ()).throw(fails.pop(0)))
    first = A.mesh_info("a/b.nif")
    assert first["placeholder"] and first["retry"] and ".retry." in first["glb"]
    second = A.mesh_info("a/b.nif")   # converted again: this time the mesh itself is at fault, and that is kept
    assert second["placeholder"] and not second.get("retry") and ".retry." not in second["glb"] and not fails
    reads = R.reads
    assert A.mesh_info("a/b.nif")["glb"] == second["glb"] and R.reads == reads   # a hit reads no source
    r.stamp = 2                                                                   # the source file changed
    monkeypatch.setattr(nifglb, "dump", lambda raw, tmp=None: (_ for _ in ()).throw(nifglb.MeshError("still not")))
    assert A.mesh_info("a/b.nif")["glb"] != second["glb"] and R.reads == reads + 1
