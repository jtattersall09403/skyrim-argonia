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

Session 14 (commit 905725f). `probes/clamp_census.py` now reads the field rules: a plate is a dry vertex whose
8-neighbour steps are all under 0.02 m, and the census attributes each one to the rule that set it (gap up/down, iso
hollow, edge lift, lo/hi bound, sites, the pre-ground). Before, plate share by window: coast -20_57 11.4 %, border
-12_63 17.3 %, river -38_25 11.8 %, marsh -21_-26 11.2 %, 0_0 1.8 %. The causes:
- entrance sites (9-17 %): a flat was levelled to one constant m, and a mouth's wet disc was raised to
  vmax + freeboard;
- the pre-ground (marsh 10 %): the relief noise faded to nothing by the water, leaving `base + floor` flat;
- gap 0.2-0.5 %, iso 0 %.
The fixes:
- a flat keeps a damped share of its own relief (FLAT_KEEP 0.35, core std held at 0.4 m);
- the wet disc climbs from its rim by the vanilla shore profile (`water_field.shore_rise`);
- the noise keeps 0.8 of its rises and 0.3 of its dips by the water (NEAR_RISE/NEAR_DIP).
After the fixes: 2.4 / 1.7 / 5.0 / 3.0 / 1.2 %. A relief-keeping remap of the gap band was tried and reverted: it
carried each cell line's level step into the ground (lattice 1.38 -> 1.66 over the 1.5 gate; measured by variants).
The gap keeps the snap. `terrain check --out out/terrain-sample/s14b`: fails [], wet/bank/dry-edge/step-bank 0,
unshaped 0, lattice 1.376 (s13 1.253). Generate 119.7 s.

The reader on `s14b`'s hillshades (`s14/hs`, same bar the gap remap) gave these verdicts:
- -12_63: terraces fixed;
- -20_57: plates mostly fixed, faint seams at x 0.50 and y 0.50, a faceted knob at (0.50-0.63,0.34-0.47);
- -38_25: big plates gone, but small rims remain and the square pools and grid shores are unchanged;
- -21_-26: the rectangle and the square pool are unchanged;
- 0_0: rim-edged rectangles at (0.73-0.88,0.62-0.88) and (0.0-0.13,0.87-1.0).

The remaining defects are measured at their cause. In -21_-26 the rectangle is the cell column x -17 (rows
-21..-25): its pre-ground stands at about 1.1 m, it is 0 % wet, and its lift is about 0. The columns either side are
88-100 % wet and carved to -1.7 m. So the "plate" is uncarved ground between the raster footprints, and the "square
pool" is the wet raster's own cell-blocky footprint (`inp.wet_level`, 88 % of each cell) carved to its bed at
CARVE_GRADE. Water planes and the field are not the cause.

Owed, in order:
1. The footprint from the ground's contour, not the raster's cell blocks: inside a water cell, wet = pre-ground under
   the level (with the raster only seeding which body it joins), and the carve then follows that contour. The likely
   place is generate.py's `foot = has & ~isnan(inp.wet_level)` (~line 497) or the hydrology raster's producer. Then
   re-run the census and the reader on the five windows.
2. The clamp path's deletion was handed to a deliver-small child (behaviour-identical, checked bit-for-bit against
   s14b); confirm it landed (`git log`).
3. ONE whole-province generate into out/terrain, then `terrain check`: not started.
