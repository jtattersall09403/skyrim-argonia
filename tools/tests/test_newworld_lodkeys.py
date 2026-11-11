"""Each LOD step's key follows what that step reads (tools/newworld/world/lodkeys.py): a change reruns only the
steps it reaches."""
import struct
import zlib

from tools.newworld.world import lodkeys

SETTINGS = {"terrain": {"tool": {"rev": 1}, "post": {"rev": 1, "meshes": {"QualityLOD4": 4}}},
            "texgen": {"tool": {"rev": 1}, "post": {"rev": 1}}, "dyndolod": {"rev": 1}}
TOOLS = {"xlodgen": "x1", "dyndolod": "d1", "dyndolod-resources": "r1"}


def sub(sig, data):
    return sig + struct.pack("<H", len(data)) + data


def rec(sig, formid, body, flags=0, compress=False):
    if compress:
        body = struct.pack("<I", len(body)) + zlib.compress(body)
        flags |= lodkeys.COMPRESSED
    return sig + struct.pack("<IIIII", len(body), flags, formid, 0, 0) + body


def grup(label, kind, content):
    return b"GRUP" + struct.pack("<I", 24 + len(content)) + label + struct.pack("<iII", kind, 0, 0) + content


def esm(land=b"\x01" * 40, water=1.0, ref_x=10.0, stat_flags=0, mnam=b"\0" * 28, interior=b"a", marker_x=0.0, cell_name=b""):
    refr = rec(b"REFR", 0x900, sub(b"NAME", struct.pack("<I", 0x800)) + sub(b"DATA", struct.pack("<6f", ref_x, 0, 0, 0, 0, 0)))
    refr += rec(b"REFR", 0x901, sub(b"NAME", struct.pack("<I", 0x32)) + sub(b"DATA", struct.pack("<6f", marker_x, 0, 0, 0, 0, 0)))
    cell = rec(b"CELL", 0x700, (sub(b"EDID", cell_name + b"\0") if cell_name else b"") + sub(b"DATA", b"\x02\x00") + sub(b"XCLC", struct.pack("<iiI", 3, -4, 0)) + sub(b"XCLW", struct.pack("<f", water))
               + sub(b"XCLR", b"\x01\x02\x03\x04"))
    children = grup(struct.pack("<I", 0x700), 6, grup(struct.pack("<I", 0x700), 9, rec(b"LAND", 0x701, sub(b"VHGT", land), compress=True) + refr))
    wrld = rec(b"WRLD", 0x600, sub(b"EDID", b"ArgoniaBlackMarsh\0") + sub(b"DNAM", struct.pack("<ff", -2048, 0)) + sub(b"MNAM", mnam))
    world = grup(b"WRLD", 0, wrld + grup(struct.pack("<I", 0x600), 1, grup(struct.pack("<i", 0), 4, grup(struct.pack("<i", 0), 5, cell + children))))
    stat = grup(b"STAT", 0, rec(b"STAT", 0x800, sub(b"EDID", b"Tree\0") + sub(b"MODL", b"t.nif\0"), flags=stat_flags))
    ltex = grup(b"LTEX", 0, rec(b"LTEX", 0x500, sub(b"EDID", b"Mud\0")))
    cells = grup(b"CELL", 0, rec(b"CELL", 0x400, sub(b"EDID", interior + b"\0") + sub(b"XCLW", struct.pack("<f", 5.0))))
    return rec(b"TES4", 0, sub(b"HEDR", b"\0" * 12)) + ltex + stat + cells + world


