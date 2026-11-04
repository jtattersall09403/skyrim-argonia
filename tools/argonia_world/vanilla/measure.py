"""The 1.15 audit: how Skyrim.esm answers each world question (decision 0034). Read only; prints JSON.

    python -m tools.argonia_world.vanilla.measure [q1 .. q10 | all]

Every function reads the cache built by load.py (Tamriel exterior of Skyrim.esm). Units are Skyrim units
(1 vertex = 128 u). Rows of a cell's 33x33 grid run south to north, columns west to east.
"""
from __future__ import annotations

import json
import math
import re
import struct
import sys
from collections import Counter, defaultdict

import numpy as np

from ..skyrim_units import CELL_UNITS, VERTEX_SPACING_UNITS
from .load import ground, tamriel

SEA = -14000.0
NOWATER = 1e30


def level(c: dict, t: dict) -> float:
    w = c["water"]
    return t["world"]["water"] if w is None or abs(w) > 1e9 else w


def mosaic(t, x0, y0, x1, y1):
    """Heights and per-vertex water level for cells x0..x1, y0..y1 (inclusive); NaN where no LAND."""
    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    H = np.full((ny * 32 + 1, nx * 32 + 1), np.nan, np.float32)
    W = np.full_like(H, np.nan)
    for (x, y), c in t["cells"].items():
        if x0 <= x <= x1 and y0 <= y <= y1 and c["h"] is not None:
            r, q = (y - y0) * 32, (x - x0) * 32
            H[r:r + 33, q:q + 33] = c["h"]
            W[r:r + 33, q:q + 33] = np.maximum(np.nan_to_num(W[r:r + 33, q:q + 33], nan=-1e9), level(c, t))
    return H, W


def chamfer(mask: np.ndarray, steps: int) -> np.ndarray:
    """Vertex distance (8-neighbour, 1 per step) to the nearest True, capped at steps+1."""
    d = np.where(mask, 0, steps + 1).astype(np.int16)
    cur = mask.copy()
    for k in range(1, steps + 1):
        p = np.pad(cur, 1)
        nb = np.zeros_like(cur)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                nb |= p[1 + di:1 + di + cur.shape[0], 1 + dj:1 + dj + cur.shape[1]]
        new = nb & ~cur
        d[new] = k
        cur = nb
    return d


