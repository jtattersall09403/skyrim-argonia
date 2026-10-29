"""The stepped river (2.W2's method, decision 0027's first step): each reach's water as flat steps at its grade, a
vanilla rapids or waterfall piece at every step (old 0064: waterfalls are the vanilla kit).

A reach's water-level profile runs linearly along its centreline from `level_from_m` to `level_to_m` (the graph's
reach is one kind, so one slope). It is cut into n steps of equal length, n = ceil(drop / STEP_MAX_M) limited so no
step is shorter than STEP_MIN_M; a step's level is the profile at its midpoint, so the water stands at most half a
step above or below the graded profile. Pieces stand at each step's downstream edge, at the upper level, facing
downstream; a fall reach has no plane, only the waterfall at its lip and mist at its plunge.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from tools.argonia_world.water.model import Graph, Reach

STEP_MAX_M = 0.5  # the largest drop between two steps of a graded reach (a riffle's line of white water)
STEP_MIN_M = 8.0  # the shortest step (four plane samples): steeper reaches take bigger drops instead
PIECE_MIN_DROP_M = 0.05  # a smaller join between steps is not a visible step and gets no piece

# The vanilla kit, by mesh (resolved through pieces.py); nominal width/height in units from each base record's
# object bounds in Skyrim.esm (measured 2026-10-29; particle bounds are loose, so the L4 stills judge the scale).
PIECES = {
    "rapids": ("meshes/effects/fxrapidsfallsline01.nif", 1149.0, 1149.0),   # FXrapidsFallsLine01 01B37E
    "cascade": ("meshes/effects/fxwaterfallbodyslope.nif", 1604.0, 1604.0),  # FXWaterfallBodySlope 01AC8C
    "falls": ("meshes/effects/fxwaterfallbodytall.nif", 1467.0, 1468.0),     # FXWaterfallBodyTall 01AC8D
    "mist": ("meshes/effects/fxwaterfallmistblast.nif", 757.0, 652.0),       # FXWaterfallMistBlast 01ACAE
}
CASCADE_DROP_M = 0.75  # a step at least this tall takes the sloped waterfall body instead of the rapids line
# A merge of steps (the plane budget, budget.py) may make a drop up to MERGED_DROP_MAX_M, or MERGED_FACTOR times the
# grade's step where that is taller (a steep reach); the merged step's level is still the graded profile at its
# midpoint, so the water stays within half a merged step of the grade.
MERGED_DROP_MAX_M = 2.0
MERGED_FACTOR = 2.0


@dataclass(frozen=True)
class Step:
    reach: str
    index: int
    s0: float  # arc metres from the reach's first point
    s1: float
    level_m: float
    profile_lo_m: float  # the profile's range over the step
    profile_hi_m: float


@dataclass(frozen=True)
class Piece:
    kind: str  # rapids | cascade | falls | mist
    reach: str
    east_m: float
    south_m: float
    z_m: float
    yaw_deg: float
    drop_m: float
    width_m: float


def arcs(points) -> list[float]:
    out = [0.0]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        out.append(out[-1] + math.hypot(x1 - x0, y1 - y0))
    return out


def at(points, s: float) -> tuple[float, float, float]:
    """(east, south, yaw degrees clockwise from north) at arc s along the polyline."""
    a = arcs(points)
    if len(points) == 1:
        return points[0][0], points[0][1], 0.0
    i = max(0, min(len(points) - 2, next((k - 1 for k, v in enumerate(a) if v >= s), len(points) - 2)))
    seg = a[i + 1] - a[i]
    t = 0.0 if seg <= 0 else min(1.0, max(0.0, (s - a[i]) / seg))
    (x0, y0), (x1, y1) = points[i], points[i + 1]
    # east is +x, north is -south: yaw = atan2(dEast, dNorth)
    yaw = math.degrees(math.atan2(x1 - x0, -(y1 - y0))) % 360.0
    return x0 + t * (x1 - x0), y0 + t * (y1 - y0), yaw


def profile(r: Reach, s: float, total: float) -> float:
    if total <= 0:
        return r.level_from_m
    return r.level_from_m + (r.level_to_m - r.level_from_m) * min(1.0, max(0.0, s / total))


def reach_steps(r: Reach) -> list[Step]:
    if not r.points:
        return []
    total = arcs(r.points)[-1]
    drop = r.level_from_m - r.level_to_m
    if drop <= 0:  # flat or the junction pin's small rise: one level
        lv = max(r.level_from_m, r.level_to_m) if drop < 0 else r.level_from_m
        return [Step(r.id, 0, 0.0, total, lv, min(r.level_from_m, r.level_to_m), max(r.level_from_m, r.level_to_m))]
    n = max(1, math.ceil(drop / STEP_MAX_M - 1e-9))
    n = max(1, min(n, int(total // STEP_MIN_M) or 1))
    out = []
    for i in range(n):
        s0, s1 = total * i / n, total * (i + 1) / n
        a, b = profile(r, s0, total), profile(r, s1, total)
        out.append(Step(r.id, i, s0, s1, profile(r, (s0 + s1) / 2, total), min(a, b), max(a, b)))
    return out


def piece_for(drop: float) -> str:
    return "cascade" if drop >= CASCADE_DROP_M else "rapids"


def merge(r: Reach, st: list[Step], k: int) -> list[Step]:
    """Steps k and k+1 of a reach as one step over both runs, at the profile's level at the joined run's midpoint."""
    total = arcs(r.points)[-1]
    a, b = st[k], st[k + 1]
    m = Step(r.id, a.index, a.s0, b.s1, profile(r, (a.s0 + b.s1) / 2, total), min(a.profile_lo_m, b.profile_lo_m),
             max(a.profile_hi_m, b.profile_hi_m))
    return st[:k] + [m] + st[k + 2:]


def drop_allowed(r: Reach, merged: bool = False) -> float:
    """The largest drop between two of a reach's steps: the grade's step (a steep reach's, as STEP_MIN_M forces),
    or MERGED_DROP_MAX_M once the budget has merged its steps."""
    total = arcs(r.points)[-1] if r.points else 0.0
    drop = max(0.0, r.level_from_m - r.level_to_m)
    fewest = max(1, int(total // STEP_MIN_M))
    base = max(STEP_MAX_M, drop / fewest)
    return max(MERGED_FACTOR * base, MERGED_DROP_MAX_M) if merged else base


def plan(g: Graph, rules: dict[str, str]) -> tuple[dict[str, list[Step]], list[Piece]]:
    """Steps of every stepped reach and the pieces of every step, join and fall. `rules`: reach id -> rule."""
    steps = {rid: reach_steps(r) for rid, r in g.reaches.items() if rules.get(rid) == "stepped"}
    return steps, pieces(g, rules, steps)


def pieces(g: Graph, rules: dict[str, str], steps: dict[str, list[Step]]) -> list[Piece]:
    """The pieces of every step, join and fall for these steps (after any merge)."""
    pieces: list[Piece] = []
    for rid, r in g.reaches.items():
        rule = rules.get(rid)
        if rule == "falls" and r.points:
            total = arcs(r.points)[-1]
            e, s, yaw = at(r.points, 0.0)
            drop = r.fall_drop_m or (r.level_from_m - r.level_to_m)
            pieces.append(Piece("falls", rid, e, s, r.level_from_m, yaw, drop, r.width_m))
            e, s, yaw = at(r.points, total)
            pieces.append(Piece("mist", rid, e, s, r.level_to_m, yaw, drop, r.width_m))
            continue
        st = steps.get(rid)
        if not st:
            continue
        for a, b in zip(st, st[1:]):
            d = a.level_m - b.level_m
            if d >= PIECE_MIN_DROP_M:
                e, s, yaw = at(r.points, a.s1)
                pieces.append(Piece(piece_for(d), rid, e, s, a.level_m, yaw, d, r.width_m))
        # the join to what lies downstream: the next reach's first step, or a body's level
        nxt = g.reaches.get(r.downstream) if r.downstream else None
        below = None
        if nxt is not None and steps.get(nxt.id):
            below = steps[nxt.id][0].level_m
        elif nxt is not None and rules.get(nxt.id) in ("body", "default"):
            below = g.bodies[nxt.body].level_m if nxt.body in g.bodies else nxt.level_from_m
        if below is not None and st[-1].level_m - below >= PIECE_MIN_DROP_M:
            e, s, yaw = at(r.points, st[-1].s1)
            d = st[-1].level_m - below
            pieces.append(Piece(piece_for(d), rid, e, s, st[-1].level_m, yaw, d, r.width_m))
    return pieces
