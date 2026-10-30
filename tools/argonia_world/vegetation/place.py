"""Our own placement from the region rules (2.W4 §a's fallback; 0.4's risk "the region generator cannot be driven
headless ... else our own placement from the same region rules, writing the same REFRs"; owner issue #15: no
Creation Kit on the game machine yet).

The rules are the data: each REGN's object list (`land_region_object`, 2.W3) gives every form its density (stems per
hectare), clustering (stems per clump), radius (the clump's radius), slope and height bands, water posture and the
ConformToSlope flag; `vegetation_form` gives each form's scale range and `vegetation_region_budget` each region's
thinning (the per-cell budget, applied by region, never by hand). Nothing here is tuned per cell.

Per cell and form (seeded by the cell and the form, so a cell rebuilds alone and identically):
- **Density, calibrated:** the cell's expected stems are density x the cell's area (0.342 ha); clump centres are
  a jittered grid of k x k strata over the cell (k = floor(sqrt(clumps))), each stratum holding floor(e) centres
  plus one with probability frac(e), so the expectation is exact; a clump scatters `clustering` stems uniformly
  over its radius (mirrored back into the cell at an edge, so an edge cell is not thinned). A form whose radius is
  under CLUMP_MIN_RADIUS_M places single stems. The rules then reject what the ground refuses, as the CK's
  generator does: density is per hectare of the cell, not of the suitable ground.
- **The ground** is the game's (terrain/build.game_heights_m: quantised, limited, regraded; the LAND's vertices).
  A stem's z is the mean of the quad's two triangulations (the navmesh's convention); a point where the two differ
  by more than TWIST_MAX_M is refused, so z is within 0.5 m of the engine's ground whichever diagonal it uses.
  Slope is the quad's gradient in degrees.
- **Water posture:** water is what ArgoniaWorld.esm places (the default 0, a cell's height, every plane: navmesh
  inputs.water_levels over out/water/cells.jsonl). Depth at a stem is the highest water over its quad's corners
  less the ground. The rows' water_min_m/water_max_m are the old palette's water_depth_m (standing water over the
  ground; negative is the height above the local water table): on dry ground the depth is minus the height above
  the table, the level of the nearest water (a coarse map, TABLE_STEP samples a tile). A form with no posture is
  dry-land flora: never where there is water.
- **Road exclusion:** no stem within the traced road's half width plus ROAD_MARGIN_M of its centreline
  (routes/paint.py's segments), nor in a quad with a painted BC_ROAD or TRACK corner (the imported paint too).
- **Place exclusion:** no stem inside a built place's footprint: the bounds of its exterior build_refs plus
  PLACE_MARGIN_M.
- **Spacing:** no two stems of a cell closer than MIN_SPACING_M (trunk on trunk), first come first kept in the
  forms' order.
- **Budget:** each stem carries a uniform draw u; a region keeps the stems with u < keep (its budget row). Keep is
  the largest value that brings the region's p95 and max cell to vanilla's forested range (VANILLA_P95,
  VANILLA_MAX) and holds every cell at or under the cap (`threshold`).
"""
from __future__ import annotations

import math
import zlib
from dataclasses import dataclass

import numpy as np

from tools.argonia_world import skyrim_units as su

SEED = 0x2E4A  # the placement's own seed (with the cell and the form)
CELL_HA = su.CELL_METRES ** 2 / 10_000.0  # 0.3421 ha
STEP_M = su.VERTEX_SPACING_UNITS / su.UNITS_PER_METRE  # 1.828 m between LAND vertices
CLUMP_MIN_RADIUS_M = 1.0  # a smaller clump radius places single stems
MIN_SPACING_M = 1.5  # no two stems of a cell closer (trunk on trunk)
TWIST_MAX_M = 0.45  # the two triangulations' half-difference refused above this (z within 0.5 m of either)
ROAD_MARGIN_M = 1.5  # beyond the road's half width
PLACE_MARGIN_M = 20.0  # beyond a built place's refs' bounds
TABLE_STEP = 8  # samples per tile of the water-table map (14.6 m)
CAP = 400  # refs per cell: the starting budget (2.W4 §a: measured on the GPU instance at L4, owed)
# Vanilla Tamriel's forested cells (Skyrim.esm, the 3,449 exterior cells with 10 or more TREE refs; TREE plus rock
# STAT refs per cell, measured 2026-10-30, docs/research/journals/vegetation.md): the range a region's cells are
# thinned into, as the CK's generator would land (planner, 2026-10-30)
VANILLA_P95 = 83
VANILLA_MAX = 162
SLOT = 512  # FormIDs reserved per province cell (>= CAP)
VEG_BASE = 0x620000  # ArgoniaWorld.esm: past the navmesh's NAVM range (0x600000 + 262^2 cells = 0x610C24)
PLUGIN = "ArgoniaWorld.esm"


