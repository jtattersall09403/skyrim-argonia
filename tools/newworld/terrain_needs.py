"""Does the built terrain give every place what it needs? One test per need, on the finished heightmap.

    python3 -m tools.newworld.terrain_needs [terrain dir]     # default out/newworld/terrain; writes needs.json there

Exit 1 on a failure that newworld/sources/terrain_needs_accepted.json does not name (place, need, and why the
failure stands). A failure is mended in the terrain or the place's record; it is accepted only when the map itself
gives the place no such ground, and the row says so.

Reads the build's places_terrain.json (every need the build shaped: table rows and kind fallbacks) and judges it on
heightmap.npy, land being ground over the water level. The bank is the bank: land within BANK_BAND_M of the water
follows the shore's walked profile (terrain_clearance), and a place's level ground begins behind it, as at Skyrim's
waterside towns and forts. Each need is judged on the ground it is about:
- island: dry ground at the place, and that ground a true island: it does not reach the edge of a
  disc 3 radii + 100 m out (a peninsula fails);
- rise: the ground within half the radius, behind the bank, stands RISE_M over the land in a ring 1.6 to 2.5 radii
  out; a top with under MIN_BEHIND of its land behind the bank fails (no room behind the bank);
- flat-pad: the land within the radius, behind the bank, has 90 % of its slopes under PAD_SLOPE_DEG; a pad with
  under MIN_BEHIND of its land behind the bank fails (no room behind the bank); a place on water stands on stilts;
- shore-access: water within the radius + 20 m, and the bank beside it no steeper than SHORE_SLOPE_DEG at its
  gentlest, read on the band's row at the waterline (the band's crest reads the lip of the ground behind it, which
  is no landing);
- seabed: water at the place, its bed SEABED_M or more under the surface;
- entrance-in-slope: the build's own entrance test (dry and open).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from tools.newworld import frame as f
from tools.newworld import terrain_shape as ts
from tools.newworld.terrain_clearance import BANK_BAND_M    # the reach the terrain eases a place's ground over

RISE_M = 2.0
PAD_SLOPE_DEG = 10.0
SHORE_SLOPE_DEG = 15.0
SEABED_M = 3.0
MIN_BEHIND = 0.25           # the least share of a pad's or a top's land that must lie behind the bank


def behind_bank(land: np.ndarray, area: np.ndarray, m: float) -> tuple[np.ndarray, np.ndarray, float]:
    """(the bank band, `area` behind it, the share of `area` behind it). The band is the land within BANK_BAND_M of
    the waterline (half a sample out from the nearest water sample); `m`: metres a sample."""
    band = land & (ndi.distance_transform_edt(land) * m - m / 2 <= BANK_BAND_M)
    behind = area & ~band
    return band, behind, float(behind.sum()) / max(1, int(area.sum()))


def slope_behind(win: np.ndarray, band: np.ndarray, behind: np.ndarray) -> np.ndarray:
    """Slope (degrees) of every sample of `win` with the bank band read as the level of the nearest ground behind
    it: the bank beside a pad never reads as the pad's own slope. `behind`: the land that is not band."""
    if not band.any() or not behind.any():
        return ts.slope_deg(win)
    ii = ndi.distance_transform_edt(~behind, return_distances=False, return_indices=True)
    return ts.slope_deg(np.where(band, win[ii[0], ii[1]], win))


def grid_of(b: dict) -> ts.Grid:
    p0x, p0y = f.world_to_px(b["origin_world_x"], b["origin_world_y"])
    return ts.Grid(rows=b["height"], cols=b["width"], p0x=p0x, p0y=p0y, ox=b["origin_world_x"], oy=b["origin_world_y"])


