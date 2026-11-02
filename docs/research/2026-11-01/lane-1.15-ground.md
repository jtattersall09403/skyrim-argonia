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

## Session 2 (2026-11-01)

Pushed 96e7247 (the footprint fix, its own commit): the ground beside water ramps from under the water at the type's shore grade (faded by SHORE_FAR); inside a water cell, ground under level + 0.3 m is the natural flood and counts as wet (1.65 M samples). The shore re-chamfers after the flood. The N/NW border distance is a soft minimum (no `min(row, col)` kink). The apron edge offset is blurred along the edge (sigma 64 samples, eased in by 60 m), and the streaks went from west |dx|/|dy| 0.23/0.64 and north 0.73/0.22 to 0.27/0.36 and 0.36/0.27. Site cores are pinned (lo = hi). Renders are at least 1,000 px, with small windows widened to 8×8 cells and shifted inside the province. Probes are in `terrain/probes/` (roles per window, big steps, apron streaks, unshaped sites). Sample check on 96e7247 plus the overlap release: fit 0/0/0, overflow 0, seams 0, 5 sites unshaped, generate 133 s (VM shared).

Reader on 96e7247: marsh FAIL, border gate FAIL(2,3), 0_0_1_1 PARTLY, river PARTLY (the left strip is now soft), coast PARTLY, sea PASS. **Cause of the remaining plus and square pools:** the plus is the *dry cells* of `cell_water`. A dry cell has no water plane, so the neighbour's water stops on the straight cell edge. The planner's materials finding agrees: dry ground at a cell edge lies below the neighbouring level.

Uncommitted in ~/wt-1.15-ground (generate.py), measured but not green:

- `edge_bank`: water-cell samples within the type's shore run of a vertex touching a dry cell are bank, not wet, so the shore slopes inside the water cell (706,717 samples).
- Site falloff warped by two angular harmonics (no discs).

Result: fit 0/0/0, but **3 overflow cells** (the edge bank against step beds) and **9 sites unshaped**. The check still measures an unwarped disc and a flat core std < 1 over 228 m city radii (stormhold, helstrom, gideon), and that test is wrong for big sites.

## Session 3 (2026-11-01): measured in Skyrim.esm, then the same (decision 0034)

`terrain/probes/vanilla_lake_cells.py` reads Skyrim.esm's Tamriel CELL XCLW + LAND VHGT. Inland levels carried by
4+ connected cells (top 15 bodies, 323 cells): every cell the body touches carries the level, including 10 cells
with no ground under it and 59 under 10 % wet. Lake Ilinalta (level 600 u, 51 cells, x −12..0, y −16..−12): median
wet share 0.48, 4 all-dry cells, 6 under 10 % wet, **0 enclosed holes**. Over all 15 bodies: 6 enclosed non-body
cells, 1 with ground under the level. The planner's audit (skyrim-does-it-this-way.md §2) agrees: 23 of 510
explicit-level cells have no wet vertex (a padding ring).

Done (pushed 32bb7cb):
- `water/solve.py`: `fill_enclosed` (938 enclosed dry cells take their ring's level) and `pad_ring` (every cell beside
  water takes the lowest neighbouring level, so no water stops on a cell edge; lowest, so a tall bank never stands
  beside a lower bed). Now 13,359 cells, 4,081 steps (3,794 closed); `water check` green; tests 15 passed.
- Shore and bed profiles from the audit §1: Morthal for brackish and blackwater, Solitude for the sea, Ilinalta for
  fresh (`SHORE_RISE_U`, `BED_DEPTH_U`); the forced lowest-third pool in empty water cells removed (the square
  pools).
- `edge_bank`: never within 6 samples of a step's channel and slope band; every vertex shared with a dry cell is
  bank; a closed step's lower side keeps a bank band over the shore run of its drop. `cellwater.from_solve` reads a
  closed step's range as −1 (it was 0..0, which made vertex 0 a channel).
- Sites: `site_dist` (warped falloff) is shared by shaping and check; windows at 1.7 r; a flat's check core is
  capped at 40 m and leaves out other sites' discs and wet samples; flats run largest first, a flat inside an
  earlier one keeps its ground; **a flat keeps its wet samples as water** (Claywater; test_creature_dens green); a
  mouth is cut into a one-sided rise (§10: 553 u over 1,024 u behind the door, shape `rise`, checked at 75 %); a pin
  no 0.8 × 75° slope can join to the water beside it is left to the limit.
