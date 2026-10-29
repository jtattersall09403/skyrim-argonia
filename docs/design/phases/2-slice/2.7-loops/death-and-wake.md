<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/death-and-wake.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: death and waking (2.7 § b, lane 2.7b3)

Rule (world/76 §126): on death the player wakes at the last rest, or at the
arrival point if never rested; nothing else is lost; the carried vastei stays
where they died as one recoverable pile (dying again replaces it); waking
counts as a rest for respawn (`respawnDue`, `RespawnSave.rests`); no grace
window. Code: `packages/game-core/src/combat/death.ts`, save family
`packages/save/src/families/death.ts`, seam `onPlayerDeath` on `CombatRuntime`
(called once on the change into "dead"), host wiring `apps/game/src/GameWorld.tsx`.

| Measurement | Result | Capture |
|---|---|---|
| Round trip: record enemy band D2 hits taken to the calibrated player health 0, die with 340 vastei, snapshot via `createSaveRegistry`, restore into a fresh registry; pile, wake point, deaths equal | pass | `packages/save/src/families/death.test.ts` |
| Pile replacement: die twice, one pile (the second); after a rest, wake kind "rest" | pass (one pile, deaths 2) | `death.test.ts` (save), `combat/death.test.ts` |
| Wake point, never rested | arrival | `packages/game-core/src/combat/death.test.ts` |
| Wake point, rested (a later arrival does not displace a rest) | rest | `packages/game-core/src/combat/death.test.ts` |
| Zero vastei makes no pile; recovery inside the radius returns the vastei and clears the pile, outside returns 0 | pass | `packages/game-core/src/combat/death.test.ts` |
| Wrong shape refused (negative deaths, bad position, bad kind, null) | `SaveRefused` | `packages/save/src/families/death.test.ts` |
| Death screen on the ui-lab viewports (desktop, phone, fold-inner: the three ui_lab_check.mjs VIEWPORTS), bars green | `npm run ui-lab:check -- --screen death`: PASS | `lanes/2.7/b-shots/death/` |

## Named gaps, re-measured against 2.8 (2.9x lane f)

All three closed; measured by `packages/scene/src/interact/seams-session.test.ts`
(the fight → die → wake → recover journey, `2.9x-loops/seams.md` row 5).

- Rest hook: closed. The sitting (`packages/scene/src/interact/rest.ts` `restSitting`) records `restAt` and counts the rest (`countRest`); waking counts one through `wakeCountsRest` (`apps/game/src/GameWorld.tsx:276`). A later arrival does not displace the rest.
- Place-entered: closed. `stepArrival` (`packages/scene/src/ui/playerProgression.ts:120`) records the arrival on entering a place, called from `apps/game/src/gameProgress.tsx:31`.
- Wallet and pickup: closed. `wakeWithWallet` piles the whole wallet; `stepDeathPile` recovers it inside `pileRecoveryRadius` only.
- New, queued: the game's wake passes `start.placeId` and `cell: null` for the fall (`apps/game/src/GameWorld.tsx:274`), so a death in an interior or a later place records the wrong place and cell.

## Reader verdict on the three viewports (`lanes/2.7/b-shots/death/`)

After the fold-inner fix (`screens.css`: the body centred in its half with inline padding) and the line split into two catalogue strings (`death.vastei`, `death.vastei-reach`), one per line:

- Title, both lines and the wake button: shown and unclipped on desktop, phone and fold-inner; comfortable margins.
- No word alone on a line: desktop, phone, fold-inner each read "Your vastei lies where you fell." / "Reach it before you fall again."
- Fold-inner: the block is centred on the left half (x≈500 of 2000), about 190 px from the edge and 185 px from the hinge.
- Phone legible: yes.
