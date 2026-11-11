"""Relief character: the landform that makes each region's ground its own (newworld/sources/region_relief.json).

The shared relief (terrain_relief) gives every region the same rolling shapes at its own heights, so regions of like
height read alike. Bethesda's neighbouring regions differ in landform type and scale, not only height (measured in
terrain_character: Hjaalmarch's marsh is pools and hummocks with 0.4 m of relief at 20 m, the Reach crags and gorges,
Whiterun open tundra). Here each land region gets the landform its research describes, on top of a share (`base`) of
the shared relief:

  root-hummocks   dense root hummocks 7 to 12 m across and up to a metre high, and a few broad dry rises
  strandlines     flat silt shores lined with low beach ridges parallel to the water, fading inland
  cuesta          north-facing scarps over long shelving south slopes (a tilted, stepped spine), rock tors
  ring-mounds     rings of firm ground 90 to 200 m across on flat swamp
  river-terraces  broad rounded rises between the rivers, and benches stepping up from the rivers' shores
  gorges          the mesa's rivers in steep-walled gorges (a short shore ramp)
  ravined-mounds  broad mounds on a plain cut by narrow winding ravines that start and end
  knob-and-kettle close knobs and kettle hollows, and a few larger ruin mounds
  inselbergs      steep isolated hills standing out of flat bog
  braided-ridges  thin ridges of firm ground midway between the channels, following them, as chains of rises
  sea-cut         a raised coastal bench with a short, cut shore, and a few low hills
  beach-ridges    sandy beach ridges parallel to the sea behind the shore
  mud-islands     dead-flat ground with small flat-topped mud islands
  tidal-flats     flat mud with raised banks along the channels
  levees          natural levees along the channels with backswamps behind them
  basin-islets    flat-topped islets on a flat basin floor
  clay-rises      broad low clay rises on a plain, rocky headlands at the sea
  clay-mounds     discrete rounded clay mounds standing on flat marsh, a raised coastal edge
  crag            a short, steep shore round the island's own rise
  spine           a ridge down the island's middle line (the ground climbs with the distance from the shore)

Every feature is placed on a lattice anchored to world position (a hash of the lattice cell), so the same ground comes
out whatever the scope. Large forms are laid before weathering (stage "before": drainage and rain then cut them like
any hill); fine forms after it (stage "after": the low-ground smoothing would erase them). Forms fade within 10 to 40 m
of a road. Each region's form is weighted by its share of the ground, blended over about 60 m at a border. Nothing
lowers the ground under 0.6 m above the water that stood over it.
"""
from __future__ import annotations

import json
import zlib
from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

from tools.newworld import frame as f

SPEC = f.ROOT / "sources" / "region_relief.json"
STEP = 128.0
U = 70.0
DRY_M = 0.6
PLACE_CLEAR_M = 60.0       # a place's footprint and this much round it stay clear of forms, as a road does
BLEND_SIGMA = 4            # coarse samples (1024 units): about 60 m of blend at a region border


def load() -> dict:
    return json.loads(SPEC.read_text())["regions"]


def overrides(spec: dict, rid: str, params: dict) -> dict:
    """The region's params with its character's base, ramp and form."""
    s = spec.get(rid) or {}
    p = dict(params)
    p.setdefault("base", 1.0)
    if "base" in s:
        p["base"] = float(s["base"])
    if "ramp_m" in s:
        p["ramp"] = float(s["ramp_m"])
    if "form" in s:
        p["form"] = s["form"]
    return p


def _hash(ix, iy, k, seed) -> np.ndarray:
    """Deterministic uniform [0, 1) per integer lattice cell (splitmix64 over the packed key)."""
    x = (np.asarray(ix, np.int64).astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)
         ^ np.asarray(iy, np.int64).astype(np.uint64) * np.uint64(0xC2B2AE3D27D4EB4F)
         ^ np.uint64((k * 0x165667B1 + seed * 0x27D4EB2F) & 0xFFFFFFFFFFFFFFFF))
    x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    x = x ^ (x >> np.uint64(31))
    return (x >> np.uint64(11)).astype(np.float64) / float(1 << 53)


