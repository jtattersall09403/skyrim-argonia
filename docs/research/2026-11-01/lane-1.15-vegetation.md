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

## Rocks
10 rock forms, none vanilla-shaped (Tropical Skyrim's RockL01 at a vanilla path excluded): BM&V 01mudrockstack
(4.1 m), 01coalroundrock (0.8 m), sink 0.38 of OBND height; KotM ArgoniaRockWall01-04 and Moss (33-38 m cliff
shells), sink 0.25, uplands only, slope 25 deg or more (rock-placement-rules.md rule 1). The pivot goes to
ground - scale x (OBND z0 + sink x height); rocks conform to the slope. Only 2 boulder forms exist as records:
BM&V ships 312 rock meshes with no form. Proposal: our own STAT forms in ArgoniaWorld.esm that point at them
(route 3, a planner call).

## Placer (sample, today's ground)
`build --sample` then the checks: 76 refs in 11 cells, 7 s, all 12 checks green (new `lists` check: no vanilla
form or rock shape, every rock sunk, a why on every row, BM&V in every list). The ground check now allows for the
sink. Posture uses `water/solve.py` (level, nearest_level) once cell_water has rows (0 today); until then it
uses the old field. `vegetation.render_layer(window)` returns points coloured by role, for terrain/render.py.
Tests: 29 passed (vegetation + navmesh). `db check` green. Full `make check` not run (planner's round gate).
The sample needed a fresh `terrain build --sample` LAND: out/terrain/land holds only 13 rows.

## Jobs (re-checked, not run)
- `tools/navmesh/inputs.ground_sources` read the refined height, regrade and place edits; it now uses
  `Sources.load()` when `out/terrain/ground-f32.npy` exists. Its water still comes from the old plane field
  (`out/water/cells.jsonl`). Owed: move it to cell_water once the water lane writes it.
- `tools/chart` reads `Sources.load()`, so it follows the ground automatically.
- `infra/gpu-box/lod.sh` reads the deployed plugin, nothing local. Pins: xLODGen beta 132, DynDOLOD 3.00 Alpha-217.
- Whole-province order: ground, water (cell_water), `vegetation forms --lists-only`, `vegetation build --budget`
  (the region keeps were set on the old forms), ArgoniaGen plugin (masters now include Black Marsh.esm, KotM,
  DoS, ArgonianLakeHouse.esl; readback owed), stack re-lay (bmv keep), `make navmesh`, chart, lod.sh run.

## Starting state
- Done: inventory, lists, sinking, the lists check, render layer, rock booth generated from the sample's placed
  rocks and dry-run ok, navmesh ground input switched.
- Diagnosed: the BM&V meshes were never laid (keep list); the sample's flooded-forest gets few stems (water
  posture on the old field).
- Owed: re-run the booth generator, `--budget` and the sample checks after the ground and water land; the
  booth L4 and the reader in the planner's batch; ArgoniaGen readback with the new masters; navmesh water
  input; the sourcing-register rows per form (only the bmv keep list was updated); own STAT forms for BM&V's
  unrecorded rocks (planner call).
