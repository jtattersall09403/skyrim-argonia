# Walk 2, lane ground: L16, L21, L30 and the tall grass of L9

Measured 2026-11-13 on the build VM, on the main tree's build 20261111T100156Z (its ESM equals its painted shards,
154,080 of 154,080 quadrants) and on Skyrim.esm and Black Marsh.esm (3,000 LAND records each, read with
`tools/argonia_world/esm.py`).

## The cause they share (L30, L16, most of L21)

The engine adds a quadrant's texture layers: each alpha layer's opacity is that texture's weight at the vertex and
the base shows 1 - their sum. The Creation Kit writes them that way: in Skyrim.esm's quadrants of three alpha layers
or more, a vertex's opacities sum to 1.00 at p50 and p90, 1.13 at p99, past 1.05 at 1.8% of vertices; in Black
Marsh.esm they never pass 1.00. Our writer (`texture.py`, `roadpaint.py`) assumed the other model, that each layer
replaces (1 - o) of what is under it, and wrote opacities inverted top down (o = w / what is left), so the upper
layers of a quadrant carried opacities near 1 for small weights. The ESM read-back and `texcheck` decoded with the
same wrong model, so both passed: that is why hard edges came back three times.

Measured on the main tree's paint, rows -170 to -156 (Aunike Ridge and round it), read as the engine adds it:
20.7% of land vertices sum past 1.05 (p99 2.1, worst 3.7: a lit square up to 3.7 times its textures' brightness);
a vertex shared by two quadrants reads up to 1.0 differently from each (each quadrant stacks its own order, so its
sum differs: the edge runs straight along the quadrant line); grass-bearing weight on a road's surface reaches 1.99,
and 11.7% of spine vertices carry over 0.1 of it. Rendered off-game (texcheck's per-triangle crop of cells -21..-19,
-164..-162 with the additive read) the ground breaks into lit and dark quadrant squares, as in the owner's picture.

| L# | cause (measured) | change | proof |
|---|---|---|---|
| L30 | Opacities written for a stacking model the engine does not use: 20.7% of land vertices overbright (p99 2.1, max 3.7), quadrant seams up to 1.0 on the engine's view (the quadrant cut, the six-texture limit and cell borders are not the cause: 0 quadrants over six, seams 0.0107 on the stacking read) | `texture.py` step 8: an alpha layer's opacity is its painted weight, rounded so a vertex's sum never passes 255/255; `decode_quad` adds. `texcheck` reads the engine's view additively and adds rows `over_share` <= 0.018 and `over_p99` <= 1.13 (Skyrim.esm's own); the seam row (<= 3/255) now measures the real edge | texcheck on the main build: FAIL (over_share 0.2066, over_p99 2.1, seam_max 1.0, step_max 1.0); on the small world after the change: PASS (over_share 0.0, over_p99 1.0, seam_max 0.0078, step_max 0.561); `test_the_engine_adds_the_layers_and_no_vertex_is_overbright` |
| L16 | The same paint: the terrain LOD's textures are baked by xLODGen from the ESM's layers; the overbright quadrants are the far land's hard-edged light squares. Ruled out: every land quadrant is painted (0 unpainted, so no default texture shows); every ground LTEX names a diffuse the profile resolves (texcheck crops, L7: no missing texture); the terrain LOD settings hold only mesh keys (`lod-settings.json` terrain.post) and leave xLODGen's texture brightness, contrast and gamma at its defaults | none in the LOD's scripts or settings: the paint's change above; the terrain step's key reads every LAND record, so it is stale after the rebuild without a hand change | the paint's proof above; the LOD proof needs the play machine (For the lead) |
| L21 | Grass grows by its ground's weight: on the engine's view the grass-bearing layers stood on the road surface at up to 1.99 (11.7% of spine vertices over 0.1). Placed things are already kept off: the place check's `refs_on_road_surface` is 0 | the paint's change above (the road's own layers are now its weights: 0.97 or more of the surface is road material, none of it grows grass); `texcheck` adds `road_surface_grass_max` <= 0.1 over the whole road surface (to 0.45 m inside its edge: 3 m from a major spine, 1.55 m from a minor); the studio's path preview and its grass reader add the layers as the engine does (`terrain_mesh.js`, `grass.js`, `path_paint.js`) | main build: road_surface_grass_max 1.992 FAIL; small world: PASS (road_surface_grass_max 0.035 over 2,733 surface vertices, road_spine_grass_max 0.027, road_spine_grassy_share 0.0); `test_the_three_layers_are_the_road_weights_the_engine_adds`, the studio's `path_paint.test.mjs` |
| L9 (grass) | KoTM's `ALPAGrassLong03A`/`03B` (cattail mesh `vactrolswamptall01.nif`) stand 273 units, 369 at their height range (5.3 m), in Murkwood's and Blackwood's marsh grass, Ultherus, Tulmek and Banujha lists. Skyrim.esm's tallest land grass stands 90 (TundraGrass01, 69 x 1.30); a 1.0-scale race's head, where the third-person camera sits, about 120. Also over 90: `ALPAGrassReeds03`/`04`, `WildSaltrice03`/`04` (116), `Heather01` (93) | A GRAS has no scale: each over-tall grass is replaced in its lists by the shorter grass of its own family in KoTM (`Long03A/B` and `Reeds03` -> `Reeds02` (88), `Reeds04` -> `Reeds01` (80), `WildSaltrice03/04` -> `02`/`01`, Hatandros Bight's `Heather01` -> Flower Fields' `ESuHeather02`, a pink flower of its own as the ground-colour check asks); a list names a grass once. New check `grasscheck` (the paint stage's): every grass a land material carries stands at most 90 units, read from its winning plugin's OBND and height range (25 of the 65, Flower Fields' flowers and Tropical Skyrim's grass plants, carry no OBND and are listed unjudged) | `grasscheck`: before FAIL (7 grasses over 90, tallest 368.5); after PASS (0 over, 0 unread) |

## Walk checks

- Travel menu, "Walk-check spots (2 of 2)", "A dry region: Aunike Ridge scrub". Look at the ground at your feet and
  around you: different ground textures should fade into one another; there should be no straight-edged squares of
  lighter or darker ground. Reply "ok" or "fault" (with a picture).
- Same spot: look out to the far hills. The far land should show no hard-edged light squares. Reply "ok" or "fault".
- Travel to any village on a road (for example Aunike Crown in the Aunike Ridge page) and follow the road out of it
  for a minute. The road should stay visible: no grass growing across it. Reply "ok" or "fault" with where.
- Travel menu, "D5, the highest danger: Murkwood cypress swamp". The grass there should stand no higher than your
  character's waist to chest, so you can see over it in third person. Reply "ok" or "fault".

## For the lead

- changes.md rows: "Ground materials or painting rules" (`texture.py`, `roadpaint.py`): `paint` stale, then `esm`,
  `upload`; "The paint's checks" (`texcheck.py`, `grasscheck.py`). `texture.py` hashes itself: the whole paint is
  made again (about 21 min of paint stage, then the ESM). The grass lists change our LTEX records' grass, written
  by `esm`.
- After the rebuild: built places' ground bundles and builds (their path paint goes through `quad_opacities`; the
  places skill's step for a ground change), and the deploy.
- The LOD: the terrain step's key reads every LAND record, so after the rebuild `lod.sh stage` finds `terrain` stale
  and runs xLODGen in full (textures and meshes; the meshes come out the same from unchanged heights) then our mesh
  pass; `dyndolod` and `collect` follow. No `LOD_FORCE` is needed. Prove it first on the small world on the play
  machine:
  `tooling/job_guard.sh run --gpu nw-lod-selftest -- infra/gpu-box/lod.sh selftest` then
  `tooling/job_guard.sh wait nw-lod-selftest`, and look at `out/newworld-small/lod/` terrain textures for squares;
  then `NW_LOD=1 tooling/job_guard.sh run --gpu nw-lod -- infra/gpu-box/lod.sh stage` and
  `tooling/job_guard.sh wait nw-lod`. A texture-only xLODGen run is not offered by `lod.ps1`; the full terrain step
  is 34 min.
- Lane `seat`/`flora`: no placement rule needs to change for L21 (placed things already keep off the road surface).
- The studio previews ground and paths additively now (`terrain_mesh.js`, `grass.js`, `path_paint.js`): reload it.
