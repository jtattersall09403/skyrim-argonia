---
name: world-lod
description: Build the new world's LOD (far terrain, trees, objects, the map) on the play machine from the world file, running only the steps a change made stale, the small test world first; then check it and deploy. Holds what gets LOD by which mechanism, the rule that LOD is made for our worldspace alone, each step's key and save points, and the machine's care. Use after any world rebuild that reaches the world file, after places are built, and for any change to the LOD plan, scripts, settings or tools.
---

# Build the new world's LOD

What the player sees beyond the loaded cells of ArgoniaBlackMarsh, and the world map drawn from it. The LOD is
made on the play machine from `ArgoniaNewWorld.esm` by three tools (xLODGen, TexGen, DynDOLOD), laid in the NewWorld
profile, archived in the private bucket, never committed. One script drives it from the build VM:
`infra/gpu-box/lod.sh`; `lod.ps1` is the machine's half. A step runs only when something it reads has changed.
Measurements and reasons are in [the LOD design](../../../docs/design/lod.md).

## The order of work

| Step | What | Where |
|---|---|---|
| 1 | The world file is green, settled and on the play machine, and every built place is level and checked on it | the skill `world-build`, section 7 |
| 2 | Read which steps the change makes stale | section 3, `lod.sh keys` |
| 3 | Run the stage on the small world when a script, a setting, a tool or the plan's code changed | section 4 |
| 4 | Preflight, and mend every fault it names | section 5 |
| 5 | Run the stage once, under the job guard | section 6 |
| 6 | Read the checks | section 7 |
| 7 | The whole read-back, then the owner's walk | section 8 |

What gets LOD: section 1. The worldspace rule: section 2. Costs and the machine: section 9.

## 1. What gets LOD, and by which mechanism

`tools/newworld/world/lodplan.py` decides for each placed base and writes `out/newworld/plugin/map/lodplan.json`
(each base with its mechanism and the reason); `ArgoniaPlugin nwmap apply` turns the plan into records and the
files the tools read. Change the plan there, never in a tool's window.

| What | Mechanism | How it is made |
|---|---|---|
| Land and water | Terrain LOD: meshes and textures at levels 4, 8, 16 and 32 | xLODGen; then LODGen again on xLODGen's own input with our mesh settings (`lod-settings.json`, `terrain.post`) |
| Trees: TREE bases and static trees, at TexGen's size | Tree LOD: one billboard a base | The base is listed in our billboard file; a static tree carries "Has Tree LOD". A master's tree with a texture repair is placed as our copy, and the flag and billboard go to the copy. At most 256 billboards a world |
| Statics with LOD models of their own (cliffs, mountain trims, cairns, cypresses: `lod_models.json`) | Object LOD from those models | Nothing: DynDOLOD finds `<model>_lod_N.nif` by name |
| Large statics without LOD models, where the block budget allows | Object LOD from the full model at LOD4 (cliffs also LOD8) | A mesh rule in our rule file |
| Heavy statics: the full model is past the block budget | Object LOD from a derived LOD model at LOD4 | `lodmodels.py` derives `meshes\lod\<model>_lod_0.nif`; a mesh rule names it. A model that fails its checks is not made, and its bases get none |
| Skyrim's own no-LOD families (small rocks, rock piles), harvestable flora, things under 512 units, ground cover under 256 units high | None | Drawn in the loaded cells only, as in Skyrim |

DynDOLOD does not decimate, so what a rule adds to one LOD block is capped at what Skyrim's own object LOD carries
there. Dynamic LOD, occlusion data and the terrain underside are not made: only DynDOLOD's own plugins use them,
and none is enabled.

## 2. The worldspace rule

LOD is built for our worldspace alone, never for another world in the load order. Each run holds each tool to it
and stops at the first breach:

