"""Generate every cell's LAND intermediate, one row of cells at a time (2.W1 §a, §b).

For each row of cells (Skyrim cy) the builder reads a window of grid rows with a halo, quantises and limits the
heights (quantize.py), computes normals from the limited heights across cell edges, paints the ground's material
into quadrant layers and the water-band shade into vertex colours (material.py), and writes one JSON line per cell to
`<out>/land/cy<+NNN>.jsonl.gz` (gzip with no timestamp, so the bytes are stable). Nothing whole-grid is held.

A cell line (the LAND contract for ArgoniaGen's Land.cs; every array base64, [y][x] with y from the south):
    {"x", "y", "cell": FormKey, "land": FormKey, "offset": float steps,
     "vhgt": 1089 int8, "vnml": 1089 x 3 int8, "vclr": 1089 x 3 uint8,
     "quads": [{"q": Quadrant name, "base": LTEX FormKey, "layers": [{"ltex": FormKey, "alpha": 289 uint8}]}]}
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import multiprocessing as mp
import os
import pickle
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import material as M
from tools.argonia_world.terrain import quantize
from tools.argonia_world.terrain.grid import Sources

V = su.LAND_VERTS
QV = su.QUADRANT_VERTS
APRON_MIN_M = -2.0  # an apron cell entirely deeper than this is open sea under the default water: no LAND
LAND_PLUGIN = "ArgoniaWorld.esm"  # the generated ground's own master (decision 0031)
LIMIT_BUCKETS_M = (0.5, 2.0, 5.0, 10.0)  # the overflow survey's histogram of limiter moves


@dataclass
class Stats:
    cells: int = 0
    province_cells: int = 0
    apron_cells: int = 0
    apron_skipped: int = 0
    overflow_pairs: int = 0  # raw quantised 4-neighbour steps beyond a signed byte (cell interiors and edges)
    limited_vertices: int = 0  # vertices the limiter moved
    max_limit_m: float = 0.0  # the largest height change the limiter made
    max_limit_province_m: float = 0.0
    overflow_cells: int = 0  # cells with at least one raw overflowing pair inside or on their edges
    overflow_at: list = field(default_factory=list)  # the first 20 such cells (cx, cy)
    overflow_max_step_m: float = 0.0  # the steepest raw neighbour step
    limit_hist_province: dict = field(default_factory=dict)  # province vertices moved by more than N m -> count
    layers_hist: dict = field(default_factory=dict)  # alpha layers per quadrant -> count
    seconds: float = 0.0

    def add_layers(self, n: int) -> None:
        self.layers_hist[n] = self.layers_hist.get(n, 0) + 1

    def merge(self, o: "Stats") -> None:
        """Fold another worker's stats in: counters add, maxima take the max, histograms add per bucket."""
        for k, v in o.__dict__.items():
            if k == "seconds":
                continue
            if isinstance(v, dict):
                d = getattr(self, k)
                for i, n in v.items():
                    d[i] = d.get(i, 0) + n
            elif k.startswith("max_") or k.endswith("_max_step_m"):
                setattr(self, k, max(getattr(self, k), v))
            else:
                setattr(self, k, (getattr(self, k) + v)[:20] if k == "overflow_at" else getattr(self, k) + v)


