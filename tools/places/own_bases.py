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

import json
from pathlib import Path

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


# The hammock bed (blocks.md, the hammock bed): the held hammocks (Black Marsh North.esp `01hammock`, Journey to Baan
# Malur `SOMRHammock`) are statics with no sleep marker. Journey to Baan Malur's own answer is the one used here: the
# hammock static stays the look and a furniture of the mod's (SOMRHammockLeft, named Hammock, a single sleeper's half
# of vanilla's commonbed01 markers) lies at the same spot. Ours is a copy of that furniture under our name; a draft
# places it at the hammock's origin, the hammock static beside it unchanged.
HAMMOCK_BED = f"{PLUGIN}:000A10"
FURNITURE = {
    HAMMOCK_BED: {"edid": "ArgoniaHammockBed", "copy": "Journey to Baan Malur.esp:0FFA2B", "name": "Hammock",
                  "model": "furniture/common/commonbed01.nif", "bounds": [[-84, -88, 0], [52, 88, 74]],
                  "keywords": ["RaceToScale"]},
}


# Weathered twins (blocks.md, the weathered twin): King of the Murkmire's pattern, one extra static per model with a
# directional material (a layer drawn over the upward-facing surfaces by angle), the model and its alternate textures
# unchanged. Our materials are copies of the mod's MossMaterialArgonia01 (a single-pass colour; the mod's moss colour
# is Dragonborn's MossMaterialSolstheim01's) with the colour set: moss kept as the mod has it, silt a pale grey brown
# (what settles below a waterline), algae a thin bright green. Falloff, thickness and projection are the mod's.
MOSS_MATERIAL, SILT_MATERIAL, ALGAE_MATERIAL, ROCK_MOSS_MATERIAL = (f"{PLUGIN}:000A{n}" for n in ("20", "21", "22", "23"))
# the moss on a rock: Moss Shaders Restored (Nexus SE 55279, Exalderan) puts moss on 28 Skyrim rock statics with
# EVE_ReachMossMaterialObject / EVE_TundraMossMaterialObject, one set of values for all: falloff scale 0.5 and bias 0.55
# (the ruin walls' material has 0.4 and 0.71), noise scale 64 (large blotches across a big rock, not the walls' 1280 fine
# grain) and normal dampener 0.4 (the walls' 0.7). Ours takes those four; colour and projection stay the walls'.
ROCK_MOSS_SET = {"FalloffScale": 0.5, "FalloffBias": 0.55, "NoiseUvScale": 64.0, "NormalDampener": 0.4}
MATERIALS = {
    MOSS_MATERIAL: {"edid": "ArgoniaMoss", "copy": "King of the Murkmire.esp:MossMaterialArgonia01", "set": {}},
    SILT_MATERIAL: {"edid": "ArgoniaSilt", "copy": "King of the Murkmire.esp:MossMaterialArgonia01",
                    "set": {"SinglePassColor": [0.52, 0.47, 0.38]}},
    ALGAE_MATERIAL: {"edid": "ArgoniaAlgae", "copy": "King of the Murkmire.esp:MossMaterialArgonia01",
                     "set": {"SinglePassColor": [0.14, 0.30, 0.10]}},
    ROCK_MOSS_MATERIAL: {"edid": "ArgoniaRockMoss", "copy": "King of the Murkmire.esp:MossMaterialArgonia01",
                         "set": ROCK_MOSS_SET},
}
VARIANTS = (("Moss", MOSS_MATERIAL), ("Silt", SILT_MATERIAL), ("Algae", ALGAE_MATERIAL))
ROCK_VARIANTS = (("Moss", ROCK_MOSS_MATERIAL), ("Silt", SILT_MATERIAL), ("Algae", ALGAE_MATERIAL))
# the first family: the Ayleid, old Imperial and Xanmeer ruin pieces of King of the Murkmire that Black Marsh's ruins
# source (id in the mod, editor id, model, bounds); the angle is the surface slope the layer takes: 90 the mod's
# default, 75 for rubble (docs/research/new-art/ruins-and-weathering.md, R1)
TWIN_FAMILY = (
    ("03A82E", "AYLDExtArch01", "argonia/ayleidruins/exterior/ararch01.nif", [[-62, -267, -523], [62, 267, 937]]),
    ("03A82F", "AYLDExtArch02", "argonia/ayleidruins/exterior/ararch02.nif", [[-62, -267, -523], [62, 267, 832]]),
    ("03A830", "AYLDExtArch03", "argonia/ayleidruins/exterior/ararch03.nif", [[-62, -267, -523], [62, 267, 534]]),
    ("03A831", "AYLDExtArchColumn01", "argonia/ayleidruins/exterior/ararchcolumn01.nif", [[-69, -222, -61], [61, 125, 807]]),
    ("03FB4B", "AYLDExtColumn01", "argonia/ayleidruins/exterior/arcolumn01.nif", [[-146, -146, 0], [146, 146, 729]]),
    ("03A836", "AYLDExtBlock01", "argonia/ayleidruins/exterior/arblock01.nif", [[-96, -96, -30], [96, 96, 32]]),
    ("03A871", "AYLDExtStairs02", "argonia/ayleidruins/exterior/arstairs02.nif", [[-355, -1450, -284], [355, -366, 140]]),
    ("03A877", "AYLDExtTower01", "argonia/ayleidruins/exterior/artower01.nif", [[0, -460, -650], [460, 0, 978]]),
    ("03A86C", "AYLDExtRingOuterWall01", "argonia/ayleidruins/exterior/arringouterwall03.nif", [[645, 1556, 0], [1432, 2036, 552]]),
    ("045C4F", "OldImpExtRuin01", "argonia/imperialruins/redruin1.nif", [[-692, -497, -65], [656, 462, 650]]),
    ("045C50", "OldImpExtRuin02", "argonia/imperialruins/redruin2.nif", [[-1102, -473, -340], [1101, 473, 340]]),
    ("045C51", "OldImpExtRuin03", "argonia/imperialruins/redruin3.nif", [[-486, -505, -629], [472, 519, 611]]),
    ("045C52", "OldImpExtRuin04", "argonia/imperialruins/redruin4.nif", [[-701, -639, -272], [777, 745, 243]]),
    ("045C53", "OldImpExtRuin05", "argonia/imperialruins/redruingate.nif", [[-432, -267, -9], [499, 77, 995]]),
    ("015689", "OldImpRubblePile02", "tesak1243/mwimperialarchitecture/architecture/keep/rubbles/mwimparchrubblepile02.nif", [[-466, -439, -3], [461, 452, 580]]),
    ("015683", "OldImpRubblePiece01", "tesak1243/mwimperialarchitecture/architecture/keep/rubbles/mwimparchrubblepiece01.nif", [[-294, -89, -74], [294, 89, 74]]),
    ("005C85", "OldImpExtRuinWall01", "argonia/xanmeer/rubble/ruinedwall01.nif", [[-18, -469, -453], [21, 121, 573]]),
    ("04B5D8", "XanmeerRubbleFloor03", "argonia/xanmeer/rubble/floorchunk01.nif", [[-280, -246, 0], [256, 286, 19]]),
    ("5E249A", "XanmeerRubbleBlocks05", "architecture/xanmeer/furniture/xanmeer_murkmire_rubblewall1_1.nif", [[-27, -174, -1], [98, 158, 88]]),
    ("01A81C", "AYLDRubble01", "creationclub/_shared/dungeons/ayleidruins/exterior/arextrubble01.nif", [[-466, -439, 55], [461, 452, 292]]),
)
RUBBLE = {"015689", "015683", "04B5D8", "5E249A", "01A81C", "005C85"}
TWIN_BASE = 0x00B000
# the second family: the rocks our world plants most (newworld/story/data/db/region_flora.jsonl density: King of the
# Murkmire's rock bases and Valenwood's mountain trims) among those Moss Shaders Restored gives a moss material, each at
# the surface angle that mod gives it (plugin, id in it, editor id, model, bounds, angle). Their keys follow the ruin
# pieces', so no key moves.
ROCK_FAMILY = (
    ("King of the Murkmire.esp", "03A89E", "ArgoniaRockM01", "landscape/rocks/rockm01.nif", [[-128, -74, -13], [119, 90, 110]], 100),
    ("King of the Murkmire.esp", "065B5C", "ArgoniaRockPileM01Mud", "landscape/rocks/rockpilem01.nif", [[-268, -300, -41], [267, 306, 51]], 90),
    ("King of the Murkmire.esp", "065BD4", "ArgoniaRockPileM02Mud", "landscape/rocks/rockpilem02.nif", [[-180, -244, -34], [202, 231, 67]], 90),
    ("King of the Murkmire.esp", "0ADFE9", "ArgoniaRockPileL01Rainforest", "landscape/rocks/rockpilel01.nif", [[-274, -439, -49], [253, 438, 323]], 90),
    ("King of the Murkmire.esp", "07A3D8", "ArgoniaRockPileL02Rainforest", "landscape/rocks/rockpilel02.nif", [[-465, -415, -83], [445, 491, 90]], 90),
    ("King of the Murkmire.esp", "07524A", "ArgoniaRockPileL03Rainforest", "landscape/rocks/rockpilel03.nif", [[-596, -592, -112], [509, 539, 148]], 90),
    ("King of the Murkmire.esp", "138592", "ArgoniaRockPileS01Mud", "landscape/rocks/rockpiles01.nif", [[-102, -153, -17], [125, 126, 42]], 120),
    ("King of the Murkmire.esp", "36B5B6", "ArgoniaRockPileS02Mud", "landscape/rocks/rockpiles02.nif", [[-121, -133, -22], [129, 118, 56]], 120),
    ("King of the Murkmire.esp", "02ACCB", "ArgoniaRockCliff02MarshGrass", "landscape/rocks/rockcliff02.nif", [[-358, -1157, -27], [659, 1017, 733]], 90),
    ("King of the Murkmire.esp", "02ACCE", "ArgoniaRockCliff05MarshGrass", "landscape/rocks/rockcliff05.nif", [[-447, -969, -72], [667, 972, 838]], 90),
    ("King of the Murkmire.esp", "06AE8A", "ArgoniaRockCliff07Rainforest", "landscape/rocks/rockcliff07.nif", [[-440, -1075, -6], [1037, 1009, 838]], 90),
    ("King of the Murkmire.esp", "02FE30", "ArgoniaMountainTrim03MarshGrass", "landscape/mountains/mountaintrim03.nif", [[-1144, -1128, 38], [1145, 1155, 225]], 90),
    ("Valenwood.esp", "069401", "01MountainTrim01FieldGrass01", "landscape/mountains/mountaintrim01.nif", [[-916, -1118, -144], [916, 1118, 205]], 80),
    ("Valenwood.esp", "069407", "01MountainTrim02Rocks01", "landscape/mountains/mountaintrim02.nif", [[-744, -1126, -88], [787, 1126, 241]], 80),
)


