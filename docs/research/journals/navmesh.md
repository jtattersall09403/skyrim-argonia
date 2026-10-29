# Journal: the navmesh (chunk 2.W4 §b; 0.4 §d navmesh (b))

What was tried, measured and learned for `tools/navmesh/` and the NAVM/NAVI in ArgoniaWorld.esm, so nothing is lost
at a hand-off. The lane report is `docs/research/2026-10-29/lane-2.W4-navmesh.md`.

## Sources read (layout only; no decompiled code, no retail offsets, decision 0003)

- **xEdit** `Core/wbDefinitionsTES5.pas` and `wbDefinitionsCommon.pas`, branch `dev-4.1.6` (MPL-2.0), fetched
  2026-10-29: `wbNVNM`, `RegisterRecordDef(NAVM)`, `RegisterRecordDef(NAVI)`, `wbNavmeshTriangleFlags`,
  `wbNavmeshCoverFlags`, `wbNavmeshEdgeLinkEnum`. The authority for field order and widths.
- **tes4skyrim** (github.com/bryantmh/tes4skyrim, commit `2abe3ce`, 2026-10-13; licence a README sentence only, so
  read as a spec and no code taken): `tes5_import/navmesh/from_pgrd.py` (the NVNM layout docstring and `pack_nvnm`),
  `edge_links.py` (the 10-byte edge link, the link bits, reciprocity), `navi.py` (NVMI, the NAVI singleton),
  `lookup_grid.py` (the bucket test), `docs/commentary/ck_navmesh_generation.md` (the CK's `[Recast]` defaults, as
  tes4skyrim read them from the CK's own settings; we copy the numbers, not any address).
- **Mutagen 0.54.4**'s own model (reflection over `NavigationMesh`, `NavigationMeshData`, `NavmeshTriangle`,
  `EdgeLink`, `DoorTriangle`, `NavigationMeshInfoMap`, `NavigationMapInfo`): cover triangles are an `IsCover` flag
  per triangle, the lookup grid a raw `MemorySlice`.
- The UESP NAVM/NAVI pages were not needed once xEdit and the vanilla survey agreed.

## What we rely on (all checked against Skyrim.esm, `python -m tools.navmesh vanilla`)

- **NVNM** (one subrecord, little-endian, every array with a u32 count): u32 version 12; u32 CRC "PathingCell"
  0xA5E9A03C; FormID parent world (0 for an interior); exterior s16 grid **Y** then s16 grid X, interior FormID cell;
  vertices (f32 x, y, z, world units); triangles, 16 bytes (u16 v0..v2, s16 edge 0-1, 1-2, 2-0, u16 flags, u16 cover
  flags); edge links, 10 bytes (u32 type, FormID navmesh, s16 triangle); door triangles, 10 bytes (s16 triangle, u32
  CRC "PathingDoor" 0xE48B73F3, FormID door REFR), sorted by (triangle, door); cover triangles (s16); the lookup grid
  (u32 divisor; f32 bucket width, height; f32 min x, y, z, max x, y, z; divisor^2 buckets of u32 count + s16
  triangles, rows from min y). Our codec (`nvnm.py`) decodes then encodes **all 14,447 Skyrim.esm NVNMs byte for byte**.
- **Triangle flags:** bits 0-2 "edge N has an edge link" (the edge field is then an index into the edge links),
  3 Deleted, 4 No Large Creatures, 5 Overlapping, 6 Preferred, 9 Water, 10 Door, 11 Found (on every generated
  triangle). Edge-link types: 0 Portal (the cell seam), 1 Ledge Up, 2 Ledge Down, 3 Enable/Disable Portal.
- **NAVM record:** in Skyrim.esm every NAVM holds NVNM alone (ONAM/PNAM/NNAM unused in Tamriel), compressed
  (flag 0x40000; 2,393 also AutoGen 0x4000000), form version 40. A subrecord over 64 KB needs `XXXX` (none in
  vanilla Tamriel, the largest is 1,296 triangles; ours peak at 32.7 KB on Claywater).
