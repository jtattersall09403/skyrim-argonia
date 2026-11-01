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
BANK_WATER_M = 40.0
DEEP_SEEK_M = 150.0  # an underwater entry looks this far for water under it  # a mouth within this of water is cut into the bank, not a mound


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
            ys, yd = (slice(0, -dy), slice(dy, None)) if dy > 0 else (slice(-dy, None), slice(0, dy or None))
            xs, xd = (slice(0, -dx), slice(dx, None)) if dx > 0 else (slice(-dx, None), slice(0, dx or None))
            cand = d[ys, xs] + w
            tgt = d[yd, xd]
            better = cand < tgt
            if better.any():
                changed = True
                np.copyto(tgt, cand, where=better)
                if v is not None:
                    np.copyto(v[yd, xd], v[ys, xs], where=better)
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
    h = np.minimum(np.maximum(h, a), np.maximum(b, a))
    pins = np.zeros(h.shape, bool)
    dx, dy = np.abs(np.diff(h, axis=1)) > lip, np.abs(np.diff(h, axis=0)) > lip
    pins[:, 1:] |= dx
    pins[:, :-1] |= dx
    pins[1:] |= dy
    pins[:-1] |= dy
    if not pins.any():
        return h, pins
    m = (minorant(h, lip) + majorant(h, lip)) / 2  # quantize.py's method: pin the steep pairs to m, cone the rest
    lo_c = majorant(np.where(pins, m, -1e9), lip)
    hi_c = minorant(np.where(pins, m, 1e9), lip)
    f = np.minimum(np.maximum(h, lo_c), hi_c)
    # the water's bounds win: where a bank and a bed are closer than the slope allows (a fall), the step is a cliff
    f = np.minimum(np.maximum(f, np.where(np.isfinite(lo), lo, -1e9)), np.maximum(np.where(np.isfinite(hi), hi, 1e9), lo))
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
    # the land stands on its water (never below the base plus its floor) and rises to the region's absolute band
    h = np.maximum(base + floor, relief) + noise * rough * away
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
    din, _ = chamfer(~foot, 32)
    din = np.where(foot, np.where(np.isfinite(din), din, 32), 0)
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
    banks = []
    chan = np.zeros((N + 1, N + 1), bool)
    sbank = np.zeros((N + 1, N + 1), bool)  # the closed banks along step edges: nothing later opens them
    chan0 = np.zeros((N + 1, N + 1), bool)  # the vertices where a channel crosses its own edge
    for s in inp.water.steps:
        r_north = (C - 1 - (s.cy - CY0)) * Q
        c_west = (s.cx - CX0) * Q
        if s.cross_lo < 0:
            s = type(s)(s.cx, s.cy, s.edge, s.upper_m, s.lower_m, Q + 1, Q, s.chain)  # closed: banks only
        drop = s.upper_m - s.lower_m
        k = int(min(Q - 1, max(1, math.ceil(drop / (0.8 * lip)))))  # 1-5 vertices, longer for a big drop
        edge_bed = s.upper_m - STEP_BED_M
        end_bed = s.lower_m - FREEBOARD_M - 0.2
        # the banks closed above the upper water along the whole edge outside the channel (options §11)
        jj = np.arange(Q + 1)
        out_ = (jj < s.cross_lo) | (jj > s.cross_hi)
        if s.edge in ("e", "w"):
            esel = (r_north + Q - jj[out_], np.full(out_.sum(), c_west + (Q if s.edge == "e" else 0)))
        else:
            esel = (np.full(out_.sum(), r_north + (0 if s.edge == "n" else Q)), c_west + jj[out_])
        banks.append((esel, s.upper_m + FREEBOARD_M))
        j = np.arange(s.cross_lo, s.cross_hi + 1)
        for kk in range(1, k + 1):  # the lower cell's band beside the edge is a graded slope, not held wet
            if s.edge in ("e", "w"):
                col = c_west + (Q + kk if s.edge == "e" else -kk)
                band = (r_north + Q - jj, np.full(Q + 1, col)) if 0 <= col <= N else None
            else:
                row = r_north + (-kk if s.edge == "n" else Q + kk)
                band = (np.full(Q + 1, row), c_west + jj) if 0 <= row <= N else None
            if band is not None:
                held = role[band] == 1
                hi[band] = np.where(held, np.inf, hi[band])
                role[band] = np.where(held, 2, role[band])
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
            first = ~chan[sel]  # a vertex two channels share keeps the lower bed
            h[sel] = np.where(first, z, np.minimum(h[sel], z))
            hi[sel] = np.where(first, z + 0.01, np.minimum(hi[sel], z + 0.01))
            chan[sel] = True
            if kk == 0:
                chan0[sel] = True
            lo[sel] = -np.inf
        nstep += 1
    role[chan] = np.where(hi[chan] < vmin[chan], 1, 2)
    for esel, z in banks:  # the banks closed above the upper water, after every channel (a corner may be one)
        keep = ~chan0[esel]
        e = (esel[0][keep], esel[1][keep])
        lo[e] = np.maximum(np.where(np.isfinite(lo[e]), lo[e], -np.inf), z)
        hi[e] = np.inf
        h[e] = np.maximum(h[e], z)
        role[e] = 3
        sbank[e] = True
    st["steps_joined"] = nstep
    h = np.minimum(np.maximum(h, lo), hi)
    log(f"constraints {time.time() - t0:.1f}s")

    # 6. entrance sites
    sites = shape_sites(h, lo, hi, role, inp, vmin, vmax, foot & ~sbank, sbank)
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


