# 1.15 round 4: the owner's play test 3 (34 findings, 2026-11-02 21:35, #37) fixed in lanes, one batch on Paris

Rulings: Paris is the only game machine; in-game loops are sped up before any check runs; the LOD rebuild
(terrain, tree, object) is the round's last step. The findings: docs/research/2026-11-02/owner-playtest-3.md.

## Wave 1 (launched 2026-11-02 ~22:00 UTC, briefs under briefs/)

| lane | findings | report |
|---|---|---|
| 1.15-r4-fast-loop | the loop itself (owner: massively faster) | lane-1.15-r4-fast-loop.md (done 0ac3304: infra/gpu-box/round.sh runs a round as one resumable job; shader cache in S3; a settle action replaces fixed waits; one save load per batch; predicted 30–35 min per 10-journey batch against 75–100) |
| 1.15-r4-water | 20, 19 | lane-1.15-r4-water.md (ef229aa: pieces sat at the upper water facing down and the foot pieces buried; Skyrim.esm's 51 steps measured: the rapids line at the upper water, skirt and ring at the foot facing up; steps over the tallest piece (20.96 m) become dry gullies, 12 reaches; still water had the river type, now four still and three river WATR; 1,532 / 174 / 415 reds to 0, 0, 0) |
| 1.15-r4-ground-steps | 20 (follow-up) | lane-1.15-r4-ground-steps.md (eight steps lose their channel in a later generate.py pass) |
| 1.15-r4-materials | 16, 17 | lane-1.15-r4-materials.md (e396d20: the pebble field is BM&V's riverbed edge chosen by height alone, 28 % of dry ground, now 2.6 % and only at the water's edge; no ground texture had a normal map, now vanilla's own, so the shine goes; then 72fbb96: every window under the 40 % bar) |
| 1.15-r4-light | 18, 9 | lane-1.15-r4-light.md (57d61ea: fog max 1.0 hid the sky, far under vanilla's class medians, grey zeniths; height fog was a 5 m slab, now a bank below eye height; then 9e492ee: seven mist weather copies by water-level band with their own Community Shaders fog files, every mist region banked between its water and eye height) |
| 1.15-r4-trees | 4, 5, 32 | lane-1.15-r4-trees.md (31c2e32: trees sunk by a measured per-model seat, the mods' own placement the reference; flora with any missing texture dropped; tree families per class, classes now 0.77–0.89 distinct; the teal cypress: its textures are laid and the mesh is KotM's own, so the colour is our lighting of its soft-lit, vertex-coloured needles; a weather-swap still at one tree in the batch settles it) |
| 1.15-r4-claywater | 3, 22, 23, 25, 29, 31, 1 | lane-1.15-r4-claywater.md (9d9f2a9 79d4b34 75f1f18: a stockade kit scattered as trees, 13 Claywater refs 31 m under the new ground, docks seated on the bed, sign textures never laid; the Claywater save; then b94ef5f: terrain_patch real as pads and bowls read by the ground, materials and renderer; the well, house and stable on pads; the scour pool a bowl under its water) |
| 1.15-r4-roads | 21 | lane-1.15-r4-roads.md (e7dcd52: Skyrim's road measured as a shallow trough with a 4 m paint blend and no edge statics; roads shaped into the ground, steep points 1,421 to 287; then e2fd18d: the road yields to water as dry runs fading to the bank, blends at junctions, benches on slopes, cut capped at 1 m; walls 637 to 240, steep points 1,421 to 1,120; handed off) |
| 1.15-r4-roads-2 | 21 (follow-up) | lane-1.15-r4-roads-2.md (0d47abf: of 240 walls, 173 were the land's own banks before any road; the tracer is now grade-aware with curves, cut and fill capped at 1 m, the fade follows the bank; road-made walls 67 to 20, over-steep points 1,120 to 571, the fold at vanilla's medians; owed: walls and steep points at the 221 crossings to bridges, on site discs to the places lane) |
| 1.12-r4-chart | 26, 14, 12, 30 | lane-1.12-r4-chart.md (19492e8: the docked pane's rule ignored modal views and a barter closing within 0.3 s; names baked into tiles scaled with zoom, now screen-space at one size; the sketch layer (coast, major roads, border, compass) now drawn under the fog with the seven cities as named dots; the chart re-rendered from the current water, every river point within one cell; P2: Lilmoth/Blackrose labels read as swapped, Thorn clipped, Claywater label on roads, doubled road near Gideon) |
| 1.x-r4-play | 2, 34, 15, 33 | lane-1.x-r4-play.md (done 7948d33: third person, 5,000 gold, Precision camera shake off; 33 left: FreeClimb has no tree filter, trees climb by the 2026-11-01 ruling, the mechanic is the modder's) |
| 1.3-r4-talk | 24, 27, 28 | lane-1.3-r4-talk.md (c1e730f: topics were offered only once learned from a keyword, now service, newcomer and local topics from the first meeting (Livia 2 to 14); the Talk perk gated on GetDead and IsInCombat as Skyrim.esm gates its corpse choice, a corpse gets Search, a fighter no prompt; Gaius had no written lines, now ten, text-reviewed; his facts and the hut record owed to 1.3) |

## Wave 2 (as wave-1 lanes return)

1.15-r4-creatures (13) done d78bee5 (lists held 1–2 kinds in 30 of 81 cases and density was a third of vanilla's measured shore figure; now 125 lists of 12–21 kinds, density at vanilla's, apex kinds at their dens); 1.12-r4-menus (6, 7, 8, 10, 11, plus the owner's custom-UI card beside the Wind UI one, 22:06) launched 22:27; done b3cbb78: `python -m tools.ui_harness menus` drives seven menus at four viewports by pad in 44 s (focus started nowhere in magic, journal and dialogue; magic's column jumped: fixed in nav.ts); the System pane on the paper sheet, contrast 3.2:1 to 6.6:1; loading screens weighted so no subject passes a third (the Hist was 42 %); two Moonlight cards, 'Argonia' as today and 'Argonia custom UI' with Wind UI and Dear Diary set aside and our own inventory and character sheet (OpenMW's tab, glyph and d-pad handling) wired through the router; owed: books from the inventory, the pause-pane cycle on the custom card, the owner's comparison.

Owner, 22:06: seven screenshots of the tree colours, shiny textures and pebble swathes, routed to the trees and materials lanes.

## The batch

Also in the batch: `tree-teal` (one KotM bald cypress under our weather and under KotM's own weather, a still each; if teal persists under KotM's, Community Shaders' soft lighting is next), `ground-materials`, `creature-spots`, `chart-zoom`, `claywater-talk`, `menu-sweep`, the third-person save and gold read, a hit-and-camera still. Before the deploy on the build VM, under the province lock: the province plugin build (land, materials, placements, lists, infra, creature lists), `vegetation check`, the chart renders (`python -m tools.chart render`, the 4k level), the region saves remade with `--fresh` (ten, with Claywater); `tools/world_sample.py --write` (its pinned heights follow the new ground) and the full `make check` once.

One deploy of main on Paris when the lanes have landed; the journeys the lanes owe (river-steps, tree-seat,
road-look, chart-zoom, claywater-walk, claywater-look, the panel's dawn stills, the save load) in one batch,
crash-prone last; stills to a reader; then the LOD; then the saves remade and the owner told on #37.

## Batch one on Paris (03 Nov 01:20–01:56, 36 min of machine time: up 8, deploy 5.7, batch 22.5; 7 of 11 journeys green, 81 stills)

Readers' verdicts (four readers, one per group):

- **Proven:** the station house exists with a door and an interior; no lilac or purple surface anywhere; no stray boardwalk or stair tower on land; Livia offers Barter plus at least eight topics, Takes and Signs nine or more, Gaius five; the map pane stays off the dialogue window; markers and names keep their size under zoom; the sketch layer (coast, roads, named city dots) shows under the fog; still water reads as still (one clear lake still); the creature reports list frogs, snails, moon-adders, kotu gava, a mudrunner and a giant snake instead of only hackwings and centipedes (few visible in the stills).
- **Not proven, the harness's fault:** 14 stills framed inside foliage and two road vantages in lakes, three Claywater vantages with the player swimming: the camera never left third person (`cgf` unknown to this runtime's console, the F key ignored) and the journeys' positions predate the re-traced roads and the moved Claywater ground; the panel stopped at its tenth still, tree-seat at its class views; menu-sweep's pad presses did nothing on the Wind UI panes; the corpse-search step lost the body from the crosshair.
- **Red in game:** water surfaces marbled and blocky white-and-dark at distance (nine stills; new since the WATR split); fog still hides the sky, no low mist bank in any still, a yellow-olive cast; the map pane over the barter window; crimson, pink and cyan foliage persists; docks and landings at or under the water line in two stills; the stables unseen, hut doors unseen.

Wave 3 (02:10): 1.15-r4-camera (a bridge camera command over the engine's API), 1.15-r4-journeys (every journey derived from the build it runs on, stale ones red at L1, pulled-back vantages), 1.15-r4-water-look (the WATR records diffed against vanilla), 1.12-r4-chart-barter, 1.15-r4-light-verify (stale weather ids, fog files laid, the yellow slot). The second pass (camera soft) and the saves job run on Paris meanwhile.

## Batch two on Paris (03 Nov 03:13–03:42, 29 min of machine time: up 0.5, deploy 9.3, batch 19.6; 7 of 10 journeys green, 72 stills)

Readers' verdicts:

- **Proven:** trunk bases meet the ground wherever a base is in frame (the erut, the hist trunks), no hovering roots; the still body reads still, no drift; the Claywater landing sits above the water, the well on dry pale sand, the station house with its door and interior, a hut with a door; no lilac anywhere, nothing Nordic, no stray boardwalk or tower; the four Claywater people talk (Livia with Barter and eight or more topics; Takes and Signs nine or more; Gaius five); the map pane stays off the dialogue window; the sketch layer with small even names under the fog; the class views read as four different forests (delta, interior swamp, rootland, northern transition).
- **Red in game:** crimson, pink and rose foliage in about twelve of nineteen world stills; a uniform fog hides the sky at the panel's vantages with a hard white line at the horizon (the Community Shaders height-fog bank at eye level, density 0.5 with falloff 30, reads as a slab), a yellow-olive cast in the mist weathers' stills; distant water still blocky white-and-dark at the lakes (the terrain LOD tiles are round 3's, with the old water heights: the LOD rebuild, the round's last step); the far Claywater docks on the waterline; the barter window missing from the barter step (the map pane shows alone).
- **Unproven, the harness:** the panel stopped at its seventh still (the editor-id `sw` left the region's pick: the third pass sets and forces by runtime form id); the river-step stills framed ground or leaves, the road stills sand or lake (the road paint is the pale sand; no trough visible); the ground-material stills inside gorse; the corpse-search step lost the body from the crosshair again; the look journey's interior check is stale (the house stands in the world); the stables in no frame.

Wave 4 (03:58): 1.15-r4-fog-bank (the height-fog bank soft and below the eye, the mist weathers' olive fog slots cool), 1.15-r4-red-trees (the crimson and pink forms named and swapped or fixed). Then the LOD rebuild on Paris (terrain, TexGen, DynDOLOD), the saves, the panel on the LOD build, the owner's comment.

## The final panel on Paris (03 Nov 05:41–05:52: deploy 4 min with the LOD laid and the shader cache archived, the panel 7 min, 37 stills, first person, weathers forced by form id)

The LOD rebuilt last (04:48–05:37: terrain 8 min, TexGen 4 min, DynDOLOD 31 min, collect 1 min, archive 1.7 GB), the ten region saves made fresh at 04:48 and pushed to the pool; the jobs lost one Paris boot to the eighth spot interruption (04:33) and two launches to Steam not running (fixed: the launch starts Steam when it is absent).

Readers' verdicts on the 37 stills:

- **Fixed:** low soft mist at dawn in most dawn stills; trunk bases on the ground, no hovering tree anywhere; distant land and trees continuous with the near ground where a far view exists; no pebble swathe read as a field; nothing Nordic; no white horizon line beyond the three coastal stills.
- **Still visible:** the sky hidden by a flat grey fog in most stills (at noon under the forced clear-dry weather too, so not the weather's fog distances) with a yellow-olive cast in about half; crimson and pink foliage in about twenty stills (trees, not the dropped ferns: their textures are vanilla pack files the build VM cannot measure); the near water at river and basin shores marbled and blotchy black-and-green (nine stills; round 3's vanilla water read as water: our records' colour and opacity overrides are the suspect, reverting now); the far water bright white and flat in three flooded-forest stills; two vantages inside willow fronds.

The next diagnosis is the owner's to run cheaply: the two Moonlight cards with Community Shaders on and off at the same shore tell whether the fog wall and the water look come from the shaders or the records.
