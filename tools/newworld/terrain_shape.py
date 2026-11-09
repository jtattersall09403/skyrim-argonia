"""Shaping the heightmap: the grid, water and banks, the map's water guaranteed, places' needs, roads, LAND's format.

All heights here are game units (70 a metre) with the water level at WATER_LEVEL = 0.

The grid. Samples every 128 units (Skyrim's LAND vertex spacing), row 0 the north edge, so a Skyrim cell is 33 x 33
samples sharing its edges with its neighbours; a sample's map position is p0 + k (j, i) px, k = 128 / 204.8.

Water and banks. Every sample takes the class of the map pixel under it (beyond the map: sea). Distances to the
shore are measured on the sample grid. Land rises from FREEBOARD at the shore toward its relief over the region's
shore ramp, h = fb + (relief - fb)(1 - exp(-d / ramp)); water falls from MIN_DEPTH at the shore along the bed slope
of its kind to the kind's cap, so a channel's depth follows its width (the deepest point is half the width in) and
the sea floor keeps deepening offshore.

The map's water held. terrain_coast turns the map's water into a smooth signed distance on the samples (its shore
a natural curve, its shape the map's at map scale); every water sample is held one LAND step under the water level
and every land sample one over it (hold_water). The map's own pixels are then matched on 4 px blocks, not pixel by
pixel, since the coast now runs between them.

Places. Needs come from `place_terrain_need`; a place with no row there takes its kind's fallback (FALLBACK_NEEDS):
- flat-pad: a plane fitted to the land under an irregular footprint (tilted with the land up to 2.5 deg, keeping a
  quarter of the fine relief), eased out over a skirt as wide as the radius (at least 40 m); water in it is left
  alone (stilts);
- entrance-in-slope: a knoll 8 m high added to the ground behind the entrance, its face 6 m deep holding the
  opening, its back and sides easing out over 45 and 28 m; in front a corridor eased to at most 1 in 3;
- rise: a mound of 3 to 12 m over the footprint; shore-access: a low pad 0.4 m above the water;
- seabed: the bed under the place is lowered to the needed depth (sunken ruin 8 m, wreck 5 m);
- island: nothing (the map's islands are kept by the water guarantee).

Roads (Skyrim's way, measured on Skyrim.esm): the centreline height is the ground smoothed along the road (sigma
15 m), held at least 0.4 m above the water and to the class's grade (grade_max less 10% headroom) by forward and
backward passes; the cross profile is the measured trough (flat to 1.5 m out, then 0.10 m down at 2 m, 0.42 at 4 m,
0.75 at 6 m, 1.03 at 8 m from the centre, minor roads two thirds of it) feathered into the ground by 14 m (major)
or 9 m (minor), cut only: past the bed the walls lower ground above them and never raise ground below, so a road
sits in the land, not on a strip. Only land samples are shaped: where the road meets water a crossing is recorded (a ford when the
water is up to FORD_M wide, else a bridge), and the water stays as drawn.

LAND's format. Heights are rounded to 8 units (VHGT stores int8 steps of 8 units); a step between neighbours over
127 x 8 units cannot be stored, so peaks are lowered until every step fits.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

U = 70.0                      # units a metre
STEP = 128.0                  # LAND vertex spacing
WATER_LEVEL = 0.0
FREEBOARD = 0.3 * U           # land at the shore
MIN_DEPTH = 0.3 * U           # water at the shore
CHECK_MARGIN = 0.1 * U
SHORE_M = 0.12                # land and water at the smooth shore (BM&V: 0.11 m at the water's edge)
QUANT = 8.0
MAX_STEP = 127 * QUANT
FORD_M = 8.0
# bed: (slope down from the shore, cap in metres)
BED = {"ocean": (0.30, 80.0), "bay": (0.30, 30.0), "estuary": (0.10, 5.0), "river": (0.10, 4.0),
       "stream": (0.12, 1.2), "lake": (0.20, 15.0), "pond": (0.15, 2.5), "blackwater-swamp": (0.10, 1.5),
       "green-marsh": (0.08, 0.9)}   # measured: sea bed 0.9 m at 4 m, 5.3 m at 16 m; channel depth ~0.05 x width
TROUGH_D = np.array([0.0, 1.5, 2.0, 4.0, 6.0, 8.0, 99.0])
TROUGH_M = np.array([0.0, 0.0, 0.10, 0.42, 0.75, 1.03, 1.03])
MAX_CUT_M = 8.0
FEATHER_M = {"major": 14.0, "minor": 9.0}
TROUGH_SCALE = {"major": 1.0, "minor": 0.66}
ENTRANCE_KINDS = {"cave", "mine", "ayleid-ruin", "kothringi-ruin", "imperial-ruin", "velothi-ruin",
                  "lilmothiit-ruin"}
FALLBACK_NEEDS = {k: "entrance-in-slope" for k in ENTRANCE_KINDS} | {
    "keep": "rise", "lighthouse": "rise", "belvedere": "rise", "peak": "rise",
    "ferry": "shore-access", "sunken-ruin": "seabed", "shipwreck": "seabed",
    "city": "flat-pad", "town": "flat-pad", "village": "flat-pad", "hamlet": "flat-pad", "outpost": "flat-pad",
    "fort": "flat-pad", "prison": "flat-pad", "estate": "flat-pad", "farm": "flat-pad", "homestead": "flat-pad",
    "logging-camp": "flat-pad", "tribal-camp": "flat-pad", "outlaw-camp": "flat-pad", "quarry": "flat-pad",
    "abandoned-village": "flat-pad", "station": None, "landmark": None}


@dataclass
class Grid:
    rows: int
    cols: int
    p0x: float           # map px of sample (0, 0)
    p0y: float
    k: float = STEP / 204.8   # map px per sample
    ox: float = 0.0       # world position of sample (0, 0)
    oy: float = 0.0

    @property
    def m(self) -> float:
        return self.k * 2.925714  # metres per sample (128 / 70)

    def px(self, i, j):
        return self.p0x + np.asarray(j) * self.k, self.p0y + np.asarray(i) * self.k

    def ij(self, px, py):
        return (np.asarray(py) - self.p0y) / self.k, (np.asarray(px) - self.p0x) / self.k


def sample_classes(grid: Grid, water_px: np.ndarray) -> np.ndarray:
    """Water (True) per sample from the map pixel under it; off the map is sea."""
    jx = np.floor(grid.p0x + np.arange(grid.cols) * grid.k).astype(int)
    iy = np.floor(grid.p0y + np.arange(grid.rows) * grid.k).astype(int)
    H, W = water_px.shape
    out = np.ones((grid.rows, grid.cols), bool)
    oki, okj = (iy >= 0) & (iy < H), (jx >= 0) & (jx < W)
    out[np.ix_(oki, okj)] = water_px[np.ix_(iy[oki], jx[okj])]
    return out


def compose(water_s: np.ndarray, relief_m: np.ndarray, ramp_m: np.ndarray, bed_slope: np.ndarray,
            bed_cap_m: np.ndarray, m_per_sample: float, sd_m: np.ndarray | None = None
            ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Land and water heights (units) from the classes and relief. Returns (h, d_land_m, d_water_m).

    With `sd_m` (terrain_coast's smooth signed distance, metres) the distances are read from it, so heights near
    the shore follow the smooth coast between samples and the shore sits at SHORE_M (BM&V: 0.11 m at the water)."""
    if sd_m is None:
        d_land = np.maximum(ndi.distance_transform_edt(~water_s) * m_per_sample - m_per_sample / 2, 0)
        d_water = np.maximum(ndi.distance_transform_edt(water_s) * m_per_sample - m_per_sample / 2, 0)
        fb, wb = FREEBOARD / U, MIN_DEPTH / U
    else:
        d_land, d_water = np.maximum(sd_m, 0), np.maximum(-sd_m, 0)
        fb = wb = SHORE_M
    d_land, d_water = d_land.astype(np.float32), d_water.astype(np.float32)
    land = fb + np.maximum(relief_m - fb, 0) * (1 - np.exp(-d_land / np.maximum(ramp_m, 1)))
    depth = np.minimum(wb + bed_slope * d_water, np.maximum(bed_cap_m, wb))
    h = np.where(water_s, -depth, land) * U
    return h.astype(np.float32), d_land, d_water


