<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/compile.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: compile (2.8 § Loops, lane 2.8a3)

Rule (world/76 §119, §128; decision 0144): every person with a statblock
names a preset class (`worldgen/npc_classes.py`, a rule by role, kit,
faction and race, never a per-record edit); `npc_roster --apply` writes
`compiled` on every row of `packages/game-core/src/generated/living.json`
through `worldgen/compiled_view.py`, which bundles `compiled_view.ts` with
rolldown and runs it under node against the shipped stats tables: a person's
`compileCharacter` block (class, race, sex, the level of its band's
character) and every row's combat block (`enemyNumbers` over the band, a
person's worn poise included). Python restates no number.

Measure: `python3 -m pytest worldgen/test_npc_roster.py -k "class or compiled"`
from `tooling/world-generation`; the roster `--apply` once under job_guard.

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Every person row names a preset class; tree-minders `tree-minder`, the Teeth's Nisswo `nightblade` and priest `grave-singer` | every row | pass, 89 people over 13 classes | 2.7 s (one run, rows 1-5) | `test_npc_roster.py` |
| Every person and creature row of living.json carries `compiled` | 89 + 177 | pass, 266 rows | 2.7 s |  `test_npc_roster.py` |
| Equivalence: every hostile's health, hit, heavy hit, armour, poise equal `hostileCombatant` (2.7's path) | bit-exact | pass, 89 hostiles (19 people, 70 creatures) | 0.6 s |  `test_npc_roster.py` |
| Retune: one curve changed in a copied StatsData moves every row, no hand edit | every row | pass, `curves.poise.agilityDivisor` 2 to 2.5 moves all 266 | 1.3 s | `test_npc_roster.py` |
| Gate: a person without a class reds (`npc_classes.problems`, paper gate, `npc_roster --check`) | deliberate red | pass, a person with classId null reds `class:`; live gate 0 reds | 1.0 s |  `test_npc_roster.py` |
| §128 ladder table generated (18 classes × 5 bands × 3 positions) | 270 rows | pass, current against the generator | 0.6 s |  `stats/ladder-table.md` |
| The player compiles (2.8b): the neutral character (the Marsh Hand in the player's identity) gives the calibrated pools 100 / 100 / 24 per s, Agility 50, poise bonus 0; `COMBAT_TUNING` reads them | equal | pass | 2.5 s | `combat/playerNumbers.test.ts` |
| One reference fight headless (steel sword light1 on the Hollow Warden, its light1 on the bare player), blows to kill before and after the swap | equal | pass, 8 and 5 both ways | (same run) | `combat/playerNumbers.test.ts` |
| Every use hook reports with the table's value and worthiness; dummy, summoned and helpless pay nothing | every hook | pass, 8 tests | 0.9 s | `character/src/combat/useReports.test.ts` |
| The sandbox strip of one reference fight before and after the swap | side by side, reader clear | pass: offense-outcomes, enemy health 26.29 / 7.24 / 0 both ways (3 blows); reader: same poses, timing and outcome, only the new magicka bar differs | about 70 s a capture (build + tiny video), one at a time | `lanes/2.8/b-strips/` |
| The sim sweep (2.8x): every enemies.json archetype and every hostile row of living.json x the five builds (melee, greatsword, spear, marksman, stealth at the band's checkpoint, as 2.7a1) | no unhittable, no trivial case | 505 duels (12 archetypes + 89 hostile rows x 5): ttk 2.3-35.9 s, swings to kill 0.5-45.9, hits to die 2-15; 2 trivial (mudcrab and marsh-rat-swarm vs start/marksman, one arrow kills), 0 unhittable, 9 losses (swamp-leviathan master x4, xal-krona legend x5); reported, not retuned | 3.0 s wall, peak 0.2 GiB | `stats/sim/compileSweep.test.ts` |

The one apply: `job_guard.sh 2.8a3 -- npc_roster --apply --whole-province`, 4.3 s, peak 0.38 GiB; registry delta `classId` only (a dry diff first).

## Named gaps

- A person's skills are its §119 starting skills at every level (no growth model for records yet); its `compiled` pools are the character's, its combat block the band's.
- The combat poise reads neutral Agility 50, as 2.7 did; reading the compiled Agility would move person poise (a retune, not done).
- The 565 catalogue persons outside reviewed places carry no statblock, so no class, until their place is reviewed.
