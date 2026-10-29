<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/weapon-class.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.7a2: every weapon class strikes inside its own contact sweep

One row per chain attack (each class with its own blade length and hand, plus dual wield); the re-measure runs the same command.
Tool: `apps/combat-sandbox/scripts/measure-contact-windows.mjs` (minimum phase one authored 30 Hz key, entry cross-fade and the settle after 0.85 of the clip excluded).
Gate: `MEASURE_TABLE=/tmp/a2/windows.json npx vitest run apps/combat-sandbox/scripts/lib/contact-windows.test.mjs` (19 passed, 2026-10-19).
Bar: a window is found for every row. Shipped is the moveset's contact window before the 0.04 margin either side; a shipped window that differs from the measured one is a borrowed reference window (the one-handed set) noted in its moveset file.
The beast hand-to-hand set (moveset `beastH2h`, class unarmed by race) measures by claw-to-torso contact (`--target-standoff`, 2.7a2c; 20 passed): L1 0.693-0.794, L2 off 0.493-0.566, L3 0.354-0.404, H 0.475-0.535, H2 off 0.495-0.529 (the left claw never reaches the torso on the axis at 0.66 m). Shortspear heavy and heavy2 share one thrust (1.333 s, sweep 0.456-0.675) but are sidestep power attacks: the feet carry the body about 0.9 m sideways (ground track; the reference lunge is not applied under foot-driven motion), and the thrust meets a torso only 20-60 degrees to the spear hand's side (`--target-standoff 1.37 --bearing`). The right step opened the chain with the warden 17-31 degrees the wrong way, so heavy1 never touched; the chain now opens with the left step (-21 to -26 degrees) and follows with the right (`SHORTSPEAR_HEAVY_ORDER`, blades.test.ts, 2.7a2d). The beast heavies lost the warden to staging drift (70-99 degrees off by the heavy); beast-unarmed-chain locks on at 3.9 s so each heavy starts facing it. Pod re-run 2.7a2e (A40): unarmed PASS (beast-unarmed-chain green under the BEAST_H2H_LIGHT_3 per-clip rotation allowance, visual-validation.mjs `CLIP_ANGULAR_STEP_ALLOWANCES`), spear PASS, but shortspear-heavy-chain lands heavy1 only (1.2 s): a chained heavy2 inherits heavy1's attack direction (CombatRuntime combo successor passes `playerAttackDirection`), so a lock-on press cannot re-aim it. Planner call (2.7a2f): the left step plays in both heavy slots (`SHORTSPEAR_HEAVY_ORDER`, SHORTSPEAR_HEAVY excluded in visualAnimationExclusions.json); the combo successor is unchanged. blades.test.ts shows the warden in the contact band for 3 or more of 5 sweep samples of heavy2 (the right step second: fewer than 3). shortspear-heavy-chain now expects two blows (`playerHits`: heavy 28.57, heavy2 36.78 ± 1.0). Pod check owed: no card under $0.60/h in stock at 19:00Z. Close-ups: a2e's reader gave the spear MATCH and the 9 fist stills PROBLEM (wireframe clutter, overlap; `lanes/2.7/a2e-shots/closeups/reader-verdict.md`). The close-up now asks for the sensor view (`?sensorview=1`: no collider wireframes, health bar or view cone; sensors drawn at 2.5x, character `applySensorView`). Pod 2.7cap2 (A4000): offense-outcomes PASS, but shortspear-heavy-chain FAIL, with 1 of 2 blows landed (heavy 28.57; heavy2 none), so the predicted 36.78 is neither confirmed nor replaced. The player states are SHORTSPEAR_HEAVY_2 twice, as the planner call set. The second left-step thrust starts from where the first step put the body, about 0.9 m to the side, with the attack direction inherited, so the warden is off the thrust's 20-60 degree band. Not yet measured with `--bearing`. The sensor-view close-ups were re-shot: 1 GREEN (weak), 8 RED. The actors fuse into one shape, because the camera sits nearly behind the target, and the sensors carry no hand label (`lanes/2.7/a2f-shots/closeups/reader.md`). 2.7a3 measured the cap2 and a2e pod telemetry. The left step carries the body 1.16 m sideways. A second left step leaves the warden 22-48 degrees off, with the tip at least 1.01 m from the torso. The right step second walks the body back and brings the tip to 0.38 m. With the warden 0.4 m nearer (`SHORTSPEAR_WARDEN_BEARING` 19.3, `SHORTSPEAR_WARDEN_STANDOFF` 0.968), both thrusts pass 0.21-0.22 m from the torso line, which is heavy1's landing distance. `SHORTSPEAR_HEAVY_ORDER` is now left then right, and SHORTSPEAR_HEAVY is unexcluded. The heavy2 damage expectation keeps 36.78 until the pod measures it. Close-ups: the camera stands on the striking hand's side (`closeupPose` `side`), and each sensor carries a label ("R hand", "L hand", "foe"; captureView `SENSOR_LABELS`). Pod owed: at 20:05Z the only card under $0.60/h in stock was the barred community RTX 3070; the secure L4 ($0.59/h) sold out at create.

