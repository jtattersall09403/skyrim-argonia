"""The ground paint (nw-02 step 7): every LAND quadrant's base + alpha layers, from the landcover.

    python3 -m tools.newworld.world.texture [--out out/newworld/plugin] [--rows lo:hi]

Reads the land manifest (its terrain build) and out/newworld/landcover/ (the same build, or it stops), paints a
weight per material per vertex, and writes one shard per cell row, `<out>/tex/cy<+NNN>.bin`, each cell in x order:
    for each quadrant (BottomLeft, BottomRight, TopLeft, TopRight):
        uint8 n (layers, 1..6) | 6 uint8 material index (base first; 255 unused) | 5 x 289 uint8 opacity (alpha layer
        k at [k], vertex [y from the south][x] in the quadrant's 17 x 17, value / 255)
then `<out>/tex/materials.json` (the palette: index -> id, the source LTEX `plugin:edid` the writer copies as our own
record (one record per material: two materials of one source are two records), the GRAS list as `plugin:edid`, the
diffuse as the NewWorld profile resolves it, the road role), `<out>/tex/manifest.json` and per-row stats.
`--rows lo:hi` paints only those cell rows (a sample; the manifest lists them alone).

The recipe (numbers from research/nw-02-ground-water-rules.md and docs/research/nw-02-walk5-ground.md):
1. Ground province: each land region belongs to one of seven ground provinces read from its research (delta marsh,
   dark swamp forest, jungle, river lands, red clay, grassland coast, windswept isles). A habitat paints its 3 to 5
   materials (PALETTE) blended 45% with its province's accent for that kind of ground (PROVINCES accent), so the same
   habitat reads differently from one province to the next; the province also sets the road set and its grass.
2. Patches at three scales: each material's share wanders by its own noise at 30 to 300 m (exp(1.4 n)); at the
   middle scale by the ground's moisture (near water, hollows), shade (the canopy field) and roughness (slope, humps),
   each material leaning by its affinities (AFF); at the small scale (15 and 37 m) by its own value noise, stronger
   where the middle scale tells the palette's materials apart least (an even, open slope of gravel, rock and scrub).
   So one ground reads for metres to tens of metres, not hundreds (Skyrim.esm: a dominant texture runs 2.6 to 10.7 m
   at p90).
3. Slope: rock patches over 22 deg on a noise mask.
4. Water's edge, by the kind of the nearest water, on the signed shore distance (EDGE): marsh, sea (bare beach on the
   strand, beach grass on the dune band behind it), mangrove, river, lake. The band's pull fades to the habitat.
5. Roads (roadpaint.py, the rule place paths share, laid as it is with no smoothing): from the surface edge (3.45 m
   from a major spine, 2 m minor) the road holds its straight ramp; its track core (two materials of the province's
   road set, varying along it) falls away over 6.5 m and the verge holds the rest; a major and a minor road's
   classes blend where they meet; toward water it is capped by a ramp over the last 8 m of
   land (ROAD_WATER).
6. Grass: in each province, the grassy materials it names carry its own grass list (a variant material `id~province`,
   its own LTEX), so a marsh in the delta grows reeds and saltrice and one on the coast violets and saltrice.
7. Smooth and cut: each vertex keeps its 4 heaviest ground materials, the ground is blurred over 1.5 vertices and the
   road laid over it; traces under 8% are dropped (the road and the ground each keeping their share). Each quadrant
   keeps at most six materials (the engine's six texture slots: base + 5 alpha layers): the heaviest ground at each of
   its corners (of the ground blurred over 6 vertices; so the quadrants round a corner always share a ground), its
   road materials (the track every road set carries first, so road quadrants always share a road material, then the
   heaviest), then by weight over the quadrant + an 8-vertex halo. A material fades to 0 over 8 vertices toward
   any quadrant that does not keep it (closed squares, so a shared vertex reads the same from every quadrant); what
   the fade takes from a road material goes to the road materials kept there and what it takes from the ground to the
   ground kept there, so the cut never opens a hole in a road nor lays road over ground.
8. Layers: base = the quadrant's heaviest; alpha layers in falling coverage. The engine adds a quadrant's layers:
   each alpha layer shows with its opacity as its weight and the base takes what is left (1 - their sum), as the
   Creation Kit writes them (Skyrim.esm: a vertex's alpha opacities sum to 1.00 at p90, over 1.05 at 1.8% of
   vertices; BM&V never over 1.00). So an alpha layer's opacity is its painted weight, written so a vertex's
   opacities never sum past 255/255, and the composite is the painted weights exactly (to 1/255).
Interrupt-proof: keyed on the land key + landcover key + this code; resumes by row; 3 worker processes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from tools.newworld import landcover as lc
from tools.newworld.world import roadpaint as rp

REPO = Path(__file__).resolve().parents[3]
LC = REPO / "out/newworld/landcover"
MAXL = 6  # base + 5 alpha layers: the six texture slots of the landscape shader (roadpaint.py)
FADE = 8.0  # vertices (no more than the halo HQ: what fades is what the neighbour's halo saw too little of)
TOP_V = 4
HQ = 8  # halo, vertices, over which a quadrant's materials are chosen
PRUNE = 0.08
CORNER_BLUR = 6.0  # vertices; its reach (3 sigma) and the ground blur's (6) end inside every row window's halo, so every window
# reads a corner alike
Q = 17
QBYTES = 1 + MAXL + (MAXL - 1) * Q * Q
M = 128 / 70.0  # metres per vertex
TS, KM, SK = "Tropical Skyrim.esp", "King of the Murkmire.esp", "Skyrim.esm"

# id: (source LTEX plugin:edid, GRAS list, diffuse as the NewWorld profile resolves it). Our own LTEX copies of these,
# with these grass lists. A vanilla LTEX's diffuse is Tropical Skyrim's loose file in the NewWorld profile.
MATERIALS = {
    "forest_floor": ("Skyrim.esm:LPineForest03", [f"{TS}:FernGrass01", f"{TS}:TropicalGrass01"], "Landscape\\PineForest03.dds"),
    "moss": ("Black Marsh North.esp:LPineForest05", [f"{TS}:FernGrass01"], "TEXTUREPACK\\landscape\\tundramoss01.dds"),
    "wet_rock_moss": ("Black Marsh.esm:LPineForestDUPLICATE004", [f"{SK}:FernGrass01"], "TEXTUREPACK\\landscape\\grass\\rocksgrasswater01.dds"),
    "swamp_mud": ("Black Marsh North.esp:LFieldGrassDUPLICATE003", [f"{KM}:ALPAGrassReeds02"], "TEXTUREPACK\\landscape\\rivermud.dds"),
    "mud_reeds": (f"{KM}:LALPAMud01Reeds", [f"{KM}:ALPAGrassReeds01", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassReeds01"], "argonia\\landscape\\rivermud.dds"),
    "marsh_grass": (f"{KM}:LALPAMarshGrass", [f"{KM}:ALPAGrassFern01", f"{KM}:ALPAGrassRams01", f"{KM}:ALPAGrassNettles01"], "argonia\\landscape\\CTQ_Grass_Lush01.dds"),
    "rainforest": (f"{KM}:LALPARainforest", [f"{TS}:ForestGrass01", f"{TS}:ReachGrass01", f"{KM}:ALPAGrassFern02"], "argonia\\landscape\\CTQ_Undergrowth_01.dds"),
    "rainforest_low": (f"{KM}:LALPARainforestLow", [f"{TS}:ForestGrass01", f"{KM}:ALPAGrassFern01", f"{TS}:TropicalGrassPlant01"], "argonia\\landscape\\CTQ_JungleGrass01_d.dds"),
    "dirt_grass": ("Black Marsh.esm:01MOSS1", [f"{SK}:FieldGrass01"], "TEXTUREPACK\\landscape\\fielddirtgrass01.dds"),
    "dark_grass_rocks": ("Black Marsh North.esp:LFieldGrassDUPLICATE002", [f"{TS}:TundraGrass01", f"{SK}:TundraGrass03"], "landscape\\darklandgrassrocks.dds"),
    "meadow": ("Skyrim.esm:LFieldGrass02", [f"{SK}:FieldGrass01", f"{TS}:TropicalGrassPlant01", f"{TS}:TropicalGrassPlant02"], "Landscape\\FieldGrass02.dds"),
    "sand": ("Black Marsh North.esp:Sand", [], "landscape\\sand\\Sand03.dds"),
    "wet_sand": (f"{KM}:LALPAMudSand01", [], "_ResourcePack\\Landscape\\SandWet01_d.dds"),
    "rock": ("Black Marsh North.esp:DarkRock1", [], "landscape\\Apel_lh_rock_02.dds"),
    "rock2": ("Black Marsh North.esp:LDirt03", [], "vvardenfell\\rm\\rm_rock02.dds"),
    "rock_grass": ("Skyrim.esm:LTundraRocks01", [f"{TS}:RockGrass01"], "Landscape\\TundraRocks01.dds"),
    "marsh_mud": (f"{KM}:LALPAMarshMud01", [], "_ResourcePack\\Landscape\\MarshMud02_d.dds"),
    "riverbed_edge": ("Skyrim.esm:LRiverbedEdge01", [], "Landscape\\RiverbedEdge.dds"),
    "river_bottom": ("Skyrim.esm:LRiverBottom01", ["Skyrim.esm:RockGrassWater01", "DepthsOfSkyrim.esp:TBPRiverKelpGrass01"], "Landscape\\RiverBottom.dds"),
    "river_mud": ("Skyrim.esm:LRiverMud01", ["Skyrim.esm:WaterKelpGrass02", "DepthsOfSkyrim.esp:TBP_Algae01"], "Landscape\\RiverMud.dds"),
    "beach": ("Skyrim.esm:LCoastBeach01", [], "Landscape\\CoastBeach01.dds"),
    "ocean_floor": ("Skyrim.esm:LCoastOceanFloor01", ["Skyrim.esm:WaterKelpGrass01", "Skyrim.esm:WaterCoralGrass01", "DepthsOfSkyrim.esp:TBPSeaweed02Test", "DepthsOfSkyrim.esp:TBP_coralsmall01"], "Landscape\\CoastOceanFloor01.dds"),
    "dirt_slopes": ("Skyrim.esm:LFrozenMarshDirtSlopes01", [f"{SK}:FrozenMarshGrass01"], "Landscape\\FrozenMarshDirtSlopes01.dds"),
    "silt": (f"{KM}:LALPASilt01", [], "argonia\\landscape\\dirt02.dds"),
    # Tropical Skyrim's ground (vanilla LTEX whose diffuse the profile takes from TS) and BM&V's rock, for the provinces
    "leaf_litter": ("Skyrim.esm:LFallForestLeaves01", [f"{KM}:ALPAGrassFern02", f"{SK}:ForestGrass02"], "Landscape\\FallForestLeaves01.dds"),
    "dark_moss": ("Skyrim.esm:LReachMoss01", [f"{SK}:FernGrass01"], "Landscape\\ReachMoss01.dds"),
    "fern_floor": ("Skyrim.esm:LPineForest02", [f"{SK}:ForestGrass01", f"{KM}:ALPAGrassFern03"], "Landscape\\PineForest02.dds"),
    "twig_floor": ("Skyrim.esm:LPineForest01", [], "Landscape\\PineForest01.dds"),
    "pebble_earth": ("Skyrim.esm:LFallForestRocks01", [f"{SK}:RockGrass01"], "Landscape\\FallForestRocks01.dds"),
    "marsh_tufts": ("Skyrim.esm:LFrozenMarshIce01", [f"{SK}:FrozenMarshGrass01", f"{KM}:ALPAGrassMarsh01"], "Landscape\\FrozenMarshIce01.dds"),
    "grey_mud": ("Skyrim.esm:LFrozenMarshLichen01", [], "Landscape\\FrozenMarshLichen01.dds"),
    "beach_grass": ("Skyrim.esm:LCoastBeachGrass01", [f"{SK}:BeachGrass01", f"{SK}:BeachGrass02"], "Landscape\\CoastBeachGrass01.dds"),
    "pale_sand": ("Skyrim.esm:LCoastBeach02", [], "Landscape\\CoastBeach02.dds"),
    "leafy_ground": ("Skyrim.esm:LReachGrass01", [f"{SK}:ReachGrass01", f"{SK}:ReachGrass02"], "Landscape\\ReachGrass01.dds"),
    "grey_gravel": ("Skyrim.esm:LSnowRocks01", [], "Landscape\\SnowRocks01.dds"),
    "black_gravel": ("Skyrim.esm:LCaveDirt", [], "Landscape\\CaveBaseGround01.dds"),
    "pale_rock": ("Valenwood.esp:LDirtDUPLICATE005", [], "TEXTUREPACK\\landscape\\mountains\\mountainslab01.dds"),
    "red_rock": ("Black Marsh North.esp:LTundraRocksDUPLICATE002", [], "landscape\\Rocks\\RedRock04.dds"),
    # roads (roadpaint.py ROAD_SETS): no grass on any of them
    "gravel_track": ("Black Marsh North.esp:LFieldDirtGrassDUPLICATE002", [], "dirtroad01.dds"),
    "earth_track": ("Skyrim.esm:LTundra02", [], "Landscape\\Tundra02.dds"),
    "mud_track": (f"{KM}:LALPARiverBottom01", [], "Landscape\\RiverMud.dds"),
    "sand_track": ("Black Marsh North.esp:LDirtDUPLICATE003", [], "landscape\\sand\\Sand06.dds"),
    "verge": ("Skyrim.esm:LDirtSnowPath01", [], "Landscape\\DirtSnowPath01.dds"),
    "clay_verge": ("Skyrim.esm:LFieldGrass01", [], "Landscape\\FieldGrass01.dds"),
}
# the ground's leaning (wet, shade, rough), each -1..1: where it gathers at the middle and small scale
AFF = {
    "forest_floor": (0, .6, 0), "moss": (.4, .6, -.2), "wet_rock_moss": (.5, .3, .6), "swamp_mud": (.8, 0, -.4),
    "mud_reeds": (.9, -.3, -.4), "marsh_grass": (.4, -.6, -.3), "rainforest": (.1, .7, 0), "rainforest_low": (0, .3, 0),
    "dirt_grass": (-.2, -.2, .2), "dark_grass_rocks": (-.4, -.3, .7), "meadow": (-.4, -.8, -.2), "sand": (-.3, -.5, -.3),
    "wet_sand": (.5, -.5, -.3), "rock": (-.3, 0, 1), "rock2": (-.2, 0, 1), "rock_grass": (-.5, -.4, .8),
    "marsh_mud": (1, 0, -.5), "riverbed_edge": (.4, 0, .6), "river_bottom": (.5, 0, .3), "river_mud": (.8, 0, -.4),
    "beach": (0, -.5, -.3), "dirt_slopes": (.6, -.2, .3), "silt": (.6, -.2, -.5), "leaf_litter": (-.2, .9, 0),
    "dark_moss": (.5, .7, -.2), "fern_floor": (.3, .6, 0), "twig_floor": (-.5, .7, .2), "pebble_earth": (-.4, -.2, .8),
    "marsh_tufts": (.7, -.6, -.3), "grey_mud": (.8, -.3, -.5), "beach_grass": (-.3, -.7, -.2), "pale_sand": (-.4, -.6, -.4),
    "leafy_ground": (.1, .3, .1), "grey_gravel": (-.4, -.3, .9), "black_gravel": (.2, .3, .6), "pale_rock": (-.3, 0, 1),
    "red_rock": (-.4, 0, 1),
}
PALETTE = {  # three or four materials a habitat (vanilla paints 3.15 a quadrant), none over 0.35
    "swamp_hummock": {"forest_floor": .3, "moss": .25, "wet_rock_moss": .2, "dirt_grass": .25},
    "dry_hammock": {"dirt_grass": .25, "meadow": .25, "forest_floor": .25, "dark_grass_rocks": .25},
    "hist_grove": {"moss": .3, "wet_rock_moss": .25, "rainforest": .25, "forest_floor": .2},
    "rainforest_floor": {"rainforest": .3, "rainforest_low": .3, "forest_floor": .2, "moss": .2},
    "riverine_forest": {"rainforest_low": .35, "forest_floor": .35, "moss": .3},
    "coastal_grassland": {"marsh_grass": .35, "meadow": .35, "wet_sand": .3},
    "upland_scrub": {"dark_grass_rocks": .35, "meadow": .35, "rock_grass": .3},
    "rocky_outcrop": {"rock_grass": .35, "rock": .35, "dark_grass_rocks": .3},
    "cliff_face": {"rock": .35, "rock2": .35, "rock_grass": .3},
    "beach_shore": {"sand": .35, "wet_sand": .35, "beach_grass": .3},
    "mangrove_fringe": {"mud_reeds": .3, "marsh_mud": .3, "swamp_mud": .2, "wet_sand": .2},
    "reed_marsh": {"mud_reeds": .3, "marsh_grass": .3, "swamp_mud": .2, "dirt_slopes": .2},
    "cypress_swamp": {"swamp_mud": .3, "moss": .25, "marsh_mud": .25, "river_mud": .2},
    "drowned_forest": {"marsh_mud": .3, "swamp_mud": .3, "moss": .2, "river_mud": .2},
    "open_still_water": {"river_mud": .5, "swamp_mud": .3, "silt": .2},
    "lake_bed": {"river_bottom": .4, "river_mud": .35, "silt": .25},
    "seabed_shallow": {"ocean_floor": .45, "beach": .35, "silt": .2},
    "seabed_mid": {"ocean_floor": .6, "river_mud": .2, "river_bottom": .2},
    "seabed_deep": {"ocean_floor": .7, "river_bottom": .3},
}
HAB_CLASS = {"reed_marsh": "wet", "cypress_swamp": "wet", "drowned_forest": "wet", "mangrove_fringe": "wet",
             "swamp_hummock": "wet", "hist_grove": "forest", "rainforest_floor": "forest", "riverine_forest": "forest",
             "dry_hammock": "forest", "coastal_grassland": "open", "upland_scrub": "open", "rocky_outcrop": "rock",
             "cliff_face": "rock"}
ACCENT = 0.45  # a province's accent's share of a habitat's palette
# Ground provinces, from each region's research (newworld/sources/flora/regions.json habitats and look notes):
# accent: the province's own ground per kind of habitat; road: roadpaint.ROAD_SETS; grass: its grass lists.
PROVINCES = {
    "delta": {  # reed mazes, cattail and black water, mangrove and saltrice, flooded lowland
        "regions": ["ultherus-swamp", "nushara-bayou", "tulmek-washes", "banujha-basin", "kotherra-mangroves"],
        "road": "marsh",
        "accent": {"wet": {"marsh_tufts": .45, "grey_mud": .2, "dark_moss": .35}, "forest": {"dark_moss": .5, "leaf_litter": .5},
                   "open": {"marsh_tufts": .6, "beach_grass": .4}, "rock": {"black_gravel": .5, "wet_rock_moss": .5}},
        "grass": {"marsh_grass": [f"{KM}:ALPAGrassReeds01", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassWildSaltrice01", f"{KM}:ALPAGrassWildSaltrice02"],
                  "meadow": [f"{KM}:ALPAGrassMarsh01", f"{KM}:ALPAGrassMarsh02", f"{KM}:ALPAGrassReeds02"],
                  "forest_floor": [f"{KM}:ALPAGrassFern01", f"{SK}:FernGrass01"]}},
    "darkwood": {  # Hist groves, huge roots, hanging moss and black heart-mud; cairn-fields on steep hills
        "regions": ["murkwood", "blackwood"],
        "road": "forest",
        "accent": {"wet": {"dark_moss": .5, "black_gravel": .2, "marsh_mud": .3}, "forest": {"dark_moss": .4, "fern_floor": .3, "twig_floor": .3},
                   "open": {"dark_moss": .5, "leafy_ground": .5}, "rock": {"black_gravel": .5, "rock2": .5}},
        "grass": {"forest_floor": [f"{KM}:ALPAGrassFern04", f"{SK}:FernGrass01"], "moss": [f"{KM}:ALPAGrassFern03"],
                  "marsh_grass": [f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassMarsh01"]}},
    "jungle": {  # jungle hardwood, tree-ferns and bright fungus; green gorges under pale cliffs
        "regions": ["arnesian-jungle", "chixathe-mesa"],
        "road": "forest",
        "accent": {"wet": {"fern_floor": .5, "leaf_litter": .5}, "forest": {"leaf_litter": .45, "fern_floor": .35, "leafy_ground": .2},
                   "open": {"leafy_ground": .5, "fern_floor": .5}, "rock": {"pale_rock": .5, "pebble_earth": .5}},
        "grass": {"forest_floor": [f"{TS}:TropicalGrass01", f"{KM}:ALPAGrassFern02", f"{TS}:TropicalGrassPlant01"],
                  "rainforest": [f"{KM}:ALPAGrassFern02", f"{SK}:ReachGrass02"], "marsh_grass": [f"{KM}:ALPAGrassRams01", f"{KM}:ALPAGrassNettles01"]}},
    "riverlands": {  # reed banks, fresh marsh and sedge plain, silt islets, ravine-cut mounds
        "regions": ["nha-enasa", "valley-of-storms", "lake-ulaish"],
        "road": "marsh",
        "accent": {"wet": {"marsh_tufts": .4, "grey_mud": .3, "leafy_ground": .3}, "forest": {"twig_floor": .5, "fern_floor": .5},
                   "open": {"meadow": .4, "marsh_tufts": .3, "leafy_ground": .3}, "rock": {"pebble_earth": .5, "grey_gravel": .5}},
        "grass": {"marsh_grass": [f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassMarsh02"],
                  "meadow": [f"{SK}:FieldGrass01", f"{KM}:ALPAGrassMarsh02"], "forest_floor": [f"{SK}:FernGrass01"]}},
    "redclay": {  # low red clay mounds, ochre-stained marsh, red-gum hills and a burn-scar regrowing
        "regions": ["okuwun-rahei", "cape-percar"],
        "road": "clay",
        "accent": {"wet": {"rock_grass": .3, "marsh_tufts": .4, "grey_mud": .3}, "forest": {"rock_grass": .4, "twig_floor": .3, "leaf_litter": .3},
                   "open": {"rock_grass": .5, "meadow": .5}, "rock": {"red_rock": .6, "pebble_earth": .4}},
        "grass": {"meadow": [f"{SK}:TundraGrass01", f"{KM}:ALPAGrassRams01"],
                  "marsh_grass": [f"{KM}:ALPAGrassRams01", f"{KM}:ALPAGrassWildSaltrice02"],
                  "forest_floor": [f"{SK}:ReachGrass01", f"{SK}:FallForestGrass02"]}},
    "coast": {  # temperate grassland, grey mud-flats, rice paddies, white Ayleid stone in reed beds
        "regions": ["hatandros-bight", "althii-archipelago", "barsaebica"],
        "road": "coast",
        "accent": {"wet": {"grey_mud": .5, "marsh_tufts": .5}, "forest": {"leafy_ground": .5, "twig_floor": .5},
                   "open": {"beach_grass": .4, "meadow": .3, "grey_mud": .3}, "rock": {"pale_rock": .5, "grey_gravel": .5}},
        "grass": {"meadow": [f"{SK}:ForestGrass01", f"{KM}:ALPAGrassMarsh02"],
                  "marsh_grass": [f"{KM}:ALPAGrassWildSaltrice01", f"{KM}:ALPAGrassWildSaltrice02", f"{KM}:ALPAGrassWildSaltrice02", f"{KM}:ALPAGrassWildSaltrice01"],
                  "forest_floor": [f"{SK}:ForestGrass01"]}},
    "isles": {  # scrub on the hills, sea-worn crags, shingle beaches, wind-cut grass
        "regions": ["aphon-isle", "skeith-isle", "aunike-ridge"],
        "road": "upland",
        "accent": {"wet": {"marsh_tufts": .5, "grey_gravel": .5}, "forest": {"pebble_earth": .5, "leafy_ground": .5},
                   "open": {"pebble_earth": .4, "grey_gravel": .3, "beach_grass": .3}, "rock": {"grey_gravel": .5, "pale_rock": .5}},
        "grass": {"meadow": [f"{SK}:TundraGrass01", f"{SK}:TundraGrass03"],
                  "marsh_grass": [f"{SK}:TundraGrass01"],
                  "rock_grass": [f"{SK}:RockGrass01"]}},
}
# Every grassy material a province does not list carries the province's own list for its role (no grass list is shared
# by every region): the role's grass keeps the material's habit (moss low, reeds tall, dry tufts short, beach grass).
ROLE = {"moss": "moss", "wet_rock_moss": "moss", "dark_moss": "moss", "mud_reeds": "reeds", "swamp_mud": "reeds",
        "marsh_tufts": "reeds", "dirt_slopes": "reeds", "rainforest": "forest", "rainforest_low": "forest",
        "leaf_litter": "forest", "fern_floor": "forest", "leafy_ground": "forest", "forest_floor": "forest",
        "dirt_grass": "dry", "dark_grass_rocks": "dry", "pebble_earth": "dry", "rock_grass": "dry", "meadow": "dry",
        "marsh_grass": "reeds", "beach_grass": "beach"}
ROLES = {
    "delta": {"moss": [f"{SK}:FernGrass01", f"{KM}:ALPAGrassFern01"], "reeds": [f"{KM}:ALPAGrassReeds01", f"{KM}:ALPAGrassReeds02", f"{TS}:CattailGrass01"],
              "forest": [f"{KM}:ALPAGrassFern01", f"{KM}:ALPAGrassMarsh01"], "dry": [f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassMarsh02"],
              "beach": [f"{KM}:ALPAGrassWildSaltrice02", f"{SK}:BeachGrass02"]},
    "darkwood": {"moss": [f"{KM}:ALPAGrassFern04"], "reeds": [f"{KM}:ALPAGrassReeds02", f"{SK}:FrozenMarshGrass01"],
                 "forest": [f"{KM}:ALPAGrassFern03", f"{KM}:ALPAGrassFern04"], "dry": [f"{SK}:FrozenMarshGrass01", f"{KM}:ALPAGrassFern04"],
                 "beach": [f"{KM}:ALPAGrassReeds02"]},
    "jungle": {"moss": [f"{KM}:ALPAGrassFern02"], "reeds": [f"{KM}:ALPAGrassNettles01", f"{KM}:ALPAGrassRams01"],
               "forest": [f"{TS}:TropicalGrassPlant01", f"{TS}:TropicalGrass01", f"{KM}:ALPAGrassFern02"],
               "dry": [f"{TS}:TropicalGrassPlant02", f"{SK}:ReachGrass02"], "beach": [f"{TS}:TropicalGrass01"]},
    "riverlands": {"moss": [f"{KM}:ALPAGrassMarsh02"], "reeds": [f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassReeds01"],
                   "forest": [f"{SK}:FieldGrass01", f"{SK}:ForestGrass02"], "dry": [f"{SK}:FieldGrass01", f"{KM}:ALPAGrassMarsh02"], "beach": [f"{KM}:ALPAGrassReeds01"]},
    "redclay": {"moss": [f"{SK}:FallForestGrass02"], "reeds": [f"{KM}:ALPAGrassWildSaltrice02", f"{SK}:FallForestGrass01"],
                "forest": [f"{SK}:ReachGrass01", f"{SK}:FallForestGrass01"], "dry": [f"{SK}:TundraGrass01", f"{SK}:FallForestGrass02"],
                "beach": [f"{KM}:ALPAGrassWildSaltrice02"]},
    "coast": {"moss": [f"{SK}:ForestGrass01"], "reeds": [f"{KM}:ALPAGrassWildSaltrice01", f"{KM}:ALPAGrassWildSaltrice01"],
              "forest": [f"{SK}:ForestGrass01"], "dry": [f"{SK}:ForestGrass01", f"{KM}:ALPAGrassWildSaltrice01"],
              "beach": [f"{SK}:BeachGrass02", f"{KM}:ALPAGrassWildSaltrice01"]},
    "isles": {"moss": [f"{SK}:RockGrass01"], "reeds": [f"{SK}:TundraGrass01"], "forest": [f"{SK}:TundraGrass03"],
              "dry": [f"{SK}:RockGrass01", f"{SK}:TundraGrass03"], "beach": [f"{SK}:BeachGrass01"]},
}
for _p, _v in PROVINCES.items():
    for _m, _r in ROLE.items():
        _v["grass"].setdefault(_m, ROLES[_p][_r])
# Each region's own signature on top of its province, from its research's look notes: one ground it shows more of
# (at least SIG of every classed habitat's palette) and its own grass list on one grassy material.
REGIONS = {
    "ultherus-swamp": {"look": "dark_moss", "grass": {"marsh_grass": ["FlowerFields.esp:ESuColumbine01Red", "FlowerFields.esp:ESpPasqueflower01red", f"{TS}:CattailGrass01", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassReeds01"], "meadow": ["FlowerFields.esp:ESuColumbine01Red", "FlowerFields.esp:ESpPasqueflower01red", f"{KM}:ALPAGrassMarsh01", f"{KM}:ALPAGrassReeds02"], "forest_floor": ["FlowerFields.esp:ESuColumbine01Red", "FlowerFields.esp:ESpPasqueflower01red", f"{KM}:ALPAGrassFern01", f"{SK}:FrozenMarshGrass01"]}},
    "nushara-bayou": {"look": "river_mud", "grass": {"marsh_grass": ["FlowerFields.esp:ESuOxeyeDaisy01", f"{KM}:ALPAGrassWildSaltrice02", f"{KM}:ALPAGrassWildSaltrice01", f"{KM}:ALPAGrassFern03"], "meadow": ["FlowerFields.esp:ESuOxeyeDaisy01", f"{KM}:ALPAGrassFern03", f"{KM}:ALPAGrassNettles01"], "forest_floor": ["FlowerFields.esp:ESuOxeyeDaisy01", f"{KM}:ALPAGrassFern01", f"{SK}:FernGrass01"]}},
    "tulmek-washes": {"look": "silt", "grass": {"meadow": [f"{SK}:FieldGrass02", f"{SK}:TundraGrass01"], "marsh_grass": [f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassMarsh02"], "forest_floor": [f"{SK}:FieldGrass02", f"{SK}:FernGrass01"], "dirt_slopes": ["FlowerFields.esp:ESuClover02leaves"]}},
    "banujha-basin": {"look": "marsh_mud", "grass": {"marsh_grass": ["FlowerFields.esp:ESpTulip02Orange1", f"{KM}:ALPAGrassReeds01", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassMarsh01"], "meadow": ["FlowerFields.esp:ESpTulip02Orange1", f"{KM}:ALPAGrassMarsh02", f"{KM}:ALPAGrassReeds02"], "forest_floor": ["FlowerFields.esp:ESpTulip02Orange1", f"{KM}:ALPAGrassFern01", f"{KM}:ALPAGrassReeds01"], "mud_reeds": ["FlowerFields.esp:ESpIris01Leaves", "FlowerFields.esp:ESpSiberianIris01"], "swamp_mud": ["FlowerFields.esp:ESpSiberianIris01"]}},
    "kotherra-mangroves": {"look": "wet_sand", "grass": {"forest_floor": ["FlowerFields.esp:ESuPoppy02Red", f"{KM}:ALPAGrassFern03", f"{KM}:ALPAGrassFern01"], "marsh_grass": ["FlowerFields.esp:ESuPoppy02Red", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassFern01"], "meadow": ["FlowerFields.esp:ESuPoppy02Red", f"{KM}:ALPAGrassFern03", f"{KM}:ALPAGrassWildSaltrice02"]}},
    "murkwood": {"look": "wet_rock_moss", "grass": {"moss": [f"{KM}:ALPAGrassFern04", f"{SK}:FernGrass01"], "forest_floor": [f"{KM}:ALPAGrassFern04", f"{SK}:FernGrass01"], "marsh_grass": [f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassFern04"], "marsh_tufts": ["FlowerFields.esp:ESpLiverleaf01leaves"]}},
    "blackwood": {"look": "rock2", "grass": {"marsh_grass": [f"{KM}:ALPAGrassLupin02", f"{SK}:FrozenMarshGrass01", f"{KM}:ALPAGrassReeds02"], "meadow": [f"{KM}:ALPAGrassLupin02", f"{KM}:ALPAGrassFern04"], "forest_floor": [f"{KM}:ALPAGrassLupin02", f"{SK}:FernGrass01"], "moss": ["FlowerFields.esp:ESpLadysMantle01"], "wet_rock_moss": ["FlowerFields.esp:ESpLadysMantle01"], "dark_moss": ["FlowerFields.esp:ESpLadysMantle01", f"{KM}:ALPAGrassFern03"], "fern_floor": ["FlowerFields.esp:ESpPacificbleedingheart01leaves"]}},
    "arnesian-jungle": {"look": "rainforest_low", "grass": {"rainforest": ["FlowerFields.esp:ESuWelshPoppy01Orange", "FlowerFields.esp:ESpTulipOrange", f"{TS}:TropicalGrassPlant02", f"{KM}:ALPAGrassFern02", f"{TS}:TropicalGrass01"], "forest_floor": ["FlowerFields.esp:ESuWelshPoppy01Orange", "FlowerFields.esp:ESpTulipOrange", f"{TS}:TropicalGrass01", f"{KM}:ALPAGrassFern02", f"{TS}:TropicalGrassPlant01"], "marsh_grass": ["FlowerFields.esp:ESuWelshPoppy01Orange", "FlowerFields.esp:ESpTulipOrange", f"{KM}:ALPAGrassRams01", f"{KM}:ALPAGrassNettles01"]}},
    "chixathe-mesa": {"look": "pebble_earth", "grass": {"meadow": ["FlowerFields.esp:ESpPasqueflower01white", f"{SK}:TundraGrass03", f"{SK}:ReachGrass01"], "forest_floor": ["FlowerFields.esp:ESpPasqueflower01white", f"{SK}:ReachGrass01", f"{KM}:ALPAGrassFern02"], "marsh_grass": ["FlowerFields.esp:ESpPasqueflower01white", f"{SK}:TundraGrass03", f"{KM}:ALPAGrassRams01"]}},
    "nha-enasa": {"look": "grey_gravel", "grass": {"marsh_grass": [f"{KM}:ALPAGrassButtercup01", f"{KM}:ALPAGrassReeds02"], "meadow": [f"{KM}:ALPAGrassButtercup01", f"{KM}:ALPAGrassMarsh02"], "forest_floor": [f"{KM}:ALPAGrassButtercup01", f"{SK}:FernGrass01"]}},
    "valley-of-storms": {"look": "dirt_slopes", "grass": {"meadow": [f"{KM}:ALPAGrassLupin01", f"{SK}:ReachGrass02"], "marsh_grass": [f"{KM}:ALPAGrassLupin01", f"{KM}:ALPAGrassMarsh02"], "forest_floor": [f"{SK}:FernGrass01", f"{SK}:ReachGrass02"]}},
    "lake-ulaish": {"look": "silt", "grass": {"marsh_grass": ["FlowerFields.esp:ESpLiverleaf02AGblue", "FlowerFields.esp:ESuColumbine01Blue", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassReeds01", f"{KM}:ALPAGrassWildSaltrice02"], "meadow": ["FlowerFields.esp:ESpLiverleaf02AGblue", "FlowerFields.esp:ESuColumbine01Blue", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassMarsh01"], "forest_floor": ["FlowerFields.esp:ESpLiverleaf02AGblue", "FlowerFields.esp:ESuColumbine01Blue", f"{KM}:ALPAGrassReeds02", f"{KM}:ALPAGrassFern01"]}},
    "okuwun-rahei": {"look": "rock_grass", "grass": {"meadow": ["FlowerFields.esp:ESuWelshPoppy01Red", f"{SK}:VolcanicGrass02", "Dragonborn.esm:DLC02VolcanicAshGrass01"], "marsh_grass": ["FlowerFields.esp:ESuWelshPoppy01Red", f"{KM}:ALPAGrassWildSaltrice01", f"{SK}:VolcanicGrass02", f"{KM}:ALPAGrassRams01"], "forest_floor": ["FlowerFields.esp:ESuWelshPoppy01Red", f"{SK}:VolcanicGrass02", f"{SK}:FallForestGrass02"]}},
    "cape-percar": {"look": "twig_floor", "grass": {"meadow": ["FlowerFields.esp:ESpTulipRed", f"{KM}:ALPAGrassRams01", f"{SK}:FallForestGrass02"], "marsh_grass": ["FlowerFields.esp:ESpTulipRed", f"{KM}:ALPAGrassRams01", f"{KM}:ALPAGrassWildSaltrice02"], "forest_floor": ["FlowerFields.esp:ESpTulipRed", f"{KM}:ALPAGrassRams01", f"{SK}:ForestGrass02"]}},
    "hatandros-bight": {"look": "grey_mud", "grass": {"meadow": ["FlowerFields.esp:ESuHeather02", "FlowerFields.esp:ESuHeather02"], "marsh_grass": [f"{KM}:ALPAGrassWildSaltrice01", "FlowerFields.esp:ESuHeather02"], "forest_floor": [f"{SK}:ForestGrass01", "FlowerFields.esp:ESuHeather02"]}},
    "althii-archipelago": {"look": "meadow", "grass": {"marsh_grass": ["FlowerFields.esp:ESpTulip02Orange2", f"{KM}:ALPAGrassWildSaltrice01", f"{KM}:ALPAGrassWildSaltrice02", f"{KM}:ALPAGrassWildSaltrice02", f"{KM}:ALPAGrassWildSaltrice01"], "meadow": ["FlowerFields.esp:ESpTulip02Orange2", f"{KM}:ALPAGrassWildSaltrice01", f"{KM}:ALPAGrassReeds01"], "forest_floor": ["FlowerFields.esp:ESpTulip02Orange2", f"{SK}:ForestGrass01", f"{KM}:ALPAGrassFern01"]}},
    "barsaebica": {"look": "pale_rock", "grass": {"marsh_grass": [f"{KM}:ALPAGrassYarrow01", f"{KM}:ALPAGrassMarsh02", f"{KM}:ALPAGrassReeds02"], "meadow": [f"{KM}:ALPAGrassMarsh02", f"{KM}:ALPAGrassYarrow01"], "forest_floor": [f"{SK}:ForestGrass01", f"{KM}:ALPAGrassYarrow01"]}},
    "aphon-isle": {"look": "pebble_earth", "grass": {"meadow": [f"{SK}:TundraGrass04", f"{SK}:TundraGrass01", f"{SK}:BeachGrass02"], "marsh_grass": [f"{SK}:TundraGrass04", f"{SK}:TundraGrass01"], "rock_grass": [f"{SK}:RockGrass01", f"{SK}:TundraGrass04"]}},
    "skeith-isle": {"look": "grey_gravel", "grass": {"meadow": [f"{KM}:ALPAGrassButtercup02", f"{SK}:BeachGrass01", f"{SK}:RockGrass01"], "marsh_grass": [f"{KM}:ALPAGrassButtercup02", f"{SK}:BeachGrass02", f"{SK}:TundraGrass01"], "rock_grass": [f"{SK}:RockGrass01"]}},
    "aunike-ridge": {"look": "dark_grass_rocks", "grass": {"meadow": [f"{KM}:ALPAGrassHeather02", f"{SK}:ReachGrass02", f"{SK}:TundraGrass03"], "marsh_grass": [f"{KM}:ALPAGrassHeather02", f"{SK}:TundraGrass01"], "rock_grass": [f"{KM}:ALPAGrassHeather02", f"{SK}:RockGrass01"]}},
}
SIG = 0.2  # the least a region's signature ground holds of each classed habitat's palette
PROV = list(PROVINCES)
DEFAULT_ROAD = "forest"
ROAD_SET_NAMES = list(rp.ROAD_SETS)
BASE = list(MATERIALS)
VARIANTS = [(m, p) for p in PROV for m in PROVINCES[p]["grass"]] + [(m, r) for r in REGIONS for m in REGIONS[r]["grass"]]
MAT = BASE + [f"{m}~{p}" for m, p in VARIANTS]
MI = {m: i for i, m in enumerate(MAT)}
NM = len(MAT)
ROAD_IX = np.array([MI[m] for m in rp.ROAD_MATERIALS])
ROAD_COMMON = MI[rp.COMMON_TRACK]
IS_ROAD = np.zeros(NM, bool)
IS_ROAD[ROAD_IX] = True


def material_rows() -> list[dict]:
    rows = []
    for i, m in enumerate(MAT):
        base, _, scope = m.partition("~")
        ltex, grass, diffuse = MATERIALS[base]
        if scope:
            grass = (PROVINCES[scope] if scope in PROVINCES else REGIONS[scope])["grass"][base]
        grass = list(dict.fromkeys(grass))  # a list names a grass once
        rows.append({"index": i, "id": m, "ltex": ltex, "grass": grass, "diffuse": diffuse, "road": base in rp.ROAD_MATERIALS,
                     "scope": scope or None})
    return rows


# water's edge: per edge family, knots of signed shore distance (m, + land) -> material weights; pull to 0 at the ends
EDGE = {
    "marsh": [(-20, {"river_mud": .5, "swamp_mud": .3, "dirt_slopes": .2}), (-7, {"swamp_mud": .35, "dirt_slopes": .3, "river_mud": .35}),
              (-1, {"dirt_slopes": .5, "swamp_mud": .3, "river_mud": .2}), (1, {"dirt_slopes": .55, "mud_reeds": .25, "swamp_mud": .2}),
              (3.5, {"marsh_grass": .3, "dirt_slopes": .3, "mud_reeds": .25, "swamp_mud": .15}),
              (7.5, {"marsh_grass": .3, "dirt_slopes": .15, "mud_reeds": .2, "moss": .2, "swamp_mud": .15}),
              (15, {"marsh_grass": .25, "moss": .2, "forest_floor": .3, "dirt_slopes": .1, "mud_reeds": .15})],
    "sea": [(-30, {"ocean_floor": .6, "beach": .4}), (-8, {"beach": .5, "ocean_floor": .35, "silt": .15}),
            (-1, {"beach": .6, "wet_sand": .2, "ocean_floor": .2}), (1, {"beach": .55, "wet_sand": .3, "sand": .15}),
            (4, {"beach": .45, "sand": .35, "wet_sand": .2}), (15, {"sand": .35, "beach": .2, "beach_grass": .25, "marsh_grass": .2}),
            (35, {"beach_grass": .3, "marsh_grass": .3, "meadow": .4})],
    "mangrove": [(-20, {"river_mud": .5, "marsh_mud": .5}), (-2, {"swamp_mud": .4, "marsh_mud": .35, "mud_reeds": .25}),
                 (2, {"mud_reeds": .45, "swamp_mud": .25, "marsh_mud": .3}),
                 (12, {"mud_reeds": .35, "swamp_mud": .2, "marsh_grass": .25, "marsh_mud": .2})],
    "river": [(-15, {"river_bottom": .5, "river_mud": .3, "riverbed_edge": .2}), (-7, {"river_bottom": .45, "riverbed_edge": .3, "river_mud": .25}),
              (-3, {"riverbed_edge": .5, "river_bottom": .5}), (-1, {"riverbed_edge": .7, "river_bottom": .3}),
              (1, {"riverbed_edge": .75, "rock_grass": .25}), (3.5, {"riverbed_edge": .5, "rock_grass": .2, "forest_floor": .3}),
              (8, {"riverbed_edge": .25, "forest_floor": .45, "rock_grass": .3})],
    "lake": [(-20, {"riverbed_edge": .6, "river_bottom": .4}), (-3, {"riverbed_edge": .55, "rock_grass": .45}),
             (1, {"rock_grass": .55, "riverbed_edge": .45}), (4, {"rock_grass": .55, "riverbed_edge": .25, "dark_grass_rocks": .2}),
             (8, {"rock_grass": .45, "dark_grass_rocks": .35, "riverbed_edge": .2})],
}
EDGE_REACH = {"marsh": (-25, 22), "sea": (-40, 45), "mangrove": (-25, 18), "river": (-20, 11), "lake": (-25, 11)}
KIND_EDGE = {"ocean": "sea", "shallow-coast": "sea", "bay": "sea", "estuary": "mangrove", "river": "river",
             "stream": "river", "lake": "lake", "pond": "marsh", "green-marsh": "marsh", "blackwater-swamp": "marsh"}
ROCK = {"rock": .5, "rock_grass": .5}
NOISE_SEED = 9113
K_ENV = 1.5   # the middle scale: moisture, shade and roughness
K_FINE = 1.8  # the small scale: each material's own value noise at 15 and 37 m
ROAD_WATER = (0.9, 8.9)  # shore distance (m; the waterline lies half a sample from the last land vertex): no road
# from here, the whole road from there
FINE_S = (8, 20)  # samples
LEAN_SPREAD = 0.25  # the spread (weighted s.d.) of a palette's materials' leanings on the median land region's median vertex
EVEN_FINE = 1.0  # what the small scale's gain rises by on ground that leans every material alike


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def vec(d: dict) -> np.ndarray:
    v = np.zeros(NM, np.float32)
    for k, w in d.items():
        v[MI[k]] = w
    return v / v.sum()


def code_key() -> str:
    h = hashlib.sha256(Path(__file__).read_bytes() + Path(rp.__file__).read_bytes())
    return h.hexdigest()[:16]


def _hash(i, j, seed: int) -> np.ndarray:
    h = (i * 374761393 + j * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float32) / 32767.5 - 1


def vnoise(seed: int, r: np.ndarray, c: np.ndarray, s: float) -> np.ndarray:
    """Value noise at global sample positions (rows, cols), lattice spacing s samples, about unit std; a pure function
    of position, so overlapping windows agree."""
    fr, fc = r / s, c / s
    i, j = np.floor(fr).astype(np.int64), np.floor(fc).astype(np.int64)
    u, v = fr - i, fc - j
    u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
    a, b = _hash(i, j, seed), _hash(i, j + 1, seed)
    c_, d = _hash(i + 1, j, seed), _hash(i + 1, j + 1, seed)
    return ((a + (b - a) * v) * (1 - u) + (c_ + (d - c_) * v) * u) / 0.42


def road_mix(wy, wx) -> np.ndarray:
    """The along-road noise that shares a road's core between its two track materials, at world sample positions
    (wy = -world y / 128, wx = world x / 128): a pure function of where the vertex is, so the world's roads, a place's
    paths (tools/places/build.py) and the studio (path_paint.js roadMix) vary alike."""
    return 0.7 * vnoise(NOISE_SEED + 777, wy, wx, 60) + 0.3 * vnoise(NOISE_SEED + 778, wy, wx, 130)


def edge_table(knots, lo, hi, n=256):
    """Signed distance grid (m) over [lo, hi] -> (weights [n, NM], pull [n])."""
    xs = np.linspace(lo, hi, n)
    kx = np.array([k[0] for k in knots])
    kv = np.stack([vec(k[1]) for k in knots])
    w = np.stack([np.interp(xs, kx, kv[:, j]) for j in range(NM)], 1)
    w /= w.sum(1, keepdims=True)
    # pull: 1 across the knots' span, cosine fade to 0 at the reach ends
    a, b = kx[0], kx[-1]
    pull = np.ones(n, np.float32)
    lo_f = xs < a
    pull[lo_f] = 0.5 - 0.5 * np.cos(np.pi * (xs[lo_f] - lo) / (a - lo))
    hi_f = xs > b
    pull[hi_f] = 0.5 + 0.5 * np.cos(np.pi * (xs[hi_f] - b) / (hi - b))
    return xs, w.astype(np.float32), pull


def province_of(regions: list[str]) -> np.ndarray:
    """Region index -> province index + 1 (0: none, the sea regions)."""
    by = {r: k + 1 for k, p in enumerate(PROV) for r in PROVINCES[p]["regions"]}
    return np.array([by.get(r, 0) for r in regions] + [0] * (256 - len(regions)), np.int16)


def signed(v: np.ndarray, look: int) -> np.ndarray:
    """A palette with the region's signature ground brought up to SIG of it (the rest scaled down). Where the
    province's accent already gives that ground SIG or more, the palette stands: the signature is never stacked on
    the accent, which would make one ground more than twice any other and one long swathe of it."""
    if v[look] >= SIG:
        return v
    out = v * ((1 - SIG) / (1 - v[look]))
    out[look] = SIG
    return out


class Painter:
    def __init__(self, legend):
        H, W = legend["shape"]
        self.habs = legend["habitats"]
        self.kinds = legend["kinds"]
        regions = legend["regions"]
        prov = province_of(regions)
        # palette per (region, habitat): the habitat's own, blended with its province's accent for its kind of ground and
        # the region's signature ground
        self.hab_vec = np.zeros((256, len(self.habs), NM), np.float32)
        for i, h in enumerate(self.habs):
            own = vec(PALETTE.get(h, {"forest_floor": 1}))
            self.hab_vec[:, i] = own
            cls = HAB_CLASS.get(h)
            if cls is None:
                continue
            for r, rn in enumerate(regions):
                v = own
                if prov[r]:
                    v = (1 - ACCENT) * own + ACCENT * vec(PROVINCES[PROV[prov[r] - 1]]["accent"][cls])
                if rn in REGIONS:
                    v = signed(v, MI[REGIONS[rn]["look"]])
                self.hab_vec[r, i] = v
        self.aff = np.zeros((NM, 3), np.float32)
        for m, a in AFF.items():
            self.aff[MI[m]] = a
        # each region's grass variant of a material (its own, else its province's): [region, NM] -> material index
        self.variant = np.tile(np.arange(NM), (256, 1))
        for r, rn in enumerate(regions):
            if prov[r]:
                for m in PROVINCES[PROV[prov[r] - 1]]["grass"]:
                    self.variant[r, MI[m]] = MI[f"{m}~{PROV[prov[r] - 1]}"]
            for m in REGIONS.get(rn, {}).get("grass", {}):
                self.variant[r, MI[m]] = MI[f"{m}~{rn}"]
        # each region's road set; its materials [set, 3]
        self.region_road = np.array([ROAD_SET_NAMES.index(PROVINCES[PROV[prov[r] - 1]]["road"] if r < len(regions) and prov[r] else DEFAULT_ROAD)
                                     for r in range(256)])
        self.set_mats = np.array([[MI[x] for x in rp.ROAD_SETS[n]] for n in ROAD_SET_NAMES])
        self.road_col = {int(m): k for k, m in enumerate(ROAD_IX)}
        self.fields = lc.Fields((H, W), BASE + ["_rock"], seed=NOISE_SEED)
        for k, m in enumerate(BASE):  # material mixes vary at 30 to 300 m, so a 1 km window always holds several
            self.fields.f[m] = lc.fbm(NOISE_SEED + 500 + k, self.fields.cs, (2, 6, 20), (0.5, 1.0, 0.3))
        self.edges = {k: edge_table(v, *EDGE_REACH[k]) for k, v in EDGE.items()}
        self.kind_edge = np.full(256, -1, np.int16)
        names = list(EDGE)
        for i, k in enumerate(self.kinds):
            self.kind_edge[i] = names.index(KIND_EDGE[k])
        self.edge_names = names
        self.rock = vec(ROCK)
        self.arr = {n: np.load(LC / f"{n}.npy", mmap_mode="r") for n in
                    ("habitat", "kind", "shore", "road", "roadcls", "slope", "region", "canopy", "relief")}
        self.mangrove = self.habs.index("mangrove_fringe")
        ox, oy = legend["origin_world"]
        self.world_off = (int(round(-oy / legend["sample_units"])), int(round(ox / legend["sample_units"])))

    def weights(self, r0, r1, c0, c1):
        """For sample rows r0:r1, cols c0:c1 (clipped to the grid): (the ground's painted, unblurred weights [rows, cols,
        NM]; the road's pull [rows, cols]; the road materials' weights [rows, cols, len(ROAD_IX)], summing to the pull).
        The road is laid over the ground after the ground's blur: its ramp is smooth by its rule, and blurring it would
        leave ground (and grass) on its spine."""
        A = self.arr
        sl = (slice(r0, r1), slice(c0, c1))
        hab = np.asarray(A["habitat"][sl])
        reg = np.asarray(A["region"][sl])
        rr, cc = np.mgrid[r0:r1, c0:c1].astype(np.float32)
        wr, wc = self.fields.coords(rr, cc)
        w = self.hab_vec[reg, hab]
        # the ground's state at the middle and small scale
        shore = np.asarray(A["shore"][sl], np.float32) / 10
        slope = np.asarray(A["slope"][sl], np.float32)
        relief = np.asarray(A["relief"][sl], np.float32) / 10  # m
        canopy = np.asarray(A["canopy"][sl], np.float32) / 200
        wet = np.clip((25 - shore) / 25, 0, 1) + np.clip(-relief / 1.5, -0.6, 1)
        shade = np.clip(2 * canopy - 1, -1, 1)
        rough = np.clip(slope / 20, 0, 1.5) + np.clip(relief / 1.5, -0.6, 1)
        env = np.stack([wet, shade, rough], -1)
        ri, ci = rr.astype(np.int64), cc.astype(np.int64)
        # where the ground's state does not tell a palette's materials apart (they lean alike, as gravel, rock and
        # scrub do on an even open slope), the small scale carries the break instead: its gain rises by up to
        # EVEN_FINE as the spread of the materials' leanings falls from LEAN_SPREAD to nothing
        nb = len(BASE)
        lean_all = env @ self.aff[:nb].T
        mean = (w[..., :nb] * lean_all).sum(-1, keepdims=True)
        spread = np.sqrt((w[..., :nb] * (lean_all - mean) ** 2).sum(-1))
        k_fine = K_FINE + EVEN_FINE * np.clip(1 - spread / LEAN_SPREAD, 0, 1)
        del lean_all, mean, spread
        for j, m in enumerate(BASE):
            col = w[..., j]
            nz = col > 0
            if not nz.any():
                continue
            fine = 0.6 * vnoise(NOISE_SEED + 31 * j, ri[nz], ci[nz], FINE_S[0]) + 0.4 * vnoise(NOISE_SEED + 31 * j + 7, ri[nz], ci[nz], FINE_S[1])
            lean = env[nz] @ self.aff[j]
            col[nz] *= np.exp(1.4 * self.fields.at(m, wr[nz], wc[nz]) + K_ENV * lean + k_fine[nz] * fine)
        w /= w.sum(-1, keepdims=True) + 1e-9
        # rock patches on slopes
        steep = slope > 18
        if steep.any():
            q = np.zeros(slope.shape, np.float32)
            q[steep] = np.clip((slope[steep] - 22) / 15, 0, 1) * np.clip(0.6 + 0.6 * self.fields.at("_rock", wr[steep], wc[steep]), 0, 1)
            w = w * (1 - q[..., None]) + q[..., None] * self.rock
        # water's edge
        kind = np.asarray(A["kind"][sl])
        fam = self.kind_edge[kind]
        fam = np.where((fam == self.edge_names.index("sea")) & (hab == self.mangrove), self.edge_names.index("mangrove"), fam)
        for fi, name in enumerate(self.edge_names):
            xs, tw, pull = self.edges[name]
            m = (fam == fi) & (shore > xs[0]) & (shore < xs[-1])
            if not m.any():
                continue
            t = np.clip(np.rint((shore[m] - xs[0]) / (xs[-1] - xs[0]) * (len(xs) - 1)).astype(int), 0, len(xs) - 1)
            p = pull[t][:, None]
            w[m] = w[m] * (1 - p) + p * tw[t]
        # roads (roadpaint.py): the measured ramp from the surface edge, track core to verge, two tracks along it
        road = np.asarray(A["road"][sl], np.float32) / 10
        cls = np.asarray(A["roadcls"][sl])
        # where a major and a minor road meet, the class (half width and scale) blends over ~3 vertices, so the nearer
        # road's change of class is a flare, never a step (read 24 rows wider than the window, as below)
        ra, rb = max(r0 - 24, 0), min(r1 + 24, A["roadcls"].shape[0])
        major = ndi.gaussian_filter((np.asarray(A["roadcls"][ra:rb, c0:c1]) == 1).astype(np.float32), 3, mode="nearest")[r0 - ra:r0 - ra + cls.shape[0]]
        half = rp.HALF_M["minor"] + (rp.HALF_M["major"] - rp.HALF_M["minor"]) * major
        scale = rp.SCALE["minor"] + (rp.SCALE["major"] - rp.SCALE["minor"]) * major
        near = (cls > 0) & (road - half < rp.reach_m(1.0)) & (shore > ROAD_WATER[0])
        pull = np.zeros(road.shape, np.float32)
        road_w = np.zeros(road.shape + (len(ROAD_IX),), np.float32)
        if near.any():
            e = road[near] - half[near]
            mix = road_mix(ri[near] + self.world_off[0], ci[near] + self.world_off[1])
            p, a, b, v = rp.road_weights(e, scale[near], mix)
            # toward water the road is capped by a ramp of its own (the lower of the two: never steeper than either)
            cap = np.clip((shore[near] - ROAD_WATER[0]) / (ROAD_WATER[1] - ROAD_WATER[0]), 0, 1)
            k = np.minimum(p, cap) / np.maximum(p, 1e-9)
            p, a, b, v = p * k, a * k, b * k, v * k
            # where two ground provinces' road sets meet, each set's share blends over ~10 m (no join in one vertex)
            # (read 24 rows wider than the window, the blur's reach, so every window paints a vertex alike)
            wide = self.region_road[np.asarray(A["region"][ra:rb, c0:c1])]
            onehot = np.stack([(wide == k).astype(np.float32) for k in range(len(ROAD_SET_NAMES))], -1)
            soft = ndi.gaussian_filter(onehot, (6, 6, 0), mode="nearest")[r0 - ra:r0 - ra + reg.shape[0]][near]
            soft /= soft.sum(-1, keepdims=True) + 1e-9
            rv = np.zeros((e.size, len(ROAD_IX)), np.float32)
            idx = np.arange(e.size)
            for k in range(len(ROAD_SET_NAMES)):
                for col, x in zip(self.set_mats[k], (a, b, v)):
                    np.add.at(rv, (idx, self.road_col[col]), soft[:, k] * x)
            pull[near] = p
            road_w[near] = rv
        # the region's grass: a grassy material takes its region's (else its province's) variant
        out = np.zeros_like(w)
        for k in np.unique(reg):
            m = reg == k
            sub = np.zeros((int(m.sum()), NM), np.float32)
            np.add.at(sub.T, self.variant[k], w[m].T)
            out[m] = sub
        return out, pull, road_w


def top_v(w: np.ndarray) -> np.ndarray:
    """Each vertex keeps its TOP_V heaviest ground materials and its 3 heaviest road materials, each group keeping its
    share of the vertex (where two road sets meet, the road is never outweighed by the ground for want of a slot)."""
    road = w[..., IS_ROAD].sum(-1, keepdims=True)
    out = np.zeros_like(w)
    for grp, k, share in ((~IS_ROAD, TOP_V, 1 - road), (IS_ROAD, 3, road)):
        part = np.where(grp, w, 0)
        n = int(grp.sum())
        kth = np.partition(part, NM - min(k, n), axis=-1)[..., NM - min(k, n):NM - min(k, n) + 1]
        part = np.where((part >= kth) & grp, part, 0)
        tot = part.sum(-1, keepdims=True)
        out += part * (share / np.maximum(tot, 1e-9))
    return out


def prune(w: np.ndarray) -> np.ndarray:
    """Traces under PRUNE are dropped before the sets are chosen (a step of at most PRUNE), the road's materials and the
    ground's each keeping their share of the vertex (so the road's ramp is the blurred ramp, never a plateau where the
    ground's traces went), and each keeping its heaviest material when every one of its traces would go."""
    road = w[..., IS_ROAD].sum(-1, keepdims=True)
    out = np.where(w < PRUNE, 0, w)
    for grp, share in ((IS_ROAD, road), (~IS_ROAD, 1 - road)):
        part = np.where(grp, out, 0)
        tot = part.sum(-1, keepdims=True)
        lost = (tot <= 1e-9) & (share > 1e-6)
        if lost.any():  # every trace of the group went: its heaviest stays
            k = np.argmax(np.where(grp, w, -1), -1)[..., None]
            back = np.zeros_like(out)
            np.put_along_axis(back, k, 1.0, -1)
            part = np.where(lost, back, part)
            tot = part.sum(-1, keepdims=True)
        out = np.where(grp, part * (share / np.maximum(tot, 1e-9)), out)
    return out


