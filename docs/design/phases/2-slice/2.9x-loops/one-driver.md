<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9x-loops/one-driver.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: one movement driver in the studio walk (2.9x § b, lane 2.9xb)

Rule (owner, 2.9x item 1, option A): the studio walk has one driver and no
modes. `?view=character` always mounts the shared `CombatRuntime` (the game's
driver, through `SceneHost` there) on `PlayerMovementController`; walking,
sprint, swim, seats, doors, travel boats and combat run on it as one.
`?fight=<preset>` only picks the kit equipped at spawn (drawn); with no flag
the walk starts sheathed. Draw and sheathe are the existing buttons (R, the
pad, the touch Draw) through one pure step (`game-core/src/combat/drawSheathe.ts`),
the drawn state saved on the inventory; the bag equips. One row per seam;
elapsed is the wall time of the row's command (2026-10-20, this machine, no GPU:
the sandbox scenarios run headless in the job guard).

| Seam | What proves it | Bar | Measured | Elapsed |
|---|---|---|---|---|
| explore (walk, sprint, jump) | `npm run visual:check -w @elder-souls/combat-sandbox -- locomotion` | every scenario PASS | 5/5 PASS (locomotion-free, locomotion-lock-on, enemy-approach, crouch-locomotion, greatsword-locomotion) | 190 s |
| explore → draw → fight → sheathe | `-- attacks`; `drawSheathe.test.ts`; `seams-session.test.ts` fight → sheathe → save → load; `TouchControls.test.tsx` | PASS; the press is one pure step and the drawn state saves | attacks 7/7 PASS; drawSheathe 3/3, the seam row green; the studio touch layer takes the runtime's `equipped` and `dualWield` | 178 s; tests 21 s |
| camera (follow, arm, terrain backstop, free camera) | `-- camera`; the runtime's `cameraGround` and `cameraRef` seams; `walkDriver.tsx` capture camera and short-arm fade | PASS | 4/4 PASS (camera-low-ceiling, locomotion-free, swim-surface-look-up, swim-dive-deep) | 82 s |
| talk / trade (the prompt arbiter on the one driver) | `walkDriver.test.ts`; `seams-session.test.ts` walk → talk → trade | resolves every frame; holds while a screen is up | green; the old fight walk resolved no prompts at all (fixed here) | in the 21 s run |
| swim / dive / breath | `-- swim`; `fightTeleport.test.ts` breath rows | PASS | 6/6 PASS; `swim-studio-path` (the explore drive's scenario) deleted with the drive | 186 s |
| teleport (M, travel, `__STUDIO_GOTO__`) and landing aim | `fightTeleport.test.ts` | the teleport resolves; the body faces the open view, the camera behind it | 7/7 green (new row: the open-view aim at the settling probe, its free arm reported) | in the 21 s run |
| climb | no climb system exists in either driver | n/a | n/a | n/a |
| game mounts the same driver | `packages/scene/src/SceneHost.tsx:36` | the same component | confirmed: the game's `SceneHost` mounts `CombatRuntime`; nothing to align | read |

## Hardware pass (2.9xt, RTX 4000 Ada pod, 2026-10-20)

Built from the working tree on dev at 80dcfcc45 plus the spawn spread (`npm run build && site:compose`), served on the pod, measured with `measure.mjs --spots lanes/2.9x/m-shots/spots.txt --only <pair>`; the panic found with the `diag=rapier` world snapshot and `probes/rapier-replay.mjs` (`lanes/2.9x/t-shots/`, `lanes/2.9x/t-report.md`).

| Seam | What proves it | Bar | Measured | Elapsed |
|---|---|---|---|---|
| no enemy step before its body mounts | `enemyStepMount.test.ts` (a handle with a null body) | passes; fails on the old code | green; zero `setAngvel` errors on the pod | 1 s |
| no two hostile bodies start on one spot | `spawnSpread.test.ts` (Rapier in Node: five ecctrl-shaped capsules on one spot go NaN; spread, 120 clean steps) | passes | green 3/3; on the pod world (step 35 snapshot) 12 NaN bodies as spawned, 0 with the duplicates moved apart | 1 s |
| studio walk loads | ready gate at Greenspring | ready, no page errors | zero page errors, no Rapier panic (376 steps under the probe), scene renders; still NOT READY (warm gate 68.9 s, complete at 150 s) because a frame takes 80-140 ms (below) | 4 loads |
| 10 s walk frame times (2.9xv, b7fb7d9b2, RTX 4000 Ada secure; was 118-143 ms median at 8 fps) | walk window; a hitch is a frame over 2x median | median under 20 ms, no hitch | RED but 5x better. Median / p95 / hitches: gs-walk 21.5 / 41.4 / 19 (longest 369.5); gs-strip 22.2 / 37.0 / 14; naga-walk 31.6 / 45.4 / 0; naga-strip 34.5 / 50.7 / 0. Settled windows: gs-freecam 15.3, gs-shortarm 15.5, naga-shortarm 17.0, mage-day 20.0, mage-close 18.9. Naga is GPU-bound (gpu p50 15-19 ms, 998-1000 draws, 3.4 M tris, against 714 draws at Greenspring), not hostile-bound. Every spot still reads NOT READY at 150 s | 5 runs |
| Greenspring walk strip | reader | PASS | PASS: character visible at 0.5, 5 and 9.5 s, scenery changes; grass overlaps the legs at 9.5 s | reader |
| Naga road strip | reader | PASS | RED: frames identical, a blurred view inside a trunk or foliage, no character | reader |
| teleport landing | stills, reader | PASS | PASS for Greenspring and Naga camp (on the ground, in frame, overlays legible); the third spot (back to Greenspring) FAILED: no warm-ready in 150 s, cause not isolated | reader |
| `?cam=` free camera, short-arm fade | stills, reader | PASS | RED, spot errors: `spots.txt:6` cam y 14 and look y 3 against a 11.7 m ground gives a close-up of leaf litter; `:7` and `:8` `--aim` pitch -1.5 rad looks up (negative is up, `followCamera.ts:24`), so sky and trunk with no character; the fade is unjudged | reader |
| bound dagger by day | stills, reader | visible, not glaring | not visible: `mage-day` frames show head and shoulders only; `mage-close` (`spots.txt:11`, look y 3.8 under the ground) is an under-terrain view. Day gain 1.6 stays unjudged | reader |
