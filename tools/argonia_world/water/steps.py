"""The step pieces (1.15, decision 0033 §1): the vanilla kit laid on a river's step at a cell edge (old 0064:
waterfalls are the vanilla kit), and the chain sized to the drop.

world-rebuild-options.md §11 measured Skyrim.esm's stepped cell edges: across the 60 with pieces,
FXrapidsFallsLine01 in 41, FxRapidsRingHeavy 37, FXWaterfallBodySlope 30, FXWaterfallSkirtSlope 33, a mist blast at
the foot. So a small step takes the rapids line and a ring, a middling one the sloped body and its skirt over the
line, a tall one the tall body, its skirt and the mist at the foot. The solve (solve.py) decides where steps stand.
"""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su

# The vanilla kit, by mesh (resolved through pieces.py); nominal width/height in units from each base record's
# object bounds in Skyrim.esm (measured 2026-10-29; particle bounds are loose, so the L4 stills judge the scale).
# The ring and the skirt carry the line's and the sloped body's nominal size (not measured: the stills judge them).
PIECES = {
    "rapids": ("meshes/effects/fxrapidsfallsline01.nif", 1149.0, 1149.0),   # FXrapidsFallsLine01 01B37E
    "ring": ("meshes/effects/fxrapidsringheavy.nif", 1149.0, 1149.0),       # FxRapidsRingHeavy
    "cascade": ("meshes/effects/fxwaterfallbodyslope.nif", 1604.0, 1604.0),  # FXWaterfallBodySlope 01AC8C
    "skirt": ("meshes/effects/fxwaterfallskirtslope.nif", 1604.0, 1604.0),   # FXWaterfallSkirtSlope
    "falls": ("meshes/effects/fxwaterfallbodytall.nif", 1467.0, 1468.0),     # FXWaterfallBodyTall 01AC8D
    "mist": ("meshes/effects/fxwaterfallmistblast.nif", 757.0, 652.0),       # FXWaterfallMistBlast 01ACAE
}
CASCADE_DROP_M = 0.75  # a step at least this tall takes the sloped waterfall body over the rapids line
FALLS_STEP_M = 3.0  # a step at least this tall takes the tall waterfall body (the graph's fallDropM)

# chain id -> the pieces laid on the step, upstream first; AT_FOOT pieces stand at the lower water
CHAINS = {
    "rapids": ("rapids", "ring"),
    "cascade": ("rapids", "cascade", "skirt", "ring"),
    "falls": ("falls", "skirt", "mist"),
}
AT_FOOT = {"ring", "mist"}
SCALE_BY_DROP = {"cascade", "skirt", "falls", "mist"}  # sized to the drop; the rest to the channel's width
MAX_DROP_M = PIECES["falls"][2] / su.UNITS_PER_METRE  # the tall body's height: the largest one-edge drop, 20.96 m


def chain_for(drop: float) -> str:
    """The chain id of a cell-edge step of this drop (metres)."""
    return "falls" if drop >= FALLS_STEP_M else "cascade" if drop >= CASCADE_DROP_M else "rapids"
