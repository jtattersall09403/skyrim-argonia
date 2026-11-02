"""The water the ground fits (the 1.15 lane contract): one level per cell, the steps between cells, and the wet
footprint at sample resolution, as arrays the generator and the renderer use whole.

`load()` reads the water lane's solve (`water/solve.py`, the `cell_water` and `water_step` tables) when it holds
rows, else a fixture derived here from the same sources the solve reads (the frozen body-level raster
`hydrology-graph-bodies.npz` with `hydrology_body.level_m`, and the reach profiles `hydrology_reach.level_from_m`
-> `level_to_m` along `hydrology_reach_point`), so the ground lane builds while the solve lands.

Cell arrays are (126, 126) indexed [row from the north, column from the west]: cell (cx, cy) is at
[125 - (cy - CY0), cx - CX0]. Sample arrays are the province grid (4033, 4033), row 0 north.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from tools.argonia_world import skyrim_units as su

Q = su.QUADS_PER_CELL
C = su.PROVINCE_CELLS
N = C * Q
CX0, CY0 = su.PROVINCE_CELL_SW
TYPES = ("sea", "brackish", "blackwater", "fresh")
STEP_MIN_M = 0.05  # a smaller level difference between neighbours is one surface, not a step
SEA_LEVEL_M = 0.05
UPLAND_M = 60.0  # the fixture's fresh/blackwater split: tarns and upland ponds (black-marsh-climatology.md) stand high


@dataclass
class Step:
    cx: int
    cy: int
    edge: str  # 'n', 'e', 's', 'w': the drop from (cx, cy) across this edge to its neighbour
    upper_m: float
    lower_m: float
    cross_lo: int  # channel vertex range along the edge (0..32, west->east or south->north); -1 when closed
    cross_hi: int
    chain: str


@dataclass
class CellWater:
    level: np.ndarray  # (126, 126) float64 metres, NaN = no water
    wtype: np.ndarray  # (126, 126) int8 index into TYPES, -1 = none
    steps: list[Step] = field(default_factory=list)
    source: str = "fixture"
    # (126, 126) True where the cell's level is a body's or a reach's own (not an enclosed or padding cell's): only
    # there is the raster's water this level's footprint; None = every water cell
    held: np.ndarray | None = None

    def at(self, cx: int, cy: int) -> tuple[int, int]:
        return C - 1 - (cy - CY0), cx - CX0

    def level_of(self, cx: int, cy: int) -> float | None:
        v = self.level[self.at(cx, cy)]
        return None if np.isnan(v) else float(v)

    def samples(self) -> np.ndarray:
        """The cell level broadcast to every sample (4033, 4033) float32; the shared last row/column copies."""
        s = np.repeat(np.repeat(self.level.astype(np.float32), Q, 0), Q, 1)
        return np.pad(s, ((0, 1), (0, 1)), mode="edge")


# ---- the sample-resolution wet raster the fixture and the generator share ---------------------------------------
def reach_raster(world, n: int = N + 1) -> tuple[np.ndarray, np.ndarray]:
    """The reaches' channels as (level float32 NaN dry, reach index int32 -1) at samples: each centreline stamped
    at half its width, its level linear in arclength from level_from_m to level_to_m. Falls carry no water."""
    mpp = su.PROVINCE_SAMPLE_M
    lev = np.full((n, n), np.nan, np.float32)
    rid = np.full((n, n), -1, np.int32)
    reaches = world.query("SELECT id, kind, width_m, level_from_m, level_to_m FROM hydrology_reach ORDER BY id")
    pts: dict[str, list] = {}
    for p in world.query("SELECT reach_id, east_m, south_m FROM hydrology_reach_point ORDER BY reach_id, ord"):
        pts.setdefault(p["reach_id"], []).append((p["east_m"], p["south_m"]))
    for i, r in enumerate(reaches):
        if r["kind"] == "vertical-fall" or r["level_from_m"] is None or r["id"] not in pts or len(pts[r["id"]]) < 2:
            continue
        xy = np.asarray(pts[r["id"]], np.float64) / mpp  # (col, row) samples
        seg = np.diff(xy, axis=0)
        ln = np.hypot(seg[:, 0], seg[:, 1])
        cum = np.concatenate([[0.0], np.cumsum(ln)])
        k = max(2, int(cum[-1] * 2) + 1)
        t = np.linspace(0.0, cum[-1], k)
        cx = np.interp(t, cum, xy[:, 0])
        cy = np.interp(t, cum, xy[:, 1])
        lv = r["level_from_m"] + (r["level_to_m"] - r["level_from_m"]) * (t / max(cum[-1], 1e-9))
        rad = max(1, int(round((r["width_m"] or 4.0) / 2 / mpp)))
        oy, ox = np.mgrid[-rad:rad + 1, -rad:rad + 1]
        m = oy * oy + ox * ox <= rad * rad
        oy, ox = oy[m], ox[m]
        rr = (np.rint(cy)[:, None] + oy[None]).astype(int).ravel()
        cc = (np.rint(cx)[:, None] + ox[None]).astype(int).ravel()
        vv = np.repeat(lv, len(oy))
        ok = (rr >= 0) & (rr < n) & (cc >= 0) & (cc < n)
        rr, cc, vv = rr[ok], cc[ok], vv[ok]
        cur = lev[rr, cc]
        take = np.isnan(cur) | (vv < cur)  # where two corridors meet, the lower water
        lev[rr[take], cc[take]] = vv[take]
        rid[rr[take], cc[take]] = i
    return lev, rid


def wet_raster(world, root=None) -> tuple[np.ndarray, np.ndarray]:
    """(level float32 NaN dry, type int8 -1) at every province sample: bodies at their raster level, the sea at 0,
    then the reach channels on samples still dry."""
    from tools.argonia_world.terrain.grid import data_root

    z = np.load((root or data_root()) / "hydrology-graph-bodies.npz")
    lev = z["level"].astype(np.float32)
    lev[~np.isfinite(lev)] = np.nan
    sea = z["sea"]
    lev[sea & np.isnan(lev)] = 0.0
    rl, _ = reach_raster(world, lev.shape[0])
    dry = np.isnan(lev)
    lev[dry] = rl[dry]
    typ = np.full(lev.shape, -1, np.int8)
    wet = ~np.isnan(lev)
    typ[wet & (lev > SEA_LEVEL_M)] = 2
    typ[wet & (lev >= UPLAND_M)] = 3
    typ[wet & (np.abs(lev) <= SEA_LEVEL_M)] = 1
    typ[sea] = 0
    return lev, typ


def _blocks(a: np.ndarray) -> np.ndarray:
    """(4033, 4033) -> (126, 126, 1024): each cell's 32 x 32 interior-plus-west/north samples."""
    return a[:N, :N].reshape(C, Q, C, Q).transpose(0, 2, 1, 3).reshape(C, C, Q * Q)


