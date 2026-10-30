"""The navmesh job (2.W4 §b; 0.4 §d navmesh (b)): every exterior cell's NAVM and the NAVI, from the game's ground.

    python -m tools.navmesh build (--block claywater | --cells x0,y0,x1,y1 | --province) [--out DIR] [--no-check] [--no-placed]
        inputs.py (the ground, water and road rasters; the built places' objects from placed.py) -> ArgoniaNav (DotRecast, per cell) -> stitch.py (seams,
        edge links, NVNM, NAVI) -> checks.py (L1); writes DIR/navm, DIR/navi.json, DIR/check.json, DIR/build.json
        (times, counts, the sha256 of the records). Exit 1 when a check is red.
    python -m tools.navmesh vanilla [--out DIR]
        the layout proof on Skyrim.esm (vanilla.py): the codec over every NAVM, the rules, and the 20-record round
        trip through ArgoniaGen and Mutagen
    python -m tools.navmesh block claywater      the block's cell box (db.py's place row, intermediate.py's mirror)

Default DIR: out/navmesh/<block|province|x0_y0_x1_y1>. ArgoniaWorld.esm takes it through `make navmesh`.
Needs the terrain's arrays in $ARGONIA_DATA, out/water/cells.jsonl (`make plugin` writes it) and the .NET SDK.
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

from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[2]
NAV_PROJ = ROOT / "tools" / "navmesh" / "ArgoniaNav"
NAV_BIN = NAV_PROJ / "bin" / "Release" / "net10.0" / "ArgoniaNav"
BLOCKS = {"claywater": "place.imperial-fringe.claywater-station"}
DOTNET_ENV = dict(os.environ, DOTNET_ROOT=str(Path.home() / ".dotnet"), DOTNET_gcServer="0", DOTNET_NOLOGO="1",
                  DOTNET_CLI_TELEMETRY_OPTOUT="1", DOTNET_GCHeapHardLimit="0x60000000",
                  PATH=f"{Path.home() / '.dotnet'}:{os.environ.get('PATH', '')}")


def block(name: str) -> tuple[int, int, int, int]:
    """The 8 x 8 cells around a place: its position row (metres from the province's NW corner, y south) through
    the mirror rule of intermediate._pos_exterior, the place's cell fourth from the block's south-west corner."""
    from tools.argonia_world import db
    rows = db.open().query("SELECT value FROM place_build_position_m WHERE place_id = ? ORDER BY ord", BLOCKS[name])
    x_m, y_m = (r[0] for r in rows[:2])
    cx, cy = su.cell_of(*su.province_to_skyrim(x_m, y_m))
    return cx - 3, cy - 3, cx + 4, cy + 4


def province() -> tuple[int, int, int, int]:
    x0, y0 = su.PROVINCE_CELL_SW
    span = (su.PROVINCE_SAMPLES - 1) // su.QUADS_PER_CELL
    return x0, y0, x0 + span - 1, y0 + span - 1


def records_sha256(out: Path) -> str:
    h = hashlib.sha256()
    for p in sorted((out / "navm").glob("cy*.jsonl.gz")) + [out / "navi.json"]:
        h.update(p.name.encode() + p.read_bytes())
    return h.hexdigest()


def build_tool() -> None:
    subprocess.run(["dotnet", "build", str(NAV_PROJ), "-c", "Release", "-nologo", "-v", "q"], check=True,
                   env=DOTNET_ENV, capture_output=True)


def build(box, out: Path, check: bool = True, objects=None) -> dict:
    from tools.navmesh import checks, inputs, stitch
    from tools.argonia_world.terrain import world

    t = {}
    t0 = time.time()
    build_tool()
    inputs.write(out / "in", box, objects=objects)
    t["inputs_s"] = round(time.time() - t0, 1)
    t0 = time.time()
    r = subprocess.run([str(NAV_BIN), "cells", "--in", str(out / "in"), "--out", str(out)], env=DOTNET_ENV,
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"navmesh: ArgoniaNav failed\n{(r.stdout + r.stderr)[-3000:]}")
    t["recast_s"] = round(time.time() - t0, 1)
    t["recast_warnings"] = sum(1 for line in (r.stdout + r.stderr).splitlines() if "dangling face" in line)
    t0 = time.time()
    gx0, gy0 = su.PROVINCE_CELL_SW[0] - su.APRON_CELLS, su.PROVINCE_CELL_SW[1] - su.APRON_CELLS
    gw = (su.PROVINCE_SAMPLES - 1) // su.QUADS_PER_CELL + 2 * su.APRON_CELLS
    totals = stitch.run(out, box, stitch.Grid(gx0, gy0, gw), world.WRLD_ID)
    t["stitch_s"] = round(time.time() - t0, 1)
    shutil.rmtree(out / "raw")
    res = {"box": list(box), "times": t, "totals": totals, "sha256": records_sha256(out)}
    if check:
        t0 = time.time()
        res["check"] = checks.run(out)
        t["check_s"] = round(time.time() - t0, 1)
        (out / "check.json").write_text(json.dumps(res["check"], indent=1, sort_keys=True) + "\n")
    (out / "build.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res


def game_data() -> Path:
    root = os.environ.get("ARGONIA_GAME_ROOT")
    return Path(root) / "Data" if root else Path.home() / "games" / "skyrimse" / "Data"


def main(argv=None) -> int:
    from tools.navmesh import placed
    ap = argparse.ArgumentParser(prog="python -m tools.navmesh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    g = b.add_mutually_exclusive_group(required=True)
    g.add_argument("--block", choices=sorted(BLOCKS))
    g.add_argument("--cells")
    g.add_argument("--province", action="store_true")
    b.add_argument("--out")
    b.add_argument("--no-check", action="store_true")
    b.add_argument("--no-placed", action="store_true", help="the ground only, without the built places' objects")
    v = sub.add_parser("vanilla")
    v.add_argument("--out", default=str(ROOT / "out" / "navmesh" / "vanilla"))
    k = sub.add_parser("block")
    k.add_argument("name", choices=sorted(BLOCKS))
    a = ap.parse_args(argv)
    if a.cmd == "block":
        print(",".join(map(str, block(a.name))))
        return 0
    if a.cmd == "vanilla":
        from tools.navmesh import vanilla
        res = {"survey": vanilla.survey(), "roundtrip": vanilla.roundtrip(Path(a.out))}
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "vanilla.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
        print(json.dumps(res, indent=1, sort_keys=True))
        rt = res["roundtrip"]
        return 0 if rt["nvnm_identical"] == rt["navm"] == 20 and res["survey"]["codec_identical"] == res["survey"]["navm"] else 1
    box = block(a.block) if a.block else province() if a.province else tuple(int(c) for c in a.cells.split(","))
    name = a.block or ("province" if a.province else "_".join(map(str, box)))
    out = Path(a.out) if a.out else ROOT / "out" / "navmesh" / name
    objects = None
    if not a.no_placed and placed.INTERMEDIATE.exists():  # the built places' references (placed.py)
        objects, tally = placed.triangles(game_data())
        print(json.dumps({"placed": tally}))
    res = build(box, out, check=not a.no_check, objects=objects)
    print(json.dumps({k: res[k] for k in ("box", "times", "totals", "sha256")}, sort_keys=True))
    if "check" in res:
        print(json.dumps(res["check"], sort_keys=True))
        return 0 if res["check"]["green"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
