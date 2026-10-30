# Lane game-11: combat A restored exactly, the roll's missing perk found, Nemesis tried for DSC, Livia's lock (2026-10-30, ~10:35 to 11:45 UTC)

The lane stopped early. argonia-play was stopped at 11:30:52 (user-initiated) during the DSC diagnosis. The
planner first said hands off for the owner's #16 play session, then corrected that. The restart (`run.sh up`) was
then refused by the permission system, so no in-game item past §3 ran. The next game lane needs the machine
started by someone allowed to start it.

## 1. Combat set A restored exactly (order item 1)
- **The 20 bad files were 20 missing files, every one with a CJK name** (rim-parry's `... - 副本.wav` copies, and
  `.hkx`/`.xlsm` files under openanimationreplacer). Windows `tar` converts pax UTF-8 names through code page 1252
  and skips one it cannot convert ("Archive entry has empty or unreadable filename ... skipping", exit 1). The push
  never checked tar's exit code. Proved with a two-file tar on the machine: `°` was laid and `副本` was skipped.
- **Fix (3fea556):** `stack.py push` sends paths that are not ASCII in a zip, which .NET's ZipFile unpacks with the
  UTF-8 flag honoured; tar's exit code is checked, and a failed unpack fails the push. Test:
  tooling/tests/test_stack_push.py (2 tests; the old send_tar fails the first).
- rim-parry re-pushed, profile laid: **`stack.py verify`: 22,573 recorded, 0 bad, 0 unrecorded, VERIFY OK**.
  tk-dodge.toml now matches its record, so 0.2 §b's verify is clean.
- **A plays, with one owed re-proof.** After the restore no roll played (smoke: no TKDR_DodgeStart; trial-a moved 0).
  - Cause: ArgoniaCore logged "combat: the sheet is uninitialised, no carrier is written". base_save.py starts with
    `coc` from the main menu, which sends no kNewGame, so NewCharacter (e668b08, 05:37 today) never ran. No roll
    tier was set, and TK Dodge's perk lock refused every roll.
  - With `player.addperk FE00D809` added by hand, smoke's roll passed (> 300 units), and walk, draw, swing, block,
    inventory and map passed too.
  - fixes-2 fixed it at source in **2dab64e** (the character is made at game ready). It is not yet deployed.
- Also in 8d32df1:
  - `stack.py install` now stops the game *before* the push: B2's push failed removing modern-stagger-lock while
    the running game held ModernStaggerLock.dll.
  - `run()` names the failed command.
- smoke's `journal` step fails ("no menu event matching 'Journal Menu'"). Our journal view replaced the vanilla menu,
  so the expectation is stale: owed to whoever owns smoke.yaml.

## 2. The DSC trial (order item 2): Nemesis tried, no wiring yet; verdict owed
- The Nemesis row (Nexus 60033 v0.84-beta, GPL-3; permission recorded) and `stack.ps1 nemesis` are in 8d32df1. The
  details are in journals/combat.md "A restored exactly; DSC's engine fallback tried".
- On B2: `-update` crashed (0xC0000005) at "New Animations extraction start (behavior templates\b\behavior)", the
  FNIS `b` template. `-generate` hung at 0 CPU until its 900 s limit, and no behaviours were written.
- DSC's hkx files are SE packfiles, so the format is not the cause. The test expectation now has Nemesis in B and
  B2 only (tools/tests/test_stack_combat.py).
- **Owed:** one Pandora run on B2's Data, reading its "FNIS Parser ... BBDarkSoulsCombat" lines (the script is
  below); then FNIS for SE, or the verdict **"DSC not viable on this stack"** for the owner's packet. FNIS for SE
  has no documented unattended mode, and it would overwrite the Nemesis-format behaviours that TDM, TK Dodge and
  the rest need, so it is unlikely to serve B2.

## 3. Livia asleep with the player present (order item 5): fixed at source, not yet proved in game
- Read from Skyrim.esm, the vanilla Sleep template (019717) is Sequence[Travel, **LockDoors** (run when bool 15
  "Lock Doors?" is set; with bool 13 "Warn Before Locking?"), Simultaneous[Find bed, Sandbox], Sleep].
- Ours had both set, which is the template default. LockDoors with a warning waits for the player to leave, which
  fits game-10's read: asleep only once the player went outside.
- **2340e35:** a home's sleep package sets "Lock Doors?" off, as vanilla's inn sleepers have it (packages.py
  `SLEEP_LOCK_DOORS`; test_packages.py). Four sleep packages were regenerated.
- Re-run livia-sleep.yaml after the deploy.