| Tool | Held by | Checked by |
|---|---|---|
| xLODGen | Its world list: ours ticked, Tamriel unticked | The step stops the moment a folder of another world appears under its output |
| DynDOLOD | Its preset file, written before every run with our world at 1 and every other at 0 | The preflight writes it the same way and reads it back; the step stops when a LODGen log of another world is written |
| TexGen | It has no world: it makes textures for the load order. Its preset's output path is written before every run, as DynDOLOD's is | Every planned billboard is found by form id; each tool's step fails when it wrote nowhere under its own folder |
| collect | Files of any other world in an output folder are dropped before the mod is laid | `mapdata.py check` on the laid folder's listing |

## 3. What each step reads, and what a change reruns

| Step | Where | What it does | Keyed on | Time |
|---|---|---|---|---|
| `map` | build VM | Map box, markers, the `.lod` file, teleports, the plan; the derived LOD models; the records and plan files applied to the world file and checked. While the plan and the markers stand, every apply writes the same bytes | Not keyed: seconds; each LOD model on its full model and target | under a minute |
| `prepare` | machine | The NewWorld profile laid fresh without our LOD; the outputs that stand linked into Data again | Runs when a step will | 1 min |
| `terrain` | machine | xLODGen, then our mesh pass | The ESM's land, water, cell grid and ground textures (each land texture and the texture set it names); the `.lod`; the xLODGen archive; `terrain.tool` for the tool run, `terrain.post` for our pass | 34 min, then 82 s |
| `texgen` | machine | TexGen with our billboard files, then every planned billboard checked | The billboard files; the ESM's tree and static base records; the DynDOLOD archives; `texgen.tool`, `texgen.post` | 6 min |
| `dyndolod` | machine | DynDOLOD (preset Medium) with our rule file and the derived LOD models | The whole ESM bar markers and names; the plan files; the LOD models' key; the terrain and texgen keys; the `dyndolod` settings; the preset; the archives | 16 min |
| `collect` | machine | The three outputs into the derived mod folder; the profile laid again with it | Skipped when the mod holds the three keys | 2 min |
| `check` | both | Every expected terrain LOD file a level; then the plan's coverage | | seconds |
| `archive` | build VM | The mod folder and the LOD models to the private bucket | The three keys | 2 min |

`infra/gpu-box/lod.sh keys` prints each step's key as wanted and as the machine holds it. A step whose key stands
on the machine is skipped; nothing that is current is made again. A key is read from the world file's own records
and from the settings of its step, never from a script's text or a stamp beside the file, and each step has its
own: a change reaches only the steps that read it.

| A change to | Reruns | Leaves alone |
|---|---|---|
| Placed references only (places built, plants scattered again with the same bases) | `dyndolod`, `collect` | `terrain`, `texgen` |
| A re-place or a navmesh rebuild (land, water and ground paint as they were) | `dyndolod`, `collect`; `texgen` only when a tree or static base is new or changed | `terrain`, always: every record keeps its registered form id (the skill `world-build`) |
| Edits of placed things, one thing or every thing of a base (`seat`, `drop`) (the skill `world-build`, [changes.md](../world-build/changes.md)) | `dyndolod`, `collect`, once for a session's edits; `texgen` only when an edit brings a tree or static base new to the world. Without the run an edit shows in the loaded cells and not far off: a seated or dropped tree's billboard stands where it stood | `terrain`, always |
| A new or changed tree base, or the billboard plan | `texgen`, `dyndolod`, `collect` | `terrain` |
| A new or changed static base that is no tree | `texgen` (it reads every static base record), `dyndolod`, `collect` | `terrain` |
| Terrain, water or ground paint, in any cells | `terrain` (its textures are made again only for what is missing: section 6), `dyndolod`, `collect` | `texgen` |
| The mesh settings of our pass (`terrain.post`) | Our mesh pass alone (82 s), `dyndolod`, `collect` | xLODGen's run, `texgen` |
| A rule, a derived LOD model, the DynDOLOD settings or preset | `dyndolod`, `collect` | `terrain`, `texgen` |
| Map markers, teleports, cell names, the map box | Nothing on the machine: `map` alone | every machine step |
| A fix to how `lod.ps1` or `lod.sh` drives a window or a step | Nothing by key. The small world first (section 4); raise the step's `rev` in `lod-settings.json` only when the fix changes what the step writes | every output |
| The plan's code or list, the plan coming out the same (`lodplan.py`, `lod_models.json`, `NewWorldMap.cs`) | Nothing by key. The small world first (section 4) | every output |
| A tool update (`lod-tools.json`) | That tool's steps and what stands on them: xLODGen `terrain` and `dyndolod`; DynDOLOD or its Resources `texgen` and `dyndolod` | the other tool's step |

