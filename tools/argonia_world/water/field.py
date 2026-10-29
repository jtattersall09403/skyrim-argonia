"""The water-level field: one level (metres) and one water type per heightfield sample, NaN where dry.

Inputs: the graph (through db.py), the frozen body-level and sea rasters (`hydrology-graph-bodies.npz`, the array
every patch gate and the old water compile read; identity in the world's `frozen_array` table) and the ground the
terrain lane builds LAND from (`terrain/refined-height-f32.npy`, memory-mapped). Order, each filling only dry
samples:
  1. bodies: a body's samples are the raster's samples at its level inside its bbox; a body the raster does not
     hold (promised plunge pools, bowls the terrain stage dug) floods the ground below its level from its seed
     (its deepest sample, else the plunge point of the fall that makes it);
  2. the rest of the raster's water at its own level (sea-level pockets, split bodies the graph merged);
  3. the sea mask at 0;
  4. stepped reaches: the samples within half the channel width (plus half a sample) of the centreline whose
     ground is below the step's level, at that level (the lower one where two reaches' corridors meet);
  5. the shore: water spreads onto dry ground below its level next to it, SHORE_FILL_SAMPLES samples deep (the
     lowest neighbouring level that stands above the ground), because the patched ground the terrain lane builds
     differs from the shaped ground the raster was solved on and a channel's corridor is narrower than its trench;
  6. hollows: dry ground below 0 is under the default water in game, so it is water at 0;
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.water.classify import WATER_TYPES
from tools.argonia_world.water.model import Graph
from tools.argonia_world.water.steps import Step, arcs

MPP = su.PROVINCE_SAMPLE_M
LEVEL_TOL_M = 0.006  # the raster stores the graph's 2-decimal level as float32
SHORE_FILL_SAMPLES = 3  # water spreads this many samples onto connected ground below its level (5. below)
DRY = 255


def data_root() -> Path:
    return Path(os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data")))


@dataclass
class Inputs:
    ground: np.ndarray  # (n, n) float32 metres, row 0 north
    level: np.ndarray  # (n, n) float32 body level, -inf where none
    sea: np.ndarray  # (n, n) bool

    @classmethod
    def load(cls, root: Path | None = None) -> "Inputs":
        r = root or data_root()
        z = np.load(r / "hydrology-graph-bodies.npz")
        return cls(np.load(r / "terrain" / "refined-height-f32.npy", mmap_mode="r"), z["level"], z["sea"])


@dataclass
class Field:
    level: np.ndarray  # float32, NaN dry
    wtype: np.ndarray  # uint8 index into WATER_TYPES, DRY where dry
    source: np.ndarray  # uint8: 0 dry, 1 body, 2 raster rest, 3 sea, 4 reach
    body_samples: dict[str, np.ndarray] = field(default_factory=dict)  # body id -> flat sample indices
    flooded: list[str] = field(default_factory=list)  # bodies realised by flooding from their seed
    empty: list[str] = field(default_factory=list)  # bodies with no sample at all
    reach_samples: dict[str, int] = field(default_factory=dict)
    shore_filled: int = 0
    shown: np.ndarray | None = None  # the level the plan stands over each sample (plan.plan_cells sets it)
    owner: np.ndarray | None = None  # int32 index into `owners` (the body or reach whose water it is), -1 none
    owners: list[str] = field(default_factory=list)


def _flood(ground: np.ndarray, level: float, seed: tuple[int, int], radius: int) -> tuple[np.ndarray, int, int]:
    """Samples below `level` connected (4-way) to `seed` within a square of `radius` samples: (mask, r0, c0)."""
    n = ground.shape[0]
    x, y = seed
    r0, r1 = max(0, y - radius), min(n, y + radius + 1)
    c0, c1 = max(0, x - radius), min(n, x + radius + 1)
    low = np.asarray(ground[r0:r1, c0:c1]) < level
    m = np.zeros_like(low)
    if not low[y - r0, x - c0]:
        return m, r0, c0
    m[y - r0, x - c0] = True
    while True:
        g = m.copy()
        g[1:] |= m[:-1]
        g[:-1] |= m[1:]
        g[:, 1:] |= m[:, :-1]
        g[:, :-1] |= m[:, 1:]
        g &= low
        if (g == m).all():
            return m, r0, c0
        m = g


def build(g: Graph, inp: Inputs, rules: dict[str, tuple[str, str]], steps: dict[str, list[Step]]) -> Field:
    """`rules`: entity id -> (rule, water type)."""
    n = inp.ground.shape[0]
    level = np.full((n, n), np.nan, dtype=np.float32)
    wtype = np.full((n, n), DRY, dtype=np.uint8)
    source = np.zeros((n, n), dtype=np.uint8)
    f = Field(level, wtype, source)
    f.owners = sorted(g.bodies) + sorted(steps)
    oix = {k: i for i, k in enumerate(f.owners)}
    f.owner = np.full((n, n), -1, dtype=np.int32)
    tix = {t: i for i, t in enumerate(WATER_TYPES)}
    # 1. bodies: the raster's samples first, for every body, then the floods of the bodies it does not hold (a
    # flood takes only ground the raster gives no water, so it never takes another body's samples)
    flat_raster = inp.level.ravel()

    def put(b, idx, t):
        level.ravel()[idx] = b.level_m
        wtype.ravel()[idx] = t
        source.ravel()[idx] = 1
        f.owner.ravel()[idx] = oix[b.id]
        f.body_samples[b.id] = idx

    pending = []
    for b in sorted(g.bodies.values(), key=lambda b: b.id):
        if b.kind == "ocean":
            continue
        idx = np.empty(0, dtype=np.int64)
        if b.bbox is not None:
            x0, y0, x1, y1 = b.bbox
            win = inp.level[y0:y1 + 1, x0:x1 + 1]
            have = level[y0:y1 + 1, x0:x1 + 1]
            # a sample another body already holds at the same level is shared (the graph's split parts and
            # duplicate measured bodies stand in one water)
            m = (np.abs(win - b.level_m) < LEVEL_TOL_M) & (np.isnan(have) | (np.abs(have - b.level_m) < LEVEL_TOL_M))
            rr, cc = np.nonzero(m)
            idx = (rr + y0) * n + (cc + x0)
        if idx.size:
            put(b, idx, tix[rules[b.id][1]])
        else:
            pending.append(b)
    for b in pending:
        idx = np.empty(0, dtype=np.int64)
        seed = b.deepest
        if seed is None and b.caused_by_fall and b.caused_by_fall in g.reaches:
            pts = g.reaches[b.caused_by_fall].points
            if pts:
                seed = (int(round(pts[-1][0] / MPP)), int(round(pts[-1][1] / MPP)))
        if seed is not None:
            radius = int(max(40.0, 2.0 * (b.area_m2 ** 0.5)) / MPP) + 2
            m, r0, c0 = _flood(inp.ground, b.level_m, seed, radius)
            rr, cc = np.nonzero(m)
            idx = (rr + r0) * n + (cc + c0)
            cur = level.ravel()[idx]
            idx = idx[(np.isnan(cur) & ~np.isfinite(flat_raster[idx])) | (np.abs(cur - b.level_m) < LEVEL_TOL_M)]
        if idx.size:
            f.flooded.append(b.id)
            put(b, idx, tix[rules[b.id][1]])
        else:
            f.empty.append(b.id)
    # 2. the raster's remaining water; 3. the sea
    rest = np.isfinite(inp.level) & np.isnan(level)
    level[rest] = inp.level[rest]
    sea_level = rest & (np.abs(inp.level) < LEVEL_TOL_M)
    wtype[rest] = tix["fresh"]
    wtype[sea_level] = tix["brackish"]
    source[rest] = 2
    sea = inp.sea & np.isnan(level)
    level[sea] = 0.0
    wtype[sea] = tix["sea"]
    source[sea] = 3
    # 4. stepped reaches
    for rid in sorted(steps):
        st = steps[rid]
        r = g.reaches[rid]
        if not st or len(r.points) < 2:
            continue
        t = tix[rules[rid][1]]
        a = arcs(r.points)
        ends = [s.s1 for s in st]
        lv = np.array([s.level_m for s in st], dtype=np.float32)
        rad = r.width_m / 2 + MPP / 2
        rs = rad / MPP
        count = 0
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
            s_arc = a[i] + tt * (a[i + 1] - a[i])
            k = np.minimum(np.searchsorted(ends, s_arc, side="left"), len(st) - 1)
            L = lv[k]
            win_g = np.asarray(inp.ground[r_lo:r_hi + 1, c_lo:c_hi + 1])
            win_l = level[r_lo:r_hi + 1, c_lo:c_hi + 1]
            win_s = source[r_lo:r_hi + 1, c_lo:c_hi + 1]
            take = (d <= rs) & (win_g < L) & (np.isnan(win_l) | ((win_s == 4) & (L < win_l)))
            if take.any():
                win_l[take] = L[take]
                wtype[r_lo:r_hi + 1, c_lo:c_hi + 1][take] = t
                win_s[take] = 4
                f.owner[r_lo:r_hi + 1, c_lo:c_hi + 1][take] = oix[rid]
                count += int(take.sum())
        f.reach_samples[rid] = count
    shore_fill(f, inp.ground)
    # 6. hollows: dry ground below the sea stands under the worldspace default water at 0 in game, so it is water
    hollow = np.isnan(f.level) & (np.asarray(inp.ground) < 0)
    f.level[hollow] = 0.0
    f.wtype[hollow] = tix["brackish"]
    f.source[hollow] = 6
    return f


def shore_fill(f: Field, ground: np.ndarray, rounds: int = SHORE_FILL_SAMPLES) -> int:
    """Spread water onto connected dry ground below its level, `rounds` samples deep, one row band at a time."""
    n = ground.shape[0]
    total = 0
    band = 256
    for _ in range(rounds):
        new_l = f.level.copy()
        new_t = f.wtype.copy()
        new_o = f.owner.copy() if f.owner is not None else None
        for r0 in range(0, n, band):
            r1 = min(n, r0 + band)
            a0, a1 = max(0, r0 - 1), min(n, r1 + 1)
            lv = f.level[a0:a1]
            gr = np.asarray(ground[a0:a1], dtype=np.float32)
            best = np.full(lv.shape, np.inf, dtype=np.float32)
            bt = np.full(lv.shape, DRY, dtype=np.uint8)
            bo = np.full(lv.shape, -1, dtype=np.int32)
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = np.full(lv.shape, np.nan, dtype=np.float32)
                nt = np.full(lv.shape, DRY, dtype=np.uint8)
                src_r = slice(max(0, dr), lv.shape[0] + min(0, dr))
                dst_r = slice(max(0, -dr), lv.shape[0] + min(0, -dr))
                src_c = slice(max(0, dc), n + min(0, dc))
                dst_c = slice(max(0, -dc), n + min(0, -dc))
                nb[dst_r, dst_c] = lv[src_r, src_c]
                nt[dst_r, dst_c] = f.wtype[a0:a1][src_r, src_c]
                no = np.full(lv.shape, -1, dtype=np.int32)
                if new_o is not None:
                    no[dst_r, dst_c] = f.owner[a0:a1][src_r, src_c]
                take = (nb > gr) & (nb < best)  # NaN compares False
                best[take] = nb[take]
                bt[take] = nt[take]
                bo[take] = no[take]
            grow = np.isnan(lv) & np.isfinite(best)
            k0 = r0 - a0
            g = grow[k0:k0 + (r1 - r0)]
            new_l[r0:r1][g] = best[k0:k0 + (r1 - r0)][g]
            new_t[r0:r1][g] = bt[k0:k0 + (r1 - r0)][g]
            if new_o is not None:
                new_o[r0:r1][g] = bo[k0:k0 + (r1 - r0)][g]
            total += int(g.sum())
        grown = np.isnan(f.level) & ~np.isnan(new_l)
        f.source[grown] = 5
        f.level, f.wtype = new_l, new_t
        if new_o is not None:
            f.owner = new_o
    f.shore_filled = total
    return total

