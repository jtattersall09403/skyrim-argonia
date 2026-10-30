# Lane game-5: side rolls, the deploy, the runner (2026-10-30 02:35 to 03:16 UTC; hand-off at the context mark)

## Measured
1. **Keytrace.esp is laid** (Data and Plugins.txt, DtryKeyUtil.dll 1.7 build). Nothing to add.
2. **Every earlier dodge number was taken in first person.** The rolls' stills show the first-person view, and
   `IsPC1stPerson >> 1.00`. In first person TDM's directional movement is off. Its global `TDM_DirectionalMovement`
   (FE00B807) read 0 at rest and through a 1.5 s walk, sheathed and drawn. So TK Dodge RE never took its own "TDM
   free movement, force forward" branch (`TKRE.cpp:62`, MIT source) and played side clips. game-3's "TDM turned the
   character" was wrong: the heading stayed at 260 through a 1.2 s E stick.
   - In first person (this lane's re-measurement), the roll's own distance by direction, sheathed then drawn:
     N 436/441, NE 115/122, E 55/42, SE 15/23, S 213/219, SW 2/2, W 107/101, NW 419/436. The backstep was 213 both.
     These match game-3's table.
   - **A 300 ms F press puts the camera in third person** (a 100 ms press did not take). In third person the global
     reads 1, and the heading turns 260 to 350 under an E stick.
3. **Third person, at QASmoke.** Sheathed: N 249, NE 326, E 313, SE 207, S 138, SW 32, W 262, NW 3, backstep 320.
   Drawn: N 274, NE 228, E 103, SE 299, S 80, SW 278, W 321, NW 331, backstep 402. Every roll now follows its stick.
   The short ones ran into QASmoke's pillars: the NW still shows the character against a pillar. QASmoke's navmesh
   reported 0 triangles, so `nav` could not find a clear spot. **Not closed:** the 8-way has to be re-run on an open
   floor (`smoke.py dodge --at tamriel,10700,-13025`, the plain west of Whiterun's palms, which is the new default).
   It also has to be re-run after this deploy, because `bUsePerkLock = true` now holds the roll to ArgoniaCore's
   burden tier.
4. **make deploy, first run:**
   - make plugin; stage 10 s (it laid tk-dodge's perk lock, Magic Expanded, Depths of Skyrim, SIRENROOT and the
     argonia-theme overlay); push 90 s;
   - skse build 103 s (ctest 29/29; ArgoniaCore.dll 1,453,056 bytes, ArgoniaBridge.dll 833,536 bytes, with
     core-suspend);
   - ESMs and the 12 scenes sent 17 s; `launch --fresh` to the main menu 116 s.
   - **Then `coc ARG_HoldingCell` from the main menu crashed:** `crash-2026-10-30-03-14-08.log`, an
     EXCEPTION_ACCESS_VIOLATION at SkyrimSE.exe+0327DC4 (`mov rcx,[rcx+rax*8]`, a null base). The base save was not
     written. Not diagnosed. Read the crash log's call stack first. The three masters added in this lane, or the
     new ESMs, are the likely suspects.
5. The machine was stopped at 03:14 (17 saves backed up, `20261030T031435Z`). Earlier, idle-stop stopped it at
   about 02:58, mid-session: bridge calls made over the tunnel outside `job_guard --gpu` do not refresh its busy
   flag. Run game work under job_guard.

## Built (committed with this report)
- `smoke.py`: `third_person()` before the launch, the dodge, the pad and the scene; `dodge --at world,x,y`.
- `stack.ps1`: SkyrimPrefs `[Interface] bShowCompass=0, bShowQuestMarkers=0` (written when the game window is set up).
- `stack.py`: stage now lays the deferred rows that our built ESMs master (`our_masters()`). Argonia.esm masters
  Magic.esp, DepthsOfSkyrim.esp and evgSIRENROOT.esm, which were not laid. Stage also lays
  `out/ui_theme/argonia-theme` above the Dear Diary family.
- `bridge.ps1 prepare` copies `C:\argonia\ours\{ArgoniaWorld,Argonia}.esm` into Data and enables them last.
- `make deploy` (`infra/gpu-box/deploy.sh`, flags --no-plugin/--no-stage/--no-skse/--no-base) and
  `infra/gpu-box/base_save.py`. The base save uses coc from the main menu, because the start quest's script needs
  the Creation Kit (#15, still open: CreationKit.exe is absent).
- `tools/run_journey.py` with `tools/tests/test_run_journey.py` (7 L2 tests: pass, broken step with reason and
  still, refused action, crash, quests against the allowed list, three identical failures stop, draft refused).
- Journeys `smoke`, `broken` and `quarantine`; ten scenes (`tests/scenes/*.txt`); the skill
  `.claude/skills/scene-author/`.

## Owed, in order (next game lane)
1. Diagnose the coc crash (step 4), then `make deploy DEPLOY_ARGS="--no-plugin --no-stage --no-skse"` to write
   argoniabase.
2. `smoke.py dodge` and `dodge --drawn` on the open plain, which also tests the burden lock. Then the check that
   Skyrim's own Block term does not double with our block carrier (core-wiring's report).
3. `run_journey.py` on `smoke` (twice), `broken` and a forced crash. Ten scenes applied, with the
   scene-to-scene time measured.
4. `smoke.py pad`; `stream-e2e` (0.0 bar: keys 39.6 ms median).
5. The uncapped water frame times: the scratch driver is at
   `$scratch/g5/water_ft.py`, and its method is uncap, measure, restore. The cells are (-39,-43) with 123 planes,
   (-18,-16) with 64 and (-28,-22) with 32, each with `tws` on, off and on again.
6. `ui-sweep` with a reader. The overlay is laid; the sweep is still in draft form.
7. The quarantine journey. The `sq` parse in `running_quests()` and the `time` key `days_passed` are untested in
   game. The music type needs a bridge read.
8. The timed loop (§e). Argonia.esm has no dialogue records yet, so an NPC greeting cannot be read back. Use another
   NPC field, or wait for the dialogue generator.
9. Lay block-build's Claywater block once that lane says it is ready.

Not closed: 0.2 (frame bar: owner #16; side rolls owed), 0.3 §c to §e, 0.4 §b. PROGRESS rows are unchanged.
`make check` is red only on other lanes' work: lint F401 in `tools/argonia_world/place_build.py`, and
plugin-check's terrain sample hash. Both belong to block-build's uncommitted edits. This lane's files are lint-clean.
