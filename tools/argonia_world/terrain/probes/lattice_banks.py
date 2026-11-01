"""Probe (1.15 ground): where the bank role's on-line lattice excess sits: on-line bank samples split by what the
cell line is there (beside a dry cell, between two levels, between equal levels; raster or padded cell), each with
its share of the excess and the mean ground minus the level. Usage: python3 -m tools.argonia_world.terrain.probes.lattice_banks"""
import numpy as np

from tools.argonia_world import db
from tools.argonia_world.terrain import cellwater, generate as G
from tools.argonia_world.terrain.cellwater import C, Q

g = np.load("out/terrain/ground-f32.npy", mmap_mode="r")
role = np.load("out/terrain/role-u8.npy", mmap_mode="r")
w = cellwater.load(db.open())
vmin, vmax = G.vertex_levels(w.level)
N = C * Q
rows = slice(None, None, 8)
d2 = np.abs(np.diff(np.asarray(g[rows], np.float64), 2, axis=1))
base = d2[:, (np.arange(1, d2.shape[1] + 1) % 16) != 0].mean()
cols = np.arange(16, N, 16)  # interior cell-line columns; d2 index col-1
dd = d2[:, cols - 1]
ro = np.asarray(role[rows])[:, cols]
lv0, lv1 = vmin[rows][:, cols], vmax[rows][:, cols]
ri = np.minimum(np.arange(0, N + 1, 8) // Q, C - 1)
left, right = w.level[ri][:, cols // Q - 1], w.level[ri][:, cols // Q]
kind = np.where(np.isnan(left) | np.isnan(right), "dry-side", np.where(np.abs(left - right) > 0.5, "two-levels", "same-level"))
gg = np.asarray(g[rows], np.float64)[:, cols]
tot = (dd[ro == 3] - base).sum()
for k in ("dry-side", "two-levels", "same-level"):
    m = (ro == 3) & (kind == k)
    if m.any():
        print(k, "samples", int(m.sum()), "ratio", round(dd[m].mean() / base, 2), "excess share",
              round(float((dd[m] - base).sum() / tot), 2), "ground-vmax mean", round(float(np.nanmean((gg - lv1)[m])), 2))
