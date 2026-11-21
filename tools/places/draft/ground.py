"""The place's ground carried from its source: under each house group our ground takes the group's LOCAL relief.

What a builder shaped under a house group is the ground's shape just round it: the bank a mud house is cut into,
the hollow under a stilt deck, the step between two neighbours. That, not the hill a whole town climbs, makes its
pieces sit; so the stage carries each group's local relief onto our ground and leaves the source's hill behind,
as a land patch (`by` "ground" rows of land.jsonl).

- Bodies. The fit's clusters (place.json `fit.clusters`) that share one map (pivot, to, rot) and whose pieces lie
  within 2 x MARGIN of each other make one body; a compact place is one body, a town the fit broke apart is many.
  A body's footprint is the convex hull of its carried pieces (exterior rows with a `src`) grown by MARGIN.
- Local relief. Inside a body the source's ground is read through the body's map; its trend is the plane fitted
  through the source's ground round the footprint's inner EDGE, and the relief carried is the source minus that
  plane, so a mound or hollow inside the body stays and the hill's slope across it goes. Where the pieces' own
  feet stood on a slope, the tilt they need is kept: the plane best fitting the source's ground at the body's feet
  minus the plane best fitting our ground at the same spots, limited to TILT_DEG (reported when limited).
- Limits. Each body's change is capped at CAP (place.json `draft.ground_cap` raises it); the blend round each
  footprint is no steeper than SLOPE_DEG; the change fades to nothing over WATER_FADE before our own water line
  and over one band round the source's own water, so no wall stands at a channel; our water line never moves
  (ground under it stays under, dry ground stays WATERLINE_GAP over it); nothing past the place record's radius
  changes; no vertex of a cell another place's land rows hold; `draft.ground_leave_out` names clusters whose body
  is left as our ground. Inside the footprints the change itself is never steeper than INSIDE_DEG (two bodies
  side by side whose relief differs meet in a slope, not a wall). The ground is reckoned from the ground bundle and this place's rows of other stages, not
  its own earlier rows nor the sap hollow, so a second run changes nothing; the sap stage digs on top afterwards.
- Measure. For each fit cluster, the gap at each piece between the source's ground under it and the patched
  ground, after the cluster's median offset: its median and worst, before and after. That is the stage's success.

    python -m tools.places draft ground <place_id> --dry     what the stage would do, nothing written
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from tools.places.seat import STEP, Ground

MARGIN = 256.0          # units the footprint reaches past the hull of a body's pieces
BAND_MIN = 384.0        # units: the narrowest blend band
SLOPE_DEG = 35.0        # the blend is never steeper than this
INSIDE_DEG = 45.0       # nor the change anywhere, between two bodies or across a capped rise, steeper than this
TILT_DEG = 20.0         # the most slope a body's feet carry from the source
WATER_FADE = 384.0      # units over which the change fades to nothing before our water line
CAP = 300.0             # units: the most a body's ground moves at any point
BIG_M2 = 8000.0         # a body's footprint wider than this takes a quadratic trend: across it the hill curves
UNITS_PER_M = 70.0


def hull(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Convex hull, counter-clockwise (monotone chain)."""
    p = sorted(set(pts))
    if len(p) < 3:
        return p

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], q) <= 0:
            hi.pop()
        hi.append(q)
    return lo[:-1] + hi[:-1]


