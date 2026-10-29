<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9x-loops/e-fx.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Phone trail and night orb light (2.9xe-f)

Loop survey, written before the first measure. Harness: the 2.9c1 scene
`apps/combat-sandbox/scripts/magic-families.mjs` (headless Chromium on
SwiftShader, no GPU, no pod). Same rows as 2.9c1 (`2.9-loops/families.md`).

| # | Step | Command | Expected elapsed |
|---|---|---|---|
| 1 | baseline still | `node apps/combat-sandbox/scripts/magic-families.mjs --out lanes/2.9x/e-f-shots/before` | about 3 s |
| 2 | tune `families.json` (projectile `trailSpacingS`, lightOrb `light`) | edit | 1 min |
| 3 | `npx vitest run src/fx` in packages/magic | | under 60 s |
| 4 | after still | same script, `--out lanes/2.9x/e-f-shots/after` | about 3 s |
| 5 | reader child on before and after | phone trail continuous; ground lit at night | few min |

Bars: phone projectile trail has no gaps between sprites; the night light
orb visibly lights the ground around the figure; budget rows stay green.

## Result

Elapsed: baseline 3.9 s (the script needed a `knownSpells` import shim, added), after 3.4 s, vitest 0.7 s.
Change: projectile `trail` 10 to 16 and `trailSpacingS` 0.012 to 0.008 (phone beads 0.48 m apart to 0.32 m; desktop shares the value, 0.24 m to 0.16 m); lightOrb `light` 6/8 m to 24/10 m. Budget rows PASS, gl error 0.
Reader (lanes/2.9x/e-f-shots/reader-verdict.md): trail yes (near-continuous, tail faintly beaded); night ground pool yes (subtle, pale warm).