def quadrant_sets(w: np.ndarray, ground: np.ndarray, hq: int = 1):
    """w [rows, cols, NM] on a window whose row/col hq lies on a quadrant line (an hq-vertex halo before it), and the
    ground under the road there, broadly blurred (the same window): -> (keep [qr, qc, NM] bool, sums [qr, qc, NM]).
    A quadrant keeps the heaviest ground at each of its four corners (so the quadrants meeting at a corner, and along
    an edge, always share a ground), then the road materials it or its halo carries (the track every road set has
    first, so road quadrants always share a road material, then the heaviest; four corners leave two slots),
    then its heaviest by summed weight over the quadrant + its hq halo, up to MAXL (a wide halo makes neighbours' sets
    agree)."""
    R, C = w.shape[0] - 2 * hq, w.shape[1] - 2 * hq
    nqr, nqc = (R - 1) // 16, (C - 1) // 16
    keep = np.zeros((nqr, nqc, NM), bool)
    sums = np.zeros((nqr, nqc, NM), np.float64)
    # rounded, ties to the lower index: every window that sees a corner or a quadrant picks alike
    corner = np.argmax(np.round(ground[hq:R + hq:16, hq:C + hq:16], 4), -1)
    for i in range(nqr):
        a, b = i * 16, i * 16 + 17 + 2 * hq  # quadrant 17 + halo each side
        for j in range(nqc):
            c, d = j * 16, j * 16 + 17 + 2 * hq
            s = np.round(w[a:b, c:d].astype(np.float64).sum((0, 1)), 4)
            sums[i, j] = s
            roads = [ROAD_COMMON] + [int(k) for k in ROAD_IX[np.argsort(-s[ROAD_IX], kind="stable")] if k != ROAD_COMMON]
            forced = list(dict.fromkeys([int(corner[i + di, j + dj]) for di in (0, 1) for dj in (0, 1)]
                                        + [k for k in roads if s[k] > 0.5]))
            top = forced + [int(k) for k in np.lexsort((np.arange(NM), -s)) if s[k] > 1e-3 and k not in forced]
            keep[i, j, top[:MAXL]] = True
    return keep, sums