def pixel_values(h: np.ndarray, grid: Grid, px_box: tuple[int, int, int, int]):
    """Bilinear heights at every map pixel centre in px_box (left, top, right, bottom); plus the sample coords."""
    l, t, r, b = px_box
    py, px = np.mgrid[t:b, l:r].astype(np.float32) + 0.5
    i, j = grid.ij(px, py)
    return ndi.map_coordinates(h, [i, j], order=1, mode="nearest"), i, j


def px_box(grid: Grid, shape: tuple[int, int]) -> tuple[int, int, int, int]:
    """Map pixels whose centres lie inside the grid (and on the map)."""
    l = max(0, math.ceil(grid.p0x - 0.5))
    t = max(0, math.ceil(grid.p0y - 0.5))
    r = min(shape[1], math.floor(grid.p0x + (grid.cols - 1) * grid.k - 0.5) + 1)
    b = min(shape[0], math.floor(grid.p0y + (grid.rows - 1) * grid.k - 0.5) + 1)
    return l, t, r, b


def guarantee(h: np.ndarray, grid: Grid, water_px: np.ndarray, rounds: int = 16) -> list:
    """Push samples until every map pixel reads on its side of the water level. Returns pixels still failing."""
    box = px_box(grid, water_px.shape)
    l, t, r, b = box
    wat = water_px[t:b, l:r]
    bad = []
    for _ in range(rounds):
        v, i, j = pixel_values(h, grid, box)
        land_short = np.where(~wat, (WATER_LEVEL + CHECK_MARGIN) - v, 0)
        water_short = np.where(wat, v - (WATER_LEVEL - CHECK_MARGIN), 0)
        bad = np.argwhere((land_short > 0) | (water_short > 0))
        if not len(bad):
            return []
        for short, sign, fn in ((land_short, 1, np.maximum), (water_short, -1, np.minimum)):
            sel = short > 0
            if not sel.any():
                continue
            ii, jj = np.floor(i[sel]).astype(int), np.floor(j[sel]).astype(int)
            push = np.ceil(short[sel] / QUANT) * QUANT
            for di in (0, 1):
                for dj in (0, 1):
                    a, c = np.clip(ii + di, 0, grid.rows - 1), np.clip(jj + dj, 0, grid.cols - 1)
                    fn.at(h, (a, c), h[a, c] + sign * push)
    return [(int(x + l), int(y + t)) for y, x in bad]


