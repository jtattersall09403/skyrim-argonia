<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/vastei.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: vastei (2.8 § Loops, lane 2.8a2)

Rule (world/76 §120.3): vastei per qualifying use = 4 × use-points ×
(1 + effSkill/50); worthiness cancels per rank; never granted by trainers,
books, quests or loot; one pile where you die (`combat/death.ts`), taken back
within `curves.vastei.pileRecoveryRadiusM`. Code:
`packages/game-core/src/stats/{vastei,store}.ts`; save family
`packages/save/src/families/progression.ts`.

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Vastei per use by the formula | 4 × 1 × (1 + eff/50) | pass | 0.75 s (whole file, 40 tests) | `store.test.ts` § ranks |
| Cancellation: vastei over three ranks, full blows vs chip (3 %, 0.5 % of health) | within one use of Σ vasteiPerRank | pass: within one use for 15, 3 and 0.5 damage on 100 | 0.75 s (whole file, 40 tests) | same |
| A maxed skill keeps paying vastei and the 1 : 3 counter | value stays 100, vastei > 0, counter +1 after 3 ranks | pass | 0.75 s (whole file, 40 tests) | same |
| Trainer and book ranks | vastei 0 | pass | 0.75 s (whole file, 40 tests) | same |
| Pile recovery radius is a curves key | 2.0 m | pass: 2.0 m | 0.75 s (whole file, 40 tests) | § the store |
| Save round trip of a played store; wrong shapes refused | equal; 9 refusals | pass: equal after JSON; 9 refusals | 0.31 s | `packages/save/src/families/progression.test.ts` |

Eyes: 2.8b wired `takeCarriedVastei` → `die` and `recoverPile` →
`returnPileVastei`; the sandbox shows the pile and its recovery
(`lanes/2.8/b-report.md`), and the sheet shows the balance (2.8e).
