"""The road census: the measures of a shaped road (profile, wall and steep census, the wet census and its bank
measure, the bridge-candidate listing) and the `python3 -m tools.argonia_world.routes check|census` commands. Split
from shape.py (lane 1.15-r6-census-split) so a measure-only edit does not move the ground stage's stamp: generate
imports shape.py's road pass, never this file."""
from __future__ import annotations

import math

import numpy as np

from tools.argonia_world.routes.shape import (
    BLEND_M, CAUSEWAY_M, FORD_M, GRADE_MAX, MPP, ROAD_RAISED, ROAD_WATER, _dense, _nearest, _runs,
    bilinear, shape,
)

TROUGH_BAND = {2.0: (0.03, 0.13), 4.0: (0.18, 0.45)}  # p25..p75 at 2 m and 4 m out
GRADE_P95 = 0.164
GRADE_BASE_M = 8.0  # the grade's baseline (vanilla measured over +-4 m)
WALL_M = 0.3  # a step across a road's edge past the land's own: a wall (the planner's rule, round 4)
SITE_REACH = 1.5  # a place's shaped ground in the census: its site eased out to SITE_BLEND radii (generate.py)
# Skyrim.esm's own roads (vanilla/measure.py q12, 2026-11-04: the LAND under Tamriel's 1571 road-surface meshes,
# the same 8 m grade and the census's edge-wall test): 23.4 % of points steeper than GRADE_MAX, 6.8 % of side points
# a wall, 9.6 % within 16 m of water. GRADE_MAX (the r4 Whiterun box's max) is the shaping target, not the bar
VANILLA_ROADS = {"steep_share": 0.2342, "walls_per_side_point": 0.0681}
STEP_M = 0.5  # a vertex whose cells' levels differ by more is a step (water/solve.py RIFFLE_M)
# Skyrim.esm's roadside embankment (0034; probes/vanilla_road_banks.py on Tamriel cells -20..20 x -25..10, 578 road
# meshes, 257 sides where the road stands above the land): the fall over the 8 m beside the road edge, p50 0.077,
# p95 0.304, p99 0.429, max 0.580 (m per m). A causeway's bank is held to the p99 per road.
BANK_BAND_M = 8.0
BANK_BAR = 0.429
BANK_BAR_SOURCE = "Skyrim.esm roadside fall over 8 m beside the edge, p99 (probes/vanilla_road_banks.py)"


