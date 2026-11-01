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

## Rerun (pad112j, 1080p): pad-panes PASS, 21 of 21 steps in 225.5 s
`out/runs/pad-panes/20261101T011645/`. Start opens Wind UI's windows, the left stick moves the cursor, A clicks, X
right-clicks, the triggers and right stick turn the wheel, the bumpers cycle stats, inventory, magic, our journal, our
map and System (last), B closes, Select waits; the same panes by keyboard (Tab, J, Esc). Touch stays owed (stream client).
Fixes behind it:
- **Tween swap** (padcursor.cpp TweenSink, rule `pad::tween_to_windows`): Wind UI does not take TweenMenu early in a
  session, so a frame after it opens untaken it is hidden and InventoryMenu shown (log "pad: tween -> Wind UI's windows").
  This covers Tab, Start and the HUD's Menu button.
- **Close by Esc, not Tab:** Tab left the windows open (pad112f).
- **Close guard** (`pad::close_allowed`, 0.5 s): the Start that opened the windows cannot close them.
- **No nav.ts change needed:** B leaves our journal back to the windows, and the bumpers carry on to the map.

## Open
- In a focused PrismaUI view the cursor yields; LB/RB there are nav.ts's, so cycling on from journal to map is the
  views' (nav.ts) job.

## Changes to the brief's input map
- Select (Back): Journal -> Wait (owner ruling); Wait keeps d-pad down too. Journal and System become panes.
- D-pad in Wind UI's windows: cursor nudges (24 px at 1080p), as "d-pad or left stick within a pane".
- Triggers: LT wheel up, RT wheel down in every Wind UI pane (zoom on a map, scroll elsewhere).
- Start in the windows closes them like B (owner: "B or Start closes").

## Panes unobstructed (pad112n, 1080p): pad-panes PASS, stills read
`out/runs/pad-panes/20261101T032035/`: 07 our journal alone; 09 our chart alone; 11 (pad) and 20 (Esc from play)
Skyrim's Journal Menu with no Wind UI window over it. It opens on its Quests tab, not System.
- Our journal, map and System open only once Wind UI's windows are closed. The windows close through the UI queue
  (kHide WindUIMenu): Esc also opened the System page (pad112m), and Tab left them open (pad112f). The windows come
  back half a second after the pane closes.
- A pane counts as open by the view host's modal record, not by PrismaUI focus: an unfocused journal had read as
  closed (pad112k/l).
- When the Journal Menu opens with Wind UI's windows up, the windows are hidden the next frame. This covers Esc from play.

## System page (pad112q): pad-panes PASS
`out/runs/pad-panes/20261101T034625/` 11 (pad) and 20 (Esc): the Journal Menu shows its System tab with the list Save,
Load, Creations, Settings, MOD CONFIGURATION, Controls, Help. 0.4 s after the menu opens, padcursor calls the movie's
`RestoreSavedSettings(2, false)` and then `SwitchPageToFront(2, true)`; the log reads the tab back ("tab 0 -> 2").
SwitchPageToFront alone left Quests showing (pad112o). Left for the UI text lane: "MOD CONFIGURATION" is SkyUI's
upper-case label, and the bottom bar still shows the Quests tab's "A Toggle Active / X Show on Map".
