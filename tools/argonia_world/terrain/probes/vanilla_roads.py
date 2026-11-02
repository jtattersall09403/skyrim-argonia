"""Probe (0034, 1.15-r4 roads): how Skyrim.esm (or Black Marsh.esm) builds a road, from the landscape it ships.

Dumps, for a box of exterior cells, every vertex's height and every LTEX layer's weight (BTXT base 1.0, ATXT/VTXT
alpha layers), the LTEX editor ids, and every placed reference with its base's signature and editor id, to an .npz
the analysis (vanilla_roads_measure.py) reads. Reads only; game data stays in the output path the caller gives
(keep it under $ARGONIA_PRIVATE or a scratch dir, never the repo).
Usage: python3 -m tools.argonia_world.terrain.probes.vanilla_roads ESM WRLD_HEX X0 X1 Y0 Y1 OUT.npz"""
import struct
import sys

import numpy as np

from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.probes.vanilla_lake_cells import vhgt

# quadrant origin in the 33x33 vertex grid (row 0 = south): 0 SW, 1 SE, 2 NW, 3 NE
QO = {0: (0, 0), 1: (0, 16), 2: (16, 0), 3: (16, 16)}


def main():
    esm, wrld_id = sys.argv[1], int(sys.argv[2], 16)
    x0, x1, y0, y1 = map(int, sys.argv[3:7])
    out = sys.argv[7]
    blob = open(esm, "rb").read()
    edid, sig = {}, {}
    wrld, cell = None, None
    heights, layers, refs = {}, {}, []
    for r in records(blob):
        e = r.first("EDID")
        if e:
            edid[r.formid] = e.rstrip(b"\0").decode("latin-1")
        sig[r.formid] = r.sig
        if r.sig == "WRLD":
            wrld = r.formid
        elif r.sig == "CELL":
            xc = r.first("XCLC")
            cell = None
            if xc and wrld == wrld_id:
                c = struct.unpack_from("<ii", xc)
                if x0 <= c[0] <= x1 and y0 <= c[1] <= y1:
                    cell = c
        elif cell is not None and r.sig == "LAND" and cell not in heights:
            v = r.first("VHGT")
            if v is None:
                continue
            heights[cell] = vhgt(v)
            lay = {}
            cur = None
            for s, b in r.subs:
                if s in ("BTXT", "ATXT"):
                    tex, quad = struct.unpack_from("<IB", b)
                    cur = (tex, quad)
                    if s == "BTXT":
                        a = lay.setdefault(tex, np.zeros((33, 33)))
                        r0, c0 = QO[quad]
                        a[r0:r0 + 17, c0:c0 + 17] = np.maximum(a[r0:r0 + 17, c0:c0 + 17], 1.0)
                elif s == "VTXT" and cur is not None:
                    tex, quad = cur
                    a = lay.setdefault(tex, np.zeros((33, 33)))
                    r0, c0 = QO[quad]
                    for k in range(len(b) // 8):
                        pos, _, op = struct.unpack_from("<HHf", b, k * 8)
                        a[r0 + pos // 17, c0 + pos % 17] = max(a[r0 + pos // 17, c0 + pos % 17], op)
            layers[cell] = lay
        elif cell is not None and r.sig in ("REFR",):
            n, d = r.first("NAME"), r.first("DATA")
            if n and d:
                base = struct.unpack_from("<I", n)[0]
                px, py, pz, ax, ay, az = struct.unpack_from("<6f", d)
                sc = r.first("XSCL")
                refs.append((base, px, py, pz, az, struct.unpack_from("<f", sc)[0] if sc else 1.0))
    texs = sorted({t for l in layers.values() for t in l})
    cells = sorted(heights)
    H = np.stack([heights[c] for c in cells])
    W = np.zeros((len(cells), len(texs), 33, 33), np.float32)
    for i, c in enumerate(cells):
        for t, a in layers[c].items():
            W[i, texs.index(t)] = a
    rb = [r[0] for r in refs]
    np.savez_compressed(out, cells=np.array(cells), H=H, W=W, tex=np.array(texs),
                        texname=np.array([edid.get(t, hex(t)) for t in texs]),
                        refs=np.array([r[1:] for r in refs]), refbase=np.array(rb),
                        refname=np.array([edid.get(b, hex(b)) for b in rb]),
                        refsig=np.array([sig.get(b, "?") for b in rb]))
    print(len(cells), "cells", len(texs), "ltex", len(refs), "refs")


if __name__ == "__main__":
    main()
