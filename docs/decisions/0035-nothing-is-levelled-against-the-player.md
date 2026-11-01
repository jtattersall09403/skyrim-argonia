# 0035 — Nothing is ever levelled against the player

**Date:** 2026-11-01 · **Status:** accepted (owner ruling in the 1.15 session; a golden rule)

## Decision

1. **Nothing in Argonia scales to the player's level:** no creature, enemy, loot, chest, trap, reward or price.
   A thing is what it is wherever it stands; the same chest holds the same thing at level 1 and level 100.
2. **Danger bands are fixed in the world.** A band says how tough a stretch is; the player grows into the harder
   bands by getting stronger, never the other way round.
3. **Skyrim's levelled machinery is used only as a random pick at a fixed level.** Levelled lists (LVLN, LVLI)
   may choose among entries, but every entry's level is 1 so the player's level never gates it; encounter zones
   carry min = max; actors carry a fixed level with PC-level-mult off, including actors templated on a mod's
   creature whose own record scales (the stats come from our record, not the template).
4. **An L1 check enforces it:** no record our plugins write carries a PC-level multiplier, a levelled entry
   above level 1, a zone with min ≠ max, or a template that imports scaling stats.

## Why

- The owner's design (decision 0023's world, the danger bands, the old project's 0062 "fixed loot and enemies,
  never levelled"): the world is a fixed place the player learns, the Morrowind and Dark Souls way.
- The first creature records of 1.15 §g used Skyrim's "calculate from all levels ≤ player" flag with each entry at
  its band's level, so a high band's list would yield nothing to a low-level player and grow as they levelled: the
  machinery's default is the opposite of our rule, so the rule needs a check, not a habit.

## Consequences

- 1.15 §g's lists, actors and zones are rewritten to the rule with the check; every later chunk that writes
  loot, chests, merchants or rewards inherits the check.
