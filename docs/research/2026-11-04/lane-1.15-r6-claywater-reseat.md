# Lane 1.15-r6-claywater-reseat: fixed heights become heights over the game ground

## Why
`test_explicit_heights_stand_on_the_game_ground` was red at abd3ab72: Claywater's 11 exterior refs with an explicit
`z_m` held absolute world heights set on an older ground. The shores-slope (c3330ce8) and pad-seat (abd3ab72) lifts
raised the ground under them, so the house (b1) stood 3.9 m under the land: buried at the play camera, a blocker.
This is the third time a regrade buried these rows (round 3: ~33 m; claywater-water: +0.34 to +0.80 m by hand).

## Measured (current out/terrain, before the fix)
| ref | z_m | ground | z - ground | cell water |
|---|---|---|---|---|
| b1 (house) | 68.30 | 72.20 | -3.90 | 68.02 |
| b1-door | 69.64 | 72.20 | -2.56 | 68.02 |
| b1-doorframe | 70.75 | 72.20 | -1.45 | 68.02 |
| b1-stairs | 69.12 | 72.15 | -3.03 | 68.02 |
| b4-door | 68.99 | 71.01 | -2.02 | 68.02 |
| b4-doorway | 67.77 | 71.09 | -3.32 | 68.02 |
| b5-door | 68.54 | 68.89 | -0.35 | dry |
| b5-doorway | 67.32 | 68.76 | -1.44 | dry |
| b6-door | 69.00 | 69.00 | 0.00 | dry |
| b6-doorway | 67.78 | 69.00 | -1.22 | dry |
| stable | 69.34 | 71.85 | -2.51 | 68.02 |

No place ref outside Claywater carries an explicit exterior z_m (the rest are studio panels and probes, markers).
None is a water seat: claywater-water's note keeps no jetty or deck on an absolute; its decks have no z and seat by
`water_seat` already. So all 11 became heights over the ground.

## Fix (at the root)
- `build_ref.z_over_m` (schema.sql): an exterior piece's height over the game ground, resolved against the built
  ground in `place_build._pos` at plugin time (also the door arrival). `z_m` stays for interiors and studio markers.
- Values keep KotM's offsets with each door on the ground: doors 0; doorways -1.22 (KotM's door-local offset);
  b1 house -1.34, stairs -0.52, doorframe +1.11 (KotM's offsets from the house's door); stable 0.
- land-dock2 moved 3 m shoreward (x 343 to 340): the deepened bed put its deck 4.21 m over the bed, past the 4 m posts
  (the second red the pad-seat note §Owed names).
- `places check` and `test_ref_heights` treat a z_over_m ref as ground-seated (offset given, not afloat).

## Proof (L1)
- test_place_seating.py 6/6 green, with the new `test_no_exterior_ref_buried_or_afloat`: every exterior ref of every
  place within 0.3 m of the game ground, unless a water seat (dock, boat, person on a deck) or a stacked piece
  checked against its named support (STACKED: doorways, b1 house, stairs, frame on their door).
- test_ref_heights green; `places check claywater`: 113 refs, 0 red; ruff clean.
- `make plugin PLAN=1`: ground and terrain already ran at HEAD (ground.stamp 54ac5294 vs HEAD key 1a09ed3d, from
  pad-seat's patches/place_build change); this lane's place_build edit moves the ground key (patches.py and
  routes/infra.py import place_build), so it adds no stage the next build was not already running. Owed (tooling):
  move `water_level` out of place_build so place edits stop keying the ground.
- tools/tests/test_journeys.py::test_the_derived_journeys_stand_on_the_current_build is red at HEAD too (not this lane).
- journeys' `own_z` reads a z_over_m ref as on the ground (its offset not added): fine for doors (offset 0).

## Owed
L4: the two Claywater ledger rows on the next world-esm build in the planner's batch.
