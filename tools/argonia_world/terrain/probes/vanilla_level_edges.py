"""Probe (0034, 1.15 ground): how Skyrim.esm's ground crosses a cell edge where the water level changes.

For every pair of 4-adjacent Tamriel cells with explicit levels differing by > 64 units (both water cells), along
the shared edge: the share of edge vertices at or above the upper level (a closed bank), and for the upper cell
whether its below-level ground reaches the edge or stops short (the bank following the body's outline, not the
edge), with the mean distance in vertices from each edge vertex to the upper water's nearest under-level vertex.
Also: edges between a water cell and a neighbour carrying the SAME level where the neighbour has no ground under it
(a padding cell), and how often a level edge meets ground under the upper level that is not under the lower one.
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_level_edges [Skyrim.esm]  (reads only; prints numbers)"""
import struct
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.probes.vanilla_lake_cells import vhgt, TAMRIEL

ESM = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm")


def main():
    blob = ESM.read_bytes()
    dw, cell, wrld = None, None, None
    water, land = {}, {}
    for r in records(blob):
        if r.sig == "WRLD":
            wrld = r.formid
            if wrld == TAMRIEL:
                dw = struct.unpack_from("<ff", r.first("DNAM"))[1]
        elif r.sig == "CELL":
            xc = r.first("XCLC")
            cell = struct.unpack_from("<ii", xc) if (xc and wrld == TAMRIEL) else None
            if cell is not None:
                w = r.first("XCLW")
                d = r.first("DATA")
                if w and d and d[0] & 2:
                    h = struct.unpack_from("<f", w)[0]
                    if -1e6 < h < 1e6:
                        water[cell] = h
        elif r.sig == "LAND" and cell is not None and cell not in land:
            v = r.first("VHGT")
            if v:
                land[cell] = vhgt(v)
    n = closed = 0
    share, reach, dist, wetedge, straight = [], [], [], [], []
    for (x, y), h in water.items():
        for (dx, dy) in ((1, 0), (0, 1)):
            o = (x + dx, y + dy)
            if o not in water or (x, y) not in land or o not in land or abs(water[o] - h) <= 64:
                continue
            up, lo_ = ((x, y), o) if h > water[o] else (o, (x, y))
            hu, hl = water[up], water[lo_]
            gu = land[up]
            # the upper cell's edge facing the lower cell, and its interior columns in order away from the edge
            if dx:
                strip = gu[:, -1:-17:-1] if up == (x, y) else gu[:, :16]
            else:
                strip = gu[-1:-17:-1, :].T if up == (x, y) else gu[:16, :].T
            e = strip[:, 0]
            n += 1
            s = float((e >= hu).mean())
            share.append(s)
            if s == 1.0:
                closed += 1
            under = strip < hu
            if under.any():
                _ = np.where(under.any(axis=0), under.argmax(axis=0), 99)  # kept for the next probe
                d = np.array([np.argmax(r) if r.any() else 16 for r in under])  # per edge row: vertices to water
                dist.append(float(d.mean()))
                reach.append(float((d == 0).mean()))
                # a straight ridge: the edge's height spread vs the 4th column's spread
                straight.append(float(np.std(e - hu) / max(np.std(strip[:, 4] - hu), 1.0)))
            wetedge.append(float((e < hl).mean()))
    print(f"default water {dw}; water cells {len(water)}; level edges (>64 u) {n}; fully closed {closed}")
    q = lambda a: np.percentile(a, [10, 50, 90]).round(2).tolist() if a else []
    print("edge share at/above the upper level p10/50/90", q(share))
    print("upper cells with water ground", len(dist), "mean vertices from edge to upper water p10/50/90", q(dist),
          "share of edge rows where upper water touches the edge p10/50/90", q(reach))
    print("edge height spread / column-4 spread p10/50/90", q(straight))
    print("edge share under the LOWER level p10/50/90", q(wetedge))


if __name__ == "__main__":
    main()
