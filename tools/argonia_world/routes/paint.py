"""The roads painted into the land-cover classes the LAND writer textures (2.W3 §b; agreed with 2.W1 on 2026-10-29).

The road table holds each leg's traced centreline (road_point, metres east and south of the province's north-west
corner) with its surface class (BC_ROAD 30 or TRACK 29) and flat width. The imported paint under a leg is continuous
for only 72% of its length, so this lays the leg's surface class over every sample within half the flat width of the
centreline. The road then reads as one unbroken surface, and its textures come with it (decision 0028: grass follows
the paint, so a painted road grows none). A road outranks a track where the two overlap; water is never painted over.

    override_classes(classes, r0, c0)   in place: a window of the terrain grid (rows r0.., cols c0.., the apron pad
                                        included), as terrain/build.py reads it after `src.classes()`
"""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su

PAD = su.APRON_CELLS * su.QUADS_PER_CELL  # 2176: the grid's apron pad, in samples (terrain/grid.py's PAD)
ROAD, TRACK = 30, 29
RANK = {TRACK: 1, ROAD: 2}  # a road wins over a track where both reach
_SEGMENTS = None


def segments(world=None) -> list[tuple[int, float, np.ndarray]]:
    """(surface class, half width in samples, (n, 2, 2) segment ends in grid (row, col)) per road, roads last."""
    global _SEGMENTS
    if _SEGMENTS is None or world is not None:
        from tools.argonia_world import db

        w = world if world is not None else db.open()
        out = []
        for r in w.query("SELECT route_id, surface_cover, flat_width_m FROM road ORDER BY route_id"):
            pts = np.array([(p["y_m"], p["x_m"]) for p in w.query(
                "SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r["route_id"])], dtype=np.float64)
            if len(pts) < 2:
                continue
            g = pts / su.PROVINCE_SAMPLE_M + PAD
            out.append((r["surface_cover"], r["flat_width_m"] / 2 / su.PROVINCE_SAMPLE_M,
                        np.stack([g[:-1], g[1:]], axis=1)))
        out.sort(key=lambda s: RANK.get(s[0], 0))
        _SEGMENTS = out
    return _SEGMENTS


def mask(seg: np.ndarray, half: float, r0: int, c0: int, shape: tuple[int, int]) -> np.ndarray:
    """Samples of the window within `half` samples of any of the segments."""
    out = np.zeros(shape, dtype=bool)
    h, w = shape
    for (ar, ac), (br, bc) in seg:
        lo_r, hi_r = int(np.floor(min(ar, br) - half)), int(np.ceil(max(ar, br) + half))
        lo_c, hi_c = int(np.floor(min(ac, bc) - half)), int(np.ceil(max(ac, bc) + half))
        lo_r, hi_r, lo_c, hi_c = max(lo_r, r0), min(hi_r, r0 + h - 1), max(lo_c, c0), min(hi_c, c0 + w - 1)
        if lo_r > hi_r or lo_c > hi_c:
            continue
        rr, cc = np.mgrid[lo_r:hi_r + 1, lo_c:hi_c + 1]
        dr, dc = br - ar, bc - ac
        L2 = dr * dr + dc * dc
        t = np.clip(((rr - ar) * dr + (cc - ac) * dc) / L2, 0, 1) if L2 > 0 else np.zeros(rr.shape)
        d2 = (rr - ar - t * dr) ** 2 + (cc - ac - t * dc) ** 2
        out[lo_r - r0:hi_r - r0 + 1, lo_c - c0:hi_c - c0 + 1] |= d2 <= half * half
    return out


def override_classes(classes: np.ndarray, r0: int, c0: int, water: frozenset[int] = frozenset(),
                     segs=None) -> np.ndarray:
    """Paint every road and track over the window `classes` (int16, grid rows r0.., cols c0..) in place."""
    for cls, half, seg in (segs if segs is not None else segments()):
        m = mask(seg, half, r0, c0, classes.shape)
        if water:
            m &= ~np.isin(classes, list(water))
        classes[m] = cls
    return classes
