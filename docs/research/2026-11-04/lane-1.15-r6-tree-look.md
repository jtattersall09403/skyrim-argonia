# Lane 1.15-r6-tree-look: tree-seat stands, stretched trunks, the slab, the neon and three classes

Evidence: out/batch/1.15-round-6/20261105T040257/11-tree-seat-1-20261105T044229 in the chain worktree (frames 01 s0, 04 s0, 05 s2, 06 s0, 07 s4, 10 s2, 11 s2 and 12 s0 read directly; the scan's s0 to s5 sit at heading +60 k). The batch's journey was the same as main's tree-seat.yaml (no difference in setpos or setangle). The measures come from the current shards (out/terrain/vegetation), checked against the forms within 6 m of each stand and within 3 m of each scan line (scratch scripts, since deleted).

## Measures

- Stand to trunk pivot in round 6: palmoke04 2.4 m, erut05 4.4 m, palmoke02 about 5 m, histtrunk01moss 2.4 m. The class stops stood 2.9 to 3.1 m from a trunk (rootland: HistTree01 3.1 m south; coastal: Cypress06 2.9 m).
- Footprint of each trunk at the ground (the 90th-percentile vertex reach from the seat to 2 m above it): PalmokeTree02Single 744 u (10.6 m), ErutTree01Tall 350 u (5.0 m), HistTreeTrunk01 1210 u (17 m). Every round-6 tree stand was inside its tree's own roots.
- UV stretch, median and area p90 per shape. The brief named three trunks for this measure:
  - PalmokeTree02Single: trunk 2.3/2.5, roots 3.3/5.5.
  - PalmokeTree01Single: trunk 3.0/3.5, roots 2.6/4.3.
  - ErutTree01Tall: trunk 4.0/5.5, Moss.001 16.4/33.3.
  - Only the erut moss is over the bar of 6.
- Kapok bark lum 137.8 was already patched to 59 on the chain's deploy (8f78adf2 is an ancestor of its HEAD).

## Defects: form, cause and fix

| Frame | Form | Cause | Fix |
|---|---|---|---|
| 01 palmoke04 s0, smooth tan slab | PalmokeTree02Single roots (dirtcliffsroots01) | Stand 2.4 m off, inside the 10.6 m root flare; the texel ratio is fine | Stand rule |
| 02 palmoke02 s0, seam and hidden base | PalmokeTree01Single, where the Roots shape meets the Trunk shape | Two shapes with two textures meet (an authored seam, no stretch); the stand was inside the flare | Stand rule. The seam stays, since it is the mod's art |
| 04 erut05 s0, streaked bark | ErutTree01Tall trunk | weepingwillowbark01_d paired with snowgumbark01_n | Patch: slot 1 takes weepingwillowbark01_n (as ErutTree01) |
| 04 erut05 s0, pale-green block at the base | ErutTree01Tall Moss.001 | UV 16.4:1 | Patch: V fit per island, giving 2.3:1 (p90 7.5:1, recorded as owed: single-quad strands) |
| 04 erut05, leaves | ErutTree01Tall leaves | Own_Emit 0.47 | Patch: cleared |
| 05 histtrunk01 s2, neon-lime cluster | ArgoniaTreeMarshroom01Green (smallmushroom01green) | Own_Emit (0.06, 1.0, 0.0) on a Telvanni globe cap; no lore dossier names a glow | Patch: Own_Emit cleared |
| 05 histtrunk01, line of fronds | ArgoniaTreeSwampPlant02B (SwampPlant08a) | Own_Emit white 1.0; ten on that line, so fully self-lit | Patch: cleared |
| 05 s0 orange near-plane trunk; 06 no base | HistTreeTrunk01 | Stand 2.4 m off a 17 m footprint | Stand rule: 8-9 m off a 21.7-22.4 m footprint |
| 11 rootland s2/s0/s4, pale-yellow slab | ArgoniaTreeHist01 (HistTree01, CrackedBark, lum 60, stretch 1.3) | Its trunk 3.1 m from the eye fills the near plane. This is no LOD or proxy mesh and no missing texture | Class stand rule (no plant over 1 m within 4 m of the eye) |
| 07 coastal s4, shear slab and plank | Slab: ArgoniaTreeMega02 (8.2 m off, bearing 271; trunk stretch 3.0/4.4). Plank: not found | Plank: none of our refs (no vegetation ref and no placed static within 20 m). It is probably part of a KotM mesh, unpinned | Class stand rule. The plank is owed to the next tree-seat read |
| 10 interior s2/s4, cream gorse-like flowers | 01giantmushroom = BM&V ztGorsebush04statwhite (not vanilla: mesh_source bmv) | Soft_Lighting with its own white diffuse as the soft map; lum 94 | Patch: Soft_Lighting and Own_Emit cleared, lum 60. Lore list drop: gorse is no Black Marsh plant |
| 10 interior s2, lime fronds | Willow04/05/07 curtain within 1.6-2.7 m | Leaf curtain at the eye | Class stand rule. Willow dropped from the interior swamp (below) |
| 12 northern s0, lime fern patch | 01TROPICAL11 = ESalixshrub03 (2.0 m off s0) | Drawn lum 73, the brightest leaf on the line | Patch: vertex colour lum_to 50 and Own_Emit (black) cleared |
| 09 flooded s2/s4, hanging leaves fill the frame | 01Willow and Willow forms whose crowns cover the eye | Stand inside crowns | Class stand rule |

`meshes patch --check` result: 33 meshes, 0 failing. The 5 new entries are in data/mesh-patches.yaml.

## Stand rule (tree_booth.py)

- A tree stop stands 6-10 m beyond the trunk's measured footprint, aims at the base (the base sits in the middle of the frame), and has nothing over 1 m within 3 m of the eye line. The eye is the engine's, about 1.6 m up.
- A class stop searches the fullest cell on an 8 m grid. Its stand has no plant over 1 m within 4 m of the eye, and it looks level along the bearing with the most trunks 8-30 m out.
- `refresh` no longer re-aims tree-seat. The round-6 re-aim was what pulled the stands to 2.4-4.4 m.
- Now: all 6 tree stops have 0 hits on the aim line and 0 at the eye. All 6 class stops have 0 plants within 4 m and look into 6-15 trunks.

## Three classes (0032)

Willow is now admitted only in flooded-forest and deep-sink-basin. Grounds: regional-variety-audit row 9 (floodplain willow) and line 156 (interior swamp: rain-tree crowns over dead snags, "dank foliage"). Gorse is admitted nowhere: the flora list in lore topics/fauna-hazards.md:92-96 has no gorse.

List density share by family, before → after (land_region_object):

| Class | Willow | Gorse | Cypress | Fern | Monstera |
|---|---|---|---|---|---|
| interior-swamp | 0.349 → 0 | | 0.023 → 0.047 | 0.059 → 0.085 | 0.177 → 0.256 |
| flooded-forest | 0.379 → 0.379 | 0.159 → 0 | | | |
| coastal-lagoon | | | | | |

Coastal-lagoon was already distinct and is unchanged: seaweed is 0.71 of its stems and willow 0.

Stems in the current shards before the change: flooded-forest willow 0.348 and gorse 0.147; interior-swamp willow 0.377.

The share of stems after the change waits on the owed regenerate. Monstera-type ground plants are still shared, at 0.256 and 0.083.

## Gates

- tree-booth and `journeys refresh --only tree-seat`: 0 stale. journey_lint ok. run_journey --dry ok. Tests: vegetation 63 passed, meshes 14 passed. ruff clean.
- trees-census is red on the current shards (depth reds in cells (-44,-7), (-61,10) and (-25,37)). test_journeys reports other journeys stale against a moved ground. This lane changed no shard or ground. The cause is the water-edges terrain work in flight (cell_water and ground changes).
- Owed: the whole-province vegetation regenerate. The province lock was held by we2-after2 (terrain generate), so it was not run. After it: re-run tree-booth and the refresh, and the census of the share of stems by form.

Birch (01BIRCH, 0.026 of coastal-lagoon stems) reads Nordic and is left for the planner.
