"""Ground held as built: a built place keeps the shape of the ground it was seated on when the world's relief changes.

Every place built as a place layer (a folder under newworld/places/) has a row in newworld/sources/terrain_held.json:
the terrain build it was seated on and the place layer's cells (Skyrim cells, 4096 units). Within those cells plus
MARGIN_M the new heightmap is that build's, sample for sample (its pier, streets, seating, navmesh and shore stay true
without re-seating); beyond, the old ground blends into the new over BLEND_M (smootherstep), rounded to LAND's step,
land kept over and water under the water level as the map says. A built place with no row stops the build; a place
layer that has grown past its row's cells stops it too (re-seat the place and give the row the new build's id).

The held ground is cut once from the named build (out/newworld/terrain when that is the build, else the bucket) into
out/newworld/terrain_held/<place>.<build>.npz, with its world origin, and reused.

    python3 -m tools.newworld.terrain_held check [terrain dir]   # inside each zone: land differs by one constant,
                                                                  # water never higher
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

from tools.newworld import frame as f

HELD = f.ROOT / "sources" / "terrain_held.json"
PLACES = f.ROOT / "places"
STORE = f.OUT / "terrain_held"
BUCKET = "s3://argonia-private-050977237313/nw/terrain"
MARGIN_M = 400.0
BLEND_M = 300.0
STEP = 128.0
U = 70.0
QUANT = 8.0
CELL = 4096.0


def built_places() -> list[str]:
    return sorted(p.name for p in PLACES.iterdir() if p.is_dir()) if PLACES.exists() else []


def rows() -> dict:
    """Every built place's held row; stops when a built place has none or its layer outgrew its cells."""
    held = json.loads(HELD.read_text())["places"] if HELD.exists() else {}
    out = {}
    for pid in built_places():
        if pid not in held:
            raise SystemExit(f"terrain_held: built place {pid} has no row in {HELD.name} (the terrain build it was "
                             "seated on and its place layer cells)")
        rec = held[pid]
        plan = f.REPO / "out" / "places" / "shards" / pid / "plan.json"
        if plan.exists():
            now = {(c["x"], c["y"]) for c in json.loads(plan.read_text())["cells"]}
            grown = now - {tuple(c) for c in rec["cells"]}
            if grown:
                raise SystemExit(f"terrain_held: {pid}'s place layer covers {len(grown)} cells its row does not "
                                 f"(e.g. {sorted(grown)[:3]}); re-seat it and update its row")
        out[pid] = rec
    return out


def _source(stamp: str) -> tuple[Path, Path, Path | None]:
    """(heightmap.npy, build.json, temp dir to delete) of terrain build `stamp`."""
    cur = f.OUT / "terrain"
    if (cur / "build.json").exists() and json.loads((cur / "build.json").read_text())["id"] == stamp:
        return cur / "heightmap.npy", cur / "build.json", None
    tmp = STORE / f"tmp.{stamp}"
    tmp.mkdir(parents=True, exist_ok=True)
    for name in ("heightmap.npy", "build.json"):
        if not (tmp / name).exists():
            subprocess.run(["aws", "s3", "cp", "--quiet", f"{BUCKET}/{stamp}/{name}", str(tmp / name)], check=True)
    return tmp / "heightmap.npy", tmp / "build.json", tmp


def zone_box(rec: dict, reach_m: float) -> tuple[float, float, float, float]:
    """World box (x0, x1, y0, y1) of the row's cells grown by reach_m, snapped out to the sample lattice."""
    c = np.array(rec["cells"], float)
    g = reach_m * U
    x0, x1 = c[:, 0].min() * CELL - g, (c[:, 0].max() + 1) * CELL + g
    y0, y1 = c[:, 1].min() * CELL - g, (c[:, 1].max() + 1) * CELL + g
    return (np.floor(x0 / STEP) * STEP, np.ceil(x1 / STEP) * STEP, np.floor(y0 / STEP) * STEP, np.ceil(y1 / STEP) * STEP)


def patch(pid: str, rec: dict) -> dict:
    """The held ground of one place: {"h": units, "x0", "y0": world position of its sample (0, 0)}."""
    stamp = rec["terrain_build"]
    fn = STORE / f"{pid}.{stamp}.npz"
    if fn.exists():
        z = np.load(fn)
        return {"h": z["h"], "x0": float(z["x0"]), "y0": float(z["y0"])}
    hp, bp, tmp = _source(stamp)
    b = json.loads(bp.read_text())
    if b["id"] != stamp:
        raise SystemExit(f"terrain_held: {bp} is build {b['id']}, not {stamp}")
    H = np.load(hp, mmap_mode="r")
    x0, x1, y0, y1 = zone_box(rec, MARGIN_M + BLEND_M + 50)
    j0, j1 = int(round((x0 - b["origin_world_x"]) / STEP)), int(round((x1 - b["origin_world_x"]) / STEP))
    i0, i1 = int(round((b["origin_world_y"] - y1) / STEP)), int(round((b["origin_world_y"] - y0) / STEP))
    i0, j0 = max(i0, 0), max(j0, 0)
    h = np.array(H[i0:i1 + 1, j0:j1 + 1], np.float32)
    px0, py0 = b["origin_world_x"] + j0 * STEP, b["origin_world_y"] - i0 * STEP
    STORE.mkdir(parents=True, exist_ok=True)
    np.savez(fn, h=h, x0=px0, y0=py0, stamp=stamp)
    del H
    if tmp is not None:
        shutil.rmtree(tmp)
    return {"h": h, "x0": px0, "y0": py0}


