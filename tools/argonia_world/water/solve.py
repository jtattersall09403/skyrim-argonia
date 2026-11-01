"""The water solve (1.15 §a, decision 0033 §1): one water level per exterior cell, the vanilla way.

Every hydrology body and reach resolves to rows of `cell_water` (one level and type per cell, written as the cell's
XCLW/XCWT) and `water_step` (a river's drop at a cell edge, with its piece chain from `steps.py`). Other lanes read
the result through `load(db)`:

    from tools.argonia_world import db
    from tools.argonia_world.water import solve
    cw = solve.load(db.open())
    cw.level(cx, cy)          # metres, or None for a cell with no water
    cw.type(cx, cy)           # 'sea' | 'brackish' | 'blackwater' | 'fresh' | None
    cw.steps()                # list[Step]
    cw.nearest_level(cx, cy)  # level of the nearest water cell ("height above local water")

The rules (each a pure function below, unit-tested in tests/test_solve.py):

1. Bodies. A body's footprint is the frozen body raster's samples at its level inside its bbox (the raster every
   earlier water stage read, `hydrology-graph-bodies.npz`); a body the raster does not hold stands in the cell of
   its deepest sample. Levels: the sea at 0; a body below SNAP_LO_M at 0; **the snap rule** for the inland bodies
   between SNAP_LO_M and SNAP_HI_M (1,086 of them): each snaps to 0, the sea-level marsh it is (Argonia's lowland
   is a tidal marsh plain: docs/design/world/50-hydrology-climate.md "Define sea level, tidal zones"),
   unless it shares a cell with a body that
   stands at SNAP_HI_M or above: then the cell rule (3) gives it that body's level, its basin's. Bodies at
   SNAP_HI_M and above keep their `level_m`.
2. Rivers. A reach's profile runs linearly from `level_from_m` to `level_to_m` along its centreline; each cell it
   visits takes the profile at the visit's midpoint, never above the cell before it (water runs downhill), and a
   drop smaller than RIFFLE_M carries the upper level on (no step too small to read). So the water is flat inside a
   cell and steps only at an edge, at most once per edge. A reach is `dry` (a dressed dry gully, vanilla's answer)
   where one cell's own profile falls more than MAX_DROP_M (it would need several steps inside one cell), or an edge
   drop exceeds MAX_DROP_M (taller than the tallest falls piece). Backwater reaches are carried by their body;
   tidal reaches stand at 0.
3. One level per cell. A cell's candidates: the sea, bodies (by samples) and wet reaches. The sea and bodies come
   first and the most samples win (a tie to the lower level), so a river entering a lake takes the lake's level in
   the lake's cells and its step moves to the edge before the lake; among reaches alone the lowest level wins
   (the downstream level at a junction).
4. Steps (world-rebuild-options.md §11, Skyrim.esm's 80 stepped edges). Where a reach crosses an edge between two
   levels: a row from the upper cell, the channel's vertex range on that edge, the chain sized to the drop
   (steps.chain_for). Any other edge between two water cells at different levels is `closed`: the bank stands at
   or above the upper water and nothing crosses. `section()` gives the ground lane the bank and bed numbers.

Vertex ranges along an edge run 0..32 west to east on the n and s edges and south to north on the e and w edges
(the VHGT order).
"""
from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.water import steps as stp

Q = su.QUADS_PER_CELL  # 32
MPP = su.PROVINCE_SAMPLE_M
CX0, CY0 = su.PROVINCE_CELL_SW
NCELL = su.PROVINCE_CELLS  # 126
WATER_TYPES = ("sea", "brackish", "blackwater", "fresh")
SNAP_LO_M = 0.5  # below this a body is at sea level
SNAP_HI_M = 3.0  # at or above this a body keeps its own level
RIFFLE_M = 0.5  # a smaller drop between two cells carries the upper level on (steps.STEP_MAX_M, the riffle)
MAX_DROP_M = stp.MAX_DROP_M  # the tallest falls piece
LEVEL_TOL_M = 0.006  # the raster stores the graph's 2-decimal level as float32
RESAMPLE_M = 1.0  # a reach's centreline is walked at this spacing
MARSH = {"marsh-fringe", "marsh-deep", "swamp", "backswamp"}