def encode_row(p: Painter, g: dict, cy: int):
    """One cell row: shard bytes and per-row stats."""
    H, W = p.arr["habitat"].shape
    north = (g["cy_top"] - cy) * 32
    halo = 40  # two quadrants + the quadrant halo (HQ); the blurs' reach (24 at most) lies inside it for the rows that count
    r0, r1 = north - halo, north + 33 + halo
    rr0, rr1 = max(r0, 0), min(r1, H)
    w, pull, road_w = p.weights(rr0, rr1, 0, W)
    pad = ((rr0 - r0, r1 - rr1), (0, 0))
    w = np.pad(w, pad + ((0, 0),), mode="edge")
    pull = np.pad(pull, pad, mode="edge")[..., None]
    road_w = np.pad(road_w, pad + ((0, 0),), mode="edge")
    # local budget: each vertex paints its TOP_V heaviest materials only (vanilla: 4 distinct LTEX a cell at p50),
    # so after the blur a quadrant rarely needs more than its six layers and the seam fade seldom has work to do
    w = top_v(w)
    w = ndi.gaussian_filter(w, (1.5, 1.5, 0), mode="nearest")
    # the road over the blurred ground, as its rule gives it (soft by itself; a blur would thin a narrow road's spine)
    ground = w
    w = ground * (1 - pull)
    w[..., ROAD_IX] += road_w
    w = prune(w)
    # quadrant lattice: 6 quadrant rows from north-32 (the cell's two are rows 2, 3), 2 quadrant columns of pad
    a0 = halo - 32 - HQ
    lat = ((0, 0), (32 + HQ, 32 + HQ), (0, 0))
    # the corners' ground is read from a broader blur (CORNER_BLUR), so a quadrant's four corners seldom name four
    ground = ndi.gaussian_filter(ground, (CORNER_BLUR, CORNER_BLUR, 0), mode="nearest", truncate=3.0)
    keep, _ = quadrant_sets(np.pad(w[a0:a0 + 97 + 2 * HQ], lat, mode="edge"), np.pad(ground[a0:a0 + 97 + 2 * HQ], lat, mode="edge"), HQ)
    del ground  # [6, nqc, NM]; quadrant row 2, 3 = the cell's; column j = global quadrant j - 2
    # seam fade: each material fades to 0 over FADE vertices toward any quadrant that does not keep it (closed
    # squares, so a shared vertex reads the same from every quadrant), a pure function of position and the sets
    nqr, nqc = keep.shape[:2]
    fade = np.ones((97, nqc * 16 + 1, NM), np.float32)
    for m in range(NM):
        lack = ~keep[:, :, m]
        if not lack.any():
            continue
        core = np.kron(lack, np.ones((16, 16), bool))
        cl = np.zeros((97, nqc * 16 + 1), bool)
        cl[:96, :nqc * 16] = core
        cl[16::16, :nqc * 16] |= core[15::16][:cl[16::16].shape[0]]
        cl[:, 16::16] |= cl[:, 15::16][:, :cl[:, 16::16].shape[1]]
        if cl.all():
            fade[..., m] = 0
            continue
        fade[..., m] = np.clip(ndi.distance_transform_edt(~cl) / FADE, 0, 1)
    out = bytearray()
    st = {"layers": []}
    cell_rows = w[halo:halo + 33]
    # what a fade takes is given back from a broad blur (sigma 6) of the materials still allowed there, so no
    # vertex is renormalised from a small remainder (which would jump): the road's loss to the road materials kept
    # there, the ground's to the ground, so the cut never thins a road
    broad = ndi.gaussian_filter(w[halo - 24:halo + 57], (6, 6, 0), mode="nearest")[24:57]
    for i in range(g["cells_x"]):
        sl = slice(i * 32, i * 32 + 33)
        allowed = fade[32:65, i * 32 + 32:i * 32 + 65]
        cw = cell_rows[:, sl] * allowed
        fill = broad[:, sl] * allowed
        for grp in (IS_ROAD, ~IS_ROAD):
            lost = (cell_rows[:, sl][..., grp].sum(-1) - cw[..., grp].sum(-1))[..., None]
            # by the broad blur of what the group keeps here, a fading material taking almost nothing back until its
            # fade is nearly done (its fade to the fourth power), so what stays rises in a straight ramp as the other
            # falls; where that has no weight, by what the group keeps
            gf, ga = fill[..., grp] * allowed[..., grp] ** 3, allowed[..., grp]
            gs, gas = gf.sum(-1, keepdims=True), ga.sum(-1, keepdims=True)
            share = np.where(gs > 1e-4, gf / np.maximum(gs, 1e-9), np.where(gas > 1e-6, ga / np.maximum(gas, 1e-9), 0))
            cw[..., grp] += lost * share
        s = cw.sum(-1, keepdims=True)
        fs = fill.sum(-1, keepdims=True)
        ok = fs[..., 0] > 1e-4
        cw[ok] += (1 - s[ok]) * fill[ok] / fs[ok]
        s = cw.sum(-1, keepdims=True)
        bad = s[..., 0] < 1e-6
        if bad.any():  # nothing the sharers keep has weight here: what they keep, by its fade (the same from each)
            st["dropout"] = st.get("dropout", 0) + int(bad.sum())
            cw[bad] = allowed[bad]
            s = cw.sum(-1, keepdims=True)
            worse = s[..., 0] < 1e-6
            if worse.any():  # they keep nothing in common (cannot happen with the corner rule): the unrestricted paint
                cw[worse] = cell_rows[:, sl][worse]
                s = cw.sum(-1, keepdims=True)
        cw /= s
        cw = cw[::-1]  # y from the south
        for (qy, qx) in ((0, 0), (0, 1), (1, 0), (1, 1)):  # BottomLeft, BottomRight, TopLeft, TopRight
            qw = cw[qy * 16:qy * 16 + Q, qx * 16:qx * 16 + Q]  # [17, 17, NM]
            tot = qw.reshape(-1, NM).sum(0)
            order = [int(k) for k in np.argsort(-tot) if tot[k] > 1e-4][:MAXL]
            out += quad_bytes(qw.reshape(-1, NM), order)
            st["layers"].append(len(order))
    return bytes(out), st


