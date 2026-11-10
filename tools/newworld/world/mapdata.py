"""The new world's map and LOD inputs (nw-02 step 11), from the current land build; the LOD stage's off-game checks.

    python3 -m tools.newworld.world.mapdata build [--plugin out/newworld/plugin]
        -> <plugin>/map/markers.json  one map marker per settlement of place.jsonl (family "settlement" in
                                       place_kind.jsonl): name, kind -> MapMarker type, x, y, z on the limited land
                                       (or the water surface), discovered only for the start place
           <plugin>/map/map.json      the WRLD's map fields: the camera's pan box over the whole province (the
                                       scope less its margin, out/newworld/scope_cells.json and margin_cells.json:
                                       land, sea and islands), kept MAP_MARGIN cells inside the built cells; the
                                       camera's heights scaled from Tamriel's for the box's size; usable size 0,0 as
                                       Tamriel's (map_box, camera)
           <plugin>/map/LODSettings/ArgoniaBlackMarsh.lod   the 16-byte LOD settings the engine and xLODGen read
                                       (Data\\LODSettings\\<world>.lod; lodsettings.py's format and rule)
           <plugin>/map/teleports.json, teleports.md   the named teleport cells (tools/newworld/teleports.py)
           <plugin>/map/lodplan.json   which placed bases get LOD and how (tools/newworld/world/lodplan.py)
    python3 -m tools.newworld.world.mapdata expect [--plugin ...]   the terrain LOD files the world needs, per level
    python3 -m tools.newworld.world.mapdata check <listing.txt> [--plugin ...]   expected vs found per level (a
        listing of the LOD mod's files, one relative path a line, as lod.sh fetches it); exit 1 on any missing
    python3 -m tools.newworld.world.mapdata checkmap [--plugin ...]   the pan box against the province; exit 1 on a fault

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
SCOPE = REPO / "out/newworld"  # scope_cells.json, margin_cells.json (tools/newworld/tiles.py scope)
MAP_MARGIN = 3  # cells the pan box keeps inside the built cells: Tamriel's least (south: box -40, LAND to -43)
TAMRIEL_BOX = (70, 55)  # Tamriel's MNAM box NW(-30,15) SE(40,-40), measured in Skyrim.esm
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


def province_cells(scope_dir: Path) -> set[tuple[int, int]]:
    """The province's Skyrim cells: scope_cells.json less margin_cells.json (tools/newworld/tiles.py), whose map
    cells are 2 x 2 Skyrim cells."""
    scope = {tuple(c) for c in json.loads((scope_dir / "scope_cells.json").read_text())}
    margin = {tuple(c) for c in json.loads((scope_dir / "margin_cells.json").read_text())}
    return {(2 * mx + i, 2 * my + j) for mx, my in scope - margin for i in (0, 1) for j in (0, 1)}


def map_box(g: su.Grid, scope_dir: Path) -> dict:
    """The map camera's pan box (MNAM NW/SE cells): the whole province, its sea and islands included, so the camera
    can centre on any of it; held at least MAP_MARGIN cells inside the built cells (Tamriel's box sits 3 cells inside
    its LAND on the south, its least margin), so beyond the box the camera looks over built land and sea."""
    prov = province_cells(scope_dir)
    px0, px1 = min(c[0] for c in prov), max(c[0] for c in prov)
    py0, py1 = min(c[1] for c in prov), max(c[1] for c in prov)
    gx0, gx1 = g.cx0 + MAP_MARGIN, g.cx0 + g.cells_x - 1 - MAP_MARGIN
    gy0, gy1 = g.cy_bottom + MAP_MARGIN, g.cy_top - MAP_MARGIN
    nw = [max(px0, gx0), min(py1, gy1)]
    se = [min(px1, gx1), max(py0, gy0)]
    return {"nw": nw, "se": se, "province": [px0, px1, py0, py1]}


def camera(box: dict) -> dict:
    """The map camera's heights and pitch (MNAM): Tamriel's 50000 / 80000 / 50 for its 70 x 55-cell box; the highest
    point scaled with the box's longer side (a bigger box needs a higher camera to see it whole), at most twice."""
    w = box["se"][0] - box["nw"][0]
    h = box["nw"][1] - box["se"][1]
    k = min(max(max(w / TAMRIEL_BOX[0], h / TAMRIEL_BOX[1]), 1.0), 2.0)
    return {"min_height": 50000.0, "max_height": round(80000.0 * k), "pitch": 50.0}