def hold_water(h: np.ndarray, water_s: np.ndarray) -> int:
    """Every water sample at least one LAND step under the water level, every land sample one over it (the smooth
    coast decides which is which). Mutates h; returns the samples moved."""
    lo = water_s & (h > WATER_LEVEL - QUANT)
    hi = ~water_s & (h < WATER_LEVEL + QUANT)
    h[lo] = WATER_LEVEL - QUANT
    h[hi] = WATER_LEVEL + QUANT
    return int(lo.sum() + hi.sum())


def quantise(h: np.ndarray) -> np.ndarray:
    """Heights onto the LAND step (QUANT units), dithered: a fixed fine pattern (a few samples across, half a step)
    decides the rounding where the ground leans gently (level ground stays one level), so gentle ground does not show its step edges as long contour ribbons."""
    from tools.newworld.terrain_relief import noise
    d = np.empty(h.shape, np.float32)
    band = 1024
    for i0 in range(0, h.shape[0], band):
        d[i0:i0 + band] = noise((min(band, h.shape[0] - i0), h.shape[1]), 2.5, 4409 + i0)
    # only where the ground leans a little (a step every 1 to 20 samples): level ground stays one clean level,
    # steeper ground has no ribbons to hide
    g = np.hypot(*np.gradient(ndi.gaussian_filter(h, 1.5))) / QUANT
    d = np.clip(d * 0.22, -0.45, 0.45) * np.clip((g - 0.05) / 0.1, 0, 1) * np.clip((1.5 - g) / 0.5, 0, 1)
    return (np.round(h / QUANT + d) * QUANT).astype(np.float32)


def clamp_steps(h: np.ndarray, limit: float = MAX_STEP, passes: int = 200) -> int:
    """Lower peaks until every step between 4-neighbours is at most `limit`. Returns passes used."""
    for n in range(passes):
        m = h.copy()
        m[:-1] = np.minimum(m[:-1], h[1:] + limit)
        m[1:] = np.minimum(m[1:], h[:-1] + limit)
        m[:, :-1] = np.minimum(m[:, :-1], h[:, 1:] + limit)
        m[:, 1:] = np.minimum(m[:, 1:], h[:, :-1] + limit)
        if np.array_equal(m, h):
            return n
        h[:] = m
    return passes


def land_format(h: np.ndarray) -> dict:
    """Does the grid fit LAND records: whole Skyrim cells, heights on the 8-unit step, every step storable."""
    q = h / QUANT
    sx = np.abs(np.diff(h, axis=1)).max() if h.shape[1] > 1 else 0
    sy = np.abs(np.diff(h, axis=0)).max() if h.shape[0] > 1 else 0
    return {"whole_cells": (h.shape[0] - 1) % 32 == 0 and (h.shape[1] - 1) % 32 == 0,
            "on_step": bool(np.all(q == np.round(q))), "max_step_units": float(max(sx, sy)),
            "steps_fit": bool(max(sx, sy) <= MAX_STEP),
            "ok": (h.shape[0] - 1) % 32 == 0 and (h.shape[1] - 1) % 32 == 0 and bool(np.all(q == np.round(q)))
            and bool(max(sx, sy) <= MAX_STEP)}


