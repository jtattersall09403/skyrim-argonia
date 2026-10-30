# Lane input (2026-10-30): the bridge's input path rebuilt at source

Input finding: [lane-game-14](lane-game-14.md) (no key or pad input reaches the game after a save load).

## What changed
- **Engine route, now the default for `input key`** (skse/ArgoniaBridge/src/ep_input.cpp `engine_event`): each key is a
  `RE::ButtonEvent::Create(kKeyboard, <user event>, scan, value, held)` sent on the main thread (SKSE task) through
  `RE::BSInputDeviceManager::SendEvent`, so every input sink (MenuControls, PlayerControls) gets it with no window,
  focus, WndProc or DirectInput acquire on the path. The user event is `ControlMap::GetUserEventName` in the top
  input context (gameplay as fallback). A press is a down (held 0), a held event every 16 ms and an up
  (protocol/input.cpp `press_ticks`). API checked against the pinned CommonLibSSE-NG v15.2.0 headers. Refused
  during a load. `input key <chord> <ms> os` keeps SendInput.
- **Focus check** compares the foreground HWND with `RE::Main::wnd` (fallback `FindWindowW("Skyrim Special Edition")`);
  `classify` names game / game_other_window (game-14's case, which the pid check passed) / other_process / none.
- **Before os input and before every pad sequence** (`focus` command; tools/bridge.py `pad()` calls it first):
  AttachThreadInput + BringWindowToTop + SetForegroundWindow + SetFocus, then an ALT tap and again; re-checked;
  on failure the error carries the foreground window's hwnd, pid, title and class.
- **SendInput** count and GetLastError are returned (`down`, `up`); fewer injected than sent is an error.
- **`input-diag`**: focus report, game window title and class, the module owning the main window's WndProc
  (`prisma_wndproc` true if PrismaUI subclassed it last), `prisma_loaded`, `loading`, the last SendInput result.
- L2: tests/test_input.cpp (calls, routes, schedule, focus classes, JSON) in bridge.protocol; `make check` green.

## Unproven until the first g6 game slot (L4)
- The engine route's effect in game: whether held W moves the player (movement may read the device state, not
  only events) and F toggles the POV. Not compiled-and-run yet beyond the windows-dev build below.

## The first g6 game slot must deploy and prove
1. Deploy the windows-dev ArgoniaBridge.dll from this commit; PrismaUI.dll restored (not `.off`).
2. Launch, `load argoniabase`, `bat claywater`, then `input-diag` (record wndproc_module, focus).
3. Load-then-input: `input key F 300` (engine) -> IsPC1stPerson 0; `input key W 800` -> position changes; then the
   same with `os` and a `pad LY=1:800`. A pass needs the change measured, not the reply.
4. PrismaUI A/B: rename PrismaUI.dll to .off, relaunch, repeat 2-3; restore it. If os/pad die only with PrismaUI and
   engine works in both, PrismaUI's WndProc/input handler is the cause: fix there (unfocus views after load) and
   keep engine as the default.
