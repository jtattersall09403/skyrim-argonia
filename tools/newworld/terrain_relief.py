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
5. A region with a relief character (terrain_forms) keeps only its `base` share of this shared relief over its
   floor; mesa plateaus and escarpment faces fade out near roads (F["road_fade"], when given).
6. Cliff share terraces hills and ridges: 5 x the share (at most 0.9) mixes in steps of a sixth of the region's
   relief with risers a twenty-fifth of a step high in plan; mesa risers are cliffs by design.
"""
from __future__ import annotations

import re

import numpy as np
from scipy import ndimage as ndi

# The one fallback table: replaced, column by column, by the region table's own values once researched.
# floor_m, summit_m: heights above the water; rough_m: hummock relief; cliff: share of steep slopes;
# wet: 0 dry upland .. 1 standing swamp; ramp_m: shore ramp length (how far inland the ground reaches its relief).
# Low ground ramps over 6 m: BM&V's marsh is level about 1.7 m up by 10 to 16 m inland (terrain-measurements.md).
FALLBACK = {
    #  landform     floor  summit rough cliff  wet  ramp  form
    "swamp":      (0.4,   4.0,  1.2, 0.00, 0.90,  6, "low"),
    "bayou":      (0.3,   3.0,  1.0, 0.00, 0.95,  6, "low"),
    "mangroves":  (0.3,   2.5,  0.8, 0.00, 1.00,  6, "low"),
    "basin":      (0.5,   6.0,  1.5, 0.00, 0.80,  6, "low"),
    "washes":     (0.5,   8.0,  2.0, 0.02, 0.60,  6, "low"),
    "lake":       (0.5,  10.0,  1.5, 0.00, 0.70,  6, "low"),
    "bight":      (0.6,  15.0,  2.5, 0.02, 0.60,  6, "low"),
    "marsh":      (0.4,   6.0,  1.5, 0.00, 0.85,  6, "low"),
    "wood":       (1.0,  30.0,  3.0, 0.03, 0.60, 25, "hills"),
    "jungle":     (2.0,  60.0,  5.0, 0.05, 0.50, 35, "hills"),
    "valley":     (3.0, 110.0,  6.0, 0.10, 0.30, 40, "hills"),
    "upland":     (5.0, 150.0,  8.0, 0.12, 0.20, 45, "hills"),
    "isle":       (1.0,  45.0,  4.0, 0.08, 0.40, 25, "hills"),
    "archipelago": (0.6, 18.0,  2.5, 0.05, 0.50, 15, "hills"),
    "cape":       (1.0,  35.0,  4.0, 0.10, 0.40, 25, "hills"),
    "mesa":       (5.0, 140.0,  4.0, 0.35, 0.10, 40, "mesa"),
    "ridge":      (5.0, 220.0,  6.0, 0.30, 0.15, 40, "ridge"),
    # land past the border and past the map: Cyrodiil's Blackwood and Nibenay lowland, Morrowind's Deshaan plain:
    # modest generic hills, never a mountain wall
    "foreign":    (2.0,  40.0,  3.0, 0.03, 0.45, 30, "hills"),
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
SCALES = {"swell": (3000, 1600), "big": (1500, 700), "mid": (300, 150), "small": (60, 25),
          "knoll": (450, 200, 120), "amod": (2500,), "micro": (12, 6), "esc": (900, 350)}   # noise wavelengths, metres
WARP_M = ((2400, 420), (700, 130), (180, 30))   # domain warp: (wavelength, amplitude) metres
EDGE_WARP_M = ((240, 60), (110, 16))            # extra warp for escarpment edges: spurs and re-entrants
MID_SHARE = 0.35     # mid-scale landform amplitude: share of the region's relief span
MID_ROUGH = 4.0      # ... or this many times its roughness
BMV_MARSH_FLOOR_M = 1.7   # BM&V's marsh lies level about 1.7 m above the water from about 10 m inland
BMV_MARSH_RAMP_M = 7.0    # its shore: 0.11 m at the water, 0.46 at 4 m, 1.03 at 8 m, 1.71 at 16 m
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
    if p["form"] == "low":            # Bethesda's numbers for marsh, whatever the table's floor
        p["floor"], p["ramp"] = BMV_MARSH_FLOOR_M, BMV_MARSH_RAMP_M
        src += f"; low ground at BM&V's {BMV_MARSH_FLOOR_M} m floor and {BMV_MARSH_RAMP_M} m shore ramp"
    return p, src


def upsample(coarse: np.ndarray, shape: tuple[int, int], factor: float, order: int = 3, warp=None) -> np.ndarray:
    """A coarse field (one value every `factor` samples) resampled onto the full grid; `warp` (di, dj), offsets in
    samples, reads it at displaced positions (domain warping)."""
    out = np.empty(shape, np.float32)
    jj = np.arange(shape[1], dtype=np.float32) / factor
    pre = ndi.spline_filter(coarse.astype(np.float64), order=order) if order > 1 else coarse.astype(np.float64)
    band = max(1, 2_000_000 // shape[1])
    for i0 in range(0, shape[0], band):
        ii = np.arange(i0, min(shape[0], i0 + band), dtype=np.float32) / factor
        I, J = np.meshgrid(ii, jj, indexing="ij")
        if warp is not None:
            I = I + warp[0][i0:i0 + len(ii)] / factor + 2
            J = J + warp[1][i0:i0 + len(ii)] / factor + 2
        out[i0:i0 + len(ii)] = ndi.map_coordinates(pre, [I, J], order=order, mode="nearest", prefilter=False)
    return out


def noise(shape, wavelength_samples: float, seed: int, warp=None) -> np.ndarray:
    """Cubic value noise, zero mean and unit spread, with features `wavelength_samples` apart; `warp` as upsample."""
    rng = np.random.default_rng(seed)
    pad = 4 if warp is None else 8
    cs = (int(shape[0] / wavelength_samples) + pad, int(shape[1] / wavelength_samples) + pad)
    z = upsample(rng.standard_normal(cs), shape, wavelength_samples, warp=warp)
    z -= z.mean()
    z /= z.std() + 1e-9
    return z


def fbm(shape, step_m: float, wavelengths_m, seed: int, warp=None) -> np.ndarray:
    out = np.zeros(shape, np.float32)
    total = 0.0
    for k, wl in enumerate(wavelengths_m):
        amp = 1.0 / (k + 1)
        out += amp * noise(shape, max(2.0, wl / step_m), seed * 101 + k, warp)
        total += amp * amp
    return out / np.sqrt(total)


def warp_field(shape, step_m: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Domain-warp offsets (samples): WARP_M = ((wavelength m, amplitude m), ...) summed, so contours of anything
    read through it wander, embay and lobe at every scale instead of tracing one smooth noise level."""
    out = []
    for a in range(2):
        w = np.zeros(shape, np.float32)
        for k, (wl, amp) in enumerate(WARP_M):
            w += (amp / step_m) * noise(shape, max(2.0, wl / step_m), seed * 31 + 10 * a + k)
        out.append(w)
    return out[0], out[1]