def _twins() -> dict[str, dict]:
    out = {}
    for i, (fid, edid, model, bounds) in enumerate(TWIN_FAMILY):
        for j, (name, mat) in enumerate(VARIANTS, 1):
            out[f"{PLUGIN}:{TWIN_BASE + i * 4 + j:06X}"] = {
                "edid": f"Argonia{edid}{name}", "copy": f"King of the Murkmire.esp:{fid}", "material": mat,
                "angle": 75 if fid in RUBBLE else 90, "model": model, "bounds": bounds}
    for i, (plug, fid, edid, model, bounds, angle) in enumerate(ROCK_FAMILY, len(TWIN_FAMILY)):
        for j, (name, mat) in enumerate(ROCK_VARIANTS, 1):
            out[f"{PLUGIN}:{TWIN_BASE + i * 4 + j:06X}"] = {
                "edid": f"Argonia{edid.removeprefix('Argonia')}{name}", "copy": f"{plug}:{fid}", "material": mat,
                "angle": angle, "model": model, "bounds": bounds}
    return out


TWINS = _twins()


# Model-only packs (asset-only rows with no plugin: Ships and Boats of Tamriel, Incaendo's banners, Morrowind Hlaalu
# Architecture, Phitt's Velothi resources): one static of ours per chosen model, key and bounds in
# newworld/sources/own/pack_statics.json ({key: {edid, model, pack, bounds}}; keys ArgoniaOwn.esp:00C000 up), the model
# path as the pack lays it under meshes/. The writer makes a plain static of that model (kind "modelstatic").
PACK_FILE = Path(__file__).resolve().parents[2] / "newworld" / "sources" / "own" / "pack_statics.json"
PACK_STATICS = json.loads(PACK_FILE.read_text()) if PACK_FILE.exists() else {}


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
             "name": None, "plugin": PLUGIN, "keywords": [], "water": look(a["water"])} for k, a in ACTIVATORS.items()] + [
        {"key": k, "edid": f["edid"], "type": "FURN", "model": f["model"], "bounds": f["bounds"], "name": f["name"],
         "plugin": PLUGIN, "keywords": f["keywords"]} for k, f in FURNITURE.items()] + [
        {"key": k, "edid": t["edid"], "type": "STAT", "model": t["model"], "bounds": t["bounds"], "name": None,
         "plugin": PLUGIN, "keywords": []} for k, t in TWINS.items()] + [
        {"key": k, "edid": t["edid"], "type": "STAT", "model": t["model"], "bounds": t["bounds"], "name": t.get("name"),
         "plugin": PLUGIN, "keywords": []} for k, t in PACK_STATICS.items()]


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
    for k in [u for u in used if u in FURNITURE]:
        f = FURNITURE[k]
        fk[k] = ids(f"furn:own:{k}")
        out.append({"kind": "furniture", "fk": fk[k], "edid": f"{f['edid']}_{tag}", "copy": f["copy"]})
    for k in [u for u in used if u in TWINS]:
        t = TWINS[k]
        if t["material"] not in fk:
            m = MATERIALS[t["material"]]
            fk[t["material"]] = ids(f"mato:own:{t['material']}")
            out.append({"kind": "material", "fk": fk[t["material"]], "edid": f"{m['edid']}_{tag}", "copy": m["copy"],
                        "set": m["set"]})
        fk[k] = ids(f"stat:own:{k}")
        out.append({"kind": "static", "fk": fk[k], "edid": f"{t['edid']}_{tag}", "copy": t["copy"],
                    "material": fk[t["material"]], "angle": t["angle"]})
    for k in [u for u in used if u in PACK_STATICS]:
        t = PACK_STATICS[k]
        fk[k] = ids(f"stat:own:{k}")
        out.append({"kind": "modelstatic", "fk": fk[k], "edid": f"{t['edid']}_{tag}", "model": t["model"], "bounds": t["bounds"]})
    for r in refs:
        if r.get("base") in fk:
            r["base"] = fk[r["base"]]
    return out
