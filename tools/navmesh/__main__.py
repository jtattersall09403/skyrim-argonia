"""The new world's navmesh (nw-02 step 10): every navmesh cell's NAVM and the NAVI, from the world plugin's own land.

    python -m tools.navmesh build [--cells x0,y0,x1,y1] [--plugin out/newworld/plugin] [--out DIR] [--no-check]
                                  [--refs DIR] [--no-placed]
        inputs.py (the LAND heights the world plugin holds, the one water level, the roads, the margin cells skipped,
        the collision of everything placed: every producer's refs shards under <plugin>/refs, placed.py) -> ArgoniaNav (DotRecast, per cell, 4 threads, cached per
        cell under DIR/cache) -> stitch.py (seams, edge links, NVNM, NAVI; cached per cell under DIR/stitch) ->
        checks.py (L1) and province.py (coverage, seams, components, settlement paths); writes DIR/navm,
        DIR/navi.json, DIR/check.json, DIR/build.json. Exit 1 when a check is red.
    python -m tools.navmesh sample [--plugin DIR] [--refs DIR] [--out DIR] [--only NAME]
        the fast test before a province build (a couple of minutes): each of SAMPLES, a block of 64 cells chosen
        for what goes wrong there, built on the bare ground and again round what is placed, into DIR/<name>-bare
        and DIR/<name> (default DIR: out/newworld/navmesh-samples). A sample is green when its checks are, every
        collidable reference is fed, and the road is on the mesh no less than on the bare ground. Exit 1 on a red one.
    python -m tools.navmesh check [--out DIR]     the checks again over a built DIR
    python -m tools.navmesh current [--plugin DIR] [--out DIR]
        exit 0 when DIR/build.json's key is the key of today's inputs (build_key): the navmesh need not be rebuilt

Default DIR: out/newworld/plugin/navmesh, which `tools/newworld/world/world.sh` hands to the ESM write
(tools/ArgoniaPlugin NewWorldNavmesh.cs). Interrupt-proof: both per-cell caches are keyed on each cell's own inputs,
so a rerun after a stop redoes only the cells not yet written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from tools.navmesh import world

ROOT = Path(__file__).resolve().parents[2]
NAV_PROJ = ROOT / "tools" / "navmesh" / "ArgoniaNav"
NAV_BIN = ROOT / "out" / "tools" / "ArgoniaNav" / "ArgoniaNav"
OUT = world.PLUGIN / "navmesh"
REFS = world.PLUGIN / "refs"
DOTNET_ENV = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_gcServer="0", DOTNET_NOLOGO="1",
                  DOTNET_CLI_TELEMETRY_OPTOUT="1", PATH=f"{Path.home() / '.dotnet'}:{os.environ.get('PATH', '')}")


def records_sha256(out: Path) -> str:
    h = hashlib.sha256()
    for p in sorted((out / "navm").glob("cy*.jsonl.gz")) + [out / "navi.json"]:
        h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


KEYED_CODE = ("inputs.py", "placed.py", "solid.py", "meshes.py", "nif.py", "bsa.py", "esm.py", "stitch.py", "nvnm.py", "params.py", "world.py",
              "ArgoniaNav/Program.cs", "ArgoniaNav/ArgoniaNav.csproj")  # what shapes the records; the checks do not


def build_key(plugin: Path, refs: Path | None) -> str:
    """What a whole-province build stands on, as one digest: the land's key, the cell table, the roads and the places
    it reads, every producer's refs shards and base lists, the mod order the meshes are found by, the Recast
    parameters and the code that shapes the records; with NW_STAGE_KEY set, that too. Stored in build.json by the
    build; `current` computes it again, and a build whose standing output carries today's key does nothing."""
    from tools.navmesh import meshes, params, placed
    h = hashlib.sha256()
    h.update(json.loads((plugin / "land" / "manifest.json").read_text())["key"].encode())
    h.update(json.dumps(params.recast(), sort_keys=True).encode())
    files = [NAV_PROJ.parent / f for f in KEYED_CODE] + [world.CELL_TABLE, world.ROADS, world.PLACES]
    if refs is not None:
        files += placed.shard_files(refs) + sorted(refs.glob("*/bases.json"))
        files.append(meshes.STACK / "profiles" / "NewWorld" / "modlist.txt")
    for f in files:
        h.update(f.name.encode() + (hashlib.sha256(f.read_bytes()).digest() if f.exists() else b"-"))
    stage = os.environ.get("NW_STAGE_KEY")  # the rebuild's digest of everything the stage reads (tools/newworld/rebuild.py)
    return h.hexdigest()[:16] + (f":{stage}" if stage else "")


