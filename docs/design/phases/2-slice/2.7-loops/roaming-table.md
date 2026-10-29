<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.7-loops/roaming-table.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# The roaming table: survey

The loop row "the roaming table" of [2.7 § Loops](../2.7-combat-and-encounters.md#loops),
lane 2.7c. The table is `packages/game-core/src/people/roaming-bands.json`
(world/98 rows: roaming-band row, band composition, territory-holder); the
code is `packages/game-core/src/encounters`. The re-measure runs this file
top to bottom.

## The spot rule

A spot is eligible by geometry and record (`encounters/eligibility.ts`, the
numbers in the table's `spotRule`): on the baked humanoid nav within 1.5 m;
standing at least 0.25 m above the high-water line (`minDryM`, the compiled
water surface's depth over the ground); 60 m clear of every
place's footprint and 35 m clear of every den; 12 to 45 m off the road; and
by the road-approach rule
([quests/20](../../../quests/20-world-provisions.md) § road-approach rule): a nav sightline from the nearest road point, a walk for the band
to that point within 1.6 times the straight distance, and a 30 m walk back
along the road for the player one way or the other. Candidates are hashed
from the save seed along the road inside each 100 m cell the road crosses
(32 per drawn cell),
so no spot is a fixed marker. Frequency and band are the region's (0004).

## Measurements

| # | Harness | The number | Bar | Capture |
|---|---|---|---|---|
| 1 | `python3 -m worldgen.roaming_bands --check` (in `tooling/world-generation`) | 9 regions, 8 filled, 37 compositions, 0 reds | 0 reds; every slice region filled | none |
| 2 | `python3 -m pytest -q worldgen/test_roaming_bands.py` | 6 passed | green (shape fill, stale band, unfilled slice region, unknown gear and holder all red) | none |
| 3 | `npx vitest run src/encounters` (in `packages/game-core`) | 21 passed: 3 pass and 8 fail spots, a planted clone red, frequency over 20,000 cells within 3 sigma, night holders kept in by day | green | none |
| 4 | the variety measure (closest pair per filled region, distance; a clone is below 1) | dunmer-north 3.50, hist-heartland 3.04, imperial-fringe 2.92, imperial-penal-south 3.19, mercantile-coast 3.50, naga-kur-deeps 3.50, pirate-freeholds 3.21, saxhleel-coast 3.38 | every pair at 1 or more | stills 6 |
| 5 | `node apps/combat-sandbox/scripts/roaming-route.mjs --seeds 400 --json lanes/2.7/c-shots/route.json`: both slice route places, 400 seeds each | hist-heartland on the 40 m route strip: 3,600 road cells, drawn 0.129 per cell against the table's 0.120 (3 sigma 0.016); met 0.83 per km against 1.2 per km of road; 44% of draws find a spot | drawn rate within 3 sigma of the table; every met spot re-checks eligible | stills 6 |
| 6 | the same run, the named walk (Greenspring down the Border road crossings, 471 m) | 88 of 400 seeds meet a band; the slice seed `slice-12` (`encounters/session.ts` `SLICE_SEED`, replaced by 2.13's world seed) meets `crossing-watch` at (4663.5, 1748.0); the session probe (the hosts' `RoamingSession`, record loader and sink) spawns its 4 heads as hostiles | at least one band on the slice seed; the probe spawns at least one hostile | stills 6 |
| 7 | the same run, the other seven slice regions | no baked wild route in the slice (only the two route places are baked off a place) | measured when a route place is baked in the region | none |

Where draws found no spot (row 5), by candidate: off nav 3,937, in water
3,127, no sightline 1,239, in a place 552, at a den 9. The draw holds the
table's frequency; the met rate falls short of it because the Border road
crossings run through river marsh and the route bakes cover only the
footprint plus 12 m. A wider wild bake along the roads would raise it
toward the table; the table is not retuned to make up for the bake.

## Captures

| # | Command | Files | Reader checklist |
|---|---|---|---|
| 6 | `bash tooling/repo-standards/job_guard.sh 2.7c --target 480 --reason "..." -- node apps/combat-sandbox/scripts/people-scene.mjs --roaming lanes/2.7/c-shots/route.json --out lanes/2.7/c-shots --strips none` (working tree, one capture) | `lanes/2.7/c-shots/roaming/<band>-{road,close}.png` for `deep-swamp-pair`, `trade-raid`, `crossing-watch`; `bands.json` | every member visible; on the ground, not in water; seen from the road; apart; dress plausible against the composition; three bands read as three groups |

Reader close: `lanes/2.7/c-reader.md`.

## Route nav strip (2.7c2-nav)

The route places' nav bake now uses `ROUTE_MARGIN_M` 40 m (was the 12 m footprint margin) in `tooling/world-generation/nav/nav_terrain.py`, rebaked for the two `place.route.*` places only. Same 400-seed route run:

| Margin | Cells | Drawn per cell (table 0.120, 3 sigma 0.016) | Met per km (table 1.2) | Draws finding a spot | Named walk | `slice-12` |
|---|---|---|---|---|---|---|
| 12 m (before) | 2,800 | 0.130 | 0.35 | 24% | 41 of 400 | crossing-watch |
| 40 m | 3,600 | 0.129 | 0.83 | 44% | 88 of 400 | crossing-watch |

Wider strips (60, 80, 100 m) gave 0.80, 0.80, 0.78: the rest fail in water or off the walkable marsh, so 40 m is the config value. The table and eligibility numbers are untouched.