@dataclass
class Crop:
    """A window of the grid: its sample offsets, world origin and the fields the forms read (metres)."""
    i0: int
    j0: int
    shape: tuple
    ox: float          # world x of the grid's sample (0, 0)
    oy: float
    m: float           # metres a sample
    rel: np.ndarray    # the ground so far (metres)
    dw: np.ndarray     # distance to any water (m, 0 in water)
    dsea: np.ndarray   # distance to the open sea (m)
    droad: np.ndarray  # distance to a road (m)
    span: np.ndarray   # the region's relief span (summit - floor, m)
    seed: int

    def world_m(self):
        """World position (metres) of every sample: x east, y north."""
        jj = (self.j0 + np.arange(self.shape[1])) * STEP + self.ox
        ii = self.oy - (self.i0 + np.arange(self.shape[0])) * STEP
        return jj[None, :] / U, ii[:, None] / U

    def points(self, spacing_m: float, keep: float, k: int, n_attr: int = 3):
        """Jittered lattice points anchored to the world: (rows, cols in the crop, attributes (n, n_attr) in [0,1))."""
        xm, ym = self.world_m()
        x0, x1 = xm.min() - spacing_m, xm.max() + spacing_m
        y0, y1 = ym.min() - spacing_m, ym.max() + spacing_m
        ix, iy = np.meshgrid(np.arange(np.floor(x0 / spacing_m), np.ceil(x1 / spacing_m)),
                             np.arange(np.floor(y0 / spacing_m), np.ceil(y1 / spacing_m)))
        ix, iy = ix.ravel().astype(np.int64), iy.ravel().astype(np.int64)
        sel = _hash(ix, iy, k, self.seed) < keep
        ix, iy = ix[sel], iy[sel]
        px = (ix + _hash(ix, iy, k + 1, self.seed)) * spacing_m       # anywhere in its cell: no rows, no columns
        py = (iy + _hash(ix, iy, k + 2, self.seed)) * spacing_m
        att = np.stack([_hash(ix, iy, k + 3 + a, self.seed) for a in range(n_attr)], 1)
        cols = (px * U - self.ox) / STEP - self.j0
        rows = (self.oy - py * U) / STEP - self.i0
        return rows, cols, att

    def nearest(self, rows, cols):
        """Distance (m) from every sample to the nearest point, and that point's index (-1 with no points)."""
        H, W = self.shape
        r, c = np.round(rows).astype(int), np.round(cols).astype(int)
        pad = int(max(H, W))
        inside = (r >= -pad) & (r < H + pad) & (c >= -pad) & (c < W + pad)
        idx = np.flatnonzero(inside)
        if not len(idx):
            return np.full(self.shape, 1e9, np.float32), np.full(self.shape, -1)
        # points just off the crop still shape it: a margin as wide as the farthest point kept
        mr = int(np.clip(-r[idx].min(), 0, pad)) + 1
        mc = int(np.clip(-c[idx].min(), 0, pad)) + 1
        big = np.full((H + mr + int(np.clip(r[idx].max() - H, 0, pad)) + 2,
                       W + mc + int(np.clip(c[idx].max() - W, 0, pad)) + 2), -1, np.int64)
        big[r[idx] + mr, c[idx] + mc] = idx
        d, (ri, ci) = ndi.distance_transform_edt(big < 0, return_indices=True)
        near = big[ri, ci][mr:mr + H, mc:mc + W]
        dist = d[mr:mr + H, mc:mc + W].astype(np.float32) * self.m
        # exact distance to the point itself, not its rounded sample
        rr, cc = np.mgrid[0:H, 0:W]
        dist = np.hypot(rr - rows[near], cc - cols[near]).astype(np.float32) * self.m
        return dist, near

    def noise(self, wl_m: float, k: int) -> np.ndarray:
        """Smooth value noise (about unit spread) anchored to the world, wavelength wl_m."""
        xm, ym = self.world_m()
        gx, gy = xm / wl_m, ym / wl_m
        # ten lattice cells of margin: the spline's edge effect dies out before the window, so two windows over
        # the same ground read the same noise
        ix0, iy0 = np.floor(gx.min()) - 10, np.floor(gy.min()) - 10
        nx, ny = int(np.ceil(gx.max()) - ix0) + 11, int(np.ceil(gy.max()) - iy0) + 11
        IX, IY = np.meshgrid(np.arange(nx) + ix0, np.arange(ny) + iy0)
        lat = _hash(IX.astype(np.int64), IY.astype(np.int64), k, self.seed) * 2 - 1
        cy, cx = np.broadcast_arrays(gy - iy0, gx - ix0)
        return 1.7 * ndi.map_coordinates(lat, [cy, cx], order=3, mode="nearest").astype(np.float32)


