# Lane 1.15-ground: the province ground, generated

Brief: [briefs/1.15-ground.md](briefs/1.15-ground.md). Code: `tools/argonia_world/terrain/generate.py`, `render.py`,
`cellwater.py`, `grid.py` (reads `out/terrain/ground-f32.npy` when present and then drops the old regrade and place
edits), `__main__.py` (`generate [--sample] [--out]`, `render`, the fit checks in `check`), tests
`terrain/tests/test_generate.py` and `test_render.py`.

## Measured (2026-11-01, on the water lane's `cell_water`: 9,978 water cells, 1,657 steps)

`python3 -m tools.argonia_world.terrain generate --sample --out DIR`, then `check --out DIR`:

| check | result |
|---|---|
| whole-province generate | 87.9 s (105 s wall clock including the sample LAND build) on the 4-CPU VM |
| wet vertex at or above its water | 0 |
| bank of a water cell at or below its water | 0 |
| step-edge bank below the upper water, outside the channel | 0 |
| overflow cells (int8 limiter) / limited vertices | 0 / 0 |
| seams (height, normal) over 637 edges | 0, 0 |
| 1,000 random points in the built cells against the generator's field | max 0.057 m (the bound is 0.5) |
| entrance sites shaped | 559 of 567, so **8 unshaped and check exits 1** (see Owed) |

