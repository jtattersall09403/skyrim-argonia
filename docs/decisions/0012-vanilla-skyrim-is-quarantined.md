# 0012: Vanilla Skyrim is quarantined: its world, quests and Nordic systems never reach the player

**Status:** decided 2026-10-27 (follows from 0005 and 0006).

## Context

Our plugin must master `Skyrim.esm` (and normally `Update.esm`, `Dawnguard.esm`, `HearthFires.esm`,
`Dragonborn.esm` and the Creation Club masters the runtime ships) to use their records and archives. Loaded
masters bring running systems: the Helgen intro, the main and civil-war quests, dragon attacks, radiant quests,
couriers (Dark Brotherhood letter, inheritance), word walls and shouts, the Dragonborn identity, standing
stones, Skyrim races' Nordic voice lines, guards' arrow-in-the-knee chatter, vanilla music, the perk
constellation menu, loading screens, the main menu, Skyrim's world map and the Tamriel worldspace itself.

## Decision

1. **New game starts in Argonia** through our own start quest (the Enderal / alternate-start pattern): the
   vanilla intro (`MQ101`) never runs; the player never sees Tamriel's worldspace or Helgen.
2. **Vanilla quests and story managers are stopped or prevented** by data (start-game-enabled flags off in an
   override, story manager branch conditions) and checked by a bridge test that lists running quests after a
   new game and after 1, 10 and 50 in-game days; the list must equal our allow-list.
3. **Dragons, shouts, word walls, Dragonborn, Sovngarde, the civil war, standing stones** do not exist for the
   player (removed from spawns, menus and text). The Shout key/menu is unbound or repurposed (Hist communion
   powers, old 0042, can use the power slot).
4. **Voice:** Argonia is unvoiced text dialogue (old 0139/0143); NPCs use voice types without Nordic barks:
   generic combat/idle barks are filtered to an allow-list or silenced. Text-only lines that go through the
   vanilla dialogue path need silent voice files of the right length (Fuz Ro D-oh pattern) unless the PrismaUI
   dialogue view handles timing.
5. **The immersion inventory (0006) includes every vanilla system above** with a verdict and a check.
6. **Vanilla content may be borrowed, not banned** (owner, 2026-10-29: "we aren't shipping them, just using them
   from the base game"): a vanilla interior, mesh or record the player's own install provides may host or furnish our
   places when its review passes: what the player sees (architecture, props, signage), any displayed name, and what
   comes placed with it. Invisible identifiers (EditorIDs, FormIDs) need no review. A Nordic-looking shell fails
   unless re-dressed until it passes.

## Consequences

- An install with other Skyrim mods present is unsupported; the modlist installs into a clean profile.
