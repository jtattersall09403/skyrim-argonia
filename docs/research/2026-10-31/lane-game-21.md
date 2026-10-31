# Lane game-21 (2026-10-31): the first check round on the London g6

The machine is the London g6, i-082ad5630dee91959, tagged argonia-play. The worktree is /home/ubuntu/wt-g21. The slot is game-21's until 13:51 UTC.
The build VM restarted at 06:29 and killed the g4dn round, which had not produced any results.

## Pushed
- **e354a6f, the deploy heartbeat lock.** The heartbeat's orphaned `sleep 300` held the job's gpu.lock for up to 5 min after DEPLOY OK. A TERM trap now kills the sleep too. L1 test: `tooling/tests/test_deploy_heartbeat.py`. The old loop leaves the lock HELD; the new one frees it.
- **70499e8, base_save and the coc timeout.** A reply timeout on the coc is no longer a failure: the new-game load holds the main thread past the 3 s reply. It failed game-20's deploy once and game-21's twice; the rerun was green in 11.9 s.
- **6a14cb8, the HUD over the load (unproven, not built yet).** The HUD view is now hidden natively when the Loading Menu opens and shown again when it closes. The 9 load stills (reader) showed no Nordic art. But they did show our bars and the "0 vastei" box over black load frames for 4-16 s. No still caught the Loading Menu's own art or text, so the Celtic-knot border is not confirmed either way.
- **ef4922b and dd515ee, the Moonlight cards.** Only the Argonia cards remain (shaders on, shaders off), and the card pictures carry the names. deploy.sh lays apps.json and the cards each deploy, and restarts Sunshine only when the list changed. London's moonlight-web lists ['Argonia (shaders on)', 'Argonia (shaders off)'].
- **dcccfa1, BLOCKER: the cards launched Skyrim without Argonia.** `stack.ps1 on` lays only the modlist and removes our ESMs, ArgoniaCore and scripts. play-modded now lays them after `on`. Proven on London: Plugins.txt keeps both ESMs after the game starts, and ArgoniaCore loaded.
  - This was also the cause of the "failed load of argoniabase" on world-sample s03 and of every item after it in batches b2 and b3. A card launch at about 10:21 removed the ESMs.
- **8baf1e0:**
  - ui-sweep and ui-probe now expect `vanilla-hud hidden 11/11`. The test was stale: the count grew from 4.
  - `lod.sh archive` and `lod.sh restore` added. The archive goes to s3://argonia-private-…/lod/<ArgoniaWorld sha12>.tar and latest.tar.
  - dev-quit-to-menu now sets resetGame again on the next frame (unproven).

## Results (batch g21-b4, 10:40, after the card fix)
- **die-and-recover: FAIL at die.** No "death: fell" within 20 s. In b1 (10:04) it passed through take-pile, and second-death failed. Not yet diagnosed. The deserter may not have attacked (fight-archetype's "no swing" is a known red).
- **ui-sweep: FAIL at hud-open.** The expectation was stale; fixed in 8baf1e0, rerun owed.
- **menus-quit: FAIL at quit-confirmed.** The quit save ("ArgoniaSuspend written (quit)") is checked first and passed; MainMenu then did not follow within 30 s. The fix in 8baf1e0 is unproven.
- **world-sample:** passed s01 to s03; running at the hand-off.
- **Machine stop:** 10:10:26, by the paris lane's switch e2e (now guarded). Restarted at 10:15.

## Owed items
- **stack.py verify --full: 2 bad of 22,574,** both in argonia-theme: scripts/ski_configmenu.pex and interface/skyui/config.txt. installed.json is probably stale since ui-review4/5; regenerate it if so.
- **xLODGen:** job g21-lod is queued after b4: `lod.sh run prepare terrain collect`, then `lod.sh archive`. A Claywater still (`lod.sh still g21`) with a reader is owed after it.
- **Touch B on the journal; the phone drive.sh runs (v5-folded, v5-unfolded):** not run.

## Next (resume here)
1. Wait for g21-lod. Then an SKSE-only deploy, `make deploy` with --no-plugin --no-papyrus --no-stage, to build 6a14cb8 and 8baf1e0.
2. Then the load-screen still capture again, starting the grabs earlier, with a reader.
3. Then re-run ui-sweep, menus-quit and die-and-recover. Then one all.yaml pass, crash-prone checks last. Update in-game-owed.md.
4. Leave the machine running.
