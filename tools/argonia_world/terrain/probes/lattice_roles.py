"""Probe (1.15 ground): the check's lattice ratio (second difference on the 16-sample lines over off them) split by
role (0 dry, 1 wet, 2 step slope, 3 bank of a water cell, 4 shore), with each role's share of the on-line excess.
Usage: python3 -m tools.argonia_world.terrain.probes.lattice_roles"""
import numpy as np

g = np.load("out/terrain/ground-f32.npy", mmap_mode="r")
role = np.load("out/terrain/role-u8.npy", mmap_mode="r")
d2 = np.abs(np.diff(np.asarray(g[::8], np.float64), 2, axis=1))
ro = np.asarray(role[::8])[:, 1:-1]
on = (np.arange(1, d2.shape[1] + 1) % 16) == 0
print("all", round(d2[:, on].mean() / d2[:, ~on].mean(), 3))
base = d2[:, ~on].mean()
for k in range(5):
    m = ro == k
    a, b = d2[:, on][m[:, on]], d2[:, ~on][m[:, ~on]]
    if a.size and b.size:
        print(k, "ratio", round(a.mean() / b.mean(), 2), "on-line excess share",
              round(float((a.sum() - a.size * base) / (d2[:, on].sum() - d2[:, on].size * base)), 2))
