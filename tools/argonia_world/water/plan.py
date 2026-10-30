"""The water plan (2.W2 §a): per exterior cell, the worldspace default (the sea at 0), one cell water height, or
placed water planes; the step pieces; and the L1 checks over all of it.

A cell's water is one level when every wet sample in it shares that level and no dry sample lies more than
LEAK_TOL_M below it (the plane would show over dry ground): a level of 0 is the default water, any other a cell
water height. Otherwise the cell keeps the default water (or none, `noWater`, where dry ground below the sea would
show it) and its other levels are placed planes: square blocks of samples split as a quadtree until each block
holds one level and no dry ground below it. Blocks partition the cell, so no two planes overlap by construction;
the z-fight check proves it on the output. A plane is vanilla's flat 1024-unit water mesh (bounds +-512, measured on
Skyrim.esm's Water1024) scaled to its block, one water-plane activator per water type.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.water.classify import WATER_TYPES
from tools.argonia_world.water.field import DRY, MPP, Field
from tools.argonia_world.water.model import Graph
from tools.argonia_world.water.steps import Piece, Step, arcs, at, drop_allowed

Q = su.QUADS_PER_CELL  # 32 samples per cell side
CX0, CY0 = su.PROVINCE_CELL_SW
LEAK_TOL_M = 0.05  # dry ground this far under a plane is a wet film at the waterline, not a floating sheet
PLANE_MESH_UNITS = 1024.0  # Water1024.nif: a flat square, object bounds -512..512 (Skyrim.esm, 2026-10-29)
BANK_OFFSET_SAMPLES = 2  # a bank is sampled this far beyond the channel's half width
BANK_TOL_M = 0.05


@dataclass(frozen=True)
class Plane:
    cx: int
    cy: int
    r0: int  # first sample row (north) and column (west) of the block
    c0: int
    rows: int
    cols: int
    level_m: float
    wtype: str


@dataclass
class CellPlan:
    cx: int
    cy: int
    mode: str  # default | height | planes
    level_m: float | None = None  # the cell water height (mode height)
    wtype: str | None = None
    planes: list[Plane] = field(default_factory=list)
    oplanes: list = field(default_factory=list)  # turned step planes (oriented.OPlane) whose centre is here
    pieces: list[Piece] = field(default_factory=list)


def cell_index(x: int, y: int, cells: int) -> tuple[int, int]:
    """(cx, cy) of the cell owning sample column x, row y (row 0 north); the last row/column joins the edge cell."""
    ix = min(x // Q, cells - 1)
    iy = min(y // Q, cells - 1)
    return CX0 + ix, CY0 + cells - 1 - iy


def cell_window(cx: int, cy: int, n: int) -> tuple[int, int, int, int]:
    """(r0, r1, c0, c1) sample rows/columns a cell owns."""
    cells = (n - 1) // Q
    ix, iy = cx - CX0, cells - 1 - (cy - CY0)
    r0, c0 = iy * Q, ix * Q
    return r0, (n if iy == cells - 1 else r0 + Q), c0, (n if ix == cells - 1 else c0 + Q)


def codes(level: np.ndarray) -> np.ndarray:
    """Levels as integer centimetres; dry = a sentinel no level takes."""
    c = np.full(level.shape, np.iinfo(np.int32).min, dtype=np.int32)
    wet = ~np.isnan(level)
    c[wet] = np.rint(level[wet] * 100).astype(np.int32)
    return c


DRYC = np.iinfo(np.int32).min


def code_of(level_m: float) -> int:
    """A level as `codes` writes it (float32 centimetres, rounded half to even): every level-to-code goes here."""
    return int(np.rint(np.float32(level_m) * np.float32(100)))


def block_level(cd: np.ndarray, gr: np.ndarray) -> tuple[bool, int | None]:
    """(valid, level code) for a block: one wet level (or none) and no dry ground below it."""
    wet = cd != DRYC
    if not wet.any():
        return True, None
    vals = cd[wet]
    lv = int(vals[0])
    if (vals != lv).any():
        return False, None
    if (gr[~wet] < lv / 100.0 - LEAK_TOL_M).any():
        return False, None
    return True, lv


def cover(req: np.ndarray, ok: np.ndarray, r0: int, c0: int, rows: int, cols: int, out: list) -> None:
    """Blocks covering every required sample, each wholly inside the allowed samples (a quadtree)."""
    if not req[r0:r0 + rows, c0:c0 + cols].any():
        return
    if ok[r0:r0 + rows, c0:c0 + cols].all():
        out.append((r0, c0, rows, cols))
        return
    if rows == 1 and cols == 1:
        raise AssertionError("a required sample is always allowed")
    hr, hc = (rows + 1) // 2 if rows > 1 else 1, (cols + 1) // 2 if cols > 1 else 1
    for dr, nr in ((0, hr), (hr, rows - hr)):
        for dc, nc in ((0, hc), (hc, cols - hc)):
            if nr > 0 and nc > 0:
                cover(req, ok, r0 + dr, c0 + dc, nr, nc, out)


def _integral(m: np.ndarray) -> np.ndarray:
    out = np.zeros((m.shape[0] + 1, m.shape[1] + 1), dtype=np.int32)
    out[1:, 1:] = m.cumsum(0).cumsum(1)
    return out


def _box(integral: np.ndarray, k: int) -> np.ndarray:
    return integral[k:, k:] - integral[:-k, k:] - integral[k:, :-k] + integral[:-k, :-k]


def greedy_cover(req: np.ndarray, ok: np.ndarray) -> list:
    """Non-overlapping squares inside the allowed samples covering every required one, the largest first (at any
    offset; the one covering the most required samples among equals, then the first in row order). Fewer planes
    than the quadtree where a shoreline or a diagonal channel staircases (measured: a third fewer in the cells over
    16); used where the quadtree's count passes the budget."""
    free, need = ok.copy(), req & ok
    out = []
    while need.any():
        fi, ni = _integral(free), _integral(need)
        lo, hi, best = 1, min(free.shape), None
        while lo <= hi:  # the largest valid side (validity is monotone in the side)
            k = (lo + hi) // 2
            nb = _box(ni, k)
            valid = (_box(fi, k) == k * k) & (nb > 0)
            if valid.any():
                i = int(np.where(valid, nb, -1).argmax())
                best = (*divmod(i, valid.shape[1]), k)
                lo = k + 1
            else:
                hi = k - 1
        r, c, k = best
        out.append((r, c, k, k))
        free[r:r + k, c:c + k] = False
        need[r:r + k, c:c + k] = False
    return out


