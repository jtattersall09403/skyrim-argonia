"""Probe (1.15 ground): 4-neighbour steps over a threshold in out/terrain ground, by cell and the roles either side.
Usage: python3 -m tools.argonia_world.terrain.probes.ground_big_steps [threshold_m]"""
import collections
import sys

import numpy as np

from tools.argonia_world.terrain.cellwater import C, CX0, CY0, Q

thr = float(sys.argv[1]) if len(sys.argv) > 1 else 14.0
g = np.load("out/terrain/ground-f32.npy").astype(np.float64)
role = np.load("out/terrain/role-u8.npy")
cnt = collections.Counter()
for ax in (0, 1):
    d = np.abs(np.diff(g, axis=ax))
    ii, jj = np.nonzero(d > thr)
    for i, j in zip(ii, jj):
        i2, j2 = (i + 1, j) if ax == 0 else (i, j + 1)
        cx, cy = CX0 + min(j, C * Q - 1) // Q, CY0 + C - 1 - min(i, C * Q - 1) // Q
        cnt[(cx, cy, int(role[i, j]), int(role[i2, j2]))] += 1
print(len(cnt), "cell/role pairs;", sum(cnt.values()), "steps")
for k, v in cnt.most_common(25):
    print(k, v)
