"""Terrain patches (the world db's `terrain_patch` rows with a kind): a place's pads and bowls over the generated
ground, applied where the ground's heights are read (grid.Sources.heights: the LAND, game_heights_m, GameGround and
the navmesh) and where its material is painted (material.Material), so a pad is a row and never a hand edit.

- `pad`: flat at the mean of the generated ground inside its disc plus rise_m (at least PAD_FREEBOARD_M over its
  cell's water), easing back to the ground over
  blend_m (smoothstep). Skyrim.esm's exterior wells (farmwell01, swell, rtplazawell01, genericwell01) stand on
  ground with p50 0.23 m of relief within 2 m and on a dirt or mud vertex (LDirt02, LFallForestDirt01,
  LRiverMud01): a flat pad under the dirt path's texture (lane 1.15-r4-claywater). A pad is a footprint (a house, a
  byre, a well), never a yard: its level is read on the ground the place's lifts leave, and its edge falls to the
  slope over at least |level - ring| / tan(SEAT_FALL_DEG), so no pad stands proud of the slope as a plate.
- `lift`: a yard or a group of huts raised as a whole by the least that sets its dry ground's LIFT_LOW_PCT PAD_FREEBOARD_M
  over its cells' water (plus rise_m), its relief kept, easing back over blend_m. Skyrim.esm never flattens a farmstead's yard: the LAND
  around 58 farmhouses on slopes (Farmhouse01-06, FarmhouseSmith01, rim slope >= 4 deg) runs on at the slope's own
  gradient (0-3 m out p50 5.0 deg, 6-12 m p50 6.5 deg), flat (|dz| < 0.15 m) a p50 2 m beyond the footprint, and
  even under the footprint keeps p50 1.9 m of relief that the house's own stone plinth takes up (lane
  1.15-r6-claywater-pad-seat: Claywater's 28 m common pad stood as a plate, 0.5 m under the site's flat at its north
  edge, falling 4-5 m at its east and west, the station house's pad 1.0 m proud of it).
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
# A lift sets this low percentile of its dry ground PAD_FREEBOARD_M over the water (the yard's low edge, not one
# bank sample; the river's bed and shelf under the water are the river's and are not counted).
LIFT_LOW_PCT = 5
# A pad's edge falls to the ground at no more than this gradient: Skyrim.esm's LAND 0-3 m out from a farmhouse's
# footprint on a slope, p90 16.7 deg (n 58 houses x 4 sides; lane 1.15-r6-claywater-pad-seat).
SEAT_FALL_DEG = 16.7
SEAT_REACH_M = 12.0  # the widest a pad's blend grows: Skyrim.esm's profiles reach their slope within 12 m (the probe's span)


@dataclass(frozen=True)
class Patch:
    id: str
    kind: str
    row: float  # grid samples, the pad included
    col: float
    radius_m: float
    blend_m: float
    level: float  # the pad's level, the bowl's floor, the lift's rise (metres)
    ltex: str | None

    def reach_m(self) -> float:
        return self.radius_m + (BOWL_REACH_M if self.kind == "bowl" else self.blend_m)

    def weight(self, d: np.ndarray) -> np.ndarray:
        """1 inside the disc, easing (smoothstep) to 0 at radius + blend."""
        t = np.clip((d - self.radius_m) / self.blend_m, 0.0, 1.0) if self.blend_m else (d > self.radius_m).astype(float)
        return 1.0 - t * t * (3 - 2 * t)


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


def disc_values(ground: np.ndarray, row: float, col: float, r0_m: float, r1_m: float) -> np.ndarray:
    """The (province, unpadded) ground's samples between r0_m and r1_m of a point (r0_m < 0: the whole disc)."""
    s = su.PROVINCE_SAMPLE_M
    k = max(int(math.ceil(r1_m / s)), 1)
    i0, j0 = max(int(row) - k, 0), max(int(col) - k, 0)
    win = np.asarray(ground[i0:int(row) + k + 2, j0:int(col) + k + 2], np.float64)
    yy, xx = np.mgrid[i0:i0 + win.shape[0], j0:j0 + win.shape[1]]
    d = np.hypot(yy - row, xx - col) * s
    return win[(d > r0_m) & (d <= max(r1_m, s))]


