"""The new world's grid as the navmesh reads it: the world plugin's own land snapshot, and which cells get a navmesh.

    Land.load(plugin_dir)   out/newworld/plugin/land/manifest.json (tools/newworld/world/land.py): the grid, the build id
                            and the limited heights (land/limited.npy, VHGT steps; x 8 = the heights the game has)
    navmesh_cells(land)     the Skyrim cells that may hold a navmesh: inside the cell table (newworld/story/data/db/
                            cell.jsonl, Morrowind cells of 8192 units, two Skyrim cells a side) and not 'margin'
                            (border scenery past the province). Deep sea is left to Recast (params.WATER_MAX_DEPTH):
                            a cell with nothing walkable gets no NAVM.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tools.newworld.world import units as nwu

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "out" / "newworld" / "plugin"
CELL_TABLE = ROOT / "newworld" / "story" / "data" / "db" / "cell.jsonl"
PLACES = ROOT / "newworld" / "story" / "data" / "db" / "place.jsonl"
ROADS = ROOT / "newworld" / "story" / "data" / "db" / "road_vertex.jsonl"
CELL_UNITS = nwu.CELL_UNITS
VERTEX_SPACING_UNITS = nwu.VERTEX_SPACING_UNITS
LAND_VERTS = nwu.LAND_VERTS
QUADS_PER_CELL = nwu.QUADS_PER_CELL
UNITS_PER_METRE = nwu.UNITS_PER_METRE
WORLD_LOCAL = 0x800  # NewWorld.cs IdWorld: the WRLD's FormID in ArgoniaNewWorld.esm
SELF_FILE = "ArgoniaNewWorld.esm"


def cell_origin(x: int, y: int) -> tuple[int, int]:
    """The south-west corner of Skyrim cell (x, y) in world units."""
    return x * CELL_UNITS, y * CELL_UNITS


@dataclass
class Land:
    grid: nwu.Grid
    build_id: str
    key: str
    dir: Path

    @classmethod
    def load(cls, plugin_dir: Path = PLUGIN) -> "Land":
        man = json.loads((plugin_dir / "land" / "manifest.json").read_text())
        g = man["grid"]
        grid = nwu.Grid(build_id=man["build_id"], width=g["width"], height=g["height"], origin_x=g["origin_x"],
                        origin_y=g["origin_y"], water=g["water"])
        return cls(grid, man["build_id"], man["key"], plugin_dir)

    def heights(self) -> np.ndarray:
        """(rows, cols) float32 game units, row 0 north: the limited VHGT steps x 8, exactly what the LAND holds."""
        lim = np.load(self.dir / "land" / "limited.npy", mmap_mode="r")
        return (np.asarray(lim, np.float32) * nwu.VHGT_STEP_UNITS).astype(np.float32)

    @property
    def box(self) -> tuple[int, int, int, int]:
        g = self.grid
        return g.cx0, g.cy_bottom, g.cx0 + g.cells_x - 1, g.cy_top


def table_cells(path: Path = CELL_TABLE) -> dict[tuple[int, int], dict]:
    out = {}
    for ln in path.read_text().splitlines():
        if ln.strip():
            r = json.loads(ln)
            out[(r["x"], r["y"])] = r
    return out


def navmesh_cells(land: Land, table: dict | None = None) -> set[tuple[int, int]]:
    """Skyrim cells of the grid, one cell in from its edge (the input window reads two samples past a cell), whose
    Morrowind cell is in the table and not margin."""
    table = table_cells() if table is None else table
    x0, y0, x1, y1 = land.box
    out = set()
    for y in range(y0 + 1, y1):
        for x in range(x0 + 1, x1):
            r = table.get((x // 2, y // 2))
            if r is not None and not r.get("margin", 0):
                out.add((x, y))
    return out


def settlements() -> list[dict]:
    """Every dry-sited place (not on water) as {id, name, kind, x, y}, world units."""
    out = []
    for ln in PLACES.read_text().splitlines():
        if ln.strip():
            p = json.loads(ln)
            if not p.get("on_water"):
                out.append({"id": p["id"], "name": p["name"], "kind": p.get("place_kind_id"), "x": p["world_x"], "y": p["world_y"]})
    return out


def road_polylines() -> list[list[tuple[float, float, bool]]]:
    """Each road's vertices in order: (world x, world y, on water)."""
    by: dict[str, list] = {}
    for ln in ROADS.read_text().splitlines():
        if ln.strip():
            v = json.loads(ln)
            by.setdefault(v["road_id"], []).append((v["seq"], v["world_x"], v["world_y"], bool(v.get("on_water"))))
    return [[(x, y, w) for _, x, y, w in sorted(vs)] for _, vs in sorted(by.items())]
