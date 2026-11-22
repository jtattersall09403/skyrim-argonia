# What a change makes stale

The stages, in order: `tools`, `scope`, `regions`, `db`, `terrain`, `needs`, `water`, `db-water`, `land`, `relief`,
`landcover`, `cells`, `landings`, `place`, `edits`, `paint`, `ground-patch`, `mist`, `atmosphere`, `height-fog`,
`navmesh`, `map`, `ecology`, `dressing`, `smithing`, `esm`, `readback`, `upload`. `tools/newworld/rebuild.sh plan`
prints the order with what each stage waits for, and is the authority on what is stale; this table says what to
expect and what follows on the other machines.

`scope`, `regions`, `terrain`, `water`, `land`, `landcover`, `cells` and `paint` are the province's ground: the fixed
base. They are never stale and never run; no row below runs them. A change that would once have reshaped the
province is a local patch now (the first table), or a new base the owner alone can ask for (the skill, section 11).

"Runs" means the stage is stale by the change itself. "Follows" means it runs only if a stage before it changes
what it reads: a stage whose inputs come out the same is skipped. "Left alone" stages are current and do not run.
`db-water` runs whenever `db` does, and `readback` runs with any edit to a Python tool under `tools/newworld/` or
`tools/navmesh/`: the rows leave both out. The placed refs are built again whenever their stage runs, under a new
key: every stage after them runs too.

