"""Patcher tests on synthetic NIFs made here (never a mod file): one fixture per op, the bars, the table."""
import struct

import numpy as np
import pytest
import yaml

from tools.argonia_world.meshes import nif as N
from tools.argonia_world.meshes import patch, source


def _sized(s: str) -> bytes:
    return struct.pack("<I", len(s)) + s.encode()


def make_nif(f1=0, f2=0, emit=(0, 0, 0), slots=("d.dds", "d_n.dds", ""), stretch_v=1.0, alpha=None) -> bytes:
    """A BS 100 NIF: block 0 BSTriShape (a 2x2 quad grid in one island), 1 BSLightingShaderProperty, 2 texture set."""
    types = ["BSTriShape", "BSLightingShaderProperty", "BSShaderTextureSet"] + (["NiAlphaProperty"] if alpha else [])
    pos = [(x, y, 0.0) for y in range(3) for x in range(3)]
    uv = [(x / 2, y / 2 / stretch_v) for y in range(3) for x in range(3)]
    tris = []
    for y in range(2):
        for x in range(2):
            a = y * 3 + x
            tris += [(a, a + 1, a + 4), (a, a + 4, a + 3)]
    desc = (6 & 0xF) | (4 << 8) | ((0x1 | 0x2) << 44)  # 24-byte vertex: pos+bitangent X, uv halfs, pad
    vd = b"".join(struct.pack("<4f", *p, 0) + np.array(u, np.float16).tobytes() + b"\0" * 4 for p, u in zip(pos, uv))
    shape = (struct.pack("<iI", 0, 0) + struct.pack("<i", -1) + struct.pack("<I", 14) + b"\0" * 12
             + struct.pack("<9f", 1, 0, 0, 0, 1, 0, 0, 0, 1) + struct.pack("<f", 1) + struct.pack("<i", -1)
             + b"\0" * 16 + struct.pack("<iii", -1, 1, 3 if alpha else -1) + struct.pack("<Q", desc)
             + struct.pack("<HHI", len(tris), len(pos), len(vd)) + vd
             + b"".join(struct.pack("<3H", *t) for t in tris))
    prop = (struct.pack("<IiI", 1, -1, 0) + struct.pack("<i", -1) + struct.pack("<II", f1, f2)
            + struct.pack("<4f", 0, 0, 1, 1) + struct.pack("<i", 2) + struct.pack("<4f", *emit, 1.0)
            + struct.pack("<I", 3) + struct.pack("<3f", 1, 1, 80) + struct.pack("<4f", 1, 1, 1, 1)
            + struct.pack("<2f", 0.3, 2.0) + b"\0" * 8)
    tex = struct.pack("<I", 9) + b"".join(_sized(s) for s in list(slots) + [""] * (9 - len(slots)))
    blocks = [shape, prop, tex] + ([struct.pack("<iIiHB", -1, 0, -1, *alpha)] if alpha else [])
    h = b"Gamebryo File Format, Version 20.2.0.7\n" + struct.pack("<IBII", 0x14020007, 1, 12, len(blocks))
    h += struct.pack("<I", 100) + b"\x01\0" * 3 + struct.pack("<H", len(types)) + b"".join(_sized(t) for t in types)
    h += struct.pack(f"<{len(blocks)}H", *range(len(blocks))) + struct.pack(f"<{len(blocks)}I", *map(len, blocks))
    h += struct.pack("<II", 1, 4) + _sized("Leaf") + struct.pack("<I", 0)
    return h + b"".join(blocks) + struct.pack("<II", 1, 0)


def entry(ops, kind="leaf", before=None, lore=False):
    e = {"mesh": "meshes/t.nif", "mod": "m", "forms": ["X"],
         "shapes": [{"shape": 0, "name": "Leaf", "kind": kind, "ops": ops, **({"before": before} if before else {})}]}
    if lore:
        e["lore_emit"] = "a cited glow"
    return e


SOFT = 1 << N.F2["Soft_Lighting"]
EMIT = 1 << N.F1["Own_Emit"]


def test_round_trip_is_byte_exact():
    d = make_nif(EMIT, SOFT, (0.1, 0.6, 0.6))
    assert N.Nif(d).to_bytes() == d
    m = patch.measure(N.Nif(d).shapes()[0])
    assert m["flags"] == ["Own_Emit", "Soft_Lighting"] and m["emissive"] == [[0.1, 0.6, 0.6], 1.0]
    assert m["stretch"] == pytest.approx(1.0, abs=0.01)


