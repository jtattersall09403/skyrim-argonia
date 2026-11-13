"""The start check (tools/newworld/start_check.py) lays our plugins in stack.ps1's order, and reads a persistent marker."""
import re
import struct

from tools.newworld import start_check as S


def test_our_plugins_follow_stack_ps1():
    ps1 = (S.REPO / "infra/gpu-box/stack.ps1").read_text()
    names = re.findall(r"name = '([^']+)'", ps1.split("$OursPlugins = ", 1)[1].split("# derived folders", 1)[0])
    assert [n for n, _ in S.OURS["NewWorld"]] == names
    assert [n for n, _ in S.OURS["Argonia"]] == names[:1]


def _rec(sig, flags, fid, body=b""):
    return sig + struct.pack("<IIIII", len(body), flags, fid, 0, 0) + body


def _grp(label, gtype, inner):
    return b"GRUP" + struct.pack("<I", 24 + len(inner)) + label + struct.pack("<iII", gtype, 0, 0) + inner


def test_scan_reads_the_marker_only_in_the_persistent_cell(tmp_path):
    hdr = _rec(b"TES4", 1, 0, b"MAST" + struct.pack("<H", 11) + b"Skyrim.esm\0")
    marker = lambda flags: _rec(b"REFR", flags, 0x01000802)
    world = lambda refs: _grp(b"WRLD", 0, _rec(b"WRLD", 0, 0x01000800) + _grp(struct.pack("<I", 0x01000800), 1,
                              _rec(b"CELL", 0x400, 0x01000801) + _grp(struct.pack("<I", 0x01000801), 6, _grp(struct.pack("<I", 0x01000801), 8, refs))))
    p = tmp_path / "W.esm"
    p.write_bytes(hdr + world(marker(0x400)))
    assert S.scan(p)["marker"] == {"persistent": True, "in_persistent_cell": True}
    p.write_bytes(hdr + world(marker(0)))
    assert S.scan(p)["marker"]["persistent"] is False