def _at(a: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return a[np.clip(np.rint(y).astype(int), 0, a.shape[0] - 1), np.clip(np.rint(x).astype(int), 0, a.shape[1] - 1)]


def frame(pts: np.ndarray, step: float = 2.0):
    """The dense centreline at `step` samples, its unit tangent and its left normal."""
    p, _s = _dense(pts, step)
    v = np.gradient(p, axis=0)
    v /= np.maximum(np.hypot(v[:, 0], v[:, 1]), 1e-9)[:, None]
    return p, v, np.stack([-v[:, 1], v[:, 0]], 1)


def corridor_reach(shape, roads) -> np.ndarray:
    """How many roads' corridors reach each sample: a wall test whose outside sample lies in another road's corridor
    reads that road's trough (a track beside a road, a junction), not a wall."""
    reach = np.zeros(shape, np.int8)
    for pts, core in roads:
        rr, cc, _d, _i = _nearest(shape, _dense(pts)[0], core + BLEND_M / MPP)
        reach[rr, cc] += 1
    return reach


def edge_walls(h, p, nrm, core, sg, reach) -> np.ndarray:
    """A wall at each point on side sg: a step across the road's edge more than WALL_M beyond the land's own step
    just outside it (outside samples in another road's corridor skipped)."""
    zz = [bilinear(h, p[:, 0] + sg * nrm[:, 0] * (core + o), p[:, 1] + sg * nrm[:, 1] * (core + o))
          for o in (-0.5, 0.5, 1.5)]
    alone = _at(reach, p[:, 0] + sg * nrm[:, 0] * (core + 0.5), p[:, 1] + sg * nrm[:, 1] * (core + 0.5)) <= 1
    return (np.abs(zz[1] - zz[0]) > WALL_M + np.abs(zz[2] - zz[1])) & alone


def grade_along(h, p, v) -> np.ndarray:
    """|rise| / run over the GRADE_BASE_M baseline at each point (0 within half a baseline of the ends)."""
    half = GRADE_BASE_M / 2 / MPP
    za = bilinear(h, p[:, 0] + v[:, 0] * half, p[:, 1] + v[:, 1] * half)
    zb = bilinear(h, p[:, 0] - v[:, 0] * half, p[:, 1] - v[:, 1] * half)
    g = np.abs(za - zb) / GRADE_BASE_M
    e = int(np.ceil(half / 2.0))
    g[:e] = g[-e:] = 0.0
    return g


def census(h, h_pre, lo, hi, water, roads, wet, sites=()) -> dict:
    """Every wall and every dry over-steep point on ground h, tagged by cause from the data (first that holds):
    crossing - within the taper (core + BLEND_M) of a water point on the centreline, or a water sample or a water's
    bank/bed cone holding the ground (h at lo or hi) within 2 samples of the edge (steep: of the centreline); pinned - a site core's
    pin (lo == hi) or a place's site disc within 2 samples; land - the same test on the ground before the roads (h_pre) already fails there (a step in the
    land, or the land's own grade); other."""
    reach = corridor_reach(h.shape, roads)
    if lo is not None:
        pin = np.isfinite(lo) & np.isfinite(hi) & (np.abs(hi - lo) < 0.05)  # a site core's pin (lo == hi)
        bank = ((np.abs(h - lo) < 0.01) | (np.abs(h - hi) < 0.01)) & ~pin  # a water's bank or bed cone binding h
    else:  # the check on a written ground: no cones, the water mask and the sites only
        pin, bank = np.zeros(h.shape, bool), np.zeros(h.shape, bool)
    for st in sites:  # a place's shaped ground (its site out to the blend): the place's to grade, not the road's
        cy, cx, r = st["y_m"] / MPP, st["x_m"] / MPP, st["radius_m"] / MPP * SITE_REACH
        r0, r1 = int(max(cy - r, 0)), int(min(cy + r + 1, h.shape[0]))
        c0, c1 = int(max(cx - r, 0)), int(min(cx + r + 1, h.shape[1]))
        yy, xx = np.mgrid[r0:r1, c0:c1]
        pin[r0:r1, c0:c1] |= np.hypot(yy - cy, xx - cx) <= r
    pin2, bank2 = pin.copy(), bank | water
    for ax in (0, 1):
        for d in (-2, -1, 1, 2):
            pin2 |= np.roll(pin, d, ax)
            bank2 |= np.roll(bank | water, d, ax)
    made = {"walls": 0, "steep": 0}  # not in the ground before the roads (h_pre): what the road itself made
    walls = {"crossing": 0, "pinned": 0, "land": 0, "other": 0}
    steep = {"crossing": 0, "pinned": 0, "land": 0, "other": 0}
    where = {"walls": [], "steep": []}
    for ri, (pts, core) in enumerate(roads):
        p, v, nrm = frame(pts)
        if len(p) < 5:
            continue
        wp = _at(water, p[:, 0], p[:, 1])
        # along-road distance (samples) to the nearest water point on the centreline
        idx = np.nonzero(wp)[0]
        pos = np.arange(len(p)) * 2.0
        dw = np.full(len(p), np.inf) if not len(idx) else np.min(np.abs(pos[:, None] - pos[idx][None]), 1) \
            if len(idx) * len(p) < 5e7 else np.full(len(p), np.inf)
        near_w = dw <= core + BLEND_M / MPP
        for sg in (1.0, -1.0):
            wl = edge_walls(h, p, nrm, core, sg, reach)
            wl0 = edge_walls(h_pre, p, nrm, core, sg, reach) if h_pre is not None else np.zeros(len(p), bool)
            ex, ey = p[:, 0] + sg * nrm[:, 0] * (core + 0.5), p[:, 1] + sg * nrm[:, 1] * (core + 0.5)
            wet_e = np.zeros(len(p), bool)
            for o in (-1.5, -0.5, 0.5, 1.5, 2.5):
                wet_e |= _at(water, p[:, 0] + sg * nrm[:, 0] * (core + o), p[:, 1] + sg * nrm[:, 1] * (core + o))
            wet_e |= _at(bank2, ex, ey)
            pe = _at(pin2, ex, ey) | _at(pin2, p[:, 0] + sg * nrm[:, 0] * (core - 0.5), p[:, 1] + sg * nrm[:, 1] * (core - 0.5))
            made["walls"] += int((wl & ~wl0).sum()) if h_pre is not None else 0
            for i in np.nonzero(wl)[0]:
                c = "crossing" if near_w[i] or wet_e[i] else "pinned" if pe[i] else "land" if wl0[i] else "other"
                walls[c] += 1
                where["walls"].append((ri, int(i), c, round(float(p[i, 0] * MPP)), round(float(p[i, 1] * MPP)),
                                       bool(not wl0[i]), sg))
        g = grade_along(h, p, v)
        g0 = grade_along(h_pre, p, v) if h_pre is not None else np.zeros(len(p))
        rl = np.isfinite(_at(wet, p[:, 0], p[:, 1])) if wet is not None else np.zeros(len(p), bool)
        pc = _at(pin2, p[:, 0], p[:, 1])
        near_w = near_w | _at(bank2, p[:, 0], p[:, 1])
        made["steep"] += int(((g > GRADE_MAX + 1e-6) & ~rl & (g0 <= GRADE_MAX)).sum()) if h_pre is not None else 0
        for i in np.nonzero((g > GRADE_MAX + 1e-6) & ~rl)[0]:
            c = "crossing" if near_w[i] else "pinned" if pc[i] else "land" if g0[i] > GRADE_MAX else "other"
            steep[c] += 1
            where["steep"].append((ri, int(i), c, round(float(p[i, 0] * MPP)), round(float(p[i, 1] * MPP)), round(float(g0[i]), 3)))
    return {"walls": walls, "steep": steep, "made_by_road": made, "where": where}


def profile(h: np.ndarray, roads: list[tuple[np.ndarray, float]], wet=None) -> dict:
    """Measure every road on ground h: the folded cross profile at 2 and 4 m (median, share in the vanilla band),
    the grade along (p50/p95/max, the count of centreline points steeper than GRADE_MAX), and the centreline
    points under water (wet: the wet level raster, NaN dry); a point on the wet raster is a crossing, not road grade.
    The trough fold is measured on roads (core >= 4 m), vanilla's class; tracks report their own median."""
    fold = {2.0: [], 4.0: []}
    track_fold = []
    grades, steep, wet_pts, total, crossings, cross_pts, walls = [], 0, 0, 0, 0, 0, 0
    reach = corridor_reach(h.shape, roads)
    for pts, _core in roads:
        p, _s = _dense(pts, 2.0)
        if len(p) < 5:
            continue
        v = np.gradient(p, axis=0)
        v /= np.maximum(np.hypot(v[:, 0], v[:, 1]), 1e-9)[:, None]
        nrm = np.stack([-v[:, 1], v[:, 0]], 1)
        z0 = bilinear(h, p[:, 0], p[:, 1])
        for o in fold:
            a = bilinear(h, p[:, 0] + nrm[:, 0] * o / MPP, p[:, 1] + nrm[:, 1] * o / MPP)
            b = bilinear(h, p[:, 0] - nrm[:, 0] * o / MPP, p[:, 1] - nrm[:, 1] * o / MPP)
            (fold[o] if _core * MPP >= 4.0 else track_fold if o == 4.0 else []).append((a + b) / 2 - z0)
        for sg in (1.0, -1.0):
            walls += int(edge_walls(h, p, nrm, _core, sg, reach).sum())
        g = grade_along(h, p, v)
        if wet is not None:  # a point on the wet raster (a water's footprint) is a crossing, not road grade:
            # `crossings` counts its runs, each a place that wants a bridge or a ford
            lv = wet[np.clip(np.rint(p[:, 1]).astype(int), 0, wet.shape[0] - 1),
                     np.clip(np.rint(p[:, 0]).astype(int), 0, wet.shape[1] - 1)]
            rl = np.isfinite(lv)
            wet_pts += int((rl & (lv > z0)).sum())
            cross_pts += int(rl.sum())
            crossings += int((rl[1:] & ~rl[:-1]).sum() + rl[0])
            dry = ~rl
        else:
            dry = np.ones(len(p), bool)
        g = g[dry]
        grades.append(g)
        steep += int((g > GRADE_MAX + 1e-6).sum())
        total += len(p)
    g = np.concatenate(grades)
    out = {"points": total, "grade_p50": round(float(np.percentile(g, 50)), 3),
           "grade_p95": round(float(np.percentile(g, 95)), 3), "grade_max": round(float(g.max()), 3),
           "steeper_than_max": steep, "under_water": wet_pts, "crossings": crossings, "crossing_points": cross_pts, "walls": walls}
    if track_fold:
        out["track_fold_4m_median"] = round(float(np.median(np.concatenate(track_fold))), 3)
    for o, a in fold.items():
        a = np.concatenate(a)
        lo, hi = TROUGH_BAND[o]
        out[f"fold_{o:.0f}m_median"] = round(float(np.median(a)), 3)
        out[f"fold_{o:.0f}m_in_band"] = round(float(((a >= lo - 0.05) & (a <= hi + 0.05)).mean()), 3)
    return out


def load_roads(w) -> list[tuple[np.ndarray, float]]:
    """The roads as generate.Inputs reads them: ((k, 2) (col, row) samples, core half width in samples)."""
    pts: dict[str, list] = {}
    for p in w.query("SELECT route_id, x_m, y_m FROM road_point ORDER BY route_id, ord"):
        pts.setdefault(p["route_id"], []).append((p["x_m"] / MPP, p["y_m"] / MPP))
    return [(np.asarray(pts[r["route_id"]]), (r["flat_width_m"] / 2 + r["shoulder_m"]) / MPP)
            for r in w.query("SELECT route_id, flat_width_m, shoulder_m FROM road ORDER BY route_id")
            if len(pts.get(r["route_id"], [])) >= 2]


def main(argv=None) -> int:
    """`check [GROUND.npy]`: L1 - the road profile on the generated ground (default the shared out/terrain one).
    Fails on any dry road point steeper than GRADE_MAX or a fold median outside the vanilla band."""
    import argparse
    import json
    from pathlib import Path

    from tools.argonia_world import db
    from tools.argonia_world.terrain import cellwater
    from tools.argonia_world.terrain.grid import generated_ground

    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "census"])
    ap.add_argument("ground", nargs="?")
    ap.add_argument("--dump", help="census: generate's ARGONIA_ROAD_DUMP (.npz): the road pass replayed on it")
    a = ap.parse_args(argv)
    w = db.open()
    if a.cmd == "census":
        return census_main(w, a) if a.dump else wet_main(w, a)
    gp = Path(a.ground or generated_ground())
    h = np.asarray(np.load(gp, mmap_mode="r"), np.float64)
    wet, _ = cellwater.wet_raster(w)
    roads = load_roads(w)
    res = profile(h, roads, wet)
    fails = []
    # the census: walls and steep points beside a water crossing (owed to bridges) or on a place's site (owed to
    # the places lane) are listed, not failed; every other one fails (generate writes the road pass's water mask)
    wm = gp.with_name(ROAD_WATER)
    water = np.load(wm) > 0 if wm.exists() else np.isfinite(wet)
    sp = gp.with_name("entrance-sites.json")
    c = census(h, None, None, None, water, roads, wet, json.loads(sp.read_text()) if sp.exists() else ())
    res["walls_by_cause"], res["steep_by_cause"] = c["walls"], c["steep"]
    res["owed_sample_m"] = {k: [x[2:5] for x in c["where"][k] if x[2] in ("crossing", "pinned")][::25]
                            for k in ("walls", "steep")}  # (cause, x, y) every 25th: the full list is census()'s
    res["own_sample_m"] = {k: [x[2:5] for x in c["where"][k] if x[2] not in ("crossing", "pinned")][:40]
                           for k in ("walls", "steep")}
    # the bar is Skyrim.esm's own roads (q12, VANILLA_ROADS): shares over every road point, all causes counted
    n_pts = res["points"]
    ws, ss = sum(c["walls"].values()) / max(1, 2 * n_pts), sum(c["steep"].values()) / max(1, n_pts)
    res["walls_per_side_point"], res["steep_share"], res["vanilla_roads"] = round(ws, 4), round(ss, 4), VANILLA_ROADS
    if ss > VANILLA_ROADS["steep_share"]:
        fails.append(f"steep share {ss:.4f} of road points over Skyrim.esm's {VANILLA_ROADS['steep_share']}")
    if ws > VANILLA_ROADS["walls_per_side_point"]:
        fails.append(f"walls {ws:.4f} a side point over Skyrim.esm's {VANILLA_ROADS['walls_per_side_point']}")
    for o, (lo, hi) in TROUGH_BAND.items():
        m = res[f"fold_{o:.0f}m_median"]
        if not lo <= m <= hi:
            fails.append(f"fold at {o:.0f} m median {m} outside vanilla's {lo}..{hi}")
    res["fails"] = fails
    print(json.dumps(res, indent=1))
    return 1 if fails else 0


