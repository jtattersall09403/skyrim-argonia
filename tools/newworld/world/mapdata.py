"""The new world's map and LOD inputs (nw-02 step 11), from the current land build; the LOD stage's off-game checks.

    python3 -m tools.newworld.world.mapdata build [--plugin out/newworld/plugin]
        -> <plugin>/map/markers.json  one map marker per settlement of place.jsonl (family "settlement" in
                                       place_kind.jsonl): name, kind -> MapMarker type, x, y, z on the limited land
                                       (or the water surface), discovered only for the start place
           <plugin>/map/map.json      the WRLD's map fields: the province's land cells (a sample above water), the
                                       camera's pan box a quarter in from each side (Bethesda's convention, measured
                                       on Tamriel and Solstheim in tools/ArgoniaPlugin/MapFix.cs), usable size 0,0
           <plugin>/map/LODSettings/ArgoniaBlackMarsh.lod   the 16-byte LOD settings the engine and xLODGen read
                                       (Data\\LODSettings\\<world>.lod; lodsettings.py's format and rule)
    python3 -m tools.newworld.world.mapdata expect [--plugin ...]   the terrain LOD files the world needs, per level
    python3 -m tools.newworld.world.mapdata check <listing.txt> [--plugin ...]   expected vs found per level (a
        listing of the LOD mod's files, one relative path a line, as lod.sh fetches it); exit 1 on any missing

The expected set: for each level L in 4, 8, 16, 32, every L x L chunk on the .lod's grid that holds a LAND cell,
as meshes\\terrain\\<W>\\<W>.<L>.<x>.<y>.btr and textures\\terrain\\<W>\\<W>.<L>.<x>.<y>.dds (+ _n.dds), the names
xLODGen writes and the engine reads.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

from tools.newworld.world import units as su

REPO = Path(__file__).resolve().parents[3]
DB = REPO / "newworld/story/data/db"
WORLD = "ArgoniaBlackMarsh"
START_PLACE = "stormhold"  # land.py's start place: its marker is the one discovered at the start
LEVELS = (4, 8, 16, 32)
# place kind -> MapMarker type (Mutagen MapMarker.Types; the vanilla icons: city, town, settlement, camp, landmark)
MARKER_TYPE = {"city": "City", "town": "Town", "village": "Settlement", "hamlet": "Settlement",
               "outpost": "Camp", "belvedere": "Landmark"}


def grid(plugin: Path) -> tuple[su.Grid, dict]:
    man = json.loads((plugin / "land" / "manifest.json").read_text())
    g = man["grid"]
    return su.Grid(g["build_id"], g["width"], g["height"], g["origin_x"], g["origin_y"], g["water"]), man


def lod_settings(g: su.Grid) -> tuple[int, int, int, int, int]:
    """(south-west cell x, y, stride, lowest level, highest level): the SW corner on the level-32 grid, the stride the
    smallest power of two covering the land's span (Valenwood's own -32,-32,128,4,32 follows the same rule)."""
    x0 = (g.cx0 // 32) * 32
    y0 = (g.cy_bottom // 32) * 32
    span = max(g.cx0 + g.cells_x - x0, g.cy_top + 1 - y0)
    stride = 1
    while stride < span:
        stride *= 2
    return x0, y0, stride, LEVELS[0], LEVELS[-1]


def expected(g: su.Grid) -> dict[int, list[str]]:
    """Per level, the relative paths xLODGen writes for every chunk holding a LAND cell (all grid cells have LAND)."""
    x0, y0, stride, _, _ = lod_settings(g)
    cx1, cy1 = g.cx0 + g.cells_x - 1, g.cy_top
    out = {}
    for lvl in LEVELS:
        files = []
        for cx in range(x0, x0 + stride, lvl):
            if cx + lvl - 1 < g.cx0 or cx > cx1:
                continue
            for cy in range(y0, y0 + stride, lvl):
                if cy + lvl - 1 < g.cy_bottom or cy > cy1:
                    continue
                stem = f"{WORLD}.{lvl}.{cx}.{cy}"
                files += [f"meshes\\terrain\\{WORLD}\\{stem}.btr", f"textures\\terrain\\{WORLD}\\{stem}.dds",
                          f"textures\\terrain\\{WORLD}\\{stem}_n.dds"]
        out[lvl] = files
    return out


def build(plugin: Path) -> dict:
    g, man = grid(plugin)
    h = np.load(plugin / "land" / "limited.npy", mmap_mode="r")
    kinds = {json.loads(ln)["id"]: json.loads(ln) for ln in (DB / "place_kind.jsonl").read_text().splitlines() if ln.strip()}
    markers = []
    for ln in (DB / "place.jsonl").read_text().splitlines():
        if not ln.strip():
            continue
        p = json.loads(ln)
        if kinds.get(p["place_kind_id"], {}).get("family") != "settlement":
            continue
        col = round((p["world_x"] - g.origin_x) / su.VERTEX_SPACING_UNITS)
        row = round((g.origin_y - p["world_y"]) / su.VERTEX_SPACING_UNITS)
        if not (0 <= row < g.height and 0 <= col < g.width):
            raise ValueError(f"{p['id']} lies outside the land grid")
        x = g.origin_x + col * su.VERTEX_SPACING_UNITS
        y = g.origin_y - row * su.VERTEX_SPACING_UNITS
        z = max(float(h[row, col]), g.water) + 64.0
        markers.append({"place": p["id"], "name": p["name"], "kind": p["place_kind_id"],
                        "type": MARKER_TYPE[p["place_kind_id"]], "x": x, "y": y, "z": z,
                        "cell": [int(x // su.CELL_UNITS), int(y // su.CELL_UNITS)],
                        "discovered": p["id"] == START_PLACE})
    if sum(m["discovered"] for m in markers) != 1:
        raise ValueError(f"start place {START_PLACE} is not one settlement marker")
    # the province's land: cells with any sample above the water
    dry = np.asarray(h[: g.cells_y * 32 + 1, : g.cells_x * 32 + 1]) > g.water
    q = su.QUADS_PER_CELL
    cell_dry = dry[:-1, :-1].reshape(g.cells_y, q, g.cells_x, q).any(axis=(1, 3))
    rows, cols = np.nonzero(cell_dry)
    lx0, lx1 = g.cx0 + int(cols.min()), g.cx0 + int(cols.max())
    ly1, ly0 = g.cy_top - int(rows.min()), g.cy_top - int(rows.max())
    ix, iy = (lx1 - lx0) // 4, (ly1 - ly0) // 4
    lod = lod_settings(g)
    mp = {"build_id": g.build_id, "world": WORLD, "land_cells": [lx0, lx1, ly0, ly1],
          "nw": [lx0 + ix, ly1 - iy], "se": [lx1 - ix, ly0 + iy], "usable": [0, 0], "lod": list(lod),
          "markers": len(markers)}
    out = plugin / "map"
    (out / "LODSettings").mkdir(parents=True, exist_ok=True)
    (out / "LODSettings" / f"{WORLD}.lod").write_bytes(struct.pack("<hhiii", *lod))
    (out / "markers.json").write_text(json.dumps({"build_id": g.build_id, "markers": markers}, indent=1))
    (out / "map.json").write_text(json.dumps(mp, indent=1))
    return mp


def check(plugin: Path, listing: Path) -> int:
    g, _ = grid(plugin)
    have = {ln.strip().replace("/", "\\").lower() for ln in listing.read_text().splitlines() if ln.strip()}
    bad = 0
    for lvl, files in expected(g).items():
        miss = [f for f in files if f.lower() not in have]
        bad += len(miss)
        print(f"level {lvl:2}: expected {len(files)}, found {len(files) - len(miss)}"
              + (f"; missing e.g. {miss[:3]}" if miss else ""))
    lod = f"lodsettings\\{WORLD}.lod".lower()
    print(f"LODSettings\\{WORLD}.lod: {'found' if lod in have else 'MISSING'}")
    return 1 if bad or lod not in have else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "expect", "check"))
    ap.add_argument("listing", nargs="?")
    ap.add_argument("--plugin", default=str(REPO / "out/newworld/plugin"))
    a = ap.parse_args(argv)
    plugin = Path(a.plugin)
    if a.cmd == "build":
        print(json.dumps(build(plugin)))
        return 0
    if a.cmd == "expect":
        for lvl, files in expected(grid(plugin)[0]).items():
            print(f"level {lvl}: {len(files)} files")
        return 0
    return check(plugin, Path(a.listing))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
