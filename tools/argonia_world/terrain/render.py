"""The L3 renderer (1.15 §b): one image per window of cells, a hillshade of the ground with the cell water drawn
where the game would show it (ground below the cell's one level), the steps as lines on their edges, and a layer
registry other lanes fill.

    python3 -m tools.argonia_world.terrain render [--cells=x0,y0,x1,y1 | --sample] [--out DIR] [--layers a,b]

Layers: name -> "module:function"; each function takes the Window and returns an (h, w, 4) uint8 RGBA overlay
or None. They import lazily: a layer whose module is not there yet is skipped, so the image draws what exists.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import png
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, Q, TYPES, CellWater

LAYERS: dict[str, str] = {
    "material": "tools.argonia_world.terrain.material:render_layer",  # the materials lane
    "placements": "tools.argonia_world.vegetation.render:render_layer",  # the vegetation lane
}
# the vibe board's dark calm water (docs/design/world/vibe-board.md): blue-teal sea and fresh water, opaque
# olive-brown brackish marsh, black water; drawn nearly opaque and unshaded (a flat calm surface), never a pale wash
WATER_RGB = {"sea": (26, 52, 66), "brackish": (44, 50, 32), "blackwater": (20, 22, 16), "fresh": (28, 60, 68)}
STEP_RGB = (230, 40, 30)
CLOSED_RGB = (250, 160, 20)


@dataclass
class Window:
    """Cells x0..x1, y0..y1 inclusive; samples rows r0:r1, columns c0:c1 of the province grid (row 0 north)."""
    x0: int
    y0: int
    x1: int
    y1: int
    ground: np.ndarray  # the window's metres
    level: np.ndarray  # the window's cell level per sample (NaN dry)
    wtype: np.ndarray  # the window's water type index per sample (-1)
    water: CellWater
    world: object = None

    @property
    def rows(self) -> tuple[int, int]:
        return (C - 1 - (self.y1 - CY0)) * Q, (C - (self.y0 - CY0)) * Q + 1

    @property
    def cols(self) -> tuple[int, int]:
        return (self.x0 - CX0) * Q, (self.x1 - CX0 + 1) * Q + 1

    @property
    def wet(self) -> np.ndarray:
        return ~np.isnan(self.level) & (self.ground < self.level)


MIN_PX = 1000  # a render's long side, so a reader can judge it
MIN_CELLS = 8  # a window narrower than this is widened about its centre (the 1-2 cell samples read in context)


def widen(cells: tuple[int, int, int, int], k: int = MIN_CELLS) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = cells
    if x1 - x0 + 1 < k:
        x0 = (x0 + x1) // 2 - k // 2 + 1
        x1 = x0 + k - 1
    if y1 - y0 + 1 < k:
        y0 = (y0 + y1) // 2 - k // 2 + 1
        y1 = y0 + k - 1
    lo, hi = CX0, CX0 + C - 1  # shifted inside the province (CX0 = CY0), not clipped
    dx = max(lo - x0, 0) - max(x1 - hi, 0)
    dy = max(lo - y0, 0) - max(y1 - hi, 0)
    return x0 + dx, y0 + dy, x1 + dx, y1 + dy


def window(ground: np.ndarray, water: CellWater, cells: tuple[int, int, int, int], world=None) -> Window:
    lo, hi = CX0, CX0 + C - 1  # the province only: the apron is grid.py's, not the generator's
    x0, y0, x1, y1 = (min(max(v, lo), hi) for v in cells)
    w = Window(x0, y0, x1, y1, None, None, None, water, world)
    (r0, r1), (c0, c1) = w.rows, w.cols
    w.ground = np.asarray(ground[r0:r1, c0:c1], np.float64)
    i0, i1 = r0 // Q, min((r1 - 1) // Q, C - 1) + 1
    j0, j1 = c0 // Q, min((c1 - 1) // Q, C - 1) + 1
    lv = np.repeat(np.repeat(water.level[i0:i1, j0:j1], Q, 0), Q, 1)
    ty = np.repeat(np.repeat(water.wtype[i0:i1, j0:j1], Q, 0), Q, 1)
    lv = np.pad(lv, ((0, 1), (0, 1)), mode="edge")[: r1 - r0, : c1 - c0]
    ty = np.pad(ty, ((0, 1), (0, 1)), mode="edge")[: r1 - r0, : c1 - c0]
    w.level, w.wtype = lv, ty
    return w


def hillshade(h: np.ndarray, az: float = 315.0, alt: float = 45.0, z: float = 1.0) -> np.ndarray:
    gy, gx = np.gradient(h * z, su.PROVINCE_SAMPLE_M)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    a, e = np.radians(360.0 - az + 90.0), np.radians(alt)
    s = np.sin(e) * np.cos(slope) + np.cos(e) * np.sin(slope) * np.cos(a - aspect)
    return np.clip(s, 0, 1)


def base_rgb(w: Window) -> np.ndarray:
    """Hillshade over a height tint (green lowland -> brown upland -> grey summit), water by type and depth."""
    h = w.ground
    t = np.clip(h / 400.0, 0, 1)[..., None]
    low, mid, top = np.array([95, 120, 70.0]), np.array([150, 125, 90.0]), np.array([200, 200, 200.0])
    tint = np.where(t < 0.5, low + (mid - low) * (t / 0.5), mid + (top - mid) * ((t - 0.5) / 0.5))
    shade = hillshade(h)[..., None]
    rgb = tint * (0.35 + 0.75 * shade)
    wet = w.wet
    if wet.any():
        depth = np.where(wet, w.level - h, 0)
        k = np.clip(depth / 3.0, 0, 1)[..., None] * 0.12 + 0.82  # the bed shows faintly only at the very edge
        col = np.zeros_like(rgb)
        for i, name in enumerate(TYPES):
            col[w.wtype == i] = WATER_RGB[name]
        rgb = np.where(wet[..., None], rgb * (1 - k) + col * k, rgb)
    return np.clip(rgb, 0, 255)


def draw_steps(rgb: np.ndarray, w: Window) -> None:
    r0, c0 = w.rows[0], w.cols[0]
    for s in w.water.steps:
        if not (w.x0 <= s.cx <= w.x1 and w.y0 <= s.cy <= w.y1):
            continue
        north = (C - 1 - (s.cy - CY0)) * Q - r0
        west = (s.cx - CX0) * Q - c0
        col = CLOSED_RGB if s.chain == "closed" else STEP_RGB
        lo, hi = (0, Q) if s.cross_lo < 0 else (s.cross_lo, s.cross_hi)
        if s.edge in ("n", "s"):
            r = north if s.edge == "n" else north + Q
            rr = np.clip(np.arange(r - 1, r + 2), 0, rgb.shape[0] - 1)
            rgb[np.ix_(rr, np.arange(west + lo, west + hi + 1))] = col
        else:
            c = west + (Q if s.edge == "e" else 0)
            cc = np.clip(np.arange(c - 1, c + 2), 0, rgb.shape[1] - 1)
            rows = north + Q - np.arange(lo, hi + 1)  # vertex j from the south
            rgb[np.ix_(rows, cc)] = col


def layer(name: str):
    mod, fn = LAYERS[name].split(":")
    try:
        return getattr(importlib.import_module(mod), fn)
    except (ImportError, AttributeError):
        return None


def render(w: Window, path: Path, layers=None, scale: int = 1) -> dict:
    rgb = base_rgb(w)
    drawn = []
    for name in (layers if layers is not None else LAYERS):
        f = layer(name)
        if f is None:
            continue
        ov = f(w)
        if ov is None:
            continue
        a = ov[..., 3:4] / 255.0
        rgb = rgb * (1 - a) + ov[..., :3] * a
        drawn.append(name)
    rgb = rgb.astype(np.uint8)
    draw_steps(rgb, w)
    if scale > 1:
        rgb = rgb[::scale, ::scale]
    up = max(1, -(-MIN_PX // max(rgb.shape[:2])))  # nearest-neighbour up to MIN_PX on the long side (the reader)
    if up > 1:
        rgb = np.repeat(np.repeat(rgb, up, 0), up, 1)
    png.write(path, rgb)
    return {"path": str(path), "cells": [w.x0, w.y0, w.x1, w.y1], "layers": drawn,
            "wet_samples": int(w.wet.sum()), "ground_m": [round(float(w.ground.min()), 2), round(float(w.ground.max()), 2)]}
