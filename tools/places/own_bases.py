"""Bases of our own that the place layer writes: records made from a vanilla record, changed only where ours differ.

A draft places them by a key of the pseudo plugin `ArgoniaOwn.esp` (never a real plugin: a key of it that reaches the
writer unswapped fails the build). The asset catalogue carries each as a row (catalogue.py, `own_rows`), so the draft,
the studio and the build's checks read its model, bounds and water as they read any base. The build (build.py
`plan_own`) gives each place that uses one its own copy, under the place's form ids, and swaps the refs' base to it;
the writer (tools/ArgoniaPlaces/Build/Own.cs) makes the records.

The Hist sap pool (docs/design/dressing.md, Hist sap): our water type ArgoniaHistSapWater and the placed water that
carries it, ArgoniaHistSapPool.
- The water is a copy of DefaultVolcanicWater (the still hot-spring pools of Eastmarch's volcanic tundra) as the load
  order's winner has it (Tropical Skyrim.esp), its noise textures, noise directions, displacement and sounds kept.
  King of the Murkmire's own DefaultHistSapWater is the same record recoloured, made fully opaque, its reflection
  turned down to 0.02 and its displacement off: an even orange skin. Ours is amber, golden at the rim and dark brown
  in the middle (the fog runs out over the bowl's depth), lets the bank show through at the rim (opacity 70), keeps a
  sky sheen at low angles (reflectivity 0.6, fresnel 0.25, reflection magnitude 0.35: Blackreach's and MurkyWater's
  fresnel, the hot spring's magnitude raised) and moves at half the hot spring's noise speed, near DefaultMarshWater's
  stillness, as a thick liquid does. No current, no damage.
- The placed water is vanilla's round puddle (Skyrim.esm WaterPuddleLiteFog's model and bounds, water/waterpuddle01.nif)
  with our water. Vanilla has one round puddle mesh (and the long WaterPuddleLong, and the square Water1024); a pool's
  size is its scale.
"""
from __future__ import annotations

PLUGIN = "ArgoniaOwn.esp"
SAP_POOL = f"{PLUGIN}:000A01"
SAP_WATER = f"{PLUGIN}:000A02"

WATER = {
    SAP_WATER: {
        "edid": "ArgoniaHistSapWater",
        "copy": "Tropical Skyrim.esp:DefaultVolcanicWater",   # the winner of Skyrim.esm:0713C4
        "set": {
            "ShallowColor": [196, 128, 24],      # golden amber at the rim
            "DeepColor": [86, 40, 6],            # dark brown amber in the middle
            "ReflectionColor": [150, 106, 44],
            "Opacity": 70,
            "FogAboveWaterDistanceNearPlane": 0.0, "FogAboveWaterDistanceFarPlane": 56.0, "FogAboveWaterAmount": 1.0,
            "FogUnderWaterDistanceNearPlane": 0.0, "FogUnderWaterDistanceFarPlane": 56.0,
            "WaterReflectivity": 0.6, "WaterFresnel": 0.25, "WaterReflectionMagnitude": 0.35,
            "NoiseLayerOneWindSpeed": 0.007, "NoiseLayerTwoWindSpeed": 0.0145, "NoiseLayerThreeWindSpeed": 0.0225,
            "DamagePerSecond": 0, "LinearVelocity": [0, 0, 0],   # damage is a whole number in the record (ushort)
        },
    },
}

ACTIVATORS = {
    SAP_POOL: {"edid": "ArgoniaHistSapPool", "model_from": "Skyrim.esm:0FD0DC", "water": SAP_WATER,
               "model": "water/waterpuddle01.nif", "bounds": [[-154, -152, -2], [148, 199, 0]]},
}


