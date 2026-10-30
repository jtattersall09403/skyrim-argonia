"""The designed still water (2.W2; the owner's ruling of 2026-10-29: the water is designed, nothing falls back).

Every body of the hydrology graph has one designed outcome (`water_body_design`):
  sea        the open sea: the worldspace default water at 0;
  own-level  lakes, lagoons, tarns and plunge pools: one level each, the body's own;
  basin      still water (STILL: marsh, swamp, backswamp, mudflat, ponds, pools) stands in a basin at one level;
  dropped    a puddle, a film or ground that stands above the body's level: no water, by design, with its reason.

Basins (`water_basin`). The still-water samples of the field (the bodies' and the raster's water no body owns) are
cut into patches (4-connected samples of one owner at one level). Touching patches join, closest levels first,
while the basin's levels stay within BASIN_SPREAD_M (a marsh stepping down a slope stays several terraces). A basin
stands at one designed level: the sample-weighted median of its patches' levels, or the lower quartile, or its
lowest level, the first whose shore does not spill: its ground below the level is water, its ground above it is
marsh ground, and the water spreads over connected lower dry ground at most GROW_SAMPLES deep; a level whose spread
is still growing there would end in a wall over lower ground, so the next lower level is taken.
The closed dry hollows below its level near it fill too (the water table), so a marsh cell stands at one cell water
height. A basin smaller than the graph's pond minimum (`pondMinM2`), shallower than FILM_DEPTH_M at its deepest or
narrower than RIBBON_SAMPLES on average (a ribbon of water along a shore), or that no body owns and that touches
another basin (a fragment of the raster beside a marsh at another level) is dropped, unless a river reach runs into
or through one of its bodies; the drops are made first, so a kept basin's shore may spread over a dropped one's
ground.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from tools.argonia_world.water import field as wfield
from tools.argonia_world.water.model import Graph
from tools.argonia_world.water.oriented import BERM_MAX_M

STILL = {"marsh-fringe", "marsh-deep", "swamp", "backswamp", "mudflat", "pond", "pool"}
BASIN_SPREAD_M = 1.5  # a basin's patches' levels lie within this: one marsh, one level; a taller terrace is another
GROW_SAMPLES = 4  # a basin's water spreads at most this many samples over connected lower dry ground
FILM_DEPTH_M = 0.15  # a basin no deeper than this at its deepest is a film
RIBBON_SAMPLES = 2.5  # a basin narrower than this on average (2 x area / perimeter) is a ribbon at a shore
QUANTILES = (0.5, 0.25, 0.0)  # the designed level's candidates, highest first
SPILL_ITERS = 12  # the spill level's bisection (to about a centimetre on a basin up to 40 m deep)
_CODE_OFF = 1 << 20


@dataclass
class Basin:
    id: str
    level_m: float
    samples: int  # its water samples after the design
    area_m2: float  # its still-water samples before the design
    depth_m: float
    patches: int
    level_rule: str  # median | lower-quartile | lowest
    outcome: str  # kept | dropped
    reason: str | None
    owner: int  # the field's owner index its water takes (its largest body), -1 none


@dataclass
class Design:
    basins: list[Basin] = field(default_factory=list)
    body: dict = field(default_factory=dict)  # body id -> (outcome, basin id or None, reason or None)
    dried: int = 0  # still-water samples above their basin's level (marsh ground by design)
    grown: int = 0  # samples the basins' shores spread over
    dips: int = 0  # closed dry hollows below a basin's level its water table fills
    dropped_samples: int = 0
    spilled: list = field(default_factory=list)  # basins whose lowest level still spills (walls, counted)


def label(key: np.ndarray) -> np.ndarray:
    """4-connected components of equal non-negative keys (-1 elsewhere), numbered in row-major order of their first
    sample: horizontal runs joined across rows by a union-find over the runs."""
    valid = key >= 0
    start = valid.copy()
    start[:, 1:] &= ~(valid[:, :-1] & (key[:, 1:] == key[:, :-1]))
    run = (np.cumsum(start, dtype=np.int32) - 1).reshape(key.shape)
    nr = int(start.sum())
    if nr == 0:
        return np.full(key.shape, -1, dtype=np.int32)
    m = valid[:-1] & (key[:-1] == key[1:])
    pairs = np.unique(run[:-1][m].astype(np.int64) * nr + run[1:][m])
    del m
    par = list(range(nr))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for p in pairs.tolist():
        a, b = find(p // nr), find(p % nr)
        if a != b:
            par[max(a, b)] = min(a, b)
    roots = np.fromiter((find(i) for i in range(nr)), dtype=np.int64, count=nr)
    _, comp = np.unique(roots, return_inverse=True)
    return np.where(valid, comp.astype(np.int32)[run], -1).astype(np.int32)


def _dilate(m: np.ndarray) -> np.ndarray:
    g = m.copy()
    g[1:] |= m[:-1]
    g[:-1] |= m[1:]
    g[:, 1:] |= m[:, :-1]
    g[:, :-1] |= m[:, 1:]
    return g


def _grow(inb: np.ndarray, gw: np.ndarray, dry_free: np.ndarray, L: float):
    """A basin's water at L: its own ground below L, spread GROW_SAMPLES deep over connected lower dry ground; and
    whether it would spread further over ground lower than a berm can close (a spill)."""
    free = dry_free & (gw < L)
    grown = inb & (gw < L)
    for _ in range(GROW_SAMPLES):
        step = _dilate(grown) & free & ~grown
        if not step.any():
            break
        grown |= step
    return grown, bool((_dilate(grown) & free & ~grown & (gw < L - BERM_MAX_M)).any())


def _dips(level: np.ndarray, gw: np.ndarray, L: float) -> np.ndarray:
    """Dry hollows below L in a basin's window that are closed (not on the window's edge, not beside lower water):
    the basin's water table fills them, so its cells stand at one level."""
    low = np.isnan(level) & (gw < L)
    if not low.any():
        return low
    lab = label(np.where(low, 0, -1).astype(np.int64))
    bad = np.zeros(int(lab.max()) + 1, dtype=bool)
    for edge in (lab[0], lab[-1], lab[:, 0], lab[:, -1]):
        bad[edge[edge >= 0]] = True
    with np.errstate(invalid="ignore"):
        lower = ~np.isnan(level) & (level < L - 0.0051)
    near = _dilate(lower) & (lab >= 0)
    bad[lab[near]] = True
    return (lab >= 0) & ~bad[np.maximum(lab, 0)]


