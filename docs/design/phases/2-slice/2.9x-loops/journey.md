<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.9x-loops/journey.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: the player journey across 2.7–2.9 (2.9x lane y)

The owner plays 2.7 combat, 2.8 progression and 2.9 magic as one journey
(lanes/2.9x/owner-words-journey.md, decision 0149). Authoring a journey or a seam scene for any phase follows the
[journey-author skill](../../../../.claude/skills/journey-author/SKILL.md). A journey is a script
as data (`journeys/<id>.json`, schema in lanes/2.9x/briefs/y-schema.md):
each step names its action (`do`), the player's real input (`keys`), the
transition it tests and its expected state (hands, drawn, screen, clip,
effect). Step 0 may carry a `stage` block (`JourneyStage`: `at`, `hour`,
`place`, `cell`, `near`), the scene's state set once before any key;
`start` holds the grants (kit, items, skills, learned effects, the dice).
One script drives three runners:

- **Headless scene**: `packages/scene/src/interact/journey.ts` `runJourney`
  maps `do` to the shipped APIs (item session, magic link, drawSheathe,
  dodgeStart, intent from the scripted keys, castCycle, rest, the
  seller and teacher services). Test: `packages/scene/src/interact/journey-session.test.ts`.
- **Headless game**: the same scripts through the game's wiring
  (`useGameUiWiring`, the game's start kit, Greenspring's seller and
  teacher). Test: `apps/game/src/journey.test.tsx`.
- **Pod studio**: the spot token `journey=<id>[/<fps>]` (tooling/gpu-lane
  `spots.mjs`, `measure.mjs playJourney`) plays `keys` with real
  keyboard and mouse input and films a numbered strip with a sidecar
  (`lanes/2.9x/y-shots/<id>/NNNN.jpg`, `strip.json`: per frame the step and
  phase; per step the expected state, the observed state from the
  observe-only `journeyState()` on the studio's debug hook, and the diff).
  A capture kit may be granted (`grantKit`, capture hook only, 0149 §3).

When a journey runs and how it closes: loops.md § Rules (a staged scene,
after the focused loops, looped until green; decision 0155).

On demand only: nothing here is in check.mjs, CI, visual:check's
default groups or any regular gate.

## How to run it

- Headless (each under 1 s test time, ~10 s wall with imports):
  `cd packages/scene && npx vitest run src/interact/journey-session.test.ts`;
  `cd apps/game && npx vitest run src/journey.test.tsx`.
- Pod: build the site, boot one pod, sync, tunnel (tooling/gpu-lane/README.md
  § The loop), then
  `node tooling/gpu-lane/measure.mjs --run <run> --cdp 127.0.0.1:<port> --no-pod --spots lanes/2.9x/y-shots/spots.txt --only gs-sword,gs-start,gs-w`.
  Each journey takes 24–46 s; hand the strips to a `reader` child.

## What each app lacked at the start

- Studio: a `fight=` preset picker stood in for the player's draw-and-fight
  flow (deleted; the studio starts with the game's start kit). The pod had
  no action token beyond `cast=` and `walk=`.
- Game: no proof of its own; no capture route on the pod (see below).
- Both: no script that crosses the systems in the order a player does.

## Survey (first pod run, RTX 5080, 2026-10-20)

H-scene and H-game: every step passes or is reported partly reachable
(light, heavy, block, parry: the intent edge, the loadout clip and the pure
guard/parry functions; the dispatch is inline at CombatRuntime.tsx ~2633-2790;
lock-on: the intent edge; walk: the W intent). Pod: the reader's verdicts
(lanes/2.9x/y-reader.md); ms = the step's elapsed time on the pod.

| journey | step | H-scene | H-game | pod studio (ms, verdict) | pod game |
|---|---|---|---|---|---|
| sword-and-spell | open-inventory | pass | pass | 1321 G | not captured |
| | equip-sword, equip-shield | pass | pass | 5040, 4708 R (click selectors missed; the bag kit left both worn, fixed fc4a463fb) | – |
| | close-inventory, draw, light, heavy, block | pass | pass (combat partly) | 181–224, 116–180 R (deck still open: the focus model's Escape backs out of the action panel first) | – |
| | parry | pass (partly) | pass (partly) | 625 U | – |
| | lock-on | pass (intent) | pass (intent) | 883 R: locked a band a settlement away, camera swung off (fixed cd641a750) | – |
| | roll, two-hand grip/release | pass | pass | 1410, 982, 1009 R/U (camera still off after lock-on) | – |
| | spell to off hand, cast off hand | pass | pass | 1518 G, 2885 G (weak effect) | – |
| | belt set, belt to shield, belt to spell | pass | pass | 1445, 707, 897 G/U | – |
| | cast main hand | pass | pass | 2922 G (fireball visible) | – |
| | sheathe, rest | pass | pass | 1377 U, 5174 U ("cannot rest while hunted": alert suspicious after the fight) | – |
| start-to-first-fight | start kit, draw, light, heavy, block | pass | pass | 929–2100 G | – |
| | sheathe for the walk, walk to hostile, parry | pass | pass | 1403, 2952, 1457 U | – |
| | lock-on, roll, sheathe after | pass | pass | 922, 1386, 1402 R (lock-on range, fixed) | – |
| | buy a spell, learn a spell | pass | pass | 15115, 4452 R: no dialogue window opened after the teleport and E | – |
| | spell to off hand … sheathe at end | pass | pass | R (follows from the failed purchase) | – |
| w-cells | draw, magic window, bound dagger readied, fireball to each hand, cast main | pod only | – | 11 G | – |
| | cast and hold bound dagger | – | – | 2933, 2392 R: no glowing blade by day | – |
| | cast off hand | – | – | 4087 U | – |
| freecam | free camera over Greenspring | – | – | R: plants and litter, no houses | – |

## The game on the pod

The composed site already carries the game (`site/game`), and measure.mjs
takes `--base`, but the game has no ready gate the capture reads
(`__STUDIO_WARM__` is the studio's), no observe hook (`journeyState` and
`grantKit` live on the studio's debug hook) and no studio-style query
spawn. A capture needs a game-side warm flag and an observe-only state
read on the game's dev seam (`apps/game/src/gameSeam.ts`). Until then the
headless `apps/game/src/journey.test.tsx` is the game's proof.
