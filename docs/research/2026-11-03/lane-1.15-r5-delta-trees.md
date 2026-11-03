# Lane 1.15-r5-delta-trees: the tidal delta's marsh trees back inside the band

## Cause
The r5 crimson lane dropped ArgoniaTreeErut03/05/07 (canopy) from every tidal-delta region; SwampPlant02 was never a delta tree. The delta's list held (canopy) 01Juniper, Erut03/05/07, Jungle03/07/09/10, Kapok02, Swamp04 and (palm) Palm03/04, PalmDate03, Palmoke01/03/07/09, Seju06; it now holds Jungle03/07/09/10, Kapok02, SejuSaplings02, Swamp02, Swamp04 and the same palms. Density per hectare is unchanged (the class number 68 a ha is the mix rule); the trees that replaced Erut (a 257-unit sapling, dry-posture jungle forms) stand on fewer delta cells, so hist-heartland.tidal-delta went 8.8 (old lists, inside the 0.5 tolerance) to 7.9.

## Fix (lists.py, FAMILY row "cypress")
The delta has no mangrove form of ours (mangrove role: 0 forms), so the cypress family (buttressed trunks that lists.IN_WATER_TREE lets stand to 2 m under the water, where the delta's cells are) now ranks first for tidal-delta too, as the stand-in for the mangrove thicket that screens a river mouth: lore regions/waters.md:31 (Red Bramman's river mouth "screened by dense thickets of mangroves"), regions/murkmire.md:23 (the mangrove wall), topics/fauna-hazards.md:94 (cypress, mangrove). Same rule as the flooded-forest and sink classes; the 68 a ha mix is untouched. Lists rebuilt (`vegetation forms --lists-only`): land_region_object rows reordered by the draft (tidal-delta now takes SwampCypress and Swamp forms).

## Province check (build + check against out/terrain/land, 649k refs), trees per cell
| region | before | after |
|---|---|---|
| dunmer-north.tidal-delta (7 cells) | 7.4 | 10.0 |
| hist-heartland.tidal-delta (11) | 7.9 | 10.4 |
| imperial-penal-south.tidal-delta (4) | 13.2 | 12.8 |
| mercantile-coast.tidal-delta (7) | 19.7 | 22.4 |
| pirate-freeholds.tidal-delta (4) | 19.5 | 15.5 |
| saxhleel-coast.tidal-delta (17) | 13.3 | 15.0 |
All inside 9.0-27.0. The draft is joint, so other classes' means moved by up to 1-3 trees a cell, all still in band (e.g. hist-heartland.coastal-lagoon 22.1 to 22.4, naga-kur-deeps.deep-river-corridor 24.6 to 21.8, pirate-freeholds.deep-sink-basin 24.9 to 22.8).

## Not mine
dunmer-north.deep-sink-basin (88 cells) reads 28.6 before and 29.4 after against 27.0 (+0.5 tolerance); it was 29.3 on the pre-r5 lists too, so it is not from the crimson lane. The brief named only the delta red; this check shows it as a second red. A region-level MARSH_TREE_HA_REGION number for it (153, now) would close it; left to the planner.

## Owed
L4: round-5 world panel tidal-delta stills (cypress-shaped trunks in the water instead of Erut). 45 vegetation tests pass.

## Second red closed
dunmer-north.deep-sink-basin: MARSH_TREE_HA_REGION 153 -> 127 (153 x 24.5 / 29.4; 24.5 = median of the other seven deep-sink-basin regions' measured means). It now reads 25.1 a cell; province check 18 green, 0 red (648,640 refs).