def current(plugin: Path, out: Path) -> tuple[str | None, str]:
    """(the key the standing navmesh was built under, the key of today's inputs): equal when it need not be rebuilt.
    A build of part of the province (--cells) or of the bare ground (--no-placed) stores no key."""
    try:
        stored = json.loads((out / "build.json").read_text()).get("key")
    except (OSError, ValueError):
        stored = None
    return stored, build_key(plugin, plugin / "refs")


def build_tool() -> None:
    subprocess.run(["dotnet", "build", str(NAV_PROJ), "-c", "Release", "-o", str(NAV_BIN.parent), "-nologo", "-v", "q"],
                   check=True, env=DOTNET_ENV, capture_output=True)


def check(out: Path, cells: set | None = None) -> dict:
    from tools.navmesh import checks, province
    if cells is None:
        cells = {tuple(c) for c in json.loads((out / "in" / "cells.json").read_text())}
    t0 = time.time()
    res = checks.run(out)
    res["province"] = province.run(out, cells, checks.Rasters(out / "in"))
    p = res["province"]
    check_s = round(time.time() - t0, 1)
    res["green"] = bool(res["green"] and not p["coverage"]["land_cells_without_navm"] and not p["coverage"]["navm_outside_navmesh_cells"]
                        and not p["seams"]["mismatched"] and not p["seams"]["unmatched_segments"])
    (out / "check.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")  # no timing: the same inputs, the same bytes
    return {**res, "check_s": check_s}


