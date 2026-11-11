"""Landcover (nw-02 step 7): one habitat per heightmap sample, the ground and planting steps' shared source.

    python3 -m tools.newworld.landcover            # build (skips when the key matches); prints the share table
    python3 -m tools.newworld.landcover --force    # rebuild

Reads the current terrain build (out/newworld/terrain/build.json + heightmap.npy: one sample per LAND vertex,
128 units), the water classification (out/newworld/water_classified.png/.json, map px), the regions
(out/newworld/cell_region.json, margin_cells.json), the db (habitat, region_habitat, road, road_vertex) and
the place pads (out/newworld/terrain/places_terrain.json). Writes out/newworld/landcover/ (never git):

    habitat.npy  uint8   habitat index (legend.json "habitats", 1-based; 0 none)
    region.npy   uint8   region index after the domain warp (legend "regions")
    kind.npy     uint8   water kind of the sample (water) or of the nearest water (land); 255 none
    shore.npy    int16   signed distance to the water line, decimetres (+ land, - water), clipped +-3000 m
    sea.npy      int16   land: distance to sea water (ocean, shallow coast, bay, estuary), dm, clipped 3000 m
    run.npy      int16   land: distance to running water (river, stream), dm, clipped 3000 m
    road.npy     uint16  distance to the nearest road spine (to its line, within 73 m), dm, clipped 6000 dm
    roadcls.npy  uint8   the nearest road's class (1 major, 2 minor; 0 none within 100 m)
    canopy.npy   uint8   tree-cover multiplier 0..255 for the planting step (glades, stands, clearings, banks)
    slope.npy    uint8   degrees (from the heightmap smoothed over ~2 samples)
    relief.npy   int8    micro-relief: height over the ground within ~11 m, dm (+ hump, - hollow)
    flags.npy    uint8   1 water, 2 place pad, 4 margin cell, 8 road surface (< 3.5 m major / 2 m minor)
    legend.json, stats.json, preview.png (habitat colours, 1 px = 4 samples)

The recipe (each rule's numbers are the studies'):
1. Context per sample: water = height < 0; depth; slope; the signed shore distance (EDT); the kind of the sample's
   own or nearest water; distances to sea and to running water; road spines (db road_vertex, bridges skipped) and
   their distance; place pads (radius from places_terrain.json); margin cells.
2. Regions are cell rectangles on the map: the region lookup is domain-warped (std 40 samples, ~73 m, over
   ~70, 290 and 880 m) so borders wander, and each region's habitat mix is drawn from its region_habitat shares.
3. Habitat per sample by priority: water (sea kinds -> mangrove fringe in the shallow coast band if the region
   has it, else seabed by depth 5/20 m; running -> lake bed; still inland -> the region's standing habitats within
   their depth caps, biased by kind: black swamp to cypress and drowned forest, green marsh to reeds, pond and
   lake to open water and lake bed); cliff face on slopes over a noisy 26-32 deg; the coast band (land within a
   noisy 15-40 m of sea water and under 3 m) to beach or mangrove when the region has them; the river band (a noisy
   20-50 m of running water) to riverine forest; the rest from the region's dry habitats by multi-scale,
   domain-warped noise scores plus context (rock on slopes and heights, hummock near water, grassland near the
   sea, upland at height), the per-region biases solved so each region's free land matches its shares.
4. Canopy (the forest/open field the salvage study found missing): stand density varying at ~190 m (CV ~0.4),
   glades ~90 m across (top ~12% of a glade field), clearings round place pads (pad + 30 m ramp), road verges
   (nothing on the 8 m skirt, ramp to 12 m), river banks opened to half within 12 m, nothing in running water,
   standing-water habitats only where trees stand in water (cypress, drowned forest, mangrove).
Interrupt-proof: one atomic write per array; the key (terrain build, inputs, this code) skips a matching rebuild.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from tools.newworld import frame as f

REPO = f.REPO
DB = REPO / "newworld/story/data/db"
OUT = f.OUT / "landcover"
TERRAIN = f.OUT / "terrain"
UPM = 70.0
SAMPLE = 128.0
M_PER_S = SAMPLE / UPM  # 1.83 m
STEP = 8  # coarse noise lattice, samples
TILE = 384  # rows per tile
SEA_KINDS = ("ocean", "shallow-coast", "bay", "estuary")
RUN_KINDS = ("river", "stream")
FREE_DRY = ("coastal_grassland", "dry_hammock", "hist_grove", "rainforest_floor", "rocky_outcrop", "swamp_hummock",
            "upland_scrub")
WET_LAND = ("reed_marsh", "cypress_swamp", "drowned_forest", "mangrove_fringe")  # also wet mud and flooded ground
STANDING = ("cypress_swamp", "drowned_forest", "reed_marsh", "open_still_water", "mangrove_fringe", "lake_bed")
TREE_IN_WATER = ("cypress_swamp", "drowned_forest", "mangrove_fringe")
FALLBACK_DRY = {"swamp_hummock": 0.4, "dry_hammock": 0.3, "coastal_grassland": 0.3}
COLOURS = {"beach_shore": (222, 205, 150), "cliff_face": (120, 110, 100), "coastal_grassland": (170, 200, 110),
           "cypress_swamp": (60, 75, 40), "drowned_forest": (55, 95, 70), "dry_hammock": (150, 160, 80),
           "hist_grove": (110, 60, 120), "lake_bed": (60, 110, 140), "mangrove_fringe": (40, 120, 90),
           "open_still_water": (90, 150, 160), "rainforest_floor": (30, 110, 40), "reed_marsh": (140, 170, 70),
           "riverine_forest": (60, 140, 60), "rocky_outcrop": (150, 140, 130), "seabed_deep": (20, 40, 90),
           "seabed_mid": (35, 70, 130), "seabed_shallow": (60, 120, 170), "swamp_hummock": (90, 120, 50),
           "upland_scrub": (180, 170, 100)}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def jsonl(name: str) -> list:
    return [json.loads(x) for x in (DB / f"{name}.jsonl").read_text().splitlines() if x.strip()]


def _save(name: str, a: np.ndarray) -> None:
    tmp = OUT / f"{name}.tmp.npy"
    np.save(tmp, a)
    os.replace(tmp, OUT / f"{name}.npy")


def _hash(paths) -> str:
    h = hashlib.sha256()
    for p in paths:
        h.update(Path(p).read_bytes() if Path(p).stat().st_size < 50_000_000 else str(Path(p).stat().st_mtime_ns).encode())
    return h.hexdigest()[:16]


# --- noise -------------------------------------------------------------------------------------------------------

def lattice(rng, shape, spacing: int) -> np.ndarray:
    g = rng.standard_normal((shape[0] // spacing + 4, shape[1] // spacing + 4)).astype(np.float32)
    z = ndi.zoom(g, spacing, order=3, prefilter=False)
    return z[:shape[0], :shape[1]]


def fbm(seed: int, shape, spacings=(4, 12, 40), weights=(0.3, 0.6, 1.0)) -> np.ndarray:
    """Multi-scale noise on the coarse lattice (1 px = STEP samples), unit std."""
    rng = np.random.default_rng(seed)
    out = sum(w * lattice(rng, shape, s) for s, w in zip(spacings, weights))
    out -= out.mean()
    return (out / (out.std() + 1e-9)).astype(np.float32)


class Fields:
    """Coarse noise fields, sampled at any sample positions through one shared domain warp."""

    def __init__(self, shape_s, names: list, seed: int = 7021):
        self.cs = (shape_s[0] // STEP + 2, shape_s[1] // STEP + 2)
        self.warp = [fbm(seed + 1, self.cs, (5, 20, 60), (0.3, 0.7, 1.0)), fbm(seed + 2, self.cs, (5, 20, 60), (0.3, 0.7, 1.0))]
        self.f = {n: fbm(seed + 10 + k, self.cs) for k, n in enumerate(names)}

    def coords(self, rr, cc):
        r, c = rr / STEP, cc / STEP
        wr = ndi.map_coordinates(self.warp[0], [r, c], order=1, mode="nearest")
        wc = ndi.map_coordinates(self.warp[1], [r, c], order=1, mode="nearest")
        return rr + 40 * wr, cc + 40 * wc  # 40 samples std (~73 m), three scales

    def at(self, name, wr, wc):
        return ndi.map_coordinates(self.f[name], [wr / STEP, wc / STEP], order=1, mode="nearest")


# --- inputs ------------------------------------------------------------------------------------------------------

def grid():
    b = json.loads((TERRAIN / "build.json").read_text())
    return b, float(b["origin_world_x"]), float(b["origin_world_y"])


def sample_to_px(rr, cc, ox, oy):
    x = ox + cc * SAMPLE
    y = oy - rr * SAMPLE
    return y / -f.UNITS_PER_PX + f.Y0_PX, x / f.UNITS_PER_PX + f.X0_PX  # (py, px)


def region_map():
    from tools.newworld.terrain import region_px  # the terrain build's own cell -> pixel reading
    cell_region = json.loads((f.OUT / "cell_region.json").read_text())
    names = sorted(set(cell_region.values()))
    code = region_px(cell_region, names, (f.HEIGHT_PX, f.WIDTH_PX))
    _, (ir, ic) = ndi.distance_transform_edt(code < 0, return_indices=True)  # off-scope px: the nearest region
    return code[ir, ic].astype(np.int16), names


def road_segments(ox, oy) -> list[tuple[float, float, float, float, int]]:
    """Road spines as segments on the sample grid: (row a, col a, row b, col b, class 1 major / 2 minor), bridges
    (both ends on water) left out."""
    cls = {r["id"]: (1 if r["road_class_id"] == "major" else 2) for r in jsonl("road")}
    verts: dict = {}
    for v in jsonl("road_vertex"):
        verts.setdefault(v["road_id"], []).append(v)
    segs = []
    for rid, vs in verts.items():
        vs.sort(key=lambda v: v["seq"])
        for a, b in zip(vs, vs[1:]):
            if a["on_water"] and b["on_water"]:
                continue
            segs.append(((oy - a["world_y"]) / SAMPLE, (a["world_x"] - ox) / SAMPLE,
                         (oy - b["world_y"]) / SAMPLE, (b["world_x"] - ox) / SAMPLE, cls.get(rid, 2)))
    return segs


ROAD_EXACT = 40  # samples (73 m): within this of a spine the distance is measured to the line itself


def road_field(shape, segs) -> tuple[np.ndarray, np.ndarray]:
    """-> (distance to the nearest road spine in samples, float32; that road's class, 0 where there is none). Within
    ROAD_EXACT samples the distance is to the spine's line itself, not to the samples it crosses, so a road's ramp
    runs straight at any heading (a rasterised spine steps by a whole sample); a major road wins a tie. Beyond it, the
    distance to the nearest sample a spine crosses."""
    H, W = shape
    ras = np.zeros(shape, np.uint8)
    exact = np.full(shape, np.inf, np.float32)
    cls = np.zeros(shape, np.uint8)
    P = ROAD_EXACT
    for ra, ca, rb, cb, k in segs:
        n = int(max(abs(cb - ca), abs(rb - ra)) * 2) + 2
        t = np.linspace(0, 1, n)
        r = np.rint(ra + (rb - ra) * t).astype(int)
        c = np.rint(ca + (cb - ca) * t).astype(int)
        ok = (r >= 0) & (r < H) & (c >= 0) & (c < W)
        cur = ras[r[ok], c[ok]]
        ras[r[ok], c[ok]] = np.where((cur == 0) | (cur > k), k, cur)
        r0, r1 = max(int(min(ra, rb)) - P, 0), min(int(max(ra, rb)) + P + 2, H)
        c0, c1 = max(int(min(ca, cb)) - P, 0), min(int(max(ca, cb)) + P + 2, W)
        if r0 >= r1 or c0 >= c1:
            continue
        rr, cc = np.mgrid[r0:r1, c0:c1].astype(np.float32)
        dr, dc = rb - ra, cb - ca
        ll = dr * dr + dc * dc
        u = np.clip(((rr - ra) * dr + (cc - ca) * dc) / ll, 0, 1) if ll > 0 else 0.0
        d = np.hypot(rr - (ra + u * dr), cc - (ca + u * dc)).astype(np.float32)
        e, kc = exact[r0:r1, c0:c1], cls[r0:r1, c0:c1]
        take = (d < e - 1e-4) | ((np.abs(d - e) <= 1e-4) & (k < kc))
        e[take] = d[take]
        kc[take] = k
    rd, (ir, ic) = ndi.distance_transform_edt(ras == 0, return_indices=True)
    near = exact <= P
    dist = np.where(near, exact, np.maximum(rd, P)).astype(np.float32)
    return dist, np.where(near, cls, ras[ir, ic]).astype(np.uint8)


def place_mask(shape, ox, oy):
    """Pad mask and the distance (m) beyond the nearest pad's rim, as float32 (0 inside)."""
    pads = json.loads((TERRAIN / "places_terrain.json").read_text())
    beyond = np.full(shape, 1e4, np.float32)
    for p in pads:
        x, y = f.px_to_world(p["px"], p["py"])
        c0, r0 = (x - ox) / SAMPLE, (oy - y) / SAMPLE
        rad = float(p.get("radius_m") or 60.0) / M_PER_S
        R = int(rad + 40 / M_PER_S) + 2
        a0, a1 = max(int(r0) - R, 0), min(int(r0) + R, shape[0])
        b0, b1 = max(int(c0) - R, 0), min(int(c0) + R, shape[1])
        if a0 >= a1 or b0 >= b1:
            continue
        rr, cc = np.mgrid[a0:a1, b0:b1]
        d = (np.hypot(rr - r0, cc - c0) - rad) * M_PER_S
        beyond[a0:a1, b0:b1] = np.minimum(beyond[a0:a1, b0:b1], np.maximum(d, 0))
    return beyond


def margin_mask(shape, ox, oy):
    cells = {tuple(c) for c in json.loads((f.OUT / "margin_cells.json").read_text())}
    ys = np.arange(shape[0]); xs = np.arange(shape[1])
    cy = np.floor((oy - ys * SAMPLE) / f.CELL_UNITS - 1e-9).astype(int)
    cx = np.floor((ox + xs * SAMPLE) / f.CELL_UNITS).astype(int)
    m = np.zeros(shape, bool)
    for (x, y) in cells:
        ri = np.nonzero(cy == y)[0]; ci = np.nonzero(cx == x)[0]
        if len(ri) and len(ci):
            m[ri[0]:ri[-1] + 1, ci[0]:ci[-1] + 1] = True
    return m


def dm(a, lo=-30000, hi=30000) -> np.ndarray:
    return np.clip(np.rint(a * 10), lo, hi).astype(np.int16)


# --- the habitat choice ------------------------------------------------------------------------------------------

class Chooser:
    def __init__(self, hab_names, regions, shares, fields, kidx):
        self.K = lambda names: [kidx[n] for n in names]
        self.H = {n: i + 1 for i, n in enumerate(hab_names)}
        self.regions = regions
        self.shares = shares  # region index -> {habitat: share}
        self.fields = fields
        self.bias = {ri: {h: 0.0 for h in self.free(ri)} for ri in range(len(regions))}
        self.depth_max = {h["id"]: h.get("depth_max_m") for h in jsonl("habitat")}

    def free(self, ri):
        s = {h: v for h, v in self.shares.get(ri, {}).items() if h in FREE_DRY + WET_LAND}
        return s if s else dict(FALLBACK_DRY)

    def choose(self, c: dict) -> np.ndarray:
        """c: arrays of one shape: wr, wc (warped coords), reg, water, depth, slope, shore (m), kind (index),
        sea (m), run (m), h (m). Returns habitat indices (uint8)."""
        F = self.fields
        n = c["reg"].shape
        out = np.zeros(n, np.uint8)
        nb = F.at("_band", c["wr"], c["wc"])
        reg = c["reg"]
        kinds = c["kind"]; K = self.K
        # water
        w = c["water"]
        is_sea = np.isin(kinds, K(SEA_KINDS[:3])) & w
        is_est = (kinds == K(["estuary"])[0]) & w
        is_run = np.isin(kinds, K(RUN_KINDS)) & w
        still = w & ~is_sea & ~is_est & ~is_run
        d = c["depth"]
        seabed = np.where(d < 5, self.H["seabed_shallow"], np.where(d < 20, self.H["seabed_mid"], self.H["seabed_deep"]))
        out[is_sea] = seabed[is_sea]
        out[is_run | is_est] = self.H["lake_bed"]
        has_mang = np.zeros(n, bool)
        for ri in np.unique(reg):
            if "mangrove_fringe" in self.shares.get(int(ri), {}):
                has_mang |= reg == ri
        mang_w = (is_sea | is_est) & has_mang & (d < 2.5) & (-c["shore"] < 40 * (1 + 0.35 * nb)) & (F.at("mangrove_fringe", c["wr"], c["wc"]) > -0.3)
        out[mang_w] = self.H["mangrove_fringe"]
        if still.any():
            idx = np.nonzero(still)
            out[idx] = self._standing(c, idx)
        # land
        land = ~w
        th = 29 + 3 * nb
        cliff = land & (c["slope"] >= th)
        out[cliff] = self.H["cliff_face"]
        rest = land & ~cliff
        coast = rest & (c["sea"] < 27 * (1 + 0.45 * nb)) & (c["h"] < 3.0)
        for ri in np.unique(reg[rest]):
            ri = int(ri)
            sh = self.shares.get(ri, {})
            m = rest & (reg == ri)
            cm = m & coast
            if cm.any() and ("beach_shore" in sh or "mangrove_fringe" in sh):
                a = F.at("beach_shore", c["wr"][cm], c["wc"][cm]) + math.log(sh.get("beach_shore", 1e-6))
                b = F.at("mangrove_fringe", c["wr"][cm], c["wc"][cm]) + math.log(sh.get("mangrove_fringe", 1e-6)) + (c["h"][cm] < 1.0) * 0.8
                out[cm] = np.where(a >= b, self.H["beach_shore"], self.H["mangrove_fringe"])
                m &= ~cm
            if "riverine_forest" in sh:
                rv = m & (c["run"] < 35 * (1 + 0.4 * nb))
                if rv.any():
                    keep = F.at("riverine_forest", c["wr"][rv], c["wc"][rv]) > -0.6
                    sel = np.nonzero(rv)
                    pick = tuple(s[keep] for s in sel)
                    out[pick] = self.H["riverine_forest"]
                    m[pick] = False
            if m.any():
                out[m] = self._free(ri, c, m)
        return out

    def _standing(self, c, idx):
        reg = c["reg"][idx]; d = c["depth"][idx]; k = c["kind"][idx]; K = self.K
        wr, wc = c["wr"][idx], c["wc"][idx]
        res = np.where(d <= 2.0, self.H["open_still_water"], self.H["lake_bed"]).astype(np.uint8)
        best = np.full(d.shape, -1e9, np.float32)
        for h in STANDING:
            cap = self.depth_max.get(h) or (6.0 if h == "lake_bed" else 2.0)
            bonus = np.zeros(d.shape, np.float32)
            if h in ("cypress_swamp", "drowned_forest"):
                bonus += 1.2 * (k == K(["blackwater-swamp"])[0])
            if h == "reed_marsh":
                bonus += 1.2 * (k == K(["green-marsh"])[0])
            if h == "open_still_water":
                bonus += 1.0 * np.isin(k, K(("pond", "lake")))
            if h == "lake_bed":
                bonus += 1.5 * (d > 1.5) + 0.8 * (k == K(["lake"])[0])
            for ri in np.unique(reg):
                s = self.shares.get(int(ri), {}).get(h)
                if not s:
                    continue
                m = (reg == ri) & (d <= cap)
                if not m.any():
                    continue
                sc = F_at(self.fields, h, wr[m], wc[m]) + math.log(s) + bonus[m]
                better = sc > best[m]
                mi = np.nonzero(m)[0]
                best[mi[better]] = sc[better]
                res[mi[better]] = self.H[h]
        return res

    def _free(self, ri, c, m):
        F = self.fields
        wr, wc = c["wr"][m], c["wc"][m]
        sl, hh, sh_ = c["slope"][m], c["h"][m], c["shore"][m]
        sea = c["sea"][m]
        names = list(self.bias[ri])
        target = self.free(ri)
        best = np.full(wr.shape, -1e9, np.float32)
        res = np.zeros(wr.shape, np.uint8)
        for h in names:
            sc = F.at(h, wr, wc) + math.log(target[h]) + self.bias[ri][h]
            if h == "rocky_outcrop":
                sc += np.clip((sl - 12) / 10, 0, 1.5) + np.clip((hh - 20) / 30, 0, 1)
            elif h == "upland_scrub":
                sc += np.clip((hh - 10) / 25, 0, 1.2)
            elif h == "swamp_hummock":
                sc += 0.8 * (sh_ < 25) - np.clip((hh - 6) / 10, 0, 1)
            elif h == "coastal_grassland":
                sc += 0.6 * (sea < 200)
            elif h in WET_LAND:
                sc += 0.6 * (sh_ < 40) - 4 * np.clip((hh - 1.5) / 2.5, 0, 1)
            better = sc > best
            best[better] = sc[better]
            res[better] = self.H[h]
        return res


def micro_relief(hs: np.ndarray) -> np.ndarray:
    """Height (units, lightly smoothed) -> its height over the ground round it (sigma 6 samples, ~11 m), dm, int8:
    + a hump or bank top, - a hollow (the ground paint's wet and rough patches follow it)."""
    d = (hs - ndi.gaussian_filter(hs, 6)) / UPM * 10
    return np.clip(np.rint(d), -127, 127).astype(np.int8)


def F_at(fields, h, wr, wc):
    return fields.at(h, wr, wc)


# --- build ---------------------------------------------------------------------------------------------------------

def build(force: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    b, ox, oy = grid()
    inputs = [TERRAIN / "build.json", f.OUT / "water_classified.json", f.OUT / "cell_region.json",
              f.OUT / "margin_cells.json", TERRAIN / "places_terrain.json", Path(__file__)] + \
             [DB / f"{t}.jsonl" for t in ("habitat", "region_habitat", "road", "road_vertex")]
    key = f"{b['id']}:{_hash(inputs)}"
    kf = OUT / "key.txt"
    if not force and kf.exists() and kf.read_text() == key and (OUT / "stats.json").exists():
        log(f"landcover current ({key})")
        return json.loads((OUT / "stats.json").read_text())
    hm = np.load(TERRAIN / "heightmap.npy", mmap_mode="r")
    H, W = hm.shape
    log(f"landcover {b['id']}: {W} x {H} samples")
    habs = [h["id"] for h in jsonl("habitat")]
    regmap, regions = region_map()
    rindex = {n: i for i, n in enumerate(regions)}
    shares: dict = {}
    for r in jsonl("region_habitat"):
        if r["region_id"] in rindex:
            shares.setdefault(rindex[r["region_id"]], {})[r["habitat_id"]] = float(r["share"])
    kinds = sorted({k["id"] for k in jsonl("water_kind")})
    kidx = {k: i for i, k in enumerate(kinds)}
    # water kind per map px, filled into land px from the nearest water px
    wc_rows = json.loads((f.OUT / "water_classified.json").read_text())
    body_kind = np.full(max(r["raster_index"] for r in wc_rows) + 1, 255, np.uint8)
    for r in wc_rows:
        body_kind[r["raster_index"]] = kidx[r["water_kind_id"]]
    wpng = np.array(Image.open(f.OUT / "water_classified.png"))
    pxkind = body_kind[wpng]
    _, (ir, ic) = ndi.distance_transform_edt(pxkind == 255, return_indices=True)
    pxkind = pxkind[ir, ic]
    del ir, ic, wpng
    # context, full resolution
    water = np.empty((H, W), bool)
    for r0 in range(0, H, 1024):
        water[r0:r0 + 1024] = np.asarray(hm[r0:r0 + 1024]) < float(b["water_level_units"])
    log("shore distance")
    dl, (ir, ic) = ndi.distance_transform_edt(~water, return_indices=True)  # land -> nearest water
    dw = ndi.distance_transform_edt(water)  # water -> nearest land
    shore = np.where(water, -dw, dl).astype(np.float32) * M_PER_S
    del dl, dw
    # each water sample's own kind (its map px, which carries the nearest water kind), then land takes its water's
    kind = np.full((H, W), 255, np.uint8)
    for r0 in range(0, H, TILE):
        rr, cc = np.mgrid[r0:min(r0 + TILE, H), 0:W]
        py, px = sample_to_px(rr, cc, ox, oy)
        k = pxkind[np.clip(py.astype(int), 0, f.HEIGHT_PX - 1), np.clip(px.astype(int), 0, f.WIDTH_PX - 1)]
        kind[r0:r0 + TILE] = np.where(water[r0:r0 + TILE], k, 255)
    for r0 in range(0, H, TILE):
        sl = slice(r0, min(r0 + TILE, H))
        kind[sl] = np.where(water[sl], kind[sl], kind[ir[sl], ic[sl]])
    del ir, ic
    log("sea and running-water distance")
    seak = np.isin(kind, [kidx[k] for k in SEA_KINDS]) & water
    sea = (ndi.distance_transform_edt(~seak) * M_PER_S).astype(np.float32)
    del seak
    runk = np.isin(kind, [kidx[k] for k in RUN_KINDS]) & water
    run = (ndi.distance_transform_edt(~runk) * M_PER_S).astype(np.float32)
    del runk
    log("slope")
    hs = ndi.gaussian_filter(np.asarray(hm, np.float32), 1.5)
    gy, gx = np.gradient(hs, SAMPLE)
    relief = micro_relief(hs)
    del hs
    slope = np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
    del gx, gy
    log("roads, pads, margin")
    rd, rcls = road_field((H, W), road_segments(ox, oy))
    road = np.clip(np.rint(rd * M_PER_S * 10), 0, 6000).astype(np.uint16)
    roadcls = np.where(rd * M_PER_S < 100, rcls, 0).astype(np.uint8)
    del rd, rcls
    pad = place_mask((H, W), ox, oy)
    margin = margin_mask((H, W), ox, oy)
    fields = Fields((H, W), habs + ["_band", "_stand", "_glade"])
    ch = Chooser(habs, regions, shares, fields, kidx)

    def ctx(rs, cs):
        rr, cc = np.meshgrid(rs, cs, indexing="ij")
        wr, wc = fields.coords(rr.astype(np.float32), cc.astype(np.float32))
        py, px = sample_to_px(wr, wc, ox, oy)
        reg = regmap[np.clip(py.astype(int), 0, f.HEIGHT_PX - 1), np.clip(px.astype(int), 0, f.WIDTH_PX - 1)]
        hh = np.asarray(hm[rs][:, cs], np.float32) / UPM
        return {"wr": wr, "wc": wc, "reg": reg, "water": water[np.ix_(rs, cs)], "depth": np.maximum(-hh, 0),
                "h": hh, "slope": slope[np.ix_(rs, cs)], "shore": shore[np.ix_(rs, cs)],
                "kind": kind[np.ix_(rs, cs)], "sea": sea[np.ix_(rs, cs)],
                "run": run[np.ix_(rs, cs)]}

    # solve the per-region biases on a coarse subsample so the free land matches the shares
    log("calibrate")
    cs_ = ctx(np.arange(0, H, STEP), np.arange(0, W, STEP))
    for it in range(12):
        hab = ch.choose(cs_)
        worst = 0.0
        for ri, bias in ch.bias.items():
            m = (cs_["reg"] == ri) & ~cs_["water"]
            target = ch.free(ri)
            got = {h: 0 for h in bias}
            hv, cnt = np.unique(hab[m], return_counts=True)
            for v, n in zip(hv, cnt):
                name = habs[v - 1] if v else None
                if name in got:
                    got[name] += n
            tot = sum(got.values())
            if tot < 50:
                continue
            ttot = sum(target.values())
            for h in bias:
                g_ = got[h] / tot
                t_ = target[h] / ttot
                worst = max(worst, abs(g_ - t_))
                bias[h] = float(np.clip(bias[h] + 0.5 * math.log((t_ + 0.01) / (g_ + 0.01)), -4, 4))
        log(f"  pass {it}: worst free-share error {worst:.3f}")
    del cs_
    log("habitats")
    habitat = np.zeros((H, W), np.uint8)
    region = np.zeros((H, W), np.uint8)
    canopy = np.zeros((H, W), np.uint8)
    tree_h = {h["id"]: h for h in jsonl("habitat")}
    base_canopy = np.zeros(len(habs) + 1, np.float32)
    for i, hname in enumerate(habs):
        dens = float(tree_h[hname].get("density_per_ha") or 0)
        wet = tree_h[hname]["water"]
        if wet == "seabed" or hname in ("open_still_water", "reed_marsh", "cliff_face", "beach_shore"):
            base_canopy[i + 1] = 0.15 if hname in ("reed_marsh", "beach_shore", "cliff_face") else 0.0
        else:
            base_canopy[i + 1] = min(1.0, 0.25 + dens / 200)
    cols = np.arange(W)
    for r0 in range(0, H, TILE):
        rs = np.arange(r0, min(r0 + TILE, H))
        c = ctx(rs, cols)
        hb = ch.choose(c)
        habitat[rs] = hb
        region[rs] = np.clip(c["reg"], 0, 254).astype(np.uint8)
        stand = fields.at("_stand", c["wr"], c["wc"])
        glade = fields.at("_glade", c["wr"] * 2.1, c["wc"] * 2.1)  # finer: ~90 m glades
        cv = base_canopy[hb] * np.clip(1 + 0.4 * stand, 0.2, 1.6)
        cv *= np.clip((1.15 - glade) / 0.35, 0.08, 1)  # top ~12% of the glade field: open
        rdm = road[rs].astype(np.float32) / 10
        cv *= np.clip((rdm - 8) / 4, 0, 1)
        cv *= np.clip(pad[rs] / 30, 0, 1)
        cv *= np.where(~c["water"] & (c["run"] < 12), 0.5, 1)
        inwater = c["water"] & ~np.isin(hb, [ch.H[h] for h in TREE_IN_WATER])
        cv[inwater] = 0
        cv[np.isin(c["kind"], ch.K(RUN_KINDS)) & c["water"]] = 0
        canopy[rs] = np.clip(cv * 200, 0, 255).astype(np.uint8)
        if (r0 // TILE) % 4 == 0:
            log(f"  rows {r0}/{H}")
    flags = (water.astype(np.uint8) | (pad <= 0).astype(np.uint8) * 2 | margin.astype(np.uint8) * 4
             | (((road < 35) & (roadcls == 1)) | ((road < 20) & (roadcls == 2))).astype(np.uint8) * 8)
    del pad, margin
    log("write")
    for name, a in (("habitat", habitat), ("region", region), ("kind", kind), ("shore", dm(shore)),
                    ("sea", dm(sea, 0)), ("run", dm(run, 0)), ("road", road), ("roadcls", roadcls),
                    ("canopy", canopy), ("slope", np.clip(np.rint(slope), 0, 90).astype(np.uint8)), ("flags", flags),
                    ("relief", relief)):
        _save(name, a)
    legend = {"build_id": b["id"], "habitats": ["none"] + habs, "regions": regions, "kinds": kinds,
              "shape": [H, W], "origin_world": [ox, oy], "sample_units": SAMPLE,
              "units": {"shore": "dm", "sea": "dm", "run": "dm", "road": "dm", "canopy": "0..255", "slope": "deg",
                        "relief": "dm"},
              "flags": {"water": 1, "place_pad": 2, "margin": 4, "road_surface": 8}}
    (OUT / "legend.json").write_text(json.dumps(legend, indent=1))
    stats = report(habitat, region, water, canopy, habs, regions, shares)
    stats["key"] = key
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1))
    preview(habitat, habs)
    kf.write_text(key)
    return stats


def report(habitat, region, water, canopy, habs, regions, shares) -> dict:
    s = habitat[::4, ::4]; r = region[::4, ::4]; w = water[::4, ::4]; cv = canopy[::4, ::4]
    tot = s.size
    hv, cnt = np.unique(s, return_counts=True)
    overall = {(habs[v - 1] if v else "none"): round(n / tot, 4) for v, n in zip(hv, cnt)}
    per_region = {}
    for ri, name in enumerate(regions):
        m = (r == ri) & ~w
        if m.sum() < 100:
            continue
        hv, cnt = np.unique(s[m], return_counts=True)
        got = {(habs[v - 1] if v else "none"): round(n / m.sum(), 3) for v, n in zip(hv, cnt)}
        tgt = {h: v for h, v in shares.get(ri, {}).items() if h not in ("seabed_deep", "seabed_mid", "seabed_shallow")}
        per_region[name] = {"land_samples": int(m.sum()), "got": got, "target": tgt}
    forest = np.isin(s, [i + 1 for i, h in enumerate(habs) if h in
                         ("rainforest_floor", "swamp_hummock", "dry_hammock", "hist_grove", "riverine_forest")])
    cvf = cv[forest].astype(np.float32)
    open_share = float((cvf < 40).mean()) if cvf.size else 0.0
    return {"habitat_share": overall, "regions": per_region,
            "canopy_forest": {"mean": round(float(cvf.mean()), 1) if cvf.size else 0,
                              "cv": round(float(cvf.std() / (cvf.mean() + 1e-9)), 2) if cvf.size else 0,
                              "open_share": round(open_share, 3)}}


def preview(habitat, habs):
    lut = np.zeros((256, 3), np.uint8)
    for i, h in enumerate(habs):
        lut[i + 1] = COLOURS.get(h, (255, 0, 255))
    Image.fromarray(lut[habitat[::4, ::4]]).save(OUT / "preview.png")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    st = build(a.force)
    print(json.dumps({"habitat_share": st["habitat_share"], "canopy_forest": st["canopy_forest"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
