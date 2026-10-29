<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/effects.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: effects (2.8 § Loops, lane 2.8a1)

Rule (world/76 §116.2, §127; decision 0144): one effect stack. Race packages
and the thirteen birthsigns are permanent `StatEffect` entries on the fields
of `EFFECT_FIELD_GROUPS` (`packages/game-core/src/stats/effects.ts`), folded
by `applyEffects` inside `compileCharacter` (`stats/compile.ts`); the sheet
lists each entry with its source. Signs: `stats/data/birthsigns.json` from
`world/sources/lore/topics/birthsigns.md`. 2.9 adds timed entries to the same
stack and reads `CAST_INTERRUPTION_RULE` (a hit interrupts a cast exactly
when it breaks poise).

Measure: `npx vitest run src/stats` in `packages/game-core`.

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Field list as data: six groups, 53 fields; an unknown field refused (`applyEffects` and `statsData` on a sign) | exact | pass | 3.3 s |  `stats/compile.test.ts` |
| Ops: fortify adds, drain subtracts, ability sets, restore leaves maxima; resistance clamps at 100, weakness negative | exact | pass | 3.3 s (one run, all rows) | `compile.test.ts` |
| Every canonical race effect names a listed field | every race | pass | 3.3 s | `compile.test.ts` |
| Thirteen signs authored, twelve months distinct, the Serpent monthless | 13 / 12 / null | pass | 3.3 s | `compile.test.ts` |
| One race on the stack: Argonian poison 100 %, common disease 75 %, water breathing | exact | pass | 3.3 s (one run, all rows) | `compile.test.ts` |
| Three signs on the stack: Steed Speed +25; Lady Endurance and Personality +25 with health and stamina following; Atronach magicka ×3 base, regen 0, absorption 50 | exact | pass | 3.3 s (one run, all rows) | `compile.test.ts` |
| Marsh Hand baseline: health 100, stamina 100 (COMBAT_TUNING), carry 180; raw steel set 50 → 25.0 % at a 24 blow | exact | pass; the compiled rating with the §121.4 Heavy Armor band at 45 is 47.51 → 24.06 % (the anchor, world/76 §116) | 3.3 s (one run, all rows) | `compile.test.ts` |
| The 19 invariants and the bit-exact sim equivalence after the change | green | 19 / 19, 177 tests pass | 3.3 s | `stats/sim/*.test.ts` |
| The sheet lists race and sign entries | every entry with its source | pass (2.8e): the effect panel groups entries by race, birthsign, rested and effect | | ui-lab `character-sheet`, fixture below |

## Fixture the sheet capture needs (2.8e)

`compileCharacter({race: "argonian", sex: "female", classId: "warrior",
birthsign: "atronach", level: 1})`: three race entries
(`race:argonian`) and three sign entries (`birthsign:atronach`) in
`CompiledCharacter.effects`, plus one `effects: [{field: "speed", op:
"drain", magnitude: 10}]` entry for a negative row.

## The anchor

§116 states the Marsh Hand at the compiled 24.06 % mitigation: §121.4
multiplies each worn piece by its armour-skill band, and her Heavy Armor 45
gives ×0.950, so the raw steel set's 50 (25.0 %) compiles to 47.51, the
sim's `steelRef` the invariants are calibrated on.
