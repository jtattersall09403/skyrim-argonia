# Phase 1: the stack, in BM&V as the default world, and foundational research

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

The owner's first walk is the whole stack *inside* Black Marsh, so the stack and the default world are one phase.

- **The stack.** `mods/dependencies.json` holds the new list: core (SKSE, Address Library, USSEP, Pandora, OAR,
  the DLL fixes), the collection's 31 mods as rows, FreeClimb, Magic Expanded, BM&V (the ModDB archive from the
  private bucket), houseCARL. `stack.py fetch --record` fills the hashes;
  `stage` applies the FOMOD choices; `push` and `stack.ps1 on` lay the hard links; Pandora runs on the machine.
- **Rebase the collection onto 1.7.104.** The collection was pinned for AE 1.6: DAR is replaced by Open
  Animation Replacer, Nemesis by Pandora, and the AE-era DLLs (Stop On Slash, Elden Counter, Animated Armoury's
  DLL if any) are checked for a 1.7.x build or dropped with a note. houseCARL reports conflicts and missing
  masters; every SKSE DLL is checked from its file (the SKSE plugin version data it exports, its Address Library
  use, its declared runtimes) for 1.7.104, without running the game.
- **The start: a new game goes straight into our own opening, Enderal-style.** No Helgen, no cart, no
  alternate-start statue or menu. **Built off game (2026-11-05); owed: the compile and the walk.** How Live Another
  Life does it, read from its esp (Nexus 272 file 729409, read and deleted): the engine starts `MQ101` on a new game
  (it is not Start Game Enabled, in Skyrim.esm or LAL), and LAL adds a stage-0 fragment to `MQ101` that diverts to its
  own chargen quest. `Argonia.esp` does the same with nothing of Helgen kept: its `MQ101` override is one start-up
  stage 0, no aliases, scenes or Helgen stages, whose fragment (`papyrus/ARG_QF_MQ101.psc`) starts `ARG_Opening` and
  stops `MQ101`. `ARG_Opening`'s script (`papyrus/ARG_StartQuestScript.psc`) waits for game mode, moves the player to
  our XMarker `ARG_OpeningMarker` on Lilmoth's dock walkway (BM&V `BlackMarsh` worldspace, cell `Dock1` (1,-2), at
  5403,-6109,66, a triangle centre of BM&V's navmesh 079823; a persistent reference in the world's persistent cell; re-derived 2026-11-05 with BM&V staged whole: Black Marsh North.esp overrides the `BlackMarsh` worldspace and cell `Dock1` but not navmesh 079823 or the pier, so the marker stays put on the winning navmesh at its height, our worldspace override starts from Black Marsh North's record and that plugin is a master after Black Marsh.esm; the read-back checks all three),
  takes everything away, opens the race menu, then dresses the player in the vanilla roughspun tunic and footwraps
  (`ClothesPrisonerTunic`, `ClothesPrisonerShoes`) and sets stage 10, the one journal line ("I woke as a prisoner on the work detail at Lilmoth. I own nothing but the roughspun I wear.", through
  text-review). Records: `plugin/Argonia/` (Spriggit YAML,
  seeded by `tools/ArgoniaPlugin`, `make plugin-seed`); `make plugin` builds `out/Argonia.esp`; `make plugin-check`
  proves the round trip and reads the ESP back into [the records table](../research/skyrim/argonia-esp-records.md).
  Owed: `records_jobs.sh papyrus` on the play machine once the CK is there (it already compiles `papyrus/*.psc`;
  `deploy.sh` sends `out/*.esp` and the `.pex` to `C:\argonia\ours`, and `stack.ps1` now lays `Argonia.esp` last and
  enabled), then the owner's walk. The race menu keeps the standing pose: our own `plugin/Argonia.ini` blanks
  `sPosePlayerRaceSexMenu` as LAL's ini does (ruling via the coordinator, 2026-11-05); `make plugin` copies it to
  `out/`, `deploy.sh` sends it and `stack.ps1` lays it beside the ESP. Phase 3 replaces the opening with the authored act.
