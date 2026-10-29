<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/sneak-attacks.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: sneak attacks (2.10 § Loops, lane 2.10-c)

Rule (world/76 §121.5; decisions 0092 §5, 0151 item 1; detection rows
`tables.sneakAttack`, `tables.searching`): a blow on an observer in
`unaware` takes the player's Sneak band multiplier for its weapon column
(melee or bow); the opener applies once (the first blow engages the
target) and is withheld by the one-shot exclusions (aware, health band
above the row's cap, boss, warded); a searching observer struck from
outside its cone takes the band times `searching.sneakAttackMul`; an
arrow's impact is a noise at its point; draw time and the aim camera do
not change with the crouch. Eyes: the dagger one-shot and the sneak shot
strips, read by a `reader`.

Measures:

- `cd packages/character && npx vitest run src/combat/sneakAttack.test.ts`
- `npm run visual:check -w @elder-souls/combat-sandbox -- stealth` (pod)

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Band multiplier from the rows, unaware, melee and bow, every band | rows verbatim | 6 of 6 bands: meleeMul, bowMul, dagger column exact | 3.3 s (file, one run) | `sneakAttack.test.ts` |
| One-shot exclusions withhold the multiplier: aware, healthBandAbove, boss, warded, melee and bow | 8 of 8 | 8 of 8 (healthBandAbove on a test cap D3: the rows carry no cap, blocker) | 3.3 s | `sneakAttack.test.ts` |
| Searching observer from outside its cone: band x searching mul; inside the cone: none | 2 of 2 | 2 of 2 (x3 x 1 at Sneak 45 one-handed; inside the cone: aware) | 3.3 s | `sneakAttack.test.ts` |
| Arrow lure: impact noise at its point; an observer within hearing goes suspicious with last-known at the point; one beyond hears nothing | 2 of 2 | 2 of 2 (person hearing 20 m: 10 m suspicious, 21 m unaware) | 3.3 s | `sneakAttack.test.ts` |
| Draw time crouched equals standing; aim camera holds while crouched | 2 of 2 | 2 of 2 (longbow raise, nock, draw: equal seconds; stance holds crouching; view aim, also locked on) | 3.3 s | `sneakAttack.test.ts` |
| A witnessed blow calls `crime.violence(event, regionId)` with witnesses = observersEngaged | 1 | 1 (witnesses a, b; victim aside; unseen files nothing) | 3.3 s | `sneakAttack.test.ts` |
| visual:check `stealth`: dagger one-shot and sneak shot strips, reader | green, reader pass | owed: scenarios `sneak-dagger-one-shot`, `sneak-shot` authored, scenario contract tests 27 of 27 green; pod run not done | - | pod strips |
