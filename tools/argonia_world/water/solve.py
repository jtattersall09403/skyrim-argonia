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
   between SNAP_LO_M and SNAP_HI_M (1,086 of them) whose samples reach ground at or below 0: each snaps to 0, the
   sea-level marsh it is (Argonia's lowland
   is a tidal marsh plain: docs/design/world/50-hydrology-climate.md "Define sea level, tidal zones"),
   unless it shares a cell with a body that
   stands at SNAP_HI_M or above: then the cell rule (3) gives it that body's level, its basin's. Bodies at
   SNAP_HI_M and above, and a snappable body whose samples all stand on ground above 0, keep their `level_m`.
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
   **Enclosed cells (decision 0034, Skyrim.esm measured by terrain/probes/vanilla_lake_cells.py):** vanilla gives
   every cell a lake or marsh touches its level, cells with no ground under it included, and leaves no hole inside
   a body (Lake Ilinalta: 51 cells, 4 all-dry, 0 enclosed holes). So a group of cells with no candidate that no
   path of such cells joins to the province edge takes the level its ring of water cells holds most (by shared
   edges; a tie to the lower level), with that ring's type and body (`fill_enclosed`). The ground lane shapes the
   shore inside such a cell; the water plane under dry ground is not seen. Then the padding ring (`pad_ring`,
   skyrim-does-it-this-way.md §2): each cell beside water takes a neighbour's level, so no water stops on a cell
   edge against a dry cell.
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
# Skyrim.esm's water steps (terrain/probes/vanilla_step_chains.py, 2026-11-02): the tallest real one-edge step is
# 65.7 m (one 394.6 m pair under a mountain aside); taller drops are chained over cells (105.7 m in two steps of
# 51.1 and 54.6 m, 13 cells start a chain of two or more). No vanilla edge holds one wall a cell's ground cannot carry.
# Ours, the same (planner ruling, session 8): two waters at Chebyshev distance d cells may differ by at most
# d x WALL_STEP_M; past it the upper water yields the cell, cell by cell, so a taller drop becomes a chain of steps
# each within vanilla's or a dry gully the ground descends (`yield_walls`).
WALL_STEP_M = 65.7
PAD_REACH_M = 0.3  # a padding cell's ground dips to within this of the level (terrain FREEBOARD_M)
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

def body_level(level_m: float, kind: str, ground_min_m: float | None = None) -> float:
    """Rule 1: the sea and every body below SNAP_HI_M at 0 (the cell rule may lift a snapped one to its basin),
    except that a body never drops below the ground its own raster samples stand on: one whose samples' lowest
    ground (`ground_min_m`) stands above 0 keeps its own level (snapped to 0 it would be a plate of empty cells)."""
    if kind == "ocean" or level_m < SNAP_LO_M:
        return 0.0
    if level_m < SNAP_HI_M and (ground_min_m is None or ground_min_m <= 0.0):
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


def fill_enclosed(cells: dict[tuple[int, int], tuple], n: int = NCELL, ground_min=None) -> dict[tuple[int, int], tuple]:
    """Rule 3's enclosed cells: each 4-connected group of cells absent from `cells` that does not reach the grid
    edge takes the value its bordering cells hold most (by shared edges; a tie to the lower level). With
    `ground_min`, a cell of the group whose lowest ground stands more than PAD_REACH_M above that level stays dry
    (an island: no water plane under a whole cell of ground). Returns the added cells only."""
    seen: set[tuple[int, int]] = set()
    added: dict[tuple[int, int], tuple] = {}
    for i0 in range(n):
        for j0 in range(n):
            if (i0, j0) in cells or (i0, j0) in seen:
                continue
            comp, st, edge, ring = [(i0, j0)], [(i0, j0)], False, {}
            seen.add((i0, j0))
            while st:
                a, b = st.pop()
                for c in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if not (0 <= c[0] < n and 0 <= c[1] < n):
                        edge = True
                    elif c in cells:
                        v = cells[c]
                        ring[(v[0], v[1])] = (ring.get((v[0], v[1]), (0, v))[0] + 1, v)
                    elif c not in seen:
                        seen.add(c)
                        comp.append(c)
                        st.append(c)
            if edge or not ring:
                continue
            _, v = max(ring.values(), key=lambda kv: (kv[0], -kv[1][0]))
            for c in comp:
                if ground_min is None or ground_min(*c) <= v[0] + PAD_REACH_M:
                    added[c] = (v[0], v[1], v[2], None)
    return added