def rim_plane(win: np.ndarray, d: np.ndarray, yy: np.ndarray, xx: np.ndarray) -> np.ndarray:
    """The plane through the ring 1.0-1.3 r about a site (least squares), over the window: what the site is
    shaped against, so a mound on a hillside is a mound and not the hill."""
    ring = (d > 1.0) & (d <= 1.3)
    if ring.sum() < 3:
        return np.full(win.shape, float(win.mean()))
    A = np.stack([yy[ring], xx[ring], np.ones(ring.sum())], 1).astype(np.float64)
    k, *_ = np.linalg.lstsq(A, win[ring], rcond=None)
    return k[0] * yy + k[1] * xx + k[2]


def shape_sites(h, lo, hi, role, inp: Inputs, vmin, vmax, foot, sbank) -> list[dict]:
    """One entrance site per dungeon record, reserved and shaped in place (options §9): a mound, or a bank cut where
    water is near, for a mouth; a depression for a sinkhole; flat landmark ground; a deep-water bowl for an
    underwater entry. A dry-shaped site standing in water is reserved as ground (its disc becomes bank above the
    water); an underwater entry with no water under it moves to the nearest wet sample within DEEP_SEEK_M, else
    becomes a bank mouth (both written to the row's request note)."""
    out = []
    order = {"flat": 0, "deep_water": 1, "depression": 2}  # the broad shapes first, the mouths on top
    for s in sorted(inp.sites, key=lambda s: (order.get(SHAPES.get(s["entrance"], "flat"), 3), s["place_id"])):
        shape = SHAPES.get(s["entrance"], "flat")
        note = s["request"] or ""
        if shape == "mound" and s["water_m"] is not None and s["water_m"] < BANK_WATER_M:
            shape = "bank"
        cx, cy = s["x_m"] / MPP, s["y_m"] / MPP
        rad = s["radius_m"] / MPP
        if shape == "deep_water":
            ci, cj = int(round(cy)), int(round(cx))
            if not (0 <= ci <= N and 0 <= cj <= N and foot[ci, cj] and not sbank[ci, cj]):
                k = int(DEEP_SEEK_M / MPP)
                r0, c0 = max(ci - k, 0), max(cj - k, 0)
                sub = foot[r0:ci + k + 1, c0:cj + k + 1]
                if sub.any():
                    yy, xx = np.nonzero(sub)
                    i = int(np.argmin((yy + r0 - cy) ** 2 + (xx + c0 - cx) ** 2))
                    cy, cx = float(yy[i] + r0), float(xx[i] + c0)
                    note = f"{note}; moved {np.hypot(cy - s['y_m'] / MPP, cx - s['x_m'] / MPP) * MPP:.0f} m to water".strip("; ")
                else:
                    shape, note = "bank", f"{note}; no water within {DEEP_SEEK_M:.0f} m: a bank mouth".strip("; ")
        r = int(math.ceil(rad * 1.5))
        ci, cj = min(max(int(round(cy)), 0), N), min(max(int(round(cx)), 0), N)
        r0, r1 = max(ci - r, 0), min(ci + r + 1, N + 1)
        c0, c1 = max(cj - r, 0), min(cj + r + 1, N + 1)
        yy, xx = np.mgrid[r0:r1, c0:c1]
        d = np.hypot(yy - cy, xx - cx) / rad
        w = np.clip((1.0 - d) / 0.4, 0, 1)  # full inside 0.6 r, ramped to the rim
        w = w * w * (3 - 2 * w)
        sl = (slice(r0, r1), slice(c0, c1))
        win, wlo, whi, wro = h[sl], lo[sl], hi[sl], role[sl]
        disc = d <= 1.0
        facing = 0.0
        if shape not in ("deep_water", "depression"):  # reserve the disc as ground above any water sharing it
            wet = disc & ~np.isnan(vmax[sl])
            whi[wet] = np.inf
            wlo[wet] = np.maximum(np.where(np.isfinite(wlo[wet]), wlo[wet], -np.inf), vmax[sl][wet] + FREEBOARD_M)
            wro[wet] = 3
            win[:] = np.maximum(win, np.where(np.isfinite(wlo), wlo, -np.inf))
        plane = rim_plane(win, d, yy, xx)
        if shape in ("mound", "bank"):
            win[:] = np.maximum(win, plane + MOUND_M * w)
            gy, gx = np.gradient(win)
            facing = float(np.degrees(np.arctan2(gx[ci - r0, cj - c0], -gy[ci - r0, cj - c0])) % 360)
        elif shape == "depression":  # a sinkhole: in a water cell its floor floods (it joins the cell's water)
            win[:] = np.minimum(win, win * (1 - w) + (plane - DEPRESSION_M) * w)
            inner = disc & ~np.isnan(vmin[sl]) & ~sbank[sl]
            sunk = inner & (win < vmin[sl])
            wlo[inner] = np.where(sunk[inner], -np.inf, vmax[sl][inner] + FREEBOARD_M)
            whi[inner] = np.where(sunk[inner], vmin[sl][inner] - FREEBOARD_M, np.inf)
            wro[inner] = np.where(sunk[inner], 1, 3)
        elif shape == "flat":
            core = d <= 0.6
            m = float(np.median(win[core]))
            if np.isfinite(wlo[core]).any():
                m = max(m, float(wlo[core][np.isfinite(wlo[core])].max()))
            wlo[core] = np.minimum(np.where(np.isfinite(wlo[core]), wlo[core], -np.inf), m)
            win[:] = win * (1 - w) + m * w
        else:  # deep water: a bowl under the cell's level
            bowl = vmin[sl] - DEEP_M - 0.5  # under the lowest water sharing each vertex
            inner = (d <= 0.5) & ~np.isnan(bowl) & (wro != 3)  # a closed bank stays closed
            whi[inner] = np.minimum(whi[inner], bowl[inner])
            wlo[inner] = -np.inf
            wro[inner] = 1
            bowl = np.where(np.isnan(bowl), win, bowl)
            win[:] = np.where(wro == 3, win, np.minimum(win, win * (1 - w) + bowl * w))
        win[:] = np.minimum(np.maximum(win, wlo), np.maximum(whi, wlo))
        out.append({"place_id": s["place_id"], "shape": shape, "x_m": round(cx * MPP, 2), "y_m": round(cy * MPP, 2),
                    "radius_m": round(s["radius_m"], 2), "facing_deg": round(facing, 1), "request": note or None})
    return out


