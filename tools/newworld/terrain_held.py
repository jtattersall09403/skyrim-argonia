"""Ground held as built: a built place keeps the shape of the ground it was seated on when the world's relief changes.

Every place built as a place layer (a folder under newworld/places/) has a row in newworld/sources/terrain_held.json:
the terrain build it was seated on and the place layer's cells (Skyrim cells, 4096 units). Within those cells plus
MARGIN_M the water's beds are that build's, sample for sample, and the land is that build's plus a lift that is
nothing at the old waterline and whole ramp_units() from it (so the waterline, the banks' slopes and the wading
depths stay as built (its pier, streets, seating, navmesh and shore stay true
without re-seating); beyond, the old ground blends into the new over BLEND_M (smootherstep), rounded to LAND's step,
land kept over and water under the water level as the map says. A built place with no row stops the build; a place
layer that has grown past its row's cells stops it too (re-seat the place and give the row the new build's id).

The held ground is cut once from the named build (out/newworld/terrain when that is the build, else the bucket) into
out/newworld/terrain_held/<place>.<build>.npz, with its world origin, and reused.

    python3 -m tools.newworld.terrain_held check [terrain dir]   # inside each zone: land differs by one constant,
                                                                  # water never higher
"""
from __future__ import annotations

import hashlib
import json
import os
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
    x0, x1, y0, y1 = zone_box(rec, MARGIN_M + BLEND_M + 50)
    # keyed by the build and the box cut from it: a row whose cells (or the margins) change cuts a new patch
    key = hashlib.sha256(json.dumps([stamp, x0, x1, y0, y1]).encode()).hexdigest()[:12]
    fn = STORE / f"{pid}.{stamp}.{key}.npz"
    if fn.exists():
        z = np.load(fn)
        return {"h": z["h"], "x0": float(z["x0"]), "y0": float(z["y0"])}
    hp, bp, tmp = _source(stamp)
    b = json.loads(bp.read_text())
    if b["id"] != stamp:
        raise SystemExit(f"terrain_held: {bp} is build {b['id']}, not {stamp}")
    if hashlib.sha256(hp.read_bytes()).hexdigest() != b["sha256"]:
        raise SystemExit(f"terrain_held: {hp} is not build {stamp}'s heightmap (sha256 differs from its build.json); "
                         f"delete {hp.parent} if it is a broken download and run again")
    H = np.load(hp, mmap_mode="r")
    j0, j1 = int(round((x0 - b["origin_world_x"]) / STEP)), int(round((x1 - b["origin_world_x"]) / STEP))
    i0, i1 = int(round((b["origin_world_y"] - y1) / STEP)), int(round((b["origin_world_y"] - y0) / STEP))
    i0, j0 = max(i0, 0), max(j0, 0)
    h = np.array(H[i0:i1 + 1, j0:j1 + 1], np.float32)
    if not h.size:
        raise SystemExit(f"terrain_held: {pid}'s cells lie outside build {stamp}")
    px0, py0 = b["origin_world_x"] + j0 * STEP, b["origin_world_y"] - i0 * STEP
    STORE.mkdir(parents=True, exist_ok=True)
    part = fn.with_suffix(".part.npz")          # written whole, then renamed: an interrupted cut leaves no patch
    np.savez(part, h=h, x0=px0, y0=py0, stamp=stamp)
    os.replace(part, fn)
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


def ramp_units(L: float) -> float:
    """How far from the old waterline (units) the lift is whole. The lift follows a smoothstep, whose steepest grade
    is 1.5 L over its length; the length is the shortest that keeps the ramp's rise from one sample to the next
    under one LAND step (QUANT), so two neighbouring samples never differ by more than one step of added height and
    no triangle gains more than RAMP_ADDED_DEG (one step along each side: atan(8 x 1.414 / 128) = 5.05 degrees).
    For 72 units that is 1745 units, 24.9 m; an islet or spit narrower than twice that never takes the whole lift."""
    return 1.5 * L * STEP / QUANT * 1.01


RAMP_ADDED_DEG = 5.06


def ramp(old: np.ndarray, L: float) -> np.ndarray:
    """The lift (units, on LAND's step) of every sample of the old ground: 0 in the water and at the waterline,
    rising without a kink to L at ramp_units(L) from the old waterline (distance from the nearest old water sample,
    less the half sample to the waterline)."""
    land = old > 0
    if L <= 0:
        return np.zeros(old.shape, np.float32)
    if land.all():
        return np.where(land, L, 0).astype(np.float32)
    d = np.maximum(ndi.distance_transform_edt(land) * STEP - STEP / 2, 0)
    t = np.clip(d / ramp_units(L), 0, 1)
    return np.where(land, np.round(L * t * t * (3 - 2 * t) / QUANT) * QUANT, 0).astype(np.float32)


