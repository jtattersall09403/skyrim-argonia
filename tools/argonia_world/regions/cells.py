"""Per-cell measurements of the province (2.W3): the fields the ecological classifier reads, one row per exterior
cell, computed in bands of one cell row from memory-mapped arrays (memory guidance: nothing whole-province held).

Inputs (all in `$ARGONIA_DATA`, never committed): the 2.W1 ground (`terrain/refined-height-f32.npy`), the land-cover
raster (`terrain/landcover-i16.npy`) and the frozen hydrology bodies (`hydrology-graph-bodies.npz`: `sea`,
`marshy`, `level`). Province space: row 0 the north edge, column 0 the west edge, one sample per LAND vertex.

    features(root) -> dict of arrays shaped (126, 126), indexed [j, i]: j the cell row from the NORTH, i from the west
"""
from __future__ import annotations

import os
from pathlib import Path

from tools.argonia_world import skyrim_units as su

Q = su.QUADS_PER_CELL
NC = su.PROVINCE_CELLS
N_COVER = 38  # land-cover ids 0..37 (landcover.SEED)


def data_root() -> Path:
    return Path(os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data")))


def cell_of_index(i: int, j: int) -> tuple[int, int]:
    """Cell grid coordinate of the cell in column i (from the west) and row j (from the north)."""
    x0, y0 = su.PROVINCE_CELL_SW
    return x0 + i, y0 + (NC - 1 - j)


def features(root: Path | None = None) -> dict:
    import numpy as np

    r = root or data_root()
    h = np.load(r / "terrain" / "refined-height-f32.npy", mmap_mode="r")
    cov = np.load(r / "terrain" / "landcover-i16.npy", mmap_mode="r")
    bodies = np.load(r / "hydrology-graph-bodies.npz")
    sea, marshy, level = bodies["sea"], bodies["marshy"], bodies["level"]
    out = {k: np.zeros((NC, NC), np.float32) for k in ("height", "height_max", "slope", "sea", "marsh", "water")}
    out["cover"] = np.zeros((NC, NC, N_COVER), np.float32)
    for j in range(NC):
        r0, r1 = j * Q, j * Q + Q + 1
        hb = np.asarray(h[r0:r1, :], dtype=np.float64)
        gy, gx = np.gradient(hb, su.PROVINCE_SAMPLE_M)
        sl = np.degrees(np.arctan(np.hypot(gx, gy)))[:Q, :NC * Q]
        hb = hb[:Q, :NC * Q]
        cb = np.asarray(cov[r0:r0 + Q, :NC * Q])
        sb = np.asarray(sea[r0:r0 + Q, :NC * Q])
        mb = np.asarray(marshy[r0:r0 + Q, :NC * Q])
        lb = np.asarray(level[r0:r0 + Q, :NC * Q])
        wet = (lb > hb + 0.05) & ~sb
        blk = lambda a: a.reshape(Q, NC, Q).swapaxes(0, 1).reshape(NC, Q * Q)  # noqa: E731
        out["height"][j] = blk(hb).mean(1)
        out["height_max"][j] = blk(hb).max(1)
        out["slope"][j] = blk(sl).mean(1)
        out["sea"][j] = blk(sb).mean(1)
        out["marsh"][j] = blk(mb).mean(1)
        out["water"][j] = blk(wet).mean(1)
        cc = blk(np.clip(cb, 0, N_COVER - 1).astype(np.int64))
        for i in range(NC):
            out["cover"][j, i] = np.bincount(cc[i], minlength=N_COVER)[:N_COVER] / (Q * Q)
    # distance to the sea in cells (4-neighbour passes; the sea is any cell more than half sea)
    d = np.where(out["sea"] > 0.5, 0.0, 1e9)
    for _ in range(2):
        for jj in range(NC):
            for ii in range(NC):
                v = d[jj, ii]
                if jj: v = min(v, d[jj - 1, ii] + 1)
                if ii: v = min(v, d[jj, ii - 1] + 1)
                d[jj, ii] = v
        for jj in range(NC - 1, -1, -1):
            for ii in range(NC - 1, -1, -1):
                v = d[jj, ii]
                if jj < NC - 1: v = min(v, d[jj + 1, ii] + 1)
                if ii < NC - 1: v = min(v, d[jj, ii + 1] + 1)
                d[jj, ii] = v
    out["coast_cells"] = d.astype(np.float32)
    return out


def load_or_compute(root: Path | None = None) -> dict:
    """The features, cached beside the inputs (`regions/cell-features.npz`, keyed on the inputs' mtimes)."""
    import numpy as np

    r = root or data_root()
    cache = r / "regions" / "cell-features.npz"
    srcs = [r / "terrain" / "refined-height-f32.npy", r / "terrain" / "landcover-i16.npy",
            r / "hydrology-graph-bodies.npz"]
    if cache.exists() and all(cache.stat().st_mtime >= s.stat().st_mtime for s in srcs):
        z = np.load(cache)
        return {k: z[k] for k in z.files}
    f = features(r)
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **f)
    return f


def river_cells(min_width_m: float, root: Path | None = None) -> set[tuple[int, int]]:
    """(j, i) of every cell a solved channel of at least `min_width_m` crosses (the frozen hydrology solution's
    centreline samples, x east and y south in samples)."""
    import numpy as np

    z = np.load((root or data_root()) / "hydrology-graph-solution.npz")
    m = z["width"] >= min_width_m
    j = np.clip((z["y"][m] // Q).astype(int), 0, NC - 1)
    i = np.clip((z["x"][m] // Q).astype(int), 0, NC - 1)
    return set(zip(j.tolist(), i.tolist()))
