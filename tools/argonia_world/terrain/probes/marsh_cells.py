"""Probe (1.15 ground, session 16): per cell of an L3 window, what the water field did to the pre-ground.

Reads the census run (clamp_census OUT/gen.npz: ground, role, h_in, lift, gap_up/gap_dn, iso) and the dump
(ARGONIA_GROUND_DUMP OUT/dump.npz: vmin, vmax, foot, touch). Per cell: level, share of raw footprint, share wet in
the output, share of touch-bank vertices, share snapped by the gap (up/down), median lift and the carve
(h_in + lift - ground where no gap snapped), and median h_in - level and ground - level.
Usage: python3 -m tools.argonia_world.terrain.probes.marsh_cells OUT x0 y0 x1 y1"""
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain.cellwater import CY0, CX0, C, Q

OUT = Path(sys.argv[1])
x0, y0, x1, y1 = (int(v) for v in sys.argv[2:6])
g, d = np.load(OUT / "gen.npz"), np.load(OUT / "dump.npz")
gr, hin, lift, role = g["ground"], g["h_in"], g["lift"], g["role"]
gap = g["gap_up"] | g["gap_dn"]
vmin, vmax, foot, touch = d["vmin"], d["vmax"], d["foot"], d["touch"]
print("cell      lvl   drop foot% wet% touch% gapU% gapD% lift  carve hin-l  out-l")
for cy in range(y1, y0 - 1, -1):
    for cx in range(x0, x1 + 1):
        r, c = (C - 1 - (cy - CY0)) * Q, (cx - CX0) * Q
        s = (slice(r, r + Q + 1), slice(c, c + Q + 1))
        lv = vmin[s]
        if not np.isfinite(lv).any():
            continue
        L = float(np.nanmedian(lv))
        carve = np.where(gap[s], np.nan, hin[s] + lift[s] - gr[s])
        print(f"{cx:3d},{cy:3d} {L:6.2f} {float(np.nanmax(vmax[s] - vmin[s])):5.1f} {100 * foot[s].mean():5.0f}"
              f" {100 * (role[s] == 1).mean():4.0f} {100 * touch[s].mean():5.0f} {100 * g['gap_up'][s].mean():5.0f}"
              f" {100 * g['gap_dn'][s].mean():5.0f} {np.median(lift[s]):5.2f} {np.nanmedian(carve):5.2f}"
              f" {np.median(hin[s] - L):6.2f} {np.median(gr[s] - L):6.2f}")
