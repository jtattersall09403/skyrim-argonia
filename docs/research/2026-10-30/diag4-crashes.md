# diag4: the three open crash cases (game-16)

Read-only diagnosis of every Crash Logger head under /home/ubuntu/wt-g16/out/batch (adhoc 202908, 211907,
213737, 215418 and all/181841). Each head was on the dev box, so the stopped game machine was not needed.

## Signatures

| run | item | uptime | fault | frames and objects |
|---|---|---|---|---|
| all/181841 | smoke | 6:12 | exec 0x01E000000000 | stack scan 69036+0x56 (+0EAE206), 21891, 442669; R12 ConsoleLogPrinter, BSMultiBoundAABB, JobThread |
| adhoc/213737 | smoke | 0:57 | exec 0x020700000000 | the same 69036/21891/442669 chain; ConsoleLogPrinter, BSMultiBoundAABB, JobThread |
| adhoc/211907 | world-sample | 0:37 | exec 0x020E00000000 | the same chain; plus BSGeometryListCullingProcess, BSTriShape ImpFloorMid01 |
| adhoc/213737 | world-sample | 0:37 | exec 0x01E400000000 | the same chain; BSGeometryListCullingProcess |
| adhoc/202908 | world-sample | 0:37 | SkyrimSE+1191BE3 `mov rcx,[rdx+8]` | probable frames are all engine (87792, 89682, 87834, the 83xxx cluster); only TrueHUDMenu::Logger is on the stack (not a frame) |
| all/181841 | world-sample | 5:11 | SkyrimSE+100F207 `call [rax+0x10]`, rax 0 | 77322/70723/76019/36818: the diag2 #1 render/update signature |
| adhoc/215418 | grow-at-rest | 1:53 | **ArgoniaBridge.dll+5DC33** `jmp [rax+0x30]`, rax 0 | probable frames are bridge +5DC33, +463FF, +47022 and +5962, then skse64 +199AF (the SKSE task), then the main loop; RDI/R15 is Character "Deserter" 1000088C, R13 is Steel Sword |

## Case 1: world-sample, first cell change after stop 1 (class: engine on cell transitions)
- Four of the five world-sample and smoke heads have one signature. The CPU executes a garbage address of the form
  0x0XXX00000000, and the stack holds 69036+0x56 (SkyrimSE+0EAE206) on a BSJobs job thread, with
  BSMultiBoundAABB and BSGeometryListCullingProcess. ConsoleLogPrinter is in R12, so a console command, the travel
  line, is running. This is the culling job walking a multibound of the grid being torn down. It matches game-6,
  game-12, diag-croc-move-crash §3 and diag2 #2.
- No probable frame is in ArgoniaCore, ArgoniaBridge, PrismaUI or any mod. EngineFixes and TDM appear only in the
  stack scan, which is noise. No record object is named.
- The 37 s uptime fits the fresh process per stop. The crash is at the first cross-grid move after stop 1's
  `teleport pos` probes. Those probes are a raw `SetPosition(to, true)` on the player
  (skse/ArgoniaBridge/src/ep_world.cpp:94), which shifts the grid without the MoveTo/fader load path.
- 202908 (SkyrimSE+1191BE3) and 181841 (+100F207) are two other engine-only signatures in the same window. +100F207
  is the null vtable on the render path from diag2 #1, which came after a `player.moveto`. So moveto alone is not
  immune.

## Case 2: smoke after `cow` to Tamriel (class: engine on cell transitions)
- Both smoke heads have the same 69036/BSMultiBoundAABB/ConsoleLogPrinter signature. The trigger is the last line
  of tests/scenes/plain-armed.txt, `cow tamriel 2 -4`, an exterior grid load from the console soon after a save
  load (57 s and 6 min uptime). No `teleport pos` was involved, so the trigger is the console-driven exterior cell
  change itself, and SetPosition only makes it worse.

## Case 3: grow-at-rest at pending-level (class: our DLL, ArgoniaBridge dev endpoint)
- The faulting frame and the next three probable frames are ArgoniaBridge.dll. The thread is the main thread (1440
  is the same thread that logged the rest), inside an SKSE task, which is the bridge's `on_main_thread`. The only
  bridge call at that step is `dev-grow 1000088C 1 2000` (skse/ArgoniaBridge/src/ep_dev.cpp:85-118). It calls the
  deserter's ActorValueOwner (Get/Restore/DamageActorValue), GetEquippedObject and SendEvent(TESHitEvent).
