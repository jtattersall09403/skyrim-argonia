"""Terrain patches (the world db's `terrain_patch` rows with a kind): a place's pads and bowls over the generated
ground, applied where the ground's heights are read (grid.Sources.heights: the LAND, game_heights_m, GameGround and
the navmesh) and where its material is painted (material.Material), so a pad is a row and never a hand edit.

- `pad`: flat at the mean of the generated ground inside its disc plus rise_m (at least PAD_FREEBOARD_M over its
  cell's water), easing back to the ground over
  blend_m (smoothstep). Skyrim.esm's exterior wells (farmwell01, swell, rtplazawell01, genericwell01) stand on
  ground with p50 0.23 m of relief within 2 m and on a dirt or mud vertex (LDirt02, LFallForestDirt01,
  LRiverMud01): a flat pad under the dirt path's texture (lane 1.15-r4-claywater).
- `bowl`: the ground carved down to depth_m under its cell's water level within its radius, its side rising
  BOWL_RISE metres a metre beyond (place_ground.py's bowl, re-based on the water: its floor_m was absolute and
  stood 35 m under the round-3 ground).
Levels are computed once at load from the ground array and the cell water, so every window agrees.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

import numpy as np

from tools.argonia_world import skyrim_units as su

TABLE = "terrain_patch"
BOWL_RISE = 0.5
BOWL_REACH_M = 20.0
# A pad stands at least this far over its cell's water: Skyrim.esm's Riverwood (cells 3..7, -13..-9) seats its
# farmhouses and smithy 1.0-3.81 m over the river's cell water (FarmhouseSmith01 1.0 m, the least; n 7), so a yard by
# the water is lifted clear of it, never left a hand's width over it (lane 1.15-r6-claywater-water: Claywater's
# common stood 0.52 m over the river, the quest-board marker 0.08 m over it on the bank's slope).
PAD_FREEBOARD_M = 1.0


@dataclass(frozen=True)
class Patch:
    id: str
    kind: str
    row: float  # grid samples, the pad included
    col: float
    radius_m: float
    blend_m: float
    level: float  # the pad's level, the bowl's floor (metres)
    ltex: str | None

    def reach_m(self) -> float:
        return self.radius_m + (self.blend_m if self.kind == "pad" else BOWL_REACH_M)


def pad_level(ground: np.ndarray, row: float, col: float, radius_m: float, rise: float = 0.0) -> float:
    """The mean of a (province, unpadded) ground array inside the disc, plus rise."""
    s = su.PROVINCE_SAMPLE_M
    k = max(int(math.ceil(radius_m / s)), 1)
    i0, j0 = max(int(row) - k, 0), max(int(col) - k, 0)
    win = np.asarray(ground[i0:int(row) + k + 2, j0:int(col) + k + 2], np.float64)
    yy, xx = np.mgrid[i0:i0 + win.shape[0], j0:j0 + win.shape[1]]
    d = np.hypot(yy - row, xx - col) * s
    sel = win[d <= max(radius_m, s)]
    return float(sel.mean()) + rise


def pad_water(r: dict, water_at) -> float | None:
    """The highest cell water under a pad's disc (its centre and four points on its rim): a pad across a cell edge
    clears the wet cell's water, not only the cell its centre falls in."""
    rad = r["radius_m"]
    got = [water_at(r["x_m"] + dx * rad, r["y_m"] + dy * rad) for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))]
    got = [g for g in got if g is not None]
    return max(got) if got else None


