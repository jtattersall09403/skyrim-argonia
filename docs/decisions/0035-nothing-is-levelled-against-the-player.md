# 0035: Nothing is ever levelled against the player

**Status:** decided 2026-11-01 (owner ruling; a golden rule).

## Decision

1. **Nothing in the game scales to the player's level:** no creature, enemy, loot, chest, trap, reward or price. A
   thing is what it is wherever it stands; the same chest holds the same thing at level 1 and level 100.
2. **Danger bands are fixed in the world.** A band says how tough a stretch is; the player grows into the harder
   bands by getting stronger, never the other way round.
3. **Skyrim's levelled machinery is used only as a random pick at a fixed level.** Levelled lists (LVLN, LVLI) may
   choose among entries, but every entry's level is 1 so the player's level never gates it; encounter zones carry
   min = max; actors carry a fixed level with PC-level-mult off, including actors templated on a mod's creature
   whose own record scales (the stats come from our record, not the template).
4. **A check enforces it:** no record our plugins write carries a PC-level multiplier, a levelled entry above
   level 1, a zone with min different from max, or a template that imports scaling stats.

## Why

The owner's design: the world is a fixed place the player learns, the Morrowind and Dark Souls way. Skyrim's
"calculate from all levels at or below the player" flag does the opposite of our rule by default, so the rule
needs a check, not a habit.