def judge(h, grid, rec, on_water=False, slope=None) -> tuple[bool, str]:
    nd, r = rec["need"], float(rec["radius_m"])
    i0, j0 = (float(v) for v in grid.ij(rec["px"], rec["py"]))
    reach = {"island": 3 * r + 100, "rise": 2.6 * r, "shore-access": r + 25}.get(nd, r + 5) + BANK_BAND_M
    sl, di, dj = ts._disc(grid, i0, j0, reach / grid.m)
    d = np.hypot(di, dj) * grid.m
    win = h[sl]
    land = win > ts.WATER_LEVEL
    sw = slope[sl] if slope is not None else ts.slope_deg(win)
    if nd == "island":
        reach -= BANK_BAND_M
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
        whole = land & (d <= 0.5 * r)
        ring = land & (d >= 1.6 * r) & (d <= 2.5 * r)
        if not whole.any() or not ring.any():
            return False, "no land at the top or round it"
        _band, top, share = behind_bank(land, whole, grid.m)
        if share < MIN_BEHIND:
            return False, f"no room behind the bank ({share:.0%} of the top)"
        lift = (float(win[top].mean()) - float(win[ring].mean())) / ts.U
        return lift >= RISE_M, f"lift {lift:.1f} m"
    if nd == "flat-pad":
        if on_water:
            return True, "on water (stilts)"
        whole = land & (d <= r)
        if not whole.any():
            return False, "no land in the footprint"
        band, sel, share = behind_bank(land, whole, grid.m)
        if share < MIN_BEHIND:
            return False, f"no room behind the bank ({share:.0%} of the pad)"
        p90 = float(np.percentile(slope_behind(win, band, land & ~band)[sel], 90))
        return p90 <= PAD_SLOPE_DEG, f"slope p90 {p90:.1f} deg"
    if nd == "shore-access":
        wat = ~land & (d <= r + 20)
        if not wat.any():
            return False, "no water within reach"
        bank = behind_bank(land, land, grid.m)[0] & (d <= r + 20) & ndi.binary_dilation(~land, np.ones((3, 3), bool))
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


ACCEPTED = f.ROOT / "sources" / "terrain_needs_accepted.json"


NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
# which way each reason's measure is worse: +1 a larger value, -1 a smaller one
WORSE = {"slope p90 # deg": 1, "gentlest bank # deg": 1, "lift # m": -1, "depth # m": -1,
         "no room behind the bank (#% of the pad)": -1, "no room behind the bank (#% of the top)": -1}


def reason(why: str) -> tuple[str, float | None]:
    """A failure's reason as its class (the judge's words, each number as #) and its first measure."""
    m = NUMBER.search(why)
    return NUMBER.sub("#", why), (float(m.group()) if m else None)


def stands(row: dict, a: dict | None) -> bool:
    """Whether a failure is the one its accepted row names: the same reason, and a measure no worse than the bound."""
    if a is None:
        return False
    cls, v = reason(row["why"])
    if cls != a.get("reason"):
        return False
    way = WORSE.get(cls)
    return way is None or v is None or (a.get("bound") is not None and (v - a["bound"]) * way <= 0)


def judge_accepted(rows: list[dict], accepted: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """(new failures, accepted failures, accepted rows that now pass or are gone). An accepted row names the
    reason its need failed for and the value measured when it was accepted (`reason`, `bound`): a failure for
    another reason, or one whose measure is worse than the bound, is new."""
    acc = {(a["place_id"], a["need"]): a for a in accepted}
    failed = {(r["place_id"], r["need"]) for r in rows if not r["ok"]}
    new = [r for r in rows if not r["ok"] and not stands(r, acc.get((r["place_id"], r["need"])))]
    old = [r for r in rows if not r["ok"] and stands(r, acc.get((r["place_id"], r["need"])))]
    return new, old, [a for a in accepted if (a["place_id"], a["need"]) not in failed]


if __name__ == "__main__":
    r = measure(Path(sys.argv[1]) if len(sys.argv) > 1 else f.OUT / "terrain")
    accepted = json.loads(ACCEPTED.read_text())["accepted"] if ACCEPTED.exists() else []
    new, old, gone = judge_accepted(r["rows"], accepted)
    print(json.dumps({**{k: v for k, v in r.items() if k != "rows"}, "accepted": len(old), "new": len(new)}))
    for row in old:
        print("accepted", row["need"], row["place_id"], row["why"])
    for a in gone:
        print("passes now, take its row out of terrain_needs_accepted.json:", a["need"], a["place_id"])
    was = {(a["place_id"], a["need"]): a for a in accepted}
    for row in new:
        a = was.get((row["place_id"], row["need"]))
        print("FAIL", row["need"], row["place_id"], row["why"],
              f"(accepted only as {a.get('reason')!r} no worse than {a.get('bound')})" if a else "")
    sys.exit(1 if new else 0)
