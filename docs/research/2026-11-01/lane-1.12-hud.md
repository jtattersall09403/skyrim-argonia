# Lane 1.12-hud: owner look 1 (the bars, vastei, the layout, the minimap)

Brief: `docs/research/2026-11-01/briefs/1.12-hud.md`. Journey `tests/journeys/hud-look.yaml`, batch
`tests/journeys/batches/lane-1.12-hud.sh` (scene `claywater`, play camera).

## Root causes (why 1.12 passed while the owner saw it broken)
- **Bars jerky and flashing.** ArgoniaCore pushes `hud.bars` 5 times a second; `main.ts` replaced the bars' innerHTML
  on every push, so the CSS width transitions never ran (each push made new elements at their final width: a 5 Hz
  staircase), and the `.regen` glint animation restarted on every push (the flashing). 1.12 judged the HUD from
  off-game stills and state reads, which cannot show motion.
- **Fat, childish bars.** 0.8-1.05 rem troughs with bright gradients and a glossy lip; never compared at the play
  camera with `tmp/image.png`.
- **Covering the top-left text.** Our column (bars, vastei, notices) sat top left at 3.5vh, where the engine's own
  notices print.
- **Minimap.** Built as a rotating round disc with a rose, 10 rem, at the 1.12 ruling; the owner changed the ruling
  (square, north up, only the marker turns). The heading was the body's AngleZ, not the camera's.
- **Smoothing on a timer failed in game (found here).** A first fix eased the bars with requestAnimationFrame, then a
  16 ms timer: the unfocused PrismaUI view gets no animation frames and its timers are throttled to ~1/s
  (run 20261101T142258: magicka moved in ~1.25 s plateaus). The final fix uses CSS transitions on persistent elements
  (compositor-driven): fill `width 0.24s linear` (just over the push gap), trail held 0.55 s after a loss then 0.7 s.

## What changed
- `ui/views/hud/main.ts`, `render.ts`: bars persist and update in place; `motion()` picks each part's transition;
  no regen class; slim 0.3/0.36 rem troughs, dark fills, dark bezel with the frame's gold-green hairline (CSS only:
  no Fal art was needed, so nothing new in the sourcing register).
- Vastei: `shimmer(gained, carried)` 0.15..1 from the share of the purse won and the gain's size; drives one light
  sweep, plate glow, mark and count brightening (`--glow`). No "+N".
- Layout: the column moved bottom left (our notices above the bars); top left is empty for the engine.
- Minimap: square `min(7.5rem,17vh)` top right, north up (`discTransform` rot 0), an N tab; lane 1.12-chart's
  `player-marker.svg` inlined as `hud/me.ts` (a test holds it to the file); the arrow turns by `turnTo` (shorter way)
  with a 0.22 s transition; ArgoniaCore's minimap push now carries `PlayerCamera` RuntimeData2 `yaw` and pushes at 1°.

## Rows
| Row | Status | Evidence |
|---|---|---|
| vastei shimmer | passed | run 20261101T132445 vastei-small-00..02 faint, vastei-large-00..16 strong, no +N (reader) |
| nothing over the top-left notices | passed | 20261101T132445 01/02/09: top left empty (reader); no engine line was on screen to test against |
| minimap | passed | 20261101T132445 03/04: square, north up, map identical, only the arrow turned (reader) |
| the bars | see the ledger | run 1: frozen (rAF); run 2: 1/s plateaus (timers throttled); run 3: CSS transitions |

## Left / notes
- The minimap draws the chart's `../chart/assets/*-2048.png` layers; if lane 1.12-chart changes the tile layout or
  the revealed-area model, the minimap must follow (it imports `revealRects` from `chart/geom.ts`).
- The three rolls drained no visible stamina in runs 1-2; the `drain-direct` step (damageav) is the control.
- Grab bursts at 8 fps sometimes show a PowerShell window over frames (magicka-16..18, run 1).
