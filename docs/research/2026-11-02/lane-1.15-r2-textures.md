# Lane 1.15-r2-textures: round 1's missing-texture look

Input: [round 1](../2026-11-01/round-1.md) session 1b stills (world panel `out/batch/adhoc/20261102T011213/`,
creature spots `20261102T005956/`). Code: `tools/argonia_world/vegetation/mesh_textures.py` (manifest and L1
check), `lists.usable` (drops untextured meshes), `tools/ArgoniaGen/WaterRecords.cs` (WATR template).

## Method (measured 2026-11-02)

- The laid stack is the local MO2 mirror (`~/.argonia/stack/MO2/mods`, what stack.py pushes) plus the vanilla
  BSAs. Each non-vanilla object_form mesh (398) was read from its loose file or its row's BSA (lz4) and every
  BSShaderTextureSet slot was resolved against every row's loose files and BSAs. All 229 placed meshes are SSE
  (bsver 100). Every resolved DDS is DXT1/3/5, BC7 or raw 32-bit, so none fails on its format.
- The BM&V vault archives (Data1.rar, Data2.rar inside `vault-bmv.tar`, ranged GETs, listed with `unrar lb`, 47,592
  entries, deleted after the listing) show which missing textures BM&V never shipped at that path.

## Findings

1. **Vegetation and rocks (mesh textures).** 41 referenced textures resolve from no row: bmv 33, King of the
   Murkmire 1, Mud Mother Grove 4 (absolute `D:\...\Data\textures\` paths: the engine reads from after `Data\`,
   so they resolve once normalised that way), plus the truncated `textures\NOR` normal strings in BM&V's kelp and
   coral and Depths of Skyrim's corals. Only one is in an archive: `textures/landscape/trees/kahl lod_n.dds`
   is in BM&V, named by KotM's violet lilies, and keep_subset drops it because no *kept BM&V* mesh names it. Every
   other one is absent from BM&V itself (paths the author never fixed: `g:\berkians folder\...`,
   `plants\grplants2\leafcol.dds`, `morrowind\landscape\azuracoast\rocks\az_rock01.dds`, the TR mushroom textures).
   Missing **diffuse** (white or lavender in game) on 9 placed meshes: bigshrub(colorful) (01giantmushroommultiple),
   ESeaBuckThorn05Sp, tr_oth_tallmush01 and 05, az_rock02 and 09, rock_28, and the round-1 pale rocks. Missing
   normals or glow only: 20 textures on Vurt and TR mushrooms, palms and gorse. These keep their diffuse and are
   waived by name.
2. **Ground.** All 19 TXST diffuses (`TEXTUREPACK\landscape\*.dds`) are laid under the keep glob
   `textures/texturepack/landscape/*`, at the exact case and folder. They are 512² DXT3 with **no mipmaps** and
   BM&V ships no normals. The ground's textures resolve, so the white upland slope (creature spots
   06-upland-night) is not a missing ground texture. Its smooth sheen matches the bare water (3) on a slope seen
   at night, or LOD. This stays with the ground lane until re-measured after (3).
3. **Water.** Our four WATR types were built bare: no NNAM noise textures and DNAM zero except colours and fog.
   Skyrim.esm's DefaultWater (0x18, and every vanilla type) carries three NNAM `Water\DefaultWater.dds` layers and 57
   DNAM floats: sun specular 1021, fresnel, noise scales, winds, displacement. BM&V has no WATR. A bare WATR has no
   normals to shade and draws flat opaque white, which explains stills 08, 09, 24 and 29.
4. **Black voids.** Still 07's black block is bounded by the bank's waterline with the plants' silhouettes on top.
   It is the water plane under the camera, from the same bare WATR. Stills 23 and 35 and the strip's 07:30
   rectangle could not be tied to a ref from the stills. Re-measure them after the water fix. No placed mesh is
   missing a model: the three unkept az rocks (0C0001-3) are not in any list.

## Fixes

- `data/dependencies.json` bmv keep: `+ textures/landscape/trees/kahl lod_n.dds`. The lists rebuild also adds the
  BM&V meshes that the freed list slots now pick.
- `lists.usable` skips a mesh with a slot-0 texture that no row lays, and a mesh that no build has read yet.
  The lists were rebuilt: `land_region_object` and `vegetation_form` changed, and nine meshes left the palette.
- `WaterRecords.cs`: each WATR is DefaultWater duplicated (`template: Skyrim.esm:DefaultWater` from layer.py),
  then our name, opacity, colours and fog are applied. `test_water_writer` asserts the 3 NNAM layers and the sun
  specular.
- The L1 check `python -m tools.argonia_world.vegetation textures check` runs in `make world` from
  `data/mesh-textures.json`, which holds paths only and is built machine-local by `textures build` after a stack
  change. It fails when a placed form's mesh is not in the manifest, a keep row's placed mesh is outside its globs,
  or a texture has no source and no keep glob (a diffuse is never waived). Result after rebasing on main: 243 placed forms, 0 problems.

## Next deploy must re-lay

bmv (new keep: kahl lod_n and the newly picked meshes), then ArgoniaWorld.esm (WATR) and Argonia.esm (lists).
Then re-shoot panel vantages 06-09, 14-19, 24, 29, 30-33 and the upland-night spot.