def level_blocks(cd: np.ndarray, gr: np.ndarray, code: int, done: np.ndarray | None = None,
                 greedy: bool = False) -> list:
    """A plane at level `code` may stand over its own water and over ground that hides it (dry ground, or the bed
    under a higher step's water, at most LEAK_TOL_M below it); never over lower water or open low ground, and
    never where a turned step plane of the same level already stands (`done`)."""
    own = cd == code
    req = own & (gr < code / 100.0)
    hidden = gr >= code / 100.0 - LEAK_TOL_M
    ok = own | (((cd == DRYC) | (cd > code)) & hidden)
    if done is not None:
        req &= ~done
        ok &= ~done
    if greedy:
        return greedy_cover(req, ok)
    out: list = []
    cover(req, ok, 0, 0, cd.shape[0], cd.shape[1], out)
    return out


def shown_levels(f: Field) -> None:
    """Set `f.shown`: the levels the plan stands, each the field's level rounded to its centimetre code."""
    f.shown = f.level.copy()
    wet = ~np.isnan(f.level)
    f.shown[wet] = np.rint(f.level[wet] * np.float32(100)) / np.float32(100)


def plan_cells(f: Field, ground: np.ndarray, oplanes: list | None = None,
               greedy_over: int | None = None) -> dict[tuple[int, int], CellPlan]:
    """Every cell's plan from `f.shown` (shown_levels first) and the turned step planes already placed. A cell whose
    quadtree planes number more than `greedy_over` takes the greedy cover where that is smaller (0: every cell takes
    the smaller of the two covers)."""
    n = ground.shape[0]
    cells = (n - 1) // Q
    out: dict[tuple[int, int], CellPlan] = {}
    by_cell: dict[tuple[int, int], list] = {}  # cell -> [(code, local mask indices)] of the turned planes
    for op in oplanes or []:
        rr, cc = op.idx // n, op.idx % n
        code = code_of(op.level_m)
        keys = np.array([cell_index(int(c), int(r), cells) for r, c in zip(rr, cc)])
        for key in {tuple(k) for k in keys.tolist()}:
            sel = (keys[:, 0] == key[0]) & (keys[:, 1] == key[1])
            by_cell.setdefault(key, []).append((code, rr[sel], cc[sel]))
        e, s = int(op.east_m / MPP), int(op.south_m / MPP)
        home = cell_index(min(e, n - 1), min(s, n - 1), cells)
        out.setdefault(home, CellPlan(*home, "planes")).oplanes.append(op)
    for iy in range(cells):
        for ix in range(cells):
            cx, cy = CX0 + ix, CY0 + cells - 1 - iy
            r0, r1, c0, c1 = cell_window(cx, cy, n)
            gr = np.asarray(ground[r0:r1, c0:c1], dtype=np.float32)
            cd = codes(f.shown[r0:r1, c0:c1])
            wet = cd != DRYC
            here = by_cell.get((cx, cy), [])
            if not wet.any():
                continue
            levels = np.unique(cd[wet])
            if len(levels) == 1 and not here and (cx, cy) not in out:
                ok, code = block_level(cd, gr)
                if ok and code == 0:
                    continue  # the default water realises it
                if ok:
                    t = np.bincount(f.wtype[r0:r1, c0:c1][wet], minlength=len(WATER_TYPES)).argmax()
                    out[(cx, cy)] = CellPlan(cx, cy, "height", code / 100.0, WATER_TYPES[t])
                    continue
            cp = out.setdefault((cx, cy), CellPlan(cx, cy, "planes"))
            wt = f.wtype[r0:r1, c0:c1]
            base = base_level(cd, gr, levels, {oc for oc, _, _ in here} | {code_of(o.level_m) for o in cp.oplanes})
            if base is not None:  # the cell's lowest water is its cell water height; only the higher are planes
                sub = wt[cd == base]
                cp.mode, cp.level_m = "height", base / 100.0
                cp.wtype = WATER_TYPES[np.bincount(sub[sub != DRY], minlength=len(WATER_TYPES)).argmax()]
            best, best_k = [], float("inf")
            for greedy in (False, True):
                planes = []
                for code in (int(v) for v in levels):
                    if code == 0 or code == base:
                        continue  # the default water, or the cell's own water height, already stands here
                    done = np.zeros(cd.shape, dtype=bool)
                    for oc, rr, cc in here:
                        if oc == code:
                            done[rr - r0, cc - c0] = True
                    sub = wt[cd == code]
                    t = np.bincount(sub[sub != DRY], minlength=len(WATER_TYPES)).argmax()
                    for br, bc, nr, nc in level_blocks(cd, gr, code, done, greedy):
                        planes.append(Plane(cx, cy, r0 + br, c0 + bc, nr, nc, code / 100.0, WATER_TYPES[t]))
                k = sum(len(squares(p)) for p in planes)
                if not greedy or k < best_k:
                    best, best_k = planes, k
                if greedy_over is None or best_k + len(cp.oplanes) <= greedy_over:
                    break
            cp.planes.extend(best)
    return out