def fixture(world, root=None) -> CellWater:
    """One level per cell from the wet raster: the median level of the cell's wet samples (rounded to 0.01 m), the
    type of the most of them; steps where neighbours differ, the channel where both sides of the edge are wet."""
    lev, typ = wet_raster(world, root)
    b = _blocks(lev)
    has = (~np.isnan(b)).sum(-1) >= 8  # a cell with a few stray wet samples has no water
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(b, axis=-1)
    level = np.where(has, np.round(med, 2), np.nan)
    tb = _blocks(typ.astype(np.int16) + 1)
    counts = np.stack([(tb == k + 1).sum(-1) for k in range(4)], -1)
    wtype = np.where(has, counts.argmax(-1), -1).astype(np.int8)
    cw = CellWater(level, wtype, source="fixture")
    cw.steps = derive_steps(level, ~np.isnan(lev))
    return cw


def derive_steps(level: np.ndarray, wet: np.ndarray, chain: str = "fixture") -> list[Step]:
    """Steps between neighbouring water cells whose levels differ; the channel is the run of edge vertices wet on
    both sides (the samples either side of the shared vertex line)."""
    out: list[Step] = []
    # east-west neighbours: cell [r, c] and [r, c+1] share grid column (c+1)*Q
    for r, c in zip(*np.nonzero(~np.isnan(level[:, :-1]) & ~np.isnan(level[:, 1:]))):
        a, b = level[r, c], level[r, c + 1]
        if abs(a - b) < STEP_MIN_M:
            continue
        col = (c + 1) * Q
        rows = np.arange(r * Q, r * Q + Q + 1)
        both = wet[rows, col - 1] & wet[rows, min(col + 1, N)]
        cx, cy = int(c + CX0), int(C - 1 - r + CY0)
        idx = np.nonzero(both[::-1])[0]  # vertex j from the south
        lo, hi, ch = (int(idx.min()), int(idx.max()), chain) if idx.size else (-1, -1, "closed")
        if a > b:
            out.append(Step(cx, cy, "e", float(a), float(b), lo, hi, ch))
        else:
            out.append(Step(cx + 1, cy, "w", float(b), float(a), lo, hi, ch))
    # north-south neighbours: cell [r, c] (north) and [r+1, c] (south) share grid row (r+1)*Q
    for r, c in zip(*np.nonzero(~np.isnan(level[:-1, :]) & ~np.isnan(level[1:, :]))):
        a, b = level[r, c], level[r + 1, c]
        if abs(a - b) < STEP_MIN_M:
            continue
        row = (r + 1) * Q
        cols = np.arange(c * Q, c * Q + Q + 1)
        both = wet[row - 1, cols] & wet[min(row + 1, N), cols]
        cx, cy = int(c + CX0), int(C - 1 - r + CY0)
        idx = np.nonzero(both)[0]
        lo, hi, ch = (int(idx.min()), int(idx.max()), chain) if idx.size else (-1, -1, "closed")
        if a > b:
            out.append(Step(cx, cy, "s", float(a), float(b), lo, hi, ch))
        else:
            out.append(Step(cx, cy - 1, "n", float(b), float(a), lo, hi, ch))
    return out


def from_solve(world) -> CellWater | None:
    """The water lane's tables when they hold rows."""
    try:
        rows = world.query("SELECT cx, cy, level_m, water_type, body_id, reach_id FROM cell_water")
    except Exception:
        return None
    if not rows:
        return None
    level = np.full((C, C), np.nan)
    wtype = np.full((C, C), -1, np.int8)
    held = np.zeros((C, C), bool)
    for r in rows:
        i, j = C - 1 - (r["cy"] - CY0), r["cx"] - CX0
        if 0 <= i < C and 0 <= j < C:
            level[i, j] = r["level_m"]
            wtype[i, j] = TYPES.index(r["water_type"])
            held[i, j] = bool(r["body_id"] or r["reach_id"])
    # a closed edge has no channel: the solve writes its range as 0..0, here -1 (no vertex is a channel)
    steps = [Step(s["cx"], s["cy"], s["edge"], s["upper_m"], s["lower_m"],
                  -1 if s["chain"] == "closed" else s["cross_lo"], -1 if s["chain"] == "closed" else s["cross_hi"],
                  s["chain"]) for s in world.query("SELECT * FROM water_step")]
    return CellWater(level, wtype, steps, source="cell_water", held=held)


def load(world=None, root=None) -> CellWater:
    from tools.argonia_world import db

    w = world if world is not None else db.open()
    return from_solve(w) or fixture(w, root)