- **NAVI:** the singleton `012FB4:Skyrim.esm` (no EDID; NVER 12; one NVMI per navmesh, 15,462 in Skyrim.esm; NVPP).
  A plugin registers its navmeshes by overriding it (tes4skyrim's finding: a NAVM not in the NAVI is ignored).
  NVMI: FormID navmesh; u32 flags (0x20 is island, 0x40 not edited); f32 x, y, z approx location; f32 preferred %;
  edge-link navmeshes, preferred edge-link navmeshes, door links (CRC, door); u8 has-island-data (+ island data);
  pathing cell (CRC, world, grid Y, grid X | cell).
- **Vanilla rules the stitch copies, measured:** the lookup-grid divisor is 1 under 17 triangles, 2 under 50, then
  `t // 50 + 2` capped at 12 (12,817 of 12,817 Tamriel NAVMs; tes4skyrim's span rule fits 2,721); the NVMI location
  is the vertex mean (12,815 of 12,817); its edge links plus preferred edge links are exactly the NVNM's neighbour
  navmeshes (12,817 of 12,817); preferred % is the share of Preferred triangles; every triangle is counter-clockwise
  seen from above (2,255,847 of 2,256,166; the rest are degenerate); 293,572 triangles are Water and lie **on the
  bed** (median 126 units under XCLW, 99 % within 953, deepest 1,373).
- **The production write path is proven:** 20 Tamriel NAVMs (17 with edge links, 5 water, 7 Preferred, 5 door
  triangles, 16 cover, up to 1,257 triangles) through `NavmeshRecords.Parse` (Mutagen's parser with the contract's
  masters) and Mutagen's writer come back **byte-identical in NVNM and in every subrecord**, compressed.

## The method (`tools/navmesh`)

- **Inputs** (`inputs.py`): the game's ground (`terrain/build.game_heights_m`: quantised, limited, regraded) in
  units; the water surface over a sample (the WRLD default 0, the cell's XCLW, then every water plane's footprint
  from `out/water/cells.jsonl`); the painted road (`routes/paint.py`). Placed-object collision has an interface
  (`ObjectSource`) and raises until the masters' meshes are synced.
- **Recast** (`ArgoniaNav`, DotRecast 2026.3.1, zlib): per cell, the ground with a 2-sample border as two triangles
  per quad; area per triangle: water (every corner under water, depth <= 1,000 units, else no navmesh), road (any
  corner painted: walkable whatever its grade), ground (slope <= 45 degrees). The CK's `[Recast]` defaults: agent
  height 128, radius 32, climb 32, slope 45, edge 512 long, error 1.3 voxels, regions 50/20, voxel height 8.
- **The voxel width is 16, not 32.** Recast's ledge filter refuses a span whose reachable neighbours differ by more
  than the climb, a slope cut of atan(climb / 2 cs): 26.6 degrees at 32, which dropped 42 % of the walkable dry
  ground on Claywater; 45 degrees at 16, the walkable angle. Cost: 4x the voxels (120 ms a cell on one core).
- **Heights back on the ground.** Recast heights are voxel tops (vertex p99 44 units above, max 60 at cs 32), and at
  a cliff edge the detail mesh takes a vertex's height from the column beside it: on the province, at a snap limit
  of 64, 57 vertices were left 65-208 units above the ground (20 of them in water polygons), which failed the
  heights check. The ground is the only collision so far, so every vertex is ground: the limit is 256, and every
  vertex goes back on the ground (the mean of the quad's two triangulations). Afterwards the vertex error is 0
  except where a seam split interpolates (max 13.6 on the boxes re-measured). Placed objects, when they join, will
  be told apart by their source, not by this distance.
- **No zero-area triangles.** Recast's detail mesh leaves slivers along long polygon edges, where a corner lies
  within half a unit of the opposite edge in plan. When that edge was open, the T-junction repair split it at the
  sliver's own corner, which made a zero-area triangle pair: 7 in the province's 4,299,037 (6 with a repeated
  corner, 1 with three corners on one line, in cells (-55,56), (28,-18) and (-15,-51)). They showed up as the
  heights check's `invalid value in divide`, a zero-length normal. Fix (`stitch.drop_slivers`, before the repair):
  remove every triangle with a corner on its opposite edge in plan, so the repair splits the neighbours' edges at
  that corner. The split also never uses the triangle's own corner, and uses each point once. The L1 check
  `degenerate` (a repeated corner, or zero plan area) is in `green`. It failed on the pre-fix province (7) and
  passes on the rebuilt boxes and Claywater (8 slivers dropped there, 0 degenerate).
- **Voxel width, measured on Claywater** (walkable dry ground, by ground slope; L1 `coverage`):

  | cs | under 30 deg | 30-40 | 40-45 | all walkable | road | islands (over 100 m2) | main m2 |
  |---|---|---|---|---|---|---|---|
  | 16 (production) | 97.6 % | 77.5 % | 23.7 % | 83.2 % | 97.5 % | 113 (21) | 154,363 |
  | 32 | 89.2 % | 7.1 % | 0.1 % | 58.3 % | 91.4 % | 232 (52) | 73,818 |

- **Seams** (`stitch.py`): each cell's open seam edges are split at the neighbour's seam vertices, so both sides
  have the same segments; each pair with both ends within 64 units in height is one Portal link each way. Links
  are symmetric by construction, and the check proves it.
- **Flags:** Water on water triangles (swim), Preferred on the road, Found on all; no cover (the CK computes it;
  ours is none until a cover pass is worth it), no door triangles until places have load doors.
- **NAVI:** our override carries only our NVMI and an empty NVPP (two zero counts): Tamriel's preferred-pathing table
  is vanilla data about vanilla roads, and is not copied (decisions 0003, 0012).
- **FormIDs:** NAVM `0x600000` + the cell's index in the terrain grid (row-major from the grid's south-west cell),
  under the contract's masters (`Skyrim.esm`, then the plugin itself); Mutagen remaps on write.

- **Claywater's islands are real unreachable ground.** The block has 113 islands, 21 of them over 100 m2 (105 to
  924 m2). All 21 are dry: 0 % water and 0 % road. None can be a roof, because the ground is the only collision so
  far. All lie on the block's mountain rows (cells y 8-9 and 14-15, z 4,500-12,200 units). On the whole-province
  build, none of the 21 joins the province's main component (33.3 M m2). Nine are larger there, because they run
  on past the block's edge (the largest, at (-59, 8), is 67,470 m2). In a 2,048-unit square around each one,
  31-81 % of the ground is steeper than 45 degrees (max 55-72), with 1.9-3.2 thousand units of relief: they are
  shelves cut off by slopes the agent cannot walk. Claywater Station itself (-232,874, 47,914; cell -57, 11) is on
  the main component (the nearest triangle is 85 units away). No fix is needed. Whether the engine should get
  Ledge links down off them is a question for the CK comparison.

- **The province (12,083 cells, L1 green):** 4,298,892 triangles; degenerate 0; heights over 0; links 303,494, all
  symmetric; NAVI 12,083 entries; road 98.4 %; walkable coverage 98.8 / 72.1 / 19.2 % (under 30, 30-40, 40-45 deg);
  7,416 islands against a main component of 33.3 M m2. The build takes about 21-30 min at a peak of 857 MB (Recast
  about 17 min on 4 threads). The sha256 `31e0537c…` is the same on a 4-thread and a 2-thread build. `make navmesh`
  takes 26:37 at a peak of 1.56 GB (the plugin write), and ArgoniaWorld.esm is 195.6 MB with every NVNM
  byte-identical.

## Open (owed)

- **In game (L4):** that the engine paths on our NAVI override without vanilla's NVMI (tes4skyrim says the engine
  merges overrides; not measured by us), 0.4 §d's NPC walk, 2.W4's 200 path requests and 20 sandboxers
  (`tests/scenes/nav-claywater.json`, `tests/journeys/nav-*.yaml`).
- **The CK comparison** on the game machine (`infra/gpu-box/navmesh_ck.ps1`, drafted, not run).
- **Placed objects:** collision from the synced masters' NIFs (bhkCompressedMeshShape, as tes4skyrim decodes it),
  door triangles at load doors, then cover.
