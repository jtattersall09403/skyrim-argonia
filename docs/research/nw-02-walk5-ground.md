# Walk 5, the ground: roads, textures and grass, measured

Measured 2026-11-11 on the build VM. Ours is the whole-world repaint of terrain build 20261111T053723Z by
`tools/newworld/world/texture.py`, read by `tools/newworld/world/texcheck.py` (every row passes); "the old build" is
the ground of the ESM the owner walked (terrain build 20261109T204317Z). Skyrim.esm, Black Marsh North.esp and King of the Murkmire.esp are read with a
Python LAND reader (`tools/argonia_world/esm.py`; BTXT, ATXT, VTXT; layers added as the engine adds them: each
alpha layer's opacity is its weight and the base shows 1 - their sum; Skyrim.esm's opacities sum to 1.00 at a
vertex at p90 and pass 1.05 at 1.8% of vertices, BM&V's never pass 1.00: measured 2026-11-13, walk2/ground.md). Every diffuse is read as the NewWorld profile resolves it.

Every number is on the engine view: a quadrant shows its first six textures, weights run linearly over each land
triangle, and a step is the change of a weight between two vertices that share a triangle edge, per vertex spacing
(1.83 m; a diagonal edge is 1.41 spacings long, so its change is divided by 1.41).

## 1. How the LAND record holds its textures

- Skyrim.esm (1,500 cells of Tamriel sampled): quadrants are numbered 0 to 3 = bottom left, bottom right, top left,
  top right; a quadrant's alpha layers are numbered 0 to n - 1 in every one of 4,060 quadrants, its base is layer -1;
  a VTXT point's position is row x 17 + column, row 0 at the south edge (read that way, two quadrants of a cell agree
  along their shared edge at the median cell; read transposed they differ by 1.0). Ours is written the same way
  (`NewWorld.cs` GroundLayers), and the ESM read-back compares every written quadrant with the painted shard, byte for
  byte (`newworld check`: on the old build's ESM, 68,561 of its 68,561 quadrants of six textures or fewer are equal).
- The landscape shader has six texture slots: Community Shaders `Lighting.hlsl` samples `TexColorSampler` and
  `TexLandColor2..6Sampler` and blends them by `LandBlendWeights1.xyzw` and `LandBlendWeights2.xy`. A quadrant is a
  base and at most five alpha layers.
- Distinct textures per quadrant: Skyrim.esm 1: 7,112, 2: 7,069, 3: 6,019, 4: 5,845, 5: 5,632, **6: 7,506, 7: 337**
  (0.85%; the pile-up at six is the Creation Kit's cap); Black Marsh North and KoTM never pass six.
- The old build: 39,183 of 107,744 quadrants (36%) carried seven. With the seventh not drawn, a vertex two quadrants
  share read differently from each by up to 1.0, and 690 road quadrants hid up to 0.91 of their road weight: the square
  and triangular patches cutting into roads, ending at quadrant lines.
- Ours: 0 of 154,080 quadrants over six. Textures written per quadrant 1: 982, 2: 67,598, 3: 5,895, 4: 5,015,
  5: 7,763, 6: 66,827; a land quadrant shows 5.45 on average; shared vertices agree to 0.0107 (limit 3/255).

How a quadrant is cut to six: it keeps the heaviest ground at each of its four corners (read from the ground blurred
over 6 vertices, so four corners seldom name four grounds, and the quadrants round a corner always share one), then
its road materials (the gravel track every road set carries first, so road quadrants always share a road material,
then the heaviest), then the heaviest over the quadrant and an 8-vertex halo. A material a quadrant does not keep
fades to nothing over 8 vertices toward it; what the fade takes from a road material goes to the road materials kept
there and what it takes from the ground to the ground kept there. So the cut never opens a hole in a road, never lays
road over ground, and every shared vertex reads the same from each side.

## 2. Roads

### Skyrim's road ground

Skyrim lays a road mesh (6.9 m surface) over ground painted with the region's dirt (or snow) LTEX. Measured under the
straight road pieces of six holds (the spine = the piece's centre line; road ground = the dirt and snow LTEX and the
default ground of a quadrant with no base):

| hold (straight pieces) | road weight at 3 / 4 / 5 / 6 / 8 / 10 m from the spine | steepest metre | spine vertices under 0.6 | spine vertices with over 0.1 grass-bearing ground |
|---|---|---|---|---|
| Rift (54) | 0.99 / 0.97 / 0.89 / 0.74 / 0.51 / 0.40 | 0.15 | 0.0% | 0.0% |
| Whiterun (56) | 0.96 / 0.97 / 0.85 / 0.68 / 0.39 / 0.32 | 0.17 | 2.8% | 0.0% |
| Falkreath (100) | 0.91 / 0.85 / 0.73 / 0.61 / 0.49 / 0.49 | 0.12 | 1.4% | 1.1% |
| Hjaalmarch (45) | 0.99 / 0.99 / 0.93 / 0.88 / 0.67 / 0.56 | 0.11 | 0.8% | 1.8% |
| Pale (18) | 0.99 / 0.99 / 0.96 / 0.92 / 0.78 / 0.61 | 0.09 | 0.6% | 1.3% |
| Reach (74) | 0.94 / 0.88 / 0.76 / 0.60 / 0.47 / 0.44 | 0.16 | 0.9% | 1.6% |

Its single steps are hard: within a road's reach the step between two vertices is 0.25 to 0.51 at the median and 1.0
at p90 in every hold (a hard brush; the mesh lies over it). So Skyrim's steps give no limit a road without a mesh can
use; its mean ramp does. BM&V paints its roads in LAND only, with a 2 m edge; the hardest hundredth of BM&V's ground
steps is 0.41 (research nw-02-ground-water-rules.md).

### The limits texcheck holds a road to

| row | limit | from | the old build | ours |
|---|---|---|---|---|
| road weight step, p99 | 0.31 | the steepest metre of any hold's mean ramp (Whiterun, 0.17 a metre) | 0.27 | 0.24 |
| road weight step, max | 0.41 | BM&V's hardest hundredth of ground steps | 1.0 | 0.261 |
| join: step of one road material where the road holds half or more, max | 0.41 | the same | 0.498 | 0.383 |
| spine vertices under 0.6 road weight | 2.8% | Skyrim's worst hold (Whiterun) | 1.58% (1,435) | 0 of 91,050 |
| lowest road weight on a spine | 0.4 | ours (Skyrim has 0.0 in four holds) | 0.0 | 0.972 |
| spine vertices with over 0.1 grass-bearing ground | 1.8% | Skyrim's worst hold (Hjaalmarch) | 42.7% | 0 (most 0.027) |
| road quadrants over six textures | 0 | the shader | 690 | 0 |

The spine is the vertices within 1.5 m of a road's centre line, clear of the ramp by which a road runs out toward
water.

### The rule (`tools/newworld/world/roadpaint.py`)

One rule, laid as it is with no smoothing after it, for the world's roads, a place's paths
(`tools/places/build.py` plan_paths) and the studio (`path_paint.js`, tested against numbers the Python rule wrote):

- The road's weight is 1 on its surface and a straight ramp from 0.97 at 0.45 m inside the surface edge (3.45 m from
  a major spine, 2 m from a minor) to 0 at 8.55 m outside it: 0.108 a metre, between Whiterun's and Falkreath's mean
  ramps. A minor road or a path has the ramp 0.8 as long. It holds 0.97 or more to 3 m from a major spine and 1.6 m
  from a minor one, and no road material grows grass: no grass-bearing ground reaches a spine, by construction.
- The track core is whole on a major spine and falls to nothing over 6.5 m (the same on every class, so a path's
  spine is four fifths track); the verge holds the rest of the road's weight. Two track materials of the road set
  share the core by a noise along the road (60 and 130 samples, each always 15% or more). So a change of material
  along or across a road is a ramp of 0.28 a vertex at most.
- Every road set carries the gravel track, so every quadrant round a road can keep one road material in common
  (section 1). Sets by ground province: marsh (mud, gravel, grassy verge), forest (gravel, mud, grassy verge), upland
  (earth, gravel, pale verge), coast (sand, gravel, pale verge), red clay (mud, gravel, pale verge).
- The distance is measured to the road's line itself (`landcover.py` road_field, within 73 m), not to the samples it
  crosses: 814,278 of the 858,560 vertices within 15 m of a road moved by up to 1.3 m, and a road's ramp runs straight
  at any heading.
- Where a major and a minor road meet, the class blends over about 3 vertices (a flare, not a step). Toward water the
  road is capped by a ramp over the last 8 m of land.

Road materials (mean RGB, luminance, contrast as resolved): BM&V dirtroad01 (81,69,51) 70 / 13.6; TS Tundra02
(112,84,46) 87 / 14.4; TS RiverMud (85,68,47) 70 / 12.7; BM&V Sand06 (91,74,53) 76 / 12.2; TS DirtSnowPath01 (a
trodden earth with grass in it) (88,74,47) 75 / 13.6; TS FieldGrass01 (121,89,58) 94 / 8.8. The old build's skirt,
vanilla `LDirt02`, shows in the NewWorld profile as Tropical Skyrim's `dirt02.dds`: (52,36,23), luminance 39, contrast
9.0, the darkest, flattest ground it painted, either side of every road. KoTM's own road LTEX is luminance 31 and
BM&V's cobble 55 to 59: both darker.

### A place's paths

`plan_paths` paints each quadrant a path reaches whole, on one lattice of vertices shared by every repainted
quadrant: the world's composite, the path over it by the rule, six textures kept (the heaviest at each corner, the
path's, then the heaviest). A texture a quadrant cannot keep fades out over 4 vertices toward it, in it and in its
eight neighbours (repainted too, with what the world paints there), and the path's loss goes to the path's other
textures. Helstrom's 13 committed paths on the old build's ground: 175 quadrants in 56 cells repainted (94 of them
neighbours), none over six textures, and the cells whose navmesh the paths touch are the same 29 as before (a path's
paint reaches 6.8 m, the path itself 96 units beyond its half width). On that ground, 342 of whose quadrants there
still carry seven textures, one vertex is left with no texture its quadrants all keep, and the build lists it as a
problem; ground of six textures a quadrant gives a neighbour nothing to cut.

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
| the old build, worst region (chixathe-mesa) | 42.1 | 90.8 | 42.6 | 92.3 |
| ours, our 20 land regions | 7.5 to 11.0 | 14.3 to 22.2 | 7.8 to 17.3 | 15.1 to 34.2 |

Ours, worst region on all four: skeith-isle, texture p90 11.0 m and p99 22.2 m, grass p90 17.3 m and p99 34.2 m.
Limits: texture p90 12 m and p99 35 m, grass p90 80 m and p99 140 m. The largest share one material holds of any 1 km
of land is 0.29 (marsh_grass; the old build 0.377; limit 0.40).

The old build's material shares wandered only at 30 to 300 m. Ours wander at three scales: that noise; the ground's
moisture, shade and roughness (shore distance, the canopy field, slope and the landcover's micro-relief, `relief.npy`),
each material leaning by its own affinities; and each material's own value noise at 15 and 37 m.

Two rules keep even ground breaking up. Skeith Isle showed why: 47% rocky outcrop on wide open slopes, far from
shore and without canopy, painted with five grounds (gravel, two rocks, rock grass, rocky dark grass) whose
affinities are nearly the same, so the middle scale told them apart least of any region (the spread of the
materials' leanings: 0.12 at its median vertex, 0.25 at the median region's), and with its signature ground, grey
gravel, stacked on the same gravel in its province's rock accent (0.38 of the palette against 0.13 to 0.18 for each
other). Gravel was the dominant ground on 53% of the island's vertices with a run over 14 m, and its texture run was
14.6 m at p90 and 38.7 m at p99. So: a region's signature ground is brought up to 0.2 of a palette and never stacked
on an accent that already gives it that (`texture.signed`); and the small scale's gain rises, by up to 1.0 on 1.8,
as the spread of a palette's materials' leanings falls from 0.25 to nothing.

## 4. Regional variety (weighted Jaccard between land regions' shares)

| | ground, max | ground, mean | grass, max | grass, mean |
|---|---|---|---|---|
| the old build | 0.776 | 0.367 | 0.855 | 0.396 |
| ours | 0.721 (banujha-basin and ultherus-swamp) | 0.262 | 0.692 (kotherra-mangroves and tulmek-washes) | 0.211 |

Ground counts materials by their diffuse; grass splits each material's share over its grass list. Seven ground
provinces (an accent per kind of habitat, a road set, grass lists) and a signature ground and grass list per land
region; 45 base materials and 40 grass variants, 85 land textures, each its own LTEX record.

## 5. Assets

All 85 materials' diffuses and all 152 grass entries' models (60 distinct GRAS records) resolve in the NewWorld
profile through `tools/places/assets/resolve.py`: 63 from King of the Murkmire, 43 from BM&V, 23 from HTBM Cipactli,
20 from Tropical Skyrim, 3 from Depths of Skyrim. Tropical Skyrim holds both a `Meshes/` and a `meshes/` folder; the
resolver follows every spelling of each part of a path, as the game's loader does.

## 6. Form ids

Each material's LTEX holds its form id by the material's id in the registry `newworld/sources/world_formids.json`
(`ltex:<material id>`), and its texture set and grass by the record they are copied from (`copy:<source form key>`).
A new material takes the next id of the ground block (0x010000..0x01FFFF); no other id moves, whatever the order of
`tex/materials.json`. The writer stops when a block is full.
