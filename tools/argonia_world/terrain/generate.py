"""The province ground, generated (1.15 §b; decision 0033 §2): `out/terrain/ground-f32.npy`, the (4033, 4033)
float32 metres grid of grid.py, row 0 north, plus `cliff-u8.npy` (the cliff mask: designed slope past the limit,
for placed cliff meshes), `role-u8.npy` (what each sample was made to be: the fit check reads it) and
`entrance-sites.json`.

Order (each step vectorised over the whole grid; the arrays are 65 MB each):
1. the prior: All-Tamriel's province window (`apron-source-near.npy` [PAD, PAD + 4033)), low-passed at ~100 m
   wavelength (three box passes, sigma 13 samples = 24 m), which also removes its 1-unit terraces;
2. relief per region (RELIEF_ECO x RELIEF_CULTURE -> `region_relief` rows, each with its dossier line): the prior
   scaled into the region's floor..summit band of height above the local water base, the bands blended across
   region borders (sigma 2 cells), the N/NW border ranges raised to the border band, light erosion (a blend toward
   the blurred ground by the region's erosion) and noise by the region's roughness away from water;
3. the water base: the level of the nearest water (cell levels, filled outward on the cell grid, blurred): the land
   stands on its water, so an upland tarn sits in uplands (water first);
4. road corridors flattened across and smoothed along (the traced roads, routes/build.py's widths);
5. the water constraints: inside the wet footprint (the wet raster in a water cell, or the cell's own low ground
   where the raster has none) the bed below the lowest level of the cells sharing the vertex, by the shore grade per
   water type down to the body's depth; every other vertex of a water cell above the highest level sharing it; the
   shore rising from the water at the type's grade; at each step the vanilla join (options §11): the channel's bed
   through the edge STEP_BED_M under the upper water, sloping inside the lower cell to below the lower water over
   1-5 vertices, the banks closed above the upper water elsewhere;
6. entrance sites shaped (one per dungeon record);
7. the slope held under DESIGN_SLOPE_DEG by an L1-Lipschitz limit inside the constraint cones (quantize.py's
   method in metres), so the int8 limiter never moves a province vertex.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain.cellwater import C, CX0, CY0, N, Q, TYPES, CellWater

MPP = su.PROVINCE_SAMPLE_M
OUT = Path(__file__).resolve().parents[3] / "out" / "terrain"
PRIOR_SIGMA = 13  # samples (24 m): a Gaussian at this sigma passes < 1 % of a 100 m wavelength... and keeps 300 m
PRIOR_TOP_M = 120.0  # the prior's land summit (raw -86..122 m): u = prior / this, clipped 0..1
BLEND_CELLS = 2.0  # sigma of the region-parameter blend across borders
DESIGN_SLOPE_DEG = 75.0  # every 4-neighbour step at most tan(75) x 1.83 m = 6.8 m (the int8 limit is 82.9 deg)
CLIFF_DEG = 60.0  # designed slope past this is a cliff-mesh site (cliff-u8.npy)
STEP_BED_M = 200 / su.UNITS_PER_METRE  # options §11: the bed crosses the edge 100-300 units (median 224) under the upper water
FREEBOARD_M = 0.3  # a bank stands this far above its water; a bed at least this far below
SHORE_FAR = 40  # samples: the shore grade reaches this far from the water
# shore grade (rise per metre) by water type: the mangrove coast flat, the upland tarn steep
# (docs/design/research/world-terrain/tropical-fluvial-geomorphology.md: "Tidal creeks ... depth 0.5-2 m", the lagoon
#  behind its barrier; mountain-terrain-synthesis.md: "cliff bands ... knickpoint waterfalls" for upland water)
SHORE_GRADE = {"sea": 0.03, "brackish": 0.04, "blackwater": 0.08, "fresh": 0.35}
BED_GRADE = {"sea": 0.03, "brackish": 0.05, "blackwater": 0.1, "fresh": 0.4}
DEPTH_M = {"sea": 6.0, "brackish": 1.5, "blackwater": 1.5, "fresh": 3.0}

# ---- relief per region (the region_relief rows): the one numeric anchor is world-rebuild-options.md:109
# "border mountains to perhaps 300 m, uplands 60 to 150 m, foothills, a marsh floor under 10 m"; heights are above
# the local water base. eco class -> (floor_m, summit_m, roughness_m, cliff_share, erosion, why)
RELIEF_ECO = {
    "deep-river-corridor": (0.5, 30.0, 1.5, 0.10, 0.70, "tropical-fluvial-geomorphology.md:43 'cut banks (outer bend, steep, 1-3 m), levees'"),
    "tidal-delta": (0.3, 4.0, 0.4, 0.0, 0.30, "tropical-fluvial-geomorphology.md:117 'Tidal creeks... depth 0.5-2 m'"),
    "coastal-lagoon": (0.3, 8.0, 0.5, 0.02, 0.25, "tropical-fluvial-geomorphology.md:132 'Lagoon... behind coastal barrier'; options §8 'a drowned coast'"),
    "deep-sink-basin": (0.3, 10.0, 0.5, 0.0, 0.15, "tropical-fluvial-geomorphology.md:75 'Domed peat rising 1-8 m'; world-rebuild-options.md:109 'a marsh floor under 10 m'"),
    "flooded-forest": (0.3, 10.0, 0.6, 0.0, 0.20, "tropical-fluvial-geomorphology.md:72 'hummock-and-hollow micro-relief'; world-rebuild-options.md:109"),
    "interior-swamp": (0.5, 15.0, 0.8, 0.02, 0.25, "mountain-terrain-synthesis.md:78 'marsh and floodplain -> smooth strongly'; world-rebuild-options.md:109"),
    "rootland": (2.0, 60.0, 3.0, 0.10, 0.40, "mountain-terrain-synthesis.md:80 'rolling firm lowland/upland -> gentle 20-80 m undulation'; world-rebuild-options.md:109 'uplands 60 to 150 m'"),
    "northern-transition": (5.0, 90.0, 5.0, 0.10, 0.45, "black-marsh-climatology.md:25 'slopes down from the interior uplands of the north'; black-marsh-province.md:64 'The north is not swamp'"),
    "western-frontier": (5.0, 150.0, 8.0, 0.25, 0.55, "blackwood-and-gloommire.md:13 'steep, lightly forested hills to the west'; world-rebuild-options.md:109"),
}
# culture region -> (summit x, floor +m, roughness x, cliff +, why)
RELIEF_CULTURE = {
    "dunmer-north": (1.6, 5.0, 1.5, 0.15, "shadowfen.md:84 'Relief exists here and only here: waterfall, mountain flank, ravines'"),
    "imperial-fringe": (1.3, 3.0, 1.3, 0.10, "blackwood-and-gloommire.md:13-14 'flooded hillscape... steep, lightly forested hills'"),
    "hist-heartland": (1.0, 0.0, 0.8, 0.0, "extrapolated: middle-argonia.md has no relief words; the low interior (options §8)"),
    "naga-kur-deeps": (0.8, -0.2, 0.7, 0.0, "extrapolated: no relief lore; the low interior (options §8)"),
    "mercantile-coast": (0.9, 0.0, 1.0, 0.05, "murkmire.md:61 'rocky cliffs over Oliis Bay'; black-marsh-climatology.md:25 'fades into the ocean'"),
    "imperial-penal-south": (1.0, 0.0, 1.0, 0.0, "extrapolated: no relief lore; the south is the lowest land"),
    "pirate-freeholds": (1.0, 0.0, 1.0, 0.05, "extrapolated: Leafwater is eastern Shadowfen (shadowfen.md:16), a mild raise"),
    "saxhleel-coast": (0.9, 0.0, 1.0, 0.05, "tropical-fluvial-geomorphology.md:106 'Rocky cove / cliff where mountain spurs reach the sea'"),
}
# the N/NW border ranges (canon: options §8; shadowfen.md:11 'Borders Morrowind to the north and Cyrodiil to the west')
BORDER_RANGE = (40.0, 300.0, 1500.0, "world-rebuild-options.md:109 'border mountains to perhaps 300 m'; mountain-terrain-synthesis.md:28 'border ranges W/NW... canon'")
BORDER_CULTURES = ("dunmer-north", "imperial-fringe")
SHAPES = {"cave-mouth": "mound", "burrow": "mound", "grave-cut": "mound", "root-mouth": "mound", "hollow-trunk": "flat",
          "sinkhole-lip": "depression", "underwater-entry": "deep_water", "door": "flat", "gate": "flat",
          "stair-throat": "flat", "cellar-door": "flat", "trapdoor": "flat", "well-shaft": "flat", "none": "flat"}
SITE_MIN_R = 12.0
MOUND_M, DEPRESSION_M, DEEP_M = 6.0, 4.0, 3.0  # options §9: a mound or bank for a mouth, a sinkhole, a deep cell
BANK_WATER_M = 40.0  # a mouth within this of water is cut into the bank, not a mound


def relief_rows(world) -> list[dict]:
    """One row per land region: the band of height above the local water, roughness, cliff share, erosion, why."""
    rows = []
    for r in world.query("SELECT id, region_id, eco_class_id FROM land_region ORDER BY id"):
        if r["eco_class_id"] not in RELIEF_ECO:
            continue
        f, s, rough, cliff, ero, why_e = RELIEF_ECO[r["eco_class_id"]]
        sm, fa, rm, ca, why_c = RELIEF_CULTURE.get(r["region_id"], (1.0, 0.0, 1.0, 0.0, "extrapolated"))
        rows.append({"land_region_id": r["id"], "floor_m": round(max(f + fa, 0.2), 2), "summit_m": round(s * sm, 1),
                     "roughness_m": round(rough * rm, 2), "cliff_share": round(min(cliff + ca, 1.0), 2),
                     "erosion": ero, "why": f"{why_e}; {why_c}"})
    return rows


# ---- numpy helpers --------------------------------------------------------------------------------------------
def box(a: np.ndarray, r: int, axis: int) -> np.ndarray:
    a = np.moveaxis(a, axis, 0)
    p = np.concatenate([a[r:0:-1], a, a[-2:-r - 2:-1]], 0) if r else a
    c = np.cumsum(p, 0, dtype=np.float64)
    c = np.concatenate([np.zeros((1,) + c.shape[1:]), c], 0)
    out = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
    return np.moveaxis(out, 0, axis)


def blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian of `sigma` samples by three box passes per axis (reflected edges)."""
    r = max(0, int(round(math.sqrt(12 * sigma * sigma / 3 + 1) - 1) // 2))
    out = np.asarray(a, np.float64)
    for ax in (0, 1):
        for _ in range(3):
            out = box(out, r, ax)
    return out


def nanblur(a: np.ndarray, sigma: float) -> np.ndarray:
    w = ~np.isnan(a)
    num = blur(np.where(w, a, 0.0), sigma)
    den = blur(w.astype(np.float64), sigma)
    with np.errstate(invalid="ignore", divide="ignore"):
        return num / den


def upsample(cell: np.ndarray) -> np.ndarray:
    """(126, 126) cell values at cell centres -> (4033, 4033) bilinear."""
    t = (np.arange(N + 1) - Q / 2) / Q
    i0 = np.clip(np.floor(t).astype(int), 0, C - 2)
    f = np.clip(t - i0, 0, 1)
    rows = cell[i0] * (1 - f)[:, None] + cell[i0 + 1] * f[:, None]
    return rows[:, i0] * (1 - f)[None] + rows[:, i0 + 1] * f[None]


def fill_nearest(cell: np.ndarray) -> np.ndarray:
    """NaN cells take the value of the nearest valued cell (8-neighbour dilation until full)."""
    a = cell.copy()
    while np.isnan(a).any():
        p = np.pad(a, 1, constant_values=np.nan)
        nb = np.stack([p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx]
                       for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx])
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            m = np.nanmean(nb, 0)
        hole = np.isnan(a) & ~np.isnan(m)
        if not hole.any():
            break
        a[hole] = m[hole]
    return a


def chamfer(src: np.ndarray, far: int, val: np.ndarray | None = None):
    """Distance in samples (8-neighbour chamfer, capped at `far`) from the True samples of `src`, and the value of
    `val` carried from the nearest source sample."""
    d = np.where(src, 0.0, np.inf)
    v = None if val is None else np.where(src, val, np.nan)
    s2 = math.sqrt(2)
    for _ in range(far):
        changed = False
        for dy, dx, w in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, s2), (1, -1, s2), (-1, 1, s2), (-1, -1, s2)):
            sh = np.full_like(d, np.inf)
            ys, yd = (slice(0, -dy), slice(dy, None)) if dy > 0 else (slice(-dy, None), slice(0, dy or None))
            xs, xd = (slice(0, -dx), slice(dx, None)) if dx > 0 else (slice(-dx, None), slice(0, dx or None))
            sh[yd, xd] = d[ys, xs] + w
            better = sh < d
            if better.any():
                changed = True
                d[better] = sh[better]
                if v is not None:
                    vs = np.full_like(v, np.nan)
                    vs[yd, xd] = v[ys, xs]
                    v[better] = vs[better]
        if not changed:
            break
    d[d > far] = np.inf
    return d, v


