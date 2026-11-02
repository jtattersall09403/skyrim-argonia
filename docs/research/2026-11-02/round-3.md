# 1.15 round 3: driver report (build 1f454bb, ArgoniaWorld.esm aad64e6d9471, argonia-play Paris)

## Round 3: LOD rebuilt, the owner walks

Scope cut by the owner's ruling (10:50): no agent-driven batch (no panel, booth, creature spots, A/B, Claywater);
terrain LOD only, no object LOD this round. Object LOD is stale.

LOD timings (lod.sh, from 10:26:59 UTC):
- prepare OK, 31 s.
- terrain (xLODGen) OK, 1118 s (14625 files linked into Data, 10:46:15).
- texgen: TexGen printed "TexGen completed successfully", then its finished dialog hit the pop-up watcher before
  the done-check, which threw "unknown pop-up: TexGen / Exit TexGen / Zip and Exit / Check log / Restart ..."
  (dialog text: "Exit TexGen, zip and exit, check log or restart?"). Fix in infra/gpu-box/lod.ps1: Watch-Popups
  skips the tool's own finished dialog (`Exit TexGen|Save & Exit`). Rerun passed: texgen OK, 209 s, 1808 files.
- dyndolod and collect: not run. At 10:57:51 UTC the Paris spot machine was interrupted (state "stopping"); its disk
  persists (terrain and texgen outputs under C:\argonia\lod\out).
- `run.sh up` (about 11:10): "argonia-play: no spot capacity in eu-west-3 now". Stopped as ordered.

Remaining on the next successful `run.sh up`: `lod.sh run collect` (terrain output is on disk), `lod.sh archive`,
launch to the main menu on the base save. Lock released. The machine is not running.

### Afternoon (planner): the LOD, the saves and the machines

- **Terrain LOD** collected and archived at 12:24 (`s3://argonia-private-…/lod/aad64e6d9471.tar`, 21,418 files, 638 MB); any deploy of this build lays it from the archive.
- **Object LOD**: TexGen passed on the rerun (its "finished" dialog is now answered by the watcher); DynDOLOD 3.0 alpha-217 refused to start without `interface\dyndolod\dyndolod.dds`, which `Link-Resources` did not link (Interface was left out as "dynamic LOD only"): fixed (Interface linked; a `resources` step re-links after a restart without the prepare's wipe). Per-step markers per ArgoniaWorld sha now let a rerun skip the steps already done. The DynDOLOD run itself is still owed (queued behind the saves on the next Paris start).
- **Saves**: the engine refused every save after loading a save (bridge `save` and console `save`, with and without spaces in the name), while saves after a new game work (the deploy's own base and walk saves). The region saves are therefore made from a fresh game each (`region_saves.py --fresh`). Whether the owner's rest-save after a load is refused too is parked for 1.14 (owner).
- **Launches died silently** nine times, all within six minutes of a boot, with no SKSE log: Steam restarts itself to apply an update about five minutes after boot; `stack.ps1 menu` now launches only once `steam.exe` is 150 s old and its client is up. Four bisections of the LOD mod (all halves and the whole launched once Steam had settled) proved the mod innocent.
- **Machines**: Paris spot-interrupted five times (10:57, 11:43, 12:53 and twice in between), Ireland without capacity all afternoon; the build VM reclaimed eleven times today. The owner ruled to stay on spot (#35). Waiting jobs bring each machine to its target state when capacity returns and stop it after.
