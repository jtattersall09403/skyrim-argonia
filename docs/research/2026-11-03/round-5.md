# 1.15 round 5: the owner's 08:55 and 09:23 replies on #37 (the sky, creature kinds, the System pane, the map, grounded spawns, water types) fixed in lanes, proven on Paris

Rulings of the day (docs/owner-brief.md 2026-11-03): nothing partially finished is handed over (a finding is fixed only
when a still at the play camera proves it); creature kinds per equal-sized region never fewer than Skyrim's or the Black
Marsh mod's; only landing-page menus are paper; the sketch is the fog-of-war layer over the whole province; every spawn
grounded in the research; the water types the Skyrim way. Briefs under briefs/, lane reports beside this file.

## Lanes (launched 09:0x–11:5x UTC)

| lane | what was wrong (measured) | report |
|---|---|---|
| 1.15-r5-sky | every cloud layer, the full-sky fill included, painted cream (vanilla: the fill dark blue 114E77, uppers blue-white); image spaces with sky scale 1.6 against vanilla 0.3, white 4.0 against ~1, eye-adapt wrong, and day/dawn/night pointing at the wrong vanilla images; cloud masks 0 so overcast sheets drew on every weather; tannin-haze a cream full-sky sheet; clear-dry's ground light olive | lane-1.15-r5-sky.md (446ee951, 58c3eaef: all to their templates' bytes; checks sky_clouds, sky_image, sky_fill_and_ambient) |
| sky A/B on Paris | the same build at the same shore: shaders off = blue sky, clouds, soft horizon; shaders on = flat grey veil, no clouds, hard white horizon line, dawn a cream wash | out/batch/1.15-round-5-sky-{on,off}/ (10:10–10:14), reader verdict in the lane log |
| 1.15-r5-cs-fog | Community Shaders' height fog at 20x its default (density 0.1, falloff 30 above the slider cap) | lane-1.15-r5-cs-fog.md (ba6bb8bb: the feature's shipped defaults, the nine per-weather files gone) |
| sky bisect on Paris | with the height fog and volumetric lighting neutered the clouds return, the veil thins and the dawn cream turns grey; a residual grey against shaders-off remains from another feature | out/batch/1.15-round-5-sky-on/20261103T114407/; ruling: both features off until authored within measured bounds (ea4a3909) |
| 1.12-r5-system-pane | the System pane on a paper sheet | lane-1.12-r5-system-pane.md (e7bfc816: the in-game frame tokens, contrast 6.61 → 10.88) |
| 1.12-r5-settings-page | the Settings page behind it reads as a distressed scroll frame in the still; the themed art on Paris matches the build (494b2136), so the cause is elsewhere; the journey expected a log line the code no longer writes | lane-1.12-r5-settings-page.md (8c6aa22d: the expectation; the frame owed to the final still) |
| 1.12-r5-sketch | the view already drew the sketch everywhere; the owner read the hand-over's words | lane-1.12-r5-sketch.md (aa760033: compositing order pinned by test; the deploy re-renders a stale chart) |
| 1.12-r5-chart-zoom | in game the chart opened at a remembered zoom 8 and the journey's four presses never reached zoom 1 | lane-1.12-r5-chart-zoom.md (a01ae4f0: the first open is the whole province; the journey zooms to 1) |
| creature kinds (research) | 4 of 9 classes under Skyrim's equal-area bar, all but one under the mod's; dry-land lists 4–5 kinds | creature-kinds-per-region.md |
| 1.15-r5-creatures | as above | lane-1.15-r5-creatures.md (4017dab8, 0a6941c8, 7ef922eb, dd34b62f, a94871fc: every class ≥ both computed bars, coast 12 → 26, dry lists 4 → 12; tree-viper and pad-sa shark; 202 kept guar rows, two placed at Claywater; day-rule packages templated from Skyrim's; every row cites the dossiers; the legacy table gone) |
| 1.15-r5-creatures-journey | the journey's stills framed nothing and read no state | lane-1.15-r5-creatures-journey.md (7dd06540: generated stops, a kinds ≥ 4 read that can fail, the guar-pen stop); first reads: 2/0/1 kinds live at three spawns, a follow-up |
| water types (research) | our seven WATR copied Skyrim.esm's DefaultWater, which Update.esm and Tropical Skyrim override: the game never draws it | water-types.md |
| 1.15-r5-water-types | as above; four identical stills and three identical flows | lane-1.15-r5-water-types.md (c74c787a: nine per-cell types from the DB, each the winning record; 65a4d569: vantages) |
| 1.15-r5-crimson | the crimson canopy is a red vertex colour baked into nine King of the Murkmire leaf shapes (Erut01–08, SwampPlant02A/B), not a texture | lane-1.15-r5-crimson.md (8a9bc8f0: dropped; `hue build-nif`; the check fails any placed red shape) |
| 1.15-r5-delta-trees | the tidal delta's marsh trees were the Erut: 7.9 trees/cell under the band; dunmer-north deep-sink 29.4 over it | lane-1.15-r5-delta-trees.md (542aa868, 34400f80: cypress family for the delta; the region figure from the sister median; 18 checks green) |
| 1.3-r5-livia | the kept guar carried the predator AI and mauled Livia (ragdolled under the player); the poler stood 2.4 m under the cell water | lane-1.3-r5-livia.md (8f35ff46: Unaggressive as Skyrim's cow; people stand on the deck over water; L1 checks) |
| 1.15-r5-panel-harness | the panel ran in third person, four stands inside geometry, the player attacked at two | lane-1.15-r5-panel-harness.md (5e5e633d: the camera re-asserted and read before every still; stands reject geometry within 2 m and slopes over 45°; tgm and tcai at step 0) |

## The first full batch on Paris (11:00–11:38: deploy 11.8 min, batch 25.7 min; 3 of 6 journeys green, 99 stills)

Readers: the System pane in the frame style but its Settings page a scroll frame; the chart a regional crop; the sky
with shaders on still veiled (hence the bisect); the creature stills framing nothing; the world panel in third person
with the player attacked, near crimson canopies in two classes (the stale tree LOD is the suspect: the lists, the
plugin YAML and the shards hold no Erut or SwampPlant02 ref), flat white water in the flooded forest from a hilltop,
marbled water with pink reflection blotches; the water types 1 of 7 (the tarn) with the rest marbled by the same
reflections and two vantages missing the water.

## The owner's 11:54 reply (#37)

Red or pink leaves are fine if the tree looks reasonable: the crimson-vertex drop is reversed and the hunt turns to
the artificial neon blue-green trees and the pale, washed-out wide-trunk trees that look unrendered (lane
1.15-r5-trees-2). AWS: $28.6 for 1–3 November is too high: the breakdown went to the owner (the Ireland standby $8.07
the top item; four disks; an S3 request churn of ~150k small writes being traced) with three deletions for the owner's
word. No creature without a model (the lizard-steed and mouth-plover stay out).

## The close (in progress)

The LOD rebuilt for the final ESM, the final deploy, the final batch (six journeys), the ten region saves remade, the
hand-over with the stills' verdicts. Open after this round: the residual Community Shaders grey (a feature bisect, one
machine run per feature); the Settings page frame; creature presence in game against the lists; lizard-steed and
mouth-plover forms (the owner's call).
