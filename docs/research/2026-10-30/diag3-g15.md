# diag3: game-15 batch g15-batch (20261030T181841)

## CLUSTER 1 - TALK (dialogue-intercept, quest-board, first-place, lf83-components, lf83-endings): regression, the os key route
- Regression proof: batch 20261030T151243 (engine route default, a9a50dd) PASSED lf83-endings f41-stage-10 (same
  `talk:` on Takes); this batch (os default, dce1c48: ep_input.cpp:1-6, protocol/input.h) fails it, with no
  OpenDialogue/Dialogue Menu in any core log. The `talk:` action (run_journey.py:319-339) is unchanged in logic: its
  crosshair gate passed in 4 of 5 (bridge crosshair ref = the NPC; the still shows the "E Talk <name>" prompt), then
  `input key E 120` went by the os route (SendInput scan code after bring_to_front, ep_input.cpp:76-93,152-169) and
  the game never activated. dce1c48 measured os only for movement/camera, never for activation.
- The 5th (first-place) failed the gate itself ("last: nothing"): camera/aim, see claywater-look below.
- Fix (one): run_journey.py:339 send activation by the engine route, `self.b.call("input", "key", "E", 120, "engine")`
  (engine ButtonEvents "open menus", dce1c48's own measurement; Activate is a ButtonEvent the same way); keep os for
  movement/camera. Also record each action's reply in report.json `calls` (now always [] - the input reply with
  route, sent counts and focus was thrown away, which is why this needed inference).
- Re-prove: `run_journey.py lf83-endings` (passed on engine before) then dialogue-intercept; speaker id within 2 s.
- If engine E also fails: run `input-diag` around E once - it names the foreground window and the last SendInput.

## CLUSTER 2 - NO HIT (fight-damage-builds novice-blow, grow-at-rest ten-blows, w3-crime strike): the swing never happens
- Not the damage code: reader on 07/04-arm.png and 05-novice-blow.png - weapon never drawn, no NPC in frame, idle,
  and a "Controller Disconnected" toast. `arm`'s RB (draw) already did nothing; its expectation (VoicePoints unchanged)
  cannot see that.
- Mechanism: bridge.pad (tools/bridge.py:386-395) calls `focus` (may ALT-tap, ep_input.cpp:81) then pad.ps1
  Connects a new ViGEm pad, waits $Settle, plays, Disconnects (pad.ps1:14-15,58). Each call is a fresh hot-plug; the
  toast shows the game saw the unplug. The RB press at the start of a 120 ms sequence is lost when the game has not
  yet switched to the new pad (it was last driven by os keyboard events in these journeys). RS/LY in other journeys
  pass because they are longer or held.
- Fix: (1) pad.ps1 - keep one pad connected for the session (connect once, never Disconnect between calls), or
  raise $Settle and prefix sequences with a 200 ms neutral `wait`; (2) fight-damage-builds / grow-at-rest / w3-crime
  draw steps expect `player.IsWeaponOut >> 1` and `GetDistance` <= 150 to the target, so a dead setup fails at the
  draw, not at the hit.
- Re-prove: `run_journey.py fight-damage-builds`; arm shows IsWeaponOut 1, novice-blow sees a hit event.

## Singles (details below): claywater-look (camera does not follow console setangle; E aims at nothing),
## smoke (engine crash in `cow tamriel 2 -4`, repeat; relaunch before worldspace-changing scenes),
## w3-crime (cluster 2).

---

## claywater-look `station-house-inside` (repeat of diag2-crash-misc; 2ab2798's stand-off did not take)
- Evidence: claywater-walk runs the *identical* steps (claywater-walk.yaml:29-32) and PASSES in the same batch.
  The only difference is history: walk drives the player with `pad` first (walk.yaml:13); look reaches the door by
  console moveto/setangle only (look.yaml:16-35). Reader on 11-station-house-inside.png: outside, camera looks
  sideways past a post to the sea, no door ahead, no activate prompt, no menu.
- Cause (check, not game): with no player input since load, the third-person camera does not follow a console
  `setangle z` (it keeps its own orbit yaw); the crosshair ray goes sideways, finds nothing, E does nothing.
