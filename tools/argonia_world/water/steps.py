"""The step pieces (1.15, decision 0033 §1): the vanilla kit laid on a river's step at a cell edge, and where each
piece stands (`place`), shared by the emit and the check.

Measured on Skyrim.esm (terrain/probes/vanilla_step_pieces.py, 2026-11-03), the 440 rapids and falls refs within
3,000 units of the 51 dressed Tamriel steps (drops 1.4 to 65.7 m, median 8.6 m):
  FXrapidsFallsLine01 (111)  at the UPPER water (z - upper median +8 u, 125 u over the ground), yawed DOWN the step
                             (0 deg off the drop in 63, +-45 in 46)
  FXWaterfallSkirtSlope (49) at the LOWER water (median -5 u), yawed UP the step (180 deg off the drop in 32 of 49)
  FxRapidsRingHeavy (49)     at the LOWER water (median 0 u)
  FXWaterfallMistBlast (22)  at the foot
  FXWaterfallBodyTall / BodySlope: none at a level step (they dress cliffs, not cell-edge steps).
So every step takes the one chain, the line on the edge at the upper water and the rest at the foot, where the
terrain's graded bed (generate.py: k vertices into the lower cell) meets the lower water; only the extras grow
with the drop. Round 3 hung the tall body and its skirt at the upper water, the skirt facing down the step, and
the foot pieces on the edge inside the bed's slope (lane 1.15-r4-water).
"""
from __future__ import annotations

import math

from tools.argonia_world import skyrim_units as su

# The vanilla kit, by mesh (resolved through pieces.py); nominal width/height in units from each base record's
# object bounds in Skyrim.esm (measured 2026-10-29; particle bounds are loose, so the L4 stills judge the scale).
PIECES = {
    "rapids": ("meshes/effects/fxrapidsfallsline01.nif", 1149.0, 1149.0),   # FXrapidsFallsLine01 01B37E
    "ring": ("meshes/effects/fxrapidsringheavy.nif", 1149.0, 1149.0),       # FxRapidsRingHeavy
    "skirt": ("meshes/effects/fxwaterfallskirtslope.nif", 1604.0, 1604.0),  # FXWaterfallSkirtSlope
    "mist": ("meshes/effects/fxwaterfallmistblast.nif", 757.0, 652.0),       # FXWaterfallMistBlast 01ACAE
    "falls": ("meshes/effects/fxwaterfallbodytall.nif", 1467.0, 1468.0),     # FXWaterfallBodyTall 01AC8D (no step)
}
CASCADE_DROP_M = 0.75  # a step at least this tall adds the skirt at the foot
FALLS_STEP_M = 3.0  # a step at least this tall adds the mist blast at the foot (the graph's fallDropM)

# chain id -> the pieces laid on the step, upstream first
CHAINS = {
    "rapids": ("rapids", "ring"),
    "cascade": ("rapids", "skirt", "ring"),
    "falls": ("rapids", "skirt", "ring", "mist"),
}
AT_FOOT = {"skirt", "ring", "mist"}  # at the lower water where the bed meets it; the rest on the edge, upper water
FACE_UP = {"skirt"}  # yawed up the step (vanilla 180 deg); the rest down it
SCALE_BY_DROP = {"mist"}  # sized to the drop; the rest to the channel's width
SCALE_RANGE = (0.1, 10.0)
# the largest one-edge drop a chain dresses: the tall body's height (20.96 m), inside vanilla's dressed steps
# (p90 22.8 m of the 51); a taller step makes its reach a dry gully (solve.py)
MAX_DROP_M = 1468.0 / su.UNITS_PER_METRE
# the terrain's step band (generate.py: the bed from STEP_BED_M under the upper water at the edge down to
# FOOT_BED_M under the lower water, k vertices in); the check holds the ground to these within BED_TOL_U
STEP_BED_M = 200 / su.UNITS_PER_METRE
FOOT_BED_M = 0.5  # FREEBOARD_M + 0.2
BED_TOL_U = 30.0
YAW = {"n": 0.0, "e": 90.0, "s": 180.0, "w": 270.0}  # down a step across this edge (clockwise from north)
OUT = {"n": (0, 1), "e": (1, 0), "s": (0, -1), "w": (-1, 0)}


def chain_for(drop: float) -> str:
    """The chain id of a cell-edge step of this drop (metres)."""
    return "falls" if drop >= FALLS_STEP_M else "cascade" if drop >= CASCADE_DROP_M else "rapids"


def foot_vertices(drop: float) -> int:
    """How many vertices into the lower cell the terrain's graded bed reaches the lower water (generate.py's k)."""
    from tools.argonia_world.terrain.generate import LIP
    return int(min(su.QUADS_PER_CELL - 1, max(1, math.ceil(drop / (0.8 * LIP)))))


def edge_point(s) -> tuple[float, float]:
    """World units: the channel's middle on the step's edge."""
    ox, oy = su.cell_origin(s.cx, s.cy)
    mid = (s.cross_lo + s.cross_hi) / 2 * su.VERTEX_SPACING_UNITS
    return {"n": (ox + mid, oy + su.CELL_UNITS), "s": (ox + mid, oy), "e": (ox + su.CELL_UNITS, oy + mid),
            "w": (ox, oy + mid)}[s.edge]


def foot_point(s) -> tuple[float, float]:
    x, y = edge_point(s)
    k = foot_vertices(s.upper_m - s.lower_m) * su.VERTEX_SPACING_UNITS
    dx, dy = OUT[s.edge]
    return x + dx * k, y + dy * k


def place(s, width_m: float) -> list[dict]:
    """The chain's pieces on step `s`: kind, pos (units), yaw (deg), scale."""
    drop = s.upper_m - s.lower_m
    out = []
    for k in CHAINS[s.chain]:
        _, wu, hu = PIECES[k]
        foot = k in AT_FOOT
        x, y = foot_point(s) if foot else edge_point(s)
        z = su.metres_to_units(s.lower_m if foot else s.upper_m)
        size = su.metres_to_units(drop) / hu if k in SCALE_BY_DROP else su.metres_to_units(width_m) / wu
        yaw = (YAW[s.edge] + (180.0 if k in FACE_UP else 0.0)) % 360
        out.append({"kind": k, "pos": (x, y, z), "yaw": yaw,
                    "scale": min(SCALE_RANGE[1], max(SCALE_RANGE[0], size))})
    return out