Ground range: −15.1 to 641.4 m. The slope limit is 75°, and 24,419 samples were moved to hold it. The cliff mask
(`cliff-u8.npy`) flags 220,515 samples: designed slopes over 60° plus the samples the limit moved. Max step between
4-neighbours: 69 m, only where a water bank and a water bed meet within one vertex. The water's bounds win there,
and the LAND limiter still reports 0 overflow in the sample. Before `cell_water` landed, the fixture run had 28
overflow cells with 160 m single-vertex drops. The step band fix (the lower cell's slope band is not held wet)
brought the overflow to 3 and then to 0.

## The prior

All-Tamriel's province window (raw −89.5 to 141.8 m), low-passed by three box passes at sigma 13 samples (24 m).
What the low-pass removed:

- the share of exactly-flat neighbour pairs (the 1-unit terraces) fell from 0.115 to 0.001;
- the RMS removed was 1.03 m, with a maximum of 15.2 m at sharp knolls.

## The relief bands (`RELIEF_ECO` × `RELIEF_CULTURE` → `relief_rows()`)

Heights are above the local water base. A research pass over the dossiers found no lore summit or floor numbers.
The one numeric anchor is world-rebuild-options.md:109: "border mountains to perhaps 300 m, uplands 60 to 150 m, a
marsh floor under 10 m".

| eco class | floor..summit (m) | source |
|---|---|---|
| tidal-delta | 0.3..4 | fluvial.md:117 |
| coastal-lagoon | 0.3..8 | fluvial.md:132 |
| deep-sink-basin, flooded-forest | 0.3..10 | fluvial.md:72,75; options:109 |
| interior-swamp | 0.5..15 | mountain-synthesis.md:78 |
| deep-river-corridor | 0.5..30 | fluvial.md:43 |
| rootland | 2..60 | mountain-synthesis.md:80 |
| northern-transition | 5..90 | climatology.md:25; black-marsh-province.md:64 |
| western-frontier | 5..150 | blackwood-and-gloommire.md:13 |

The culture regions scale these bands:

| culture region | summit factor | source |
|---|---|---|
| dunmer-north | ×1.6 | shadowfen.md:84, "Relief exists here and only here" |
| imperial-fringe | ×1.3 | blackwood-and-gloommire.md:13-14 |
| mercantile-coast, saxhleel-coast | ×0.9 | lore-backed |
| naga-kur-deeps | ×0.8 | extrapolated |
| hist-heartland, imperial-penal-south, pirate-freeholds | ×1.0 | extrapolated |

Within 1.5 km of the N/NW border, in the two border cultures, the bands ramp to 40..300 m (the canon border ranges).
Each band's `why` text is in the code. The bands are not yet a DB table (see Owed).

## Method notes

- The land never stands below its local water base plus its floor: `max(base + floor, banded prior)`.
- Inside a water cell, the wet raster (the bodies, the sea and the reach channels) gives the footprint. The bed is
  carved below the lowest level sharing each vertex, following a bed grade per water type down to that type's depth.
  Every other vertex stands at least 0.3 m above the highest level sharing it.
- Shores rise at a grade per type: sea 0.03, brackish 0.04, blackwater 0.08, fresh 0.35.
- Steps use the vanilla join from options §11:
  - the bed crosses the edge 200 units under the upper water;
  - it then slopes down to below the lower water over ceil(drop / 0.8 × slope limit) vertices, at least 1;
  - the band beside the edge in the lower cell is released from being held wet;
  - banks on the edge are closed above the upper water. Closed banks are applied last, and nothing reopens them.
- Entrance sites take the shapes in `SHAPES`; 'bank' replaces 'mound' within 40 m of water. Each site is shaped
  against the plane fitted to its rim:
  - a dry-shaped site in water is reserved as ground;
  - a sinkhole floods where its floor sinks below the cell's water;
  - an underwater entry with no water under it moves to the nearest water within 150 m. Notes on these are in
    `request`.
  - Counts: flat 424, bank 50, mound 40, deep_water 42, depression 11. 260 dungeon records have no position and
    get no site.

## L3 renders and reader verdicts

Six windows (`world.SAMPLE_1_15`) were rendered with the material layer: `render --sample --out DIR/render`.

A reader read the renders, worst first. Four of them are 32 to 128 px wide, too small to judge firmly. Item (1)
asks whether the relief reads right, (2) whether there is no hard edge, (3) whether the water meets its bank.

- **-21_-26_-14_-19, the marsh: FAIL (1)(2), PARTLY (3).** A grey-brown plateau shaped like a plus sign, with
  axis-aligned cell-grid edges and water in the corners. The likely cause: every non-footprint vertex of a water
  cell is held 0.3 m above the cell's highest level, so a marsh cell whose raster footprint is partial becomes a
  bank plateau on the cell grid. **Fix:** in water cells, take the footprint as the raster plus the natural flood
  (the pre-constraint ground below the level), and hold only the true rim as bank.
- **-38_25_-22_40, the river: PARTLY (1), FAIL (2), PARTLY (3).**
  - Steps sit on the channel.
  - There is a hard vertical edge on a grey strip at the left. This is probably the N/NW border ramp, which is
    `min(row, col)` and so has a kink; fix it with a smooth distance.
  - Blocky pale-blue and green plateaus read as water standing on slopes. These are probably the same
    bank-plateau cause as the marsh.
  - An orange disc is an entrance site's flat or mound. The renderer should draw sites as markers, not as relief.
- **0_0_1_1: FAIL (1).** Mostly water mid-province. Check its `cell_water` levels against the ground (likely the
  same cause).
- **-12_63, the border gate: FAIL (1).** No grey high ground shows, but the image is 128 px. Render it at a larger
  window.
- **-63_-63 (sea) and -20_57 (coast): PASS or PARTLY, too small to judge.**

Next iteration: fix the footprint/bank rule and the border ramp, render 4×4-cell-or-larger windows for the four
small ones, and send them to the reader again.

## Starting state (hand-off)

Done (pushed: 00fad6c, c2777d0, 88ae454; this report's commit follows):

- the renderer with its layer registry;
- the cell-water adapter, which reads `cell_water` and `water_step` and falls back to the fixture;
- the generator, and the generate, render and check commands;
- the fit checks, with 0 water faults on the real `cell_water`;
- `grid.Sources.load` reads the generated ground.

`out/terrain/ground-f32.npy` is written. It is the shared out dir, and the other lanes run on it.

Diagnosed:

- `out/terrain/land` is shared with the other lanes (a concurrent build replaced the sample once). Run
  `generate --sample --out <own dir>`; the ground always goes to `out/terrain/`.
- The chamfer distances were the time sink: 180 s, down to about 40 s with in-place slices.

Owed (first: the reader's FAILs above, the footprint/bank plateau and the border-ramp kink):

1. **8 unshaped sites.** These are mostly flat sites on steep or banked ground, where the slope limit re-slopes the
   terrace rim, plus one mound and one depression. They include stormhold, helstrom, porter-relay-poling,
   the-thorn-bond, the-north-holding-pit and treasure-hunters-live-camp. Fix in `shape_sites`: pin the shaped core as
   lo=hi bounds so the limiter cannot move it.
2. **The `region_relief` and `entrance_site` rows are not in the DB yet.** `relief_rows()` and `entrance-sites.json`
   hold them. Schema plus a db.py write: `entrance_site` exists from the water lane; `region_relief` needs a
   CREATE TABLE.
3. **ArgoniaGen `pipeline.py`'s terrain stage** has not been touched.
4. **`regional cliff_share` is recorded but unused.** Cliff placement goes to the cliff-mesh pass.
5. **A reader iteration on any fix.** `make check` is not yet run whole; the planner's round gate runs it. Done so
   far: pytest on terrain (31 passed) and ruff clean.
