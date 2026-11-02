# 1.15 round 4: the owner's play test 3 (34 findings, 2026-11-02 21:35, #37) fixed in lanes, one batch on Paris

Rulings: Paris is the only game machine; in-game loops are sped up before any check runs; the LOD rebuild
(terrain, tree, object) is the round's last step. The findings: docs/research/2026-11-02/owner-playtest-3.md.

## Wave 1 (launched 2026-11-02 ~22:00 UTC, briefs under briefs/)

| lane | findings | report |
|---|---|---|
| 1.15-r4-fast-loop | the loop itself (owner: massively faster) | lane-1.15-r4-fast-loop.md (done 0ac3304: infra/gpu-box/round.sh runs a round as one resumable job; shader cache in S3; a settle action replaces fixed waits; one save load per batch; predicted 30–35 min per 10-journey batch against 75–100) |
| 1.15-r4-water | 20, 19 | lane-1.15-r4-water.md |
| 1.15-r4-materials | 16, 17 | lane-1.15-r4-materials.md |
| 1.15-r4-light | 18, 9 | lane-1.15-r4-light.md (57d61ea: fog max 1.0 hid the sky, far under vanilla's class medians, grey zeniths; height fog was a 5 m slab, now a bank below eye height; then 9e492ee: seven mist weather copies by water-level band with their own Community Shaders fog files, every mist region banked between its water and eye height) |
| 1.15-r4-trees | 4, 5, 32 | lane-1.15-r4-trees.md (31c2e32: trees sunk by a measured per-model seat, the mods' own placement the reference; flora with any missing texture dropped; tree families per class, classes now 0.77–0.89 distinct; the teal cypress traced to resource-pack textures, being closed) |
| 1.15-r4-claywater | 3, 22, 23, 25, 29, 31, 1 | lane-1.15-r4-claywater.md (9d9f2a9 79d4b34 75f1f18: a stockade kit scattered as trees, 13 Claywater refs 31 m under the new ground, docks seated on the bed, sign textures never laid; the Claywater save; then b94ef5f: terrain_patch real as pads and bowls read by the ground, materials and renderer; the well, house and stable on pads; the scour pool a bowl under its water) |
| 1.15-r4-roads | 21 | lane-1.15-r4-roads.md |
| 1.12-r4-chart | 26, 14, 12, 30 | lane-1.12-r4-chart.md |
| 1.x-r4-play | 2, 34, 15, 33 | lane-1.x-r4-play.md (done 7948d33: third person, 5,000 gold, Precision camera shake off; 33 left: FreeClimb has no tree filter, trees climb by the 2026-11-01 ruling, the mechanic is the modder's) |
| 1.3-r4-talk | 24, 27, 28 | lane-1.3-r4-talk.md |

## Wave 2 (as wave-1 lanes return)

1.15-r4-creatures (13) launched 22:12; 1.12-r4-menus (6, 7, 8, 10, 11, plus the owner's custom-UI card beside the Wind UI one, 22:06) launched 22:27.

Owner, 22:06: seven screenshots of the tree colours, shiny textures and pebble swathes, routed to the trees and materials lanes.

## The batch

One deploy of main on Paris when the lanes have landed; the journeys the lanes owe (river-steps, tree-seat,
road-look, chart-zoom, claywater-walk, claywater-look, the panel's dawn stills, the save load) in one batch,
crash-prone last; stills to a reader; then the LOD; then the saves remade and the owner told on #37.
