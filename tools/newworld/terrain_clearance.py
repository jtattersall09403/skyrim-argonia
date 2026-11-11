"""Clearance from the water plane: land stands clear above it and beds lie clear below it outside a narrow shore band,
as Skyrim's do, so distant land and the one-square-per-cell distant water never fight for depth (the far-off
flicker and the square water edges).

Measured in Skyrim.esm (Tamriel, terrain_character.SKYRIM_BOXES; height against each cell's own water), the share of
points within 32 units of the water plane by distance from the waterline:
  Hjaalmarch marsh   2-8 m inland 0.34, 8-20 m 0.027, 20-50 m 0.001;  2-8 m out 0.23, 8-20 m 0.008
  the Rift (lake)    2-8 m inland 0.16, 8-20 m 0.014, 20-50 m 0.000;  2-8 m out 0.11, 8-20 m 0.002
  north coast        2-8 m inland 0.22, 8-20 m 0.016, 20-50 m 0.000;  2-8 m out 0.12, 8-20 m 0.004
Medians: land 8-20 m inland 192 to 328 units up; beds 2-8 m out 48 to 96 units down, 8-20 m out 80 to 300.
So only the first few metres either side of the waterline lie near the plane.

The rule (after places and roads are laid, before LAND's rounding; the waterline is untouched since land only rises
and water only deepens):
- land: at least LAND_CLEAR_M over the water, reached by LAND_REACH_M from the waterline (linear from the shore
  height); marsh stays low and flat, a low terrace clear of the plane;
- water: at least BED_CLEAR_M deep, reached by BED_REACH_M from the waterline.

    shares(h) -> {stride: {"pm32", "pm64"}}   # share of points within 32 and 64 units, at full resolution and at
                                              # LOD4 to LOD32 sample spacings (every 4th to 32nd sample)
"""
from __future__ import annotations

import numpy as np

U = 70.0
LAND_CLEAR_M = 1.1          # 77 units: over the 64-unit band
LAND_REACH_M = 6.0
BED_CLEAR_M = 1.1
BED_REACH_M = 4.0
SHORE_M = 0.12              # terrain_shape.SHORE_M: the land at the waterline
STRIDES = (1, 4, 8, 16, 32)
# Skyrim.esm's Tamriel, every point with LAND against its cell's water (shares() on terrain_ref/tamriel_h.npy):
# 0.0137 within 32 units and 0.0253 within 64 at full resolution, the same (0.0135-0.0138, 0.0249-0.0256) at every
# LOD spacing; its land alone 0.0082-0.0087 and 0.0155-0.0158. Ours on build 20261109T204317Z: 0.049-0.072 and
# 0.107-0.132 (land alone 0.038-0.071, 0.092-0.131), worse the coarser the LOD.
SKYRIM = {"pm32": 0.0137, "pm64": 0.0253}
MAX_PM32 = 0.03             # the terrain check: at most about twice Skyrim's share at any spacing
MAX_PM64 = 0.05


# Still inland water (marsh, swamp, pond) is walked in and out of: its shore takes Hjaalmarch's profile (Skyrim.esm:
# the rise across a shore edge 8 / 24 / 48 units at p10 / median / p90; land and bed clear of the plane by 8 m,
# share within 32 units 0.34 at 2-8 m inland and 0.027 at 8-20 m), a longer reach on both sides.
STILL = ("green-marsh", "blackwater-swamp", "pond")
STILL_REACH_M = 8.0


def floors(d_land_m: np.ndarray, d_water_m: np.ndarray, water_s: np.ndarray, still=None) -> np.ndarray:
    """The clearance (units) each sample must keep from the plane: up for land, down for water. `still`: samples
    whose water is still inland water (STILL_REACH_M both sides)."""
    lr = LAND_REACH_M if still is None else np.where(still, STILL_REACH_M, LAND_REACH_M)
    br = BED_REACH_M if still is None else np.where(still, STILL_REACH_M, BED_REACH_M)
    land = U * np.minimum(LAND_CLEAR_M, SHORE_M + (LAND_CLEAR_M - SHORE_M) * d_land_m / lr)
    bed = U * np.minimum(BED_CLEAR_M, SHORE_M + (BED_CLEAR_M - SHORE_M) * d_water_m / br)
    return np.where(water_s, bed, land).astype(np.float32)