def base_level(cd: np.ndarray, gr: np.ndarray, levels, tile_codes: set) -> int | None:
    """The code of a cell's lowest water when it can stand as the cell's water height under the planes of the
    higher: it is above sea level, no dry ground lies below it (it would show there), every higher water's bed hides
    it (no water surface under another), and no turned tile stands at it."""
    lo = int(levels[0])
    if lo <= 0 or len(levels) < 2 or lo in tile_codes:
        return None
    wet = cd != DRYC
    z = lo / 100.0 - LEAK_TOL_M
    if (gr[~wet] < z).any() or (gr[wet & (cd > lo)] < z).any():
        return None
    return lo


def squares(p: Plane) -> list[tuple[int, int, int]]:
    """A plane block as square meshes (r0, c0, side) tiling it exactly (the mesh scales uniformly)."""
    out, stack = [], [(p.r0, p.c0, p.rows, p.cols)]
    while stack:
        r0, c0, rows, cols = stack.pop()
        s = min(rows, cols)
        k = max(rows, cols) // s
        for i in range(k):
            out.append((r0 + i * s, c0, s) if rows > cols else (r0, c0 + i * s, s))
        if rows > cols and rows - k * s:
            stack.append((r0 + k * s, c0, rows - k * s, cols))
        elif cols >= rows and cols - k * s:
            stack.append((r0, c0 + k * s, rows, cols - k * s))
    return sorted(out)


def plane_refs(p: Plane) -> list[dict]:
    """Placed-reference fields for a plane, in Skyrim units: centre, z, scale (the mesh is 1024 units square)."""
    out = []
    for r0, c0, side in squares(p):
        east = (c0 + (side - 1) / 2) * MPP
        south = (r0 + (side - 1) / 2) * MPP
        x, y = su.province_to_skyrim(east, south)
        out.append({"pos": [su.rounded(x, 2), su.rounded(y, 2), su.rounded(su.metres_to_units(p.level_m), 2)],
                    "rot": [0.0, 0.0, 0.0], "scale": su.rounded(side * su.VERTEX_SPACING_UNITS / PLANE_MESH_UNITS, 6)})
    return out


