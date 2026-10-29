<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/pickpocket.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: pickpocket (2.10 § Loops, lane 2.10-e)

Rule (decision 0151 item 4; world/76 §118, §121.5; lanes/2.10/briefs/rules.md):
pickpocketing is the one roll. A verb on a person while the player sneaks and
that person is not engaged on the player; the sheet lists what the person
carries, each with a percent; the roll is the next draw of the walk's seeded
dice; success moves the item silently; failure turns the target engaged and
files a witnessed pickpocket with the target as witness. Worn armour is never
listed. Eyes: none here (the sheet strip is lane j's pod).

Chance per item (rows `world/sources/registries/pickpocket.json`, view
`packages/game-core/src/crime/data/pickpocket.json`):
base by Sneak band − target spot × 0.25 − weight-class penalty − value penalty,
floored at 0 and capped at the top base row (90). Weight class by the item's
kg against the top edges 1 / 5 / 10 (light 4, medium 20, heavy 40; above 10 kg
reads heavy); value penalty is the highest band the value is above (50→5,
100→10, 250→25, 500→50), else 0.

Worked rows (tests in `packages/game-core/src/interaction/pickpocket.test.ts`):

| Sneak | Target spot | Item kg | Item value | Base | Spot | Weight | Value | Percent |
|---|---|---|---|---|---|---|---|---|
| 25 | 40 (person) | 0 (a key) | 0 | 35 | −10 | −4 (light) | 0 | 21 |
| 60 | 40 | 4 | 120 | 75 | −10 | −20 (medium) | −10 | 35 |
| 80 | 40 | 12 | 600 | 90 | −10 | −40 (heavy) | −50 | 0 (floored from −10) |

Measures:

- `cd packages/game-core && npx vitest run src/interaction/pickpocket.test.ts`
- `cd packages/scene && npx vitest run src/interact/pickpocket-session.test.ts`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Chance on the three worked rows; worn armour never listed | 3 of 3; 0 worn rows | 3 of 3 (21, 35, 0); worn daedric boots unlisted and refused "worn"; cap 90 held | 2.9 s (8 tests, one run) | `pickpocket.test.ts` |
| Seeded roll: same seed state rolls the same; the stream advances | 2 of 2 | 2 of 2 | same run | `pickpocket.test.ts` |
| Verb refusals: not sneaking; target engaged | 2 of 2 refused | 2 of 2 ("not-sneaking", "seen"; suspicious still offers) | 3.8 s (4 tests, one run) | `pickpocket-session.test.ts` |
| Success moves the item, no crime; failure engages the target and files a pickpocket with the target as witness | 2 of 2 | 2 of 2 (lift: key moved, ledger empty; miss: keeper engaged, pickpocket 25 filed, witness = victim = keeper) | same run | `pickpocket-session.test.ts` |
| Seam: a key lifted opens its lock (`locks.ts` `openWithKey`) | opened | opened, how "key" (lock.greenspring.door-2; refused without the key) | same run | `pickpocket-session.test.ts` |
| Greenspring crowd by day: a lift, a failed lift, the file | 3 of 3 | 3 of 3 (root-herald and spring-keeper out at 14:00, keys by `carriedBy`) | same run | `pickpocket-session.test.ts` |
