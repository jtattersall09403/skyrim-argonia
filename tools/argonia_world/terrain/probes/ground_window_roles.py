"""Probe (1.15 ground): per water cell in a window, the share of wet/bank roles and the bank height above water,
from out/terrain ground and role. Usage: python3 -m tools.argonia_world.terrain.probes.ground_window_roles x0 y0 x1 y1 [outdir]"""
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world import db
from tools.argonia_world.terrain import cellwater
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, Q
from tools.argonia_world.terrain.generate import vertex_levels

x0, y0, x1, y1 = map(int, sys.argv[1:5])
out = Path(sys.argv[5]) if len(sys.argv) > 5 else Path("out/terrain")
g = np.load(out / "ground-f32.npy", mmap_mode="r")
role = np.load(out / "role-u8.npy", mmap_mode="r")
w = cellwater.load(db.open())
vmin, vmax = vertex_levels(w.level)
tot = {}
for cy in range(y1, y0 - 1, -1):
    line = []
    for cx in range(x0, x1 + 1):
        i, j = C - 1 - (cy - CY0), cx - CX0
        sl = (slice(i * Q, i * Q + Q + 1), slice(j * Q, j * Q + Q + 1))
        r = np.asarray(role[sl]); gg = np.asarray(g[sl], float)
        lv = w.level[i, j]
        if np.isnan(lv):
            line.append("  ----  ")
            continue
        wet = (r == 1).mean(); bank = (r == 3).mean()
        above = float(np.median(gg[r == 3] - vmax[sl][r == 3])) if (r == 3).any() else 0
        line.append(f"{wet:.2f}/{bank:.2f}/{above:+.1f}")
        for k in range(6):
            tot[k] = tot.get(k, 0) + int((r == k).sum())
    print(f"{cy:4d} " + " ".join(line))
print("roles", tot)
