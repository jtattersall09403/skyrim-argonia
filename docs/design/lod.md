# The new world's LOD: how it is built

What the player sees beyond the loaded cells of ArgoniaBlackMarsh, and the world map drawn from it. The LOD is a
derived build output (decision 0014): made on the play machine from the world file, laid in the NewWorld profile,
archived in the private bucket, never committed.

## The rule of the world

The LOD is built for our worldspace only, never for any other world in the load order (owner, 2026-11-11). Every run
proves it four ways, and stops at the first that fails:

- xLODGen's world list: only ArgoniaBlackMarsh is ticked (`Pick-World`), and the step stops the moment a folder of
  another world appears under its output (`Assert-Terrain-Ours`).
- DynDOLOD's preset (`Edit Scripts\DynDOLOD\Presets\DynDOLOD_SSE_Default.ini`): written before every run with our
  world at 1 and every other at 0 (`Set-DynDOLOD-Worlds`); the preflight writes it the same way and reads it back.
- DynDOLOD's logs: the step stops when a `LODGen_SSE_<world>_log.txt` of another world is written (`Assert-Only-Ours`).
- collect: files of any other world in an output folder are dropped before the mod is laid.

## What gets LOD, by which mechanism, and why

`tools/newworld/world/lodplan.py` decides per placed base and writes `out/newworld/plugin/map/lodplan.json`;
`ArgoniaPlugin nwmap apply` turns the plan into records and the files the tools read.

| what | mechanism | how it is made |
|---|---|---|
| land and water | terrain LOD (`.btr` meshes and textures at levels 4, 8, 16, 32) | xLODGen, then LODGen again with our mesh settings |
| trees: TREE bases, and STAT trees, at TexGen's size (bounds diagonal 512, height 256) | tree LOD: one billboard a base, drawn in the `.btt` files | the base is listed in `DynDOLOD_SSE_TexGen_Billboards_<plugin>.txt` (TexGen's own filter wants "tree" in the model path and would drop most of ours); a STAT carries "Has Tree LOD" (a master's static tree on an override of ours; a master's base with a texture repair is placed as our copy of it, so the flag and the billboard go to the copy). At most 256 billboards a world. |
| statics with LOD models of their own (cliffs, mountains, cairns, cypress knees: `lod_models.json`) | object LOD from those models | nothing: DynDOLOD's preset finds `<model>_lod_N.nif` by name |
| large statics without LOD models (over 512 units; rocks over 1,500), where the block budget allows | object LOD from the full model at LOD4 (cliffs also LOD8) | a mesh rule in `DynDOLOD_SSE_argonianewworldesm.ini`: `<model>,Full,Full or None,None,None,FarLOD,Unchanged,0` |
| heavy statics: the full model is past the block budget | object LOD from a derived LOD model at LOD4 | `lodmodels.py` makes `meshes\lod\<model path>_lod_0.nif`; a mesh rule names it: `<model>,Level0,None,None,None,FarLOD,Unchanged,0` |
| Skyrim's own no-LOD families (RockL/M/S, rock piles), rocks under 1,500 units, harvestable flora, small things (under 512 units), low ground cover (under 256 units high) | none: drawn in the loaded cells only, as in Skyrim | |

The block budget: DynDOLOD does not decimate, so what a rule adds to one LOD block is capped at what Tamriel's own
object LOD carries there (the 90th percentile of Skyrim's `.bto` files: 9,327 triangles a LOD4 block, 14,263 a LOD8
block). Full models are taken largest first; a model that would carry a block past the budget is heavy. A heavy
model's LOD model gets a triangle target: Skyrim's own share of the full model (0.137, the median of its level-0 LOD
models against their full models), lowered until the model's densest block fits the budget beside everything already
there; under 12 triangles the model gets none.

DynDOLOD's rules, as they bear on the plan: rules apply top to bottom and the first match wins; a plugin's rule file
(`Data\DynDOLOD\DynDOLOD_SSE_<plugin, letters and digits>.ini`, section `[Skyrim LODGen]`) is listed ahead of the
preset's; a `plugin;form id` mask names a reference, never a base, so ours are mesh masks; billboards are keyed by
plugin and form id, so ours are made from our own records.

## Derived LOD models

