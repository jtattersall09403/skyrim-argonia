"""The new world's rebuild: one command for every stage from the scope to the read-back, each stage run only when
what it reads has changed, each check run straight after the stage it judges. The recipe is the skill world-build.

    tools/newworld/rebuild.sh plan                  # the order, and which stages are stale (and why) or current
    tools/newworld/rebuild.sh preflight             # everything checkable before the first long stage
    tooling/job_guard.sh run nw-rebuild -- tools/newworld/rebuild.sh run [--to STAGE] [--force STAGE ...]
    tooling/job_guard.sh wait nw-rebuild

How it decides. STAGES names, for each stage, what it reads and what it writes. The order is derived from that: a
stage follows every stage that writes something it reads. A stage's key is the digest of everything it reads (file
contents, the columns of a database table, the named fields of an upstream manifest) and of its commands and
checks; its build key is the same without what its checks alone read. The key of its last green run is its stamp,
`out/newworld/rebuild/<stage>.json`. A stage is current when its stamp holds today's key and its outputs exist and
name the builds they stand on (`agree`); otherwise it is stale, and so is every stage after it until its own
inputs prove unchanged once the stages before it have run.

The stamp is the record of one run. `running` (the build key) is written before the stage's commands start, so a
run that was killed, or whose command was red, leaves a stage that is stale whatever its inputs then are; `built`
replaces it when the commands are done, so only the checks are repeated while the build key holds; `key` is
written when the checks are green. A stage the rebuild has no record of is current only on proof its own tool left
beside its output: the key the tool stored there, recomputed by the tool from today's inputs (`proof`). The run
that witnesses the proof runs the stage's checks and marks the stage `proved` on today's key: from then on it
goes stale by everything the stage reads, as a stamped stage does.

A stage tool that skips on a key of its own is told the run's build key (`NW_STAGE_KEY`) and folds it into its
key (tools/newworld/keyed.py, world.sh): it skips only what it built for this very build key, and resumes by row or
by cell when the same run is started again (decision 0037). A stage with no record is run without it, so its tool
decides by its own key alone, as its proof would.

How it runs. Stale stages start as soon as the stages they read from are done, side by side while their measured
peak memory fits the machine (`gb`; two stages that share a `lock` never overlap). A stage's checks run in the same
slot straight after its commands. A red command or check stops the run there: nothing new starts, the stages
already running finish, and the check's own lines are printed. A run decides by content: the digest cache
(`digests.json`, keyed on each file's inode, size and times) serves `plan` and `preflight` alone.

Out: `out/newworld/rebuild/` (stamps, `logs/<stage>.log`, `summary.json`, `run.pid`, `digests.json`); never git.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLUGIN = "out/newworld/plugin"
GAME = Path(os.environ.get("ARGONIA_GAME_ROOT", Path.home() / "games/skyrimse")) / "Data"
STACK = Path(os.environ.get("ARGONIA_STACK") or Path.home() / ".argonia/stack")
RESERVE_GB = 2.0      # memory left to the machine beside the stages' measured peaks
DISK_GB = 4.0         # a whole rebuild rewrites about 2.3 GB under out/newworld (measured), old and new side by side
# the prose and people columns of `place`: no ground stage reads them, so an edit to them moves no ground
PLACE_GROUND = ("db:place[-summary,-held_by,-status,-population,-danger_band_id,-importance,-statement_tier_id,"
                "-culture_id,-read_sure,-siting]")
# the columns of `place` the placed and mapped stages read: its position, size, kind, name and rank
PLACE_MAP = ("db:place[-summary,-held_by,-status,-population,-danger_band_id,-statement_tier_id,-culture_id,"
             "-read_sure,-siting]")
# the read-back's groups that judge other machines' work: the LOD's, the deploy's and the built places' recipes run them
DOWNSTREAM_GROUPS = "lod,deploy,places"
# the mod rows the rebuild itself stages (height-fog): left out of what the other stages read of the laid stack
OWN_ROWS = ("cs-height-fog",)


@dataclass(frozen=True)
class Stage:
    """One stage. `reads`: `src:<glob>` (a committed file, by content), `out:<path>[#field,...]` (a build output under
    out/, by content or by the named JSON fields, `#-field` for all but those; a glob or a folder reads every file
    under it), `db:<table>[cols]` (a table of the world database; `-col` leaves a column out), `ext:<path>` (a file
    outside the repo, by size and time), `laid:<profile>` (the mod stack as laid for that profile: its record but
    for OWN_ROWS, and its load order). `check_reads`: the same, for what the checks read and the commands do not.
    `writes`: `out:<path>`, `db:<table>` or `db:*`, `src:<path>` (a tracked file the stage rewrites).
    `after`: stages it waits for without reading them (a long stage waits for the cheap checks).
    `proof`: the tool's own command that exits 0 when the key it stored beside its output is the key it computes
    from today's inputs; it writes nothing. It stands for a stamp only while the stage has none.
    `agree`: pairs (a, b, how) of `out:` specs that must be equal ("eq") or a prefixed by b ("starts"): an output
    names the build it stands on. `gb` and `minutes`: the measured peak memory and wall time on the build VM."""
    name: str
    what: str
    cmds: tuple = ()
    checks: tuple = ()
    reads: tuple = ()
    check_reads: tuple = ()
    writes: tuple = ()
    agree: tuple = ()
    gb: float = 1.0
    minutes: float = 1.0
    after: tuple = ()
    proof: tuple = ()
    lock: str | None = None
    alone: bool = False


PY = "{py}"
BUILD = "out:newworld/terrain/build.json#id,sha256"       # the terrain build: its id and its heightmap's digest
LAND = "out:newworld/plugin/land/manifest.json#key"
LANDCOVER = "out:newworld/landcover/key.txt"
FLORA = "out:newworld/plugin/refs/flora/manifest.json#key,shard_sha256"
CELLS = "out:newworld/plugin/cells.json"
# The compiled tools are read by their sources: the same sources compile to different bytes from one build to the next.
DLL = "out:tools/ArgoniaPlugin/ArgoniaPlugin.dll"
WRITER_CS = ("src:tools/ArgoniaPlugin/NewWorld.cs", "src:tools/ArgoniaPlugin/NewWorldAtmosphere.cs",
             "src:tools/ArgoniaPlugin/NewWorldMap.cs", "src:tools/ArgoniaPlugin/NewWorldNavmesh.cs",
             "src:tools/ArgoniaPlugin/WaterBlend.cs", "src:tools/ArgoniaPlugin/ForeignCopy.cs")
BUILT_PLACES = ("src:newworld/places/*/land.jsonl", "src:newworld/places/*/spaces/exterior/refs.jsonl")
DBPY = "src:tools/argonia_world/db.py"
LAID = "laid:NewWorld"
ESM = "out:newworld/plugin/ArgoniaNewWorld.esm"
MAPS = ("src:newworld/sources/maps/PT3-map-Black_Marsh.png", "src:newworld/sources/maps/PT3-map-Black_Marsh_Regions.png")
DB_SOURCES = (*MAPS, "src:newworld/sources/road_corrections.json", "src:newworld/places/*/people.jsonl",
              "src:newworld/places/*/place.json", "src:tools/newworld/regions.py", "src:tools/newworld/frame.py",
              "src:tools/newworld/tiles.py", "src:tools/places/stock/*.py",
              "src:newworld/sources/key.json", "src:newworld/sources/research/**/*.json", "src:newworld/sources/danger/**/*",
              "src:newworld/sources/stock/**/*", "src:newworld/sources/people/**/*", "src:newworld/sources/atmosphere/*.json",
              "src:newworld/sources/flora/**/*", "src:newworld/sources/travel/**/*", "src:newworld/story/data/schema.sql",
              "src:newworld/sources/water_overrides.json", "src:newworld/sources/water_paint.json",
              "out:newworld/symbols.json", "out:newworld/cell_region.json", "out:newworld/margin_cells.json",
              "out:newworld/raster/water.png", "out:newworld/raster/foreign.png", "out:newworld/roads.json",
              "out:newworld/borders.json",
              "src:tools/newworld/build_db.py", "src:tools/newworld/danger.py", "src:tools/newworld/place_danger.py",
              "src:tools/newworld/stockdb.py", "src:tools/newworld/wealth.py", "src:tools/newworld/travel.py",
              "src:tools/newworld/place_law.py", "src:tools/newworld/flora.py", "src:tools/newworld/atmosphere.py",
              "src:tools/newworld/terrain_beyond.py", "src:tools/argonia_world/db.py")
# what the map extraction (the phase before this one) left under out/newworld: read here, built by its own tools
# the stages whose checks are cheap and early: every long stage waits for them
EARLY_CHECKS = ("needs", "water", "relief", "landings", "place")
EXTERNAL = ("newworld/raster/water.png", "newworld/raster/foreign.png", "newworld/roads.json", "newworld/borders.json",
            "newworld/symbols.json", "newworld/research/flora_catalogue.json", "newworld/terrain_ref/tamriel_h.npy",
            "newworld/terrain_ref/tamriel_w.npy")

STAGES: tuple[Stage, ...] = (
    Stage("tools", "the C# tools compile (ArgoniaPlugin, ArgoniaNav)",
          cmds=(("dotnet", "build", "-c", "Release", "-o", "out/tools/ArgoniaPlugin", "tools/ArgoniaPlugin", "-v", "q", "-nologo"),
                ("dotnet", "build", "-c", "Release", "-o", "out/tools/ArgoniaNav", "tools/navmesh/ArgoniaNav", "-v", "q", "-nologo")),
          reads=("src:tools/ArgoniaPlugin/**/*.cs", "src:tools/ArgoniaPlugin/*.csproj", "src:tools/navmesh/ArgoniaNav/**/*.cs",
                 "src:tools/navmesh/ArgoniaNav/*.csproj"),
          writes=(DLL, "out:tools/ArgoniaNav/ArgoniaNav.dll"), gb=1.0, minutes=0.5, lock="dotnet"),
    Stage("scope", "the cells the world covers: the province, its margin and the cells beyond the picture",
          cmds=((PY, "-m", "tools.newworld.tiles", "scope"),),
          reads=(*MAPS, "src:tools/newworld/tiles.py", "src:tools/newworld/frame.py"),
          writes=("out:newworld/scope_cells.json", "out:newworld/margin_cells.json"), gb=0.5, minutes=0.2),
    Stage("regions", "each cell's region",
          cmds=((PY, "-m", "tools.newworld.regions"),),
          reads=(*MAPS, "out:newworld/scope_cells.json", "src:tools/newworld/regions.py", "src:tools/newworld/tiles.py",
                 "src:tools/newworld/frame.py"),
          writes=("out:newworld/cell_region.json",), gb=0.5, minutes=0.3),
    Stage("db", "the world database from its sources (the tables the ground stages read)",
          cmds=((PY, "-m", "tools.newworld.build_db"),),
          reads=DB_SOURCES, writes=("db:*",), gb=1.1, minutes=0.5, alone=True),
    Stage("terrain", "the heightmap, and its check: the map held, held ground as built, banks within Skyrim's measure",
          cmds=((PY, "-m", "tools.newworld.terrain", "--no-upload"),),
          checks=((PY, "-m", "tools.newworld.terrain", "check"),),
          reads=("out:newworld/raster/water.png", "out:newworld/raster/foreign.png", "out:newworld/cell_region.json",
                 "out:newworld/scope_cells.json", "out:newworld/roads.json",
                 "out:newworld/terrain_ref/tamriel_h.npy", "out:newworld/terrain_ref/tamriel_w.npy",
                 "out:places/shards/*/plan.json",
                 PLACE_GROUND, "db:place_terrain_need",
                 "db:region[id,name,landform,kind,elevation_floor_m,elevation_summit_m,roughness_m,cliff_share,wetness]",
                 "db:road_class", "db:settlement_tier", "db:symbol", "db:water_kind", "db:terrain_need", DBPY,
                 "src:newworld/sources/region_relief.json", "src:newworld/sources/terrain_held.json",
                 "src:newworld/sources/water_overrides.json", "src:newworld/sources/water_owner_bodies.png",
                 "src:tools/newworld/terrain.py", "src:tools/newworld/terrain_*.py", "src:tools/newworld/frame.py",
                 "src:tools/newworld/tiles.py", "src:tools/newworld/water_held.py"),
          writes=("out:newworld/terrain/build.json", "out:newworld/terrain/inputs.json",
                  "out:newworld/terrain/heightmap.npy", "out:newworld/terrain/check.json",
                  "out:newworld/terrain/places_terrain.json", "out:newworld/terrain/character.json",
                  "out:newworld/terrain/water_bodies.png", "out:newworld/water_bodies.json"),
          proof=(PY, "-m", "tools.newworld.terrain", "inputs"), gb=5.7, minutes=9.0),
    Stage("needs", "every place's terrain need on the built heightmap, against the accepted failures",
          cmds=((PY, "-m", "tools.newworld.terrain_needs"),),
          reads=(BUILD, "out:newworld/terrain/places_terrain.json", "db:place[id,on_water]",
                 "src:newworld/sources/terrain_needs_accepted.json", "src:tools/newworld/terrain_needs.py",
                 "src:tools/newworld/terrain_shape.py", "src:tools/newworld/terrain_clearance.py",
                 "src:tools/newworld/terrain_relief.py", "src:tools/newworld/frame.py", DBPY),
          writes=("out:newworld/terrain/needs.json",),
          agree=(("out:newworld/terrain/needs.json#build", "out:newworld/terrain/build.json#id", "eq"),),
          gb=1.0, minutes=0.4),
    Stage("water", "water kinds and flow, against the accepted classification and the owner's edits",
          cmds=((PY, "-m", "tools.newworld.water_kinds", "--png"),),
          reads=(BUILD, "out:newworld/water_bodies.json", "out:newworld/cell_region.json", "out:newworld/raster/water.png",
                 "src:newworld/sources/water_overrides.json", "src:newworld/sources/water_paint.json",
                 "src:newworld/sources/water_owner_bodies.png", "src:newworld/sources/water_accepted.json",
                 "db:region", "db:region_note", "db:water_kind",
                 "src:tools/newworld/water_kinds.py", "src:tools/newworld/water_held.py", "src:tools/newworld/terrain_relief.py",
                 "src:tools/newworld/terrain_water.py", "src:tools/newworld/terrain.py", "src:tools/newworld/frame.py", DBPY),
          writes=("out:newworld/water_classified.json", "out:newworld/water_classified.png", "out:newworld/water_flow_cells.json",
                  "out:newworld/water_check.json"),
          agree=(("out:newworld/water_check.json#terrain_build", "out:newworld/terrain/build.json#id", "eq"),),
          gb=1.1, minutes=0.7),
    Stage("db-water", "the database's record of the terrain build and its water bodies",
          cmds=((PY, "-m", "tools.newworld.build_db"),), after=("db",),
          reads=DB_SOURCES + ("out:newworld/terrain/build.json#id,sha256", "out:newworld/water_classified.json",
                              "out:newworld/water_bodies.json"),
          writes=("db:terrain_build", "db:water_body"), gb=1.1, minutes=0.5, alone=True),
    Stage("land", "the LAND shards: heights in the engine's steps, normals, the start marker",
          cmds=((PY, "-m", "tools.newworld.keyed", "land", "--out", PLUGIN),),
          proof=(PY, "-m", "tools.newworld.proofs", "land", "--plugin", PLUGIN),
          reads=(BUILD, "db:place[id,world_x,world_y]", "src:tools/newworld/world/land.py", "src:tools/newworld/world/quantize.py",
                 "src:tools/newworld/world/units.py"),
          writes=("out:newworld/plugin/land/manifest.json", "out:newworld/plugin/land/limited.npy"),
          agree=(("out:newworld/plugin/land/manifest.json#build_id", "out:newworld/terrain/build.json#id", "eq"),
                 ("out:newworld/plugin/land/manifest.json#heightmap_sha256", "out:newworld/terrain/build.json#sha256", "eq")),
          gb=0.6, minutes=0.3),
    Stage("relief", "read-back, relief rows: regions read apart, the land reaches past the picture, held ground kept",
          checks=((PY, "-m", "tools.newworld.verify", "--only", "relief"),),
          reads=(BUILD, "out:newworld/terrain/character.json", "out:newworld/terrain/check.json", LAND,
                 "src:tools/newworld/verify.py", "src:tools/newworld/terrain_character.py",
                 "src:tools/newworld/terrain_held.py"),
          gb=0.6, minutes=0.2),
    Stage("landcover", "one habitat per sample, with shore, road and water-kind fields",
          cmds=((PY, "-m", "tools.newworld.keyed", "landcover"),), proof=(PY, "-m", "tools.newworld.proofs", "landcover"),
          reads=(BUILD, "out:newworld/terrain/places_terrain.json", "out:newworld/water_classified.json",
                 "out:newworld/water_classified.png", "out:newworld/cell_region.json", "out:newworld/margin_cells.json",
                 "db:habitat", "db:region_habitat", "db:road", "db:road_vertex", "db:region", "db:water_kind",
                 "src:tools/newworld/landcover.py", "src:tools/newworld/terrain.py", "src:tools/newworld/frame.py"),
          writes=("out:newworld/landcover/key.txt", "out:newworld/landcover/legend.json"),
          agree=(("out:newworld/landcover/legend.json#build_id", "out:newworld/terrain/build.json#id", "eq"),),
          gb=2.6, minutes=0.8),
    Stage("cells", "each cell's water record and region",
          cmds=((PY, "-m", "tools.newworld.world.cells", "--out", PLUGIN),),
          proof=(PY, "-m", "tools.newworld.world.cells", "--current", "--out", PLUGIN),
          reads=(LAND, LANDCOVER, "out:newworld/water_flow_cells.json", "db:region", "db:region_note", "db:water_kind",
                 "src:tools/newworld/world/cells.py", "src:tools/newworld/world/water_types.py",
                 "src:tools/newworld/water_kinds.py", "src:tools/newworld/landcover.py", "src:tools/newworld/terrain.py",
                 "src:tools/newworld/frame.py"),
          writes=(CELLS,),
          agree=(("out:newworld/plugin/cells.json#build_id", "out:newworld/plugin/land/manifest.json#build_id", "eq"),),
          gb=1.0, minutes=0.3),
    Stage("landings", "every teleport has its landing: dry land in each place's cell, each walk check's water near it",
          checks=((PY, "-m", "tools.newworld.teleports", "landings", "--plugin", PLUGIN),),
          reads=(LAND, CELLS, PLACE_MAP, *BUILT_PLACES, "src:tools/newworld/teleports.py",
                 "src:tools/newworld/world/units.py"),
          gb=1.0, minutes=0.3),
    Stage("place", "trees, plants, rocks, cliffs and road dressing placed and seated, and the placement check",
          cmds=((PY, "-m", "tools.newworld.keyed", "place", "run"),), proof=(PY, "-m", "tools.newworld.place", "current"),
          checks=((PY, "-m", "tools.newworld.place", "check"),),
          reads=(LAND, LANDCOVER, "out:newworld/landcover/legend.json", BUILD, "out:newworld/margin_cells.json",
                 "out:newworld/research/flora_catalogue.json", "out:newworld/research/hollow_extra.json", LAID,
                 "src:tools/navmesh/esm.py", "src:tools/navmesh/meshes.py", "src:tools/navmesh/placed.py",
                 "src:tools/navmesh/bsa.py",
                 "db:flora_base", "db:flora_class", "db:flora_family", "db:flora_guild", "db:flora_guild_member",
                 "db:region_flora", "db:habitat", "db:road", "db:road_class", "db:road_node", "db:road_vertex", PLACE_MAP,
                 "db:water_kind", "db:region", "src:tools/newworld/place/__init__.py", "src:tools/newworld/place/__main__.py",
                 "src:tools/newworld/place/place.py",
                 "src:tools/newworld/place/texsets.py"),
          check_reads=("src:tools/newworld/place/checks.py",),
          writes=("out:newworld/plugin/refs/flora/manifest.json", "out:newworld/plugin/refs/flora/bases.json"),
          agree=(("out:newworld/plugin/refs/flora/manifest.json#build_id", "out:newworld/terrain/build.json#id", "eq"),),
          gb=3.4, minutes=1.8),
    Stage("paint", "the ground paint, and its check on the engine's view: layers, seams, edges, roads, swathes",
          cmds=((PY, "-m", "tools.newworld.keyed", "paint", "--out", PLUGIN),),
          proof=(PY, "-m", "tools.newworld.proofs", "paint", "--plugin", PLUGIN),
          checks=((PY, "-m", "tools.newworld.world.texcheck", "--out", PLUGIN),),
          reads=(LAND, LANDCOVER, "db:habitat", "db:region", "db:road", "src:tools/newworld/world/texture.py",
                 "src:tools/newworld/world/roadpaint.py", "src:tools/newworld/landcover.py", "src:tools/newworld/terrain.py",
                 "src:tools/newworld/frame.py"),
          check_reads=("src:tools/newworld/world/texcheck.py", "src:tools/places/assets/resolve.py", LAID),
          writes=("out:newworld/plugin/tex/manifest.json", "out:newworld/plugin/tex/materials.json"),
          agree=(("out:newworld/plugin/tex/manifest.json#key", "out:newworld/plugin/land/manifest.json#key", "starts"),),
          after=EARLY_CHECKS, gb=5.6, minutes=21.0),
    Stage("mist", "the low mist over marsh, swamp and pond",
          cmds=((PY, "-m", "tools.newworld.world.mist", "--out", PLUGIN),),
          reads=(LAND, LANDCOVER, CELLS, FLORA, BUILD, "db:region_atmosphere", "db:atmosphere_class",
                 "src:newworld/sources/atmosphere/classes.json", "src:tools/newworld/world/mist.py",
                 "src:tools/newworld/atmosphere.py", DBPY),
          writes=("out:newworld/plugin/refs/mist/manifest.json",),
          agree=(("out:newworld/plugin/refs/mist/manifest.json#build_id", "out:newworld/plugin/land/manifest.json#build_id", "eq"),),
          gb=0.3, minutes=0.2),
    Stage("atmosphere", "the weather, image space, lighting and climate records' spec",
          cmds=((PY, "-m", "tools.newworld.atmosphere", "spec", "--plugin", PLUGIN),),
          after=("tools",),
          reads=("src:newworld/sources/atmosphere/*.json", "db:atmosphere_class", "db:region_atmosphere",
                 "src:tools/ArgoniaPlugin/NewWorldAtmosphere.cs",
                 f"ext:{GAME}/Skyrim.esm", f"ext:{GAME}/Update.esm", "src:tools/newworld/atmosphere.py", DBPY),
          writes=("out:newworld/plugin/atmosphere.json",), gb=0.5, minutes=0.2, lock="dotnet"),
    Stage("height-fog", "Community Shaders' height fog: a settings file per weather in the mod row, staged",
          cmds=((PY, "-m", "tools.newworld.atmosphere_cs", "write", "--plugin", PLUGIN),
                ("python3", "infra/gpu-box/stack.py", "stage")),
          reads=("out:newworld/plugin/atmosphere.json", LAND, LANDCOVER, BUILD, "db:region_atmosphere",
                 "src:tools/newworld/atmosphere_cs.py", "src:tools/newworld/atmosphere.py",
                 "src:tools/newworld/world/mist.py"),
          writes=("src:mods/dependencies.json",),
          gb=1.5, minutes=1.0, lock="stack"),
    Stage("navmesh", "the navmesh of every land cell round the placed objects, its seams and paths checked",
          cmds=((PY, "-m", "tools.navmesh", "build", "--plugin", PLUGIN, "--out", f"{PLUGIN}/navmesh"),),
          checks=((PY, "-m", "tools.newworld.world.navobjects", "--plugin", PLUGIN),),
          reads=(LAND, FLORA, "out:newworld/plugin/refs/flora/bases.json", "out:newworld/plugin/refs/mist/manifest.json",
                 "out:newworld/margin_cells.json", "out:newworld/scope_cells.json", "db:road", "db:road_vertex", LAID,
                 PLACE_MAP, "src:tools/navmesh/ArgoniaNav/**/*.cs", "src:tools/navmesh/*.py",
                 "src:tools/newworld/world/units.py"),
          check_reads=("src:tools/newworld/world/navobjects.py",),
          writes=("out:newworld/plugin/navmesh/build.json", "out:newworld/plugin/navmesh/check.json"),
          agree=(("out:newworld/plugin/navmesh/build.json#build_id", "out:newworld/plugin/land/manifest.json#build_id", "eq"),),
          after=EARLY_CHECKS + ("tools",), gb=0.8, minutes=4.5),
    Stage("map", "map markers and pan box, the named teleports, the LOD plan; then every landing checked",
          cmds=((PY, "-m", "tools.newworld.world.mapdata", "build", "--plugin", PLUGIN),),
          checks=((PY, "-m", "tools.newworld.teleports", "check", "--plugin", PLUGIN),),
          reads=(LAND, CELLS, FLORA, "out:newworld/plugin/refs/flora/bases.json", "out:newworld/plugin/refs/mist/manifest.json",
                 "out:newworld/scope_cells.json", "out:newworld/margin_cells.json", PLACE_MAP, "db:place_kind", *BUILT_PLACES,
                 "src:tools/newworld/world/lod_models.json", "out:newworld/lod/logs/coverage.json", LAID,
                 "src:tools/newworld/world/mapdata.py", "src:tools/newworld/teleports.py",
                 "src:tools/newworld/world/lodplan.py", "src:tools/newworld/world/units.py"),
          writes=("out:newworld/plugin/map/map.json", "out:newworld/plugin/map/markers.json",
                  "out:newworld/plugin/map/teleports.json", "out:newworld/plugin/map/lodplan.json"),
          agree=(("out:newworld/plugin/map/teleports.json#build_id", "out:newworld/plugin/land/manifest.json#build_id", "eq"),
                 ("out:newworld/plugin/map/lodplan.json#bases_key", "out:newworld/plugin/refs/flora/bases.json#key", "eq")),
          gb=1.5, minutes=1.0),
    Stage("esm", "ArgoniaNewWorld.esm written, the map data applied, and the file's own check",
          cmds=(("tools/newworld/world/world.sh", "write"), ("tools/newworld/world/world.sh", "map")),
          checks=(("tools/newworld/world/world.sh", "check"),),
          reads=(LAND, "out:newworld/plugin/tex/manifest.json#key", "out:newworld/plugin/tex/materials.json", CELLS,
                 "out:newworld/plugin/atmosphere.json", FLORA, "out:newworld/plugin/refs/flora/bases.json",
                 "out:newworld/plugin/refs/mist", "out:newworld/plugin/navmesh/build.json#sha256",
                 "out:newworld/plugin/map/map.json", "out:newworld/plugin/map/markers.json",
                 "out:newworld/plugin/map/teleports.json", "out:newworld/plugin/map/lodplan.json", *WRITER_CS,
                 f"ext:{GAME}/Skyrim.esm", f"ext:{GAME}/Update.esm", f"ext:{GAME}/Black Marsh.esm", LAID,
                 "src:tools/newworld/world/world.sh"),
          writes=("out:newworld/plugin/ArgoniaNewWorld.esm", "out:newworld/plugin/ArgoniaNewWorld.json",
                  "out:newworld/plugin/check.txt"),
          agree=(("out:newworld/plugin/ArgoniaNewWorld.json#key", "out:newworld/plugin/land/manifest.json#key", "starts"),),
          after=("tools",), gb=6.0, minutes=3.0, lock="dotnet"),
    Stage("readback", "the read-back of the written file: every requirement with a number",
          checks=((PY, "-m", "tools.newworld.verify", "--skip", f"{DOWNSTREAM_GROUPS},relief"),),
          reads=(ESM, "out:newworld/plugin/ArgoniaNewWorld.json#key", "out:newworld/plugin/check.txt",
                 "out:newworld/plugin/navmesh/check.json#-check_s", "out:newworld/water_check.json",
                 "src:mods/dependencies.json", f"ext:{STACK}/installed-NewWorld.json", f"ext:{STACK}/installed.json",
                 f"ext:{STACK}/MO2/profiles/NewWorld/modlist.txt",
                 "src:tools/newworld/*.py", "src:tools/newworld/world/*.py", "src:tools/newworld/place/*.py",
                 "src:tools/navmesh/*.py", "src:tools/places/assets/resolve.py", DBPY,
                 "src:tools/ArgoniaPlugin/NewWorldVerify.cs", "src:tools/ArgoniaPlugin/WaterStudy.cs"),
          gb=2.7, minutes=3.5, lock="dotnet"),
    Stage("upload", "the world file and its records to the bucket",
          cmds=((PY, "-m", "tools.newworld.terrain_upload"), ("tools/newworld/world/world.sh", "upload")),
          reads=(BUILD, ESM, "out:newworld/plugin/ArgoniaNewWorld.json#key", "out:newworld/plugin/check.txt",
                 "src:tools/newworld/terrain_upload.py", "src:tools/newworld/frame.py"),
          after=("readback",), gb=0.2, minutes=0.5),
)

# What a world rebuild leaves stale beyond this machine's out/newworld: (what, the stages that feed it, where its recipe is)
DOWNSTREAM = (
    ("the LOD on the play machine (terrain, trees, objects, the map)", ("land", "paint", "place", "map", "esm"),
     "docs/design/lod.md"),
    ("the play machine's deploy of ArgoniaNewWorld.esm", ("esm",), "the skill world-build, section Deploy"),
    ("each built place's ground bundle, stages and build ({places})", ("terrain", "land", "paint", "place", "navmesh", "esm"),
     "the skill place-build, section 7"),
)


# ---- the tree a rebuild works in --------------------------------------------------------------------------------

@dataclass
class Tree:
    repo: Path = REPO
    stages: tuple = STAGES
    out: Path = field(default=None)
    db: Path = field(default=None)
    state: Path = field(default=None)
    py: str = field(default=None)
    stack: Path = field(default=None)
    fresh: bool = False       # digest by content, whatever the cache holds: a run and a tool's proof decide so

    def __post_init__(self):
        self.repo = Path(self.repo)
        self.out = Path(self.out or self.repo / "out")
        self.db = Path(self.db or self.repo / "newworld/story/data/db")
        self.state = Path(self.state or self.out / "newworld/rebuild")
        self.stack = Path(self.stack or STACK)
        venv = Path.home() / ".argonia/venv/bin/python"
        self.py = self.py or (str(venv) if venv.exists() else sys.executable)
        self._cache: dict | None = None
        self._laid: dict[str, str] = {}
        self.by_name = {s.name: s for s in self.stages}

    # -- digests

    def _file_sha(self, p: Path) -> str:
        """A file's sha256. A plan remembers it by the file's inode, size, and times of change (the inode's own
        included: no edit keeps it), so it never reads a large output twice; `fresh` reads the file whatever is
        remembered."""
        if self._cache is None:
            try:
                self._cache = json.loads((self.state / "digests.json").read_text())
            except (OSError, ValueError):
                self._cache = {}
        st = p.stat()
        sig = [st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
        hit = self._cache.get(str(p))
        if not self.fresh and isinstance(hit, list) and hit[:4] == sig and len(hit) == 5:
            return hit[4]
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        self._cache[str(p)] = [*sig, h.hexdigest()[:20]]
        return self._cache[str(p)][4]

    def _laid_digest(self, profile: str) -> str:
        """The stack as laid for a profile: its record's rows, plugins and files but for OWN_ROWS, and its load order."""
        rec, ml = self.stack / f"installed-{profile}.json", self.stack / "MO2/profiles" / profile / "modlist.txt"
        if not rec.exists():
            return "absent"
        sha = self._file_sha(rec)
        if sha not in self._laid:
            try:
                doc = json.loads(rec.read_text())
            except ValueError:
                return "unreadable"
            doc["rows"] = {k: v for k, v in (doc.get("rows") or {}).items() if k not in OWN_ROWS}
            doc["files"] = {k: v for k, v in (doc.get("files") or {}).items() if v[0] not in OWN_ROWS}
            self._laid[sha] = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:20]
        return f"{self._laid[sha]}:{self._file_sha(ml) if ml.exists() else 'absent'}"

    def save_cache(self) -> None:
        if self._cache is not None and self.state.exists():
            tmp = self.state / "digests.json.tmp"
            tmp.write_text(json.dumps(self._cache))
            os.replace(tmp, self.state / "digests.json")

    def _files(self, root: Path, pattern: str) -> list[Path]:
        p = root / pattern
        if any(c in pattern for c in "*?["):
            hits = sorted(q for q in root.glob(pattern) if q.is_file() and not {"__pycache__", "obj", "bin"} & set(q.parts))
        elif p.is_dir():
            hits = sorted(q for q in p.rglob("*") if q.is_file())
        else:
            hits = [p] if p.is_file() else []
        return hits

    def digest(self, spec: str) -> str:
        """The digest of one thing a stage reads; "absent" when it is not there."""
        kind, _, rest = spec.partition(":")
        if kind == "ext":
            p = Path(rest).expanduser()
            return f"{p.stat().st_size}:{p.stat().st_mtime_ns}" if p.exists() else "absent"
        if kind == "laid":
            return self._laid_digest(rest)
        if kind == "db":
            m = re.fullmatch(r"([a-z_]+)(?:\[(.*)\])?", rest)
            p = self.db / f"{m.group(1)}.jsonl"
            if not p.exists():
                return "absent"
            if not m.group(2):
                return self._file_sha(p)
            cols = [c.strip() for c in m.group(2).split(",")]
            drop, keep = {c[1:] for c in cols if c.startswith("-")}, [c for c in cols if not c.startswith("-")]
            h = hashlib.sha256()
            for ln in p.read_text(encoding="utf-8").splitlines():
                if ln.strip():
                    r = json.loads(ln)
                    r = {k: r.get(k) for k in keep} if keep else {k: v for k, v in r.items() if k not in drop}
                    h.update(json.dumps(r, sort_keys=True).encode() + b"\n")
            return h.hexdigest()[:20]
        root = self.repo if kind == "src" else self.out
        path, _, fields = rest.partition("#")
        if fields:
            p = root / path
            if not p.exists():
                return "absent"
            try:
                doc = json.loads(p.read_text())
            except ValueError:
                return "unreadable"
            names = fields.split(",")
            if all(n.startswith("-") for n in names):
                return hashlib.sha256(json.dumps({k: v for k, v in doc.items() if f"-{k}" not in names},
                                                 sort_keys=True).encode()).hexdigest()[:20]
            return json.dumps({k: doc.get(k) for k in names}, sort_keys=True)
        hits = self._files(root, path)
        if not hits:
            return "absent"
        if len(hits) == 1 and hits[0] == root / path:
            return self._file_sha(hits[0])
        h = hashlib.sha256()
        for q in hits:
            h.update(f"{q.relative_to(root)}:{self._file_sha(q)}\n".encode())
        return h.hexdigest()[:20]

    def inputs(self, s: Stage) -> dict:
        d = {spec: self.digest(spec) for spec in s.reads + s.check_reads}
        d["commands"] = hashlib.sha256(json.dumps(s.cmds).encode()).hexdigest()[:20]
        d["checks"] = hashlib.sha256(json.dumps(s.checks).encode()).hexdigest()[:20]
        return d

    def build_key(self, s: Stage, inputs: dict) -> str:
        """The key of what the stage's commands read: the stage's key without its checks and what they alone read."""
        return self.key_of({k: inputs[k] for k in (*s.reads, "commands")})

    @staticmethod
    def key_of(inputs: dict) -> str:
        return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:20]

    # -- stamps

    def stamp(self, s: Stage) -> dict:
        p = self.state / f"{s.name}.json"
        try:
            return json.loads(p.read_text()) if p.exists() else {}
        except ValueError:
            return {}

    def write_stamp(self, s: Stage, doc: dict) -> None:
        self.state.mkdir(parents=True, exist_ok=True)
        tmp = self.state / f"{s.name}.json.tmp"
        tmp.write_text(json.dumps(doc, indent=1))
        os.replace(tmp, self.state / f"{s.name}.json")

    def path_of(self, spec: str) -> Path | None:
        kind, _, rest = spec.partition(":")
        if kind == "db":
            return None if rest == "*" else self.db / f"{rest.split('[')[0]}.jsonl"
        if kind in ("ext", "laid"):
            return None
        return (self.repo if kind == "src" else self.out) / rest.split("#")[0]

    def disagreement(self, s: Stage) -> str | None:
        """Why the stage's outputs are not of the builds they stand on, or None."""
        for w in s.writes:
            p = self.path_of(w)
            if p is not None and not p.exists():
                return f"its output {w.split(':', 1)[1]} is missing"
        for a, b, how in s.agree:
            va, vb = self.digest(a), self.digest(b)
            if "absent" in (va, vb):
                return f"{(a if va == 'absent' else b).split(':', 1)[1]} is missing"
            if "unreadable" in (va, vb):
                return f"{(a if va == 'unreadable' else b).split(':', 1)[1]} cannot be read"
            xa, xb = (next(iter(json.loads(v).values())) for v in (va, vb))
            if (how == "eq" and xa != xb) or (how == "starts" and not str(xa).startswith(str(xb))):
                return f"{a.split(':', 1)[1]} is {xa}, {b.split(':', 1)[1]} is {xb}"
        return None

    def unproven(self, s: Stage) -> str | None:
        """Why the stage's own record does not prove its output was made from today's inputs, or None."""
        p = subprocess.run([self.py if a == PY else a for a in s.proof], cwd=self.repo, env=_env(), capture_output=True, text=True)
        return None if p.returncode == 0 else (p.stdout.strip().splitlines() or p.stderr.strip().splitlines() or ["its proof is red"])[-1][:160]

    def own_state(self, s: Stage, inputs: dict | None = None) -> tuple[str, str]:
        """(state, why) from the stage's own record, inputs and outputs, whatever the stages before it are:
        `current`; `stale` (it runs); `proved` (no record, and its tool's own record proves its output: its checks
        alone run, and it is marked)."""
        inputs = inputs or self.inputs(s)
        st = self.stamp(s)
        if st.get("running"):
            return "stale", "its last run stopped part-way through its commands"
        held = st.get("key") or st.get("proved")
        if held:
            if held != self.key_of(inputs):
                was = st.get("inputs") or {}
                ch = [k for k in inputs if was.get(k) != inputs[k]]
                why = "changed: " + ", ".join(k.split(":", 1)[-1] for k in ch[:4]) + (f" and {len(ch) - 4} more" if len(ch) > 4 else "")
                if s.checks and st.get("built") == self.build_key(s, inputs) and not self.disagreement(s):
                    why += " (its checks alone read it: they alone run)"
                return "stale", why
            bad = self.disagreement(s)
            if bad:
                return "stale", bad
            return "current", st.get("at", "") + ("" if st.get("key") else " (proved by its own record)")
        if st.get("built"):
            return "stale", "its check was red or never finished at the last run"
        if not s.proof:
            return "stale", "never run by the rebuild, and its output carries no proof of its inputs"
        bad = self.disagreement(s) or self.unproven(s)
        if bad:
            return "stale", f"never run by the rebuild; {bad}"
        return "proved", "by its own record" + ("; its checks alone run" if s.checks else "")


