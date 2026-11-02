"""Probe (1.15 ground, session 10): the water as smooth fields (water_field.py) against the clamp generator, on the
L3 windows, from the pre-water dump (generate with ARGONIA_GROUND_DUMP) and the clamp run (clamp_census gen.npz).
Writes OUT/<old|new>-<window>.png (hillshade, water blue where the ground lies under its cell's water) and prints,
per window, the share of vertices on a bound, the shore share on cell lines, max 4-neighbour step and p99 slope.
Usage: python3 -m tools.argonia_world.terrain.probes.water_field_trial [OUT]"""
import math
import sys
import time
from pathlib import Path

import numpy as np

from tools.argonia_world.terrain import generate as G
from tools.argonia_world.terrain import png
from tools.argonia_world.terrain.cellwater import Q
from tools.argonia_world.terrain.probes.clamp_census import window
from tools.argonia_world.terrain.render import hillshade, widen
from tools.argonia_world.terrain.water_field import water_field
from tools.argonia_world.terrain.world import SAMPLE_1_15

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out/terrain-sample/census")
WINS = [widen(w) for w in SAMPLE_1_15 if w != (-63, -63, -62, -62)]


def image(g, vmin, wet):
    s = hillshade(g)
    rgb = np.stack([s * 200 + 30] * 3, -1)
    rgb = np.where(wet[..., None], rgb * 0.45 + np.array([20, 50, 110.0]) * 0.55, rgb)
    return np.repeat(np.repeat(np.clip(rgb, 0, 255).astype(np.uint8), 2, 0), 2, 1)


def stats(g, lo, hi, wet):
    on = (np.isfinite(lo) & (np.abs(g - lo) < 0.05)) | (np.isfinite(hi) & (np.abs(g - hi) < 0.05) & ~wet)
    e = np.zeros_like(wet)
    e[1:] |= wet[1:] & ~wet[:-1]; e[:-1] |= wet[:-1] & ~wet[1:]
    e[:, 1:] |= wet[:, 1:] & ~wet[:, :-1]; e[:, :-1] |= wet[:, :-1] & ~wet[:, 1:]
    ii, jj = np.indices(g.shape)
    line = (ii % Q == 0) | (jj % Q == 0)  # windows start on cell lines
    gy, gx = np.gradient(g, G.MPP)
    return {"dry_on_bound_%": round(100 * (on & ~wet).sum() / g.size, 1),
            "shore_on_line_%": round(100 * (e & line).sum() / max(e.sum(), 1), 1),
            "max_step_m": round(float(max(np.abs(np.diff(g, axis=0)).max(), np.abs(np.diff(g, axis=1)).max())), 1),
            "p99_slope_deg": round(float(np.percentile(np.degrees(np.arctan(np.hypot(gx, gy))), 99)), 1)}


def main():
    t0 = time.time()
    p = np.load(OUT / "pre.npz")
    old = np.load(OUT / "gen.npz")
    vmin, vmax = p["vmin"].astype(np.float64), p["vmax"].astype(np.float64)
    h2, role, lo, hi, dg = water_field(p["h"].astype(np.float64), p["foot"], vmin, vmax, p["touch"], p["chz"], p["tsamp"])
    print(f"field {time.time() - t0:.1f}s; lift>0 {int((dg['lift'] > 0.05).sum())} carve>0 {int((dg['carve'] > 0.05).sum())}")
    f, moved = G.limit(h2, lo, hi, G.LIP)
    print(f"limit {time.time() - t0:.1f}s moved {int(moved.sum())}")
    has = np.isfinite(vmin)
    for w in WINS:
        sl = window(*w)
        tag = "_".join(map(str, w[:2]))
        go, ro = old["ground"][sl].astype(np.float64), old["role"][sl]
        wo = (ro == 1) | (ro == 2)
        wn = has[sl] & (f[sl] < vmin[sl])
        png.write(OUT / f"old-{tag}.png", image(go, vmin[sl], wo))
        png.write(OUT / f"new-{tag}.png", image(f[sl], vmin[sl], wn))
        print(w, "old", stats(go, old["lo"][sl].astype(float), old["hi"][sl].astype(float), wo))
        print(w, "new", stats(f[sl], lo[sl], hi[sl], wn), "bank<=water", int((has[sl] & ~wn & (f[sl] <= vmax[sl])).sum()))
    np.save(OUT / "field-ground.npy", f.astype(np.float32))


if __name__ == "__main__":
    main()
