<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/alchemy.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: alchemy (2.9b § Alchemy, lane 2.9b-b)

One row per measure. Numbers are headless: the formula tests
(`packages/game-core/src/stats/crafting.test.ts`), the verb tests
(`packages/crafting/src/{alchemy,potion,coating,gather}.test.ts`) and the
seam drive (`packages/scene/src/interact/crafting-session.test.ts`), which
drives the interact, item and magic sessions over the real effect rows and
the save registry. Written before the first measure; results filled after.

## The formula (world/76 §124, on effective values)

```
score    = effective Alchemy + effective Intelligence / 10      (skills.json alchemy scoreDivisor 10)
strength = score × apparatus / (3 × effectBaseCost)             (× magic.json magnitudeMultiplier 18 on a pool effect)
duration = score × apparatus / effectBaseCost                    (seconds)
```

- `apparatus`: magic.json `alchemy.apparatus` (mortar 0.6, journeyman 1.0, master 1.5).
- `effectBaseCost`: magic.json `alchemy.effectBaseCost` where it names the effect
  (restore-health → `restoreHealth`, a fortify on an attribute → `fortifyAttribute`,
  resist-poison → `resistPoison`, water-breathing → `waterBreathing`), else the
  effect row's `baseCost` (packages/magic effects.json).
- The multiplier 18 is magic.json's heal-amount scale (its note: `healAmount =
  magnitudeMultiplier × …`): it scales an effect on a current pool (health,
  stamina, magicka), whose magnitude is a total. A stat effect (fortify, resist,
  drain) keeps canon's strength in points.
- A pool restore lands at once (§126: potions heal instantly); a pool damage
  (a poison, a fire oil) lands its total over the brew's duration, carried on
  the victim's stack while it runs.
- Effective values: the compiled actor (`compileCharacter`), timed entries
  folded, so a fortify-Alchemy potion drunk raises the next brew (0144 item 7).

Worked examples (restore-health, base cost 5, a pool effect):

| Case | score | strength | duration |
|---|---|---|---|
| Alchemy 30, Int 40, journeyman | 30 + 4 = 34 | 18 × 34 × 1.0 / 15 = 40.8 | 34 × 1.0 / 5 = 6.8 s |
| Alchemy 60, Int 60, master | 60 + 6 = 66 | 18 × 66 × 1.5 / 15 = 118.8 | 66 × 1.5 / 5 = 19.8 s |
| Alchemy 15, Int 40, mortar | 15 + 4 = 19 | 18 × 19 × 0.6 / 15 = 13.68 | 19 × 0.6 / 5 = 2.28 s |

A stat effect: fortify-alchemy (base cost 4.3) at Alchemy 30, Int 40,
journeyman: strength 34 / 12.9 = 2.64 points for 34 / 4.3 = 7.91 s.

## Survey

| Row | Measure (bar) | Elapsed | Result |
|---|---|---|---|
| 1 formula | three worked examples to 2 dp; a fortify-Alchemy timed entry on the compiled actor raises the next brew's strength | 0.7 s | green: crafting.test.ts 3/3 (40.8/6.8, 118.8/19.8, 13.68/2.28; fortify-Alchemy entry raises the next brew) |
| 2 brew | 2–4 ingredients; effects shared by ≥ 2 brew; effect slot i shown at effective Alchemy ≥ 15·(i+1) (skills.json `effectVisibilityAt`), an unseen effect brews and is listed hidden; ingredients consumed; potion instance row written; `{alchemy, 2.0}` (§120.1) | 5.4 s (rows 2–5 one run) | green: alchemy/potion/coating/gather tests 17/17 |
| 3 drink | belt press on a beneficial potion: its effects on the timed stack as `potion` with the potion id, one consumed; the strip lists it | 5.4 s | green (row 2's run); drive row 6 shows the entry on the strip |
| 4 coat | belt press on an all-harmful potion: coats the main hand, or the arrow stack with a bow; the next landed hit puts the effect on the victim's stack and clears the coat; Argonian (Resist Poison 100) takes 0 | 5.4 s | green: every effect coats (`Coating.effects[]`, a two-effect poison test); Argonian takes 0 |
| 5 gather | a `gather` binding adds the node's yield; the node is taken until respawnHours pass on the clock; no skill | 5.4 s | green; the taken map saves in the `crafting` family (`gathered`) |
| 6 drive | gather → brew → drink → strip; brew → coat blade → hit → victim entry → cleared; coat arrow → arrow hit; save round trip of coating and brewed potion | 9.4 s | green: crafting-session.test.ts "alchemy and gathering" 1/1 (moss → Fortify Long Blade on the strip; Damage Health + Weakness to Poison on blade, then arrow; reload keeps coating, brew, taken node) |
