"""Probe (0034, 1.15 ground): what a padding cell of a vanilla lake looks like, and whether a lake's outline is
the body's shape or the cell squares.

For the 15 largest inland levels carried by 4+ connected Tamriel cells, stitch the body's LAND onto one vertex grid
and measure: the components of ground under the level (4-connected across cell edges); the share of under-level
vertices in the largest; per padding cell (< 10 % wet) where its wet vertices are (touching the main component or
isolated) and how high its dry ground stands over the level; and the share of the outline lying on cell-edge lines
(about 2/32 for a raster shape, near 1 for cell squares).
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_lake_padding [Skyrim.esm]  (reads only; prints)"""
import collections
import struct
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.probes.vanilla_lake_cells import TAMRIEL, vhgt

ESM = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm")


def components(m: np.ndarray) -> np.ndarray:
    lab = np.zeros(m.shape, int)
    n = 0
    for s in zip(*np.nonzero(m)):
        if lab[s]:
            continue
        n += 1
        st = [s]
        lab[s] = n
        while st:
            i, j = st.pop()
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= a < m.shape[0] and 0 <= b < m.shape[1] and m[a, b] and not lab[a, b]:
                    lab[a, b] = n
                    st.append((a, b))
    return lab


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
    tot = collections.Counter()
    for h, comp in bodies[:15]:
        xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
        x0, y0 = min(xs), min(ys)
        W, H = (max(xs) - x0 + 1) * 32 + 1, (max(ys) - y0 + 1) * 32 + 1
        g = np.full((H, W), np.nan)  # row 0 south
        inb = np.zeros((H, W), bool)
        for (x, y) in comp:
            if (x, y) in land:
                r0, c0 = (y - y0) * 32, (x - x0) * 32
                g[r0:r0 + 33, c0:c0 + 33] = land[(x, y)]
                inb[r0:r0 + 33, c0:c0 + 33] = True
        under = inb & (g < h)
        lab = components(under)
        sizes = np.bincount(lab.ravel())[1:]
        main_ = 1 + int(np.argmax(sizes)) if len(sizes) else 0
        mainm = lab == main_
        # the outline: under-level vertices with a 4-neighbour inside the body above the level
        dry = inb & ~under
        edge = np.zeros_like(under)
        edge[1:] |= under[1:] & dry[:-1]; edge[:-1] |= under[:-1] & dry[1:]
        edge[:, 1:] |= under[:, 1:] & dry[:, :-1]; edge[:, :-1] |= under[:, :-1] & dry[:, 1:]
        ii, jj = np.nonzero(edge)
        on_line = float(((ii % 32 == 0) | (jj % 32 == 0)).mean()) if len(ii) else 0.0
        pad_cells = pad_main = pad_iso = 0
        free = []
        for (x, y) in comp:
            if (x, y) not in land:
                continue
            r0, c0 = (y - y0) * 32, (x - x0) * 32
            u = under[r0:r0 + 33, c0:c0 + 33]
            if u.mean() >= 0.1:
                continue
            pad_cells += 1
            pad_main += int((u & mainm[r0:r0 + 33, c0:c0 + 33]).sum())
            pad_iso += int((u & ~mainm[r0:r0 + 33, c0:c0 + 33]).sum())
            free.append(float((land[(x, y)][~u] - h).min()) if (~u).any() else 0.0)
        print(f"level {h:8.1f} cells {len(comp):3d}  under-level components {len(sizes):3d}, largest holds "
              f"{sizes.max() / max(under.sum(), 1):.2f} of {int(under.sum())}  outline on cell lines {on_line:.3f}  "
              f"padding cells {pad_cells}: wet vertices joined to the main body {pad_main}, isolated {pad_iso}; "
              f"their dry ground's lowest freeboard (u) {sorted(round(f) for f in free)[:8]}")
        tot.update(cells=len(comp), comps=len(sizes), under=int(under.sum()), main=int(sizes.max() if len(sizes) else 0),
                   pad=pad_cells, pad_main=pad_main, pad_iso=pad_iso, edge=len(ii),
                   online=int(round(on_line * len(ii))))
    print("top-15 totals", dict(tot), f"outline on cell lines {tot['online'] / max(tot['edge'], 1):.3f}")


if __name__ == "__main__":
    main()
