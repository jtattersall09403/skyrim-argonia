# Lane 1.15-r6-veg-forms-3: the willow curtains and the stretched trunks at the round-6 panel

Evidence: r6 batch 20261105T005149, 16-world-panel. L1 is the mesh bytes measured before and after; L4 is owed to the planner's batch (checks.md row "No blocky cut-out willow curtains...").

## Method
- Each still's frustum: the stand (the step's `pos` window centre in tests/journeys/world-panel.yaml), the heading h0 + k·60°, refs 0-40 m within ±32°, read from the current shards (out/terrain/vegetation) and object_form.
- Caveat: the batch's plugin may predate these shards (lane-clear found this on the Blackwood Road), so a form named here is a candidate until the L4 still confirms it.
- LOD is ruled out for every still. All the candidates stand within 40 m, inside the loaded cells, so the full model draws, never the billboard.
- Measured per shape:
  - the NiAlphaProperty (newly read by nif.py: flags and threshold);
  - soft lighting;
  - the slots;
  - the UV stretch as a median and as an area-weighted p90 (new);
  - texels per metre.

## Bethesda's leaf alpha (0034)
- Every vanilla and Tropical Skyrim tree leaf measured uses alpha test with no blend: flags 0x12EC.
  - Vanilla: aspen at threshold 80, pine 112, reach tree 70/45.
  - Tropical Skyrim: valenwood 198/66/45, palms 123.
- "A missing alpha blend" is therefore not a cause. Bethesda never blends tree leaves.
- Bethesda's own weeping willow (_ResourcePack treeweepingwillow01/02) draws the same WeepingWillowBranches01_d (2048 px, DXT5) with:
  - Soft_Lighting off;
  - the alpha test at threshold 127.
- The KotM willows draw that texture soft-lit at wrap 5.0, with the diffuse as the soft-light map, and the test at threshold 80.

## Per still
| still | candidates (form, distance) | measurement | fix |
|---|---|---|---|
| 14 / 15 flooded-forest-shore s4 | Willow04 0E67A8 at 10.6-12.9 m (3 refs); Mega04 at 11.5 m; Willow07 at 22.7 m; 01Willow (BM&V) at 31.6 m | leaf card: soft 5.0, Soft_Lighting on, alpha 0x12EC thr 80 (Willow04/05/07 the same). Bethesda's willow: Soft_Lighting off, thr 127 | new op `alpha {threshold}`. Willow04, 05 and 07 leaf: clear Soft_Lighting, threshold 127 (Bethesda's two values) |
| 16 flooded-forest-high s2 | only Undergrowth01 0F0ACB at 7.9 m (the SoulCairn shrub card: snowgum, soft 5.0 with a map, thr 95), braken, meadowsweet. No trunk form within 40 m | no bar fails | none. The shard is probably a placed static or the shards are stale. Owed: a crosshair ref read at this stand in the batch |
| 18 interior-swamp-shore s4 | Mega02 15B1E0 at 3.0 m (scale 1.18); Bottle02 at 8.7 m | Mega02 trunk median 3.0, area p90 4.6, 343 texels/m (at 3 m, about 1:1 with screen pixels) | within the bars. No op. The near-camera magnification is judged by the still |
| 10 / 11 deep-sink-basin-shore s2 | SwampPlant08a at 7.8 m; Kapok03 at 13.2 m; Jungle06 (JungleTree03.nif) at 24.4 m; Mega03 at 38.8 m | JungleTree03 trunk (trunk2.dds): median 5.1 (passed the old bar), area p90 8.4. Kapok bark count-p90 6.3 but area p90 3.9 | JungleTree03 (0EB924/0EB926): V fit, 5.1/8.4 -> 1.6/2.7. Stepped silhouette: no alpha or LOD cause found (the SwampPlant vine card is opaque by its texture; the imagespaces carry no depth of field). Owed: a ref read |
| 26 rootland-shore s2 | SwampPlant08a at 2.5 m; Kapok01 at 9.6 m; Jungle06 at 21.3 m | as above | the JungleTree03 fit |
| 22 northern-transition-shore s2 | Erut02 155FE7 at 11.9 m; Erut01 155FE5 at 15.6 m; Mega02 at 24.2 m; Seju07 at 36.9 m (patched) | Erut01/02 trunk: weepingwillowbark01_d paired with snowgumbark01_n (the wrong bark's relief). Leaves Own_Emit grey 0.47 | slot 1 = weepingwillowbark01_n (as Erut07); clear Own_Emit |

## The patcher
- `nif.py`: `Shape.alpha` / `set_alpha` read and write the NiAlphaProperty.
- `patch.py`, op `alpha {threshold}`.
- `patch.py`, new bark bar: area-weighted p90 stretch <= 6. A count p90 is ruled by slivers: the kapok's count p90 is 6.3, its area p90 3.8.
- `uv_scale fit` now minimises the island's area p90. All existing fits still pass, and their tails drop. Examples:
  - rainforest01 bark 9.2 -> 3.0 count p90;
  - GreatSeju 9.5 -> 3.8 area p90.
- `p90_owed` (data) names a measured tail that no per-island scale reaches:
  - Swamp04 branches: 18.3 area p90 after fit; the UVs are sheared inside 1593 islands, and v/u/v fits give 18.3;
  - Jungle01Stump bark: 7.0.
  - A re-unwrap is owed for both. Neither is in these stills.
- data/mesh-patches.yaml: 23 -> 28 meshes (Willow04, Willow07, Erut01, Erut02, JungleTree03; Willow05 adds its leaf).

## Checks
- `patch --check`: 28 meshes, 0 failing.
- pytest meshes: 13 passed (2 new: alpha op, p90 bar/owed). Vegetation tests: 48 passed.
- ruff: clean.
- `make plugin PLAN=1`: ground, terrain, water and vegetation run.
  - These keys move with other lanes' dirty files.
  - The pipeline has no mesh-patch input. The patch rides the deploy's `mesh patches` lay step.
  - No vegetation rerun is needed for this lane.

## Owed (L4, the planner's batch)
- 14/15 s4: the willow curtain reads as strands, not as lime slabs.
- 22 s2: the Erut trunks show even bark.
- 10/26 s2: no streaks on the JungleTree03 trunk.
- 16 s2 and 10 s2: a state read of the ref under the crosshair, to name the shard and the stepped pillar.
- Not fixed: JungleTree03's trunk2 diffuse is paired with weepingwillowbark01_n (noted).
