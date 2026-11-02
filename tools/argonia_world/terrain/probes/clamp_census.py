"""Probe (1.15 ground, session 14): which water-field rule set each flat ("plate") vertex, per L3 window.

Runs generate() in memory (writes nothing shared), saves ground/lo/hi/role and the field's diag to OUT/gen.npz (reused
when present). A plate vertex is dry (role != 1) with max |height step| to its 8 neighbours under 0.02 m. Per window:
the share of the window that is plate, split by the rule that set it (gap snapped up/down, the iso hollow lift, the
edge lift, a lo/hi bound, free), the share of all window vertices each rule moved by more than 0.05 m, and the share
of shore vertices lying on a cell line (a raster shape gives about 2/Q).
Usage: python3 -m tools.argonia_world.terrain.probes.clamp_census [OUT]"""
import sys
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain import generate as G
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, Q
from tools.argonia_world.terrain.render import widen
from tools.argonia_world.terrain.world import SAMPLE_1_15

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out/terrain-sample/census")
KEYS = ("gap_up", "gap_dn", "iso", "lift", "src", "h_in", "chan", "h_sites_in", "h_lim_in")


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
    m = {k: d[k][sl] for k in KEYS}
    p = np.pad(g, 1, mode="edge")
    step = np.max([np.abs(p[1 + a:1 + a + g.shape[0], 1 + b:1 + b + g.shape[1]] - g)
                   for a in (-1, 0, 1) for b in (-1, 0, 1)], axis=0)
    plate = (step < 0.02) & (role != 1)
    on_lo = np.isfinite(lo) & (np.abs(g - lo) < 0.05)
    on_hi = np.isfinite(hi) & (np.abs(g - hi) < 0.05)
    lifted = m["lift"] > 0.05
    cls = {"gap up": m["gap_up"], "gap down": m["gap_dn"], "iso hollow": m["iso"] & ~m["gap_up"],
           "edge lift": lifted & ~m["iso"] & ~m["gap_up"] & ~m["gap_dn"], "on lo": on_lo, "on hi": on_hi}
    n = g.size
    out = {"plate_%": round(100 * plate.sum() / n, 1)}
    taken = np.zeros_like(plate)
    for k, v in cls.items():
        out["plate:" + k] = round(100 * (plate & v & ~taken).sum() / n, 1)
        taken |= v
    out["plate:free"] = round(100 * (plate & ~taken).sum() / n, 1)
    out["prior_plate_%"] = round(100 * (plate & (np.abs(g - m["h_in"]) < 0.05)).sum() / n, 1)
    mv = np.abs(g - m["h_in"]) > 0.05
    for k in ("gap_up", "gap_dn", "iso"):
        out["moved:" + k] = round(100 * (m[k] & mv).sum() / n, 1)
    out["moved:lift"] = round(100 * lifted.sum() / n, 1)
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
