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
trapezoids with narrow shoulders, then one 3-vertex box: a blend spans 1-5 vertices, as vanilla's painted strokes
(Skyrim.esm audit, skyrim-does-it-this-way.md §4: a 0.02-0.98 run is 1 vertex at p50, 5 at p90). Upland stops read a
band height `dh + noise * amp` (amp grows with height), so mountainsides break into bands and patches (options §8).
Classes blend over ~5 vertices where they change, and weights under 3 % are dropped. The water edge is vanilla's:
bed below -384 u, mud and edge from -384 u to the line, the edge on to +128 u, then land (no mud above the water);
sea shores run the beach to +256 u (§4).

The apron beyond the border polygon is bare, as vanilla's far ground (§9): the `border` class alone, no province
blend, and one base texture per quadrant (no alpha layers).

Quadrants (`quadrant_sets`): each LAND quadrant keeps its base plus up to `MAX_ALPHA` alpha layers by total
weight, ties broken toward the textures its neighbours keep. The seam fix: a vertex's weights are restricted to
the textures kept by every quadrant that shares it (1, 2 or 4) and renormalised, so the two sides of a quadrant
or cell seam composite the same weights and nothing drops out at the seam.

VCLR (`vclr`): white by default; darkened only in a band within 256 u of water (to ~150) and on wet flats (§4:
vanilla's VCLR is p50 255 and its steep ground is not darker). build.py no longer multiplies the old ground tint in.

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
MAX_ALPHA = 6  # base plus six: Skyrim.esm's quadrants run to base + 6 and 6 is the commonest count (audit §4)
HALO = 64  # vertices of context a window reads around itself (the blurs' and the wetness's reach)
MIN_W = 0.03
SHORE_BAND, SHORE_DROP = 3.0, 2.5  # vertices of bed band under the edge (~384 u, audit §4), metres deeper a vertex beyond
FAR_DH = 8.0  # m: dry ground beyond NEAR_FAR of any water reads at least this high, above every water-edge stop (top 6 m)
NEAR_FAR = (40.0, 64.0)  # vertices: the nearest wet vertex's level rules within 40 (~70 m), the cell rule beyond 64
INF = float("inf")
EDGE_REACH = (1.0, 3.0)  # vertices from the nearest wet vertex: the edge band fades out over this reach on dry ground
# (r6: (2, 4) laid 8.3 % of dry ground within 16 v of water over 34 windows, above Skyrim.esm's window p90 6.1 %; q11)


# ---- the texture set ------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Tex:
    edid: str  # the vanilla LTEX we paint (Skyrim.esm), re-pointed at BM&V's file by our TXST
    form_key: str
    bmv: str  # BM&V's diffuse, under textures\ (Black Marsh & Valenwood part 2, TEXTUREPACK\landscape)
    why: str

    @property
    def name(self) -> str:
        return self.bmv.rsplit("\\", 1)[1][:-4]

    @property
    def diffuse(self) -> str:
        """The TXST's diffuse: BM&V's file with its mip chain, derived at install (derive_textures.py, 0014)."""
        return "argonia\\landscape\\" + self.name + ".dds"

    @property
    def normal(self) -> str:
        """The TXST's normal: derived at install from BM&V's diffuse (derive_textures.py), its tilt and specular
        alpha set to Skyrim.esm's own normal of this name (`vanilla_normal`); BM&V ships none."""
        return "argonia\\landscape\\" + self.name + "_n.dds"

    @property
    def vanilla_normal(self) -> str:
        """Skyrim.esm's landscape normal for this diffuse's name (`landscape\\<name>_n.dds`, the player's BSA): the
        derived normal's bar (vanilla alpha p50 of means ~20/255; TS's DXT1 copies carry 255, r4)."""
        return "landscape\\" + self.name + "_n.dds"


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
ROAD_BLEND_M = 4.0  # the road paint blends into the land over this each side (routes/shape.py)


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
    seed: int = 0  # 0: the shared noise; else the stop's own field (rock patches never follow the litter patches)


SOFT = {"dh": 0.25, "slope": 2.0, "wet": 0.05, "noise": 0.04}  # narrow shoulders: blends of 1-5 vertices (audit §4)
# the water edge, as Skyrim.esm paints it (skyrim-does-it-this-way.md §4): bed below -384 u; mud and edge from -384 u
# to the line; the edge on to +128 u (one vertex above); land from there. No mud band above the water.
BED_M = -su.units_to_metres(384)
EDGE_TOP_M = su.units_to_metres(128)  # 1.83 m
BEACH_TOP_M = su.units_to_metres(256)  # 3.66 m: sea shores run the beach to +256 u (§4)
BED = Stop("LRiverBottom01", dh=(-INF, BED_M), why="audit §4: LRiverBottom01 below -384 u")
EDGE = Stop("LRiverbedEdge01", dh=(BED_M, EDGE_TOP_M), slope=(-INF, 30), w=1.3,
            why="audit §4: LRiverbedEdge01 from -384 u to +128 u")
MUD = Stop("LRiverMud01", dh=(BED_M, 0.0), noise=(-INF, 0.5), w=1.2,
           why="audit §4: LRiverMud01 under water only; shoreline A2/A6/A8: sheltered water leaves mud")
L = EDGE_TOP_M  # land begins one vertex above the line
S = BEACH_TOP_M  # on the sea, above the beach
LIFT_DH = S + 0.3  # m: dry ground beyond EDGE_REACH reads at least this high (above every edge and beach band)
# Rock is a patch texture on steep ground, never the whole of it: Skyrim.esm's dominant texture on slopes over 34°
# is rock on 24-25 % of vertices (9 % under 10°, 20 % at 20-30°), the rest the area's ground and snow; a steep
# cell carries 3 distinct dominant textures at p50, 6 at p90 (measured 2026-11-01, 9,500 LAND; options §8). Without
# snow our rock share on >34° aims at ~35-45 %: patches by the stop's own noise, a little more as it steepens.
ROCK = Stop("LReachMossyRocks01", slope=(28, INF), noise=(0.5, INF), w=1.4, north=0.3, seed=7,
            why="Skyrim.esm: rock on ~25 % of slopes over 34°, in patches (options §8)")
CRAG = Stop("LReachMossyRocks01", slope=(48, INF), noise=(0.38, INF), w=1.4, north=0.3, seed=7,
            why="Skyrim.esm: the steepest faces carry rock a little more often")

STOPS: dict[str, tuple[Stop, ...]] = {
    "coastal-lagoon": (
        Stop("LCoastOceanFloor01", dh=(-INF, -2.5), why="shoreline A10: the shelf"),
        Stop("LCoastBeach01", dh=(-2.5, S), wet=(-INF, 0.75), why="shoreline A1: wave-sorted sand"),
        MUD,
        Stop("LFrozenMarshGrass01", dh=(S, 6), noise=(0.25, INF), why="shoreline A6: marsh above the mud"),
        Stop("LFallForestDirt01", dh=(4, INF), why="shoreline A3: mangrove-forest floor inland"),
        Stop("LCoastBeachGrass01", dh=(S, 6), noise=(0.55, INF), seed=31, w=1.3, why="shoreline A1: grassed backshore patches"),
        ROCK),
    "tidal-delta": (
        Stop("LCoastOceanFloor01", dh=(-INF, -2.5), why="shoreline A4: delta front"),
        Stop("LCoastBeach01", dh=(-2.5, S), noise=(0.45, INF), why="shoreline A4: sand bars"),
        MUD, EDGE,
        Stop("LFrozenMarshGrass01", dh=(S, 5), why="shoreline A4: marsh on the flanks"),
        Stop("LCoastBeachGrass01", dh=(S, INF), why="shoreline A1: grassed bar tops"),
    ),
    "flooded-forest": (
        BED, MUD, EDGE,
        # five land stops, each on its own noise, so no one covers more than about half a window (audit §4: vanilla
        # forest floors carry 4-6 textures; r 2026-11-01: 0_0 read as one dark-green swathe)
        Stop("LPineForest03", dh=(L, INF), why="BM&V's swamp forest floor (its most painted ground)"),
        Stop("LFallForestLeaves01", dh=(L, INF), noise=(0.48, INF), seed=21, w=1.3, why="shoreline A8: wet litter"),
        Stop("LFallForestDirt01", dh=(1, INF), noise=(0.56, INF), seed=22, w=1.35, why="rooty patches (BM&V roots-in-mudbank)"),
        Stop("LFrozenMarshLichen01", dh=(L, 3), noise=(0.5, INF), seed=23, w=1.4, why="shoreline A8: muck in the hollows"),
        Stop("LReachMoss01", dh=(1, INF), noise=(0.6, INF), seed=24, w=1.45, why="moss on raised roots and hummocks"),
    ),
    "interior-swamp": (
        BED, MUD,
        Stop("LFrozenMarshLichen01", dh=(L, 2.5 + L), wet=(0.15, INF), why="shoreline A8: muck margin"),
        Stop("LFrozenMarshGrass01", dh=(L, INF), noise=(-INF, 0.6), why="shoreline A9: reed and marsh grass"),
        Stop("LFallForestDirt01", dh=(2.5, INF), noise=(0.5, INF), why="shoreline A8: swamp-forest floor"),
        Stop("LReachMoss01", slope=(18, INF), why="moss on the few banks"),
        Stop("LFallForestLeaves01", dh=(L, INF), noise=(0.55, INF), seed=33, w=1.3, why="shoreline A8: litter under swamp trees"),
        Stop("LReachMoss01", dh=(L, INF), noise=(0.62, INF), seed=34, w=1.4, why="moss on hummocks (shoreline A9)"),
    ),
    "deep-sink-basin": (
        BED, MUD, EDGE,
        Stop("LFrozenMarshLichen01", dh=(L, 4), why="shoreline A8: muck round the sink"),
        Stop("LFallForestLeaves01", dh=(2.5, INF), why="litter on the basin rim"),
        ROCK, CRAG),
    "deep-river-corridor": (
        BED, EDGE, MUD,
        Stop("LFallForestLeaves01", dh=(L, INF), noise=(-INF, 0.5), why="gallery forest litter"),
        Stop("LFallForestDirt01", dh=(L, INF), noise=(0.5, INF), why="rooty banks"),
        ROCK, CRAG),
    "rootland": (
        BED, EDGE,
        Stop("LPineForest03", dh=(L, INF), w=1.1, why="root-bound forest floor"),
        Stop("LFallForestDirt01", dh=(L, INF), noise=(0.55, INF), why="roots in mud bank"),
        Stop("LReachMoss01", slope=(14, INF), north=0.5, why="moss on rises"),
        Stop("LFallForestLeaves01", dh=(L, INF), noise=(0.55, INF), seed=40, w=1.3, why="litter between the roots"),
        Stop("LFrozenMarshLichen01", dh=(L, 3), noise=(0.55, INF), seed=41, w=1.4, why="shoreline A8: muck in root hollows"),
        ROCK, CRAG),
    "seasonal-floodplain": (
        BED, MUD, EDGE,
        Stop("LFieldGrass02", dh=(L, INF), why="BM&V's mossy grass on the flood flats"),
        Stop("LFrozenMarshGrass01", dh=(L, 3 + L), wet=(0.2, INF), why="wet marsh grass near the channel"),
        Stop("LFallForestDirt01", dh=(3, INF), noise=(0.6, INF), why="levee floor"),
        Stop("LFrozenMarshGrass01", dh=(L, INF), noise=(0.55, INF), seed=35, w=1.3, why="marsh grass in the flood swales (shoreline A9)"),
        Stop("LReachMoss01", dh=(L, INF), noise=(0.62, INF), seed=36, w=1.4, why="moss on the flats' hummocks"),
    ),
    "northern-transition": (
        BED, EDGE,
        Stop("LReachDirt01", dh=(L, INF), noise=(0.5, INF), why="red earth of the drier north (Dunmer border)"),
        Stop("LFieldGrass02", dh=(L, 120), noise=(-INF, 0.6), why="grass of the transition"),
        Stop("LPineForest02", dh=(L, INF), noise=(0.55, INF), seed=37, w=1.3, why="drier upland forest floor of the north"),
        Stop("LTundraRocks01", slope=(24, INF), noise=(0.6, INF), seed=8, w=1.2, why="scree patches below the ranges"),
        Stop("LRocks01", slope=(34, INF), noise=(0.58, INF), seed=7, w=1.4, why="bare rock of the Velothi foothills, in patches"),
    ),
    "western-frontier": (
        BED, EDGE,
        Stop("LPineForest02", dh=(L, 260), slope=(-INF, 40), why="upland forest (Kinabalu cloud forest, mountain synthesis)"),
        Stop("LReachMoss01", dh=(L, INF), slope=(14, INF), north=0.6, noise=(0.35, INF),
             why="moss bands on the flanks (options §8)"),
        Stop("LFallForestLeaves01", dh=(L, INF), noise=(0.55, INF), seed=48, w=1.3, why="cloud-forest litter (mountain synthesis)"),
        Stop("LFallForestDirt01", dh=(L, INF), noise=(0.6, INF), seed=49, w=1.35, why="rooty upland floor"),
        ROCK,
        Stop("LRocks01", dh=(220, INF), slope=(26, INF), noise=(0.5, INF), seed=7, w=1.2,
             why="bare rock of the summits (border ranges), in patches"),
    ),
    "karst-cavern-belt": (
        BED, EDGE,
        Stop("LFallForestDirt01", dh=(L, INF), why="forest floor over limestone"),
        Stop("LReachMoss01", slope=(12, INF), north=0.5, why="moss on karst"),
        ROCK,
        Stop("LTundraRocks01", slope=(26, INF), noise=(0.62, INF), seed=8, why="broken limestone"),
    ),
    "border": (
        Stop("LCoastOceanFloor01", dh=(-INF, 0), why="the apron's sea (bare far ground, audit §9)"),
        Stop("LPineForest03", dh=(0, 200), why="the apron's forest"),
        Stop("LRocks01", slope=(34, INF), w=1.4, why="the apron's steep ground"),
        Stop("LRocks01", dh=(200, INF), w=1.2, why="the apron's ranges"),
    ),
}
CLASSES = tuple(STOPS)


def _fallback(stops) -> str:
    """The class's plain land stop (open above, any slope, no patch noise): what a vertex no stop covers takes."""
    land = [s for s in stops if s.dh[1] == INF and s.dh[0] >= 0 and s.slope[0] == -INF and not s.seed]
    plain = [s for s in land if s.noise == (-INF, INF)]
    return (plain or land or [s for s in stops if s.dh[1] == INF] or list(stops))[0].ltex


FALLBACK = {c: _fallback(st) for c, st in STOPS.items()}


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
    # the hash only on the lattice the window spans (one value per lattice node, then gathered): the same hash of
    # the same nodes as hashing every vertex, so the bytes do not move, at period^-2 of the hashing
    y0, x0 = int(iy.min()), int(ix.min())
    g = _hash(np.arange(y0, int(iy.max()) + 2)[:, None], np.arange(x0, int(ix.max()) + 2)[None, :], seed)
    ly, lx = (iy - y0)[:, 0], ix - x0
    # x first on each lattice row, then rows gathered: per vertex the same float32 operations in the same order
    gx = g[:, lx[0]] * (1 - fx) + g[:, lx[0] + 1] * fx
    return gx[ly] * (1 - fy) + gx[ly + 1] * fy


# ---- inputs: water and regions ------------------------------------------------------------------------------
class Water:
    """The solved water (the 1.15 contract): one level per cell from `cell_water` (via terrain/cellwater.py, which
    falls back to its fixture while the table is empty), wet where the ground is below its cell's level; and the
    local water level of every cell from `water/solve.nearest_level`, bilinear between cell centres so "height
    above local water" never steps at a cell edge. Beyond the province the sea (0 m) wherever the ground is below
    it."""

    def __init__(self, level: np.ndarray, near: np.ndarray, pad: int, rain: np.ndarray | None = None):
        self.level, self.near, self.pad = level, near, pad  # (C, C) [row from north, col from west]
        self.rain = np.full(level.shape, RAIN_BASE) if rain is None else rain  # the climatology's R per cell

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
        return cls(cw.level, near, pad, rain_field(cw))

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

    def local(self, r0: int, r1: int, c0: int, c1: int, field: np.ndarray | None = None, beyond: float = 0.0) -> np.ndarray:
        """The nearest water's level (or another per-cell field) per vertex, bilinear between cell centres
        (`beyond` outside the province)."""
        pr, pc, inside, q, C = self._cells(r0, r1, c0, c1)
        fy = np.clip((pr - q / 2) / q, 0, C - 1)
        fx = np.clip((pc - q / 2) / q, 0, C - 1)
        i0, j0 = np.floor(fy).astype(int), np.floor(fx).astype(int)
        i1, j1 = np.minimum(i0 + 1, C - 1), np.minimum(j0 + 1, C - 1)
        ty, tx = (fy - i0)[:, None], (fx - j0)[None, :]
        n = self.near if field is None else field
        v = ((n[i0][:, j0] * (1 - tx) + n[i0][:, j1] * tx) * (1 - ty)
             + (n[i1][:, j0] * (1 - tx) + n[i1][:, j1] * tx) * ty)
        return np.where(inside, v, beyond).astype(np.float32)


RAIN_BASE, RAIN_WINDWARD, RAIN_COAST = 0.5, 0.3, 0.2  # climatology §3 R
# its 40 km coastal decay is for the real province; our 7.4 km province keeps the same share of the span (~1/4)
RAIN_COAST_SPAN = 0.25
RAIN_WET = 0.25  # the wetness R = 1 adds to bone-dry ground
WIND_FROM = (-1.0, 1.0)  # (north, east) unit-ish: moist air comes off the Padomaic, south-east (climatology §4)


def rain_field(cw) -> np.ndarray:
    """The climatology's rain amplitude per cell (docs/design/research/world-terrain/black-marsh-climatology.md
    §3): R = 0.5 + 0.3 windward + 0.2 exp(-dCoast / 40 km). dCoast from the solve's sea cells; windward where the
    smoothed cell-mean ground rises into the south-east wind, peaking on mid-slopes (§2 orographic maximum)."""
    from tools.argonia_world.terrain.grid import generated_ground
    sea = (cw.wtype == 0) & np.isfinite(cw.level)
    _, d = nearest_wet(np.where(sea, 0.0, np.nan))
    coast = np.exp(-np.where(np.isfinite(d), d, 1e6) / (RAIN_COAST_SPAN * cw.level.shape[0]))
    wind = np.zeros(cw.level.shape)
    g = generated_ground()
    if g.exists():
        q, C = su.QUADS_PER_CELL, cw.level.shape[0]
        h = np.asarray(np.load(g, mmap_mode="r")[q // 2::q, q // 2::q][:C, :C], np.float64)
        h = box(box(h.astype(np.float32), 3), 3)  # ~400 m: the massif, not the bank
        gy, gx = np.gradient(h, su.CELL_METRES)  # rows run south
        rise = -(gy * -WIND_FROM[0] + gx * WIND_FROM[1]) / np.hypot(*WIND_FROM)  # rise along the wind's travel
        mid = np.exp(-(((h - 300.0) / 250.0) ** 2))  # the mid-slope maximum (§2)
        wind = np.clip(rise / 0.05, 0.0, 1.0) * (0.4 + 0.6 * mid)
    return RAIN_BASE + RAIN_WINDWARD * wind + RAIN_COAST * coast


def nearest_wet(lev: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per vertex the level of the nearest finite vertex of `lev` and the distance to it in vertices (jump
    flooding, vectorised; NaN and inf where the window has none)."""
    R, Cn = lev.shape
    sy = np.where(np.isfinite(lev), np.arange(R)[:, None], -1).astype(np.int32)
    sx = np.where(np.isfinite(lev), np.arange(Cn)[None, :], -1).astype(np.int32)
    yy, xx = np.mgrid[0:R, 0:Cn].astype(np.int32)
    big = np.iinfo(np.int32).max
    def dist(ay, ax):
        return np.where(ay >= 0, (ay - yy) ** 2 + (ax - xx) ** 2, big)
    bd = dist(sy, sx)
    if (sy >= 0).any():
        k = 1 << int(np.ceil(np.log2(max(R, Cn))))
        while k >= 1:
            for dy in (-k, 0, k):
                for dx in (-k, 0, k):
                    if dy == dx == 0 or abs(dy) >= R or abs(dx) >= Cn:
                        continue
                    ys, yd = slice(max(dy, 0), R + min(dy, 0)), slice(max(-dy, 0), R + min(-dy, 0))
                    xs, xd = slice(max(dx, 0), Cn + min(dx, 0)), slice(max(-dx, 0), Cn + min(-dx, 0))
                    # only the overlap can improve: candidate seeds from the shifted window, compared in place
                    cy, cx = sy[ys, xs].copy(), sx[ys, xs].copy()
                    dd = np.where(cy >= 0, (cy - yy[yd, xd]) ** 2 + (cx - xx[yd, xd]) ** 2, big)
                    better = dd < bd[yd, xd]
                    if better.any():
                        sy[yd, xd] = np.where(better, cy, sy[yd, xd])
                        sx[yd, xd] = np.where(better, cx, sx[yd, xd])
                        bd[yd, xd] = np.where(better, dd, bd[yd, xd])
            k //= 2
    has = sy >= 0
    near = np.where(has, lev[np.maximum(sy, 0), np.maximum(sx, 0)], np.nan)
    d = np.where(has, np.sqrt(bd.astype(np.float64)), np.inf)
    return near.astype(np.float32), d.astype(np.float32)


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


WARP, WARP_PERIOD = 30.0, 160  # vertices: class borders meander by up to ~55 m over ~290 m (r1: ±14 left cell-straight edges)
APRON_INHERIT = 0.0  # the apron is `border` alone, bare beyond the border polygon (audit §9); no province class runs into it
TIE, TIE_PERIOD = 0.5, 14  # vertices: tied stops split into patches of ~25 m (r1 2026-11-01: 45 m read as cartoon blobs)
SLOPE_R = 8  # box radius (twice) of the ground the slope keys read: one source-sample span (16 vertices)
CLASS_BLEND = 1  # the class blend box radius (twice): ~5 vertices, only where classes change (audit §4)


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
    dwater: np.ndarray | None = None  # vertices to the nearest wet vertex (0 in water)
    apron: np.ndarray | None = None  # bool: beyond the border polygon
    dshore: np.ndarray | None = None  # vertices to the nearest dry vertex (0 on dry ground)


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
        return Window(w[s], k["dh"][s], k["slope"][s], k["north"][s], k["wet"][s], k["dwater"][s],
                      self.apron(r0, r1, c0, c1), k["dshore"][s])

    def apron(self, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
        """Vertices beyond the border polygon (the province square): the bare far ground (audit §9)."""
        p, n = self.regions.pad, self.regions.n
        r = np.arange(r0, r1)[:, None] - p
        c = np.arange(c0, c1)[None, :] - p
        return (r < 0) | (r > n) | (c < 0) | (c > n)

    def _keys(self, h, a0, a1, b0, b1) -> dict:
        lev = self.water.levels(a0, a1, b0, b1, h)
        wm = np.isfinite(lev).astype(np.float32)
        # local water: the level of the nearest wet vertex (a per-vertex nearest, smoothed over ~30 m so two waters'
        # levels meet in a slope, not a crease), easing into the nearest water cell's (solve.nearest_level) beyond
        # NEAR_FAR vertices. A box mean switched to the cell rule at a fixed reach (a ring) and the cell rule alone
        # is bilinear between cell centres (a lattice): the thin outlines of 2026-11-01.
        far = self.water.local(a0, a1, b0, b1)
        near, d = nearest_wet(lev)
        t = np.clip((d - NEAR_FAR[0]) / (NEAR_FAR[1] - NEAR_FAR[0]), 0.0, 1.0)
        local = box(box(np.where(np.isfinite(near), near * (1 - t) + far * t, far), 8), 8)
        dh = (h - local).astype(np.float32)
        # dry ground is never below its water: a dry hollow under a nearby level read as a riverbed (-38_25)
        dh = np.where(np.isfinite(lev), dh, np.maximum(dh, 0.0)).astype(np.float32)
        # dry ground with no water in reach is land, not bank: its height above the cell-rule level (a water far off,
        # read through the raster) never lands in the bed/edge/mud bands (0_0_1_1: bed texture at 35-39 m, no level).
        # The band height keeps the true height above that level for the upland stops.
        dh_up = dh
        dh = np.where(np.isfinite(lev), dh, np.maximum(dh, FAR_DH * t)).astype(np.float32)
        # the bed band: mud and the edge texture lie only under the edge, within SHORE_BAND vertices of dry ground;
        # farther out the bed reads deeper (SHORE_DROP m a vertex), so an open shallow bed takes the bed texture,
        # never mud blobs (r1, 2026-11-01: mud on open water beds)
        wetv = np.isfinite(lev)
        dshore = np.where(wetv, INF, 0.0).astype(np.float32)
        if wetv.any() and not wetv.all():
            _, dshore = nearest_wet(np.where(wetv, np.nan, 0.0))
            dshore = np.where(wetv, dshore, 0.0).astype(np.float32)
            dh = np.where(wetv, dh - np.maximum(dshore - SHORE_BAND, 0.0) * SHORE_DROP, dh).astype(np.float32)
        # the edge and beach are bands at the line, not every flat a metre above it: dry ground beyond EDGE_REACH
        # vertices of water reads at least LIFT_DH, above the edge (+128 u) and the beach (+256 u), so it takes the
        # class's land stops (r4: LRiverbedEdge01 held 34 % of dry ground, half of it > 16 vertices from water).
        # Skyrim.esm's banks rise, so its height band is a one-vertex strip (audit §4); ours are flat, so reach rules.
        lift = np.clip((d - EDGE_REACH[0]) / (EDGE_REACH[1] - EDGE_REACH[0]), 0.0, 1.0)
        dh = np.where(wetv, dh, np.maximum(dh, LIFT_DH * lift)).astype(np.float32)
        wet = np.clip(0.65 * box(box(wm, 4), 4) + 0.35 * box(wm, 12) * 1.6, 0.0, 1.0)
        # rainier ground reads wetter: the climatology's R (0.5 dry pole .. 1.0 windward coast) lifts dry ground
        rain = self.water.local(a0, a1, b0, b1, self.water.rain, RAIN_BASE + RAIN_COAST)
        wet = (wet + (1.0 - wet) * RAIN_WET * np.clip((rain - RAIN_BASE) / (1.0 - RAIN_BASE), 0.0, 1.0)).astype(np.float32)
        # slope, aspect and the band read the ground smoothed over a 16-vertex tent: the source heights are
        # piecewise linear between samples 16 vertices apart, so the raw slope steps along straight lines every
        # half cell and slope-gated stops switched there (the cell-aligned seams on -38_25, 2026-11-01)
        hs = box(box(h, SLOPE_R), SLOPE_R)
        gy, gx = np.gradient(hs, su.PROVINCE_SAMPLE_M)
        slope = np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)
        mag = np.maximum(np.hypot(gx, gy), 1e-6)
        north = np.where(np.hypot(gx, gy) > 0.05, -gy / mag, 0.0).astype(np.float32)  # rows run south: +gy rises south
        n1 = value_noise(a0, a1, b0, b1, 28, 1)
        n2 = value_noise(a0, a1, b0, b1, 9, 2)
        noise = (0.55 * n1 + 0.45 * n2).astype(np.float32)
        amp = np.clip(dh_up / 20.0, 0.0, 1.0) * 14.0  # bands break up with height, never at the water's edge
        band = dh_up + (hs - h) + (noise - 0.5) * 2 * amp
        return {"h": h, "dh": dh, "band": band, "wet": wet, "slope": slope, "north": north, "noise": noise,
                "dwater": d.astype(np.float32), "dshore": dshore}

    def _weights(self, k, a0, a1, b0, b1) -> np.ndarray:
        n_tex = len(TEXTURES)
        cls = self.regions.at(a0, a1, b0, b1)
        apron = self.apron(a0, a1, b0, b1)
        present = [int(c) for c in np.unique(cls)]
        out = np.zeros(cls.shape + (n_tex,), dtype=np.float32)
        ties: dict[int, np.ndarray] = {}
        for c in present:
            raw = (cls == c).astype(np.float32)
            m = np.where(apron, raw, box(box(raw, CLASS_BLEND), CLASS_BLEND))  # the class blend; none in the apron
            if not m.any():
                continue
            # the rule is per vertex: work only over the box where the class has weight (outside it m is 0 and the
            # class adds nothing), the same values in the same order as over the whole window
            ry, rx = np.nonzero(m.any(axis=1))[0], np.nonzero(m.any(axis=0))[0]
            y0, y1, x0, x1 = int(ry[0]), int(ry[-1]) + 1, int(rx[0]), int(rx[-1]) + 1
            sl = (slice(y0, y1), slice(x0, x1))
            ks = {n: k[n][sl] for n in ("band", "dh", "slope", "wet", "noise", "north")}
            wc = np.zeros((y1 - y0, x1 - x0, n_tex), dtype=np.float32)
            for s in STOPS[CLASSES[c]]:
                x = ks["band"] if s.dh[0] > 5 else ks["dh"]
                nz = ks["noise"] if not s.seed else self._noise(k, s.seed, a0, a1, b0, b1)[sl]
                f = (ramp(x, *s.dh, SOFT["dh"]) * ramp(ks["slope"], *s.slope, SOFT["slope"])
                     * ramp(ks["wet"], *s.wet, SOFT["wet"]) * ramp(nz, *s.noise, SOFT["noise"]))
                f = f * s.w * (1.0 + s.north * ks["north"])
                wc[..., self.index[s.ltex]] += f.astype(np.float32)
            # one texture rules each vertex, as a painted stroke (audit §4: no sustained 30/70 mixes); where stops
            # tie, a per-texture noise breaks the tie in patches, never in a straight line
            tot = wc.sum(axis=2)
            fb = self.index[FALLBACK[CLASSES[c]]]  # a vertex no stop covers takes the class's land stop
            for t in {self.index[s.ltex] for s in STOPS[CLASSES[c]]}:
                if t not in ties:
                    ties[t] = self._tie(t, a0, a1, b0, b1)
                wc[..., t] *= 1.0 + TIE * (ties[t][sl] - 0.5)
            win = np.where(tot > 1e-4, np.argmax(wc, axis=2), fb)
            # the one-hot stroke added at its texture alone (adding the other textures' zeros moves nothing)
            o = out[sl]
            yy, xx = np.indices(win.shape)
            o[yy, xx, win] += m[sl]
        if self.roads:
            out = self._road(out, k, a0, b0)
        if getattr(self.src, "patches", None) is not None:
            self.src.patches.paint(out, a0, b0, self.index)  # a pad's own ground (patches.py)
        # the material blend: a 2x2 mean over the one-hot strokes, so a texture's edge is one part-weighted vertex, two
        # where it runs diagonally (audit §4: a 0.02-0.98 run is 1 vertex at p50, 5 at p90; ours ran 6-17)
        out = np.pad(out, ((0, 1), (0, 1), (0, 0)), mode="edge")
        out = 0.25 * (out[:-1, :-1] + out[1:, :-1] + out[:-1, 1:] + out[1:, 1:])
        out = np.where(out < MIN_W, 0.0, out)
        return (out / np.maximum(out.sum(axis=2, keepdims=True), 1e-6)).astype(np.float32)

    @staticmethod
    def _noise(k: dict, seed: int, a0, a1, b0, b1) -> np.ndarray:
        """A stop's own two-octave noise (cached in the window's keys)."""
        key = f"noise{seed}"
        if key not in k:
            k[key] = (0.65 * value_noise(a0, a1, b0, b1, 22, 300 + seed)
                      + 0.35 * value_noise(a0, a1, b0, b1, 8, 400 + seed)).astype(np.float32)
        return k[key]

    def _tie(self, t: int, a0, a1, b0, b1) -> np.ndarray:
        return value_noise(a0, a1, b0, b1, TIE_PERIOD, 100 + t) * 0.7 + value_noise(a0, a1, b0, b1, TIE_PERIOD // 4, 200 + t) * 0.3

    def _road(self, w, k, a0, b0):
        from tools.argonia_world.routes import paint as road_paint
        try:
            segs = road_paint.segments()
        except Exception:  # no route data in this checkout (a test fixture): no roads
            return w
        # Skyrim.esm's road paint (routes/shape.py, the Whiterun-Riverwood road): the dirt whole across the flat
        # width, then blending into the land's own stroke over ROAD_BLEND_M each side (0.70 dirt at the centre, 0.62
        # at 5 m, 0.53 at 8 m); the 2x2 mean after this softens the last vertex, as everywhere
        a = np.zeros(w.shape[:2])
        blend = ROAD_BLEND_M / su.PROVINCE_SAMPLE_M
        for _cls, half, seg in segs:
            d = road_paint.distance(seg, half + blend, a0, b0, a.shape)
            np.maximum(a, np.clip(1.0 - (d - half) / blend, 0.0, 1.0), out=a)
        a = np.where(k["dh"] > 0.0, a, 0.0)  # a road is never painted under water
        m = a > 0
        if m.any():
            w[m] *= (1.0 - a[m])[:, None]
            w[m, self.index[ROAD]] += a[m]
        return w


# ---- quadrants: the kept sets and the seam fix ------------------------------------------------------------------
def quadrant_sets(w: np.ndarray, max_alpha: int = MAX_ALPHA, bare: np.ndarray | None = None):
    """Weights (rows, cols, n) over whole quadrants (rows and cols = 16k + 1, the window's corner on a quadrant
    corner) -> (the restricted weights, keep[qy][qx] lists, base first). A vertex's weights keep only the
    textures every quadrant sharing it keeps, renormalised (the seam fix). A quadrant whose centre is `bare` (the
    apron) keeps its base alone: vanilla's far ground has no alpha layers (audit §9)."""
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
    is_bare = [[bare is not None and bool(bare[i * QS + QS // 2, j * QS + QS // 2]) for j in range(qx)] for i in range(qy)]
    for i in range(qy):
        for j in range(qx):
            order = [int(t) for t in np.argsort(-score[i, j], kind="stable") if tot[i, j, t] > 0]
            if not order:
                order = [int(np.argmax(score[i, j]))]
            base = int(np.argmax(tot[i, j]))
            if is_bare[i][j]:
                ks = [base]
            else:  # a bare neighbour's base comes first, so the seam they share composites the same
                must = list(dict.fromkeys(int(np.argmax(tot[a, b])) for a in range(max(i - 1, 0), min(i + 2, qy))
                                          for b in range(max(j - 1, 0), min(j + 2, qx)) if is_bare[a][b]))
                rest = [t for t in must if t != base] + [t for t in order if t != base and t not in must]
                ks = [base] + rest[:max_alpha]
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


def blend_runs(w: np.ndarray, lo: float = 0.02, hi: float = 0.98) -> np.ndarray:
    """(rows, cols, n) weights -> the length of every run of vertices strictly between lo and hi along rows and
    columns, per texture: the audit's blend width (skyrim-does-it-this-way.md §4: p50 1, p90 5). Runs that touch
    the array's edge are left out (their length is unknown)."""
    out = []
    mid = (w > lo) & (w < hi)
    for m in (mid, np.swapaxes(mid, 0, 1)):
        x = np.moveaxis(m, 2, 1).reshape(-1, m.shape[1]).astype(np.int8)
        p = np.pad(x, ((0, 0), (1, 1)))
        d = np.diff(p, axis=1)
        r, st = np.nonzero(d == 1)
        _, en = np.nonzero(d == -1)
        ok = (st > 0) & (en < x.shape[1])
        out.append((en - st)[ok])
    return np.concatenate(out) if out else np.zeros(0, int)


# ---- vertex colour --------------------------------------------------------------------------------------------
# the band falls from the line over 6 vertices either side and wet flats take 0.2: the six sample windows read
# p10 179, p50 255, 14.5 % under 200 and `terrain check`'s built sample 203.5 / 255 / 9.3 %, against Skyrim.esm's
# 185 / 255 / 13.9 % (audit §4; fitted 2026-11-01: 2 vertices read 221 / 7.3 % on the windows, darkening the whole
# bed read 147 / 20.7 %)
WATER_BAND_V = 6.0
WATER_DARK = 0.42  # to ~150/255 at the line (audit §4: the darkest band, within 256 u of water, p10 149)
FLAT_DARK = 0.2  # wet flats a little darker


def vclr(win: Window, tint: np.ndarray | None = None) -> np.ndarray:
    """uint8 RGB, white by default (audit §4: p50 255, 13.9 % under 200; steep ground is not darker, so no slope or
    aspect term): darker within 256 u of water, falling monotonically from the line (no ring, w4/w5 2026-11-01),
    and a little on wet flats; times the old ground tint, which the apron does not take (§9)."""
    d = win.dwater if win.dwater is not None else np.where(win.wet >= 0.99, 0.0, INF)
    if win.dshore is not None:  # the band straddles the waterline: the open bed is not darkened (vanilla p10 185)
        d = d + np.maximum(win.dshore - 1.0, 0.0)
    band = np.clip(1.0 - d / (WATER_BAND_V + 1.0), 0.0, 1.0)
    flat = np.clip((win.wet - 0.6) / 0.4, 0, 1) * (1.0 - np.clip((win.slope - 3.0) / 5.0, 0, 1))
    g = np.minimum(1.0 - WATER_DARK * band, 1.0 - FLAT_DARK * flat)[..., None]
    f = g * (1.0 - (1.0 - g) * np.array([0.0, 0.0, 0.1], dtype=np.float32))  # a touch cooler where darkened only
    base = np.full(win.dh.shape + (3,), 255.0) if tint is None else tint.astype(np.float32)
    if win.apron is not None and tint is not None:
        base = np.where(win.apron[..., None], 255.0, base)
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
    rgb = np.tensordot(built_weights(mat, r0, r1, c0, c1), pal, axes=([2], [0]))
    if shade:
        rgb = rgb * (vclr(win).astype(np.float32) / 255.0)
    out = np.empty(rgb.shape[:2] + (4,), dtype=np.uint8)
    out[..., :3] = np.clip(np.rint(rgb), 0, 255)
    out[..., 3] = 255
    return out


def built_weights(mat: Material, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
    """The weights the build writes over rows [r0, r1), columns [c0, c1): the window widened to whole quadrants (a
    quadrant corner sits where (index - pad) % 16 == 0), each quadrant's kept set and the seam fix applied
    (quadrant_sets), the apron's quadrants one base each (audit §9), then cut back. The render draws these, not the
    raw per-vertex weights (the apron on -38_25, 2026-11-01)."""
    p, size = mat.regions.pad, mat.src.size
    a0 = r0 - (r0 - p) % QS
    b0 = c0 - (c0 - p) % QS
    a1 = r1 - 1 + (-(r1 - 1 - p)) % QS + 1
    b1 = c1 - 1 + (-(c1 - 1 - p)) % QS + 1
    g0, g1, h0, h1 = max(a0, 0), min(a1, size), max(b0, 0), min(b1, size)
    padw = ((g0 - a0, a1 - g1), (h0 - b0, b1 - h1))
    w = np.pad(mat.window(g0, g1, h0, h1).weights, padw + ((0, 0),), mode="edge")
    bare = np.pad(mat.apron(g0, g1, h0, h1), padw, mode="edge")
    wr, _ = quadrant_sets(w, bare=bare)
    return wr[r0 - a0:r1 - a0, c0 - b0:c1 - b0]


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
