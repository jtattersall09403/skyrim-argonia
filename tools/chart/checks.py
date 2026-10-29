"""The chart's L1 checks, on the rendered masks and index (2.W4 §c):

- cities: each of the seven sits in the index at its database position (recomputed here from the metres, x east and
  y south, no flip), on land in the terrain at that sample, and ringed in ink; the same seven mirrored north-south
  would put at least one in the sea, so the land test can tell the mirror;
- rivers: every major river's centreline has river ink within 8 px (the hand's wobble is at most 5.2) along >= 95% of its length;
- roads: every major road's centreline has road ink within 8 px along >= 90% (drawn as a double line);
- no player-position marker: the index and the layers carry none (C9) - the index has no "player" key.
"""
from __future__ import annotations

import numpy as np

from tools.chart.data import CITIES, SEA, Features
from tools.chart.render import MASTER, Chart, dilate, wobble


def _near(mask: np.ndarray, r: int) -> np.ndarray:
    m = mask > 24
    for k in range(r):
        m = dilate(m, diag=k % 2 == 1)
    return m


def _coverage(near: np.ndarray, pts_px: np.ndarray, step: float) -> float:
    p = wobble(pts_px, np.random.default_rng(0), step, 0.0, 1.0, smooth=1)
    s = near.shape[0]
    ij = np.clip(np.rint(p).astype(int), 0, s - 1)
    return float(near[ij[:, 1], ij[:, 0]].mean())


def run_all(chart: Chart, f: Features) -> dict:
    out = {}
    idx = chart.index["places"]
    S, n = f.sample_m, f.n
    rows = []
    mirrored_sea = 0
    ring = _near(chart.masks["cities"], 3)
    ok = True
    for pid in CITIES:
        p = next(x for x in f.places if x.id == pid)
        want = (chart.margin + p.x_m * chart.scale, chart.margin + p.y_m * chart.scale)
        got = idx[pid]["px"]
        i, j = min(n, int(p.y_m / S)), min(n, int(p.x_m / S))
        on_land = int(f.cover[i, j]) not in SEA and float(f.ground[i, j]) > f.sea_level_m - 1
        mirrored_sea += int(f.cover[n - i, j]) in SEA
        x, y = round(want[0]), round(want[1])
        r = round(46 * chart.size / MASTER) + 2
        inked = bool(ring[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1].any())
        pos_ok = abs(got[0] - want[0]) < 0.01 and abs(got[1] - want[1]) < 0.01
        rows.append({"city": p.name, "px": got, "position_ok": pos_ok, "on_land": on_land, "inked": inked})
        ok &= pos_ok and on_land and inked
    out["cities"] = {"ok": ok and mirrored_sea > 0 and len(rows) == 7, "rows": rows,
                     "mirrored_in_sea": mirrored_sea}
    del ring
    for key, lines, need in (("rivers", f.rivers, 0.95), ("roads", f.roads, 0.90)):
        near = _near(chart.masks[key], round(8 * chart.size / MASTER) + 1)
        cov = {r.id: round(_coverage(near, chart.margin + r.pts * chart.scale, 2.0), 4) for r in lines if r.major}
        out[key] = {"ok": bool(cov) and min(cov.values()) >= need, "need": need, "count": len(cov),
                    "min": min(cov.values()) if cov else None, "coverage": cov}
        del near
    out["no_player_marker"] = {"ok": not any("player" in k for k in chart.index), "keys": sorted(chart.index)}
    return out