def write(res: dict, out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "ground-f32.npy", res["ground"])
    np.save(out / "cliff-u8.npy", res["cliff"])
    np.save(out / "role-u8.npy", res["role"])
    (out / "entrance-sites.json").write_text(json.dumps(res["sites"], indent=0) + "\n")
    (out / "generate.json").write_text(json.dumps(res["stats"], indent=1, sort_keys=True) + "\n")
    return res["stats"]


def check(ground: np.ndarray, role: np.ndarray, water: CellWater, sites: list[dict]) -> dict:
    """L1: every cell water fits its ground (no wet vertex at or above the lowest water sharing it; no bank of a
    water cell below the highest; no bank below the upper water at a step outside its channel); every site shaped."""
    g = np.asarray(ground, np.float64)
    vmin, vmax = vertex_levels(water.level)
    wet_bad = (role == 1) & ~(g < vmin)  # NaN (wet with no water over it) counts
    bank_bad = (role == 3) & ~(g > vmax)
    step_bad = 0
    chan_v = set()
    for s in water.steps:
        if s.cross_lo < 0:
            continue
        rn, cw_ = (C - 1 - (s.cy - CY0)) * Q, (s.cx - CX0) * Q
        for j in range(s.cross_lo, s.cross_hi + 1):
            chan_v.add((rn + Q - j, cw_ + (Q if s.edge == "e" else 0)) if s.edge in ("e", "w")
                       else (rn + (0 if s.edge == "n" else Q), cw_ + j))
    for s in water.steps:
        rn, cw_ = (C - 1 - (s.cy - CY0)) * Q, (s.cx - CX0) * Q
        j = np.arange(Q + 1)
        if s.edge in ("e", "w"):
            col = cw_ + (Q if s.edge == "e" else 0)
            z = g[rn + Q - j, col]
        else:
            z = g[rn + (0 if s.edge == "n" else Q), cw_ + j]
        chan = (j >= s.cross_lo) & (j <= s.cross_hi) if s.cross_lo >= 0 else np.zeros(Q + 1, bool)
        pts = [(rn + Q - jv, col) for jv in j] if s.edge in ("e", "w") else [(rn + (0 if s.edge == "n" else Q), cw_ + jv) for jv in j]
        other = np.array([p in chan_v for p in pts])
        step_bad += int((~chan & ~other & (z < s.upper_m)).sum())
    site_bad = []
    for s in sites:
        ci, cj = int(round(s["y_m"] / MPP)), int(round(s["x_m"] / MPP))
        r = int(s["radius_m"] / MPP)
        if not (r <= ci <= N - r and r <= cj <= N - r):
            continue
        win = g[ci - r:ci + r + 1, cj - r:cj + r + 1]
        yy, xx = np.mgrid[ci - r:ci + r + 1, cj - r:cj + r + 1]
        rr = int(r * 1.3) + 1
        if not (rr <= ci <= N - rr and rr <= cj <= N - rr):
            continue
        big = g[ci - rr:ci + rr + 1, cj - rr:cj + rr + 1]
        by, bx = np.mgrid[ci - rr:ci + rr + 1, cj - rr:cj + rr + 1]
        bd = np.hypot(by - s["y_m"] / MPP, bx - s["x_m"] / MPP) / (s["radius_m"] / MPP)
        rel = float(g[ci, cj] - rim_plane(big, bd, by, bx)[rr, rr])
        inner = win[np.hypot(yy - ci, xx - cj) <= 0.4 * r]
        c = float(g[ci, cj])
        lev = vmin[ci, cj]
        ok = {"mound": rel >= 2.0, "bank": rel >= 2.0, "depression": rel <= -1.5,
              "flat": float(inner.std()) < 1.0,
              "deep_water": not np.isnan(lev) and lev - c >= DEEP_M}[s["shape"]]
        if not ok:
            site_bad.append((s["place_id"], s["shape"], int(role[ci, cj])))
    return {"wet_above_water": int(wet_bad.sum()), "bank_below_water": int(bank_bad.sum()),
            "step_bank_below_upper": step_bad, "sites": len(sites), "sites_unshaped": len(site_bad),
            "sites_unshaped_by": {f"{k[0]}/role{k[1]}": n for k, n in
                                  sorted(__import__("collections").Counter((b[1], b[2]) for b in site_bad).items())},
            "sites_unshaped_ids": [b[0] for b in site_bad[:20]]}
