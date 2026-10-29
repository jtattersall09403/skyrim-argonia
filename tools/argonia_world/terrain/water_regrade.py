"""The water's regrade (2.W2's per-cell fallback; the planner's ruling of 2026-10-29), as a layer on the ground.

A cell the plane budget could not bring under its budget stands at one water height; at its border the ground is
raised so no water sheet ends in the air. The water plan (tools/argonia_world/water/budget.py) decides each
raised vertex and records it in the world db's `water_regrade` table: province sample column `x`, row `y` (the
hydrology frame, row 0 north) and `floor_m`, the height the ground stands at least at. This module is the only
place the terrain reads it: `Sources.heights` applies it to the province ground (h = max(h, floor)), so the LAND,
its normals and `build.game_heights_m` all carry it. It never edits the frozen arrays.
"""
from __future__ import annotations

import hashlib

import numpy as np

TABLE = "water_regrade"


class Regrade:
    def __init__(self, rows: np.ndarray, cols: np.ndarray, floors: np.ndarray):
        """Grid rows and columns (province samples + the grid's pad) and their floors in metres."""
        order = np.lexsort((cols, rows))
        self.rows, self.cols, self.floors = rows[order], cols[order], floors[order]

    def __len__(self) -> int:
        return int(self.rows.size)

    @classmethod
    def load(cls, pad: int, world=None) -> "Regrade | None":
        """The db's rows in grid space, or None when the table is empty (or not in this schema)."""
        from tools.argonia_world import db
        w = world if world is not None else db.open()
        try:
            rows = w.query(f'SELECT x, y, floor_m FROM "{TABLE}"')
        except Exception:  # an older schema without the table
            return None
        if not rows:
            return None
        a = np.array([(r[1], r[0], r[2]) for r in rows], dtype=np.float64)
        return cls(a[:, 0].astype(np.int64) + pad, a[:, 1].astype(np.int64) + pad, a[:, 2])

    @classmethod
    def from_flat(cls, floors: dict, n: int, pad: int) -> "Regrade | None":
        """From the water plan's {flat province index: floor} (before the rows are in the db)."""
        if not floors:
            return None
        idx = np.fromiter(floors, dtype=np.int64, count=len(floors))
        val = np.fromiter((floors[i] for i in floors), dtype=np.float64, count=len(floors))
        return cls(idx // n + pad, idx % n + pad, val)

    def apply(self, out: np.ndarray, r0: int, c0: int) -> None:
        """Raise `out` (a window whose first grid row and column are r0, c0) to every floor inside it."""
        r1, c1 = r0 + out.shape[0], c0 + out.shape[1]
        lo, hi = np.searchsorted(self.rows, r0), np.searchsorted(self.rows, r1)
        rr, cc, ff = self.rows[lo:hi], self.cols[lo:hi], self.floors[lo:hi]
        m = (cc >= c0) & (cc < c1)
        if m.any():
            i, j = rr[m] - r0, cc[m] - c0
            out[i, j] = np.maximum(out[i, j], ff[m])


def stamp(world=None) -> str:
    """The table's content hash, for the terrain's rebuild stamp."""
    from tools.argonia_world import db
    w = world if world is not None else db.open()
    try:
        rows = w.query(f'SELECT x, y, floor_m FROM "{TABLE}" ORDER BY y, x')
    except Exception:
        return "none"
    return hashlib.sha256(repr([tuple(r) for r in rows]).encode()).hexdigest()
