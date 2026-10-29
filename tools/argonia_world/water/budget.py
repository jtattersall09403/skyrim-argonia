"""The per-cell plane budget (2.W2; the planner's ruling of 2026-10-29 on the plane count).

A cell may hold at most `budget` water-plane references (default BUDGET). A cell over it is reduced in two stages,
and every change is measured as a loss against the unreduced plan:

1. Merges, smallest loss first (loss = samples moved x centimetres): two interleaved non-river levels of the cell
   within SNAP_TOL_M stand as one (the smaller-count level takes the larger's, within this cell only: `snaps`), and
   two consecutive steps of one reach whose levels both stand in the cell become one taller step
   (steps.merge; the whole step moves, so no seam; drops stay within steps.drop_allowed(merged=True)). After each
   round the field, the turned planes and the cells are rebuilt and the counts measured again.
2. The brief's fallback for a cell still over: one water height for the cell, the weighted median of its water
   levels (the height that moves the fewest sample-centimetres). Ground below it in the cell is under that water
   (raised water, flooded ground: losses); water above it whose ground stands higher is dry (lost). At the cell's
   border the terrain is regraded: each border vertex below the height (plus REGRADE_CLEAR_M) where the water
   beyond is not at that height is raised to stand above both (`floors`), so no water sheet ends in the air; the
   terrain applies the floors through terrain/water_regrade.py.

The losses go to the world db (`water_budget_cell`, `water_loss`, `water_regrade`) through `rows()`.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dfield

import numpy as np

from tools.argonia_world.water import field as wfield
from tools.argonia_world.water import oriented, plan, steps
from tools.argonia_world.water.plan import DRYC, Q

BUDGET = 32
SNAP_TOL_M = 0.25  # interleaved levels this close may merge (kept under 2 x STEP_MAX_M: no river step snaps)
REGRADE_CLEAR_M = 0.1  # a regraded border vertex stands this far above the water it holds
MAX_ROUNDS = 8
SOURCES = ["dry", "body", "raster", "sea", "reach", "shore", "hollow"]


@dataclass
class Result:
    budget: int
    steps: dict  # reach id -> steps after the merges
    merged: set  # reaches whose steps were merged
    snaps: dict  # cell -> {code: code}
    fallback: dict  # cell -> level metres
    floors: dict  # flat sample index -> floor metres (the regrade)
    before: dict  # cell -> plane refs in the unreduced plan (cells over the budget only)
    rounds: int = 0
    ring_cut: dict = dfield(default_factory=dict)  # cell -> border vertices raised where water stood beyond


def count(cp) -> int:
    return sum(len(plan.squares(p)) for p in cp.planes) + len(cp.oplanes)


def build(g, inp, by_id, st, snaps, budget, fallback=None, ground=None, forbid=None):
    """Field, shown levels, turned planes and cells for these steps, snaps and fallback heights."""
    gr = inp.ground if ground is None else ground
    f = wfield.build(g, wfield.Inputs(gr, inp.level, inp.sea), by_id, st)
    n = gr.shape[0]
    plan.shown_levels(f, n, remap=snaps)
    if fallback:
        apply_fallback(f, gr, fallback)
    op = oriented.plan(g, st, f, gr, {rid: w for rid, (_, w) in by_id.items()}, plan.LEAK_TOL_M, forbid=forbid)
    cells = plan.plan_cells(f, gr, op, greedy_over=budget)
    return f, op, cells


def apply_fallback(f, ground, fallback: dict) -> None:
    """Each fallback cell: every sample whose ground is below the height is water at it, the rest dry."""
    n = ground.shape[0]
    for (cx, cy), h in fallback.items():
        r0, r1, c0, c1 = plan.cell_window(cx, cy, n)
        gr = np.asarray(ground[r0:r1, c0:c1])
        sh = f.shown[r0:r1, c0:c1]
        wt = f.wtype[r0:r1, c0:c1]
        wet = ~np.isnan(sh)
        t = np.bincount(wt[wet], minlength=len(wfield.WATER_TYPES)).argmax() if wet.any() else 0
        under = gr < h - 0.0051
        sh[:] = np.where(under, np.float32(h), np.float32(np.nan))
        wt[under & ~wet] = t
        wt[~under] = wfield.DRY


def _local_ops(oplanes, n, cells_n):
    """cell -> [(code, local rows, local cols, (reach, step index), home?)] for every turned plane."""
    out: dict = {}
    for op in oplanes:
        rr, cc = op.idx // n, op.idx % n
        code = plan.code_of(op.level_m)
        e, s = int(op.east_m / wfield.MPP), int(op.south_m / wfield.MPP)
        home = plan.cell_index(min(e, n - 1), min(s, n - 1), cells_n)
        keys = np.array([plan.cell_index(int(c), int(r), cells_n) for r, c in zip(rr, cc)])
        for key in {tuple(k) for k in keys.tolist()} | {home}:
            sel = (keys[:, 0] == key[0]) & (keys[:, 1] == key[1])
            r0, _, c0, _ = plan.cell_window(key[0], key[1], n)
            out.setdefault(key, []).append((code, rr[sel] - r0, cc[sel] - c0, (op.reach, op.step), key == home))
    return out


def estimate(cd: np.ndarray, gr: np.ndarray, ops: list, budget: int | None = None) -> int:
    """The plane refs plan_cells would place in a cell with these codes and turned planes (the greedy cover where
    the quadtree's passes `budget`, as plan_cells)."""
    q = _estimate(cd, gr, ops, False)
    return q if budget is None or q <= budget else min(q, _estimate(cd, gr, ops, True))


def _estimate(cd: np.ndarray, gr: np.ndarray, ops: list, greedy: bool) -> int:
    wet = cd != DRYC
    if not wet.any():
        return 0
    levels = np.unique(cd[wet])
    if len(levels) == 1 and not ops:
        ok, _ = plan.block_level(cd, gr)
        if ok:
            return 0
    total = sum(1 for o in ops if o[4])
    for code in (int(v) for v in levels):
        if code == 0:
            continue
        done = np.zeros(cd.shape, dtype=bool)
        for oc, rr, cc, _, _ in ops:
            if oc == code:
                done[rr, cc] = True
        for br, bc, nr, nc in plan.level_blocks(cd, gr, code, done, greedy):
            total += len(plan.squares(plan.Plane(0, 0, br, bc, nr, nc, 0.0, "")))
    return total


def _reduce(key, f, ground, ops, res: Result, g, glob: dict, nbodies: int) -> bool:
    """Merge levels in one cell, smallest loss first, until its estimate is within the budget. True if changed."""
    n = ground.shape[0]
    r0, r1, c0, c1 = plan.cell_window(key[0], key[1], n)
    cd = plan.codes(f.shown[r0:r1, c0:c1])
    gr = np.asarray(ground[r0:r1, c0:c1], dtype=np.float32)
    ow = f.owner[r0:r1, c0:c1]
    ops = list(ops)
    est = estimate(cd, gr, ops, res.budget)
    changed = False
    tol = int(round(SNAP_TOL_M * 100))
    while est > res.budget:
        wet = cd != DRYC
        present = set(np.unique(cd[wet]).tolist())
        rids = sorted({f.owners[i] for i in np.unique(ow[wet]).tolist() if i >= nbodies})
        step_codes = set()
        cands = []  # (loss, tiebreak, kind, payload, new cd, new ops)
        for rid in rids:
            st = res.steps[rid]
            codes_k = [plan.code_of(s.level_m) for s in st]
            step_codes.update(c for c in codes_k if c in present)
            r = g.reaches[rid]
            allowed = steps.drop_allowed(r, merged=True) + 1e-6
            for k in range(len(st) - 1):
                a, b = codes_k[k], codes_k[k + 1]
                if a not in present or b not in present:
                    continue
                new = steps.merge(r, st, k)
                lv = [s.level_m for s in new]
                if any(x - y > allowed or x - y < -1e-6 for x, y in zip(lv, lv[1:])):
                    continue
                nc = plan.code_of(new[k].level_m)
                loss = glob.get((rid, a), 0) * abs(nc - a) + glob.get((rid, b), 0) * abs(nc - b)
                oi = f.owners.index(rid)
                m = ((cd == a) | (cd == b)) & (ow == oi)
                cd2 = cd.copy()
                cd2[m] = nc
                ops2 = [o for o in ops if o[3] not in ((rid, st[k].index), (rid, st[k + 1].index))]
                cands.append((loss, (1, rid, k), "step", (rid, k, new), cd2, ops2))
        others = sorted(c for c in present if c not in step_codes)
        cnt = {c: int((cd == c).sum()) for c in others}
        for a, b in zip(others, others[1:]):
            if b - a > tol:
                continue
            if a == 0:
                src, dst = b, 0
            else:
                src, dst = (a, b) if (cnt[a], a) < (cnt[b], b) else (b, a)
            if src == 0:
                continue
            cd2 = cd.copy()
            cd2[cd == src] = dst
            cands.append((cnt[src] * abs(src - dst), (0, src, dst), "snap", (src, dst), cd2, ops))
        best = None
        for c in sorted(cands, key=lambda c: (c[0], c[1])):
            e2 = estimate(c[4], gr, c[5], res.budget)
            if e2 < est:
                best = (c, e2)
                break
        if best is None:
            break
        (loss, _, kind, payload, cd2, ops2), est = best
        if kind == "step":
            rid, k, new = payload
            res.steps[rid] = new
            res.merged.add(rid)
        else:
            src, dst = payload
            m = res.snaps.setdefault(key, {})
            for k2, v in list(m.items()):
                if v == src:
                    m[k2] = dst
            m[src] = dst
        cd, ops = cd2, ops2
        changed = True
    return changed


def _glob_counts(f) -> dict:
    """(reach id, level code) -> samples of that reach's water at that level, over the whole field."""
    nb = sum(1 for o in f.owners if o.startswith("body."))
    m = (f.owner >= nb) & ~np.isnan(f.shown)
    o = f.owner[m]
    c = np.rint(f.shown[m] * 100).astype(np.int64)
    keys, counts = np.unique(o.astype(np.int64) * (1 << 32) + (c + (1 << 31)), return_counts=True)
    return {(f.owners[int(k >> 32)], int((k & 0xFFFFFFFF) - (1 << 31))): int(v) for k, v in zip(keys, counts)}


def _floors(key, h, sh, ground) -> tuple[dict, int]:
    """Border vertices of a fallback cell raised above the height and the water beyond (the regrade)."""
    n = ground.shape[0]
    r0, r1, c0, c1 = plan.cell_window(key[0], key[1], n)
    R1, C1 = min(r1, n - 1), min(c1, n - 1)  # the shared edge vertex row/column (the next cell's first)
    out, cut = {}, 0
    ring = [(r, c, r - 1, c) for c in range(c0, C1 + 1) for r in (r0,)] + \
        [(R1, c, R1 + 1, c) for c in range(c0, C1 + 1)] + \
        [(r, c0, r, c0 - 1) for r in range(r0, R1 + 1)] + \
        [(r, C1, r, C1 + 1) for r in range(r0, R1 + 1)]
    for r, c, ro, co in ring:
        g = float(ground[r, c])
        beyond = []
        for rr, cc in ((r, c), (ro, co)):
            if 0 <= rr < n and 0 <= cc < n and not (r0 <= rr < r1 and c0 <= cc < c1):
                beyond.append(sh[rr, cc])
        lv = [float(x) for x in beyond if not np.isnan(x)]
        if lv and all(abs(x - h) < 0.0051 for x in lv):
            continue  # the same water continues across the border
        top = max([h] + lv) + REGRADE_CLEAR_M
        if g < top:
            i = r * n + c
            out[i] = max(out.get(i, -1e9), round(top, 3))
            cut += bool(lv)
    return out, cut


def run(g, inp, by_id, st0: dict, budget: int = BUDGET, log=None):
    """Reduce every cell to the budget: (result, final (field, turned planes, cells), the regraded ground, the
    unreduced field)."""
    res = Result(budget, dict(st0), set(), {}, {}, {}, {})
    n = inp.ground.shape[0]
    cells_n = (n - 1) // Q
    nb = sum(1 for b in g.bodies)
    f, op, cells = build(g, inp, by_id, res.steps, res.snaps, budget)
    f0 = f  # the unreduced plan's field: the losses are measured against it
    res.before = {k: count(cp) for k, cp in cells.items() if count(cp) > budget}
    for rnd in range(MAX_ROUNDS):
        over = sorted(k for k, cp in cells.items() if count(cp) > budget)
        if log:
            log(f"budget {budget}: round {rnd}: {len(over)} cells over")
        if not over:
            break
        glob = _glob_counts(f)
        ops = _local_ops(op, n, cells_n)
        changed = False
        for key in over:
            changed |= _reduce(key, f, inp.ground, ops.get(key, []), res, g, glob, nb)
        res.rounds = rnd + 1
        if not changed:
            break
        f, op, cells = build(g, inp, by_id, res.steps, res.snaps, budget)
    # the fallback, repeated while the regrade pushes another cell over
    ground = inp.ground
    for _ in range(4):
        over = sorted(k for k, cp in cells.items() if count(cp) > budget and k not in res.fallback)
        if not over:
            break
        sh = f.shown
        for key in over:
            r0, r1, c0, c1 = plan.cell_window(key[0], key[1], n)
            cd = plan.codes(sh[r0:r1, c0:c1])
            gr = np.asarray(inp.ground[r0:r1, c0:c1])
            wet = (cd != DRYC) & (gr < cd / 100.0)
            vals = np.sort(cd[wet])
            h = float(vals[(len(vals) - 1) // 2]) / 100.0 if vals.size else 0.0
            res.fallback[key] = h
            fl, cut = _floors(key, h, sh, inp.ground)
            for i, v in fl.items():
                res.floors[i] = max(res.floors.get(i, -1e9), v)
            res.ring_cut[key] = cut
        if log:
            log(f"budget {budget}: fallback {len(res.fallback)} cells, {len(res.floors)} regraded vertices")
        ground = regraded(inp.ground, res.floors)
        forbid = np.zeros(n * n, dtype=bool)
        for (cx, cy) in res.fallback:
            r0, r1, c0, c1 = plan.cell_window(cx, cy, n)
            forbid.reshape(n, n)[r0:r1, c0:c1] = True
        f, op, cells = build(g, inp, by_id, res.steps, res.snaps, budget, res.fallback, ground, forbid)
    return res, (f, op, cells), ground, f0


def regraded(ground: np.ndarray, floors: dict) -> np.ndarray:
    """The ground with the regrade's floors applied (a copy; the frozen array is never written)."""
    if not floors:
        return ground
    out = np.array(ground, dtype=np.float32)
    idx = np.fromiter(floors, dtype=np.int64, count=len(floors))
    val = np.fromiter((floors[i] for i in floors), dtype=np.float32, count=len(floors))
    flat = out.reshape(-1)
    flat[idx] = np.maximum(flat[idx], val)
    return out


def losses(orig_level: np.ndarray, orig_owner: np.ndarray, owners0: list, f, ground, res: Result, min_cm: int = 1):
    """Every changed sample against the unreduced field, grouped by (entity, cell, kind): the loss table's rows.
    Kinds: in a fallback cell `fallback-raised`, `fallback-lowered`, `fallback-dried`, `fallback-flooded`; else
    `step-merge` (a reach's water) or `snap` (any other water), `dried` or `flooded` where the merge moved the
    waterline."""
    n = ground.shape[0]
    cells_n = (n - 1) // Q
    a, b = orig_level, f.shown
    wa, wb = ~np.isnan(a), ~np.isnan(b)
    with np.errstate(invalid="ignore"):
        moved = wa & wb & (np.abs(np.rint(b * 100) - np.rint(a * 100)) >= min_cm)
    dried = wa & ~wb & (np.asarray(ground) < a)
    flooded = ~wa & wb
    fb = np.zeros((n, n), dtype=bool)
    for (cx, cy) in res.fallback:
        r0, r1, c0, c1 = plan.cell_window(cx, cy, n)
        fb[r0:r1, c0:c1] = True
    out: dict = {}
    for kind_mask, kind in ((moved, "moved"), (dried, "dried"), (flooded, "flooded")):
        rr, cc = np.nonzero(kind_mask)
        if rr.size == 0:
            continue
        own = np.where(orig_owner[rr, cc] >= 0, orig_owner[rr, cc], -1)
        own_b = f.owner[rr, cc]
        d = np.zeros(rr.size) if kind != "moved" else (b[rr, cc] - a[rr, cc]).astype(np.float64)
        if kind == "dried":
            d = (np.asarray(ground)[rr, cc] - a[rr, cc]).astype(np.float64)  # how far the ground stands above
        if kind == "flooded":
            d = (b[rr, cc] - np.asarray(ground)[rr, cc]).astype(np.float64)  # the new water's depth
        src = f.source[rr, cc]
        for i in range(rr.size):
            r, c = int(rr[i]), int(cc[i])
            o = int(own[i]) if own[i] >= 0 else int(own_b[i])
            ent = owners0[o] if o >= 0 else f"source:{SOURCES[int(src[i])]}"
            if fb[r, c]:
                k = {"moved": "fallback-raised" if d[i] > 0 else "fallback-lowered", "dried": "fallback-dried",
                     "flooded": "fallback-flooded"}[kind]
            elif kind == "moved":
                k = "step-merge" if ent.startswith("reach.") else "snap"
            else:
                k = kind
            key = (ent, *plan.cell_index(c, r, cells_n), k)
            e = out.setdefault(key, [0, 0.0, 0.0])
            e[0] += 1
            e[1] = max(e[1], abs(d[i]))
            e[2] += abs(d[i])
    return out
