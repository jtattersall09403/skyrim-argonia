# Lane 1.15-r6-ground-roads: matte varied ground, roads as worn lanes, rocks seated (hand-off note)

## 1. Ground
**The bar is Skyrim.esm's own riverbed edge share** (`python -m tools.argonia_world.vanilla.measure q11`, new):
- Tamriel's LAND has 8.20 M dry vertices, and LRiverbedEdge01 is the only riverbed edge LTEX.
- It covers 0.32 % of all dry land: 2.51 % of dry land within 16 vertices of water and 0.06 % beyond.
- 83.8 % of the texture lies within 16 vertices of water.
- Over 78 8x8-cell shore windows, the share within 16 vertices runs p50 0, p75 2.9 %, p90 6.1 %.
- The check fails above 6.1 % within 16 vertices or above 0.06 % beyond.

**Ours, `terrain check-materials`** (34 one-km windows, seed 1; 6.46 M dry vertices):

| EDGE_REACH | within 16 v | beyond 16 v | all dry |
|---|---|---|---|
| (2, 4) | 8.3 % | 0 | 2.83 % |
| (1, 3), new | **4.21 %** | 0 | 1.43 % |

- The new reach puts the edge on the first dry vertex only, which is Skyrim's one-vertex strip.
- check-materials: 19 textures, 0 fails.

**Derived textures** (`terrain derive-textures [--dry-run]`, new: derive_textures.py):
- Output: out/derived/argonia-ground, 38 files, 51 MB, about 39 s.
- BM&V's 19 diffuses now carry 10 mips, written as uncompressed BGRA.
- The normals are built from the diffuse's luminance relief. Their tilt and alpha are set to Skyrim.esm's normal of the same name.
- Laid result: alpha 16.9-40.7 (vanilla mean 22.0, p90 28.9; riverbededge 40.7 is its own vanilla figure); tilt 13.9-59.6°.
- The TXSTs now name `argonia\landscape\<name>.dds` and `<name>_n.dds`.
- L1 tests: test_derive_textures.py (mip round trip, alpha 22 ± 1, tilt ± 1.5°).

**Install**:
- deploy.sh step "ground textures" runs the tool and sends the folder to `C:\argonia\ours\derived\argonia-ground`.
- stack.ps1 `on` lays every `ours\derived\<name>` over the mods; `verify` skips those files.
- The mesh-patcher lane can use the same `ours\derived\<its name>` folder.
- Risk: Argonia.esm's TXSTs now name these paths, so a deploy that skips this step shows missing textures.

## 2. Roads (not closed)
**Before**:
- Fresh province generate: out/r6/gen0, 367 s, with road dump out/r6/road-dump.npz (202 MB). Both can be rebuilt; delete them once the next pass has used them.
- New `routes.shape census GROUND_DIR --dump D` replays the road pass on the dump: 17-19 s a run on an idle VM, 62 s and 2.6 GB under load.
- Walls: 215. 52 of them were made by the road (pinned 29, other 16, crossing 7).
- Dry points over grade: 602. 211 are where the land itself is steeper than the grade (ledger row's before: 287).

**Changed** (shape.py):
- BLEND_M 6 → 9 m.
- Lateral cap: the bench gives up at most 0.1 m of the land's cross fall at the core's edge, plus 0.15 m per sample inward.
- Harmonic fade of the blend band.

**After**:
- Walls the road made: 34 (pinned 15, other 17, crossing 2).
- Over-steep points the road made: 5; 249 remain where the land itself is too steep.

**Still red**:
- Road-made walls are not 0, so census exits 1.
- Steep runs have no re-route with a refused reason; build.py was not touched.

**Tried and measured**, all worse or blocked by the grade test:
- A Lipschitz envelope from the core: 163 walls.
- CROSS_KEEP 0.7 or 1.0: 27 and 108.
- A hard edge cap: 17, but it breaks test_steep_road_held_to_the_grade.

**Next**:
- Cap the along-road evening (zc - zg) at the core's edge too, re-measured against the grade test.
- The pinned walls at the climbs onto Gideon and Glenbridge belong to the place grade.

## 3. Rocks
- booth.py stood each still uphill of its rock: it took the bearing from the Euler lean, and the sign was wrong. So round 2 looked down past the rocks (1 of 6 framed).
- The stand now comes from the generated ground's own fall at the rock.
- Regenerated: the stills now look up 24-44° at each rock. For rock 1, the eye went from 204 u above the rock's origin to 271 u below it.

## L4 owed to the planner's batch
- journey `ground-materials` (row 151): stills at -9 27 and -50 8, midday. Needs a deploy with the ground textures step, Argonia.esm and ArgoniaWorld.esm.
- journey `rock-booth` (row 148): six stills.
- journey `road-look` (row 149): only after the roads are green.

## Tests
- terrain, routes and vegetation tests: 131 passed.
- `make check` was not run, because the shared tree carries other lanes' uncommitted reds.
