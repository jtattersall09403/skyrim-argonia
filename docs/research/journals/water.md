# Journal: the water (chunk 2.W2)

What was tried, measured and learned for `tools/argonia_world/water/` and the water in ArgoniaWorld.esm, so nothing
is lost at a hand-off. The lane reports are `docs/research/2026-10-29/lane-2.W2-water.md`.

## 2026-10-29: the data side (lane 2.W2-water, first context)

- **The model.** Every sample of the 4033^2 heightfield gets one water level, or none (`field.py`): the bodies'
  raster first, the rest of the raster, the sea mask, the stepped reaches' corridors, a 3-sample shore fill and
  dry hollows below 0. Each cell then takes the default water (the sea at 0), one cell water height, or placed
  planes: vanilla's flat `Water\Water1024.nif` (bounds +-512), one activator per water type, scaled to squares.
- **The stepped river.** A reach's profile runs linearly; its steps are at most 0.5 m apart and at least 8 m long
  (a steep reach takes bigger drops). Each step stands at the profile's midpoint. Pieces from the vanilla kit sit
  at the step lines: rapids under 0.75 m, the sloped waterfall body above. The falls use the Dawnguard tall body
  and the mist blast.
- **Snapping and films, measured and turned off.** Snapping levels within 0.2 m saved 5 % of the planes but
  buried 18 bodies. Skipping films under 0.1 m saved 10 % but left 1,400 bodies' edges bare. A leak tolerance of
  0.5 m saved 20 %; 0.05 m was kept.
- **The plane count** (before the budget): 56,310 references. The median cell held 10, the maximum 264, and cell
  (12,-5) overflowed its 256-id FormID slot.

## 2026-10-29: the plane budget (continuation)

- **The causes, measured in the cells over 32** (425 on the refined ground). The step bands cost the most: in 303
  of them, most levels are river steps, and (12,-5) holds 15 levels, 14 of them steps. A narrow diagonal band
  staircases under the quadtree, 69 samples taking 42 blocks. Merging two steps doubles the band but keeps its
  staircase, so merging alone moved only 56 cells under 32.
- **A rounding bug** hid most step merges. Step codes came from `round(level * 100)` in float64 and the field's
  from float32 `np.rint`, so they were off by 1 cm (227 against 228). One `plan.code_of` now does every
  level-to-code conversion.
- **The greedy cover** is lossless and comes first: non-overlapping squares, largest first, at any offset. It
  needs a third fewer plane references than the quadtree in the 828 cells over 16 (41,261 to 27,818) and takes
  4 s. It runs only where the quadtree passes the budget.
- **Turned step planes** fail mostly on 1 to 13 samples of the lower step's water under the square: the field cuts
  steps perpendicular to each centreline segment, and the square is the step's length on a side. Shrinking the
  square by one sample doubles the valid ones on gentle reaches. Not done; it is the next lever (see the report).
