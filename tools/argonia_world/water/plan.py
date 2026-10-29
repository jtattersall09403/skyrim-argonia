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
# Within a cell, water levels closer than this stand as one level (the most common of them): the marsh sheets'
# levels interleave a few centimetres apart, and every distinct level is its own set of planes. Kept under
# STEP_MAX_M so a river's steps never merge. The change it makes is measured (`snap` in the plan) and is the loss.
SNAP_M = 0.0
# Water shallower than this at a sample need not be covered (a plane covers it when it passes): the ragged film at
# a marsh sheet's edge is otherwise one tiny plane per sample. The film left uncovered is measured (`shallowLeft`).
SHALLOW_M = 0.0  # measured: 0.1 m saves 10 % of the planes but leaves 1,400 bodies' edges bare (see the journal)
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
    req = own & (gr < code / 100.0 - SHALLOW_M)  # a film shallower than SHALLOW_M is covered only in passing
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


def snap(cd: np.ndarray, snap_cm: int) -> np.ndarray:
    """Levels grouped from the lowest while within `snap_cm` of the group's first; each group takes its most
    common level (the higher on a tie)."""
    wet = cd != DRYC
    if snap_cm <= 0 or not wet.any():
        return cd
    vals, counts = np.unique(cd[wet], return_counts=True)
    to = {}
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] - vals[i] <= snap_cm:
            j += 1
        grp = range(i, j + 1)
        rep = max(grp, key=lambda k: (counts[k], vals[k]))
        for k in grp:
            to[int(vals[k])] = int(vals[rep])
        i = j + 1
    out = cd.copy()
    out[wet] = np.vectorize(to.__getitem__, otypes=[np.int32])(cd[wet])
    return out


def shown_levels(f: Field, n: int, snap_m: float = SNAP_M, remap: dict | None = None) -> None:
    """Set `f.shown`: each cell's water levels after `snap` and the budget's per-cell `remap` ({cell: {code:
    code}}, budget.py), the levels the plan stands."""
    f.shown = f.level.copy()
    cells = (n - 1) // Q
    sc = int(round(snap_m * 100))
    for iy in range(cells):
        for ix in range(cells):
            key = (CX0 + ix, CY0 + cells - 1 - iy)
            m = (remap or {}).get(key)
            r0, r1, c0, c1 = cell_window(*key, n)
            cd = snap(codes(f.level[r0:r1, c0:c1]), sc)
            for a, b in (m or {}).items():
                cd[cd == a] = b
            wet = cd != DRYC
            if wet.any():
                f.shown[r0:r1, c0:c1][wet] = cd[wet] / 100.0


def plan_cells(f: Field, ground: np.ndarray, oplanes: list | None = None,
               greedy_over: int | None = None) -> dict[tuple[int, int], CellPlan]:
    """Every cell's plan from `f.shown` (shown_levels first) and the turned step planes already placed. A cell whose
    quadtree planes number more than `greedy_over` takes the greedy cover where that is smaller."""
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
            best, best_k = [], float("inf")
            for greedy in (False, True):
                planes = []
                for code in (int(v) for v in levels):
                    if code == 0:
                        continue  # the default water already stands at 0 here
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


