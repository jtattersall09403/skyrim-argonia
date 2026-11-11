# What a change makes stale

The stages, in order: `tools`, `scope`, `regions`, `db`, `terrain`, `needs`, `water`, `db-water`, `land`, `relief`,
`landcover`, `cells`, `landings`, `place`, `paint`, `mist`, `atmosphere`, `height-fog`, `navmesh`, `map`, `esm`,
`readback`, `upload`. `tools/newworld/rebuild.sh plan` prints the order with what each stage waits for, and is the
authority on what is stale; this table says what to expect and what follows on the other machines.

"Runs" means the stage is stale by the change itself. "Follows" means it runs only if a stage before it changes
what it reads: a stage whose inputs come out the same is skipped. "Left alone" stages are current and do not run.

## The ground

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Region relief or landforms | `newworld/sources/region_relief.json`, `tools/newworld/terrain_*.py` | `terrain` (and any stage that reads the edited module) | every stage after it but `atmosphere` | `tools`, `scope`, `regions`, `db`, `atmosphere` | the whole LOD; the deploy; every built place (held, so `seating` moves nothing unless its row's build changes; ground bundle, build, check) |
| Scope (how far the world reaches) | `tools/newworld/tiles.py` | `scope` | `regions`, `db`, `terrain` and every stage after | `tools` | as relief; the map's pan box moves with it |
| The source map's water | the map picture's reading: `python3 -m tools.newworld.raster` | `db`, `terrain`, `water` | every stage after | `tools`, `scope`, `regions` | as relief. The waterline moves: `water` stays red until the owner accepts the classification (the skill's section 2) |
| An owner's water edit from the Atlas | the pull, below | `db`, `terrain`, `water` | every stage after | `tools`, `scope`, `regions`, `atmosphere` | as relief; republish the Atlas |
| Water kinds' rules | `tools/newworld/water_kinds.py` | `water`, `cells` | `db-water`, `landcover`, then `landings`, `place`, `paint`, `navmesh`, `mist`, `height-fog`, `map`, `esm`, `readback`, `upload` | `terrain`, `needs`, `land`, `relief`, `atmosphere` | if `landcover` ran: the whole LOD, the deploy, each built place's ground bundle and `clearance`; else the deploy alone. `--accept` only on the owner's word |
| Roads | `newworld/sources/road_corrections.json`, then `python3 -m tools.newworld.roads` | `db`, `terrain` | every stage after | `tools`, `scope`, `regions` | as relief |
| A place added or moved, its size or its terrain needs | its research record (the skill `place-research`) | `db` | `terrain` and every stage after, when its position, footprint or needs changed; else `land`, `landings`, `place`, `navmesh`, `map` only | the rest | as relief when the terrain ran; else the deploy if `esm` ran |
| A place's words, people, stock or wealth | its sources | `db` | the stages that read the database, each skipped at its turn: the tables they read are the same | every other stage | nothing |

The owner's water edits are pulled, never typed: list the Atlas's `water_edits` and `water_paint` collections
with the ArtifactData tool into a folder, then `python3 -m tools.newworld.water_overrides_pull <folder>`
(`tools/newworld/water_overrides_pull.py` has the steps). Pull on the build the Atlas was published from.

## What dresses the ground

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Ground materials or painting rules | `tools/newworld/world/texture.py`, `roadpaint.py` | `paint` | `esm`, `readback`, `upload` | everything before `paint`; `place`, `mist`, `navmesh`, `map` | the terrain LOD's textures; the deploy; each built place's ground bundle and build (it reads the world's ground records by name) |
| The paint's check | `tools/newworld/world/texcheck.py` | `paint` (its own key keeps the shards: only the check works) | nothing unless the shards change | all else | nothing |
| Flora sets | `newworld/sources/flora/` | `db` | `place`, then `navmesh`, `mist`, `map`, `esm`, `readback`, `upload` | `terrain` to `cells`, `paint`, `atmosphere` | tree and object LOD (not terrain LOD); the deploy; each built place's `clearance` |
| Placement rules | `tools/newworld/place/*.py` | `place` | `navmesh` (it is cut round the placed objects), `mist`, `map`, `esm`, `readback`, `upload` | as flora sets | as flora sets |
| Navmesh parameters | `tools/navmesh/*.py`, `tools/navmesh/ArgoniaNav/` | `navmesh` (and `tools` for the C#) | `esm`, `readback`, `upload` | every other stage | the deploy; each built place's build and check (its navmesh joins the world's) |

## Water's look, air, mist

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Water records' look or flow | `tools/newworld/world/water_types.py`, `tools/ArgoniaPlugin/WaterBlend.cs` | `cells` for the Python; `tools` and `esm` for the C# | `landings`, `mist`, `map`, `esm`, `readback`, `upload` | `terrain` to `landcover`, `place`, `paint`, `navmesh` | the deploy; each built place's build (over the new world file) |
| Atmosphere classes or weathers | `newworld/sources/atmosphere/`, `tools/newworld/atmosphere.py` | `db`, `atmosphere`, `mist` | `height-fog`, `map`, `esm`, `readback`, `upload` | every ground stage, `paint`, `navmesh` | the deploy of the world file and the stack; each built place's ground bundle (the studio's night view reads the climate) |
| Mist | `tools/newworld/world/mist.py` | `mist`, `height-fog` | `navmesh`, `map`, `esm`, `readback`, `upload` | everything before `mist`, `paint` | the deploy |
| Community Shaders settings | `tools/newworld/atmosphere_cs.py` | `height-fog` | `readback` | `esm` and every stage before it | the stack's deploy only: the world file is unchanged |

## The map, and tools

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Map data, teleports | `tools/newworld/world/mapdata.py`, `tools/newworld/teleports.py` | `map`, `landings` | `esm` (the map is applied; the file is not written again), `readback`, `upload` | every stage before `map` | the deploy; the walk list's teleports if names changed |
| The LOD plan | `tools/newworld/world/lodplan.py`, `lod_models.json` | `map` | `esm`, `readback`, `upload` | every stage before `map` | tree and object LOD; the deploy |
| A built place's exterior or land patches | `newworld/places/<id>/` (the skill `place-build`) | `landings`, `map` | `esm`, `readback`, `upload` | every other stage | the deploy |
| The world file's writer | `tools/ArgoniaPlugin/NewWorld*.cs`, `WaterBlend.cs`, `ForeignCopy.cs`, `WaterStudy.cs` | `tools`, and the stage that reads the edited file: `esm` (the writer, the map, the navmesh records, water, copied records), `atmosphere` (`NewWorldAtmosphere.cs`), `readback` (`NewWorldVerify.cs`, `WaterStudy.cs`) | `readback`, `upload` after `esm` | every shard stage | the deploy if `esm` ran |
| A tool or script fix that changes no output | the tool | the stage that reads the file | nothing: its output is the same bytes, so every later stage is skipped | all else | nothing |
| The read-back | `tools/newworld/verify.py` | `readback` | nothing | all else | nothing |

A tool fix that should change nothing is proved by the plan and the run together: the plan shows its one stage
stale and the rest following, and the run's summary shows every following stage skipped. If a following stage
runs, the fix changed an output: read the diff before going on.
