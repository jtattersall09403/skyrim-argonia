"""Probe (1.15 ground): vertices a dry cell shares with a water cell at or below that water, by cell and role, and
step-edge banks below the upper water. Usage: python3 -m tools.argonia_world.terrain.probes.dry_edge"""
import collections

import numpy as np

from tools.argonia_world import db
from tools.argonia_world.terrain import cellwater, generate as G

g = np.load("out/terrain/ground-f32.npy").astype(np.float64)
role = np.load("out/terrain/role-u8.npy")
w = cellwater.load(db.open())
vmin, vmax = G.vertex_levels(w.level)
i = np.arange(G.N + 1)
lo_c, hi_c = np.clip((i - 1) // G.Q, 0, G.C - 1), np.clip(i // G.Q, 0, G.C - 1)
dryc = np.isnan(w.level)
touch = np.zeros(g.shape, bool)
for a in (lo_c, hi_c):
    for b in (lo_c, hi_c):
        touch |= dryc[a][:, b]
bad = touch & ~np.isnan(vmax) & ~(g > vmax)
print("dry-edge bad", int(bad.sum()), "roles", np.bincount(role[bad], minlength=5).tolist(),
      "depth under vmax p50/max", np.round(np.percentile(vmax[bad] - g[bad], [50, 100]), 2).tolist() if bad.any() else 0)
cnt = collections.Counter((G.CX0 + int(c) // G.Q, G.CY0 + G.C - 1 - int(r) // G.Q) for r, c in zip(*np.nonzero(bad)))
print(cnt.most_common(12))
