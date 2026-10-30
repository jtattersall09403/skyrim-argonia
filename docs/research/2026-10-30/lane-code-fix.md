# lane-code-fix: chart close, B-close dodge, journal notice event, actor-endpoint guards

Build-VM lane. Its inputs were lane-game-16.md ("Still red" and #17) and lane-mobile-17.md. Every CommonLib call
below was checked against ~/.argonia/commonlib: `BSTEventSource::PrependEventSink`, `ButtonEvent::GetRuntimeData().heldDownSecs`,
`ControlMap::GetUserEventName(id, device, kGameplay)`, `UserEvents::{cancel,tweenMenu,journal,quickMap}`,
`UI::IsMenuOpen`, `UIMessageQueue::AddMessage(.., kHide, ..)`, `TESObjectREFR::IsDisabled/Is3DLoaded`,
`TESObjectCELL::IsAttached` and `Actor::GetActorRuntimeData().currentProcess`.

## 1. Nothing closes the chart (ui-sweep map-closed)
- **Evidence.** The ui-sweep log (out/batch/adhoc/20261030T215418/03-ui-sweep-1-*) shows the chart pushed at 21:59:56. Then `view.close`
  closed our view: at 22:00:04 the HUD shows again. MapMenu, though, never sent a close event. The router's kHide, sent
  while MapMenu was opening, does not take, so the engine map stayed open under our closed chart. The chart already had a
  back action (B, Esc in the page) and a touch Close button (render.ts:19).
- **Fix** (skse/ArgoniaCore/src/views.cpp):
  - `CloseView("chart")` queues kHide to MapMenu when it is open.
  - A MapMenu close event closes our chart.
  - New `CloseByControl` in the input sink: while the journal or chart is open, a press closes it if it is Cancel
    (menu context), or if its gameplay event is Tween Menu (Tab), Journal (Esc, pad Back, J) or, for the chart only,
    Quick Map (M again). The press goes through `ViewIntent(view.close)`.
  - nav.ts maps Tab to back inside the page.
- **Next slot must prove:** in ui-sweep, M opens the map, then each of B, Esc, Tab, M and a touch Close tap closes it
  and gives a `MapMenu opening:false` event. The log line is `views: chart closed; MapMenu hidden`. After that, LY moves
  the player.

## 2. The B that closes the journal still rolls (TKDR_DodgeStart)
- **Mechanism.** TK_Dodge_RE.dll has its own `InputEventHandler`, a `BSTEventSink<InputEvent*>` (the DLL's strings
  include `Register input event...` and `src\InputEvents.h`). With `EnableSprintKeyDodge`, it rolls on a sprint-key
  release whose held time is under `SprintingPressDuration`, and it reads the key by code. 5f7e595 only blanked the
  user event. TK Dodge registers at input-loaded, before our data-loaded sink, so it reads the release first, and it
  does not read the user event anyway. Its use of the key code is inferred from the strings and ini, not from source.
- **Fix:** our input sink is now prepended (`PrependEventSink`), so it runs before TK Dodge. On the release of a
  press that began in a view, it now also sets `heldDownSecs` to 3600, so the release reads as a hold-to-run and not
  a tap. Presses that begin outside a view are never touched, so B outside a view still rolls.
- **Next slot must prove:** in pad #17, Back opens the journal and B closes it, with no TKDR_DodgeStart within 2 s.
  Then B while moving gives TKDR_DodgeStart, and a touch B tap gives the same two results. If it still rolls, the
  fallback is to defer the view's Unfocus until that button is released, so the game stays paused through the
  release.

## 3. ArgoniaJournalNotice never reaches the bridge (lf83-components stage-20)
- **Cause** (the code, not the sink). talk-takes and hear-station passed their notice expectation in the same run
  (out/batch/adhoc/20261030T211907/04-*), so the source and the sink both work. In the log, `journal notice 10: ... clue 11`
  came at 26:00.042, then `entry 20 merged into the last` at 26:00.220. The merged notice returned early and sent no
  mod event, and clue 11's event had fallen in the previous step.
- **Fix:** `JournalNoticeNow` sends the mod event for every journal change. Only the HUD notice still merges. The
  event is sent outside the core lock.
- **Next slot must prove:** lf83-components passes stage-20 and the rest of its notice expectations.

## 4. Crash in dev-grow on a disabled actor (diag4-crashes.md)
- `actor_unready()` (ArgoniaBridge ep_world.cpp) refuses an actor that is disabled, has no 3D, is not in an attached
  cell, or has no AI process. dev-grow and every `actor_arg` endpoint (av and the others) now return that reason as an
  error instead of crashing.
- life.cpp `ResetActors` skips disabled actors, with a log line.
- **Next slot must prove:** grow-at-rest's dev-grow either answers or errors with "is disabled", and does not crash.

## Gate and build
See the commit and the build job `code-fix` for results.
