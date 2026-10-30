# Lane game-16 (2026-10-30): the strike, rest and close actions; respawn goes home; reds narrowed

Machine: argonia-play, the g4dn. Six deploys from a clean worktree at origin/main, the last at 18ed1e4 plus this
lane's commits. Batches g16-r1 to r5, and pad17 (#17) run live. The machine was stopped at the end, with no lane queued.

## Fixed and proven
- **rest-respawn passes, 3 runs.** ArgoniaCore.log said `1000088C has no editor location`.
  `MoveToEditorLocation` refuses an actor the engine has never moved, because it has no starting-position extra.
  The roster now keeps each actor's placement from the data (kDataLoaded). A failed MoveToEditorLocation falls back
  to `SetPosition` in the same worldspace or cell. `MoveTo_Impl` is private in CommonLib. The roster was
  **2930 actors**: every vanilla and dependency actor with the Respawn flag was reset on each rest. It is now our
  plugins' actors only (0012). Code is in skse/ArgoniaCore/src/life.cpp and core.h.
- **fight-damage-builds passes, god-blow included.** The first god-blow read 1961.31 = 2000 - 8.94 - 29.75:
  `setav health` keeps the last blow's damage. The journey now runs `restoreav` after it, and nothing was retuned.
- **New runner actions** in tools/run_journey.py:
  - `_aim`: yaw and pitch to the target's measured GetPos, then a 40 ms W so the camera picks the new angle up.
  - `rest: <marker>`: E up to 3 times until ArgoniaCore logs the rest or why it refused. It now fails clearly,
    e.g. "You cannot rest with enemies nearby".
  - `close_menu: <menu>`: tries the chart's view.close, then pad B, ESC and TAB on the engine and os routes. Pad B
    closes our journal live; ESC and TAB do not.
- **First-place ask-signs passes.** Livia's dialogue was still open; the step now says goodbye first.
- **The R3 lock-on (#17) passes:** `tdm-target` read `locked: true` after RS was pressed with the deserter faced.
- **Bridge:** the `frametime` wait is capped at 100 s, so it gives a reason instead of NoReply.
- **world-sample:** relaunches per stop and before the run. tools/world_sample.py and its tests are updated.

## Still red: findings (the step, what the game does, game or check)
- quest-board strike: Livia is never under the crosshair. A still from r2 showed her already dead before the blows,
  because `damageav 1000` then `setav 5` killed her. `forceav 5` is the current version, and it still failed in r4.
  The check is at fault; this needs a still.
- grow-at-rest: ten-blows and the rest now pass. The game then crashed at pending-level (r5, `dev-grow`). Probably
  a game crash; not diagnosed.
- die-and-recover: the rest passes, then earn finds GetVastei 0 after the blows. The cause is likely that the hits
  do not land on the deserter after it is re-enabled, so the check is at fault; this needs a still.
- lf83-components stage-20: the code sends ArgoniaJournalNotice (logged "journal notice 10", with no
  missing-source warning), now on the main thread. The bridge's mod ring holds SKI events but never ours. This is
  a **code** fault in ArgoniaCore's event source against the bridge's sink. Grep ~/.argonia/commonlib for
  GetModCallbackEventSource.
- first-place terms-with-signs: the stage stays at 30. Signs' one-charge needs both objections answered (the yearly
  mending found), and the journey skips that. The **check** is at fault: take lf83-components' why-failing steps.
- ui-sweep map-closed: neither view.close {chart}, pad B, ESC nor TAB closes the map (no MapMenu close event, or
  the chart stays open). Our chart owns the input. **Code**: the chart needs a close binding.
- ui-probe frames-open: 0 frames arrive while a menu is open, because the game pauses. The **check** is at fault.
- menus-quit quit-confirmed: no `ArgoniaSuspend written (quit)` line. Not diagnosed.
- suspend-save in-combat-drop: after one blow on the crocodile, the player is not in combat. The check is at fault.
- smoke: crashes on the cow to Tamriel, even after a relaunch. world-sample crashes at the first cell change or quit
  after stop 1's `teleport pos` probes, 3 times. That is the game (diag3), and the trigger is raw SetPosition.
  Next: probe by moveto to a placed marker.
- #17: B closes the journal, but TKDR_DodgeStart still fires (5f7e595 is deployed, so this is a regression for the
  fix lane). D-up gave no FavoritesMenu, and whether the favourite took is unproven.

## Not reached
The vastei pile still, the xLODGen still and installer line, `stack.py verify` (tk-dodge.toml), and the PROGRESS
and Outcomes `[from batch]` lines.
