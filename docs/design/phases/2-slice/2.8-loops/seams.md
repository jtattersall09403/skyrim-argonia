<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/seams.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: seams (2.8 § Loops, lane 2.8s)

One row per hand-off. The number is the headless acceptance session
(`packages/scene/src/interact/progression-session.test.ts`: fight a D1
record, rank skills through the store, rest at a camp, consolidate, buy,
die to a D2 record with vastei carried, wake at the rest with the pile
where you fell, recover it; every step round-trips the death, progression
and respawn families into a fresh registry). The eyes are one ui-lab still
per viewport at the hand-off (`npm run ui-lab:check -- --screen <id>` under
`job_guard.sh 2.8s --mem 4`), copied to `lanes/2.8/s-shots/`, judged by a
reader. Screens are shot on the working tree, which carries 2.8e's
uncommitted screen work.

| Hand-off | Headless measure (bar) | Still (screen) | Reader checks | Result | Elapsed | Reader |
|---|---|---|---|---|---|---|
| bed or calm ground → rest prompt | calm wild offers a camp sitting; the sitting writes `restAt` at the feet (offer `{mode: rest, tier: camp}`; wake point kind `rest`) | `sleep`, `rest` | the prompt names the bed or ground; the rest screen offers hours and a rest, not only a wait | pass: calm wild offers `{rest, camp}`; the sitting's wake point is kind `rest` at the camp (500, 2, 500) | 5 s (one test file, all rows) | clear after 2.8e2: the rest window names the bed or the ground by tier |
| rest screen → level-up | a sitting with one pending level consolidates it (level 1 → 2) and opens the sitting; the level view's prices equal `priceOf` | `level-up` | the new level, the vastei balance, list prices, the cap of five, health after | pass: 6 trainer ranks after the fights make one pending level; the camp sitting consolidates 1 → 2; the view's endurance price = `priceOf` (164.26) | 5 s (one test file, all rows) | clear after 2.8e2: the cap line and Done sit under the attributes; Done covers no line on phone |
| death → wake at the rest, pile left | `die` with the carried balance: wallet 0, pile = the balance at the fall point, wake kind `rest` at the camp; recovery inside the radius returns it, outside does not | `death` | the death screen says where you wake and that the vastei lie where you fell | pass: D2 crocodile (hit 31) kills the level-2 warrior (health 53.7) in 2 blows; wallet 0, wake kind `rest` at the camp, pile at the fall holding the whole 457.23; recovery 3 m out none, 1 m in all | 5 s (one test file, all rows) | clear: "Wake at your last rest"; "Your vastei lie where you fell." |
| skill rise → toast → sheet | a rank risen in the fight fires `onRose` once per rank; the notice is `skill-rose` with the skill's catalogue id and value; the live character's skill equals the store's | `hud-notices`, `pause-deck` | the toast reads "rose to" with the skill and rank; the sheet shows the same value | pass: 18 D1 crow fights (72 blows, crow health 55) rose Long Blade 35 → 38 and Unarmored 10 → 12, five `onRose` events; the `skill-rose` notice carries `text.stat.skill.long-blade`; the live character's Long Blade equals the store's | 5 s (one test file, all rows) | clear: "Your Long Blade skill rose to 49." (2.8e) |
| trainer or book rank → level counter | a trainer and a book rank each add one to the counter and no vastei; a book teaches once | `training`, `reader-book` | the trainer offer and the book read; nothing promises vastei | pass: a book rank and 6 trainer ranks moved the counter to one pending level with the wallet unchanged | 5 s (one test file, all rows) | clear: nothing promises vastei; gold sits above the offers; the dimming of dear offers on phone is a `P3` backlog row |

Every step (fight, rank, rest, buy, die, wake, recover) snapshots the
three families and restores them into a fresh registry with equal state;
the session continues from the restored copy.

## Reds

None. `combat/death.ts:56` keeps the fraction, so the pile holds the whole
carried balance (`progression-session.test.ts` § "the pile holds the whole
carried balance").

## Balance re-measure (shipped tree)

`packages/game-core/src/stats/balance.test.ts`, 0.38 s, five sims: every
number equals [balance.md](balance.md) (level 2 at 1.75 / 1.75 / 1.25 h,
harness 1.87 / 1.87 / 1.37; ten D1 fights +1 Long Blade, 376 vastei;
sitting 245 / 2567 and 540 / 5645; maxed skill 182 = 182, 2014 vastei;
no deferral 11 ≥ 9, 12 ≥ 9). The mage finding stands.

Stills: `lanes/2.8/s-shots/` and `lanes/2.8/e-shots/`; the screens' final
verdicts are in [screens.md](screens.md).