def vertex_levels(level: np.ndarray):
    """Per sample: the lowest and highest level of the water cells sharing the vertex (NaN when none has water)."""
    i = np.arange(N + 1)
    lo_c, hi_c = np.clip((i - 1) // Q, 0, C - 1), np.clip(i // Q, 0, C - 1)
    stack = np.stack([level[a][:, b] for a in (lo_c, hi_c) for b in (lo_c, hi_c)])
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmin(stack, 0), np.nanmax(stack, 0)


def _sweep(a: np.ndarray, op, lip: float, axis: int) -> np.ndarray:
    a = np.moveaxis(a, axis, 0)
    s = 1.0 if op is np.minimum else -1.0
    for i in range(1, a.shape[0]):
        op(a[i], a[i - 1] + s * lip, out=a[i])
    for i in range(a.shape[0] - 2, -1, -1):
        op(a[i], a[i + 1] + s * lip, out=a[i])
    return np.moveaxis(a, 0, axis)


def minorant(a, lip):
    return _sweep(_sweep(a.copy(), np.minimum, lip, 1), np.minimum, lip, 0)


def majorant(a, lip):
    return _sweep(_sweep(a.copy(), np.maximum, lip, 1), np.maximum, lip, 0)


def limit(h: np.ndarray, lo: np.ndarray, hi: np.ndarray, lip: float) -> tuple[np.ndarray, np.ndarray]:
    """h held lip-Lipschitz (4-neighbour) inside the cones of the bounds lo <= h <= hi; returns (f, steep) where
    steep marks the samples the limit moved (the designed cliffs)."""
    a, b = majorant(np.where(np.isfinite(lo), lo, -1e9), lip), minorant(np.where(np.isfinite(hi), hi, 1e9), lip)
    m = (minorant(h, lip) + majorant(h, lip)) / 2  # the L-infinity-closest lip-Lipschitz ground
    f = np.minimum(np.maximum(m, a), np.maximum(b, a))
    return f, np.abs(f - h) > 0.05


# ---- the generator -------------------------------------------------------------------------------------------
@dataclass
class Inputs:
    prior: np.ndarray  # (4033, 4033) raw metres
    region: np.ndarray  # (126, 126) land_region index into rows, -1 none
    rows: list[dict]
    culture: list[str]  # per row
    water: CellWater
    wet_level: np.ndarray  # (4033, 4033) the wet raster's level (NaN dry)
    roads: list[tuple[np.ndarray, float]]  # (points (k, 2) as (col, row) samples, half flat width + shoulder in samples)
    sites: list[dict]  # dungeon records: place_id, x_m, y_m, radius_m, entrance, water_m, request

    @classmethod
    def load(cls, world=None) -> Inputs:
        from tools.argonia_world import db
        from tools.argonia_world.terrain import cellwater
        from tools.argonia_world.terrain.grid import PAD, data_root

        w = world if world is not None else db.open()
        a = np.load(data_root() / "terrain" / "apron-source-near.npy", mmap_mode="r")
        prior = np.asarray(a[PAD:PAD + N + 1, PAD:PAD + N + 1], np.float32)
        rows = relief_rows(w)
        idx = {r["land_region_id"]: i for i, r in enumerate(rows)}
        cult = {r["id"]: r["region_id"] for r in w.query("SELECT id, region_id FROM land_region")}
        region = np.full((C, C), -1, np.int32)
        for r in w.query("SELECT * FROM cell_region_run"):
            i = C - 1 - (r["cy"] - CY0)
            if 0 <= i < C and r["land_region_id"] in idx:
                region[i, max(r["cx0"] - CX0, 0):min(r["cx1"] - CX0 + 1, C)] = idx[r["land_region_id"]]
        water = cellwater.load(w)
        wet_level, _ = cellwater.wet_raster(w)
        roads = []
        pts: dict[str, list] = {}
        for p in w.query("SELECT route_id, x_m, y_m FROM road_point ORDER BY route_id, ord"):
            pts.setdefault(p["route_id"], []).append((p["x_m"] / MPP, p["y_m"] / MPP))
        for r in w.query("SELECT route_id, flat_width_m, shoulder_m FROM road"):
            if len(pts.get(r["route_id"], [])) >= 2:
                roads.append((np.asarray(pts[r["route_id"]]), (r["flat_width_m"] / 2 + r["shoulder_m"]) / MPP))
        sites = [{"place_id": p["id"], "x_m": p["position_m_x"], "y_m": p["position_m_y"],
                  "radius_m": max(p["footprint_radius_m"] or 0.0, SITE_MIN_R), "entrance": p["entrance"] or "none",
                  "water_m": p["plot_facts_distance_to_water_m"]}
                 for p in w.query("SELECT * FROM place WHERE interior_kind IS NOT NULL AND position_m_x IS NOT NULL ORDER BY id")]
        reqs = {}
        for q in w.query("SELECT place_id, kind FROM place_terrain_requests ORDER BY place_id, ord"):
            reqs.setdefault(q["place_id"], q["kind"])
        for s in sites:
            s["request"] = reqs.get(s["place_id"])
        return cls(prior, region, rows, [cult[r["land_region_id"]] for r in rows], water, wet_level, roads, sites)


def stamp_polyline(mask_val: np.ndarray, pts: np.ndarray, rad: float, value=True) -> None:
    seg = np.diff(pts, axis=0)
    ln = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(ln)])
    t = np.linspace(0, cum[-1], max(2, int(cum[-1]) + 1))
    cx, cy = np.interp(t, cum, pts[:, 0]), np.interp(t, cum, pts[:, 1])
    r = int(math.ceil(rad))
    oy, ox = np.mgrid[-r:r + 1, -r:r + 1]
    m = oy * oy + ox * ox <= rad * rad
    rr = (np.rint(cy)[:, None] + oy[m][None]).astype(int).ravel()
    cc = (np.rint(cx)[:, None] + ox[m][None]).astype(int).ravel()
    ok = (rr >= 0) & (rr <= N) & (cc >= 0) & (cc <= N)
    mask_val[rr[ok], cc[ok]] = value