def b64(a: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")


def form_key(base: int, k: int, plugin: str) -> str:
    return f"{base + k:06X}:{plugin}"


class Builder:
    def __init__(self, src: Sources, mat=None, plugin: str = LAND_PLUGIN,
                 formid_base: int = su.FORMID_FIRST + 0x10):
        self.src, self.plugin, self.base = src, plugin, formid_base
        self.mat = mat if isinstance(mat, M.Material) else default_material(src)
        self.ltex = [t.form_key for t in M.TEXTURES]
        self.stats = Stats()
        gx0, gy0, gx1, _ = src.cell_range
        self.gx0, self.gy0, self.gw = gx0, gy0, gx1 - gx0 + 1

    def keys(self, cx: int, cy: int) -> tuple[str, str]:
        k = 2 * ((cy - self.gy0) * self.gw + (cx - self.gx0))
        return form_key(self.base, k, self.plugin), form_key(self.base, k + 1, self.plugin)

    def row(self, cy: int, x0: int, x1: int):
        """Yield the cell dicts of row cy, cells x0..x1 inclusive."""
        src, size, H = self.src, self.src.size, quantize.HALO
        north, south = src.cell_rows(cy)
        c_lo, _ = src.cell_cols(x0)
        _, c_hi = src.cell_cols(x1)
        r0, r1 = max(north - H, 0), min(south + H + 1, size)
        c0, c1 = max(c_lo - H, 0), min(c_hi + H + 1, size)
        h = src.heights(r0, r1, c0, c1)
        steps = np.rint(su.height_to_steps(h)).astype(np.int64)
        lim = quantize.limit(steps)
        # stats over this row's own vertices (its south edge row is the next row's north edge: count rows once)
        own = (slice(north - r0, south - r0 + (1 if cy == src.cell_range[1] else 0)), slice(c_lo - c0, c_hi - c0 + 1))
        moved = np.abs(lim - steps)[own]
        s = self.stats
        s.limited_vertices += int((moved > 0).sum())
        if moved.size:
            s.max_limit_m = max(s.max_limit_m, float(moved.max()) * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE)
        blk = steps[north - r0:south - r0 + 1, c_lo - c0:c_hi - c0 + 1]  # rows north..south, every column
        last = cy == src.cell_range[1]
        s.overflow_pairs += int((np.abs(np.diff(blk if last else blk[:-1], axis=1)) > quantize.L).sum())
        s.overflow_pairs += int((np.abs(np.diff(blk, axis=0)) > quantize.L).sum())
        # normals from the limited heights (units), central differences across cell edges
        z = lim.astype(np.float64) * su.VHGT_STEP_UNITS
        gr, gc = np.gradient(z, su.VERTEX_SPACING_UNITS)
        nx, ny, nz = -gc, gr, np.ones_like(z)  # x east; y north = -row; d/dy = -d/drow
        norm = np.sqrt(nx * nx + ny * ny + nz * nz)
        nrm = np.stack([nx, ny, nz], axis=-1) / norm[..., None]
        nrm8 = np.clip(np.rint(nrm * su.VNML_SCALE), -su.VNML_SCALE, su.VNML_SCALE).astype(np.int8)
        # material: weights over the row plus one quadrant each side, so the seam fix sees every neighbour
        wq, keep = self.material_row(north, south, c_lo, c_hi)
        win = self.mat.window(north, south + 1, c_lo, c_hi + 1)
        tint = M.vclr(win)  # white but near water: the old ground tint is not how Skyrim.esm colours (audit §4, p50 255)
        for cx in range(x0, x1 + 1):
            a, b = src.cell_cols(cx)
            inside = src.in_province(cx, cy)
            hm = h[north - r0:south - r0 + 1, a - c0:b - c0 + 1]
            if not inside and hm.max() < APRON_MIN_M:
                s.apron_skipped += 1
                continue
            cell = lim[north - r0:south - r0 + 1, a - c0:b - c0 + 1][::-1]  # [y from south, x]
            raw = steps[north - r0:south - r0 + 1, a - c0:b - c0 + 1]
            if quantize.overflow_pairs(raw):
                s.overflow_cells += 1
                s.overflow_at = (s.overflow_at + [[cx, cy]])[:20]
                s.overflow_max_step_m = max(s.overflow_max_step_m, max(
                    float(np.abs(np.diff(raw, axis=1)).max()), float(np.abs(np.diff(raw, axis=0)).max()))
                    * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE)
            offset, d = quantize.encode(cell)
            vn = nrm8[north - r0:south - r0 + 1, a - c0:b - c0 + 1][::-1]
            vc = tint[:, a - c_lo:b - c_lo + 1][::-1]
            quads = []
            for qi, qname in enumerate(su.QUADRANTS):
                qy, qx = divmod(qi, 2)  # qy 0 = the south half: grid quadrant row 2 (north halo, north, south)
                gi, gj = 2 - qy, 1 + 2 * ((a - c_lo) // (V - 1)) + qx
                q = wq[gi * (QV - 1):gi * (QV - 1) + QV, gj * (QV - 1):gj * (QV - 1) + QV][::-1]
                base, layers = M.quadrant_layers(q, keep[gi][gj])
                s.add_layers(len(layers))
                quads.append({"q": qname, "base": self.ltex[base],
                              "layers": [{"ltex": self.ltex[i], "alpha": b64(al)} for i, al in layers]})
            ck, lk = self.keys(cx, cy)
            s.cells += 1
            if inside:
                s.province_cells += 1
                mv = np.abs(cell - raw[::-1]) * (su.VHGT_STEP_UNITS / su.UNITS_PER_METRE)
                s.max_limit_province_m = max(s.max_limit_province_m, float(mv.max()))
                for t in LIMIT_BUCKETS_M:
                    s.limit_hist_province[t] = s.limit_hist_province.get(t, 0) + int((mv > t).sum())
            else:
                s.apron_cells += 1
            yield {"x": cx, "y": cy, "cell": ck, "land": lk, "offset": offset, "vhgt": b64(d),
                   "vnml": b64(vn), "vclr": b64(vc), "quads": quads}


    def material_row(self, north: int, south: int, c_lo: int, c_hi: int):
        """The row's weights with a one-quadrant halo (edge-padded at the grid's rim), seam-fixed."""
        size, H = self.src.size, M.QS
        r0, r1, c0, c1 = north - H, south + H + 1, c_lo - H, c_hi + H + 1
        a0, a1, b0, b1 = max(r0, 0), min(r1, size), max(c0, 0), min(c1, size)
        w = self.mat.window(a0, a1, b0, b1).weights
        w = np.pad(w, ((a0 - r0, r1 - a1), (b0 - c0, c1 - b1), (0, 0)), mode="edge")
        bare = np.pad(self.mat.apron(a0, a1, b0, b1), ((a0 - r0, r1 - a1), (b0 - c0, c1 - b1)), mode="edge")
        return M.quadrant_sets(w, bare=bare)  # the apron's quadrants keep their base alone (audit §9)


def default_material(src: Sources):
    """A material for a synthetic grid (tests): the sea as the only water, one region class."""
    return M.Material(src, M.Water.sea(src.pad, src.n), M.Regions.uniform("flooded-forest", src.pad, src.n),
                      roads=False)


def shard_name(cy: int) -> str:
    return f"cy{cy:+04d}.jsonl.gz"


def _atomic(path: Path, data: bytes) -> None:
    part = path.with_name(path.name + ".part")
    part.write_bytes(data)
    part.replace(path)


def write_row(b: Builder, boxes, land: Path, cy: int) -> Stats:
    """One row's shard (whole or absent) and its stats file; returns the row's stats."""
    spans = sorted({(bx[0], bx[2]) for bx in boxes if bx[1] <= cy <= bx[3]})
    keep, b.stats = b.stats, Stats()
    try:
        lines = [json.dumps(c, separators=(",", ":"), sort_keys=True) for x0, x1 in spans for c in b.row(cy, x0, x1)]
        st = b.stats
    finally:
        b.stats = keep
    if lines:
        part = land / (shard_name(cy) + ".part")
        with open(part, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as z:
            z.write(("\n".join(lines) + "\n").encode("ascii"))
        part.replace(land / shard_name(cy))
    _atomic(row_stats_path(land, cy), pickle.dumps((len(lines), st)))
    return st


def row_stats_path(land: Path, cy: int) -> Path:
    return land / "_stats" / f"{cy:+04d}.pkl"


def row_complete(land: Path, boxes, cy: int) -> Stats | None:
    """The stats of a finished row left by an interrupted build, or None: the shard reads to its end with the cell
    count its stats file recorded."""
    try:
        want, st = pickle.loads(row_stats_path(land, cy).read_bytes())
        n = 0
        if want:
            with gzip.open(land / shard_name(cy), "rt", encoding="ascii") as z:
                n = sum(1 for _ in z)
        return st if n == want else None
    except (OSError, EOFError, ValueError, pickle.UnpicklingError):
        return None


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


def code_stamp() -> str:
    """The terrain code the cell lines depend on (the files the pipeline's terrain stamp reads)."""
    h = hashlib.sha256()
    here = Path(__file__).parent
    for n in ("__main__.py", "build.py", "grid.py", "landcover.py", "material.py", "png.py", "place_ground.py",
              "quantize.py", "world.py"):
        h.update(n.encode() + (here / n).read_bytes())
    return h.hexdigest()


def _pid_alive(name: str) -> bool:
    tail = name.rsplit("-", 1)[-1]
    if not tail.isdigit():
        return False
    try:
        os.kill(int(tail), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def claim_tmp(out: Path, inputs: dict | None, mine: Path) -> bool:
    """Reuse an interrupted build's land.tmp-* directory whose inputs.json equals `inputs` (moved to `mine`); delete
    every other one that no live process owns. True when rows were inherited."""
    reused = False
    for d in sorted(out.glob("land.tmp-*")):
        try:
            same = inputs is not None and json.loads((d / "inputs.json").read_text()) == inputs
        except (OSError, ValueError):
            same = False
        if same and not reused:
            if d != mine:
                shutil.rmtree(mine, ignore_errors=True)
                d.rename(mine)
            reused = True
        elif d != mine and not _pid_alive(d.name):
            shutil.rmtree(d, ignore_errors=True)
    return reused


_WORKER: dict = {}


def _worker_init(factory, boxes, land, kw) -> None:
    src, mat = factory()  # this process's own memory maps and database connection
    _WORKER.update(b=Builder(src, mat, **kw), boxes=boxes, land=land)


def _worker_row(cy: int):
    return cy, write_row(_WORKER["b"], _WORKER["boxes"], _WORKER["land"], cy)


def build(src: Sources, mat, out: Path, cells=None, progress=None, jobs: int = 1, factory=None, inputs: dict | None = None,
          **kw) -> Stats:
    """Every cell of the grid, or of `cells`: one box (x0, y0, x1, y1) or a list of boxes (the gate's sample).
    jobs > 1 (0 = every CPU) splits the rows over forked workers, each calling `factory() -> (src, mat)` for its own
    sources; the files and stats are the single process's. `inputs`: what the rows depend on (terrain stamp, ground
    sha256, code stamp); an interrupted build's land.tmp-* with equal inputs.json is resumed, its finished rows kept."""
    t0 = time.time()
    b = Builder(src, mat, **kw)
    gx0, gy0, gx1, gy1 = src.cell_range
    boxes = [cells] if cells and isinstance(cells[0], int) else list(cells or [(gx0, gy0, gx1, gy1)])
    for x0, y0, x1, y1 in boxes:
        if not (gx0 <= x0 <= x1 <= gx1 and gy0 <= y0 <= y1 <= gy1):
            raise ValueError(f"cells {x0},{y0},{x1},{y1} outside the grid {gx0},{gy0},{gx1},{gy1}")
    final = out / "land"
    land = out / f"land.tmp-{os.getpid()}"  # rows go here; the old land stays whole until they are all written
    if inputs is not None:
        inputs = {**inputs, "cells": [list(bx) for bx in boxes]}
    reused = claim_tmp(out, inputs, land)
    if not reused:
        shutil.rmtree(land, ignore_errors=True)
    (land / "_stats").mkdir(parents=True, exist_ok=True)
    if inputs is not None:
        _atomic(land / "inputs.json", json.dumps(inputs, sort_keys=True).encode())
    rows = list(range(max(bx[3] for bx in boxes), min(bx[1] for bx in boxes) - 1, -1))  # north to south: the
    # grid's row order, so the memory maps read forward
    done = {cy: st for cy in rows if reused and (st := row_complete(land, boxes, cy)) is not None}
    todo = [cy for cy in rows if cy not in done]
    for cy in todo:  # a partial or stale row goes
        for q in (land / shard_name(cy), land / (shard_name(cy) + ".part"), row_stats_path(land, cy)):
            q.unlink(missing_ok=True)
    if done:
        print(f"  resuming {land.name}: {len(done)} of {len(rows)} rows kept", flush=True)
    jobs = max(1, min(jobs if jobs else (os.cpu_count() or 1), len(todo) or 1))
    if jobs > 1 and factory is None:
        jobs = 1
    try:
        if jobs == 1:
            for cy in rows:
                b.stats.merge(done[cy] if cy in done else write_row(b, boxes, land, cy))
                if progress:
                    progress(cy, b.stats)
        else:
            ctx = mp.get_context("fork")
            with ctx.Pool(jobs, initializer=_worker_init, initargs=(factory, boxes, land, kw)) as pool:
                it = pool.imap(_worker_row, todo)  # in row order; each worker holds its own maps
                for cy in rows:
                    b.stats.merge(done[cy] if cy in done else next(it)[1])
                    if progress:
                        progress(cy, b.stats)
    except BaseException:
        shutil.rmtree(land, ignore_errors=True)
        raise
    shutil.rmtree(land / "_stats", ignore_errors=True)
    (land / "inputs.json").unlink(missing_ok=True)
    old = out / f"land.old-{os.getpid()}"
    if final.exists():
        final.rename(old)
    land.rename(final)
    shutil.rmtree(old, ignore_errors=True)
    b.stats.seconds = round(time.time() - t0, 1)
    return b.stats


def read_cells(out: Path):
    """Stream every cell line back (the checks and tests read the files the writer reads)."""
    for p in sorted((out / "land").glob("cy*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="ascii") as f:
            for line in f:
                yield json.loads(line)


def unpack(cell: dict) -> dict:
    """A cell line's arrays as numpy: vhgt (33,33) int8, vnml (33,33,3) int8, vclr (33,33,3) uint8."""
    def arr(k, dt, shape):
        return np.frombuffer(base64.b64decode(cell[k]), dtype=dt).reshape(shape)
    return {"vhgt": arr("vhgt", np.int8, (V, V)), "vnml": arr("vnml", np.int8, (V, V, 3)),
            "vclr": arr("vclr", np.uint8, (V, V, 3))}


def game_heights_m(src: Sources, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
    """The ground as the game will have it (quantised and limited, the LAND's vertices) in metres, for grid rows
    [r0, r1) and columns [c0, c1): the same numbers the cells carry, for any window (2.W2's water checks)."""
    H, size = quantize.HALO, src.size
    a0, a1, b0, b1 = max(r0 - H, 0), min(r1 + H, size), max(c0 - H, 0), min(c1 + H, size)
    steps = np.rint(su.height_to_steps(src.heights(a0, a1, b0, b1))).astype(np.int64)
    lim = quantize.limit(steps)[r0 - a0:r1 - a0, c0 - b0:c1 - b0]
    return lim * (su.VHGT_STEP_UNITS / su.UNITS_PER_METRE)