## 4. The small world first

    tools/newworld/rebuild.sh small
    tooling/job_guard.sh run --gpu nw-lod-selftest -- infra/gpu-box/lod.sh selftest
    tooling/job_guard.sh wait nw-lod-selftest

The small world is one 16 by 16 cell block of the real build with one of everything the plan has a rule for,
written by the real writer (the skill `world-build`, section 5). `lod.sh selftest` runs this whole stage on it
(preflight, prepare, terrain with the mesh pass, TexGen, DynDOLOD with the rules and LOD models, collect, check,
coverage) under its own names: the world `ArgoniaSmallWorld` in `ArgoniaSmallWorld.esm`, `out/newworld-small/lod/`
here, `C:\argonia\lod-small\` there, with a game folder of its own that the tools are pointed at (hard links to
the game's Data without our LOD mod). It never lays the profile and never writes the game's Data or the real
LOD's folders and keys. About ten minutes from nothing; a step proven for today's code is skipped.

- Run it whenever `lod.sh`, `lod.ps1`, `pscheck.ps1`, `lodkeys.py`, the plan's code (`mapdata.py`, `lodplan.py`,
  `lodmodels.py`, `niflod.cpp`, `lod_models.json`, `NewWorldMap.cs`), `lod-settings.json` or a tool changed. Each
  step that ends green is recorded on the machine with its code key; `lod.sh stage` refuses a step that will run
  and whose code key is not recorded. A step whose code stands is skipped here and asks for nothing there.
  `lod.sh keys` prints each step's code key beside the one proven.
- Mend what it finds and run it again: a fault costs minutes here.
- `lod.sh selftest pass` runs our mesh pass alone over the standing terrain output;
  `LOD_FORCE=terrain SELFTEST_STOP=<seconds> lod.sh selftest prepare terrain` stops the terrain tool part-way, and
  `lod.sh selftest prepare terrain` then carries the run on.

What the small world cannot prove, so what a full run still risks: memory and time at the province's reference
counts (DynDOLOD's own pass above all); the limits a whole world reaches and a block does not (256 billboards, the
object atlas's size, the block budget where placing is densest); the bases, rules and LOD models of ground the
block does not hold (its plan carries about half the world's tree bases and one of the three derived cliff
models); the terrain at sea, at the province's edge and on the map.

## 5. Preflight

    infra/gpu-box/run.sh up
    infra/gpu-box/lod.sh map
    infra/gpu-box/lod.sh preflight

One `FAULT ...` line a fault, exit 1 on any, kept in `out/newworld/lod/preflight.txt`. It proves, before any long
step:

- the world file is settled (`tools/newworld/rebuild.sh settled` exits 0; the skill `world-build`, section 7,
  step 3), so the file cannot change under the run;
- the map and plan against the world file; the plan is this build's, the billboard files list the planned
  trees and no others, the rule file names the planned models and no others, every planned and derived model is
  there;
- the tools are at their pinned hashes on both machines; the machine holds the world file, the `.lod`, the plan
  files and the LOD models built here;
- the machine's scripts pass the script checker (`pscheck.ps1`: a parse error, a function's variable that hides
  one of the script's own under another case, an exit code read from a process whose handle was never taken), and
  every step has its code;
- no tool or game is running; disk and memory are enough; DynDOLOD's preset holds our world alone;
- every step that will run was proven on the small world.

A fault about the machine quotes what the machine printed, in place of the line the preflight wanted. A machine
that answered with no report at all gives one fault that says so. Mend every fault and run the preflight again: no
long step starts on a red preflight.

## 6. Run

    NW_LOD=1 tooling/job_guard.sh run --gpu nw-lod -- infra/gpu-box/lod.sh stage
    tooling/job_guard.sh wait nw-lod

- Run it from the main tree. `stage` runs `map`, the preflight, the stale machine steps, `check` and `archive`.
  Never stop a `--gpu` job with `job_guard.sh stop`: it stops the machine.
- No lane that changes a source of the world file is started or landed while the stage runs.
- A stopped or failed run is started again with the same command. Finished steps are skipped by their keys.
- Save points inside a step, each marked the moment it is whole:

| Save point | Marked when | What is lost by a fault after it |
|---|---|---|
| each terrain texture | xLODGen has written it | Nothing: a stopped terrain run of the same key is carried on, the newest textures made again, the rest skipped; meshes are written again (seconds) |
| `terrain-tool` | xLODGen says it has finished | Our mesh pass, the counts and the link: 82 s |
| `texgen-tool` | TexGen says it has completed | Our billboard check and the link: seconds |
| `dyndolod` | DynDOLOD's finish line | Leaving the tool, collect, check, coverage, archive |

- TexGen and DynDOLOD keep nothing part-way: a fault inside either costs that run again (6 and 16 minutes).
  That is the worst rerun.
- `LOD_FORCE="texgen dyndolod"` runs the named steps, tool and all, whatever their keys. Use it only when an output
  is wrong for a reason no key reads, and say why in the commit message.

## 7. The checks after

- `out/newworld/lod/check.txt`: every expected terrain mesh and texture a level is in the laid folder; then the
  coverage: every base planned for a billboard has one, every base planned for object LOD is in DynDOLOD's export
  drawn from the model planned, every rule of ours matched references. Exit 1 on any miss.
- `out/newworld/lod/logs/`: each step's log and the tools' message panes; `metrics/`: seconds and peak memory.
- A miss is mended at its cause: the plan (`lodplan.py`), a model, a rule, a setting. Then the same command runs
  the one step that reads the mend.
- A `note:` line of the coverage names a model DynDOLOD found LOD models of that the list lacks: add it to
  `tools/newworld/world/lod_models.json` in its sorted place, so the plan gives its bases no rule of ours.
- Findings beyond the checks are weighed by what the player would notice (the skill `world-build`, section 6).

## 8. Deploy, read-back, walk

- The world file is laid by `lod.sh send` (the preflight and the stage run it): `C:\argonia\ours\newworld\`, which
  the NewWorld profile alone loads. `collect` lays the profile again with the LOD folder. The place layer follows
  with `infra/gpu-box/places_deploy.sh`; a changed mod stack with `python3 infra/gpu-box/stack.py stage` and its push.
- Then the whole read-back on the build VM: `python3 -m tools.newworld.verify` (the `lod` and `deploy` rows read
  this stage's files and the machine's copy of the world file). It passes in full before the owner is asked to walk.
- The owner judges the look in the walk; what a file proves is never asked of the owner.

## 9. Costs, and the machine's care

- The play machine costs about $0.80 an hour while it runs and stops itself when idle. Start it for this stage
  (`infra/gpu-box/run.sh up`), run every machine step as a job under `tooling/job_guard.sh run --gpu`, and stop it
  when the stage and the deploy are done (`infra/gpu-box/run.sh stop`). Never leave it waiting on a build that has
  not finished on the build VM.
- A whole LOD is about an hour of machine time; object and tree LOD alone (after places) about 20 minutes; the
  selftest ten minutes.
- The three tools have no unattended mode: each is driven by window messages in the desktop session. An unknown
  pop-up stops the step and is named in its log; add it to the known list in `lod.ps1` with its answer only when the
  tool's documentation gives the answer.
