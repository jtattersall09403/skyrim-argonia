# Lane 1.15-r6-mesh-patcher: the oddly coloured trees fixed at the mesh, never dropped

Owner #37, 2026-11-04 07:36: find the cause and fix it, never drop. The causes were measured in round 5 (lane-1.15-r5-trees-2, lane-1.15-r5-white-trunks). This lane fixes them at the mesh with an install-time patcher (0010 route 5; 0014: a derived file made from the player's own mods). L1 is the bytes before and after, L2 is the patcher tests. L4 is owed to the planner's batch.

## 1. The patcher
- `tools/argonia_world/meshes/` holds the patcher code:
  - `nif.py`: a Skyrim SE NIF read into blocks and written back byte-exact. An unedited `to_bytes()` equals the input. It reads BSLightingShaderProperty flags, emissive, slots and the soft-lighting wrap, plus BSTriShape positions, half-float UVs, vertex colours, triangles, UV islands and the UV-stretch measure.
  - `source.py`: finds a mod's mesh loose or in its BSA, with a pure-Python LZ4 frame decoder (the build VM has no lz4 wheel).
  - `patch.py`: the ops and the bars.
  - `__main__.py`: `patch --check | --out DIR | --list`.
- `data/mesh-patches.yaml` is data only: 13 meshes. Each lists every shape with its kind, and each shape with ops carries its measured `before` (the patch fails if the mod's bytes change) and its reason.
- The ops are clear_flags, set_flags, emissive, texture_slot and uv_scale. uv_scale's `fit` mode works per UV island and scales V about the island's own minimum, so the half floats stay small.
- The bars apply to every shape of a patched mesh:
  - a soft-lit shape has a slot-2 map;
  - no shape is Own_Emit unless the entry cites the lore (`lore_emit`);
  - a bark shape has a normal and a median UV stretch of 6:1 or less.

## 2. Ops and numbers (`patch --check`: 13 meshes, 0 failing; before -> after)
| form | mesh / shape | cause | op | after |
|---|---|---|---|---|
| 7FD0F3 Bamboo | bambocluster01 leaf 10 | soft 5.0, slot 2 empty, Own_Emit grey 0.474 | slot 2 = the leaf's own tree03.dds; clear Own_Emit | slot 2 set, no emit |
| 7FD0F3 | stem 7 | Own_Emit grey 0.474 | clear Own_Emit | no emit |
| 0D85C2 kelp | kelptallstatic01aaa 1 | Own_Emit cyan (0.077, 0.617, 0.621) | clear Own_Emit | off |
| 0EB91F / 0EB921 Rainforest 01/02 | bark 5 / 9 | soft-lit, double-sided, no map | clear Soft_Lighting and Double_Sided | plain bark |
| 0EB91F / 0EB921 | leaf 9 / 5 | soft 2.3 / 5.0, slot 2 empty | slot 2 = treeoakleafcol44.dds | set |
| 04E139 01skydead | 11skykahl1 trunk 9 | Own_Emit, soft-lit, double-sided | clear all three | plain |
| 04E139 | leaves 5, 12, 16 | Own_Emit (colour black) | clear | off |
| 155FEC Erut07 | eruttree03tall trunk 15 | slot 1 (normal) empty; snowgumbark01_n in slot 2 | slot 1 = weepingwillowbark01_n (the pair of its diffuse); slot 2 cleared | normal set |
| 155FEC | leaves 7 | Own_Emit grey 0.474 | clear | off |
| 15B1E2 / 15B1E3 Mega04/05 | Twigs 18 / 11 | UV stretch 90.6:1 | uv_scale v fit | 1.2:1 |
| 15B1E7 Swamp04 | Branches 10 (1593 islands) | 43.3:1 (a single global factor gets no better than 6.48) | v fit per island | 1.5:1 |
| 0EB922 / 0EB923 / 155FE0 / 155FE2 Jungle 01/02/05/06 | trunk 7 | 23.5 / 23.7 / 22.8 / 27.1:1 | v fit | 1.4 / 1.3 / 1.6 / 1.6:1 |

- Every slot path points at a texture its mod already lays. No new art (0006).
- `--check` ran over the staged KotM mod and BM&V's two meshes. Those two were read from the vault archive (Data1.rar), because the stage had pruned them while the forms were dropped.
- The lists rebuild adds them back to the BM&V keep list (data/dependencies.json, +2 paths). The next `stack stage` unpacks them, and the deploy's patcher then reads them in place.
- Still dropped, because no mesh op fixes them without new art:
  - kapok 01-05: the bark diffuse is bright (luminance 132);
  - Groundplant10: the lime leaf diffuse.

## 3. Lists and checks
- LOOK_DROP is down from 22 to 6 entries. Thirteen forms are back, with these land_region_object rows:

| form | rows |
|---|---|
| 7FD0F3 | 12 |
| 0D85C2 | 6 |
| 0EB91F | 13 |
| 0EB921 | 8 |
| 04E139 | 14 |
| 155FEC | 1 |
| 15B1E2 | 14 |
| 15B1E3 | 11 |
| 15B1E7 | 6 |
| 0EB922 | 8 |
| 0EB923 | 6 |
| 155FE0 | 3 |
| 155FE2 | 2 |

- `vegetation forms --lists-only` raises the placed forms from 195 to 208.
- `textures check`: 0 problems.
- pytest on meshes and vegetation tests: 56 passed. The 9 patcher tests use synthetic NIFs made by the test: one per op, the bars, the before-mismatch, run and list, LZ4, and the table.
- Province vegetation check: see §6.

## 4. The deploy's lay step
- `deploy.sh` gains the step `mesh patches`, after `stack push`. It runs `patch --out out/mesh_patches/argonia-mesh-patches` and sends the result to `C:\argonia\MO2\mods\argonia-mesh-patches`.
- `stack.ps1 on` lays that folder after every profile mod, so a loose patched copy wins over the source loose file or BSA entry. The verify pass skips its paths, as it does for pandora-output and the LOD.
- `stack.py push` never removes the folder: it prunes only the rows it sent.
- Dry run: `patch --list` names the 13 files with their sources.
- `out/` is gitignored. Nothing patched is committed (0003).

## 5. Willows and the snowgum cards (named; bytes plain)
- **Deep-river-corridor high (yaw 135):**
  - KotM Willow05 (0E67A9): 25 rows, 41-117 m.
  - Willow07 (0E67AA): 22 rows.
  - Willow04 (0E67A8): 13 rows.
  - BM&V 01Willow (034580): 6 rows, 72-77 m.
- **Corridor shore:** Willow05 and 01Willow.
- **Willow leaf shapes:** soft 5.0 with slot 2 set to their own diffuse, which is vanilla's pattern (aspen 2.0, pine 8.0). Emissive colour is black and vertex colour white. The diffuse is hue 66, sat 0.53. No byte cause.
- **Lagoon shore:** no willows. The lime-yellow reflections are most likely Depths of Skyrim seaweed 01/02 (02BAF6, 02BAF8): 21 rows at 50-84 m, soft 5.0 with a map, hue 66-81.
- **Snowgum cards (coordinator's ask):** every placed KotM shape on snowgumbranches01_d (hue 62, sat 0.47) has no soft lighting, emissive black, and slot 2 empty but unused, so no bar fails. They do carry a green vertex tint:
  - Swamp01-08: about (125, 168, 80);
  - Jungle04-06: (37, 160, 95);
  - Jungle07/09/10: about (80, 170, 125).
  
  The engine multiplies that tint into the diffuse. Swamp's tint takes the olive card to roughly (32, 43, 11), hue 81 and sat 0.74: a more saturated yellow-green. That fits the cast, but the tint is what the author drew, not a fault. No op was added; the still decides.
- **Undergrowth01-05:** snowgum at soft 5.0 with a map, vertex colour white. Plain.

## 6. Owed: booth stills for the planner's batch (checks.md `tree-look`)
Take one booth still per form, near and at mid distance, noon. The reader judges:
- 7FD0F3 bamboo: are the frond leaves an ordinary green, with no flat teal or neon? The stems stay green.
- 0D85C2 kelp, in water: is it olive-orange with no cyan glow?
- 0EB91F and 0EB921 rainforest 01/02: is the trunk as dark as nearby bark, not pale or washed out? Are the leaves normal?
- 04E139 01skydead: is the trunk dark, not pale, and do no leaves self-glow?
- 155FEC Erut07: is the trunk shaded with bark relief, not cream-white or brighter than the sunlit litter? The leaves may read red.
- 15B1E2, 15B1E3, 15B1E7 and 0EB922 / 0EB923 / 155FE0 / 155FE2: is the bark grain even, with no streaks, swirls or smears along the trunk or branches, and no seam where the islands meet?
- Willow05 (0E67A9) and 01Willow (034580), same pose: is either frond neon lime? If only the KotM willows are, the shared leaf shape's wrap 5.0 is the cause and the next op is a lower wrap. If both are, it is the weather or shader.
- Swamp01 (KotM snowgum) beside Undergrowth01: is the Swamp card's yellow-green beyond the undergrowth's? If yes, the vertex tint is the cause, and the next op is a vertex-colour scale.
- Then the world-panel stops: deep-river-corridor 6-9, deep-sink-basin shore and high, and the lagoon shore (reflections), plus the water-types stops.

## Hand-off
All acceptance items are met except the in-game rows. Next: the planner's deploy (stage, then the `mesh patches` step) and the batch above.
