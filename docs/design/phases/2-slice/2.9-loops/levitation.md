<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9-loops/levitation.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: levitation, the bound dagger, Soultrap's death hook, the bite (2.9 § Loops, lane 2.9b2)

Rule (2.9 § b; decision 0146 item 6): levitation is a `MovementMode`
("levitate") beneath `PlayerMovementController`
(`game-core/src/physics/levitateDrive.ts`, the adapter's `levitate()`,
`character/src/combat/levitateRuntime.ts`): it starts on the timed entry's
presence, ends on its expiry, and a poise break ends it
(`CAST_INTERRUPTION_RULE`); steering is the swim's look law at the entry's
speed; the collider is kept, so the body stops on the real mesh, and on
expiry the grounded controller's gravity lands it. The bound item is
conjured through 2.3's `equipItem` (`character/src/combat/boundWeapon.ts`);
a creature's death goes through one hook (`game-core/src/combat/creatureDeath.ts`)
that Soultrap listens on; a landed creature strike calls the host's bite
hook (`CreatureStepContext.onBite`, CombatRuntime `onCreatureBite`).

Measure: `npx vitest run <file>` in the package named; the scenes by
`bash tooling/repo-standards/job_guard.sh 2.9b2 --mem 6 -- npm run visual:check -w @elder-souls/combat-sandbox -- magic`.

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Mode rule: starts on the entry (from ground or water), ends on expiry, walk and swim untouched with no entry, poise break ends it and latches the entry, a non-breaking hit does not | exact | pass (8 tests) | 0.4 s | `game-core/src/physics/levitateDrive.test.ts` |
| Rapier, real adapter: rise 2 s looking up at 3 m/s | > 1.5 m | 5.97 m | 3 s (file) | `character/src/levitate.rapier.test.ts` |
| Level travel 1 s | 3.0 ± 0.05 m, drift < 0.02 m | 3.00 m, 0.000 m | (same) | (same) |
| Expiry over a box: back in grounded, lands on the box top | stand 1.17 ± 0.05 m over the box | 0.53 s to ground, 1.170 m | (same) | (same) |
| Sinking onto the ground stops on it (collider kept) | still levitating, above the ground | 0.719 m, levitate | (same) | (same) |
| Poise break drops the body; same entry stays ended; new entry lifts | exact | fell 4.47 m, pass | (same) | (same) |
| Bound dagger: conjured to the main hand (shield kept), dagger class resolves the dagger moveset, expiry gives sword and shield back, own copy kept, stack tick | exact | pass (5 tests) | 2.6 s | `character/src/combat/boundWeapon.test.ts` |
| Giant leech drive: blocked strike no bite; landed strikes call the bite hook with the leech row; seeded 75 % resist | exact | pass | 4 s (with the rows below) | `character/src/combat/creatureDeathBite.test.ts` |
| Leech death through the one hook once: loot, then Soultrap fills the smallest sufficient gem; untrapped fills none | exact | pass | (same) | (same) |
| Death hook order and Soultrap listener | exact | pass (2 tests) | 0.2 s | `game-core/src/combat/creatureDeath.test.ts` |
| The 13-species creature drive after the hook change | green | pass | (same) | `character/src/combat/creatureEnemy.test.ts` |
| `levitate` scene: rise, level travel 1.2 m/s, expiry, landed on the arena floor | expectations `levitate` | see report | see report | strip: reader child |
| `bound-dagger` scene: dagger in hand 0.3–3.0 s, light swing, sword back | expectations `bound` | see report | see report | stills `conjured`, `swing`, `restored` |

Reader checklist for the strip: the body leaves the floor and climbs;
it moves level without sinking; it stands (or walks) upright in the air, no
falling pose while it flies; after the expiry it falls and the feet meet
the floor, not sunk into it and not floating.
