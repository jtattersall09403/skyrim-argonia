<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/stations.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 2.9b stations and resource nodes in the eleven slice places

One row per crafting station socket and resource-node placement in the published bundles of the eleven slice places: 14 stations and 41 node placements. The 43 rows below are lane e's; 2.9b-p added 12 placements (the table at the end). The test also counts 72 plant sockets as nodes (`node.<plantClass>`; pearl clams excluded). Those sockets are listed in [plants.md](plants.md); some are hosted on the placements here. The count equals what `packages/scene/src/interact/stations-reach.test.ts` checks (it also asserts each resolves to a stations.json or node row and lies within the place radius). The semantics review (who uses each station and why it stands there) is `lanes/2.9b/e-semantics.md`; verdicts here are copied from it. Places with no station (rose-bone-waystation, naga-highway-camp-active-north, voriplasm-vault) keep none. The wamasu-shrine's non-crafting shrine socket is not listed. Positions are world x, z in metres.

| place | station class / node | host uid / asset | x, z | who uses it | verdict |
|---|---|---|---|---|---|
| bog-iron-workings | station forge | socket bog-iron-workings.station-forge on sm-forge | 1994, 2550 | the season's diggers | keep |
| bog-iron-workings | station grindstone | socket bog-iron-workings.station-grindstone on sm-grindstone | 1995, 2554 | the season's diggers | keep |
| bog-iron-workings | station workbench | socket bog-iron-workings.station-workbench on sm-workbench | 1996, 2548 | the season's diggers | keep |
| bog-iron-workings | node.marshweed | bmv:landscape/trees/reedsmall2 (n-marshweed) | 2041, 2583 | any gatherer | keep |
| bog-iron-workings | node.somnalius-fern | bmv:landscape/plants/fern01 (n-somnalius-fern) | 2003, 2591 | any gatherer | keep |
| upriver-hist-village | station alchemy (station.alchemy.mortar) | socket upriver-hist-village.station-alchemy on minder-alchemy | 3453, 1425 | hh-smith (forge, bench, grindstone); the tree-minder (alchemy) | keep |
| upriver-hist-village | station forge | socket upriver-hist-village.station-forge on smith-forge | 3305, 1456 | hh-smith (forge, bench, grindstone); the tree-minder (alchemy) | keep |
| upriver-hist-village | station grindstone | socket upriver-hist-village.station-grindstone on smith-grindstone | 3305, 1452 | hh-smith (forge, bench, grindstone); the tree-minder (alchemy) | keep |
| upriver-hist-village | station workbench | socket upriver-hist-village.station-workbench on smith-workbench | 3303, 1453 | hh-smith (forge, bench, grindstone); the tree-minder (alchemy) | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (bk-reed1) | 3455, 1448 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (bk-reed2) | 3458, 1449 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (bk-reed3) | 3463, 1448 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (bk-reed4) | 3469, 1449 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (bk-shore1) | 3457, 1451 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (bk-shore2) | 3465, 1452 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (fl-poolreed1) | 3464, 1444 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (fl-poolreed2) | 3466, 1444 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (fl-reed1) | 3470, 1451 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (fl-reed2) | 3467, 1455 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedsmall1 (fl-reed5) | 3470, 1436 | any gatherer | keep |
| upriver-hist-village | node.hanging-moss | bmv:landscape/plants/florahangingmoss02aaa (n-hanging-moss) | 3438, 1452 | any gatherer | keep |
| upriver-hist-village | node.somnalius-fern | bmv:landscape/plants/espfernbrakencluster01 (n-somnalius-fern) | 3456, 1421 | any gatherer | keep |
| greenspring | station alchemy (station.alchemy.journeyman) | socket greenspring.station-alchemy on craft-alchemy | 4762, 1876 | the tree-minder | keep |
| greenspring | node.rootland-mushroom | bmv:trdata/mushrooms/tr_oth_tallmush01 (node-rootland-mushroom) | 4734, 1889 | any gatherer | keep |
| greenspring | node.swamp-fungal-pod | vanilla:plants/floraswampfungalpod01 (node-swamp-fungal-pod) | 4747, 1889 | any gatherer | keep |
| claywater-station | station alchemy (station.alchemy.journeyman) | socket claywater-station.station-alchemy on sh-alchemy | 314, 3062 | the well-keeper | keep |
| claywater-station | node.marshweed | bmv:landscape/trees/reedsmall2 (node-marshweed) | 328, 3055 | any gatherer | keep |
| claywater-station | node.mountain-flower | vanilla:plants/floramountainflower01purple (node-mtflower) | 326, 3064 | any gatherer | keep |
| lighter-flotilla | station alchemy (station.alchemy.mortar) | socket lighter-flotilla.station-alchemy on pier-alchemy | 3848, 6357 | the purser | keep |
| lighter-flotilla | node.marshweed | bmv:landscape/trees/reedsmall2 (shore-marshweed) | 3820, 6359 | any gatherer | keep |
| pearl-lots | station grindstone | socket pearl-lots.station-grindstone on s-grind | 5398, 4297 | the lot divers | keep |
| the-wamasu-shrine | station enchanting | socket the-wamasu-shrine.station-enchanting on s-enchant-table | 4728, 940 | the offering-bearers (no keeper; owner call open) | keep |
| the-wamasu-shrine | node.hanging-moss | bmv:landscape/plants/florahangingmoss02aaa (n-hanging-moss) | 4732, 944 | any gatherer | keep |
| rose-bone-waystation | node.somnalius-fern | bmv:landscape/plants/fern01 (n-somnalius-fern) | 2546, 6562 | any gatherer | keep |
| voriplasm-vault | node.swamp-fungal-pod | vanilla:plants/floraswampfungalpod01 (node-2) | 1730, 6689 | any gatherer | keep |
| voriplasm-vault | node.rootland-mushroom | bmv:trdata/mushrooms/tr_oth_tallmush01 (node-1) | 1701, 6667 | any gatherer | keep |
| naga-highway-camp-active-north | node.hanging-moss | bmv:landscape/plants/florahangingmoss02aaa (n-hanging-moss) | 2322, 4579 | any gatherer | keep |
| naga-highway-camp-active-north | node.marshweed | bmv:landscape/trees/reedsmall2 (n-marshweed) | 2317, 4583 | any gatherer | keep |
| opening-work-camp | station grindstone (station.grindstone) | socket opening-work-camp.station-grindstone on cw-grindstone | 3947, 1375 | the gang's own hands | keep |
| opening-work-camp | station workbench (station.workbench) | socket opening-work-camp.station-workbench on cw-workbench | 3949, 1376 | the gang's own hands | keep |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedsmall2 (cw-marshweed-1) | 3952, 1391 | any gatherer | keep |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedsmall2 (cw-marshweed-2) | 3955, 1389 | any gatherer | keep |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedsmall2 (cw-marshweed-3) | 3958, 1395 | any gatherer | keep |

