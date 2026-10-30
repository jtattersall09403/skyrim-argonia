# Progress

The live status of every chunk. One row each; the planner updates rows as lanes start and close.
Status: `todo`, `in progress (lane)`, `done (commit)`, `blocked (why)`, `dropped (decision)`. Chunk ids and briefs:
[phases/README.md](phases/README.md).

| Part | Chunk | Title | Status |
|---|---|---|---|
| 0 | 0.0 | Can it be played? Vanilla Skyrim streamed, touch and GameSir controls, a feel probe (G0) | done (2026-10-29; the owner's sessions passed; the dodge and pad fixes the owner reported go to 0.2 §c) |
| 0 | 0.1 | Bootstrap: repo, ways of working, lean toolchain, import | done (2026-10-29; see the brief's Outcome; the owner answered #11 the same day and the arrays are pulled) |
| 0 | 0.2 | Our stack on the game machine | in progress (game-3: install, verify, bridge done; the dodge's zeroed root motion and the 60/45 frame bar open; lane-game-3) |
| 0 | 0.3 | The agent's hands: bridge, SKSE build, scenes, runner, deploy, the timed loop | in progress (§a done live 50/50, 09b1a66 759f37e; §b built, deploy and Papyrus compile owed (CK missing, #15); §c–§e next) |
| 0 | 0.4 | The pipeline, the quarantine, the inventory and the first block | in progress (§0 data model done e62a0e5…9217521; §a pipeline done 33b453f; §c inventory done 63ea3ed; §b journey and §d the block owed on the game machine) |
| 1 | 1.1 | The game-state seam | in progress (native map, core rules, schema, adapters built and L2 green: c26c042 aae9ac8 0710bee; L4 owed) |
| 1 | 1.2 | The UI, stage one: Pelagiad, the paper theme, the dialogue window, the journal, our HUD and the chart | in progress (the four views at L3, reader passes dialogue, journal, HUD: 2d7dcb5 dd0d5cf; §0 probe, §a theme and L4 owed) |
| 1 | 1.3 | Talk and carry, on the sheet | in progress (route b, topics, actions, items, AV audit: f7ca725 7ccb595; LF83's three people written 645ddf7 356c0ac; L4 owed) |
| 1 | 1.4 | One quest through the journal | in progress (LF83 reviewed, lines written, QUST generated: 979cf55 7ccb595 dfc29b9; owner read #14; Papyrus (#15) and L4 owed) |
| 1 | 1.5 | Grow, die, rest, save | todo |
| 1 | 1.6 | Fight on the tuned stack, wired to the sheet | todo |
| 1 | 1.7 | The first-place journey and the owner's verdict | todo |
| 2 | 2.W1 | Terrain, apron and edges (the world track starts after 0.4, beside Part 1) | in progress (data done: 82df321 0b9d5a7; the world sample's L4 owed) |
| 2 | 2.W2 | Water | in progress (designed water done: 1aa04cc 44d5bae; L4 sample owed) |
| 2 | 2.W3 | Regions, weather, light, roads and the route graph | in progress (data done: aed4264 e279217 6b220f1; L4 sample owed) |
| 2 | 2.W4 | Vegetation, navmesh and LOD | in progress (navmesh 08a88e5 and the chart 39a8eb46 done; the CK region generator and LOD blocked on the Creation Kit, #15) |
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