def weight(rec: dict, p: dict) -> np.ndarray:
    """1 inside the zone (cells + MARGIN_M), smootherstep to 0 at BLEND_M beyond, on the patch's samples."""
    shape = p["h"].shape
    inside = np.zeros(shape, bool)
    for cx, cy in rec["cells"]:
        j0 = int(round((cx * CELL - p["x0"]) / STEP))
        i0 = int(round((p["y0"] - (cy + 1) * CELL) / STEP))
        inside[max(i0, 0):max(i0 + 33, 0), max(j0, 0):max(j0 + 33, 0)] = True
    d = ndi.distance_transform_edt(~inside) * (STEP / U)
    x = np.clip((d - MARGIN_M) / BLEND_M, 0, 1)
    return (1 - x * x * x * (x * (6 * x - 15) + 10)).astype(np.float32)


def _window(grid, p: dict):
    """Slices of the grid and of the patch that overlap, or None."""
    oj = (p["x0"] - grid.ox) / STEP
    oi = (grid.oy - p["y0"]) / STEP
    if abs(oj - round(oj)) > 1e-6 or abs(oi - round(oi)) > 1e-6:
        raise SystemExit("terrain_held: the held ground is off the sample lattice")
    oi, oj = int(round(oi)), int(round(oj))
    H, W = p["h"].shape
    gi0, gj0 = max(oi, 0), max(oj, 0)
    gi1, gj1 = min(oi + H, grid.rows), min(oj + W, grid.cols)
    if gi1 <= gi0 or gj1 <= gj0:
        return None
    return (slice(gi0, gi1), slice(gj0, gj1)), (slice(gi0 - oi, gi1 - oi), slice(gj0 - oj, gj1 - oj))


def lift(rec: dict, p: dict) -> float:
    """The smallest constant (units, on LAND's step) that stands the zone's land LAND_REACH_M or more from the water
    at least LAND_CLEAR_M over the plane."""
    from tools.newworld import terrain_clearance as tcl
    o = p["h"]
    land = o > 0
    d = ndi.distance_transform_edt(land) * (STEP / U)
    sel = (weight(rec, p) >= 1) & land & (d >= tcl.LAND_REACH_M)
    if not sel.any():
        return 0.0
    need = tcl.LAND_CLEAR_M * U - float(o[sel].min())
    return float(max(0.0, np.ceil(need / QUANT) * QUANT))


def held_ground(rec: dict, p: dict, new: np.ndarray, L: float) -> np.ndarray:
    """The held heights on the patch window: old land + L, old water kept or deepened to the new ground's bed."""
    old = p["h"]
    return np.where(old > 0, old + L, np.where(new < 0, np.minimum(old, new), old)).astype(np.float32)


def apply(h: np.ndarray, grid, water_s: np.ndarray) -> dict:
    """Lay every built place's held ground into h (units, mutated). Returns per place what was held and its lift."""
    out = {}
    for pid, rec in rows().items():
        p = patch(pid, rec)
        win = _window(grid, p)
        if win is None:
            out[pid] = {"note": "outside the grid"}
            continue
        gs, ps = win
        w = weight(rec, p)[ps]
        L = lift(rec, p)
        new = h[gs]
        old = held_ground(rec, {"h": p["h"][ps]}, new, L)
        mix = w * old + (1 - w) * new
        ring = (w > 0) & (w < 1)
        mix = np.where(ring, np.round(mix / QUANT) * QUANT, mix)
        ws = water_s[gs]
        mix = np.where(ring & ws & (mix > -QUANT), -QUANT, mix)
        mix = np.where(ring & ~ws & (mix < QUANT), QUANT, mix)
        h[gs] = np.where(w >= 1, old, mix).astype(h.dtype)
        out[pid] = {"terrain_build": rec["terrain_build"], "lift_units": L, "held_samples": int((w >= 1).sum()),
                    "blend_samples": int(ring.sum()), "margin_m": MARGIN_M, "blend_m": BLEND_M}
    return out


def check(h: np.ndarray, grid) -> dict:
    """Per built place, inside its zone: the largest departure (units) of a land sample from its held build's height
    plus the lift (must be 0), and the water samples standing higher than in the held build (must be 0)."""
    out = {}
    for pid, rec in rows().items():
        p = patch(pid, rec)
        win = _window(grid, p)
        if win is None:
            out[pid] = {"max_diff_units": None, "note": "outside the grid"}
            continue
        gs, ps = win
        w = weight(rec, p)[ps]
        inside = w >= 1
        full = int((weight(rec, p) >= 1).sum())
        L = lift(rec, p)
        old, new = p["h"][ps][inside].astype(np.float64), h[gs][inside].astype(np.float64)
        land = old > 0
        d = np.abs(new[land] - old[land] - L)
        out[pid] = {"terrain_build": rec["terrain_build"], "samples": int(inside.sum()),
                    "zone_samples_in_grid": f"{int(inside.sum())} of {full}", "lift_units": L,
                    "max_diff_units": float(d.max()) if d.size else None,
                    "water_higher": int((new[~land] > old[~land]).sum()),
                    "waterline_moved": int(((new > 0) != land).sum())}
    return out


def ok(res: dict) -> bool:
    return all(r.get("max_diff_units") == 0.0 and r["samples"] > 0 and not r.get("water_higher")
               and not r.get("waterline_moved") for r in res.values())


if __name__ == "__main__":
    from tools.newworld import terrain_needs as tn
    tdir = Path(sys.argv[2]) if len(sys.argv) > 2 else f.OUT / "terrain"
    b = json.loads((tdir / "build.json").read_text())
    res = check(np.load(tdir / "heightmap.npy"), tn.grid_of(b))
    print(json.dumps(res, indent=1))
    sys.exit(0 if ok(res) else 1)
