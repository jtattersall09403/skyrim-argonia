"""The LOD key (tools/navmesh/lodkey.py): a navmesh-only change keeps it; a LAND change moves the terrain key alone, a placement the object key alone."""
import struct
import zlib

from tools.navmesh.lodkey import lod_keys


def rec(sig, fid, data, compress=False):
    flags = 0
    if compress:
        data, flags = struct.pack("<I", len(data)) + zlib.compress(data), 0x00040000
    return sig + struct.pack("<IIIIHH", len(data), flags, fid, 0, 44, 0) + data


def grup(label, gtype, body):
    return b"GRUP" + struct.pack("<I4siI", 24 + len(body), label, gtype, 0) + b"\0" * 4 + body


def esm(tmp_path, name, refr_x=1.0, navm=b"nav-a", n_navm=1, height=b"h1", water=b"w1"):
    sub = lambda s, p: s + struct.pack("<H", len(p)) + p  # noqa: E731
    navms = b"".join(rec(b"NAVM", 0x900 + i, sub(b"NVNM", navm)) for i in range(n_navm))
    cell = rec(b"CELL", 0x100, sub(b"XCLC", b"\0" * 12) + sub(b"XCLW", water))
    kids = grup(struct.pack("<I", 0x100), 6, grup(struct.pack("<I", 0x100), 9,
           rec(b"LAND", 0x200, sub(b"VHGT", height), compress=True)
           + rec(b"REFR", 0x300, sub(b"DATA", struct.pack("<6f", refr_x, 0, 0, 0, 0, 0))) + navms))
    body = rec(b"TES4", 0, sub(b"HEDR", struct.pack("<fII", 1.7, 3 + n_navm, 0x800))) \
        + grup(b"WRLD", 0, rec(b"WRLD", 0x50, sub(b"EDID", b"ARG\0")) + grup(struct.pack("<I", 0x50), 1, cell + kids)) \
        + grup(b"NAVI", 0, rec(b"NAVI", 0x60, sub(b"NVMI", navm)))
    p = tmp_path / name
    p.write_bytes(body)
    return p


def test_navmesh_only_change_keeps_both_keys(tmp_path):
    a = lod_keys(esm(tmp_path, "a.esm"))
    assert lod_keys(esm(tmp_path, "b.esm", navm=b"nav-b-longer", n_navm=3)) == a


def test_land_only_change_moves_the_terrain_key_alone(tmp_path):
    a, b = lod_keys(esm(tmp_path, "a.esm")), lod_keys(esm(tmp_path, "b.esm", height=b"h2"))
    assert b["terrain"] != a["terrain"] and b["object"] == a["object"]


def test_placement_only_change_moves_the_object_key_alone(tmp_path):
    a, b = lod_keys(esm(tmp_path, "a.esm")), lod_keys(esm(tmp_path, "b.esm", refr_x=2.0))
    assert b["object"] != a["object"] and b["terrain"] == a["terrain"]


def test_water_height_change_keeps_both_keys(tmp_path):
    assert lod_keys(esm(tmp_path, "a.esm")) == lod_keys(esm(tmp_path, "b.esm", water=b"w2"))


def test_each_tool_salt_moves_its_own_key(tmp_path):
    p = esm(tmp_path, "a.esm")
    a, b = lod_keys(p, [b"xlodgen a"], [b"dyn"]), lod_keys(p, [b"xlodgen b"], [b"dyn"])
    assert a["terrain"] != b["terrain"] and a["object"] == b["object"]
