# Lane world-fixes (build VM): croc den depth, travel crash (proving ground dropped)

From diag-croc-move-crash.md. Scope changed mid-lane by owner rulings: the proving-ground fix and its combat-trial-a
edit were dropped and reverted (checks-simplify owns combat-trial-a), and w3-road-hops was dropped.

## 1. The crocodile's shallows den: now in water 2.57 m deep
- `world/db/build_ref.jsonl` (through db.py): `ref.claywater-station.crocodile-den-shallows` moves from (281.5, 3058.0)
  to the scour pool's centre (281.5, 3052.0), with no z_m, so place_build stands it on the generated game ground.
- Measured on GameGround: the old spot was the bank at 33.24 m, above the 32.84 m surface. That matches the game-12 z
  of 2328 = 33.26 m. The new spot has its floor at 30.27 m, so the water is 2.57 m deep. Plugin: the croc and its den
  are at z 2120 (was 2328), y 48418.51.
- The ford (the raft) is 81 m away, and the territory is 2.5 m (it must be 20 m or less).
- L1: `test_shallows_den_sits_in_water_at_least_2_5_m_deep` (tools/argonia_world/tests/test_creature_dens.py) reads the
  depth on the generated ground. It also checks that the ford is outside the territory and that the actor starts at
  the den.

## 2. Proving ground: dropped (owner ruling). One real bug was found and left unfixed, for whoever owns it
- `fixtures.py` TILE_M is 7.0, but the floor piece impfloormid01 measures 3.641 m (out/pieces-index.json sizeM). That
  leaves a 3.36 m gap between pieces. The duel markers (x = 0) and Start stand in a gap, which explains game-12's grey
  void and the T-posed opponent. The fix was written and tested, then reverted per the ruling.

## 3. Travel crash: routed through the holding cell
- The teleport route was not possible: `TESObjectREFR::MoveTo_Impl` is private in CommonLibSSE-NG (MSVC C2248, from
  hudfix3's build), and ep_world.cpp is back to HEAD.
- `tools/world_sample.py`: `HOLD = coc ARG_HoldingCell, wait 5` now comes before each stop's `bat` arrival, the s07
  coast cow and the s09 segment cow. world-sample.yaml and the scenes are regenerated with `--write`.
- L1: `test_every_cow_in_a_journey_step_comes_from_the_holding_cell`, plus the updated arrival test.
- w3-road-hops is dropped: the generator, its tests, the yaml, the game-13 batch entry and the 2.W3 brief line.

## game-13: deploy and re-prove
- `make deploy` (plugin: ARG_Province RecordData, the croc and den z 2120).
- croc-den: read `ARG_Ref_ClaywaterStationCrocodile.GetPos z` (about 2120) and `IsSwimming` = 1.
- world-sample: s01 to s02 three times, plus s07 and s09, with no crash. Each cow comes from ARG_HoldingCell.
