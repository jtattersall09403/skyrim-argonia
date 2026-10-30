# Lane game-14 (2026-10-30): every red blocked by dead game input

## Verdicts
- g13-reds2 (25 items) and g14-reds (20 items, crash items and grow-at-rest once each): **all failed at scene, "the camera stays in first person"** (run_journey.py third_person). No journey reached its steps, so no check was rewritten and no verdict of passed, fixed check or game finding is possible yet. None closes a PROGRESS row or Outcomes L4 line; none edited.
- Not done (machine handed to g6-cut, which took the lock when g14-reds ended and stopped argonia-play): interactive fixes, grow-at-rest, vastei pile still and pickup, respawn flag reads, LOD restore and still, rest-respawn. ui-probe frame times dropped (planner: the g6 measures them).

## Finding: no keyboard or pad input reaches the game (measured live)
- After a save load, `input key F|W|J|I` and the ViGEm pad (`LY=1:1500`, `RS`) change nothing: IsPC1stPerson stays 1.00, the position is unchanged to the unit, no menu event. GetPlayerControlsDisabled lists every control Enabled; game time and frames advance (60 fps); no menu open in the event stream; no modal view (ViewState).
- The bridge's focus check passed throughout, but it compares process ids only (ep_input.cpp game_has_focus); the foreground HWND was twice not the main window (3015804, 3408944 vs main 328054).
- Input came back twice, each time right after a window activation cycle (closing Crash Logger's 4 Notepad windows at 16:41; opening and closing a Notepad, 16:5x): F switched to third person. It died again at the next save load, and the same cycle after a later load did not revive it. Not reproducible: cause unproven.
- Candidates, unproven: PrismaUI's WndProc subclass and InputHandler (PrismaUI.log "WndProc subclass installed" on the main HWND at launch; it arrived with ui-live, and the game-13 run on the earlier deploy walked on the pad); a load leaving DirectInput unacquired. The A/B (launch without PrismaUI.dll) was cut off when the machine was stopped.
- **The machine still has PrismaUI.dll renamed PrismaUI.dll.off** (Data\SKSE\Plugins); reported to the planner to undo on or before the g6 image.

## Fixed
- bridge.ps1 `kill` also closes Notepad: Crash Logger opens every crash log in it, and those windows took focus from the next launch (4 were open, the oldest from 13:50). Installed on the machine.

## Next (first thing on the g6)
1. Undo the PrismaUI rename if g6-cut has not.
2. The A/B: launch, load argoniabase, `bat claywater`, input key F and W; then the same without PrismaUI.dll. If PrismaUI is the cause, Unfocus every view after load or fix its input handler at source.
3. game_has_focus: compare against the main window, not the pid; check SendInput's return value.
4. Then the reds batch, the interactive fixes, and the slot items above.
