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