Each stage is keyed on what it reads, and of a built place's files the world reads fields, never the file: the
database who gives which promise (`people.jsonl` `id`, `role` and `services`' `seq`) and the stations found
(`place.json` `stations.found`). A place build that changes none of them leaves every stage current.

Of the form id table (`tools/newworld/idspace.py`) a stage reads only the rows it allocates from (`idspace.py#row,row`):
placement the placed and navmesh rows, the edits the added row besides, the ecology its own. A range added or moved
for another stage leaves every other stage current.

A built place, in its turn, stands on records of the world file, never on the file's bytes: the LAND, the navmesh
and the placed references of the cells it read (the ground bundle its whole reach, the build its own cells and the
ring its navmesh joins), the bases those references name, the worldspace record, the land textures, the file's
masters and description, and the form ids of the map markers its travel lines land on. Where a row's last column
names the built places, it means those whose records the change moved: `python3 -m tools.places worldparts
<place_id>` names what moved under a place, and the run's summary lists only those places. A rewrite that moves
none (a map marker, the map box, a teleport marker, a far cell) leaves every place current.

## The ground: patches over the fixed base

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| A place's own ground (carried ground, pad, bank, sap hollow, its paint, its paths) | the place's `land.jsonl`, `paint.jsonl`, `paths.jsonl` by the skills `place-site` and `place-change`, then its build | nothing in the world rebuild: the place build lays it in the place layer over the place's cells | nothing | every stage | the place's own build and check; the deploy of the place layer |
| Ground outside any place (a road's bed, a landing, a bank a walk fault names) | a row of `newworld/sources/ground_patches.jsonl` (the skill, section 3) | `ground-patch` | `esm`, `readback`, `upload` | every other stage | the terrain LOD of the patched cells; the deploy; a built place whose cells a patch reaches (`worldparts`) |
| Roads | `newworld/sources/road_corrections.json`, then `python3 -m tools.newworld.roads` | `db` | `place`, `edits`, `navmesh` (road dressing and the road kept clear), `map`, `esm`, `upload` | the base | tree and object LOD; the deploy. A new road's ground is owed: the plan lists it, and its bed and paint are a place's path or a patch row |
| A place added or moved, its size, whether it stands on water, its terrain needs | its research record (the skill `place-research`) | `db` | `needs` (judged on the base), `landings`, `place`, `navmesh`, `map` for a position, name, kind or rank | the base | the deploy if `esm` ran. A need the base does not meet is met by the place's own ground |
| A place's words, people, stock or wealth, a region's notes | its sources; of a built place's files, who gives which promise (`people.jsonl`) and the stations found (`place.json`) | `db` | the stages that read the database, each skipped at its turn: the columns and rows they read are the same | every other stage | nothing |
| A built place built again with the same content (its ground stamp, a bed, a routine, the plan's own numbers) | `python3 -m tools.places build <place_id>` | nothing | nothing | every stage | nothing |
| Region relief, landforms, scope, the map's water, an owner's water edit, water kinds' rules | only on the owner's word: a new base (the skill, section 11) | every base stage, with the override | every stage after | `tools` | the whole LOD; the deploy; every built place (ground bundle, `seating`, build, check); republish the Atlas |

The owner's water edits are pulled, never typed: list the Atlas's `water_edits` and `water_paint` collections
with the ArtifactData tool into a folder, then `python3 -m tools.newworld.water_overrides_pull <folder>`
(`tools/newworld/water_overrides_pull.py` has the steps). They reach the world only with a new base.

## What dresses the ground

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Ground materials or painting rules | `tools/newworld/world/texture.py`; `roadpaint.py` (shared with a place's paths) | nothing: the base's paint stands; a place's paths take the rule at their next place build | nothing | every stage | each place built again after it |
| The patches' rule | `tools/newworld/world/patches.py` | `ground-patch` | `esm`, `readback`, `upload` | every other stage | as a patch row |
| Flora sets | `newworld/sources/flora/` | `db` | `place`, then `navmesh`, `mist`, `map`, `esm`, `upload` | the base, `atmosphere` | tree and object LOD (not terrain LOD); the deploy; each built place's `clearance` |
| Placement rules | `tools/newworld/place/place.py`, `texsets.py`, `audit.py` (the seating rule by the mesh) | `place` | `navmesh` (it is cut round the placed objects), `mist`, `map`, `esm`, `upload` | as flora sets | as flora sets. Run the navmesh's fast test first ([checks.md](checks.md)) |
| The placement's check | `tools/newworld/place/checks.py` | `place`'s check alone: the refs stand | nothing | all else | nothing |
| Navmesh parameters | `tools/navmesh/*.py`, `tools/navmesh/ArgoniaNav/` | `navmesh` (and `tools` for the C#; and `place` for `esm.py`, `meshes.py`, `bsa.py`, `nif.py`, `placed.py`, `solid.py`, `params.py` and `inputs.py`: the placement reads the models through the first three and keeps the road clear by each collision's blocked columns through the rest, so its refs, and with them the flora sets' row, follow; and the check of `edits` for `placed.py`, `solid.py` and `params.py`) | `esm`, `upload` | every other stage | the deploy; each built place's build and check (its navmesh joins the world's) |
| The laid mod stack (a mod added, taken out, reordered or changed) | `mods/dependencies.json`, staged | `place`, `edits`, `navmesh`, `map`, `esm` | `mist`, `upload` | the base, `landings`, `atmosphere`, `height-fog` | tree and object LOD; the deploy of the world file and the stack; each built place's build |

`place` writes the placement as the rules make it (`out/newworld/plugin/placed/flora`). `edits` applies
`newworld/sources/placed_edits.jsonl` over it into `out/newworld/plugin/refs/flora`, which every later stage reads;
nothing is placed again. An edit of one placed thing (a tree removed, a rock moved, a base swapped, a thing added):

1. List what stands there: `python3 -m tools.newworld.place refs --cell CX CY` (or `--fid HEX`, `--at X Y`).
2. Append the edit: `python3 -m tools.newworld.place edit remove|move|swap|add|restore --by <who> ...`. It
   validates the row; never write the file by hand, and never change a rule to move one thing.
3. `tools/newworld/rebuild.sh small`, then `tools/newworld/rebuild.sh plan`: it lists, for the edits waiting, the
   shard rows, the navmesh cells, the mist, the built places and the LOD they reach. Then run.
4. Gather a session's edits into one rebuild and one DynDOLOD run (the skill `world-lod`, section 3).

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| One placed thing | `python3 -m tools.newworld.place edit`, as above | `edits` | `navmesh` (the cells within reach), `map`, `esm`, `readback`, `upload`; `mist` only when a cell's count changes | `place`, and every ground stage: `terrain` to `landings`, `paint` | the deploy; `dyndolod` alone, `texgen` only for a base new to the world, never terrain LOD; a built place whose `clear.jsonl` names an edited thing or whose cells hold one (the skill `place-change`) |

After a change to the placement's rules, read the `ORPHANED` lines of the plan and of the `edits` stage: each is an
edit whose thing the rules no longer place. Answer each with a new edit or with `edit restore`.

## Water's look, air, mist

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Water records' look or flow | `tools/ArgoniaPlugin/WaterBlend.cs` (the records' look); `tools/newworld/world/water_types.py` is the base's `cells` and changes only with a new base | `tools` and `esm` | `readback`, `upload` | the base, `place` | the deploy |
| Atmosphere classes or weathers | `newworld/sources/atmosphere/`, `tools/newworld/atmosphere.py` | `db`, `atmosphere` (and `mist` and `height-fog` for `atmosphere.py`) | `mist`, `height-fog`, `navmesh`, `map`, `esm`, `upload` | every ground stage, `paint` | the deploy of the world file and the stack; each built place's ground bundle (the studio's night view reads the climate) |
| A region's identity (light, sight, weather, sound, water look, ground colour, signature) | `newworld/sources/identity/regions.json` (check: `python -m tools.newworld.identity check`; recipe `docs/design/identity.md`) | `atmosphere` (light, sight, weather, sound), `dressing` (the signature things); the water look and the ground colour are the base's (`cells`, `paint`) and change only with a new base | `height-fog`, `esm`, `upload` | the base, `place` | the deploy of the world file and the stack |
| Region neighbours | `python -m tools.newworld.identity adjacency` after the regions' borders move | nothing (the identity check reads it) | | every stage | none |
| Mist | `tools/newworld/world/mist.py` | `mist`, `height-fog` | `navmesh`, `map`, `esm`, `upload` | everything before `mist`, `paint` | the deploy |
| Community Shaders settings | `tools/newworld/atmosphere_cs.py` | `height-fog` | nothing | `esm` and every stage before it | the stack's deploy only: the world file is unchanged |

## The map, and tools

| A change to | Edit | Runs | Follows | Left alone | Beyond this build |
|---|---|---|---|---|---|
| Map data, teleports | `tools/newworld/world/mapdata.py`, `tools/newworld/teleports.py` | `map`, and `landings` for `teleports.py` | `esm` (the map is applied; the file is not written again), `upload` | every stage before `map` | the deploy; the walk list's teleports if names changed; a built place only when a cell of its own is named anew or a map marker its travel lines land on takes another form id |
| The LOD plan | `tools/newworld/world/lodplan.py`, `lod_models.json` | `map` | `esm`, `upload`, when the plan comes out different | every stage before `map` | the small world's selftest (the skill `world-lod`, section 4); tree and object LOD and the deploy when the plan changed |
| A built place's exterior or land patches | `newworld/places/<id>/` (the skill `place-system`) | `landings`, `map` | `esm`, `readback`, `upload` | every other stage | the deploy |
| The world file's writer | `tools/ArgoniaPlugin/NewWorld*.cs`, `WaterBlend.cs`, `ForeignCopy.cs`, `FormIds.cs`, `WaterStudy.cs`, `tools/newworld/world/world.sh` | `tools` for the C#, and the stage that reads the edited file: `esm` (the writer, the map, the navmesh records, water, copied records, `world.sh`), `atmosphere` (`NewWorldAtmosphere.cs`), `readback` (`NewWorldVerify.cs`, `WaterStudy.cs`) | `readback`, `upload` after `esm`, each skipped when the file comes out the same bytes | every shard stage | if the file's bytes changed: the deploy, the LOD steps whose keys moved (`infra/gpu-box/lod.sh keys`), each built place whose records moved (`python3 -m tools.places worldparts <place_id>`). `NewWorldMap.cs` is also read by the LOD's selftest (the skill `world-lod`, section 4) |
| The travel menu (the "Argonia Travel" power's pages) | `tools/newworld/travel_menu.py`, then `python3 -m tools.newworld.travel_menu generate` writes `newworld/sources/travel/menu.json` (its `check` holds every page to the message box's one row of buttons) | `esm` | `readback`, `upload` | every stage before `esm` | the deploy |
| The Atlas page | `tools/newworld/map_page.py`, `map_page.html` | nothing | nothing | every stage | republish the Atlas (section 7, step 2) |
| Where a new game starts | `papyrus/ARG_QF_MQ101.psc` (Argonia.esp), the start marker in `NewWorld.cs` (a persistent ref of the world's persistent cell) | `tools` and `esm` for the marker | `readback`, `upload` | every shard stage | the deploy; `python3 -m tools.newworld.start_check` reads each card's laid plugins and names where a new game starts |
| A tool or script fix that changes no output | the tool | the stage that reads the file (never a base stage) | nothing, when its output is the same bytes; every stage after it, when the stage is `place` | all else | nothing, or as the row of the stage that was built again |
| The read-back | `tools/newworld/verify.py` | `readback`, `relief` (the base's relief rows, read again) | nothing | all else | nothing |
| The table of form id ranges | `tools/newworld/idspace.py` | `place`, `edits` | every stage after `place` | the base, `landings`, `atmosphere` | as placement rules |
| What a stage reads, or the rebuild itself | `tools/newworld/rebuild.py` | `readback` | nothing. A stage whose read is named more narrowly keeps its record while the wider read it recorded is unchanged: the main tree's next plan writes the record under the new name and nothing is built again | all else | nothing |
| The base's pin | `newworld/sources/ground_base.json`: written only by `rebuild.sh pin-base` (the first pin) or a run with the owner's override | nothing: every base stage is held to it | nothing | every stage | nothing |
| Creatures, hostile people or their rules | `newworld/sources/ecology/` (region tables, `bindings.json`, `npc_encounters.json`, `walk_spots.json`, `blows.json` from `toughness.py measure`), `tools/newworld/ecology/` (`place.py`, `toughness.py`, `anim_audit.py`) | `ecology` | `esm`, `readback`, `upload` | everything before `ecology`: actors live in `plugin/ecology/`, beside `refs/`, so the navmesh and the LOD never read them | the world file only; no LOD |
| Small signature things (bones, eggs, fungi, insects, mist) | `newworld/sources/dressing/kinds.json`, `tools/newworld/dressing/place.py` | `dressing` | `esm`, `readback`, `upload` | everything before `dressing`: its references live in `plugin/dressing/`, beside `refs/`, small or walk-through and without LOD, so the navmesh and the LOD never read them | the world file only; no LOD |
| Music (the pieces, where each plays, combat and the stings) | `newworld/sources/music/records.json` and `pieces.json`, `tools/ArgoniaPlugin/NewWorldMusic.cs` (recipe `docs/design/music.md`); the sound files in the soundtrack pack's stack row | `tools` for the C#, `esm` | `readback`, `upload` | every stage before `esm` | the stack's deploy when the sound files change |
| A region's ground-cover colour (its grass lists) | `REGIONS` and `PROVINCES` grass in `tools/newworld/world/texture.py`; check `python3 -m tools.newworld.dressing.ground_colour` | nothing: it is the base's paint, and changes only with a new base | nothing | every stage | nothing |

A tool fix that should change nothing is proved by the plan and the run together: the plan shows its one stage
stale and the rest following, and the run's summary shows every following stage skipped. If a following stage
runs, the fix changed an output: read the diff before going on. A fix to `place/place.py`, or to a file it reads, is
the exception: plan it as a rebuild of everything after `place`, and put what is not the rule itself in another
file. A fix to a base stage's tool changes nothing built: the base stands until the owner asks for a new one.
