"""A river step as turned square tiles, and the step-and-pool regrade that makes each tile hold (2.W2's designed
rivers; the owner's ruling of 2026-10-29).

A step's stretch of centreline is cut into k tiles of equal length, each a square turned to the flow, its side at
least the channel's width plus two samples a side (TILE_MIN_M at the least), so one tile covers the channel and its
banks. A tile is valid when every sample under it is
  - its own water (the step's level),
  - ground at most LEAK_TOL_M below the level, dry or under a higher step's water (it hides the plane),
  - dry ground lower than that, which the regrade raises to the level plus BANK_CLEAR_M (at most RAISE_MAX_M): the
    bank holds the pool (only in the regrade's pass; in the final pass such a tile is invalid), or
  - under the step's piece: the next lower water of the same reach within OVERHANG_M past the step's downstream line
    (the overhang), or the previous higher water within OVERHANG_M before its upstream line (the underlap), where
    the rapids or cascade piece stands (vanilla hides its step lines the same way),
and no other tile of its level lies under it. Below a cascade or fall (a drop of steps.CASCADE_DROP_M or more) the
channel's first SILL_M past the lip is raised to the upper level plus BANK_CLEAR_M: the sill that holds the upper
pool, under the piece. A river does not spread over its banks (field.py): every dry vertex within BANK_RING samples
of its water and lower than it is raised the same way, so the river stands in its channel and no edge of it hangs
over lower ground; the shore of any other water above sea level is closed the same way by a berm of at most
BERM_MAX_M. The raised vertices are the `water_regrade` layer (terrain/water_regrade.py).
A tile that is not valid leaves its samples to the cell planner's axis blocks.
Before all of it the bed is carved (`carve`): every channel sample of a step (the field's corridor) stands at least
POOL_DEPTH_M below the step's level, at most CARVE_MAX_M deeper than the ground, so a steep reach's flat steps are
pools that hold water and a player can swim, not a dry slope under a level the ground stands above. The carve never
cuts below adjoining lower water (`clamp_beds`): the lip between a pool and a lower marsh, lake or river stands.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from tools.argonia_world.water.field import MPP, Field
from tools.argonia_world.water.model import Graph
from tools.argonia_world.water.plan import code_of
from tools.argonia_world.water.steps import CASCADE_DROP_M, PIECE_MIN_DROP_M, Step, arcs, at

OWN_TOL_M = 0.0051
TILE_MIN_M = 12.0
BANK_SAMPLES = 2  # a tile reaches this many samples beyond each bank
BANK_CLEAR_M = 0.15  # a raised bank or sill stands this far above the water it holds
RAISE_MAX_M = 6.0
OVERHANG_M = 2.5 * MPP
SILL_M = 1.5 * MPP
BANK_RING = 2
POOL_DEPTH_M = 1.5  # a pool's depth below its level at the least: swimming depth (the graph's depth where deeper)
CARVE_MAX_M = 6.0  # a bed is carved at most this far down
BERM_MAX_M = 1.0  # a still water's berm stands at most this far above the ground it raises


@dataclass(frozen=True)
class OPlane:
    reach: str
    step: int
    tile: int
    east_m: float  # centre
    south_m: float
    yaw_deg: float
    side_m: float
    level_m: float
    wtype: str
    idx: np.ndarray  # flat indices of the samples under it
    over: np.ndarray  # the overhang's samples (lower water under the step's piece)


def frame(n: int, east: float, south: float, yaw: float, half_u: float, half_v: float):
    """(flat indices, u along the flow, v across it) of the samples whose centres lie in the turned rectangle."""
    rad = math.hypot(half_u, half_v) / MPP + 1
    cx, cy = east / MPP, south / MPP
    c0, c1 = max(0, int(cx - rad)), min(n - 1, int(cx + rad) + 1)
    r0, r1 = max(0, int(cy - rad)), min(n - 1, int(cy + rad) + 1)
    if c0 > c1 or r0 > r1:
        e = np.empty(0)
        return e.astype(np.int64), e, e
    yy, xx = np.mgrid[r0:r1 + 1, c0:c1 + 1]
    de, ds = xx * MPP - east, yy * MPP - south
    fe, fs = math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))  # the flow in (east, south)
    u = de * fe + ds * fs
    v = -de * fs + ds * fe
    m = (np.abs(u) <= half_u) & (np.abs(v) <= half_v)
    return (yy[m] * n + xx[m]).astype(np.int64), u[m], v[m]


def footprint(n: int, east: float, south: float, yaw: float, side: float) -> np.ndarray:
    return frame(n, east, south, yaw, side / 2, side / 2)[0]


def tiles(r, s: Step) -> list[tuple[float, float, float, float]]:
    """(east, south, yaw, side) of a step's tiles, upstream first."""
    length = s.s1 - s.s0
    k = max(1, int(length // max(TILE_MIN_M, r.width_m + 2 * BANK_SAMPLES * MPP)))
    side = length / k
    return [(*at(r.points, s.s0 + (i + 0.5) * side), side) for i in range(k)]


def drops_below(g: Graph, steps: dict[str, list[Step]], rid: str) -> list[float]:
    """Each step's drop to the water below its downstream line (the next step, or the next reach's first step)."""
    st = steps[rid]
    out = [a.level_m - b.level_m for a, b in zip(st, st[1:])]
    nxt = g.reaches[rid].downstream
    out.append(st[-1].level_m - steps[nxt][0].level_m if nxt in steps and steps[nxt] else 0.0)
    return out


def plan(g: Graph, steps: dict[str, list[Step]], f: Field, ground: np.ndarray, wtypes: dict[str, str],
         leak_tol_m: float, floors: dict | None = None) -> list[OPlane]:
    """The valid tiles. With `floors` (a dict), the regrade's pass: low dry ground under a tile is accepted and its
    floor recorded ({flat index: (floor m, reach id, kind)}), and the sills below cascades are added."""
    n = ground.shape[0]
    shown = f.shown.ravel()
    owner = f.owner.ravel()
    gr = np.asarray(ground).reshape(-1)
    oix = {k: i for i, k in enumerate(f.owners)}
    taken: dict[int, set] = {}  # level code -> samples under a tile of that level
    out: list[OPlane] = []
    if floors is not None:
        _banks(f, ground, floors, leak_tol_m)
    for rid in sorted(steps):
        r = g.reaches[rid]
        st = steps[rid]
        if len(r.points) < 2 or not st:
            continue
        drops = drops_below(g, steps, rid)
        for si, s in enumerate(st):
            L = s.level_m
            if abs(L) < OWN_TOL_M:  # sea level: the default water stands there
                continue
            if floors is not None and drops[si] >= CASCADE_DROP_M:
                _sill(r, s, L, n, gr, shown, floors)
            ts = tiles(r, s)
            code = code_of(L)
            for ti, (e, so, yaw, side) in enumerate(ts):
                if side <= MPP:
                    continue
                idx, u, _ = frame(n, e, so, yaw, side / 2, side / 2)
                if idx.size == 0:
                    continue
                lv, gg = shown[idx], gr[idx]
                own = np.abs(lv - L) < OWN_TOL_M
                if not own.any():
                    continue
                with np.errstate(invalid="ignore"):
                    hidden = (np.isnan(lv) | (lv > L + OWN_TOL_M)) & (gg >= L - leak_tol_m)
                    low = np.isnan(lv) & (gg < L - leak_tol_m) & (L + BANK_CLEAR_M - gg <= RAISE_MAX_M)
                    same = owner[idx] == oix[rid]
                    over = (lv < L - OWN_TOL_M) & same & (u > side / 2 - OVERHANG_M) & \
                        (ti == len(ts) - 1) & (drops[si] >= PIECE_MIN_DROP_M)
                    if ti == 0 and si > 0 and drops[si - 1] >= PIECE_MIN_DROP_M:
                        over |= (lv > L + OWN_TOL_M) & same & (u < -side / 2 + OVERHANG_M)
                ok = own | hidden | over | (low if floors is not None else False)
                if not ok.all():
                    continue
                il = idx.tolist()
                t = taken.setdefault(code, set())
                if not t.isdisjoint(il):
                    continue
                t.update(il)
                if floors is not None:
                    for i in idx[low].tolist():
                        _floor(floors, i, L + BANK_CLEAR_M, rid, "bank")
                out.append(OPlane(rid, s.index, ti, e, so, yaw, side, L, wtypes[rid], idx, idx[over]))
    return out


def _sill(r, s: Step, L: float, n: int, gr: np.ndarray, shown: np.ndarray, floors: dict) -> None:
    """The channel's first SILL_M past the step's lip raised to hold the upper pool."""
    e, so, yaw = at(r.points, s.s1)
    fe, fs = math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))
    idx, _, _ = frame(n, e + fe * SILL_M / 2, so + fs * SILL_M / 2, yaw, SILL_M / 2, r.width_m / 2 + MPP)
    with np.errstate(invalid="ignore"):
        lift = (gr[idx] < L + BANK_CLEAR_M) & (L + BANK_CLEAR_M - gr[idx] <= RAISE_MAX_M) & \
            ~(shown[idx] > L + OWN_TOL_M)
    for i in idx[lift].tolist():
        _floor(floors, i, L + BANK_CLEAR_M, r.id, "sill")


