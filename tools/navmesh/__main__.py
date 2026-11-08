"""The new world's navmesh (nw-02 step 10): every navmesh cell's NAVM and the NAVI, from the world plugin's own land.

    python -m tools.navmesh build [--cells x0,y0,x1,y1] [--plugin out/newworld/plugin] [--out DIR] [--no-check]
                                  [--refs DIR] [--no-placed]
        inputs.py (the LAND heights the world plugin holds, the one water level, the roads, the margin cells skipped,
        placed collision from the refs shards when present) -> ArgoniaNav (DotRecast, per cell, 4 threads, cached per
        cell under DIR/cache) -> stitch.py (seams, edge links, NVNM, NAVI; cached per cell under DIR/stitch) ->
        checks.py (L1) and province.py (coverage, seams, components, settlement paths); writes DIR/navm,
        DIR/navi.json, DIR/check.json, DIR/build.json. Exit 1 when a check is red.
    python -m tools.navmesh check [--out DIR]     the checks again over a built DIR

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
    res["green"] = bool(res["green"] and not p["coverage"]["land_cells_without_navm"] and not p["coverage"]["navm_outside_navmesh_cells"]
                        and not p["seams"]["mismatched"] and not p["seams"]["unmatched_segments"])
    res["check_s"] = round(time.time() - t0, 1)
    (out / "check.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res


def build(out: Path, box=None, plugin: Path = world.PLUGIN, run_check: bool = True, objects=None, cells=None,
          land=None, heights=None, polylines=None, after_inputs=None) -> dict:
    from tools.navmesh import inputs, stitch
    land = land or world.Land.load(plugin)
    box = tuple(box) if box else (land.box[0] + 1, land.box[1] + 1, land.box[2] - 1, land.box[3] - 1)
    cells = world.navmesh_cells(land) if cells is None else cells
    cells = {c for c in cells if box[0] <= c[0] <= box[2] and box[1] <= c[1] <= box[3]}
    t = {}
    t0 = time.time()
    build_tool()
    inputs.write(out / "in", land, box, cells, objects=objects, polylines=polylines, heights=heights)
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
    if run_check:
        res["check"] = check(out, cells)
        t["check_s"] = res["check"]["check_s"]
    (out / "build.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res


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
    b.add_argument("--refs", default=str(REFS), help="placed references, one JSON line each (placed.from_shards)")
    b.add_argument("--no-placed", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    out = Path(a.out)
    if a.cmd == "check":
        res = check(out)
        print(json.dumps(res, sort_keys=True))
        return 0 if res["green"] else 1
    t0 = time.time()
    objects = None
    if not a.no_placed and Path(a.refs).is_dir() and any(Path(a.refs).glob("*.jsonl")):
        from tools.navmesh import placed
        objects, tally = placed.from_shards(Path(a.refs), game_data())
        print(json.dumps({"placed": tally}), flush=True)
    box = tuple(int(v) for v in a.cells.split(",")) if a.cells else None
    res = build(out, box, Path(a.plugin), run_check=not a.no_check, objects=objects)
    res["times"]["wall_s"] = round(time.time() - t0, 1)
    (out / "build.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in ("box", "build_id", "times", "totals", "sha256")}, sort_keys=True))
    if "check" in res:
        ck = res["check"]
        print(json.dumps({k: ck[k] for k in ("green", "heights", "degenerate", "links", "islands", "navi", "road", "province")}, sort_keys=True))
        return 0 if ck["green"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