def check_bodies(g: Graph, f: Field, R: np.ndarray, ground: np.ndarray, tol_m: float = SNAP_M,
                 lost: dict | None = None) -> dict:
    """Every body has water over every one of its samples whose ground lies below its shown level (its level after
    the snap; the snap's own loss is measured in check_wet): the default water,
    a cell water height or a plane, at its level within the snap (the ocean: the worldspace default water at 0).
    A body whose every sample is above its level on the terrain lane's ground (patched since the graph was
    solved) has no water to show: it is listed as `buried`, and counted uncovered."""
    sh = f.shown.ravel()
    Rr = R.ravel()
    gr = ground.reshape(-1)
    bad, buried, stands_in, carve_lost, recorded = [], [], {}, [], []
    covered = 0
    n = ground.shape[0]
    for b in g.bodies.values():
        if b.kind == "ocean":
            ok = True
        elif b.realised_by and b.realised_by in g.bodies:
            ok = True  # the graph's own record: another body realises it (the Blackrose lake's bowl)
            stands_in[b.id] = {"in": b.realised_by, "why": "realised_by"}
        else:
            idx = f.body_samples.get(b.id)
            if idx is not None and idx.size:
                idx = idx[np.asarray(gr[idx]) < sh[idx] - 0.0051]
                if idx.size == 0:
                    buried.append(b.id)
            # realised at the level the plan stands (the budget's merges move it: the move is a recorded loss)
            ok = idx is not None and idx.size > 0 and bool(np.all(np.abs(Rr[idx] - sh[idx]) <= tol_m + 0.0051))
        if not ok and b.lost_at_carve:
            carve_lost.append(b.id)  # the graph records it lost at the carve: no water of its own by design
            ok = True
        elif not ok and b.deepest is not None:
            # a body with no water of its own whose deepest sample stands in other water (a carve-made backswamp
            # inside a lower sheet): that water realises it, at its own level; the difference is listed
            x, y = b.deepest
            i = y * n + x
            if not np.isnan(sh[i]) and float(gr[i]) < sh[i] and abs(Rr[i] - sh[i]) <= 0.0051:
                ok = True
                stands_in[b.id] = {"levelM": b.level_m, "shownM": round(float(sh[i]), 3)}
        if not ok and lost and b.id in lost:
            ok = True  # no water of its own left, and the loss is recorded (water_loss)
            recorded.append(b.id)
        covered += ok
        if not ok:
            bad.append(b.id)
    return {"bodies": len(g.bodies), "covered": covered, "uncovered": bad, "buried": buried,
            "standsInOtherWater": stands_in, "lostAtCarve": carve_lost, "recordedLoss": recorded}


def check_wet(f: Field, R: np.ndarray, ground: np.ndarray, tol_m: float = SNAP_M) -> dict:
    """Every wet sample whose ground lies below its shown level has that level over it; the snap's loss is the
    samples it dried (shown below their ground though their own level is above it)."""
    wet = ~np.isnan(f.level)
    gr = np.asarray(ground)
    below = wet & (gr < f.shown - 0.0051)
    miss = below & ~(np.abs(R - f.shown) <= 0.0051)
    dried = wet & (gr >= f.shown - 0.0051) & (gr < f.level)
    moved = np.abs(f.shown[wet] - f.level[wet])
    moved = moved[~np.isnan(moved)]  # a fallback cell's dried samples are counted in driedBySnapOrRounding
    return {"wetSamples": int(wet.sum()), "wetAboveGround": int(below.sum()),
            "groundAboveItsWater": int((wet & (gr >= f.level)).sum()), "driedBySnapOrRounding": int(dried.sum()),
            "unrealised": int(miss.sum()),
            "snappedSamples": int((moved > 0.0051).sum()), "snapMaxM": round(float(moved.max()) if moved.size else 0.0, 3),
            "snapMeanM": round(float(moved.mean()) if moved.size else 0.0, 4)}


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
    """Every plane sample that is not its own water must be hidden by ground (no sheet over lower water or air)."""
    floating, stacked = 0, 0
    for cp in cells.values():
        for p in cp.planes:
            sl = (slice(p.r0, p.r0 + p.rows), slice(p.c0, p.c0 + p.cols))
            lv = f.shown[sl]
            own = np.abs(lv - p.level_m) < 0.0051
            gr = np.asarray(ground[sl])
            floating += int((~own & (gr < p.level_m - LEAK_TOL_M)).sum())
            stacked += int((~own & ~np.isnan(lv)).sum())
        for op in cp.oplanes:
            lv = f.shown.ravel()[op.idx]
            own = np.abs(lv - op.level_m) < 0.0051
            gr = np.asarray(ground.reshape(-1)[op.idx])
            floating += int((~own & (gr < op.level_m - LEAK_TOL_M)).sum())
            stacked += int((~own & ~np.isnan(lv)).sum())
    return {"floatingSamples": floating, "underHigherWaterSamples": stacked}


def check_steps(g: Graph, steps: dict[str, list[Step]], merged: set | frozenset = frozenset()) -> dict:
    """Each step's level inside the graded profile over its run, and each drop within the grade's step (the
    merged one where the budget merged the reach's steps)."""
    bad, n, max_dev, max_drop = [], 0, 0.0, 0.0
    for rid, st in steps.items():
        r = g.reaches[rid]
        allowed = drop_allowed(r, rid in merged) + 1e-6
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
