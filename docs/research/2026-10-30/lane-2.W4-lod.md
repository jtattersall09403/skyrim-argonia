# Lane 2.W4-lod: LOD for ARG_Province as a scripted job (2026-10-30; hand-off, the run is not done)

## Delivered (commit 690dcbd)
- `data/dependencies.json`: the xlodgen (GitHub sheson/xLODGen v132), dyndolod (Nexus 68518, 3.00 Alpha-217) and
  dyndolod-resources (Nexus 52897, Alpha-59) rows. They are `profile: pipeline` and `install: tool`, fetched with
  `stack.py fetch` and their sha256 recorded (082a2fb7…, 2826037d…, 562280d8…). The licences are taken from the
  archive: CC BY-NC-SA 4.0, and MPL 1.1 for the exes. `data/sourcing-register.json` has three rows.
- `infra/gpu-box/lod.sh` (build VM): `tools` lays the rows under C:\argonia\tools\<id>; `survey <tool>` dumps a
  tool's windows; `run [prepare terrain texgen dyndolod collect]`; `still <tag>` takes the vantage still at the
  highest ground within 8 cells of Claywater (cell -53,3, 440 m, read from the LAND shards).
- `infra/gpu-box/lod.ps1` (machine): each step writes `metrics/<step>.json` (wall time, peak working set of the tool
  and its LODGen and Texconv processes, lowest free RAM).
- `stack.py` and `stack.ps1` (outside the brief's paths, needed for its item 2c): the MO2 mod
  "Argonia LOD (generated)" is always in the profile, never pushed, and counted as machine-made by verify.
- `docs/research/journals/lod.md`: the flags and the blocker.

## Blocker for headless use (named)
None of xLODGen, TexGen or DynDOLOD has an unattended mode. `-sse -autoload -o: -d: -p: -m:` cover the paths and
skip the plugin list. The worldspace, the preset and Start/OK/Generate are GUI only: xEdit 4.1.6 calls
`mniNavGenerateLODClick` with an unconditional ShowModal, and dyndolod.info's Command Line Argument page lists paths
only. lod.ps1 drives these dialogs by window messages in the desktop session. The control captions are unproven
until the survey runs. **Open call for the planner:** does message-driven dialog control meet "no UI clicks"?

## Not done (owed in game-8's slot)
- game-8 holds argonia-play for about 3-4 h more and will message when the GPU lock is free. In that slot:
  `lod.sh tools`, then `lod.sh survey` for each tool, then `lod.sh still without`, then
  `job_guard.sh run --gpu lod -- infra/gpu-box/lod.sh run`, then `lod.sh still with`, a reader on the two stills,
  installer/steps/lod.md with the measured time and RAM, and the brief's §c Outcome.
- The PowerShell has not been parsed yet (no pwsh on the build VM): parse it on the machine first.
- `make check` not yet run. Run so far: `make guard` and test_combat_records (6 passed), both on the manifest.