def pad_ring(cells: dict[tuple[int, int], tuple], n: int = NCELL, ground_min=None) -> dict[tuple[int, int], tuple]:
    """Vanilla's padding ring (skyrim-does-it-this-way.md §2: 23 of Skyrim.esm's 510 explicit-level cells have no
    wet vertex; the level is carried one cell past the water): every cell absent from `cells` with a water cell
    among its 8 neighbours takes the lowest of their levels (with that cell's type and body): a step between two
    levels stays on the higher water's own edge, as a closed bank, and never moves a tall bank beside the lower
    water's bed. The water plane then runs under the shore's ground, never stopping on a cell edge against a dry
    cell. With `ground_min` ((i, j) -> the cell's lowest ground, metres) a cell is padded only to a level its ground
    reaches (lowest ground at or under the level + PAD_REACH_M): vanilla's padding cells hold ground just above the
    level (0-8 units, probes/vanilla_lake_padding.py), never a whole cell standing over it (that drew the plates and
    the level-0 cell on a 40 m hillside). Returns the added cells only."""
    added: dict[tuple[int, int], tuple] = {}
    for (i, j) in {(a + di, b + dj) for (a, b) in cells for di in (-1, 0, 1) for dj in (-1, 0, 1)}:
        if (i, j) in cells or not (0 <= i < n and 0 <= j < n):
            continue
        nb = [cells[(i + di, j + dj)] for di in (-1, 0, 1) for dj in (-1, 0, 1) if (i + di, j + dj) in cells]
        if ground_min is not None:
            nb = [c for c in nb if ground_min(i, j) <= c[0] + PAD_REACH_M]
            if not nb:
                continue
        v = min(nb, key=lambda c: c[0])
        added[(i, j)] = (v[0], v[1], v[2], None)
    return added


def yield_walls(cells: dict[tuple[int, int], tuple], keep: set[tuple[int, int]] = frozenset()) -> set:
    """Every cell whose water stands more than d x WALL_STEP_M above a water cell d cells away (Chebyshev, d <= 2)
    leaves `cells` (in place), repeated until none does: the drop then runs through dry ground over at least one more
    cell (a chain of steps each within Skyrim.esm's tallest, or a dry gully). Sea cells and `keep` (the
    wet reaches' cells, whose steps the falls chains carry) never yield. Returns the removed cells."""
    gone: set[tuple[int, int]] = set()
    while True:
        bad = set()
        for (i, j), v in cells.items():
            if v[1] == "sea" or (i, j) in keep:
                continue
            for di in range(-2, 3):
                for dj in range(-2, 3):
                    o = cells.get((i + di, j + dj))
                    if o is not None and v[0] - o[0] > WALL_STEP_M * max(abs(di), abs(dj)):
                        bad.add((i, j))
        if not bad:
            return gone
        for c in bad:
            del cells[c]
        gone |= bad


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
    enclosed: int = 0  # cells given their ring's level by fill_enclosed
    walls: int = 0  # cells yielded to a dry gully by yield_walls
    seconds: float = 0.0


