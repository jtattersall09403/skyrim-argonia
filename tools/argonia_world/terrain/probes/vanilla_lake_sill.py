"""Probe (1.15 ground, session 11): where a vanilla lake's level sits against its basin's outlet sill.

For the 15 largest inland levels carried by 4+ connected Tamriel cells (as vanilla_lake_padding.py), stitch the LAND of
the body's cells plus a PAD-cell ring, take the largest component of ground under the level as the lake, and flood
outward by minimax height (water filling the basin): the sill is the lowest height at which the flood reaches the
window's edge. Prints level - sill (metres; negative = the level stands below the lowest pass out) and the lake bed.
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_lake_sill [Skyrim.esm]  (reads only; prints)"""
import heapq
import sys

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.probes import vanilla_lake_padding as P

PAD = 3


def sill(g: np.ndarray, seed: np.ndarray) -> float:
    H, W = g.shape
    best = np.full(g.shape, np.inf)
    hq = []
    for i, j in zip(*np.nonzero(seed)):
        best[i, j] = g[i, j]
        hq.append((g[i, j], i, j))
    heapq.heapify(hq)
    while hq:
        v, i, j = heapq.heappop(hq)
        if v > best[i, j]:
            continue
        if i in (0, H - 1) or j in (0, W - 1):
            return float(v)
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if np.isfinite(g[a, b]):
                nv = max(v, g[a, b])
                if nv < best[a, b]:
                    best[a, b] = nv
                    heapq.heappush(hq, (nv, a, b))
    return float("nan")


def main():
    import struct
    from tools.argonia_world.terrain.esm import records
    from tools.argonia_world.terrain.probes.vanilla_lake_cells import TAMRIEL, vhgt
    import collections
    blob = P.ESM.read_bytes()
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
    m = su.UNITS_PER_METRE
    out = []
    for h, comp in bodies[:15]:
        xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
        x0, y0 = min(xs) - PAD, min(ys) - PAD
        nx, ny = max(xs) + PAD - x0 + 1, max(ys) + PAD - y0 + 1
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
        lab = P.components(under)
        sizes = np.bincount(lab.ravel())[1:]
        if not len(sizes):
            continue
        lake = lab == 1 + int(np.argmax(sizes))
        s = sill(g, lake)
        d = (h - s) / m
        out.append(d)
        print(f"level {h / m:8.1f} m cells {len(comp):3d}  bed {np.nanmin(g[lake]) / m:7.1f} m  sill {s / m:7.1f} m  "
              f"level - sill {d:+6.2f} m")
    a = np.array(out)
    print(f"level - sill over {len(a)}: median {np.median(a):+.2f} m, min {a.min():+.2f}, max {a.max():+.2f}; "
          f"within 1 m {(np.abs(a) <= 1).sum()}")


if __name__ == "__main__":
    main()
