# Progress

The live status of every chunk, one row each, moved in the commit that changes it. `tools/check_records.py`
(in `make check`) fails when a row disagrees with its part README, its brief or its `checks.md` ledger, or cites
what the repo no longer has.
Status: `todo`, `in progress (evidence; owed)`, `done (evidence)`, `blocked (why)`, `dropped (decision)`. Chunk ids and briefs:
[phases/README.md](phases/README.md).

| Part | Chunk | Title | Status |
|---|---|---|---|
| 0 | 0.0 | Can it be played? Vanilla Skyrim streamed, touch and GameSir controls, a feel probe (G0) | done (the owner's sessions passed; Outcome in docs/phases/0-foundation/0.0-can-it-be-played.md) |
| 0 | 0.1 | Bootstrap: repo, ways of working, lean toolchain, import | done (Outcome in docs/phases/0-foundation/0.1-bootstrap.md; the arrays pulled after #11) |
| 0 | 0.2 | Our stack on the game machine | in progress (the stack installed by stack.py; smoke green (lane-game-18.md); the Argonia cards launch our ESMs dcccfa1; owed: frame times on the Paris g6 against the #16 bar, `stack.py verify --full` 2 bad of 22,574 in argonia-theme (lane-game-21.md)) |
| 0 | 0.3 | The agent's hands: bridge, SKSE build, scenes, runner, deploy, the timed loop | in progress (bridge 50/50; deploy builds SKSE, Papyrus and the base save, SKSE-only DEPLOY OK in 219 s (lane-game-21.md); Papyrus compiled on the machine 9351d1d; owed: the timed edit-deploy-verdict row in game) |
| 0 | 0.4 | The pipeline, the quarantine, the inventory and the first block | in progress (§0-§c done; claywater-walk, claywater-look and quarantine green (lane-game-17.md); owed: the owner's walk of the Claywater block, the Part 0 check-in) |
| 1 | 1.1 | The game-state seam | in progress (L2: c26c042 aae9ac8 0710bee 0c53bee; L4 cosave and dialogue-intercept green (lane-game-17.md), attributes and quest-board green (lane-game-18.md); owed: the Part 1 batch in one pass) |
| 1 | 1.2 | The UI, stage one: Pelagiad, the paper theme, the dialogue window, the journal, our HUD and the chart | in progress (the four views at L3: 2d7dcb5 dd0d5cf; PrismaUI 54658cc; CHRT b14743f; ui-probe green once (lane-game-19.md); owed: our HUD drawn over the load (6a14cb8 not yet effective) (lane-game-21.md), the screen numbers (1.17); the sweep, review, quit and device rows are 1.12's) |
| 1 | 1.3 | Talk and carry, on the sheet | in progress (route b, topics, actions, items: f7ca725 7ccb595; LF83's people 645ddf7 356c0ac; Livia the trader c745ef3; attributes green (lane-game-18.md), livia-sleep green (lane-game-17.md); owed: the Part 1 batch in one pass) |
| 1 | 1.4 | One quest through the journal | in progress (LF83 record, lines, QUST: 979cf55 7ccb595 dfc29b9; lf83-components green (lane-game-19.md); lf83-endings and quest-board green (lane-game-18.md); first-place green (lane-game-17.md); owed: the Part 1 batch in one pass) |
| 1 | 1.5 | Grow, die, rest, save | in progress (life module L2: 4bfe537 f2582ea 0f3eaa4; sitting 48c12a6; rest-is-the-only-save, suspend-save, rest-respawn green (lane-game-17.md); grow-at-rest green once (lane-game-19.md); owed: die-and-recover (red at die, lane-game-21.md); rest-respawn-cleared (respawn until the place is wholly cleared, then never) when a clearable place is built) |
| 1 | 1.6 | Fight on the tuned stack, wired to the sheet | in progress (wiring spec L1 dbf8da4; fight-damage-builds, fight-lock-on, fight-roll-burden, combat-trial-a, croc-den green (lane-game-17.md); fight-archetype green as our records only c413ce5 (lane-game-18.md); owed: the Part 1 batch in one pass) |
| 1 | 1.8 | A play machine you can rely on | in progress (the pool built and running: the play page chooses Paris or Ireland, the owner's IAM paste done (#33), saves seeded to S3 pool/, both standbys on e2c03d5; owed: the owner's play through the pool (#34); saves backup proven) |
| 1 | 1.9 | The front door and loads | done (every row proven: the owner's play test 2, docs/research/2026-10-31/owner-playtest-2.md) |
| 1 | 1.10 | The player character | done (every row proven: the owner's play test 2, docs/research/2026-10-31/owner-playtest-2.md) |
| 1 | 1.11 | Our HUD, rebuilt from the old game's | in progress (in game on argonia-play, docs/research/2026-10-31/owner-playtest-2.md; owed: the owner's look) |
| 1 | 1.12 | The in-game UI: Wind UI under our Argonian patch, the chart, the journal, the dialogue window, the minimap, every device | in progress (the owner's look 1: all 18 findings built, e2c03d5 on both standbys; 11 proven in game, 7 with the owner, #34) |
| 1 | 1.15 | The world, rebuilt | in progress (round 6, 2026-11-04: the owner's 19:05 #41 rulings recorded and built (five rows closed as fine; the yellow smog fog root-caused: our image spaces copied Tropical's rain tint, 7f856d1f; the black swamp's blue is reflected sky, the record takes Dawnguard's dark-water reflectivity, 61509997; the road-look stands were 3.6-10 m off the road, re-derived on the line, 0670560d; creature checks are state reads, 076d7cf1; every look stop takes a six-heading scan and each journey is read as it lands, 6d2ed788); found by the measure: 23 of 24 roads run under their cells' water for up to 46 % (the water footprint held the ground under the level across the road) and the ground stage stood stale from 11-03 while the plan said skip (stamp fixed cf620169): lane roads-dry (causeway and ford rule, planner's call 20:15) running; the batch runs on a spot clone of Paris of a smaller GPU type, argonia-play-4 (owner #42 19:16; Paris's own type has had no spot capacity since 18:10): r6-chain15 on the clone at 0670560d, the ledger closes rows as readers pass them; owed: the batch's reader verdicts per row (checks.md 1.15: 7 proven, 13 owed, 1 superseded), chain16 on the regenerated ground after roads-dry, then the final step (both LOD halves, the saves) and the hand-over on #37; round record docs/research/2026-11-04/round-6.md) |
| 1 | 1.14 | Death, the pile and respawn | todo |
| 1 | 1.16 | The owed integration checks | todo |
| 1 | 1.17 | Frame rate and the screen numbers | todo |
| 1 | 1.7 | The first-place journey and the owner's verdict | in progress (packet drafted, docs/research/2026-10-30/verdict-packet-draft.md; waits on 1.8–1.17, the owner's first play test docs/research/2026-10-31/owner-playtest-1.md) |
| 2 | 2.W1 | Terrain, apron and edges | dropped (decision 0033: superseded by 1.15, the world rebuilt; the proven rows stand in docs/phases/1-core-loop/checks.md) |
| 2 | 2.W2 | Water | dropped (decision 0033: superseded by 1.15, the world rebuilt; the proven rows stand in docs/phases/1-core-loop/checks.md) |
| 2 | 2.W3 | Regions, weather, light, roads and the route graph | dropped (decision 0033: superseded by 1.15, the world rebuilt; the proven rows stand in docs/phases/1-core-loop/checks.md) |
| 2 | 2.W4 | Vegetation, navmesh and LOD | dropped (decision 0033: superseded by 1.15, the world rebuilt; the proven rows stand in docs/phases/1-core-loop/checks.md) |
| 2 | 2.W5 | The slice places, in two waves | todo |
| 2 | 2.W5 wave 1 | Greenspring, The Broke Column, Riverwalk, Lighter Flotilla, two routes | todo |
| 2 | 2.W5 wave 2 | the other eleven slice places | todo |
| 2 | 2.W6 | Performance and the world walk | todo |
| 2 | 2.1 | The sheet whole: races, birthsigns, classes, effects, perks | todo |
| 2 | 2.2 | The UI, stage two: the design system, the windows, the HUD, every screen | todo |
| 2 | 2.3 | Items | todo |
| 2 | 2.4 | People | todo |
| 2 | 2.5 | Dialogue | todo |
| 2 | 2.6 | Trade, services and travel | todo |
| 2 | 2.7 | Combat: the map, DSR measured, timing, the built rows, encounters | todo |
| 2 | 2.8 | Progression, rest and death | todo |
| 2 | 2.9 | Magic | todo |
| 2 | 2.10 | Crafting | todo |
| 2 | 2.11 | Stealth, crime, locks and the Owing | todo |
| 2 | 2.12 | Quests, journal and maps | todo |
| 2 | 2.13 | Swim and climb | todo |
| 2 | 2.14 | Marsh specials: hazards, effect arrows, harvests, materials | todo |
| 2 | 2.15 | Boats | todo |
| 2 | 2.16 | Sound and music | todo |
| 2 | 2.17 | Persistence, the immersion gate and the playthrough | todo |
| 3 | 3.1 | Boot, main menu, loading, settings and controls | todo |
| 3 | 3.2 | Character creation | todo |
| 3 | 3.3 | The opening | todo |
| 3 | 3.4 | Install, release and the owner's permanent setup | todo |
| 3 | 3.5 | First playable | todo |
| 4 | 4.1 | Before scale | todo |
| 4 | 4.2 | Region packets | todo |
| 4 | 4.3 | Narrative lines | todo |
| 4 | 4.4 | Assembled interiors | todo |
| 4 | 4.5 | Systems depth | todo |
| 4 | 4.6 | Final look, polish and release | todo |

Part 4 packets (`4.2-<region>-<n>`), lines (`4.3-<line>`) and depth chunks (`4.5-<system>`) get rows as 4.1 plans them.