## 2.9b-p additions

The first 11 rows are dressing that was already placed. It became a node when its species joined the record. The nirnroot is the one new piece.

| place | station class / node | host uid / asset | x, z | who uses it | verdict |
|---|---|---|---|---|---|
| upriver-hist-village | node.somnalius-fern | bmv:landscape/plants/espfernbrakencluster04 (fl-fern1) | 3459, 1452 | any gatherer | keep |
| upriver-hist-village | node.somnalius-fern | bmv:landscape/plants/espfernbrakencluster04 (fl-fern2) | 3461, 1442 | any gatherer | keep |
| upriver-hist-village | node.somnalius-fern | bmv:landscape/plants/espfernbrakencluster04 (fl-backfern1) | 3452, 1420 | any gatherer | keep |
| upriver-hist-village | node.somnalius-fern | bmv:landscape/plants/espfernbrakencluster04 (fl-backfern2) | 3418, 1424 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedmed1 (fl-reed3) | 3474, 1452 | any gatherer | keep |
| upriver-hist-village | node.marshweed | bmv:landscape/trees/reedmed1 (fl-reed4) | 3472, 1432 | any gatherer | keep |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedmed1 (k-reed1) | 3976, 1363 | any gatherer | keep (reader PASS) |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedmed1 (k-reed2) | 3984, 1362 | any gatherer | keep (reader PASS) |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedmed1 (k-reed3) | 3970, 1366 | any gatherer | keep (reader PASS) |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedmed1 (k-reed4) | 3930, 1346 | any gatherer | keep |
| opening-work-camp | node.marshweed | bmv:landscape/trees/reedmed1 (k-reed5) | 3938, 1348 | any gatherer | keep |
| greenspring | node.nirnroot | vanilla:plants/nirnroot01 (node-nirnroot) | 4717, 1864 | any gatherer | blocker: reader FAIL, the leaves render pale and near translucent with no glow (a kit material defect); removing it is a rebuild, so it waits on the kit fix |