def _dome(d, r):
    t = np.clip(1 - d / r, 0, 1)
    return t * t * (3 - 2 * t)


def _steep(d, r, p=0.6):
    return np.clip(1 - (d / r) ** 2, 0, 1) ** p


def _flat_top(d, r, edge=0.3):
    return np.clip((1 - d / r) / edge, 0, 1) ** 1.5


def _blobs(c: Crop, spacing, keep, k, r_lo, r_hi, h_lo, h_hi, prof=_dome, rough=0.25):
    """Scattered shapes of profile `prof`, each with its own radius and height; `rough` wanders every outline (no
    shape is a circle)."""
    rows, cols, a = c.points(spacing, keep, k)
    if not len(rows):
        return np.zeros(c.shape, np.float32)
    d, near = c.nearest(rows, cols)
    if rough:
        d = d * np.clip(1 + rough * c.noise(0.75 * (r_lo + r_hi), k + 7), 0.45, 1.8)
    r = r_lo + (r_hi - r_lo) * a[near, 0]
    h = h_lo + (h_hi - h_lo) * a[near, 1]
    return (h * prof(d, r)).astype(np.float32)


def _smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _road_fade(c: Crop, near=10.0, far=40.0):
    return _smoothstep(near, far, c.droad)


# each character: stage -> fn(crop) -> metres to add (before weighting by the region's share)
def root_hummocks(c, stage):
    if stage == "before":
        return _blobs(c, 320, 0.7, 10, 60, 120, 1.5, 3.5) * _road_fade(c)
    hum = _blobs(c, 13, 0.85, 20, 4.0, 7.0, 0.7, 1.8)       # Hjaalmarch's marsh: 0.4 m of relief at 20 m
    return hum * _smoothstep(2, 10, c.dw) * _road_fade(c, 4, 12)


def strandlines(c, stage):
    if stage == "before":
        return None
    ph = 2 * np.pi * c.dw / 40.0 + 0.9 * c.noise(180, 30)
    return 1.2 * np.maximum(np.cos(ph), 0) ** 3 * np.exp(-c.dw / 500.0) * _smoothstep(3, 10, c.dw) \
        * _road_fade(c, 4, 12)


def cuesta(c, stage):
    xm, ym = c.world_m()
    if stage == "before":
        s = ym / 260.0 + 0.9 * c.noise(700, 40) + 0.25 * c.noise(180, 41) + 0.0 * xm     # scarps wander and fork
        t = s - np.floor(s)
        prof = np.where(t < 0.9, t / 0.9, 1 - _smoothstep(0.9, 0.97, t))
        run = 0.5 + 0.5 * _smoothstep(-0.6, 0.4, c.noise(900, 42))                        # and die out along their run
        return (0.2 * c.span * prof * run).astype(np.float32) * _road_fade(c)
    return _blobs(c, 140, 0.5, 45, 5, 10, 2.0, 4.0, lambda d, r: _steep(d, r, 0.5)) * _road_fade(c, 8, 20)


def ring_mounds(c, stage):
    if stage == "before":
        return None
    rows, cols, a = c.points(280, 0.7, 50)
    if not len(rows):
        return np.zeros(c.shape, np.float32)
    d, near = c.nearest(rows, cols)
    d = d * np.clip(1 + 0.22 * c.noise(110, 51), 0.5, 1.6)        # no ring is a circle
    R = 45 + 55 * a[near, 0]
    w = 10 + 8 * a[near, 1]
    h = (2.0 + 1.5 * a[near, 2]) * (0.35 + 0.65 * _smoothstep(-0.7, 0.1, c.noise(90, 52)))   # and each has its gaps
    return (h * np.exp(-((d - R) / w) ** 2)).astype(np.float32) * _smoothstep(3, 10, c.dw) * _road_fade(c, 4, 15)