@dataclass(frozen=True)
class Rule:
    """One RDOT row as the placement reads it (metres and degrees)."""
    form_key: str
    density_per_ha: float
    clustering: int
    radius_m: float
    min_slope: float
    max_slope: float
    min_height: float | None
    max_height: float | None
    water_min: float | None
    water_max: float | None
    conform: bool
    scale: tuple[float, float]

    @property
    def dry_only(self) -> bool:
        return self.water_min is None and self.water_max is None


def ref_id(cx: int, cy: int, k: int) -> int:
    """The local FormID of a cell's k-th stem (0031 §3: computed from the grid, never allocated)."""
    x0, y0 = su.PROVINCE_CELL_SW
    i = (cy - y0) * su.PROVINCE_CELLS + (cx - x0)
    if not (0 <= i < su.PROVINCE_CELLS ** 2) or not (0 <= k < SLOT):
        raise ValueError(f"cell ({cx},{cy}) stem {k}: outside the reserved vegetation range")
    return VEG_BASE + i * SLOT + k


def rng_for(cx: int, cy: int, form_key: str) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([SEED, cx + 1024, cy + 1024, zlib.crc32(form_key.encode())]))


# --- candidates ------------------------------------------------------------------------------------------------
def candidates(rule: Rule, cx: int, cy: int) -> dict[str, np.ndarray]:
    """The form's candidate stems in the cell before any rule: u, v (units from the cell's south-west corner),
    yaw (radians), scale and the thinning draw."""
    g = rng_for(cx, cy, rule.form_key)
    side = float(su.CELL_UNITS)
    stems = rule.density_per_ha * CELL_HA
    clump = rule.clustering if rule.radius_m >= CLUMP_MIN_RADIUS_M else 1
    clumps = stems / clump
    k = max(1, int(math.floor(math.sqrt(clumps))))
    e = clumps / (k * k)
    n = np.floor(e) + (g.random(k * k) < (e - math.floor(e)))
    n = n.astype(np.int64)
    si = np.repeat(np.arange(k * k), n)
    cu = (si % k + g.random(si.size)) * (side / k)
    cv = (si // k + g.random(si.size)) * (side / k)
    if clump > 1:
        r = su.metres_to_units(rule.radius_m) * np.sqrt(g.random((si.size, clump)))
        t = g.random((si.size, clump)) * 2 * math.pi
        u = (cu[:, None] + r * np.cos(t)).ravel()
        v = (cv[:, None] + r * np.sin(t)).ravel()
    else:
        u, v = cu, cv
    # at the precision the writer emits, so the rules judge the position the game gets (a point a rounding away
    # from a vertex line would otherwise be judged on the neighbouring quad)
    u = np.minimum(np.round(_mirror(u, side), 2), side - 0.01)
    v = np.minimum(np.round(_mirror(v, side), 2), side - 0.01)
    m = u.size
    lo, hi = rule.scale
    return {"u": u, "v": v, "yaw": g.random(m) * 2 * math.pi, "scale": lo + (hi - lo) * g.random(m),
            "thin": g.random(m)}


def _mirror(a: np.ndarray, side: float) -> np.ndarray:
    a = np.abs(a)
    a = np.where(a >= side, 2 * side - a, a)
    return np.clip(a, 0.0, np.nextafter(side, 0))


# --- the ground ------------------------------------------------------------------------------------------------
def ground_at(H: np.ndarray, u: np.ndarray, v: np.ndarray):
    """(zA, zB, gx, gy, i, j): the ground at the points under the quad's two triangulations (metres), the quad's
    gradient (rise per metre east and north) and its vertex index. H is the cell's (33, 33) vertex heights in
    metres, [i from the south, j from the west]."""
    fx, fy = u / su.VERTEX_SPACING_UNITS, v / su.VERTEX_SPACING_UNITS
    j = np.clip(np.floor(fx).astype(np.int64), 0, su.LAND_VERTS - 2)
    i = np.clip(np.floor(fy).astype(np.int64), 0, su.LAND_VERTS - 2)
    fx, fy = fx - j, fy - i
    h00, h10, h01, h11 = H[i, j], H[i, j + 1], H[i + 1, j], H[i + 1, j + 1]
    za = np.where(fx >= fy, h00 + fx * (h10 - h00) + fy * (h11 - h10), h00 + fy * (h01 - h00) + fx * (h11 - h01))
    zb = np.where(fx + fy <= 1, h00 + fx * (h10 - h00) + fy * (h01 - h00),
                  h11 + (1 - fx) * (h01 - h11) + (1 - fy) * (h10 - h11))
    gx = ((h10 - h00) + (h11 - h01)) / (2 * STEP_M)
    gy = ((h01 - h00) + (h11 - h10)) / (2 * STEP_M)
    return za, zb, gx, gy, i, j


def slope_deg(gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def conform_rot(gx: float, gy: float, yaw: float) -> tuple[float, float]:
    """(rx, ry) radians tilting the object's up axis onto the ground's normal, in its own turned frame (Skyrim's
    angles turn clockwise looking along each axis; owed: the L4 still of a conformed rock)."""
    c, s = math.cos(yaw), math.sin(yaw)
    lx, ly = gx * c - gy * s, gx * s + gy * c
    return -math.atan(ly), math.atan(lx)


def depth_at(L: np.ndarray, i: np.ndarray, j: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Standing water over the point: the highest water over the quad's corners less the ground (metres)."""
    lv = np.maximum(np.maximum(L[i, j], L[i, j + 1]), np.maximum(L[i + 1, j], L[i + 1, j + 1]))
    return lv - z


def posture_ok(rule: Rule, depth: np.ndarray, above_table: np.ndarray) -> np.ndarray:
    """The water posture: dry-land flora never on water; otherwise the depth (minus the height above the local
    water table on dry ground) within [water_min, water_max]."""
    wet = depth > 0
    if rule.dry_only:
        return ~wet
    d = np.where(wet, depth, -np.maximum(above_table, 0.0))
    lo = -np.inf if rule.water_min is None else rule.water_min
    hi = np.inf if rule.water_max is None else rule.water_max
    return (d >= lo) & (d <= hi)


def seg_dist(pr: np.ndarray, pc: np.ndarray, seg: np.ndarray) -> np.ndarray:
    """Distance (samples) from each point (grid row, col) to the nearest of the segments (n, 2, 2)."""
    out = np.full(pr.shape, np.inf)
    if not len(seg) or not pr.size:
        return out
    a, b = seg[:, 0], seg[:, 1]
    d = b - a
    L2 = np.maximum((d * d).sum(axis=1), 1e-12)
    for k in range(0, len(seg), 256):  # chunks: points x segments stays small
        ak, dk, lk = a[k:k + 256], d[k:k + 256], L2[k:k + 256]
        rr = pr[:, None] - ak[None, :, 0]
        cc = pc[:, None] - ak[None, :, 1]
        t = np.clip((rr * dk[None, :, 0] + cc * dk[None, :, 1]) / lk[None], 0, 1)
        e = (rr - t * dk[None, :, 0]) ** 2 + (cc - t * dk[None, :, 1]) ** 2
        out = np.minimum(out, np.sqrt(e.min(axis=1)))
    return out


@dataclass
class CellInputs:
    """What one cell's placement reads, all over its 33 x 33 vertices [i from the south, j from the west]."""
    cx: int
    cy: int
    H: np.ndarray  # ground, metres
    L: np.ndarray  # water surface, metres (the default 0 included)
    T: np.ndarray  # the local water table, metres (nan: no water anywhere)
    painted: np.ndarray  # bool: a BC_ROAD or TRACK sample
    south_row: int  # the grid row of vertex i = 0
    west_col: int  # the grid column of vertex j = 0
    roads: list  # [(half width in samples, (n, 2, 2) segments in grid row, col)] near the cell
    footprints: list  # [(row0, col0, row1, col1)] grid rectangles near the cell

    def grid(self, u: np.ndarray, v: np.ndarray):
        s = su.VERTEX_SPACING_UNITS
        return self.south_row - v / s, self.west_col + u / s


def excluded(ci: CellInputs, u: np.ndarray, v: np.ndarray, i: np.ndarray, j: np.ndarray) -> np.ndarray:
    """Road and place exclusion (bool per point)."""
    p = ci.painted
    out = p[i, j] | p[i, j + 1] | p[i + 1, j] | p[i + 1, j + 1]
    pr, pc = ci.grid(u, v)
    margin = ROAD_MARGIN_M / su.PROVINCE_SAMPLE_M
    for half, seg in ci.roads:
        out |= seg_dist(pr, pc, seg) < half + margin
    for r0, c0, r1, c1 in ci.footprints:
        out |= (pr >= r0) & (pr <= r1) & (pc >= c0) & (pc <= c1)
    return out


def place_cell(ci: CellInputs, rules: list[Rule]) -> dict[str, np.ndarray]:
    """Every stem the rules accept in the cell, before the budget: columns form (index into rules), u, v, z (metres),
    rx, ry, rz (radians), scale, thin."""
    cols: dict[str, list] = {k: [] for k in ("form", "u", "v", "z", "rx", "ry", "rz", "scale", "thin")}
    kept_u: list[float] = []
    kept_v: list[float] = []
    bucket: dict[tuple[int, int], list[int]] = {}
    sep = su.metres_to_units(MIN_SPACING_M)
    for fi, rule in enumerate(rules):
        c = candidates(rule, ci.cx, ci.cy)
        u, v = c["u"], c["v"]
        if not u.size:
            continue
        za, zb, gx, gy, i, j = ground_at(ci.H, u, v)
        z = (za + zb) / 2
        ok = np.abs(za - zb) / 2 <= TWIST_MAX_M
        sl = slope_deg(gx, gy)
        ok &= (sl >= rule.min_slope) & (sl <= rule.max_slope)
        if rule.min_height is not None:
            ok &= z >= rule.min_height
        if rule.max_height is not None:
            ok &= z <= rule.max_height
        depth = depth_at(ci.L, i, j, z)
        ti = np.where(np.isnan(ci.T[i, j]), -np.inf, ci.T[i, j])
        ok &= posture_ok(rule, depth, z - ti)
        idx = np.nonzero(ok)[0]
        if idx.size:
            idx = idx[~excluded(ci, u[idx], v[idx], i[idx], j[idx])]
        for k in idx.tolist():  # spacing, first come first kept
            pu, pv = float(u[k]), float(v[k])
            bx, by = int(pu // sep), int(pv // sep)
            near = False
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for q in bucket.get((bx + dx, by + dy), ()):
                        if (kept_u[q] - pu) ** 2 + (kept_v[q] - pv) ** 2 < sep * sep:
                            near = True
                            break
                    if near:
                        break
                if near:
                    break
            if near:
                continue
            bucket.setdefault((bx, by), []).append(len(kept_u))
            kept_u.append(pu)
            kept_v.append(pv)
            yaw = float(c["yaw"][k])
            rx, ry = conform_rot(float(gx[k]), float(gy[k]), yaw) if rule.conform else (0.0, 0.0)
            for key, val in (("form", fi), ("u", pu), ("v", pv), ("z", float(z[k])), ("rx", rx), ("ry", ry),
                             ("rz", yaw), ("scale", float(c["scale"][k])), ("thin", float(c["thin"][k]))):
                cols[key].append(val)
    return {k: np.asarray(v, dtype=np.int64 if k == "form" else np.float64) for k, v in cols.items()}


def threshold(thin: np.ndarray, cap: int = CAP) -> float:
    """The largest keep at which a cell holds no more than `cap` stems (1.0 when it never exceeds it)."""
    if thin.size <= cap:
        return 1.0
    return float(np.partition(thin, cap)[cap])


def vanilla_keep(counts) -> float:
    """The share of a region's stems that puts its cells' p95 and max at or under vanilla's forested cells'."""
    a = np.asarray(counts, dtype=np.float64)
    if not a.size or a.max() == 0:
        return 1.0
    return min(1.0, VANILLA_P95 / max(float(np.percentile(a, 95)), 1e-9), VANILLA_MAX / float(a.max()))


def keep_value(t: float) -> float:
    """A region's keep as stored: rounded down to 1e-6, so a stored keep never lets a cell over the cap."""
    return math.floor(t * 1e6) / 1e6
