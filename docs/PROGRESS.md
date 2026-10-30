# Progress

The live status of every chunk. One row each; the planner updates rows as lanes start and close.
Status: `todo`, `in progress (lane)`, `done (commit)`, `blocked (why)`, `dropped (decision)`. Chunk ids and briefs:
[phases/README.md](phases/README.md).

| Part | Chunk | Title | Status |
|---|---|---|---|
| 0 | 0.0 | Can it be played? Vanilla Skyrim streamed, touch and GameSir controls, a feel probe (G0) | done (2026-10-29; the owner's sessions passed; the dodge and pad fixes the owner reported go to 0.2 §c) |
| 0 | 0.1 | Bootstrap: repo, ways of working, lean toolchain, import | done (2026-10-29; see the brief's Outcome; the owner answered #11 the same day and the arrays are pulled) |
| 0 | 0.2 | Our stack on the game machine | in progress (game-7: rolls 338-373, backstep 416-428, burden lock; game-8: smoke pad green 75 s, scene twice with no crash, the Stats key is SLASH (0x35), the compass gone in 11/11 stills; red: the Map is Skyrim's world map (chart view not registered), the menus open late behind the pause-hub save, the smoke roll unseen; frame bar owner #16; lane-game-8) |
| 0 | 0.3 | The agent's hands: bridge, SKSE build, scenes, runner, deploy, the timed loop | in progress (§a done live 50/50; §b built, Papyrus compile owed (the CK to install on the machine, #15); §c-§d done; §e the timed loop measured 238 s, a data row to the in-game read with the machine up (game-8); the bridge's `actors` read and the runner's owed steps, lane-game-8) |
| 0 | 0.4 | The pipeline, the quarantine, the inventory and the first block | in progress (§0, §a, §b, §c done; §d: the people run their packages since the navmesh ships with every plugin build (game-8, 6f0bfa5); claywater-walk green to step 7 twice; the night owed on the station house's door off the navmesh (2.W4); lane-game-8) |
| 1 | 1.1 | The game-state seam | in progress (L2 done: c26c042 aae9ac8 0710bee 0c53bee; L4 cosave, dialogue-intercept, quest-board [from batch], game-13) |
| 1 | 1.2 | The UI, stage one: Pelagiad, the paper theme, the dialogue window, the journal, our HUD and the chart | in progress (the four views at L3 with reader passes: 2d7dcb5 dd0d5cf; PrismaUI binding 54658cc; CHRT b14743f; L4 ui-sweep, ui-probe, menus-quit [from batch], game-13) |
| 1 | 1.3 | Talk and carry, on the sheet | in progress (route b, topics, actions, items, AV audit: f7ca725 7ccb595; LF83's people 645ddf7 356c0ac; sheet at game ready 2dab64e; L4 [from batch], game-13) |
| 1 | 1.4 | One quest through the journal | in progress (LF83 record, lines, QUST: 979cf55 7ccb595 dfc29b9; Papyrus 5/5 (game-9); stages 10-40 green twice as components (game-10, 99bd4d5); L4 lf83-*, first-place [from batch], game-13) |
| 1 | 1.5 | Grow, die, rest, save | in progress (life module and adapters L2: 4bfe537 f2582ea 0f3eaa4; sitting 48c12a6 3551f0a; records dbf8da4; L4 grow-at-rest, die-and-recover, rest and suspend saves [from batch], game-13) |
| 1 | 1.6 | Fight on the tuned stack, wired to the sheet | in progress (wiring spec and records L1: dbf8da4; group A verify 0 bad; DSC B/B2 not viable on this stack (f74e2f5); L4 the fight journeys in real places [from batch], game-13) |
| 1 | 1.7 | The first-place journey and the owner's verdict | in progress (brief rewritten to the 2026-10-30 rulings: no soak, no arena, one batch; packet drafted, docs/research/2026-10-30/verdict-packet-draft.md; its [from batch] lines wait on game-13) |
| 2 | 2.W1 | Terrain, apron and edges (the world track starts after 0.4, beside Part 1) | in progress (data done: 82df321 0b9d5a7; world-sample stops 1-3 [from batch]; stop 13 after the CK LOD) |
| 2 | 2.W2 | Water | in progress (designed water done: 1aa04cc 44d5bae; world-sample stops 4-7 and water-swim [from batch]) |
| 2 | 2.W3 | Regions, weather, light, roads and the route graph | in progress (data done: aed4264 e279217 6b220f1; gates, landings, signposts placed 002dca4; L4 world-sample 9-11 and the w3 journeys [from batch]) |
| 2 | 2.W4 | Vegetation, navmesh and LOD | in progress (navmesh 08a88e5, load doors afdbae4, the chart 39a8eb46, vegetation done; L4 world-sample 8 and 12 [from batch]; LOD by the Creation Kit after the batch (owner 2026-10-30)) |
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
