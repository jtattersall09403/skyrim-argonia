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
| 1 | 1.2 | The UI, stage one: Pelagiad, the paper theme, the dialogue window, the journal, our HUD and the chart | in progress (the four views at L3: 2d7dcb5 dd0d5cf; PrismaUI 54658cc; CHRT b14743f; ui-probe green once (lane-game-19.md); owed: ui-sweep (favourites), menus-quit (no MainMenu after quit), ui-review, our HUD drawn over the load (6a14cb8 not yet effective) (lane-game-21.md)) |
| 1 | 1.3 | Talk and carry, on the sheet | in progress (route b, topics, actions, items: f7ca725 7ccb595; LF83's people 645ddf7 356c0ac; Livia the trader c745ef3; attributes green (lane-game-18.md), livia-sleep green (lane-game-17.md); owed: the Part 1 batch in one pass) |
| 1 | 1.4 | One quest through the journal | in progress (LF83 record, lines, QUST: 979cf55 7ccb595 dfc29b9; lf83-components green (lane-game-19.md); lf83-endings and quest-board green (lane-game-18.md); first-place green (lane-game-17.md); owed: the Part 1 batch in one pass) |
| 1 | 1.5 | Grow, die, rest, save | in progress (life module L2: 4bfe537 f2582ea 0f3eaa4; sitting 48c12a6; rest-is-the-only-save, suspend-save, rest-respawn green (lane-game-17.md); grow-at-rest green once (lane-game-19.md); owed: die-and-recover (red at die, lane-game-21.md); rest-respawn-cleared (respawn until the place is wholly cleared, then never) when a clearable place is built) |
| 1 | 1.6 | Fight on the tuned stack, wired to the sheet | in progress (wiring spec L1 dbf8da4; fight-damage-builds, fight-lock-on, fight-roll-burden, combat-trial-a, croc-den green (lane-game-17.md); fight-archetype green as our records only c413ce5 (lane-game-18.md); owed: the Part 1 batch in one pass) |
| 1 | 1.7 | The first-place journey and the owner's verdict | in progress (packet drafted, docs/research/2026-10-30/verdict-packet-draft.md; waits on 1.2's and 1.5's reds and the distant terrain (2.W4)) |
| 2 | 2.W1 | Terrain, apron and edges (the world track starts after 0.4, beside Part 1) | in progress (data: 82df321 0b9d5a7; world-sample green once on London, stops 1-3 first (lane-game-21.md); owed: stop 13, the distant view, after the xLODGen LOD is restored) |
| 2 | 2.W2 | Water | in progress (designed water: 1aa04cc 44d5bae; world-sample stops 4-7 green (lane-game-19.md); water-swim dropped, swimming is base Skyrim (d66900f); water-budget a draft) |
| 2 | 2.W3 | Regions, weather, light, roads and the route graph | in progress (data: aed4264 e279217 6b220f1; gates, landings, signposts 002dca4; w3-crime and w3-interior-sun green (lane-game-17.md); the border push (s09) green in world-sample's London run (lane-game-21.md); weather stills dropped (d66900f)) |
| 2 | 2.W4 | Vegetation, navmesh and LOD | in progress (navmesh 08a88e5, load doors afdbae4, the chart 39a8eb46, vegetation done; LOD is xLODGen's (owner 2026-10-30): the terrain made on the retired machine was lost, regenerated on argonia-play-london (lod.sh archive, 8baf1e0); owed: the archive, its restore on argonia-play and a Claywater still; w4-veg-densest a draft) |
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
