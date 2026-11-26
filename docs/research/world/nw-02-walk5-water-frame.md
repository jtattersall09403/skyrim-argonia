# Water kinds on the widened world, and the frame of every consumer (nw-02 walk 5, lane X)

Measured 2026-11-11 on terrain build 20261111T025937Z (grid 6849 x 5761 samples, the build before at sample
(512, 512) of it) against the build before, 20261109T204317Z (5825 x 4737), whose water classification is the
deployed one. The previous classification was rebuilt from the previous terrain's body raster in the bucket with
the same sources and gave the deployed chain's own numbers (2,195 bodies, 733 flowing, 224 owner bodies, round
Helstrom 27.0 ha river kept and 30.9 ha to marsh), so body-by-body comparison is against the deployed state.

## No raster or point moved

The widening added samples to the heightmap only. Everything the water is cut on is in map pixels of the source
picture (3521 x 2841), before and after: the terrain's body raster, the regions raster (`terrain.region_px`), the
owner's edit points, place positions. The water pixels inside the picture's ruler band are identical in both
builds (0 of 3,840,979 differ). Flowing bodies did not fall either: 733 before, 728 in the faulty run (the 1,385
in older records is a count from 2026-11-09 morning, before the fringe and Helstrom rules).

## What did go wrong: three causes

1. **The terrain's body list carried the owner's kinds, and water_kinds read them as the map's.** The terrain
   build lays `water_overrides.json` over its own bodies by id (the kinds set the beds) and wrote the result as
   `water_kind_id`. water_kinds took that as the drawn kind. The previous terrain was built at 20:43 on
   2026-11-09, before the owner's evening edits were pulled (21:19), so this was the first terrain build to see
   them. One of them, `wb-1807-1384` (a 488 m2 bit of channel beside the 105.1 ha river body
   `wb-1300-1162`, set to lake), turned the terrain's body from stream to lake; a still patch in a channel network
   is merged back into its channel (`reshape`), so the bit joined the river; the lake edit (21:12:14) is later
   than the river edit on that body (21:10:23), and edits on one body merge latest-first. The whole 105.1 ha river
   became lake. Measured: river to lake 122,687 px (105.0 ha), running water reaching the sea 395,848 px to
   268,253, flow cells 2,855 to 2,184, Murkwood's river 57.9 ha to 3.6 ha (all of it under the 50 m main-course
   width, so 0 kept), and no river cell within 3 cells of (-21, -140) for `ANWWalkHelstromRiver`.
2. **An edit was only a point.** The bodies are cut afresh on every run, so a point finds whatever body holds it
   that day. Nothing recorded which water the edit was made on, so nothing could tell that 18 edits had landed on
   a body of another size or kind.
3. **The picture's ruler band stopped reading as land.** `terrain_beyond` now reads the 88 px band as the map's
   edge carried outward. Sea: the band no longer counts as coast or as enclosing land, so inside the picture
   372,579 px (319 ha) of shallow coast along the old ruler is open ocean and the north-east bay (290,137 px) is
   shallow coast and ocean; this is the rule's own answer without the ruler, and is accepted. Inland: a lake in
   the northern margin at px (821, 132), closed on the source map under the ruler, was carried out to the
   picture's edge, and open water touching the edge was sea (`terrain_water.label_bodies`): 11 ha of lake became
   shallow coast and the terrain gave it a sea bed.

## The fixes

- `terrain.py` writes `map_kind` and `map_why` beside each body's kind; `water_kinds.map_kinds` classifies from
  those. A body list without them (build 20261111T025937Z) is labelled again from the body raster by the terrain's
  own `label_bodies`.
- `water_held.py`: when an edit that sets a kind is taken in, the water of the body it was made on is stamped into
  `newworld/sources/water_owner_bodies.png` and the edit records `held` and `area_m2`. water_kinds cuts every held
  body out first, whole, with the owner's kind, and classifies the rest round it. The 289 existing edits were
  stamped once from the deployed classification: 222 held bodies (286 kind edits), 3 edits without a kind.
- `terrain_water.label_bodies`: the map's edge makes open water sea only when the water it belongs to reaches a
  sea region. The northern lake is a lake again, with a lake's bed.
