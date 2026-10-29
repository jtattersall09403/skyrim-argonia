<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.8-loops/rest.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: rest (2.8 § Loops, lane 2.8c)

Rule (world/76 §126, §120.4): rest in the calm wild (outside settlement
bounds, outside a dungeon, no hostile engaged or searching) or in a bed you
own or rent; refused in a dungeon, in combat, while hunted, or in a settlement
without a bed, the line saying why. A sitting saves, consolidates one pending
level, opens the purchase (five a sitting per attribute, list price), recomputes
health, fills the pools, records `restAt`, counts the rest for respawn and
advances the clock. Wait passes time only. Code: rules in
`packages/game-core/src/interaction/interactables.ts`, the respawn ledger in
`packages/game-core/src/actors/hostileRecords.ts`, the sitting in
`packages/scene/src/interact/rest.ts` and `session.ts`.

Harness: `npx vitest run packages/scene/src/interact/rest.test.ts` (the
headless interact session), plus `packages/game-core/src/interaction/interactables.test.ts`
and `packages/game-core/src/actors/hostileSpawns.test.ts` for the pure rules.

| Case | Bar | Result | Elapsed | Capture (2.8e) |
|---|---|---|---|---|
| Allowed: calm wild, camp | rest offered, tier camp | pass: camp | 5.6 s (whole file, 18 tests) | rest screen, wild |
| Allowed: rented bed in a settlement | rest offered, tier rented | pass: rented | 5.6 s (whole file, 18 tests) | rest screen, inn bed |
| Allowed: owned bed | rest offered, tier owned | pass: owned | 5.6 s (whole file, 18 tests) | |
| Refused: dungeon | `text.system.cannot-rest-in-dungeon`, wait offered | pass | 5.6 s (whole file, 18 tests) | wait screen with the line |
| Refused: in combat (engaged) | `text.system.cannot-rest-enemies-near`, no wait | pass | 5.6 s (whole file, 18 tests) | sign window |
| Refused: hunted (searching) | `text.system.cannot-rest-hunted`, no wait | pass | 5.6 s (whole file, 18 tests) | sign window |
| Refused: settlement, no bed (pause deck and an unrented inn bed) | `text.system.cannot-rest-in-settlement`, wait offered | pass (both) | 5.6 s (whole file, 18 tests) | wait screen with the line |
| Save | the registry snapshot holds `death`, `progression`, `respawn` | pass: death, progression, respawn | 5.6 s (whole file, 18 tests) | |
| One level | one of two pending consolidates; the level-up view opens | pass: level 2, 1 left pending | 5.6 s (whole file, 18 tests) | level-up screen |
| Purchase with the cap | prices equal `priceOf`; the sixth point in one attribute refused | pass: 6 asked, 5 bought | 5.6 s (whole file, 18 tests) | level-up screen, a capped row |
| Health recompute | max health equals `maxHealth(attributes, level)` after the purchase | pass | 5.6 s (whole file, 18 tests) | |
| Pools | health, stamina, magicka full | pass: 1/1/1 | 5.6 s (whole file, 18 tests) | |
| `restAt` | wake point kind `rest` at the player | pass: kind rest at (500, 2, 500) | 5.6 s (whole file, 18 tests) | |
| Respawn | an `onRest` record dead before the rest is due again; a `never` record is not | pass: onRest back, never stays, rests 1 | 5.6 s (whole file, 18 tests) | |
| Clock | +hours through `advanceHours`; catch-up once | pass: +480 min, catch-up 1 | 5.6 s (whole file, 18 tests) | |
| Rested entry | rented ×1.05 for 8 h, owned ×1.08, camp none; rented bed given back | pass: 1.05 / 1.08 / 1, lodging cleared | 5.6 s (whole file, 18 tests) | |
| Wait | clock only: no save, level, pools, respawn | pass | 5.6 s (whole file, 18 tests) | |
| Wake as a rest | waking from death counts a rest (respawn) and wakes at the last rest | pass: rests 2, wake at the rest | 5.6 s (whole file, 18 tests) | |
| Trainer and book ranks | `grantRank`: counter +1, vastei 0; a book once | pass: counter +1, vastei 0, second read refused | 5.6 s (whole file, 18 tests) | |

Fixtures 2.8e needs for the three viewports: the rest view in each mode
(`rest` with the tier, `wait` with each refusal line) and a `LevelView` from
`levelViewOf(store)` with one pending level and enough vastei to reach the cap.
