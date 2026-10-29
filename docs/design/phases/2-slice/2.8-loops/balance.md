<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/balance.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: balance (2.8 § Loops, lane 2.8a2)

Short targeted sims, seconds each, driving the real progression store
(`reportUse`, `beginSitting`, `attributePurchase`) with the stats sim's
content model (`sim/data/content-argonia.json`: act 0's quest track, the
archetype's verb profile) and the sim's fight model (`simulateFight`,
`bandActor`). Numbers only; no capture. Test:
`packages/game-core/src/stats/balance.test.ts`. Bars from world/76 §120.5
and §120.4.

| Moment of play | Bar | Result | Elapsed | Test |
|---|---|---|---|---|
| First two hours: hour level 2 is reached, warrior (melee), scout (marksman), mage (magic) | within 0.5 h of the campaign harness (`playCampaign`); 1.5–2.5 h (§120.5) | store: warrior 1.75 h, scout 1.75 h, mage 1.25 h; harness 1.87 / 1.87 / 1.37 h. Warrior and scout in band; mage below 1.5 h in both, accepted (§120.5) | 0.36 s (whole file, 5 sims) | § first two hours |
| Ten lowest-band (D1) fights: ranks gained, warrior | reported | 10 of 10 won; longBlade +1 rank; level counter 1 of 10; 376 vastei | 0.36 s (whole file, 5 sims) | § ten fights |
| One sitting's cost at level 2 and level 12: first point, five in one attribute | reported; level 12 dearer | level 2: first 245, five in Strength 2567; level 12: first 540, five 5645 (Str 60) | 0.36 s (whole file, 5 sims) | § sitting cost |
| A skill at 100 feeding the counter: uses per counted level rank | 3 × pointsToNextRank(100) | 182 uses = bar 182; 2014 vastei on the way | 0.36 s (whole file, 5 sims) | § maxed skill |
| No deferral over two orderings (spend each sitting vs hoard one) | spend ≥ hoard | 600 then 1400: spend 11, hoard 9; 1400 then 600: spend 12, hoard 9 | 0.36 s (whole file, 5 sims) | § no deferral |

## Findings

- **The mage levels early, accepted.** Level 2 at 1.25 h on the store and
  1.37 h on the campaign harness, against §120.5's 1.5–2.5 h; world/76
  §120.5 records the harness number. The cause is the content model's
  utility-cast rate for the magic profile plus every offensive cast
  counting a full point, not the store; nothing is retuned.
- **One home for the use table.** `data/rules-argonia.json` `use` and
  `armourAccrual` take every value `$from` `curves.worthiness` (2.8a4);
  climbing is 0.2/m everywhere.