# --- the L1 checks --------------------------------------------------------------------------------------------
def realised(f: Field, cells: dict[tuple[int, int], CellPlan], n: int) -> np.ndarray:
    """The level the plan puts over each sample (NaN where none): default 0, the cell height, or its plane.
    Cell bases first, then every plane (a turned step plane reaches into its neighbours)."""
    R = np.zeros((n, n), dtype=np.float32)  # the default water at 0 everywhere a cell sets nothing
    for cp in cells.values():
        if cp.mode == "height":
            r0, r1, c0, c1 = cell_window(cp.cx, cp.cy, n)
            R[r0:r1, c0:c1] = cp.level_m
    for cp in cells.values():
        for op in cp.oplanes:
            rr, cc = op.idx // n, op.idx % n
            own = np.abs(f.shown[rr, cc] - op.level_m) < 0.0051
            R[rr[own], cc[own]] = op.level_m
        for p in cp.planes:  # a plane realises the samples whose water is its level
            win = R[p.r0:p.r0 + p.rows, p.c0:p.c0 + p.cols]
            own = np.abs(f.shown[p.r0:p.r0 + p.rows, p.c0:p.c0 + p.cols] - p.level_m) < 0.0051
            win[own] = p.level_m
    return R


def check_bodies(g: Graph, f: Field, R: np.ndarray, ground: np.ndarray, design) -> dict:
    """Every body by its designed outcome (design.py): the sea and a body at sea level stand under the default water;
    a body at its own level has water realised over every one of its samples below its level (or the graph's
    `realised_by` body does); a basin's body is realised by its basin, which has water and every sample of it
    realised; a dropped body is listed with its reason. `uncovered` lists any other body: a failure."""
    sh, Rr = f.shown.ravel(), R.ravel()
    gr = np.asarray(ground).reshape(-1)
    basin_ok = {}
    for b in design.basins:
        basin_ok[b.id] = b.outcome == "kept" and b.samples > 0
    bad, dropped, outcomes = [], {}, {}
    for b in g.bodies.values():
        outcome, basin, reason = design.body[b.id]
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        if outcome == "dropped":
            dropped[b.id] = reason or next(x.reason for x in design.basins if x.id == basin)
            continue
        if outcome == "basin":
            ok = basin_ok.get(basin, False)
        elif outcome == "own-level" and not (b.realised_by and b.realised_by in g.bodies):
            idx = f.body_samples.get(b.id)
            idx = idx[gr[idx] < sh[idx] - 0.0051] if idx is not None else None
            ok = idx is not None and idx.size > 0 and bool(np.all(np.abs(Rr[idx] - sh[idx]) <= 0.0051))
        else:
            ok = True
        if not ok:
            bad.append(b.id)
    return {"bodies": len(g.bodies), "outcomes": outcomes, "realised": len(g.bodies) - len(dropped) - len(bad),
            "droppedByDesign": len(dropped), "uncovered": bad, "dropped": dropped}


def check_wet(f: Field, R: np.ndarray, ground: np.ndarray) -> dict:
    """Every wet sample whose ground lies below its shown level has that level over it."""
    wet = ~np.isnan(f.level)
    gr = np.asarray(ground)
    below = wet & (gr < f.shown - 0.0051)
    miss = below & ~(np.abs(R - f.shown) <= 0.0051)
    return {"wetSamples": int(wet.sum()), "wetAboveGround": int(below.sum()),
            "groundAboveItsWater": int((wet & (gr >= f.level)).sum()), "unrealised": int(miss.sum())}