- New check `dry_edge_below_water`; `CLIFF_DEG` 55 (climb-anything.md).
- `region_relief` table (47 rows, `terrain relief`; generate reads it), `entrance_site` (567 rows, written by
  generate), pipeline.py `ground()` runs `terrain generate` when its stamp is stale, and the terrain stamp includes it.
- `world_sample.py` reads `sampleStep`; test_world_sample: 9 passed, 1 red not ours (`tests/scenes/world-panel.txt`
  has `cow ARG_Province 26 -17`, the sample lane's panel.py).

Sample check on 32bb7cb: fit wet 0, bank 0, step-bank 0, **dry_edge 6** (cell 21,20, role 1), **9 sites unshaped**
(flats beside gorges: swampmoth-town, stillrise-village, the-tide-fair, ...: the unpinned core is sloped by the
limit), **overflow 2 cells** (−20,59 and −42,13: a padded/enclosed cell's 250 m ground beside a 40/72 m lake;
bank role 3 at 254 m one vertex from the bed). Height fit 0.057 m, seams 0. Generate 174 s.

## Session 4 (2026-11-01): padding cells measured, then the same (0034)

`terrain/probes/vanilla_lake_padding.py` (Skyrim.esm, 15 largest inland levels, 323 cells, 16 s): the ground under
the level is 74 components, but the largest holds 97 % of it (110,657 of 113,608 vertices). In padding cells (< 10 % wet,
69 cells) 2,497 wet vertices join the main body and 227 do not. Their dry ground stands 0-8 units over the level.
**The outline lies on cell lines for 5.9 % of its length** (2/32 = 6.25 % for a raster shape), so outlines are the
body's shape, not cell squares.

Done (pushed 52f2af7, dc744c6, 7738c4e, 5b2605a):
- The natural flood is only the low ground 4-connected to the body's raster water (`generate.reach`, numpy run
  labelling), and only inside cells that hold raster water. Padded and filled cells keep their ground as bank at
  level + 0.3 (175 k low samples left dry). The 0_0_1_1 padded cells went from 0.9-1.0 wet to 0.0.
- `limit`: where two waters' cones clash at the design slope (a 374 m tarn 117 m from a 40 m lake), the cones are
  taken at `CLIFF_HARD_DEG` 80°. The 214 m wall at (−20,59) is gone, and overflow fell from 2 cells to 1 (−25,48:
  a 327/67 m pair).
- A dry cell's vertex stays bank under a sinkhole (the 6 dry-edge vertices of (21,20) were the
  sinkhole-mouth-basin's disc). dry_edge is now 0.
- Flats: each is fitted to the band its window's bounds allow (lo cone ≤ m ≤ hi cone at 0.8 × the limit). It
  shrinks ×0.85 down to 0.3 r, then is terraced at the band's level; a note goes in `request`. A step's sloped
  bed (role 2) is water, not town ground, in both the shaping and the check. The unshaped sites went 9 → 5.
