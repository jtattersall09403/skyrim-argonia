"""Probe (0034, 1.15 ground, audit §1): how vanilla's ground rises from a lake over the first 20 vertices.

For the 15 largest inland levels carried by 4+ connected Tamriel cells, stitch the body's cells and two cells around
them onto one vertex grid; the water is the under-level ground joined to the largest under-level component; for every
dry vertex within 20 vertices of it, the height over the level (m) by distance (vertices, chamfer). Prints the
percentiles per distance and the share standing within 1 m of the level (a plate), split by whether the vertex lies in
a water cell or in the cells around (a freeboard plate would show as a flat band inside the water cells only).
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_shore_profile [Skyrim.esm]  (reads only; prints)"""
import collections
import struct
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world.skyrim_units import UNITS_PER_METRE
from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.generate import chamfer
from tools.argonia_world.terrain.probes.vanilla_lake_cells import TAMRIEL, vhgt
from tools.argonia_world.terrain.probes.vanilla_lake_padding import components

ESM = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm")
D = 20


def main():
    blob = ESM.read_bytes()
    default_water, cell, wrld = None, None, None
    water, land, flags = {}, {}, {}
    for r in records(blob):
        if r.sig == "WRLD":
            wrld = r.formid
            if wrld == TAMRIEL:
                default_water = struct.unpack_from("<ff", r.first("DNAM"))[1]
        elif r.sig == "CELL":
            xc = r.first("XCLC")
            cell = struct.unpack_from("<ii", xc) if (xc and wrld == TAMRIEL) else None
            if cell is not None:
                data = r.first("DATA")
                flags[cell] = data[0] if data else 0
                w = r.first("XCLW")
                water[cell] = struct.unpack_from("<f", w)[0] if w else default_water
        elif r.sig == "LAND" and cell is not None and cell not in land:
            v = r.first("VHGT")
            if v:
                land[cell] = vhgt(v)
    by = collections.defaultdict(set)
    for c, h in water.items():
        if h is not None and -1e6 < h < 1e6 and h > default_water + 1 and flags.get(c, 0) & 2:
            by[round(h, 1)].add(c)
    bodies = []
    for h, cells in by.items():
        left = set(cells)
        while left:
            seed = left.pop(); comp = {seed}; st = [seed]
            while st:
                x, y = st.pop()
                for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if n in left:
                        left.remove(n); comp.add(n); st.append(n)
            if len(comp) >= 4:
                bodies.append((h, comp))
    bodies.sort(key=lambda b: -len(b[1]))
    rise = {k: collections.defaultdict(list) for k in ("in", "out")}
    for h, comp in bodies[:15]:
        xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
        x0, y0 = min(xs) - 2, min(ys) - 2
        nx, ny = max(xs) - x0 + 3, max(ys) - y0 + 3
        g = np.full((ny * 32 + 1, nx * 32 + 1), np.nan)
        inb = np.zeros(g.shape, bool)
        for x in range(x0, x0 + nx):
            for y in range(y0, y0 + ny):
                if (x, y) in land:
                    r0, c0 = (y - y0) * 32, (x - x0) * 32
                    g[r0:r0 + 33, c0:c0 + 33] = land[(x, y)]
                    if (x, y) in comp:
                        inb[r0:r0 + 33, c0:c0 + 33] = True
        under = inb & (g < h)
        if not under.any():
            continue
        lab = components(under)
        wet = lab == 1 + int(np.argmax(np.bincount(lab.ravel())[1:]))
        d, _ = chamfer(wet, D + 1)
        ok = ~wet & np.isfinite(g) & np.isfinite(d)
        for k, m in (("in", ok & inb), ("out", ok & ~inb)):
            for dist, z in zip(np.ceil(d[m] - 1e-9).astype(int), (g[m] - h) / UNITS_PER_METRE):
                rise[k][int(dist)].append(z)
    for k in ("in", "out"):
        print(f"dry vertices {'inside the water cells' if k == 'in' else 'in the cells around'}: rise over the level (m)")
        print(" d      n    p10    p50    p90  <1m share")
        for dist in range(1, D + 1):
            z = np.array(rise[k][dist])
            if len(z):
                p = np.percentile(z, [10, 50, 90])
                print(f"{dist:2d} {len(z):6d} {p[0]:6.2f} {p[1]:6.2f} {p[2]:6.2f}   {(z < 1).mean():.2f}")


if __name__ == "__main__":
    main()
