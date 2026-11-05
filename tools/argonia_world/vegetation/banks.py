"""The river-bank view (lane 1.15-r6-bank-plants): the share of river and creek bank whose view across the water at
eye height is open, by the journeys' tall_near measure (nothing whose top stands more than TALL_M over its ground
comes within OFF_M of the line out REACH_M from the bank, its canopy radius widened; a trunked plant whose crown
starts over the eye, from CROWN_FROM of its height as the journeys' clearance reads it, by its trunk alone), for our build and for
Skyrim.esm (0034: the White River and the Treva in Whiterun Hold are the bar).

A bank point is a dry LAND vertex with a wet 4-neighbour (ground under its cell's water) in a river or creek cell;
its view runs across the water (towards the wet vertices within HEAD_SAMPLES). Our river and creek cells are the
cell_water rows of a clearwater or whitewater reach; Skyrim's are Whiterun Hold's inland water cells (XCLW).

    python3 -m tools.argonia_world.vegetation.banks [--skyrim ESM] [--box X0 X1 Y0 Y1]
        prints the measure as JSON (ours; Skyrim's too with --skyrim: game data is read, never written)
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import struct
from collections import defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su

ROOT = Path(__file__).resolve().parents[3]
REACH_M, OFF_M, TALL_M = 15.0, 4.0, 1.0  # tools/journeys tall_near's constants
EYE_M, CROWN_FROM, TRUNK_M = 1.7, 0.4, 0.35  # tools/journeys: a trunked plant's crown from 0.4 of its height up
BANK_M = 10.0  # the bank band: plants this near the water are its bank's plants
HEAD_SAMPLES = 3
RIVER_WATERS = ("clearwater", "whitewater")  # the reach waters that are a river or a creek
WHITERUN_BOX = (-2, 22, -14, 10)  # Tamriel cells: the White River from Riverwood to Valtheim and the Treva
TAMRIEL = 0x3C


def eye_radius(radius, top, trunked: bool):
    """A plant's reach at eye height (units): a trunked plant whose crown starts over the eye is its trunk there."""
    u = su.UNITS_PER_METRE
    return TRUNK_M * u if trunked and CROWN_FROM * top > EYE_M * u else radius


# --- the measure -----------------------------------------------------------------------------------------------
def bank_points(H: np.ndarray, lev: np.ndarray, x0: float, y0: float, step: float = su.VERTEX_SPACING_UNITS):
    """(xy (n, 2) units, unit headings (n, 2) across the water) of a grid (rows south to north, origin x0, y0
    units at [0, 0]); lev: the water level per vertex (nan: no river water)."""
    wet = np.nan_to_num(lev, nan=-np.inf) > H
    dry = ~wet
    edge = np.zeros_like(wet)
    edge[1:] |= wet[:-1]
    edge[:-1] |= wet[1:]
    edge[:, 1:] |= wet[:, :-1]
    edge[:, :-1] |= wet[:, 1:]
    r, c = np.nonzero(dry & edge)
    k = HEAD_SAMPLES
    hx, hy = np.zeros(r.size), np.zeros(r.size)
    for dr in range(-k, k + 1):
        for dc in range(-k, k + 1):
            if dr == dc == 0:
                continue
            rr, cc = np.clip(r + dr, 0, H.shape[0] - 1), np.clip(c + dc, 0, H.shape[1] - 1)
            w = wet[rr, cc] / math.hypot(dr, dc)
            hx += w * dc
            hy += w * dr
    n = np.hypot(hx, hy)
    ok = n > 0
    xy = np.c_[x0 + c[ok] * step, y0 + r[ok] * step]
    return xy, np.c_[hx[ok] / n[ok], hy[ok] / n[ok]]