def test_clear_flags_and_emissive():
    n = N.Nif(make_nif(EMIT, 0, (0.1, 0.6, 0.6)))
    assert patch.bars(n, entry({})) and "Own_Emit" in patch.bars(n, entry({}))[0]
    assert not patch.bars(n, entry({}, lore=True))
    patch.apply(n, entry({"clear_flags": ["Own_Emit"], "emissive": {"rgb": [0, 0, 0], "mult": 1.0}}))
    n2 = N.Nif(n.to_bytes())
    assert patch.measure(n2.shapes()[0])["flags"] == [] and not patch.bars(n2, entry({}))
    assert patch.measure(n2.shapes()[0])["emissive"] == [[0, 0, 0], 1.0]


def test_set_flags():
    n = N.Nif(make_nif())
    patch.apply(n, entry({"set_flags": ["Double_Sided"]}))
    assert patch.measure(N.Nif(n.to_bytes()).shapes()[0])["flags"] == ["Double_Sided"]


def test_texture_slot_rewrites_the_block_size():
    d = make_nif(0, SOFT)
    n = N.Nif(d)
    assert "soft-lit with no soft-light map" in patch.bars(n, entry({}))[0]
    patch.apply(n, entry({"texture_slot": {2: "textures\\longer\\diffuse.dds", 1: "n.dds"}}))
    out = n.to_bytes()
    assert len(out) > len(d)
    m = patch.measure(N.Nif(out).shapes()[0])
    assert m["slot2"] == "textures\\longer\\diffuse.dds" and m["slot1"] == "n.dds"
    assert not patch.bars(N.Nif(out), entry({}))


def test_uv_scale_fit_and_number():
    n = N.Nif(make_nif(stretch_v=40.0))
    assert patch.measure(n.shapes()[0])["stretch"] == pytest.approx(40, rel=0.02)
    assert "UV stretch" in patch.bars(n, entry({}, kind="bark"))[0]
    patch.apply(n, entry({"uv_scale": {"axis": "v", "factor": "fit"}}, kind="bark"))
    n2 = N.Nif(n.to_bytes())
    assert patch.measure(n2.shapes()[0])["stretch"] <= patch.STRETCH_BAR
    assert not patch.bars(n2, entry({}, kind="bark"))
    n3 = N.Nif(make_nif(stretch_v=4.0))
    patch.apply(n3, entry({"uv_scale": {"axis": "v", "factor": 4}}))
    assert patch.measure(n3.shapes()[0])["stretch"] == pytest.approx(1.0, abs=0.02)


def test_vertex_colour_lum_to_adds_the_attribute(monkeypatch):
    monkeypatch.setattr(patch, "_diffuse_rgb", lambda p: [200, 200, 180])
    n = N.Nif(make_nif())  # no colour attribute
    m = patch.measure(n.shapes()[0])
    assert m["lum"] > patch.BARK_LUM_BAR and "pale" not in str(patch.bars(n, entry({}, kind="bark")))
    assert any("luminance" in b for b in patch.bars(n, entry({}, kind="bark")))
    patch.apply(n, entry({"vertex_colour": {"lum_to": 59.0}}, kind="bark"))
    n2 = N.Nif(n.to_bytes())
    m2 = patch.measure(n2.shapes()[0])
    assert m2["lum"] == pytest.approx(59, abs=0.6) and m2["sat"] == m["sat"] and "Vertex_Colors" in m2["flags"]
    assert m2["stretch"] == m["stretch"] and not patch.bars(n2, entry({}, kind="bark"))


def test_vertex_colour_sat_to(monkeypatch):
    monkeypatch.setattr(patch, "_diffuse_rgb", lambda p: [52, 68, 10])
    n = N.Nif(make_nif())
    e = entry({"vertex_colour": {"sat_to": patch.LEAF_SAT_BAR}})
    patch.apply(n, e)
    n2 = N.Nif(n.to_bytes())
    assert patch.measure(n2.shapes()[0])["sat"] == pytest.approx(0.71, abs=0.01) and not patch.bars(n2, e)


def test_before_mismatch_is_reported():
    n = N.Nif(make_nif())
    assert patch.apply(n, entry({}, before={"slot2": "x.dds"}))


