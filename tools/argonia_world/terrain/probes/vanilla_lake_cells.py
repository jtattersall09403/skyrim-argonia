"""Probe (0034, 1.15 ground): how Skyrim.esm gives a multi-cell lake or marsh its water, cell by cell.

For each inland water level carried by 4+ connected Tamriel cells (XCLW), count per cell the share of LAND vertices
under the level, the cells with the level whose ground is all above it, and the "holes": cells beside or enclosed by
the body that hold vertices under its level but carry another level (or none).
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_lake_cells [Skyrim.esm]  (reads only; prints numbers)"""
import collections
import struct
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain.esm import records

ESM = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm")
TAMRIEL = 0x3C


def vhgt(b: bytes) -> np.ndarray:
    off = struct.unpack_from("<f", b, 0)[0]
    d = np.frombuffer(b, np.int8, 33 * 33, 4).reshape(33, 33).astype(np.float64)
    return (off + _acc(d)) * 8.0


def _acc(d):
    col = np.cumsum(d[:, 0])                      # each row's start accumulates down the first column
    return col[:, None] + np.cumsum(np.c_[np.zeros(33), d[:, 1:]], axis=1)


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
    print(f"Tamriel default water {default_water}; cells {len(water)}; LAND {len(land)}")
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
        fr = {c: float((land[c] < h).mean()) for c in comp if c in land}
        dry = sum(1 for f in fr.values() if f == 0)
        low = sum(1 for f in fr.values() if 0 < f < 0.1)
        ring = {(x + dx, y + dy) for x, y in comp for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - comp
        holes = [c for c in ring if c in land and (land[c] < h - 1).any()]
        walls = 0  # body-cell edge vertices under the level on an edge shared with a cell carrying a lower level
        for (x, y) in comp:
            if (x, y) not in land:
                continue
            g = land[(x, y)]  # rows run south to north, columns west to east
            for (dx, dy), edge in (((1, 0), g[:, -1]), ((-1, 0), g[:, 0]), ((0, 1), g[-1, :]), ((0, -1), g[0, :])):
                n = (x + dx, y + dy)
                if n not in comp and (water.get(n) is None or not -1e6 < water[n] < h - 1 or not flags.get(n, 0) & 2):
                    walls += int((edge < h - 1).sum())
        xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
        enclosed = [(x, y) for x in range(min(xs), max(xs) + 1) for y in range(min(ys), max(ys) + 1)
                    if (x, y) not in comp and all(any((x + k * dx, y + k * dy) in comp for k in range(1, 30))
                                                  for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        enc_wet = [c for c in enclosed if c in land and (land[c] < h).any()]
        print(f"level {h:8.1f}  cells {len(comp):3d}  x {min(xs)}..{max(xs)} y {min(ys)}..{max(ys)}  "
              f"wet-share min {min(fr.values()):.3f} median {np.median(list(fr.values())):.2f}  "
              f"all-dry cells {dry}  <10% wet {low}  ring cells with ground >1u under level {len(holes)} "
              f"(their levels {sorted({round(water.get(c) or 0) for c in holes if -1e6 < (water.get(c) or 0) < 1e6})[:6]})  "
              f"enclosed non-body cells {len(enclosed)} (wet {len(enc_wet)})  edge vertices under the level facing a lower/no level {walls}")
        tot.update(walls=walls, cells=len(comp), dry=dry, low=low, holes=len(holes), enc=len(enclosed), encwet=len(enc_wet))
    print("top-15 totals", dict(tot))


if __name__ == "__main__":
    main()