- **The shutdown. Built off game (2026-11-05); owed: the walk's 30-day check.** Route order as planned, and the first
  two routes were enough, no startup script: (1) Start Game Enabled off in overrides of 92 openers (the main
  quest's MQ00 and MQ103, the civil war, Thieves Guild, Dark Brotherhood, guild, misc and Daedric openers, Dawnguard's
  DLC1Init, DLC1VQ00 and radiant, Dragonborn's DLC2Init and DLC2MQ00, Hearthfire's house quests, and the free Creation Club openers: Fishing's Fish_MQ1, Crab_MQ1 and radiant quests, Saints & Seducers' QuestA, Staada and two misc quests); each override is
  the load order's winner with its player-visible text removed; (2) 105 story-manager nodes, children of the event
  nodes, gated by a first condition `GetGlobalValue ARG_VanillaStoryManager == 1` (the global is 0): couriers
  (inheritance, guild letters), World Interactions, bounties, radiant and favour quests, world encounters, main-quest
  dragons, civil-war garrisons and scenes, guild radiants, Dawnguard's vampire attacks and scouts, Dragonborn's cultist
  ambush and world encounters, Hearthfire's letters, Saints & Seducers' world encounters. MQ102 on never starts: only MQ101 starts it. The list and its
  reasons: `tools/ArgoniaPlugin/shutdown.json`; what stays: `mods/allowed-quests.json` (578 Start Game Enabled quests
  in the staged load order: 92 off, 148 the mods' (Valenwood.esp's two arrival-greeting quests kept as BM&V's world; Black Marsh North.esp and the Bosmer armour master hold no quests or nodes; Survival's only quest is the mode itself, Curios' only one its
  stock), 338 vanilla dialogue, dungeon and mechanics quests that start nothing by themselves). The four free
  Creation Club files are masters (ruling via the coordinator, 2026-11-05). Two nodes (MG01ShoutNode,
  CompanionsJorrvaskrTheftNode) hold GetVMQuestVariable conditions that Spriggit 0.41's YAML loses one of; `make
  plugin` re-copies their conditions from the load order's winners after deserialising, and the read-back proves
  the count against the winners.
- **The map.** Skyrim's world map shows BM&V's worldspace when the player is in it (BM&V's own map if it ships
  one; otherwise the vanilla map of that worldspace). Doors and boats to Skyrim are left as BM&V made them.
  Read 2026-11-05: BM&V's `BlackMarsh` worldspace carries map data (camera heights 50000 to 80000, bounds) and
  `Argonia.esp` keeps it unchanged, but the staged BM&V files hold no terrain LOD, so the map may show little but
  the markers; owed: the owner looks in the walk, and LOD is generated only if it is bare.
- BM&V's known gap: 203 of its texture-set records name diffuse textures no archive holds
  ([research/bmv](../research/bmv/)); it is left as BM&V ships it unless the owner finds it ugly
- In parallel: **The census, into the story data.** Redone 2026-11-05 over the whole of BM&V
  ([census](../research/bmv/census.md)): the first pass read `Black Marsh.esm` alone, from a trimmed BM&V. BM&V is
  four plugins (BosmerArmorMATY743.esm, Black Marsh.esm, Black Marsh North.esp, Valenwood.esp);
  `tools/argonia_world/bmv_census.py build` reads them in load order with its own reader (`esm.py`), the last
  version of a form winning and a deleted winner removing it, each row keeping its defining master's form key with
  `plugin` and `overridden_by`. It found 10 worldspaces (5 BM&V's own: BlackMarsh, BlackMarsh2, BlackMarshNorth
  "Thorn", an empty UnderDark, Valenwood; 10,530 LAND cells, 36.1 km², 94% of Skyrim's Tamriel measured the same way),
  11,561 cells, 674 actor bases, 2,869 placements, 241 load doors, 40 BM&V map markers, 12 books, 5 quests,
  grouped into 86 settlements and 2 sites. `verify` is the completeness proof: per plugin and type the census
  accounts for every WRLD, CELL, LAND, ACHR, NPC_, FACT, QUST, LCTN, BOOK, load door and map marker (byte-walk
  count = read = in census + overridden later + deleted). The ways in: Dawnstar's Windpeak Inn's book portal to
  Lilmoth (Black Marsh North.esp deletes the old undersea Nordic door), Cragslane Cavern's rewired door into
  BlackMarsh2, Riverwood's Sleeping Giant Inn's two portals and a Tamriel cave into Valenwood; ships and book
  portals between the Black Marsh worlds; Valenwood joins none of them. Thorn is now mapped (high); nine designed
  places still wait (no record of the four files names them); story/lore has no Valenwood place. Black Marsh
  North.esp deletes ten placements the Act I records cited and peoples Helstrom: the citations are updated (census
  §Changed citations). Owed: the MQ05 hall (BMN puts merchants in it) to the quest writer; Valenwood's two
  start-game-enabled quests against the shutdown; display names for unmarked settlements. Reviewer rounds: census §Review rounds.
- In parallel: **An offline 2d interactive map** of BM&V. Redone 2026-11-05 over all four plugins. `make map`
  (tools/bmv_map) writes one self-contained page, `out/bmv-map/index.html` (about 9 MB, no network), and then
  checks it: a switcher over all 10 worldspaces, the land drawn from the load order's winning LAND (32 px a cell,
  Valenwood 16), with a hillshade and water; layers for settlements, load doors (book portals marked), people and
  creatures, navmesh, BM&V's own map markers, our places by confidence and our markers. `verify` reads the page back:
  every census cell, settlement, door, placement and map marker of each worldspace is on it, and every exterior cell
  with LAND is drawn. `ARG_OpeningMarker` still stands on Lilmoth's pier (`DLC2RRDockPier01`, 005A9F). The page is
  derived from BM&V's files, so it is never committed (decision 0003). Rebuild after the census or the plugin changes.
- **Loop**: read the files that the game will consume and verify (to the extent that you can) that everything you intended to implement has been implemented correctly. If not, diagnose, fix, then repeat this loop until your read of the built game files (esm and plugin and whatever else) does meet this bar. But do not run the actual game yourself, just read/mine from the game files that you build. *Then* pass on to the owner. For the census mine, do a loop between a miner and reviewer, where the reviewer thinks critically about what the miner might have missed and provides feedback. You as the planner use your judgment to decide when that loop exits. We need to know we have information about every place from the BM&V mod, and we have enough information about every place to meet the requirements for our goal (and for being able to properly author and review our quests).
- **Owner test (the first walk, the first owner test since the pivot):** both cards on the play page, Vanilla
  Skyrim (a quick check that the stream and the game run) and Argonia. On Argonia, a new game: character creation, then straight into Black Marsh with no Helgen and no start menu; a fight with the
  collection's moveset, a climb, a Morrowind spell from Magic Expanded, a walk between two BM&V places; then wait
  30 days: no dragon, no courier, no civil-war or guild starts; the journal holds only what the allow-list says.