def held_ground(p: dict, L: float) -> np.ndarray:
    """The held heights on the whole patch: the old beds exactly (a built place's wading routes, piers and stilts
    were fitted to them), the old land plus the ramped lift."""
    return (p["h"] + ramp(p["h"], L)).astype(np.float32)


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
        old = held_ground(p, L)[ps]
        mix = w * old + (1 - w) * new
        ring = (w > 0) & (w < 1)
        mix = np.where(ring, np.round(mix / QUANT) * QUANT, mix)
        ws = water_s[gs]
        mix = np.where(ring & ws & (mix > -QUANT), -QUANT, mix)
        mix = np.where(ring & ~ws & (mix < QUANT), QUANT, mix)
        h[gs] = np.where(w >= 1, old, mix).astype(h.dtype)
        out[pid] = {"terrain_build": rec["terrain_build"], "lift_units": L, "ramp_m": round(ramp_units(L) / U, 1),
                    "held_samples": int((w >= 1).sum()), "blend_samples": int(ring.sum()), "margin_m": MARGIN_M,
                    "blend_m": BLEND_M}
    return out


def zone_mask(grid, shape, blend: bool = True) -> np.ndarray:
    """The samples of every held zone (with its blend ring when `blend`)."""
    out = np.zeros(shape, bool)
    for pid, rec in rows().items():
        p = patch(pid, rec)
        win = _window(grid, p)
        if win is not None:
            w = weight(rec, p)[win[1]]
            out[win[0]] |= (w > 0) if blend else (w >= 1)
    return out


def check(h: np.ndarray, grid) -> dict:
    """Per built place, inside its zone: water samples against the held build (largest difference, must be 0); land
    samples against the held build plus the ramped lift (must be 0); samples whose side of the waterline changed
    (0); the share of waterline triangles steeper than the navmesh walks, in the held build and now (no higher
    now); and the most any land triangle steepened (at most RAMP_ADDED_DEG)."""
    from tools.newworld import terrain_clearance as tcl
    out = {}
    for pid, rec in rows().items():
        p = patch(pid, rec)
        win = _window(grid, p)
        if win is None:
            out[pid] = {"max_diff_units": None, "note": "outside the grid"}
            continue
        gs, ps = win
        wfull = weight(rec, p)
        inside = wfull[ps] >= 1
        L = lift(rec, p)
        old = p["h"][ps].astype(np.float64)
        want = held_ground(p, L)[ps].astype(np.float64)
        new = np.asarray(h[gs], np.float64)
        land = old > 0
        dl = np.abs(new - want)[inside & land]
        dw = np.abs(new - old)[inside & ~land]
        so, sn = tcl.shore_steep(old, inside), tcl.shore_steep(new, inside)
        added = 0.0
        for a, b in zip(tcl.triangle_slopes(old), tcl.triangle_slopes(new)):
            q = (inside & land)[:-1, :-1] & (inside & land)[:-1, 1:] & (inside & land)[1:, :-1] & (inside & land)[1:, 1:]
            if q.any():
                added = max(added, float((b - a)[q].max()))
        out[pid] = {"terrain_build": rec["terrain_build"], "samples": int(inside.sum()),
                    "zone_samples_in_grid": f"{int(inside.sum())} of {int((wfull >= 1).sum())}", "lift_units": L,
                    "ramp_m": round(ramp_units(L) / U, 1),
                    "max_diff_units": float(dl.max()) if dl.size else None,
                    "water_max_diff_units": float(dw.max()) if dw.size else 0.0,
                    "waterline_moved": int((((new > 0) != land) & inside).sum()),
                    "shore_over_walk_held_build": so["over_walk"], "shore_over_walk": sn["over_walk"],
                    "shore_median_deg_held_build": so["median_deg"], "shore_median_deg": sn["median_deg"],
                    "land_triangle_steepened_max_deg": round(added, 2)}
    return out


def ok(res: dict) -> bool:
    return all(r.get("max_diff_units") == 0.0 and r["samples"] > 0 and r.get("water_max_diff_units") == 0.0
               and not r.get("waterline_moved") and r["shore_over_walk"] <= r["shore_over_walk_held_build"]
               and r["land_triangle_steepened_max_deg"] <= RAMP_ADDED_DEG for r in res.values())


if __name__ == "__main__":
    from tools.newworld import terrain_needs as tn
    tdir = Path(sys.argv[2]) if len(sys.argv) > 2 else f.OUT / "terrain"
    b = json.loads((tdir / "build.json").read_text())
    res = check(np.load(tdir / "heightmap.npy"), tn.grid_of(b))
    print(json.dumps(res, indent=1))
    sys.exit(0 if ok(res) else 1)
