<!-- imported unchanged from elder-souls-argonia packages/game-core/src/stats/README.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# stats — the character model (module 76 §116–§129)

Pure, deterministic functions over versioned data: the workstream S design
(decisions 0031–0037) ported from `tooling/stats-sim` (retired; proved at commit
`7e93d7de`), proved equal to it.
No React, no three, no state; the folder imports nothing outside itself
(a test enforces it). Import from `@elder-souls/game-core/stats/index` in an
app, or `../stats` inside game-core. Why this home and what differs from the
sim: [decision 0088](../old-decisions/0088-the-stats-model-lives-in-game-core-and-reads-injected-data.md).
Phase brief: [2.8 progression](../phases/2-slice/2.8-progression.md).

## Data

`data/*.json` is the canonical copy of every number (module 76 §129). Each file carries `schemaVersion`
(registered in `tooling/repo-standards/data-registry.json`) and a
`designRef`; no prose and no labels (names come from the text catalogue).
`STATS_DATA` is the frozen canonical set. Every function takes an optional
last argument `data: StatsData`; build one with `statsData(raw)` to test a
retune or to run the sim's own tables.

| File | Holds |
|---|---|
| `curves.json` | k exponent, P range, health/stamina/magicka/carry, burden and roll tiers, mitigation, breath, movement, XP, vastei (with `pileRecoveryRadiusM`), level-up costs and the ranks-per-level curve (`levelUp.ranksPerLevel`, read by `levels.ts` `ranksToNextLevel`; §120.5, 0147), difficulty, sneak table, climbing, poise, block cap, check constants, `worthiness` (the §120.1 use values, armour weights, the athletics budget), `rested` (camp, rented and owned multipliers, hours), `jump` (`clearsRiseM`, `clearsRunM`), `fall` (OpenMW character.cpp getFallDamage with Morrowind GMSTs: fFallDistanceMult 0.07 per unit = 4.902 HP/m at 0.01428 m/unit, fFallAcroBase 0.25, fFallAcroMult 0.01; damage = damagePerMetre × (drop − safeFallMetres) × (acrobaticsBase + acrobaticsMult × (100 − min(100, Acrobatics))); none on landing in water; read by `locomotion/hazards.ts`) |
| `skills.json` | the 27 skills: governing and score attribute, specialization, family, bands `[lo, hi]` over k(score) |
| `attributes.json` | the seven attributes, start range, favoured bonus, purchase cap, the reference character |
| `races.json` | one record per roster race, both sexes, Morrowind's packages ([0096](../old-decisions/0096-one-race-record-keyed-by-the-roster-with-morrowinds-packages.md)) |
| `classes.json` | the 18 preset classes (§119) |
| `birthsigns.json` | the thirteen birthsigns as Black Marsh reads them (Jel month names, world/sources/lore/topics/birthsigns.md): guardian, month (Serpent none), stack entries, powers and spells by id (§119, §127) |
| `ladder.json` | D1–D5 bands, each band's `characterLevel`, variants, the ±25 % clamp (§128) |
| `magic.json`, `economy.json` | spell tiers, castability, enchanting bounds, `dualCast` ratios, `innateResist` (Willpower divisor), `diseases` (resist field, stages); prices, training, services |
| `rules-argonia.json` | our progression rules, `$from` references into `curves` (resolved into `STATS_DATA.progression`) |
| `ladder-table.md` | generated, never edited: what each class at each band and position 0.1/0.5/0.9 compiles to (§128), for authors; regenerate with `python3 -m worldgen.compiled_view --ladder` from `tooling/world-generation` after any table change |
| `sim/data/*.json` | harness-only tables: the gear mirror, build checkpoints, worked enemies, content models, Morrowind's rules |

## API (stable; the combat lane consumes the first block)