def outside(poly: list[tuple[float, float]], X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Distance of each point outside the convex polygon (0 inside)."""
    if len(poly) == 1:
        return np.hypot(X - poly[0][0], Y - poly[0][1])
    d = np.full(X.shape, np.inf)
    inside = np.ones(X.shape, bool)
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L2 = ex * ex + ey * ey or 1.0
        t = np.clip(((X - ax) * ex + (Y - ay) * ey) / L2, 0, 1)
        d = np.minimum(d, np.hypot(X - ax - t * ex, Y - ay - t * ey))
        inside &= (ex * (Y - ay) - ey * (X - ax)) >= 0
    return np.where(inside, 0.0, d)


def smooth(t: np.ndarray) -> np.ndarray:
    t = np.clip(t, 0, 1)
    return 1 - t * t * (3 - 2 * t)


def grow(mask: np.ndarray, n: int) -> np.ndarray:
    """Steps (in vertices, 8-neighbour) from each vertex to the nearest True of mask, up to n (n+1 beyond)."""
    dist = np.where(mask, 0, n + 1)
    cur = mask.copy()
    for k in range(1, n + 1):
        nxt = cur.copy()
        nxt[1:, :] |= cur[:-1, :]
        nxt[:-1, :] |= cur[1:, :]
        nxt[:, 1:] |= cur[:, :-1]
        nxt[:, :-1] |= cur[:, 1:]
        nxt[1:, 1:] |= cur[:-1, :-1]
        nxt[:-1, :-1] |= cur[1:, 1:]
        nxt[1:, :-1] |= cur[:-1, 1:]
        nxt[:-1, 1:] |= cur[1:, :-1]
        dist[nxt & ~cur] = k
        cur = nxt
    return dist


def owners(gx: int, gy: int):
    """(cell, row, col) of every cell that holds global vertex (gx, gy) (shared edges belong to two or four)."""
    kx, col = divmod(gx, 32)
    ky, row = divmod(gy, 32)
    out = [((kx, ky), row, col)]
    if col == 0:
        out.append(((kx - 1, ky), row, 32))
    if row == 0:
        out.append(((kx, ky - 1), 32, col))
    if col == 0 and row == 0:
        out.append(((kx - 1, ky - 1), 32, 32))
    return out


def through(m, x, y):
    """Our (x, y) read into the source through a map (pivot, to, rot radians)."""
    pv, to, r = m[0], m[1], m[2]
    cr, sr = math.cos(r), math.sin(r)
    dx, dy = x - to[0], y - to[1]
    return pv[0] + dx * cr - dy * sr, pv[1] + dx * sr + dy * cr


def plane(x, y, z):
    """(a, b, c) of the least-squares plane z = a x + b y + c (flat at the mean when too few points)."""
    x, y, z = (np.asarray(v, float) for v in (x, y, z))
    if len(z) < 3:
        return 0.0, 0.0, float(np.mean(z)) if len(z) else 0.0
    A = np.c_[x, y, np.ones(len(z))]
    sol, *_ = np.linalg.lstsq(A, z, rcond=None)
    return float(sol[0]), float(sol[1]), float(sol[2])


def trend(x, y, z, quad: bool):
    """Coefficients of the least-squares plane (quad False) or quadratic surface through the points."""
    x, y, z = (np.asarray(v, float) for v in (x, y, z))
    x0, y0 = float(x.mean()), float(y.mean())
    u, v = (x - x0) / 1000.0, (y - y0) / 1000.0
    cols = [u, v, np.ones(len(z))] + ([u * u, u * v, v * v] if quad and len(z) >= 12 else [])
    sol, *_ = np.linalg.lstsq(np.c_[tuple(cols)], z, rcond=None)
    return x0, y0, sol


def trend_at(t, X, Y):
    x0, y0, sol = t
    u, v = (X - x0) / 1000.0, (Y - y0) / 1000.0
    out = sol[0] * u + sol[1] * v + sol[2]
    if len(sol) > 3:
        out = out + sol[3] * u * u + sol[4] * u * v + sol[5] * v * v
    return out


def slope_hold(dz: np.ndarray, free: np.ndarray, deg: float) -> np.ndarray:
    """dz with every `free` vertex brought toward zero until no slope between neighbours exceeds `deg` (vertices
    not free keep their change and set the limit round them)."""
    s = math.tan(math.radians(deg)) * STEP
    P = dz.copy()
    n = int(2 * np.max(np.abs(P)) / (s * 0.7)) + 4 if P.size else 0
    for _ in range(n):
        lo, hi = np.full(P.shape, -np.inf), np.full(P.shape, np.inf)
        for dy, dx, k in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (-1, -1, 1.414),
                          (1, -1, 1.414), (-1, 1, 1.414)):
            ys = slice(max(dy, 0), P.shape[0] + min(dy, 0))
            yd = slice(max(-dy, 0), P.shape[0] + min(-dy, 0))
            xs = slice(max(dx, 0), P.shape[1] + min(dx, 0))
            xd = slice(max(-dx, 0), P.shape[1] + min(-dx, 0))
            hi[ys, xs] = np.minimum(hi[ys, xs], P[yd, xd] + s * k)
            lo[ys, xs] = np.maximum(lo[ys, xs], P[yd, xd] - s * k)
        Q = np.where(P > 0, np.maximum(np.minimum(P, hi), 0.0), np.minimum(np.maximum(P, lo), 0.0))
        Q = np.where(free, Q, P)
        if np.array_equal(Q, P):
            break
        P = Q
    return P


def bodies(clusters: list[dict], margin: float = MARGIN) -> list[dict]:
    """Group clusters ({id, map, pts}) sharing one map and lying within 2 x margin of each other into bodies."""
    def key(m):
        return (round(m[0][0], 1), round(m[0][1], 1), round(m[1][0], 1), round(m[1][1], 1), round(m[2], 5))
    out = []
    groups: dict = {}
    for c in clusters:
        if c["pts"]:
            groups.setdefault(key(c["map"]), []).append(c)
    for cs in groups.values():
        parent = list(range(len(cs)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        P = [np.asarray(c["pts"]) for c in cs]
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                d = np.min(np.hypot(P[i][:, None, 0] - P[j][None, :, 0], P[i][:, None, 1] - P[j][None, :, 1]))
                if d <= 2 * margin:
                    parent[find(i)] = find(j)
        comp: dict = {}
        for i, c in enumerate(cs):
            comp.setdefault(find(i), []).append(c)
        for members in comp.values():
            out.append({"ids": [c["id"] for c in members], "map": members[0]["map"],
                        "pts": [tuple(p) for c in members for p in c["pts"]], "clusters": members})
    out.sort(key=lambda b: b["ids"][0])
    return out


def feet_gaps(G: Ground, src: Ground, clusters: list[dict]) -> dict:
    """Per cluster: (median, worst) |gap| between the source's ground under each piece and G under it, after the
    cluster's own median offset."""
    out = {}
    for c in clusters:
        d = []
        for x, y in c["pts"]:
            g, s = G.height(x, y), src.height(*through(c["map"], x, y))
            if g is not None and s is not None:
                d.append(s - g)
        if len(d) >= 2:
            a = np.abs(np.asarray(d) - np.median(d))
            out[c["id"]] = (float(np.median(a)), float(a.max()))
    return out


def summary(gaps: dict) -> dict:
    if not gaps:
        return {}
    med = [v[0] for v in gaps.values()]
    worst = [v[1] for v in gaps.values()]
    return {"median_of_medians": round(float(np.median(med)), 1), "median_worst": round(float(np.median(worst)), 1),
            "worst": round(float(max(worst)), 1), "clusters_worst_over_64": sum(1 for w in worst if w > 64)}


def carry(ours: Ground, src: Ground, clusters: list[dict], centre=None, radius: float | None = None,
          taken: set = frozenset(), gap: float | None = None, margin: float = MARGIN, cap: float = CAP,
          leave_out: set = frozenset()) -> tuple[list[dict], dict]:
    """(land rows `by` "ground", report) carrying each body's local relief onto `ours`. `clusters`: [{id, map:
    (source pivot, our to, rot radians), pts: [(x, y) of its carried pieces in our coordinates]}]."""
    from tools.places.draft.fit import WATERLINE_GAP
    gap = WATERLINE_GAP if gap is None else gap
    bs = bodies(clusters, margin)
    if not bs:
        return [], {"rows": 0, "why": "no carried pieces"}
    allp = np.asarray([p for b in bs for p in b["pts"]])
    reach = margin + max(BAND_MIN, cap / math.tan(math.radians(SLOPE_DEG)) + STEP) + 2 * STEP
    g0x, g1x = math.floor((allp[:, 0].min() - reach) / STEP), math.ceil((allp[:, 0].max() + reach) / STEP)
    g0y, g1y = math.floor((allp[:, 1].min() - reach) / STEP), math.ceil((allp[:, 1].max() + reach) / STEP)
    GX, GY = np.meshgrid(np.arange(g0x, g1x + 1), np.arange(g0y, g1y + 1))
    X, Y = GX * STEP, GY * STEP
    H0 = np.full(X.shape, np.nan)
    W = np.full(X.shape, np.nan)
    for i, j in np.ndindex(X.shape):
        h = ours.vertex(int(GX[i, j]), int(GY[i, j]))
        if h is None:
            continue
        H0[i, j] = h
        w = ours.water(X[i, j], Y[i, j])
        if w is not None:
            W[i, j] = w
    ourwet = ~np.isnan(W) & ~np.isnan(H0) & (H0 < W)
    nf = max(1, int(math.ceil(WATER_FADE / STEP)))
    ourfade = 1 - smooth(grow(ourwet, nf) / nf) if ourwet.any() else np.ones(X.shape)   # 0 at our water, 1 clear
    num = np.zeros(X.shape)
    wsum = np.zeros(X.shape)
    wmax = np.zeros(X.shape)
    per = []
    srcfaded = np.zeros(X.shape, bool)
    infoot = np.zeros(X.shape, bool)
    for b in bs:
        rec = {"ids": b["ids"][:3] + (["+%d" % (len(b["ids"]) - 3)] if len(b["ids"]) > 3 else []),
               "pieces": len(b["pts"])}
        if leave_out & set(b["ids"]):
            per.append({**rec, "left_out": True})
            continue
        poly = hull(b["pts"])
        D = outside(poly, X, Y) - margin
        near = D < reach - margin
        ii, jj = np.nonzero(near)
        HS = np.full(X.shape, np.nan)
        SW = np.zeros(X.shape, bool)
        for i, j in zip(ii, jj):
            sx, sy = through(b["map"], X[i, j], Y[i, j])
            hs = src.height(sx, sy)
            if hs is None:
                continue
            HS[i, j] = hs
            sw = src.water(sx, sy)
            SW[i, j] = sw is not None and hs < sw
        core = (D <= 0) & ~np.isnan(HS) & ~np.isnan(H0)
        infoot |= D <= 0
        if not core.any():
            per.append({**rec, "why": "no source ground"})
            continue
        ring = core & (D > -3 * STEP) & ~SW
        if ring.sum() < 4:
            ring = core & ~SW if (core & ~SW).sum() >= 3 else core
        area = float((D <= 0).sum()) * (STEP / UNITS_PER_M) ** 2
        te = plane(X[ring], Y[ring], HS[ring])                     # the trend: the source's surface at the edge
        tq = trend(X[ring], Y[ring], HS[ring], area > BIG_M2)
        rec["trend"] = "quadratic" if len(tq[2]) > 3 else "plane"
        R = HS - trend_at(tq, X, Y)
        R = R - float(np.median(R[ring]))
        # the tilt the feet need: the source's plane at the feet minus ours there
        fx = np.asarray([p[0] for p in b["pts"]])
        fy = np.asarray([p[1] for p in b["pts"]])
        fs = [src.height(*through(b["map"], x, y)) for x, y in b["pts"]]
        fo = [ours.height(x, y) for x, y in b["pts"]]
        ok = np.asarray([s is not None and o is not None for s, o in zip(fs, fo)])
        wa = wb = ra = rb = 0.0            # the slope the feet need (source minus ours); what the residual holds
        if ok.sum() >= 3 and (np.ptp(fx[ok]) > STEP or np.ptp(fy[ok]) > STEP):
            ps = plane(fx[ok], fy[ok], [s for s, k in zip(fs, ok) if k])
            po = plane(fx[ok], fy[ok], [o for o, k in zip(fo, ok) if k])
            wa, wb = ps[0] - po[0], ps[1] - po[1]
            ra, rb = ps[0] - te[0], ps[1] - te[1]
        t = math.hypot(wa, wb)
        lim = math.tan(math.radians(TILT_DEG))
        rec["tilt_deg"] = round(math.degrees(math.atan(t)), 1)
        if t > lim:
            wa, wb = wa * lim / t, wb * lim / t
            rec["tilt_limited_to"] = TILT_DEG
        ta, tb = wa - ra, wb - rb
        cx, cy = float(fx.mean()), float(fy.mean())
        d = R + ta * (X - cx) + tb * (Y - cy)
        d = d - float(np.median(d[ring]))
        need = np.abs(d[core & ~SW])
        rec["capped_share"] = round(float((need > cap).mean()), 3) if need.size else 0.0
        rec["need_p50_p90_max"] = [round(float(np.percentile(need, q))) for q in (50, 90, 100)] if need.size else []
        d = np.clip(np.nan_to_num(d), -cap, cap)
        edge = float(np.abs(d[(D <= 0) & (D > -2 * STEP)]).max()) if ((D <= 0) & (D > -2 * STEP)).any() else 0.0
        band = max(BAND_MIN, edge / math.tan(math.radians(SLOPE_DEG)) * 1.6 + STEP)
        band = min(band, reach - margin - STEP)
        wet = SW & ~np.isnan(HS)
        nfd = max(1, int(math.ceil(band / STEP)))
        fade = smooth(grow(wet, nfd) / nfd) if wet.any() else np.zeros(X.shape)
        srcfaded |= (fade > 0.01) & (D <= 0)
        wt = smooth(D / band) * (1 - fade)
        wt = np.where(np.isnan(HS), 0.0, wt)
        nw = wt / ((D + margin) ** 2 + margin ** 2) ** 2     # bodies mix by nearness to their own pieces
        num += nw * d
        wsum += nw
        wmax = np.maximum(wmax, wt)
        rec.update(band=round(band), max_change=round(float(np.abs(d[core]).max()), 1),
                   area_m2=round(float((D <= 0).sum()) * (STEP / UNITS_PER_M) ** 2))
        per.append(rec)
    dz = np.where(wsum > 0, num / np.where(wsum > 0, wsum, 1), 0.0) * wmax * ourfade
    if centre is not None and radius is not None:
        dz = np.where(np.hypot(X - centre[0], Y - centre[1]) <= radius, dz, 0.0)
    # no blend steeper than SLOPE_DEG: outside the footprints, and near our water inside them, the change is
    # brought down until it is not; our water itself takes none
    dz = np.where(ourwet, 0.0, dz)
    dz = slope_hold(dz, np.ones(dz.shape, bool), INSIDE_DEG - 2)
    dz = slope_hold(dz, ~infoot | (ourfade < 0.999), SLOPE_DEG - 2)
    newh = H0 + dz
    under = ~np.isnan(W) & (H0 < W)
    dry = ~np.isnan(W) & ~(H0 < W)
    newh = np.where(under, np.minimum(newh, np.maximum(H0, W - gap)), newh)
    newh = np.where(dry, np.maximum(newh, np.minimum(H0, W + gap)), newh)
    dz = np.round(np.where(np.isnan(H0), 0.0, newh - H0), 1)
    cells: dict[tuple, dict] = {}
    skipped = 0
    for i, j in zip(*np.nonzero(np.abs(dz) >= 1.0)):
        own = owners(int(GX[i, j]), int(GY[i, j]))
        if any(k in taken for k, _, _ in own):
            skipped += 1
            continue
        for k, r_, c_ in own:
            if k in ours.cells:
                cells.setdefault(k, {})[(r_, c_)] = float(dz[i, j])
    rows = [{"cell": list(k), "verts": [[r, c_, v] for (r, c_), v in sorted(vs.items())],
             "why": "the source's local ground carried under its house groups", "by": "ground"}
            for k, vs in sorted(cells.items())]

    def slope(h):
        ny, nx = np.gradient(np.where(np.isnan(h), 0, h), STEP)
        return np.degrees(np.arctan(np.hypot(nx, ny)))
    moved = np.abs(dz) >= 1.0
    sl, was = slope(H0 + dz), slope(H0)
    dsl = slope(dz)                                     # the slope the change itself makes
    steeper = moved & (sl > was + 0.5) & ~np.isnan(H0) & ~infoot & (dsl > 5)   # the blend, outside every footprint
    G1 = Ground({k: list(v) for k, v in ours.cells.items()}, ours.water_by_cell, ours.default_water)
    G1.apply_patches(rows)
    before, after = feet_gaps(ours, src, clusters), feet_gaps(G1, src, clusters)
    a = (STEP / UNITS_PER_M) ** 2
    rep = {"rows": len(rows), "bodies": len(bs), "bodies_patched": sum(1 for p in per if "max_change" in p),
           "clusters": len(clusters), "vertices": int(moved.sum()),
           "largest_change": round(float(np.abs(dz).max()), 1) if dz.size else 0.0,
           "raised_max": round(float(dz.max()), 1), "lowered_max": round(float(-dz.min()), 1),
           "capped_share_max": max((p.get("capped_share", 0) for p in per), default=0),
           "bodies_capped_over_10pct": sum(1 for p in per if p.get("capped_share", 0) > 0.1),
           "tilts_limited": sum(1 for p in per if "tilt_limited_to" in p),
           "steepest_inside_deg": round(float(sl[moved & infoot].max()), 1) if (moved & infoot).any() else 0.0,
           "steepest_blend_deg": round(float(sl[steeper].max()), 1) if steeper.any() else 0.0,
           "steepest_blend_at": [round(float(X[steeper][np.argmax(sl[steeper])])),
                                round(float(Y[steeper][np.argmax(sl[steeper])]))] if steeper.any() else None,
           "change_steepest_blend_deg": round(float(dsl[moved & ~infoot].max()), 1) if (moved & ~infoot).any() else 0.0,
           "steeper_than_35_m2": round(float((steeper & (sl > SLOPE_DEG + 0.5)).sum()) * a),
           "faded_for_our_water_m2": round(float(((ourfade < 0.99) & (wmax > 0.01)).sum()) * a),
           "faded_for_source_water_m2": round(float(srcfaded.sum()) * a),
           "taken_skipped": skipped,
           "feet_before": summary(before), "feet_after": summary(after),
           "per_body": per, "feet_per_cluster": {k: [round(before[k][0]), round(before[k][1]),
                                                     round(after[k][0]), round(after[k][1])]
                                                 for k in sorted(after) if k in before}}
    return rows, rep


def plan(st, other_places: Path | None = None) -> tuple[list[dict], dict]:
    """The ground rows for a Standing place, and the report."""
    from tools.places.draft import io
    fit = st.place.get("fit") or {}
    if not fit.get("anchor"):
        return [], {"rows": 0, "why": "the place has no fit"}
    G0 = Ground.load(st.grd.path)
    G0.apply_patches([r for r in st.files["land"] if r.get("by") not in ("ground", "sap")])
    taken = set()
    root = other_places or io.PLACES
    for d in sorted(Path(root).glob("*/land.jsonl")):
        if d.parent.name == st.place_id:
            continue
        taken |= {tuple(r["cell"]) for r in io.read_jsonl(d)}
    centre = radius = None
    try:
        from tools.places.extract import load_place
        rec = load_place(st.place_id)
        if rec.get("world_x") is not None and st.place.get("radius_m"):
            centre, radius = (float(rec["world_x"]), float(rec["world_y"])), float(st.place["radius_m"]) * UNITS_PER_M
    except (KeyError, FileNotFoundError):
        pass
    main_rot = math.radians(float(fit.get("rot_deg", 0.0)))
    main = (fit["pivot"], fit["anchor"], main_rot)
    byc: dict = {}
    for r in st.ext:
        if r.get("src"):
            byc.setdefault(r.get("cluster"), []).append((float(r["pos"][0]), float(r["pos"][1])))
    clusters = []
    for cid, pts in sorted(byc.items(), key=lambda kv: str(kv[0])):
        cf = (fit.get("clusters") or {}).get(cid) or {}
        m = (cf["pivot"], cf["to"], float(cf.get("rot", main_rot))) if cf.get("pivot") and cf.get("to") else main
        clusters.append({"id": str(cid), "map": m, "pts": pts})
    dr = st.place.get("draft") or {}
    cap = float(dr.get("ground_cap") or CAP)
    rows, rep = carry(G0, st.S, clusters, centre, radius, taken, cap=cap,
                      leave_out=set(dr.get("ground_leave_out") or []))
    rep["cap"] = cap
    return rows, rep


def apply(st, log=print, dry: bool = False) -> dict:
    rows, rep = plan(st)
    for k, v in rep.items():
        if k not in ("per_body", "feet_per_cluster"):
            log(f"draft ground {st.place_id}: {k} {v}")
    for p in rep.get("per_body", []):
        log(f"draft ground {st.place_id}: body {p}")
    if dry:
        return rep
    st.files["land"][:] = [r for r in st.files["land"] if r.get("by") != "ground"] + rows
    st.G = Ground.load(st.grd.path)
    st.G.apply_patches(st.files["land"])
    log(f"draft ground {st.place_id}: {len(rows)} cells patched; run `draft sap {st.place_id}` again for the hollow")
    return rep
