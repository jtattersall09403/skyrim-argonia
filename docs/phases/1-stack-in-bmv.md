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
  5403,-6109,66, a triangle centre of BM&V's navmesh 079823; a persistent reference in the world's persistent cell),
  takes everything away, opens the race menu, then dresses the player in the vanilla roughspun tunic and footwraps
  (`ClothesPrisonerTunic`, `ClothesPrisonerShoes`) and sets stage 10, the one journal line ("You wake on the Lilmoth
  work detail, a prisoner in roughspun with nothing to your name."). Records: `plugin/Argonia/` (Spriggit YAML,
  seeded by `tools/ArgoniaPlugin`, `make plugin-seed`); `make plugin` builds `out/Argonia.esp`; `make plugin-check`
  proves the round trip and reads the ESP back into [the records table](../research/skyrim/argonia-esp-records.md).
  Owed: `records_jobs.sh papyrus` on the play machine once the CK is there (it already compiles `papyrus/*.psc`;
  `deploy.sh` sends `out/*.esp` and the `.pex` to `C:\argonia\ours`, and `stack.ps1` now lays `Argonia.esp` last and
  enabled), then the owner's walk. The race menu may show the bound-hands pose (LAL blanks `sPosePlayerRaceSexMenu`
  in its ini); left as Skyrim does it unless the owner minds. Phase 3 replaces the opening with the authored act.
- **The shutdown. Built off game (2026-11-05); owed: the walk's 30-day check.** Route order as planned, and the first
  two routes were enough, no startup script: (1) Start Game Enabled off in overrides of 85 vanilla openers (the main
  quest's MQ00 and MQ103, the civil war, Thieves Guild, Dark Brotherhood, guild, misc and Daedric openers, Dawnguard's
  DLC1Init, DLC1VQ00 and radiant, Dragonborn's DLC2Init and DLC2MQ00, Hearthfire's house quests); each override is
  the load order's winner with its player-visible text removed; (2) 102 story-manager nodes, children of the event
  nodes, gated by a first condition `GetGlobalValue ARG_VanillaStoryManager == 1` (the global is 0): couriers
  (inheritance, guild letters), World Interactions, bounties, radiant and favour quests, world encounters, main-quest
  dragons, civil-war garrisons and scenes, guild radiants, Dawnguard's vampire attacks and scouts, Dragonborn's cultist
  ambush and world encounters, Hearthfire's letters. MQ102 on never starts: only MQ101 starts it. The list and its
  reasons: `tools/ArgoniaPlugin/shutdown.json`; what stays: `mods/allowed-quests.json` (576 Start Game Enabled quests
  in the staged load order: 85 off, 153 the mods', 338 vanilla dialogue, dungeon and mechanics quests that start
  nothing by themselves). Left on, owner calls: the Creation Club content in the owner's install (Fish, Saints &
  Seducers, Curios, Survival; gating them would make their files masters), and two nodes Mutagen cannot copy
  (their quests never start here).
- **The map.** Skyrim's world map shows BM&V's worldspace when the player is in it (BM&V's own map if it ships
  one; otherwise the vanilla map of that worldspace). Doors and boats to Skyrim are left as BM&V made them.
  Read 2026-11-05: BM&V's `BlackMarsh` worldspace carries map data (camera heights 50000 to 80000, bounds) and
  `Argonia.esp` keeps it unchanged, but the staged BM&V files hold no terrain LOD, so the map may show little but
  the markers; owed: the owner looks in the walk, and LOD is generated only if it is bare.
- BM&V's known gap: 203 of its texture-set records name diffuse textures no archive holds
  ([research/bmv](../research/bmv/)); it is left as BM&V ships it unless the owner finds it ugly
- In parallel: **The census, into the story data.** BM&V's locations, cells, NPCs, factions and quests are read from
  `Black Marsh.esm` (Spriggit on the build VM) into new tables of the one relational store
  (`story/data/schema.sql`, loaded by `tools/argonia_world/db.py` like every other table): `bmv_location`,
  `bmv_cell`, `bmv_npc`, `bmv_faction`, `bmv_quest`, keyed by form key, with editor id, name, worldspace and
  position. Our designed places, people and factions are then **linked, not copied**: mapping tables
  `place_bmv_location`, `npc_bmv_npc` and `faction_bmv_faction` say which BM&V record a designed row lands on, and
  our own authored records carry their form keys in `mod_form` as the Magic Expanded forms already do. The quest
  skills read the mapping, so a quest written against a designed place resolves to a BM&V cell. Where BM&V has no
  place for a designed one, the row is mapped to the nearest BM&V place or marked waiting.
- **An offline 2d interactive map**, after the census, of BM&V's world (owner, 2026-11-05), for the owner and agents
  to explore, linked to the mined records: pan and zoom over each BM&V worldspace, the land drawn from BM&V's own
  terrain heights and water, every exterior cell gridded, each settlement, door, NPC placement and quest-relevant
  place clickable to its census row (form key, editor id, name, settlement, NPCs there) and to our designed place
  mapped onto it. A generator under `tools/` builds one self-contained HTML page into `out/bmv-map/` from
  `story/data` and the ESM; the rendered terrain image is derived from BM&V's files, so it is never committed
  (decision 0003): the owner gets it as a private page, agents open the local build. Searchable by name and editor
  id; coordinates shown in cell grid and game units, so an agent can turn a click into a marker position.
- **Loop**: read the files that the game will consume and verify (to the extent that you can) that everything you intended to implement has been implemented correctly. If not, diagnose, fix, then repeat this loop until your read of the built game files (esm and plugin and whatever else) does meet this bar. But do not run the actual game yourself, just read/mine from the game files that you build. *Then* pass on to the owner. For the census mine, do a loop between a miner and reviewer, where the reviewer thinks critically about what the miner might have missed and provides feedback. You as the planner use your judgment to decide when that loop exits. We need to know we have information about every place from the BM&V mod, and we have enough information about every place to meet the requirements for our goal (and for being able to properly author and review our quests).
- **Owner test (the first walk, the first owner test since the pivot):** both cards on the play page, Vanilla
  Skyrim (a quick check that the stream and the game run) and Argonia. On Argonia, a new game: character creation, then straight into Black Marsh with no Helgen and no start menu; a fight with the
  collection's moveset, a climb, a Morrowind spell from Magic Expanded, a walk between two BM&V places; then wait
  30 days: no dragon, no courier, no civil-war or guild starts; the journal holds only what the allow-list says.