def test_run_writes_and_lists(tmp_path):
    mods = tmp_path / "mods"
    (mods / "m" / "meshes").mkdir(parents=True)
    (mods / "m" / "meshes" / "t.nif").write_bytes(make_nif(EMIT, SOFT))
    t = tmp_path / "t.yaml"
    t.write_text(yaml.safe_dump({"meshes": [entry({"clear_flags": ["Own_Emit"], "texture_slot": {2: "d.dds"}})]}))
    lines = []
    assert patch.run([mods], out=tmp_path / "out", table=t, say=lines.append) == 0
    assert (tmp_path / "out" / "meshes" / "t.nif").exists()
    assert patch.run([mods], table=t, say=lines.append) == 0
    t.write_text(yaml.safe_dump({"meshes": [entry({})]}))
    assert patch.run([mods], table=t, say=lines.append) == 1  # the bars fail with no ops


def test_lz4_frame_decoder():
    # a hand-made frame: one compressed block "abcabcabcabc" = literal "abc" + match(offset 3, length 9)
    blk = bytes([0x35]) + b"abc" + struct.pack("<H", 3)
    frame = b"\x04\x22\x4d\x18" + bytes([0x60, 0x40, 0x82]) + struct.pack("<I", len(blk)) + blk + struct.pack("<I", 0)
    assert source.lz4_frame(frame) == b"abc" + b"abc" * 3


def test_the_table_loads_and_names_every_op_shape():
    for e in patch.load():
        assert e["mod"] and e["mesh"].startswith("meshes/") and e["forms"]
        for s in e["shapes"]:
            assert s["kind"] in ("leaf", "bark", "other")
            if s.get("ops"):
                assert s["reason"] and s["before"]
                for f in s["ops"].get("clear_flags", []) + s["ops"].get("set_flags", []):
                    assert f in N.F1 or f in N.F2


def test_alpha_op_sets_the_threshold_and_keeps_the_flags():
    d = make_nif(alpha=(0x12EC, 80))
    n = N.Nif(d)
    assert n.shapes()[0].alpha == (0x12EC, 80)
    assert patch.apply(n, entry({"alpha": {"threshold": 127}, "clear_flags": ["Soft_Lighting"]},
                                before={"alpha": [0x12EC, 80]})) == []
    assert N.Nif(n.to_bytes()).shapes()[0].alpha == (0x12EC, 127)


def test_bark_stretch_tail_fails_unless_owed():
    n = N.Nif(make_nif(stretch_v=9.0))
    e = entry({}, kind="bark")
    assert any("p90" in b for b in patch.bars(n, e))
    e["p90_owed"] = "measured; a re-unwrap is owed"
    assert not any("p90" in b for b in patch.bars(n, e))


def test_the_tree_look_defects_carry_their_ops():
    """Lane 1.15-r6-tree-look: each defect's mesh is in the table with the op that fixes it."""
    want = {"meshes/argonia/trees/greguire/eruttree01tall.nif": {"texture_slot", "uv_scale", "clear_flags"},
            "meshes/argonia/trees/greguire/swampplant08a.nif": {"clear_flags"},
            "meshes/argonia/trees/smallmushroom01green.nif": {"clear_flags"},
            "meshes/landscape/plants/esalixshrub03.nif": {"clear_flags", "vertex_colour"},
            "meshes/landscape/trees/ztgorsebush04statwhite.nif": {"clear_flags", "vertex_colour"}}
    got = {e["mesh"]: {k for s in e["shapes"] for k in (s.get("ops") or {})} for e in patch.load()}
    for mesh, ops in want.items():
        assert ops <= got.get(mesh, set()), mesh


def _absent(tmp_path, kept):
    import json
    mods = tmp_path / "mods"
    (mods / "m").mkdir(parents=True)
    t = tmp_path / "t.yaml"
    t.write_text(yaml.safe_dump({"meshes": [entry({})]}))
    d = tmp_path / "deps.json"
    d.write_text(json.dumps({"keep": {"m": ["meshes/t.nif"] if kept else []}}))
    lines = []
    return patch.run([mods], table=t, say=lines.append, deps=d), lines


def test_absent_and_unplaced_is_skipped(tmp_path):
    rc, lines = _absent(tmp_path, kept=False)
    assert rc == 0 and any("skipped: not staged, not placed" in x for x in lines)


def test_absent_but_placed_fails(tmp_path):
    rc, lines = _absent(tmp_path, kept=True)
    assert rc == 1 and any(x.startswith("FAIL") for x in lines)
