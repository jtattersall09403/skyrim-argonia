"""Skyrim's LAND unit facts and the new world's cell grid, the one place they live for tools/newworld/world.

The grid is read from the terrain build (out/newworld/terrain/build.json, the row in
newworld/story/data/db/terrain_build.jsonl): a float32 heightmap in game units, row 0 the north edge, one sample per
LAND vertex (128 units), origin = the north-west corner in world units. A cell is 32 x 32 quads (33 x 33 vertices,
the edge shared with the neighbour), so the sample counts are 32 n + 1.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

VERTEX_SPACING_UNITS = 128  # LAND vertex spacing
CELL_UNITS = 4096  # an exterior cell's side
LAND_VERTS = 33  # LAND vertices per cell side
QUADS_PER_CELL = LAND_VERTS - 1  # 32
VHGT_STEP_UNITS = 8  # one VHGT signed-byte step
VHGT_DELTA_MAX = 127
VNML_SCALE = 127  # VNML: signed-byte unit normals x 127
UNITS_PER_METRE = 70.0  # the terrain build's own figure ("70 a metre", build.json "about")


@dataclass(frozen=True)
class Grid:
    build_id: str
    width: int  # samples, west to east
    height: int  # samples, north to south
    origin_x: float  # world units, west edge
    origin_y: float  # world units, north edge
    water: float  # units

    @property
    def cells_x(self) -> int:
        return (self.width - 1) // QUADS_PER_CELL

    @property
    def cells_y(self) -> int:
        return (self.height - 1) // QUADS_PER_CELL

    @property
    def cx0(self) -> int:  # the west column's cell x
        return int(self.origin_x) // CELL_UNITS

    @property
    def cy_top(self) -> int:  # the north row's cell y (its north edge is origin_y)
        return int(self.origin_y) // CELL_UNITS - 1

    @property
    def cy_bottom(self) -> int:
        return self.cy_top - self.cells_y + 1

    def cell_rows(self, cy: int) -> tuple[int, int]:
        """Sample rows (north, south) inclusive of cell row cy."""
        north = (self.cy_top - cy) * QUADS_PER_CELL
        return north, north + QUADS_PER_CELL

    def cell_cols(self, cx: int) -> tuple[int, int]:
        west = (cx - self.cx0) * QUADS_PER_CELL
        return west, west + QUADS_PER_CELL

    def to_dict(self) -> dict:
        return {"build_id": self.build_id, "width": self.width, "height": self.height, "origin_x": self.origin_x,
                "origin_y": self.origin_y, "water": self.water, "cells_x": self.cells_x, "cells_y": self.cells_y,
                "cx0": self.cx0, "cx1": self.cx0 + self.cells_x - 1, "cy_top": self.cy_top, "cy_bottom": self.cy_bottom}


def load_grid(build_json: Path) -> Grid:
    b = json.loads(Path(build_json).read_text())
    g = Grid(build_id=b["id"], width=b["width"], height=b["height"], origin_x=float(b["origin_world_x"]),
             origin_y=float(b["origin_world_y"]), water=float(b["water_level_units"]))
    if b["sample_units"] != VERTEX_SPACING_UNITS:
        raise ValueError(f"sample {b['sample_units']} units, LAND needs {VERTEX_SPACING_UNITS}")
    if (g.width - 1) % QUADS_PER_CELL or (g.height - 1) % QUADS_PER_CELL:
        raise ValueError(f"{g.width} x {g.height} samples is not 32 n + 1")
    if g.origin_x % CELL_UNITS or g.origin_y % CELL_UNITS:
        raise ValueError("origin is not on a cell corner")
    return g
