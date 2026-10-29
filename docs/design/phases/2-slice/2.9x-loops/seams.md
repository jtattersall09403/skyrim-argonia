<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9x-loops/seams.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: seams of the earlier systems (2.9x § f, lane 2.9xf)

A seam is the transition into and out of a system inside a user journey.
One row per journey, each a scripted headless session on the real packages
and the published slice data (the pattern of
`packages/scene/src/interact/progression-session.test.ts`). The number is
`packages/scene/src/interact/seams-session.test.ts`; every row ends in a
save round trip of the families the journey touched, restored into a fresh
registry with equal state.

Written before the first measure; results and elapsed filled after.

Every row names two owners, the system on each side of the seam (the
bracketed phases); a red goes to both.

| Journey (systems) | Headless measure (bar) | Result | Elapsed |
|---|---|---|---|
| walk → talk → trade → leave (2.5, 2.6) | the Claywater well-keeper is a speaker on the published bundles; `createDialogueHost` opens him, a topic answers and joins `knownTopics`; `host.service("barter")` opens; the scene's `barterScreen` stocks him (`openMerchant`) and its settle buys a ware for coin (gold down by the quote, the shelf down one, the purse up); close; knowledge, trade and disposition round-trip | pass: `topic.about-blackwood` learnt; bought `an-wamasu-belted-robe` for 41 gold (shelf 1 → 0, purse +41); after the round trip a fresh host offers the topic as known | 77 ms |
| pick up → equip → open container → take → drop → burden (2.3) | the item session takes a weapon socket, `equipItem` puts it in the hand, a chest opens and `takeFromContainer` moves its contents, `setDown` drops a thing into the world, `inventoryBurden` follows the carried weight both ways; the world-items families round-trip | pass: steel sword 3.2 kg taken and equipped; 12 more from the chest: band fast 0.018 → mid 0.231; one set down: 12 × 3.2 kg, the hand keeps its copy; after the round trip the chest is empty, the dropped sword is offered, the taken socket is not | 4 ms |
| talk → rent a bed → rest → wake → clock advanced (2.6, 2.8) | the well-keeper's `rest` service opens; `lodgingScreen`'s rent takes the band price and writes `rentBed`; the bed (lodging slug `claywater-station`) reads tier `rented` through `bedTierOf`; the sitting runs 8 h: clock +480 min, catch-up called once at the new minute, the rented bed given back (`restTaken`), wake point `rest`; lodging, death and progression round-trip | pass: `lodging.imperial-fringe.claywater-station.well-keeper` rented for 7 gold; offer `rest`/`rented` with the rented line; 1200 → 1680 min, one catch-up at 1680; bed given back, health full, wake point the inn cell; a second night in the settlement is not a rest without a second rent | 11 ms |
| travel by the service → arrive → people on the lamp clock (2.6, 2.4) | the Claywater landing poler's service from the published graph; `travelServiceHost` resolves a trip, the fare leaves the purse; `tripClock` moves the clock by `tripHours` and catches the people up once at the arrival minute; a roster member's day (`dayOf` + `jitterDay`) gives the block at the arrival minute, and the block changes with the clock | pass: `ferry.imperial-fringe.drowning-gate` east → west, 15 gold, 15.7 m, 0.25 h; one catch-up at the arrival minute; the poler's own day turns `eat` → `work` across a trip placed over its edge | 9 ms |
| fight → die → wake at last rest → walk back → pick up the vastei pile (2.7, 2.8) | closes death-and-wake.md's named gaps: `stepArrival` records the arrival on entering a place; a sitting records `restAt` and a later arrival does not displace it; death through `wakeWithWallet` forms the pile of the whole wallet, wakes at the rest; `wakeCountsRest` counts the rest; `stepDeathPile` recovers inside the radius only | pass: arrival at Claywater; marsh rat dead in 4 blows and on the ledger; the camp sitting's `restAt` survives a later arrival; 321.5 vastei pile at the fall, wallet 0, wake at the camp, `rests` +1; death and respawn round-trip; walking back 75 m in 1 m steps the wallet stays 0 until inside 2 m, then 321.5 | 5 ms |
| cast → levitate → land → fight → sheathe (2.9, 2.7) | a Levitate cast lifts the mode; expiry lands it `grounded`; a blow then resolves through `resolveHit` with the compiled player; sheathing goes through a pure, reachable step | cast → levitate → land → fight pass (mode `levitate`, `grounded` at 31 s, the blow lands). **Red: sheathe.** Draw and sheathe are a ref toggle inside the runtime frame (`packages/character/src/combat/CombatRuntime.tsx:2575-2581`, `equipped.current = !equipped.current`), no pure step to drive or save; lane b (one movement driver, draw and sheathe as buttons) owns that file (`it.todo` in the test) | 2 ms |
| read a document → journal knowledge → dialogue topic unlocked (2.3, 2.5) | the item session's read of a document writes a topic or fact into `KnowledgeState`; the dialogue view then offers the topic | knowledge → topic pass (a topic written into the store is offered as known next conversation). **Red: document → knowledge.** No document names a topic or fact (`world/sources/registries/documents.json`: id, textRef, name, kind, status, item, leaves, sources, notes), and the read reaches only progression (`packages/scene/src/items/useItemScreens.tsx:90` `onRead` → `readBookFor`, `packages/scene/src/items/kills.ts:18`). No brief built it (2.3 § 8 skill books only); needs a `teaches`-style field on the document row and a knowledge write on read (`it.todo`) | 2 ms |

