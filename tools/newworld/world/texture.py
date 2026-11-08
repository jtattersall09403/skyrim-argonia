"""The ground paint (nw-02 step 7): every LAND quadrant's base + alpha layers, from the landcover.

    python3 -m tools.newworld.world.texture [--out out/newworld/plugin]

Reads the land manifest (its terrain build) and out/newworld/landcover/ (the same build, or it stops), paints a
weight per material per vertex, and writes one shard per cell row, `<out>/tex/cy<+NNN>.bin`, each cell in x order:
    for each quadrant (BottomLeft, BottomRight, TopLeft, TopRight):
        uint8 n (layers, 1..7) | 7 uint8 material index (base first; 255 unused) | 6 x 289 uint8 opacity (alpha layer
        k at [k], vertex [y from the south][x] in the quadrant's 17 x 17, value / 255)
then `<out>/tex/materials.json` (the palette: index -> id, the source LTEX `plugin:edid` the writer copies as our own
record, and the GRAS list as `plugin:edid`), `<out>/tex/manifest.json` and `<out>/tex/stats.json` (the metrics below).

The recipe (numbers from research/nw-02-ground-water-rules.md and nw-02-salvage.md):
1. Habitat palette: each habitat paints 3 to 5 materials; each material's share wanders by its own multi-scale noise
   (exp(1.4 n), 30 to 300 m), so a habitat is never one texture and no texture holds a 1 km window.
2. Slope: rock patches over 22 deg on a noise mask (rock is a patch on noise, never a slope contour).
3. Water's edge, by the kind of the nearest water, on the signed shore distance: marsh (still inland: dirt slopes
   and mud straddling the line, marsh grass rising to 10 m), sea (beach straddling the line, ocean floor under it,
   beach fading over 40 m inland; mud under a mangrove fringe), river and stream (riverbed edge 0.42 -> 0.09 over
   10 m, river bottom in the bed), lake (rocky shelf and riverbed edge). The band's pull fades to the habitat.
4. Roads: the road dirt to the surface edge (3.45 m from a major spine, 2 m minor), the ground skirt beyond it,
   pull 1 to the edge, 0.36 at 8 m, 0 by 12 m (major; minor scaled 0.6).
5. Smooth: the weights are blurred over 1.5 vertices (soft ramps of 1 to 5 vertices), then each quadrant keeps
   its 7 heaviest materials (base + 6), chosen over the quadrant plus a one-vertex halo; at a vertex shared by
   quadrants only materials every sharer keeps survive, renormalised, so no layer drops out at a seam.
6. Layers: base = the quadrant's heaviest; alpha layers in falling coverage; opacities inverted from the weights
   (top down: o = w / what is left), so the composite is the painted weights exactly (to 1/255).
Interrupt-proof: keyed on the land key + landcover key + this code; resumes by row; 3 worker processes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from tools.newworld import landcover as lc

REPO = Path(__file__).resolve().parents[3]
LC = REPO / "out/newworld/landcover"
MAXL = 7
FADE = 6.0  # vertices
TOP_V = 4
HQ = 8  # halo, vertices, over which a quadrant's materials are chosen
PRUNE = 0.08
Q = 17
QBYTES = 1 + MAXL + (MAXL - 1) * Q * Q
M = 128 / 70.0  # metres per vertex

# id: (source LTEX plugin:edid, GRAS list) -- our own LTEX copies of these, with these grass lists
MATERIALS = {
    "forest_floor": ("Skyrim.esm:LPineForest03", ["Tropical Skyrim.esp:FernGrass01", "Tropical Skyrim.esp:TropicalGrass01"]),
    "moss": ("Black Marsh North.esp:LPineForest05", ["Tropical Skyrim.esp:FernGrass01"]),
    "wet_rock_moss": ("Black Marsh.esm:LPineForestDUPLICATE004", ["Skyrim.esm:FernGrass01"]),
    "swamp_mud": ("Black Marsh North.esp:LFieldGrassDUPLICATE003", ["King of the Murkmire.esp:ALPAGrassLong03B"]),
    "mud_reeds": ("King of the Murkmire.esp:LALPAMud01Reeds", ["King of the Murkmire.esp:ALPAGrassReeds01", "King of the Murkmire.esp:ALPAGrassReeds02", "King of the Murkmire.esp:ALPAGrassReeds03", "King of the Murkmire.esp:ALPAGrassReeds04"]),
    "marsh_grass": ("King of the Murkmire.esp:LALPAMarshGrass", ["King of the Murkmire.esp:ALPAGrassFern01", "King of the Murkmire.esp:ALPAGrassRams01", "King of the Murkmire.esp:ALPAGrassNettles01", "King of the Murkmire.esp:ALPAGrassLupin01"]),
    "rainforest": ("King of the Murkmire.esp:LALPARainforest", ["Tropical Skyrim.esp:ForestGrass01", "Tropical Skyrim.esp:ReachGrass01", "King of the Murkmire.esp:ALPAGrassFern02"]),
    "rainforest_low": ("King of the Murkmire.esp:LALPARainforestLow", ["Tropical Skyrim.esp:ForestGrass01", "King of the Murkmire.esp:ALPAGrassFern01", "Tropical Skyrim.esp:TropicalGrassPlant01"]),
    "dirt_grass": ("Black Marsh.esm:01MOSS1", ["Skyrim.esm:FieldGrass01"]),
    "dark_grass_rocks": ("Black Marsh North.esp:LFieldGrassDUPLICATE002", ["Tropical Skyrim.esp:TundraGrass01", "Skyrim.esm:TundraGrass04"]),
    "meadow": ("Skyrim.esm:LFieldGrass02", ["Skyrim.esm:FieldGrass02", "Tropical Skyrim.esp:TropicalGrassPlant01", "Tropical Skyrim.esp:TropicalGrassPlant02"]),
    "sand": ("Black Marsh North.esp:Sand", ["Skyrim.esm:BeachGrass01"]),
    "wet_sand": ("King of the Murkmire.esp:LALPAMudSand01", ["Skyrim.esm:BeachGrass01", "Skyrim.esm:BeachGrass02"]),
    "rock": ("Black Marsh North.esp:DarkRock1", []),
    "rock2": ("Black Marsh North.esp:LDirt03", []),
    "rock_grass": ("Skyrim.esm:LTundraRocks01", ["Tropical Skyrim.esp:RockGrass01"]),
    "dirt_road": ("Black Marsh North.esp:LFieldDirtGrassDUPLICATE002", []),
    "road_skirt": ("Skyrim.esm:LDirt02", []),
    "marsh_mud": ("King of the Murkmire.esp:LALPAMarshMud01", []),
    "riverbed_edge": ("Skyrim.esm:LRiverbedEdge01", []),
    "river_bottom": ("Skyrim.esm:LRiverBottom01", ["Skyrim.esm:RockGrassWater01", "DepthsOfSkyrim.esp:TBPRiverKelpGrass01"]),
    "river_mud": ("Skyrim.esm:LRiverMud01", ["Skyrim.esm:WaterKelpGrass02", "DepthsOfSkyrim.esp:TBP_Algae01"]),
    "beach": ("Skyrim.esm:LCoastBeach01", []),
    "ocean_floor": ("Skyrim.esm:LCoastOceanFloor01", ["Skyrim.esm:WaterKelpGrass01", "Skyrim.esm:WaterCoralGrass01", "DepthsOfSkyrim.esp:TBPSeaweed02Test", "DepthsOfSkyrim.esp:TBP_coralsmall01"]),
    "dirt_slopes": ("Skyrim.esm:LFrozenMarshDirtSlopes01", ["Tropical Skyrim.esp:CattailGrass01"]),
    "silt": ("King of the Murkmire.esp:LALPASilt01", []),
}
MAT = list(MATERIALS)
MI = {m: i for i, m in enumerate(MAT)}
NM = len(MAT)
PALETTE = {  # three or four materials a habitat (vanilla paints 3.15 a quadrant), none over 0.35
    "swamp_hummock": {"forest_floor": .3, "moss": .25, "wet_rock_moss": .2, "dirt_grass": .25},
    "dry_hammock": {"dirt_grass": .25, "meadow": .25, "forest_floor": .25, "dark_grass_rocks": .25},
    "hist_grove": {"moss": .3, "wet_rock_moss": .25, "rainforest": .25, "forest_floor": .2},
    "rainforest_floor": {"rainforest": .3, "rainforest_low": .3, "forest_floor": .2, "moss": .2},
    "riverine_forest": {"rainforest_low": .35, "forest_floor": .35, "moss": .3},
    "coastal_grassland": {"marsh_grass": .35, "meadow": .35, "wet_sand": .3},
    "upland_scrub": {"dark_grass_rocks": .35, "meadow": .35, "rock_grass": .3},
    "rocky_outcrop": {"rock_grass": .35, "rock": .35, "dark_grass_rocks": .3},
    "cliff_face": {"rock": .35, "rock2": .35, "rock_grass": .3},
    "beach_shore": {"sand": .35, "wet_sand": .35, "marsh_grass": .3},
    "mangrove_fringe": {"mud_reeds": .3, "marsh_mud": .3, "swamp_mud": .2, "wet_sand": .2},
    "reed_marsh": {"mud_reeds": .3, "marsh_grass": .3, "swamp_mud": .2, "dirt_slopes": .2},
    "cypress_swamp": {"swamp_mud": .3, "moss": .25, "marsh_mud": .25, "river_mud": .2},
    "drowned_forest": {"marsh_mud": .3, "swamp_mud": .3, "moss": .2, "river_mud": .2},
    "open_still_water": {"river_mud": .5, "swamp_mud": .3, "silt": .2},
    "lake_bed": {"river_bottom": .4, "river_mud": .35, "silt": .25},
    "seabed_shallow": {"ocean_floor": .45, "beach": .35, "silt": .2},
    "seabed_mid": {"ocean_floor": .6, "river_mud": .2, "river_bottom": .2},
    "seabed_deep": {"ocean_floor": .7, "river_bottom": .3},
}
# water's edge: per edge family, knots of signed shore distance (m, + land) -> material weights; pull to 0 at the ends
EDGE = {
    "marsh": [(-20, {"river_mud": .5, "swamp_mud": .3, "dirt_slopes": .2}), (-7, {"swamp_mud": .35, "dirt_slopes": .3, "river_mud": .35}),
              (-1, {"dirt_slopes": .5, "swamp_mud": .3, "river_mud": .2}), (1, {"dirt_slopes": .55, "mud_reeds": .25, "swamp_mud": .2}),
              (3.5, {"marsh_grass": .3, "dirt_slopes": .3, "mud_reeds": .25, "swamp_mud": .15}),
              (7.5, {"marsh_grass": .3, "dirt_slopes": .15, "mud_reeds": .2, "moss": .2, "swamp_mud": .15}),
              (15, {"marsh_grass": .25, "moss": .2, "forest_floor": .3, "dirt_slopes": .1, "mud_reeds": .15})],
    "sea": [(-30, {"ocean_floor": .6, "beach": .4}), (-8, {"beach": .5, "ocean_floor": .35, "silt": .15}),
            (-1, {"beach": .6, "wet_sand": .2, "ocean_floor": .2}), (1, {"beach": .55, "wet_sand": .3, "sand": .15}),
            (4, {"beach": .45, "sand": .3, "marsh_grass": .25}), (15, {"sand": .4, "beach": .3, "marsh_grass": .3}),
            (35, {"sand": .3, "marsh_grass": .3, "meadow": .4})],
    "mangrove": [(-20, {"river_mud": .5, "marsh_mud": .5}), (-2, {"swamp_mud": .4, "marsh_mud": .35, "mud_reeds": .25}),
                 (2, {"mud_reeds": .45, "swamp_mud": .25, "marsh_mud": .3}),
                 (12, {"mud_reeds": .35, "swamp_mud": .2, "marsh_grass": .25, "marsh_mud": .2})],
    "river": [(-15, {"river_bottom": .5, "river_mud": .3, "riverbed_edge": .2}), (-7, {"river_bottom": .45, "riverbed_edge": .3, "river_mud": .25}),
              (-3, {"riverbed_edge": .5, "river_bottom": .5}), (-1, {"riverbed_edge": .7, "river_bottom": .3}),
              (1, {"riverbed_edge": .75, "rock_grass": .25}), (3.5, {"riverbed_edge": .5, "rock_grass": .2, "forest_floor": .3}),
              (8, {"riverbed_edge": .25, "forest_floor": .45, "rock_grass": .3})],
    "lake": [(-20, {"riverbed_edge": .6, "river_bottom": .4}), (-3, {"riverbed_edge": .55, "rock_grass": .45}),
             (1, {"rock_grass": .55, "riverbed_edge": .45}), (4, {"rock_grass": .55, "riverbed_edge": .25, "dark_grass_rocks": .2}),
             (8, {"rock_grass": .45, "dark_grass_rocks": .35, "riverbed_edge": .2})],
}
EDGE_REACH = {"marsh": (-25, 22), "sea": (-40, 45), "mangrove": (-25, 18), "river": (-20, 11), "lake": (-25, 11)}
KIND_EDGE = {"ocean": "sea", "shallow-coast": "sea", "bay": "sea", "estuary": "mangrove", "river": "river",
             "stream": "river", "lake": "lake", "pond": "marsh", "green-marsh": "marsh", "blackwater-swamp": "marsh"}
ROCK = {"rock": .5, "rock_grass": .5}
NOISE_SEED = 9113
_VR = np.arange(33)
QRA = np.where(_VR % 16, 1 + _VR // 16, _VR // 16)  # the keep rows a cell vertex row shares (one, or two on a line)
QRB = 1 + _VR // 16


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def vec(d: dict) -> np.ndarray:
    v = np.zeros(NM, np.float32)
    for k, w in d.items():
        v[MI[k]] = w
    return v / v.sum()


def code_key() -> str:
    h = hashlib.sha256(Path(__file__).read_bytes())
    return h.hexdigest()[:16]


def edge_table(knots, lo, hi, n=256):
    """Signed distance grid (m) over [lo, hi] -> (weights [n, NM], pull [n])."""
    xs = np.linspace(lo, hi, n)
    kx = np.array([k[0] for k in knots])
    kv = np.stack([vec(k[1]) for k in knots])
    w = np.stack([np.interp(xs, kx, kv[:, j]) for j in range(NM)], 1)
    w /= w.sum(1, keepdims=True)
    # pull: 1 across the knots' span, cosine fade to 0 at the reach ends
    a, b = kx[0], kx[-1]
    pull = np.ones(n, np.float32)
    lo_f = xs < a
    pull[lo_f] = 0.5 - 0.5 * np.cos(np.pi * (xs[lo_f] - lo) / (a - lo))
    hi_f = xs > b
    pull[hi_f] = 0.5 + 0.5 * np.cos(np.pi * (xs[hi_f] - b) / (hi - b))
    return xs, w.astype(np.float32), pull


class Painter:
    def __init__(self, legend):
        H, W = legend["shape"]
        self.habs = legend["habitats"]
        self.kinds = legend["kinds"]
        self.hab_vec = np.zeros((len(self.habs), NM), np.float32)
        for i, h in enumerate(self.habs):
            self.hab_vec[i] = vec(PALETTE.get(h, {"forest_floor": 1}))
        self.fields = lc.Fields((H, W), MAT + ["_rock"], seed=NOISE_SEED)
        for k, m in enumerate(MAT):  # material mixes vary at 30 to 300 m, so a 1 km window always holds several
            self.fields.f[m] = lc.fbm(NOISE_SEED + 500 + k, self.fields.cs, (2, 6, 20), (0.5, 1.0, 0.3))
        self.edges = {k: edge_table(v, *EDGE_REACH[k]) for k, v in EDGE.items()}
        self.kind_edge = np.full(256, -1, np.int16)
        names = list(EDGE)
        for i, k in enumerate(self.kinds):
            self.kind_edge[i] = names.index(KIND_EDGE[k])
        self.edge_names = names
        self.rock = vec(ROCK)
        self.arr = {n: np.load(LC / f"{n}.npy", mmap_mode="r") for n in ("habitat", "kind", "shore", "road", "roadcls", "slope")}
        self.mangrove = self.habs.index("mangrove_fringe")

    def weights(self, r0, r1, c0, c1) -> np.ndarray:
        """Painted, unblurred weights [rows, cols, NM] for sample rows r0:r1, cols c0:c1 (clipped to the grid)."""
        A = self.arr
        sl = (slice(r0, r1), slice(c0, c1))
        hab = np.asarray(A["habitat"][sl])
        rr, cc = np.mgrid[r0:r1, c0:c1].astype(np.float32)
        wr, wc = self.fields.coords(rr, cc)
        w = self.hab_vec[hab].copy()
        for j, m in enumerate(MAT):
            col = w[..., j]
            nz = col > 0
            if nz.any():
                col[nz] *= np.exp(1.4 * self.fields.at(m, wr[nz], wc[nz]))
        w /= w.sum(-1, keepdims=True) + 1e-9
        # rock patches on slopes
        slope = np.asarray(A["slope"][sl], np.float32)
        steep = slope > 18
        if steep.any():
            q = np.zeros(slope.shape, np.float32)
            q[steep] = np.clip((slope[steep] - 22) / 15, 0, 1) * np.clip(0.6 + 0.6 * self.fields.at("_rock", wr[steep], wc[steep]), 0, 1)
            w = w * (1 - q[..., None]) + q[..., None] * self.rock
        # water's edge
        shore = np.asarray(A["shore"][sl], np.float32) / 10
        kind = np.asarray(A["kind"][sl])
        fam = self.kind_edge[kind]
        fam = np.where((fam == self.edge_names.index("sea")) & (hab == self.mangrove), self.edge_names.index("mangrove"), fam)
        for fi, name in enumerate(self.edge_names):
            xs, tw, pull = self.edges[name]
            m = (fam == fi) & (shore > xs[0]) & (shore < xs[-1])
            if not m.any():
                continue
            t = np.clip(np.rint((shore[m] - xs[0]) / (xs[-1] - xs[0]) * (len(xs) - 1)).astype(int), 0, len(xs) - 1)
            p = pull[t][:, None]
            w[m] = w[m] * (1 - p) + p * tw[t]
        # roads
        road = np.asarray(A["road"][sl], np.float32) / 10
        cls = np.asarray(A["roadcls"][sl])
        near = (cls > 0) & (road < 12) & (shore > 0)
        if near.any():
            s = np.where(cls[near] == 1, 1.0, 0.6)
            r = road[near] / s
            core = 3.45
            pull = np.interp(r, [0, 3.0, 5.0, 6.0, 8.0, 12.0], [1, 0.97, 0.76, 0.56, 0.36, 0.0]).astype(np.float32)
            inner = np.clip((core + 0.9 - r) / 1.8, 0, 1)  # road dirt to the surface edge, skirt dirt beyond
            rv = np.zeros((r.size, NM), np.float32)
            rv[:, MI["dirt_road"]] = inner
            rv[:, MI["road_skirt"]] = 1 - inner
            w[near] = w[near] * (1 - pull[:, None]) + pull[:, None] * rv
        return w


def quadrant_sets(w: np.ndarray, hq: int = 1):
    """w [rows, cols, NM] on a window whose row/col hq lies on a quadrant line (an hq-vertex halo before it):
    -> (keep [qr, qc, NM] bool, sums [qr, qc, NM]). A quadrant keeps the heaviest material at each of its four
    corners (so the quadrants meeting at a corner, and along an edge, always share one), then its heaviest by
    summed weight over the quadrant + its hq halo, up to MAXL (a wide halo makes neighbours' sets agree)."""
    R, C = w.shape[0] - 2 * hq, w.shape[1] - 2 * hq
    nqr, nqc = (R - 1) // 16, (C - 1) // 16
    keep = np.zeros((nqr, nqc, NM), bool)
    sums = np.zeros((nqr, nqc, NM), np.float64)
    corner = np.argmax(w[hq:R + hq:16, hq:C + hq:16], -1)  # the heaviest material at every quadrant corner
    for i in range(nqr):
        a, b = i * 16, i * 16 + 17 + 2 * hq  # quadrant 17 + halo each side
        for j in range(nqc):
            c, d = j * 16, j * 16 + 17 + 2 * hq
            # summed directly and rounded, ties to the lower index: every window that sees this quadrant picks alike
            s = np.round(w[a:b, c:d].astype(np.float64).sum((0, 1)), 4)
            sums[i, j] = s
            forced = list(dict.fromkeys(int(corner[i + di, j + dj]) for di in (0, 1) for dj in (0, 1)))
            top = forced + [int(k) for k in np.lexsort((np.arange(NM), -s)) if s[k] > 1e-3 and k not in forced]
            keep[i, j, top[:MAXL]] = True
    return keep, sums


def final_sets(w: np.ndarray) -> np.ndarray:
    """Seam-safe sets. Base sets first; then every vertex on a quadrant's border whose sharers' common base set holds
    under 95% of its weight forces its heaviest missing materials into each sharer (a pure function of the base sets, so
    overlapping windows agree); a quadrant keeps its forced materials, then its heaviest, up to MAXL. Returns the
    final sets of the inner quadrants (all but the outermost ring) as [qr-2, qc-2, NM]."""
    base, sums = quadrant_sets(w)
    nqr, nqc = base.shape[:2]
    forced = np.zeros_like(base)

    def sharers(v):
        return [v // 16 - 1, v // 16] if v % 16 == 0 else [v // 16]

    for i in range(1, nqr - 1):
        for j in range(1, nqc - 1):
            ys = list(range(16 * i, 16 * i + 17)); xs = list(range(16 * j, 16 * j + 17))
            border = [(y, x) for y in (16 * i, 16 * i + 16) for x in xs] + [(y, x) for x in (16 * j, 16 * j + 16) for y in ys[1:-1]]
            for (y, x) in border:
                rs, cs_ = sharers(y), sharers(x)
                inter = np.logical_and.reduce([base[r, c] for r in rs for c in cs_ if 0 <= r < nqr and 0 <= c < nqc])
                wv = w[y + 1, x + 1]
                miss = np.where(inter, 0, wv)
                while wv.sum() - miss.sum() < 0.95 and miss.max() > 0:  # force the heaviest missing ones
                    k = int(np.argmax(miss))
                    forced[i, j, k] = True
                    miss[k] = 0
    out = np.zeros((nqr - 2, nqc - 2, NM), bool)
    for i in range(1, nqr - 1):
        for j in range(1, nqc - 1):
            f_ = np.nonzero(forced[i, j])[0].tolist()
            rest = [int(k) for k in np.argsort(-sums[i, j]) if base[i, j, k] and k not in f_]
            out[i - 1, j - 1, (f_ + rest)[:MAXL]] = True
    return out


def encode_row(p: Painter, g: dict, cy: int):
    """One cell row: shard bytes and per-row stats."""
    H, W = p.arr["habitat"].shape
    north = (g["cy_top"] - cy) * 32
    halo = 40  # two quadrants + halo vertex + the blur's reach (6)
    r0, r1 = north - halo, north + 33 + halo
    rr0, rr1 = max(r0, 0), min(r1, H)
    w = p.weights(rr0, rr1, 0, W)
    w = np.pad(w, ((rr0 - r0, r1 - rr1), (0, 0), (0, 0)), mode="edge")
    # local budget: each vertex paints its TOP_V heaviest materials only (vanilla: 4 distinct LTEX a cell at p50),
    # so after the blur a quadrant rarely needs more than its 7 layers and the seam fade seldom has work to do
    kth = np.partition(w, NM - TOP_V, axis=-1)[..., NM - TOP_V:NM - TOP_V + 1]
    w = np.where(w >= kth, w, 0)
    w /= w.sum(-1, keepdims=True)
    w = ndi.gaussian_filter(w, (1.5, 1.5, 0), mode="nearest")
    w[w < PRUNE] = 0  # traces under 8% are dropped before the sets are chosen (a step of at most PRUNE)
    w /= w.sum(-1, keepdims=True)
    # quadrant lattice: 6 quadrant rows from north-32 (the cell's two are rows 2, 3), 2 quadrant columns of pad
    a0 = halo - 32 - HQ
    win = np.pad(w[a0:a0 + 97 + 2 * HQ], ((0, 0), (32 + HQ, 32 + HQ), (0, 0)), mode="edge")
    keep, _ = quadrant_sets(win, HQ)  # [6, nqc, NM]; quadrant row 2, 3 = the cell's; column j = global quadrant j - 2
    # seam fade: each material fades to 0 over FADE vertices toward any quadrant that does not keep it (closed
    # squares, so a shared vertex reads the same from every quadrant), a pure function of position and the sets
    nqr, nqc = keep.shape[:2]
    fade = np.ones((97, nqc * 16 + 1, NM), np.float32)
    for m in range(NM):
        lack = ~keep[:, :, m]
        if not lack.any():
            continue
        core = np.kron(lack, np.ones((16, 16), bool))
        cl = np.zeros((97, nqc * 16 + 1), bool)
        cl[:96, :nqc * 16] = core
        cl[16::16, :nqc * 16] |= core[15::16][:cl[16::16].shape[0]]
        cl[:, 16::16] |= cl[:, 15::16][:, :cl[:, 16::16].shape[1]]
        if cl.all():
            fade[..., m] = 0
            continue
        fade[..., m] = np.clip(ndi.distance_transform_edt(~cl) / FADE, 0, 1)
    out = bytearray()
    st = {"layers": []}
    cell_rows = w[halo:halo + 33]
    # what a fade takes is given back from a broad blur (sigma 6) of the materials still allowed there, so no
    # vertex is renormalised from a small remainder (which would jump)
    broad = ndi.gaussian_filter(w[halo - 24:halo + 57], (6, 6, 0), mode="nearest")[24:57]
    for i in range(g["cells_x"]):
        sl = slice(i * 32, i * 32 + 33)
        allowed = fade[32:65, i * 32 + 32:i * 32 + 65]
        cw = cell_rows[:, sl] * allowed
        s = cw.sum(-1, keepdims=True)
        fill = broad[:, sl] * allowed
        fs = fill.sum(-1, keepdims=True)
        ok = fs[..., 0] > 1e-4
        cw[ok] += (1 - s[ok]) * fill[ok] / fs[ok]
        s = cw.sum(-1, keepdims=True)
        bad = s[..., 0] < 1e-6
        if bad.any():  # nothing allowed at all: the unrestricted paint (counted as dropout)
            st["dropout"] = st.get("dropout", 0) + int(bad.sum())
            cw[bad] = cell_rows[:, sl][bad]
            s = cw.sum(-1, keepdims=True)
        cw /= s
        cw = cw[::-1]  # y from the south
        for (qy, qx) in ((0, 0), (0, 1), (1, 0), (1, 1)):  # BottomLeft, BottomRight, TopLeft, TopRight
            qw = cw[qy * 16:qy * 16 + Q, qx * 16:qx * 16 + Q]  # [17, 17, NM]
            tot = qw.reshape(-1, NM).sum(0)
            order = [int(k) for k in np.argsort(-tot) if tot[k] > 1e-4][:MAXL]
            out += _quad_bytes(qw, order)
            st["layers"].append(len(order))
    return bytes(out), st


def _quad_bytes(qw, order) -> bytes:
    n = len(order)
    mats = np.full(MAXL, 255, np.uint8)
    mats[:n] = order
    alph = np.zeros((MAXL - 1, Q * Q), np.uint8)
    flat = qw.reshape(-1, NM)
    left = np.ones(Q * Q, np.float64)
    ops = []
    for k in range(n - 1, 0, -1):  # top layer first
        wk = flat[:, order[k]].astype(np.float64)
        o = np.where(left > 1e-6, np.clip(wk / np.maximum(left, 1e-9), 0, 1), 0)
        ops.append((k - 1, o))
        left = left * (1 - o)
    for k, o in ops:
        alph[k] = np.rint(o * 255).astype(np.uint8)
    return bytes([n]) + mats.tobytes() + alph.tobytes()


def decode_quad(b: bytes, off: int):
    """-> (materials list, composite weights [289, n]) as the engine stacks them."""
    n = b[off]
    mats = list(b[off + 1:off + 1 + n])
    alph = np.frombuffer(b, np.uint8, (MAXL - 1) * Q * Q, off + 1 + MAXL).reshape(MAXL - 1, Q * Q).astype(np.float32) / 255
    w = np.zeros((Q * Q, n), np.float32)
    w[:, 0] = 1
    for k in range(1, n):
        o = alph[k - 1]
        w[:, :k] *= (1 - o)[:, None]
        w[:, k] = o
    return mats, w


WORKERS = 3
_W: dict = {}


def _init(legend, g, tex):
    _W.update(p=Painter(legend), g=g, tex=Path(tex))


def _row(cy: int) -> int:
    f_ = _W["tex"] / f"cy{cy:+04d}.bin"
    data, st = encode_row(_W["p"], _W["g"], cy)
    tmp = f_.with_suffix(".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, f_)
    f_.with_suffix(".json").write_text(json.dumps(st))
    return cy


def build(out: Path) -> dict:
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    if legend["build_id"] != man["build_id"]:
        raise RuntimeError(f"landcover is build {legend['build_id']}, land is {man['build_id']}: rerun landcover")
    g = man["grid"]
    tex = out / "tex"
    tex.mkdir(parents=True, exist_ok=True)
    key = f"{man['key']}:{(LC / 'key.txt').read_text()}:{code_key()}"
    kf = tex / "key.txt"
    if (kf.read_text() if kf.exists() else "") != key:
        for f_ in tex.iterdir():
            f_.unlink()
        kf.write_text(key)
    mats = [{"index": i, "id": m, "ltex": MATERIALS[m][0], "grass": MATERIALS[m][1]} for i, m in enumerate(MAT)]
    (tex / "materials.json").write_text(json.dumps(mats, indent=1))
    rows = list(range(g["cy_top"], g["cy_bottom"] - 1, -1))
    todo = [cy for cy in rows if not ((tex / f"cy{cy:+04d}.bin").exists() and (tex / f"cy{cy:+04d}.json").exists())]
    # rows are independent (each window carries its neighbours' quadrants), so a pool paints them; the landcover
    # arrays are memory-mapped, shared between workers
    if todo:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(WORKERS, initializer=_init, initargs=(legend, g, str(tex))) as ex:
            for k, cy in enumerate(ex.map(_row, todo)):
                if k % 10 == 0:
                    log(f"  tex row {cy} ({k + 1}/{len(todo)})")
    layers, drop = [], 0
    for cy in rows:
        st = json.loads((tex / f"cy{cy:+04d}.json").read_text())
        layers += st["layers"]
        drop += st.get("dropout", 0)
    hist = np.bincount(layers, minlength=MAXL + 1).tolist()
    mf = {"key": key, "build_id": man["build_id"], "quad_bytes": QBYTES, "max_layers": MAXL,
          "shards": [f"cy{cy:+04d}.bin" for cy in rows], "layers_hist": hist, "seam_dropout_vertices": drop}
    (tex / "manifest.json").write_text(json.dumps(mf, indent=1))
    log(f"tex: layers per quadrant {hist}, seam dropout vertices {drop}")
    return mf


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    a = ap.parse_args(argv)
    build(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
