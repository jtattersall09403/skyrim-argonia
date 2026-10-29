<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/effects.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: effects (2.9 § Loops, lane 2.9a2)

Rule (world/76 §123, §127; decision 0146): timed entries join 2.8's one
stack. `TimedEffect` {field, op, magnitude, durationSeconds (null = until
dispelled), startedAt, source: spell|scroll|potion|blessing|disease|bound|power,
sourceId} in `packages/game-core/src/stats/timed.ts`; the same effect from the
same source refreshes, from another source stacks; expiry on tick; dispel by
source kind; folded by `compileCharacter` (`spec.timed`, `spec.now`) after
the permanent entries. A cast resolves in `packages/magic/src/apply.ts`.

Measure: `npx vitest run <file>` in the package named.

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Timed entries: sources, refresh vs stack, refusals, countdown, until-dispelled, expiry at the duration, tick split, dispel by kind/kinds/id, fold into the compile, expired dropped at `now`, two sources fold, separate elemental resist | 20 unit tests | 21 pass | 1 s (with the row below) | `game-core/src/stats/timed.test.ts` |
| Known spells: sheet writes class + sign starting spells (Ritual: Blessed Word, Blessed Touch; power Mara's Gift); purchase (`spells` row) and teaching write; other purchases refuse | exact | pass | 1 s | `stats/magicState.test.ts` |
| Swamp fever: §127 values (−10 Endurance, −15 Athletics, until cured); seeded roll; Argonian catches 21–29 % of 2000 seeded bites (75 % resist), Breton every bite; cure by purchase and by a disease dispel | exact / band | pass | 1 s | `stats/magicState.test.ts` |
| Powers: Mara's Gift twice in one day refuses the second; next day allowed; day = epoch minutes / 1440 | exact | pass | 1 s | `stats/magicState.test.ts` |
| A headless cast of each slice id (`SLICE_SPELL_IDS`): Fireball, Frostbite, Hearth Heal, Cure Common Disease, Shield, Levitate, Light, Soul Trap, Bound Dagger: field, magnitude (row × school magnitude band), duration; Willpower/4 + magic + elemental resist, clamped; armour not read; scroll unbounded by skill | every slice id | pass on the real rows (`data/spells.json`, `effects.json`); Shield is a flag entry on `armourRating` (non-stat) the compile ignores | 0 s | `magic/src/apply.test.ts` |
| Absorb Health, Absorb Fatigue, Absorb Magicka transfer target to caster (pool changes + stack entry); Absorb Strength drains target, absorbs on caster; paralyzed, invisible, chameleon are flag entries the compile ignores | exact | pass | 0 s | `apply.test.ts` |
| Atronach 50 % spell absorption in `castSpell`: absorbed cast has no effect and refunds the cost; 1000 of 2000 evenly spaced rolls absorbed; self casts and non-Atronach never | exact | pass | 0 s | `apply.test.ts` |
| All 876 spell rows (single and dual) apply against a compiled Marsh Hand without throwing, finite magnitudes | 876 | pass | 0 s | `apply.test.ts` |
| Dual-cast ratios from `magic.json dualCast` | ×2.2 magnitude, ×2.8 cost | pass | 0 s | `apply.test.ts` |
| Soul Trap: a trapped creature's death fills the smallest sufficient empty gem; none when untrapped, expired or too big | exact | pass | 0 s | `apply.test.ts` |
| Bound Dagger: entry names the item and expiry; due to unequip at expiry | exact | pass | 0 s | `apply.test.ts` |
| Save family `magic`: save→load→compare for timed, known spells, powers, disease; another version refused; wrong shape refused | exact | pass | 1 s | `save/src/families/magic.test.ts` |
| The whole stats folder after the change (19 invariants, sim equivalence, import isolation) | green | 218 / 218 | 5 s | `src/stats` |

Captures owed by other lanes: the disease strip and sheet line (2.9e), the
Soul Trap and bound dagger stills (2.9b2).