def carve(g: Graph, steps: dict[str, list[Step]], ground: np.ndarray) -> dict:
    """{flat index: (bed ceiling m, reach id)}: each step's corridor (field.py's) carved to its pool's depth."""
    n = ground.shape[0]
    out: dict = {}
    for rid in sorted(steps):
        st = steps[rid]
        r = g.reaches[rid]
        if not st or len(r.points) < 2:
            continue
        a = arcs(r.points)
        ends = [s.s1 for s in st]
        lv = np.array([s.level_m for s in st], dtype=np.float64)
        depth = max(POOL_DEPTH_M, r.depth_m)
        rs = (r.width_m / 2 + MPP / 2) / MPP
        for i, ((e0, s0), (e1, s1)) in enumerate(zip(r.points, r.points[1:])):
            x0, y0, x1, y1 = e0 / MPP, s0 / MPP, e1 / MPP, s1 / MPP
            c_lo, c_hi = max(0, int(np.floor(min(x0, x1) - rs))), min(n - 1, int(np.ceil(max(x0, x1) + rs)))
            r_lo, r_hi = max(0, int(np.floor(min(y0, y1) - rs))), min(n - 1, int(np.ceil(max(y0, y1) + rs)))
            if c_lo > c_hi or r_lo > r_hi:
                continue
            yy, xx = np.mgrid[r_lo:r_hi + 1, c_lo:c_hi + 1]
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy
            tt = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0, 1) if L2 > 0 else np.zeros(xx.shape)
            d = np.hypot(xx - (x0 + tt * dx), yy - (y0 + tt * dy))
            k = np.minimum(np.searchsorted(ends, a[i] + tt * (a[i + 1] - a[i]), side="left"), len(st) - 1)
            bed = np.round(lv[k] - depth, 3)
            gw = np.asarray(ground[r_lo:r_hi + 1, c_lo:c_hi + 1])
            m = (d <= rs) & (np.abs(lv[k]) >= OWN_TOL_M) & (gw > bed) & (gw - bed <= CARVE_MAX_M)
            for j, z in zip((yy[m] * n + xx[m]).tolist(), bed[m].tolist()):
                if j not in out or (z, rid) < out[j]:
                    out[j] = (z, rid)
    return out


