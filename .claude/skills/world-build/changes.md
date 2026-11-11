# What a change makes stale

The stages, in order: `tools`, `scope`, `regions`, `db`, `terrain`, `needs`, `water`, `db-water`, `land`, `relief`,
`landcover`, `cells`, `landings`, `place`, `paint`, `mist`, `atmosphere`, `height-fog`, `navmesh`, `map`, `esm`,
`readback`, `upload`. `tools/newworld/rebuild.sh plan` prints the order with what each stage waits for, and is the
authority on what is stale; this table says what to expect and what follows on the other machines.

"Runs" means the stage is stale by the change itself. "Follows" means it runs only if a stage before it changes
what it reads: a stage whose inputs come out the same is skipped. "Left alone" stages are current and do not run.
`db-water` runs whenever `db` does, and `readback` runs with any edit to a Python tool under `tools/newworld/` or
`tools/navmesh/`: the rows leave both out.

Two things decide how far a change reaches. A terrain build whose heightmap comes out the same bytes is the same
build and keeps its id, so the stages after it are skipped. The land shards, the landcover, the placed refs and the
ground paint are built again whenever their stage runs, under a new key: every stage after one of them runs too.

## The ground

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Region relief or landforms | `newworld/sources/region_relief.json`, `tools/newworld/terrain_*.py` | `terrain`, and each stage that reads the edited module (`needs` and `water` for `terrain_relief.py`; `water`, `landcover`, `cells` and `paint` for `terrain.py`) | every stage after it but `atmosphere` | `tools`, `scope`, `regions`, `db`, `atmosphere` | the whole LOD; the deploy; every built place (held, so `seating` moves nothing unless its row's build changes; ground bundle, build, check) |
| Scope (how far the world reaches) | `tools/newworld/tiles.py` | `scope`, `regions`, `db`, `terrain` | every stage after | `tools` | as relief; the map's pan box moves with it |
| The source map's water | the map picture's reading: `python3 -m tools.newworld.raster` | `db`, `terrain`, `water` | every stage after | `tools`, `scope`, `regions` | as relief. The waterline moves: `water` stays red until the owner accepts the classification (the skill's section 2) |
| An owner's water edit from the Atlas | the pull, below | `db`, `terrain`, `water` | every stage after | `tools`, `scope`, `regions` | as relief; republish the Atlas |
| Water kinds' rules | `tools/newworld/water_kinds.py` | `water`, `cells` | `landcover`, then `landings`, `place`, `paint`, `mist`, `height-fog`, `navmesh`, `map`, `esm`, `upload` | `terrain`, `needs`, `land`, `relief`, `atmosphere` | if `landcover` ran: the whole LOD, the deploy, each built place's ground bundle and `clearance`; else the deploy alone. `--accept` only on the owner's word |
| Roads | `newworld/sources/road_corrections.json`, then `python3 -m tools.newworld.roads` | `db`, `terrain` | every stage after | `tools`, `scope`, `regions` | as relief |
| A place added or moved, its size or its terrain needs | its research record (the skill `place-research`) | `db` | `terrain` and every stage after, when its position, footprint or needs changed; else only the stages that read the columns that changed (`landings`, `place`, `navmesh`, `map` for a name, a kind or a rank) | the rest | as relief when the terrain ran; else the deploy if `esm` ran |
| A place's words, people, stock or wealth | its sources; a built place's `people.jsonl` and `place.json` | `db` | the stages that read the database, each skipped at its turn: the columns they read are the same | every other stage | nothing |

The owner's water edits are pulled, never typed: list the Atlas's `water_edits` and `water_paint` collections
with the ArtifactData tool into a folder, then `python3 -m tools.newworld.water_overrides_pull <folder>`
(`tools/newworld/water_overrides_pull.py` has the steps). Pull on the build the Atlas was published from.

## What dresses the ground

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Ground materials or painting rules | `tools/newworld/world/texture.py`, `roadpaint.py` | `paint` | `esm`, `upload` | everything before `paint`; `place`, `mist`, `navmesh`, `map` | the terrain LOD's textures; the deploy; each built place's ground bundle and build (it reads the world's ground records by name) |
| The paint's check | `tools/newworld/world/texcheck.py` | `paint`'s check alone: the shards stand | nothing | all else | nothing |
| Flora sets | `newworld/sources/flora/` | `db` | `place`, then `navmesh`, `mist`, `map`, `esm`, `upload` | `terrain` to `cells`, `paint`, `atmosphere` | tree and object LOD (not terrain LOD); the deploy; each built place's `clearance` |
| Placement rules | `tools/newworld/place/place.py`, `texsets.py` | `place` | `navmesh` (it is cut round the placed objects), `mist`, `map`, `esm`, `upload` | as flora sets | as flora sets |
| The placement's check | `tools/newworld/place/checks.py` | `place`'s check alone: the refs stand | nothing | all else | nothing |
| Navmesh parameters | `tools/navmesh/*.py`, `tools/navmesh/ArgoniaNav/` | `navmesh` (and `tools` for the C#; and `place` for `esm.py`, `meshes.py`, `placed.py` and `bsa.py`, which the placement reads the models through) | `esm`, `upload` | every other stage | the deploy; each built place's build and check (its navmesh joins the world's) |
| The laid mod stack (a mod added, taken out, reordered or changed) | `mods/dependencies.json`, staged | `place`, `navmesh`, `map`, `esm`; `paint`'s check alone | `mist`, `upload` | `terrain` to `landings`, `atmosphere`, `height-fog` | tree and object LOD; the deploy of the world file and the stack; each built place's build |

## Water's look, air, mist

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Water records' look or flow | `tools/newworld/world/water_types.py`, `tools/ArgoniaPlugin/WaterBlend.cs` | `cells` for the Python; `tools` and `esm` for the C# | `landings`, `mist`, `navmesh`, `map`, `esm`, `upload` | `terrain` to `landcover`, `place`, `paint` | the deploy; each built place's build (over the new world file) |
| Atmosphere classes or weathers | `newworld/sources/atmosphere/`, `tools/newworld/atmosphere.py` | `db`, `atmosphere`, `mist` (and `height-fog` for `atmosphere.py`) | `height-fog`, `navmesh`, `map`, `esm`, `upload` | every ground stage, `paint` | the deploy of the world file and the stack; each built place's ground bundle (the studio's night view reads the climate) |
| Mist | `tools/newworld/world/mist.py` | `mist`, `height-fog` | `navmesh`, `map`, `esm`, `upload` | everything before `mist`, `paint` | the deploy |
| Community Shaders settings | `tools/newworld/atmosphere_cs.py` | `height-fog` | nothing | `esm` and every stage before it | the stack's deploy only: the world file is unchanged |

## The map, and tools

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Map data, teleports | `tools/newworld/world/mapdata.py`, `tools/newworld/teleports.py` | `map`, and `landings` for `teleports.py` | `esm` (the map is applied; the file is not written again), `upload` | every stage before `map` | the deploy; the walk list's teleports if names changed |
| The LOD plan | `tools/newworld/world/lodplan.py`, `lod_models.json` | `map` | `esm`, `upload` | every stage before `map` | tree and object LOD; the deploy |
| A built place's exterior or land patches | `newworld/places/<id>/` (the skill `place-build`) | `landings`, `map` | `esm`, `readback`, `upload` | every other stage | the deploy |
| The world file's writer | `tools/ArgoniaPlugin/NewWorld*.cs`, `WaterBlend.cs`, `ForeignCopy.cs`, `WaterStudy.cs`, `tools/newworld/world/world.sh` | `tools` for the C#, and the stage that reads the edited file: `esm` (the writer, the map, the navmesh records, water, copied records, `world.sh`), `atmosphere` (`NewWorldAtmosphere.cs`), `readback` (`NewWorldVerify.cs`, `WaterStudy.cs`) | `readback`, `upload` after `esm` | every shard stage | the deploy if `esm` ran |
| A tool or script fix that changes no output | the tool | the stage that reads the file | nothing, when its output is the same bytes; every stage after it, when the stage is `land`, `landcover`, `place` or `paint` | all else | nothing, or as the row of the stage that was built again |
| The read-back | `tools/newworld/verify.py` | `readback`, `relief` | nothing | all else | nothing |

A tool fix that should change nothing is proved by the plan and the run together: the plan shows its one stage
stale and the rest following, and the run's summary shows every following stage skipped. If a following stage
runs, the fix changed an output: read the diff before going on. A fix to `world/land.py`, `landcover.py`,
`place/place.py` or `world/texture.py`, or to a file one of them reads, is the exception: plan it as a rebuild of
everything after that stage, and put what is not the rule itself in another file.
