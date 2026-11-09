"""Does the built terrain give every place what it needs? One test per need, on the finished heightmap.

    python3 -m tools.newworld.terrain_needs [terrain dir]     # default out/newworld/terrain; writes needs.json there

Reads the build's places_terrain.json (every need the build shaped: table rows and kind fallbacks) and judges it on
heightmap.npy, land being ground over the water level:
- island: dry ground at the place, and that ground a true island: it does not reach the edge of a
  disc 3 radii + 100 m out (a peninsula fails);
- rise: the ground within half the radius stands RISE_M over the land in a ring 1.6 to 2.5 radii out;
- flat-pad: the land within the radius (less the bank, 2 samples from the water) has 90 % of its slopes under PAD_SLOPE_DEG (a place on water stands on stilts);
- shore-access: water within the radius + 20 m, and dry ground beside it no steeper than SHORE_SLOPE_DEG;
- seabed: water at the place, its bed SEABED_M or more under the surface;
- entrance-in-slope: the build's own entrance test (dry and open).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from tools.newworld import frame as f
from tools.newworld import terrain_shape as ts

RISE_M = 2.0
PAD_SLOPE_DEG = 10.0
SHORE_SLOPE_DEG = 15.0
SEABED_M = 3.0


def grid_of(b: dict) -> ts.Grid:
    p0x, p0y = f.world_to_px(b["origin_world_x"], b["origin_world_y"])
    return ts.Grid(rows=b["height"], cols=b["width"], p0x=p0x, p0y=p0y, ox=b["origin_world_x"], oy=b["origin_world_y"])


def judge(h, grid, rec, on_water=False, slope=None) -> tuple[bool, str]:
    nd, r = rec["need"], float(rec["radius_m"])
    i0, j0 = (float(v) for v in grid.ij(rec["px"], rec["py"]))
    reach = {"island": 3 * r + 100, "rise": 2.6 * r, "shore-access": r + 25}.get(nd, r + 5)
    sl, di, dj = ts._disc(grid, i0, j0, reach / grid.m)
    d = np.hypot(di, dj) * grid.m
    win = h[sl]
    land = win > ts.WATER_LEVEL
    sw = slope[sl] if slope is not None else ts.slope_deg(win)
    if nd == "island":
        lab, _ = ndi.label(land & (d <= reach))
        core = np.unique(lab[land & (d <= 5)])
        core = core[core > 0]
        if not len(core):
            return False, "no dry ground at the place"
        edge = (d > reach - 2 * grid.m) & (d <= reach)
        joined = np.isin(lab[edge], core).any()
        area = float(np.isin(lab, core).sum() * grid.m ** 2)
        return (not joined), f"islet {area:.0f} m2" + (", joined to the mainland" if joined else ", islanded")
    if nd == "rise":
        top = land & (d <= 0.5 * r)
        ring = land & (d >= 1.6 * r) & (d <= 2.5 * r)
        if not top.any() or not ring.any():
            return False, "no land at the top or round it"
        lift = (float(win[top].mean()) - float(win[ring].mean())) / ts.U
        return lift >= RISE_M, f"lift {lift:.1f} m"
    if nd == "flat-pad":
        if on_water:
            return True, "on water (stilts)"
        sel = land & (d <= r) & ~ndi.binary_dilation(~land, iterations=2)   # the bank into the water is no pad
        if not sel.any():
            return False, "no land in the footprint"
        p90 = float(np.percentile(sw[sel], 90))
        return p90 <= PAD_SLOPE_DEG, f"slope p90 {p90:.1f} deg"
    if nd == "shore-access":
        wat = ~land & (d <= r + 20)
        if not wat.any():
            return False, "no water within reach"
        bank = land & (d <= r + 20) & ndi.binary_dilation(~land, iterations=2)
        if not bank.any():
            return False, "no dry bank within reach"
        best = float(sw[bank].min())
        return best <= SHORE_SLOPE_DEG, f"gentlest bank {best:.1f} deg"
    if nd == "seabed":
        sel = d <= max(5.0, 0.3 * r)
        depth = -float(win[sel].min()) / ts.U
        return depth >= SEABED_M, f"depth {depth:.1f} m"
    if nd == "entrance-in-slope":
        ok = bool(rec.get("dry") and rec.get("open"))
        return ok, "entrance " + ("open" if ok else "bad")
    return True, "no test"


def measure(out_dir: Path) -> dict:
    from tools.argonia_world import db
    w = db.open("newworld")
    on_water = {p.id: bool(p.on_water) for p in w.rows("place")}
    b = json.loads((out_dir / "build.json").read_text())
    grid = grid_of(b)
    h = np.load(out_dir / "heightmap.npy")
    slope = ts.slope_deg(h)
    recs = json.loads((out_dir / "places_terrain.json").read_text())
    rows, fails = [], {}
    for rec in recs:
        ok, why = judge(h, grid, rec, on_water.get(rec["place_id"], False), slope)
        rows.append({"place_id": rec["place_id"], "need": rec["need"], "ok": ok, "why": why})
        if not ok:
            fails[rec["need"]] = fails.get(rec["need"], 0) + 1
    res = {"build": b["id"], "needs": len(rows), "failures": sum(fails.values()), "by_need": fails, "rows": rows}
    (out_dir / "needs.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = measure(Path(sys.argv[1]) if len(sys.argv) > 1 else f.OUT / "terrain")
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}))
    for row in r["rows"]:
        if not row["ok"]:
            print("FAIL", row["need"], row["place_id"], row["why"])
    sys.exit(0 if r["failures"] == 0 else 1)