# ---- the order ----------------------------------------------------------------------------------------------------

def _feeds(write: str, read: str) -> bool:
    wk, _, wp = write.partition(":")
    rk, _, rp = read.partition(":")
    if wk != rk or wk == "ext":
        return False
    if wk == "db":
        return wp == "*" or wp == rp.split("[")[0]
    rp = rp.split("#")[0]
    return rp == wp or rp.startswith(wp + "/") or wp.startswith(rp + "/") or fnmatch.fnmatch(wp, rp)


def deps(stages: tuple, waits: bool = True) -> dict[str, list[str]]:
    """For each stage, the stages that write something it reads and, with `waits`, the stages it waits for without
    reading them. A table named by a narrower writer (`db:x`) is that writer's; `db:*` writes every other table."""
    narrow = {w for s in stages for w in s.writes if w.startswith("db:") and w != "db:*"}
    out: dict[str, list[str]] = {}
    names = {s.name for s in stages}
    for s in stages:
        if set(s.after) - names:
            raise ValueError(f"{s.name} waits for {sorted(set(s.after) - names)}: no such stage")
        need = list(s.after) if waits else []
        for o in stages:
            if o.name == s.name:
                continue
            for w in o.writes:
                for r in s.reads:
                    if w == "db:*" and f"db:{r.partition(':')[2].split('[')[0]}" in narrow:
                        continue
                    if _feeds(w, r) and o.name not in need:
                        need.append(o.name)
        out[s.name] = need
    return out


