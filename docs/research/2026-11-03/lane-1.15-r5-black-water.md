# Lane 1.15-r5-black-water: the black type is black

L1 lane, 2026-11-03. In game (round 5 rest batch, 02-water-types-1, read by a reader): black swamp read grey-green olive with dark blotches; the sea turquoise with dark smoky blotches and faint pink-lilac glints. Owner wants black water against green marsh water (owner-brief 2026-11-03 09:23).

## (1) Measured: every WATR in the load order (bytes, `tools/argonia_world/water/layer.py` top_group over Skyrim, Update, Dawnguard, Dragonborn, ccBGSSSE025, evgSIRENROOT, Tropical Skyrim, King of the Murkmire; Black Marsh.esm, HTBM, Tropical Birds and Depths of Skyrim carry no WATR; 106 records)
DNAM floats (228/232-byte layout): colours at bytes 40/44/48 (shallow/deep/reflection), 16 sun specular power, 20 reflectivity, 24 fresnel, 32/36 fog above near/far; opacity is ANAM (not DNAM). Dark records, winner per editor id, deep-colour luminance L:
| record (winner) | shallow / deep / reflection | ANAM opacity | fog above | refl / fresnel / spec |
|---|---|---|---|---|
| Shadowmere, Apocrypha, Lava, Blood | 0..69 / 0..12 | 50 | 0..40 | not natural water |
| **Update.esm MurkyWater** (L 9) | 26,19,19 / 9,9,6 / 32,35,27 | 100 | 0 - 60 | 0.55 / 0.25 / 3838 |
| Dawnguard DLC01DarkFallCaveDarkStillWater (L 12) | 31,33,33 / 12,12,12 / 10,10,5 | 75 | 0 - 30 | 0.28 / 0.00 / 1373 |
| Puddle, Int water | 11,13,12 / 11,15,15, opacity 0 | 0 | 0 - 10 | puddles/interiors |
| Skyrim DefaultWater (Skyrim.esm, overridden) | 37,52,37 / 5,16,5 / 103,122,117 | 30 | 0 - 110 | 1.0 / 0.05 / 1021 |
| Tropical DefaultMarshWater (our green marsh) | 56,53,37 / 77,61,36 / 113,91,51 | 30 | 0 - 110 | 0.23 / 0.05 / 1021 |
| KotM DefaultBlackmarshWater (was our black) | 130,116,34 / 61,95,52 / 97,130,72 | 30 | 0 - 110 | 1.00 / 0.05 / 1021 |
| Tropical DefaultWater (sea) | 81,174,165 / 28,104,140 / 103,122,117 | 30 | -100 - 580 | 0.50 / 0.05 / 1021 |
KotM's "black" record is the brightest dark-named water in the stack (shallow luminance 111, deeper than the green marsh's 52). That is the cause of the grey-green olive read: it is lighter than the marsh type beside it, not darker.

## (2) The black type
Winner: Update.esm MurkyWater (Skyrim.esm's copy is byte-equal): the darkest natural open water in the load order, near-opaque (ANAM 100), fog 0-60 (shorter than the marsh's 110), a brown tint (26,19,19 / 9,9,6 is black-brown, not green). Dawnguard's dark cave water is darker in reflectivity (0.28) but is a cave record with a Dawnguard image space; MurkyWater is the open-air one. No authored DNAM was needed: no number of ours.
Delta, ARG_WATR_black from KotM DefaultBlackmarshWater (08184260) to MurkyWater: shallow 130,116,34 to 26,19,19; deep 61,95,52 to 9,9,6; reflection 97,130,72 to 32,35,27; opacity 30 to 100; fog far 110 to 60; reflectivity 1.00 to 0.55; fresnel 0.05 to 0.25; specular 1021 to 3838. Sea stays Tropical's DefaultWater. Cell keys and FormIDs are unchanged (the type id is by position), so the plugin YAML does not change (the WATR live in ArgoniaWorld.esm, which is generated; `git diff plugin/` is empty).
Lore (0032): world/sources/lore/black-marsh-province.md:73 and topics/fauna-hazards.md:60 name the peat bogs (the Great Burn, peat fire); no lore file gives a water colour. "Black = swamp and marsh-fringe, tannin-dark" stays EXTRAPOLATED, as the water-types lane flagged.
Vanilla gate (0012): the WATR copy is a body, written as our own record; the planner's L4 still is the review.

## (3) The blotching: measured candidates (nothing proven in game)
- Records. All 106 WATR use the one noise map DefaultWater.dds x3; the sea, the green marsh and KotM's black differ in the noise only by wind speeds (0.017/0.013/0.096 vs 0.007 x3), so the records do not make the sea blotchy and the marsh not.
- Tropical lays its own `textures/water/defaultwater.dds` (1024x1024 DXT1, 699,192 bytes, mips) over the BSA's (2,431,549 bytes), for every WATR; this is the noise normal map of every type. A different map from vanilla's is a candidate; header of the vanilla file not decoded here.
- Community Shaders 1.9.1 (stack copy ~/.argonia/stack/MO2/mods/community-shaders): `data/dependencies.json` carries no water setting and no Argonia override for any water feature (only height fog, volumetric lighting, cloud and terrain shadows, terrain shadows, grass lighting), so every CS water feature is at its compiled default; defaults are in CommunityShaders.dll, not readable as text here. Features present with ini: WaterEffects 1-2-1 (no settings in the translation table; caustics and parallax compiled in), UnifiedWater 0-2-0 beta (replaces distant water tiles), DynamicCubemaps 2-5-0 (has "Enable Screen Space Reflections on Water", on by default).
  - WaterEffects caustics (`Shaders/WaterEffects/WaterCaustics.hlsli`, applied in `Lighting.hlsl:2179` as `dirLightColor *= ComputeCaustics`): min of two panning samples x4, multiplies the sun on anything under water, 0 to 4x. This is a moving bright and dark lattice on a visible bed. The black type is now opaque (ANAM 100) so its bed is hidden; the sea's (ANAM 30) is not.
  - Water SSR reflects dark screen content (trees, shadow) into the surface: "dark smoky blotches". The pink-lilac glints are not in any WATR colour (all reflection colours are green/teal/olive); the sky/cubemap tint of the weather is the candidate.
- Not set: no record or stack byte is proven the cause, and a CS switch is a stack change that needs its own L4 proof (CLAUDE: no tuning for feel without measure). Planner's A/B for the water journey: drop `Shaders/Features/WaterEffects.ini` (CS switches a feature off without its ini, see the height-fog row) on one batch; and compare a still with DynamicCubemaps SSR off.

## Tests
`water/tests/test_water_writer.py` (skipped if ArgoniaGen or game data absent): black winner is Update.esm; the written black WATR has the shallow, deep and reflection bytes, ANAM 100, fog 0/60, reflectivity 0.55 and fresnel 0.25 above; every WATR is still byte-equal to its winner.