Skyrim's native far-off shape of a static is a LOD model: a low-triangle copy of the shape with the same textures,
named `<model>_lod_0.nif` (and `_lod_1`, `_lod_2` for the farther levels), anywhere under `meshes\`; DynDOLOD scans
for the name, merges the model into each block's `.bto` and its textures into the atlas, and never decimates
(dyndolod.info, Mod-Authors and Help/Object-LOD). The game reads only the `.bto`, so the LOD models are needed while
DynDOLOD runs and at no other time.

`python -m tools.newworld.world.lodmodels build` derives one for each model `lodplan.json` gives a target
(`lod_targets`), into `out/newworld/lodmodels/` (a manifest and a Data-shaped `meshes\` tree):

1. The full model is read with nifdump (nifly). Its drawn shapes (not hidden, not skinned, lit by a
   BSLightingShaderProperty, textured) are baked into the root's space.
2. Each shape is simplified by quadric edge collapse (fast-simplification) on its position-welded surface, so a UV
   seam cannot open; the target is shared between the shapes by area.
3. Every vertex of the result is one of the full model's own: the position of the source vertex nearest the
   collapsed point, the UV, normal and colour of a source vertex in the same UV island. The bounds cannot grow and no
   UV leaves the source's range, so DynDOLOD treats the textures as it would the full model's.
4. `niflod` (tools/newworld/niflod, built against nifly) writes the nif as Skyrim's own LOD models are laid out,
   measured on 28 `*_lod_*.nif` of Skyrim - Meshes: a BSFadeNode root; BSTriShape children, each with a
   BSLightingShaderProperty of type 0 and a BSShaderTextureSet of diffuse and normal map; shader flags
   0x80400300 and 0x8001 (0x20 with vertex colours, 0x10 two-sided); an alpha property only for an alpha test
   (LOD has no blending and tests at 128); no collision, no extra data, no other node.

A model is kept only when every check on the written file passes; otherwise it is not in the manifest and its
bases stay without LOD, with the reason in the manifest's `failed` and in `lodplan.json`:

- it reads back with both readers (nifdump and `niflod --info`), which count the same triangles;
- it has triangles, and no more than its target;
- root and blocks are the layout above;
- its bounds lie inside the source's, and no side falls short of the source's by more than a tenth of that axis's
  extent (or 8 units);
- no UV leaves the source's range for that texture;
- every texture it names is in the profile.

After a DynDOLOD run, `lodplan coverage` proves from DynDOLOD's own export that each such base was drawn from its
derived model.

Each model is keyed on the full model's bytes, the target, the maker's version and niflod; a rerun makes only what
changed. `lod.sh send` lays the folder on the machine (`C:\argonia\lod\lodmodels`) when its key changed; the
dyndolod step links it into Data; `lod.sh archive` stores it beside the LOD.

What decides whether a heavy model gets one is the density of its refs, not the tool: where a block holds hundreds
of logs and stumps, the budget leaves each a dozen triangles, and no faithful shape exists at that count. Those
bases stay without LOD.

## The steps

`infra/gpu-box/lod.sh` drives everything from the build VM; `lod.ps1` is the machine's half. The three tools have no
unattended mode, so each is driven by window messages in the desktop session; an unknown pop-up stops the step.

| step | where | what it does | reads (its key) |
|---|---|---|---|
| map | build VM | `mapdata.py build` (map box, markers, the `.lod` file, teleports, the plan), `lodmodels.py build`, the plan again, `nwmap apply` (records, billboard and rule files), `nwmap check` | not keyed: seconds |
| preflight | both | every check that needs no long step (below) | |
| prepare | machine | the NewWorld profile laid fresh with no LOD of ours; the `.lod` into Data; DynDOLOD Resources linked into Data; the outputs of the steps that stand kept and linked into Data again, the others cleared | runs when a step will |
| terrain | machine | xLODGen terrain LOD for our world (save point `terrain-tool`); then LODGen again on xLODGen's own input file with `lod-settings.json`'s mesh settings (sheson's recipe: LOD4 quality 4 with protected cell borders; LOD8/16/32 quality 6/8/10 with Optimize Unseen 550), replacing the meshes and keeping the textures | from the ESM: the world's land and water fields, every LAND, every exterior cell's grid, water height and water type, LTEX and TXST; the `.lod`; the xLODGen archive; `terrain.tool` for xLODGen's run, `terrain.post` for our pass |
| texgen | machine | TexGen: LOD textures and the billboards, our billboard lists laid in `Data\DynDOLOD\` first (save point `texgen-tool`); then every planned billboard checked by form id | the billboard files; the ESM's STAT and TREE records; the DynDOLOD and Resources archives; `texgen.tool` for TexGen's run, `texgen.post` for our pass |
| dyndolod | machine | DynDOLOD (preset Medium): object and tree LOD, with our rule file and the derived LOD models in Data. Static LOD only: `Dynamic LOD`, `Occlusion data` and `Terrain underside` are unticked (`lod-settings.json`), since only DynDOLOD's own plugins use what they make and this job enables none | the whole ESM; the billboard and rule files; the LOD models' key; the terrain and texgen keys (it culls under the terrain LOD and reads TexGen's textures); the `dyndolod` settings; the preset; the DynDOLOD and Resources archives |
| collect | machine | Resources, TexGen's, the terrain's and DynDOLOD's outputs into the derived mod folder; the profile laid again with it | skipped when the mod already holds the three steps' keys |
| check | both | every expected terrain LOD file per level (`mapdata.py check`), then `lodplan.py coverage` | |
| archive | build VM | the mod folder and the LOD models to the private bucket | the three keys |

What the terrain mesh settings do, read from the rewritten `.btr` (the second pass rewrites every one: 2,484 / 672 /
195 / 56 at levels 4 / 8 / 16 / 32 in 82 s): LOD water is two triangles for each cell that holds water, at the
water height. At LOD8, 16 and 32 (Optimize Unseen 550) land more than 550 units under the water is not drawn as
land: an all-sea block's land becomes one coarse sheet (640 triangles) pushed far below (7,600 to 9,800 units
down), and in a shore block no land triangle is left lying wholly deeper than 550 under. Land less than 550 under
the water keeps its shape at every level, and LOD4 keeps everything. So the setting clears the deep sea floor from
under the far water and off the map; it does nothing for marsh land a few units above or below the water, whose
far-off flicker against the water plane is a matter of the land's relief at the waterline.

Save points. A long tool run's output is marked the moment the tool has finished, before any pass or check of
ours runs on it, so a fault in our own code never costs the tool's run again:

| save point | marked when | what runs after it, alone and again at will |
|---|---|---|
| `terrain-tool` | xLODGen says it has finished (about 34 minutes) | our pass: the file counts, the world rule, the LODGen mesh pass from xLODGen's kept input file (82 s), the link into Data; then `terrain` is marked |
| `texgen-tool` | TexGen says it has completed (about 6 minutes) | our pass: every planned billboard is there by form id, the link into Data; then `texgen` is marked |
| `dyndolod` | DynDOLOD's finish line (about 15 to 30 minutes) | leaving the tool, collect, check, coverage, archive |

`prepare` never deletes an output whose marker is one of the keys wanted now. The settings of a tool run and of our
pass over it are separate sections of `lod-settings.json` (`tool`, `post`), each with its own `rev`, and each save
point is keyed on its own section: a change to a pass reruns that pass, never the tool before it.

What the tools give no handle for, so a fault inside costs that tool's whole run: xLODGen's terrain run and
DynDOLOD's run are each one pass driven through one window; neither has been split into kept pieces here.

Keys (`tools/newworld/world/lodkeys.py`, shown by `lod.sh keys`): each save point's key is what it truly reads, so a
change reruns only what it reaches. A change to placed references alone (places built) reruns dyndolod and
leaves terrain and texgen; a changed billboard list or tree base reruns texgen and dyndolod; changed land or water
reruns terrain and dyndolod. The key of a finished step lives on the machine beside its output
(`C:\argonia\lod\out\<step>.key`, removed when the step starts, written when it ends well), so a step is skipped
only when the output that is really there was made for the inputs wanted now. `lod.ps1`'s own text is in no key: a
fix to how a window is driven reruns nothing. Each step's settings are in `infra/gpu-box/lod-settings.json`; change a
setting, or raise the step's `rev` when a code change alters what the step writes, and that step runs again.

## Before a run: preflight

`infra/gpu-box/lod.sh preflight` (after `lod.sh map`; the stage runs it too). One `FAULT ...` line per fault, exit 1 on
any, written to `out/newworld/lod/preflight.txt`:

- `nwmap check`: the map, the Has-Tree-LOD flags, the billboard files and the rule file against the world file;
- `lodplan preflight`: the plan is this build's and is what the plan builds to now; the billboard files list
  exactly the planned trees (256 at most); the rule file names exactly the planned models, each drawn as planned;
  every planned model is in the profile; every derived LOD model is built, and no other placed model shares its
  file name (DynDOLOD pairs by file name);
- the tools fetched and at their pinned hashes (`lod-tools.json`), on the build VM and on the machine;
- the ESM, the `.lod`, the plan files and the LOD models sent, and the machine's copies hashed against ours;
- on the machine: `pscheck.ps1` over `lod.ps1` and `stack.ps1` (parser errors; a function-local name that hides a
  script-scope one, since PowerShell names are case-blind; one name under two spellings; `.ExitCode` read from a
  process whose handle was never taken; PSScriptAnalyzer's errors); no tool or game still running; 30 GB free on
  C:; 8 GB of memory free; DynDOLOD's preset holding our world alone.

## The run

```
infra/gpu-box/run.sh up
infra/gpu-box/lod.sh map
infra/gpu-box/lod.sh preflight
NW_LOD=1 tooling/job_guard.sh run --gpu nw-lod -- infra/gpu-box/lod.sh stage
tooling/job_guard.sh wait nw-lod
infra/gpu-box/run.sh stop
```

A stopped or failed run is started again with the same command: the steps that finished are skipped by their keys.
`LOD_FORCE="texgen dyndolod"` runs the named steps, tool and all, whatever their keys.

After places are built, only the object and tree LOD change: the same commands; terrain is skipped by its key.

## After a run: what proves it

- `out/newworld/lod/check.txt`: every expected `.btr` and texture per level found; `lodplan coverage`: every base
  planned for a billboard has one by name, every base planned for object LOD is in DynDOLOD's export, drawn from
  the model planned (its own LOD models, the full model, or the derived one), and every rule of ours matched
  references. Exit 1 on any miss.
- `out/newworld/lod/logs/`: each step's log, the tools' message panes, DynDOLOD's `BillboardsUsed` and `LODGen
  export`; `out/newworld/lod/metrics/`: seconds and peak memory per step; `timings.txt`.
- `tools/newworld/verify.py`'s `lod` section reads the same files into the world's read-back.

The owner judges the look in the walk.