def order(stages: tuple) -> list[str]:
    """The stages in dependency order, ties in the order STAGES lists them; a cycle is an error."""
    d = deps(stages)
    done: list[str] = []
    left = [s.name for s in stages]
    while left:
        ready = [n for n in left if all(x in done for x in d[n])]
        if not ready:
            raise ValueError(f"the stages' reads and writes make a cycle among: {', '.join(left)}")
        done.append(ready[0])
        left.remove(ready[0])
    return done


def plan(tree: Tree, force: tuple = ()) -> list[dict]:
    """Every stage in order with its state: `current`; `stale` with its own reason (it runs); `proved` by its own
    tool's record (its checks alone run, and the run marks it); or `follows` a stale stage it reads from (it runs
    only if that stage changes what it reads)."""
    d, reads = deps(tree.stages), deps(tree.stages, waits=False)
    rows, moved = [], set()
    for name in order(tree.stages):
        s = tree.by_name[name]
        state, why = tree.own_state(s)
        if name in force:
            state, why = "stale", "forced"
        up = [x for x in reads[name] if x in moved]
        if state != "stale" and up:
            state, why = "follows", f"{', '.join(up)}: runs only if what it reads changes"
        if state in ("stale", "follows"):
            moved.add(name)
        rows.append({"stage": name, "what": s.what, "after": d[name], "state": state, "why": why,
                     "minutes": s.minutes, "gb": s.gb})
    tree.save_cache()
    return rows


