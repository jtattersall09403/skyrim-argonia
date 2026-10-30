# Lane water-design-2: the designed water on main

The planner's ruling of 2026-10-30: the per-cell plane budget is 128, the measured-safe level. The game lane held
127, 65 and 32 planes on the 60 fps cap with no measurable cost. The budget stays a hard error that names any cell
over it. If the owed uncapped run shows a cost, it tightens with its reason recorded.

## What was done

1. **The parked model applied.** `git diff 32bd3c8 wip/water-design` (the merge base) on the water paths only
   (water/, terrain/water_regrade.py, the schema's water block, the allowlist line, the water db tables), then
   `git apply`. Nothing had touched those paths on main since the merge base. Commit 1aa04cc.
2. **The budget is 128** (`water/budget.py`). Every cell now takes the smaller of its two covers (quadtree or
   greedy; `greedy_over=0`). Before, the greedy cover was tried only above the budget.
3. **The one unrealised body.** body.1746-2172 (a 90 m2 swamp) stood on samples another body held (field step 2
   shares samples at one level). That body's basin was a puddle, so its water was dropped. The sharer was in no
   basin, fell through to "own level", and had no water. Now a body on another body's samples takes that body's
   outcome (`design.shares`; 33 bodies, test `test_a_body_sharing_another_bodys_water_takes_its_outcome`).
4. **The carve below adjoining marsh (correctness).** A carved bed beside lower water left an open side: the lower
   water looks under the higher surface into the pool. Measured on the plan before the fix: 7,413 such samples,
   4,934 of them on carved beds. `oriented.clamp_beds` now raises a bed sample beside another owner's lower water
   (8 neighbours) to that level, in each regrade pass (4,126, then 2,280 raised). The new `checks.sides` counts
   the rest: 3,907 (1,606 under a piece, 2,301 not, 1,195 of those a river's). They are counted, not failed.
   Test: `test_the_carve_never_cuts_below_adjoining_lower_water`.
5. **A gate red found and fixed (343d52f).** The plan's db-staleness check compared `str()` of the rows, and a
   rounded -0.0 basin depth read back as 0.0. So `make plugin` exited at the water step for every lane after
   1aa04cc. The rows now write 0.0.

## The plan (full province, the LAND's ground)

| measure | value |
|---|---|
| cells over the budget 128 | 0 |
| float / same-height overlap / unrealised wet samples / unrealised bodies | 0 / 0 / 0 / 0 |
| step violations | 0 (1,130 steps on 281 reaches, max drop 19.7 m) |
| plane refs, max, p95 per cell | 20,165, 120, 26 (the parked model: 25,225, 127, 31) |
| cell modes | planes 1,914, height 1,518, default 15 |
| turned step tiles | 649 |
| pieces | rapids 203, cascade 382, falls 486, mist 18 |
| body outcomes | basin 783, own level 37, sea 37, dropped by design 1,423 |
| basins | 616 kept, 1,941 dropped |
| regraded vertices | 90,694 |
| walls (not under a piece) | 1,530 |
| open sides (not under a piece) | 2,301 |
| banks flagged | 105 reaches |
| time, peak RSS | 53 to 91 s, 0.93 GB |

**Dropped by design, with the thresholds:**
- puddle: a basin under `pondMinM2` (500 m2), 1,934 basins;
- film: a basin under 0.15 m deep at its deepest, 2;
- ribbon: a basin under 2.5 samples wide on average (2 x area / perimeter), 5;
- fragment: unowned raster water beside a basin at another level, 0.
- A basin a river reach runs into or through is never dropped.

Bodies: 1,410 are dropped with their basin, 12 have ground above their level everywhere, and 1 shares a dropped
body's water.

## Plugin and navmesh

- `make plugin` twice: ArgoniaWorld.esm is 115,210,144 bytes, sha256 0190ed40ebe8.. both times, peak 1.13 GB.
- `tools/argonia_world/terrain/sample-manifest.json` was regenerated deliberately (04c44e0c63ba..; commit 815473a).
  `make plugin-check` is green, and the navmesh sample hash is unchanged.
- `make navmesh` (28 min 21 s, peak 1.53 GB, the navmesh tool's): L1 green on 12,085 cells (0 degenerate; 98.7 %
  coverage under 30 degrees); all 12,085 NAVM in the ESM and identical; ArgoniaWorld.esm with navmesh sha256 3aa3cd1e...
- `make check`: CHECK GREEN.

## Docs

The 2.W2 Outcome is rewritten to the designed model. Its owed L4 list is now the Part 1 world sample's stops 4 to 7
and 12: one stepped reach, one waterfall, one marsh basin, one lake shore, and one NPC swim. The Acceptance, loops
and risks are rewritten the same way. The journal has the entry for 2026-10-30.

## Next

- The uncapped frame time (the game lane) confirms or tightens the 128.
- The 2,301 open sides and the 1,530 walls go to the L4 stills at stops 4 to 7. A third regrade pass, or a clamp
  over a fixed point, would cut the river's 1,195.
- Tell the navmesh lane: `water_regrade` and `cells.jsonl` changed.
