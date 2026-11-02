# Lane 1.15-r4-water: rivers on slopes, hovering pieces, still water (owner play test 3, findings 19 and 20)

## What was wrong (measured on the round-3 build: its DB, out/water and out/terrain/ground-f32.npy)
- **Pieces off their step**: `water/__main__.py` emit (round 3) put every non-foot piece at the UPPER water on the
  edge and every piece yawed DOWN the step (`yaw[s.edge]`, `z = s.lower_m if k in AT_FOOT else s.upper_m`). Skyrim.esm
  (new probe `terrain/probes/vanilla_step_pieces.py`, 440 FX refs at 51 dressed steps) lays the rapids line at the
  upper water facing down (63 of 111 at 0 deg), but the skirt (49) and ring (49) at the LOWER water, the skirt facing
  UP the step (32 of 49 at 180 deg); the tall and sloped waterfall bodies stand at no level step. Round 3 hung the tall
  body and the skirt at the upper water facing down (the "hovering, flowing the wrong way" pieces), and the foot
  pieces on the edge where the graded bed is still a median 213 u (up to 1,296 u) above the lower water: buried.
- **Hovering surface**: 174 of 228 chained steps ("falls") had no rapids line, so the upper sheet's end over the
  channel (200 u over the bed, generate.py STEP_BED_M) was bare. Bank edges were clean: 0 of 2,619 dry-neighbour
  edges and 0 of 2,305 level edges had ground more than 30 u under a level outside a channel.
- **Over-tall steps**: steps take the cells' final levels (a body's level at a reach's end cells), so the reach's own
  MAX_DROP_M test (solve.py solve_reach) missed them: drops up to 119.8 m (p90 16.8 m) on a 20.96 m piece.
- **Still water flowing**: layer.py copied Skyrim.esm DefaultWater into all four types, rivers included, so nothing
  told still from flowing. Vanilla: lakes take the world default DefaultWater (10,742 Tamriel cells), rivers
  RiverWaterFlow*/DefaultRiverWater (298 cells); they differ in the noise winds (0.019/0.013/0.096 vs 0.044/0.033/0.145).

## What changed (commits on origin/main, ending 13279dd)
- steps.py: one vanilla chain per step (line on the edge at the upper water facing down; skirt, ring, mist at the
  foot, where generate.py's graded bed meets the lower water, `foot_vertices` = its k; skirt facing up), `place()`
  shared by emit and check; the tall/sloped bodies leave the chains.
- solve.py: the owner's rule: a reach whose cells step taller than MAX_DROP_M (20.96 m) at any edge becomes a dry
  gully and the cells are assembled again. **12 reaches turned dry** (16 -> 28; 27 cells fewer, 10,634 -> 10,607;
  chained steps 228 -> 203, max drop 119.8 -> 19.6 m). **Graph edits: 0** (the hydrology graph is unchanged).
- emit: a step whose ground keeps no channel (8 of 203 on the r4 ground) lays no chain and reads as a closed bank;
  listed in out/water/plan.json `noChannel`. Each piece goes in the cell it stands in.
- layer.py: 7 WATR types: 4 still (DefaultWater body), 3 flowing (`<class>-flow`, DefaultRiverWater body) for a
  river's own cells (reach, no body); keys WATER_BASE+0..6.
- judge.py + `water check`: the three rules (pieces on a step, base not over the graded bed, facing; no hovering sheet
  at banks or over a bare channel; still/flow templates). Tests: water/tests/test_judge.py (8, synthetic cells).

## Measured
- `water check` on round 3 (its stream and ground): pieces 1,532 reds, hovering 174, still/flow 415.
- On this lane (`terrain generate --out out/terrain-r4`, 616 s, under the province lock; emit; check): **0 reds**,
  728 pieces on 203 steps, 39 s.
- L3: `terrain render` of the two steepest kept windows (-52,45..-48,49 and -49,14..-45,18). The reader could not
  judge step pieces or surface height: the renders are flat land-cover maps. **L3 is not proven**; the L4 journey
  judges it.

## Owed
- In game (the planner's batch): `tests/journeys/river-steps.yaml` (3 steepest kept steps, 3 new dry gullies, 2
  still bodies; `--dry` ok); checks.md row "River steps and still water" (owed).
- The ground lane: 8 steps where the final ground keeps no channel (generate.py's step stamp is lost to a later
  pass), e.g. (-22,26) s, a 13.3 m wall along the whole edge. Listed in plan.json `noChannel`.
- Not proven offline: whether DefaultWater itself reads as still at the play camera under Community Shaders. Round 3
  already used it for lakes. If the still bodies still drift, the next suspect is CS water flow, not the WATR.
- The whole province needs `make plugin` (cell_water changed), and the world sample's two world_sample tests are red
  on main before this lane too (stale scene files, `test_numbers_decide_where_the_brief_says`).