def slope_deg(H: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(H.astype(np.float64), 128.0)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def pct(a, ps=(10, 50, 90)):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return {f"p{p}": round(float(np.percentile(a, p)), 1) for p in ps} | {"n": int(a.size)} if a.size else {"n": 0}


def edid(t, fid):
    if fid is None or fid == 0:
        return "(default)"
    f = t["forms"].get(fid)
    return f[1] if f else ""


def sig(t, fid):
    f = t["forms"].get(fid)
    return f[0] if f else ""


# ---------- Q1 shores ----------
AREAS = {"ilinalta": (-12, -14, -4, -8), "solitude_sea": (-19, 22, -13, 28), "morthal_marsh": (-13, 13, -6, 19)}


def shore_profile(t, box):
    H, W = mosaic(t, *box)
    ok = np.isfinite(H)
    wet = ok & (H < W)
    dry = ok & ~wet
    din = chamfer(dry, 12)  # for wet vertices: distance to dry
    dout = chamfer(wet, 12)  # for dry vertices: distance to wet
    above = H - W
    out = {"cells": (box[2] - box[0] + 1) * (box[3] - box[1] + 1), "wet_share": round(float(wet.sum() / ok.sum()), 3),
           "levels": sorted({round(float(v)) for v in np.unique(W[ok])})[:8]}
    out["depth_by_vertices_from_shore"] = {k: pct(-above[wet & (din == k)])["p50"] if (wet & (din == k)).any() else None
                                          for k in (1, 2, 3, 5, 8, 12, 13)}
    out["rise_by_vertices_from_water"] = {k: pct(above[dry & (dout == k)])["p50"] if (dry & (dout == k)).any() else None
                                         for k in (1, 2, 3, 5, 8, 10, 12, 13)}
    # grade over the first 1-10 vertices above the line: median slope (u per u)
    s = slope_deg(np.nan_to_num(H, nan=0))
    out["slope_deg_first_10_above"] = pct(s[dry & (dout >= 1) & (dout <= 10)])
    out["slope_deg_first_3_below"] = pct(s[wet & (din <= 3)])
    # cell-centre depth for cells mostly wet
    cc = []
    for (x, y), c in t["cells"].items():
        if box[0] <= x <= box[2] and box[1] <= y <= box[3] and c["h"] is not None and c["h"][16, 16] < level(c, t):
            cc.append(level(c, t) - c["h"][16, 16])
    out["cell_centre_depth"] = pct(cc)
    return out


def q1(t):
    return {k: shore_profile(t, b) for k, b in AREAS.items()}


# ---------- Q2 partly-wet cells and holes ----------
def q2(t):
    C = t["cells"]
    exp = {k: c["water"] for k, c in C.items() if c["water"] is not None and abs(c["water"]) < 1e9}
    frac = []
    no_wet = 0
    for k, w in exp.items():
        h = C[k]["h"]
        f = float((h < w).mean())
        frac.append(f)
        no_wet += f == 0
    # holes: a cell without explicit water, whose 4 neighbours (>=2) carry one explicit level, ground below that level
    holes, dry_enclosed = [], 0
    for (x, y), c in C.items():
        if (x, y) in exp:
            continue
        nb = [exp[n] for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if n in exp]
        if len(nb) >= 2:
            lv = Counter(round(v) for v in nb).most_common(1)[0][0]
            below = float((c["h"] < lv).mean())
            dry_enclosed += 1
            if below > 0:
                holes.append(((x, y), lv, round(below, 3)))
    # does an explicit level ever sit in a cell whose ground is fully above it (a padded footprint)?
    flags_water = Counter(bool(c["flags"] & 2) for c in C.values())
    return {"cells": len(C), "has_water_flag": dict(flags_water), "explicit_levels": len(exp),
            "default_level": t["world"]["water"],
            "explicit_wet_share": pct(frac, (5, 10, 25, 50, 75)),
            "explicit_cells_with_no_wet_vertex": int(no_wet),
            "explicit_cells_under_10pct_wet": int(sum(f < .1 for f in frac)),
            "default_cells_flanked_by_2plus_explicit": dry_enclosed,
            "of_which_ground_dips_below_neighbour_level": len(holes), "examples": holes[:8]}


# ---------- Q3 slopes and cliffs ----------
CLIFF = re.compile(r"^(Mountain|RockCliff|Cliff|.*Cliff)", re.I)


def q3(t):
    C = t["cells"]
    allS, per = [], {}
    for k, c in C.items():
        s = slope_deg(c["h"])
        allS.append(s.ravel())
        per[k] = float((s > 45).mean())
    S = np.concatenate(allS)
    bins = [0, 10, 20, 30, 40, 45, 50, 60, 70, 75, 80, 82.9, 90]
    hist = np.histogram(S, bins)[0] / S.size
    cl = Counter()
    for r in t["refs"]:
        if sig(t, r[1]) == "STAT" and CLIFF.match(edid(t, r[1])):
            cl[r[0]] += 1
    groups = defaultdict(list)
    for k, f in per.items():
        b = "0" if f == 0 else "<5%" if f < .05 else "5-20%" if f < .2 else ">=20%"
        groups[b].append(cl.get(k, 0))
    return {"vertices": int(S.size), "share_by_slope": {f"{a}-{b}": round(float(h), 4) for a, b, h in zip(bins, bins[1:], hist)},
            "over_45": round(float((S > 45).mean()), 4), "over_60": round(float((S > 60).mean()), 4),
            "over_75": round(float((S > 75).mean()), 5), "max_deg": round(float(S.max()), 1),
            "cliff_refs_per_cell_by_steep_share": {g: {"cells": len(v), "mean": round(float(np.mean(v)), 1),
                                                       "share_with_any": round(float(np.mean(np.array(v) > 0)), 2)}
                                                   for g, v in sorted(groups.items())},
            "cliff_ref_forms_top": Counter(edid(t, r[1]) for r in t["refs"] if sig(t, r[1]) == "STAT" and CLIFF.match(edid(t, r[1]))).most_common(12)}


# ---------- Q4 materials ----------
QOFF = {0: (0, 0), 1: (0, 16), 2: (16, 0), 3: (16, 16)}  # quadrant -> (row, col) offset; 0 SW,1 SE,2 NW,3 NE


def cell_weights(c):
    """{ltex: 33x33 weight} using base + layers in order (alpha over)."""
    w = defaultdict(lambda: np.zeros((33, 33), np.float32))
    for q, (r0, c0) in QOFF.items():
        layers = sorted([a for a in c["atxt"] if a[0] == q], key=lambda a: a[1])
        acc = {c["btxt"][q] or 0: np.ones((17, 17), np.float32)}
        for _, _, tex, alpha in layers:
            a = alpha.reshape(17, 17)
            for k in acc:
                acc[k] = acc[k] * (1 - a)
            acc[tex] = acc.get(tex, 0) + a
        for k, v in acc.items():
            w[k][r0:r0 + 17, c0:c0 + 17] = np.maximum(w[k][r0:r0 + 17, c0:c0 + 17], v)
    return w


def q4(t):
    C = t["cells"]
    per_quad, per_cell, region_tex = [], [], defaultdict(set)
    ramps, steps = [], []
    for k, c in C.items():
        texs = set(x or 0 for x in c["btxt"]) | {a[2] for a in c["atxt"]}
        per_cell.append(len(texs))
        for q in range(4):
            per_quad.append(sum(a[0] == q for a in c["atxt"]) + (c["btxt"][q] is not None))
        for rg in c["regions"][:1]:
            region_tex[rg] |= texs
        for a in c["atxt"]:
            A = a[3].reshape(17, 17)
            d = np.abs(np.diff(A, axis=1))
            steps.extend(d[d > 0.01].tolist())
            for row in A:  # ramp length: consecutive vertices strictly between 0.02 and 0.98
                run = 0
                for v in row:
                    if 0.02 < v < 0.98:
                        run += 1
                    elif run:
                        ramps.append(run)
                        run = 0
    # VCLR
    lum, lum_steep, lum_flat, lum_wet = [], [], [], []
    for k, c in list(C.items())[::4]:
        if c["vclr"] is None:
            continue
        L = c["vclr"].mean(axis=2)
        s = slope_deg(c["h"])
        lum.append(L.ravel())
        lum_steep.append(L[s > 40])
        lum_flat.append(L[s < 10])
        lum_wet.append(L[np.abs(c["h"] - level(c, t)) < 256])
    cat = lambda xs: np.concatenate(xs) if xs else np.array([])
    vc = sum(c["vclr"] is not None for c in C.values())
    # sequence from bed to land: dominant LTEX by height above local water, in explicit-water cells and sea shores
    seq = {"rivers_lakes": defaultdict(Counter), "sea": defaultdict(Counter)}
    for k, c in C.items():
        lv = level(c, t)
        h = c["h"]
        if not ((h < lv).any() and (h > lv).any()):
            continue
        kind = "rivers_lakes" if c["water"] is not None and abs(c["water"]) < 1e9 else "sea"
        w = cell_weights(c)
        keys = list(w)
        stack = np.stack([w[x] for x in keys])
        dom = np.array(keys)[stack.argmax(0)]
        dh = h - lv
        b = np.clip(np.floor(dh / 128), -6, 12).astype(int)
        for bb, tex in zip(b.ravel(), dom.ravel()):
            seq[kind][int(bb)][edid(t, int(tex))] += 1
    seqo = {kind: {f"{bb * 128}..{bb * 128 + 128}": [(n, round(v / sum(cn.values()), 2)) for n, v in cn.most_common(3)]
                   for bb, cn in sorted(d.items())} for kind, d in seq.items()}
    return {"layers_per_quadrant_incl_base": dict(sorted(Counter(per_quad).items())),
            "distinct_ltex_per_cell": pct(per_cell, (10, 50, 90, 99)),
            "distinct_ltex_per_region": pct([len(v) for v in region_tex.values()], (10, 50, 90)),
            "alpha_ramp_vertices": pct(ramps, (10, 50, 90)),
            "alpha_step_between_neighbours": pct(steps, (10, 50, 90)),
            "vclr_cells": vc, "vclr_lum": pct(cat(lum), (1, 10, 50, 90)), "vclr_lum_steep_over_40": pct(cat(lum_steep), (10, 50, 90)),
            "vclr_lum_flat_under_10": pct(cat(lum_flat), (10, 50, 90)), "vclr_lum_within_2v_of_water": pct(cat(lum_wet), (10, 50, 90)),
            "share_vclr_under_200": round(float((cat(lum) < 200).mean()), 3),
            "sequence_dominant_ltex_by_height_above_water": seqo}


# ---------- Q5 rocks ----------
ROCK = re.compile(r"^(Rock[LMS]\d|RockPile|Boulder|RockCliff|MountainCliff|MountainTrim|MountainSlab|MountainTrimSlab)", re.I)


def tilt_deg(rx, ry):
    return math.degrees(math.acos(max(-1, min(1, math.cos(rx) * math.cos(ry)))))


def ground_slope(t, x, y):
    a, b, c_, d = ground(t, x + 64, y), ground(t, x - 64, y), ground(t, x, y + 64), ground(t, x, y - 64)
    if None in (a, b, c_, d):
        return None
    return math.degrees(math.atan(math.hypot((a - b) / VERTEX_SPACING_UNITS, (c_ - d) / VERTEX_SPACING_UNITS)))


def q5(t):
    out = defaultdict(lambda: {"sink_u": [], "sink_frac": [], "tilt": [], "slope": [], "tilt_minus_slope": []})
    for r in t["refs"]:
        if sig(t, r[1]) != "STAT":
            continue
        e = edid(t, r[1])
        m = ROCK.match(e)
        if not m:
            continue
        cls = ("boulder" if re.match(r"Rock[LMS]\d", e) else "pile" if e.lower().startswith("rockpile") else "cliff")
        x, y, z, rx, ry, rz, sc = r[2:9]
        g = ground(t, x, y)
        ob = t["forms"][r[1]][2]
        if g is None or not ob:
            continue
        hgt = (ob[5] - ob[2]) * sc
        bottom = z + ob[2] * sc
        o = out[cls]
        o["sink_u"].append(g - bottom)
        if hgt > 0:
            o["sink_frac"].append((g - bottom) / hgt)
        tl = tilt_deg(rx, ry)
        sl = ground_slope(t, x, y)
        o["tilt"].append(tl)
        if sl is not None:
            o["slope"].append(sl)
            o["tilt_minus_slope"].append(tl - sl)
    res = {}
    for cls, o in out.items():
        tl = np.array(o["tilt"])
        res[cls] = {"n": len(tl), "sink_u": pct(o["sink_u"]), "sink_frac_of_bound": pct(o["sink_frac"]),
                    "tilt_deg": pct(tl), "upright_under_2deg": round(float((tl < 2).mean()), 2),
                    "ground_slope": pct(o["slope"]), "tilt_minus_slope": pct(o["tilt_minus_slope"])}
    return res


# ---------- Q6 vegetation ----------
def cell_class(t, c):
    w = cell_weights(c)
    k = max(w, key=lambda x: w[x].sum())
    e = edid(t, k).lower()
    for key, name in (("snow", "snow"), ("mountain", "mountain"), ("tundra", "tundra"), ("pine", "pine forest"),
                      ("forest", "forest"), ("field", "field/grass"), ("grass", "field/grass"), ("marsh", "marsh"),
                      ("mud", "marsh"), ("dirt", "dirt"), ("rock", "rock"), ("beach", "shore"), ("sand", "shore")):
        if key in e:
            return name
    return "other:" + edid(t, k)


def q6(t):
    C = t["cells"]
    tree, flor = Counter(), Counter()
    for r in t["refs"]:
        s = sig(t, r[1])
        if s == "TREE":
            if re.search(r"(shrub|bush|fern|plant|grass|flower|hanging|moss)", edid(t, r[1]), re.I):
                flor[r[0]] += 1
            else:
                tree[r[0]] += 1
        elif s == "FLOR":
            flor[r[0]] += 1
    bycls = defaultdict(lambda: ([], []))
    for k, c in C.items():
        cl = cell_class(t, c)
        bycls[cl][0].append(tree.get(k, 0))
        bycls[cl][1].append(flor.get(k, 0))
    # tree height above local water and distance to wet, in cells with water at the surface
    dz, dist = [], []
    wetcells = {k for k, c in C.items() if (c["h"] < level(c, t)).any()}
    for r in t["refs"]:
        if r[0] not in wetcells or sig(t, r[1]) != "TREE" or re.search(r"(shrub|bush|fern|plant|grass|flower)", edid(t, r[1]), re.I):
            continue
        c = C[r[0]]
        lv = level(c, t)
        dz.append(r[4] - lv)
        u, v = (r[2] - r[0][0] * CELL_UNITS) / VERTEX_SPACING_UNITS, (r[3] - r[0][1] * CELL_UNITS) / VERTEX_SPACING_UNITS
        ii, jj = np.nonzero(c["h"] < lv)
        dist.append(float(np.min(np.hypot(ii - v, jj - u))) * 128)
    dist = np.array(dist)
    return {"by_class": {k: {"cells": len(a), "trees_mean": round(float(np.mean(a)), 1), "trees_p90": float(np.percentile(a, 90)),
                             "flora_mean": round(float(np.mean(b)), 1)} for k, (a, b) in sorted(bycls.items(), key=lambda x: -len(x[1][0])) if len(a) >= 30},
            "trees_total": sum(tree.values()), "flora_total": sum(flor.values()),
            "trees_in_wet_cells": len(dist), "tree_z_minus_water_u": pct(dz, (1, 5, 10, 50)),
            "tree_dist_to_water_u": pct(dist, (1, 5, 10, 50)), "share_trees_standing_in_water": round(float(np.mean(np.array(dz) < 0)), 3) if dz else None,
            "share_within_256u_of_water": round(float((dist < 256).mean()), 3)}


# ---------- Q7 weather ----------
COLS = ["sky_upper", "fog_near", "unk", "ambient", "sunlight", "sun", "stars", "sky_lower", "horizon", "effect",
        "cloud_lod_diffuse", "cloud_lod_ambient", "fog_far", "sky_statics", "water_mult", "sun_glare", "moon_glare"]
TIMES = ["sunrise", "day", "sunset", "night"]


def q7(t):
    F = t["forms"]
    rows = []
    for fid, (s, e, _, sb) in F.items():
        if s != "WTHR":
            continue
        d = {}
        for k, b in sb:
            d.setdefault(k, b)
        if b"FNAM" not in d or b"NAM0" not in d or b"DATA" not in d:
            continue
        fn = struct.unpack_from("<8f", d[b"FNAM"]) if len(d[b"FNAM"]) >= 32 else struct.unpack_from("<6f", d[b"FNAM"]) + (0, 0)
        flags = d[b"DATA"][11]
        cls = "snow" if flags & 8 else "rain" if flags & 4 else "cloudy" if flags & 2 else "pleasant" if flags & 1 else "none"
        n0 = d[b"NAM0"]
        col = {}
        for ci in range(min(17, len(n0) // 16)):
            for ti in range(4):
                r_, g_, b_, _ = n0[(ci * 4 + ti) * 4:(ci * 4 + ti) * 4 + 4]
                col[(COLS[ci], TIMES[ti])] = (r_ + g_ + b_) / 3
        rows.append((e, cls, fn, col))
    out = {}
    for cls in ("pleasant", "cloudy", "rain", "snow", "none"):
        rs = [r for r in rows if r[1] == cls]
        if not rs:
            continue
        o = {"n": len(rs), "fog_day_near": pct([r[2][0] for r in rs]), "fog_day_far": pct([r[2][1] for r in rs]),
             "fog_night_near": pct([r[2][2] for r in rs]), "fog_night_far": pct([r[2][3] for r in rs]),
             "fog_day_max": pct([r[2][6] for r in rs])}
        for ti in TIMES:
            o[f"ambient/sunlight_{ti}"] = pct([r[3][("ambient", ti)] / max(1, r[3][("sunlight", ti)]) for r in rs])
            o[f"sunlight_lum_{ti}"] = pct([r[3][("sunlight", ti)] for r in rs])
        out[cls] = o
    # region weather lists
    lists = []
    for fid, (s, e, _, sb) in F.items():
        if s != "REGN":
            continue
        typ = None
        for k, b in sb:
            if k == b"RDAT":
                typ = struct.unpack_from("<I", b)[0]
            if k == b"RDWT" and typ == 3:
                ent = [struct.unpack_from("<III", b, i) for i in range(0, len(b), 12)]
                lists.append((e, [(edid(t, w), c, edid(t, g) if g else "") for w, c, g in ent]))
    ent_n = [len(x[1]) for x in lists]
    tot = [sum(c for _, c, _ in x[1]) for x in lists]
    glob = sum(1 for x in lists for _, _, g in x[1] if g)
    return {"weathers_by_class": out, "weather_rows": len(rows), "region_lists": len(lists),
            "entries_per_list": pct(ent_n, (10, 50, 90)), "chance_sum_per_list": pct(tot, (10, 50, 90)),
            "entries_with_global": glob, "entries_total": sum(ent_n),
            "examples": [x for x in lists if x[0] in ("WeatherCoastFog", "WeatherTundraMarsh", "WeatherFalkreath",
                                                      "WeatherPineForest", "WeatherTundraMarshNoPrecip", "WeatherReach")][:4]}


# ---------- Q8 mist ----------
def q8(t):
    C = t["cells"]
    per_form, cells, dz, slope, nearw = Counter(), Counter(), [], [], []
    for r in t["refs"]:
        e = edid(t, r[1])
        if sig(t, r[1]) != "MSTT" or not re.match(r"FX(MistLow|Fog|VolumeMist|AmbBlowingFog|MistStreet)", e):
            continue
        per_form[e] += 1
        cells[r[0]] += 1
        c = C[r[0]]
        lv = level(c, t)
        dz.append(r[4] - lv)
        nearw.append(bool((np.abs(c["h"] - lv) < 512).any() and (c["h"] < lv).any()))
        s = ground_slope(t, r[2], r[3])
        if s is not None:
            slope.append(s)
    cls = Counter(cell_class(t, C[k]) for k in cells)
    return {"refs": sum(per_form.values()), "cells_with_mist": len(cells), "of_cells": len(C),
            "forms": per_form.most_common(10), "refs_per_mist_cell": pct(list(cells.values()), (50, 90)),
            "z_above_cell_water": pct(dz, (10, 50, 90)), "in_cells_with_surface_water": round(float(np.mean(nearw)), 2),
            "ground_slope": pct(slope), "cell_classes": cls.most_common(8),
            "top_cells": [(k, C[k]["edid"], n) for k, n in cells.most_common(8)]}


# ---------- Q9 border ----------
def region_polys(t, name):
    sb = next(f[3] for f in t["forms"].values() if f[0] == "REGN" and f[1] == name)
    polys = []
    for k, b in sb:
        if k == b"RPLD":
            polys.append(np.array(struct.unpack(f"<{len(b) // 4}f", b)).reshape(-1, 2))
    return polys


def inside(poly, x, y):
    n, j, ins = len(poly), len(poly) - 1, False
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            ins = not ins
        j = i
    return ins


def q9(t):
    C = t["cells"]
    polys = region_polys(t, "BorderRegionSkyrim")
    big = max(polys, key=len)
    refs = Counter(r[0] for r in t["refs"])
    tree = Counter(r[0] for r in t["refs"] if sig(t, r[1]) == "TREE")
    ins, outs = defaultdict(list), defaultdict(list)
    for (x, y), c in C.items():
        o = ins if inside(big, x * CELL_UNITS + CELL_UNITS // 2, y * CELL_UNITS + CELL_UNITS // 2) else outs
        o["h"].append(float(c["h"].mean()))
        o["relief"].append(float(c["h"].max() - c["h"].min()))
        o["refs"].append(refs.get((x, y), 0))
        o["trees"].append(tree.get((x, y), 0))
        o["layers"].append(len(c["atxt"]))
        o["vclr"].append(c["vclr"] is not None)
        o["slope45"].append(float((slope_deg(c["h"]) > 45).mean()))
    xs = [k[0] for k in C]
    ys = [k[1] for k in C]
    return {"polygons": [len(p) for p in polys], "cells_inside": len(ins["h"]), "cells_outside": len(outs["h"]),
            "cell_bounds": [min(xs), min(ys), max(xs), max(ys)], "world_bounds_u": [t["world"].get("min"), t["world"].get("max")],
            **{f"{side}_{k}": pct(v, (10, 50, 90)) for side, d in (("in", ins), ("out", outs)) for k, v in d.items() if k != "vclr"},
            "out_share_with_refs": round(float(np.mean(np.array(outs["refs"]) > 0)), 2),
            "out_share_with_vclr": round(float(np.mean(outs["vclr"])), 2)}


# ---------- Q10 entrances ----------
ENTR = re.compile(r"^(NorDoor.*Load|NorLargeDoor|MineDoor.*Load|DweDoor.*Load|AutoLoadDoor01)$")


def q10(t):
    stats = [(r, edid(t, r[1])) for r in t["refs"] if sig(t, r[1]) == "STAT"]
    pos = np.array([(r[2], r[3]) for r, _ in stats])
    rows = []
    doors = [r for r in t["refs"] if r[9] and sig(t, r[1]) == "DOOR" and ENTR.match(edid(t, r[1]))]
    doors.sort(key=lambda r: (edid(t, r[1]), r[2]))
    pick = doors[::max(1, len(doors) // 24)][:24]
    for r in pick:
        x, y, z = r[2:5]
        g = ground(t, x, y)
        ring = [ground(t, x + 1024 * math.cos(a), y + 1024 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]
        ring = [v for v in ring if v is not None]
        near = np.hypot(pos[:, 0] - x, pos[:, 1] - y) < 1500
        kinds = Counter(re.sub(r"\d+.*$", "", e) for (s, e), m in zip(stats, near) if m and not e.startswith(("XMarker", "Critter", "Collision")))
        rows.append({"door": edid(t, r[1]), "cell": r[0], "door_z_minus_ground": round(z - g) if g is not None else None,
                     "ring1024_mean_minus_door_ground": round(float(np.mean(ring) - g)) if ring and g is not None else None,
                     "ring_relief": round(float(np.ptp(ring))) if ring else None,
                     "slope_at_door": round(ground_slope(t, x, y) or -1, 1), "statics_1500": kinds.most_common(5)})
    return {"doors_with_teleport_matching": len(doors), "sample": rows,
            "summary": {"ring_minus_door": pct([r["ring1024_mean_minus_door_ground"] for r in rows if r["ring1024_mean_minus_door_ground"] is not None]),
                        "slope_at_door": pct([r["slope_at_door"] for r in rows]),
                        "door_z_minus_ground": pct([r["door_z_minus_ground"] for r in rows if r["door_z_minus_ground"] is not None])}}


# ---------- Q11 the riverbed edge's share of dry land (lane 1.15-r6-ground-roads) ----------
EDGE_LTEX = re.compile(r"riverbed\w*edge", re.I)
EDGE_NEAR_V = 16  # vertices (~29 m): the band the material's edge stop is meant to hold


def q11(t):
    """The share of dry LAND (vertex at or above its cell's water) painted with Skyrim.esm's riverbed edge LTEX
    (alpha-over weight, cell_weights), over all dry land, within EDGE_NEAR_V vertices of water and beyond it."""
    C = t["cells"]
    xs, ys = [k[0] for k in C], [k[1] for k in C]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    H, W = mosaic(t, x0, y0, x1, y1)
    E = np.zeros_like(H)
    for (x, y), c in C.items():
        if c["h"] is None:
            continue
        r, q = (y - y0) * 32, (x - x0) * 32
        for k, v in cell_weights(c).items():
            if EDGE_LTEX.search(edid(t, int(k))):
                E[r:r + 33, q:q + 33] = np.maximum(E[r:r + 33, q:q + 33], v)
    have = np.isfinite(H)
    wet = have & (H < W)
    dry = have & ~wet
    d = chamfer(wet, EDGE_NEAR_V)
    near, far = dry & (d <= EDGE_NEAR_V), dry & (d > EDGE_NEAR_V)
    names = sorted({f[1] for f in t["forms"].values() if f and f[0] == "LTEX" and EDGE_LTEX.search(f[1] or "")})
    win = []  # per 8x8-cell window with shore (>= 2000 dry vertices within 16 of water): the band of the share
    for r in range(0, H.shape[0] - 1, 256):
        for q in range(0, H.shape[1] - 1, 256):
            n = near[r:r + 256, q:q + 256]
            if n.sum() >= 2000:
                win.append(100.0 * float(E[r:r + 256, q:q + 256][n].sum()) / n.sum())  # percent
    e = float(E[dry].sum())
    return {"edge_ltex": names, "dry_vertices": int(dry.sum()),
            "edge_share_of_dry": round(e / max(1, dry.sum()), 4),
            "edge_share_of_dry_within_16v": round(float(E[near].sum()) / max(1, near.sum()), 4),
            "edge_share_of_dry_beyond_16v": round(float(E[far].sum()) / max(1, far.sum()), 4),
            "edge_within_16v_of_its_area": round(float(E[near].sum()) / max(e, 1e-9), 4),
            "dry_within_16v_share": round(float(near.sum()) / max(1, dry.sum()), 4),
            "windows": len(win), "window_pct_within_16v": pct(win, (10, 25, 50, 75, 90))}


# ---------- Q12 roads (lane 1.15-r6-ground-roads): grade, cross fall, edge walls along every road-surface mesh ----------
ROAD_SURF = re.compile(r"^Road(?!.*(Sign|Chunk|Marker))", re.I)
ROAD_GRADE_MAX = 0.219  # routes/shape.py GRADE_MAX (the r4 box's max)


def q12(t):
    """Along Tamriel's road-surface statics (Road*, no signs, chunks or markers), on the LAND under them: the grade
    over an 8 m baseline, the cross fall over +-4 m, and the edge wall test routes/shape.py's census uses (a step over
    0.3 m across the edge at 3 m out beyond the land's own step just outside), and the share within 16 m of water."""
    C = t["cells"]
    xs, ys = [k[0] for k in C], [k[1] for k in C]
    x0, y0 = min(xs), min(ys)
    H, W = mosaic(t, x0, y0, max(xs), max(ys))
    U = VERTEX_SPACING_UNITS / 128.0 * 70.0  # units per metre (1 m = 70 u)

    def at(A, xu, yu):
        c = (xu - x0 * CELL_UNITS) / VERTEX_SPACING_UNITS
        r = (yu - y0 * CELL_UNITS) / VERTEX_SPACING_UNITS
        c0, r0 = np.clip(np.floor(c).astype(int), 0, A.shape[1] - 2), np.clip(np.floor(r).astype(int), 0, A.shape[0] - 2)
        fc, fr = c - c0, r - r0
        return (A[r0, c0] * (1 - fc) * (1 - fr) + A[r0, c0 + 1] * fc * (1 - fr) + A[r0 + 1, c0] * (1 - fc) * fr
                + A[r0 + 1, c0 + 1] * fc * fr)
    P = np.array([r[2:4] for r in t["refs"] if sig(t, r[1]) == "STAT" and ROAD_SURF.match(edid(t, r[1]) or "")])
    wet = np.isfinite(H) & (H < W)
    dw = chamfer(wet, 9)  # vertices (1.83 m): within 16 m
    grade, cross, walls, nearw, steep_runs = [], [], 0, 0, 0
    for p in P:
        nb = P[np.hypot(*(P - p).T) < 40 * U]
        if len(nb) < 3:
            continue
        v = np.linalg.svd(nb - nb.mean(0))[2][0]
        n = np.array([-v[1], v[0]])
        a = at(H, p[0] + v[0] * 4 * U * np.array([-1, 1]), p[1] + v[1] * 4 * U * np.array([-1, 1])) / U
        b = at(H, p[0] + n[0] * 4 * U * np.array([-1, 1]), p[1] + n[1] * 4 * U * np.array([-1, 1])) / U
        if not (np.isfinite(a).all() and np.isfinite(b).all()):
            continue
        grade.append(abs(a[1] - a[0]) / 8.0)
        cross.append(abs(b[1] - b[0]) / 8.0)
        for sg in (1, -1):
            z = at(H, p[0] + sg * n[0] * U * np.array([2.1, 3.9, 5.7]), p[1] + sg * n[1] * U * np.array([2.1, 3.9, 5.7])) / U
            walls += int(abs(z[1] - z[0]) > 0.3 + abs(z[2] - z[1]))
        c = int((p[0] - x0 * CELL_UNITS) / VERTEX_SPACING_UNITS); r = int((p[1] - y0 * CELL_UNITS) / VERTEX_SPACING_UNITS)
        nearw += int(dw[min(max(r, 0), dw.shape[0] - 1), min(max(c, 0), dw.shape[1] - 1)] <= 9)
    g = np.array(grade)
    return {"road_meshes": int(len(P)), "measured": int(len(g)),
            "grade": pct(100 * g, (50, 90, 95, 99, 100)), "cross_fall": pct(100 * np.array(cross), (50, 90, 99, 100)),
            "share_over_grade_max": round(float((g > ROAD_GRADE_MAX).mean()), 4),
            "edge_walls_per_side_point": round(walls / max(1, 2 * len(g)), 4), "edge_walls": walls,
            "share_within_16m_of_water": round(nearw / max(1, len(g)), 4)}


QS = {f"q{i}": f for i, f in enumerate((q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12), 1)}

if __name__ == "__main__":
    t = tamriel()
    want = sys.argv[1:] or ["all"]
    for k, f in QS.items():
        if "all" in want or k in want:
            print(json.dumps({k: f(t)}, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
            sys.stdout.flush()
