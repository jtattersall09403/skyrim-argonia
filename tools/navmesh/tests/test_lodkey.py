"""The LOD key (tools/navmesh/lodkey.py): a navmesh-only change keeps it; a placement or height change moves it."""
import struct
import zlib

from tools.navmesh.lodkey import lod_key


def rec(sig, fid, data, compress=False):
    flags = 0
    if compress:
        data, flags = struct.pack("<I", len(data)) + zlib.compress(data), 0x00040000
    return sig + struct.pack("<IIIIHH", len(data), flags, fid, 0, 44, 0) + data


def grup(label, gtype, body):
    return b"GRUP" + struct.pack("<I4siI", 24 + len(body), label, gtype, 0) + b"\0" * 4 + body


def esm(tmp_path, name, refr_x=1.0, navm=b"nav-a", n_navm=1, height=b"h1"):
    sub = lambda s, p: s + struct.pack("<H", len(p)) + p  # noqa: E731
    navms = b"".join(rec(b"NAVM", 0x900 + i, sub(b"NVNM", navm)) for i in range(n_navm))
    cell = rec(b"CELL", 0x100, sub(b"XCLC", b"\0" * 12))
    kids = grup(struct.pack("<I", 0x100), 6, grup(struct.pack("<I", 0x100), 9,
           rec(b"LAND", 0x200, sub(b"VHGT", height), compress=True)
           + rec(b"REFR", 0x300, sub(b"DATA", struct.pack("<6f", refr_x, 0, 0, 0, 0, 0))) + navms))
    body = rec(b"TES4", 0, sub(b"HEDR", struct.pack("<fII", 1.7, 3 + n_navm, 0x800))) \
        + grup(b"WRLD", 0, rec(b"WRLD", 0x50, sub(b"EDID", b"ARG\0")) + grup(struct.pack("<I", 0x50), 1, cell + kids)) \
        + grup(b"NAVI", 0, rec(b"NAVI", 0x60, sub(b"NVMI", navm)))
    p = tmp_path / name
    p.write_bytes(body)
    return p


def test_navmesh_only_change_keeps_the_key(tmp_path):
    a = lod_key(esm(tmp_path, "a.esm"))
    assert lod_key(esm(tmp_path, "b.esm", navm=b"nav-b-longer", n_navm=3)) == a


def test_placement_or_ground_change_moves_the_key(tmp_path):
    a = lod_key(esm(tmp_path, "a.esm"))
    assert lod_key(esm(tmp_path, "b.esm", refr_x=2.0)) != a
    assert lod_key(esm(tmp_path, "c.esm", height=b"h2")) != a


def test_the_tool_salt_moves_the_key(tmp_path):
    p = esm(tmp_path, "a.esm")
    assert lod_key(p, [b"dyndolod 3.00 a"]) != lod_key(p, [b"dyndolod 3.00 b"])
