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
  stage 0, no aliases, scenes or Helgen stages, whose fragment (`papyrus/ARG_QF_MQ101.psc`) takes everything away,
  moves the player to our XMarker `ARG_OpeningMarker` on Lilmoth's dock (BM&V `BlackMarsh` worldspace, cell `005A21` (7,-1), one of Lilmoth's cells in the census, at 30901,-2903,3: triangle 14's centre of BM&V's navmesh 07EEF8, the winner, on the fishing dock beside Black Marsh North's "Lilmoth Dock" map marker 082193 at 30909,-2852; a persistent reference in the world's persistent cell; our worldspace override starts from Black Marsh North's record and that plugin is a master after Black Marsh.esm; the read-back checks the navmesh and masters). **Moved 2026-11-06 (owner's walk: New Game landed at Hereguard Plantation):** the old spot, cell `Dock1` (1,-2) at 5403,-6109, is Hereguard Plantation's dock (its map marker 09348E at 5332,-3634), not Lilmoth's,
  starts `ARG_Opening` and stops `MQ101`; `ARG_Opening`'s script (`papyrus/ARG_StartQuestScript.psc`) then, in game
  mode, forces third person, strips the player (`UnequipAll`, `RemoveAllItems`: the Player NPC's default outfit `ArmorIronAllOutfit`, with its iron helmet, is put on when the player's 3D loads, after stage 0's strip, so the owner's race menu showed a helmet, 2026-11-06), opens the race menu, then dresses the player in the vanilla roughspun tunic and footwraps
  (`ClothesPrisonerTunic`, `ClothesPrisonerShoes`), gives the **test kit for the walk phases** (removed with the authored opening in Phase 3: the Imperial sword `0135B8` and Imperial light shield `013AB2`, no Nordic item, and fourteen Magic Expanded spells from `Magic.esp`, which has no Levitate: Mark, Recall, Jump, Slowfall, Water Walking, Fire Touch, Damage Health, Force, Burden, Teleport, Analyze, Dispel Self, Soul Trap Mass, Bound Shield) and sets stage 10, the one journal line ("I woke as a prisoner on the work detail at Lilmoth. I own nothing but the roughspun I wear.", through
  text-review) and shows objective 10, "Stay with the work detail on Lilmoth's dock" (**owner, 2026-11-07: the Quests menu was empty**: Skyrim lists an active quest only once one of its objectives is shown, as every vanilla stage that writes a log line also shows one; the log entry alone never listed "The Work Detail"), forcing third person again (third person is the default: `fMinCurrentZoom` in `stack.ps1` stops the
  zoom before first person). **New Game did nothing (owner, 2026-11-06), fixed:** the menu stayed up with its music
  because the player was never moved into a cell. MQ101's stage 0 had no log entry, and a quest fragment binds to a
  stage's log entry (VMAD: stage, entry index), so the fragment never ran: the game started (Papyrus.0.log, 15:55:07,
  SkyUI and MCM quests initialised) with no `ARG_` line, `ARG_Opening` never started, and nothing moved the player,
  whom the engine leaves in no cell until MQ101 moves them. LAL's MQ101 stage-0 fragment does `Player.MoveTo(NewStartMarker)`
  itself and then starts its chargen quest (its `qf_mq101_0003372b.psc`, Fragment_332, read from its BSA and deleted);
  we now do the same, and stage 0 of both quests carries one empty log entry (`QSDT`), checked by the read-back.
  Papyrus logging (`bEnableLogging`, `bEnableTrace`, `bLoadDebugInformation`) is set in `stack.ps1`'s Set-GameWindow. Records: `plugin/Argonia/` (Spriggit YAML,
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
- **Weapon drawn: the normal run (owner's walk 2, 2026-11-07).** AMMCO.esp (Arena Movement, Mern edit, owner #53) wins
  `NPC_1HM_MT` and `NPC_2HM_MT` with run 170 and 130, which the owner felt as a fast walk. `Argonia.esp` overrides both
  (tools/ArgoniaPlugin/Combat.cs) with Dark Souls Movement's run, 300 every way, the same as the sheathed run
  (`NPC_Default_MT`, Dark Souls Movement); walk and turn speeds stay AMMCO's. Bows stay AMMCO's (run 300).
- **Combat and HUD after walk 2 (2026-11-07).** TrueHUD's MCM defaults in the staged `settings.ini` (row `truehud`;
  display mode 1 is "Dynamic", the earlier 2 was "In combat"), and MCM Helper's user file
  `MCM/Settings/TrueHUD.ini` absent on argonia-play (searched 2026-11-08), so they hold. No health regen for the player: an ability
  `ARG_NoHealthRegen` (Value Modifier, HealRateMult -100) on the Player's base record, no script. Compass on in
  `stack.ps1`; quest markers stay off. Elden Parry's window end 0.5 s (stream delay; row `elden-parry`). The standing
  dodge is Dynamic Dodge's backstep clip (our 80110-80140 submods lay its `StepDodgeBack.hkx`), cut to its first
  push (owner, 2026-11-08): its AMR `animmotion` keys travel 1.86 m in 0 to 0.333 s, then 3.56 m more to 0.833 s;
  `infra/gpu-box/backstep.py`, run at stage time on the player's own copy (row `first_push`), holds every key after
  0.333 s at the first push's end, so it travels 1.86 m and the clip still plays whole (0.833 s). Measured
  alternatives: the vanilla DodgeBack 2.96 m in one 0.9 s push, TK Dodge's step 4.29 m, Elder Souls' backward
  dodge 4.97 m, Dynamic Dodge's diagonal steps 5.45 m. A dodge tapped during an attack (80210-80240) is the
  author's back roll, 5.95 m, unchanged. The backstab is Rim Parry's: the
  light bash (block held, attack tapped) within 30 degrees of straight behind, cast through Payload Interpreter; Elden
  Parry's parry from behind does nothing because its parry only answers hits from the front. Magistrate Levitate
  (Nexus 24695, data only) laid; its Levitate is in the test kit.
