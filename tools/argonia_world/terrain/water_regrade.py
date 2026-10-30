"""The water's step-and-pool regrade (2.W2; the owner's ruling of 2026-10-29), as a layer on the ground.

A river is designed as stepped flat pools (water/steps.py, water/oriented.py). The terrain is shaped to hold them:
each step's channel bed is carved to its level less the pool's depth (`bed`, a ceiling), the dry banks beside its
water and under its tiles are raised above it (`bank`, a floor), and below a cascade or fall the lip is raised to
hold the upper pool (`sill`, a floor). The water plan decides each vertex and records it in the world db's
`water_regrade` table: province sample column `x`, row `y` (the hydrology frame, row 0 north), `kind` and `z_m`.
This module is the only place the terrain reads it: `Sources.heights` applies it to the province ground (ceilings
first, h = min(h, bed); then floors, h = max(h, bank or sill)), so the LAND, its normals and `build.game_heights_m`
all carry it. It never edits the frozen arrays.
"""
from __future__ import annotations

import hashlib

import numpy as np

TABLE = "water_regrade"
CEILINGS = ("bed",)


class Regrade:
    def __init__(self, rows: np.ndarray, cols: np.ndarray, z: np.ndarray, ceiling: np.ndarray | None = None):
        """Grid rows and columns (province samples + the grid's pad), their heights in metres, and whether each is a
        ceiling (a carved bed) rather than a floor."""
        ceiling = np.zeros(rows.shape, dtype=bool) if ceiling is None else ceiling.astype(bool)
        order = np.lexsort((cols, rows))
        self.rows, self.cols, self.z, self.ceiling = rows[order], cols[order], z[order], ceiling[order]

    def __len__(self) -> int:
        return int(self.rows.size)

    @classmethod
    def load(cls, pad: int, world=None) -> "Regrade | None":
        """The db's rows in grid space, or None when the table is empty (or not in this schema)."""
        from tools.argonia_world import db
        w = world if world is not None else db.open()
        try:
            rows = w.query(f'SELECT x, y, z_m, kind FROM "{TABLE}"')
        except Exception:  # an older schema without the table
            return None
        if not rows:
            return None
        a = np.array([(r[1], r[0], r[2]) for r in rows], dtype=np.float64)
        ceil = np.array([r[3] in CEILINGS for r in rows], dtype=bool)
        return cls(a[:, 0].astype(np.int64) + pad, a[:, 1].astype(np.int64) + pad, a[:, 2], ceil)

    @classmethod
    def from_flat(cls, floors: dict, n: int, pad: int, ceilings: dict | None = None) -> "Regrade | None":
        """From the water plan's {flat province index: metres} floors and ceilings (before the rows are in the db)."""
        ceilings = ceilings or {}
        if not floors and not ceilings:
            return None
        keys = list(floors) + list(ceilings)
        idx = np.fromiter(keys, dtype=np.int64, count=len(keys))
        val = np.fromiter((floors[i] for i in floors), dtype=np.float64, count=len(floors))
        val = np.concatenate([val, np.fromiter((ceilings[i] for i in ceilings), dtype=np.float64,
                                               count=len(ceilings))])
        ceil = np.concatenate([np.zeros(len(floors), dtype=bool), np.ones(len(ceilings), dtype=bool)])
        return cls(idx // n + pad, idx % n + pad, val, ceil)

    def apply(self, out: np.ndarray, r0: int, c0: int) -> None:
        """Lower `out` (a window whose first grid row and column are r0, c0) to every ceiling inside it, then raise it
        to every floor."""
        r1, c1 = r0 + out.shape[0], c0 + out.shape[1]
        lo, hi = np.searchsorted(self.rows, r0), np.searchsorted(self.rows, r1)
        rr, cc, zz, ce = self.rows[lo:hi], self.cols[lo:hi], self.z[lo:hi], self.ceiling[lo:hi]
        m = (cc >= c0) & (cc < c1)
        for sel, op in ((m & ce, np.minimum), (m & ~ce, np.maximum)):
            if sel.any():
                i, j = rr[sel] - r0, cc[sel] - c0
                out[i, j] = op(out[i, j], zz[sel])


def stamp(world=None) -> str:
    """The table's content hash, for the terrain's rebuild stamp."""
    from tools.argonia_world import db
    w = world if world is not None else db.open()
    try:
        rows = w.query(f'SELECT x, y, kind, z_m FROM "{TABLE}" ORDER BY y, x, kind')
    except Exception:
        return "none"
    return hashlib.sha256(repr([tuple(r) for r in rows]).encode()).hexdigest()
