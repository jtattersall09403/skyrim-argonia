"""The place's ground carried from its source: inside the place's footprint our ground takes the source's relief.

The source's builder shaped the land under the town and built on it; a town set on ground of another shape sinks
through its decks and floats off its mounds. So the ground under a place's footprint is reshaped to what the source
stood on, as a land patch (`by` "ground" rows of land.jsonl) blended into our ground at the footprint's edge.

- The source's ground is the source bundle's own exterior land (its LAND heights and water per cell: Ground.load of
  the src bundle). The map from source to ours is the fit's main transform (place.json `fit`: pivot, anchor,
  rot_deg) and each cluster's own map beside it: a vertex reads the source through every cluster's map, weighted by
  its nearness to that cluster's pieces, so a cluster the fit shifted apart from the main body still stands on the
  relief it stood on (the stage names each and its shift).
- The footprint is the convex hull of the source pieces carried over (exterior rows with a `src`), grown by MARGIN;
  the band round it is BAND_MIN wide or wider, so that the blend makes no slope steeper than the source's own
  steepest inside the footprint or SLOPE_DEG, whichever is steeper, and never steeper than SLOPE_MAX; nothing
  reaches past the place record's radius. A cluster the fit set apart has a footprint of its own (its own hull) and
  its own levels (the medians of our ground and the source's under its own pieces), so it carries the relief round
  itself and neither the gap between it and the main body nor the source's ground at another height is brought.
- The target at a vertex is our reference level plus the source's relief there (the source height minus the
  source's reference level); each reference level is the median of that ground round the footprint's inner edge
  (the anchor and the pivot when the edge holds too little dry ground), so a mound stays a mound and the edge
  meets our ground with the least to blend; the change is that target minus our ground, times the
  blend weight (1 in the footprint, a smoothstep down to 0 across the band).
- Limits: no change larger than CAP (or place.json `draft.ground_cap`; the report gives the share of the dry
  footprint the cap held and the change needed at its 50th, 90th and 99th percentiles); no point carried across our water line (ground under our water stays under,
  dry ground stays WATERLINE_GAP over it); the source's water is not brought: where the source's ground lay under its
  own water the change fades to nothing (the area is reported: pieces that stood in water there need a decision);
  no vertex of a cell another place's land rows hold. The ground is reckoned from the ground bundle and this place's
  rows of other stages but neither its own earlier rows nor the sap hollow, so a second run changes nothing; the sap
  stage's hollow goes on top of it afterwards.

    python -m tools.places draft ground <place_id> --dry     what the stage would do, nothing written
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from tools.places.seat import STEP, Ground

MARGIN = 256.0          # units the footprint reaches past the hull of the carried pieces
BAND_MIN = 512.0        # units: the narrowest blend band
SLOPE_DEG = 35.0        # the blend is never steeper than this unless the source's own ground is
SLOPE_MAX = 45.0        # nor ever steeper than this: a source's sea wall or cliff does not make a cliff at our edge
CAP = 600.0             # units: the most the ground moves at any point
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


def carry(ours: Ground, src: Ground, pivot, anchor, rot_deg: float, pieces: list[tuple[float, float]],
          centre=None, radius: float | None = None, taken: set = frozenset(), gap: float | None = None,
          margin: float = MARGIN, cap: float = CAP, maps: list | None = None) -> tuple[list[dict], dict]:
    """(land rows `by` "ground", report) carrying src's relief under `pieces` (our coordinates) onto `ours`. `maps`:
    [(pivot, to, rot radians, centre in ours[, its pieces in ours, set apart])] per cluster; a vertex reads the source
    through each, weighted by nearness to the cluster's pieces (its centre when none are given; the main map alone
    when no maps); a cluster set apart gets its own footprint and levels."""
    from tools.places.draft.fit import WATERLINE_GAP
    gap = WATERLINE_GAP if gap is None else gap
    rep = {"rows": 0}
    poly = hull(pieces)
    if not poly:
        return [], {**rep, "why": "no carried pieces"}
    rot = math.radians(rot_deg)
    our_ref, src_ref = ours.height(*anchor), src.height(*pivot)
    if our_ref is None or src_ref is None:
        return [], {**rep, "why": "no ground at the anchor or the pivot"}

    def grid(reach):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        g0x, g1x = math.floor((min(xs) - reach) / STEP), math.ceil((max(xs) + reach) / STEP)
        g0y, g1y = math.floor((min(ys) - reach) / STEP), math.ceil((max(ys) + reach) / STEP)
        GX, GY = np.meshgrid(np.arange(g0x, g1x + 1), np.arange(g0y, g1y + 1))
        return GX, GY

    ms = maps or [(pivot, anchor, rot, anchor)]
    own = [(m[4] if len(m) > 4 else None, bool(m[5]) if len(m) > 5 else False) for m in ms]
    apart_pts = {tuple(p) for (pts, ap) in own if ap and pts for p in pts}
    main_pts = [p for p in pieces if tuple(p) not in apart_pts]
    polys = ([hull(main_pts)] if main_pts else []) + [hull(pts) for (pts, ap) in own if ap and pts]

    def foot(X, Y):
        """Distance outside the footprint: the main body's hull and each set-apart cluster's own, so the gaps
        between clusters the fit set apart are not carried."""
        return np.minimum.reduce([outside(q, X, Y) for q in polys]) if apart_pts else outside(poly, X, Y)

    def through(m, x, y):
        pv, to, r = m[0], m[1], m[2]
        cr, sr = math.cos(r), math.sin(r)
        dx, dy = x - to[0], y - to[1]
        return pv[0] + dx * cr - dy * sr, pv[1] + dx * sr + dy * cr

    def sample(GX, GY):
        X, Y = GX * STEP, GY * STEP
        HSm, SWm, Wm = [], [], []
        for m, (pts, ap) in zip(ms, own):
            ctr = m[3]
            SX, SY = through(m, X, Y)
            if len(ms) == 1:
                wt_ = np.ones(X.shape)
            else:
                d2 = outside(hull(pts), X, Y) ** 2 if pts else (X - ctr[0]) ** 2 + (Y - ctr[1]) ** 2
                wt_ = 1.0 / (d2 + 512.0 ** 2) ** 2
            hs_, sw_ = np.full(X.shape, np.nan), np.zeros(X.shape, bool)
            for i, j in np.ndindex(X.shape):
                hs = src.height(SX[i, j], SY[i, j])
                if hs is None:
                    continue
                hs_[i, j] = hs
                sw = src.water(SX[i, j], SY[i, j])
                sw_[i, j] = sw is not None and hs < sw
            HSm.append(hs_)
            SWm.append(sw_)
            Wm.append(np.where(np.isnan(hs_), 0.0, wt_))
        wsum = np.sum(Wm, axis=0)
        wet = np.sum([w * s for w, s in zip(Wm, SWm)], axis=0)
        SW = (wsum > 0) & (wet > 0.5 * wsum)
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
        return X, Y, H0, HSm, Wm, W, SW

    def blend(HSm, Wm, offs):
        """The source's height as read through every map, each map's reading shifted by its own offset."""
        num = np.zeros(HSm[0].shape)
        ws = np.zeros(HSm[0].shape)
        for hs_, w_, o in zip(HSm, Wm, offs):
            num += np.where(w_ > 0, w_ * (np.nan_to_num(hs_) + o), 0.0)
            ws += w_
        return np.where(ws > 0, num / np.where(ws > 0, ws, 1), np.nan)

    reach0 = margin + BAND_MIN
    GX, GY = grid(reach0 + 4096)
    X, Y, H0, HSm, Wm, W, SW = sample(GX, GY)
    D = foot(X, Y) - margin                              # <= 0: in the footprint
    # the reference levels: the median of each ground round the footprint's edge (dry source ground), so the
    # source's mound becomes a mound on ours and the patch meets our ground with the least to blend; read through
    # the maps of the main body (a cluster set apart takes its own levels below)
    main_w = [w if not ap else np.zeros(w.shape) for w, (_, ap) in zip(Wm, own)]
    HSn = blend(HSm, main_w if any(w.any() for w in main_w) else Wm, [0.0] * len(ms))
    HSn = np.where(np.isnan(H0), np.nan, HSn)
    ring = (D <= 0) & (D > -3 * STEP) & ~np.isnan(HSn) & ~np.isnan(H0) & ~SW
    if ring.sum() >= 8:
        our_ref, src_ref = float(np.median(H0[ring])), float(np.median(HSn[ring]))
        rep.update(our_ref=round(our_ref, 1), src_ref=round(src_ref, 1), ref="the footprint's edge")
    else:
        rep["ref"] = "the anchor"
    # a cluster the fit set apart carries the relief round itself: its own levels are the medians of our ground and
    # of the source's ground under its own pieces, so the source's ground far below or above the main body's
    # (another hill, another shore) is not brought to it
    offs = []
    for m, (pts, ap) in zip(ms, own):
        if not (ap and pts):
            offs.append(0.0)
            continue
        oh = [h for h in (ours.height(x, y) for x, y in pts) if h is not None]
        sh = [h for h in (src.height(*through(m, x, y)) for x, y in pts) if h is not None]
        offs.append((float(np.median(oh)) - our_ref) - (float(np.median(sh)) - src_ref) if oh and sh else 0.0)
    rep["clusters_own_levels"] = sum(1 for (pts, ap) in own if ap and pts)
    HS = np.where(np.isnan(H0), np.nan, blend(HSm, Wm, offs))
    # the source's steepest inside the footprint sets the band's slope limit
    core = (D <= 0) & ~np.isnan(HS)
    gy_, gx_ = np.gradient(np.where(np.isnan(HS), 0, HS), STEP)
    src_steep = float(np.degrees(np.arctan(np.hypot(gx_, gy_)[core & ~SW].max()))) if (core & ~SW).any() else 0.0
    limit = min(max(SLOPE_DEG, src_steep), SLOPE_MAX)
    rep.update(src_steepest_deg=round(src_steep, 1), slope_limit_deg=round(limit, 1))
    target = our_ref + (HS - src_ref)
    delta = np.clip(np.where(np.isnan(HS) | np.isnan(H0), 0.0, target - H0), -cap, cap)
    need = np.abs(np.where(np.isnan(HS) | np.isnan(H0), 0, target - H0))
    dry_core = (D <= 0) & ~SW
    rep["capped"] = int((need > cap)[dry_core].sum())            # on the source's dry ground (its water fades out)
    rep["capped_share"] = round(float((need > cap)[dry_core].mean()), 3) if dry_core.any() else 0.0
    rep["needed_p50_p90_p99"] = [round(float(np.percentile(need[dry_core], q))) for q in (50, 90, 99)] if dry_core.any() else []
    edge = float(np.abs(delta[(D <= 0) & (D > -2 * STEP)]).max()) if ((D <= 0) & (D > -2 * STEP)).any() else 0.0
    band = max(BAND_MIN, 1.5 * edge / math.tan(math.radians(limit)) + STEP)
    if band + margin + 0 > 4096 + reach0 - margin:
        band = 4096 + reach0 - 2 * margin
    # the source's water fades out over one band
    wet = SW & ~np.isnan(HS)
    nfade = max(1, int(math.ceil(band / STEP)))
    fade = smooth(grow(wet, nfade) / nfade) if wet.any() else np.zeros(X.shape)
    wt = smooth(D / band) * (1 - fade)
    if centre is not None and radius is not None:
        wt = np.where(np.hypot(X - centre[0], Y - centre[1]) <= radius, wt, 0.0)
    dz = delta * wt
    # our water line
    newh = H0 + dz
    under = ~np.isnan(W) & (H0 < W)
    dry = ~np.isnan(W) & ~(H0 < W)
    newh = np.where(under, np.minimum(newh, np.maximum(H0, W - gap)), newh)
    newh = np.where(dry, np.maximum(newh, np.minimum(H0, W + gap)), newh)
    dz = np.round(np.where(np.isnan(H0), 0.0, newh - H0), 1)
    rep["held_by_water"] = int((np.abs(dz - np.round(delta * wt, 1)) > 0.5).sum())
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
             "why": "the source's ground carried under the place", "by": "ground"} for k, vs in sorted(cells.items())]
    moved = np.abs(dz) >= 1.0
    # the slope the patch made, where it changed the ground
    def slope(h):
        ny, nx = np.gradient(np.where(np.isnan(h), 0, h), STEP)
        return np.degrees(np.arctan(np.hypot(nx, ny)))
    sl, was = slope(H0 + dz), slope(H0)
    ring = moved & (D > 0) & (sl > was + 0.5)      # where the blend made the ground steeper than it was
    rep.update(rows=len(rows), cells=len(rows), vertices=int(moved.sum()), band=round(band, 0),
               footprint_area_m2=round(float((D <= 0).sum()) * (STEP / UNITS_PER_M) ** 2),
               raised_max=round(float(dz.max()), 1), lowered_max=round(float(-dz.min()), 1),
               relief=[round(float(np.nanmin(HS[core]) - src_ref), 1), round(float(np.nanmax(HS[core]) - src_ref), 1)]
               if core.any() else None,
               source_water_area_m2=round(float((wet & (D <= 0)).sum()) * (STEP / UNITS_PER_M) ** 2),
               band_steepest_deg=round(float(sl[ring].max()), 1) if ring.any() else 0.0,
               band_steeper_than_limit_m2=round(float((ring & (sl > limit + 0.5)).sum()) * (STEP / UNITS_PER_M) ** 2),
               band_steepest_at=[round(float(X[ring][np.argmax(sl[ring])])), round(float(Y[ring][np.argmax(sl[ring])]))]
               if ring.any() else None,
               taken_skipped=skipped, hull=[[round(x), round(y)] for x, y in poly])
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
    pieces = [(float(r["pos"][0]), float(r["pos"][1])) for r in st.ext if r.get("src")]
    centre = radius = None
    try:
        from tools.places.extract import load_place
        rec = load_place(st.place_id)
        if rec.get("world_x") is not None and st.place.get("radius_m"):
            centre, radius = (float(rec["world_x"]), float(rec["world_y"])), float(st.place["radius_m"]) * UNITS_PER_M
    except (KeyError, FileNotFoundError):
        pass
    # each cluster reads the source through its own map from the fit, so a cluster the fit set apart stands on the
    # relief it stood on; between clusters the reading blends by nearness to each cluster's centre
    maps, apart = [], []
    main_rot = math.radians(float(fit.get("rot_deg", 0.0)))
    for cid, cf in sorted((fit.get("clusters") or {}).items()):
        mine = [(float(r["pos"][0]), float(r["pos"][1])) for r in st.ext if r.get("src") and r.get("cluster") == cid]
        if not mine or not cf.get("pivot") or not cf.get("to"):
            continue
        ctr = (sum(p[0] for p in mine) / len(mine), sum(p[1] for p in mine) / len(mine))
        sh = math.dist(cf["to"], fit["anchor"]) if cf["pivot"] == fit.get("pivot") else 0.0
        ap = sh > 1 or abs(float(cf.get("rot", main_rot)) - main_rot) > 1e-4
        maps.append((cf["pivot"], cf["to"], float(cf.get("rot", main_rot)), ctr, mine, ap))
        if ap:
            apart.append({"cluster": cid, "shift": round(sh), "on": "its own map and levels"})
    cap = float((st.place.get("draft") or {}).get("ground_cap") or CAP)
    rows, rep = carry(G0, st.S, fit["pivot"], fit["anchor"], float(fit.get("rot_deg", 0.0)), pieces,
                      centre, radius, taken, maps=maps or None, cap=cap)
    rep["cap"] = cap
    rep["clusters_apart"] = apart
    return rows, rep


def apply(st, log=print, dry: bool = False) -> dict:
    rows, rep = plan(st)
    for k, v in rep.items():
        if k != "hull":
            log(f"draft ground {st.place_id}: {k} {v}")
    if dry:
        return rep
    st.files["land"][:] = [r for r in st.files["land"] if r.get("by") != "ground"] + rows
    st.G = Ground.load(st.grd.path)
    st.G.apply_patches(st.files["land"])
    log(f"draft ground {st.place_id}: {len(rows)} cells patched; run `draft sap {st.place_id}` again for the hollow")
    return rep
