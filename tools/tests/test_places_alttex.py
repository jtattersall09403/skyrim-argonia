"""A base's alternate textures: the shapes whose texture set resolves to no record are the ones the game leaves
undrawn (King of the Murkmire's dead Hists: the living tree's model with its leaves pointed at nothing)."""
import struct

from tools.places.assets import alttex


def sub(sig: bytes, data: bytes) -> bytes:
    return sig + struct.pack("<H", len(data)) + data


def rec(sig: bytes, fid: int, body: bytes) -> bytes:
    return sig + struct.pack("<IIIII", len(body), 0, fid, 0, 0) + body


def grup(label: bytes, recs: bytes) -> bytes:
    return b"GRUP" + struct.pack("<I", 24 + len(recs)) + label + struct.pack("<III", 0, 0, 0) + recs


def mods(entries) -> bytes:
    out = struct.pack("<I", len(entries))
    for name, fid in entries:
        n = name.encode() + b"\0"
        out += struct.pack("<I", len(n)) + n + struct.pack("<II", fid, 0)
    return out


def plugin(path, masters, records):
    head = b"".join(sub(b"MAST", m.encode() + b"\0") + sub(b"DATA", b"\0" * 8) for m in masters)
    data = rec(b"TES4", 0, head) + b"".join(records)
    path.write_bytes(data)


def test_a_shape_pointed_at_no_texture_set_is_hidden_and_one_at_a_real_set_is_drawn(tmp_path, monkeypatch):
    master, mod = tmp_path / "Base.esm", tmp_path / "Mod.esp"
    plugin(master, [], [grup(b"TXST", rec(b"TXST", 0x000100, sub(b"EDID", b"Bark\0")))])
    stat = rec(b"STAT", 0x01000ABC, sub(b"EDID", b"TreeDead\0") + sub(b"MODS", mods([("Plane.001", 0x00000028),
                                                                                     ("Trunk", 0x00000100)])))
    plugin(mod, ["Base.esm"], [grup(b"STAT", stat)])
    monkeypatch.setattr(alttex, "_find", lambda name: str({"Base.esm": master, "Mod.esp": mod}.get(name)))
    alttex._index.cache_clear()
    assert alttex.hidden_shapes("Mod.esp:000ABC") == ["Plane.001"]
    assert alttex.parse_mods(mods([("a", 5)])) == [("a", 5)]