def slope_deg(h: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(h, STEP)
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)


# ---- places -------------------------------------------------------------------------------------------------

def _disc(grid: Grid, i0: float, j0: float, r_samples: float):
    a0, a1 = max(0, int(i0 - r_samples) - 1), min(grid.rows, int(i0 + r_samples) + 2)
    b0, b1 = max(0, int(j0 - r_samples) - 1), min(grid.cols, int(j0 + r_samples) + 2)
    I, J = np.mgrid[a0:a1, b0:b1]
    return (slice(a0, a1), slice(b0, b1)), I - i0, J - j0


def _ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


PAD_TILT_DEG = 6.0            # a pad follows the land's lie up to this tilt
PAD_KEEP = 0.4                # share of the land's fine relief a pad keeps


def wobble(i0: float, j0: float, theta: np.ndarray, amount: float = 0.25) -> np.ndarray:
    """A footprint's radius factor by heading: a few low harmonics seeded by the place, so no footprint is a circle."""
    rng = np.random.default_rng(int(abs(i0) * 7919 + abs(j0) * 104729) % (2 ** 32))
    out = np.zeros_like(theta)
    for k in (2, 3, 5):
        out += rng.normal(0, 1.0 / k) * np.cos(k * theta + rng.uniform(0, 2 * np.pi))
    return 1 + amount * out / 0.8


def flat_pad(h, water_s, grid, i0, j0, r_m, floor_units=None):
    """A buildable pad that still reads as ground: a plane fitted to the land under an irregular footprint (tilted
    with the land, at most PAD_TILT_DEG), keeping PAD_KEEP of the land's fine relief, eased back into the ground
    over a skirt as wide as the radius (at least 40 m) with zero slope at both ends: no rim, no bowl, no circle.
    Returns the pad's height at the centre (units)."""
    skirt = max(40.0, r_m)
    sl, di, dj = _disc(grid, i0, j0, (1.3 * r_m + skirt) / grid.m)
    d = np.hypot(di, dj) * grid.m
    rr = r_m * wobble(i0, j0, np.arctan2(di, dj))
    land = ~water_s[sl]
    inner = land & (d <= rr)
    if not inner.any():
        return None
    win = h[sl].astype(np.float64)
    smooth = ndi.gaussian_filter(win, max(1.0, r_m / grid.m / 3), mode="nearest")
    if floor_units is None:
        A = np.stack([di[inner] * grid.m, dj[inner] * grid.m, np.ones(inner.sum())], 1)
        gi, gj, c0 = np.linalg.lstsq(A, smooth[inner], rcond=None)[0]
        g = math.hypot(gi, gj)
        lim = math.tan(math.radians(PAD_TILT_DEG)) * U
        if g > lim:
            gi, gj = gi * lim / g, gj * lim / g
        c0 = max(c0, FREEBOARD + 0.5 * U)
        plane = c0 + gi * di * grid.m + gj * dj * grid.m
    else:
        c0 = floor_units
        plane = np.full(win.shape, c0)
    target = plane + PAD_KEEP * (win - smooth)
    x = np.clip((d - rr) / skirt, 0, 1)
    w = 1 - x * x * x * (x * (6 * x - 15) + 10)       # smootherstep: no crease at either edge
    h[sl] = np.where(land, win * (1 - w) + target * w, win).astype(h.dtype)
    return float(c0)


def shore_access(h, water_s, grid, i0, j0, r_m):
    """Within the radius, land near the water eases down to a gentle shore (1 in 8) to the waterline."""
    sl, di, dj = _disc(grid, i0, j0, (r_m + 20) / grid.m)
    if not water_s[sl].any():           # no water in reach: nothing to give access to (no dish dug in dry ground)
        return
    d = np.hypot(di, dj) * grid.m
    dw = ndi.distance_transform_edt(~water_s[sl]) * grid.m
    target = FREEBOARD + 0.125 * dw * U
    x = np.clip((d - r_m) / 20.0, 0, 1)
    w = 1 - x * x * (3 - 2 * x)
    land = ~water_s[sl]
    h[sl] = np.where(land, np.minimum(h[sl], h[sl] * (1 - w) + np.minimum(h[sl], target) * w), h[sl])


