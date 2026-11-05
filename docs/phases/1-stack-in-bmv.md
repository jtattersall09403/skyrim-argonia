# Phase 1: the stack, in BM&V as the default world

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.

The owner's first walk is the whole stack *inside* Black Marsh, so the stack and the default world are one phase.

- **The stack.** `mods/dependencies.json` holds the new list: core (SKSE, Address Library, USSEP, Pandora, OAR,
  the DLL fixes), the collection's 31 mods as rows, FreeClimb, Magic Expanded, BM&V (the ModDB archive from the
  private bucket), Alternate Start - Live Another Life, houseCARL. `stack.py fetch --record` fills the hashes;
  `stage` applies the FOMOD choices; `push` and `stack.ps1 on` lay the hard links; Pandora runs on the machine.
- **Rebase the collection onto 1.7.104.** The collection was pinned for AE 1.6: DAR is replaced by Open
  Animation Replacer, Nemesis by Pandora, and the AE-era DLLs (Stop On Slash, Elden Counter, Animated Armoury's
  DLL if any) are checked for a 1.7.x build or dropped with a note. houseCARL reports conflicts and missing
  masters; the game reaches the main menu with every DLL loaded (SKSE's log).
- **The start.** Our plugin adds a Live Another Life start option that places the player in Black Marsh
  (LAL's addon pattern: a start quest, a marker in a BM&V cell, a line in the statue's dialogue), the opening
  taken from the story's prisoner work-detail premise in its lightest form. If LAL's addon route fails, the
  seed in `papyrus/ARG_StartQuestScript.psc` (a start-game-enabled quest that moves the player) is the fallback.
- **The shutdown.** Our plugin stops what still fires with LAL: the main quest chain from MQ102 on (no dragon
  ever rises), the civil war, the Thieves Guild, Dark Brotherhood and inheritance couriers, World Interaction and
  radiant quests, bounty letters. Method in route order: Start Game Enabled off in an override, story-manager node
  conditions, a startup script that stops the rest. The allow-list of quests that may run (the mods' own
  controller and MCM quests, LAL's, BM&V's) is written in this phase as `mods/allowed-quests.json`; a console
  `sqs`-style listing after 30 in-game days is the proof the owner can take, and the agent proves the override
  diff in xEdit first.
- **The map.** Skyrim's world map shows BM&V's worldspace when the player is in it (BM&V's own map if it ships
  one; otherwise the vanilla map of that worldspace). Doors and boats to Skyrim are left as BM&V made them.
- BM&V's known gap: 203 of its texture-set records name diffuse textures no archive holds
  ([research/bmv](../research/bmv/)); it is left as BM&V ships it unless the owner finds it ugly.
- **Owner test (the first walk):** new game, choose the Black Marsh start, arrive in BM&V; a fight with the
  collection's moveset, a climb, a Morrowind spell from Magic Expanded, a walk between two BM&V places; then wait
  30 days: no dragon, no courier, no civil-war or guild starts; the journal holds only what the allow-list says.
