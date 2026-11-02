# Lane 1.15-r4-claywater (round 4)

## Causes
- **Stray plank walkways and stair towers (finding 3)**: King of the Murkmire's cypress stockade kit (walkways, scaffold towers/bridges/stairs, planks, house platforms) took the role `canopy` from the word "cypress" (`tools/argonia_world/vegetation/forms.py` ROLE_WORDS; EXCLUDE lacked them) and was scattered as trees in every marsh region; `lists.py` UPLAND_DENY removed them only in the hills. Before: 218 land_region_object rows of 32 building forms (summed 1,226/ha); after: 0.
- **No house, no stable, no hut doors (findings 22, 23)**: the station house (b1, door, frame, stairs), the stable and the three hut doors/doorways carried absolute `z_m` from the old ground (~35 m); the round-3 ground stands ~68.5 m there, so all 13 stood 31-34 m underground (and the door arrivals with them). The data did not lack them.
- **Docks underwater (finding 31)**: the landing stage, raft, canoe, cleats had no z and stood on the river bed (65.1-67.5 m) under the cell water (68.02 m); `routes/infra.py` landings used max(ground, 0 m), the sea's level.
- **Lilac sign boards (finding 29)**: BM&V's roadsignmedium01l/r.nif name `textures/hana/signs/roadsignmedium.dds` and `roadsign_n.dds`; BM&V's keep globs did not keep them and no row or vanilla BSA lays them.

## Changes (pushed to main)
- 9d9f2a9 forms.EXCLUDE takes the stockade kit; lists.usable re-applies role_of to stored rows; lists rebuilt; tests.
- 79d4b34 Claywater z re-seated on today's ground (house at its pad datum offset, doors on the ground, doorways at KotM's offset, crocodile on the ground); place_build.water_seat/seated_z: docks and cleats 0.85 m over the cell water (Skyrim.esm DockStRSol01/02 origin over XCLW, p50 0.76-0.88 m, n 5), boats at the water; infra landings likewise. L1 test_place_seating: explicit z within -1.5..+3 m of ground (13 failing before, 0 after); every dock, landing and boat on or over its water with its deck <= 4 m over the bed.
- 75f1f18 `textures/hana/signs/*` in BM&V's keep; L1 test (4 slot textures unlaid before, 0 after).
- region_saves.py: tenth save 'Argonia Claywater' at ARG_Ref_ClaywaterStationQuestBoard (by the well), third person via ensure_third_person.

## Not done / owed
- The well's ground pad and texture (finding 25) and the Tropical Skyrim farmhouse re-seat as terrain_patch rows: not done (terrain_patch is a key-only table; no consumer). The house and stable now stand on today's ground with KotM/HTBM pieces.
- `build_ground` scour-pool floor_m 30.3 is the same stale-datum class; test_creature_dens shallows fails on main before and after this lane (water 68.02, floor 65.85).
- The sign textures rely on BM&V's archive holding textures/hana/signs (not verifiable here); the planner's textures check after the next lay proves it.
- L3 render not made (no province build run: memory rule). L4: the checks.md row; journeys claywater-walk/look in the planner's batch after rebuilding lists, the place layer and infra.
