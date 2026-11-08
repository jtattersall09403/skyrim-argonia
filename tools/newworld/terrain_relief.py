"""Relief: the natural ground of each region before water, places and roads shape it.

Each region gives seven numbers (floor and summit height above the water, roughness, cliff share, wetness, the shore
ramp length, the form). They come from the `region` table (elevation_floor_m, elevation_summit_m, roughness_m,
cliff_share, wetness, landform); a column still empty there takes the FALLBACK row for the landform word in the
region's name. Land beyond the province border (the map's grey) takes the `foreign` row; land in a sea region (an
islet) takes `islet`.

How a height is made:
1. Every parameter is laid on a coarse grid (1024 units) by the region of its cell, blurred by one Morrowind cell
   (sigma), so regions blend over about two cells, and resampled to the heightmap grid.
2. Value noise (seeded, cubic) at four scales (SCALES), sized to a province about 10 km across: big (1.5 km, 700 m),
   mid (300, 150 m), small (60, 25 m), hummock (10 m, strong only on low ground; mesa tops keep 15% of the
   roughness).
3. Form shapes, mixed by the blended form weights:
   hills  = smooth rolling ground (jungle, wood, valley, upland, isle, cape);
   mesa   = flat tops at two levels (about two thirds of the ground) with sheer risers (cliffs), low floors between;
   ridge  = a long spine down the region's main axis (its cells' principal direction), spurs off it;
   low    = hummocks barely above the water, an occasional low rise (swamp, bayou, basin, washes, mangroves, lake).
4. The relief of hills and low ground grows inland: it is scaled by 0.35 + 0.65 (1 - exp(-d / 5 km)), d the distance
   from the open sea, so rivers run downhill to the sea; mesas and ridges keep their full height, hills most of it.
5. Cliff share terraces hills and ridges: 5 x the share (at most 0.9) mixes in steps of a sixth of the region's
   relief with risers a twenty-fifth of a step high in plan; mesa risers are cliffs by design.
"""
from __future__ import annotations

import re

import numpy as np
from scipy import ndimage as ndi

# The one fallback table: replaced, column by column, by the region table's own values once researched.
# floor_m, summit_m: heights above the water; rough_m: hummock relief; cliff: share of steep slopes;
# wet: 0 dry upland .. 1 standing swamp; ramp_m: shore ramp length (how far inland the ground reaches its relief).
FALLBACK = {
    #  landform     floor  summit rough cliff  wet  ramp  form
    "swamp":      (0.4,   4.0,  1.2, 0.00, 0.90, 12, "low"),
    "bayou":      (0.3,   3.0,  1.0, 0.00, 0.95, 10, "low"),
    "mangroves":  (0.3,   2.5,  0.8, 0.00, 1.00,  8, "low"),
    "basin":      (0.5,   6.0,  1.5, 0.00, 0.80, 15, "low"),
    "washes":     (0.5,   8.0,  2.0, 0.02, 0.60, 15, "low"),
    "lake":       (0.5,  10.0,  1.5, 0.00, 0.70, 15, "low"),
    "bight":      (0.6,  15.0,  2.5, 0.02, 0.60, 15, "low"),
    "marsh":      (0.4,   6.0,  1.5, 0.00, 0.85, 12, "low"),
    "wood":       (1.0,  30.0,  3.0, 0.03, 0.60, 25, "hills"),
    "jungle":     (2.0,  60.0,  5.0, 0.05, 0.50, 35, "hills"),
    "valley":     (3.0, 110.0,  6.0, 0.10, 0.30, 40, "hills"),
    "upland":     (5.0, 150.0,  8.0, 0.12, 0.20, 45, "hills"),
    "isle":       (1.0,  45.0,  4.0, 0.08, 0.40, 25, "hills"),
    "archipelago": (0.6, 18.0,  2.5, 0.05, 0.50, 15, "hills"),
    "cape":       (1.0,  35.0,  4.0, 0.10, 0.40, 25, "hills"),
    "mesa":       (5.0, 140.0,  4.0, 0.35, 0.10, 40, "mesa"),
    "ridge":      (5.0, 220.0,  6.0, 0.30, 0.15, 40, "ridge"),
    "foreign":    (2.0,  60.0,  4.0, 0.05, 0.40, 30, "hills"),
    "islet":      (0.5,  10.0,  1.5, 0.02, 0.50, 10, "hills"),
}
# Region names with no landform word: a guess from where they lie, until the research fills `landform`.
NAME_GUESS = {
    "barsaebica": "upland",      # the northern uplands of the Barsaebic Ayleids
    "okuwun-rahei": "upland",    # the eastern interior high ground
    "nha-enasa": "marsh",        # the western lowland beside the Kotherra mangroves
}
WORDS = {"swamp": "swamp", "bayou": "bayou", "mangroves": "mangroves", "basin": "basin", "washes": "washes",
         "lake": "lake", "bight": "bight", "wood": "wood", "murkwood": "wood", "blackwood": "wood",
         "jungle": "jungle", "valley": "valley", "isle": "isle", "archipelago": "archipelago", "cape": "cape",
         "mesa": "mesa", "ridge": "ridge", "upland": "upland", "uplands": "upland", "marsh": "marsh",
         "hills": "upland", "island": "isle", "islands": "archipelago", "bog": "marsh", "floodplain": "basin", "delta": "basin"}