- **The map.** Owner, 2026-11-07 walk: in BlackMarsh the M map shows Skyrim's Tamriel with BM&V's markers. Measured
  2026-11-08 (research lane): BM&V's four worldspaces have no parent and an all-zero MNAM (no usable map bounds; only
  the camera heights 50000 to 80000 are set), and SkyrimSE.exe's `sMapWorldDefaultWorldSpace` default is Tamriel, so
  the map falls back to Tamriel (inferred; the plan's first owner check settles it). BM&V does ship terrain LOD (levels
  4 to 32, .btr under meshes/terrain/<world>, object LOD .bto for three worlds), but only Valenwood has a
  `lodsettings/*.lod` file. The earlier line here ("map data ... bounds", "no terrain LOD") was wrong. The fix is
  built as block W-wrld-map in [Phase 4](4-first-act-built.md) (2026-11-08: MNAM pan boxes, derived lodsettings,
  "Lilmoth" marker name; owner check owed); the fallbacks in [Phase 5](5-scale.md). Doors and
  boats to Skyrim are left as BM&V made them.
- BM&V's known gap: 203 of its texture-set records name diffuse textures no archive holds
  ([research/bmv](../research/bmv/)); it is left as BM&V ships it unless the owner finds it ugly
- BM&V's window gap (owner walk 2026-11-07, "Lilmoth docks windows look like they have some piece missing"): BM&V
  ships 105 loose NIFs edited for Enhanced Lighting (ELFX), many at vanilla paths (Solitude, Whiterun, Riften houses,
  imperial tents), naming `textures\effects\ELFX\windows\*` and `cubemaps\tundra_e.dds`, which nothing staged holds;
  the panes draw flat pale blue. In BM&V's worlds 14 bases, 48 refs use them: Lilmoth 10 (5 Solitude houses, a pot),
  tents 39 (Murkwood, Temple, Black Marsh North's marsh, Murkmire, Longmont, Castle, Valenwood), Riften farmhouses 2
  (Dock2), 2 single Valenwood refs. Fixed in the stage: the bmv row's `drop` in `mods/dependencies.json` removes the
  62 ELFX meshes whose path the game's own archives also hold, so the vanilla mesh draws (all 14 bases, 48 refs). The
  other 43 matches (BM&V's own ELFX\* meshes, terrain .bto, rocks) shadow nothing and are kept; none is placed in
  Lilmoth. Owner check owed on the next walk.
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
