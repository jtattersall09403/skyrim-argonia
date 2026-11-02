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

## Round two (the planner's three items)
- 2aba074 terrain_patch made real: `terrain/patches.py` (pad flat at its ground's mean + rise_m, smoothstep blend; bowl depth_m under its cell's water; no absolute heights), applied in grid.Sources.heights (LAND, game_heights_m, GameGround, navmesh) and painted by material._weights; row reuse keys and the pipeline stamp carry it. Rows: the well (r 2 m, blend 3 m, LDirtPath01; Skyrim.esm's exterior wells stand on p50 0.23 m relief within 2 m, on a dirt/mud vertex), the station house (r 6 m) and the stable (r 5.5 m, LDirtPath01). Old bed-cut rows stay keys (kind NULL). L2 test_patches.py on synthetic rows (4 tests).
- bbdc518 the scour pool: a bowl 2.6 m under its cell's water (68.02 m) replaces build_ground's absolute floor 30.3 m, which the generated ground never read. test_creature_dens green (the shallows 2.56 m deep; it was red on main).
- fb4accb the L3 renderer applies the patches. Render of cells -58,11..-57,12 (an 8x8-cell window), read by a reader: the river and its banks read naturally. The reader saw rectilinear, plate-edged dark water at the window's west edge, a straight north bank on the main water, and a hard-edged orange block near (650, 220) px. The pads (2-6 m) are below the render's pixel scale. The water's edge shapes are the ground lane's cell-water output, not this lane's; the orange block should be checked in the claywater-look stills.
- Still red on main, not mine: tools/ArgoniaGen/test_pipeline.py::test_world_hands_the_frozen_ground_to_every_stage (its _terrain_stamp lambda takes no `ground` keyword; from 929d2e1).

## Not done / owed
- The Tropical Skyrim farmhouse kit: not re-seated. The house and stable keep the KotM and HTBM pieces, now on their pads.
- The sign textures rely on BM&V's archive holding textures/hana/signs (not verifiable here); the planner's textures check after the next lay proves it.
- L4: the checks.md row; journeys claywater-walk/look in the planner's batch after rebuilding lists, the place layer and infra.