Whole file: 7 passed, 2 todo, 7.9 s wall (vitest, `packages/scene`). The test
joins the affected set by workspace (`packages/scene` and what it depends
on) and by the published data it reads (`tooling/repo-standards/check.mjs`,
vitest job: `apps/world-studio/public/dialogue/`,
`province/travel-services.json`).

## Found on the way (queued, not built here)

- The death pile is placed at the start place and the open ground:
  `apps/game/src/GameWorld.tsx:274` calls `wakeWithWallet(..., { placeId:
  start.placeId, cell: null, ... })`, so a death inside an interior or in a
  later place records the wrong place and cell (the walk tracks the place in
  `apps/game/src/gameProgress.tsx:31`). Fix: pass the tracked place and the
  body's cell.

## Inventory: which of the three checks each system has had

Functionality = unit or headless tests of the system; visual = shots or
strips judged by a reader; seams = a scripted journey across its edges.
Started from the planner's audit (2.1–2.6 no loop folder; 2.7 visual reds
with lane c2; 2.8, 2.9 full) and checked against the tree.

| System | Functionality | Visual | Seams |
|---|---|---|---|
| 2.1 composition | `packages/save/src/*.test.ts` (registry round trip) | `lanes/2.1/*.png` before/after pairs; no reader loop | none of its own; every row here ends in its registry round trip |
| 2.2 UI | `packages/ui` tests | `lanes/2.2/d-shots/` + readers `lanes/2.2/*-reader.md`; ui-lab grid (2.2 loop in loops.md) | none |
| 2.3 items and containers | `packages/scene/src/items/session.test.ts`, `packages/game-core/src/inventory/*.test.ts` | ui-lab `container`, inventory screens; no place shots (`lanes/2.3/` has none) | this survey row 2 (pass), row 7 (red) |
| 2.4 people | `packages/game-core/src/people/*.test.ts`; clock loop `tooling/stats-sim/clock-loop/run.mjs` | `lanes/2.4/*-shots/` (pod and lane shots) | this survey row 4 (pass) |
| 2.5 dialogue | `packages/dialogue/src/**/*.test.ts`, host smoke `packages/dialogue/src/host/smoke.ts` | ui-lab `dialogue*`, `journal*`; voice panels (loops.md 2.5) | this survey rows 1, 7 |
| 2.6 trade and services | `packages/economy/src/*.test.ts`, `packages/scene/src/dialogue/trade.test.tsx`, `TravelMenu.test.tsx` | ui-lab `barter*`, `gift`, `training`, `lodging`; no reader file | this survey rows 1, 3, 4 (pass) |
| 2.7 combat | `packages/game-core/src/combat/*.test.ts`; `2.7-loops/*.md` | `2.7-loops/` strips; reds re-shot by lane c2 (`lanes/2.9x/c2-survey.md`) | `2.7-loops/death-and-wake.md` gaps closed by row 5; sheathe red (row 6) |
| 2.8 progression | `2.8-loops/compile.md`, `skill-use.md`, `vastei.md`, `rest.md`, `balance.md`, `effects.md` | `2.8-loops/screens.md` | `2.8-loops/seams.md`, `progression-session.test.ts` |
| 2.9 magic | `2.9-loops/catalogue.md`, `casting.md`, `effects.md`, `families.md`, `levitation.md`, `people.md` | `2.9-loops/screens.md`, `clips.md`, `lanes/2.9/b5-shots/`, `b6-shots/`, `e3-shots/` | `2.9-loops/seams.md`, `magic-session.test.ts` |

Gaps left: 2.1, 2.3, 2.5 and 2.6 have no reader-judged in-world visual
pass of their own (ui-lab screens only); 2.2 has no seam of its own beyond
the screens these journeys open (the screens are driven here through their
`view` props, not rendered).