def quad_opacities(flat: np.ndarray, order: list[int]) -> np.ndarray:
    """Vertex weights [289, NM] and a quadrant's layer order (base first) -> alpha opacities [n - 1, 289]: each alpha
    layer's own weight (the engine adds the layers; the base shows 1 - their sum)."""
    n = len(order)
    ops = np.zeros((max(n - 1, 0), flat.shape[0]))
    for k in range(1, n):
        ops[k - 1] = np.clip(flat[:, order[k]].astype(np.float64), 0, 1)
    return ops


def quantise(ops: np.ndarray) -> np.ndarray:
    """Opacities [k, 289] -> uint8, rounded so no vertex's sum passes 255 (an overshoot is taken from its largest)."""
    a = np.rint(np.asarray(ops) * 255).astype(np.int32)
    if a.size:
        over = np.maximum(a.sum(0) - 255, 0)
        top = np.argmax(a, 0)
        a[top, np.arange(a.shape[1])] -= over
    return np.clip(a, 0, 255).astype(np.uint8)


def quad_bytes(flat, order) -> bytes:
    n = len(order)
    mats = np.full(MAXL, 255, np.uint8)
    mats[:n] = order
    alph = np.zeros((MAXL - 1, Q * Q), np.uint8)
    alph[:n - 1] = quantise(quad_opacities(flat, order))
    return bytes([n]) + mats.tobytes() + alph.tobytes()