def river_terraces(c, stage):
    if stage == "before":
        return _blobs(c, 420, 0.7, 56, 120, 220, 6.0, 14.0) * _smoothstep(40, 160, c.dw) * _road_fade(c)
    step = 5.0
    wander = 1.0 * c.noise(160, 55)                       # a bench's edge wanders off the contour and breaks
    q = (c.rel + wander) / step
    fr = q - np.floor(q)
    tq = step * (np.floor(q) + _smoothstep(0.78, 1.0, fr)) - wander
    return ((tq - c.rel) * 0.85 * np.exp(-c.dw / 90.0)).astype(np.float32) * _road_fade(c)


def gorges(c, stage):
    return None          # the short shore ramp (ramp_m) is the gorge wall


def ravined_mounds(c, stage):
    if stage == "before":
        return None
    mounds = _blobs(c, 200, 0.6, 60, 40, 75, 4.0, 9.0) * _smoothstep(10, 30, c.dw)
    n = c.noise(220, 61) + 0.35 * c.noise(70, 62)
    v = np.clip(1 - np.abs(n) / 0.2, 0, 1) ** 1.2
    reach = _smoothstep(-0.4, 0.3, c.noise(450, 63))          # a ravine starts and ends: none closes on itself
    cut = -7.0 * v * reach * _smoothstep(1.5, 5.0, c.rel + mounds) * _smoothstep(8, 30, c.dw)
    return (mounds + cut).astype(np.float32) * _road_fade(c, 6, 20)


def knob_and_kettle(c, stage):
    if stage == "before":
        return _blobs(c, 420, 0.6, 70, 45, 80, 3.0, 6.0) * _road_fade(c)
    rows, cols, a = c.points(55, 0.9, 75)
    if not len(rows):
        return np.zeros(c.shape, np.float32)
    d, near = c.nearest(rows, cols)
    r = 14 + 12 * a[near, 0]
    kettle = a[near, 2] < 0.5
    h = np.where(kettle, -(1.0 + 1.2 * a[near, 1]), 2.0 + 2.0 * a[near, 1])
    return (h * _dome(d, r)).astype(np.float32) * _smoothstep(4, 15, c.dw) * _road_fade(c, 6, 20)


def inselbergs(c, stage):
    if stage == "before":
        rows, cols, a = c.points(220, 0.85, 80)
        if not len(rows):
            return np.zeros(c.shape, np.float32)
        d, near = c.nearest(rows, cols)
        r = (50 + 60 * a[near, 0]) * (1 + 0.18 * c.noise(120, 81))
        h = (0.45 + 0.45 * a[near, 1]) * c.span
        return (h * _steep(d, r, 0.8)).astype(np.float32) * _smoothstep(5, 20, c.dw) * _road_fade(c, 15, 50)
    return None


def braided_ridges(c, stage):
    if stage == "before":
        return None
    # the crest of the ground between two channels: where the distance to the water stops rising
    gy, gx = np.gradient(ndi.gaussian_filter(c.dw, 2.0), c.m)
    crest = _smoothstep(0.15, 0.6, 1 - np.clip(np.hypot(gx, gy), 0, 1)) * _smoothstep(5, 12, c.dw)
    ridge = np.clip(ndi.gaussian_filter(crest.astype(np.float32), 3.0) * 1.6, 0, 1)
    ridge = ridge * (0.55 + 0.45 * _smoothstep(-0.8, 0.3, c.noise(140, 91)))      # a chain of rises, not a wall
    hum = _blobs(c, 30, 0.6, 95, 5, 9, 0.2, 0.5)
    return ((2.2 * ridge + hum * ridge) * _smoothstep(2, 8, c.dw)).astype(np.float32) * _road_fade(c, 4, 12)


def sea_cut(c, stage):
    if stage == "before":
        return _blobs(c, 520, 0.6, 100, 90, 160, 3.0, 6.0) * _road_fade(c)
    return (2.2 * np.exp(-c.dsea / 120.0) * (c.dsea < 600)).astype(np.float32) * _road_fade(c)


