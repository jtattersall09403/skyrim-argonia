"""The ground's material: per region class a gradient of BM&V landscape textures keyed to the ground (1.15 §c).

Replaces paint.py and the land-cover raster as the paint source. For every LAND vertex the rule reads four keys:

- `dh`: height above local water (metres; negative = submerged depth). Local water is the low-passed level of
  the water near the vertex (the water lane's `nearest_level` once `water/solve.py` lands; the old body-level
  raster `hydrology-graph-bodies.npz` as the fixture until then), the sea at 0 where no water is near;
- `slope` (degrees) and `north` (the northness of the slope's aspect, -1..1), from the heights;
- `wet`: a low-pass of the water mask at two scales (≈15 m and ≈45 m), 0 dry .. 1 in water;
- `noise`: position-seeded value noise (two octaves, 90 m and 30 m), the same at a vertex whatever the window.

Each region class (`eco_class`, from `cell_region_run`; the apron is `border`) has 4-6 stops (`STOPS`, the
`material_gradient` rows): an LTEX and soft ranges on the keys. A stop's weight is the product of smooth
trapezoids, so every transition is a gradient of the keys, never a class edge. Upland stops read a band height
`dh + noise * amp` (amp grows with height), so mountainsides break into bands and patches (options §8). The
classes blend over ~30 m (a double box over the per-cell class map), the stop weights are smoothed again over
~12 m (a double 3-vertex box: a blend spans 6-11 vertices), and weights under 3 % are dropped.

Quadrants (`quadrant_sets`): each LAND quadrant keeps its base plus up to `MAX_ALPHA` alpha layers by total
weight, ties broken toward the textures its neighbours keep. The seam fix: a vertex's weights are restricted to
the textures kept by every quadrant that shares it (1, 2 or 4) and renormalised, so the two sides of a quadrant
or cell seam composite the same weights and nothing drops out at the seam.

VCLR (`vclr`): shade from slope and aspect (north faces darker) and wet (darker toward water), multiplied into
the old ground tint.

Lore and research behind the stops: `docs/design/research/world-terrain/tropical-shoreline-materials.md`
(A1-A10: exposure sorts sediment; sheltered shores are mud, mangrove fringe is dark organic mud),
`docs/design/research/rendering/skyrim-morrowind-landscape-texture-granularity.md` (vanilla's three-stage water
edge RiverBottom -> RiverMud -> RiverbedEdge; ~6 textures per quad; biome families),
`docs/design/research/world-terrain/mangrove-coastal-ecology.md`, the lore dossier black-marsh-province.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import numpy as np

from tools.argonia_world import skyrim_units as su

QV = su.QUADRANT_VERTS  # 17
QS = QV - 1  # 16 quads per quadrant side
MAX_ALPHA = 5  # base plus five: six textures a quadrant (the CK's practical limit; options §2)
HALO = 64  # vertices of context a window reads around itself (the blurs' and the wetness's reach)
MIN_W = 0.03
INF = float("inf")


# ---- the texture set ------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Tex:
    edid: str  # the vanilla LTEX we paint (Skyrim.esm), re-pointed at BM&V's file by our TXST
    form_key: str
    bmv: str  # BM&V's diffuse, under textures\ (Black Marsh & Valenwood part 2, TEXTUREPACK\landscape)
    why: str


TEXTURES: tuple[Tex, ...] = tuple(Tex(*r) for r in (
    ("LRiverBottom01", "013184:Skyrim.esm", r"TEXTUREPACK\landscape\riverbottom.dds",
     "submerged bed: vanilla's water-edge stage 3 (granularity research)"),
    ("LRiverMud01", "0132E9:Skyrim.esm", r"TEXTUREPACK\landscape\rivermud.dds",
     "exposed wet mud, sheltered flats (shoreline A2, A6, A8)"),
    ("LRiverbedEdge01", "01301F:Skyrim.esm", r"TEXTUREPACK\landscape\riverbededge.dds",
     "the waterline band (granularity research: RiverBedEdge)"),
    ("LCoastOceanFloor01", "06B4C6:Skyrim.esm", r"TEXTUREPACK\landscape\coastoceanfloor01.dds",
     "sea floor below the shelf (shoreline A10)"),
    ("LCoastBeach01", "06B3CF:Skyrim.esm", r"TEXTUREPACK\landscape\coastbeach01.dds",
     "BM&V's dark tidal sand: exposed shore and bars (shoreline A1, A4)"),
    ("LCoastBeachGrass01", "06DD55:Skyrim.esm", r"TEXTUREPACK\landscape\coastbeachgrass01.dds",
     "grassed backshore above the sand (shoreline A1)"),
    ("LFrozenMarshLichen01", "075069:Skyrim.esm", r"TEXTUREPACK\landscape\frozenmarshlichen01.dds",
     "organic muck at swamp margins (shoreline A3, A8)"),
    ("LFrozenMarshGrass01", "075067:Skyrim.esm", r"TEXTUREPACK\landscape\frozenmarshgrass01.dds",
     "marsh grass of the upper bank (shoreline A6, A9)"),
    ("LFallForestDirt01", "057DCF:Skyrim.esm", r"TEXTUREPACK\landscape\fallforestdirt01.dds",
     "rooty forest floor (asset strategy: BM&V's rooty floors)"),
    ("LFallForestLeaves01", "057DC7:Skyrim.esm", r"TEXTUREPACK\landscape\fallforestleaves01.dds",
     "leaf litter under swamp forest (shoreline A3 upper fringe, A8)"),
    ("LPineForest03", "013876:Skyrim.esm", r"TEXTUREPACK\landscape\pineforest03.dds",
     "BM&V's own most painted ground (6,079 of its LAND layers): the swamp forest floor"),
    ("LPineForest02", "0137CC:Skyrim.esm", r"TEXTUREPACK\landscape\pineforest02.dds",
     "upland forest floor with fern"),
    ("LFieldGrass02", "01342A:Skyrim.esm", r"TEXTUREPACK\landscape\fieldgrass02.dds",
     "BM&V's mossy grass, its third most painted (909 layers): open floodplain"),
    ("LReachMoss01", "01CC43:Skyrim.esm", r"TEXTUREPACK\landscape\reachmoss01.dds",
     "moss mat: the grass-to-rock transition (granularity research's transition slot)"),
    ("LReachMossyRocks01", "01CC45:Skyrim.esm", r"TEXTUREPACK\landscape\reachmossyrocks01.dds",
     "wet mossy rock on steep inland ground"),
    ("LReachDirt01", "021711:Skyrim.esm", r"TEXTUREPACK\landscape\reachdirt01.dds",
     "red-brown earth of the drier north (shoreline A6 clay bank)"),
    ("LRocks01", "000AE4:Skyrim.esm", r"TEXTUREPACK\landscape\rocks01.dds",
     "bare rock of cliffs and summits (border ranges)"),
    ("LTundraRocks01", "02C6C6:Skyrim.esm", r"TEXTUREPACK\landscape\tundrarocks01.dds",
     "scree and broken rock below cliffs"),
    ("LDirtPath01", "0B424C:Skyrim.esm", r"TEXTUREPACK\landscape\dirtpath01.dds", "roads and paths (2.W3)"),
))
TEX = {t.edid: t for t in TEXTURES}
ROAD = "LDirtPath01"


# ---- the gradient ---------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Stop:
    ltex: str
    dh: tuple[float, float] = (-INF, INF)  # metres above local water (band height for upland stops)
    slope: tuple[float, float] = (-INF, INF)  # degrees
    wet: tuple[float, float] = (-INF, INF)  # 0..1
    noise: tuple[float, float] = (-INF, INF)  # 0..1
    w: float = 1.0
    north: float = 0.0  # weight gain on north faces (moss), loss on south
    why: str = ""


SOFT = {"dh": 0.8, "slope": 5.0, "wet": 0.12, "noise": 0.12}
# the shared water edge: bed, mud, waterline (vanilla's three stages)
BED = Stop("LRiverBottom01", dh=(-INF, -1.0), why="granularity research: submerged stage")
EDGE = Stop("LRiverbedEdge01", dh=(-0.6, 0.5), slope=(-INF, 30), w=1.3, why="granularity research: waterline band")
MUD = Stop("LRiverMud01", dh=(0.6, 2.2), slope=(-INF, 14), wet=(0.2, INF), w=1.2,
           why="shoreline A2/A6/A8: sheltered water leaves mud")
ROCK = Stop("LReachMossyRocks01", slope=(34, INF), w=1.4, north=0.3, why="options §8: steep ground is rock")

STOPS: dict[str, tuple[Stop, ...]] = {
    "coastal-lagoon": (
        Stop("LCoastOceanFloor01", dh=(-INF, -2.5), why="shoreline A10: the shelf"),
        Stop("LCoastBeach01", dh=(-2.5, 1.2), wet=(-INF, 0.75), why="shoreline A1: wave-sorted sand"),
        MUD,
        Stop("LFrozenMarshGrass01", dh=(0.8, 6), noise=(0.25, INF), why="shoreline A6: marsh above the mud"),
        Stop("LFallForestDirt01", dh=(4, INF), why="shoreline A3: mangrove-forest floor inland"),
        ROCK),
    "tidal-delta": (
        Stop("LCoastOceanFloor01", dh=(-INF, -2.5), why="shoreline A4: delta front"),
        Stop("LCoastBeach01", dh=(-2.5, 0.6), noise=(0.45, INF), why="shoreline A4: sand bars"),
        MUD, EDGE,
        Stop("LFrozenMarshGrass01", dh=(0.6, 5), why="shoreline A4: marsh on the flanks"),
        Stop("LCoastBeachGrass01", dh=(3, INF), why="shoreline A1: grassed bar tops"),
    ),
    "flooded-forest": (
        BED, MUD, EDGE,
        Stop("LFallForestLeaves01", dh=(0.6, 8), noise=(-INF, 0.55), why="shoreline A8: submerged and wet litter"),
        Stop("LPineForest03", dh=(1.5, INF), w=1.1, why="BM&V's swamp forest floor (its most painted ground)"),
        Stop("LFallForestDirt01", dh=(2, INF), noise=(0.6, INF), why="rooty patches (BM&V roots-in-mudbank)"),
    ),
    "interior-swamp": (
        BED, MUD,
        Stop("LFrozenMarshLichen01", dh=(-0.3, 2.5), wet=(0.15, INF), why="shoreline A8: muck margin"),
        Stop("LFrozenMarshGrass01", dh=(1, INF), noise=(-INF, 0.6), why="shoreline A9: reed and marsh grass"),
        Stop("LFallForestDirt01", dh=(2.5, INF), noise=(0.5, INF), why="shoreline A8: swamp-forest floor"),
        Stop("LReachMoss01", slope=(18, INF), why="moss on the few banks"),
    ),
    "deep-sink-basin": (
        BED, MUD, EDGE,
        Stop("LFrozenMarshLichen01", dh=(0.4, 4), why="shoreline A8: muck round the sink"),
        Stop("LFallForestLeaves01", dh=(2.5, INF), why="litter on the basin rim"),
        ROCK),
    "deep-river-corridor": (
        BED, EDGE, MUD,
        Stop("LFallForestLeaves01", dh=(1.5, INF), noise=(-INF, 0.5), why="gallery forest litter"),
        Stop("LFallForestDirt01", dh=(1.5, INF), noise=(0.5, INF), why="rooty banks"),
        ROCK),
    "rootland": (
        BED, EDGE,
        Stop("LPineForest03", dh=(0.8, INF), w=1.1, why="root-bound forest floor"),
        Stop("LFallForestDirt01", dh=(0.8, INF), noise=(0.55, INF), why="roots in mud bank"),
        Stop("LReachMoss01", slope=(14, INF), north=0.5, why="moss on rises"),
        ROCK),
    "seasonal-floodplain": (
        BED, MUD, EDGE,
        Stop("LFieldGrass02", dh=(0.8, INF), why="BM&V's mossy grass on the flood flats"),
        Stop("LFrozenMarshGrass01", dh=(0.8, 3), wet=(0.2, INF), why="wet marsh grass near the channel"),
        Stop("LFallForestDirt01", dh=(3, INF), noise=(0.6, INF), why="levee floor"),
    ),
    "northern-transition": (
        BED, EDGE,
        Stop("LReachDirt01", dh=(0.8, INF), noise=(0.5, INF), why="red earth of the drier north (Dunmer border)"),
        Stop("LFieldGrass02", dh=(0.8, 120), noise=(-INF, 0.6), why="grass of the transition"),
        Stop("LTundraRocks01", slope=(24, 38), why="scree below the ranges"),
        Stop("LRocks01", slope=(36, INF), w=1.3, why="bare rock of the Velothi foothills"),
    ),
    "western-frontier": (
        BED, EDGE,
        Stop("LPineForest02", dh=(0.8, 260), slope=(-INF, 26), why="upland forest (Kinabalu cloud forest, mountain synthesis)"),
        Stop("LReachMoss01", dh=(0.8, INF), slope=(14, 34), north=0.6, noise=(0.35, INF),
             why="moss bands on the flanks (options §8)"),
        ROCK,
        Stop("LRocks01", dh=(220, INF), slope=(26, INF), w=1.2, why="bare rock of the summits (border ranges)"),
    ),
    "karst-cavern-belt": (
        BED, EDGE,
        Stop("LFallForestDirt01", dh=(0.8, INF), why="forest floor over limestone"),
        Stop("LReachMoss01", slope=(12, 34), north=0.5, why="moss on karst"),
        ROCK,
        Stop("LTundraRocks01", slope=(26, 38), noise=(0.5, INF), why="broken limestone"),
    ),
    "border": (
        Stop("LCoastOceanFloor01", dh=(-INF, -3), why="the apron's sea"),
        EDGE,
        Stop("LPineForest03", dh=(0.8, 200), why="the apron's forest"),
        Stop("LReachMoss01", slope=(16, 36), north=0.5, why="moss on the apron's slopes"),
        ROCK,
        Stop("LRocks01", dh=(200, INF), w=1.2, why="the apron's ranges"),
    ),
}
CLASSES = tuple(STOPS)


def gradient_rows() -> list[dict]:
    """The `material_gradient` rows: one per eco class and stop (the code-only `border` fallback has none)."""
    out = []
    for c, stops in STOPS.items():
        if c == "border":
            continue
        for i, s in enumerate(stops):
            out.append({"eco_class_id": c, "stop": i, "ltex_form_key": TEX[s.ltex].form_key,
                        "dh_lo": _fin(s.dh[0]), "dh_hi": _fin(s.dh[1]), "slope_lo": _fin(s.slope[0]),
                        "slope_hi": _fin(s.slope[1]), "wet_lo": _fin(s.wet[0]), "wet_hi": _fin(s.wet[1]),
                        "noise_lo": _fin(s.noise[0]), "noise_hi": _fin(s.noise[1]), "weight": s.w,
                        "north": s.north, "why": s.why})
    return out


def write_gradient(w) -> int:
    """Replace `material_gradient` with gradient_rows() and save (`terrain gradient`)."""
    for r in w.query("SELECT eco_class_id, stop FROM material_gradient"):
        w.delete("material_gradient", *r)
    n = w.insert_many("material_gradient", gradient_rows())
    w.save()
    return n


def _fin(v: float):
    return None if abs(v) == INF else v


# ---- numpy helpers --------------------------------------------------------------------------------------------
def box(a: np.ndarray, r: int, axes=(0, 1)) -> np.ndarray:
    """A (2r+1) box mean over the first two axes (edge-padded), by cumulative sums."""
    out = np.asarray(a, dtype=np.float32)
    for ax in axes:
        pad = [(0, 0)] * out.ndim
        pad[ax] = (r + 1, r)
        c = np.cumsum(np.pad(out, pad, mode="edge"), axis=ax, dtype=np.float64)
        n = out.shape[ax]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax)
        lo = np.take(c, np.arange(0, n), axis=ax)
        out = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return out


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def ramp(x: np.ndarray, lo: float, hi: float, soft: float) -> np.ndarray:
    """A soft trapezoid: 1 inside [lo, hi], falling to 0 over `soft` either side of each bound."""
    up = 1.0 if lo == -INF else _smooth((x - lo + soft) / (2 * soft))
    dn = 1.0 if hi == INF else 1.0 - _smooth((x - hi + soft) / (2 * soft))
    return up * dn


def _hash(iy: np.ndarray, ix: np.ndarray, seed: int) -> np.ndarray:
    h = (iy.astype(np.uint64) * np.uint64(0x9E3779B1) + ix.astype(np.uint64) * np.uint64(0x85EBCA77)
         + np.uint64(seed * 0xC2B2AE3D)) & np.uint64(0xFFFFFFFF)
    h ^= h >> np.uint64(15)
    h = (h * np.uint64(0x2C1B3C6D)) & np.uint64(0xFFFFFFFF)
    h ^= h >> np.uint64(12)
    return (h & np.uint64(0xFFFF)).astype(np.float32) / 65535.0


def value_noise(r0: int, r1: int, c0: int, c1: int, period: int, seed: int) -> np.ndarray:
    """Smooth lattice noise on global grid indices (the same value at a vertex in any window), 0..1."""
    rr = np.arange(r0, r1, dtype=np.int64)[:, None] + 1_000_000
    cc = np.arange(c0, c1, dtype=np.int64)[None, :] + 1_000_000
    iy, ix = rr // period, cc // period
    fy = _smooth((rr % period) / period).astype(np.float32)
    fx = _smooth((cc % period) / period).astype(np.float32)
    a, b = _hash(iy, ix, seed), _hash(iy, ix + 1, seed)
    c, d = _hash(iy + 1, ix, seed), _hash(iy + 1, ix + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


# ---- inputs: water and regions ------------------------------------------------------------------------------
class Water:
    """The solved water (the 1.15 contract): one level per cell from `cell_water` (via terrain/cellwater.py, which
    falls back to its fixture while the table is empty), wet where the ground is below its cell's level; and the
    local water level of every cell from `water/solve.nearest_level`, bilinear between cell centres so "height
    above local water" never steps at a cell edge. Beyond the province the sea (0 m) wherever the ground is below
    it."""

    def __init__(self, level: np.ndarray, near: np.ndarray, pad: int):
        self.level, self.near, self.pad = level, near, pad  # (C, C) [row from north, col from west]

    @classmethod
    def load(cls, world, pad: int):
        from tools.argonia_world.terrain import cellwater
        from tools.argonia_world.water import solve
        cw = cellwater.load(world)
        C = cw.level.shape[0]
        x0, y0 = su.PROVINCE_CELL_SW
        if cw.source == "cell_water":
            sw = solve.load(world)
            near = np.array([[sw.nearest_level(x0 + j, y0 + C - 1 - i) for j in range(C)] for i in range(C)])
        else:  # the fixture: the same rule on its own levels
            near = nearest_fill(cw.level)
        return cls(cw.level, near, pad)

    @classmethod
    def sea(cls, pad: int, n: int):
        """Synthetic grids (tests): every cell's water is the sea at 0 m."""
        c = max(n // su.QUADS_PER_CELL, 1)
        return cls(np.zeros((c, c)), np.zeros((c, c)), pad)

    def _cells(self, r0, r1, c0, c1):
        q, C = su.QUADS_PER_CELL, self.level.shape[0]
        pr = np.arange(r0, r1) - self.pad
        pc = np.arange(c0, c1) - self.pad
        inside = ((pr >= 0) & (pr <= C * q))[:, None] & ((pc >= 0) & (pc <= C * q))[None, :]
        return pr, pc, inside, q, C

    def levels(self, r0: int, r1: int, c0: int, c1: int, h: np.ndarray) -> np.ndarray:
        """Water level (m) per vertex, NaN where dry."""
        pr, pc, inside, q, C = self._cells(r0, r1, c0, c1)
        i = np.clip(pr // q, 0, C - 1)[:, None]
        j = np.clip(pc // q, 0, C - 1)[None, :]
        lv = np.where(inside, self.level[i, j], np.nan)
        wet = np.isfinite(lv) & (h < lv)
        out = np.where(wet, lv, np.nan)
        return np.where(~inside & (h < 0.0), 0.0, out).astype(np.float32)

    def local(self, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
        """The nearest water's level per vertex, bilinear between cell centres (0 beyond the province)."""
        pr, pc, inside, q, C = self._cells(r0, r1, c0, c1)
        fy = np.clip((pr - q / 2) / q, 0, C - 1)
        fx = np.clip((pc - q / 2) / q, 0, C - 1)
        i0, j0 = np.floor(fy).astype(int), np.floor(fx).astype(int)
        i1, j1 = np.minimum(i0 + 1, C - 1), np.minimum(j0 + 1, C - 1)
        ty, tx = (fy - i0)[:, None], (fx - j0)[None, :]
        n = self.near
        v = ((n[i0][:, j0] * (1 - tx) + n[i0][:, j1] * tx) * (1 - ty)
             + (n[i1][:, j0] * (1 - tx) + n[i1][:, j1] * tx) * ty)
        return np.where(inside, v, 0.0).astype(np.float32)


def nearest_fill(level: np.ndarray) -> np.ndarray:
    """Each cell's nearest water cell's level (Euclidean in cells), 0 where there is none: solve.nearest_level's
    rule on an array."""
    ii, jj = np.nonzero(np.isfinite(level))
    if not len(ii):
        return np.zeros(level.shape)
    out = np.empty(level.shape)
    vals = level[ii, jj]
    for i in range(level.shape[0]):
        d = (ii[None, :] - i) ** 2 + (jj[None, :] - np.arange(level.shape[1])[:, None]) ** 2
        out[i] = vals[np.argmin(d, axis=1)]
    return out


WARP, WARP_PERIOD = 14.0, 96  # vertices: class borders meander by up to ~28 m over ~170 m
APRON_INHERIT = float("inf")  # the apron carries on the nearest province class (a `border` class line read as a hard edge at the rim, mat3 2026-11-01)
CLASS_BLEND = 12  # the class blend box radius (twice): ~25 vertices, ~45 m


class Regions:
    """The eco class index (into CLASSES) per province cell from `cell_region_run`; the apron is `border`."""

    def __init__(self, grid: np.ndarray, pad: int, n: int):
        self.grid, self.pad, self.n = grid, pad, n  # grid[cy - CY0, cx - CX0]

    @classmethod
    def load(cls, world, pad: int, n: int = su.PROVINCE_SAMPLES - 1):
        span = n // su.QUADS_PER_CELL
        g = np.full((span, span), CLASSES.index("border"), dtype=np.int8)
        eco = {r[0]: r[1] for r in world.query("SELECT id, eco_class_id FROM land_region")}
        x0, y0 = su.PROVINCE_CELL_SW
        for cy, a, b, lr in world.query("SELECT cy, cx0, cx1, land_region_id FROM cell_region_run"):
            e = eco.get(lr)
            if e in STOPS and 0 <= cy - y0 < span:
                g[cy - y0, max(a - x0, 0):min(b - x0 + 1, span)] = CLASSES.index(e)
        return cls(g, pad, n)

    @classmethod
    def uniform(cls, eco: str, pad: int, n: int):
        span = max(n // su.QUADS_PER_CELL, 1)
        return cls(np.full((span, span), CLASSES.index(eco), dtype=np.int8), pad, n)

    def at(self, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
        """The class per vertex. The lookup is domain-warped by position-seeded noise (up to WARP vertices), so a
        class border meanders instead of following cell edges (mat0's block borders, 2026-11-01); the apron takes
        the nearest province cell's class out to APRON_INHERIT vertices, then `border`, along a warped line (mat3's
        straight edge at the rim)."""
        q = su.QUADS_PER_CELL
        wy = (value_noise(r0, r1, c0, c1, WARP_PERIOD, 11) * 0.7 + value_noise(r0, r1, c0, c1, WARP_PERIOD // 3, 12) * 0.3
              - 0.5) * 2 * WARP
        wx = (value_noise(r0, r1, c0, c1, WARP_PERIOD, 13) * 0.7 + value_noise(r0, r1, c0, c1, WARP_PERIOD // 3, 14) * 0.3
              - 0.5) * 2 * WARP
        pr = np.arange(r0, r1)[:, None] - self.pad + wy
        pc = np.arange(c0, c1)[None, :] - self.pad + wx
        cy = np.floor((self.n - pr) / q).astype(np.int64)
        cx = np.floor(pc / q).astype(np.int64)
        span = self.grid.shape[0]
        out_r = np.maximum(np.maximum(-pr, pr - self.n), 0)
        out_c = np.maximum(np.maximum(-pc, pc - self.n), 0)
        near = np.hypot(out_r, out_c) <= APRON_INHERIT
        v = self.grid[np.clip(cy, 0, span - 1), np.clip(cx, 0, span - 1)]
        return np.where(near, v, CLASSES.index("border")).astype(np.int8)


# ---- the rule -----------------------------------------------------------------------------------------------
@dataclass
class Window:
    """The keys and weights of a window of grid rows [r0, r1) and columns [c0, c1)."""
    weights: np.ndarray  # (rows, cols, len(TEXTURES)) float32, summing to 1
    dh: np.ndarray
    slope: np.ndarray
    north: np.ndarray
    wet: np.ndarray


class Material:
    def __init__(self, src, water, regions, roads: bool = True):
        self.src, self.water, self.regions, self.roads = src, water, regions, roads

    @cached_property
    def index(self) -> dict[str, int]:
        return {t.edid: i for i, t in enumerate(TEXTURES)}

    def window(self, r0: int, r1: int, c0: int, c1: int) -> Window:
        size = self.src.size
        a0, a1, b0, b1 = max(r0 - HALO, 0), min(r1 + HALO, size), max(c0 - HALO, 0), min(c1 + HALO, size)
        h = self.src.heights(a0, a1, b0, b1)
        k = self._keys(h, a0, a1, b0, b1)
        w = self._weights(k, a0, a1, b0, b1)
        s = (slice(r0 - a0, r1 - a0), slice(c0 - b0, c1 - b0))
        return Window(w[s], k["dh"][s], k["slope"][s], k["north"][s], k["wet"][s])

    def _keys(self, h, a0, a1, b0, b1) -> dict:
        lev = self.water.levels(a0, a1, b0, b1, h)
        wm = np.isfinite(lev).astype(np.float32)
        # local water: the mean level of the water within ~60 m, else the nearest water cell's (solve.nearest_level)
        lv = np.where(np.isfinite(lev), lev, 0.0).astype(np.float32)
        r = 32
        ws = box(box(wm, r // 2), r // 2)
        far = self.water.local(a0, a1, b0, b1)
        local = np.where(ws > 1e-3, box(box(lv * wm, r // 2), r // 2) / np.maximum(ws, 1e-3), far)
        # no exact per-cell level here: a cell-level step would print the cell edge into dh (mat2 boxes, 2026-11-01)
        dh = (h - local).astype(np.float32)
        wet = np.clip(0.65 * box(box(wm, 4), 4) + 0.35 * box(wm, 12) * 1.6, 0.0, 1.0)
        gy, gx = np.gradient(h, su.PROVINCE_SAMPLE_M)
        slope = np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
        mag = np.maximum(np.hypot(gx, gy), 1e-6)
        north = np.where(np.hypot(gx, gy) > 0.05, -gy / mag, 0.0).astype(np.float32)  # rows run south: +gy rises south
        n1 = value_noise(a0, a1, b0, b1, 48, 1)
        n2 = value_noise(a0, a1, b0, b1, 16, 2)
        noise = (0.65 * n1 + 0.35 * n2).astype(np.float32)
        amp = np.clip(dh / 20.0, 0.0, 1.0) * 14.0  # bands break up with height, never at the water's edge
        band = dh + (noise - 0.5) * 2 * amp
        return {"h": h, "dh": dh, "band": band, "wet": wet, "slope": slope, "north": north, "noise": noise}

    def _weights(self, k, a0, a1, b0, b1) -> np.ndarray:
        n_tex = len(TEXTURES)
        cls = self.regions.at(a0, a1, b0, b1)
        present = [int(c) for c in np.unique(cls)]
        out = np.zeros(cls.shape + (n_tex,), dtype=np.float32)
        for c in present:
            m = box(box((cls == c).astype(np.float32), CLASS_BLEND), CLASS_BLEND)  # the class blend, ~45 m
            if not m.any():
                continue
            wc = np.zeros_like(out)
            for s in STOPS[CLASSES[c]]:
                x = k["band"] if s.dh[0] > 2 else k["dh"]
                f = (ramp(x, *s.dh, SOFT["dh"]) * ramp(k["slope"], *s.slope, SOFT["slope"])
                     * ramp(k["wet"], *s.wet, SOFT["wet"]) * ramp(k["noise"], *s.noise, SOFT["noise"]))
                f = f * s.w * (1.0 + s.north * k["north"])
                wc[..., self.index[s.ltex]] += f.astype(np.float32)
            tot = wc.sum(axis=2, keepdims=True)
            fb = self.index[STOPS[CLASSES[c]][-2].ltex]  # a vertex no stop covers takes the class's land stop
            wc = np.where(tot > 1e-4, wc / np.maximum(tot, 1e-4), 0.0)
            wc[..., fb] += (tot[..., 0] <= 1e-4)
            out += wc * m[..., None]
        if self.roads:
            out = self._road(out, k, a0, b0)
        out = box(box(out, 4), 4)  # the material blend, 8-17 vertices (a 3-box left 1-2 px waterline rings, mat0)
        out = np.where(out < MIN_W, 0.0, out)
        return (out / np.maximum(out.sum(axis=2, keepdims=True), 1e-6)).astype(np.float32)

    def _road(self, w, k, a0, b0):
        from tools.argonia_world.routes import paint as road_paint
        try:
            segs = road_paint.segments()
        except Exception:  # no route data in this checkout (a test fixture): no roads
            return w
        cls = np.zeros(w.shape[:2], dtype=np.int16)
        road_paint.override_classes(cls, a0, b0, segs=segs)
        m = (cls != 0) & (k["dh"] > 0.0)  # a road is never painted under water
        if m.any():
            w[m] = 0.0
            w[m, self.index[ROAD]] = 1.0
        return w


# ---- quadrants: the kept sets and the seam fix ------------------------------------------------------------------
def quadrant_sets(w: np.ndarray, max_alpha: int = MAX_ALPHA):
    """Weights (rows, cols, n) over whole quadrants (rows and cols = 16k + 1, the window's corner on a quadrant
    corner) -> (the restricted weights, keep[qy][qx] lists, base first). A vertex's weights keep only the
    textures every quadrant sharing it keeps, renormalised (the seam fix)."""
    R, C, n = w.shape
    qy, qx = (R - 1) // QS, (C - 1) // QS
    tot = np.zeros((qy, qx, n), dtype=np.float64)
    for i in range(qy):
        for j in range(qx):
            tot[i, j] = w[i * QS:i * QS + QV, j * QS:j * QS + QV].sum(axis=(0, 1))
    # neighbours' totals break ties toward shared textures
    nb = np.zeros_like(tot)
    nb[1:] += tot[:-1]
    nb[:-1] += tot[1:]
    nb[:, 1:] += tot[:, :-1]
    nb[:, :-1] += tot[:, 1:]
    score = tot + 0.15 * nb
    keep = [[None] * qx for _ in range(qy)]
    allowed = np.ones((R, C, n), dtype=bool)
    for i in range(qy):
        for j in range(qx):
            order = [int(t) for t in np.argsort(-score[i, j], kind="stable") if tot[i, j, t] > 0]
            if not order:
                order = [int(np.argmax(score[i, j]))]
            base = int(np.argmax(tot[i, j]))
            ks = [base] + [t for t in order if t != base][:max_alpha]
            keep[i][j] = ks
            m = np.zeros(n, dtype=bool)
            m[ks] = True
            allowed[i * QS:i * QS + QV, j * QS:j * QS + QV] &= m
    wr = np.where(allowed, w, 0.0)
    s = wr.sum(axis=2, keepdims=True)
    lost = s[..., 0] <= 1e-6
    if lost.any():  # every kept-by-all texture had no weight here: the strongest texture all sides keep
        cand = np.where(allowed, w + 1e-3, -1.0)
        best = np.argmax(cand, axis=2)
        rr, cc = np.nonzero(lost)
        wr[rr, cc, :] = 0.0
        wr[rr, cc, best[rr, cc]] = 1.0
        s = wr.sum(axis=2, keepdims=True)
    return (wr / s).astype(np.float64), keep


def quadrant_layers(wq: np.ndarray, keep: list[int]) -> tuple[int, list[tuple[int, np.ndarray]]]:
    """(17, 17, n) restricted weights of one quadrant, [y, x] from its south-west, and its kept textures (base
    first) -> (base, [(texture, opacity bytes (17, 17))] in draw order, weakest first). The engine draws each
    alpha layer over what lies below, so layer i's opacity is w_i / (w_base + w_1 + ... + w_i): composited in
    order every texture shows its weight. Opacity bytes are n / 255 (byte-stable); empty layers are omitted."""
    tot = wq[:, :, keep].sum(axis=(0, 1))
    alpha = [t for _, t in sorted(((-tot[i], t) for i, t in enumerate(keep[1:], 1)), key=lambda p: p[0])]
    cum = wq[:, :, keep[0]].copy()
    layers = []
    for t in reversed(alpha):  # weakest first, strongest drawn last
        cum = cum + wq[:, :, t]
        a = np.where(cum > 0, wq[:, :, t] / np.where(cum > 0, cum, 1), 0.0)
        a8 = np.rint(a * 255).astype(np.uint8)
        if a8.any():
            layers.append((t, a8))
    return keep[0], layers


def composite(base: int, layers: list[tuple[int, np.ndarray]], n: int) -> np.ndarray:
    """What the engine shows: (17, 17, n) weights from a base and alpha layers drawn in order."""
    out = np.zeros((QV, QV, n))
    out[:, :, base] = 1.0
    for i, a in layers:
        f = a.astype(np.float64)[:, :, None] / 255.0
        out *= 1 - f
        out[:, :, i] += f[:, :, 0]
    return out


# ---- vertex colour --------------------------------------------------------------------------------------------
def vclr(win: Window, tint: np.ndarray | None = None) -> np.ndarray:
    """uint8 RGB: shade (steep and north faces darker, by up to 25 %) and wet (darker and a touch greener toward
    water, by up to 22 %), times the old ground tint."""
    shade = 1.0 - 0.18 * np.clip(win.slope / 50.0, 0, 1) - 0.07 * np.clip(win.north, 0, 1)
    wetf = 1.0 - 0.22 * np.clip(win.wet, 0, 1) * (win.dh > -0.5)
    f = (shade * wetf)[..., None] * np.array([1.0, 1.0, 0.96], dtype=np.float32)
    base = np.full(win.dh.shape + (3,), 255.0) if tint is None else tint.astype(np.float32)
    return np.clip(np.rint(base * f), 0, 255).astype(np.uint8)


# ---- the render layer (for terrain/render.py) ---------------------------------------------------------------------
PALETTE = {  # a false colour per texture: water family blues, mud browns, grass greens, rock greys
    "LRiverBottom01": (30, 60, 140), "LCoastOceanFloor01": (20, 30, 90), "LRiverbedEdge01": (90, 150, 200),
    "LRiverMud01": (110, 80, 50), "LFrozenMarshLichen01": (70, 50, 40), "LCoastBeach01": (220, 200, 140),
    "LCoastBeachGrass01": (190, 210, 120), "LFrozenMarshGrass01": (150, 170, 60), "LFieldGrass02": (110, 200, 80),
    "LFallForestDirt01": (150, 100, 60), "LFallForestLeaves01": (200, 120, 40), "LPineForest03": (40, 110, 50),
    "LPineForest02": (20, 140, 110), "LReachMoss01": (100, 160, 40), "LReachMossyRocks01": (120, 130, 110),
    "LReachDirt01": (180, 80, 60), "LRocks01": (200, 200, 200), "LTundraRocks01": (160, 150, 170),
    "LDirtPath01": (240, 60, 200),
}


def layer_rgba(mat: Material, r0: int, r1: int, c0: int, c1: int, shade: bool = True) -> np.ndarray:
    """Grid rows [r0, r1), columns [c0, c1) -> (rows, cols, 4) uint8 RGBA: the false-colour weight map times the
    VCLR."""
    win = mat.window(r0, r1, c0, c1)
    pal = np.array([PALETTE[t.edid] for t in TEXTURES], dtype=np.float32)
    rgb = np.tensordot(win.weights, pal, axes=([2], [0]))
    if shade:
        rgb = rgb * (vclr(win).astype(np.float32) / 255.0)
    out = np.empty(rgb.shape[:2] + (4,), dtype=np.uint8)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255)
    out[..., 3] = 255
    return out


_MAT: list = []


def render_layer(w) -> np.ndarray:
    """terrain/render.py's layer hook: its Window (province rows and columns) -> RGBA over the whole window."""
    if not _MAT:
        from tools.argonia_world import db
        from tools.argonia_world.terrain.grid import Sources
        world = w.world if w.world is not None else db.open()
        src = Sources.load()
        _MAT.append(Material(src, Water.load(world, src.pad), Regions.load(world, src.pad, src.n)))
    mat = _MAT[0]
    (r0, r1), (c0, c1) = w.rows, w.cols
    p = mat.src.pad
    return layer_rgba(mat, r0 + p, r1 + p, c0 + p, c1 + p)
