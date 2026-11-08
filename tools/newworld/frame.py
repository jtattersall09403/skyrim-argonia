"""The map frame of the new world: Project Tamriel's Black Marsh map (`newworld/sources/maps/PT3-map-Black_Marsh.png`,
3521 x 2841 px) against Morrowind's exterior grid, which the new world keeps (one map cell is one Morrowind cell,
8192 units a side, so two Skyrim cells a side).

Measured on the map: the grid lines fall every 40 px from the image edge; the column of cell x = 0 starts at px 1640
and the row of cell y = -53 (its north edge the line y = -52 cells) starts at px 160. The rulers print the absolute value of a negative
coordinate (the "39" left of 0 is x = -39; every row number is a negative y). World units: x east, y north,
so a pixel row grows southwards and y falls.

    from tools.newworld import frame as f
    f.px_to_world(px, py) -> (x, y) units;  f.world_to_px(x, y);  f.px_to_cell(px, py) -> (cx, cy)
    f.cell_px_box(cx, cy) -> (left, top, right, bottom) px
"""
from __future__ import annotations

import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "newworld"
MAPS = ROOT / "sources" / "maps"
BASE_MAP = MAPS / "PT3-map-Black_Marsh.png"
REGION_MAP = MAPS / "PT3-map-Black_Marsh_Regions.png"
KEY_IMAGE = MAPS / "PT3-key-Hammerfell-High-Rock.png"
OUT = REPO / "out" / "newworld"

WIDTH_PX, HEIGHT_PX = 3521, 2841
FRAME_PX = 42                          # the ruler band (and its white rule) on every edge: no ground
PX_PER_CELL = 40
CELL_UNITS = 8192                      # a Morrowind exterior cell
UNITS_PER_PX = CELL_UNITS / PX_PER_CELL  # 204.8
UNITS_PER_METRE = 70.0                  # Skyrim's (and near enough Morrowind's) scale
SKYRIM_CELL_UNITS = 4096
X0_PX = 1640                           # west edge of cell column x = 0
Y52_PX = 160                           # the line y = -52 cells: the north edge of cell row y = -53
Y0_PX = Y52_PX - 52 * PX_PER_CELL      # where the line y = 0 would fall (-1920 px)


def px_to_world(px: float, py: float) -> tuple[float, float]:
    """A map pixel position (x right, y down; pixel centres at +0.5) to world units (x east, y north)."""
    return (px - X0_PX) * UNITS_PER_PX, -(py - Y0_PX) * UNITS_PER_PX


def world_to_px(x: float, y: float) -> tuple[float, float]:
    return x / UNITS_PER_PX + X0_PX, -y / UNITS_PER_PX + Y0_PX


def px_to_cell(px: float, py: float) -> tuple[int, int]:
    """The Morrowind cell holding a map pixel position."""
    x, y = px_to_world(px, py)
    return math.floor(x / CELL_UNITS), math.floor(y / CELL_UNITS)


def cell_px_box(cx: int, cy: int) -> tuple[int, int, int, int]:
    """(left, top, right, bottom) in px of a cell; right and bottom exclusive."""
    left = X0_PX + cx * PX_PER_CELL
    top = Y0_PX - (cy + 1) * PX_PER_CELL
    return left, top, left + PX_PER_CELL, top + PX_PER_CELL


def cell_range() -> tuple[range, range]:
    """Every cell wholly or partly on the image: (x range, y range)."""
    x_lo = math.floor((0 - X0_PX) / PX_PER_CELL)
    x_hi = math.floor((WIDTH_PX - 1 - X0_PX) / PX_PER_CELL)
    y_hi = -math.floor((0 - Y0_PX) / PX_PER_CELL) - 1
    y_lo = -math.floor((HEIGHT_PX - 1 - Y0_PX) / PX_PER_CELL) - 1
    return range(x_lo, x_hi + 1), range(y_lo, y_hi + 1)


def metres(units: float) -> float:
    return units / UNITS_PER_METRE