def keys(tmp_path, raw, settings=SETTINGS, tools=TOOLS, preset="Medium", lodmodels="", bill=b"p;00000800;Tree,True\n", rules=b"[Skyrim LODGen]\n"):
    plugin = tmp_path / "plugin"
    (plugin / "map" / "LODSettings").mkdir(parents=True, exist_ok=True)
    (plugin / "ArgoniaNewWorld.esm").write_bytes(raw)
    (plugin / "map" / "LODSettings" / "ArgoniaBlackMarsh.lod").write_bytes(b"\0" * 16)
    (plugin / "map" / "DynDOLOD_SSE_TexGen_Billboards_argonianewworldesm.txt").write_bytes(bill)
    (plugin / "map" / "DynDOLOD_SSE_argonianewworldesm.ini").write_bytes(rules)
    k = lodkeys.keys(plugin, preset, lodmodels, settings, tools)
    return k["terrain"], k["texgen"], k["dyndolod"]


def test_a_change_to_placed_references_alone_reruns_dyndolod_and_not_terrain(tmp_path):
    t0, x0, d0 = keys(tmp_path, esm())
    t1, x1, d1 = keys(tmp_path, esm(ref_x=99.0))  # a reference moved (a place built)
    assert t1 == t0 and x1 == x0 and d1 != d0
    # a place's interior cell is no terrain either, but DynDOLOD reads the file it is in
    ti, xi, di = keys(tmp_path, esm(interior=b"b"))
    assert (ti, xi) == (t0, x0) and di != d0


def test_what_the_map_stage_writes_reruns_nothing(tmp_path):
    # the map's box, a teleport marker moved, a cell named for its teleport: no LOD is made from any of them
    k0 = keys(tmp_path, esm())
    assert keys(tmp_path, esm(mnam=b"\1" * 28)) == k0
    assert keys(tmp_path, esm(marker_x=512.0)) == k0
    assert keys(tmp_path, esm(cell_name=b"ANWHelstrom")) == k0


def test_a_new_billboard_plan_reruns_texgen_and_dyndolod_and_not_terrain(tmp_path):
    t0, x0, d0 = keys(tmp_path, esm())
    t1, x1, d1 = keys(tmp_path, esm(), bill=b"p;00000800;Tree,True\np;00000801;Palm,True\n")
    assert t1 == t0 and x1 != x0 and d1 != d0
    t2, x2, d2 = keys(tmp_path, esm(stat_flags=0x40))  # Has Tree LOD set on a base
    assert t2 == t0 and x2 != x0 and d2 != d0


def test_land_or_water_reruns_terrain_and_what_stands_on_it(tmp_path):
    t0, x0, d0 = keys(tmp_path, esm())
    for changed in (esm(land=b"\x02" * 40), esm(water=7.0)):
        t1, x1, d1 = keys(tmp_path, changed)
        assert t1 != t0 and x1 == x0 and d1 != d0


def test_a_steps_settings_and_tool_rekey_that_step_only(tmp_path):
    t0, x0, d0 = keys(tmp_path, esm())
    t1, x1, d1 = keys(tmp_path, esm(), settings={**SETTINGS, "dyndolod": {"rev": 2}})
    assert (t1, x1) == (t0, x0) and d1 != d0
    t2, x2, d2 = keys(tmp_path, esm(), settings={**SETTINGS, "terrain": {"tool": {"rev": 1}, "post": {"rev": 1, "meshes": {"QualityLOD4": 5}}}})
    assert t2 != t0 and x2 == x0 and d2 != d0
    t3, x3, d3 = keys(tmp_path, esm(), tools={**TOOLS, "xlodgen": "x2"})
    assert t3 != t0 and x3 == x0
    # rules, LOD models and the preset are DynDOLOD's alone
    for k in (keys(tmp_path, esm(), rules=b"[Skyrim LODGen]\nLODGen1=a.nif,Full,None,None,None,FarLOD,Unchanged,0\n"),
              keys(tmp_path, esm(), lodmodels="abc"), keys(tmp_path, esm(), preset="Low")):
        assert k[:2] == (t0, x0) and k[2] != d0


