# The new world's LOD: measurements and reasons

What the player sees beyond the loaded cells of ArgoniaBlackMarsh, and the world map drawn from it. The LOD is a
derived build output (decision 0014): made on the play machine from the world file, laid in the NewWorld profile,
archived in the private bucket, never committed. The recipe (the order of work, what a change reruns, the small
world's selftest, preflight, run, checks, deploy) is the skill `world-lod`; this file holds what was measured and
why each rule is so.

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

## The mesh settings of our terrain pass

xLODGen keeps its mesh options in its window, so its own LODGen input (`LODGen_Terrain_<world>.txt`, kept beside
the output) is rewritten with `lod-settings.json`'s `terrain.post` keys and LODGen run again on the same height
data: sheson's recipe (LOD4 quality 4 with protected cell borders; LOD8/16/32 quality 6/8/10 with Optimize Unseen
550). The meshes are replaced, the textures kept.

Read from the rewritten `.btr` (the pass rewrites every one: 2,484 / 672 / 195 / 56 at levels 4 / 8 / 16 / 32 in
82 s): LOD water is two triangles for each cell that holds water, at the water height. At LOD8, 16 and 32 land
more than 550 units under the water is not drawn as land: an all-sea block's land becomes one coarse sheet (640
triangles) pushed far below (7,600 to 9,800 units down), and in a shore block no land triangle is left lying wholly
deeper than 550 under. Land less than 550 under the water keeps its shape at every level, and LOD4 keeps
everything. So the setting clears the deep sea floor from under the far water and off the map; it does nothing for
marsh land a few units above or below the water, whose far-off flicker against the water plane is a matter of the
land's relief at the waterline.

## Keys

Each step's key (`tools/newworld/world/lodkeys.py`) is what the step truly reads, so a change reruns only what it
reaches, and the key of a finished step lives on the machine beside its output: a step is skipped only when the
output that is really there was made for the inputs wanted now. The settings of a tool run and of our pass over it
are separate sections of `lod-settings.json`, each with its own `rev`. `lod.ps1`'s text is in no output key, since
a fix to how a window is driven changes no output; it is in each step's code key (`proof`), which the small
world's selftest records and a full run asks for.

## Save points: what each tool gives, and what was proven

Measured on the small world (16 by 16 cells; `lod.sh selftest`), every comparison by sha256 of each output file:

| Tool | Handle | Source | Proven | Built |
|---|---|---|---|---|
| xLODGen | A terrain texture already in the output folder is skipped ("can be used to continue generating", its Terrain-LOD readme) | the tool's readme | A run stopped after 25 s with 290 of 340 textures written, then carried on: all 340 textures and 35 meshes the same bytes as an unstopped run's | Yes: a stopped terrain run of the same key is carried on; the newest textures (twice the thread count) and empty files are made again |
| xLODGen | Meshes are written again by every run | the tool's readme | | Nothing to keep: our own pass writes every mesh again in any case |
| LODGen (terrain) | Run again on xLODGen's kept input file | sheson's xLODGen notes | Our pass alone over the standing output: 35 meshes the same bytes, 2 s | Yes: `terrain-tool` then `terrain` |
| xLODGen | "Specific chunk" (a level and a south-west cell) makes one chunk's textures | the tool's readme; whether a chunk's bytes equal a whole run's is not documented | Not tested | No: skipping existing textures gives the same saving with no window to drive. A change to terrain or paint in some cells still makes every texture again: regenerating only the chunks a change touches needs a key per chunk and is not built |
| TexGen | None: no skip of existing files, no cache | dyndolod.info, TexGen | | No handle: a fault inside costs the run (about 3 to 6 minutes) |
| DynDOLOD | Its own pass keeps nothing part-way | dyndolod.info | | No handle: a fault inside costs the pass |
| LODGen (objects) | DynDOLOD ends by exporting the object LOD's inputs and starting LODGen on them; expert mode's "Execute LODGen" runs LODGen from that export again | dyndolod.info, Expert Mode | LODGen run on the small world's export: 27 of its 32 object LOD files differ in bytes from DynDOLOD's own run (tree LOD, textures and plugins the same) | No: not proven equal, so no save point is marked on it |
| DynDOLOD | Tree LOD and object LOD as separate runs | their boxes are separate; whether one keeps the other's output is not documented | Not tested | No |

Two faults of the tools' own state, found by the first small runs and held since by the scripts: TexGen and
DynDOLOD each open with the output path their preset file saved at the run before, whatever `-o:` says, so a run
for another folder writes into the last one's. Each preset's `OutputPath` is written before every run, and each
step fails when its tool wrote nowhere under its own folder. And TexGen refuses to start while an earlier TexGen
output is in the Data folder it reads, so the small world runs against a Data folder of its own (hard links to the
game's, without our LOD mod's files).

xLODGen's finish line can come back unreadable from its window (one small run in seven sat idle on it): the terrain
step also ends when the output has settled (files there, their count unchanged and the tool idle for 90 s).

The worst rerun after a fault or a stop: DynDOLOD (16 minutes on the whole world), or
TexGen's run (6 minutes). A stopped terrain run loses the textures being written; a fault in any pass of ours
loses that pass.

## The small world

`ArgoniaSmallWorld`: the block of cells (4, -134) to (19, -119) of the real build, cut and built by
`tools/newworld/rebuild.sh small` (the skill `world-build`), renamed for the play machine by `small play`.
Its plan holds 94 of the world's 172 billboard bases, 12 bases with LOD models of their own, 9 rule-matched
bases and one of the three derived cliff models.

| Step | Small world | Whole world |
|---|---|---|
| prepare (its own game folder: 104,650 hard links) | 52 s | 1 min |
| terrain: xLODGen, then our mesh pass (375 files) | 77 s | 34 min, then 82 s |
| texgen | 195 s | 6 min |
| dyndolod | 194 s | 16 min |
| collect | 17 s | 2 min |
| the whole selftest, preflight and checks included | 612 s | about an hour |

What is fixed in a small run: TexGen spends 98 s loading the load order and making its object textures
whatever the world holds, then 88 s on the block's 94 billboards (it renders only bases the loaded plugins hold, and
keeps none between runs); DynDOLOD's 148 s is 11 s of loading and the rest its own pass over the load order's rules.
A step proven for today's code whose output stands is skipped, so a warm run costs only the steps a change
reaches; `lod.sh`, `lod.ps1` and `pscheck.ps1` are in every step's code key, so a change to one of them runs all
three again.
What the small world cannot prove is listed in the skill `world-lod`, section 4.