def seat_blend(ground: np.ndarray, row: float, col: float, radius_m: float, blend_m: float, level: float | None,
               step: float | None = None) -> float:
    """The least blend (at least blend_m, at most SEAT_REACH_M) over which the pad's step off the ground at its rim,
    the worst of its sides, eases away at no more than tan(SEAT_FALL_DEG) on top of the slope's own fall (the
    smoothstep's steepest is 1.5 x its mean; a downhill side on a slope steps more than the ring's mean says). A lift
    passes its rise as `step` (the same everywhere on its rim)."""
    s = su.PROVINCE_SAMPLE_M
    th = np.linspace(0.0, 2 * np.pi, 48, endpoint=False)

    def ring(r_m: float) -> np.ndarray:
        rr = np.clip(np.rint(row + np.sin(th) * r_m / s).astype(int), 0, ground.shape[0] - 1)
        cc = np.clip(np.rint(col + np.cos(th) * r_m / s).astype(int), 0, ground.shape[1] - 1)
        return np.asarray(ground[rr, cc], np.float64)
    g0 = ring(radius_m)
    if step is None:
        step = float(np.abs(level - g0).max())
    tan_ = math.tan(math.radians(SEAT_FALL_DEG))
    k = float(np.abs(ring(radius_m + 2 * s) - g0).max()) / (2 * s)  # the slope's own fall outward: the pad's share is
    need = 1.5 * step / max(tan_ - k, 0.5 * tan_)  # what is left of the bar (half of it at least)
    return round(max(blend_m, min(need, SEAT_REACH_M)), 3)


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
        rows = [r for r in rows if r["kind"]]
        lifts, out = [], []
        for r in rows:  # the lifts first: a pad's level is read on the ground they leave
            if r["kind"] != "lift":
                continue
            row, col = r["y_m"] / s, r["x_m"] / s
            lv = pad_water(r, water_at)
            lift = 0.0
            if lv is not None:  # the yard's dry ground clears the water; the river's own bed and shore in the disc
                # are the river's, never lifted into a bank (Claywater's common holds 28 bed and 75 shore samples)
                v = disc_values(ground, row, col, -1.0, r["radius_m"])
                v = v[v > lv]
                lift = max(0.0, lv + PAD_FREEBOARD_M - float(np.percentile(v, LIFT_LOW_PCT))) if v.size else 0.0
            lift += r["rise_m"] or 0.0
            blend = seat_blend(ground, row, col, r["radius_m"], r["blend_m"] or 0.0, None, abs(lift))
            lifts.append(Patch(r["id"], "lift", row + pad, col + pad, r["radius_m"], blend, round(lift, 3),
                               r["ltex_edid"]))

        def lifted(row: float, col: float) -> float:
            return sum(float(q.weight(np.array(math.hypot(row + pad - q.row, col + pad - q.col) * s))) * q.level
                       for q in lifts)
        for r in rows:
            row, col = r["y_m"] / s, r["x_m"] / s
            if r["kind"] == "pad":
                level = pad_level(ground, row, col, r["radius_m"], r["rise_m"] or 0.0) + lifted(row, col)
                lv = pad_water(r, water_at)
                if lv is not None:
                    level = max(level, lv + PAD_FREEBOARD_M)
                blend = seat_blend(ground, row, col, r["radius_m"], r["blend_m"] or 0.0, level - lifted(row, col))
                out.append(Patch(r["id"], "pad", row + pad, col + pad, r["radius_m"], round(blend, 3),
                                 round(level, 3), r["ltex_edid"]))
            elif r["kind"] == "bowl":
                lv = water_at(r["x_m"], r["y_m"])
                if lv is None:
                    raise ValueError(f"{r['id']}: a bowl in a cell with no water")
                out.append(Patch(r["id"], "bowl", row + pad, col + pad, r["radius_m"], r["blend_m"] or 0.0,
                                 round(lv - r["depth_m"], 3), r["ltex_edid"]))
        return cls(lifts + out)

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
            if p.kind == "lift":
                win += p.level * p.weight(d)
            elif p.kind == "pad":
                win[...] = p.level + (win - p.level) * (1.0 - p.weight(d))
            else:
                np.minimum(win, p.level + np.maximum(0.0, d - p.radius_m) * BOWL_RISE, out=win)

    def paint(self, w: np.ndarray, r0: int, c0: int, index: dict[str, int]) -> None:
        """Texture weights (rows, cols, n) of a window: a patch's ltex rules its disc and fades into the ground's own
        material over its blend (smoothstep), as Skyrim.esm's yards fade their dirt over a few vertices (audit §4: a
        0.02-0.98 run is 1 vertex at p50, 5 at p90). A binary disc on the 1.83 m vertex grid read as a square slab with
        hard straight edges (Claywater's well, round 6; lane 1.15-r6-claywater-pads-look)."""
        for p in self.items:
            if not p.ltex:
                continue
            got = self._window(p, r0, c0, w.shape[:2])
            if got is None:
                continue
            sl, d = got
            fade = max(p.blend_m, 2 * su.PROVINCE_SAMPLE_M)
            t = np.clip((d - p.radius_m) / fade, 0.0, 1.0)
            a = 1.0 - t * t * (3 - 2 * t)  # 1 inside the disc, 0 beyond its blend
            m = a > 0.0
            if m.any():
                win = w[sl]
                k = index[p.ltex]
                am = a[m].astype(win.dtype)[:, None]
                v = win[m] * (1.0 - am)
                v[:, k] += am[:, 0]
                win[m] = v

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
