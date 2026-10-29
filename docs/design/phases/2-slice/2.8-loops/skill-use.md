<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/skill-use.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: skill use (2.8 § Loops, lane 2.8a2)

Rule (world/76 §120.1, §120.2; 0037: no practice discount, no repeat-target
damping): every qualifying use reports into one store with its canon value
from `curves.json` `worthiness.uses`, scaled by worthiness where §120.2 says
so; books and trainers count toward a level and yield no vastei. Code:
`packages/game-core/src/stats/{skillUse,worthiness,levels,store}.ts`; tests
`packages/game-core/src/stats/store.test.ts`. Command:
`npx vitest run src/stats/store.test.ts` in `packages/game-core`.

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Every §120.1 use (21 rows) reports its canon value at full worth | equal to the table | pass | 0.75 s (whole file, 40 tests) | `store.test.ts` § canon use values |
| Uses that changed nothing (failed persuasion, light at noon, a jump over nothing, a downward climb) | 0 | pass | 0.75 s (whole file, 40 tests) | same |
| Blow worthiness: damage / target max health, full at 15 %, floor 0.05 | 1, 0.5, 0.05, 0 | pass | 0.75 s (whole file, 40 tests) | § worthiness |
| Armour kill (winWeight × 3 × clamp) and hit (hitWeight × worth) per class | light 3.0 / medium 1.8 / heavy 1.05; hits 0.25 / 0.6 / 0.5 | pass | 0.75 s (whole file, 40 tests) | same |
| Training dummy, summoned, helpless, non-hostile | 0 points, 0 vastei | pass | 0.75 s (whole file, 40 tests) | same |
| No repeat-target damping | 20th blow = 1st | pass | 0.75 s (whole file, 40 tests) | same |
| Athletics: 1200 s a rest, nothing in a settlement, cleared by a rest | 20 + 6 then 0, 0.2 after rest | pass | 0.75 s (whole file, 40 tests) | same |
| Falls: damaging only, once per location per rest | 0, 3, 0, 3, 3 after rest | pass | 0.75 s (whole file, 40 tests) | same |
| Rank cost = pointsToNextRank (uses to first rank) | ceil(cost) | pass | 0.75 s (whole file, 40 tests) | § ranks |
| Trainer and book ranks count toward a level, no vastei; a book teaches once; a maxed skill is not trained | as stated | pass | 0.75 s (whole file, 40 tests) | same |
| Rested: rented ×1.05, owned ×1.08, eight game hours, camp ×1; vastei unscaled | as stated | pass | 0.75 s (whole file, 40 tests) | § the sitting |

Eyes: the "rose to" toast on three viewports is the seam loop's
([seams.md](seams.md)); 2.8b wired `reportUse` into the game.

## Named gaps

- The rested entry is a timed `fortify` on `skillExperience`
  (`store.ts` `SKILL_EXPERIENCE_FIELD`), a pool field of the one stack
  (`effects.ts`).
- The sitting cap is world/76 §120.4's: at most five points in one
  attribute a sitting (`levelUp.sittingCap`).
- Not built (no number in world/76 yet): per-spell-per-rest diminishing
  for casts (2.9), per-recipe diminishing for brews (2.9b), the merchant's
  purse cap and per-vendor cap on trade, and the Security lock-rating
  window (2.10).
