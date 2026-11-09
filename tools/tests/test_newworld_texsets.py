"""texsets.py: a wrong diffuse path is repaired by file name within the mod, ambiguity refused, other slots warn."""
from tools.newworld.place import texsets


class FakeAssets:
    def __init__(self, files):
        self.files = set(files)

    def has(self, p):
        return p.lower() in self.files


def test_doubled_extension_and_moved_folder():
    files = {"textures\\landscape\\trees\\gkbbranch1.dds", "textures\\landscape\\plants\\fern2.dds"}
    a = texsets.Audit(FakeAssets(files), lambda m: files)
    assert a.find("textures\\landscape\\trees\\gkbbranch1.dds.dds", "bmv")[0] == "textures\\landscape\\trees\\gkbbranch1.dds"
    assert a.find("textures\\plants\\groundplants1\\fern2.dds", "bmv")[0] == "textures\\landscape\\plants\\fern2.dds"


def test_ambiguous_and_no_mod_refused():
    files = {"textures\\a\\x.dds", "textures\\b\\x.dds"}
    a = texsets.Audit(FakeAssets(files), lambda m: files)
    new, why = a.find("textures\\c\\x.dds", "bmv")
    assert new is None and why.startswith("ambiguous")
    assert a.find("textures\\c\\x.dds", None)[0] is None


def test_tex_key_reads_from_last_textures():
    assert texsets.tex_key("C:\\Work\\Textures\\Plants\\A.dds") == "textures\\plants\\a.dds"
    assert texsets.tex_key("plants\\a.dds") == "textures\\plants\\a.dds"