def wet_census(h, roads, ids, level, reach, step: float = 1.0, raised=None, rid=None, rnames=None, drop=None) -> dict:
    """Per road on ground h: metres under its cell's water (`level`, per sample, NaN dry) outside fords, the longest
    wet run, the fords (wet runs touching a reach: count, deepest), the causeway metres (dry over a cell with water)
    and the bank's steepest grade beside the causeway (core edge out to 30 m, where the ground falls to the water)."""
    out = {}
    for name, (pts, core) in zip(ids, roads):
        p, v, nrm = frame(pts, step)
        z, lv = bilinear(h, p[:, 0], p[:, 1]), _at(level, p[:, 0], p[:, 1])
        wet = np.isfinite(lv) & (z < lv)
        rch = np.zeros(len(p), bool)
        for o in np.arange(-core, core + 0.5, 1.0):
            rch |= _at(reach, p[:, 0] + nrm[:, 0] * o, p[:, 1] + nrm[:, 1] * o)
        ds = step * MPP
        fords, under, longest, deepest, steps_x = [], 0.0, 0.0, None, []
        for a0, a1 in _runs(wet):
            seg = slice(a0, a1)
            depth = float((lv[seg] - z[seg]).max())
            if drop is not None and (_at(drop, p[seg, 0], p[seg, 1]) > STEP_M).any():
                k = a0 + int(np.argmax(_at(drop, p[seg, 0], p[seg, 1])))
                steps_x.append({"drop_m": round(float(_at(drop, p[k:k + 1, 0], p[k:k + 1, 1])[0]), 2),
                                "at_m": [round(float(p[k, 0] * MPP)), round(float(p[k, 1] * MPP))]})
                continue  # a road over a step (a fall between two cells' levels): a bridge, never a ford
            if rch[max(a0 - 2, 0):a1 + 2].any():
                fords.append(round(depth, 2))
                if rid is not None and (deepest is None or depth > deepest["depth_m"]):
                    k = a0 + int(np.argmax(lv[seg] - z[seg]))
                    near = [int(_at(rid, p[k, 0] + nrm[k, 0] * o, p[k, 1] + nrm[k, 1] * o))
                            for o in np.arange(-core - 4, core + 4.5, 1.0)]
                    near = [x for x in near if x >= 0]
                    deepest = {"depth_m": round(depth, 2), "at_m": [round(float(p[k, 0] * MPP)), round(float(p[k, 1] * MPP))],
                               "reach": rnames[max(set(near), key=near.count)] if near and rnames else None}
            else:
                under += (a1 - a0) * ds
                longest = max(longest, (a1 - a0) * ds)
        cw = np.isfinite(lv) & ~wet & (z < lv + CAUSEWAY_M + 1.0)  # low dry ground over a cell's water
        # the bank: the fall from the core's edge over BANK_BAND_M beside it, on the sides where the road stands
        # above the land, where generate raised the ground (Skyrim.esm's bar, BANK_BAR)
        falls = []
        if cw.any():
            for sg in (-1, 1):
                xa, ya = p[cw, 0] + sg * nrm[cw, 0] * core, p[cw, 1] + sg * nrm[cw, 1] * core
                ob = core + BANK_BAND_M / MPP
                xb, yb = p[cw, 0] + sg * nrm[cw, 0] * ob, p[cw, 1] + sg * nrm[cw, 1] * ob
                fall = (bilinear(h, xa, ya) - bilinear(h, xb, yb)) / BANK_BAND_M
                m = fall > 0
                if raised is not None:
                    mid = core + BANK_BAND_M / MPP / 2
                    m &= _at(raised, p[cw, 0] + sg * nrm[cw, 0] * mid, p[cw, 1] + sg * nrm[cw, 1] * mid) > 0
                falls.append(fall[m])
        falls = np.concatenate(falls) if falls else np.zeros(0)
        g = float(falls.max()) if len(falls) else 0.0
        g99 = float(np.percentile(falls, 99)) if len(falls) else 0.0
        out[name] = {"length_m": round(len(p) * ds), "under_m": round(under), "longest_wet_m": round(longest),
                    "fords": len(fords), "ford_max_m": max(fords) if fords else 0.0,
                    "causeway_m": round(float(cw.sum()) * ds), "bank_max_grade": round(g, 3),
                    "bank_p99": round(g99, 3), "deepest_ford": deepest, "step_crossings": steps_x}
    return out


