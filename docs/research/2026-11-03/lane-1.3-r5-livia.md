# Lane 1.3-r5-livia: why the chart-zoom step speak-livia found nobody (round 5)

Cause (L1, read-only then fixed): Livia's placement is fine. Her actor is at ground 68.54 m, 0.52 m over the cell water
(68.02 m), the same Z as the other pad pieces (4800 u; the station pad rose from 3176 u in round 4, all pieces moved with it).
The pen socket (2 m north of her, 3.2 m from her spot) did not displace her. The still shows her ragdolled upside-down at
the player's feet and the two guar facing the player with open jaws: lane 1.15-r5-creatures' kept guar were built with the
creature predator AI (`place_build.CREATURE_AI`: VeryAggressive, Foolhardy, aggro radius 2000/1500) although their npc rows
are `hostility: neutral`, and the template's factions are the wild guar's. They attacked Livia (and the player) at the well.

Second finding, same check: Signs-For-The-Cargo (the poler) and her marker stood on the river bed 2.4 m under the cell water
(ground 65.58 m, water 68.02 m), a person under the water.

Fixes (tools/argonia_world/place_build.py): a neutral creature gets `KEPT_AI` (Unaggressive, Cowardly, no aggro radius, as
Skyrim's cow and goat); `check_creatures` accepts an Unaggressive record. A person's actor or owned marker over the cell water
stands on the deck at water + `DOCK_DECK_M` (0.85 m, the landing's deck), creatures excepted (the crocodile hunts in the shallows).

L1 (tools/argonia_world/tests/test_place_seating.py): `test_no_person_stands_under_the_ground_or_the_cell_water` (failed before on the
poler, passes now), `test_a_kept_animal_is_not_a_predator`. 14 passed with test_creature_dens and test_hostile_armed.

Owed by the planner: `make plugin` regenerates the NPC_ AI of ARG_Npc_DomesticGuar1/2 and the poler's position in the plugin YAML,
then re-run chart-zoom speak-livia. Check that the guar stay calm at the well (a wading guar may still crowd Livia; if so, move the pen bearing).