| Class | Attack | Clip | Hand | Blade m | Measured | Shipped |
|---|---|---|---|---|---|---|
| dagger | light1 | `LIGHT_1` | main | 0.42 | 0.350-0.462 | 0.365-0.475 |
| dagger | light2 | `LIGHT_2` | main | 0.42 | 0.337-0.431 | 0.346-0.423 |
| dagger | light3 | `LIGHT_3` | main | 0.42 | 0.458-0.524 | 0.476-0.774 |
| dagger | heavy | `HEAVY` | main | 0.42 | 0.653-0.750 | 0.543-0.720 |
| dagger | heavy2 | `HEAVY_2` | main | 0.42 | 0.470-0.537 | 0.470-0.543 |
| shortSword | light1 | `LIGHT_1` | main | 0.72 | 0.350-0.469 | 0.365-0.475 |
| shortSword | light2 | `LIGHT_2` | main | 0.72 | 0.337-0.437 | 0.346-0.423 |
| shortSword | light3 | `LIGHT_3` | main | 0.72 | 0.458-0.530 | 0.476-0.774 |
| shortSword | heavy | `HEAVY` | main | 0.72 | 0.535-0.562 | 0.543-0.720 |
| shortSword | heavy2 | `HEAVY_2` | main | 0.72 | 0.470-0.543 | 0.470-0.543 |
| straightSword | light1 | `LIGHT_1` | main | 0.98 | 0.350-0.475 | 0.365-0.475 |
| straightSword | light2 | `LIGHT_2` | main | 0.98 | 0.337-0.437 | 0.346-0.423 |
| straightSword | light3 | `LIGHT_3` | main | 0.98 | 0.458-0.530 | 0.476-0.774 |
| straightSword | heavy | `HEAVY` | main | 0.98 | 0.535-0.562 | 0.543-0.720 |
| straightSword | heavy2 | `HEAVY_2` | main | 0.98 | 0.470-0.543 | 0.470-0.543 |
| scimitar | light1 | `LIGHT_1` | main | 0.95 | 0.350-0.469 | 0.365-0.475 |
| scimitar | light2 | `LIGHT_2` | main | 0.95 | 0.337-0.437 | 0.346-0.423 |
| scimitar | light3 | `LIGHT_3` | main | 0.95 | 0.458-0.530 | 0.476-0.774 |
| scimitar | heavy | `HEAVY` | main | 0.95 | 0.535-0.562 | 0.543-0.720 |
| scimitar | heavy2 | `HEAVY_2` | main | 0.95 | 0.470-0.543 | 0.470-0.543 |
| greatsword | light1 | `GREATSWORD_LIGHT_1` | main | 1.42 | 0.410-0.480 | 0.410-0.480 |
| greatsword | light2 | `GREATSWORD_LIGHT_2` | main | 1.42 | 0.365-0.418 | 0.365-0.418 |
| greatsword | light3 | `GREATSWORD_LIGHT_3` | main | 1.42 | 0.426-0.507 | 0.426-0.507 |
| greatsword | heavy | `GREATSWORD_HEAVY` | main | 1.42 | 0.420-0.466 | 0.420-0.466 |
| greatsword | heavy2 | `GREATSWORD_HEAVY_2` | main | 1.42 | 0.419-0.486 | 0.419-0.486 |
| axe | light1 | `LIGHT_1` | main | 0.78 | 0.350-0.469 | 0.365-0.475 |
| axe | light2 | `LIGHT_2` | main | 0.78 | 0.337-0.437 | 0.346-0.423 |
| axe | light3 | `LIGHT_3` | main | 0.78 | 0.458-0.530 | 0.476-0.774 |
| axe | heavy | `HEAVY` | main | 0.78 | 0.535-0.562 | 0.543-0.720 |
| axe | heavy2 | `HEAVY_2` | main | 0.78 | 0.470-0.543 | 0.470-0.543 |
| greataxe | light1 | `GREATAXE_LIGHT_1` | main | 1.35 | 0.414-0.480 | 0.414-0.480 |
| greataxe | light2 | `GREATAXE_LIGHT_2` | main | 1.35 | 0.365-0.418 | 0.365-0.418 |
| greataxe | light3 | `GREATAXE_LIGHT_3` | main | 1.35 | 0.430-0.489 | 0.430-0.489 |
| greataxe | heavy | `GREATAXE_HEAVY` | main | 1.35 | 0.467-0.520 | 0.467-0.520 |
| greataxe | heavy2 | `GREATAXE_HEAVY_2` | main | 1.35 | 0.419-0.486 | 0.419-0.486 |
| mace | light1 | `LIGHT_1` | main | 0.8 | 0.350-0.469 | 0.365-0.475 |
| mace | light2 | `LIGHT_2` | main | 0.8 | 0.337-0.437 | 0.346-0.423 |
| mace | light3 | `LIGHT_3` | main | 0.8 | 0.458-0.530 | 0.476-0.774 |
| mace | heavy | `HEAVY` | main | 0.8 | 0.535-0.562 | 0.543-0.720 |
| mace | heavy2 | `HEAVY_2` | main | 0.8 | 0.470-0.543 | 0.470-0.543 |
| warhammer | light1 | `GREATAXE_LIGHT_1` | main | 1.3 | 0.414-0.480 | 0.414-0.480 |
| warhammer | light2 | `GREATAXE_LIGHT_2` | main | 1.3 | 0.365-0.418 | 0.365-0.418 |
| warhammer | light3 | `GREATAXE_LIGHT_3` | main | 1.3 | 0.430-0.489 | 0.430-0.489 |
| warhammer | heavy | `GREATAXE_HEAVY` | main | 1.3 | 0.467-0.520 | 0.467-0.520 |
| warhammer | heavy2 | `GREATAXE_HEAVY_2` | main | 1.3 | 0.419-0.486 | 0.419-0.486 |
| spear | light1 | `PIKE_LIGHT_1` | main | 2.1 | 0.310-0.387 | 0.310-0.387 |
| spear | light2 | `PIKE_LIGHT_2` | main | 2.1 | 0.310-0.387 | 0.310-0.387 |
| spear | light3 | `PIKE_LIGHT_3` | main | 2.1 | 0.628-0.722 | 0.628-0.722 |
| spear | heavy | `PIKE_HEAVY` | main | 2.1 | 0.337-0.444 | 0.337-0.444 |
| spear | heavy2 | `PIKE_HEAVY_2` | main | 2.1 | 0.319-0.444 | 0.316-0.444 |
| pike | light1 | `PIKE_LIGHT_1` | main | 2.5 | 0.310-0.387 | 0.310-0.387 |
| pike | light2 | `PIKE_LIGHT_2` | main | 2.5 | 0.310-0.387 | 0.310-0.387 |
| pike | light3 | `PIKE_LIGHT_3` | main | 2.5 | 0.628-0.722 | 0.628-0.722 |
| pike | heavy | `PIKE_HEAVY` | main | 2.5 | 0.337-0.444 | 0.337-0.444 |
| pike | heavy2 | `PIKE_HEAVY_2` | main | 2.5 | 0.316-0.444 | 0.316-0.444 |
| halberd | light1 | `HALBERD_LIGHT_1` | main | 2.2 | 0.383-0.480 | 0.383-0.480 |
| halberd | light2 | `HALBERD_LIGHT_2` | main | 2.2 | 0.310-0.387 | 0.310-0.387 |
| halberd | light3 | `HALBERD_LIGHT_3` | main | 2.2 | 0.441-0.553 | 0.441-0.553 |
| halberd | heavy | `HALBERD_HEAVY` | main | 2.2 | 0.531-0.628 | 0.531-0.628 |
| halberd | heavy2 | `HALBERD_HEAVY_2` | main | 2.2 | 0.480-0.565 | 0.480-0.565 |
| rapier | light1 | `RAPIER_LIGHT_1` | main | 1.1 | 0.256-0.425 | 0.256-0.425 |
| rapier | light2 | `RAPIER_LIGHT_2` | main | 1.1 | 0.331-0.400 | 0.331-0.400 |
| rapier | light3 | `RAPIER_LIGHT_3` | main | 1.1 | 0.240-0.353 | 0.240-0.353 |
| rapier | heavy | `RAPIER_HEAVY` | main | 1.1 | 0.694-0.722 | 0.451-0.569 |
| rapier | heavy2 | `RAPIER_HEAVY_2` | main | 1.1 | 0.464-0.571 | 0.464-0.571 |
| katana | light1 | `KATANA_LIGHT_1` | main | 1.05 | 0.356-0.425 | 0.356-0.425 |
| katana | light2 | `KATANA_LIGHT_2` | main | 1.05 | 0.375-0.500 | 0.375-0.500 |
| katana | light3 | `KATANA_LIGHT_3` | main | 1.05 | 0.407-0.442 | 0.476-0.774 |
| katana | heavy | `KATANA_HEAVY` | main | 1.05 | 0.745-0.783 | 0.745-0.783 |
| katana | heavy2 | `KATANA_HEAVY_2` | main | 1.05 | 0.375-0.429 | 0.375-0.429 |
| claw | light1 | `CLAW_LIGHT_1` | main | 0.45 | 0.394-0.500 | 0.394-0.500 |
| claw | light2 | `CLAW_LIGHT_2` | main | 0.45 | 0.406-0.500 | 0.406-0.500 |
| claw | light3 | `CLAW_LIGHT_3` | main | 0.45 | 0.349-0.372 | 0.476-0.774 |
| claw | heavy | `CLAW_HEAVY` | main | 0.45 | 0.458-0.528 | 0.458-0.528 |
| claw | heavy2 | `CLAW_HEAVY_2` | main | 0.45 | 0.419-0.475 | 0.419-0.475 |
| shortspear | light1 | `SHORTSPEAR_LIGHT_1` | main | 1.5 | 0.371-0.561 | 0.371-0.561 |
| shortspear | light2 | `SHORTSPEAR_LIGHT_2` | main | 1.5 | 0.371-0.561 | 0.371-0.561 |
| shortspear | light3 | `SHORTSPEAR_LIGHT_3` | main | 1.5 | 0.458-0.524 | 0.458-0.524 |
| shortspear | heavy | `SHORTSPEAR_HEAVY` | main | 1.5 | 0.456-0.675 | 0.456-0.675 |
| shortspear | heavy2 | `SHORTSPEAR_HEAVY_2` | main | 1.5 | 0.456-0.675 | 0.456-0.675 |
| unarmed | light1 | `H2H_LIGHT_1` | main | 0.1 | 0.436-0.521 | 0.436-0.521 |
| unarmed | light2 | `H2H_LIGHT_2` | off | 0.1 | 0.436-0.507 | 0.436-0.507 |
| unarmed | light3 | `H2H_LIGHT_3` | main | 0.1 | 0.648-0.705 | 0.648-0.705 |
| unarmed | heavy | `H2H_HEAVY` | main | 0.1 | 0.475-0.554 | 0.475-0.554 |
| unarmed | heavy2 | `H2H_HEAVY_2` | off | 0.1 | 0.495-0.529 | 0.495-0.529 |
| staff | light1 | `QUARTERSTAFF_LIGHT_1` | main | 1.6 | 0.343-0.419 | 0.343-0.419 |
| staff | light2 | `QUARTERSTAFF_LIGHT_2` | main | 1.6 | 0.339-0.403 | 0.339-0.403 |
| staff | light3 | `QUARTERSTAFF_LIGHT_3` | main | 1.6 | 0.615-0.722 | 0.615-0.722 |
| staff | heavy | `QUARTERSTAFF_HEAVY` | main | 1.6 | 0.397-0.510 | 0.397-0.510 |
| staff | heavy2 | `QUARTERSTAFF_HEAVY_2` | main | 1.6 | 0.490-0.687 | 0.490-0.687 |
| dualWield | offLight | `DW_ATTACK_LEFT` | off | 0.98 | 0.314-0.436 | 0.322-0.448 |
| dualWield | offPower | `DW_POWER_LEFT` | off | 0.98 | 0.500-0.630 | 0.511-0.639 |
| dualWield | dualPower | `DW_POWER_DUAL` | off | 0.98 | 0.424-0.522 | 0.350-0.533 |
