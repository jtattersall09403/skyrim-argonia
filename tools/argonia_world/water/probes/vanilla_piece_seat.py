"""Probe (0034, lane 1.15-r6-water-steps): how Skyrim.esm seats its step pieces' OBND against the two waters of a
stepped Tamriel cell edge: per FX base its OBND, and per ref near a step its scaled OBND top and bottom against the
upper and lower water (units). Feeds steps.py's seat rule. Reads only; prints numbers.
Usage: python3 -m tools.argonia_world.water.probes.vanilla_piece_seat [Skyrim.esm]"""
import collections
import struct
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.esm import records
from tools.argonia_world.terrain.probes.vanilla_lake_cells import TAMRIEL

FX = {"FXrapidsFallsLine01", "FxRapidsRingHeavy", "FXWaterfallSkirtSlope", "FXWaterfallMistBlast"}


def main(path: str) -> None:
    blob = Path(path).read_bytes()
    base, obnd, water, refs, wrld, cell = {}, {}, {}, [], None, None
    for r in records(blob):
        if r.sig in ("ACTI", "STAT", "MSTT"):
            e = (r.first("EDID") or b"").rstrip(b"\0").decode()
            if e in FX:
                base[r.formid] = e
                ob = r.first("OBND")
                obnd[e] = struct.unpack("<6h", ob) if ob else None
        elif r.sig == "WRLD":
            wrld = r.formid
        elif r.sig == "CELL":
            xc = r.first("XCLC")
            cell = struct.unpack_from("<ii", xc) if (xc and wrld == TAMRIEL) else None
            if cell:
                wl, d = r.first("XCLW"), r.first("DATA")
                if wl and d and d[0] & 2:
                    h = struct.unpack_from("<f", wl)[0]
                    if -1e6 < h < 1e6:
                        water[cell] = h
        elif r.sig == "REFR" and wrld == TAMRIEL:
            n = struct.unpack("<I", r.first("NAME"))[0]
            if n in base:
                sc = r.first("XSCL")
                refs.append((base[n], struct.unpack_from("<6f", r.first("DATA")), struct.unpack("<f", sc)[0] if sc else 1.0))
    print("obnd (x0,y0,z0,x1,y1,z1):", obnd)
    steps = []
    for (x, y), h in water.items():
        for o in ((x + 1, y), (x, y + 1)):
            if o in water and abs(water[o] - h) > 64:
                hi, lo = ((x, y), o) if h > water[o] else (o, (x, y))
                ex = max(hi[0], lo[0]) * su.CELL_UNITS if hi[0] != lo[0] else hi[0] * su.CELL_UNITS + su.CELL_UNITS // 2
                ey = max(hi[1], lo[1]) * su.CELL_UNITS if hi[1] != lo[1] else hi[1] * su.CELL_UNITS + su.CELL_UNITS // 2
                steps.append((ex, ey, water[hi], water[lo]))
    st = np.array(steps)
    out = collections.defaultdict(list)
    for e, (px, py, pz, *_), sc in refs:
        d = np.hypot(st[:, 0] - px, st[:, 1] - py)
        i = int(np.argmin(d))
        if d[i] > 3000 or obnd[e] is None:
            continue
        up, lo = st[i, 2], st[i, 3]
        z0, z1 = obnd[e][2] * sc, obnd[e][5] * sc
        out[e].append((pz + z1 - up, pz + z0 - up, pz + z1 - lo, pz + z0 - lo, up - lo))
    for e, v in sorted(out.items()):
        a = np.array(v)
        q = lambda c: np.percentile(a[:, c], [10, 50, 90]).round(0).tolist()
        print(f"{e} n={len(v)} top-upper {q(0)} bottom-upper {q(1)} top-lower {q(2)} bottom-lower {q(3)} "
              f"bottom<=lower {int((a[:, 3] <= 0).sum())} top<=upper+64 {int((a[:, 0] <= 64).sum())}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/games/skyrimse/Data/Skyrim.esm")