def data_root() -> Path:
    return Path(os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data")))


@dataclass(frozen=True)
class Step:
    cx: int
    cy: int
    edge: str  # 'n' | 'e' | 's' | 'w': the drop from (cx, cy) across this edge to its neighbour
    upper_m: float
    lower_m: float
    cross_lo: int  # the channel's vertex range along the edge (0..32)
    cross_hi: int
    chain: str  # the piece chain id (steps.CHAINS), or 'closed'


class CellWater:
    """The solved water of the province, read from `cell_water` and `water_step`."""

    def __init__(self, cells: dict[tuple[int, int], tuple[float, str]], steps: list[Step]):
        self._cells = cells
        self._steps = steps
        self._keys = np.array(list(cells), dtype=np.int64).reshape(-1, 2)
        self._levels = np.array([v[0] for v in cells.values()], dtype=np.float64)

    def level(self, cx: int, cy: int) -> float | None:
        v = self._cells.get((cx, cy))
        return v[0] if v else None

    def type(self, cx: int, cy: int) -> str | None:
        v = self._cells.get((cx, cy))
        return v[1] if v else None

    def steps(self) -> list[Step]:
        return list(self._steps)

    def nearest_level(self, cx: int, cy: int) -> float:
        """The level of the nearest water cell (Euclidean in cells); 0.0 (the sea) when there is none."""
        v = self._cells.get((cx, cy))
        if v:
            return v[0]
        if not len(self._keys):
            return 0.0
        d = (self._keys[:, 0] - cx) ** 2 + (self._keys[:, 1] - cy) ** 2
        return float(self._levels[int(np.argmin(d))])


def load(w) -> CellWater:
    """The solved water from an open world database (`db.open()`)."""
    cells = {(r["cx"], r["cy"]): (r["level_m"], r["water_type"])
             for r in w.query("SELECT cx, cy, level_m, water_type FROM cell_water")}
    steps = [Step(*r) for r in w.query(
        "SELECT cx, cy, edge, upper_m, lower_m, cross_lo, cross_hi, chain FROM water_step ORDER BY cx, cy, edge")]
    return CellWater(cells, steps)


# ---- the rules -------------------------------------------------------------------------------------------------

def body_level(level_m: float, kind: str) -> float:
    """Rule 1: the sea and every body below SNAP_HI_M at 0 (the cell rule may lift a snapped one to its basin)."""
    if kind == "ocean" or level_m < SNAP_HI_M:
        return 0.0
    return round(level_m, 2)


def body_type(kind: str, band: str | None) -> str:
    """Salinity: coastal and tidal water brackish, peat and deep marsh blackwater, upland water fresh
    (50-hydrology-climate.md "Salinity", "Model estuarine salinity and tidal reach"; classify.py's classes)."""
    if kind == "ocean":
        return "sea"
    if kind in ("lagoon", "mudflat") or band == "tidal":
        return "brackish"
    if kind in MARSH:
        return "fresh" if band in ("upland", "montane") else "blackwater"
    return "fresh"


def reach_type(water: str | None, tidal: bool) -> str:
    if tidal:
        return "brackish"
    return "blackwater" if water == "blackwater" else "fresh"


def cell_of(east_m: float, south_m: float) -> tuple[int, int]:
    """Local cell indices (i east, j north, 0..NCELL-1) of a province point."""
    i = int(min(NCELL - 1, max(0, east_m // (Q * MPP))))
    j = int(min(NCELL - 1, max(0, (NCELL * Q * MPP - south_m) // (Q * MPP))))
    return i, j


def edge_between(a: tuple[int, int], b: tuple[int, int]) -> str:
    di, dj = b[0] - a[0], b[1] - a[1]
    return {(1, 0): "e", (-1, 0): "w", (0, 1): "n", (0, -1): "s"}[(di, dj)]


def edge_vertex(i: int, j: int, edge: str, east_m: float, south_m: float) -> float:
    """Where along a cell's edge a point lies, in vertices (0..32): west->east on n/s, south->north on e/w."""
    if edge in ("n", "s"):
        return east_m / MPP - i * Q
    return (NCELL * Q * MPP - south_m) / MPP - j * Q


@dataclass
class Visit:
    cell: tuple[int, int]
    s0: float
    s1: float
    cross: tuple[float, float] | None = None  # the entry point (east, south) on the edge from the cell before


def walk(points: list[tuple[float, float]]) -> tuple[list[Visit], float]:
    """The cells a centreline visits in order (4-connected: a corner crossing goes through the east/west cell
    first), with arc ranges and entry points."""
    if not points:
        return [], 0.0
    pts = [points[0]]
    s = [0.0]
    for (e0, s0), (e1, s1) in zip(points, points[1:]):
        d = math.hypot(e1 - e0, s1 - s0)
        n = max(1, math.ceil(d / RESAMPLE_M))
        for k in range(1, n + 1):
            pts.append((e0 + (e1 - e0) * k / n, s0 + (s1 - s0) * k / n))
            s.append(s[-1] + d / n)
    total = s[-1]
    out: list[Visit] = [Visit(cell_of(*pts[0]), 0.0, 0.0)]
    for p, a in zip(pts[1:], s[1:]):
        c = cell_of(*p)
        last = out[-1].cell
        if c != last:
            if c[0] != last[0] and c[1] != last[1]:  # a corner: through the e/w neighbour
                mid = (c[0], last[1])
                out[-1].s1 = a
                out.append(Visit(mid, a, a, p))
                last = mid
            out[-1].s1 = a
            out.append(Visit(c, a, a, p))
        out[-1].s1 = a
    return out, total


def profile(lf: float, lt: float, s: float, total: float) -> float:
    return lf if total <= 0 else lf + (lt - lf) * min(1.0, max(0.0, s / total))


@dataclass
class ReachSolve:
    visits: list[Visit]
    levels: list[float]
    dry: str | None = None  # why the reach is a dry gully, or None


def solve_reach(points, level_from: float, level_to: float) -> ReachSolve:
    """Rule 2 on one reach: a level per visited cell, flat inside it, monotone, riffles merged; or dry, and why."""
    visits, total = walk(points)
    levels: list[float] = []
    first: dict[tuple[int, int], float] = {}
    for v in visits:
        inside = profile(level_from, level_to, v.s0, total) - profile(level_from, level_to, v.s1, total)
        if inside > MAX_DROP_M:
            return ReachSolve(visits, [], f"{inside:.1f} m inside cell {v.cell}: several steps in one cell")
        lv = profile(level_from, level_to, (v.s0 + v.s1) / 2, total)
        if levels:
            prev = levels[-1]
            lv = prev if prev - lv < RIFFLE_M else lv
        if v.cell in first:  # a meander back into a cell: that cell has one level
            lv = first[v.cell]
        first.setdefault(v.cell, lv)
        levels.append(round(lv, 2))
    for a, b in zip(levels, levels[1:]):
        if a - b > MAX_DROP_M:
            return ReachSolve(visits, [], f"a {a - b:.1f} m edge drop: taller than the tallest falls piece")
    return ReachSolve(visits, levels)


def resolve(cands: list[tuple[int, float, str, str | None, str | None, float]]) -> tuple[float, str, str | None,
                                                                                          str | None]:
    """Rule 3: one cell's candidates (src 0 sea / 1 body / 2 reach, level, type, body, reach, weight) -> the one."""
    still = [c for c in cands if c[0] < 2]
    if still:
        best = max(still, key=lambda c: (c[5], -c[1]))
    else:
        best = min(cands, key=lambda c: c[1])
    return best[1], best[2], best[3], best[4]


def section(upper_m: float, lower_m: float) -> dict[str, float]:
    """§11's vanilla step, for the ground lane: banks at or above the upper water, the bed through the edge
    100-300 units under the upper surface, sloping into the lower cell over 1-5 vertices (more for a big drop)."""
    upm = su.UNITS_PER_METRE
    drop_u = max(0.0, upper_m - lower_m) * upm
    depth_u = min(300.0, max(100.0, 100.0 + 0.25 * drop_u))
    verts = max(1, math.ceil(drop_u / (2 * su.VERTEX_SPACING_UNITS)))
    return {"bank_min_m": upper_m, "bed_edge_m": upper_m - depth_u / upm,
            "bed_foot_m": lower_m - 100.0 / upm, "slope_vertices": float(min(verts, 28))}


# ---- the province ----------------------------------------------------------------------------------------------

@dataclass
class Result:
    cells: dict[tuple[int, int], tuple[float, str, str | None, str | None]]  # local (i, j) -> the one
    steps: list[Step]
    dry: dict[str, str]  # reach id -> why
    reach_kind: dict[str, str]  # reach id -> 'water' | 'dry'
    body_outcome: dict[str, str] = field(default_factory=dict)  # body id -> 'cells N' or a drop reason
    contested: int = 0  # cells with more than one level among candidates
    seconds: float = 0.0


def _sample_cells(rows: np.ndarray, cols: np.ndarray, n: int) -> np.ndarray:
    i = np.minimum(cols // Q, NCELL - 1)
    j = np.clip((n - 1 - rows) // Q, 0, NCELL - 1)
    return i * NCELL + j


def solve(w, raster=None) -> Result:
    """The whole province from the world database and the frozen body raster (level, sea)."""
    t0 = time.time()
    if raster is None:
        z = np.load(data_root() / "hydrology-graph-bodies.npz")
        raster = (z["level"], z["sea"])
    lev, sea = raster
    n = lev.shape[0] - 1
    cands: dict[int, list] = {}

    # the sea: per-cell sample counts
    s = np.asarray(sea[:n, :n], dtype=np.int32).reshape(NCELL, Q, NCELL, Q).sum(axis=(1, 3))  # [row cell, col cell]
    for rc, cc in zip(*np.nonzero(s)):
        j = NCELL - 1 - rc
        cands.setdefault(int(cc) * NCELL + int(j), []).append((0, 0.0, "sea", None, None, float(s[rc, cc])))

    bodies = w.query("SELECT id, kind, level_m, altitude_band, bbox_x0, bbox_y0, bbox_x1, bbox_y1, deepest_x, "
                     "deepest_y, area_m2 FROM hydrology_body ORDER BY id")
    body_cells: dict[str, set[int]] = {}
    for b in bodies:
        lvl, wt = body_level(b["level_m"] or 0.0, b["kind"]), body_type(b["kind"], b["altitude_band"])
        if b["kind"] == "ocean":
            body_cells[b["id"]] = set()
            continue
        rr = cc = np.zeros(0, dtype=np.int64)
        x0 = y0 = 0
        if b["bbox_x0"] is not None:
            x0, y0, x1, y1 = (int(b[k]) for k in ("bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1"))
            win = lev[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
            rr, cc = np.nonzero(np.abs(win - np.float32(b["level_m"])) <= LEVEL_TOL_M)
        if len(rr):
            ids, cnt = np.unique(_sample_cells(rr + max(0, y0), cc + max(0, x0), n), return_counts=True)
        else:  # not in the raster: the cell of its deepest sample, weighted by its area
            ids = np.array([_sample_cells(np.array([b["deepest_y"]]), np.array([b["deepest_x"]]), n)[0]])
            cnt = np.array([max(1.0, (b["area_m2"] or 0) / MPP ** 2)])
        body_cells[b["id"]] = set(int(k) for k in ids)
        for k, c in zip(ids, cnt):
            cands.setdefault(int(k), []).append((1, lvl, wt, b["id"], None, float(c)))

    # the snap rule's basin: a snapped body sharing a cell with a body at SNAP_HI_M or above takes the cell's level
    # (rule 3 does it: the cell holds one level, the body's samples count toward the winner's cell)

    reaches = w.query("SELECT id, kind, level_from_m, level_to_m, water, tidal, width_m FROM hydrology_reach "
                      "ORDER BY id")
    pts: dict[str, list] = {}
    for r in w.query("SELECT reach_id, east_m, south_m FROM hydrology_reach_point ORDER BY reach_id, ord"):
        pts.setdefault(r[0], []).append((r[1], r[2]))
    dry: dict[str, str] = {}
    kind: dict[str, str] = {}
    solved: dict[str, ReachSolve] = {}
    width: dict[str, float] = {}
    for r in reaches:
        rid = r["id"]
        if r["kind"] == "horizontal-backwater":
            kind[rid] = "water"  # its body carries it
            continue
        p = pts.get(rid, [])
        if not p:
            kind[rid] = "water"
            continue
        lf, lt = (0.0, 0.0) if r["kind"] == "horizontal-tidal" else (r["level_from_m"], r["level_to_m"])
        rs = solve_reach(p, lf, lt)
        if rs.dry:
            dry[rid], kind[rid] = rs.dry, "dry"
            continue
        kind[rid] = "water"
        solved[rid] = rs
        width[rid] = r["width_m"] or 4.0
        wt = reach_type(r["water"], bool(r["tidal"]))
        for v, lv in zip(rs.visits, rs.levels):
            k = v.cell[0] * NCELL + v.cell[1]
            cands.setdefault(k, []).append((2, lv, wt, None, rid, v.s1 - v.s0))

    cells: dict[tuple[int, int], tuple[float, str, str | None, str | None]] = {}
    contested = 0
    for k, cs in cands.items():
        if len({c[1] for c in cs}) > 1:
            contested += 1
        cells[(k // NCELL, k % NCELL)] = resolve(cs)

    # steps: along each wet reach, then closed edges between any two water cells at different levels
    steps: dict[tuple[int, int, str], Step] = {}
    for rid, rs in solved.items():
        half = width[rid] / 2 / MPP + 0.5
        for a, b in zip(rs.visits, rs.visits[1:]):
            if a.cell == b.cell or b.cross is None:
                continue
            la, lb = cells[a.cell][0], cells[b.cell][0]
            if abs(la - lb) < 1e-6:
                continue
            up, lo = (a, b) if la > lb else (b, a)
            e = edge_between(up.cell, lo.cell)
            x = edge_vertex(up.cell[0], up.cell[1], e, *b.cross)
            lo_v, hi_v = int(max(0, math.floor(x - half))), int(min(Q, math.ceil(x + half)))
            key = (up.cell[0], up.cell[1], e)
            u, d = max(la, lb), min(la, lb)
            steps[key] = Step(CX0 + up.cell[0], CY0 + up.cell[1], e, u, d, lo_v, max(hi_v, lo_v + 1),
                              stp.chain_for(u - d))
    for (i, j), (lv, *_rest) in cells.items():
        for e, (di, dj) in (("n", (0, 1)), ("e", (1, 0)), ("s", (0, -1)), ("w", (-1, 0))):
            o = cells.get((i + di, j + dj))
            if o is not None and lv > o[0] + 1e-6 and (i, j, e) not in steps:
                steps[(i, j, e)] = Step(CX0 + i, CY0 + j, e, lv, o[0], 0, 0, "closed")

    outcome: dict[str, str] = {}
    won: dict[str, int] = {}
    for c in cells.values():
        if c[2]:
            won[c[2]] = won.get(c[2], 0) + 1
    for b in bodies:
        bid = b["id"]
        if b["kind"] == "ocean":
            outcome[bid] = "sea cells"
        elif won.get(bid):
            outcome[bid] = f"cells {won[bid]}"
        else:
            lv = sorted({cells[(k // NCELL, k % NCELL)][0] for k in body_cells[bid]})
            outcome[bid] = "drop: its cells hold another body or the sea, at " + ", ".join(f"{x:g}" for x in lv)
    return Result({(CX0 + i, CY0 + j): v for (i, j), v in cells.items()}, sorted(steps.values(),
                  key=lambda s: (s.cx, s.cy, s.edge)), dry, kind, outcome, contested, time.time() - t0)


def write(w, res: Result) -> None:
    """Replace cell_water and water_step, set every reach's cell_kind, and save."""
    for r in w.query("SELECT cx, cy, edge FROM water_step"):
        w.delete("water_step", *r)
    for r in w.query("SELECT cx, cy FROM cell_water"):
        w.delete("cell_water", *r)
    w.insert_many("cell_water", ({"cx": cx, "cy": cy, "level_m": lv, "water_type": wt, "body_id": b,
                                  "reach_id": r} for (cx, cy), (lv, wt, b, r) in sorted(res.cells.items())))
    w.insert_many("water_step", (s.__dict__ for s in res.steps))
    for rid, k in sorted(res.reach_kind.items()):
        w.update("hydrology_reach", rid, cell_kind=k)
    w.save()  # raises on any failing check
