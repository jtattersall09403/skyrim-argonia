# Lane 1.15-vegetation: Black Marsh forms, rock sinking, the placer on the contract

Brief: `docs/research/2026-11-01/briefs/1.15-vegetation.md`. Paths touched: `tools/argonia_world/vegetation/`
(forms.py, lists.py, layer.py, booth.py; place/build/checks/__main__), `world/schema.sql` (object_form,
land_region_object.why, vegetation_form.sink_frac), `world/db/{object_form,object_role,land_region_object,
vegetation_form}.jsonl`, `data/dependencies.json` (bmv keep list), `tools/navmesh/inputs.py` (ground_sources),
`tools/argonia_world/regions/classify.py` (object lists delegated to vegetation/lists.py),
`tests/journeys/rock-booth.yaml`, `tests/scenes/rock-booth.txt`.

## Form inventory (`python3 -m tools.argonia_world.vegetation forms --bmv-nifs <list>`)
Landscape TREE/FLOR/STAT (role from mesh file name, then path, then editor ID; Nordic and built paths excluded):

| mod | usable (a mod supplies the mesh) | vanilla mesh (dropped) | in the lists |
|---|---|---|---|
| BM&V (Black Marsh.esm) | 92 (90 from its archive, 2 laid) | 15 | 62 |
| King of the Murkmire | 323 | 225 | 148 |
| Depths of Skyrim | 7 | 27 | 1 |
| Mud Mother Grove | 3 | 1 | 3 |
| HTBM | 0 landscape forms | | 0 |

Finding: BM&V was laid with a keep list of 6 prop meshes, so its flora meshes were not in the game. The lists'
BM&V meshes (64 paths) are now in the bmv row's keep list; stack.py keeps the textures they name. A re-lay
(`stack.py`) is owed before any in-game check. BM&V's archive file list came from the vault (S3 vault-bmv.tar,
`unrar lb`), not kept in the repo.

Every Skyrim.esm form is gone from object_form (was 34, all vanilla). Lists: 47 regions, 13 to 57 rows each,
every row with a `why` citing a dossier or research line; roles: canopy, emergent, gallery, mangrove, palm, shrub,
aquatic (new), mushroom (new), deadwood, rock. Giant mushrooms (taller than 6 m, e.g. vurt_shroom_big6) only in
deep marsh (rootland, deep-sink-basin, interior-swamp, flooded-forest), capped at 0.6/ha; sea plants only on the
coast in 1.5 to 25 m of water. Each list has 3 core forms per role, then a tail rotated by packet, so regions differ.

