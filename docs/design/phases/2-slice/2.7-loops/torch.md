<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/torch.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.7m3: the torch flame

One row per measurement; the re-measure runs the same commands. Report: [lanes/2.7/m3-report.md](../../../../lanes/2.7/m3-report.md).

## Checklist

- [x] An equipped torch burns the shared `torchHandheld` flame (FlameSystem, the campfire's cards and embers, a smaller preset) at the item's AttachLight node, head only.
- [x] The flame's strength is the carried light's level: flame and light flicker and go out together.
- [x] No torch equipped: no flame (tested).
- [x] Phone band keeps the light and cuts embers.
- [x] One flame source: the campfire and the torch call the same FlameSystem.

## Measurements (2026-10-19)

| Measure | Command | Bar | Measured |
|---|---|---|---|
| Fire effect tests | `npx vitest run src/fx/fire` (packages/game-core) | pass | 31/31 |
| Carried flame rig | `npx vitest run src/carriedFlame.test.ts` (packages/character) | pass | 3/3 |
| Character types | `npx tsc --noEmit` (packages/character) | clean | clean |
| Offhand scenarios | `npm run visual:check -w @elder-souls/combat-sandbox -- offhand` | PASS | PASS (dual-wield x2, torch-carry, torch-flame) |
| Cost per band | by design | desktop 3 cards + 3 embers; phone 3 cards + 1 ember | 2 extra draws per carrier; 1 point light, as before |

## Capture and reader

Strip: `lanes/2.7/m3-shots/still-{idle,swing,walk,sheathed}.png` (night staging against a wall).
Checklist for the reader: flame at the head only; flame rises through the swing; light falls on the ground and the wall.
Close: PASS. Idle and swing read weaker because the backlit silhouette hides the shaft.

## Ruling: the sheathed torch

A held torch stays lit while the sword is sheathed (Skyrim's rule; TORCH_MOUNT held = sheathed). The planner's call; sheathing does not douse it.
