"""Probe (1.15 ground, session 10): which per-cell clamp holds the final ground, per L3 window.

Runs generate() in memory (writes nothing shared), saves ground/lo/hi/role/diag to OUT/gen.npz (reused when present),
then per window prints the share of vertices whose final height lies on a bound (|f - bound| < 0.05 m) by the rule
that set it, the share on a cone of a bound (the limit carried a clamp outward), and the share of shore vertices
(wet with a dry 4-neighbour) lying on a cell line (a raster shape gives 2/Q).
Usage: python3 -m tools.argonia_world.terrain.probes.clamp_census [OUT]"""
import math
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain import generate as G
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, Q
from tools.argonia_world.terrain.render import widen
from tools.argonia_world.terrain.world import SAMPLE_1_15

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out/terrain-sample/census")
KEYS = ("edge_bank", "spread", "sbank", "ct", "chan", "pad")


def load():
    f = OUT / "gen.npz"
    if f.exists():
        z = np.load(f)
        return {k: z[k] for k in z.files}
    from tools.argonia_world import db
    r = G.generate(G.Inputs.load(db.open()))
    d = {"ground": r["ground"], "lo": r["lo"].astype(np.float32), "hi": r["hi"].astype(np.float32), "role": r["role"]}
    d.update({k: r["diag"][k] for k in KEYS})
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(f, **d)
    return d


def window(x0, y0, x1, y1):
    r0, r1 = (C - 1 - (y1 - CY0)) * Q, (C - 1 - (y0 - CY0)) * Q + Q
    c0, c1 = (x0 - CX0) * Q, (x1 - CX0) * Q + Q
    return slice(r0, r1 + 1), slice(c0, c1 + 1)


def census(d, sl):
    g = d["ground"][sl].astype(np.float64)
    lo, hi, role = d["lo"][sl].astype(np.float64), d["hi"][sl].astype(np.float64), d["role"][sl]
    lip = math.tan(math.radians(G.DESIGN_SLOPE_DEG)) * G.MPP
    on_lo = np.isfinite(lo) & (np.abs(g - lo) < 0.05)
    on_hi = np.isfinite(hi) & (np.abs(g - hi) < 0.05)
    a = G.majorant(np.where(np.isfinite(lo), lo, -1e9), lip)
    b = G.minorant(np.where(np.isfinite(hi), hi, 1e9), lip)
    cone = ~on_lo & ~on_hi & ((np.abs(g - a) < 0.05) | (np.abs(g - b) < 0.05))
    m = {k: d[k][sl] for k in KEYS}
    n = g.size
    cls = {
        "step bank (sbank)": on_lo & m["sbank"],
        "two-level spread": on_lo & m["spread"] & ~m["sbank"],
        "edge bank": on_lo & m["edge_bank"] & ~m["spread"] & ~m["sbank"],
        "pad cell bank": on_lo & m["pad"] & (role == 3) & ~m["edge_bank"] & ~m["spread"] & ~m["sbank"],
        "bank floor (role 3)": on_lo & (role == 3) & ~m["pad"] & ~m["edge_bank"] & ~m["spread"] & ~m["sbank"],
        "shore floor (role 4)": on_lo & (role == 4),
        "channel": (on_lo | on_hi) & m["chan"],
        "bed ceiling (hi, wet)": on_hi & ~m["chan"],
        "other lo (site)": on_lo & (role == 0),
        "cone of a bound (limit)": cone,
    }
    out = {k: round(100 * v.sum() / n, 1) for k, v in cls.items()}
    out["free"] = round(100 - sum(out.values()), 1)
    wet = (role == 1) | (role == 2)
    edge = np.zeros_like(wet)
    edge[1:] |= wet[1:] & ~wet[:-1]
    edge[:-1] |= wet[:-1] & ~wet[1:]
    edge[:, 1:] |= wet[:, 1:] & ~wet[:, :-1]
    edge[:, :-1] |= wet[:, :-1] & ~wet[:, 1:]
    ii, jj = np.mgrid[sl]
    online = (ii % Q == 0) | (jj % Q == 0)
    out["shore_on_cell_line_%"] = round(100 * (edge & online).sum() / max(edge.sum(), 1), 1)
    out["raster_expect_%"] = round(100 * (2 * Q - 1) / Q / Q, 1)
    return out


if __name__ == "__main__":
    d = load()
    for w in SAMPLE_1_15:
        if w == (-63, -63, -62, -62):
            continue
        print(widen(w), census(d, window(*widen(w))))