FORMS = ("low", "hills", "mesa", "ridge")
SCALES = {"big": (1500, 700), "mid": (300, 150), "small": (60, 25), "hum": (10,)}   # noise wavelengths, metres
COARSE = 8           # coarse field spacing in samples (1024 units)
BLEND_SIGMA = 8      # coarse samples: one Morrowind cell


def landform_word(text: str | None) -> str | None:
    for w in re.findall(r"[a-z]+", (text or "").lower()):
        if w in WORDS:
            return WORDS[w]
    return None


def region_params(region) -> tuple[dict, str]:
    """A region row -> (params, source note). Database values win column by column over the fallback row."""
    word = landform_word(getattr(region, "landform", None)) or landform_word(region.name) \
        or landform_word(region.id) or NAME_GUESS.get(region.id) or "upland"
    fl, su, ro, cl, we, ramp, form = FALLBACK[word]
    p = {"floor": fl, "summit": su, "rough": ro, "cliff": cl, "wet": we, "ramp": ramp, "form": form}
    used = []
    for col, key in (("elevation_floor_m", "floor"), ("elevation_summit_m", "summit"), ("roughness_m", "rough"),
                     ("cliff_share", "cliff"), ("wetness", "wet")):
        v = getattr(region, col, None)
        if v is not None:
            p[key] = float(v)
            used.append(col)
    src = f"db: {', '.join(used)}; fallback '{word}' for the rest" if used else f"fallback '{word}'"
    return p, src


