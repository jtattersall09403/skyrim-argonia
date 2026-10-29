# Lane game-1: 0.3 §a live and the 0.2 close (2026-10-29, 22:18 to ~00:15 UTC; hand-off at the context mark)

## Verdicts the planner gave (for the record)
- houseCARL's 374 dangling refs inside KotM, Depths, HTBM and EREP: accepted as shipped upstream; re-examined only
  if reachable in our world.
- SkyLink dropped (the skylink-rebuild lane has since built one for 1.7.104; not tried in this slot).
- SSE Engine Fixes 7.0.21 added.
- Owner ruling applied: slim the dependency list (below).

## Done and measured

**Fast verify (0.2 §b), `stack.py verify [--full]`:** sizes and mtimes against a hash cache on the machine
(`C:\argonia\stack-state\hashcache.tsv`; a hard link shares both with its mod file, so it holds across off/on),
hashing on every core (C# `Parallel.For` in PS 5.1), progress every 500 files, streamed to the build VM.
Full pass 424 s (68,801 files); cached pass 20-27 s. **VERIFY OK** at 68,845 recorded files, 0 bad, 0 unrecorded
(before the slimming). The serial job was killed at 22:20 (17 min, no output). Three real faults it found, fixed:
- **64 files laid with mojibake names** (BM&V, Rim Parry, Modern Stagger Lock): Windows tar read the GNU tar's
  UTF-8 names as cp437 (`°` laid as `┬░`). `push` now tars with `--format=pax`; the laid files were renamed on the
  machine (85 names, files and folders).
- `stack.ps1 off` used `cmd dir`, whose OEM code page mangled non-ASCII names so they were never removed (a 0.0
  Chinese readme survived every `off`); `off` and `verify` enumerate with .NET now.
- Pandora's 30 outputs replace 8 recorded mod files in Data; verify skips those paths. Inis and logs the plugins
  write at first run (`SKSE\Plugins\*.ini`, `SKSE\*.log`) are not "unrecorded".

**The bridge live (0.3 §a, L4)**, `tools/tests/bridge_live.py`, three full runs and fixes between:
- Run 1 crashed at the first `load`: SKSE passes kPostLoadGame's success *as the pointer value*; we dereferenced
  it (address 0x1). Fixed in `main.cpp`.
- Run 2 (46/48 as designed) then run 3 (46/50 with the new cases). Fixed after run 2: an unknown cell is refused
  before `coc` (coc scans every plugin's cells on the main thread and held the task queue past 3 s: the next
  calls failed with "main thread did not run the task"); `av` round-trips the name (the lookup answered
  `NoSuchValueZZ` with a real value); booth framing from the object's 3D world bound, 160+ units out, pitch 0.3.
- **Proved live:** ping and bad token; the main-menu refusals; load of a missing save and of a path; load of the
  base (12.1-12.8 s); player; console with output and a refused line; save then load (2.6 s); teleport pos, cell
  QASmoke (1.0 s), unknown cell refused (20 ms); time set and read back, hour 25 refused; weather read, force
  outdoors, not-a-weather; quest, global, av, inventory with their refusals; quest-stage event; input over the
  cap and an unknown key; a wait_event that never comes; pad stick walk (moved 352 and 694 units); pad cap;
  frametime 120 (p50 16.9-22.3 ms; Defender busy, see below), 5 refused, a missed budget; nav near and off-mesh;
  booth six views (frame differences 0.47-0.62) and a non-bound form; **the screenshot oracle live** (two stills
  1 s apart differ: changed fraction 0.38 and 0.65, Pillow from `~/.argonia/venv`); a frozen frame refused.
- **Crash: reported in 5.9 s and 12.0 s** (Crash Logger log, process still up); **the relaunch killed the
  crashed zombie** (`killed: [2268]`, no survivors, 217 s with Defender busy).
- Still red, fixed in code but not re-proved: the hit event (a self-cast spell raises no hit; now a placed wolf
  bites the player), key W walk and the pad walk inside QASmoke (QASmoke streams every item of the game and stalls
  the main thread; the input group now reloads the base save first; in Riverwood a W press left pings at 10-30 ms).
  The extra hung-game case (NtSuspendProcess) was reported in 74.9 s, over the 60 s bar, and the relaunch then
  killed it (`killed: [7628]`); the suspended-thread health check was added after that run, not yet re-run.
- Note: Pillow is only in `~/.argonia/venv`; without it `frame_difference` falls back to bytes. Run the live
  suite with `~/.argonia/venv/bin/python`.

**Dependency slimming (owner ruling, `docs/research/2026-10-29/dependency-audit.md`):** in `data/dependencies.json`,
14 rows `dropped` with the reason (papyrusutil, po3-tweaks, po3-papyrus-extender, consoleutil-extended, xalfek,
drjacopo-grass, base-object-swapper, boats-operational, tropical-skyrim-le, hoddminir, darkwater-den,
script-free-ship-sailing, cyrodiil-ships, skylink-ai); 18 rows deferred with `from` (2.5, 2.7, 2.9, 2.12, 2.W5);
stale `chunk` fields fixed (combat rows 1.6, traversal 0.2, boats 0.4, fuz-ro-doh 2.5, spid 2.7, flat-world-map
2.12, no-google-maps 1.4, depths 2.W5). `stack.py stage/install --through <part|chunk>` (default part 0) lays only
started rows (`started()`: earlier parts, then the same track up to the chunk). **BM&V by `keep`:** the 7 meshes the
world references outside flora (16 prop and sign refs, plus Claywater's reedsmall2), the textures they name and
Black Marsh.esm: 36 of 45,225 files, 21 GB to 33 MB. Profile now **63 mods, 26 plugins, 22,330 files**
(was 88 / 35 / 68,845). Note: BM&V's kept textures include vanilla-named ones (riftenroofshingles01, stallroof01,
castlewindow01, farmwoodend01, metal_01) that override vanilla everywhere, as the whole mod did before.
KotM without rows 73/74: both are mesh-only (no plugin, so no master); KotM.esp loads, and its keep records only
lack meshes until 2.W5, where no place before uses them.

**Fixes to the install:** stage frees the old staged copy before unpacking (BM&V's restage failed its 10 GB room
check otherwise); each 1 GB push part retries scp three times (one dropped with exit 255); install quits a running
game before `off`.

## Reds and decisions for the planner
- **Windows Defender** held the machine at 100 % CPU (MsMpEng 2,857 CPU-s by 23:20; +80 CPU-s in the next 40 min,
  so settling). Exclusions were refused by the permission classifier ([Security Weaken]); not worked around. Frame
  time (§d) must wait for exclusions (owner) or a quiet Defender (CPU delta over 30 s near 0).
- Deleting the machine's stale 0.0 mod folders (named with spaces, not in the modlist, never laid) was refused by
  the classifier; they stay (harmless; a few GB).
- `skse_build.sh` skipped its install step because core.messages failed under MSVC (now fixed by the planner); the
  DLL was copied by hand from `build\windows-dev\ArgoniaBridge`.

## Left, in order (the next game-machine lane)
1. Done at hand-off: the slimmed install from bare Data reached **MAIN-MENU OK** (data loaded in 67 s; **27 DLLs
   loaded, 0 not**, was 35; Pandora 29 behaviour files from 10 mods; off removed 68,878 files; peak RSS 100 MB).
   Next: `stack.py verify` (rehashes the new laid set), then the smoke runs prove the Papyrus-helper cuts by removal
   (read the Papyrus log for "unable to find function"); restore only a row that is needed, with why.
2. Rebuild ArgoniaBridge (`skse_build.sh build windows-dev`; picks up f8ae7af's SEH wrap and the core.messages
   fix), then `tooling/job_guard.sh run --gpu bridge-live -- ~/.argonia/venv/bin/python -u -m tools.tests.bridge_live
   --save argoniariverwood --crash`: expect the hit, W walk, pad walk and hung-game cases green. If any is red,
   fix and record. Then fill the journal's measured-times table (numbers above).
3. 0.2 §c with `infra/gpu-box/smoke.py` (now on tools/bridge.py; uncommitted parts tested only by import):
   `smoke.py launch`, `dodge` (8 directions plus backstep by position; if a roll is no more than the walk, bisect:
   dynamic-dodge's OAR folders, then AMR), `pad` (RT power attack: IsPowerAttacking during and the attack tags;
   LB IsBlocking; RS lock-on with a placed bandit and a still), `scene` (runs twice: load, walk, draw, swing, roll,
   block, every menu with a still, logs). Climb, swim, ladder and Sailable Ship need places found first (not
   written). A `reader` judges the menu stills for the paper theme.
4. 0.2 §d once Defender is quiet or excluded: `smoke.py frametime --label cs-on`, then CS off; latency by
   `tooling/job_guard.sh run stream-e2e -- infra/stream-client/e2e/e2e.sh`. Numbers into infra/README.md and 0007.
5. Close 0.2: infra/README.md "Game stack" section, 0007 numbers, the 0.2 Outcome (counts above), 0.3 Starting
   state, PROGRESS 0.2; delete `combat_test_stage.py` and `combat-test-mods.json` and fix the two citations (1.6
   brief:12, 0019:47); `stack.py prune` and `evict` after verify passes; `make check`.
6. Mark 0.3 §a done in its brief with the live numbers once step 2 is green.

Build-VM peak RSS: verify 64 MB; install (stage of BM&V) under MemoryMax=3G, see `stack-install.log`.
The machine is left running.

**Gate:** `make check` at hand-off: one red, `tooling/tests/test_job_guard.py::test_locks_are_per_machine` (another
lane's new test), which failed with "gpu lock busy" while this lane's install held the real GPU lock. Run alone
after the job: 2 passed. Every other part of the gate was green. The test reads the real lock, not one in
`tmp_path`: a fix for its owner.
