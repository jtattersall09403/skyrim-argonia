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
4. the roads laid in (routes/shape.py: Skyrim.esm's measured trough across and grade limit along, the traced roads);
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
import os
import math
import zlib
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
CLIFF_HARD_DEG = 80.0  # a forced cliff between two waters' cones: under the int8 limit (82.9 deg)
CLIFF_DEG = 55.0  # designed slope past this is a cliff face: the cliff and climbable mask (cliff-u8.npy); Free Climb climbs normal.z <= 0.70, i.e. 45.6 deg walked to 55 deg, climbed past (docs/research/2026-11-01/climb-anything.md)
LIP = math.tan(math.radians(DESIGN_SLOPE_DEG)) * MPP  # the limit's 4-neighbour step
STEP_BED_M = 200 / su.UNITS_PER_METRE  # options §11: the bed crosses the edge 100-300 units (median 224) under the upper water
FREEBOARD_M = 0.3  # a bank stands this far above its water; a bed at least this far below
RIFFLE_M = 0.5  # water/solve.py: a smaller drop is no step
SHORE_WOBBLE = 4  # samples: the footprint's edge moves this far in or out by noise (no straight bank)
NEAR_RISE, NEAR_DIP = 0.8, 0.3  # by the water the relief noise keeps this share of its rises and of its dips
SHORE_FAR = 40  # samples: the shore grade reaches this far from the water
# shore grade (rise per metre) by water type: the mangrove coast flat, the upland tarn steep
# (docs/design/research/world-terrain/tropical-fluvial-geomorphology.md: "Tidal creeks ... depth 0.5-2 m", the lagoon
#  behind its barrier; mountain-terrain-synthesis.md: "cliff bands ... knickpoint waterfalls" for upland water)
# The shore and bed profiles, measured in Skyrim.esm (docs/research/2026-11-01/skyrim-does-it-this-way.md §1,
# decision 0034): median rise above the water (units) at 0/1/2/3/5/8/10 vertices out, and bed depth at 0/1/2/3/5/8
# vertices in. One of our samples is one vertex. The marsh (Morthal) for brackish and blackwater, the open sea
# (Solitude) for the sea, the lake (Ilinalta) for fresh. Past the last vertex the rise keeps its last grade; the
# bed keeps its last depth, capped by DEPTH_M.
PROFILE_V = (0, 1, 2, 3, 5, 8, 10)
SHORE_RISE_U = {"sea": (0, 24, 88, 152, 304, 508, 728), "brackish": (0, 8, 40, 72, 160, 264, 326),
                "blackwater": (0, 8, 40, 72, 160, 264, 326), "fresh": (0, 24, 80, 128, 240, 480, 648)}
BED_DEPTH_U = {"sea": (0, 32, 96, 184, 336, 528), "brackish": (0, 24, 48, 64, 80, 80),
               "blackwater": (0, 24, 48, 64, 80, 80), "fresh": (0, 32, 96, 152, 272, 432)}
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
SHAPES = {"cave-mouth": "rise", "burrow": "rise", "grave-cut": "rise", "root-mouth": "rise", "hollow-trunk": "flat",
          "sinkhole-lip": "depression", "underwater-entry": "deep_water", "door": "flat", "gate": "flat",
          "stair-throat": "flat", "cellar-door": "flat", "trapdoor": "flat", "well-shaft": "flat", "none": "flat"}
SITE_MIN_R = 12.0
SITE_BLEND = 1.5  # radii: a site's ground eases into the relief out to here (inside SITE_WIN)
SITE_WIN = 1.7  # a site window in radii: holds the rim ring (1.0-1.3) under the warp (up to 1/0.74)
FLAT_MIN_SCALE = 0.3  # a flat on a gorge lip shrinks (x0.85 a try) to no less than this share of its radius
FLAT_KEEP, FLAT_SD_M = 0.35, 0.4  # a flat keeps this share of its relief, its core's spread held to this std (m)
FLAT_CORE_M = 40.0  # the check's flat-core window is capped at this radius
DEPRESSION_M, DEEP_M = 4.0, 3.0  # options §9: a sinkhole, a deep cell
SINK_FREE = 6  # samples: a flooded sinkhole's unpinned bank (a 15 m rise at the 75 deg limit's 6.8 m a sample, doubled)
# a mouth is cut into the foot of a rise, never raised on a ring mound (skyrim-does-it-this-way.md §10: Skyrim.esm's
# cave doors stand p50 553 u below the ground 1,024 u around, slope 35 deg at the door): the ground RISE_L_M behind
# the mouth stands RISE_M above its door; the check asks RISE_OK of it
RISE_M, RISE_L_M, RISE_OK = 553 / su.UNITS_PER_METRE, 1024 / su.UNITS_PER_METRE, 0.75
BANK_WATER_M = 40.0
DEEP_SEEK_M = 150.0  # an underwater entry looks this far for water under it  # a mouth within this of water is cut into the bank, not a mound


def bed_depth(t: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Metres the bed lies under its water `d` samples in, by water type index `t` (BED_DEPTH_U)."""
    out = np.zeros(np.shape(d))
    for i, n in enumerate(TYPES):
        m = t == i
        if m.any():
            ys = np.asarray(BED_DEPTH_U[n], float) / su.UNITS_PER_METRE
            out[m] = np.interp(d[m], PROFILE_V[:len(ys)], ys)
    return out


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


def write_relief(w) -> int:
    """Replace `region_relief` with relief_rows() and save (`terrain relief`)."""
    for r in w.query("SELECT land_region_id FROM region_relief"):
        w.delete("region_relief", r[0])
    n = w.insert_many("region_relief", relief_rows(w))
    w.save()
    return n


def read_relief(w) -> list[dict]:
    """The `region_relief` rows (the generator's input), or relief_rows() while the table is empty."""
    rows = [dict(r) for r in w.query("SELECT land_region_id, floor_m, summit_m, roughness_m, cliff_share, erosion, "
                                     "why FROM region_relief ORDER BY land_region_id")]
    return rows or relief_rows(w)


def write_sites(w, sites: list[dict]) -> int:
    """Replace `entrance_site` with the shaped sites and save."""
    for r in w.query("SELECT place_id FROM entrance_site"):
        w.delete("entrance_site", r[0])
    n = w.insert_many("entrance_site", sites)
    w.save()
    return n


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
    # bilinear has a slope kink on every cell line (a lattice of straight creases): smoothed at half a cell
    return blur(rows[:, i0] * (1 - f)[None] + rows[:, i0 + 1] * f[None], Q / 2)


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


def _diag(a: np.ndarray, op, lip: float) -> np.ndarray:
    """The 8-neighbour pass: both diagonals at lip x sqrt 2, so a cone is an octagon, not the 4-neighbour sweep's
    square pyramid (the planar faces and straight ridges of world-panel stills 28, 29, 36, 37)."""
    s = (1.0 if op is np.minimum else -1.0) * lip * math.sqrt(2)
    for _ in range(2):
        for i in range(1, a.shape[0]):
            op(a[i, 1:], a[i - 1, :-1] + s, out=a[i, 1:])
            op(a[i, :-1], a[i - 1, 1:] + s, out=a[i, :-1])
        for i in range(a.shape[0] - 2, -1, -1):
            op(a[i, 1:], a[i + 1, :-1] + s, out=a[i, 1:])
            op(a[i, :-1], a[i + 1, 1:] + s, out=a[i, :-1])
    return a


def minorant(a, lip):
    a = _sweep(_sweep(a.copy(), np.minimum, lip, 1), np.minimum, lip, 0)
    return _sweep(_sweep(_diag(a, np.minimum, lip), np.minimum, lip, 1), np.minimum, lip, 0)


def majorant(a, lip):
    a = _sweep(_sweep(a.copy(), np.maximum, lip, 1), np.maximum, lip, 0)
    return _sweep(_sweep(_diag(a, np.maximum, lip), np.maximum, lip, 1), np.maximum, lip, 0)


def limit(h: np.ndarray, lo: np.ndarray, hi: np.ndarray, lip: float) -> tuple[np.ndarray, np.ndarray]:
    """h held lip-Lipschitz (4-neighbour) inside the cones of the bounds lo <= h <= hi; returns (f, steep) where
    steep marks the samples the limit moved (the designed cliffs)."""
    lo_, hi_ = np.where(np.isfinite(lo), lo, -1e9), np.where(np.isfinite(hi), hi, 1e9)
    a, b = majorant(lo_, lip), minorant(hi_, lip)
    # where two waters' cones cannot both hold at the design slope (a tarn's bank above a lake's bed closer than the
    # slope allows), the ground between is a cliff at CLIFF_HARD_DEG (still inside the int8 limit), not one wall
    clash = a > b + 1e-6
    if clash.any():
        lh = math.tan(math.radians(CLIFF_HARD_DEG)) * MPP
        a = np.where(clash, majorant(lo_, lh), a)
        b = np.where(clash, minorant(hi_, lh), b)
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
    reach: np.ndarray | None = None  # (4033, 4033) a reach's channel (river or stream) outside the still bodies
    seats: list | None = None  # routes/infra.seats: each bridge end's seat on the road (lane 1.15-r6-bridges)

    @classmethod
    def load(cls, world=None) -> Inputs:
        from tools.argonia_world import db
        from tools.argonia_world.terrain import cellwater
        from tools.argonia_world.terrain.grid import PAD, data_root

        w = world if world is not None else db.open()
        a = np.load(data_root() / "terrain" / "apron-source-near.npy", mmap_mode="r")
        prior = np.asarray(a[PAD:PAD + N + 1, PAD:PAD + N + 1], np.float32)
        rows = read_relief(w)
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
        from tools.argonia_world.terrain.grid import data_root as _dr
        rl, _ = cellwater.reach_raster(w)
        zb = np.load(_dr() / "hydrology-graph-bodies.npz")
        reach = ~np.isnan(rl) & ~np.isfinite(zb["level"]) & ~zb["sea"]
        del rl, zb
        # the bridges' crossings (routes/infra.BRIDGES on their roads' lines): the deck tops are set by generate on
        # the corridor after dry_corridor (shape.bridge_decks), never on an older ground
        from tools.argonia_world.routes.shape import bridge_crossings
        seats = bridge_crossings(w)
        return cls(prior, region, rows, [cult[r["land_region_id"]] for r in rows], water, wet_level, roads, sites,
                   reach, seats)


def reach(seed: np.ndarray, allowed: np.ndarray) -> np.ndarray:
    """The samples of `allowed` 4-connected to `seed` (seed itself always kept). Numpy only (no scipy): the
    components of allowed-and-not-seed are labelled over their row runs (min-label propagation with pointer jumping
    on the run graph), and a component touching the seed joins it."""
    L = allowed & ~seed
    got = seed.copy()
    if not L.any():
        return got
    H, W = L.shape
    start = L.copy()
    start[:, 1:] &= ~L[:, :-1]
    rid = np.cumsum(start.ravel()).reshape(H, W) - 1  # a run's id on each of its samples
    nrun = int(start.sum())
    v = L[:-1] & L[1:]
    a, b = rid[:-1][v], rid[1:][v]
    lab = np.arange(nrun)
    while True:
        old = lab
        m = np.minimum(lab[a], lab[b])
        lab = lab.copy()
        np.minimum.at(lab, a, m)
        np.minimum.at(lab, b, m)
        lab = lab[lab]
        if np.array_equal(lab, old):
            break
    touch = np.zeros_like(L)
    touch[1:] |= seed[:-1]; touch[:-1] |= seed[1:]
    touch[:, 1:] |= seed[:, :-1]; touch[:, :-1] |= seed[:, 1:]
    keep = np.zeros(nrun, bool)
    keep[lab[rid[L & touch]]] = True
    got[L] = keep[lab[rid[L]]]
    return got | seed


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


def generate(inp: Inputs, log=print, pre_only: bool = False) -> dict:
    """A whole-province generate (the full 4033² prior) takes the province lock: one at a time on the build VM."""
    from tools.argonia_world.province_lock import province_lock
    if inp.prior.size >= 2000 * 2000:
        with province_lock("terrain generate", log):
            return _generate(inp, log, pre_only)
    return _generate(inp, log, pre_only)


def _generate(inp: Inputs, log=print, pre_only: bool = False) -> dict:
    t0 = time.time()
    st: dict = {}
    diag: dict = {}  # masks for probes (probes/clamp_census.py): which rule set each bound
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
    ks = 200.0  # samples: a soft minimum of the distances to the N and W borders (no kink on the diagonal)
    dist_nw = -ks * np.logaddexp(-ii / ks, -jj / ks) * MPP
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
    # the base comes from the wet raster (the hydrology's own levels), never from the solved cell levels: the solve
    # reads this ground to set those levels (water/solve.py, levels from the ground), so the ground comes first
    rawf = ~np.isnan(inp.wet_level)
    with np.errstate(all="ignore"):
        wlr = np.nanmin(np.where(rawf, inp.wet_level, np.inf)[:N, :N].reshape(C, Q, C, Q), axis=(1, 3))
    wlr[~np.isfinite(wlr)] = np.nan
    base = nanblur(upsample(blur(fill_nearest(wlr), 1.0)), 32)
    del wlr
    vmin, vmax = vertex_levels(wl)
    has = ~np.isnan(vmin)
    # one level definition (session 17): a sample's water is its own cell's solved level, never the lowest of the
    # four cells at a vertex nor the raster's level. Raster water in a cell the solve left dry is a dry gully (a bed
    # with no level, carved by the field); raster water on a vertex of a drop belongs to no body (the step's banks
    # and join own it). So the carve stops at the body's own footprint: session 16's coast gap carved a 199-374 m
    # gully down to the 0 m sea of the padded cell beside it
    lev_s = np.pad(np.repeat(np.repeat(wl, Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge")
    rawf_ = ~np.isnan(inp.wet_level)
    own = np.isfinite(lev_s) & has & (np.nan_to_num(lev_s - vmin, nan=0.0) <= RIFFLE_M)
    # an enclosed or padding cell's level is its ring's, not the raster water's in it: raster water there standing
    # over the level by more than a riffle is another body's or a gully's (a 63 m pool in a 0 m padding cell at
    # -55,-20), carved as a dry bed, never down to the ring's level
    if inp.water.held is not None:
        hs_ = np.pad(np.repeat(np.repeat(inp.water.held, Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge")
        own &= hs_ | ~(inp.wet_level > lev_s + RIFFLE_M)
        del hs_
    foot = rawf_ & own
    gully = rawf_ & ~own & ~(np.isfinite(lev_s) & (np.nan_to_num(lev_s - vmin, nan=0.0) > RIFFLE_M))
    del rawf_
    # a water cell the raster leaves dry (an enclosed cell, water/solve.py fill_enclosed) gets no pool of its own:
    # as in Skyrim.esm (Lake Ilinalta's 4 all-dry cells), only its ground under the level is wet (the natural
    # flood below); a forced lowest-third pool cut on the cell grid made the square pools
    blocks = foot[:N, :N].reshape(C, Q, C, Q).any(axis=(1, 3))
    empty = ~np.isnan(wl) & ~blocks
    st["water"] = {"source": inp.water.source, "cells": int((~np.isnan(wl)).sum()), "steps": len(inp.water.steps),
                   "empty_water_cells": int(empty.sum()), "footprint_samples": int(foot.sum()),
                   "gully_samples": int(gully.sum())}
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
        # each octave's bilinear lattice smoothed at half its spacing (no creases every N / k samples)
        noise += amp * blur(rows_[:, i0] * (1 - f)[None] + rows_[:, i0 + 1] * f[None], max(N / k / 2, 1.0))
    # the outline: the raster's polygon edges and cell lines drew ruler-straight banks (world-panel stills 08, 09, 29);
    # Skyrim.esm's outlines are the body's shape (on cell lines 5.9 % of their length, probes/vanilla_lake_padding.py),
    # so the footprint's edge is moved up to SHORE_WOBBLE samples in or out by a fine noise, inside water cells only
    k_ = N // 8
    g_ = np.random.default_rng(1151).standard_normal((k_ + 2, k_ + 2))
    t_ = np.linspace(0, k_, N + 1)
    i_ = np.floor(t_).astype(int)
    f_ = t_ - i_
    r_ = g_[i_] * (1 - f_)[:, None] + g_[i_ + 1] * f_[:, None]
    wob = blur(r_[:, i_] * (1 - f_)[None] + r_[:, i_ + 1] * f_[None], 4.0)
    wob = SHORE_WOBBLE * np.clip(wob / max(float(wob.std()), 1e-9), -1.5, 1.5) / 1.5
    del g_, r_
    # ... never beside a two-level line (a step's bank and bed must stay where the join puts them) nor on a site
    two_, _ = chamfer(np.nan_to_num(vmax - vmin, nan=0.0) > RIFFLE_M, 16)
    wob[np.isfinite(two_)] = 0.0
    for s_ in inp.sites:
        r_s = int(math.ceil(s_["radius_m"] * SITE_WIN / MPP)) + 2
        ci_, cj_ = int(round(s_["y_m"] / MPP)), int(round(s_["x_m"] / MPP))
        wob[max(ci_ - r_s, 0):ci_ + r_s + 1, max(cj_ - r_s, 0):cj_ + r_s + 1] = 0.0
        gully[max(ci_ - r_s, 0):ci_ + r_s + 1, max(cj_ - r_s, 0):cj_ + r_s + 1] = False  # a site shapes its own ground
    del two_
    din_, _ = chamfer(~foot, SHORE_WOBBLE + 1)
    dout_, _ = chamfer(foot, SHORE_WOBBLE + 1)
    foot = has & np.where(foot, ~(np.nan_to_num(din_, nan=99) <= wob), np.nan_to_num(dout_, nan=99) <= -wob)
    del din_, dout_, wob
    st["water"]["footprint_samples"] = int(foot.sum())
    # the nearest raster water's level and type ride the chamfer together (type x 1e4 + level + 1e3)
    tw = np.pad(np.repeat(np.repeat(inp.water.wtype, Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge").astype(np.float64)
    draw, _ = chamfer(rawf, SHORE_FAR)  # the raw raster's water: the relief noise fades by it (ground first)
    away = np.clip(np.where(np.isfinite(draw), draw, SHORE_FAR) / SHORE_FAR, 0, 1)
    del draw
    # the land stands on its water (never below the base plus its floor) and rises to the region's absolute band
    # the noise near water keeps its rises and a share of its dips (session 14: fading it to nothing by the water left
    # the lowland a flat plate at base + floor, the marsh's 0.15 x 0.64 plate); a dip never reaches the water
    n_ = noise * rough
    h = np.maximum(base + floor, relief) + np.where(n_ > 0, n_ * np.maximum(away, NEAR_RISE), n_ * np.maximum(away, NEAR_DIP))
    h = h * (1 - 0.5 * ero) + blur(h, 4) * 0.5 * ero
    nz = np.clip(noise / max(float(noise.std()), 1e-9), -2, 2) / 2  # the relief noise, unit range, for edges
    del noise
    log(f"noise+erosion {time.time() - t0:.1f}s")

    # the shore: the ground beside the water rises from under it at the type's grade (the mangrove coast flat, the
    # upland tarn steep), faded out by SHORE_FAR so the land beyond keeps its relief; inside a water cell the ground
    # that falls below the cell's water is the natural flood and counts as wet (a partly-wet cell is no plateau)
    if pre_only:  # the continuous ground (prior + relief + erosion): water/solve.py sets the levels from it
        return {"pre": h.astype(np.float32), "stats": st}
    h_pre = h.copy() if os.environ.get("ARGONIA_GROUND_DUMP") else None  # probes/clamp_census.py: the prior before any water rule
    # a water cell meeting a dry cell rises to a bank at the shared edge (the dry cell has no water plane): the
    # samples within the type's shore run of a vertex touching a dry cell are bank, not wet, so the shore slopes
    # inside the water cell instead of being cut along the cell edge
    i = np.arange(N + 1)
    lo_c, hi_c = np.clip((i - 1) // Q, 0, C - 1), np.clip(i // Q, 0, C - 1)
    dryc = np.isnan(wl)
    touch = np.zeros((N + 1, N + 1), bool)
    for a_ in (lo_c, hi_c):
        for b_ in (lo_c, hi_c):
            touch |= dryc[a_][:, b_]
    touch[0, :] = touch[-1, :] = touch[:, 0] = touch[:, -1] = False
    # and so does the lower water at a closed step (two levels at one vertex): its bank rises from the lower water
    # over the shore run of the drop, never a wall beside the lower bed (the drop rides the chamfer from its edge)
    # ... except about a step's channel: the vanilla join (bed through the edge, slope band) owns those vertices
    chz = np.zeros((N + 1, N + 1), bool)
    for s_ in inp.water.steps:
        if s_.cross_lo < 0:
            continue
        k_ = int(min(Q - 1, max(1, math.ceil((s_.upper_m - s_.lower_m) / (0.8 * lip)))))
        r_n, c_w = (C - 1 - (s_.cy - CY0)) * Q, (s_.cx - CX0) * Q
        a0, a1 = s_.cross_lo, s_.cross_hi
        if s_.edge in ("e", "w"):
            e0 = c_w + (Q if s_.edge == "e" else 0)
            chz[max(r_n + Q - a1, 0):r_n + Q - a0 + 1, max(e0 - k_, 0):e0 + k_ + 1] = True
        else:
            e0 = r_n + (0 if s_.edge == "n" else Q)
            chz[max(e0 - k_, 0):e0 + k_ + 1, max(c_w + a0, 0):c_w + a1 + 1] = True
    if h_pre is not None:
        np.savez(os.environ["ARGONIA_GROUND_DUMP"], h=h_pre.astype(np.float32), foot=foot, vmin=vmin.astype(np.float32),
                 vmax=vmax.astype(np.float32), touch=touch, chz=chz, tsamp=tw.astype(np.int8), blocks=blocks)
    del tw

    # 4. roads: laid in after the water constraints (step 5 below), inside their cones

    # 5. water constraints
    wtype = np.full((C, C), "", object)
    for i, n in enumerate(TYPES):
        wtype[inp.water.wtype == i] = n
    tsamp = np.pad(np.repeat(np.repeat(inp.water.wtype, Q, 0), Q, 1), ((0, 1), (0, 1)), mode="edge")
    lo = np.full((N + 1, N + 1), -np.inf)
    hi = np.full((N + 1, N + 1), np.inf)
    from tools.argonia_world.terrain.water_field import water_field
    h_wf_in = h.astype(np.float32)
    h, role, lo, hi, wf_ = water_field(h, foot, vmin, vmax, touch, chz, tsamp, gully)
    st["water"]["field"] = {"lift_samples": int((wf_["lift"] > 0.05).sum()), "carve_samples": int((wf_["carve"] > 0.05).sum()),
                            "iso_samples": int(wf_["iso"].sum()), "iso_in_raster_cells": int((wf_["iso"] & blocks[hi_c][:, hi_c]).sum())}
    diag["iso"] = wf_["iso"]
    diag["gap_up"], diag["gap_dn"], diag["lift"] = wf_["gap_up"], wf_["gap_dn"], wf_["lift"].astype(np.float32)
    diag["src"], diag["h_in"] = wf_["src"], h_wf_in
    fbank = wf_["src"] & ~wf_["iso"]  # the field's clipped edges: a site never cuts them (step-bank)
    del wf_
    foot = role == 1
    # steps: the vanilla join
    nstep = 0
    chan = np.zeros((N + 1, N + 1), bool)
    sbank = np.zeros((N + 1, N + 1), bool)  # the closed banks along step edges: nothing later opens them
    chan0 = np.zeros((N + 1, N + 1), bool)  # the vertices where a channel crosses its own edge
    for s in inp.water.steps:
        r_north = (C - 1 - (s.cy - CY0)) * Q
        c_west = (s.cx - CX0) * Q
        if s.cross_lo < 0:
            # a closed step whose upper cell holds no raster water (a pad_ring or filled cell beside another level)
            # needs no edge bank: that cell's ground is all bank above its level already (lo = vmax + freeboard),
            # and pinning its edge drew the straight ridges along cell lines (probes/vanilla_level_edges.py: 18 of
            # Skyrim.esm's 77 level edges are closed, the upper water stopping a median 9 vertices short of them)
            ui, uj = C - 1 - (s.cy - CY0), s.cx - CX0
            if not blocks[ui, uj] and not pad_wet_edge(s, foot):
                continue
            s = type(s)(s.cx, s.cy, s.edge, s.upper_m, s.lower_m, Q + 1, Q, s.chain)  # closed: banks only
        drop = s.upper_m - s.lower_m
        k = int(min(Q - 1, max(1, math.ceil(drop / (0.8 * lip)))))  # 1-5 vertices, longer for a big drop
        edge_bed = s.upper_m - STEP_BED_M
        end_bed = s.lower_m - FREEBOARD_M - 0.2
        jj = np.arange(Q + 1)
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
    # a channel's end vertex that a dry cell shares (the solve pads only cells whose ground reaches the level, so a
    # corner may stand by dry ground) stays bank above the water: no water stops on a dry cell's edge
    ct = chan & touch & ~np.isnan(vmax)
    lo[ct], hi[ct] = vmax[ct] + FREEBOARD_M, np.inf
    h[ct] = np.maximum(h[ct], lo[ct])
    role[ct] = 3
    chan &= ~ct
    chan0 &= ~ct
    # the roads keep to dry ground (lane 1.15-r6-roads-dry, planner 2026-11-04 20:15): the corridor a causeway over
    # its cell's water, a reach crossed at a ford (routes/shape.py dry_corridor); a step's channel keeps its bed
    from tools.argonia_world.routes.shape import dry_corridor
    reach_ = inp.reach if inp.reach is not None else np.zeros((N + 1, N + 1), bool)
    span = np.zeros_like(chan)
    if inp.seats:  # under a bridge's deck the water stays (the step shows under it): no causeway there
        from tools.argonia_world.routes.shape import deck_span
        span = deck_span(chan.shape, inp.seats)
    dc = dry_corridor(inp.roads, lo, hi, role, vmin, vmax, reach_, keep=chan | span)
    st["roads_dry"] = dc["stats"]
    decks = []
    if inp.seats:  # each deck at its road's corridor (the higher end), the ends eased up to it (the channel untouched)
        from tools.argonia_world.routes.shape import bridge_decks, bridge_seats, corridor
        hc = np.minimum(np.maximum(h, lo), hi)
        decks = bridge_decks(hc, inp.seats)
        bs = bridge_seats(inp.seats, lo, hi, keep=chan | span, corridor_m=corridor(lo.shape, inp.roads), h=hc)
        del hc
        st["bridge_seats"] = bs["stats"]
        role[bs["seated"] & (role == 1)] = 3
        dc["bank"] = dc["bank"] | bs["seated"]
        del bs
    road_dry = dc["bank"]
    road_raised = dc["raised"].astype(np.uint8)
    foot &= ~road_dry
    del dc
    diag["sbank"], diag["ct"], diag["chan"] = sbank.copy(), ct.copy(), chan.copy()
    diag["pad"] = has & ~blocks[hi_c][:, hi_c] & ~blocks[lo_c][:, lo_c]
    st["steps_joined"] = nstep
    h = np.minimum(np.maximum(h, lo), hi)
    log(f"constraints {time.time() - t0:.1f}s")

    # 6. entrance sites
    diag["h_sites_in"] = h.astype(np.float32)
    sites = shape_sites(h, lo, hi, role, inp, vmin, vmax, foot & ~sbank, sbank | touch | fbank, nz, chan)  # a dry cell's vertex stays bank; a step's channel keeps its bed
    diag["h_roads_in"] = h.astype(np.float32)  # after the sites, before the roads
    st["sites"] = {k: sum(s["shape"] == k for s in sites) for k in ("rise", "bank", "depression", "flat", "deep_water")}

    # 4 (run here). the roads laid in as Skyrim.esm lays them (routes/shape.py: the measured trough across, the grade
    # along), after the water field and the sites so neither re-slopes them, then held inside their cones: a pinned
    # site core and a water's bank or bed keep their shape (a crossing: routes.shape check's crossings, a bridge)
    # the road yields to water: no shaping on a bed, a gully, a step channel or the wet raster, and the trough and
    # the smoothing stop at the bank (routes/shape.py), so a crossing keeps the graded bed and banks (no wall)
    from tools.argonia_world.routes import shape as road_shape
    rwater = ((foot | ~np.isnan(inp.wet_level)) & ~road_dry) | gully | chan
    if os.environ.get("ARGONIA_ROAD_DUMP"):  # routes/shape.py's window loop: the ground the road pass starts from
        np.savez(os.environ["ARGONIA_ROAD_DUMP"], h=h.astype(np.float32), lo=lo.astype(np.float32),
                 hi=hi.astype(np.float32), water=rwater)
    st["roads"] = road_shape.shape(h, inp.roads, rwater, lo, hi)
    road_water = rwater.astype(np.uint8)  # routes.shape check reads it: a wall or a steep point by water is a crossing
    h = np.minimum(np.maximum(h, lo), hi)

    # 7. the slope limit inside the cones
    diag["h_lim_in"] = h.astype(np.float32)
    f, moved = limit(h, lo, hi, lip)
    # the cliff mask is the final ground's steep faces (vanilla dresses them with cliff meshes, the LAND under them
    # at the cap): the vegetation lane's cliff shells stand where this is set
    gy, gx = np.gradient(f, MPP)
    cliff = np.degrees(np.arctan(np.hypot(gx, gy))) > CLIFF_DEG
    st["slope"] = {"design_deg": DESIGN_SLOPE_DEG, "moved_samples": int(moved.sum()), "cliff_samples": int(cliff.sum()),
                   "max_step_m": round(float(max(np.abs(np.diff(f, axis=0)).max(), np.abs(np.diff(f, axis=1)).max())), 3)}
    st["ground_m"] = [round(float(f.min()), 2), round(float(f.max()), 2)]
    st["seconds"] = round(time.time() - t0, 1)
    log(f"limit {time.time() - t0:.1f}s")
    return {"ground": f.astype(np.float32), "cliff": cliff.astype(np.uint8), "role": role, "lo": lo, "hi": hi,
            "sites": sites, "stats": st, "diag": diag, "road_water": road_water,
            "road_raised": road_raised, "bridge_decks": decks}


def pad_wet_edge(s, foot) -> bool:
    """Whether the lower water's footprint reaches a closed step's edge (then its bank is kept even when the upper
    cell holds no raster water: the upper plane would show over the lower water's ground there)."""
    r_n, c_w = (C - 1 - (s.cy - CY0)) * Q, (s.cx - CX0) * Q
    if s.edge in ("e", "w"):
        e0 = c_w + (Q if s.edge == "e" else 0)
        return bool(foot[r_n:r_n + Q + 1, max(e0 - 1, 0):e0 + 2].any())
    e0 = r_n + (0 if s.edge == "n" else Q)
    return bool(foot[max(e0 - 1, 0):e0 + 2, c_w:c_w + Q + 1].any())


def site_dist(place_id: str, yy, xx, cy: float, cx: float, rad: float) -> np.ndarray:
    """A site's falloff distance in radii: warped by two angular harmonics seeded by the place, so no site is a disc
    (the shaping and the check use the same one)."""
    ph = np.random.default_rng(zlib.crc32(place_id.encode())).uniform(0, 2 * np.pi, 2)
    th = np.arctan2(yy - cy, xx - cx)
    return np.hypot(yy - cy, xx - cx) / rad / (1 + 0.18 * np.sin(3 * th + ph[0]) + 0.08 * np.sin(5 * th + ph[1]))


def rim_plane(win: np.ndarray, d: np.ndarray, yy: np.ndarray, xx: np.ndarray) -> np.ndarray:
    """The plane through the ring 1.0-1.3 r about a site (least squares), over the window: what the site is
    shaped against, so a mound on a hillside is a mound and not the hill."""
    ring = (d > 1.0) & (d <= 1.3)
    if ring.sum() < 3:
        return np.full(win.shape, float(win.mean()))
    A = np.stack([yy[ring], xx[ring], np.ones(ring.sum())], 1).astype(np.float64)
    k, *_ = np.linalg.lstsq(A, win[ring], rcond=None)
    return k[0] * yy + k[1] * xx + k[2]


def blend_w(d: np.ndarray, nz: np.ndarray) -> np.ndarray:
    """A site's weight: full inside 0.6 r, eased out to SITE_BLEND r through the relief noise (the audit's §10 mounds
    and towns merge into the hill; a 0.4 r ramp made a cone or a plate with a crease at its rim)."""
    t = np.clip((SITE_BLEND - d + 0.25 * nz) / (SITE_BLEND - 0.6), 0, 1)
    return t * t * (3 - 2 * t)


def shape_sites(h, lo, hi, role, inp: Inputs, vmin, vmax, foot, sbank, nz=None, chan=None) -> list[dict]:
    """One entrance site per dungeon record, reserved and shaped in place (options §9): a mound, or a bank cut where
    water is near, for a mouth; a depression for a sinkhole; flat landmark ground; a deep-water bowl for an
    underwater entry. A dry-shaped site standing in water is reserved as ground (its disc becomes bank above the
    water); an underwater entry with no water under it moves to the nearest wet sample within DEEP_SEEK_M, else
    becomes a bank mouth (both written to the row's request note)."""
    if nz is None:
        nz = np.zeros(h.shape)
    if chan is None:
        chan = np.zeros(h.shape, bool)
    out = []
    order = {"flat": 0, "deep_water": 1, "depression": 2}  # the broad shapes first, the mouths on top
    # the broad shapes first (a city before the districts inside it), the mouths on top
    for s in sorted(inp.sites, key=lambda s: (order.get(SHAPES.get(s["entrance"], "flat"), 3), -s["radius_m"],
                                               s["place_id"])):
        shape = SHAPES.get(s["entrance"], "flat")
        note = s["request"] or ""
        if shape == "rise" and s["water_m"] is not None and s["water_m"] < BANK_WATER_M:
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
        r = int(math.ceil(max(rad * SITE_WIN, 2.4 * RISE_L_M / MPP if shape in ("rise", "bank") else 0)))
        ci, cj = min(max(int(round(cy)), 0), N), min(max(int(round(cx)), 0), N)
        r0, r1 = max(ci - r, 0), min(ci + r + 1, N + 1)
        c0, c1 = max(cj - r, 0), min(cj + r + 1, N + 1)
        yy, xx = np.mgrid[r0:r1, c0:c1]
        d = site_dist(s["place_id"], yy, xx, cy, cx, rad)
        sl = (slice(r0, r1), slice(c0, c1))
        w = blend_w(d, nz[sl])
        win, wlo, whi, wro = h[sl], lo[sl], hi[sl], role[sl]
        disc = d <= 1.0
        facing = 0.0
        scale = 1.0
        # a site overlapping an earlier one is shaped over it (the earlier core's pin released in this disc), and a
        # dry hollow is not held up by the shore grade
        # (a flat inside an earlier flat keeps the earlier ground: a district stands on its city)
        prev = disc & (wlo == whi)
        held = prev.copy() if shape == "flat" else np.zeros_like(prev)
        keep = win.copy()
        if shape != "flat":
            wlo[prev], whi[prev] = -np.inf, np.inf
        if shape == "depression":
            wlo[disc & (wro == 4)] = -np.inf
        fw0 = (foot[sl] | (wro == 2)) if shape == "flat" else np.zeros(disc.shape, bool)  # water and a step's sloped bed
        # a flat keeps its wet samples as water (no plate over a river: test_creature_dens, the audit's §10); a
        # mouth's disc is reserved as ground above any water sharing it
        if shape in ("rise", "bank"):
            # ... except a step's channel (the vanilla join's bed through the edge): a mouth's disc over it would lift
            # the bed to a bank and bury the channel, a wall where the river should step (lane 1.15-r4-ground-steps:
            # 8 of 203 steps lost their channel here)
            wet = disc & ~np.isnan(vmax[sl]) & ~chan[sl]
            whi[wet] = np.inf
            wlo[wet] = np.maximum(np.where(np.isfinite(wlo[wet]), wlo[wet], -np.inf), vmax[sl][wet] + FREEBOARD_M)
            wro[wet] = 3
            # the disc climbs out of the water by Skyrim.esm's shore profile from its rim, never a plate at the
            # level (session 14: the coast's mouths stood on flat discs at vmax + freeboard)
            from tools.argonia_world.terrain.water_field import shore_rise
            rise_ = np.where(wet, shore_rise(np.maximum(1.0 - d, 0.0) * rad), 0.0)
            win[:] = np.maximum(win, np.where(np.isfinite(wlo), wlo + rise_, -np.inf))
        plane = rim_plane(win, d, yy, xx)
        if shape in ("rise", "bank"):
            # the mouth faces the water (a bank) or down the rim plane's slope; the rise stands behind it
            fr = fc = 0.0
            if shape == "bank" and foot[sl].any():
                wy, wx = np.nonzero(foot[sl])
                k = int(np.argmin((wy + r0 - cy) ** 2 + (wx + c0 - cx) ** 2))
                fr, fc = wy[k] + r0 - cy, wx[k] + c0 - cx
            else:
                fr, fc = plane[0, 0] - plane[1, 0], plane[0, 0] - plane[0, 1]  # downhill
            if math.hypot(fr, fc) < 1e-3:
                a_ = np.random.default_rng(zlib.crc32(s["place_id"].encode())).uniform(0, 2 * np.pi)
                fr, fc = -math.cos(a_), math.sin(a_)
            nr, nc = fr / math.hypot(fr, fc), fc / math.hypot(fr, fc)
            facing = float(math.degrees(math.atan2(nc, -nr)) % 360)  # compass: 0 north, 90 east
            L = RISE_L_M / MPP
            u = -((yy - cy) * nr + (xx - cx) * nc) / L  # along the back, in rise lengths
            v = np.abs(-(yy - cy) * nc + (xx - cx) * nr) / max(rad, L)  # across
            sm = lambda t: (lambda c: c * c * (3 - 2 * c))(np.clip(t, 0, 1))
            hill = RISE_M * sm(u / 0.8) * sm((1.4 - v) / 0.6) * sm((2.2 - u) / 0.8)
            ki, kj = min(max(int(round(cy)) - r0, 0), plane.shape[0] - 1), min(max(int(round(cx)) - c0, 0), plane.shape[1] - 1)
            door = float(plane[ki, kj])
            if np.isfinite(wlo[ki, kj]):  # a door held above water stands there; its rise is measured from it
                door = max(door, float(wlo[ki, kj]))
            # the rise is eased in by its own weight (hill / RISE_M): only the ground behind the door is raised, never
            # the whole window to the door's level (session 13: a hillside mouth lifted the flats 100-200 m away by
            # 14-35 m, all five unshaped flats)
            win[:] = np.maximum(win, win + (door + hill - win) * (hill / RISE_M))
            win[:] = np.where(d <= 0.3, np.minimum(win, door + hill), win)  # the door's own ground is cut, not raised
        elif shape == "depression":  # a sinkhole: in a water cell its floor floods (it joins the cell's water)
            win[:] = np.minimum(win, win * (1 - w) + (plane - DEPRESSION_M) * w)
            # the blend cuts the rim too (session 19: the slumped-hamlet's ring fell 241.1 -> 239.3 m to its bank's
            # floor, the plane under it 238.0 -> 235.1 m, the floor 233.96 pinned 1.1 m under it): the disc is dug
            # again from the rim it leaves (clamped as the bank will hold it), never under the lowest water beside it
            plane2 = rim_plane(np.minimum(np.maximum(win, wlo), np.maximum(whi, wlo)), d, yy, xx)
            low_ = np.nanmin(vmin[sl]) - DEPRESSION_M if (~np.isnan(vmin[sl])).any() else -np.inf
            win[:] = np.where(disc, np.minimum(win, win * (1 - w) + np.maximum(plane2 - DEPRESSION_M, low_) * w), win)
            del plane2
            inner = disc & ~np.isnan(vmin[sl]) & ~sbank[sl] & ~chan[sl]
            sunk = inner & (win < vmin[sl])
            wlo[inner] = np.where(sunk[inner], -np.inf, vmax[sl][inner] + FREEBOARD_M)
            whi[inner] = np.where(sunk[inner], vmin[sl][inner] - FREEBOARD_M, np.inf)
            wro[inner] = np.where(sunk[inner], 1, 3)
        elif shape == "flat":
            # a flat is levelled where it can be joined to the water beside it: a flat on a gorge's lip is re-sized
            # to the ground that fits (vanilla's towns on steep ground stand on what the slope leaves: Skyrim.esm's
            # entrance and settlement ground, audit §10, read in reverse: the level ground is cut where the rise allows)
            # the band the ground already allows here: above every bank's cone, below every bed's cone (a step bank
            # uphill, a lake beside), at the slope the limit will join it with
            A = majorant(np.where(np.isfinite(wlo), wlo, -1e9), 0.8 * LIP)
            B = minorant(np.where(np.isfinite(whi), whi, 1e9), 0.8 * LIP)
            scale = 1.0
            while True:
                ds = d / scale
                core = (ds <= 0.6) & ~held & ~fw0
                if not core.any():
                    core = (ds <= 0.6) & ~fw0 if ((ds <= 0.6) & ~fw0).any() else ds <= 0.6
                m = float(np.median(win[core]))
                if np.isfinite(wlo[core]).any():
                    m = max(m, float(wlo[core][np.isfinite(wlo[core])].max()))
                if (A[core] <= m + 0.01).all() and (m <= B[core] + 0.01).all():
                    break
                if scale <= FLAT_MIN_SCALE:  # the smallest flat: cut to the level the band allows (a terrace)
                    lo_m, hi_m = float(A[core].max()), float(B[core].min())
                    if lo_m <= hi_m:
                        m = min(max(m, lo_m), hi_m)
                        note = f"{note}; terraced at {m:.1f} m".strip("; ")
                    else:  # the band is empty (bank cone above, bed cone below): vanilla's hillside town, a
                        # terrace cut into the slope at the banks' level; the place record stays where it is
                        m = lo_m
                        note = f"{note}; terraced into the slope at {m:.1f} m (no level band between bank and water)".strip("; ")
                    break
                scale *= 0.85
            if scale < 1.0:
                note = f"{note}; re-sized to {s['radius_m'] * scale:.0f} m: the ground beside it falls or rises too fast".strip("; ")
                d = ds
                disc = d <= 1.0
                w = blend_w(d, nz[sl])
            wlo[core] = np.minimum(np.where(np.isfinite(wlo[core]), wlo[core], -np.inf), m)
            # levelled to m keeping a damped share of the ground's own relief (Skyrim.esm's towns are level where
            # built, never a plate: the check asks the core's std under 1 m), session 14
            rel_ = win - plane
            sd_ = float(rel_[core].std()) if core.any() else 0.0
            keep_ = min(FLAT_KEEP, FLAT_SD_M / max(sd_, 1e-6))
            tgt = m + keep_ * (rel_ - (float(np.median(rel_[core])) if core.any() else 0.0))
            win[:] = np.where(held | fw0, keep, win * (1 - w) + tgt * w)
        else:  # deep water: a bowl under the cell's level
            bowl = vmin[sl] - DEEP_M - 0.5  # under the lowest water sharing each vertex
            inner = (d <= 0.5) & ~np.isnan(bowl) & (wro != 3) & ~chan[sl]  # a closed bank stays closed
            whi[inner] = np.minimum(whi[inner], bowl[inner])
            wlo[inner] = -np.inf
            wro[inner] = 1
            bowl = np.where(np.isnan(bowl), win, bowl)
            win[:] = np.where(wro == 3, win, np.minimum(win, win * (1 - w) + bowl * w))
        win[:] = np.minimum(np.maximum(win, wlo), np.maximum(whi, wlo))
        # the shaped core pinned (lo = hi) so the slope limit cannot re-slope it (a flat on a hillside, a mouth's door)
        core = d <= (0.6 if shape == "flat" else 0.3 if shape in ("rise", "bank") else 0.35)
        pin = core & ~sbank[sl] & ~held & ~fw0
        if shape == "depression":  # a sinkhole's bank in a water cell is never pinned: its
            # flooded floor (hi under the level) beside its pinned rim drew 15 m single-sample walls (session 17:
            # the province's overflow pairs at -26,59 and 31,50 were the drawdown-flats and slumped-hamlet sinkholes)
            # the flooded floor keeps its pin; the bank within SINK_FREE samples of it is left to the limit
            dfl, _ = chamfer(wro == 1, SINK_FREE)
            pin &= ~np.isfinite(dfl) | (wro == 1)
        fw = foot[sl]
        if fw.any() and "terraced into" not in note:  # a pin no slope can join to the water beside it is left to
            # the limit (no wall into a lake); a terrace cut into the slope keeps its pin (its drop is a cliff)
            df, fl = chamfer(fw, 2 * r + 2, np.where(fw, vmin[sl], np.nan))
            reach_ = np.where(np.isfinite(df), fl + 0.8 * LIP * df, np.inf)
            pin &= win <= reach_
        wlo[pin] = win[pin]
        whi[pin] = win[pin]
        out.append({"place_id": s["place_id"], "shape": shape, "x_m": round(cx * MPP, 2), "y_m": round(cy * MPP, 2),
                    "radius_m": round(s["radius_m"] * scale, 2), "facing_deg": round(facing, 1), "request": note or None})
    return out


def atomic(path: Path, dump, mode: str = "wb") -> None:
    """Write through `<name>.tmp-<pid>` and rename into place: a reader (a build in another tree sharing out/terrain)
    sees the whole old file or the whole new one, and an interrupted write leaves the old one."""
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    try:
        with open(tmp, mode) as f:
            dump(f)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def write(res: dict, out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    atomic(out / "ground-f32.npy", lambda f: np.save(f, res["ground"]))
    atomic(out / "cliff-u8.npy", lambda f: np.save(f, res["cliff"]))
    atomic(out / "role-u8.npy", lambda f: np.save(f, res["role"]))
    if "bridge_decks" in res:  # infra.bridge_placements reads the deck tops from here (one definition)
        atomic(out / "bridge-decks.json", lambda f: f.write(json.dumps(res["bridge_decks"], indent=1) + "\n"), "w")
    if "road_raised" in res:
        from tools.argonia_world.routes.shape import ROAD_RAISED
        atomic(out / ROAD_RAISED, lambda f: np.save(f, res["road_raised"]))
    if "road_water" in res:
        from tools.argonia_world.routes.shape import ROAD_WATER
        atomic(out / ROAD_WATER, lambda f: np.save(f, res["road_water"]))
    atomic(out / "entrance-sites.json", lambda f: f.write(json.dumps(res["sites"], indent=0) + "\n"), "w")
    atomic(out / "generate.json", lambda f: f.write(json.dumps(res["stats"], indent=1, sort_keys=True) + "\n"), "w")
    return res["stats"]


def check(ground: np.ndarray, role: np.ndarray, water: CellWater, sites: list[dict]) -> dict:
    """L1: every cell water fits its ground (no wet vertex at or above the lowest water sharing it; no bank of a
    water cell below the highest; no bank below the upper water at a step outside its channel); every site shaped."""
    g = np.asarray(ground, np.float64)
    vmin, vmax = vertex_levels(water.level)
    wet_bad = (role == 1) & ~(g < vmin)  # NaN (wet with no water over it) counts
    bank_bad = (role == 3) & ~(g > vmax)
    # every vertex a dry cell shares with a water cell stands above that water (no water stopped on a cell edge)
    i = np.arange(N + 1)
    lo_c, hi_c = np.clip((i - 1) // Q, 0, C - 1), np.clip(i // Q, 0, C - 1)
    dryc = np.isnan(water.level)
    touch = np.zeros((N + 1, N + 1), bool)
    for a_ in (lo_c, hi_c):
        for b_ in (lo_c, hi_c):
            touch |= dryc[a_][:, b_]
    dry_bad = touch & ~np.isnan(vmax) & ~(g > vmax)
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
        rr = int(r * SITE_WIN) + 1
        if not (rr <= ci <= N - rr and rr <= cj <= N - rr):
            continue
        big = g[ci - rr:ci + rr + 1, cj - rr:cj + rr + 1]
        by, bx = np.mgrid[ci - rr:ci + rr + 1, cj - rr:cj + rr + 1]
        bd = site_dist(s["place_id"], by, bx, s["y_m"] / MPP, s["x_m"] / MPP, s["radius_m"] / MPP)
        rel = float(g[ci, cj] - rim_plane(big, bd, by, bx)[rr, rr])
        # a flat is judged on its warped core, capped at FLAT_CORE_M (a 228 m city is flat where it is built, not
        # across a whole hillside window)
        wd = site_dist(s["place_id"], yy, xx, s["y_m"] / MPP, s["x_m"] / MPP, s["radius_m"] / MPP)
        own = (wd <= 0.4) & (np.hypot(yy - ci, xx - cj) <= FLAT_CORE_M / MPP) & ~np.isin(role[ci - r:ci + r + 1, cj - r:cj + r + 1], (1, 2))
        for o in sites:  # another site's disc inside this core is that site's ground (a mouth, a district)
            if o is not s and abs(o["x_m"] - s["x_m"]) < o["radius_m"] * SITE_WIN + s["radius_m"] and \
                    abs(o["y_m"] - s["y_m"]) < o["radius_m"] * SITE_WIN + s["radius_m"]:
                own &= site_dist(o["place_id"], yy, xx, o["y_m"] / MPP, o["x_m"] / MPP, o["radius_m"] / MPP) > 1.0
        inner = win[own] if own.any() else np.zeros(1)
        c = float(g[ci, cj])
        lev = vmin[ci, cj]
        back = None
        if s["shape"] in ("rise", "bank"):
            a_ = math.radians(s["facing_deg"])
            L = RISE_L_M / MPP
            bi, bj = int(round(s["y_m"] / MPP + math.cos(a_) * L)), int(round(s["x_m"] / MPP - math.sin(a_) * L))
            back = float(g[min(max(bi, 0), N), min(max(bj, 0), N)] - g[ci, cj])
        ok = {"rise": back is not None and back >= RISE_OK * RISE_M,
              "bank": back is not None and back >= RISE_OK * RISE_M, "depression": rel <= -1.5,
              "flat": float(inner.std()) < 1.0,
              "deep_water": not np.isnan(lev) and lev - c >= DEEP_M}[s["shape"]]
        if not ok:
            site_bad.append((s["place_id"], s["shape"], int(role[ci, cj])))
    # no lattice: the second difference on the 16-sample lines no larger than off them (vanilla LAND has none)
    d2 = np.abs(np.diff(np.asarray(ground[::8], np.float64), 2, axis=1))
    on = (np.arange(1, d2.shape[1] + 1) % 16) == 0
    lattice = round(float(d2[:, on].mean() / max(d2[:, ~on].mean(), 1e-9)), 3)
    return {"lattice_ratio": lattice, "wet_above_water": int(wet_bad.sum()), "bank_below_water": int(bank_bad.sum()),
            "dry_edge_below_water": int(dry_bad.sum()),
            "step_bank_below_upper": step_bad, "sites": len(sites), "sites_unshaped": len(site_bad),
            "sites_unshaped_by": {f"{k[0]}/role{k[1]}": n for k, n in
                                  sorted(__import__("collections").Counter((b[1], b[2]) for b in site_bad).items())},
            "sites_unshaped_ids": [b[0] for b in site_bad[:20]]}
