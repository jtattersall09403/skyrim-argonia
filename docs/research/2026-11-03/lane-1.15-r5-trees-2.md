# Lane 1.15-r5-trees-2: red leaves back, the neon and washed-out trees named and dropped

Owner ruling (#37, 2026-11-03 11:54): red or pink leaves are fine if they look reasonable. The faults are "artificial looking neon bluey green" trees and "strangely pale washed out wide trunk trees that looked like they weren't rendering properly". This lane is L1 only; the L4 check is owed.

## 1. The crimson drop reversed (lane 1.15-r5-crimson, 8a9bc8f0)
- `lists.usable` no longer drops a form for a red vertex shape. `leaf_hue.problems` (run by `textures check` in make check) counts only red leaf diffuses. The new `leaf_hue.vertex_report` makes the vertex measure a report line in `textures check`, not a red. `hue build-nif` and data/leaf-hue.json are unchanged.
- Lists rebuilt: land_region_object went from 1399 to 1493 rows and placed forms from 210 to 219. All 9 forms are back: Erut 155FE5/E7/E8/E9/EA/EC/ED (5, 8, 4, 1, 1, 7, 4 rows) and SwampPlant02A/B 3A3FA3/A4 (4, 8). The red-diffuse drop for ground flora (lane r4-red-trees: meadowsweet 04, rose lake plant) is kept.
- The delta cypress family (542aa868) and the deep-sink figure (34400f80, MARSH_TREE_HA_REGION 127) are untouched.

## 2. Neon blue-green: named
Reader on the owner's seven stills: the teal is one tree type, "a tall slender bamboo/cane-stemmed tree with feathery needle-like frond clusters". It shows in stills 1, 3 and 4, and only the leaves are teal: the stems are normal green. The colour is flat, not glowing. The round-5 desktop stills show no teal, only lime palm fronds in sun (an ordinary lit diffuse, hue 89, sat 0.49).

I read each placed flora mesh's BSLightingShaderProperty from the laid stack: 181 meshes (scratch parser; the flags, emissive, lighting effect 1 and texture set of each). The results:
- **ArgoniaTreeBambooCluster01 (7FD0F3, King of the Murkmire)** is the owner's tree: a cane stem with a frond leaf, placed only in flooded-forest (6 rows).
  - Leaf shape: tree03.dds (hue 98, sat 0.54), soft lighting on with lighting effect 1 = 5.0, but texture slot 2 (the soft-light map) is empty. It also carries Own_Emit at grey 0.47, vertex colour on, and double-sided.
  - Stem shape: tree04.dds, no soft lighting, and it reads normal. This matches the reader: leaves teal, stems green.
  - Of the 14 KotM soft-lit shapes with an empty slot 2, this is the only leaf that is also emissive. The cypress branches named in round 4 have slot 2 set to their diffuse.
- **01kelpcluser (0D85C2, BM&V)**, aquatic, placed in tidal-delta (6 rows): Own_Emit cyan (0.08, 0.62, 0.62) on an orange-olive diffuse (coastkelpgrass01, hue 43, sat 0.83), soft-lit 3.0. That is a literal cyan self-glow, the likely source of the round-5 "teal/neon green fleck".
- Other emissive placed meshes: the Erut leaves (grey 0.47, a red tint the owner now allows), swampplant08 (white 1.0), histgland (orange, the Hist's light; lore), and the blue and green tiny mushrooms (lucan-mold glow, lore loading-facts.json:896). None of these is teal foliage, so they are kept.

## 3. Pale wide trunk: named
The reader found two huge buttressed, flared trunks in owner stills 1, 2 and 6, pale grey-beige with green moss, textured, and not a billboard. Round 5 shows the same (rootland 28, flooded 16, frontier 36). I compared the bark diffuse means of the placed canopy forms; the bark median luminance is 59 (bald cypress 50, erut/willow 60, hist crackedbark 59, jungle trunk2 36).
- **ctq_kapoktree01-05 (463246-46324A, KotM)**: kapok bark diffuse luminance 132 at saturation 0.19, more than twice the median. The normal map resolves (ctq_kapokbark_n). There is no spec flag, gloss is 20, and the vertex colour is white (255, or 225 on 05). That is a buttressed wide trunk that reads pale and flat. 51 rows: rootland, deep-sink, tidal-delta, coastal-lagoon, interior-swamp, deep-river.
- **RainforestTree01/02 (0EB91F, 0EB921, KotM)**: the bark (snowgumbark01_d, luminance 91) has soft lighting and double-sided on with no soft-light map, so the sun wraps through the trunk and washes it out. 21 rows.
- Textures: no placed tree has a texture absent from the stack. The only unresolved paths are two GV grass meshes with an absolute `d:/steamlibrary/...` path (cattail, tallgrass01), and those are not trees. One mesh lacks a normal map: eruttree03tall's bark, whose normal sits in slot 2 instead.
- The "dissolving" pale tree at the right of round-5 still 36 is the engine's 3D tree fade dither at the LOD switch (fTreesMidLODSwitchDist), not a form fault. Nothing changed for it; the L4 still at the fade distance reads it.

## 4. Fix
No install-time NIF patcher exists yet (installer/ has only the manifest steps), so a shader rewrite (filling slot 2, clearing Own_Emit or soft lighting, darkening via vertex colour) has nowhere to run. Each cause is in the form's own mesh, so per 0010 the data route drops the form: `lists.LOOK_DROP` lists 9 forms, each with its measured reason. Bamboo stays lore-grounded (topics/fauna-hazards.md:95, lilmoth.md:49) for when a patcher can restore it; KotM's Bamboo01/02 (no soft lighting) are gallery forms with no placement today.
- Lists: land_region_object went from 1493 to 1399 rows (the regions draw other forms) and placed forms from 219 to 210. `textures check` reports 0 problems, and 45 vegetation tests pass.
- Province check (`vegetation build` + `check` against out/terrain/land): **18 green, 0 red, 647,783 refs**.

| class (trees a countable cell) | band | | class | band | |
|---|---|---|---|---|---|
| dunmer-north.coastal-lagoon | 9-27 | 26.7 | imperial-penal-south.flooded-forest | 15.5-46.5 | 30.7 |
| dunmer-north.deep-sink-basin | 9-27 | 21.6 | imperial-penal-south.interior-swamp | 15.5-46.5 | 32.3 |
| dunmer-north.interior-swamp | 15.5-46.5 | 20.8 | mercantile-coast.coastal-lagoon | 9-27 | 21.9 |
| dunmer-north.northern-transition | 2.5-15 | 5.8 | mercantile-coast.deep-sink-basin | 9-27 | 26.0 |
| hist-heartland.coastal-lagoon | 9-27 | 21.6 | mercantile-coast.flooded-forest | 15.5-46.5 | 24.5 |
| hist-heartland.deep-sink-basin | 9-27 | 24.3 | mercantile-coast.interior-swamp | 15.5-46.5 | 31.3 |
| hist-heartland.flooded-forest | 15.5-46.5 | 26.9 | mercantile-coast.western-frontier | 2.5-15 | 8.4 |
| hist-heartland.interior-swamp | 15.5-46.5 | 34.7 | naga-kur-deeps.deep-sink-basin | 9-27 | 26.3 |
| hist-heartland.rootland | 15.5-46.5 | 25.3 | naga-kur-deeps.flooded-forest | 15.5-46.5 | 28.2 |
| hist-heartland.tidal-delta | 9-27 | 9.3 | naga-kur-deeps.interior-swamp | 15.5-46.5 | 32.2 |
| hist-heartland.western-frontier | 2.5-15 | 7.7 | naga-kur-deeps.rootland | 15.5-46.5 | 27.2 |
| imperial-fringe.deep-sink-basin | 9-27 | 16.2 | pirate-freeholds.coastal-lagoon | 9-27 | 16.0 |
| imperial-fringe.rootland | 15.5-46.5 | 23.3 | pirate-freeholds.deep-sink-basin | 9-27 | 21.0 |
| imperial-fringe.western-frontier | 2.5-15 | 6.2 | pirate-freeholds.flooded-forest | 15.5-46.5 | 25.1 |
| imperial-penal-south.coastal-lagoon | 9-27 | 15.0 | pirate-freeholds.western-frontier | 2.5-15 | 4.9 |
| imperial-penal-south.deep-river-corridor | 15.5-46.5 | 22.9 | saxhleel-coast.coastal-lagoon | 9-27 | 19.5 |
| imperial-penal-south.deep-sink-basin | 9-27 | 25.5 | saxhleel-coast.deep-sink-basin / flooded-forest / interior-swamp / tidal-delta | | 23.3 / 26.1 / 32.8 / 15.0 |

## Owed (checks.md rows)
- `tree-look` (L4): after the planner's next terrain/vegetation build and ESM. Take one still per affected class (flooded-forest where the bamboo stood, rootland and deep-sink where the kapok stood, interior-swamp where the rainforest trees stood, tidal-delta where the kelp stood), near and at the fade distance. A reader checks for "no neon blue-green or teal foliage, no pale washed-out wide trunk"; Erut canopies may read red.
- A later patcher lane: an install-time NIF shader patch (0014) could restore the bamboo (fill slot 2 with the diffuse, clear Own_Emit) and the rainforest bark (clear soft lighting). That is the planner's call.
