# Lane 1.12-pad (1.12 §8: every menu on the pad)

Job `pad112e` on argonia-play-ie (deploy + checks in one job, `tests/journeys/batches/pad-1.12.sh`), 2026-11-01.
Stills and logs in `out/pad112/{p1080,folded,unfolded}/` and `out/runs/pad-panes/` (not committed).

## Route
- Data/dependency check: nothing in our stack gives Wind UI a pad cursor; Wind UI has no pad support (windui.md).
  Gamepad-to-mouse tools (Steam Input, ControllerBuddy) act at the OS, which Wind UI ignores (OS SetCursorPos did
  not move it). So route 5: our SKSE (`skse/ArgoniaCore/src/padcursor.cpp`), rules in `skse/core` (`pad.h`).
- How Wind UI reads the cursor (measured with `bridge.py input mouse`): writing `RE::MenuCursor` cursorPosX/Y moves the
  drawn cursor (p1080/02, 03); a MouseMoveEvent alone does not (move-event.json: before = after). Clicks are engine
  mouse ButtonEvents (pad-log: "left down/up" at the anchor, still 08-a). The pad cursor does both.

## Results (L4)
| Check | 1080p | V5 folded (2560x1142) | V5 unfolded (2240x2068) |
|---|---|---|---|
| Left stick moves the cursor | MenuCursor 800 -> 99.5 y (cursor-pad.json) | yes (log) | yes (log) |
| Bumpers cycle panes (stats, inventory, magic; anchors scale) | log, 05-07 | magic at 1971,377 | magic at 1725,682 |
| A clicks / releases | log 08-a | log | log |
| B closes to play | 10-b.png, "windows closed" | log | log |
| Select opens wait | 13-select.png ("Wait how long?") | yes | yes |
| Start opens Wind UI's windows | **FAIL**: Start (and engine Tab) open Skyrim's themed TweenMenu; Wind UI's windows appeared only later (04) | same | same |
| pad-panes journey | FAIL at step 1 (same cause) | same | same |
Not proven: X right-click, triggers/right-stick wheel, journal/map/System panes (journey stops at step 1).

## Open
- Start -> Wind UI: with vanilla.txt removed (Test-Path False) the tween is still Skyrim's on open. Needs the
  Wind UI-takeover owner (1.12 §1) to say what opens its menu mode; then pad-panes re-runs.
- In a focused PrismaUI view the cursor yields; LB/RB there are nav.ts's, so cycling on from journal to map is the
  views' (nav.ts) job.

## Changes to the brief's input map
- Select (Back): Journal -> Wait (owner ruling); Wait keeps d-pad down too. Journal and System become panes.
- D-pad in Wind UI's windows: cursor nudges (24 px at 1080p), as "d-pad or left stick within a pane".
- Triggers: LT wheel up, RT wheel down in every Wind UI pane (zoom on a map, scroll elsewhere).
- Start in the windows closes them like B (owner: "B or Start closes").