def clamp_beds(beds: dict, f: Field) -> int:
    """The carve never cuts below adjoining lower water: a carved bed sample beside (8 neighbours) water of another
    owner at a lower level is raised to the highest such level, so the lip between the two waters stands, and the
    lower water never looks into the higher one's pool under its surface. Returns the samples raised."""
    if not beds:
        return 0
    n = f.level.shape[0]
    idx = np.fromiter(beds.keys(), dtype=np.int64, count=len(beds))
    z = np.fromiter((v[0] for v in beds.values()), dtype=np.float64, count=len(beds))
    r, c = np.divmod(idx, n)
    lv, own = f.level.ravel(), f.owner.ravel()
    hi = lv[idx]
    floor = np.full(idx.shape, -np.inf)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            rr, cc = r + dr, c + dc
            ok = (rr >= 0) & (rr < n) & (cc >= 0) & (cc < n)
            j = np.where(ok, rr * n + cc, 0)
            nl = lv[j]
            with np.errstate(invalid="ignore"):
                m = ok & np.isfinite(hi) & np.isfinite(nl) & (own[j] != own[idx]) & (nl < hi - OWN_TOL_M)
            floor = np.where(m, np.maximum(floor, nl), floor)
    raise_ = floor > z
    for k in np.flatnonzero(raise_).tolist():
        i = int(idx[k])
        beds[i] = (round(float(floor[k]), 3), beds[i][1])
    return int(raise_.sum())


def _banks(f: Field, ground: np.ndarray, floors: dict, leak_tol_m: float) -> None:
    """Every dry vertex within BANK_RING samples (a square) of water above sea level and lower than it, raised to the
    highest such water plus BANK_CLEAR_M: a river's bank at most RAISE_MAX_M, any other water's berm at most
    BERM_MAX_M (a marsh or a lake is closed by a low bank, not by a wall)."""
    n = ground.shape[0]
    wet = ~np.isnan(f.level) & (np.abs(f.level) >= OWN_TOL_M) & (f.source != 3) & (f.source != 6)
    lv = np.where(wet, f.level, np.float32(-np.inf)).astype(np.float32)
    river = (f.source == 4) & wet
    best = np.full((n, n), -np.inf, dtype=np.float32)
    who = np.full((n, n), -1, dtype=np.int32)
    riv = np.zeros((n, n), dtype=bool)
    k = BANK_RING
    for dr in range(-k, k + 1):
        for dc in range(-k, k + 1):
            a = np.s_[max(0, dr):n + min(0, dr), max(0, dc):n + min(0, dc)]
            b = np.s_[max(0, -dr):n + min(0, -dr), max(0, -dc):n + min(0, -dc)]
            m = lv[a] > best[b]
            best[b] = np.where(m, lv[a], best[b])
            who[b] = np.where(m, f.owner[a], who[b])
            riv[b] = np.where(m, river[a], riv[b])
    del lv, river
    gr = np.asarray(ground, dtype=np.float32)
    cap = np.where(riv, np.float32(RAISE_MAX_M), np.float32(BERM_MAX_M))
    with np.errstate(invalid="ignore"):
        cand = np.isnan(f.level) & (gr < best - leak_tol_m) & (best + BANK_CLEAR_M - gr <= cap)
    for i in np.flatnonzero(cand).tolist():
        o = int(who.flat[i])
        _floor(floors, i, float(best.flat[i]) + BANK_CLEAR_M, f.owners[o] if o >= 0 else None,
               "bank" if riv.flat[i] else "berm")


def _floor(floors: dict, i: int, z: float, eid: str | None, kind: str) -> None:
    z = round(z, 3)
    if i not in floors or (z, eid or "") > (floors[i][0], floors[i][1] or ""):
        floors[i] = (z, eid, kind)