- `terrain_water.hold` replaces the terrain's matching of edits to its own bodies by id: the owner's held water is
  laid on the terrain's bodies (a body it covers takes the owner's kind; a part it covers is cut off as its own
  body), so each owner-set water gets its kind's bed. The inland rise is still measured from the sea by kind, and
  from open water the map's edge cuts (`edge_cut`: off the picture counts as sea for the rise).
- `teleports.ground` read `land/limited.npy` (VHGT steps) as game units: every landing was written at steps + 32,
  so 108 units under the ground at Helstrom (ground 160). Now steps x 8.

## After the fixes, on 20261111T025937Z

| Measure | Deployed (20261109T204317Z) | Faulty run | Fixed |
|---|---|---|---|
| Bodies / flowing bodies | 2,195 / 733 | 2,138 / 728 | 2,141 / 725 |
| Running px reaching the sea | 395,848 | 268,253 | 389,043 |
| Flow cells | 2,855 | 2,184 | 2,813 |
| Round Helstrom: river kept / to marsh | 27.0 / 30.9 ha | 0 / 3.6 ha | 27.0 / 30.9 ha |
| Owner bodies | 224 | 221 | 224 |
| Owner edits on the same body (area within 10%), kind as made / overtaken by a later edit | 269 / 20 | 259 / 12, 18 off | 269 / 20 |

Inland water inside the picture is the deployed classification pixel for pixel but for 6,229 px (5.3 ha): river
mouths in the western margin (region none, px x 86 to 224, y 785 to 1180: 3,952 px of stream and river now shallow coast or bay
against the larger western sea), one fringe of 1.6 ha (estuary to green marsh at px (2457, 1544)) and an estuary
of 0.9 ha in the north-east margin. The 6,805 fewer running pixels are these. One edit is on other water than
before: `wb-1846-2606`, a name only ("Update-2026-11-09c", no kind), whose point lay in the shallow coast drawn
along the old ruler and now lies in open ocean; the name follows the point.
`teleports build`: 266 landings, 0 faults; `ANWWalkHelstromRiver` lands in its own cell (-21, -140).

## The terrain rebuilt with the owner's kinds by held water

