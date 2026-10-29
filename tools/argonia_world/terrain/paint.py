"""Land-cover classes to LAND texture layers: a base layer and at most six alpha layers per quadrant.

Each vertex's class gives an LTEX; a 3 x 3 box over the one-hot field (read across cell edges, so a quadrant's
edge agrees with its neighbour's) gives each vertex a weight per LTEX. Per quadrant the reducer keeps the LTEX
with the largest total weight as the base and the next LAND_QUADRANT_LAYERS as alpha layers (strongest first,
drawn last), drops the rest and renormalises. The engine draws each alpha layer over what lies below it, so the
opacity of layer i is w_i / (w_base + w_1 + ... + w_i): composited in order, every LTEX then shows exactly its
weight. Opacities are stored as bytes (n / 255) so regeneration is byte-stable; zero entries are omitted.
"""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su

QV = su.QUADRANT_VERTS
MAX_LAYERS = su.LAND_QUADRANT_LAYERS
MIN_WEIGHT = 0.5  # a layer must cover at least half a vertex of the quadrant to be kept


def weights(ltex_idx: np.ndarray, n_ltex: int) -> np.ndarray:
    """(rows, cols) LTEX indices with a one-sample border -> (rows-2, cols-2, n_ltex) box-filtered weights."""
    h, w = ltex_idx.shape
    onehot = (ltex_idx[:, :, None] == np.arange(n_ltex, dtype=ltex_idx.dtype)).astype(np.float32)
    out = np.zeros((h - 2, w - 2, n_ltex), dtype=np.float32)
    for dy in range(3):
        for dx in range(3):
            out += onehot[dy:dy + h - 2, dx:dx + w - 2]
    return out / 9.0


def quadrant_layers(wq: np.ndarray) -> tuple[int, list[tuple[int, np.ndarray]]]:
    """(17, 17, n) weights of one quadrant, [y, x] from its south-west -> (base LTEX index, [(LTEX index,
    opacity bytes (17, 17) uint8)] in draw order, weakest first)."""
    tot = wq.sum(axis=(0, 1))
    order = [int(i) for i in np.argsort(-tot, kind="stable") if tot[i] > 0]
    keep = [order[0]] + [i for i in order[1:1 + MAX_LAYERS] if tot[i] >= MIN_WEIGHT]
    w = wq[:, :, keep].astype(np.float64)
    s = w.sum(axis=2)
    w = np.where(s[:, :, None] > 0, w / np.where(s > 0, s, 1)[:, :, None], 0.0)
    w[:, :, 0] = np.where(s > 0, w[:, :, 0], 1.0)  # a vertex with no kept weight shows the base
    cum = w[:, :, 0].copy()
    layers = []
    for j in range(len(keep) - 1, 0, -1):  # weakest first, strongest drawn last
        cum = cum + w[:, :, j]
        a = np.where(cum > 0, w[:, :, j] / np.where(cum > 0, cum, 1), 0.0)
        a8 = np.rint(a * 255).astype(np.uint8)
        if a8.any():
            layers.append((keep[j], a8))
    return keep[0], layers


def composite(base: int, layers: list[tuple[int, np.ndarray]], n_ltex: int) -> np.ndarray:
    """What the engine shows: (17, 17, n) weights from a base and alpha layers drawn in order (a check)."""
    out = np.zeros((QV, QV, n_ltex))
    out[:, :, base] = 1.0
    for i, a in layers:
        f = a.astype(np.float64)[:, :, None] / 255.0
        out *= 1 - f
        out[:, :, i] += f[:, :, 0]
    return out
