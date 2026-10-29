"""The 2.W3 families into the world database (decision 0030 §6), once; then the database is the source.

Imported (paths passed on the command line, so no tool names a world/ path; the world-reads gate):
- climate/weather-states.json: weather states, the five regionFrequencies groups and their weights, the seasons;
- regions/authored-overrides.json: the owner's central-jungle polygon;
- flora/palettes.json: per old region class, the per-role totals of its layers (stems per hectare, clumping, slope,
  water posture). The palette's layers themselves are 2.W4's flora_rule; this reads only the totals.

Authored here (the 2.W3 seed, written once; afterwards edit the rows): the 11 ecological classes, the old raster
classes' place in them, the object roles and the Tropical Skyrim forms that fill them, our weathers, image spaces and
the climate. Evidence for each Tropical Skyrim form: its TREE override's model in `Tropical Skyrim.esp` (SSE 78044,
read 2026-10-29; docs/research/journals/regions-roads.md).

    python3 -m tools.argonia_world.regions.migrate --weather W.json --overrides O.json --palettes P.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from tools.argonia_world import db

# --- the old region raster's classes (flora/palettes.json byRegionClass ids; id 10 burnt by old 0050) ----------
# raster id, id, name, ecological class
RASTER = (
    (0, "ocean", "ocean", "coastal-lagoon"),
    (1, "border-mountains", "border mountains", "western-frontier"),
    (2, "upland-hills", "upland hills", "western-frontier"),
    (3, "tidal-delta", "tidal delta", "tidal-delta"),
    (4, "coastal-lagoon-salt-marsh", "coastal lagoon & salt marsh", "coastal-lagoon"),
    (5, "deep-river-corridor", "deep river corridor", "deep-river-corridor"),
    (6, "rootland-deep-marsh", "rootland deep marsh", "rootland"),
    (7, "interior-swamp", "interior swamp", "interior-swamp"),
    (8, "fringe-marsh", "fringe marsh", "interior-swamp"),
    (9, "seasonal-floodplain", "seasonal floodplain", "seasonal-floodplain"),
    (11, "firm-lowland", "firm lowland", "flooded-forest"),
    (12, "lake-and-standing-water", "lake & standing water", "deep-sink-basin"),
    (13, "tropical-jungle", "tropical jungle", "flooded-forest"),
    (14, "mangrove-forest", "mangrove forest", "tidal-delta"),
)
# firm ground of the Morrowind-facing north is the northern transition (20-province-design §16)
ECO_OVERRIDE = (
    ("border-mountains", "dunmer-north", "northern-transition"),
    ("upland-hills", "dunmer-north", "northern-transition"),
    ("firm-lowland", "dunmer-north", "northern-transition"),
    ("firm-lowland", "imperial-fringe", "western-frontier"),
)

# id, name, weather group, misty, exterior, about (20-province-design §16)
ECO = (
    ("tidal-delta", "tidal delta", "coastal", True, True, "braided channels, mudflats, mangroves"),
    ("coastal-lagoon", "coastal lagoon", "coastal", False, True, "sheltered water, reed beds, salt; the sea"),
    ("deep-river-corridor", "deep river corridor", "marsh", True, True, "large channel, levees, oxbows"),
    ("flooded-forest", "flooded forest", "jungle", True, True, "shallow water under canopy; the jungle"),
    ("interior-swamp", "interior swamp", "marsh", True, True, "pools, hummocks, winding channels"),
    ("seasonal-floodplain", "seasonal floodplain", "lowland", True, True, "temporary lakes and channels"),
    ("rootland", "rootland", "marsh", True, True, "Hist root influence, organic ground"),
    ("northern-transition", "northern transition", "lowland", False, True, "firmer Morrowind-facing ground"),
    ("western-frontier", "western frontier", "uplands", False, True, "red clay, roads, the border hills"),
    ("deep-sink-basin", "deep sink basin", "marsh", True, True, "permanently flooded depressions"),
    ("karst-cavern-belt", "karst/root cavern belt", "marsh", True, False,
     "sinkholes and caves: interiors only, so no exterior REGN (lighting templates carry it)"),
)

# weather-states.json's regionFrequencies keys -> our group ids
GROUPS = {
    "coastal (ocean, delta, lagoon)": ("coastal", "coastal (ocean, delta, lagoon)"),
    "marsh (fringe/interior/rootland/lakes)": ("marsh", "marsh (fringe, interior, rootland, lakes)"),
    "jungle": ("jungle", "jungle"),
    "uplands & mountains": ("uplands", "uplands and mountains"),
    "firm lowland & floodplain": ("lowland", "firm lowland and floodplain"),
}
YEAR_ORDER = ("dry", "hatching", "wet")  # the seasons from the year's first day (a reversible design choice)
SEASON_FACTOR = {  # from each season's `effects` text
    "wet": {"monsoon-downpour": 2.0, "storm": 2.0, "dry-haze": 0.0},
    "dry": {"monsoon-downpour": 0.5},
    "hatching": {"dry-haze": 0.0},
}

# --- roles and the Tropical Skyrim forms that fill them --------------------------------------------------------
ROLES = {
    "emergent": "rare giant trunks above the roof",
    "canopy": "the closed jungle roof",
    "palm": "palms of coast, fringe and gaps",
    "mangrove": "mangroves at the waterline and in the basin",
    "gallery": "bank walls and gallery ribbons along water: bamboo and weeping trees",
    "shrub": "understorey, thickets and shrubs under or between trees",
    "cliff-tree": "trees that hold to rock and steep ground",
    "deadwood": "stumps, branch piles and drift",
    "rock": "rocks, wet rocks and cliff dressing",
}
# old palette role -> our role (None: not a CK object: aquatic and seabed layers are 2.W2/2.W4's; herbs are grass)
ROLE_OF = {
    "emergent": "emergent", "canopy": "canopy", "subcanopy": "canopy", "tall-palm": "palm", "palm": "palm",
    "waterline-tree": "mangrove", "basin-mangrove": "mangrove", "overlay-waterline-tree": "mangrove",
    "gallery": "gallery", "bank-wall": "gallery", "green-wall": "gallery",
    "gap-thicket": "shrub", "understory": "shrub", "interior-shrub": "shrub", "drowned-thicket": "shrub",
    "rock": "rock", "wet-rock": "rock", "cliff-dressing": "rock", "deadwood": "deadwood", "snag": "deadwood",
    "deadfall": "deadwood", "strand-deadfall": "deadwood", "dead-shrub": "shrub", "landmark-giant": "emergent",
    "drowned-tree": "gallery", "drowned-tree-dry": "gallery", "overlay-basin-mangrove": "mangrove",
}
REVIEW_TS = "Tropical Skyrim replaces the model in place (Tropical Skyrim.esp TREE override); no Nordic tell remains"
# FormKey, EditorID, type, role, Tropical Skyrim model
FORMS = (
    ("04FBB0:Skyrim.esm", "TreePineForest04", "TREE", "emergent", "anvilgianttrunk"),
    ("051126:Skyrim.esm", "TreePineForest05", "TREE", "canopy", "gkbtreeofwolene"),
    ("04B016:Skyrim.esm", "TreePineForest03", "TREE", "canopy", "gkbjungletreenew8"),
    ("0B8A73:Skyrim.esm", "TreeReachTree01", "TREE", "canopy", "gkbjungletreenew27v2weeping"),
    ("0AAE8E:Skyrim.esm", "TreeReachShrub02", "TREE", "canopy", "gkbjungletreenew18v2"),
    ("0B8A69:Skyrim.esm", "TreeReachBush02", "TREE", "canopy", "gkbjungletreenew2v2"),
    ("0EF5A5:Skyrim.esm", "TreePineForestSnow01Dead", "TREE", "canopy", "gkbjungletreenew1"),
    ("018A02:Skyrim.esm", "TreePineForest02", "TREE", "palm", "anvil_palm_trunk"),
    ("0AAE90:Skyrim.esm", "TreeFallForestShrub02", "TREE", "palm", "palmtree3"),
    ("0AAE8D:Skyrim.esm", "TreeReachShrub01", "TREE", "palm", "palmtree4"),
    ("0A731C:Skyrim.esm", "TreeDeadShrub", "TREE", "palm", "fanpalm4"),
    ("01306D:Skyrim.esm", "TreePineForest01", "TREE", "mangrove", "mangrovereachtree0gkb8"),
    ("0B927E:Skyrim.esm", "TreePineForest05Dead", "TREE", "mangrove", "mangrovereachtree0gkb2"),
    ("0B927D:Skyrim.esm", "TreePineForest04Dead", "TREE", "mangrove", "mangrovereachtree0gkb3"),
    ("0B927C:Skyrim.esm", "TreePineForest03Dead", "TREE", "mangrove", "mangrovereachtree0gkb9"),
    ("07614B:Skyrim.esm", "TreeAspen05", "TREE", "gallery", "gkbtreeaspenbamboo01"),
    ("07614A:Skyrim.esm", "TreeAspen06", "TREE", "gallery", "gkbtreeaspenbamboo04"),
    ("06C9D4:Skyrim.esm", "TreeAspen03", "TREE", "gallery", "gkbtreeaspenbamboo05"),
    ("0B73C2:Skyrim.esm", "TreeSwordFern06", "TREE", "gallery", "gkbjungletreenew24v2weeping"),
    ("0B8A57:Skyrim.esm", "TreeReachBush01", "TREE", "shrub", "Tamira Bush01"),
    ("0A7312:Skyrim.esm", "TreePineShrub03", "TREE", "shrub", "Tamira PalmPlant"),
    ("0B8A64:Skyrim.esm", "TreeSwordFernCluster02", "TREE", "shrub", "Tamira TropicalPlant01"),
    ("0B8A65:Skyrim.esm", "TreeSwordFernCluster03", "TREE", "shrub", "Tamira TropicalPlant02"),
    ("0A7329:Skyrim.esm", "TreeThicket01", "TREE", "shrub", "ManFern"),
    ("0B91F0:Skyrim.esm", "TreeFloraThistle01", "TREE", "shrub", "Tamira Bush04"),
    ("0AAE8F:Skyrim.esm", "TreeFallForestShrub01", "TREE", "shrub", "CITSfloraBamboo01"),
    ("0B8A76:Skyrim.esm", "TreeReachCliffTree01", "TREE", "cliff-tree", "gkbreachclifftree01"),
    ("0B8A77:Skyrim.esm", "TreeReachCliffTree02", "TREE", "cliff-tree", "gkbreachclifftree02"),
    ("09DAA2:Skyrim.esm", "TreePineShrub01Snow", "TREE", "cliff-tree", "gkbjunipertree"),
    ("0B8A75:Skyrim.esm", "TreeReachTreeStump01", "TREE", "deadwood", "gkbreachtreestump01"),
    ("04FF0F:Skyrim.esm", "TreeReachBranchPile02", "STAT", "deadwood", "gkbreachbranchpile02"),
    ("018199:Skyrim.esm", "RockL01", "STAT", "rock", "rockl01 (Tropical Skyrim's mesh and rocks01 texture)"),
    ("024E4A:Skyrim.esm", "RockPileL03FieldGrass01Moss", "STAT", "rock", "vanilla moss pile, Tropical Skyrim rocks01"),
    ("0BB8BC:Skyrim.esm", "RockL01Wet", "STAT", "rock", "vanilla wet rock, Tropical Skyrim rocks01"),
)

# --- weathers ---------------------------------------------------------------------------------------------------
# Tropical Skyrim's own region weather lists (its REGN overrides, read 2026-10-29) are the base of each group:
# coastal <- WeatherCoast (snow entries dropped), marsh <- WeatherTundraMarsh, jungle <- WeatherPineForest,
# uplands <- WeatherFallForest, lowland <- WeatherFallForest's clear and WeatherTundraMarsh's fog.
TS = {  # id: (FormKey, EditorID, state)
    "clear-co": ("10A234:Skyrim.esm", "SkyrimClearCO", "clear-humid"),
    "cloudy-co": ("10A236:Skyrim.esm", "SkyrimCloudyCO", "clear-humid"),
    "fog-co": ("10A235:Skyrim.esm", "SkyrimFogCO", "ground-mist"),
    "clear-ma": ("10A230:Skyrim.esm", "SkyrimClearMA", "clear-humid"),
    "cloudy-ma": ("10A233:Skyrim.esm", "SkyrimCloudyMA", "clear-humid"),
    "fog-ma": ("10A232:Skyrim.esm", "SkyrimFogMA", "ground-mist"),
    "rain-ma": ("10A231:Skyrim.esm", "SkyrimOvercastRainMA", "monsoon-downpour"),
    "clear": ("00081A:Skyrim.esm", "SkyrimClear", "clear-humid"),
    "cloudy": ("012F89:Skyrim.esm", "SkyrimCloudy", "clear-humid"),
    "fog": ("0C821E:Skyrim.esm", "SkyrimFog", "ground-mist"),
    "rain": ("0C821F:Skyrim.esm", "SkyrimOvercastRain", "monsoon-downpour"),
    "storm-rain": ("0C8220:Skyrim.esm", "SkyrimStormRain", "storm"),
    "clear-ff": ("10A23B:Skyrim.esm", "SkyrimClearFF", "clear-humid"),
    "cloudy-ff": ("10A23F:Skyrim.esm", "SkyrimCloudyFF", "clear-humid"),
    "fog-ff": ("10A23E:Skyrim.esm", "SkyrimFogFF", "ground-mist"),
    "rain-ff": ("10A23D:Skyrim.esm", "SkyrimOvercastRainFF", "monsoon-downpour"),
    "storm-ff": ("10A23C:Skyrim.esm", "SkyrimStormRainFF", "storm"),
}
# ours: id -> (EditorID, template id, state, fog day near/far, night near/far (m), fog tint, day, dawn, night image)
OURS = {
    "mist": ("ARG_Weather_mist", "fog-ma", "ground-mist", 0, 180, 0, 120, "8C9A6E", "mist", "dawn", "night",
             "ground mist: the marsh dawn and dusk default, fog in under 200 m, green-grey"),
    "tannin-haze": ("ARG_Weather_tannin_haze", "clear-ma", "dry-haze", 0, 900, 0, 500, "A88A4E", "haze", "dawn",
                    "night", "dry-season tannin haze: a brown-gold air over peat water"),
    "storm": ("ARG_Weather_storm", "storm-rain", "storm", 0, 350, 0, 250, "4E5A44", "storm", "storm", "night",
              "the marsh storm: lightning, near fog, green-black"),
    "squall": ("ARG_Weather_squall", "storm-rain", "sea-squall", 0, 500, 0, 300, "5A6A66", "storm", "storm",
               "night", "a sea squall over the coast and the delta"),
}
REALISE = {  # group -> state -> [weather ids]
    "coastal": {"clear-humid": ["clear-co", "cloudy-co"], "ground-mist": ["fog-co", "mist"],
                "monsoon-downpour": ["rain"], "sea-squall": ["squall"], "storm": ["storm", "storm-rain"]},
    "marsh": {"clear-humid": ["cloudy-ma", "clear-ma"], "ground-mist": ["mist", "fog-ma"],
              "monsoon-downpour": ["rain-ma"], "storm": ["storm"], "dry-haze": ["tannin-haze"]},
    "jungle": {"clear-humid": ["cloudy", "clear"], "ground-mist": ["fog", "mist"], "monsoon-downpour": ["rain"],
               "storm": ["storm", "storm-rain"], "dry-haze": ["tannin-haze"]},
    "uplands": {"clear-humid": ["clear-ff", "cloudy-ff"], "ground-mist": ["fog-ff"], "storm": ["storm-ff"],
                "dry-haze": ["tannin-haze"], "monsoon-downpour": ["rain-ff"]},
    "lowland": {"clear-humid": ["clear-ff", "cloudy-ma"], "ground-mist": ["fog-ma", "mist"],
                "monsoon-downpour": ["rain-ma"], "dry-haze": ["tannin-haze"], "storm": ["storm"]},
}
# image spaces: duplicated from Tropical Skyrim's marsh image spaces (Skyrim.esm forms it overrides), restyled
IMAGES = (  # id, EditorID, template, saturation, brightness, contrast, tint, amount, why
    ("day", "ARG_ImageSpace_marsh_day", "10A1BF:Skyrim.esm", 1.08, 1.0, 1.04, "C8BC6A", 0.12,
     "the humid green-gold day: warm, saturated, a little hazed; no Nordic blue-grey"),
    ("dawn", "ARG_ImageSpace_marsh_dawn", "10A1C0:Skyrim.esm", 1.05, 0.98, 1.02, "D8A458", 0.16,
     "sunrise and sunset gold over the water"),
    ("night", "ARG_ImageSpace_marsh_night", "10A1C2:Skyrim.esm", 0.9, 0.92, 1.0, "5A7A4E", 0.12,
     "the marsh night: green, not blue; the bioluminescence reads against it"),
    ("mist", "ARG_ImageSpace_marsh_mist", "10A1C7:Skyrim.esm", 0.92, 1.0, 0.96, "9AA478", 0.15,
     "mist light: flattened, green-grey"),
    ("haze", "ARG_ImageSpace_marsh_haze", "10A1BF:Skyrim.esm", 1.0, 1.02, 0.98, "B89A58", 0.18,
     "tannin haze: brown-gold, low contrast"),
    ("storm", "ARG_ImageSpace_marsh_storm", "10A1CB:Skyrim.esm", 0.85, 0.9, 1.08, "6A7A5A", 0.14,
     "storm light: dark green, hard contrast"),
)
CLIMATE = dict(id="black-marsh", edid="ARG_Climate_black_marsh", template_form_key="000812:Skyrim.esm",
               sunrise_begin_min=330, sunrise_end_min=420, sunset_begin_min=1080, sunset_end_min=1170,
               volatility=60, moon_phase_days=3, timescale=30, weather_group_id="jungle",
               why="a tropical day of near twelve hours (dawn 05:30-07:00, dusk 18:00-19:30); time scale 30 as the "
                   "old design (one game hour in two real minutes); the region lists choose the weather, this list "
                   "is the fallback")


def rows_from(weather: dict, overrides: dict, palettes: dict) -> dict[str, list[dict]]:
    """Every row this migration writes, by table (pure: the tests call it on small documents)."""
    out: dict[str, list[dict]] = defaultdict(list)
    for s in weather["states"]:
        out["weather_state"].append({"id": s["id"]})
        out["weather_state_profile"].append({"weather_state_id": s["id"], "name": s["name"],
                                             "visibility_factor": s["visibilityFactor"], "wetness": s["wetness"],
                                             "notes": s.get("notes")})
    for key, (gid, label) in GROUPS.items():
        out["weather_group"].append({"id": gid, "label": label})
        for st, w in weather["regionFrequencies"][key].items():
            out["weather_group_weight"].append({"weather_group_id": gid, "weather_state_id": st, "weight": w})
    for s in weather["seasons"]:
        out["season"].append({"id": s["id"], "name": s["name"], "share": s["share"], "effects": s["effects"],
                              "year_ord": YEAR_ORDER.index(s["id"])})
        out["condition_shape_season"].append({"term": "calendarIs", "season_id": s["id"],
                                              "ord": YEAR_ORDER.index(s["id"])})
        for st, f in SEASON_FACTOR.get(s["id"], {}).items():
            out["season_factor"].append({"season_id": s["id"], "weather_state_id": st, "factor": f})
    for i, name, wg, misty, ext, about in ECO:
        out["eco_class"].append({"id": i, "name": name, "weather_group_id": wg, "misty": misty, "exterior": ext,
                                 "about": about})
    for rid, cid, name, eco in RASTER:
        out["region_class"].append({"id": cid})
        out["region_class_profile"].append({"region_class_id": cid, "raster_id": rid, "name": name,
                                            "eco_class_id": eco, "about": palettes["byRegionClass"][str(rid)].get("note")})
    for cid, reg, eco in ECO_OVERRIDE:
        out["region_class_eco_override"].append({"region_class_id": cid, "region_id": reg, "eco_class_id": eco})
    by_raster = {r: c for r, c, _, _ in RASTER}
    for o in overrides["overrides"]:
        out["region_class_override"].append({"id": o["id"], "region_class_id": by_raster[o["regionClass"]],
                                             "confidence": overrides["confidence"], "notes": o.get("notes")})
        for k, (u, v) in enumerate(o["polygonUV"]):
            out["region_class_override_point"].append({"override_id": o["id"], "ord": k, "u": u, "v": v})
        for c in o["appliesToClasses"]:
            out["region_class_override_applies"].append({"override_id": o["id"], "region_class_id": by_raster[c]})
    for rid, about in ROLES.items():
        out["object_role"].append({"id": rid, "about": about})
    for rid, cid, _, _ in RASTER:
        agg: dict[str, dict] = {}
        for lay in palettes["byRegionClass"][str(rid)]["layers"]:
            role = ROLE_OF.get(lay.get("role"))
            if role == "canopy" and "palm" in lay.get("species", ""):
                role = "palm"
            if role is None:
                continue
            a = agg.setdefault(role, {"per_ha": 0.0, "w": 0.0, "clump": 0.0, "rad": 0.0, "slope": [], "wmin": [],
                                      "wmax": [], "n": 0})
            n = float(lay.get("instances_per_hectare", 0))
            a["per_ha"] += n
            a["w"] += n
            a["clump"] += n * float(lay.get("clump_size_median", 1))
            a["rad"] += n * float(lay.get("clump_radius_m", 0))
            if "slope_deg_max" in lay:
                a["slope"].append(lay["slope_deg_max"])
            if "water_depth_m" in lay:
                a["wmin"].append(lay["water_depth_m"][0])
                a["wmax"].append(lay["water_depth_m"][1])
            a["n"] += 1
        for role, a in sorted(agg.items()):
            w = a["w"] or 1.0
            out["region_class_role"].append({
                "region_class_id": cid, "role_id": role, "per_ha": round(a["per_ha"], 3),
                "clump_median": round(a["clump"] / w, 2), "clump_radius_m": round(a["rad"] / w, 2),
                "slope_max_deg": max(a["slope"]) if a["slope"] else None,
                "water_min_m": min(a["wmin"]) if a["wmin"] else None,
                "water_max_m": max(a["wmax"]) if a["wmax"] else None, "layers": a["n"]})
    for fk, edid, typ, role, model in FORMS:
        out["object_form"].append({"form_key": fk, "edid": edid, "record_type": typ, "role_id": role,
                                   "ts_model": model, "review": REVIEW_TS})
    for iid, edid, tpl, sat, bri, con, tint, amt, why in IMAGES:
        out["image_space"].append({"id": iid, "edid": edid, "template_form_key": tpl, "saturation": sat,
                                   "brightness": bri, "contrast": con, "tint": tint, "tint_amount": amt, "why": why})
    for wid, (fk, edid, st) in TS.items():
        out["weather"].append({"id": wid, "edid": edid, "form_key": fk, "weather_state_id": st,
                               "why": "Tropical Skyrim's restyle of the vanilla weather (its WTHR override)"})
    for wid, (edid, tpl, st, dn, df, nn, nf, tint, im_d, im_a, im_n, why) in OURS.items():
        out["weather"].append({"id": wid, "edid": edid, "template_form_key": TS[tpl][0], "weather_state_id": st,
                               "fog_day_near_m": dn, "fog_day_far_m": df, "fog_night_near_m": nn,
                               "fog_night_far_m": nf, "fog_tint": tint, "image_day_id": im_d,
                               "image_dawn_id": im_a, "image_night_id": im_n, "why": why})
    for gid, states in REALISE.items():
        for st, ws in states.items():
            for w in ws:
                out["weather_realisation"].append({"weather_group_id": gid, "weather_state_id": st,
                                                   "weather_id": w, "share": round(1 / len(ws), 4)})
    out["climate"].append(dict(CLIMATE))
    return out


ORDER = ("weather_state", "weather_state_profile", "weather_group", "weather_group_weight", "season",
         "condition_shape_season",
         "season_factor", "eco_class", "region_class", "region_class_profile", "region_class_eco_override",
         "region_class_override", "region_class_override_point", "region_class_override_applies", "object_role",
         "region_class_role", "object_form", "image_space", "weather", "weather_realisation", "climate")


def write(w, rows: dict[str, list[dict]]) -> dict[str, int]:
    counts = {}
    for t in ORDER:
        for r in rows.get(t, []):
            w.upsert(t, r)
        counts[t] = len(rows.get(t, []))
    return counts


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--weather", required=True)
    ap.add_argument("--overrides", required=True)
    ap.add_argument("--palettes", required=True)
    a = ap.parse_args(argv)
    load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    rows = rows_from(load(a.weather), load(a.overrides), load(a.palettes))
    w = db.open()
    counts = write(w, rows)
    w.save()
    for t, n in counts.items():
        print(f"{n:6} {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