Trial build 20261111T052124Z in a worktree (same inputs as 20261111T025937Z, not uploaded), against 025937Z:
- `build.json` reports 0 override problems (8 unknown bodies before) and 222 held waters; a held water lying on no
  water stops the build, and `terrain check` fails on it and when `water_overrides.json` or
  `water_owner_bodies.png` has changed since the build (both are in the input digests). 2,227 terrain bodies
  (2,211), none under 40 px, the smallest the labelling keeps. Kinds changed on 639,814 map px, the largest: the
  south-west sea bay to ocean (the owner's ocean), river to blackwater swamp, the northern lake ocean to lake,
  estuary to green marsh.
- `terrain check` 0; Helstrom's held zone the old ground plus 72 units on 865,322 of 865,322 samples, max
  difference 0; `terrain_needs` the same 6 failures (blackrose-prison, fort-chalkmoth, mine-28-m65, vicrium,
  seafalls, blackrose).
- water_kinds on it: check ok, 2,143 bodies, 725 flowing, round Helstrom 27.0 ha kept and 30.9 ha to marsh, 289
  edits: 269 as made, 20 overtaken, none off, no held water lost.
- Heights: 2,493,770 of 39,457,089 samples differ. 1,244,412 lie in or within 3 map px (9 m) of water whose kind
  changed: the beds, up to 4,904 units where bay became ocean. 717 other water samples differ by one step.
- The land moved too: 1,246,119 samples (3.2% of the grid) more than 9 m from any changed bed, 70% of them by one
  step (8 units), 99% by 104 units or less, the most 936 units (13 m). The cause is the inland rise. It is measured
  from the sea (`coast_t`, a 5 km fall-off that feeds the relief, both landform passes and the erosion), and the
  sea is now read from the map's own kinds (`map_kind`) and from open water the map's edge cuts, so an owner's
  kind sets a bed and moves no land. Build 025937Z read the kinds with the owner's laid on by id, so its rise
  counted as sea the owner-set shallow coast its id matching happened to hit, 81,003 map px in 33 patches, the
  largest 72,817 px at map px (2232, 2239) and 4,603 px at (1730, 2359); those are inland water again for the rise
  and the land round them stands a little higher. Measured by building both ways from the same inputs: with the
  rise read from the owner's kinds by held water the land outside the beds differs from 025937Z on 282,875
  samples (99% by 64 units or less, the most 304), with the map's kinds on 1,246,119. Of the 1,246,119, 17,634 lie
  within 18 m of a changed bed and 510,258 within 88 m of a road line; the rest was not split further between the
  rise and the road lines that sample bank heights.

## The checks that would have caught it

`water_kinds` ends with two checks, written to `out/newworld/water_check.json`, and exits 1 when either fails;
`verify` reads the file as two rows.
- Kinds: per kind, the bodies and the area inside the picture (the map less its ruler band) against
  `newworld/sources/water_accepted.json`; a kind off by more than 2% (or 2 ha, or 3 bodies) fails, and so does a
  waterline that moved by over 0.1%, another source water picture (the record keeps the sha256 of
  `out/newworld/raster/water.png`) or a missing record. On the faulty run: river 208 ha to 101 ha, lake 114 ha to
  219 ha. `water_kinds --accept` is the only writer of the record, after the new classification has been looked at. The record in the
  repository is the fixed classification of 20261111T025937Z; against the deployed one it differs in the sea
  (bay 294 to 73 ha, ocean 926 to 1,309 ha, shallow coast 1,209 to 1,051 ha: cause 3) and by 6 ponds.
- Edits: every owner edit, the body its point finds, that body's area against the edit's `area_m2` (10% or
  500 m2) and its kind against the owner's kind on that water (the latest kind edit made on it). On the faulty
  run: 18 off. A held water left on no water fails the same check.

## The frame of every consumer

Each row was measured on the built outputs of 20261111T025937Z; the test is in
`tools/tests/test_newworld_frame.py` unless named.

| Consumer | How it finds a position | Measured | Verdict |
|---|---|---|---|
| terrain grid | `build.json` origin (-409600, -319488) | Helstrom's sample (1725, 2437) to (2237, 2949): +512, +512; wet/dry agreement with the build before 0.959 at that offset, 0.664 at (0, 0) | correct; `test_a_place_keeps_its_game_coordinates_and_cell_when_the_grid_grows` |
| terrain_held (Helstrom's ground; tools/places reads it through the land) | world position | new minus old over 300 x 300 samples at Helstrom: exactly +72 on all land, 0 on water; one sample off, 77% | correct; same test |
| water_kinds (`region_px`, `heights_px`), map_page terrain layer | map px; px to sample through the build's origin | map water against ground under 0: 0.989; 0.660 if 512 samples off | correct; `test_a_map_pixel_reads_its_ground_through_the_builds_origin`, `test_the_regions_raster_is_in_map_pixels_whatever_the_grid` |
| water overrides, paint, water_overrides_pull, the atlas | map px, raster 3521 x 2841 | 289 of 289 points on a body; held raster the picture's size | correct, and now recorded; `test_the_owners_water_edits_and_their_held_water_share_the_maps_frame` |
| landcover (and what reads its legend origin: texture, mist, place flora, tools/places/build) | legend `origin_world`, `sample_to_px` | origin and shape equal the build's; region at Helstrom murkwood, at Stormhold valley-of-storms | correct; `test_the_map_pixel_of_a_place_is_the_same_from_either_grid` |
| world/land.py | `units.Grid` from build.json | grid cx0 -100, cy_top -79; limited x 8 equals the heightmap at Helstrom; start marker (-26880, -521856), cell (-7, -128), as deployed | correct; Grid test |
| world/cells.py | Grid | 20,406 of 20,640 cells inside a region carry the map's region for their map cell; Helstrom's cell (-8, -148) murkwood | correct; Grid test |
| place (flora) and mist refs | Grid, legend origin | 95,392 of 95,392 sampled refs in the cell row their file names; flora 15 units (median) from the ground at its position | correct; Grid test |
| world/mapdata.py | Grid | 116 of 116 markers within a cell of their place record; marker heights were read in the wrong unit | frame correct; unit fixed; `test_a_marker_stands_over_the_ground_in_game_units` |
| teleports.py | Grid | 266 landings, 0 faults; heights were read in the wrong unit | frame correct; unit fixed; `test_the_ground_is_in_game_units_from_the_limited_steps` |
| tools/navmesh | Grid from the land manifest | build box (-99, -257) to (112, -80), inside the land grid | correct; Grid test |
| build_db rasters and positions | map px, `frame.px_to_world` | Helstrom px (1482.9, 1038.2) to (-32174, -605839), the record's | correct; map pixel test |