def generate(inp: Inputs, log=print) -> dict:
    t0 = time.time()
    st: dict = {}
    lip = math.tan(math.radians(DESIGN_SLOPE_DEG)) * MPP

    # 1. the prior, low-passed
    lp = blur(inp.prior, PRIOR_SIGMA)
    st["prior"] = {"raw_m": [round(float(inp.prior.min()), 2), round(float(inp.prior.max()), 2)],
                   "removed_rms_m": round(float(np.sqrt(np.mean((inp.prior - lp) ** 2))), 3),
                   "removed_max_m": round(float(np.abs(inp.prior - lp).max()), 2),
                   "flat_share_raw": round(float((np.diff(inp.prior, axis=1) == 0).mean()), 3),
                   "flat_share_lp": round(float((np.abs(np.diff(lp, axis=1)) < 1e-4).mean()), 3)}
    log(f"prior {time.time() - t0:.1f}s")

    # 2. relief bands per region, blended
    def param(key, default):
        v = np.array([r[key] for r in inp.rows] + [default], np.float64)
        return upsample(blur(v[inp.region], BLEND_CELLS))

    floor, summit = param("floor_m", 0.5), param("summit_m", 10.0)
    rough, ero = param("roughness_m", 0.5), param("erosion", 0.3)
    bord = np.array([c in BORDER_CULTURES for c in inp.culture] + [False], np.float64)
    bw = upsample(blur(bord[inp.region], BLEND_CELLS))
    ii, jj = np.mgrid[0:N + 1, 0:N + 1]
    dist_nw = np.minimum(ii, jj) * MPP
    t = np.clip(1 - dist_nw / BORDER_RANGE[2], 0, 1)
    rng = bw * t * t * (3 - 2 * t)  # 1 at the N/NW border inside the border cultures, 0 a band's width in
    summit = summit + (BORDER_RANGE[1] - summit) * rng
    floor = floor + (BORDER_RANGE[0] - floor) * rng
    u = np.clip(lp / PRIOR_TOP_M, 0, 1) ** 1.2
    relief = floor + (summit - floor) * u
    del ii, jj, dist_nw, t
    log(f"relief {time.time() - t0:.1f}s")

    # 3. the water base and the footprint
    wl = inp.water.level
    base = nanblur(upsample(blur(fill_nearest(wl), 1.0)), 32)
    vmin, vmax = vertex_levels(wl)
    has = ~np.isnan(vmin)
    foot = has & ~np.isnan(inp.wet_level)
    # a water cell the raster leaves dry takes its own low ground (the prior's lowest third of the cell)
    pre = base + relief
    blocks = foot[:N, :N].reshape(C, Q, C, Q).any(axis=(1, 3))
    empty = ~np.isnan(wl) & ~blocks
    if empty.any():
        cell_pre = pre[:N, :N].reshape(C, Q, C, Q)
        q = np.quantile(cell_pre.transpose(0, 2, 1, 3).reshape(C, C, -1), 0.33, axis=-1)
        thr = np.pad(np.repeat(np.repeat(np.where(empty, q, -np.inf), Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge")
        foot |= has & (pre <= thr)
    st["water"] = {"source": inp.water.source, "cells": int((~np.isnan(wl)).sum()), "steps": len(inp.water.steps),
                   "empty_cells_flooded": int(empty.sum()), "footprint_samples": int(foot.sum())}
    log(f"water base {time.time() - t0:.1f}s")

    # noise by roughness, away from water; erosion as a blend toward the blurred ground
    rs = np.random.default_rng(1150)
    noise = np.zeros((N + 1, N + 1))
    for k, amp in ((C // 2, 1.0), (C * 2, 0.5), (C * 8, 0.25)):
        g = rs.standard_normal((k + 2, k + 2))
        t = np.linspace(0, k, N + 1)
        i0 = np.floor(t).astype(int)
        f = t - i0
        rows_ = g[i0] * (1 - f)[:, None] + g[i0 + 1] * f[:, None]
        noise += amp * (rows_[:, i0] * (1 - f)[None] + rows_[:, i0 + 1] * f[None])
    dwet, near_lvl = chamfer(foot, SHORE_FAR, np.where(foot, vmin, np.nan))
    away = np.clip(np.where(np.isfinite(dwet), dwet, SHORE_FAR) / SHORE_FAR, 0, 1)
    h = base + relief + noise * rough * away
    h = h * (1 - 0.5 * ero) + blur(h, 4) * 0.5 * ero
    del noise
    log(f"noise+erosion {time.time() - t0:.1f}s")

    # 4. roads: flat across, smooth along
    road = np.zeros((N + 1, N + 1), bool)
    for pts, rad in inp.roads:
        stamp_polyline(road, pts, rad)
    if road.any():
        hs = blur(h, 8)
        wroad = blur(road.astype(np.float64), 2)
        h = h * (1 - wroad) + hs * wroad
    st["roads"] = {"roads": len(inp.roads), "samples": int(road.sum())}

    # 5. water constraints
    wtype = np.full((C, C), "", object)
    for i, n in enumerate(TYPES):
        wtype[inp.water.wtype == i] = n
    tsamp = np.pad(np.repeat(np.repeat(inp.water.wtype, Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge")
    sg = np.zeros((N + 1, N + 1))
    bg = np.zeros((N + 1, N + 1))
    dp = np.zeros((N + 1, N + 1))
    for i, n in enumerate(TYPES):
        sg[tsamp == i], bg[tsamp == i], dp[tsamp == i] = SHORE_GRADE[n], BED_GRADE[n], DEPTH_M[n]
    din, _ = chamfer(~foot & np.ones_like(foot), 64)
    din = np.where(foot, np.minimum(np.where(np.isfinite(din), din, 64), 64), 0)
    lo = np.full((N + 1, N + 1), -np.inf)
    hi = np.full((N + 1, N + 1), np.inf)
    role = np.zeros((N + 1, N + 1), np.uint8)  # 0 dry, 1 wet, 2 step slope, 3 bank of a water cell, 4 shore
    bed = vmin - np.minimum(FREEBOARD_M + bg * din * MPP, np.maximum(dp, FREEBOARD_M + 0.2))
    hi[foot] = np.minimum(vmin[foot] - FREEBOARD_M, bed[foot] + 0.0)
    h[foot] = np.minimum(h[foot], bed[foot])
    bank = has & ~foot
    lo[bank] = vmax[bank] + FREEBOARD_M
    role[foot], role[bank] = 1, 3
    shore = ~has & np.isfinite(dwet) & ~foot
    shore_lo = near_lvl + FREEBOARD_M + sg * np.where(np.isfinite(dwet), dwet, 0) * MPP
    lo[shore] = np.maximum(lo[shore], shore_lo[shore])
    role[shore] = 4
    # steps: the vanilla join
    nstep = 0
    for s in inp.water.steps:
        r_north = (C - 1 - (s.cy - CY0)) * Q
        c_west = (s.cx - CX0) * Q
        if s.cross_lo < 0:
            continue
        drop = s.upper_m - s.lower_m
        k = int(min(5, max(1, math.ceil(drop / lip))))
        edge_bed = s.upper_m - STEP_BED_M
        end_bed = s.lower_m - FREEBOARD_M - 0.2
        j = np.arange(s.cross_lo, s.cross_hi + 1)
        for kk in range(0, k + 1):
            z = edge_bed + (end_bed - edge_bed) * kk / k
            if s.edge in ("e", "w"):
                col = c_west + (Q + kk if s.edge == "e" else -kk)
                rows_ = r_north + Q - j
                if not 0 <= col <= N:
                    continue
                sel = (rows_, np.full_like(rows_, col))
            else:
                row = r_north + (-kk if s.edge == "n" else Q + kk)
                if not 0 <= row <= N:
                    continue
                cols = c_west + j
                sel = (np.full_like(cols, row), cols)
            h[sel] = z
            lo[sel] = -np.inf
            hi[sel] = z + 0.01
            role[sel] = np.where(z < vmin[sel] - 1e-3, 1, 2)
        nstep += 1
    st["steps_joined"] = nstep
    h = np.minimum(np.maximum(h, lo), hi)
    log(f"constraints {time.time() - t0:.1f}s")

    # 6. entrance sites
    sites = shape_sites(h, lo, hi, role, inp)
    st["sites"] = {k: sum(s["shape"] == k for s in sites) for k in ("mound", "bank", "depression", "flat", "deep_water")}

    # 7. the slope limit inside the cones
    gy, gx = np.gradient(h, MPP)
    cliff = np.degrees(np.arctan(np.hypot(gx, gy))) > CLIFF_DEG
    f, moved = limit(h, lo, hi, lip)
    cliff |= moved
    st["slope"] = {"design_deg": DESIGN_SLOPE_DEG, "moved_samples": int(moved.sum()), "cliff_samples": int(cliff.sum()),
                   "max_step_m": round(float(max(np.abs(np.diff(f, axis=0)).max(), np.abs(np.diff(f, axis=1)).max())), 3)}
    st["ground_m"] = [round(float(f.min()), 2), round(float(f.max()), 2)]
    st["seconds"] = round(time.time() - t0, 1)
    log(f"limit {time.time() - t0:.1f}s")
    return {"ground": f.astype(np.float32), "cliff": cliff.astype(np.uint8), "role": role, "lo": lo, "hi": hi,
            "sites": sites, "stats": st}


def shape_sites(h, lo, hi, role, inp: Inputs) -> list[dict]:
    """One entrance site per dungeon record, shaped in place (options §9): a mound, or a bank cut where water is
    near, for a mouth; a depression for a sinkhole; flat landmark ground; a deep-water bowl for an underwater entry."""
    out = []
    wl = inp.water.level
    for s in inp.sites:
        shape = SHAPES.get(s["entrance"], "flat")
        if shape == "mound" and s["water_m"] is not None and s["water_m"] < BANK_WATER_M:
            shape = "bank"
        cx, cy = s["x_m"] / MPP, s["y_m"] / MPP
        rad = s["radius_m"] / MPP
        r = int(math.ceil(rad * 1.5))
        r0, r1 = max(int(cy) - r, 0), min(int(cy) + r + 1, N + 1)
        c0, c1 = max(int(cx) - r, 0), min(int(cx) + r + 1, N + 1)
        if r0 >= r1 or c0 >= c1:
            continue
        yy, xx = np.mgrid[r0:r1, c0:c1]
        d = np.hypot(yy - cy, xx - cx) / rad
        w = np.clip(1 - d, 0, 1)
        w = w * w * (3 - 2 * w)
        win = h[r0:r1, c0:c1]
        ci, cj = min(max(int(round(cy)), 0), N), min(max(int(round(cx)), 0), N)
        cell = (min(ci // Q, C - 1), min(cj // Q, C - 1))
        facing = 0.0
        if shape in ("mound", "bank"):
            win += MOUND_M * w
            gy, gx = np.gradient(win)
            facing = float(np.degrees(np.arctan2(gx[ci - r0, cj - c0], -gy[ci - r0, cj - c0])) % 360)
        elif shape == "depression":
            win -= DEPRESSION_M * w
        elif shape == "flat":
            m = float(win[d <= 1].mean()) if (d <= 1).any() else float(win[ci - r0, cj - c0])
            win[:] = win * (1 - w) + m * w
        else:  # deep water: a bowl under the cell's level
            lev = wl[cell]
            if not np.isnan(lev):
                win[:] = np.minimum(win, win * (1 - w) + (lev - DEEP_M - 0.5) * w)
        h[r0:r1, c0:c1] = np.minimum(np.maximum(win, lo[r0:r1, c0:c1]), hi[r0:r1, c0:c1])
        out.append({"place_id": s["place_id"], "shape": shape, "x_m": round(s["x_m"], 2), "y_m": round(s["y_m"], 2),
                    "radius_m": round(s["radius_m"], 2), "facing_deg": round(facing, 1), "request": s["request"]})
    return out


def write(res: dict, out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "ground-f32.npy", res["ground"])
    np.save(out / "cliff-u8.npy", res["cliff"])
    np.save(out / "role-u8.npy", res["role"])
    (out / "entrance-sites.json").write_text(json.dumps(res["sites"], indent=0) + "\n")
    (out / "generate.json").write_text(json.dumps(res["stats"], indent=1, sort_keys=True) + "\n")
    return res["stats"]