## 4. Other pieces done off the machine
- **0.3's two timings** are in journals/bridge.md: scene to scene p50 7.7 s (7.1 to 11.8 s, 80 runs); launch to a
  scene about 68 s; edit to verdict 238.3 s. **0.3 can close on recording.**
- **infra/gpu-box/memclimb.py** is committed (game-10's load-only loop, tidied); not yet run.
- **The owner's shader cards** (planner's item): `stack.ps1 play-modded -Shaders on|off` sets CS's DLL aside for
  "off"; its settings files stay, and the next `on` lays the DLL again. sunshine-apps.json replaces "Skyrim (Argonia
  stack)" with "Argonia (shaders on)" and "Argonia (shaders off)".
  - Not yet on the machine: copy apps.json as setup.ps1:88 does, and push stack.ps1.
  - Then check that both cards launch, and the CS log reads on or off.
  - Note: if the game is already running, a card only brings it to the front and does not switch the mode.

## 5. Machine state left
- B2 is staged and laid. The Nemesis run ended mid-way: Data holds Nemesis_Engine's tool files and 197 behaviour
  files as copies, and pandora-output is empty.
- **The first step on the machine is `stack.py combat A --skip-fetch`**: it stops the game, re-pushes the tools
  without Nemesis, runs Pandora and the animdata patch, then the menu.
- After that: `stack.py verify` (expect 0 bad), then `make deploy` built from a HEAD worktree. fixes-2 and the
  falls-croc lane edit skse/ and plugin/ in the shared checkout, so use
  `git worktree add --detach <scratch> HEAD; <scratch>/infra/gpu-box/skse_build.sh build`, then
  `make deploy DEPLOY_ARGS=--no-skse`. The deploy carries 2dab64e, cf11cb0 (the crocodile's shallows den), 2340e35
  and the notice, thing hooks and HUD locks.

## 6. Left, in order (for the next game lane)
0. **Planner's order (11:45):** start `infra/gpu-box/lod.sh` (tools, survey, the "without" still, then run) in
   the background as soon as the machine is up, alongside the functional checks. Measure no frame times while it
   runs. The map does not wait on LOD: check that M opens our own 2D chart and shows our map, at any time.
1. Start argonia-play (refused for this lane by the permission system). Then `stack.py combat A`, verify 0 bad, and
   the deploy as in §5. Check that ArgoniaCore.log reads "new character: argonian ..." with no "sheet is
   uninitialised". Then smoke (relax or fix its journal step) and combat-trial-a: the roll covers its distance.
2. DSC verdict: Pandora on B2 with Nemesis set aside, reading the log's DSC lines. The script is
   `run.sh ps 'Rename-Item C:\argonia\MO2\tools\nemesis nemesis.off'`, then `DESKTOP_WAIT=900 run.sh desktop
   '& C:\argonia\infra\stack.ps1 pandora'`, then `stack.py pandora-check`. If it is not wired, record "DSC not viable
   on this stack" in journals/combat.md and the owner's packet. If it is, run combat-trial-b2 and combat-trial-b.
   Either way, return to A with verify 0 bad.
3. ui-probe past `hud` (fixes-2's three HUD locks; the Views line lists the members): frames closed/open p50/p99,
   scroll, journal, Escape, chart, relaunch. Send the planner the numbers for decision 0017.
4. lf83-components with the journal notice asserted (`event: {kind: mod, match: ArgoniaJournalNotice}` at each stage
   and clue). The thing hooks: HasPerk ARG_Perk_ThingHooks 1, then flags crack-seen, tub-seen, ledger-read.
5. croc-den.yaml twice (the shallows den, cf11cb0; a water ambusher by design): placed, attacks when the player wades in, killable, no respawn.
6. livia-sleep.yaml twice (2340e35): asleep with the player in the room.
7. w3-infra (002dca4, in deploy1): s09 gate message, s10 sign still (reader: arm direction and height), crime on
   ARG_Faction_ClaywaterStation.
8. The world sample (13 scenes; deploy sends 30). LOD's result (started at step 0), then FWMF (no Whiterun).
9. memclimb.py (`job_guard.sh run --gpu memclimb -- python3 infra/gpu-box/memclimb.py 8`).
10. The shader cards (§4). Menus and the quit save (fixes-1). LAST: the soak, once, never a gate.

## Commits
3fea556 (push: non-ASCII names by zip; test), 2340e35 (sleep: Lock Doors off; test; 4 packages), 8d32df1 (Nemesis
row and stack.ps1 nemesis, install order, run() message, memclimb.py, combat-set test), and this report with the
journals and the shader cards.
