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
- **Heights back on the ground.** Recast heights are voxel tops (vertex p99 44 units above, max 60 at cs 32); every
  vertex within 64 units of the ground is put back on it (the mean of the quad's two triangulations). After that
  the vertex error is 0 except where a seam split interpolates (max 18).
- **Seams** (`stitch.py`): each cell's open seam edges are split at the neighbour's seam vertices, so both sides
  have the same segments; each pair with both ends within 64 units in height is one Portal link each way. Links
  are symmetric by construction, and the check proves it.
- **Flags:** Water on water triangles (swim), Preferred on the road, Found on all; no cover (the CK computes it;
  ours is none until a cover pass is worth it), no door triangles until places have load doors.
- **NAVI:** our override carries only our NVMI and an empty NVPP (two zero counts): Tamriel's preferred-pathing table
  is vanilla data about vanilla roads, and is not copied (decisions 0003, 0012).
- **FormIDs:** NAVM `0x600000` + the cell's index in the terrain grid (row-major from the grid's south-west cell),
  under the contract's masters (`Skyrim.esm`, then the plugin itself); Mutagen remaps on write.

## Open (owed)

- **In game (L4):** that the engine paths on our NAVI override without vanilla's NVMI (tes4skyrim says the engine
  merges overrides; not measured by us), 0.4 §d's NPC walk, 2.W4's 200 path requests and 20 sandboxers
  (`tests/scenes/nav-claywater.json`, `tests/journeys/nav-*.yaml`).
- **The CK comparison** on the game machine (`infra/gpu-box/navmesh_ck.ps1`, drafted, not run).
- **Placed objects:** collision from the synced masters' NIFs (bhkCompressedMeshShape, as tes4skyrim decodes it),
  door triangles at load doors, then cover.