class Plants:
    """Plants as (x, y, radius, top over the ground) units, bucketed for the line test."""

    def __init__(self, a: np.ndarray, keys: list[str] | None = None):
        self.a = np.asarray(a, dtype=np.float64).reshape(-1, 4)
        self.keys = keys
        self.b = 30.0 * su.UNITS_PER_METRE
        self.rmax = float(self.a[:, 2].max()) if len(self.a) else 0.0
        self.idx: dict[tuple[int, int], list[int]] = defaultdict(list)
        for i, (x, y) in enumerate(self.a[:, :2]):
            self.idx[(int(x // self.b), int(y // self.b))].append(i)

    def near(self, x: float, y: float, reach: float) -> np.ndarray:
        k = int(reach // self.b) + 1
        bx, by = int(x // self.b), int(y // self.b)
        out = [n for i in range(bx - k, bx + k + 1) for j in range(by - k, by + k + 1) for n in self.idx.get((i, j), ())]
        return np.asarray(out, dtype=np.int64)


def closed(xy: np.ndarray, head: np.ndarray, p: Plants) -> np.ndarray:
    """True where a plant over TALL_M comes within OFF_M (less its radius) of the line out REACH_M (tall_near)."""
    u = su.UNITS_PER_METRE
    out = np.zeros(len(xy), dtype=bool)
    tall = p.a[:, 3] > TALL_M * u
    for n, ((x, y), (hx, hy)) in enumerate(zip(xy, head)):
        dx, dy = hx * REACH_M * u, hy * REACH_M * u
        i = p.near(x + dx / 2, y + dy / 2, REACH_M * u / 2 + OFF_M * u + p.rmax)
        if not i.size:
            continue
        i = i[tall[i]]
        q = p.a[i]
        t = np.clip(((q[:, 0] - x) * dx + (q[:, 1] - y) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
        d = np.hypot(x + t * dx - q[:, 0], y + t * dy - q[:, 1]) - q[:, 2]
        out[n] = bool((d < OFF_M * u).any())
    return out


def within(xy: np.ndarray, p: Plants, m: float = BANK_M) -> np.ndarray:
    """Indices of the plants within m metres of any bank point."""
    u = su.UNITS_PER_METRE
    hit = set()
    for x, y in xy:
        i = p.near(x, y, m * u)
        if i.size:
            d = np.hypot(p.a[i, 0] - x, p.a[i, 1] - y)
            hit.update(i[d <= m * u].tolist())
    return np.asarray(sorted(hit), dtype=np.int64)


def measure(xy, head, p: Plants, focus: str | None = None) -> dict:
    u = su.UNITS_PER_METRE
    km = len(xy) * su.VERTEX_SPACING_UNITS / u / 1000  # a bank vertex stands for one vertex spacing of bank line
    cl = closed(xy, head, p)
    near = within(xy, p)
    tall = near[p.a[near, 3] > TALL_M * u] if near.size else near
    out = {"bank_points": int(len(xy)), "bank_km": round(km, 2), "open_share": round(1 - float(cl.mean()), 3) if len(xy) else None,
           "tall_within_10m_per_km": round(len(tall) / km, 1) if km else None}
    if focus and p.keys is not None:
        f = np.asarray([k == focus for k in p.keys])
        out["focus_within_10m_per_km"] = round(int(f[near].sum()) / km, 1) if km else None
    return out


# --- our build ---------------------------------------------------------------------------------------------------
def ours(veg: Path = ROOT / "out" / "terrain" / "vegetation", focus: str = "03A583:King of the Murkmire.esp") -> dict:
    from tools.argonia_world import db
    from tools.journeys import Build
    from tools.world_sample import Ground
    w = db.open()
    g = Ground()
    Hn = g.H  # row 0 north, metres
    H = Hn[::-1] * su.UNITS_PER_METRE  # row 0 south, units
    lev = np.full(H.shape, np.nan)
    cells = [(r["cx"], r["cy"], r["level_m"]) for r in w.query(
        "SELECT c.cx, c.cy, c.level_m FROM cell_water c JOIN hydrology_reach r ON r.id = c.reach_id "
        f"WHERE r.water IN ({','.join('?' * len(RIVER_WATERS))})", *RIVER_WATERS)]
    x0c, y0c = su.PROVINCE_CELL_SW
    for cx, cy, lv in cells:
        r0, c0 = (cy - y0c) * su.QUADS_PER_CELL, (cx - x0c) * su.QUADS_PER_CELL
        lev[r0:r0 + 33, c0:c0 + 33] = su.metres_to_units(lv)
    xy, head = bank_points(H, lev, x0c * su.CELL_UNITS, y0c * su.CELL_UNITS)
    shapes = Build().shapes()
    rows, keys, scales = [], [], []
    region = _cell_regions(w)
    eco = {r["id"]: r["eco_class_id"] for r in w.query("SELECT id, eco_class_id FROM land_region")}
    by_eco: dict[str, int] = defaultdict(int)
    for p in sorted(veg.glob("cy*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="ascii") as f:
            for ln in f:
                c = json.loads(ln)
                for r in c["refs"]:
                    k = c["bases"][r[1]]
                    s = shapes.get(k)
                    if not s:
                        continue
                    x, y, z, sc = r[2], r[3], r[4], r[8]
                    top = z + s[3] * sc + s[1] * sc - _ground(H, x, y)
                    rows.append((x, y, eye_radius(s[0] * sc, top, not s[2]), top))
                    keys.append(k)
                    if k == focus:
                        scales.append(sc)
                        by_eco[eco.get(region.get((c["x"], c["y"])), "?")] += 1
    p = Plants(np.asarray(rows), keys)
    out = measure(xy, head, p, focus)
    ha = defaultdict(float)
    for (cx, cy), rid in region.items():
        ha[eco.get(rid, "?")] += (su.CELL_METRES ** 2) / 1e4
    out["focus"] = focus
    out["focus_per_ha_by_eco"] = {e: round(n / ha[e], 2) for e, n in sorted(by_eco.items()) if ha.get(e)}
    if scales:
        out["focus_scale_p10_p50_p90"] = [round(float(v), 3) for v in np.percentile(scales, [10, 50, 90])]
    out["river_cells"] = len(cells)
    return out


def _cell_regions(w) -> dict:
    from tools.argonia_world.vegetation import build
    return build.cell_regions(w)


def _ground(H: np.ndarray, x: float, y: float) -> float:
    """Bilinear ground (units) of a south-up province grid at a Skyrim point."""
    x0c, y0c = su.PROVINCE_CELL_SW
    c = (x - x0c * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
    r = (y - y0c * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS
    r0, c0 = min(max(int(r), 0), H.shape[0] - 2), min(max(int(c), 0), H.shape[1] - 2)
    fr, fc = min(max(r - r0, 0.0), 1.0), min(max(c - c0, 0.0), 1.0)
    return float(H[r0, c0] * (1 - fr) * (1 - fc) + H[r0, c0 + 1] * (1 - fr) * fc + H[r0 + 1, c0] * fr * (1 - fc)
                 + H[r0 + 1, c0 + 1] * fr * fc)


# --- Skyrim.esm ----------------------------------------------------------------------------------------------------
def skyrim(esm: Path, box=WHITERUN_BOX) -> dict:
    from tools.argonia_world.terrain.esm import records
    from tools.argonia_world.terrain.probes.vanilla_lake_cells import vhgt
    x0, x1, y0, y1 = box
    obnd, edid, sig = {}, {}, {}
    water, land, refs = {}, {}, []
    wrld = cell = None
    for r in records(esm.read_bytes()):
        sig[r.formid] = r.sig
        if r.sig in ("TREE", "STAT", "FLOR"):
            b = r.first("OBND")
            if b:
                obnd[r.formid] = struct.unpack_from("<6h", b)
            e = r.first("EDID")
            edid[r.formid] = e.rstrip(b"\0").decode("latin-1") if e else ""
        elif r.sig == "WRLD":
            wrld = r.formid
        elif r.sig == "CELL":
            xc = r.first("XCLC")
            cell = None
            if xc and wrld == TAMRIEL:
                c = struct.unpack_from("<ii", xc)
                if x0 - 1 <= c[0] <= x1 + 1 and y0 - 1 <= c[1] <= y1 + 1:
                    cell = c
                    wv, d = r.first("XCLW"), r.first("DATA")
                    if wv and d and d[0] & 2:
                        h = struct.unpack_from("<f", wv)[0]
                        if -1e6 < h < 1e6:
                            water[c] = h
        elif cell is not None and r.sig == "LAND" and cell not in land:
            v = r.first("VHGT")
            if v:
                land[cell] = vhgt(v)
        elif cell is not None and r.sig == "REFR":
            n, d = r.first("NAME"), r.first("DATA")
            if n and d:
                sc = r.first("XSCL")
                refs.append((struct.unpack_from("<I", n)[0], *struct.unpack_from("<3f", d),
                             struct.unpack_from("<f", sc)[0] if sc else 1.0))
    nx, ny = x1 - x0 + 3, y1 - y0 + 3
    H = np.zeros((ny * 32 + 1, nx * 32 + 1))
    lev = np.full(H.shape, np.nan)
    for (cx, cy), g in land.items():
        r0, c0 = (cy - y0 + 1) * 32, (cx - x0 + 1) * 32
        H[r0:r0 + 33, c0:c0 + 33] = g
        if (cx, cy) in water and x0 <= cx <= x1 and y0 <= cy <= y1:
            lev[r0:r0 + 33, c0:c0 + 33] = water[(cx, cy)]
    ox, oy = (x0 - 1) * su.CELL_UNITS, (y0 - 1) * su.CELL_UNITS
    xy, head = bank_points(H, lev, ox, oy)

    def ground(x, y):
        c, r = (x - ox) / su.VERTEX_SPACING_UNITS, (y - oy) / su.VERTEX_SPACING_UNITS
        r0, c0 = min(max(int(r), 0), H.shape[0] - 2), min(max(int(c), 0), H.shape[1] - 2)
        return H[r0, c0]

    rows, keys = [], []
    for base, x, y, z, sc in refs:
        if sig.get(base) != "TREE" and not (sig.get(base) in ("STAT", "FLOR") and any(
                k in edid.get(base, "").lower() for k in ("shrub", "bush", "fern", "plant", "reed", "cattail"))):
            continue
        b = obnd.get(base)
        if not b:
            continue
        rad = max(abs(b[0]), abs(b[1]), abs(b[3]), abs(b[4])) * sc
        top = z + b[5] * sc - ground(x, y)
        e = edid.get(base, "").lower()
        rows.append((x, y, eye_radius(rad, top, "tree" in e and not any(k in e for k in ("shrub", "bush"))), top))
        keys.append(edid.get(base, ""))
    out = measure(xy, head, Plants(np.asarray(rows), keys))
    out["water_cells"] = sum(1 for c in water if x0 <= c[0] <= x1 and y0 <= c[1] <= y1)
    out["box"] = list(box)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skyrim", type=Path)
    ap.add_argument("--box", type=int, nargs=4, default=WHITERUN_BOX)
    ap.add_argument("--no-ours", action="store_true")
    a = ap.parse_args(argv)
    out = {}
    if not a.no_ours:
        out["ours"] = ours()
    if a.skyrim:
        out["skyrim"] = skyrim(a.skyrim, tuple(a.box))
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
