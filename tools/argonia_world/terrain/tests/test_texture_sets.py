"""L1: the ground's TXST records point at BM&V's landscape pack and every painted LTEX is re-pointed at one, with
its planned grass list; the grass layer leaves those LTEX to the texture sets (one override each)."""
from tools.argonia_world.intermediate import compose
from tools.argonia_world.terrain import grass, material as M, texture_sets as T


class Alloc:
    def __init__(self):
        self.n = 0x800

    def form_key(self, edid, rtype, key):
        self.n += 1
        return f"{self.n:06X}:Argonia.esm"


def scan():
    lt = [{"formKey": t.form_key, "edid": t.edid, "winner": "Skyrim.esm", "textureSet": "000010:Skyrim.esm",
           "materialType": "000020:Skyrim.esm", "friction": 30, "restitution": 30, "specular": 30, "flags": None,
           "grasses": ["000200:Skyrim.esm"]} for t in M.TEXTURES]
    return {"ltex": lt, "grass": [{"formKey": "000100:Tropical Skyrim.esp", "edid": "TropicalGrass01", "model": "",
                                   "plugins": ["Tropical Skyrim.esp"]}]}


def test_every_painted_ltex_points_at_a_bmv_texture_set():
    first = M.TEXTURES[0].form_key
    recs = T.records(Alloc(), scan(), {first: ["000100:Tropical Skyrim.esp"]})
    txst = {r["formKey"]: r for r in recs if r["type"] == "TXST"}
    ltex = {r["formKey"]: r for r in recs if r["type"] == "LTEX"}
    assert len(txst) == len(ltex) == len(M.TEXTURES)
    assert all(r["diffuse"].startswith("argonia\\landscape\\") and r["normal"].startswith("argonia\\landscape\\")
               and r["normal"].endswith("_n.dds") for r in txst.values())  # derived at install (r6, 0014)
    for t in M.TEXTURES:
        o = ltex[t.form_key]
        assert o["override"] and txst[o["textureSet"]]["diffuse"] == t.diffuse
    assert ltex[first]["grasses"] == ["000100:Tropical Skyrim.esp"]  # the plan's list
    assert ltex[M.TEXTURES[1].form_key]["grasses"] == ["000200:Skyrim.esm"]  # no plan row: the winner's


def test_grass_layer_leaves_the_ground_ltex_to_the_texture_sets():
    s = scan()
    intended = {t.form_key: ["000100:Tropical Skyrim.esp"] for t in M.TEXTURES}
    assert grass.overrides(s, intended) == []
    recs = compose([T.Layer("patch:ground-textures", T.records(Alloc(), s, intended))])
    assert [r["type"] for r in recs].count("LTEX") == len(M.TEXTURES)
