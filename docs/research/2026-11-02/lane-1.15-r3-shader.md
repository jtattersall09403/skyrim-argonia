# Lane 1.15-r3-shader: the lavender surfaces come from Black Marsh.esm's alternate texture sets

Build 252db64, files only (no game machine). Inputs: [machine diagnosis](lane-1.15-r3-machine.md) §1,
[round 2](round-2.md). Readers were throwaway scripts over the local MO2 mirror `~/.argonia/stack/MO2/mods`, the 23
vanilla BSAs in `~/games/skyrimse/Data`, and `out/ArgoniaWorld.esm` and `out/Argonia.esm` as built at 04:49.

## 1. Cause: MODS overrides the NIF's texture slots, and the TXST diffuses it names are absent

- A STAT or TREE record's **MODS** field holds alternate texture sets. Each one maps a NIF shape to a TXST, and the
  TXST's TX00 replaces the shape's diffuse. `data/mesh-textures.json` and §1 of the machine diagnosis read only the
  NIF slots, so they never saw these TXSTs.
- In Black Marsh.esm, 228 of 435 STAT/TREE/ACTI/MSTT records carry MODS, and 203 of those name a TX00 diffuse that
  is in no local source. That is 57 distinct files, searched in BM&V's loose files, every mod BSA and all 23 vanilla
  BSAs. Examples: `vurt_*` (Vurt's Flora), `2014sabercatletextures\*`, `witcher2\*`, `architecture\7db7b43b.dds`.
  King of the Murkmire's 902 MODS users resolve, with one exception.
- **ArgoniaWorld.esm places 155,958 refs of 14 such bases.** Each base below is followed by its ref count and the
  diffuse its TXST names:

| Base (Black Marsh.esm) | Refs | Mesh | Missing TXST diffuse |
|---|---|---|---|
| 17BD20 01tROPICAL2 | 52,372 | TropicalPlant01.nif | landscape\plants\TropicalPlant01.dds |
| 196181 01largefern | 50,856 | FernLarge03.nif | landscape\plants\ferny.dds |
| 17BD15 01mossDUPLICATE001 | 20,485 | florahangingmoss02aaa.nif | landscape\plants\vurt_spmoss021.dds |
| 1B32DC 01cypressmoss | 8,722 | cypress1.nif | vurt_bcmossbark01.dds |
| 0AA5F4 01fortFlower | 8,216 | vvardenfell\stronghold\fort00.nif | architecture\jg\jgayleidleaftrim.dds |
| 17BCFD 01TROPICAL11 | 7,323 | ESalixshrub03.nif | landscape\plants\TropicalShrub05.dds |
| 0D85BB 01mushroomDUPLICATE001 | 4,629 | vurt_treeWigs.nif | landscape\trees\abark2.dds |
| 1DE971, 1DE977, 1B32D4, 1B32E0, 1B32CE, 1B32E4, 1D3CC3 | 3,355 | rocks, mushrooms, cypress, oak | sheomud01, Bark0005, vurtdeadbark, EPineBark06Snow, ... |

- These match the round-2 lavender: trunks (cypress, vurt dead trees), ruin walls (fort00 with the jgayleid
  trim), rock stacks, and the plants. Skyrim draws a missing diffuse as its missing-texture lavender.
- **The blue moss** is 17BD15. Its TXST `MOSS` (BM 0x17BCFE) names `vurt_spmoss021.dds` and no normal map. Its NIF
  shader also has Own_Emit (SLSF1 bit 22) with emissive colour (0, 0.73, 1.0) × 1.5, which is the only coloured
  emissive among BM&V's 147 lighting shaders. That gives a missing diffuse plus a cyan self-glow, so the moss draws
  saturated blue. The olive `ReachGrassObj01.dds` that the NIF names is never drawn.
- **Caveat:** "absent" means absent from the local mirror and vanilla. The machine could hold a loose copy that the
  mirror lacks. The A/B in §3 settles this.
- **FernLarge03 cannot be the correct control.** Its NIF (ferny3.dds) is clean, but 01largefern's MODS swaps in the
  missing `ferny.dds`.

## 2. Candidates ruled out from the files

- (a) Vertex colours. Of BM&V's and Mud Mother Grove's 305 BSTriShapes, none sets SLSF2 Vertex_Colors without
  colour data. 14 shapes carry colours with the flag off, which is harmless. No shape's mean vertex colour is tinted
  blue or purple (a mean that far from grey would have been reported).
- (c) Slot order. Every NIF diffuse slot and every TXST TX00 is a diffuse path, and none is an `_n` map. The one odd
  diffuse is `rockl01.nif` → `effects\fxbird03.dds`, mean (60,55,103), which is not placed.
- (b) Community Shaders. The laid features are the 27 `Shaders/Features/*.ini`. Our overrides are CloudShadows,
  ExponentialHeightFog, GrassLighting (SSS 1.0, gloss 20, specular 0.3), TerrainShadows and VolumetricLighting. None
  of them touches texture lookup, and no BM&V shader uses TruePBR or parallax types (all are type 0). CS cannot
  create lavender from a resolved diffuse. Only the Own_Emit glow on the moss is shader-side, and that is vanilla
  behaviour.

## 3. A/B for the round-3 driver (one vantage: flooded-forest-shore, -3666,24998, 12:00, `sw ARG_Weather_clear_dry`)

Use the same camera for all four stills (setpos then `tfc` frozen, with the blue moss 0FA56A27 in frame). Confirm
each still before moving on.

1. A: the deployed build. Expect lavender plants and a blue moss.
2. B: rename `CommunityShaders.dll` off and restart. If the colours are unchanged, the cause is not CS.
3. C: CS on, `Argonia_*.json` overrides removed. If the colours are unchanged, the cause is not our overrides.
4. D, the decisive still: CS on, with the 57 diffuses resolved. Either drop one placeholder copy at
   `Data\textures\landscape\plants\vurt_spmoss021.dds` and `ferny.dds` (a copy of the NIF's own diffuse, machine
   only, never committed), or `disable` the ref and `placeatme` the NIF-only twin. If the moss turns olive and the
   fern green, the TXST cause is proved.
   Also list `Data\textures\landscape\plants\vurt_spmoss021.dds` and `ferny.dds` on the machine (`dir`) before step 1.

## 4. Fix at source (not made here: it belongs to the textures and placer lanes)

1. `tools/argonia_world/vegetation/mesh_textures.py` (textures lane): follow each placed base's MODS to its TXSTs and
   check TX00/TX01 like a NIF slot. This L1 check would have failed on all 14 bases.
2. Pick one remedy per base: source the missing textures (Vurt's Flora and the other packs named, recorded in the
   sourcing register), or have ArgoniaGen write an override of the base with MODS dropped, so the NIF's own resolved
   diffuse draws. That is native data with no mod file changed (0026). The moss also needs Own_Emit cleared, or the
   base dropped from the palette, unless the glow is wanted.
3. Re-shoot 04, 16 and 20 after the fix.
