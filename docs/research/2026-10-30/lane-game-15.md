# Lane game-15 (2026-10-30): input after a load proved; talk and strike rebuilt; reds re-run

Machine: argonia-play stayed the g4dn (no g6 capacity; g6-migrate restored PrismaUI). One deploy from a clean
worktree at origin/main (1c3f9b4: input route, rest-respawn, respawn-until-cleared): DEPLOY OK in 460 s, both DLLs
compiled first time. Then bridge-only redeploys (~140 s each). `stack.py verify`: 1 bad, `tk-dodge.toml` (another
lane's tuning; not touched).

## Input proof (L4, measured live after `load argoniabase`, `bat claywater`)
- **Focus check was wrong at source:** `RE::Main::wnd` read a code address (0x7FF6...), so every focus check said
  `game_other_window` and refused os and pad input. Fixed: the game window found by class and pid (7d52a63).
- **After that fix:** os `W` 2.5 s moves ~900-950 units, each time; pad `LY=1` moves; with and without PrismaUI
  (A/B done: PrismaUI is not the cause). Engine-route `W` moves ~30 units, and engine `F` does nothing.
- **Engine route does activation and menus:** engine `E` opens our dialogue, `R` draws the weapon, `J` opens the
  journal, and `MOUSE1` attacks (a hit lands). os `E`, `ESC` and `TAB` were lost.
- **Default route per key** (460541a): os for W A S D F SPACE LALT LSHIFT LCTRL C; engine for everything else.
  `MOUSE1`/`MOUSE2` are engine-only mouse ButtonEvents (e2ac75a). L2 tests are in test_input.cpp; ctest 33/33.
- **The first E after a scene's setup is lost:** a second E, 3.5 s later, opens the dialogue. `talk:` and
  `key: E` now pitch the camera 15 degrees down, step 80 ms, and press E up to 3 times until a menu opens or the
  cell changes (d025c7f, e2ac75a).
- **`strike: <ref>`** (e2ac75a): the ref faced at 80 units, then `R` if IsWeaponOut reads 0, then `MOUSE1`. Live,
  one strike on Livia gave a hit event and violent crime gold 40. `sae` attack and draw events were refused by the
  player's graph ("not processed"). The virtual pad was dead after mobile17b (X, RB and RT did nothing).

## Journey verdicts (batches g15-batch, g15-reds 1-3 and live runs)
- Passed: attributes, claywater-walk, combat-trial-a, fight-archetype, livia-sleep, croc-den, water-swim, quarantine,
  cosave, rest-is-the-only-save (g15-batch).
- Passed in reds3: lf83-endings (talk fix).
- Fixed check, now passing: dialogue-intercept (talk aim and retry; the RouterLog expect now checks for the hook,
  because RouterLog never said "OpenDialogue"); claywater-look (nudge and E retry); w3-crime (strike; reds3 PASS).
- Still red when this was written (reds3 may have more by the time it ends):
  - quest-board: `arm` IsWeaponOut 0. The arm step's `key: R` after equipitem may sheathe a weapon already
    out. Fix: drop R from the arm steps and let `strike` draw.
  - fight-damage-builds: novice-blow. Live, the hit landed, but Health 1991.06 means 8.94 damage against the
    expected 10.8 +- 0.5. **Game finding, not retuned.** In reds3, 0 hits.
  - grow-at-rest: `strike {opp}` never got the deserter under the crosshair in 5 s (`_face` with a runtime id).
  - first-place `ask-signs`: talk gate never showed Signs.
  - lf83-components `stage-20`: no ArgoniaJournalNotice event.
  - rest-respawn: after the rest the deserter is 2941 units from the ambush marker (wanted < 1500), so it was not
    moved back. The ArgoniaCore `respawn: roster` and `K actors reset` lines are not read yet: read them first.
  - The batch was stopped here for touchfix. Not re-run: ui-sweep, smoke, ui-probe, world-sample,
    die-and-recover, menus-quit, suspend-save.
  - Not done: the vastei pile still, the respawn-flag reads, the ArgoniaCore `respawn: roster of N` line, the
  xLODGen still and the installer line, the crash items. Likewise the PROGRESS, in-game-owed.md and Outcomes L4
  edits.

## Other fixes
- deploy.sh header: a fresh worktree must link the main tree's untracked `out/*` folders. Without them
  `make plugin` drops the province navmesh (ArgoniaWorld.esm 150 MB instead of 229 MB) and rewrites committed YAML.
- run_batch `relaunch_before: true` (smoke). world-sample's crash is mid-journey at stop 2, so it needs the
  generator to split stops. suspend-save expects "(stream drop)".
- pad.ps1 wakes the hot-plugged pad with a small right-stick nudge. The planner's ask, one persistent pad host, is
  not built.
