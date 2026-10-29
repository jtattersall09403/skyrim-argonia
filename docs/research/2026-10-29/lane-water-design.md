# Lane water-design: the designed water model (hand-off, not green)

The owner's ruling of 2026-10-29: no thoughtless fallback; the water is designed. This lane diagnosed the 259
fallback cells and built most of a designed model. **The per-cell budget of 32 does not yet hold by design:** 141
cells are over it. The work is kept on the side ref `wip/water-design` (commit b50f2ab, on top of 32bd3c8). The
shared tree is back at HEAD for every path this lane touched, so the gate reds the planner reported are gone:
`db check` is green, the water tests pass (8, venv), and HEAD's plan rebuilds `out/water/cells.jsonl` byte-identical
to before (37 s, peak 1.35 GB). Nothing was committed except this report and the journal entry.

## 1. The 259 fallback cells by cause (budget 32, the unreduced plan)

A cell's cause is the kind of water that needs the most plane references in it. Map:
`out/water/fallback-causes.png`; rows: `out/water/fallback-causes.json`. Wet area is the cell's wet samples x
3.34 m2.

| cause | cells | plane refs (unreduced) | wet area m2 |
|---|---|---|---|
| steep reach (one reach, grade > 0.03) | 75 | 5,905 | 77,180 |
| marsh, large bodies (≥ 2,000 m2) | 50 | 2,419 | 135,808 |
| raster water no body owns | 46 | 2,446 | 102,041 |
| junction (two or more reaches) | 44 | 2,813 | 42,224 |
| marsh, small bodies | 13 | 603 | 21,453 |
| marsh, interleaved (4 or more marsh levels) | 10 | 696 | 27,085 |
| diagonal gentle reach | 9 | 566 | 13,344 |
| small ponds | 5 | 268 | 15,111 |
| shore fill no body owns | 3 | 141 | 8,356 |
| ponds | 2 | 64 | 3,635 |
| lake or lagoon | 2 | 117 | 3,348 |

Rivers cause 128 cells and still water 131. Other measurements on the unreduced field:
- **Walls.** 7,465 water samples stand beside dry ground lower than they are (the edge hangs in the air). All of
  them are at the shore fill's 3-sample limit, and 4,665 are on river corridors (median 1.05 m, p90 11 m).
- **Marsh.** 2,115 marsh bodies form 1,841 touching groups. 1,414 groups are under 500 m2 (the graph's
  `pondMinM2`, 238,211 m2 in all). 152 groups have more than one member; they hold 70 % of the area, and their
  level spread is p50 0.08 m and p90 0.41 m. The raster's water that no body owns is 358,017 samples at 61 levels.
- **Steep rapids hold no water.** Sloped-rapid grade is p50 0.18 and chutes are p50 0.58. On reach.113-2459 the
  game ground stands 1 to 5 m above every step level, so the planned flat steps are dry slopes.

## 2. The designed model as built (on `wip/water-design`)

- **`water/design.py`, still water.** Patches are 4-connected samples of one owner at one level, labelled with a
  run-length union-find (no scipy). Touching patches join into basins, closest levels first, while the spread stays
  within 1.5 m. A basin stands at one level: the median, the lower quartile or the lowest of its levels, the first
  whose shore does not spill (4 samples of spread, then a 1 m berm), or else its spill level found by bisection.
  Closed dry dips below the level fill (the water table).
- **Dropped by design** (`water_body_design`, `water_basin`): puddles under 500 m2 (`pondMinM2`), films under
  0.15 m deep, ribbons under 2.5 samples wide on average, and fragments (raster water no body owns that touches
  another basin). A basin that a reach runs into or through is never dropped.
- **`water/steps.py`, rivers.** STEP_MIN_M goes from 8 to 16 m: gentle reaches step 0.5 m at a rapids line, and
  steep reaches become step-and-pool, dropping grade x 16 m at a cascade, or at a falls piece from 3 m. Step merges
  are deleted.
- **`water/oriented.py`, turned tiles.** Each step is laid as square tiles at least the width plus two samples
  each side, turned to the flow. The overhang and underlap of 2.5 samples under the step's piece are counted apart
  in the float check.