def rise(h, water_s, grid, i0, j0, r_m):
    H = float(np.clip(0.1 * r_m + 3, 3, 12)) * U
    sl, di, dj = _disc(grid, i0, j0, 1.6 * r_m / grid.m)
    d = np.hypot(di, dj) * grid.m
    h[sl] = np.where(~water_s[sl], h[sl] + H * (1 - _ease(d / (1.6 * r_m))), h[sl])


def seabed(h, water_s, grid, i0, j0, r_m, depth_m):
    sl, di, dj = _disc(grid, i0, j0, 2 * r_m / grid.m)
    d = np.hypot(di, dj) * grid.m
    target = -depth_m * U * (1 - _ease((d - r_m) / r_m))
    h[sl] = np.where(water_s[sl], np.minimum(h[sl], target), h[sl])


def _ray(grid, i0, j0, deg, t0, t1, step=1.0):
    a = math.radians(deg)
    ts_ = np.arange(t0, t1 + 1e-9, step) / grid.m
    return i0 - ts_ * math.cos(a), j0 + ts_ * math.sin(a)


def ray_dry(water_s, grid, i0, j0, deg, reach=24.0) -> float:
    ii, jj = _ray(grid, i0, j0, deg, 0, reach)
    if ii.min() < 0 or jj.min() < 0 or ii.max() > grid.rows - 1 or jj.max() > grid.cols - 1:
        return 0.0
    ii2, jj2 = [ii], [jj]
    a = math.radians(deg + 90)
    for side in (-3.0, 3.0):                          # the corridor 3 m either side
        ii2.append(ii - side / grid.m * math.cos(a))
        jj2.append(jj + side / grid.m * math.sin(a))
    wet = ndi.map_coordinates(water_s.astype(np.float32), [np.concatenate(ii2), np.concatenate(jj2)], order=0)
    return float(1 - wet.max())


def choose_facing(h, water_s, grid, i0, j0, prefer=None) -> tuple[float, float]:
    """The heading (deg, 0 north, clockwise) whose corridor out to 24 m is dry and falls most; `prefer` wins when
    its own corridor is dry. Returns (heading, 1.0 if dry else 0.0)."""
    if prefer is not None and ray_dry(water_s, grid, i0, j0, prefer) == 1.0:
        return float(prefer), 1.0
    best = (-1e9, 0.0, 0.0)
    g0 = float(ndi.map_coordinates(h, [[i0], [j0]], order=1)[0])
    for deg in range(0, 360, 15):
        dry = ray_dry(water_s, grid, i0, j0, deg)
        ii, jj = _ray(grid, i0, j0, deg, 3, 40)
        ok = (ii >= 0) & (jj >= 0) & (ii <= grid.rows - 1) & (jj <= grid.cols - 1)
        hv = ndi.map_coordinates(h, [ii[ok], jj[ok]], order=1) if ok.any() else np.array([g0])
        score = 100 * dry + np.clip((g0 - hv.mean()) / U, -5, 5)
        if score > best[0]:
            best = (score, float(deg), dry)
    return best[1], best[2]


def place_entrance(h, water_s, grid, i0, j0, prefer=None, search_m=40.0):
    """The entrance's spot and facing: the place's own point if a dry corridor leaves it, else the nearest land point
    within `search_m` that has one. Returns (i, j, facing, moved_m) or None."""
    if not water_s[int(round(i0)), int(round(j0))]:
        f, dry = choose_facing(h, water_s, grid, i0, j0, prefer)
        if dry:
            return i0, j0, f, 0.0
    r = int(search_m / grid.m)
    cands = []
    for di in range(-r, r + 1, 2):
        for dj in range(-r, r + 1, 2):
            dd = math.hypot(di, dj) * grid.m
            ii, jj = int(round(i0)) + di, int(round(j0)) + dj
            if dd <= search_m and 0 <= ii < grid.rows and 0 <= jj < grid.cols and not water_s[ii, jj]:
                cands.append((dd, ii, jj))
    for dd, ii, jj in sorted(cands):
        f, dry = choose_facing(h, water_s, grid, ii, jj, prefer)
        if dry:
            return float(ii), float(jj), f, dd
    return None


