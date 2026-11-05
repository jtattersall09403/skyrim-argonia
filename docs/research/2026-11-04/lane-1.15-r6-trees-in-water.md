# Lane 1.15-r6-trees-in-water

## Evidence
Round-6 water-types sea stand (out/batch/1.15-round-6/20261105T040257/02-water-types-1-20261105T040657, cell (-53,-28),
sea, level 0 m): read 01-sea-s0, s1, s5. Rows of tall olive conifers stand in open turquoise water, trunks under the
surface, each reflected; s1 and s5 show the bank's real trees beside them.

## Root cause
lists.py MARSH_TREE gave every marsh-class tree role (canopy, emergent, palm, gallery) a water posture of -6..+1.2 m,
and IN_WATER_TREE -6..+2 m for cypress and mangrove names in every marsh class, coast included. The placer honoured it:
trees stood in up to 2 m of sea, brackish lagoon, fresh river and black water. The checks only tested "inside its
posture", so nothing went red. 14.3 % of trees stood in water against Skyrim.esm's 5.8 % in the old audit.

## Census before (shards of 646,460 refs, 350,398 stems: tree roles + shrubs at least 2 m tall)
29,135 stems in water (ground under the cell level, or within 1 m of a wet LAND vertex), plus 5,777 cypress or mangrove in blackwater.
The worst depth is 2.0 m. By region class / water type (stems, in water, excepted, worst m):

| class/water | stems | in water | excepted | worst m |
|---|---|---|---|---|
| coastal-lagoon/blackwater | 167 | 35 | 4 | 1.05 |
| coastal-lagoon/brackish | 896 | 384 | 0 | 1.91 |
| coastal-lagoon/sea | 11505 | 3428 | 0 | 2.0 |
| deep-river-corridor/blackwater | 1006 | 816 | 0 | 1.2 |
| deep-sink-basin/blackwater | 13961 | 5451 | 5453 | 1.2 |
| deep-sink-basin/brackish | 231 | 176 | 0 | 1.97 |
| deep-sink-basin/fresh | 1212 | 394 | 0 | 2.0 |
| deep-sink-basin/sea | 787 | 64 | 0 | 1.93 |
| flooded-forest/blackwater | 25677 | 2436 | 103 | 1.2 |
| flooded-forest/brackish | 1054 | 135 | 0 | 1.78 |
| flooded-forest/fresh | 3226 | 298 | 0 | 1.78 |
| flooded-forest/sea | 16187 | 834 | 0 | 1.95 |
| interior-swamp/blackwater | 47880 | 7242 | 217 | 1.2 |
| interior-swamp/brackish | 591 | 90 | 0 | 1.13 |
| interior-swamp/fresh | 87 | 17 | 0 | 1.17 |
| interior-swamp/sea | 12207 | 836 | 0 | 2.0 |
| northern-transition/blackwater | 1335 | 52 | 0 | 0.35 |
| northern-transition/brackish | 32 | 1 | 0 | 0.27 |
| northern-transition/fresh | 5873 | 122 | 0 | 0.35 |
| northern-transition/sea | 7107 | 93 | 0 | 0.35 |
| rootland/blackwater | 28161 | 5094 | 0 | 1.2 |
| rootland/brackish | 1281 | 248 | 0 | 1.19 |
| rootland/fresh | 543 | 50 | 0 | 1.13 |
| rootland/sea | 6326 | 480 | 0 | 1.2 |
| tidal-delta/blackwater | 45 | 6 | 0 | 0.55 |
| tidal-delta/brackish | 278 | 79 | 0 | 1.82 |
| tidal-delta/sea | 529 | 93 | 0 | 1.89 |
| western-frontier/blackwater | 2418 | 67 | 0 | 0.35 |
| western-frontier/fresh | 5241 | 111 | 0 | 0.35 |
| western-frontier/sea | 258 | 3 | 0 | 0.19 |

## How Bethesda did it (0034)
Skyrim.esm Tamriel TREE refs (shrub, fern, grass, plant and moss names dropped), with the ground under the ref bilinear from the LAND
against the cell's water. Cells at the default or zero level: 236 of 64,170 trees (0.37 %). Lake cells: 276 of 6,560 (4.2 %).
Overall 512 of 70,730 (0.72 %), median depth 0.45 m. The ones in water are mostly TreeThicket01, TreeTundraDriftWoodTree01 and
TreePineForest0xDead: deliberate driftwood and dead trees. Live trees stand on dry land.
The probe is in the scratchpad and was not kept.

## Rule (place.py, at the root)
A stem (tree role, cliff-tree, or a shrub at least SHRUB_STEM_M = 2 m tall by its OBND) is refused when the ground under it is below
its cell's water, or when a LAND vertex within WET_REACH_M = 1 m is under it. The 1 m is the freeboard on the footprint.
The exception (0032): cypress and mangrove, by role, model or edid, in blackwater cells only. Both marsh stops of the journey
(black swamp, green marsh) are blackwater. The lore is world/sources/lore/topics/fauna-hazards.md:92-95 (Flora, CANON_EXPLICIT:
"Cypress, mangrove"). The sea, brackish lagoons and fresh rivers, streams and lakes take no tree.
The band shortfall this caused was fixed by measured ratios in lists.MARSH_TREE_HA_REGION (canopy a ha):
imperial-penal-south.deep-river-corridor had 4.2 trees a cell against a band of 15.5, and hist-heartland.tidal-delta 8.5 against 9.0.

## Gate
`make trees-census` runs `python -m tools.argonia_world.vegetation census`. A red names the cell, the ref, the form and the depth.
The result is cached in out/terrain/vegetation/census.json, keyed by its stamp: the bytes of the shards and LAND it reads,
cell_water, object_form, the road tables, census.py and place.py. It takes 21 s cold and no time when the stamp holds.
census.py is excluded from the vegetation stage's stamp and the band cache's stamp, because it measures and places nothing.
The L1 tests are in vegetation/tests/test_trees_in_water.py (4 tests); the vegetation and pipeline suites pass (68).

## After (whole province regenerated twice under the province lock; the second run carries the band fix)
- Refs: 646,460 before, 619,765 after. Stems: 350,398 before, 323,075 after.
- Stems in water: 29,135 before, 0 after. Cypress and mangrove kept in blackwater: 5,916.
- Trees in water, by the check's share: 0.1425 before, 0.0351 after (vanilla 0.058).
- Vegetation checks: 18 green, 0 red.
veg.stamp was not rewritten: the chain's own stage reruns, because its stamp moved with the code.

## Scope add: roads (planner)
(a) A stem whose OBND body reaches a road lane (the paint.py lane half width) is a census red: 0 province-wide.
The flat-46 trunk: no tree REFR lies within 30 m of the stop's setpos (-191886, 41148) in the deployed ArgoniaWorld.esm
(03:55, parsed directly) or in the new shards. Argonia.esm has none either. The candidate on the s1 heading (322) is
A8FC13 ArgoniaTreeErut03 at (-192952, 42961), 30 m away and 23.4 m off the Blackwood Road centreline.
The trunk is not a vegetation-pass stem on the lane. Owed: a state read of the player's position and the ref under the crosshair at that stop.
(b) Ground flora that is not a stem, rock or water plant, on the lane: 0 refs. place.excluded reads the corridor
(half width + 1.5 m + body reach, plus painted BC_ROAD/TRACK quads). So the ferns in every frame are GRAS grown by the
LTEX under the lane (terrain/grass.py, ltex_grass). That pass belongs to the road-course lane, not this one.