def edge_field(shape, step_m: float, seed: int, warp) -> np.ndarray:
    """The field whose levels are mesa edges (0.6 big + 0.4 mid + 0.12 esc, the same noises as the relief) read
    through the main warp plus a fine one (EDGE_WARP_M), so an escarpment's edge is crenellated by spurs and
    re-entrants at 100 to 300 m rather than one smooth curve."""
    wi, wj = (w.copy() for w in warp)
    for k, (wl, amp) in enumerate(EDGE_WARP_M):
        wi += (amp / step_m) * noise(shape, wl / step_m, seed * 37 + k)
        wj += (amp / step_m) * noise(shape, wl / step_m, seed * 37 + 10 + k)
    return (0.6 * fbm(shape, step_m, SCALES["big"], seed, (wi, wj))
            + 0.4 * fbm(shape, step_m, SCALES["mid"], seed + 1, (wi, wj))
            + 0.12 * fbm(shape, step_m, SCALES["esc"], seed + 9, (wi, wj)))


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
    fields = {"_code": code, "_lut": lut}
    for key in ("floor", "summit", "rough", "cliff", "wet", "ramp", "base"):
        vals = np.array([params[n].get(key, 1.0) for n in names], np.float64)
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
    """Natural ground height (metres above the water) from full-resolution fields F and noise n (the large noises
    read through one domain warp, so no shape traces a single smooth noise contour).

    Large landforms first: swells and swales at 1.6 to 3 km under everything (low in marsh, real hills in uplands),
    hills at 0.7 to 1.5 km, knolls, spurs and swales at 120 to 450 m whose amplitude varies over 2.5 km, so some
    ground is busy and some calm. Low ground is BM&V's flat floor with broad low swells and sparse hummocks. Cliff
    share makes escarpments: a few single steep faces where a warped 350 to 900 m field crosses its level, never
    stacked terraces; mesa risers are cut the same way, so their edges lobe and embay. No isotropic fine noise: fine
    detail is added after erosion, by slope and drainage (terrain_erode)."""
    amod = smoothstep(-0.9, 1.0, n["amod"])
    ridg = 1 - np.sqrt(n["knoll"] ** 2 + 0.03)              # crests a little rounded, never a crease
    knolls = amod * (ridg - 0.55)
    base = np.clip(0.5 + 0.22 * (0.55 * n["swell"] + 0.6 * n["big"] + 0.45 * n["mid"]), 0, 1)
    hill = np.clip(base + 0.4 * knolls, 0, 1.2) ** 1.6
    m = n["edge"]
    # roads run in the cuts between mesas and below escarpments, never up a cliff: both fade out near a road
    rf = F.get("road_fade", 1.0)
    plateau = (0.55 * smoothstep(-0.38, -0.29, m) + 0.45 * smoothstep(0.42, 0.51, m)) * rf
    mesa = 0.25 * hill + 0.75 * plateau
    ridge = F["spine"] * (0.5 + 0.35 * hill + 0.1 * n["mid"]) + 0.25 * hill * (1 - F["spine"])
    ridge = np.maximum(ridge, 0) / (1 + 0.3 * np.maximum(ridge, 0))          # soft top, no clipped flat
    hummock = np.clip(ridg - 0.7, 0, None) / 0.3 * amod      # sparse, soft, varied
    swell = smoothstep(-1.2, 1.4, n["swell"] + 0.35 * n["big"])
    low = 0.22 * swell ** 2 + 0.06 * np.clip(base, 0, 1) ** 3 + 0.2 * hummock ** 2
    rel = F["w_hills"] * hill + F["w_mesa"] * mesa + F["w_ridge"] * ridge + F["w_low"] * low
    span = np.maximum(F["summit"] - F["floor"], 0)
    inland = 0.35 + 0.65 * coast_t
    keep = np.clip(F["w_mesa"] + F["w_ridge"] + 0.6 * F["w_hills"], 0, 1)
    h = F["floor"] + span * rel * (inland + (1 - inland) * keep)
    # mid-scale landforms in metres, not a share of the broad shape: knolls, spurs and swales at 120 to 450 m, their
    # amplitude a share of the span (MID_SHARE) or a multiple of the roughness, whichever is more, varying over
    # 2.5 km; on low ground only soft swells of about the roughness
    a_mid = np.maximum(MID_SHARE * span, MID_ROUGH * F["rough"]) * (F["w_hills"] + F["w_ridge"] + 0.8 * F["w_mesa"])
    a_mid = a_mid + 1.6 * F["rough"] * F["w_low"]
    h = h + a_mid * (0.25 + amod) * (ridg - 0.45) * np.clip(0.6 + coast_t, 0, 1)
    # escarpments: one steep face (about a fifth of the relief) where the warped field crosses its level; the cliff
    # share sets how much ground lies above one
    c = np.clip(F["cliff"] * 3.0, 0, 0.8) * (1 - F["w_mesa"]) * (1 - F["w_low"])
    e = n["esc"] + 0.5 * n["big"] + 0.06 * n["small"]
    face = (smoothstep(0.30, 0.40, e) + smoothstep(0.95, 1.05, e)) * rf
    h = h + c * 0.22 * span * face * smoothstep(-0.6, 0.4, n["mid"])      # faces die out and return along their run
    tops = F["w_mesa"] * plateau
    # mesa tops: level overall, but with low knolls and shallow swales (about 12% of the relief), never a slab
    h += tops * 0.12 * span * (0.4 + amod) * (ridg - 0.45)
    h += F["rough"] * 0.05 * n["small"] * (1 - 0.85 * tops) * (1 - 0.7 * F["w_low"])
    # the region's character keeps only `base` of the shared relief (terrain_forms adds its own landform)
    h = F["floor"] + F.get("base", 1.0) * (h - F["floor"])
    h += 0.11 * n["micro"]          # micro relief over a LAND step: no 8-unit contour ribbons on gentle ground
    lo = F["floor"] * 0.5            # a soft floor: ground pressed below it eases onto it, never a clipped flat
    return (0.5 * (h + lo + np.sqrt((h - lo) ** 2 + 4.0))).astype(np.float32)
