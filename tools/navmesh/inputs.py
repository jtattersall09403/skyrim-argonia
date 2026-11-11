"""The navmesh job's inputs for the new world: the ground, the water and the road, one sample per LAND vertex.

    write(out, land, box, cells, objects=None)
        out/grid.json and three rasters over the whole terrain grid (row 0 north):
          height.f32  the ground as the game has it: the world plugin's limited VHGT steps x 8 (world.Land.heights)
          water.f32   the one water level (the build's water_level_units) over a sample whose ground is below it,
                      else NaN
          flags.u8    bit 0: on a road (newworld road_vertex polylines, samples within ROAD_HALF_UNITS; segments
                      with both ends on water left out: those are crossings, not ground)
          skip.u8     one byte per cell of the box, north row first, west to east: 1 = no navmesh (outside the cell
                      table, or margin; world.navmesh_cells)
          objects.f32 placed collision triangles (a place's, or a test's own), 3 corners x 3 floats, world units;
                      written only when there are some
          objects/    the new world's placed collision from the refs shards (`refs`: placed.write_rows) as the
                      voxel columns it blocks, one file a cell row, with its tally and the probe points the check
                      reads; the rows are kept under `<out>/../rows`, each under the digest of what it is made from.
                      `cleared`: positions of world references a place switches off, left out of them
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

from tools.navmesh import params, world

ROAD_HALF_UNITS = 192.0  # 2.7 m: the BM&V roads' worn strip either side of the centre line, about 1.5 samples


def road_mask(shape, x0: float, ytop: float, step: float, polylines=None) -> np.ndarray:
    rows, cols = shape
    m = np.zeros(shape, bool)
    reach = int(np.ceil(ROAD_HALF_UNITS / step))
    for line in (world.road_polylines() if polylines is None else polylines):
        for (ax, ay, aw), (bx, by, bw) in zip(line, line[1:]):
            if aw and bw:
                continue
            c_lo = int(np.floor((min(ax, bx) - x0) / step)) - reach
            c_hi = int(np.ceil((max(ax, bx) - x0) / step)) + reach
            r_lo = int(np.floor((ytop - max(ay, by)) / step)) - reach
            r_hi = int(np.ceil((ytop - min(ay, by)) / step)) + reach
            c_lo, r_lo = max(c_lo, 0), max(r_lo, 0)
            c_hi, r_hi = min(c_hi, cols - 1), min(r_hi, rows - 1)
            if c_lo > c_hi or r_lo > r_hi:
                continue
            cc, rr = np.meshgrid(np.arange(c_lo, c_hi + 1), np.arange(r_lo, r_hi + 1))
            px, py = x0 + cc * step, ytop - rr * step
            dx, dy = bx - ax, by - ay
            ll = dx * dx + dy * dy
            s = np.clip(((px - ax) * dx + (py - ay) * dy) / ll, 0, 1) if ll else np.zeros_like(px, float)
            d2 = (px - ax - s * dx) ** 2 + (py - ay - s * dy) ** 2
            m[r_lo:r_hi + 1, c_lo:c_hi + 1] |= d2 <= ROAD_HALF_UNITS ** 2
    return m


def write(out: Path, land: world.Land, box, cells: set, objects: np.ndarray | None = None, polylines=None,
          heights: np.ndarray | None = None, refs: Path | None = None, data: Path | None = None, resolver=None,
          cleared=None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    g = land.grid
    h = land.heights() if heights is None else heights
    shape = h.shape
    step = float(world.VERTEX_SPACING_UNITS)
    x0u, ytop = float(g.origin_x), float(g.origin_y)
    wet = np.where(h < g.water, np.float32(g.water), np.float32(np.nan)).astype(np.float32)
    flags = road_mask(shape, x0u, ytop, step, polylines).astype(np.uint8)
    bx0, by0, bx1, by1 = box
    skip = np.array([[0 if (x, y) in cells else 1 for x in range(bx0, bx1 + 1)] for y in range(by1, by0 - 1, -1)], np.uint8)
    h.astype(np.float32).tofile(out / "height.f32")
    wet.tofile(out / "water.f32")
    flags.tofile(out / "flags.u8")
    skip.tofile(out / "skip.u8")
    obj = out / "objects.f32"
    obj.unlink(missing_ok=True)
    n_obj = 0
    if objects is not None and len(objects):
        n_obj = len(objects)
        np.asarray(objects, np.float32).tofile(obj)
    rows_dir = out / "objects"
    if rows_dir.exists():
        shutil.rmtree(rows_dir)
    placed_tally = None
    if refs is not None:
        from tools.navmesh import placed
        placed_tally = placed.write_rows(refs, data, rows_dir, box, np.asarray(h, np.float32), (x0u, ytop, step),
                                         cache=out.parent / "rows", resolver=resolver,
                                         exclude=None if cleared is None else placed.Cleared(cleared))
        n_obj += placed_tally["band_triangles"]
    grid = {"rows": shape[0], "cols": shape[1], "x0": x0u, "ytop": ytop, "step": step, "cells": list(box),
            "build_id": land.build_id, "water": g.water, "params": params.recast(), **({"objects": n_obj} if n_obj else {}),
            **({"placed": {k: placed_tally[k] for k in ("refs", "collidable", "fed", "no_collision", "unresolved", "triangles", "band_triangles", "columns", "cleared")
                           if k in placed_tally}}
               if placed_tally else {})}
    (out / "grid.json").write_text(json.dumps(grid, indent=1, sort_keys=True) + "\n")
    return grid