def decode_quad(b: bytes, off: int):
    """-> (materials list, composite weights [289, n]) as the engine adds them (base = 1 - the alpha layers' sum)."""
    n = b[off]
    mats = list(b[off + 1:off + 1 + n])
    alph = np.frombuffer(b, np.uint8, (MAXL - 1) * Q * Q, off + 1 + MAXL).reshape(MAXL - 1, Q * Q).astype(np.float32) / 255
    w = np.zeros((Q * Q, n), np.float32)
    for k in range(1, n):
        w[:, k] = alph[k - 1]
    w[:, 0] = np.clip(1 - w[:, 1:].sum(1), 0, 1)
    return mats, w


WORKERS = 3
_W: dict = {}


def _init(legend, g, tex):
    _W.update(p=Painter(legend), g=g, tex=Path(tex))


def _row(cy: int) -> int:
    f_ = _W["tex"] / f"cy{cy:+04d}.bin"
    data, st = encode_row(_W["p"], _W["g"], cy)
    tmp = f_.with_suffix(".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, f_)
    f_.with_suffix(".json").write_text(json.dumps(st))
    return cy


def build(out: Path, rows: list[int] | None = None) -> dict:
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    if legend["build_id"] != man["build_id"]:
        raise RuntimeError(f"landcover is build {legend['build_id']}, land is {man['build_id']}: rerun landcover")
    g = man["grid"]
    tex = out / "tex"
    tex.mkdir(parents=True, exist_ok=True)
    key = f"{man['key']}:{(LC / 'key.txt').read_text()}:{code_key()}"
    kf = tex / "key.txt"
    if (kf.read_text() if kf.exists() else "") != key:
        for f_ in tex.iterdir():
            f_.unlink()
        kf.write_text(key)
    (tex / "materials.json").write_text(json.dumps(material_rows(), indent=1))
    rows = rows or list(range(g["cy_top"], g["cy_bottom"] - 1, -1))
    todo = [cy for cy in rows if not ((tex / f"cy{cy:+04d}.bin").exists() and (tex / f"cy{cy:+04d}.json").exists())]
    # rows are independent (each window carries its neighbours' quadrants), so a pool paints them; the landcover
    # arrays are memory-mapped, shared between workers
    if todo:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(WORKERS, initializer=_init, initargs=(legend, g, str(tex))) as ex:
            for k, cy in enumerate(ex.map(_row, todo)):
                if k % 10 == 0:
                    log(f"  tex row {cy} ({k + 1}/{len(todo)})")
    layers, drop = [], 0
    for cy in rows:
        st = json.loads((tex / f"cy{cy:+04d}.json").read_text())
        layers += st["layers"]
        drop += st.get("dropout", 0)
    hist = np.bincount(layers, minlength=MAXL + 1).tolist()
    mf = {"key": key, "build_id": man["build_id"], "quad_bytes": QBYTES, "max_layers": MAXL,
          "shards": [f"cy{cy:+04d}.bin" for cy in rows], "layers_hist": hist, "seam_dropout_vertices": drop}
    (tex / "manifest.json").write_text(json.dumps(mf, indent=1))
    log(f"tex: layers per quadrant {hist}, seam dropout vertices {drop}")
    return mf


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    ap.add_argument("--rows", help="lo:hi cell rows only (a sample)")
    a = ap.parse_args(argv)
    rows = None
    if a.rows:
        lo, hi = map(int, a.rows.split(":"))
        rows = list(range(hi, lo - 1, -1))
    build(a.out, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