def entrance(h, water_s, grid, i0, j0, facing_deg, protect=None):
    """A bank behind the entrance (10 m, steep on its face) and a corridor in front eased to at most 1 in 3."""
    a = math.radians(facing_deg)
    fi, fj = -math.cos(a), math.sin(a)          # facing in (row, col)
    ground = float(ndi.map_coordinates(h, [[i0], [j0]], order=1)[0])
    ground = max(ground, FREEBOARD + 0.5 * U)
    # a knoll behind the entrance: its face (6 m deep) holds the opening, its back falls away over 45 m, its
    # sides over 28 m; added to the ground so the land's own undulation carries over it (no rim, no plateau)
    face_m, back_m, side_m, height_m = 6.0, 45.0, 28.0, 8.0
    ci, cj = i0 - fi * face_m / grid.m, j0 - fj * face_m / grid.m
    sl, di, dj = _disc(grid, ci, cj, (back_m + 2) / grid.m)
    along = (di * fi + dj * fj) * grid.m
    across = (di * fj - dj * fi) * grid.m
    rr = np.hypot(np.where(along > 0, along / face_m, along / back_m), across / side_m)
    x = np.clip(rr, 0, 1)
    bump = height_m * U * (1 - x * x * x * (x * (6 * x - 15) + 10))
    land = ~water_s[sl]
    if protect is not None:
        land = land & ~protect[sl]                    # a road's bed is never buried
    h[sl] = np.where(land, h[sl] + bump, h[sl])
    # the corridor: 2..30 m out, 5 m either side, eased to the entrance's ground at no more than 1 in 3
    sl, di, dj = _disc(grid, i0, j0, 32 / grid.m)
    along = (di * fi + dj * fj) * grid.m
    across = np.abs(di * fj - dj * fi) * grid.m
    end_i, end_j = i0 + fi * 30 / grid.m, j0 + fj * 30 / grid.m
    far = float(ndi.map_coordinates(h, [[np.clip(end_i, 0, grid.rows - 1)], [np.clip(end_j, 0, grid.cols - 1)]],
                                    order=1)[0])
    t = np.clip(along / 30.0, 0, 1)
    lim = np.maximum(along, 0) * U / 3.0
    prof = ground + np.clip((far - ground) * t, -lim, lim)
    w = (along > -1) & (along < 30) & (across < 5)
    wt = np.where(w, 1 - _ease((across - 3) / 2), 0) * (1 - _ease((along - 26) / 4))
    land = ~water_s[sl]
    if protect is not None:
        land = land & ~protect[sl]
    h[sl] = np.where(land, h[sl] * (1 - wt) + np.maximum(prof, FREEBOARD) * wt, h[sl])


def entrance_ok(h, water_s, cliff, grid, i0, j0, facing_deg) -> dict:
    ii, jj = _ray(grid, i0, j0, facing_deg, 2, 20)
    if cliff is None:                                  # judge on a local window
        a0, b0 = max(0, int(i0) - 16), max(0, int(j0) - 16)
        win = h[a0:int(i0) + 17, b0:int(j0) + 17]
        cl = ndi.map_coordinates((slope_deg(win) > 55).astype(np.float32), [ii - a0, jj - b0], order=0, mode="nearest")
    else:
        cl = ndi.map_coordinates(cliff.astype(np.float32), [ii, jj], order=0)
    hv = ndi.map_coordinates(h, [ii, jj], order=1)
    steep = np.degrees(np.arctan(np.abs(hv[2:] - hv[:-2]) / (2.0 * U)))   # over a 2 m stride
    return {"dry": ray_dry(water_s, grid, i0, j0, facing_deg, 20.0) == 1.0,
            "open": bool(cl.max() == 0 and steep.max() < 35), "max_slope_deg": round(float(steep.max()), 1)}


# ---- roads --------------------------------------------------------------------------------------------------