def build(out: Path, box=None, plugin: Path = world.PLUGIN, run_check: bool = True, objects=None, cells=None,
          land=None, heights=None, polylines=None, after_inputs=None, refs: Path | None = None, resolver=None) -> dict:
    from tools.navmesh import inputs, stitch
    land = land or world.Land.load(plugin)
    box = tuple(box) if box else (land.box[0] + 1, land.box[1] + 1, land.box[2] - 1, land.box[3] - 1)
    cells = world.navmesh_cells(land) if cells is None else cells
    cells = {c for c in cells if box[0] <= c[0] <= box[2] and box[1] <= c[1] <= box[3]}
    t = {}
    t0 = time.time()
    build_tool()
    grid = inputs.write(out / "in", land, box, cells, objects=objects, polylines=polylines, heights=heights, refs=refs,
                        data=game_data(), resolver=resolver)
    if "placed" in grid:
        print(json.dumps({"placed": grid["placed"]}), flush=True)
    (out / "in" / "cells.json").write_text(json.dumps(sorted(cells)))
    if after_inputs:  # a test's hook: edit the rasters before the cells are read
        after_inputs(out / "in")
    t["inputs_s"] = round(time.time() - t0, 1)
    t0 = time.time()
    env = dict(DOTNET_ENV, DOTNET_GCHeapHardLimit="0xC0000000")
    r = subprocess.run([str(NAV_BIN), "cells", "--in", str(out / "in"), "--out", str(out)], env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"navmesh: ArgoniaNav failed\n{(r.stdout + r.stderr)[-3000:]}")
    t["recast_s"] = round(time.time() - t0, 1)
    t["recast_log"] = r.stdout.strip().splitlines()[-2:]
    t0 = time.time()
    g = land.grid
    totals = stitch.run(out, box, stitch.Grid(g.cx0, g.cy_bottom, g.cells_x), world.WORLD_LOCAL)
    t["stitch_s"] = round(time.time() - t0, 1)
    shutil.rmtree(out / "raw")
    print(f"cells: {totals['reused']} reused, {totals['built']} built", flush=True)
    navi = json.loads((out / "navi.json").read_text())
    navi["build_id"] = land.build_id  # NewWorldNavmesh.cs attaches the records only to the ESM of this land build
    (out / "navi.json").write_text(json.dumps(navi, sort_keys=True) + "\n")
    sha = records_sha256(out)
    res = {"box": list(box), "build_id": land.build_id, "times": t, "totals": totals, "sha256": sha}
    if "placed" in grid:  # objects: the placed references whose collision was fed to the voxeliser
        res["placed"] = {**grid["placed"], "objects": grid["placed"]["fed"]}
    if run_check:
        res["check"] = check(out, cells)
        t["check_s"] = res["check"].pop("check_s")
    (out / "build.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res


# The fast test's blocks, (x0, y0, x1, y1) in cells, each for what it holds
SAMPLES = {
    "jungle-road": (-16, -152, -9, -145),  # a hist grove and cypress swamp with a dressed road: wide root and trunk collision
    "upland": (-24, -176, -17, -169),  # upland scrub and outcrop: cliff pieces, boulders, a dressed road
    "marsh": (-40, -200, -33, -193),  # drowned forest and mangrove: trees standing in water, a road on the dry ground
    "town-approach": (-40, -160, -33, -153),  # the roads into Gul-Tej past mountain-trim pieces
    "coast-ridges": (36, -223, 43, -216),  # ridge pieces across a shore east of Lilmoth: ground closed in behind them
}


def sample(plugin: Path, refs: Path, out: Path, only: str | None = None) -> bool:
    from tools.navmesh import meshes
    meshes.PROFILE = "NewWorld"
    ok = True
    for name, box in SAMPLES.items():
        if only and name != only:
            continue
        bare = build(out / f"{name}-bare", box, plugin)["check"]
        res = build(out / name, box, plugin, refs=refs)
        ck, pl, comp = res["check"], res["check"]["placed"], res["check"]["province"]["components"]
        green = bool(ck["green"] and pl["fed"] == pl["collidable"] and ck["road"]["on_navmesh"] >= bare["road"]["on_navmesh"])
        ok &= green
        print(json.dumps({"sample": name, "green": green, "road": [ck["road"]["on_navmesh"], ck["road"]["samples"]],
                          "road_bare": bare["road"]["on_navmesh"], "heights_over": ck["heights"]["over"],
                          "fed": pl["fed"], "collidable": pl["collidable"], "cut_round_tall": pl["stands_tall"]["share"],
                          "band_triangles": pl["band_triangles"], "triangles": pl["triangles"],
                          "main_m2": comp["main_m2"], "main_m2_bare": bare["province"]["components"]["main_m2"],
                          "cut_off": [comp["cut_off_on_a_main_landmass"], comp["cut_off_m2"]],
                          "cut_off_bare": [bare["province"]["components"]["cut_off_on_a_main_landmass"], bare["province"]["components"]["cut_off_m2"]],
                          "largest_cut_off": comp["largest_cut_off"][:2], "cut_off_share": comp["cut_off_share"],
                          "shut_in": [ck["province"]["reach"]["places_in_a_cut_off_piece"], ck["province"]["reach"]["road_vertices_in_a_cut_off_piece"]],
                          "seams_mismatched": ck["province"]["seams"]["mismatched"],
                          "sha256": res["sha256"], "seconds": res["times"]}), flush=True)
    return ok


def game_data() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    return Path(root) / "Data" if root else Path.home() / "games" / "skyrimse" / "Data"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m tools.navmesh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--cells")
    b.add_argument("--plugin", default=str(world.PLUGIN))
    b.add_argument("--out", default=str(OUT))
    b.add_argument("--no-check", action="store_true")
    b.add_argument("--refs", help="the placed references' shards, <producer>/cy*.jsonl (default: <plugin>/refs)")
    b.add_argument("--no-placed", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--out", default=str(OUT))
    sm = sub.add_parser("sample", help="the fast test: five blocks of 64 cells, bare and round what is placed")
    sm.add_argument("--plugin", default=str(world.PLUGIN))
    sm.add_argument("--refs")
    sm.add_argument("--out", default=str(world.PLUGIN.parent / "navmesh-samples"))
    sm.add_argument("--only", choices=sorted(SAMPLES))
    k = sub.add_parser("current", help="exit 0 when the standing navmesh was built from today's inputs; writes nothing")
    k.add_argument("--plugin", default=str(world.PLUGIN))
    k.add_argument("--out")
    a = ap.parse_args(argv)
    if a.cmd == "current":
        try:
            stored, now = current(Path(a.plugin), Path(a.out or Path(a.plugin) / "navmesh"))
        except (OSError, ValueError, KeyError) as e:
            print(f"navmesh: no record to prove it ({type(e).__name__}: {e})")
            return 1
        print("navmesh: its key is today's" if stored == now else f"navmesh: its key {stored} is not today's {now}")
        return 0 if stored == now else 1
    out = Path(a.out)
    if a.cmd == "sample":
        return 0 if sample(Path(a.plugin), Path(a.refs or Path(a.plugin) / "refs"), out, a.only) else 1
    if a.cmd == "build" and not a.refs:
        a.refs = str(Path(a.plugin) / "refs")
    if a.cmd == "check":
        res = check(out)
        res.pop("check_s")
        print(json.dumps(res, sort_keys=True))
        return 0 if res["green"] else 1
    t0 = time.time()
    refs = None
    if not a.no_placed:
        from tools.navmesh import meshes, placed
        if not placed.shard_files(Path(a.refs)):
            raise SystemExit(f"navmesh: no placed-reference shards under {a.refs} (<producer>/cy*.jsonl): build the placement first, "
                             "or say --no-placed for a navmesh of the bare ground")
        meshes.PROFILE = "NewWorld"  # the new world's card: the BM&V stack plus the world-asset mods
        refs = Path(a.refs)
    box = tuple(int(v) for v in a.cells.split(",")) if a.cells else None
    whole = box is None and refs is not None and refs == Path(a.plugin) / "refs"
    key = build_key(Path(a.plugin), refs) if whole else None  # taken before the work: an input changed meanwhile shows
    if key and (out / "check.json").exists() and current(Path(a.plugin), out)[0] == key:
        print(f"navmesh: current (key {key}): nothing to build")
        return 0 if json.loads((out / "check.json").read_text())["green"] else 1
    res = build(out, box, Path(a.plugin), run_check=not a.no_check, refs=refs)
    if key:
        res["key"] = key
    res["times"]["wall_s"] = round(time.time() - t0, 1)
    (out / "build.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in ("box", "build_id", "times", "totals", "sha256")}, sort_keys=True))
    if "check" in res:
        ck = res["check"]
        print(json.dumps({k: ck[k] for k in ("green", "heights", "degenerate", "links", "islands", "navi", "road", "placed", "province")}, sort_keys=True))
        shut = ck["province"]["reach"]  # measured, not judged: the ground's own cut-off pieces are the terrain's to mend
        if shut["places_in_a_cut_off_piece"] or shut["road_vertices_in_a_cut_off_piece"]:
            print(f"navmesh: {shut['places_in_a_cut_off_piece']} places and {shut['road_vertices_in_a_cut_off_piece']} road vertices lie in a cut-off piece: "
                  f"{[p['id'] for p in shut['places']]} {shut['road'][:3]}")
        return 0 if ck["green"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