- **The step-and-pool regrade** (`terrain/water_regrade.py` now carries ceilings too):
  - `bed`: the channel is carved to the level less max(1.5 m, the graph's depth), at most 6 m.
  - `bank`: dry ground beside a river and under its tiles is raised to level + 0.15 m, at most 6 m. A river no
    longer shore-fills.
  - `sill`: the lip below a cascade is raised.
  - `berm`: the shore of other water is raised, at most 1 m.
  - There are two regrade passes. The table becomes (x, y, kind, z_m, entity_id).
- **`water/plan.py`.** Snap and shallow are gone. There is a new walls check. `base_level`: a cell's lowest water
  may be its cell water height under the higher planes, when no dry ground lies below it and every higher water's
  bed hides it.
- **`water/budget.py`** is a hard error that names each cell over the budget. The fallback, merges and loss
  tables are gone (`water_budget_cell` and `water_loss` are dropped).

## 3. Before and after (full province, the LAND's ground)

| measure | before (HEAD, budget 32) | designed (wip) |
|---|---|---|
| fallback cells | 259 (+85 merged) | 0, and there is no fallback code |
| cells over 32 planes | 0, by fallback | **141 (hard error)** |
| plane refs / max / p95 per cell | 32,214 / 32 / 27 | 25,225 / 127 / 31 |
| cell modes default / height / planes | 52 / 1,150 / 3,001 | 15 / 1,515 / 1,917 |
| turned step planes | 221 | 643 tiles |
| bodies: realised, dropped, lost | 2,271 + 9 recorded losses | 858 realised (757 basin, 64 own level, 37 sea), 1,422 dropped by design, 1 not realised (body.1746-2172) |
| dropped bodies' reasons | | 1,403 puddle, 12 ground above level, 5 ribbon, 2 film |
| basins kept / dropped | | 616 / 1,941 (269,422 m2 dropped, 3.37 km2 kept; level: 546 median, 69 spill, 1 lowest) |
| walls (samples, not under a piece) | 7,465 (unreduced) | 1,530 (reach 1,028, shore 412, body 90) |
| float / same-height overlap / unrealised wet | 0 / 0 / 0 | 0 / 0 / 0 (overhang 1,819 under pieces) |
| step violations; steps on 281 reaches | 0; 1,570 | 0; 1,130 (max drop 19.7 m on a chute) |
| pieces | rapids 264, cascade 1,231, falls 18 | rapids 203, cascade 382, falls 486, mist 18 |
| banks flagged | 110 reaches | 105 reaches |
| regraded vertices | 11,243 (fallback borders) | 90,693 (bed 65,449, bank 10,934, berm 10,701, sill 3,609) |
| time / peak RSS | 45.6 s / 1.34 GB | 38 to 65 s / 0.94 to 1.04 GB |

## 4. Why 141 cells are still over

The over cells split evenly: rivers need 3,547 plane refs in them, bodies' water 2,824 and unowned water 548.
- **Rivers: the tiles fail.** In the last measured pass, 667 of 1,547 tiles were valid. The rest failed because:
  - 219 have no water at their level (the bed is still above it beyond the 6 m carve cap, or the step lies in a
    lake);
  - 210 have dry low ground left after the two regrade passes;
  - 191 have another, lower water inside the tile (junctions, river mouths);
  - 57 stand over another higher water.
- **Still water: axis squares staircase along diagonal boundaries between waters at different levels.** Example
  (-31,-22): a marsh at 0.34 m needs 55 squares around a 29 m channel stub at 0.84 m (reach.1015-2725). The carve
  put that stub's bed at -1.16 m, below the marsh, so the marsh plane cannot pass under it. The stub needs 31
  more squares against the marsh.
- **The cell-height lever's ceiling.** If every over cell's lowest level stood as its cell height regardless of
  the conditions, 66 of 141 would pass; with the two lowest levels, 111. With the conditions (no stacked
  surfaces) it fixed none, because of hollow samples at 0 and carved beds under the higher water.

## 5. Next, in order (for the planner)

1. **Ask whether 32 is the right number before designing further.** The budget was a ruling, not a measurement.
   The previous lane asked for the L4 frame time of a 60-plane cell. With no fallback, the over cells reach 127.
   A frame-time still of (-39,-43) at about 127 planes would show whether "over 32" is a real cost or not. If
   64 is affordable, measure the designed model at 64 first: one `water plan` run, after changing BUDGET.
2. **The carve must not cut below adjoining still water.** Clamp a bed to the lowest basin level within its
   step's tile. This unblocks `base_level` in the marsh-and-river cells (the 66 to 111 ceiling above).
3. **Absorb hollow samples at 0 into a cell's base.** They lie below its level and would be flooded by it.
4. **Make tiles survive at junctions and mouths:** smaller tiles where a tile meets other water, and the carve cap
   reviewed for the 219 dry tiles. Then iterate the regrade to a fixed point instead of two passes.
5. Only then: the 2.W2 Outcome rewrite, the L4 sample (one stepped reach, one marsh basin, one lake shore, one
   waterfall, one NPC swim: five stills sets and one swim journey), `make plugin` twice, and the sample manifest
   regenerated. None of these was done, because the plan is not green.

## Resume

To compare: `git diff HEAD wip/water-design`. To take the work, apply it into the tree as a patch:
`git diff HEAD wip/water-design | git apply`. On applying:
- `world/db/water_regrade.jsonl` grows to about 90k rows; its allowlist line is in the patch.
- `water_budget_cell.jsonl` and `water_loss.jsonl` are deleted, together with their schema block.
- Run `~/.argonia/venv/bin/python -m tools.argonia_world.water plan --write-db`, then commit the db rows by
  pathspec with the code.

Tell the navmesh lane (a5668740af183a423) when `cells.jsonl` or `water_regrade` changes; the regrade table's
columns change (x, y, kind, z_m), and `Regrade.load` keeps its signature. The probes are in this lane's scratchpad
(state, worst-cell, tile-failure and ceiling scripts); `plan_province()` in the wip `__main__` gives the plan's
full state for them.
