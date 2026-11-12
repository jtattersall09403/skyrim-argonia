import struct

from tools.argonia_world.esm import Plugin, Record
from tools.newworld import assets_audit as A


def s(b: bytes) -> bytes:
    return struct.pack("<I", len(b)) + b


def test_nif_textures_reads_length_prefixed_paths():
    blob = b"\x01\x02" + s(b"textures\\Landscape\\Grass\\EWpShore17.dds") + b"zz" + s(b"Effects\\x.DDS") + b"junk.dds"
    assert A.nif_textures(blob) == ["effects\\x.dds", "textures\\landscape\\grass\\ewpshore17.dds"]


def test_norm_asset_roots_and_absolute_paths():
    assert A.norm_asset("Landscape\\grass\\a.nif") == "meshes\\landscape\\grass\\a.nif"
    assert A.norm_asset("skyrimhd\\build\\pc\\data\\textures\\plants\\t.dds") == "textures\\plants\\t.dds"
    assert A.norm_asset("Sky\\c.dds") == "textures\\sky\\c.dds"


def test_loaded_archive():
    act = {"black marsh", "skyui_se"}
    assert A.loaded_archive("Skyrim - Textures5.bsa", act)
    assert A.loaded_archive("SkyUI_SE.bsa", act)
    assert A.loaded_archive("Black Marsh - Textures.bsa", act)
    assert not A.loaded_archive("King of the Murkmire.bsa", act)


class FakeR:
    def __init__(self, files):
        self.files = files

    def archives(self):
        return []

    def read(self, k):
        return self.files.get(k)

    def where(self, k):
        return "x" if k in self.files else None


def test_run_ranks_missing_by_placed_uses():
    p = Plugin("W.esm", [], [])
    gras = Record("GRAS", 0, 0x10, [("EDID", b"G\0"), ("MODL", b"g.nif\0")])
    ltex = Record("LTEX", 0, 0x11, [("EDID", b"L\0"), ("GNAM", struct.pack("<I", 0x10))])
    land = Record("LAND", 0, 0x12, [("BTXT", struct.pack("<I", 0x11) + b"\0\0\0\0")] * 3)
    stat = Record("STAT", 0, 0x13, [("EDID", b"S\0"), ("MODL", b"s.nif\0")])
    ref = Record("REFR", 0, 0x14, [("NAME", struct.pack("<I", 0x13))])
    for r in (gras, ltex, land, stat, ref):
        r.plugin = p
        p._records.append(r)
    R = FakeR({"meshes\\g.nif": s(b"textures\\gone.dds") + s(b"textures\\here.dds"), "textures\\here.dds": b""})
    rep = A.Audit(R).run([p])
    assert [(m["path"], m["uses"]) for m in rep["missing"]] == [("textures\\gone.dds", 3), ("meshes\\s.nif", 1)]
    assert rep["missing_meshes"] == 1 and rep["missing_textures"] == 1