## Rocks (session 2: our own STATs for BM&V's unrecorded rock meshes)
Planner ruling: BM&V ships 312 rock meshes with no record and only 2 boulder forms exist, so ArgoniaWorld.esm now
carries 20 STATs of our own (`vegetation/rocks.py`, FormIDs 0x0C0000-0x0C0013, EDIDs `ARG_Rock_<mesh>`), each
naming one BM&V mesh. Route 1 (data): the player's BM&V supplies the mesh. `vegetation rocks --nifs <dir>`
read each NIF's vertex box (`tools/navmesh/nif_bounds.py`) into object_form's OBND. The archive was unpacked
from the vault's `vault-bmv.tar` into `~/bmvtmp` (412 rock NIFs), outside the repo. The mesh sets are four
families of Morrowind region rock, admitted by eco class (`rocks.FAMILY_ECO`, `lists.admits`):
- az (Azura's Coast, 5 forms): the northern transition only.
- gl (Grazelands, 5 forms): the uplands.
- al (Ascadian Isles, 5 forms): the western frontier and the river walls.
- bm (BM&V's landscaping boulders, 5 forms): every class that has rocks. These are a third-party resource
  that BM&V bundles; the register row notes this.

Every boulder sinks 0.38 of its OBND height and every cliff shell 0.25 (rock-placement-rules.md rule 1). Each list
now gets up to 8 boulder forms plus at most 2 cliff shells, the shells at 0.4/ha. `pick` no longer drops forms when n
is below CORE: that bug had let 7 cliff shells into one list. The research rules now applied:
- Rule 3: boulders on slopes up to 45 deg; cliff shells need at least 28 deg.
- Rule 2: cliff shells stand upright (conform off).
- Rule 5: our rocks are dry-only. The palette's -6..45 m posture had kept them off the uplands.

Densities (ROCK_HA) are set from rule 4 (Clark-Evans R 0.32-0.58 at a 7-15 m nearest neighbour, so 3-7 rocks a
hectare) and from 16f-ledger.md:109: northern transition 6/ha, western frontier 5/ha, river corridor 3/ha. Before
this, the palette's border-mountains row gave 48/ha a form.

ArgoniaWorld.esm now:
- `terrain/world.py` writes `statics` and `extraMasters` (`rocks.masters`, in the plugin order from
  dependencies.json).
- `LandWorld.cs` writes the STATs and passes `WithExtraIncludedMasters`.
- `VegetationRecords.cs` maps the plugin's own name to its own index.

Sample plugin, built end to end with `pipeline.world(sample)`:
- Masters: Skyrim.esm, King of the Murkmire.esp, ArgonianLakeHouse.esl, DepthsOfSkyrim.esp, Black Marsh.esm.
- It holds the 20 ARG_Rock STATs.
- Readback: 10 cells, 464 refs, matching the shards.

Risk for the planner: an ESM-flagged ArgoniaWorld.esm now has ESP masters (KotM, Depths of Skyrim). The
first in-game load must prove that the engine accepts it.

## Placer, water and budget (session 2)
- Posture: the per-cell level from `water/solve.py` (cell_water has 9,978 rows). The checks now apply the same
  posture: before, they used the old field, giving 5 false water reds at (1,0).
- `tools/navmesh/inputs.water_levels` reads cell_water whenever the default water file is asked for
  (`cell_levels`; -inf where a cell has no water). The navmesh, the water table and the vegetation now all read
  one water. `make navmesh` has not been run.
- Sample (`build --sample`, fresh `terrain build --sample` LAND): 484 refs in 11 cells, 10 s, 12 checks green.
  The ground lane rewrote ground-f32.npy at 18:39 and again at 18:49. A stale LAND gives slope reds, so rebuild the
  LAND before every check.
- Whole province (`build --budget`): 532,550 refs in 15,876 cells (max 111, p95 81), 169 s.
  vegetation_region_budget was re-set. Northern transition keep 0.75; western frontier keep 0.54-1.0.
- Rocks placed in the province: 14 of our forms (2,950 refs; gl_rock03 617, az_rock02 502, ...) and the 2 BM&V
  boulders (772 and 762).
- Booth (`booth --out` over cells -12,52 to -1,63, the northern transition; the sample has too few rocks): six
  distinct boulders: gl_rock04, az_rock09, gl_rock09, gl_rock03, 01coalroundrock, gl_rock06. Tilt is 35-46 deg;
  the earlier cliff shell at 66 deg is gone. `run_journey.py --dry` ok.
- Tests: `pytest tools/argonia_world/{vegetation,regions,terrain} tools/navmesh`: 78 passed (3 new: rock
  families, pick below the core, navmesh cell_water levels). `make world` green; ruff clean.
- Sourcing register: 5 rows: BM&V forms (62), KotM (147), Mud Mother Grove (3), Depths of Skyrim (1), and the 20
  BM&V rock meshes. The bmv keep list has 80 paths.

## Jobs, in order for the whole province
ground, water, `vegetation forms --lists-only`, `vegetation build --budget` (done on today's ground), ArgoniaGen
plugin, stack re-lay (bmv keep list: the rock meshes and their textures), `make navmesh` (now on cell_water),
chart, then lod.sh. Pins: xLODGen beta 132, DynDOLOD 3.00 Alpha-217.

## Starting state
- Session 7 (2026-11-02, round-1 session 1b finding): reader on stills 20-25: the northern-transition trees (22, 23) are drooping conifer-like boughs and (24, 25) weeping columns, Nordic. Placed within 60 m of the four upland panel vantages: 01cypressDUPLICATE001/cypressmoss (cypress5/1), ArgoniaTreeWillow05, 01Willow, hanging moss, 01BIRCH, 01Juniper. `lists.UPLAND_DENY` now refuses cypress, willow, hanging moss, birch, poplar, juniper, bristlecone, redwood and the stockade/house pieces the role words took for cypress, in the tree roles of northern-transition and western-frontier (broadleaf oak, maple, alder, jungle and swamp trees remain; collision rule untouched). Lists and budget rows regenerated, `build --sample` 16 checks green. Owed: an in-game re-read of stills 22-25.
- Session 5 (2026-11-01, the plugin-check gate's vegetation reds): cause of the sample red was a rule, not the check:
  the marsh palette bounds a tree to 6 m above the nearest water level, and on the northern hills that level is the
  sea's (0 m) with the ground 40-95 m over it, so cells (-12,63) and (-11,63) held 0 trees and 145 shrubs (shrubs carry
  no such bound). `lists.UPLAND_DRY` (canopy, emergent, palm, gallery in northern-transition and western-frontier) drops
  that lower water bound; with it the province's northern-transition ran 20.8 trees a cell (band 2.5-15, vanilla field
  10), so `lists.UPLAND_TREE_SCALE` 0.5 halves their density. Lists and budget rows regenerated (`forms --lists-only`,
  `build --budget`). Sample on fresh LAND: northern-transition 7.8 trees a cell (6 cells), flooded-forest 32.5; 528 refs,
  16 checks green; pytest vegetation 24 passed. Whole `make plugin-check` was not waited out (16 min and still in the
  dotnet builds under shared load); its vegetation step is the same `build --sample` + checks, run alone. Province
  (602107 refs, 15876 cells, 278 s) on LAND with 113 of 127 rows: northern-transition in band (trees green for it).
  Remaining province reds: ground (`no LAND` rows -62: stale/partial LAND, the terrain lane still writing) and slope
  (cy 23 stems at 41-71 deg: LAND older than the ground, same cause) are stale LAND; trees red for coastal-lagoon,
  tidal-delta (7 cells) and deep-sink-basin (0-1.5 against 9-27) is a RULE: the palette's canopy posture there
  (-1.5..1.0 m about the water) admits only the 1-2 m ground band, which the new relief (-6..+7 m in those cells)
  leaves at 20-39 % of vertices after slope; owed to the next session (widen from the vanilla marsh posture, 0034).
  A stale sample LAND also reads as "ground 126 m off": rebuild `terrain build --sample` after any ground rewrite.
- Session 4 (2026-11-01, climbable collision, climb-anything.md section 1): `object_form` gained `collision_layer` and
  `collision_mass` (the NIF's first mass-0 bhkRigidBody, else the first; -1 = no body, NULL = not measured), read by
  `vegetation collision --nifs ~/bmvtmp/out` (`forms.measure`; laid mods through the stack, BM&V rocks from the
  unpacked archive). `forms.climbable` (rock: Static or Terrain; canopy, emergent, mangrove, palm: Static, Trees or
  Terrain; mass 0; other roles are flora) now gates `lists.usable`, and `checks.climbable` makes every placed rock and
  tree form red when its measured body is not climbable (share per role in checks.json `climbable_share`). Measured:
  the 22 BM&V rock forms (our 20 STATs + 2 boulders) are all layer 1 mass 0, so none of ours dropped and the booth
  stands (the 74 no-collision NIFs are in the 312 we did not pick); 8 KotM trees with no body and one mass-1 HTBM tree
  dropped from the lists. Owed: 88 BM&V archive flora (31 canopy, 13 emergent, 6 palm, ...) are unmeasured (NULL;
  trees admitted, counted `unmeasured`; rocks never): their NIFs are in the 9.6 GB vault tar, not unpacked. Sample:
  15 checks, 14 green; the one red (northern-transition field 1.5 trees a cell, band 2.5) is not from this change:
  the same sample with the filter off gives 1.8 on today's ground. `forms` (full re-read) clears the layers: run
  `collision` after it.
- Session 3 (2026-11-01, Skyrim.esm audit, decision 0034, audit sections 5 and 6): rocks sink by vanilla's medians
  (boulders 0.5 of their OBND height, cliff shells 0.7; were 0.38 and 0.25: `lists.SINK_*`); 25 % of boulders stand
  upright (`Rule.upright`, the cell-and-form seeded draw `up`, added last so older draws are unchanged; shells always
  conform); `checks.tree_bands` compares trees per cell by region with vanilla's bands (forest 31, marsh 18, field 10;
  eco classes mapped in `ECO_BAND`, band 0.5-1.5 of the mean, field from 0.25 because the lore calls the hills lightly
  forested) and reports trees in water (0 %, vanilla 5.8 %) and the dry trees' p10 distance to wet ground (241 u,
  vanilla 198 u). Sample (11 cells, fresh LAND from `terrain build --sample`): northern-transition 4.0 trees per
  cell (6 cells), flooded-forest 28.0 (4 cells), both in band; 604 refs, 14 checks green. The rock booth is
  regenerated (one upright rock among the six; its vantage stands south). Owed: the whole-province band numbers
  (`build` without `--sample`), and the p10 distance there. A stale `out/terrain/land` fails `ground` by 1 m in
  cell (-19,57) with or without this change: rebuild the LAND first.
- Done:
  - The placer and checks on the new ground and solved water.
  - 20 own rock STATs in ArgoniaWorld.esm, varying by region.
  - Rock densities and gates from the research.
  - Booth regenerated with six distinct forms.
  - Register rows.
  - Navmesh water from cell_water.
  - Budgets re-set.
- Diagnosed:
  - The ground moves under the lane (ground lane regenerates): rebuild the LAND before each check.
  - Rocks were few because of the palette's water posture (fixed).
- Owed:
  - Stack re-lay for the new keep list, before any in-game check.
  - The booth L4 and its reader in the planner's batch.
  - The first load of ArgoniaWorld.esm with ESP masters.
  - `make navmesh` on the whole province.
  - Coast rocks: none listed, because the coast dossiers ground none (wet rocks, rule 5, need a wet family).
- Session 6 (2026-11-01, marsh trees, golden rule 0034): measured Skyrim.esm's Morthal-marsh TREE refs (159 cells with
  their own water level, 1,465 refs) against their cell's water: p5 -0.02, p10 0.17, p50 2.0, p90 4.8, p99 8.8 m above
  it, 7.5 % with the ground under the water, bases p10 0.4 m under the ground (Riften shore: p50 4.4, p90 13 m). Rules
  (`lists.py`): marsh canopy/emergent/palm/gallery stand -6..+1.2 m about the water, cypress-named forms -6..+2.0
  (no mangrove form exists in the pool: the palette's 650 a ha mangrove served nothing and hid that the delta had no
  trees); slope 38 for marsh trees; per-class tree density `MARSH_TREE_HA_BY` (lagoon 170, sink 90, delta 68, rootland
  100, corridor 80, others 52 a ha) tops up or scales the palette's, because a lagoon or sink cell is mostly water
  deeper than a tree stands in. Check (`checks.py`): a cell with under a quarter of its vertices within 2 m under the
  water is open water, not a marsh cell, and is left out of a region's mean; a region of under 10 such cells is
  reported, not failed. Province (out/terrain/land, 641652 refs, 107 s): 16 checks green; lagoon 12-25, sink 10-27,
  delta 8-27 trees a cell (band 9-27), rootland 19-34; trees in water 18.1 % (vanilla 5.8 %), dry p10 215 u (198).
  Open: the in-water share is 3x vanilla's. Sample 564 refs, green; pytest vegetation 24 passed.