# King of the Murkmire's dead Hists: the living tree's model with the crown shapes' alternate textures (MODS) pointed
# at Skyrim.esm:000028, the engine's hardcoded NullTextureSet (no textures; that it hides the shape in game is inferred
# from the mods' use, not proven). Ours do not lean on it. Ours are copies of those statics with those rows pointed at our clear texture set: vanilla's sky alpha
# (textures/sky/alpha.dds, Skyrim - Textures5.bsa, alpha 3 of 255 at most), under the crown shapes' own alpha test
# (threshold 128), so the crown is cut away whole and the bare tree stands. Places keep the mod's bases; the build
# swaps each ref of a replaced base to the place's copy, and the studio draws the replaced base as the copy.
CLEAR_TXST = f"{PLUGIN}:000A03"
TEXTURE_SETS = {
    CLEAR_TXST: {"edid": "ArgoniaClearTextureSet", "diffuse": "textures/sky/alpha.dds"},
}
STATICS = {
    f"{PLUGIN}:000A04": {"edid": "ArgoniaHistTree01Dead", "copy": "King of the Murkmire.esp:52D306", "clear": CLEAR_TXST},
    f"{PLUGIN}:000A05": {"edid": "ArgoniaHistTree04Dead", "copy": "King of the Murkmire.esp:551538", "clear": CLEAR_TXST},
}
REPLACES = {s["copy"]: k for k, s in STATICS.items()}


def alt_tex(key: str, alt: list[dict] | None) -> list[dict] | None:
    """A base's alternate textures as the game will draw them with our plugin: a replaced base's rows that resolve to
    no texture set take our clear set."""
    if key not in REPLACES or not alt:
        return alt
    t = TEXTURE_SETS[STATICS[REPLACES[key]]["clear"]]
    return [a if a.get("textures") else {**a, "txst": STATICS[REPLACES[key]]["clear"], "edid": t["edid"],
                                         "textures": {"diffuse": t["diffuse"], "normal": None}} for a in alt]


def is_own(key: str) -> bool:
    return str(key).startswith(PLUGIN + ":")


def look(water_key: str) -> dict:
    """A water of ours as the catalogue's `water` entry (what the studio shades a placed water from)."""
    w = WATER[water_key]
    s = w["set"]
    return {"edid": w["edid"], "shallow": s["ShallowColor"], "deep": s["DeepColor"], "reflect": s["ReflectionColor"],
            "opacity": s["Opacity"], "reflectivity": s["WaterReflectivity"], "fresnel": s["WaterFresnel"],
            "fog_far": s["FogAboveWaterDistanceFarPlane"]}


def own_rows() -> list[dict]:
    """The catalogue rows of our own placed bases."""
    return [{"key": k, "edid": a["edid"], "type": "ACTI", "model": a["model"], "bounds": a["bounds"],
             "name": None, "plugin": PLUGIN, "keywords": [], "water": look(a["water"])} for k, a in ACTIVATORS.items()]


def plan_own(refs: list[dict], ids, place_id: str) -> list[dict]:
    """The records of ours one place needs, under the place's form ids (`ids(name)` -> its form key), and every ref
    whose base is ours swapped to the place's copy (editor id: ours + "_" + the place). Returns the writer's rows."""
    tag = "".join(c for c in place_id.title() if c.isalnum())
    for r in refs:   # a replaced base (a dead Hist of the mod's): the ref takes our copy
        if r.get("base") in REPLACES:
            r["base"] = REPLACES[r["base"]]
    used = sorted({r["base"] for r in refs if is_own(r.get("base", ""))})
    out, fk = [], {}
    for k in [u for u in used if u in STATICS]:
        s = STATICS[k]
        if s["clear"] not in fk:
            fk[s["clear"]] = ids(f"txst:own:{s['clear']}")
            t = TEXTURE_SETS[s["clear"]]
            out.append({"kind": "txst", "fk": fk[s["clear"]], "edid": f"{t['edid']}_{tag}", "diffuse": t["diffuse"]})
        fk[k] = ids(f"stat:own:{k}")
        out.append({"kind": "static", "fk": fk[k], "edid": f"{s['edid']}_{tag}", "copy": s["copy"], "clear": fk[s["clear"]]})
    for k in [u for u in used if u in ACTIVATORS]:
        a = ACTIVATORS[k]
        for wk in (a["water"],):
            if wk not in fk:
                fk[wk] = ids(f"watr:own:{wk}")
                out.append({"kind": "water", "fk": fk[wk], "edid": f"{WATER[wk]['edid']}_{tag}", "copy": WATER[wk]["copy"],
                            "set": WATER[wk]["set"]})
        fk[k] = ids(f"acti:own:{k}")
        out.append({"kind": "activator", "fk": fk[k], "edid": f"{a['edid']}_{tag}", "model_from": a["model_from"], "water": fk[a["water"]]})
    for r in refs:
        if r.get("base") in fk:
            r["base"] = fk[r["base"]]
    return out
