"""A river step as one rotated plane: a square the step's length on a side, centred on the step's stretch of
centreline and turned to its flow. Axis-aligned blocks cut a diagonal step line into one tiny plane per sample; one
turned square does the whole step when its footprint is valid: every sample under it is its own water, or ground
(or the bed under a higher step's water) at most LEAK_TOL_M below it, and no other plane of the same level lies
under it. A step whose square is not valid (a bend, a channel wider than its step) is left to the cell planner.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from tools.argonia_world.water.field import MPP, Field
from tools.argonia_world.water.model import Graph
from tools.argonia_world.water.steps import Step, at

OWN_TOL_M = 0.0051


@dataclass(frozen=True)
class OPlane:
    reach: str
    step: int
    east_m: float  # centre
    south_m: float
    yaw_deg: float
    side_m: float
    level_m: float
    wtype: str
    idx: np.ndarray  # flat indices of the samples under it


def footprint(n: int, east: float, south: float, yaw: float, side: float) -> np.ndarray:
    """Flat indices of the samples whose centres lie inside the turned square."""
    h = side / 2
    rad = h * math.sqrt(2) / MPP + 1
    cx, cy = east / MPP, south / MPP
    c0, c1 = max(0, int(cx - rad)), min(n - 1, int(cx + rad) + 1)
    r0, r1 = max(0, int(cy - rad)), min(n - 1, int(cy + rad) + 1)
    if c0 > c1 or r0 > r1:
        return np.empty(0, dtype=np.int64)
    yy, xx = np.mgrid[r0:r1 + 1, c0:c1 + 1]
    de, ds = xx * MPP - east, yy * MPP - south
    fe, fs = math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))  # the flow in (east, south)
    u = de * fe + ds * fs
    v = -de * fs + ds * fe
    m = (np.abs(u) <= h) & (np.abs(v) <= h)
    return (yy[m] * n + xx[m]).astype(np.int64)


def plan(g: Graph, steps: dict[str, list[Step]], f: Field, ground: np.ndarray, wtypes: dict[str, str],
         leak_tol_m: float) -> list[OPlane]:
    n = ground.shape[0]
    shown = f.shown.ravel()
    gr = np.asarray(ground).ravel() if not isinstance(ground, np.memmap) else ground.reshape(-1)
    taken: dict[int, set] = {}  # level code -> samples under a plane of that level
    out: list[OPlane] = []
    for rid in sorted(steps):
        r = g.reaches[rid]
        if len(r.points) < 2:
            continue
        for s in steps[rid]:
            length = s.s1 - s.s0
            if length <= MPP or abs(s.level_m) < OWN_TOL_M:  # sea level: the default water stands there
                continue
            e, so, yaw = at(r.points, (s.s0 + s.s1) / 2)
            idx = footprint(n, e, so, yaw, length)
            if idx.size == 0:
                continue
            lv = shown[idx]
            own = np.abs(lv - s.level_m) < OWN_TOL_M
            if not own.any():
                continue
            other = ~own
            hidden = (np.isnan(lv[other]) | (lv[other] > s.level_m + OWN_TOL_M)) & \
                (np.asarray(gr[idx[other]]) >= s.level_m - leak_tol_m)
            code = int(round(s.level_m * 100))
            if not hidden.all() or (code in taken and not taken[code].isdisjoint(idx.tolist())):
                continue
            taken.setdefault(code, set()).update(idx.tolist())
            out.append(OPlane(rid, s.index, e, so, yaw, length, s.level_m, wtypes[rid], idx))
    return out