def print_plan(rows: list[dict], file=None) -> None:
    file = file or sys.stdout
    print("order (derived from what each stage reads and writes):", file=file)
    for i, r in enumerate(rows, 1):
        print(f"  {i:2d}. {r['stage']:<11} after {', '.join(r['after']) or '-'}", file=file)
    st = [r for r in rows if r["state"] == "stale"]
    fo = [r for r in rows if r["state"] == "follows"]
    if st:
        print(f"stale: {len(st)} of {len(rows)} (about {sum(r['minutes'] for r in st):.0f} min of stage time, largest peak "
              f"{max(r['gb'] for r in st)} GB); {len(fo)} follow (up to {sum(r['minutes'] for r in fo):.0f} min more)", file=file)
    else:
        print(f"stale: 0 of {len(rows)}: every stage is current" + (" or proved" if any(r["state"] == "proved" for r in rows) else ""), file=file)
    for r in rows:
        print(f"  {r['state']:<7} {r['stage']:<11} {r['why']}", file=file)


# ---- preflight ----------------------------------------------------------------------------------------------------

BUSY = re.compile(r"python\S*\s+(-\S+\s+)*-m\s+tools\.(newworld\.(?!rebuild\s+(plan|preflight)|verify|map_page)|navmesh\s+build|places\s+(build|finalise|draft|seat|extract))"
                  r"|tools[./]places[./]finalise|(^|[\s/])(world|rebuild)\.sh(\s|$)")


