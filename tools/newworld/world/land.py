"""The new world's LAND shards from the terrain build: VHGT (limited to signed-byte steps), VNML, the start marker.

    python3 -m tools.newworld.world.land [--terrain out/newworld/terrain] [--out out/newworld/plugin]

Reads the current terrain build (build.json + heightmap.npy; its id is the stamp), quantises the heights to 8-unit
steps, limits every neighbour step to +-127 over the whole grid at once (quantize.limit: no seam by construction),
computes the normals from the limited heights across cell edges (central differences, the CK's smooth normals),
and writes one shard per cell row, `<out>/land/cy<+NNN>.bin`, each cell in x order as
    float32 offset (steps) | 1089 int8 VHGT deltas [y from the south][x] | 1089 x 3 int8 VNML [y][x][xyz]
then `<out>/land/manifest.json` (grid, build id, heightmap sha256, limiter stats, the ArgoniaNWStart marker).
Interrupt-proof: the limited grid and every shard are written atomically and keyed on the build id + this code's
hash; a rerun keeps what matches and writes the rest, a new terrain build rewrites everything.
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

from tools.newworld.world import quantize
from tools.newworld.world import units as su

REPO = Path(__file__).resolve().parents[3]
PLACES = REPO / "newworld/story/data/db/place.jsonl"
START_PLACE = "stormhold"
CELL_BYTES = 4 + su.LAND_VERTS ** 2 * 4  # offset + VHGT + VNML


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def _atomic(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def code_key() -> str:
    h = hashlib.sha256()
    for f in ("land.py", "quantize.py", "units.py"):
        h.update((Path(__file__).parent / f).read_bytes())
    return h.hexdigest()[:16]


def shard_name(cy: int) -> str:
    return f"cy{cy:+04d}.bin"


def normals(lim: np.ndarray) -> np.ndarray:
    """Unit normals x 127 as int8 [row, col, xyz] from limited steps; x east, y north (= -row)."""
    z = lim.astype(np.float32) * su.VHGT_STEP_UNITS
    gr, gc = np.gradient(z, float(su.VERTEX_SPACING_UNITS))
    del z
    nx, ny = -gc, gr
    norm = np.sqrt(nx * nx + ny * ny + 1.0)
    out = np.empty(lim.shape + (3,), np.int8)
    for k, a in enumerate((nx, ny, np.ones_like(nx))):
        out[..., k] = np.clip(np.rint(a / norm * su.VNML_SCALE), -su.VNML_SCALE, su.VNML_SCALE)
    return out


def row_bytes(g: su.Grid, lim: np.ndarray, nrm: np.ndarray, cy: int) -> bytes:
    north, south = g.cell_rows(cy)
    parts = []
    for cx in range(g.cx0, g.cx0 + g.cells_x):
        a, b = g.cell_cols(cx)
        cell = lim[north:south + 1, a:b + 1][::-1]  # [y from the south, x]
        offset, d = quantize.encode(cell)
        parts += [np.float32(offset).tobytes(), d.tobytes(), np.ascontiguousarray(nrm[north:south + 1, a:b + 1][::-1]).tobytes()]
    data = b"".join(parts)
    assert len(data) == g.cells_x * CELL_BYTES
    return data


def start_marker(g: su.Grid, h: np.ndarray) -> dict:
    """A dry, gentle spot just outside the start place's footprint, facing its centre."""
    p = next(json.loads(ln) for ln in PLACES.read_text().splitlines() if ln.strip() and json.loads(ln)["id"] == START_PLACE)
    col = (p["world_x"] - g.origin_x) / su.VERTEX_SPACING_UNITS
    row = (g.origin_y - p["world_y"]) / su.VERTEX_SPACING_UNITS
    r_min = (p.get("footprint_radius_m") or 60.0) * su.UNITS_PER_METRE / su.VERTEX_SPACING_UNITS + 2
    R = int(r_min) + 60
    r0, c0 = int(row) - R, int(col) - R
    win = h[max(r0, 1):r0 + 2 * R, max(c0, 1):c0 + 2 * R].astype(np.float64)
    rr, cc = np.mgrid[max(r0, 1):r0 + 2 * R, max(c0, 1):c0 + 2 * R]
    slope = np.zeros_like(win)
    slope[1:-1, 1:-1] = np.maximum(np.abs(win[2:, 1:-1] - win[:-2, 1:-1]), np.abs(win[1:-1, 2:] - win[1:-1, :-2])) / 2
    dist = np.hypot(rr - row, cc - col)
    ok = (win > g.water + 2 * su.UNITS_PER_METRE) & (slope < 32) & (dist >= r_min)
    ok[[0, -1], :] = ok[:, [0, -1]] = False
    if not ok.any():
        raise RuntimeError(f"no dry gentle ground within {R} samples of {START_PLACE}")
    k = np.argmin(np.where(ok, dist, np.inf))
    r, c = int(rr.flat[k]), int(cc.flat[k])
    x = g.origin_x + c * su.VERTEX_SPACING_UNITS
    y = g.origin_y - r * su.VERTEX_SPACING_UNITS
    heading = math.atan2(p["world_x"] - x, p["world_y"] - y)  # radians clockwise from north, toward the centre
    return {"place": START_PLACE, "x": x, "y": y, "z": float(h[r, c]) + 16.0, "rot_z": heading,
            "cell": [int(x // su.CELL_UNITS), int(y // su.CELL_UNITS)], "sample": [r, c]}


def build(terrain: Path, out: Path) -> dict:
    src = out / "source"  # a snapshot: the terrain agents may rewrite out/newworld/terrain while this runs
    src.mkdir(parents=True, exist_ok=True)
    cur = json.loads((terrain / "build.json").read_text())["id"]
    have = json.loads((src / "build.json").read_text())["id"] if (src / "build.json").exists() else None
    if have != cur or not (src / "heightmap.npy").exists():
        import shutil
        shutil.copyfile(terrain / "heightmap.npy", src / "heightmap.tmp.npy")
        shutil.copyfile(terrain / "build.json", src / "build.tmp.json")
        os.replace(src / "heightmap.tmp.npy", src / "heightmap.npy")
        os.replace(src / "build.tmp.json", src / "build.json")
    g = su.load_grid(src / "build.json")
    hm_path = src / "heightmap.npy"
    land = out / "land"
    land.mkdir(parents=True, exist_ok=True)
    hm_sha = sha256_file(hm_path)
    key = f"{g.build_id}:{hm_sha[:16]}:{code_key()}"
    man_path = land / "manifest.json"
    old = json.loads(man_path.read_text()) if man_path.exists() else {}
    keyf = land / "key.txt"
    if (keyf.read_text() if keyf.exists() else "") != key:  # another build or code: start over
        for f in land.iterdir():
            f.unlink()
        _atomic(keyf, key.encode())
        old = {}
    h = np.load(hm_path, mmap_mode="r")
    if h.shape != (g.height, g.width):
        raise ValueError(f"heightmap {h.shape} != build.json {g.height} x {g.width}")
    lim_path = land / "limited.npy"
    if lim_path.exists():
        lim = np.load(lim_path)
        stats = old.get("stats") or json.loads((land / "limit_stats.json").read_text())
    else:
        log(f"limit: {g.build_id} {g.width} x {g.height}")
        steps = np.rint(np.asarray(h, np.float64) / su.VHGT_STEP_UNITS).astype(np.int64)
        off_plane = quantize.off_plane(steps, h, g.water, su.VHGT_STEP_UNITS)
        before = quantize.overflow_pairs(steps)
        lim64 = quantize.limit(steps)
        moved = np.abs(lim64 - steps)
        stats = {"overflow_pairs_before": before, "overflow_pairs_after": quantize.overflow_pairs(lim64),
                 "off_plane_moved": off_plane, "on_plane_after": int((lim64 * su.VHGT_STEP_UNITS == g.water).sum()),
                 "limited_vertices": int((moved > 0).sum()),
                 "max_limit_move_units": int(moved.max()) * su.VHGT_STEP_UNITS,
                 "min_height_units": float(np.min(h)), "max_height_units": float(np.max(h))}
        del steps, moved
        lim = lim64.astype(np.int32)
        del lim64
        _atomic(land / "limit_stats.json", json.dumps(stats).encode())
        tmp = land / "limited.tmp.npy"
        np.save(tmp, lim)
        os.replace(tmp, lim_path)
    if stats["overflow_pairs_after"]:
        raise RuntimeError(f"{stats['overflow_pairs_after']} steps still overflow after the limiter")
    nrm = None
    rows = range(g.cy_top, g.cy_bottom - 1, -1)
    for cy in rows:
        p = land / shard_name(cy)
        if p.exists() and p.stat().st_size == g.cells_x * CELL_BYTES:
            continue
        if nrm is None:
            log("normals")
            nrm = normals(lim)
        _atomic(p, row_bytes(g, lim, nrm, cy))
    marker = start_marker(g, h)
    man = {"key": key, "build_id": g.build_id, "heightmap": str(hm_path.resolve()), "heightmap_sha256": hm_sha,
           "grid": g.to_dict(), "cell_bytes": CELL_BYTES, "shards": [shard_name(cy) for cy in rows], "stats": stats,
           "marker": marker}
    _atomic(man_path, json.dumps(man, indent=1).encode())
    log(f"land: {len(man['shards'])} rows x {g.cells_x} cells, stats {stats}, marker {marker}")
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--terrain", type=Path, default=REPO / "out/newworld/terrain")
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    a = ap.parse_args(argv)
    build(a.terrain, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
