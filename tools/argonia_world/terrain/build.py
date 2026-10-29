"""Generate every cell's LAND intermediate, one row of cells at a time (2.W1 §a, §b).

For each row of cells (Skyrim cy) the builder reads a window of grid rows with a halo, quantises and limits the
heights (quantize.py), computes normals from the limited heights across cell edges, paints the land-cover classes
into quadrant layers (paint.py) and the tint into vertex colours, and writes one JSON line per cell to
`<out>/land/cy<+NNN>.jsonl.gz` (gzip with no timestamp, so the bytes are stable). Nothing whole-grid is held.

A cell line (the LAND contract for ArgoniaGen's Land.cs; every array base64, [y][x] with y from the south):
    {"x", "y", "cell": FormKey, "land": FormKey, "offset": float steps,
     "vhgt": 1089 int8, "vnml": 1089 x 3 int8, "vclr": 1089 x 3 uint8,
     "quads": [{"q": Quadrant name, "base": LTEX FormKey, "layers": [{"ltex": FormKey, "alpha": 289 uint8}]}]}
"""
from __future__ import annotations

import base64
import gzip
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.terrain import paint, quantize
from tools.argonia_world.terrain.grid import Sources
from tools.argonia_world.terrain.landcover import Cover

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
    overflow_max_step_m: float = 0.0  # the steepest raw neighbour step
    limit_hist_province: dict = field(default_factory=dict)  # province vertices moved by more than N m -> count
    layers_hist: dict = field(default_factory=dict)  # alpha layers per quadrant -> count
    seconds: float = 0.0

    def add_layers(self, n: int) -> None:
        self.layers_hist[n] = self.layers_hist.get(n, 0) + 1


def b64(a: np.ndarray) -> str:
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode("ascii")


def form_key(base: int, k: int, plugin: str) -> str:
    return f"{base + k:06X}:{plugin}"


class Builder:
    def __init__(self, src: Sources, covers: dict[int, Cover], plugin: str = LAND_PLUGIN,
                 formid_base: int = su.FORMID_FIRST + 0x10):
        self.src, self.plugin, self.base = src, plugin, formid_base
        self.ltex = sorted({c.ltex for c in covers.values()})
        index = {fk: i for i, fk in enumerate(self.ltex)}
        self.lut = np.full(max(covers) + 1, -1, dtype=np.int16)
        for c in covers.values():
            self.lut[c.id] = index[c.ltex]
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
        # classes (one-sample border for the box filter) and tint
        k0, k1 = max(north - 1, 0), min(south + 2, size)
        j0, j1 = max(c_lo - 1, 0), min(c_hi + 2, size)
        cls = src.classes(k0, k1, j0, j1, h[k0 - r0:k1 - r0, j0 - c0:j1 - c0])
        lt = self.lut[cls]
        if (lt < 0).any():
            bad = sorted(set(cls[lt < 0].tolist()))
            raise ValueError(f"row {cy}: land-cover class(es) {bad} have no LTEX")
        lt = np.pad(lt, ((k0 - (north - 1), south + 2 - k1), (j0 - (c_lo - 1), c_hi + 2 - j1)), mode="edge")
        w = paint.weights(lt, len(self.ltex))  # rows north..south, cols c_lo..c_hi
        tint = src.tint_rgb(north, south + 1, c_lo, c_hi + 1)
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
                s.overflow_max_step_m = max(s.overflow_max_step_m, max(
                    float(np.abs(np.diff(raw, axis=1)).max()), float(np.abs(np.diff(raw, axis=0)).max()))
                    * su.VHGT_STEP_UNITS / su.UNITS_PER_METRE)
            offset, d = quantize.encode(cell)
            vn = nrm8[north - r0:south - r0 + 1, a - c0:b - c0 + 1][::-1]
            vc = tint[:, a - c_lo:b - c_lo + 1][::-1]
            wc = w[:, a - c_lo:b - c_lo + 1][::-1]
            quads = []
            for qi, qname in enumerate(su.QUADRANTS):
                qy, qx = divmod(qi, 2)
                wq = wc[qy * (QV - 1):qy * (QV - 1) + QV, qx * (QV - 1):qx * (QV - 1) + QV]
                base, layers = paint.quadrant_layers(wq)
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


def shard_name(cy: int) -> str:
    return f"cy{cy:+04d}.jsonl.gz"


def build(src: Sources, covers: dict[int, Cover], out: Path, cells=None, progress=None, **kw) -> Stats:
    """Every cell of the grid, or of `cells`: one box (x0, y0, x1, y1) or a list of boxes (the gate's sample)."""
    t0 = time.time()
    b = Builder(src, covers, **kw)
    gx0, gy0, gx1, gy1 = src.cell_range
    boxes = [cells] if cells and isinstance(cells[0], int) else list(cells or [(gx0, gy0, gx1, gy1)])
    for x0, y0, x1, y1 in boxes:
        if not (gx0 <= x0 <= x1 <= gx1 and gy0 <= y0 <= y1 <= gy1):
            raise ValueError(f"cells {x0},{y0},{x1},{y1} outside the grid {gx0},{gy0},{gx1},{gy1}")
    land = out / "land"
    land.mkdir(parents=True, exist_ok=True)
    for old in land.glob("cy*.jsonl.gz"):
        old.unlink()
    for cy in range(max(bx[3] for bx in boxes), min(bx[1] for bx in boxes) - 1, -1):  # north to south: the
        # grid's row order, so the memory maps read forward
        spans = sorted({(bx[0], bx[2]) for bx in boxes if bx[1] <= cy <= bx[3]})
        lines = [json.dumps(c, separators=(",", ":"), sort_keys=True) for x0, x1 in spans for c in b.row(cy, x0, x1)]
        if lines:
            with open(land / shard_name(cy), "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, filename="") as z:
                z.write(("\n".join(lines) + "\n").encode("ascii"))
        if progress:
            progress(cy, b.stats)
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
