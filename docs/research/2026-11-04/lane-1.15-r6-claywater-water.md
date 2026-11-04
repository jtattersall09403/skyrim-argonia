# Lane 1.15-r6-claywater-water (round 6)

## Cause, with numbers (frozen ground: out/terrain/land, the round-5 close build; GameGround agrees with its LAND to 0.001 m at 10 sampled refs)
- **The water did not rise.** Cell -57,11's water is 68.02 m, the same number lane 1.15-r4-claywater recorded; the round-5 solve left it.
- **The station stood a hand's width over its river, and the marker stood off the pad.** The round-4 pads sit at their ground's mean with no rule against the water: the well pad, the yard and the house stood 0.52-0.64 m over 68.02. The quest-board marker (321.5, 3057.0) stands 5.3 m south of the well, outside the well pad (r 2 m + blend 3 m), on the bank's slope: ground 68.10 m (0.08 m over the water), with the lowest LAND vertex of its quad at 67.74 m (0.28 m under it, so shin-deep). 30 of 115 station refs failed the 0.5 m rule. Among them: the signpost p1 (1.01 m under), the ford barrel (1.07 m under), the poler's work marker (2.44 m under, on the river bed under the dock), hut walls and lamps (0.15-0.41 m over), the house origin (z 67.96 m, 0.06 m under).

## How Skyrim does it (0034)
- Skyrim.esm, Riverwood (Tamriel cells 3..7, -13..-9): the ground under the farmhouses and the smithy stands 1.0-3.81 m over their cells' water (FarmhouseSmith01 is the lowest at 1.0 m; n 7). Bethesda lifted the pad, not lowered the river. Caveat: those cells carry the default water level (-3.57 m) as their XCLW.

## Fix (rule and data; no absolute heights)
- `terrain/patches.py`: `PAD_FREEBOARD_M = 1.0`. A pad's level is max(its ground's mean + rise, the highest cell water under its disc + 1.0 m). The disc is sampled at its centre and four rim points (`pad_water`), so a pad that crosses a cell edge clears the wet cell's water. Only Claywater has pads, so no other place is affected.
- Data (db.py): three pads, each with no height of its own: `common` (322, 3074, r 28 m, blend 4 m: the well, the quest board, the house and the byre), `south-huts` (318, 2998, r 12 m, blend 3 m; it ends 3 m short of the canoe's water) and `hut-b6` (329, 2982, r 8 m). Each explicit z_m (house, doors, doorways, stairs, stable) moved by its own ground's lift (+0.34 to +0.80 m), so offsets to the pad are kept. poler-work belongs to the landing's poler, so it takes the 0.85 m deck seat. The ford barrel moved to the bank (318.5, 3051). al-candle1 moved onto the south pad (325, 3005).
- New check `python3 -m tools.argonia_world.places check claywater`: it prints ground, seated z, water and clearance for all 115 refs, the ten markers first. Rules: dry ground must stand at least 0.5 m over the water. Docks and people over water must sit at their seat ±0.02 m. Creatures and anything in a bowl's reach are wet by design. Result after the fix: **115 refs, 0 red**. Before it: 30 red (freeboard off, old data). The quest board is now 0.98 m clear. Every dock piece is 0.85 m clear and the boats sit at 0.00.

## Tests
- L2 test_patches (5 passed, one new: freeboard over the wettest rim cell); L1 test_place_clearance (2, new); test_place_seating, test_ref_heights and creatures green (32 passed); db check green; world-reads clean; claywater-walk and claywater-look `--dry` ok.

## Owed
- **Rebuild before L4:** run terrain LAND, navmesh and the place layer. The LAND in out/terrain/land still holds the old pads, and the check reads the DB's patches live.
- L4 stills for the planner's batch (claywater-walk / claywater-look): the well, the quest board (the save marker, dry footing), the docks (the deck 0.85 m over the water, the poler on it), the station-house door, and also huts b4/b6 (doors flush with the lifted huts).
- The explicit z_m values are still absolute numbers; making them relative to their pad is a follow-up for the place build.