def beach_ridges(c, stage):
    if stage == "before":
        return None
    ph = 2 * np.pi * c.dsea / 44.0 + 0.9 * c.noise(200, 110)
    return (1.0 * np.maximum(np.cos(ph), 0) ** 2 * _smoothstep(420, 150, c.dsea)
            * _smoothstep(3, 12, c.dw)).astype(np.float32) * _road_fade(c, 4, 12)


def mud_islands(c, stage):
    if stage == "before":
        return None
    return _blobs(c, 70, 0.45, 120, 10, 24, 0.6, 1.2, _flat_top) * _smoothstep(2, 8, c.dw) * _road_fade(c, 4, 12)


def tidal_flats(c, stage):
    if stage == "before":
        return None
    return (0.9 * np.exp(-((c.dw - 14.0) / 8.0) ** 2)).astype(np.float32) * _road_fade(c, 4, 12)


def levees(c, stage):
    if stage == "before":
        return None
    crest = 1.8 * np.exp(-((c.dw - 12.0) / 7.0) ** 2)
    swamp = 0.5 * _smoothstep(30, 80, c.dw) * _smoothstep(260, 140, c.dw)
    return (crest - swamp).astype(np.float32) * _road_fade(c, 4, 12)


def basin_islets(c, stage):
    if stage == "before":
        return None
    return _blobs(c, 110, 0.45, 140, 18, 34, 1.0, 1.8, lambda d, r: _flat_top(d, r, 0.25)) \
        * _smoothstep(3, 10, c.dw) * _road_fade(c, 4, 15)


def _ridged(c, wl, k):
    return 1 - np.abs(c.noise(wl, k))


def clay_rises(c, stage):
    if stage == "before":
        return _blobs(c, 650, 0.8, 150, 150, 260, 4.0, 8.0) * _road_fade(c)
    return (3.5 * np.clip(_ridged(c, 60, 151) - 0.3, 0, 1) * np.exp(-c.dsea / 90.0)
            * _smoothstep(3, 12, c.dw)).astype(np.float32) * _road_fade(c, 6, 20)


def clay_mounds(c, stage):
    if stage == "before":
        return None
    mounds = _blobs(c, 190, 0.7, 160, 35, 70, 3.5, 8.0) * _smoothstep(8, 25, c.dw) * _road_fade(c, 15, 50)
    return mounds + (3.5 * np.exp(-c.dsea / 100.0) * (c.dsea < 500)).astype(np.float32) * _road_fade(c)


def crag(c, stage):
    return None          # the short shore ramp (ramp_m) is the cliff; the island's own rise is the crag


def spine(c, stage):
    if stage == "after":
        return None
    # the island's middle line stands highest: the ground climbs with the distance from the shore
    return np.clip(0.09 * c.dw, 0, 16.0).astype(np.float32) * _road_fade(c)


CHARACTERS = {"root-hummocks": root_hummocks, "strandlines": strandlines, "cuesta": cuesta,
              "ring-mounds": ring_mounds, "river-terraces": river_terraces, "gorges": gorges,
              "ravined-mounds": ravined_mounds, "knob-and-kettle": knob_and_kettle, "inselbergs": inselbergs,
              "braided-ridges": braided_ridges, "sea-cut": sea_cut, "beach-ridges": beach_ridges,
              "mud-islands": mud_islands, "tidal-flats": tidal_flats, "levees": levees,
              "basin-islets": basin_islets, "clay-rises": clay_rises, "clay-mounds": clay_mounds,
              "crag": crag, "spine": spine}


def region_weights(code: np.ndarray, lut: dict, rids) -> dict:
    """Coarse share (0..1) of each region's ground, blended over BLEND_SIGMA. `code`: region index per coarse
    point (foreign land and sea regions already coded apart)."""
    return {r: ndi.gaussian_filter((code == lut[r]).astype(np.float32), BLEND_SIGMA, mode="nearest") for r in rids}