def densify(points_px: np.ndarray, step_px: float) -> np.ndarray:
    seg = np.hypot(*np.diff(points_px, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] == 0:
        return points_px[:1]
    t = np.arange(0, s[-1] + 1e-9, step_px)
    return np.stack([np.interp(t, s, points_px[:, 0]), np.interp(t, s, points_px[:, 1])], 1)


def grade_limit(z: np.ndarray, ds: float, g: float, floor: np.ndarray, passes: int = 60) -> np.ndarray:
    z = z.copy()
    for _ in range(passes):
        z0 = z.copy()
        for k in range(1, len(z)):
            z[k] = min(max(z[k], z[k - 1] - g * ds), z[k - 1] + g * ds)
        for k in range(len(z) - 2, -1, -1):
            z[k] = min(max(z[k], z[k + 1] - g * ds), z[k + 1] + g * ds)
        z = np.maximum(z, floor)
        if np.abs(z - z0).max() < 0.5:
            break
    return z


def plan_road(h, water_px, grid, points_px, grade_max, m_per_px=2.925714, water_s=None):
    """Centreline (px points every ~1 m, z units, wet flags) for one road edge, and its water crossings. Wet is read
    from the samples' water (`water_s`, the smooth coast) when given, else from the map's pixels."""
    pts = densify(np.asarray(points_px, float), 1.0 / m_per_px)
    ii, jj = grid.ij(pts[:, 0], pts[:, 1])
    if water_s is not None:
        wet = water_s[np.clip(np.round(ii).astype(int), 0, grid.rows - 1), np.clip(np.round(jj).astype(int), 0,
                                                                                    grid.cols - 1)]
    else:
        H, W = water_px.shape
        xi = np.clip(pts[:, 0].astype(int), 0, W - 1)
        yi = np.clip(pts[:, 1].astype(int), 0, H - 1)
        wet = water_px[yi, xi]
    ground = ndi.map_coordinates(h, [ii, jj], order=1)
    dry = ~wet
    smooth = ground.astype(np.float64)
    if dry.any():
        idx = np.arange(len(pts))
        smooth = np.interp(idx, idx[dry], ground[dry])
        smooth = ndi.gaussian_filter1d(smooth, 15, mode="nearest")
    floor = np.where(wet, -1e9, FREEBOARD + 0.1 * U)
    z = grade_limit(np.maximum(smooth, FREEBOARD + 0.1 * U), U * 1.0, grade_max * 0.9 * 1.0, floor)
    crossings = []
    lab, n = ndi.label(wet)
    for k in range(1, n + 1):
        w = np.flatnonzero(lab == k)
        length = len(w) * 1.0
        crossings.append({"kind": "ford" if length <= FORD_M else "bridge", "length_m": length,
                          "from_px": [round(float(pts[w[0], 0]), 1), round(float(pts[w[0], 1]), 1)],
                          "to_px": [round(float(pts[w[-1], 0]), 1), round(float(pts[w[-1], 1]), 1)]})
    cut = np.where(dry, (z - ground) / U, 0)
    return {"px": pts, "i": ii, "j": jj, "z": z, "wet": wet, "cut_m": cut, "crossings": crossings, "ground": ground}


def solve_network(edges: list, grade_of: dict, rounds: int = 8) -> dict:
    """Roads as one network. edges: [(plan, class, from_node, to_node)]. Each node takes the mean height of the ends
    that meet it, relaxed until every edge can join its two nodes within its grade; each edge is then re-graded with both ends pinned to its nodes (forward and backward passes at the
    class's grade less 15%), and the nodes re-read, until they settle. Returns the node heights."""
    for p, *_ in edges:
        p["z_free"] = p["z"].copy()
    node_z: dict = {}
    for _ in range(rounds):
        acc: dict = {}
        for p, c, a, b in edges:
            acc.setdefault(a, []).append(p["z"][0])
            acc.setdefault(b, []).append(p["z"][-1])
        new = {k: float(np.mean(v)) for k, v in acc.items()}
        for _relax in range(50):                       # nodes an edge can join within its grade
            worst = 0.0
            for p, c, a, b in edges:
                reach = grade_of[c] * 0.85 * U * (len(p["z"]) - 1)
                gap = new[b] - new[a]
                if abs(gap) > reach:
                    fix = (abs(gap) - reach) / 2 * np.sign(gap)
                    new[a] += fix
                    new[b] -= fix
                    worst = max(worst, abs(fix))
            if worst < 0.5:
                break
        moved = max((abs(new[k] - node_z.get(k, 1e9)) for k in new), default=0)
        node_z = new
        for p, c, a, b in edges:
            g = grade_of[c] * 0.85
            z = p["z_free"].copy()
            z[0], z[-1] = node_z[a], node_z[b]
            for _pass in range(40):
                z0 = z.copy()
                for k in range(1, len(z) - 1):
                    z[k] = min(max(z[k], z[k - 1] - g * U), z[k - 1] + g * U)
                for k in range(len(z) - 2, 0, -1):
                    z[k] = min(max(z[k], z[k + 1] - g * U), z[k + 1] + g * U)
                z[1:-1] = np.maximum(z[1:-1], np.where(p["wet"][1:-1], -1e9, FREEBOARD + 0.1 * U))
                if np.abs(z - z0).max() < 0.5:
                    break
            p["z"] = z
        if moved < 1.0:
            break
    for p, *_ in edges:
        p["cut_m"] = np.where(~p["wet"], (p["z"] - p["ground"]) / U, 0)
    return node_z


def stamp_roads(h, water_s, grid, plans: list):
    """Lay every planned road's trough into the land samples."""
    cz = np.full(h.shape, np.nan, np.float32)
    cls = np.zeros(h.shape, np.int8)
    for p, c in plans:
        keep = ~p["wet"]
        ii = np.clip(np.round(p["i"][keep]).astype(int), 0, grid.rows - 1)
        jj = np.clip(np.round(p["j"][keep]).astype(int), 0, grid.cols - 1)
        cz[ii, jj] = p["z"][keep]
        cls[ii, jj] = 1 if c == "major" else 2
    centre = ~np.isnan(cz)
    if not centre.any():
        return np.zeros(h.shape, bool)
    reach = int(FEATHER_M["major"] / grid.m) + 2
    near = ndi.binary_dilation(centre, iterations=reach)
    rows = np.flatnonzero(near.any(1))
    r0, r1 = rows.min(), rows.max() + 1
    sub = ~centre[r0:r1]
    d, (ii, jj) = ndi.distance_transform_edt(sub, return_indices=True)
    d = d * grid.m
    ii += r0
    zc = cz[ii, jj]
    kc = cls[ii, jj]
    feather = np.where(kc == 1, FEATHER_M["major"], FEATHER_M["minor"])
    scale = np.where(kc == 1, TROUGH_SCALE["major"], TROUGH_SCALE["minor"])
    fold = np.interp(d, TROUGH_D, TROUGH_M) * scale * U
    target = zc + fold
    # the bed (flat width and a little beyond) takes the road's height, cut or fill; past it the trough's walls only
    # ever cut ground that stands above them, so the road sits in the land and never on a raised strip
    w_bed = 1 - _ease((d - 2.0) / 3.0)
    w_cut = 1 - _ease((d - 4.0) / np.maximum(feather - 4.0, 1))
    hs = h[r0:r1]
    land = ~water_s[r0:r1] & near[r0:r1]
    new = hs + w_bed * (target - hs) + (1 - w_bed) * w_cut * np.minimum(target - hs, 0)
    hs[land] = np.maximum(new[land], FREEBOARD)
    corridor = np.zeros(h.shape, bool)
    corridor[r0:r1] = near[r0:r1] & (d <= 6.0)
    return corridor


def road_checks(h, grid, plans, grade_of: dict) -> dict:
    """Grade along (8 m baseline, dry stretches) and the trough at 4 m against the measured band."""
    grades, over, trough, where = [], 0, [], []
    for p, c in plans:
        hv = ndi.map_coordinates(h, [p["i"], p["j"]], order=1) / U
        dry = ~p["wet"]
        if len(hv) > 9:
            g = np.abs(hv[8:] - hv[:-8]) / 8.0
            ok = dry[8:] & dry[:-8]
            ok &= ndi.binary_erosion(dry, iterations=10)[8:]
            zp = p["z"] / U
            gp = np.abs(zp[8:] - zp[:-8]) / 8.0
            badk = np.flatnonzero(ok & (g > grade_of[c] + 0.03))
            for k in badk[::8][:3]:
                where.append({"px": [round(float(v), 1) for v in p["px"][k]], "class": c,
                              "grade": round(float(g[k]), 3), "planned_grade": round(float(gp[k]), 3),
                              "moved_after_m": round(float(np.abs(hv[k] - zp[k])), 2)})
            g = g[ok]
            grades.append(g)
            over += int((g > grade_of[c] + 0.03).sum())
        if len(hv) > 3:
            t = np.gradient(p["px"], axis=0)
            t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
            nrm = np.stack([-t[:, 1], t[:, 0]], 1) * (4.0 / 2.925714)
            sides = []
            for s in (1, -1):
                q = p["px"] + s * nrm
                si, sj = grid.ij(q[:, 0], q[:, 1])
                sides.append(ndi.map_coordinates(h, [si, sj], order=1) / U)
            dep = (sides[0] + sides[1]) / 2 - hv
            if c == "major":
                trough.append(dep[ndi.binary_erosion(dry, iterations=12)])
    g = np.concatenate(grades) if grades else np.zeros(1)
    t = np.concatenate(trough) if trough else np.zeros(1)
    return {"grade_p50": round(float(np.percentile(g, 50)), 3), "grade_p95": round(float(np.percentile(g, 95)), 3),
            "grade_max": round(float(g.max()), 3), "grade_over_limit_points": over, "grade_points": int(g.size), "grade_over_where": where[:60],
            "trough4m_p10": round(float(np.percentile(t, 10)), 2), "trough4m_p50": round(float(np.percentile(t, 50)), 2),
            "trough4m_p90": round(float(np.percentile(t, 90)), 2),
            "trough4m_in_band_share": round(float(((t >= 0.1) & (t <= 1.0)).mean()), 3)}