def test_the_committed_settings_hold_every_step():
    import json
    s = json.loads(lodkeys.SETTINGS.read_text())
    assert all("rev" in x for x in (s["terrain"]["tool"], s["terrain"]["post"], s["texgen"]["tool"], s["texgen"]["post"], s["dyndolod"]))
    m = s["terrain"]["post"]["meshes"]
    assert m["ProtectCellBorders"] == "True" and m["WaterDeltaLOD32"] == 550
    assert s["dyndolod"]["untick"] == ["Dynamic LOD", "Occlusion data", "Terrain underside"]


def test_a_change_to_our_own_pass_never_rekeys_the_tool_run(tmp_path):
    def all_keys(settings):
        plugin = tmp_path / "plugin"
        keys(tmp_path, esm())
        return lodkeys.keys(plugin, "Medium", "", settings, TOOLS)
    a = all_keys(SETTINGS)
    b = all_keys({**SETTINGS, "terrain": {"tool": {"rev": 1}, "post": {"rev": 2, "meshes": {"QualityLOD4": 9}}},
                  "texgen": {"tool": {"rev": 1}, "post": {"rev": 2}}})
    assert (b["terrain-tool"], b["texgen-tool"]) == (a["terrain-tool"], a["texgen-tool"])  # xLODGen and TexGen stand
    assert b["terrain"] != a["terrain"] and b["texgen"] != a["texgen"] and b["dyndolod"] != a["dyndolod"]
    c = all_keys({**SETTINGS, "terrain": {"tool": {"rev": 2}, "post": SETTINGS["terrain"]["post"]}})
    assert c["terrain-tool"] != a["terrain-tool"] and c["terrain"] != a["terrain"] and c["texgen"] == a["texgen"]


def test_a_steps_code_key_follows_its_own_scripts_settings_and_tools(tmp_path):
    """The proof keys (what `lod.sh selftest` records and `lod.sh stage` asks for): a change to the plan's writer
    asks texgen and dyndolod to be proven again and leaves terrain; a driver script asks all three; a step's own
    setting or tool asks that step alone."""
    for files in lodkeys.PROOF.values():
        for f in files:
            (tmp_path / f).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / f).write_text(f)
            assert (lodkeys.REPO / f).exists(), f
    base = lodkeys.proof_keys(SETTINGS, TOOLS, tmp_path)
    assert set(base) == {"terrain", "texgen", "dyndolod"}

    def moved(settings=SETTINGS, tools=TOOLS):
        now = lodkeys.proof_keys(settings, tools, tmp_path)
        return {s for s in base if now[s] != base[s]}
    assert moved() == set()
    (tmp_path / "tools/newworld/world/lodplan.py").write_text("changed")
    assert moved() == {"texgen", "dyndolod"}
    (tmp_path / "tools/newworld/world/lodplan.py").write_text("tools/newworld/world/lodplan.py")
    (tmp_path / "infra/gpu-box/lod.ps1").write_text("changed")
    assert moved() == {"terrain", "texgen", "dyndolod"}
    (tmp_path / "infra/gpu-box/lod.ps1").write_text("infra/gpu-box/lod.ps1")
    assert moved(settings={**SETTINGS, "dyndolod": {"rev": 2}}) == {"dyndolod"}
    assert moved(tools={**TOOLS, "xlodgen": "x2"}) == {"terrain"}


def test_the_small_world_is_keyed_under_its_own_names(tmp_path):
    m = tmp_path / "map/LODSettings"
    m.mkdir(parents=True)
    (m / "ArgoniaSmallWorld.lod").write_bytes(b"\0" * 16)
    (tmp_path / "ArgoniaSmallWorld.esm").write_bytes(esm())
    k = lodkeys.keys(tmp_path, settings=SETTINGS, tools=TOOLS, esm="ArgoniaSmallWorld.esm", world="ArgoniaSmallWorld")
    assert k["terrain"] and k["dyndolod"] and set(k["proof"]) == {"terrain", "texgen", "dyndolod"}