def apply(relief_m: np.ndarray, stage: str, spec: dict, weights: dict, coarse: int, *, ox: float, oy: float,
          m: float, dw: np.ndarray, coast_t: np.ndarray, road_ij: np.ndarray, span: np.ndarray,
          places=None, seed: int = 1952) -> dict:
    """Add each region's character for `stage` to relief_m (mutated). `weights`: region -> coarse share; dw: full
    distance to water (m); coast_t: full 1 - exp(-d_sea / 5 km); road_ij: (n, 2) road sample positions; places:
    (n, 3) sample i, j and footprint radius (m), kept clear like a road out to PLACE_CLEAR_M past the radius. Returns,
    per region, the samples touched and the RMS added (metres)."""
    from tools.newworld.terrain_relief import upsample
    done = {}
    H, W = relief_m.shape
    for rid, wc in sorted(weights.items()):
        ch = (spec.get(rid) or {}).get("character")
        fn = CHARACTERS.get(ch)
        if fn is None:
            continue
        on = np.argwhere(wc > 0.01)
        if not len(on):
            continue
        ci0, cj0 = on.min(0)
        ci1, cj1 = on.max(0) + 1
        i0, j0 = int(ci0) * coarse, int(cj0) * coarse
        i1, j1 = min(H, int(ci1) * coarse + 1), min(W, int(cj1) * coarse + 1)
        if i1 <= i0 or j1 <= j0:
            continue
        sl = (slice(i0, i1), slice(j0, j1))
        shape = (i1 - i0, j1 - j0)
        w = upsample(wc[ci0:ci1 + 2, cj0:cj1 + 2], shape, coarse, order=1)
        w = np.clip(w, 0, 1)
        sel = (road_ij[:, 0] >= i0 - 60) & (road_ij[:, 0] < i1 + 60) & (road_ij[:, 1] >= j0 - 60) & (road_ij[:, 1] < j1 + 60)
        if sel.any():
            rm = np.ones((shape[0] + 120, shape[1] + 120), bool)
            rr = np.round(road_ij[sel] - [i0 - 60, j0 - 60]).astype(int)
            rr = rr[(rr[:, 0] >= 0) & (rr[:, 0] < rm.shape[0]) & (rr[:, 1] >= 0) & (rr[:, 1] < rm.shape[1])]
            rm[rr[:, 0], rr[:, 1]] = False
            droad = (ndi.distance_transform_edt(rm) * m)[60:-60, 60:-60].astype(np.float32)
        else:
            droad = np.full(shape, 1e6, np.float32)
        for pi, pj, pr in (places if places is not None else ()):
            reach = (pr + PLACE_CLEAR_M + 60) / m
            if not (i0 - reach <= pi < i1 + reach and j0 - reach <= pj < j1 + reach):
                continue
            a, b = int(max(i0, pi - reach)), int(min(i1, pi + reach + 1))
            e, g = int(max(j0, pj - reach)), int(min(j1, pj + reach + 1))
            if b <= a or g <= e:
                continue
            ii, jj = np.ogrid[a:b, e:g]
            dp = (np.hypot(ii - pi, jj - pj) * m - pr - PLACE_CLEAR_M).astype(np.float32)
            win = droad[a - i0:b - i0, e - j0:g - j0]
            np.minimum(win, np.maximum(dp, 0), out=win)
        dsea = (-5000.0 * np.log(np.clip(1 - coast_t[sl], 1e-6, 1))).astype(np.float32)
        crop = Crop(i0=i0, j0=j0, shape=shape, ox=ox, oy=oy, m=m, rel=relief_m[sl].copy(), dw=dw[sl],
                    dsea=dsea, droad=droad, span=span[sl],
                    seed=seed + zlib.crc32(rid.encode()) % 1_000_003)      # by the region's id: one region's
        # forms never move because another region joined or left the table
        add = fn(crop, stage)
        if add is None:
            continue
        before = relief_m[sl]
        new = before + w * add
        relief_m[sl] = np.maximum(new, np.minimum(before, DRY_M)).astype(np.float32)
        touched = w > 0.5
        done[rid] = {"character": ch, "samples": int(touched.sum()),
                     "rms_added_m": round(float(np.sqrt(np.mean((w * add)[touched] ** 2))) if touched.any() else 0, 3)}
    return done