def _river_bodies(g: Graph) -> set:
    out = {r.body for r in g.reaches.values() if r.body} | \
        {r.fall_plunge_body for r in g.reaches.values() if r.fall_plunge_body}
    return out | {b.id for b in g.bodies.values() if b.caused_by_fall}


def design(g: Graph, f: wfield.Field, ground: np.ndarray) -> Design:
    """Decide every basin and body outcome on this field and apply it to the field in place."""
    n = ground.shape[0]
    nb = len(g.bodies)
    body_ids = f.owners[:nb]
    still_owner = np.array([g.bodies[o].kind in STILL for o in body_ids] + [False] * (len(f.owners) - nb))
    wet = ~np.isnan(f.level)
    code = np.zeros((n, n), dtype=np.int64)
    code[wet] = np.rint(f.level[wet] * 100).astype(np.int64)
    own = f.owner
    # a body whose every sample another body already holds at the same level shares that body's water (field step
    # 2): it takes that body's outcome
    pos = {o: i for i, o in enumerate(body_ids)}
    shares: dict = {}
    ownf = own.ravel()
    for bid_, idx in f.body_samples.items():
        if bid_ in pos and idx.size:
            o = ownf[idx]
            if not (o == pos[bid_]).any() and (o >= 0).any():
                shares[bid_] = body_ids[int(np.bincount(o[o >= 0]).argmax())]
    unowned_still = (own < 0) & ((f.source == 2) | (f.source == 5))
    still = wet & (code != 0) & (np.where(own >= 0, still_owner[np.maximum(own, 0)], False) | unowned_still)
    key = np.where(own >= 0, own.astype(np.int64), len(f.owners)) * (2 * _CODE_OFF) + (code + _CODE_OFF)
    key[~still] = -1
    del code
    lab = label(key)
    del key
    flat = np.flatnonzero(lab.ravel() >= 0)
    pl = lab.ravel()[flat]
    npatch = int(pl.max()) + 1 if pl.size else 0
    cnt = np.bincount(pl, minlength=npatch)
    lvl = np.zeros(npatch, dtype=np.float64)
    lvl[pl] = f.level.ravel()[flat]
    gmin = np.full(npatch, np.inf)
    np.minimum.at(gmin, pl, np.asarray(ground).ravel()[flat])
    p_owner = np.full(npatch, -1, dtype=np.int64)
    p_owner[pl] = own.ravel()[flat]
    # touching patches, closest levels first, while the basin's spread holds
    pairs = set()
    for a, b in ((lab[:, :-1], lab[:, 1:]), (lab[:-1], lab[1:])):
        m = (a >= 0) & (b >= 0) & (a != b)
        e = np.unique(np.minimum(a[m], b[m]).astype(np.int64) * npatch + np.maximum(a[m], b[m]))
        pairs.update(e.tolist())
    par = list(range(npatch))
    lo, hi = lvl.copy(), lvl.copy()

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for p in sorted(pairs, key=lambda p: (abs(lvl[p // npatch] - lvl[p % npatch]), p)):
        a, b = find(p // npatch), find(p % npatch)
        if a != b and max(hi[a], hi[b]) - min(lo[a], lo[b]) <= BASIN_SPREAD_M + 1e-9:
            r, s = min(a, b), max(a, b)
            par[s] = r
            lo[r], hi[r] = min(lo[r], lo[s]), max(hi[r], hi[s])
    root = np.fromiter((find(i) for i in range(npatch)), dtype=np.int64, count=npatch)
    roots, binv = np.unique(root, return_inverse=True)
    touches = np.zeros(len(roots), dtype=bool)  # a basin that touches another basin
    for p in pairs:
        a, b = binv[p // npatch], binv[p % npatch]
        if a != b:
            touches[a] = touches[b] = True
    bl = np.full(n * n, -1, dtype=np.int32)
    bl[flat] = binv[pl]
    bl = bl.reshape(n, n)
    del lab
    river = _river_bodies(g)
    pond_min = g.thresholds.get("pondMinM2", 500.0)
    out = Design()
    best: dict = {}  # body id -> (samples in the basin, -basin index): a body split over basins takes its largest
    rows, cols = np.divmod(flat, n)
    bsel = binv[pl]
    order = np.argsort(bsel, kind="stable")
    bounds = np.searchsorted(bsel[order], np.arange(len(roots) + 1))
    perim = np.zeros(len(roots), dtype=np.int64)  # 4-neighbour edges from a basin's samples to anything else
    for a, b in ((bl[:, :-1], bl[:, 1:]), (bl[:, 1:], bl[:, :-1]), (bl[:-1], bl[1:]), (bl[1:], bl[:-1])):
        m = (a >= 0) & (a != b)
        perim += np.bincount(a[m], minlength=len(roots))
    kept = []
    for k in range(len(roots)):
        mem = np.flatnonzero(binv == k)
        sel = order[bounds[k]:bounds[k + 1]]
        first = int(flat[sel].min())
        bid = f"basin.{first % n}-{first // n}"
        w = cnt[mem]
        levels = lvl[mem]
        bodies = sorted({body_ids[o] for o in p_owner[mem].tolist() if 0 <= o < nb})
        by_body: dict = {}
        for o, c in zip(p_owner[mem].tolist(), w.tolist()):
            if 0 <= o < nb:
                by_body[o] = by_body.get(o, 0) + c
        owner = max(sorted(by_body), key=lambda o: by_body[o]) if by_body else -1
        samples = int(w.sum())
        area = samples * wfield.MPP ** 2
        depth = float((levels.max() - gmin[mem].min()))
        fed = any(b in river for b in bodies)
        reason = None
        if not fed and area < pond_min:
            reason = f"a puddle: {area:.0f} m2 under the pond minimum {pond_min:.0f} m2"
        elif not fed and depth < FILM_DEPTH_M:
            reason = f"a film: {depth:.2f} m deep at its deepest, under {FILM_DEPTH_M} m"
        elif not by_body and touches[k]:
            reason = "a fragment: the raster's water no body owns, beside a basin at another level"
        elif not fed and 2 * samples / max(1, perim[k]) < RIBBON_SAMPLES:
            reason = (f"a ribbon: {2 * samples / max(1, perim[k]) * wfield.MPP:.1f} m wide on average, under "
                      f"{RIBBON_SAMPLES * wfield.MPP:.1f} m")
        r0, r1 = int(rows[sel].min()), int(rows[sel].max()) + 1
        c0, c1 = int(cols[sel].min()), int(cols[sel].max()) + 1
        if reason:
            win = (slice(r0, r1), slice(c0, c1))
            m = bl[win] == k
            _dry(f, win, m)
            out.dropped_samples += int(m.sum())
            out.basins.append(Basin(bid, float(np.median(levels)), 0, area, depth, len(mem), "median", "dropped",
                                    reason, owner))
            _assign(out, best, by_body, body_ids, k, ("dropped", bid, None))
            continue
        kept.append((k, mem, bid, w, levels, by_body, owner, samples, area, depth, r0, r1, c0, c1))
    # the kept basins' levels, once every drop is dry (a kept basin's shore may spread over a dropped one's ground)
    for k, mem, bid, w, levels, by_body, owner, samples, area, depth, r0, r1, c0, c1 in kept:
        srt = np.argsort(levels, kind="stable")
        cum = np.cumsum(w[srt]) / samples
        g0 = GROW_SAMPLES + 1
        R0, R1, C0, C1 = max(0, r0 - g0), min(n, r1 + g0), max(0, c0 - g0), min(n, c1 + g0)
        win = (slice(R0, R1), slice(C0, C1))
        inb = bl[win] == k
        gw = np.asarray(ground[win])
        dry_free = np.isnan(f.level[win]) & ~inb
        chosen = None
        for q, rule in zip(QUANTILES, ("median", "lower-quartile", "lowest")):
            L = float(levels[srt][min(len(srt) - 1, int(np.searchsorted(cum, q, side="left")))]) if q > 0 \
                else float(levels.min())
            grown, spill = _grow(inb, gw, dry_free, L)
            if not spill:
                chosen = (L, rule, grown)
                break
        if chosen is None:  # the spill level: the highest level under the lowest whose shore holds
            lo_l, hi_l = float(gmin[mem].min()), float(levels.min())
            best_l = None
            for _ in range(SPILL_ITERS):
                mid = round((lo_l + hi_l) / 2, 2)
                grown, spill = _grow(inb, gw, dry_free, mid)
                if spill:
                    hi_l = mid
                else:
                    lo_l, best_l = mid, (mid, grown)
                if hi_l - lo_l < 0.015:
                    break
            if best_l is not None and best_l[0] - float(gmin[mem].min()) >= FILM_DEPTH_M:
                chosen = (best_l[0], "spill", best_l[1])
            else:
                m = inb
                _dry(f, win, m)
                out.dropped_samples += int(m.sum())
                reason = "no pool: its shore spills below a film's depth"
                out.basins.append(Basin(bid, float(np.median(levels)), 0, area, depth, len(mem), "median",
                                        "dropped", reason, owner))
                _assign(out, best, by_body, body_ids, k, ("dropped", bid, None))
                continue
        L, rule, grown = chosen
        if rule == "spill":
            out.spilled.append(bid)
        t = np.bincount(f.wtype[win][inb], minlength=len(wfield.WATER_TYPES)).argmax()
        dried = inb & ~grown
        out.dried += int(dried.sum())
        out.grown += int((grown & ~inb).sum())
        _dry(f, win, dried)
        f.level[win][grown] = np.float32(L)
        f.wtype[win][grown] = t
        f.owner[win][grown] = owner
        f.source[win][grown & ~inb] = 5
        dips = _dips(f.level[win], gw, L)
        f.level[win][dips] = np.float32(L)
        f.wtype[win][dips] = t
        f.owner[win][dips] = owner
        f.source[win][dips] = 5
        out.dips += int(dips.sum())
        grown |= dips
        out.basins.append(Basin(bid, L, int(grown.sum()), area, depth, len(mem), rule, "kept", None, owner))
        _assign(out, best, by_body, body_ids, k, ("basin", bid, None))
    del bl
    # dry ground below 0 stands under the default water: water at 0 (field step 6, again after the drops)
    hollow = np.isnan(f.level) & (np.asarray(ground) < 0)
    f.level[hollow] = 0.0
    f.wtype[hollow] = wfield.WATER_TYPES.index("brackish")
    f.source[hollow] = 6
    for b in g.bodies.values():
        if b.id in out.body:
            continue
        if b.kind == "ocean":
            out.body[b.id] = ("sea", None, None)
        elif b.lost_at_carve:
            out.body[b.id] = ("dropped", None, "the graph records it lost at the carve")
        elif b.realised_by and b.realised_by in g.bodies:
            out.body[b.id] = ("own-level", None, f"realised by {b.realised_by} (the graph)")
        elif b.id in shares:
            continue  # after every other body
        elif abs(b.level_m) <= 0.005:
            out.body[b.id] = ("sea", None, "at sea level: the worldspace default water")
        else:
            idx = f.body_samples.get(b.id)
            gr = np.asarray(ground).ravel()
            if idx is None or not idx.size or not (gr[idx] < b.level_m - 0.0051).any():
                out.body[b.id] = ("dropped", None, "its ground stands above its level everywhere")
            else:
                out.body[b.id] = ("own-level", None, None)
    for b_id, other in shares.items():
        if b_id not in out.body:
            outcome, basin, reason = out.body[other]
            out.body[b_id] = (outcome, basin, f"it shares the water of {other}" + (f": {reason}" if reason else ""))
    return out


def _assign(out: Design, best: dict, by_body: dict, body_ids: list, k: int, outcome: tuple) -> None:
    for o, c in by_body.items():
        b = body_ids[o]
        if (c, -k) > best.get(b, (-1, 0)):
            best[b] = (c, -k)
            out.body[b] = outcome


def _dry(f: wfield.Field, win, m: np.ndarray) -> None:
    f.level[win][m] = np.nan
    f.wtype[win][m] = wfield.DRY
    f.source[win][m] = 0
    f.owner[win][m] = -1


def rows(d: Design) -> dict:
    """The design's rows for the world db."""
    basins = [{"id": b.id, "level_m": round(b.level_m, 2), "samples": b.samples, "area_m2": round(b.area_m2, 1),
               "depth_m": round(b.depth_m, 2), "patches": b.patches, "level_rule": b.level_rule,
               "outcome": b.outcome, "reason": b.reason} for b in sorted(d.basins, key=lambda b: b.id)]
    bodies = [{"body_id": k, "outcome": v[0], "basin_id": v[1], "reason": v[2]} for k, v in sorted(d.body.items())]
    return {"water_basin": basins, "water_body_design": bodies}
