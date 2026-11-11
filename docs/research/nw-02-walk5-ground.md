# Walk 5, lane G: roads, ground and grass, measured

Measured 2026-11-10 on the build VM. Our build is terrain 20261109T204317Z (the ground paint in `out/newworld/plugin/tex`,
the ESM written from it); Skyrim.esm, Black Marsh North.esp and King of the Murkmire.esp are read with a Python LAND
reader (BTXT/ATXT/VTXT, layers stacked as the engine stacks them: base 1, each alpha layer replaces (1 - o) of what is
under it). Every diffuse is read as the NewWorld profile resolves it (`~/.argonia/stack/installed-NewWorld.json`, then
the archives).

## 1. How many textures a quadrant can show

- The landscape shader has six texture slots: Community Shaders `Lighting.hlsl` samples `TexColorSampler` and
  `TexLandColor2..6Sampler` and blends them by `LandBlendWeights1.xyzw` and `LandBlendWeights2.xy` (weights computed per
  vertex, interpolated linearly over each land triangle). A quadrant is base + at most five alpha layers.
- Distinct textures per quadrant (base and alpha): Skyrim.esm 1: 7,112, 2: 7,069, 3: 6,019, 4: 5,845, 5: 5,632,
  **6: 7,506, 7: 337** (0.85%, the pile-up at six is the Creation Kit's cap); Black Marsh North and KoTM never pass 6.
- Our build before the fix: 39,183 of 107,744 quadrants (36%) carried 7 textures. In the engine view (the seventh
  layer not shown) a shared vertex read differently from two quadrants by up to 1.0, and 651 road quadrants lost up to
  0.91 of their road weight to the hidden layer: square and triangular patches cutting into the road, ending at
  quadrant lines. Lane L measured that 83% of the 3,222 too-light LOD ground squares are such quadrants.
- After: base + at most 5 alpha layers; 0 quadrants over 6. Textures per quadrant (layers written) 1: 558,
  2: 24,358, 3: 5,659, 4: 5,866, 5: 6,944, 6: 64,359 (final numbers in the lane's report).

## 2. How a road is painted

- Skyrim lays a road mesh (`Road*`, 6.9 m surface) over ground painted with the region's dirt LTEX: 0.97 to 3 m from the
  spine, 0.76 at 5 m, 0.56 at 6 m, 0.36 at 8 m (research nw-02-ground-water-rules.md 2.3). The dirt's ramp from 0.85
  to 0.15 spans 1.7 to 2.0 vertices at p50 (LDirt02 1.81, LFallForestDirt01 1.99, LReachDirt01 1.67, LDirt01 1.95) and
  its neighbour steps are hard (p90 0.99 to 1.0): the mesh hides them. Road cells carry 5 alpha layers in 1,492 of
  3,032 quadrants.
- BM&V paints its roads in LAND only (cobble `road01`, the dirt track `dirtroad01`), with a 2 m edge.
- We lay no road mesh: the land is the road, so it must be soft itself. The rule (`tools/newworld/world/roadpaint.py`),
  shared by the world, a place's paths and the studio: the measured ramp from the surface edge (3.45 m major, 2 m
  minor), a minor road or path at 0.6 scale; a track core of two materials mixed by an along-road noise (60 and 130
  samples, each always 15% or more) handing to a verge over 4.5 m; no grass on any road material; the road runs out
  over the last 4 m before water.
- Root causes of the owner's road faults, in the old build: (1) the seventh texture hidden by the engine (above);
  (2) the core (`dirtroad01`) switched to the skirt (`LDirt02`) over 1.8 m, one vertex: a join of 0.50 between the two;
  (3) the skirt `LDirt02` shows in the NewWorld profile as Tropical Skyrim's `dirt02.dds`, mean RGB (52,36,23),
  luminance 39, contrast 9.0, the darkest, flattest ground we painted, 3.5 to 12 m either side of every road;
  (4) traces under 8% pruned from the ground left the road at 1.0 where its ramp said 0.88 (a plateau, then a step);
  (5) where two ground provinces' road sets meet, each vertex kept only its four heaviest materials, so the road lost
  slots to the ground; (6) place paths (tools/places/build.py) feathered over 96 units, under one vertex (128): a
  path went from 1 to 0 between two vertices, a hard triangular edge, and added a layer over the world's six.
- Road materials (mean RGB, luminance, contrast as resolved): BM&V dirtroad01 (81,69,51) 70 / 13.6; TS Tundra02
  (112,84,46) 87 / 14.4; TS RiverMud (85,68,47) 70 / 12.7; BM&V Sand06 (91,74,53) 76 / 12.2; TS DirtSnowPath01 (a
  trodden earth with grass in it) (88,74,47) 75 / 13.6; TS FieldGrass01 (121,89,58) 94 / 8.8. KoTM's own road LTEX
  (`Road01MarshMud02_d`) is luminance 31 and BM&V's cobble 55 to 59: both darker.

## 3. Swathes

Run = for each land vertex, the distance to the nearest vertex whose dominant texture (or grass list) differs.

| | texture run p90 | p99 | grass run p90 | p99 |
|---|---|---|---|---|
| Skyrim Whiterun tundra | 4.1 | 16.5 | 26.6 | 58.2 |
| Skyrim Falkreath pine | 7.8 | 19.4 | 36.4 | 95.1 |
| Skyrim Hjaalmarch marsh | 2.6 | 7.5 | 15.1 | 43.5 |
| Skyrim Rift fall forest | 10.7 | 33.7 | 77.1 | 135.4 |
| Skyrim Pale snow | 5.2 | 11.6 | 29.8 | 92.3 |
| BM&V Black Marsh North | 376 | 602 | 376 | 602 |
| ours before, worst region | 42.1 (chixathe-mesa) | 90.8 | 42.6 | 92.3 |

Ours before: every region's texture run p90 was 15 to 42 m, against Skyrim's 2.6 to 10.7: one ground read for
tens of metres because each material's share wandered only at 30 to 300 m. After (three scales, final numbers in the
lane's report): worst region p90 12.8 m, p99 31.8 m; grass p90 21.9, p99 41.7.

## 4. Regional variety (weighted Jaccard between land regions' shares)

Ground (materials grouped by diffuse) before max 0.776, mean 0.367; grass before max 0.855, mean 0.396. After the
provinces alone: ground max 0.605, mean 0.253; grass max 0.745, mean 0.208 (with the regional signatures: the lane's
report).

## 5. Assets

All 85 materials' diffuses and all 152 grass entries' models resolve in the NewWorld profile (installed files and
archives). Note: `tools/places/assets/resolve.py` does not find Tropical Skyrim's `Meshes\\Landscape\\grass\\*.nif`
(the mod holds both `Meshes/` and `meshes/`), though the profile lays them.