- **The ground.** The plan stands on `build.game_heights_m` (the LAND's quantised, limited ground), not the refined
  field. Checked against the refined plan, the float check found 2,342 floating samples: the quantisation steps
  (0.114 m) are larger than the leak tolerance (0.05 m). Planned on the game ground, floating is 0.
- **Merging steep reaches.** A merged step may drop up to max(2.0 m, 2 x the grade's step). With only 2.0 m, the
  steep reaches (2.42 m per step) could not merge at all.
- **Totals.** The table is in the lane report. At budget 32: 344 cells over, 85 merged, 259 fall back,
  11,243 regraded vertices, 153 bodies and 154 reaches with a recorded loss.
- **The fallback** floods the low ground in the cell to one height and dries water above it. In samples, that is
  most of the loss at every budget (fallback-flooded 38,397 at 32). The regrade raises only the border vertices.
- **The sample reach** (reach.949-1591) was merged from 9 steps to 5 at budget 32. Its banks are not flagged.
- **A bug the writer test caught:** `sea ??= Type(mod, r)` in C# skips the call once `sea` is set, so only one
  WATR was written. Fixed, and the test asserts all four.
- **A bug 2.W3 caught:** the regrade's `apply` was pasted into `grid.Sources.classes` too, because the anchor text
  occurs twice, and wrote height floors (92 m) into the land-cover class ids. Fixed; the regrade test asserts
  classes are unchanged.

## 2026-10-29: the designed model (lane water-design; hand-off, not green)

- **The 259 fallback cells by cause:** steep reach 75, marsh 73 (large 50, small 13, interleaved 10), unowned
  raster water 46, junction 44, diagonal reach 9, ponds 7, other 5. Map: `out/water/fallback-causes.png`. Walls
  (water beside lower dry ground) were 7,465 samples, all at the shore fill's limit.
- **Steep rapids hold no water as planned.** The game ground stands 1 to 5 m above the step levels
  (reach.113-2459), so a step-and-pool design must carve beds (`bed` ceilings), not only raise banks.
- **What worked:**
  - basins, at one level each (2,557, of which 1,941 dropped as puddles under `pondMinM2`, films, ribbons and
    fragments);
  - a river kept in its corridor with raised banks, and berms on other shores (walls down to 1,530);
  - 16 m pools;
  - turned tiles (643).
  - Plane refs fell from 32,214 to 25,225, with no fallback.
- **What did not:**
  - 141 cells are still over 32 (max 127). Axis squares staircase where two waters at different levels meet on a
    diagonal.
  - The carve cut a stub's bed below the marsh beside it, which blocks a cell water height under the higher
    planes.
  - Tiles fail at junctions and mouths, and where the bed is beyond the 6 m carve cap.
  - Even unconditionally, a cell height at the lowest level would fix only 66 of 141 cells.
- The work is on the ref `wip/water-design` (b50f2ab); the shared tree stayed at HEAD. The next steps are in
  `docs/research/2026-10-29/lane-water-design.md` §5. The first is to measure whether 32 is the right budget
  (an L4 frame time) before designing further.

## 2026-10-30: the plane budget measured in game (lane game-2, L4)

**The test plugin.** `ArgoniaWaterTest.esp` is dev only and never committed (a scratch build:
`wip/water-design`'s `water plan` re-run in a worktree, 25,225 plane refs, max 127 at (-39,-43); Mutagen
0.54.4). It holds the designed plane refs of three cells, laid in empty Tamriel exteriors, with the plan's 2
WATR and 2 ACTI (fresh, black). Each set has a persistent XMarker as its enable parent, so `prid <marker>` then
`disable` takes the set off.
- **A:** (-39,-43), 127 planes, at Tamriel (-21,-4).
- **B:** (-32,-16), 65 planes (no cell has exactly 64), at (35,15).
- **C:** (-58,11), 32 planes, at (-6,-15).

The `out/water/cells.jsonl` in the shared tree is an older plan, with a maximum of 41 per cell.

**The run.** Defender was quiet (+0.38 CPU-s over 30 s), Community Shaders on, 12:00, clear weather, AI off.
Each set was measured with the bridge's `frametime 600`: planes on, then the set disabled, then enabled again.

| Set | Planes | On: p50 / p99 ms (fps p50, 1% low) | Off | On again |
|---|---|---|---|---|
| A (-39,-43) | 127 | 16.69 / 17.73 (59.9, 56.4) | 16.65 / 19.37 (60.0, 51.6) | 16.66 / 20.51 (60.0, 48.8) |
| B (-32,-16) | 65 | 16.66 / 19.44 (60.0, 51.4) | 16.66 / 19.74 (60.0, 50.7) | 16.63 / 19.98 (60.1, 50.0) |
| C (-58,11) | 32 | 16.72 / 21.60 (59.8, 46.3) | 16.67 / 27.91 (60.0, 35.8) | 16.68 / 21.18 (60.0, 47.2) |

**Reading.**
- Every median sits on the 60 fps vsync cap (16.67 ms), with the planes on and off.
- The 1% lows move by more between two runs of the same state (C: 35.8 to 47.2) than between on and off.
- So **127 planes show no measurable cost against the 0.2 §d bar** (60 fps median, 45 fps 1% low) on the
  g4dn.xlarge. Every on-state passes the bar. The plane count is not what limits the budget at 127.

**Caveats, owed:**
- The vsync cap hides the headroom. An uncapped run, or the GPU time per frame (PresentMon wrote no CSV in this
  slot), would give the true cost per plane.
- The player fell from the teleport point (600 above the planes) to the ground, so the view was at plane level
  rather than looking down from above.
- One run per state.

For scale, Riverwood alone runs at 45.8 fps median and 35.3 fps 1% low with CS on in the same slot. The dense
land, not water planes, misses the bar.
