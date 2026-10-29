<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/nav-solid.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.7m1b: the nav bake and the spots against the solids

One row per measurement; the re-measure runs the same commands.

| Measure | Command | Bar | Measured (2026-10-19) |
|---|---|---|---|
| Mesh inside a collider (humanoid, large) | `node tooling/world-generation/nav/nav_carve.mjs --place <id>` per slice place | 0 solids per class | 0 in all 18 nav places (was 4 places: archon neck 2 solids, border road 3, jungle-root-hollow 2 + 1 large, claywater large 1 before the stood-on rule) |
| Home, bed and work spots in a collider | `node tooling/world-generation/worldgen/spot_solids.mjs --place <id>` per slice place | 0 | 0 in the 16 places (was 7: riverwalk 3, claywater 1, opening-work-camp 3) |
| Walk crossings, opening-work-camp 06:00-06:45 | `npx vitest run src/people/solidWalk.rapier.test.ts` (packages/scene) | 0 crossings; no walker held over 10 steps | 0 crossings without and with bodies; most held 2 steps (was 351/271/221) |
| Tool tests | `node --test tooling/world-generation/worldgen/spot_solids.test.mjs tooling/world-generation/nav/nav_carve.test.mjs` | pass | 4/4 |

No capture: nothing here is drawn. A reader is not needed.