def upsample(coarse: np.ndarray, shape: tuple[int, int], factor: float, order: int = 3) -> np.ndarray:
    """A coarse field (one value every `factor` samples) resampled onto the full grid."""
    out = np.empty(shape, np.float32)
    jj = np.arange(shape[1], dtype=np.float32) / factor
    pre = ndi.spline_filter(coarse.astype(np.float64), order=order) if order > 1 else coarse.astype(np.float64)
    band = max(1, 2_000_000 // shape[1])
    for i0 in range(0, shape[0], band):
        ii = np.arange(i0, min(shape[0], i0 + band), dtype=np.float32) / factor
        I, J = np.meshgrid(ii, jj, indexing="ij")
        out[i0:i0 + len(ii)] = ndi.map_coordinates(pre, [I, J], order=order, mode="nearest", prefilter=False)
    return out


def noise(shape, wavelength_samples: float, seed: int) -> np.ndarray:
    """Cubic value noise, zero mean and unit spread, with features `wavelength_samples` apart."""
    rng = np.random.default_rng(seed)
    cs = (int(shape[0] / wavelength_samples) + 4, int(shape[1] / wavelength_samples) + 4)
    z = upsample(rng.standard_normal(cs), shape, wavelength_samples)
    z -= z.mean()
    z /= z.std() + 1e-9
    return z


def fbm(shape, step_m: float, wavelengths_m, seed: int) -> np.ndarray:
    out = np.zeros(shape, np.float32)
    total = 0.0
    for k, wl in enumerate(wavelengths_m):
        amp = 1.0 / (k + 1)
        out += amp * noise(shape, max(2.0, wl / step_m), seed * 101 + k)
        total += amp * amp
    return out / np.sqrt(total)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ridge_spine(points_xy: np.ndarray, region_xy: np.ndarray) -> np.ndarray:
    """Spine strength (0..1) at `points_xy` for a ridge region whose cell centres are `region_xy` (world units)."""
    c = region_xy.mean(0)
    u, s, vt = np.linalg.svd(region_xy - c, full_matrices=False)
    axis, perp = vt[0], vt[1]
    d = points_xy - c
    t = d @ axis
    r = d @ perp
    t_max = np.abs((region_xy - c) @ axis).max() + 4096
    w = max(1.2 * np.std((region_xy - c) @ perp), 4096.0)
    return np.exp(-(r / w) ** 2) * np.clip(1 - (np.abs(t) / t_max) ** 4, 0, 1)


def coarse_fields(wx: np.ndarray, wy: np.ndarray, region_of_cell: dict, params: dict, foreign_frac: np.ndarray,
                  sea_regions: set, ridge_cells: dict, cell_units: float = 8192.0) -> dict:
    """Parameter fields on the coarse grid, blended across borders.

    wx, wy: world position of each coarse point; region_of_cell: "cx,cy" -> region id; params: region id (plus
    'foreign' and 'islet') -> params; foreign_frac: share of foreign land at each coarse point; ridge_cells: region
    id -> array of its cell centres (world units)."""
    shape = wx.shape
    cx = np.floor(wx / cell_units).astype(int)
    cy = np.floor(wy / cell_units).astype(int)
    names = sorted(params)
    code = np.full(shape, -1, np.int32)
    lut = {n: k for k, n in enumerate(names)}
    keys = [f"{a},{b}" for a, b in zip(cx.ravel(), cy.ravel())]
    flat = code.ravel()
    for n, key in enumerate(keys):
        r = region_of_cell.get(key)
        if r is not None and r not in sea_regions:
            flat[n] = lut[r]
        elif r is not None:
            flat[n] = lut["islet"] if "islet" in lut else -1
    code = flat.reshape(shape)
    code[(code < 0) | (foreign_frac > 0.5)] = lut["foreign"]
    fields = {}
    for key in ("floor", "summit", "rough", "cliff", "wet", "ramp"):
        vals = np.array([params[n][key] for n in names], np.float64)
        fields[key] = ndi.gaussian_filter(vals[code], BLEND_SIGMA, mode="nearest")
    for form in FORMS:
        vals = np.array([params[n]["form"] == form for n in names], np.float64)
        fields["w_" + form] = ndi.gaussian_filter(vals[code], BLEND_SIGMA, mode="nearest")
    spine = np.zeros(shape)
    for rid, cells_xy in ridge_cells.items():
        near = ndi.binary_dilation(code == lut[rid], iterations=3 * BLEND_SIGMA)
        pts = np.stack([wx[near], wy[near]], 1)
        spine[near] = np.maximum(spine[near], ridge_spine(pts, cells_xy))
    fields["spine"] = ndi.gaussian_filter(spine, BLEND_SIGMA / 2, mode="nearest")
    return fields


def relief(F: dict, n: dict, coast_t: np.ndarray) -> np.ndarray:
    """Natural ground height (metres above the water) from full-resolution fields F and noise n."""
    hill = np.clip(0.5 + 0.22 * (0.7 * n["big"] + 0.5 * n["mid"]), 0, 1) ** 1.6
    m = 0.6 * n["big"] + 0.4 * n["mid"] + 0.04 * n["small"]
    plateau = 0.55 * smoothstep(-0.35, -0.33, m) + 0.45 * smoothstep(0.45, 0.47, m)
    mesa = 0.12 * hill + 0.88 * plateau
    ridge = np.clip(F["spine"] * (0.8 + 0.12 * n["mid"]) + 0.25 * hill * (1 - F["spine"])
                    + 0.08 * np.abs(n["small"]) * F["spine"], 0, 1)
    low = 0.3 * hill ** 2
    rel = F["w_hills"] * hill + F["w_mesa"] * mesa + F["w_ridge"] * ridge + F["w_low"] * low
    span = np.maximum(F["summit"] - F["floor"], 0)
    inland = 0.35 + 0.65 * coast_t
    keep = np.clip(F["w_mesa"] + F["w_ridge"] + 0.6 * F["w_hills"], 0, 1)
    h = F["floor"] + span * rel * (inland + (1 - inland) * keep)
    # terraces: cliff share mixes in steps with sheer risers (hills and ridges; mesas have their own)
    step = np.maximum(span / 6.0, 1.0)
    q = (h - F["floor"]) / step
    terr = F["floor"] + step * (np.floor(q) + smoothstep(0.93, 0.97, q - np.floor(q)))
    c = np.clip(F["cliff"] * 5.0, 0, 0.9) * (1 - F["w_mesa"]) * (1 - F["w_low"])
    h = (1 - c) * h + c * terr
    tops = F["w_mesa"] * plateau                     # mesa tops stay flat
    h += F["rough"] * (0.35 * n["small"] + (0.08 + 0.25 * F["w_low"]) * n["hum"]) * (1 - 0.85 * tops)
    return np.maximum(h, F["floor"] * 0.5).astype(np.float32)
