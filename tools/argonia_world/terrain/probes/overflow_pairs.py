"""Probe (1.15 ground, session 17): every 4-neighbour step over the VHGT byte (127 x 8 units) in a ground, with
what each end was made to be. Reads GROUND (ground-f32.npy) and, beside it or in CENSUS/gen.npz, role/lo/hi; with
DUMP (ARGONIA_GROUND_DUMP npz) also vmin/vmax/foot. Per pair: cell, both ends' (h, role, lo, hi, vmin, foot).
Usage: python3 -m tools.argonia_world.terrain.probes.overflow_pairs GROUND [CENSUS_DIR]"""
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, Q

LIM = su.VHGT_DELTA_MAX * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE


def main():
    g = np.load(sys.argv[1], mmap_mode="r")
    cen = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    z = np.load(cen / "gen.npz") if cen and (cen / "gen.npz").exists() else None
    d = np.load(cen / "dump.npz") if cen and (cen / "dump.npz").exists() else None
    role = np.load(Path(sys.argv[1]).with_name("role-u8.npy"), mmap_mode="r")
    g = np.asarray(g, np.float64)
    hits = []
    for ax in (0, 1):
        s = np.abs(np.diff(g, axis=ax)) > LIM
        for r, c in zip(*np.nonzero(s)):
            hits.append(((r, c), (r + 1, c) if ax == 0 else (r, c + 1)))
    print(f"{len(hits)} pairs over {LIM:.2f} m")
    for a, b in hits:
        cx, cy = CX0 + min(a[1], C * Q - 1) // Q, CY0 + C - 1 - min(a[0], C * Q - 1) // Q
        def f(p):
            out = f"h {g[p]:7.1f} r{role[p]}"
            if z is not None:
                out += f" lo {z['lo'][p]:7.1f} hi {z['hi'][p]:7.1f} in {z['h_in'][p]:7.1f}"
            if d is not None:
                out += f" vmin {d['vmin'][p]:6.1f} vmax {d['vmax'][p]:6.1f} f{int(d['foot'][p])} t{int(d['touch'][p])}"
            return out
        print(f"({cx},{cy}) {a}->{b}: {f(a)} | {f(b)}")


if __name__ == "__main__":
    main()