- The state that leads to it comes from the journey. rest-no-pending runs `disable`, then the rest, then `enable`.
  The rest runs ArgoniaCore's ResetActors (skse/ArgoniaCore/src/life.cpp:151-174; logged "respawn: 2 actors
  reset"). That reset moves the disabled deserter to its editor location. The crash log puts him in "Wilderness"
  0B012B46, while the player rested in 0B000800. He is therefore re-enabled out of the loaded area, with no
  middle-high process or 3D. dev-grow checks only `!IsDead()` before calling into him, and a vtable or process
  pointer read as 0 jumps through `[0+0x30]`.
- The cause is not the sitting view, the level-up code or PrismaUI. No PrismaUI, WebCore or ArgoniaCore frame
  exists, the core log's last lines are the rest save (no sitting or level line), and the fault is in the bridge
  before any pending level exists.
- Not pinned: which exact call is at +5DC33. There is no ArgoniaBridge.pdb or .map on the dev box. The next lane
  should read the crash full log's symbolised frames once a PDB ships.

## Stack check
- data/dependencies.json:214 lists Crash Logger 1.27.0 (loads on 1.7.104). data/dependencies.json:241 lists SSE
  Engine Fixes 7.0.21, which installs only `EngineFixes FOMOD Installer/Required/*` and `/AE/*`.
- No EngineFixes.toml override exists anywhere in the repo, and infra/gpu-box/stack.py writes none, so the defaults
  run. Part 2 is not installed (the preloader d3dx9_42.dll, EngineFixes_preload.txt and the tbb allocator). The
  memory-manager and Scaleform-allocator replacements depend on Part 2.
- No Engine Fixes patch is documented against this exact multibound/culling-job signature, so Part 2 is a route 2
  stabiliser to measure, not a proven match.

## One root fix per class
1. **Engine on cell transitions:** make every travel go through the engine's own load path, never a raw grid shift
   from a console line.
   - In tools/world_sample.py:109/311/358/389/436, replace `teleport pos` with a `player.moveto` to a marker placed
     at the probe point. The marker is placed in the world database or ESM, or placed with `placeatme` from a
     loaded marker. Then read z.
   - In tests/scenes/plain-armed.txt, replace the last line `cow tamriel 2 -4` with `player.moveto` to a placed
     Tamriel marker.
   - Keep the existing fresh process per worldspace or stop.
   - Second step, route 2 and native: add the Engine Fixes Part 2 preloader to dependencies.json and stack.py. Keep
     it only if a 3x world-sample and 3x smoke rerun goes from 5 crashes to 0.
2. **Our DLL:** in ep_dev.cpp, dev-grow (and `strike`/any actor endpoint) refuses a target that is disabled, has no
   parent cell in the player's loaded grid, is not `Is3DLoaded()`, or has no `currentProcess`/middle-high. The
   refusal returns a reply error instead of calling in.
   - Second fix, in ArgoniaCore ResetActors (life.cpp:151): skip disabled actors. The rest should not move a
     reference the world has switched off.
   - Test: the bridge unit test for the guard, and grow-at-rest rerun to pending-level.
   - Journey: in grow-at-rest, after the rest, `{opp}.moveto player` before `enable`, so the target is loaded.
3. **Mod:** none found. No probable frame belongs to a mod.
4. **Record:** none found. No record object is implicated (Dawnguard's Moric Sidrey and Ruunvald on grow's stack
   are stale stack values, not frames).

## Blast radius and risk
- Fix 1 touches tools/world_sample.py and its tests, and tests/scenes/plain-armed.txt. It may also add markers in
  the world DB and ESM (a rebuild). The risk is moveto landing at another z than the probe expects; check the
  z-read assertions.
- Fix 2 touches ArgoniaBridge ep_dev.cpp and ArgoniaCore life.cpp, which means rebuilding both DLLs. The risk is
  that skipping disabled actors in the rest reset leaves a disabled roster actor unhealed; the respawn unit tests
  cover this.
