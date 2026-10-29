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