def apply(h: np.ndarray, sd_m: np.ndarray, water_s: np.ndarray, keep: np.ndarray | None = None, still=None) -> dict:
    """Raise land and deepen water to their clearance (h in units, mutated). sd_m: the smooth signed distance from
    the waterline (metres, water < 0). `keep`: samples left as they are. `still`: as floors."""
    c = floors(np.maximum(sd_m, 0), np.maximum(-sd_m, 0), water_s, still)
    up = ~water_s & (h < c)
    down = water_s & (h > -c)
    if keep is not None:
        up &= ~keep
        down &= ~keep
    out = {"land_raised": int(up.sum()), "beds_deepened": int(down.sum()),
           "land_raised_mean_m": round(float((c[up] - h[up]).mean() / U), 3) if up.any() else 0.0,
           "beds_deepened_mean_m": round(float((h[down] + c[down]).mean() / U), 3) if down.any() else 0.0}
    h[up] = c[up]
    h[down] = -c[down]
    return out


def shares(h: np.ndarray, water_level: float | np.ndarray = 0.0, valid: np.ndarray | None = None) -> dict:
    out = {}
    for s in STRIDES:
        a = (h[::s, ::s] - (water_level[::s, ::s] if isinstance(water_level, np.ndarray) else water_level))
        if valid is not None:
            a = a[valid[::s, ::s]]
        a = np.abs(a)
        out[f"lod{s}" if s > 1 else "full"] = {"pm32": round(float((a <= 32).mean()), 4),
                                               "pm64": round(float((a <= 64).mean()), 4)}
    return out


STEP = 128.0
WALK_DEG = 45.0             # tools/navmesh/params.py MAX_SLOPE_DEG: the steepest triangle the navmesh walks


def triangle_slopes(h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Slope (degrees) of the two triangles of every quad of samples: (north-west, south-east), each (R-1, C-1)."""
    a, b, c, d = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
    t1 = np.degrees(np.arctan(np.hypot(b - a, c - a) / STEP)).astype(np.float32)
    t2 = np.degrees(np.arctan(np.hypot(d - c, d - b) / STEP)).astype(np.float32)
    return t1, t2


def waterline(h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Which of those triangles cross the waterline (a corner in the water and a corner on land)."""
    w = h <= 0
    a, b, c, d = w[:-1, :-1], w[:-1, 1:], w[1:, :-1], w[1:, 1:]
    return (a | b | c) & ~(a & b & c), (b | c | d) & ~(b & c & d)


def shore_steep(h: np.ndarray, inside: np.ndarray | None = None, code: np.ndarray | None = None,
                names: list | None = None) -> dict:
    """Waterline triangles and the share of them over WALK_DEG; `inside` (samples): only quads wholly inside;
    `code` (samples) with `names`: the same per code (the code of a quad's north-west sample)."""
    t1, t2 = triangle_slopes(h)
    w1, w2 = waterline(h)
    if inside is not None:
        q = inside[:-1, :-1] & inside[:-1, 1:] & inside[1:, :-1] & inside[1:, 1:]
        w1, w2 = w1 & q, w2 & q
    n = int(w1.sum() + w2.sum())
    over = int((t1[w1] > WALK_DEG).sum() + (t2[w2] > WALK_DEG).sum())
    out = {"triangles": n, "over_walk": round(over / n, 4) if n else 0.0,
           "median_deg": round(float(np.median(np.concatenate([t1[w1], t2[w2]]))), 1) if n else 0.0}
    if code is not None:
        cq = code[:-1, :-1]
        out["by"] = {}
        for k, name in enumerate(names):
            s1, s2 = w1 & (cq == k), w2 & (cq == k)
            m = int(s1.sum() + s2.sum())
            if m:
                out["by"][name] = {"triangles": m, "over_walk": round(
                    float(((t1[s1] > WALK_DEG).sum() + (t2[s2] > WALK_DEG).sum()) / m), 4)}
    return out


def shore_rise(h: np.ndarray, sel: np.ndarray | None = None) -> list:
    """The rise (units) across every sample edge that crosses the waterline: p10, median, p90."""
    r = []
    for ax in (0, 1):
        x, y = (h[:-1], h[1:]) if ax == 0 else (h[:, :-1], h[:, 1:])
        m = (x <= 0) != (y <= 0)
        if sel is not None:
            m &= (sel[:-1] & sel[1:]) if ax == 0 else (sel[:, :-1] & sel[:, 1:])
        r.append(np.abs(x[m] - y[m]))
    r = np.concatenate(r)
    return [float(v) for v in np.percentile(r, (10, 50, 90))] if r.size else []