def _sample_cells(rows: np.ndarray, cols: np.ndarray, n: int) -> np.ndarray:
    i = np.minimum(cols // Q, NCELL - 1)
    j = np.clip((n - 1 - rows) // Q, 0, NCELL - 1)
    return i * NCELL + j


def solve(w, raster=None, ground=None) -> Result:
    """The whole province from the world database, the frozen body raster (level, sea) and the refined ground
    (metres, the raster's grid; loaded with the raster, None skips the ground tests)."""
    t0 = time.time()
    if raster is None:
        z = np.load(data_root() / "hydrology-graph-bodies.npz")
        raster = (z["level"], z["sea"])
        gp = data_root() / "terrain" / "refined-height-f32.npy"
        ground = np.load(gp, mmap_mode="r") if ground is None and gp.exists() else ground
    lev, sea = raster
    n = lev.shape[0] - 1
    gmin = None
    if ground is not None:
        gmin = np.asarray(ground[:n, :n], dtype=np.float32).reshape(NCELL, Q, NCELL, Q).min(axis=(1, 3))
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
        wt = body_type(b["kind"], b["altitude_band"])
        if b["kind"] == "ocean":
            body_cells[b["id"]] = set()
            continue
        rr = cc = np.zeros(0, dtype=np.int64)
        x0 = y0 = 0
        if b["bbox_x0"] is not None:
            x0, y0, x1, y1 = (int(b[k]) for k in ("bbox_x0", "bbox_y0", "bbox_x1", "bbox_y1"))
            win = lev[max(0, y0):y1 + 1, max(0, x0):x1 + 1]
            rr, cc = np.nonzero(np.abs(win - np.float32(b["level_m"])) <= LEVEL_TOL_M)
        gm = None
        if ground is not None and len(rr):
            gm = float(np.asarray(ground[max(0, y0):y1 + 1, max(0, x0):x1 + 1])[rr, cc].min())
        lvl = body_level(b["level_m"] or 0.0, b["kind"], gm)
        if len(rr):
            ids, cnt = np.unique(_sample_cells(rr + max(0, y0), cc + max(0, x0), n), return_counts=True)
        else:  # not in the raster: the cell of its deepest sample, weighted by its area
            ids = np.array([_sample_cells(np.array([b["deepest_y"]]), np.array([b["deepest_x"]]), n)[0]])
            cnt = np.array([max(1.0, (b["area_m2"] or 0) / MPP ** 2)])
        body_cells[b["id"]] = set(int(k) for k in ids)
        for k, c in zip(ids, cnt):
            lk = lvl  # a snapped body's cell whose ground stands wholly above 0 holds the body at its own level
            if gmin is not None and lvl == 0.0 and b["level_m"] and b["level_m"] >= SNAP_LO_M \
                    and gmin[NCELL - 1 - int(k) % NCELL, int(k) // NCELL] > 0.0:
                lk = round(b["level_m"], 2)
            cands.setdefault(int(k), []).append((1, lk, wt, b["id"], None, float(c)))

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
    if gmin is not None:  # raster water on a cell's edge reaches it: that cell holds the level whatever its ground
        wet = (lev[:n, :n] > -1e9) | np.asarray(sea[:n, :n], bool)
        near = wet.copy()
        near[1:] |= wet[:-1]
        near[:-1] |= wet[1:]
        near[:, 1:] |= wet[:, :-1]
        near[:, :-1] |= wet[:, 1:]
        gmin = np.where(near.reshape(NCELL, Q, NCELL, Q).any(axis=(1, 3)), -np.inf, gmin)
        del wet, near
    gm_cell = None if gmin is None else (lambda i, j: float(gmin[NCELL - 1 - j, i]))
    enclosed = fill_enclosed(cells, ground_min=gm_cell)
    cells.update(enclosed)
    padded = pad_ring(cells, ground_min=gm_cell)
    cells.update(padded)
    enclosed.update(padded)
    walls = yield_walls(cells, {v.cell for rs in solved.values() for v in rs.visits})
    for c in walls:
        enclosed.pop(c, None)

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
            lv = sorted({cells[(k // NCELL, k % NCELL)][0] for k in body_cells[bid] if (k // NCELL, k % NCELL) in cells})
            outcome[bid] = "drop: its cells hold another body or the sea, at " + ", ".join(f"{x:g}" for x in lv)
    return Result({(CX0 + i, CY0 + j): v for (i, j), v in cells.items()}, sorted(steps.values(),
                  key=lambda s: (s.cx, s.cy, s.edge)), dry, kind, outcome, contested, len(enclosed), len(walls),
                  time.time() - t0)


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