def check_map(plugin: Path, scope_dir: Path) -> list[str]:
    """Faults of map.json against the province: a province cell the pan box leaves out (more than the margin the
    view reaches past the box), a box outside the built cells."""
    g, _ = grid(plugin)
    mp = json.loads((plugin / "map" / "map.json").read_text())
    want = map_box(g, scope_dir)
    bad = []
    if mp["nw"] != want["nw"] or mp["se"] != want["se"]:
        bad.append(f"pan box NW{mp['nw']} SE{mp['se']}, the province gives NW{want['nw']} SE{want['se']}")
    px0, px1, py0, py1 = want["province"]
    if mp["nw"][0] - px0 > MAP_MARGIN or px1 - mp["se"][0] > MAP_MARGIN or py1 - mp["nw"][1] > MAP_MARGIN or mp["se"][1] - py0 > MAP_MARGIN:
        bad.append(f"province x {px0}..{px1} y {py0}..{py1} reaches past the box NW{mp['nw']} SE{mp['se']} by more than {MAP_MARGIN} cells")
    if mp["nw"][0] < g.cx0 or mp["se"][0] > g.cx0 + g.cells_x - 1 or mp["se"][1] < g.cy_bottom or mp["nw"][1] > g.cy_top:
        bad.append("pan box outside the built cells")
    return bad


def build(plugin: Path, scope_dir: Path = None) -> dict:
    scope_dir = scope_dir or SCOPE
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
    # the land: cells with any sample above the water
    dry = np.asarray(h[: g.cells_y * 32 + 1, : g.cells_x * 32 + 1]) > g.water
    q = su.QUADS_PER_CELL
    cell_dry = dry[:-1, :-1].reshape(g.cells_y, q, g.cells_x, q).any(axis=(1, 3))
    rows, cols = np.nonzero(cell_dry)
    lx0, lx1 = g.cx0 + int(cols.min()), g.cx0 + int(cols.max())
    ly1, ly0 = g.cy_top - int(rows.min()), g.cy_top - int(rows.max())
    box = map_box(g, scope_dir)
    lod = lod_settings(g)
    mp = {"build_id": g.build_id, "world": WORLD, "land_cells": [lx0, lx1, ly0, ly1],
          "nw": box["nw"], "se": box["se"], "province_cells": box["province"], "usable": [0, 0], "lod": list(lod),
          "camera": camera(box),
          # NAM0/NAM9 object bounds in cells as Mutagen reads them (Tamriel: land x-57..61 -> -57..62), x4096 on disk
          "bounds": [g.cx0, g.cy_bottom, g.cx0 + g.cells_x, g.cy_top + 1],
          "markers": len(markers)}
    out = plugin / "map"
    (out / "LODSettings").mkdir(parents=True, exist_ok=True)
    (out / "LODSettings" / f"{WORLD}.lod").write_bytes(struct.pack("<hhiii", *lod))
    (out / "markers.json").write_text(json.dumps({"build_id": g.build_id, "markers": markers}, indent=1))
    (out / "map.json").write_text(json.dumps(mp, indent=1))
    # the files nwmap apply reads beside these: the named teleport cells, and which bases get LOD and how
    from tools.newworld import teleports
    from tools.newworld.world import lodplan
    teleports.build(plugin)
    lodplan.build(plugin, plugin.parent / "lod" / "logs" / "coverage.json")
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
    ap.add_argument("cmd", choices=("build", "expect", "check", "checkmap"))
    ap.add_argument("listing", nargs="?")
    ap.add_argument("--plugin", default=str(REPO / "out/newworld/plugin"))
    ap.add_argument("--scope", default=str(SCOPE), help="the folder of scope_cells.json and margin_cells.json")
    a = ap.parse_args(argv)
    plugin = Path(a.plugin)
    if a.cmd == "build":
        print(json.dumps(build(plugin, Path(a.scope))))
        return 0
    if a.cmd == "checkmap":
        bad = check_map(plugin, Path(a.scope))
        mp = json.loads((plugin / "map" / "map.json").read_text())
        print(f"map box NW{mp['nw']} SE{mp['se']} province {mp.get('province_cells')} camera {mp.get('camera')}: {len(bad)} faults")
        for b in bad:
            print("  FAIL", b)
        return 1 if bad else 0
    if a.cmd == "expect":
        for lvl, files in expected(grid(plugin)[0]).items():
            print(f"level {lvl}: {len(files)} files")
        return 0
    return check(plugin, Path(a.listing))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