def check_walls(f: Field, ground: np.ndarray, pieces: list, tol_m: float = LEAK_TOL_M) -> dict:
    """Water beside lower dry ground (its edge would stand in the air): wet samples with a 4-neighbour that is dry
    and lower than the water by more than `tol_m`; those within two samples of a step piece are under the piece."""
    n = ground.shape[0]
    gr = np.asarray(ground)
    lv = f.shown
    wet = ~np.isnan(lv)
    wall = np.zeros((n, n), dtype=bool)
    height = np.zeros((n, n), dtype=np.float32)
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a = np.s_[max(0, dr):n + min(0, dr), max(0, dc):n + min(0, dc)]
        b = np.s_[max(0, -dr):n + min(0, -dr), max(0, -dc):n + min(0, -dc)]
        with np.errstate(invalid="ignore"):
            m = wet[b] & ~wet[a] & (gr[a] < lv[b] - tol_m)
        wall[b] |= m
        height[b] = np.maximum(height[b], np.where(m, lv[b] - gr[a], 0))
    near = np.zeros((n, n), dtype=bool)
    for p in pieces:
        c, r = int(round(p.east_m / MPP)), int(round(p.south_m / MPP))
        near[max(0, r - 2):r + 3, max(0, c - 2):c + 3] = True
    w = wall & ~near
    hs = height[w]
    src = np.bincount(f.source[w], minlength=7)
    return {"samples": int(w.sum()), "underPieces": int((wall & near).sum()),
            "bySource": {k: int(v) for k, v in zip(["dry", "body", "raster", "sea", "reach", "shore", "hollow"], src)},
            "heightP50M": round(float(np.percentile(hs, 50)), 2) if hs.size else 0.0,
            "heightP90M": round(float(np.percentile(hs, 90)), 2) if hs.size else 0.0,
            "heightMaxM": round(float(hs.max()), 2) if hs.size else 0.0}


def check_sides(f: Field, ground: np.ndarray, pieces: list, tol_m: float = 0.05) -> dict:
    """Open sides between waters: a water sample beside (4 neighbours) lower water whose ground stands more than
    `tol_m` below that lower water's level, so the lower water looks into the higher one under its surface; those
    within two samples of a step piece are under the piece. Counted, by the higher water's source."""
    n = ground.shape[0]
    gr = np.asarray(ground)
    lv = f.shown
    side = np.zeros((n, n), dtype=bool)
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        a = np.s_[max(0, dr):n + min(0, dr), max(0, dc):n + min(0, dc)]
        b = np.s_[max(0, -dr):n + min(0, -dr), max(0, -dc):n + min(0, -dc)]
        with np.errstate(invalid="ignore"):
            side[b] |= (lv[a] < lv[b] - tol_m) & (gr[b] < lv[a] - tol_m)
    near = np.zeros((n, n), dtype=bool)
    for p in pieces:
        c, r = int(round(p.east_m / MPP)), int(round(p.south_m / MPP))
        near[max(0, r - 2):r + 3, max(0, c - 2):c + 3] = True
    w = side & ~near
    src = np.bincount(f.source[w], minlength=7)
    return {"samples": int(w.sum()), "underPieces": int((side & near).sum()),
            "bySource": {k: int(v) for k, v in zip(["dry", "body", "raster", "sea", "reach", "shore", "hollow"], src)}}


def footprints(cells: dict[tuple[int, int], CellPlan], n: int):
    """(level code, flat sample indices) of every plane, blocks and turned step planes alike."""
    for cp in cells.values():
        for p in cp.planes:
            rr, cc = np.mgrid[p.r0:p.r0 + p.rows, p.c0:p.c0 + p.cols]
            yield code_of(p.level_m), (rr * n + cc).ravel()
        for op in cp.oplanes:
            yield code_of(op.level_m), op.idx


def check_overlap(cells: dict[tuple[int, int], CellPlan], n: int) -> dict:
    """No two planes over one sample at one height; no plane at its cell's own water level (z-fight risk)."""
    by_code: dict[int, list] = {}
    for code, idx in footprints(cells, n):
        by_code.setdefault(code, []).append(idx)
    same = 0
    for parts in by_code.values():
        allx = np.concatenate(parts)
        same += int(allx.size - np.unique(allx).size)
    at_cell = 0
    for cp in cells.values():
        base = cp.level_m if cp.mode == "height" else 0.0
        at_cell += sum(abs(p.level_m - base) < 0.0051 for p in cp.planes)
        at_cell += sum(abs(op.level_m - base) < 0.0051 for op in cp.oplanes)
    return {"sameHeightOverlapSamples": same, "planesAtCellLevel": at_cell}


