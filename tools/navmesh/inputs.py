"""The navmesh job's inputs for a box of exterior cells: the ground, the water and the road, one sample per LAND vertex.

    write(out, box)   out/grid.json and three rasters over the box plus a border of BORDER_SAMPLES (row 0 north):
                      height.f32  the ground as the game has it (terrain/build.game_heights_m: quantised, limited and
                                  regraded), in units
                      water.f32   the water surface over a sample whose ground is below it, else NaN, in units:
                                  the worldspace default (0) under every cell, a cell's own water height over its
                                  window, then every water plane over its footprint (out/water/cells.jsonl, what
                                  ArgoniaWorld.esm places; 2.W2)
                      flags.u8    bit 0: the painted road (routes/paint.py's BC_ROAD and TRACK, 2.W3)

Placed-object collision joins later (`ObjectSource`): once the masters' meshes are synced, each placed REFR's
collision triangles go into the same cell job beside the ground, walkable or blocking by their normals.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable, Protocol

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.navmesh import params

ROOT = Path(__file__).resolve().parents[2]
WATER_CELLS = ROOT / "out" / "water" / "cells.jsonl"
PLANE_BASES_FIRST, PLANE_BASES_LAST = 0x100004, 0x100007  # the four water-plane ACTIs (water/layer.py's order)
PLANE_HALF_UNITS = 512.0  # Water1024.nif: -512..512 (water/plan.py PLANE_MESH_UNITS / 2)


class ObjectSource(Protocol):
    """Placed-object collision for a cell box (the interface the synced masters will fill)."""

    def triangles(self, box: tuple[int, int, int, int]) -> Iterable[tuple[np.ndarray, int]]:
        """(3x3 float32 world-unit vertices, area hint) per collision triangle."""


def ground_sources():
    """terrain/grid.Sources.load without the ground tint (the navmesh reads heights and cover only; the tint's PNG
    decode is 9 of the 11 s a small box takes)."""
    from tools.argonia_world.terrain import grid, water_regrade
    r = grid.data_root() / "terrain"
    return grid.Sources(ground=np.load(r / "refined-height-f32.npy", mmap_mode="r"),
                        apron=np.load(r / "apron-source-near.npy", mmap_mode="r"),
                        cover=np.load(r / "landcover-i16.npy", mmap_mode="r"), tint=None, pad=grid.PAD,
                        regrade=water_regrade.Regrade.load(grid.PAD))


def window(src, box, border: int = params.BORDER_SAMPLES) -> tuple[int, int, int, int]:
    """Grid rows [r0, r1) and columns [c0, c1) covering the box's cells and the border."""
    x0, y0, x1, y1 = box
    north, _ = src.cell_rows(y1)
    _, south = src.cell_rows(y0)
    west, _ = src.cell_cols(x0)
    _, east = src.cell_cols(x1)
    return north - border, south + border + 1, west - border, east + border + 1


def water_levels(box, r0: int, c0: int, shape, x0u: float, ytop: float, cells_path: Path = WATER_CELLS) -> np.ndarray:
    """The water surface over every sample of the window (units): default, cell heights, then planes."""
    rows, cols = shape
    step = su.VERTEX_SPACING_UNITS
    level = np.zeros(shape, np.float32)  # the worldspace default water (terrain/world.py DEFAULT_WATER_UNITS)
    planes = []
    bx0, by0, bx1, by1 = box
    with open(cells_path, encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if not (bx0 - 1 <= c["x"] <= bx1 + 1 and by0 - 1 <= c["y"] <= by1 + 1):
                continue
            if "waterHeight" in c:
                cx0, cy0 = su.cell_origin(c["x"], c["y"])
                ca = int(round((cx0 - x0u) / step))
                ra = int(round((ytop - (cy0 + su.CELL_UNITS)) / step))
                a0, a1 = max(ca, 0), min(ca + su.LAND_VERTS, cols)
                b0, b1 = max(ra, 0), min(ra + su.LAND_VERTS, rows)
                if a0 < a1 and b0 < b1:
                    level[b0:b1, a0:a1] = c["waterHeight"]
            for r in c["refs"]:
                fid = int(r["base"].split(":")[0], 16)
                if r["base"].endswith(":ArgoniaWorld.esm") and PLANE_BASES_FIRST <= fid <= PLANE_BASES_LAST:
                    planes.append((r["pos"], r["rot"][2], r.get("scale", 1.0)))
    xs = x0u + np.arange(cols) * step
    ys = ytop - np.arange(rows) * step
    for (px, py, pz), rz, scale in sorted(planes):
        half = PLANE_HALF_UNITS * scale
        reach = half * math.sqrt(2.0)
        ca, cb = np.searchsorted(xs, px - reach), np.searchsorted(xs, px + reach, side="right")
        ra, rb = np.searchsorted(-ys, -(py + reach)), np.searchsorted(-ys, -(py - reach), side="right")
        if ca >= cb or ra >= rb:
            continue
        dx = xs[None, ca:cb] - px
        dy = ys[ra:rb, None] - py
        cs, sn = math.cos(rz), math.sin(rz)  # Skyrim's z rotation turns clockwise seen from above
        lx, ly = dx * cs - dy * sn, dx * sn + dy * cs
        inside = (np.abs(lx) <= half + 0.5) & (np.abs(ly) <= half + 0.5)
        win = level[ra:rb, ca:cb]
        win[inside] = np.maximum(win[inside], np.float32(pz))
    return level


def write(out: Path, box, src=None, cells_path: Path = WATER_CELLS, objects: ObjectSource | None = None) -> dict:
    """Write the rasters and grid.json for `box` (x0, y0, x1, y1) into `out`; returns grid.json's content."""
    from tools.argonia_world.routes import paint as road_paint
    from tools.argonia_world.terrain import build

    if objects is not None:
        raise NotImplementedError("placed-object collision: waits for the synced masters (2.W4 §b)")
    src = src or ground_sources()
    out.mkdir(parents=True, exist_ok=True)
    r0, r1, c0, c1 = window(src, box)
    shape = (r1 - r0, c1 - c0)
    x0u = su.cell_origin(box[0], box[1])[0] - params.BORDER_SAMPLES * su.VERTEX_SPACING_UNITS
    ytop = su.cell_origin(box[0], box[3])[1] + su.CELL_UNITS + params.BORDER_SAMPLES * su.VERTEX_SPACING_UNITS
    hm = np.lib.format.open_memmap(out / "height.npy", "w+", np.float32, shape)
    band = 256
    for a in range(r0, r1, band):  # row bands: nothing whole-province held at once
        b = min(a + band, r1)
        hm[a - r0:b - r0] = (build.game_heights_m(src, a, b, c0, c1) * su.UNITS_PER_METRE).astype(np.float32)
    hm.flush()
    level = water_levels(box, r0, c0, shape, x0u, ytop, cells_path)
    wet = np.where(level > hm, level, np.float32(np.nan)).astype(np.float32)
    road = np.zeros(shape, np.int16)
    road_paint.override_classes(road, r0, c0)
    flags = (road != 0).astype(np.uint8)
    np.asarray(hm).tofile(out / "height.f32")
    wet.tofile(out / "water.f32")
    flags.tofile(out / "flags.u8")
    del hm
    (out / "height.npy").unlink()
    grid = {"rows": shape[0], "cols": shape[1], "x0": x0u, "ytop": ytop, "step": su.VERTEX_SPACING_UNITS,
            "cells": list(box), "params": params.recast()}
    (out / "grid.json").write_text(json.dumps(grid, indent=1, sort_keys=True) + "\n")
    return grid