- Lattice (the materials lane's fault): `upsample` and the noise octaves are smoothed at half their spacing.
  `check` now measures the ratio of the second difference on the 16-sample lines to off them: it went 3.14 → 2.45.
  It fails above 1.5.

Sample check on 5b2605a: fit wet 0, bank 0, step-bank 0, dry_edge 0; **5 sites unshaped**; **overflow 1 cell**;
**lattice 2.45**. Generate 323 s under a load of 12 (170 s on a quieter VM). pytest terrain: 43 passed.

## Session 6 (2026-11-02): round 1's stills mapped to the rules

The stills are in out/batch/adhoc/20261102T011213/01-world-panel-1-20261102T011214. `probes/vantage_ground.py` reads the ground about each world-panel
vantage. A reader read stills 07-09, 20, 21, 23, 24, 28, 29 and 35-37.

| finding (stills) | reader | the rule that made it |
|---|---|---|
| pyramids (24, 28, 29, 36, 37) | planar faces and ruler-straight ridges at the high vantages | `limit`'s 4-neighbour sweeps make L1 cones (square pyramids) wherever the slope sits at the 75° cap; every high window has p99 slope 75°. On 28/29 (rootland-high, 71 m from the flat hist-paatru-lowcrown) a pinned flat with a 0.4 r ramp makes a ledge with a hard corner |
| blocky cliff edge (28, 29, 36, 37) | a straight crease where the face meets the ledge | the same cones meeting a pinned site core |
| straight banks (08, 09, 29) | a ruler-straight diagonal or horizontal shore, ground just above flat water | the footprint edge is the raster polygon's edge or a cell line |
| black voids (07, 35, 37) | flat black with straight edges, a hole | not the ground: build.py writes a LAND row for every province cell (it skips only low apron cells outside it, build.py:130-133). This goes to the materials lane. 23 is shadow |
| camera on a moss slope (20, 21) | the frame filled by a steep face | interior-swamp-high stands on a 69° p99 window. This is a harness vantage problem, not the ground |

Done in generate.py:
- `limit` cones are 8-neighbour (diagonals at lip × √2), so they are octagons, not pyramids.
- Sites ease out to `SITE_BLEND` 1.5 r through the relief noise (`blend_w`). The old ramp was 0.6-1.0 r.
- The cliff mask is the final ground's slope over `CLIFF_DEG` (it used to be the designed slope plus the moved samples). The vegetation lane's cliff shells stand on it.
- The footprint's edge moves ±`SHORE_WOBBLE` 4 samples by a fine noise. The wobble stays off two-level lines (16 samples) and site windows: measured, the wobble there made 3 overflow cells and 6 unshaped sites.

A/B on the sample: without the diagonal pass, still 3 overflow cells; with the wobble at 0, 1 overflow cell. So the overflow came from the wobble.

## Starting state (hand-off)

Session 8 (main at its commit or later). Planner rulings applied: (a) `water/solve.py` `WALL_STEP_M` 65.7 m (vanilla's
tallest one-edge step): waters d cells apart differ by at most d x 65.7 m, the upper yields cell by cell (88 cells;
closed steps over 65.7 m: 1, its upper a wet reach cell, which never yields). (c) Diagnosed: of 3,041 water cells
whose refined ground stands wholly above their level, 1,808 were `pad_ring` cells (incl. (-32,31), (-20,58) at 0 on a
40 m hillside), 647 `fill_enclosed` holes and 570 snapped-body cells (rule 1). Fixed at source: a snapped body keeps its
own level when its samples' lowest ground stands above 0 (per body and per cell); padding and enclosed fill only where
the cell's ground reaches the level + 0.3 m or raster water lies within one sample of it. Now 191 such cells (all
within 0.3 m of their level but 14 reach cells and the pads raster water touches); the generator's own
`empty_water_cells` (no raster sample) 3,088 -> 1,613. (b) A flat whose band is empty is terraced into the slope at
the banks' level, pin kept, `request` says so (3 terraced, all now shaped). Generate: a channel end vertex a dry cell
shares stays bank (dry-edge 4 -> 0). Build stats list `overflow_at`.
Sample check (whole-province generate, written once into the shared out/terrain: the field the next build uses):
dry-edge 0, wet/bank/step-bank 0, **overflow 1 cell (-20,58)**, **5 sites unshaped**, lattice 1.992. Owed:

1. (-20,58) overflow: its west column (bank, role 3, ~60 m, the dry cell (-21,58)'s shared vertices) stands 20 m over
   a wet column at 40 m (raster water one sample in from the edge). Tried clamping `limit`'s pin midpoint into the
   water cones: overflow 1 -> 2 cells, reverted. Next: find what holds that bank's lo near 60 (print lo/hi there).
2. Unshaped: flats the-back-kiln, the-eight-steps (re-sized, band not empty, still std >= 1), naga-village-raiding
   (role 1, no note), depressions the-drawdown-flats, the-slumped-hamlet.
3. Lattice 1.992 (> 1.5): session 7 item 2 stands.
4. Reader on the six hillshades (session 8 ground): plates with hard straight edges remain on -38_25 (shelves at
   0.35-0.58 x 0.18-0.31, 0.20-0.30 x 0.38-0.68), -20_57 (worst: facets, striped bands), 0_0 (square pool and walls
   0.45-0.95 x 0.44-0.9), -12_63 shore; lakes clipped at cell lines on -21_-26. The solve's empty cells are no longer
   the cause (191 left, near-level): next diagnose the generator's role-3 bank floor (`lo[bank] = vmax + FREEBOARD`)
   and the relief prior on those windows.
5. Re-shoot world-panel 24, 28, 29, 36, 37 and 08, 09, 29 at L4 in the planner's batch.
