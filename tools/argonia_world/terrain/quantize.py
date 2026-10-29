"""Heights to VHGT: quantise to 8-unit steps, then make every neighbour step fit a signed byte.

VHGT stores one float offset per cell and 33 x 33 signed-byte deltas: [0, y] relative to [0, y-1] (the row
start, carried north), [x, y] relative to [x-1, y]. A cell holds a single offset, so a row cannot be re-based on
its own; a step steeper than 127 x 8 units over 128 (82.9 degrees) cannot be stored at all. The cure is on the
heights, once, for the whole grid: the quantised heights H (integer steps) are replaced by the L-infinity-closest
heights whose 4-neighbour steps are all within +-127 (the mean of the greatest 127-Lipschitz minorant and the
least majorant under the grid's L1 distance; separable, exact). Where no step overflows the result is H itself.
Every cell then reads its 33 x 33 from that one grid, so shared edge vertices are equal by construction (no seam).

The minorant at a vertex depends only on vertices within (max H - min H) / 127 samples, so a window with a halo
of that many rows and columns gives the global answer for its interior (HALO covers 1,100 m of relief).
"""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su

L = su.VHGT_DELTA_MAX
HALO = 64  # samples: 64 * 127 * 8 units = 930 m of relief, above the province's 761 m


def _sweep(a: np.ndarray, op, axis: int) -> np.ndarray:
    """In place along an axis: forward then backward, a[i] = op(a[i], a[i -+ 1] +- L)."""
    a = np.moveaxis(a, axis, 0)
    sign = 1 if op is np.minimum else -1
    for i in range(1, a.shape[0]):
        op(a[i], a[i - 1] + sign * L, out=a[i])
    for i in range(a.shape[0] - 2, -1, -1):
        op(a[i], a[i + 1] + sign * L, out=a[i])
    return np.moveaxis(a, 0, axis)


def limit(steps: np.ndarray) -> np.ndarray:
    """Integer steps (int64 array) -> the closest array whose 4-neighbour differences are all within +-L."""
    lo = steps.copy()  # greatest minorant: min over j of H_j + L * d1(i, j)
    _sweep(lo, np.minimum, 1)
    _sweep(lo, np.minimum, 0)
    hi = steps.copy()  # least majorant: max over j of H_j - L * d1(i, j)
    _sweep(hi, np.maximum, 1)
    _sweep(hi, np.maximum, 0)
    return (lo + hi) // 2


def overflow_pairs(steps: np.ndarray) -> int:
    """4-neighbour pairs whose step does not fit a signed byte."""
    return int((np.abs(np.diff(steps, axis=1)) > L).sum() + (np.abs(np.diff(steps, axis=0)) > L).sum())


def encode(cell: np.ndarray) -> tuple[float, np.ndarray]:
    """A cell's 33 x 33 integer steps, indexed [y, x] (y = row from the south) -> (offset, int8 deltas [y, x])."""
    c = cell.astype(np.int64)
    d = np.empty_like(c)
    d[:, 1:] = c[:, 1:] - c[:, :-1]
    d[1:, 0] = c[1:, 0] - c[:-1, 0]
    d[0, 0] = 0
    if np.abs(d).max() > L:
        raise ValueError(f"VHGT delta {int(np.abs(d).max())} overflows a signed byte: heights not limited")
    return float(c[0, 0]), d.astype(np.int8)


def decode(offset: float, deltas: np.ndarray) -> np.ndarray:
    """The inverse of encode: steps [y, x] as floats (multiply by VHGT_STEP_UNITS for units)."""
    d = deltas.astype(np.float64)
    starts = offset + np.cumsum(d[:, 0])
    rows = np.cumsum(np.concatenate([starts[:, None], d[:, 1:]], axis=1), axis=1)
    return rows
