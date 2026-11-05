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
  alternate-start statue or menu. Our plugin carries a start quest (Start Game Enabled, run before anything else)
  that, on a new game: stops the vanilla intro `MQ101` before its cart scene, opens the race menu for character
  creation, and moves the player to our opening's marker in Black Marsh. In this phase the opening is its lightest
  form: the player wakes on the prisoner work detail at a BM&V place (Lilmoth's dock cell `Dock1` or another
  BM&V exterior picked from the census; BM&V's only link to Skyrim is a ship door placed under the sea, so there
  is no in-world arrival to reuse), with a work-detail outfit and a one-line journal entry. Phase 3 replaces it with
  the authored opening act. The method is how total conversions on Skyrim's engine do it: Enderal ships its own
  master and its own start quest; on top of Skyrim.esm the same effect comes from an `MQ101` override (its
  Start Game Enabled flag and stage-0 fragment) plus our start quest, seeded by
  `papyrus/ARG_StartQuestScript.psc`. The agent proves the record diff in xEdit; the owner sees it in the walk.
- **The shutdown.** Our plugin stops what still fires once Helgen is skipped: the main quest chain from MQ102 on (no dragon
  ever rises), the civil war, the Thieves Guild, Dark Brotherhood and inheritance couriers, World Interaction and
  radiant quests, bounty letters. Method in route order: Start Game Enabled off in an override, story-manager node
  conditions, a startup script that stops the rest. The allow-list of quests that may run (the mods' own
  controller and MCM quests, BM&V's, ours) is written in this phase as `mods/allowed-quests.json`; a console
  `sqs`-style listing after 30 in-game days is the proof the owner can take, and the agent proves the override
  diff in xEdit first.
- **The map.** Skyrim's world map shows BM&V's worldspace when the player is in it (BM&V's own map if it ships
  one; otherwise the vanilla map of that worldspace). Doors and boats to Skyrim are left as BM&V made them.
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
- **An offline 2d interactive map**
- After the census: **an offline interactive 2D map of BM&V's world** (owner, 2026-11-05), for the owner and agents
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
