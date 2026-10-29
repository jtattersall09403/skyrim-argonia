<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9b-loops/journeys.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the three crafting journeys (2.9b lane j)

The owner plays alchemy, smithing and enchanting as journeys (0150). Each
journey is a script as data (`journeys/<id>.json`, the 2.9x schema in
lanes/2.9x/briefs/y-schema.md plus the crafting verbs below), driven by
three runners as docs/phases/2-slice/2.9x-loops/journey.md describes:

- **H-scene**: `packages/scene/src/interact/journey.ts` `runJourney` over the
  interact session with every crafting option (stations and recipes,
  alchemy, enchanting), the place's spots from its published bundle
  (`interactSpotsOf`), the items session's belt and the magic session.
  Test: `packages/scene/src/interact/journey-session.test.ts` (crafting cases).
- **H-game**: the same scripts through the game's composition
  (`useWalkInteract` with what `GameWorld.tsx` passes, the store, the game's
  wiring). Test: `apps/game/src/journey.test.tsx` (crafting cases).
- **Pod**: the studio and the game filmed as strips (`journey=<id>`), read
  by a `reader` child (lanes/2.9b/j-reader.md).

Crafting verbs (`do.action`): gather{place,node}, openStation{place,station},
brew{effect,ingredients}, drink{effect,slot}, coat{effect,slot}, hit{target},
useCharged{target}, buyItem{npc,item,count}, forge{recipe,times?},
temper{item}, soulTrap{target}, enchant{item,effect,magnitude,duration,gem},
disenchant{item}, recharge{item,gem}. `start.grant` and `start.learned` are
the tester's kit (the pod's grantKit, 0149 §3). Expect extras: has,
stationVerbs, brewed, made (the potion's effects, shown or hidden), active, victim, coating, temperGrade, enchanted,
learned, skillRose.

On demand only: nothing here is in check.mjs, CI, visual:check's default
groups or any regular gate.

## How to run it

- `cd packages/scene && JOURNEY=1 npx vitest run src/interact/journey-session.test.ts -t crafting` (JOURNEY unset: skipped, so no regular gate runs them)
- `cd apps/game && JOURNEY=1 npx vitest run src/journey.test.tsx` (the crafting cases and the journey probe)
- Pod: tooling/gpu-lane/README.md § The loop with `--spots lanes/2.9b/j-shots/spots.txt`.

## The game on the pod

The game URL with `?probe=1` mirrors `__GAME_JOURNEY__` (apps/game/src/gameSeam.ts
`createJourneyProbe`, published in GameWorld.tsx beside the trip probe): `warm()`
(the render warm gate) and `state()` (hands, drawn, screen open, active effect ids,
the main hand's coating, bag counts, temper grades, the main hand's enchantment).
It only reads; it has no setter and starts nothing (0149).

## Survey

Verdicts: pass; R (red: the mechanism and file:line in the notes); P (partly
reachable: the missing seam, file:line); G/U/R for the pod per the reader.
ms = the runner's step time (headless) or the step's elapsed time (pod).

| journey | step | H-scene (ms, verdict) | H-game (ms, verdict) | pod studio (ms, verdict) | pod game (ms, verdict) |
|---|---|---|---|---|---|
| crafting-alchemy | gather-fungal-pod | 7.4 pass | 10.3 pass | 6277 pass (j4) | not filmed (no game pod reader) |
| crafting-alchemy | open-alchemy | 7.6 pass | 5.6 pass | 20868 pass (j4; panel about 7 s after the prompt) | not filmed (no game pod reader) |
| crafting-alchemy | brew-restore-health | 2.7 pass | 2.9 pass | 3553 pass (j4, frame 54) | not filmed (no game pod reader) |
| crafting-alchemy | close-alchemy | 0.3 pass | 0.2 pass | 869 pass (j4) | not filmed (no game pod reader) |
| crafting-alchemy | drink-restore-health | 2.2 P | 1.4 P | 5913 pass (j4: the brew leaves the bag, frames 61-62; no effect icon read) | not filmed (no game pod reader) |
| crafting-alchemy | open-alchemy-again | 4 pass | 4.4 pass | 1108 pass (j4) | not filmed (no game pod reader) |
| crafting-alchemy | brew-poison | 1.3 pass | 1.3 pass | 3117 pass (j4, frames 67-68) | not filmed (no game pod reader) |
| crafting-alchemy | close-alchemy-again | 0.3 pass | 0.2 pass | 850 pass (j4) | not filmed (no game pod reader) |
| crafting-alchemy | coat-blade | 1.6 pass | 1 pass | 3390 pass (j4 and j5 filmed the kit's unbrewed stack on the belt, whose template name is right; the brewed slot names as the bag does, proven at the HUD in `beltHost.test.tsx`, 2.9b-c4; the next pod films the brewed slot) | not filmed (no game pod reader) |
| crafting-alchemy | hit-hostile | 1.6 pass, seam played | 1 pass, seam played | 2916 R (j4): no wasp on frames 74-79 | not filmed (no game pod reader) |
| crafting-smithing | buy-bog-iron | 5.2 pass | 5.5 pass | 45588 R (j4): no trade panel from the work-socket start (frames 1-112) | not filmed (no game pod reader) |
| crafting-smithing | buy-leather-strips | 1.7 pass | 1.8 pass | 21745 R (j4): follows buy-bog-iron | not filmed (no game pod reader) |
| crafting-smithing | open-forge | 2.6 pass | 5.1 pass | R (j4): run 1 at (1995.5, 2551.2) opened the grindstone (1.05 m, nearest); runs 2-3 at (1992.2, 2549.0) opened nothing; now (1992.8, 2549.6), unfilmed | not filmed (no game pod reader) |
| crafting-smithing | forge-iron-sword | 1 pass | 1.7 pass | R (j4): follows open-forge | not filmed (no game pod reader) |
| crafting-smithing | close-forge | 0.2 pass | 0.2 pass | 961 R: follows the missed buy | not filmed (no game pod reader) |
| crafting-smithing | open-inventory | 0.2 pass | 0.1 pass | 1369 R: follows the missed buy | not filmed (no game pod reader) |
| crafting-smithing | equip-iron-sword | 0.3 pass | 0.1 pass | R (j4): no iron sword to equip | not filmed (no game pod reader) |
| crafting-smithing | close-inventory | 0.1 pass | 0 pass | 2023 R: follows the missed buy | not filmed (no game pod reader) |
| crafting-smithing | open-grindstone | 2.2 pass | 2.7 pass | 20839 R (j4): prompt shows at (1996.0, 2554.0) but no panel opens (frames 211-257) | not filmed (no game pod reader) |
| crafting-smithing | temper-grade-1 | 1.1 pass | 1.4 pass | R (j4): follows open-grindstone | not filmed (no game pod reader) |
| crafting-enchanting | soul-trap-leech | 2.6 pass | 2.5 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | open-enchanting | 2.2 pass | 3.9 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | disenchant-chills | 0.9 pass | 3.1 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | enchant-dagger | 1.5 pass | 2.3 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | close-enchanting | 0.2 pass | 0.2 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | open-inventory | 0.2 pass | 0.1 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | equip-dagger | 0.4 pass | 0.3 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | close-inventory | 0.1 pass | 0.1 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | strike-enchanted | 1.4 pass, seam played | 1.7 pass, seam played | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | open-enchanting-again | 4.4 pass | 2.8 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |
| crafting-enchanting | recharge-dagger | 1 pass | 1.7 pass | R (j4): wamasu kill at the table, death screen from frame 1 (place-builder: move its home) | not filmed (no game pod reader) |

"pass, seam played" = the step passed with the runtime's inline seam played by the host (named in the step's `unreachable`).
Headless measured 2026-10-20, second measure after lanes e, f, d, w9 and p landed: scene 269 ms, game 460 ms test time for the file; every step under 10 ms.

## Findings (headless)

1. **FIXED (2.9b-b3): a brewed potion on the belt is never the row drunk.** The belt now holds `Belt.potions` (the brew's `potion.id`) beside the item id and `beltPotion` matches it. The belt holds an
   item id and `beltPotion` drinks the first stack of it
   (packages/game-core/src/inventory/belt.ts:90-93). A brew takes a catalogue
   template id (`potionTemplateOf`, packages/crafting/src/alchemy.ts:68-77), here
   healing-draught, which the start kit also carries, so pressing the belt drinks a
   kit draught and the brewed potion stays in the bag. Fix at source: the belt keeps
   the potion's id (`potion.id`) beside the item id, and `beltPotion` matches it.
   Owner: game-core inventory (planner).
2. **FIXED (2.9b-b3): a drunk restore never shows on the effects strip.** `magic.drink` now lists a restore as a display timed entry for its brewed duration (pool heal unchanged). A restore lands as a
   pending pool drain, not a timed entry (packages/scene/src/ui/playerMagic.ts:262-271
   `landPotion`), and the strip reads only the timed stack
   (packages/scene/src/ui/session.ts:189-192). Morrowind lists a Restore Health
   potion in the active effects for its duration. Owner: magic (planner).
3. **Seam played: a landed hit's coating and charge.** CombatRuntime.tsx calls
   `onCoatedHit` inline and has no call from a landed hit to `useEnchantment`
   (lanes/2.9b/d-report.md); the host plays both. Owner: lane d or the planner.
4. **Note: the reference character sees no effect names.** Alchemy 10 is under the
   first `effectVisibilityAt` (15, skills.json), so the by-effect filter lists nothing
   and the brew shows no effects (it still carries them: `made`). The journeys pick
   the ingredients by row. Owner call if a new character should see the first effect.

Fixed since the first measure: stations and nodes placed (lanes e, p); every
station opens its own window in the game (lane f); the stations take enchant,
disenchant and recharge (lane d); the smith's trade has bog iron and leather
strips; the runner's buy now buys the step's count; the smithing journey buys a
third bog iron for the temper (the temper takes one, packages/crafting/src/smithing.ts:100).

## Findings (pod, 2.9b-j3)

Pod treb9rn3fx5y9r: an A40 secure. The studio was built at HEAD with b3, and the strips were read in lanes/2.9b/j-reader.md.
1. **FIXED (tooling): far teleports dropped the body before the ground streamed.** The journey player (tooling/gpu-lane/measure.mjs `journeyTeleportFn`) and touch-cells `teleportExpr` called the debug `teleport()` (apps/world-studio/src/character/walkHarnessHooks.ts:110-122). That call returns false where `groundAt` is null. Both now take `__STUDIO_GOTO__` and wait for the landing.
2. **FIXED (tooling): a touch tap reported ok on a target below the fold.** touch-cells `centreExpr` now scrolls the target into view and checks `elementFromPoint`. This is why "Ready right" was never pressed in the magic screen at phone or fold, and why the paperdoll and touch-cast strips show the dagger.
3. **R: the smithing journey teleports about 100 m west of the smith.** The journey uses (3306.5, 1457.2). The work socket `socket.upriver-hist-village.idle-trader-work` is at x 3407-3409, z ~1455 (world/sources/blueprints/place.pirate-freeholds.upriver-hist-village.json:18137). Fix the step 1 teleport in journeys/crafting-smithing.json, then check the shelf stocks bog-iron and leather-strips.
4. **R: the coat-blade key `[data-es-bag] [data-es-item]:has-text("Poison")` can never match.** A bag slot carries no text, only an aria-label (packages/ui/src/screens/Items.tsx:127-151), and at Alchemy 10 the brew is named "Unknown Potion" (packages/scene/src/ui/inventory.ts:25-34). Select the slot by its stack id in journeys/crafting-alchemy.json.
5. **R (slice blocker): the Wamasu Shrine's wamasu kills the player at the enchanting table before the journey starts.** The hostile is `creature-at.dunmer-north.the-wamasu-shrine.n1`, home (4733.43, 946.2), territory 120 m. Its home is 8 m from `s-enchant-table` (4727.8, 940.4). A player cannot use the station without fighting it. This is a planner or place call: the journey kills it first, or the station or den moves.
6. **Not a defect: waking inside the Naga camp.** A player who never rested wakes at the last arrival (packages/game-core/src/combat/death.ts:34-36, 62-65; 0144). The strip teleported straight into the camp. A rest or an arrival step before the fight gives a fair wake.

## Findings (pod, 2.9b-j4)

Pod g02ktaa357hl1w: an RTX A2000 community. Built at 50f03ac51 plus the smithing teleport edits; read in lanes/2.9b/j-reader.md § j4.
1. **FIXED (j4): the coat-blade key.** It now selects `[data-es-bag] [data-es-item="weak-magicka-poison"]`, the brew's template id (`potionTemplateOf`, packages/crafting/src/alchemy.ts:68). The poison reaches belt slot 2.
2. **R: belt slot 2 names a brewed poison by its template ("Weak Magicka Poison").** The bag says "Unknown Potion" (packages/scene/src/ui/inventory.ts:25-34 `brewedNameOf`), but the belt's view takes the record name. Fix at source: the belt entry for a stack with `potion` takes `rowNameOf`. Owner: ui or scene (planner).
3. **R: smithing, buying from the work-socket start.** At (3409.5, 1454.5), 10:00, no trade panel opened in 45 s (frames 1-112). The smith's post is `idle-trader-work`, with no day blocks (living.json `hh-smith`). The socket's route runs (3407.45, 1456.23) to (3412.45, 1451.73), and talk reach is 1.6 m (`INTERACTION_REACH_M`, game-core interaction/worldItems.ts:25). The start sits about 2-3 m from either end, so the press likely found nobody in reach. Next step: log the smith's position on the pod and teleport within 1 m of it.
4. **R: smithing, choosing the station at the Bog Iron Workings.** The interaction pick is the nearest station within reach, in 2D (packages/game-core/src/interaction/arbiter.ts:50-57).
   - From (1995.5, 2551.2) the grindstone (1.05 m) won over the forge (1.8 m).
   - From (1992.2, 2549.0) the forge (2.06 m) never opened.
   - The step now stands at (1992.8, 2549.6), 1.26 m from the forge. This is unfilmed.
   - The grindstone at (1996.0, 2554.0) shows its prompt, but no panel opened in about 9 s.
5. **R (place-builder): the enchanting journey is still dead on arrival.** The planner's ruling 1 (move the wamasu's home 40 m or more from the table) moves three sockets in the-wamasu-shrine.layout.json (`idle-wamasu-home`, `idle-wamasu-hunt`, `npc-wamasu`, all on the bank about 11 m from `s-enchant-table`). It needs water and approach geometry, so it is a place-builder job.
6. **R: phone trade paying with goods.** The steps open Vees-Wai's spells service, which buys spells for coin only. The sell grid is empty, and 68 gold was paid in coin. Fix: touch-phone.steps opens a barter service (a trader with `trade`), never `spells`.
7. **R: Naga camp fight.** After the teleport to (2308, 4592), no enemy came on frame and no death in 150 s. Likely the camp's hostiles are not at that spot at 12:51. Next step: aim the teleport from the camp's den sockets.
8. **Not filmed: a refused cast.** Five 3 s holds never emptied the magicka (140) on the phone. Add a grant-free drain first: more holds, or a costlier spell.
9. **Nirnroot: FAIL, day and night.** At 2.8 m the plant reads as a pale curl of about 30 px, with no glow at night. Lever (lanes/2.9b/k2-report.md): `LIVING_SCREEN_GAIN` 1.4 toward 1.8, and a saturation mix toward the emissive hue (windowGlow.ts). Framing: the look point at y 4.9 over 4.5 m ground may sit above the plant. No retune in this lane.

## Findings (pod, 2.9b-j5)

Pod q1m17445ajqizx: an RTX A4000 secure. It filmed the three journeys, the nirnroot stills and the phone and fold strips. The lane died before its readers ran. The j5b readers' verdicts are in lanes/2.9b/j-reader.md § j5. Pod 6va5sx4ctfu1ue (j5b) re-shot the phone strip only. Its journey re-shoot was refused at start because the call had no `--pod`/`--no-pod` (measure.mjs:141), so the journeys stand as j5 filmed them.

Pod studio column for j5. The ms come from strip.json.

| journey | step | pod studio (ms, verdict) |
|---|---|---|
| crafting-alchemy | gather-fungal-pod | 6278 pass |
| crafting-alchemy | open-alchemy | 20814 pass, late (the panel shows at f61, after about 15 s of dead frames) |
| crafting-alchemy | brew-restore-health | 3561 pass |
| crafting-alchemy | close-alchemy | 866 pass |
| crafting-alchemy | drink-restore-health | 4637 P (the effect is in state; no strip icon read) |
| crafting-alchemy | open-alchemy-again | 1066 pass |
| crafting-alchemy | brew-poison | 3229 pass ("You brewed Unknown Potion") |
| crafting-alchemy | close-alchemy-again | 913 pass |
| crafting-alchemy | coat-blade | 3243 P (slot 2 is filled; no coating cue) |
| crafting-alchemy | hit-hostile | 6884 R: no wasp clearly on frame, and the player dies at f99 |
| crafting-smithing | buy-bog-iron | 45644 R: the Talk prompt is Zaxi-Kanna, and the smith is not in reach |
| crafting-smithing | buy-leather-strips | 21669 R: follows the missed buy |
| crafting-smithing | open-forge | 6287 R: a cascade, Zaxi-Kanna's dialogue still open (close-forge observes `open`) |
| crafting-smithing | forge-iron-sword | 4461 R: follows |
| crafting-smithing | close-forge | 953 R: follows |
| crafting-smithing | open-inventory | 947 R: Escape opened the pause deck |
| crafting-smithing | equip-iron-sword | 8478 R: no iron sword |
| crafting-smithing | close-inventory | 4460 pass |
| crafting-smithing | open-grindstone | 6282 pass (the panel opens with Forge, Temper and Mend) |
| crafting-smithing | temper-grade-1 | 5347 R: only the steel sword is listed (no iron sword) |
| crafting-enchanting | soul-trap-leech … recharge-dagger (11 steps) | R: a crocodile kills the player at about 12.7 s, and the death screen covers every later step (red 1, a place-builder job) |

1. **R, FIXED in the tool (unfilmed): a fixed spot misses a person or creature who moves.** Examples: the smith on his work route, the wasp on its hunt, Haj-Tei. A journey `teleport` now takes `actor` and `near_m`. The player lands, reads the actor's live census spot, and stands `near_m` from it, facing it (measure.mjs `journeyTeleportFn`). touch-cells has `teleportto~<id>[~m]` (`teleportToExpr`). An actor inside an interior is refused. Tests: journey.test.mjs and touch-cells.test.mjs, 16/16. The smithing step 1 now names `hh-smith` and alchemy hit-hostile names the wasp.
2. **R, FIXED in the steps (unfilmed): smithing never closed the smith's dialogue.** buy-leather-strips ends with a second Escape, so the forge's E is no longer swallowed by an open modal. The forge spot is now (1993.0, 2549.8), 1.0 m from the forge's use point (1994.0, 2550.0) and 3.5 m from the grindstone (public/province/settlements/place.imperial-fringe.bog-iron-workings.json, `socket.bog-iron-workings.station-forge`).
3. **R: phone barter. Haj-Tei works inside an interior at midday.** The census gives his cell `KeebaHouseCrafter`, with cell-local `at` (102.96, 83.01, 54.4). Before the refusal was added, j5b's teleportto dropped the body at y 260 on a rock slope. The barter step needs an outdoor trader at that hour, or a walk through his door. Next: pick an outdoor `trade` person from the census at 12:00.
4. **R: the refused cast.** Twenty debug `cast("fireball")` calls all returned false, yet the magicka bar is full in phone-drained.jpg. So the cast hook refuses while magicka is full, which means the hook fails before any cost is paid: it is not a refusal for lack of magicka. A held touch cast also leaves the bar full on every frame (j4, j5 and j5b). Mechanism unverified: either the fireball's cost is never charged on the touch path, or magicka refills between frames. Next: one pod probe that reads magicka before and after a hold.
5. **PASS in part: the Naga death (j5b).** `teleportto` landed beside the death-hoppers (2277.7, 4629.7), and `.es-death` was seen with "You died." No enemy is on frame, though, and the wake frames stay at the death spot, at the same position as the final read. The killer is not filmed. In j5 the body ended back at Greenspring, likely a death and a wake at the first spawn (studioWalk.tsx:96-101), and j5b's position log is consistent with that.
6. **Nirnroot (j5 stills):** cyan and saturated, the brightest thing at night, with no bloom. It is legible at night and small and thin by day. If day legibility is wanted, the lever is a deeper emissive hue at the kit (the ownEmit emissive read at tooling/asset-pipeline/pipeline/nif_blocks.py:342-364, carried by build_kit), not a retune.