| Function | Returns |
|---|---|
| `meleeModifiers(skillId, skill, attrs?)` | `{damagePosition, staminaCost, strength, wear, targetStaminaDamage}`; replaces `combat/skillScalars.meleeScalars` |
| `marksmanModifiers(skill, attrs?)` | combat's `RangedModifiers` shape; replaces `marksmanScalars` |
| `blockModifiers(skill, attrs?)`, `capBlockStability(x)` | Block's stability and guard-stamina bands; the 0.95 cap |
| `burdenTier(kg, attrs)`, `burdenStaminaMultiplier(tier)`, `rollModifiers(tier)` | §122 tiers and what they do |
| `k`, `effectiveSkill`, `canonScore`, `band`, `damagePosition`, `strengthDamage`, `strengthApplies`, `skillBand` | the curve (§116, §117.1, §121.1) |
| `softRequirementStaminaMultiplier` | §121.1, §121.6 |
| `maxHealth`, `maxStamina`, `staminaRegen`, `maxMagicka`, `magickaRegen`, `carryCapacity` | §117, §121.2 |
| `mitigation`, `damageAfterArmour`, `incomingDamage`, `unarmouredRating`, `basePoise`, `piecePoise` | §121.3–§121.4 |
| `walkSpeed`, `sprintSpeed`, `swimSpeed`, `jumpApex`, `safeFallMetres`, `breathSeconds`, `climb` | §122 |
| `sneakMultiplier` | §121.5 |
| `lockOpens`, `maxCastableCost`, `enchantPointBudget`, `chargedUseCostMultiplier`, `persuasionScore`, `craftableMaterialTier`, `temperGrade`, `outOfCombatFatigueFactor` | §117.1, §117.3, §118 |
| `pointsToNextRank`, `vasteiPerRank`, `attributeCost` | §120 |
| `REFERENCE_ATTRIBUTES` | the Marsh Hand (§116), the default attributes |
| `startingCharacter({race, sex, classId})`, `raceStats`, `classDef`, `skillClassOf` | §119 creation |
| `compileActor({id, band, position, variants})`, `bandActor` | the semantic compiler for actors (0019 fourth amendment, §128) |
| `EFFECT_FIELD_GROUPS`, `EFFECT_FIELDS`, `isEffectField`, `applyEffects(base, effects)`, `resistance(totals, field)` | the one effect stack and its field list (§127); fortify/resist/absorb add, drain/damage subtract, ability sets, restore leaves maxima alone |
| `CAST_INTERRUPTION_RULE`, `castInterrupted({poiseBroken})` | for 2.9: a hit interrupts a cast exactly when it breaks poise |
| `compileCharacter({race, sex, classId, birthsign?, level, skills?, attributes?, effects?, timed?, now?, loadout?})`, `birthsign(id)`, `characterMitigation` | the one character compiler (0144): attributes and skills after the stack, pools, carry, armour (§121.4), poise, `combat: CombatantNumbers`, `startingSpells` (class then sign), `powers` (race then sign) |
| `TIMED_SOURCES`, `TimedEffect`, `addTimed`, `expireTimed`, `dispelTimed(stack, kinds, sourceId?)`, `activeTimed`, `remainingSeconds` (`timed.ts`) | timed entries on the one stack (2.9): same effect from the same source refreshes, from another source stacks; `durationSeconds: null` lasts until dispelled; save family `magic` |
| `knownSpellsFromSheet`, `learnByPurchase`, `learnByTeaching`, `knowsSpell` (`knownSpells.ts`) | the known-spells record per actor; the only three writers |
| `diseaseRow`, `catchDisease(stack, totals, id, now, seed)`, `advanceDisease`, `curePurchased`, `hasDisease`, `seededUnit` (`disease.ts`) | `magic.json` `diseases`: a staged until-cured timed entry; the resist roll is seeded |
| `powerDay`, `canUsePower`, `usePower` (`powers.ts`) | once a day, the day = world-time epoch minutes / 1440 |
| `playerNumbers(spec?)`, `enemyNumbers(ref, body?)` | each side's `CombatantNumbers`; the player's are compiled through `combat/playerNumbers.ts` `compilePlayer` |
| `createProgressionStore(host, state)`, `progressionStateFor`, `reportUse`, `grantRank`, `beginSitting`, `endSitting`, `consolidateLevel`, `attributePurchase`, `priceOf`, `experienceMultiplier`, `takeCarriedVastei`, `returnPileVastei` (`store.ts`) | the one progression store: use reports, trainer and book ranks, the rest sitting, the purchase, the death pile's wallet (§120, §126); data and clock injected, no singleton; save family `progression` |
| `usePoints` (`skillUse.ts`), the worthiness rules (`worthiness.ts`), pending levels and the purchase (`levels.ts`), `vasteiForUse`, `pileRecoveryRadius` (`vastei.ts`) | §120.1–§120.4 pieces the store composes |
| `resolveRuleSet`, `rankCost` | §120 rule sets |
| `sim/run.ts` `runSim(data?, {matrix?})` | the balance harness: every sweep and the 19 invariants (import `…/stats/sim/run`; not in `index.ts`, so game code never bundles it) |

## Proof

`equivalence.test.ts` runs every `__fixtures__/sample-*.inputs.json` case
through the port and compares with answers generated from the sim
(`generate-expected.mjs`, never from the port) to 1e-12 relative. Sample `a`
is hand-written; `b` was drawn fresh (`draw-sample.mjs b 20260924`) after
`a` passed and passed with no change. `stats.test.ts` holds the design's
reference numbers (Marsh Hand: 100 health, 100 stamina, 180 kg, 25.0 %
mitigation on the raw steel set; `compile.test.ts` pins the compiled 24.06 %), the owner's Marksman mastery numbers, monotonicity, purity,
and a data diff that fails if any sim value moved other than the recorded
differences. `sim/equivalence.test.ts` runs the whole harness on the sim's
own tables (`__fixtures__/sim-data`, via `fromSimTables`) against
`__fixtures__/sim-output.json.gz` (the sim's `run.mjs --json --matrix`,
generated before the port): 12,924 numbers, bit-exact. `sim/invariants.test.ts`
is the standing gate (module 76 §104): all 19 invariants on the canonical
data.