def check_float(f: Field, cells: dict[tuple[int, int], CellPlan], ground: np.ndarray) -> dict:
    """Every plane sample that is not its own water must be hidden by ground (no sheet over lower water or air); a
    tile's overhang (lower water under its step's piece, oriented.py) is counted apart."""
    floating, stacked, overhang = 0, 0, 0
    for cp in cells.values():
        for p in cp.planes:
            sl = (slice(p.r0, p.r0 + p.rows), slice(p.c0, p.c0 + p.cols))
            lv = f.shown[sl]
            own = np.abs(lv - p.level_m) < 0.0051
            gr = np.asarray(ground[sl])
            floating += int((~own & (gr < p.level_m - LEAK_TOL_M)).sum())
            stacked += int((~own & ~np.isnan(lv)).sum())
        for op in cp.oplanes:
            keep = ~np.isin(op.idx, op.over)
            idx = op.idx[keep]
            lv = f.shown.ravel()[idx]
            own = np.abs(lv - op.level_m) < 0.0051
            gr = np.asarray(ground.reshape(-1)[idx])
            floating += int((~own & (gr < op.level_m - LEAK_TOL_M)).sum())
            stacked += int((~own & ~np.isnan(lv)).sum())
            overhang += int(op.over.size)
    return {"floatingSamples": floating, "underHigherWaterSamples": stacked, "overhangSamples": overhang}


def check_steps(g: Graph, steps: dict[str, list[Step]]) -> dict:
    """Each step's level inside the graded profile over its run, and each drop within the grade's step."""
    bad, n, max_dev, max_drop = [], 0, 0.0, 0.0
    for rid, st in steps.items():
        r = g.reaches[rid]
        allowed = drop_allowed(r) + 1e-6
        for s in st:
            n += 1
            dev = max(0.0, s.profile_lo_m - s.level_m, s.level_m - s.profile_hi_m)
            max_dev = max(max_dev, dev)
            if dev > 1e-6:
                bad.append(f"{rid}#{s.index}: level {s.level_m:.3f} outside {s.profile_lo_m:.3f}..{s.profile_hi_m:.3f}")
        for a, b in zip(st, st[1:]):
            d = a.level_m - b.level_m
            max_drop = max(max_drop, d)
            if d < -1e-6 or d > allowed:
                bad.append(f"{rid}#{a.index}->{b.index}: drop {d:.3f} m (allowed 0..{allowed:.3f})")
    return {"steps": n, "violations": bad, "maxDeviationM": round(max_dev, 4), "maxDropM": round(max_drop, 3)}


def _ground_at(ground: np.ndarray, east: float, south: float, water: np.ndarray | None = None) -> float:
    """The bank's top: the ground, or the water standing on it (a lake or the sea beside the channel)."""
    n = ground.shape[0]
    c = min(n - 1, max(0, int(round(east / MPP))))
    r = min(n - 1, max(0, int(round(south / MPP))))
    g = float(ground[r, c])
    if water is not None and not np.isnan(water[r, c]):
        g = max(g, float(water[r, c]))
    return g


def check_banks(g: Graph, steps: dict[str, list[Step]], ground: np.ndarray, water: np.ndarray | None = None) -> dict:
    """The step's water level against the ground just beyond each bank, at every centreline point."""
    flagged: dict[str, dict] = {}
    points = 0
    for rid, st in steps.items():
        r = g.reaches[rid]
        if len(r.points) < 2:
            continue
        a = arcs(r.points)
        off = r.width_m / 2 + BANK_OFFSET_SAMPLES * MPP
        worst, nbad = 0.0, 0
        for s in a:
            e, so, yaw = at(r.points, s)
            k = min(range(len(st)), key=lambda i: 0 if st[i].s0 <= s <= st[i].s1 else min(abs(s - st[i].s0), abs(s - st[i].s1)))
            L = st[k].level_m
            ny, nx = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))  # flow (north, east)
            # the banks lie perpendicular: (east, south) offsets of the left and right normals
            left = _ground_at(ground, e - ny * off, so - nx * off, water)
            right = _ground_at(ground, e + ny * off, so + nx * off, water)
            ex = L - min(left, right)
            points += 1
            if ex > BANK_TOL_M:
                nbad += 1
                worst = max(worst, ex)
        if nbad:
            flagged[rid] = {"points": nbad, "of": len(a), "maxAboveBankM": round(worst, 3)}
    return {"reaches": len(steps), "points": points, "flagged": flagged}


def sample_reach(g: Graph, steps: dict[str, list[Step]], drop_m: float = 4.0, length_m: float = 200.0) -> str:
    """The stepped-river proof's reach: the stepped reach closest to `drop_m` over `length_m`."""
    def score(rid):
        r = g.reaches[rid]
        return abs((r.level_from_m - r.level_to_m) - drop_m) / drop_m + abs(r.length_m - length_m) / length_m
    return min(sorted(steps), key=score)