def bridge_candidates(res: dict, bridges: list[dict]) -> dict:
    """The step crossings still owed a bridge: per road, those no bridge covers (a bridge covers a crossing on one of
    its roads within half its length of its centre)."""
    from tools.argonia_world.routes.infra import BRIDGE_LEN_M

    def covered(road, x):
        return any(road in b["routes"] and math.hypot(x["at_m"][0] - b["at_m"][0], x["at_m"][1] - b["at_m"][1])
                   <= BRIDGE_LEN_M / 2 for b in bridges)
    out = {k: [x for x in r["step_crossings"] if not covered(k, x)] for k, r in res.items()}
    return {k: v for k, v in out.items() if v}


def wet_main(w, a) -> int:
    """`census [GROUND.npy]`: every road's wet census on the generated ground (lane 1.15-r6-roads-dry). Fails on any
    metre under water outside a ford, a ford deeper than FORD_M, or a bank steeper than GRADE_MAX (the slope's
    lip-limit is the land's elsewhere, so the bank grade is reported against the bar)."""
    import json
    from pathlib import Path

    from tools.argonia_world.terrain import cellwater
    from tools.argonia_world.terrain.generate import Q
    from tools.argonia_world.terrain.grid import data_root, generated_ground
    gp = Path(a.ground or generated_ground())
    h = np.asarray(np.load(gp, mmap_mode="r"), np.float64)
    wl = cellwater.load(w).level
    level = np.pad(np.repeat(np.repeat(wl, Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge")[:h.shape[0], :h.shape[1]]
    rl, rid = cellwater.reach_raster(w, h.shape[0])
    rnames = [f"{r['id']} ({r['kind']}, {r['width_m']} m)"
              for r in w.query("SELECT id, kind, width_m FROM hydrology_reach ORDER BY id")]
    rp = gp.with_name(ROAD_RAISED)
    raised = np.load(rp) if rp.exists() else None
    zb = np.load(data_root() / "hydrology-graph-bodies.npz")
    reach = ~np.isnan(rl) & ~np.isfinite(zb["level"]) & ~zb["sea"]
    ids = [r["route_id"] for r in w.query("SELECT route_id FROM road ORDER BY route_id")]
    pts: dict[str, list] = {}
    for p in w.query("SELECT route_id, x_m, y_m FROM road_point ORDER BY route_id, ord"):
        pts.setdefault(p["route_id"], []).append(1)
    ids = [i for i in ids if len(pts.get(i, [])) >= 2]
    from tools.argonia_world.terrain.generate import vertex_levels
    vmin, vmax = vertex_levels(wl)
    drop = np.nan_to_num(vmax - vmin, nan=0.0)[:h.shape[0], :h.shape[1]]
    for _ in range(3):  # a step's channel runs a few samples into the lower cell: the drop carried to it
        drop = np.maximum.reduce([drop, np.roll(drop, 1, 0), np.roll(drop, -1, 0), np.roll(drop, 1, 1), np.roll(drop, -1, 1)])
    res = wet_census(h, load_roads(w), ids, level, reach, raised=raised, rid=rid, rnames=rnames, drop=drop)
    tot = {k: round(sum(r[k] for r in res.values()), 1) for k in ("length_m", "under_m", "causeway_m", "fords")}
    tot["roads_wet"] = sum(r["under_m"] > 0 for r in res.values())
    tot["ford_max_m"] = max([r["ford_max_m"] for r in res.values()] or [0])
    tot["bank_max_grade"] = max([r["bank_max_grade"] for r in res.values()] or [0])
    fails = [f"{k}: {r['under_m']} m under water" for k, r in res.items() if r["under_m"] > 0]
    fails += [f"{k}: ford {r['ford_max_m']} m" for k, r in res.items() if r["ford_max_m"] > FORD_M + 0.01]
    fails += [f"{k}: bank p99 {r['bank_p99']} over the bar {BANK_BAR}" for k, r in res.items()
              if raised is not None and r["bank_p99"] > BANK_BAR]
    from tools.argonia_world.routes.infra import census_bridges
    bridges = census_bridges(w, lambda x, y: float(bilinear(h, np.array([x / MPP]), np.array([y / MPP]))[0]))
    tot["bridge_candidates"] = bridge_candidates(res, bridges)
    print(json.dumps({"total": tot, "roads": res, "fails": fails, "bridges": bridges, "grade_max": GRADE_MAX,
                      "bank_bar": {"value": BANK_BAR, "band_m": BANK_BAND_M, "source": BANK_BAR_SOURCE},
                      "bank_measured_on": "raised" if raised is not None else "all low ground (no road-raised mask)"}, indent=1))
    return 1 if fails else 0


def census_main(w, a) -> int:
    """`census --dump D [GROUND_DIR]`: the road pass replayed on generate's dump (the ground before the roads, the
    cones and the water mask), then every wall and dry over-steep point by cause, with what the road itself made
    (not in the ground before it). The sites are GROUND_DIR's entrance-sites.json (default out/terrain)."""
    import json
    from pathlib import Path

    from tools.argonia_world.terrain import cellwater
    d = np.load(a.dump)
    h_pre = np.asarray(d["h"], np.float64)
    lo, hi, water = np.asarray(d["lo"], np.float64), np.asarray(d["hi"], np.float64), d["water"]
    h = h_pre.copy()
    roads = load_roads(w)
    shape(h, roads, water, lo, hi)
    h = np.minimum(np.maximum(h, lo), hi)
    wet, _ = cellwater.wet_raster(w)
    sp = Path(a.ground or "out/terrain") / "entrance-sites.json"
    c = census(h, h_pre, lo, hi, water, roads, wet, json.loads(sp.read_text()) if sp.exists() else ())
    pts_n = sum(len(frame(pts)[0]) for pts, _c in roads)
    vb = VANILLA_ROADS
    sh = {"points": pts_n, "walls_per_side_point": round(sum(c["walls"].values()) / (2 * pts_n), 4),
          "made_walls_per_side_point": round(c["made_by_road"]["walls"] / (2 * pts_n), 4),
          "steep_share": round(sum(c["steep"].values()) / pts_n, 4), "vanilla": vb}
    fails = []
    if sh["walls_per_side_point"] > vb["walls_per_side_point"]:
        fails.append(f"walls {sh['walls_per_side_point']} a side point over Skyrim.esm's {vb['walls_per_side_point']}")
    if sh["steep_share"] > vb["steep_share"]:
        fails.append(f"steep share {sh['steep_share']} over Skyrim.esm's {vb['steep_share']}")
    land = {}
    for ri, _i, cause, x, y, g0 in c["where"]["steep"]:
        if cause == "land":
            land.setdefault(ri, []).append((x, y, g0))
    made = {}
    for x in c["where"]["walls"]:
        if x[5]:
            made[x[2]] = made.get(x[2], 0) + 1
    res = {"bar": sh, "fails": fails, "walls": c["walls"], "steep": c["steep"], "made_by_road": c["made_by_road"],
           "made_walls_by_cause": made,
           "made_walls_m": [x[:5] for x in c["where"]["walls"] if x[5]][:60],
           "walls_total": sum(c["walls"].values()), "steep_total": sum(c["steep"].values()),
           "steep_land_by_road": {str(r): {"points": len(v), "land_grade_median": round(float(np.median([g for *_, g in v])), 3),
                                           "first_m": v[0][:2]} for r, v in sorted(land.items())}}
    print(json.dumps(res, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
