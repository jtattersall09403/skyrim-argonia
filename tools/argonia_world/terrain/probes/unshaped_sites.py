"""Probe (1.15 ground): each unshaped entrance site with its shape, role, centre height, rim-plane relief, core
std and water levels. Usage: python3 -m tools.argonia_world.terrain.probes.unshaped_sites"""
import json
import os

import numpy as np

from tools.argonia_world import db
from tools.argonia_world.terrain import cellwater, generate as G

g = np.load(os.environ.get("ARGONIA_GROUND", "out/terrain") + "/ground-f32.npy").astype(np.float64)
role = np.load(os.environ.get("ARGONIA_GROUND", "out/terrain") + "/role-u8.npy")
sites = json.load(open(os.environ.get("ARGONIA_GROUND", "out/terrain") + "/entrance-sites.json"))
w = cellwater.load(db.open())
res = G.check(g, role, w, sites)
vmin, vmax = G.vertex_levels(w.level)
bad = set(res["sites_unshaped_ids"])
for s in sites:
    if s["place_id"] not in bad:
        continue
    ci, cj = int(round(s["y_m"] / G.MPP)), int(round(s["x_m"] / G.MPP))
    r = int(s["radius_m"] / G.MPP)
    win = g[ci - r:ci + r + 1, cj - r:cj + r + 1]
    yy, xx = np.mgrid[ci - r:ci + r + 1, cj - r:cj + r + 1]
    core = win[np.hypot(yy - ci, xx - cj) <= 0.4 * r]
    ro = role[ci - r:ci + r + 1, cj - r:cj + r + 1]
    print(s["place_id"], s["shape"], "r", r, "role", int(role[ci, cj]), "c", round(g[ci, cj], 2), "std", round(core.std(), 2),
          "min/max", round(core.min(), 1), round(core.max(), 1), "lv", vmin[ci, cj], vmax[ci, cj],
          "roles", np.bincount(ro.ravel(), minlength=5).tolist(), s["request"])