def _git(repo: Path, *a: str, timeout: int = 40) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True, timeout=timeout)


def mem_available_gb() -> float:
    for ln in Path("/proc/meminfo").read_text().splitlines():
        if ln.startswith("MemAvailable:"):
            return int(ln.split()[1]) / 1e6
    return 0.0


def others_running() -> list[str]:
    """Other writers of out/: a place build, a studio finalise, a stage tool or another rebuild, outside this
    process's own group."""
    mine, hits = os.getpgid(0), []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            cmd = (d / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()
            if cmd and BUSY.search(cmd) and os.getpgid(int(d.name)) != mine and "job_guard.sh" not in cmd:
                hits.append(f"pid {d.name}: {cmd[:110]}")
        except (OSError, ValueError):
            continue
    return hits


def not_the_writer(tree: Tree) -> str | None:
    """Why this tree may not write out/, or None. The main tree is the one writer: a worktree's out/ is hard links
    to the main tree's files, and a stage that writes there writes the main tree's build."""
    gd, cd = (_git(tree.repo, "rev-parse", "--path-format=absolute", a).stdout.strip() for a in ("--git-dir", "--git-common-dir"))
    return None if gd == cd else f"a worktree of {Path(cd).parent}"


def preflight(tree: Tree, rows: list[dict]) -> list[tuple[str, bool, str]]:
    """Everything checkable before the first long stage: (what, ok, detail) rows."""
    out: list[tuple[str, bool, str]] = []
    stale = [tree.by_name[r["stage"]] for r in rows if r["state"] != "current"]
    # the tree: the one writer is the main tree, level with origin/main
    why = not_the_writer(tree)
    out.append(("this is the main tree, the one writer of out/ (a worktree only plans)", why is None, why or ""))
    f = _git(tree.repo, "fetch", "--quiet", "origin", "main")
    if f.returncode:
        out.append(("the tree is level with origin/main", False, "git fetch origin main failed: " + f.stderr.strip()[:120]))
    else:
        behind = _git(tree.repo, "rev-list", "--count", "HEAD..origin/main").stdout.strip()
        out.append(("the tree is level with origin/main", behind == "0", "" if behind == "0" else f"{behind} commits behind: git pull --rebase"))
    busy = others_running()
    out.append(("no other rebuild, place build, studio finalise or stage tool is running", not busy, "; ".join(busy[:3])))
    # inputs
    miss = [p for p in EXTERNAL if not (tree.out / p).exists()]
    out.append(("the map extraction's outputs are present", not miss, "missing out/" + ", out/".join(miss) if miss else ""))
    miss = sorted({r.split(":", 1)[1] for s in stale for r in s.reads + s.check_reads if r.startswith(("src:", "ext:", "laid:"))
                   and not any(c in r for c in "*?[") and tree.digest(r) == "absent"
                   and r not in {w for o in tree.stages for w in o.writes}})
    out.append(("every source, tool and game file a stale stage reads is present", not miss, "missing " + ", ".join(miss[:6]) if miss else ""))
    # the records a build is judged against, and held ground for every built place
    acc = ["newworld/sources/water_accepted.json", "newworld/sources/terrain_needs_accepted.json",
           "newworld/sources/terrain_held.json", "newworld/sources/water_owner_bodies.png"]
    miss = [a for a in acc if not (tree.repo / a).exists()]
    out.append(("the accepted records are present (water kinds, terrain needs, held ground, the owner's water)", not miss, ", ".join(miss)))
    held = tree.repo / "newworld/sources/terrain_held.json"
    built = sorted(p.parent.name for p in (tree.repo / "newworld/places").glob("*/place.json"))
    rows_held = set(json.loads(held.read_text()).get("places", {})) if held.exists() else set()
    out.append(("every built place has its held-ground row", set(built) <= rows_held, "no row for " + ", ".join(sorted(set(built) - rows_held)) if set(built) - rows_held else ", ".join(built)))
    # the machine
    free = shutil.disk_usage(tree.out if tree.out.exists() else tree.repo).free / 1e9
    out.append((f"disk: {DISK_GB:.0f} GB free under out/", free >= DISK_GB, f"{free:.1f} GB free"))
    need = max((s.gb for s in stale), default=0.0) + RESERVE_GB
    have = mem_available_gb()
    out.append((f"memory: {need:.1f} GB available (the largest stale stage's peak + {RESERVE_GB:.0f})", have >= need, f"{have:.1f} GB available"))
    # every stale stage's tool starts: an import error is found now, not at its turn
    mods = sorted({m for s in stale for c in s.cmds + s.checks for m in tool_modules(c)})
    if mods:
        p = subprocess.run([tree.py, "-c", "import importlib,sys\nfor m in sys.argv[1:]:\n    importlib.import_module(m)", *mods],
                           cwd=tree.repo, capture_output=True, text=True)
        out.append(("every stale stage's tool imports", p.returncode == 0, (p.stderr.strip().splitlines() or [""])[-1][:160]))
    if any(c[0] == "dotnet" or "world.sh" in c[0] for s in stale for c in s.cmds + s.checks):
        ok = shutil.which("dotnet") is not None or (Path.home() / ".dotnet/dotnet").exists()
        out.append(("dotnet is installed", ok, ""))
    return out


def tool_modules(argv: tuple) -> list[str]:
    """The Python modules a command runs: the `-m` module, and the tool a keyed command wraps."""
    from tools.newworld import keyed
    out = []
    for i, t in enumerate(argv[:-1]):
        if t == "-m":
            out.append(argv[i + 1])
            if argv[i + 1] == keyed.__name__ and len(argv) > i + 2:
                out += keyed.TOOLS[argv[i + 2]][::2]
    return out


def print_preflight(rows: list[tuple[str, bool, str]]) -> bool:
    for what, ok, detail in rows:
        print(f"  {'ok  ' if ok else 'FAIL'} {what}" + (f": {detail}" if detail else ""))
    return all(ok for _, ok, _ in rows)


# ---- the run ------------------------------------------------------------------------------------------------------

def _env() -> dict:
    dn = str(Path.home() / ".dotnet")
    return dict(os.environ, DOTNET_ROOT=dn, PATH=f"{dn}:{os.environ.get('PATH', '')}", DOTNET_CLI_TELEMETRY_OPTOUT="1",
                DOTNET_NOLOGO="1", PYTHONUNBUFFERED="1")


class Run:
    def __init__(self, tree: Tree, todo: list[str], budget_gb: float, echo=print):
        self.tree, self.todo, self.budget, self.echo = tree, list(todo), budget_gb, echo
        self.deps = deps(tree.stages)
        self.done: dict[str, dict] = {}          # stage -> result
        self.running: dict[str, Stage] = {}
        self.q: queue.Queue = queue.Queue()
        self.red: str | None = None
        self.lock = threading.Lock()

    def _say(self, name: str, line: str) -> None:
        with self.lock:
            self.echo(f"[{name}] {line}")

    def _one(self, s: Stage, argv: tuple, log, stage_key: str | None = None) -> tuple[int, list[str]]:
        argv = [self.tree.py if a == PY else a for a in argv]
        self._say(s.name, "$ " + " ".join(argv))
        env = _env()
        env.pop("NW_STAGE_KEY", None)
        if stage_key:
            env["NW_STAGE_KEY"] = stage_key
        p = subprocess.Popen(argv, cwd=self.tree.repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             errors="replace")
        tail: list[str] = []
        for ln in p.stdout:
            ln = ln.rstrip("\n")
            log.write(ln + "\n")
            log.flush()
            if ln.strip():
                tail.append(ln)
                del tail[:-400]
            self._say(s.name, ln)
        return p.wait(), tail

    def _stage(self, s: Stage) -> None:
        t0 = time.time()
        tree = self.tree
        res = {"stage": s.name, "result": "green", "line": ""}
        try:
            inputs = tree.inputs(s)
            key, bkey = tree.key_of(inputs), tree.build_key(s, inputs)
            st = tree.stamp(s)
            forced = s.name in self.forced
            state, _ = ("stale", "") if forced else tree.own_state(s, inputs)
            if state == "current":
                res.update(result="skipped", line="its inputs are unchanged")
                return
            at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            # the commands stand when the record says they finished on this build key: the checks alone run
            built = state == "proved" or (not forced and not st.get("running") and st.get("built") == bkey
                                          and tree.disagreement(s) is None)
            # a stage tool that keeps a key of its own is told this build key, so it skips only what it built for
            # it; a stage with no record is left to its tool's own key, and a stopped run is resumed as it began
            if forced:
                stage_key = f"{bkey}-forced-{at}"
            elif not st:
                stage_key = None
            else:
                stage_key = st.get("stage_key") if st.get("running") == bkey else bkey
            (tree.state / "logs").mkdir(parents=True, exist_ok=True)
            with open(tree.state / "logs" / f"{s.name}.log", "w") as log:
                for kind, cmds in (("stage", () if built else s.cmds), ("check", s.checks)):
                    if kind == "stage" and cmds:
                        tree.write_stamp(s, {"running": bkey, "stage_key": stage_key, "at": at})
                    for argv in cmds:
                        rc, tail = self._one(s, argv, log, stage_key if kind == "stage" else None)
                        if rc:
                            hit = [ln for ln in tail if re.search(r"\bFAIL\b|Error|error:|Traceback", ln)][-8:] or tail[-5:]
                            res.update(result="red", failed=kind, line="\n".join(hit), rc=rc)
                            return
                    if kind == "stage" and state != "proved":      # the commands stand: a check is repeated alone
                        tree.write_stamp(s, {"built": bkey, "at": at})
            # the stage's own tracked or database outputs may be among another stage's reads, never its own
            bad = tree.disagreement(s)
            if bad:
                res.update(result="red", failed="stage", line=f"after a green run {bad}")
                return
            if state == "proved":
                tree.write_stamp(s, {"proved": key, "built": bkey, "inputs": inputs, "at": at})
                res.update(result="proved", line="its own record proves it" + ("; its checks are green" if s.checks else ""))
                return
            tree.write_stamp(s, {"key": key, "built": bkey, "inputs": inputs, "seconds": round(time.time() - t0, 1), "at": at})
        except Exception as e:  # a stage that cannot start is a red stage, never a hung run
            res.update(result="red", failed="stage", line=f"{type(e).__name__}: {e}")
        finally:
            res["seconds"] = round(time.time() - t0, 1)
            self.q.put(res)

    def go(self, forced: tuple = ()) -> dict[str, dict]:
        self.forced = set(forced)
        left = [n for n in order(self.tree.stages) if n in self.todo]
        while left or self.running:
            if not self.red:
                for name in list(left):
                    s = self.tree.by_name[name]
                    if any(d in left or d in self.running for d in self.deps[name]):
                        continue
                    if any(self.done.get(d, {}).get("result") == "red" for d in self.deps[name]):
                        continue
                    if self.running and (s.alone or any(r.alone for r in self.running.values())):
                        continue
                    if s.lock and any(r.lock == s.lock for r in self.running.values()):
                        continue
                    if self.running and sum(r.gb for r in self.running.values()) + s.gb > self.budget:
                        continue
                    left.remove(name)
                    self.running[name] = s
                    self._say(name, f"start: {s.what}" + (f" (beside {', '.join(n for n in self.running if n != name)})" if len(self.running) > 1 else ""))
                    threading.Thread(target=self._stage, args=(s,), daemon=True).start()
            if not self.running:
                break
            res = self.q.get()
            name = res["stage"]
            del self.running[name]
            self.done[name] = res
            self._say(name, f"{res['result']} in {res['seconds']:.0f} s" + (f": {res['line']}" if res["result"] in ("skipped", "proved") else ""))
            if res["result"] == "red" and not self.red:
                self.red = name
                self._say(name, f"RED at its {res['failed']}; nothing new starts" + (f"; waiting for {', '.join(self.running)}" if self.running else ""))
                for ln in res["line"].splitlines():
                    self._say(name, "  " + ln)
        for name in left:
            self.done[name] = {"stage": name, "result": "not run", "line": f"stopped at {self.red}", "seconds": 0}
        return self.done


def downstream(tree: Tree, ran: list[str]) -> list[str]:
    places = sorted(p.parent.name for p in (tree.repo / "newworld/places").glob("*/place.json"))
    out = []
    for what, feeders, where in DOWNSTREAM:
        hit = [f for f in feeders if f in ran]
        if hit and ("{places}" not in what or places):
            out.append(f"{what.format(places=', '.join(places))}: stale after {', '.join(hit)} ({where})")
    return out


def summary(tree: Tree, rows: list[dict], done: dict[str, dict]) -> dict:
    ran = [n for n, r in done.items() if r["result"] == "green"]
    red = [n for n, r in done.items() if r["result"] == "red"]
    skipped = [r["stage"] for r in rows if r["state"] == "current"] + [n for n, r in done.items() if r["result"] == "skipped"]
    proved = [n for n, r in done.items() if r["result"] == "proved"]
    checks_ok = sum(len(tree.by_name[n].checks) for n in ran + proved)
    tracked = _git(tree.repo, "status", "--short", "--", "mods/dependencies.json", "newworld/story/data/db").stdout.splitlines()
    doc = {"ran": ran, "skipped": skipped, "proved": proved, "red": red,
           "not_run": [n for n, r in done.items() if r["result"] == "not run"],
           "checks_passed": checks_ok, "checks_failed": [f"{n}: {done[n]['failed']}" for n in red],
           "downstream": downstream(tree, ran), "tracked_changes": [t.strip() for t in tracked],
           "seconds": {n: r["seconds"] for n, r in done.items() if r["seconds"]}}
    tree.state.mkdir(parents=True, exist_ok=True)
    (tree.state / "summary.json").write_text(json.dumps(doc, indent=1))
    return doc


def print_summary(doc: dict) -> None:
    print("summary")
    print(f"  stages run: {len(doc['ran'])}" + (f" ({', '.join(doc['ran'])})" if doc["ran"] else ""))
    print(f"  stages skipped as current: {len(doc['skipped'])}" + (f" ({', '.join(doc['skipped'])})" if doc["skipped"] else ""))
    if doc.get("proved"):
        print(f"  stages proved by their own record, their checks run: {len(doc['proved'])} ({', '.join(doc['proved'])})")
    print(f"  checks passed: {doc['checks_passed']} commands; failed: {', '.join(doc['checks_failed']) or 'none'}")
    if doc["not_run"]:
        print(f"  not run: {', '.join(doc['not_run'])}")
    for d in doc["downstream"]:
        print(f"  now stale beyond this build: {d}")
    if not doc["downstream"]:
        print("  nothing beyond this build went stale")
    if doc["tracked_changes"]:
        print("  tracked files the run rewrote, to commit by path: " + ", ".join(doc["tracked_changes"]))


def take_lock(pidf: Path) -> str | None:
    """Take the one-writer lock, or say who holds it. The file appears whole or not at all (a hard link to a file
    that already holds this pid), so two rebuilds started together cannot both take it; a lock is removed only when
    the process it names is dead."""
    pidf.parent.mkdir(parents=True, exist_ok=True)
    mine = pidf.with_name(f"{pidf.name}.{os.getpid()}")
    mine.write_text(str(os.getpid()))
    try:
        for _ in range(2):
            try:
                os.link(mine, pidf)
                return None
            except FileExistsError:
                try:
                    pid = int(pidf.read_text())
                    os.kill(pid, 0)
                except (ValueError, ProcessLookupError, FileNotFoundError):
                    pidf.unlink(missing_ok=True)        # the rebuild it names is dead
                    continue
                except PermissionError:
                    pass
                return f"another rebuild (pid {pidf.read_text().strip()}) is running"
        return "another rebuild took the lock"
    finally:
        mine.unlink(missing_ok=True)


def run(tree: Tree, to: str | None = None, force: tuple = (), budget_gb: float | None = None, check_first: bool = True) -> int:
    for n in (*force, *([to] if to else [])):
        if n not in tree.by_name:
            print(f"no stage {n!r}; stages: {', '.join(order(tree.stages))}", file=sys.stderr)
            return 2
    tree.fresh = True        # a run decides by content, never by the digest cache
    rows = plan(tree, force)
    print_plan(rows)
    names = order(tree.stages)
    todo = [r["stage"] for r in rows if r["state"] != "current"]
    if to:
        d = deps(tree.stages)
        keep, stack = set(), [to]
        while stack:
            n = stack.pop()
            if n not in keep:
                keep.add(n)
                stack += d[n]
        todo = [n for n in todo if n in keep]
    if not todo:
        print_summary(summary(tree, rows, {}))
        return 0
    if not_the_writer(tree):
        print(f"refused: this is {not_the_writer(tree)}; the main tree is the one writer of out/", file=sys.stderr)
        return 2
    pidf = tree.state / "run.pid"
    held = take_lock(pidf)
    if held:
        print(held, file=sys.stderr)
        return 2
    try:
        if check_first:
            print("preflight")
            if not print_preflight(preflight(tree, rows)):
                print("preflight red: nothing was run")
                return 2
        budget = budget_gb if budget_gb is not None else max(mem_available_gb() - RESERVE_GB, 1.0)
        print(f"run: {len(todo)} stages ({', '.join(n for n in names if n in todo)}); side by side within {budget:.1f} GB")
        done = Run(tree, todo, budget).go(force)
    finally:
        pidf.unlink(missing_ok=True)
        tree.save_cache()
    doc = summary(tree, rows, done)
    print_summary(doc)
    return 1 if doc["red"] else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="the order and each stage's state; writes nothing but the digest cache, which no run reads")
    sub.add_parser("preflight", help="everything checkable before the first long stage")
    r = sub.add_parser("run", help="run the stale stages")
    r.add_argument("--to", help="only the stale stages this stage needs, and itself")
    r.add_argument("--force", action="append", default=[], help="treat this stage as stale (repeatable)")
    r.add_argument("--budget-gb", type=float, help="memory the stages may use side by side (default: available less 2)")
    a = ap.parse_args(argv)
    tree = Tree()
    if a.cmd == "plan":
        print_plan(plan(tree))
        return 0
    if a.cmd == "preflight":
        return 0 if print_preflight(preflight(tree, plan(tree))) else 1
    return run(tree, a.to, tuple(a.force), a.budget_gb)


if __name__ == "__main__":
    sys.exit(main())