class Patches:
    def __init__(self, items: list[Patch]):
        self.items = items

    def __len__(self) -> int:
        return len(self.items)

    @classmethod
    def from_rows(cls, rows, ground: np.ndarray, pad: int, water_at) -> "Patches":
        """rows: dicts of terrain_patch; ground: the province array (no pad); water_at(x_m, y_m) -> level or None."""
        s = su.PROVINCE_SAMPLE_M
        out = []
        for r in rows:
            if not r["kind"]:
                continue
            row, col = r["y_m"] / s, r["x_m"] / s
            if r["kind"] == "pad":
                level = pad_level(ground, row, col, r["radius_m"], r["rise_m"] or 0.0)
                lv = pad_water(r, water_at)
                if lv is not None:
                    level = max(level, lv + PAD_FREEBOARD_M)
            else:
                lv = water_at(r["x_m"], r["y_m"])
                if lv is None:
                    raise ValueError(f"{r['id']}: a bowl in a cell with no water")
                level = lv - r["depth_m"]
            out.append(Patch(r["id"], r["kind"], row + pad, col + pad, r["radius_m"], r["blend_m"] or 0.0,
                             round(level, 3), r["ltex_edid"]))
        return cls(out)

    @classmethod
    def load(cls, ground: np.ndarray, pad: int, world=None) -> "Patches | None":
        from tools.argonia_world import db
        w = world if world is not None else db.open()
        try:
            rows = [dict(r) for r in w.query(f'SELECT * FROM "{TABLE}" WHERE kind IS NOT NULL ORDER BY id')]
        except Exception:  # an older schema: keys only
            return None
        if not rows:
            return None
        from tools.argonia_world.place_build import water_level
        return cls.from_rows(rows, ground, pad, lambda x, y: water_level(w, x, y))

    def _window(self, p: Patch, r0: int, c0: int, shape):
        s = su.PROVINCE_SAMPLE_M
        k = math.ceil(p.reach_m() / s) + 1
        i0, i1 = max(r0, math.floor(p.row) - k), min(r0 + shape[0], math.ceil(p.row) + k + 1)
        j0, j1 = max(c0, math.floor(p.col) - k), min(c0 + shape[1], math.ceil(p.col) + k + 1)
        if i0 >= i1 or j0 >= j1:
            return None
        rr, cc = np.mgrid[i0:i1, j0:j1]
        return (slice(i0 - r0, i1 - r0), slice(j0 - c0, j1 - c0)), np.hypot(rr - p.row, cc - p.col) * s

    def apply(self, out: np.ndarray, r0: int, c0: int) -> None:
        """Heights of a window whose first grid row and column are r0, c0 (the pad included)."""
        for p in self.items:
            got = self._window(p, r0, c0, out.shape)
            if got is None:
                continue
            sl, d = got
            win = out[sl]
            if p.kind == "pad":
                t = np.clip((d - p.radius_m) / p.blend_m, 0.0, 1.0) if p.blend_m else (d > p.radius_m).astype(float)
                keep = t * t * (3 - 2 * t)
                win[...] = p.level + (win - p.level) * keep
            else:
                np.minimum(win, p.level + np.maximum(0.0, d - p.radius_m) * BOWL_RISE, out=win)

    def paint(self, w: np.ndarray, r0: int, c0: int, index: dict[str, int]) -> None:
        """Texture weights (rows, cols, n) of a window: a patch's ltex rules its disc."""
        for p in self.items:
            if not p.ltex:
                continue
            got = self._window(p, r0, c0, w.shape[:2])
            if got is None:
                continue
            sl, d = got
            m = d <= p.radius_m
            if m.any():
                win = w[sl]
                win[m] = 0.0
                win[m, index[p.ltex]] = 1.0

    def key(self, r0: int, r1: int) -> bytes:
        """The patches reaching grid rows [r0, r1), for the LAND row reuse key."""
        s = su.PROVINCE_SAMPLE_M
        return repr([p for p in self.items if p.row + p.reach_m() / s >= r0 and p.row - p.reach_m() / s < r1]).encode()


def stamp(world=None) -> str:
    from tools.argonia_world import db
    w = world if world is not None else db.open()
    try:
        rows = w.query(f'SELECT * FROM "{TABLE}" WHERE kind IS NOT NULL ORDER BY id')
    except Exception:
        return "none"
    return hashlib.sha256(repr([tuple(r) for r in rows]).encode()).hexdigest()
