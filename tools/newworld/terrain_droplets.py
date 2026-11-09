"""Particle hydraulic erosion at the heightmap's full resolution (after Beyer 2015, "Implementation of a method for
hydraulic erosion"): many rain droplets run downhill over the ground, picking up sediment where they speed up and
dropping it where they slow, so slopes carry branching rills and gullies that join and widen downstream, and the
eroded sediment settles as fans and smooth valley floors. Runs inside terrain_erode.weather on dry land only: a
droplet ends at the water or the grid's edge, so no water course is added; the caller holds the ground above the
water afterwards.

Heights in metres, one cell a sample (1.83 m). `k` scales erosion and deposition per sample (0 on marsh floors and
mesa tops). Seeded; droplets run on every core at once, so two runs differ only where two droplets touched the same
sample in the same instant (millimetres).
"""
from __future__ import annotations

import numpy as np
try:
    from numba import njit, prange
except ImportError:            # numba (the nwvenv has it) only makes it fast; the recipe is the same without it
    prange = range

    def njit(*a, **k):
        return (lambda f: f) if not (len(a) == 1 and callable(a[0])) else a[0]

INERTIA = 0.05
CAPACITY = 4.0
MIN_SLOPE = 0.01
DEPOSIT = 0.3
ERODE = 0.5
EVAPORATE = 0.015
GRAVITY = 4.0
MAX_STEPS = 80
RADIUS = 3


def _brush(r: int):
    oi, oj, w = [], [], []
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            d = (di * di + dj * dj) ** 0.5
            if d <= r:
                oi.append(di)
                oj.append(dj)
                w.append(1 - d / r if r else 1.0)
    w = np.array(w, np.float64)
    return np.array(oi, np.int64), np.array(oj, np.int64), w / w.sum()


@njit(cache=True)
def _grad(h, x, y):
    i, j = int(y), int(x)
    u, v = x - j, y - i
    a, b, c, d = h[i, j], h[i, j + 1], h[i + 1, j], h[i + 1, j + 1]
    gx = (b - a) * (1 - v) + (d - c) * v
    gy = (c - a) * (1 - u) + (d - b) * u
    z = a * (1 - u) * (1 - v) + b * u * (1 - v) + c * (1 - u) * v + d * u * v
    return gx, gy, z


@njit(cache=True, parallel=True)
def _run(h, k, stop, starts, oi, oj, ow, inertia, capacity, min_slope, deposit, erode, evaporate, gravity,
         max_steps):
    R, C = h.shape
    for n in prange(starts.shape[0]):
        x, y = starts[n, 1], starts[n, 0]
        dx = 0.0
        dy = 0.0
        speed = 1.0
        water = 1.0
        sed = 0.0
        for _ in range(max_steps):
            i, j = int(y), int(x)
            if i < 1 or j < 1 or i >= R - 2 or j >= C - 2 or stop[i, j]:
                break
            u, v = x - j, y - i
            gx, gy, z0 = _grad(h, x, y)
            dx = dx * inertia - gx * (1 - inertia)
            dy = dy * inertia - gy * (1 - inertia)
            ln = (dx * dx + dy * dy) ** 0.5
            if ln < 1e-9:
                break
            dx /= ln
            dy /= ln
            x += dx
            y += dy
            ni, nj = int(y), int(x)
            if ni < 1 or nj < 1 or ni >= R - 2 or nj >= C - 2:
                break
            _, _, z1 = _grad(h, x, y)
            dz = z1 - z0
            cap = max(-dz, min_slope) * speed * water * capacity
            if sed > cap or dz > 0:
                # deposit at the old position, bilinearly
                amt = min(dz, sed) if dz > 0 else (sed - cap) * deposit
                sed -= amt
                kk = k[i, j]
                amt *= kk
                h[i, j] += amt * (1 - u) * (1 - v)
                h[i, j + 1] += amt * u * (1 - v)
                h[i + 1, j] += amt * (1 - u) * v
                h[i + 1, j + 1] += amt * u * v
            else:
                amt = min((cap - sed) * erode, -dz)
                for b in range(oi.shape[0]):
                    bi, bj = i + oi[b], j + oj[b]
                    if bi < 0 or bj < 0 or bi >= R or bj >= C:
                        continue
                    e = amt * ow[b] * k[bi, bj]
                    if e > 0:
                        h[bi, bj] -= e
                        sed += e
            speed = (max(speed * speed + dz * gravity, 0.0)) ** 0.5
            water *= 1 - evaporate
    return h


def erode(h: np.ndarray, k: np.ndarray, stop: np.ndarray, droplets: int, seed: int = 1952) -> np.ndarray:
    """`h` eroded by `droplets` droplets started at random on samples where k > 0 and not `stop`. Returns a copy."""
    rng = np.random.default_rng(seed)
    cand = np.flatnonzero((k.ravel() > 0.02) & ~stop.ravel())
    if cand.size == 0 or droplets <= 0:
        return h.copy()
    pick = cand[rng.integers(0, cand.size, droplets)]
    starts = np.stack([pick // h.shape[1], pick % h.shape[1]], 1).astype(np.float64)
    starts += rng.uniform(0, 1, starts.shape)
    oi, oj, ow = _brush(RADIUS)
    out = h.astype(np.float64).copy()
    _run(out, k.astype(np.float64), stop, starts, oi, oj, ow, INERTIA, CAPACITY, MIN_SLOPE, DEPOSIT, ERODE,
         EVAPORATE, GRAVITY, MAX_STEPS)
    return out.astype(np.float32)
