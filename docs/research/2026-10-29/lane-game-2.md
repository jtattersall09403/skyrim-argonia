# Lane game-2: 0.2 continued on the game machine (2026-10-29 23:25 to 2026-10-30 ~01:00 UTC; hand-off at the context mark)

Commits: 759f37e (bridge, SkyLink, smoke, dodge bisect, journals) and the hand-off commit that adds this report,
the water and frame-time numbers.

## Done and measured
1. **`stack.py verify` on the slimmed set: VERIFY OK.** 22,330 files, 0 bad, 0 unrecorded, 54 s on the machine,
   build-VM peak RSS 100 MB.
2. **Bridge rebuilt** (ctest 21/21 on MSVC after a second `core.messages` skip for `ui/schema`).
   **`bridge_live --crash`: 50/50.** Crash reported in 4.6 s. **Hung game reported in 21.5 s** (was 74.0 s:
   `bridge.ps1 health` now counts a majority of suspended threads, since one thread stays in an Executive wait).
   The stage case moved last, with a base-save reload.
   **Rebuilt SkyLink loads on 1.7.104.** Compared beside ours (`tools/tests/skylink_compare.py`): ping, player,
   console, save/load and teleport all answer. Its console output is a stale last line, and its save and load
   do not wait for completion. It is not laid. The times table is in `journals/bridge.md`.
3. **0.2 §c, partial.**
   - RT heavy: green (`IsPowerAttacking`, power-attack tags).
   - LB block: fires (`blockStartOut`). The probe's wording is fixed but not re-run.
   - RS lock-on: not run (the bandit id was refused; now a wolf).
   - **Dodge: red.** TK Dodge fires in every direction, but the backstep and a standing power attack move 0.0.
     Animation-driven motion is zeroed for all clips.
   - The bisect ruled out AMR, Dynamic Dodge's OAR clips, Pandora's motion data (present: DodgeBack 202 units),
     the test's teleport, and 11 DLLs (TDM, Precision, TrueHUD, FreeClimb, Svimex, Display Tweaks, MSL,
     MaxsuIFrame, Elden Parry, OCPA, AQF). The table is in `journals/stack.md`.
   - `scene` ×2 and the menus' reader: not run.
   - Papyrus logging is now on (`stack.ps1`), so the helper-cut proof can be read on the next launch. Not yet read.
4. **0.2 §d, Defender quiet.**
   - Riverwood with CS on: 45.0-45.8 fps median, 32.3-35.3 1% low. CS off: 52.9 / 40.4. **The bar is missed.**
   - PresentMon wrote no CSV: owed.
   - Stream latency: owed.
   - **Water budget:** 127, 65 and 32 designed planes each sit on the 60 fps cap, planes on or off; the 1% low
     noise is larger than the on/off difference. In `journals/water.md`.

## Next lane, in order
1. **Dodge:** continue the bisect over Engine Fixes, BDI, Payload Interpreter, OAR, SkySA, Custom Skills,
   Pandora's behaviour outputs and the inis (`infra/gpu-box/aside.ps1`; the driver is the scratch `bis2.py`
   pattern: aside, launch, backstep plus power attack, back). Then a vanilla control with the profile off.
2. `smoke.py pad` (re-run with the fixes), then `scene` twice plus a `reader` on the menu stills; read
   `Logs\Script\Papyrus.0.log` for the helper cuts.
3. §d: get PresentMon working (run it in the desktop session) for CPU/GPU-bound and an uncapped water run; then
   `stream-e2e`; then the brief's fallback for the missed bar (lighter CS, then a larger instance), each
   measured, then 0007 and infra/README.
4. Close 0.2 (Outcome, 0.3 Starting state, PROGRESS, delete `combat_test_stage.py`/`combat-test-mods.json` and
   fix their citations, `prune`/`evict`, `make check`). Mark 0.3 §a done: the bridge is green 50/50 now.
5. 0.3 §b-§e: not started. For §b, ArgoniaCore.dll is already built and laid (628,736 bytes in
   `MO2\mods\Argonia SKSE`). Its natives need an `ArgoniaCore.psc` (`Scriptname ArgoniaCore Hidden`, `string
   Function Version() global native`, `int Function SaveCount() global native`), compiled by `records_jobs.sh
   papyrus`. The bridge needs a call into the VM (`DispatchStaticCall`), since the console has no global-function
   call.

## Machine state
Left running at the main menu: the profile is on, without SkyLink and without the water test plugin (both
removed, and plugins.txt restored). Nothing is aside. The build VM's peak RSS was 950 MB (the water plan, child
agent). The scratch files (water test plugin, worktree of `wip/water-design`, bisect drivers) are in this session's
scratchpad only.

## Gate
`make check` was not run for the whole gate. What was run: `tools/tests/test_bridge.py` (10 passed), py_compile of
the changed scripts, and ctest 21/21 on the machine.
