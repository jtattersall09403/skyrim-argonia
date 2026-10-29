"""L1: the painted ground grows only grass-source GRAS (decision 0006), on a small scan and plan; and the check
fails, once on purpose, when a vanilla grass would reach the marsh."""
from tools.argonia_world.terrain import grass

TS, V = "Tropical Skyrim.esp", "Skyrim.esm"
SCAN = {
    "ltex": [
        {"formKey": "000001:Skyrim.esm", "edid": "LMarsh", "winner": TS, "textureSet": "000010:Skyrim.esm",
         "materialType": "000020:Skyrim.esm", "friction": 30, "restitution": 30, "specular": 30, "flags": None,
         "grasses": ["000100:Tropical Skyrim.esp", "000200:Skyrim.esm"]},
        {"formKey": "000002:Skyrim.esm", "edid": "LSand", "winner": V, "textureSet": None,
         "materialType": "000021:Skyrim.esm", "friction": 30, "restitution": 30, "specular": 30, "flags": None,
         "grasses": []},
    ],
    "grass": [
        {"formKey": "000100:Tropical Skyrim.esp", "edid": "TropicalGrass01", "model": "", "plugins": [TS]},
        {"formKey": "000200:Skyrim.esm", "edid": "SnowGrass01", "model": "", "plugins": [V, "Update.esm"]},
    ],
}


class World:
    def __init__(self, plan):
        self.plan = plan

    def query(self, sql, *a):
        if "grass_source" in sql:
            return [(TS,)]
        if "FROM ltex_grass_plan" in sql:
            return [(k,) for k in self.plan]
        if "FROM ltex_grass " in sql:
            return [(k, g) for k, gs in self.plan.items() for g in gs]
        return [("000001:Skyrim.esm", "LMarsh"), ("000002:Skyrim.esm", "LSand")]  # land_cover_ltex


def test_seed_plan_drops_vanilla_grass_and_overrides_only_what_differs():
    _, plans, rows = grass.seed_plan(SCAN, {"000001:Skyrim.esm": "LMarsh", "000002:Skyrim.esm": "LSand"})
    assert [r["grass_form_key"] for r in rows] == ["000100:Tropical Skyrim.esp"] and len(plans) == 2
    w = World({"000001:Skyrim.esm": ["000100:Tropical Skyrim.esp"], "000002:Skyrim.esm": []})
    recs = grass.layer(w, SCAN).records
    assert [r["formKey"] for r in recs] == ["000001:Skyrim.esm"]
    assert recs[0]["grasses"] == ["000100:Tropical Skyrim.esp"] and recs[0]["textureSet"] == "000010:Skyrim.esm"
    assert grass.check(SCAN, w, recs) == []


def test_check_fails_on_purpose_when_vanilla_grass_survives():
    w = World({"000001:Skyrim.esm": ["000100:Tropical Skyrim.esp"], "000002:Skyrim.esm": []})
    errs = grass.check(SCAN, w, [])  # no override written: the winner's SnowGrass01 reaches the marsh
    assert errs == ["LMarsh: grass not from a grass source: SnowGrass01"]
    w = World({"000001:Skyrim.esm": ["000100:Tropical Skyrim.esp"]})  # a painted LTEX with no plan
    assert grass.check(SCAN, w, grass.layer(w, SCAN).records) == ["LSand: painted but has no ltex_grass_plan row"]
