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

## 2. Roads: green against Skyrim.esm's own roads
**Bethesda's bar** (`vanilla/measure.py q12`, new). It measures the LAND under Tamriel's road-surface meshes: 1672 Road* statics, 1571 of them measurable. It uses the census's own 8 m grade and its edge-wall test.
- Grade: p50 10.3 %, p95 44 %, max 144 %. **23.4 % of the points are steeper than our 0.219 GRADE_MAX.**
- Cross fall: p50 4 %, p90 13.7 %.
- **6.8 % of side points are walls** by our test.
- 9.6 % of the points lie within 16 m of water. Bethesda builds ramps (the RoadStraightLongRamp and RoadSCurveRamp meshes).
- The r4 bar (max 0.219, 0 walls) came from one flat Whiterun box (n = 71). It is stricter than Skyrim itself.
- GRADE_MAX stays as the shaping target. The pass/fail bar is now the vanilla share (`shape.VANILLA_ROADS`). `check` and `census` both fail above it.

**Ours.** A fresh province generate (out/r6/gen0, 367 s) was replayed through the new `routes.shape census --dump` (17-41 s a run, 2.6 GB):

| measure | before | after | Skyrim.esm |
|---|---|---|---|
| walls the road made | 52 | **34** | |
| all walls | 215 | 232 | |
| walls per side point | | **0.74 %** | 6.8 % |
| over-steep points the road made | 9 | **5** | |
| over-steep points, land itself too steep | 211 | 249 | |
| share of points over grade | | **4.2 %** | 23.4 % |

- The ledger's earlier figure was 287 over-steep points.
- `check` on gen0 also passes: 0.63 % walls, 3.9 % steep, folds 0.088 m and 0.253 m (in the band).

**Changed** (shape.py):
- BLEND_M 6 → 9 m.
- Lateral cap: the bench gives up at most 0.1 m at the core's edge, plus 0.15 m per sample inward.
- Harmonic fade of the blend band.

**Re-route not built.** Skyrim's own roads are steep 5.6 times as often as ours, so the bar moved to the measured share instead (0034). build.py is untouched.

**Remaining (not reds)**:
- 34 walls the road made: 15 pinned (the climbs onto places), 17 other, 2 crossing.
- 249 over-steep points where the land itself is too steep.

## 3. Rocks
- booth.py stood each still uphill of its rock: it took the bearing from the Euler lean, and the sign was wrong. So round 2 looked down past the rocks (1 of 6 framed).
- The stand now comes from the generated ground's own fall at the rock.
- Regenerated: the stills now look up 24-44° at each rock. For rock 1, the eye went from 204 u above the rock's origin to 271 u below it.

## L4 owed to the planner's batch
- journey `ground-materials` (row 151): stills at -9 27 and -50 8, midday. Needs a deploy with the ground textures step, Argonia.esm and ArgoniaWorld.esm.
- journey `rock-booth` (row 148): six stills.
- journey `road-look` (row 149): three Blackwood Road vantages. It needs ArgoniaWorld.esm rebuilt from a generate with the new shape.py.

## Tests
- terrain, routes and vegetation tests: 131 passed.
- `make check` was not run, because the shared tree carries other lanes' uncommitted reds.
