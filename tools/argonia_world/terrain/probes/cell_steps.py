"""Probe (1.15 ground): one cell's water and ground: its level and its 8 neighbours', ground range by role, and the
largest 4-neighbour steps inside it with the ground, role and lowest/highest level either side.
Usage: python3 -m tools.argonia_world.terrain.probes.cell_steps CX CY [n]"""
import sys

import numpy as np

from tools.argonia_world import db
from tools.argonia_world.terrain import cellwater, generate as G
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, Q

cx, cy = int(sys.argv[1]), int(sys.argv[2])
n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
g = np.load("out/terrain/ground-f32.npy", mmap_mode="r")
role = np.load("out/terrain/role-u8.npy", mmap_mode="r")
w = cellwater.load(db.open())
vmin, vmax = G.vertex_levels(w.level)
r0, c0 = (C - 1 - (cy - CY0)) * Q, (cx - CX0) * Q
ci, cj = C - 1 - (cy - CY0), cx - CX0
print("levels (rows north to south):")
for a in (-1, 0, 1):
    print("  ", [None if not (0 <= ci + a < C and 0 <= cj + b < C) or np.isnan(w.level[ci + a, cj + b])
                 else round(float(w.level[ci + a, cj + b]), 2) for b in (-1, 0, 1)])
sl = (slice(r0, r0 + Q + 1), slice(c0, c0 + Q + 1))
gg, rr = np.asarray(g[sl], np.float64), np.asarray(role[sl])
for k in range(5):
    if (rr == k).any():
        print(f"role {k}: {int((rr == k).sum())} samples, ground {gg[rr == k].min():.1f}..{gg[rr == k].max():.1f}")
steps = []
for ax in (0, 1):
    d = np.abs(np.diff(gg, axis=ax))
    for i, j in zip(*np.nonzero(d > 10)):
        i2, j2 = (i + 1, j) if ax == 0 else (i, j + 1)
        steps.append((float(d[i, j]), (int(i), int(j)), (int(i2), int(j2))))
steps.sort(reverse=True)
V0, V1 = vmin[sl], vmax[sl]
for s, p, q in steps[:n]:
    print(f"step {s:.1f} m  {p}: g {gg[p]:.1f} role {rr[p]} lv {V0[p]:.2f}/{V1[p]:.2f}   "
          f"{q}: g {gg[q]:.1f} role {rr[q]} lv {V0[q]:.2f}/{V1[q]:.2f}")