- Fix: tests/journeys/claywater-look.yaml:34 - after setangle add a camera reset before E, e.g. `{pad: "LY=1:100"}`
  (one tiny forward nudge, as walk's history gives) or switch to first person for the step; and gate E on the
  crosshair showing the door (as `talk:` does, run_journey.py:331-338), so a missed aim fails as aim, not as entry.
- Re-prove: `run_journey.py claywater-look` alone, step station-house-inside; GetInWorldspace >> 0.

## dialogue-intercept `speak-livia` (new)
- Evidence: `talk:` crosshair gate passed (no StepFailed from run_journey.py:336), so the bridge's crosshair ref was
  Livia and E was sent. Reader on 02-speak-livia.png: prompt "E Talk / Livia Varinius" live, no dialogue window,
  camera looking away over the water with Livia hidden behind the player. Core log: no OpenDialogue, no router
  entry for Dialogue Menu, no input line (bridge log has none).
- Cause (most likely, same family as above): E is the first OS key of the run; in this journey nothing but console
  precedes it (dialogue-intercept.yaml:13-17). The prompt shows, so activation would have fired had the key
  reached the game: the os SendInput (ep_input.cpp:112, default route since dce1c48) E was not taken by the game
  (focus/first-input after the ALT-tap foreground dance, ep_input.cpp:68-100). Walk's E works after pad input.
  Not ruled out: the perk hook.dialogue-intercept swallowing activation without opening our view (would log).
- Fix: run_journey.py:339 - check the input reply (route, injected count, foreground) and log it into the step;
  then retry E once if no menu/ViewState within 1 s. Diagnose first with the bridge `input-diag` before and after E.
- Re-prove: `run_journey.py dialogue-intercept`, with `input-diag` called around E; speaker id within 2 s.

## fight-damage-builds `novice-blow` (new): 0 hit events
- Evidence: steps find..arm pass (arm only checks VoicePoints). Reader on 04-arm.png and 05-novice-blow.png: weapon
  NOT drawn, no NPC in frame, idle pose, and a **"Controller Disconnected"** toast on 04-arm. So `pad: RB` (the
  virtual gamepad) reached nothing: no draw, no swing. Also no deserter in view after `player.moveto {opp} 0 -110 0`
  plus `setangle z 0` (same third-person camera/aim issue as claywater-look, or {opp} = actors listed.0 is not the
  deserter).
- Cause (harness/bridge, not our combat code): the virtual pad is disconnected in this session, so every `pad:`
  step is a no-op; arm's expectation cannot see it (it checks a value that is unchanged either way).
- Fix: (1) run_journey.py pad action - fail the step when the bridge reports the pad absent (read the pad status
  first) instead of silently sending; reconnect the virtual pad at journey start. (2) fight-damage-builds.yaml arm
  step: expect the weapon drawn (`player.IsWeaponOut >> 1`) and the opp within 150 units (GetDistance), so a dead
  setup fails at arm. (3) move the player to the opp inside novice-blow, right before RB.
- Re-prove: `run_journey.py fight-damage-builds` alone; arm shows IsWeaponOut 1, novice-blow sees 1 hit.
- Note: if the pad is down, claywater-look's suggested `{pad}` nudge will not help; use the bridge `input key W 100`.

## smoke: CRASH at scene apply (repeat of diag2-crash-misc #1; its settle fix took, the crash did not go)
- crash-head.log: execute at 0x01E000000000, RBP "cow tamriel 2 -4" (tests/scenes/plain-armed.txt last line), R12
  ConsoleLogPrinter, BSMultiBoundAABB, JobThread; uptime 6:12; same signature as game-6 and diag-croc-move-crash #3.
  run_journey.py:219 now waits for a settled load, so the "load tail" theory is disproved: the crash is the engine's
  cross-worldspace `cow` in a process that has already changed cells many times. Game, not our DLL.
- Fix: tools/run_batch.py - relaunch the game before any journey whose scene changes worldspace (`cow` line), or
  mark smoke `crash_risk: high` so the batch gives it a fresh process; long term, base the save in the scene's own
  worldspace so the scene uses moveto, not cow.
- Re-prove: smoke 3 times in one batch after other journeys; 0 crashes.

## quest-board `talk-takes` and first-place `talk-to-takes` (same class as speak-livia / station-house-inside)
- quest-board: talk gate passed, E sent, KnowsTopic false, no OpenDialogue/Dialogue Menu in the core log = speak-livia.
- first-place: `player.moveto Takes 0 -120 0`, setangle z 0 and x 0, then the talk gate saw "nothing" for 5 s: the
  crosshair ray does not follow the console heading (claywater-look's camera class), so even the NPC moved in front
  by run_journey.py:325-328 is not under it.
- Fix (one for all four): in run_journey.py, before any E (`talk:` at :339 and `key: E`), re-sync the camera to the
  player heading - a short bridge `input key W 80` or the bridge's camera reset - and then gate on the crosshair; then
  log the input reply and retry E once if no menu opens in 1 s (see speak-livia).
- Re-prove: dialogue-intercept, quest-board, first-place, claywater-look in one batch.

## w3-crime `strike`: crime-gold violent 0 (same class as fight-damage-builds novice-blow)
- `pad: RB` swing, no hit; core log has no hit. As in novice-blow, the swing hit nothing (aim/camera or pad) - fix
  with novice-blow's: assert IsWeaponOut and GetDistance in the draw step, and gate RB on the crosshair showing the
  target. Re-prove: w3-crime alone; a hit event and violent > 0.

## grow-at-rest `ten-blows` (0 hits), lf83-components `talk-takes` (speaker None), lf83-endings `f41-stage-10` (stage 0)
- Same two classes: grow-at-rest = the swing class (w3-crime / novice-blow); lf83-components and lf83-endings = the
  talk class (talk gate then no OpenDialogue in the core log; endings never reaches stage 10 because Takes' greeting
  never ran). One fix each, as above; no separate cause.

## ui-sweep `map-closed`: TAB did not close MapMenu (0 menu events)
- Opens and closes of Tween, Inventory, Magic and the map open all passed on the os route; only TAB inside the
  MapMenu was lost (earlier batch: M inside the map was lost too, ui-sweep.yaml:41). The map consumes keyboard
  input in its own context, and the key arrived by os SendInput 1.5 s after the open, not held long enough to read.
- Most likely the same route question as cluster 1. Fix: ui-sweep.yaml:42 send `key: "TAB 120 engine"` (engine
  ButtonEvents go to MenuControls, which handles Cancel) - or hold 250 ms. Re-prove: ui-sweep alone, map-closed.

## ui-probe `talk-livia`: speaker None - cluster 1 (TALK); same fix, no separate cause.

## world-sample: CRASH after s01-probe-west-30m (repeat; game)
- crash-head.log: SkyrimSE.exe+100F207 `call [rax+0x10]`, rax 0 (null vtable), uptime 5:11 - the exact signature of
  diag2-crash-misc #1 (09, render/update path), and world-sample crashed in batch 151243 too (diag-croc-move-crash #3).
  It falls on the travel to stop 2 (the next step after stop 1's probes). Engine cell-change crash, not our DLL.
- Fix: same as smoke - a fresh process before each cross-cell travel stop (split world-sample per stop with a
  relaunch, or `crash_risk: high` so run_batch relaunches). Re-prove: world-sample 3 times, 0 crashes.

## die-and-recover `rest`: WakePoint '' - cluster 1 (activation by os E: camp activate never fired, as the NPC talks).
## menus-quit `journal-closed`: our journal still "ready open" after ESC 80 by os route
- J opened it (journal-stays passed), so os keys reach the game; ESC did not close our view. Our HTML view holds
  input while open (PrismaUI focus), and an 80 ms os ESC is not read by the close path, which listens on the
  game's input events. Same route class as ui-sweep map-closed: menu-context keys on the os route are lost.
- Fix: send menu-closing keys by the engine route (`key: "ESC 120 engine"`, menus-quit.yaml:23; TAB in ui-sweep), or
  make the bridge's default per key: os for movement/look, engine for E/ESC/TAB/menu keys (ep_input.cpp:140 route
  pick, protocol/input.h). Re-prove: menus-quit alone, journal-closed.

## suspend-save `stream-drop`: the check's text, not the game
- Core log 19:01:05 "saves: ArgoniaSuspend written (stream drop)": the save WAS written. The log prints
  to_string(why) = "stream drop" (skse/core/src/life.cpp:285, via ArgoniaCore/src/life.cpp:188); the journey wants
  "(stream_drop)" (tests/journeys/suspend-save.yaml:29).
- Fix: suspend-save.yaml:29 contains "saves: ArgoniaSuspend written (stream drop)". Re-prove: suspend-save alone.
