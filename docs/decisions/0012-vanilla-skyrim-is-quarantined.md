# 0012: Vanilla Skyrim is quarantined: its world, quests and Nordic systems never reach the player

**Status:** decided 2026-10-27; applies to the new world ([0042](0042-the-new-world-is-the-project.md)). Owner,
2026-11-05: a new game starts in our own opening, with no alternate-start mod.

## Context

Our plugin must master `Skyrim.esm` (and normally `Update.esm`, `Dawnguard.esm`, `HearthFires.esm`,
`Dragonborn.esm` and the Creation Club masters the runtime ships) to use their records and archives. Loaded
masters bring running systems: the Helgen intro, the main and civil-war quests, dragon attacks, radiant quests,
couriers (Dark Brotherhood letter, inheritance), word walls and shouts, the Dragonborn identity, standing
stones, Skyrim races' Nordic voice lines, guards' arrow-in-the-knee chatter, vanilla music, the perk
constellation menu, loading screens, the main menu, Skyrim's world map and the Tamriel worldspace itself.

## Decision

1. **A new game starts in our world** through our own start quest: the vanilla intro (`MQ101`) never runs; the
   player never sees Tamriel's worldspace or Helgen.
2. **Vanilla quests and story managers are stopped or prevented** by data (start-game-enabled flags off in an
   override, story manager branch conditions) and checked by listing the running quests after a new game and
   after 1, 10 and 50 in-game days; the list must equal our allow-list.
3. **Dragons, shouts, word walls, Dragonborn, Sovngarde, the civil war and standing stones** do not exist for the
   player (removed from spawns, menus and text).
4. **Voice:** our talk is unvoiced text dialogue; NPCs use voice types without Nordic barks, and generic combat
   and idle barks are filtered to an allow-list or silenced. Text-only lines on the vanilla dialogue path use the
   Fuz Ro D-oh pattern for silent timing.
5. **Vanilla content may be borrowed, not banned** (owner, 2026-10-29: "we aren't shipping them, just using them
   from the base game"): a vanilla interior, mesh or record the player's own install provides may host or furnish
   our places when it reads as Black Marsh: what the player sees (architecture, props, signage), any displayed
   name, and what comes placed with it. Invisible identifiers (EditorIDs, FormIDs) need no review. A
   Nordic-looking shell is judged as [0006](0006-black-marsh-immersion-nothing-we-add-is-nordic.md) says.

## Consequences

- An install with other Skyrim mods present is unsupported; the modlist installs into a clean profile.
