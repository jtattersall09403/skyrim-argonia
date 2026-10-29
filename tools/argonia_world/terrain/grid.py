"""The terrain's sample grid: the province and its near apron as one grid, read in row windows (memory guidance:
every array is memory-mapped, nothing whole-province is held).

Grid index space (`g`): rows from the north edge of the near apron, columns from its west edge, one sample per
LAND vertex; the province occupies rows and columns [PAD, PAD + 4032]. Skyrim cell (cx, cy) has its west column
at PAD + (cx - CX0) * 32 and its south row at PAD + 4032 - (cy - CY0) * 32; Skyrim vertex row j (0 = south)
is grid row south - j.

Sources (each a file in `$ARGONIA_DATA`, identified by its sha256 in the database):
- the province ground: the old chain's output after every applied terrain and route-grade patch
  (`terrain/refined-height-f32.npy`), which is the frozen base (`refined-height-frozen-f32.npy`) plus the patch
  layer: the receipts chain frozen -> terrain patches -> route-grade patches -> this file by sha256, and it differs
  from the frozen base only inside applied patches' regions (both checked by `check`);
- the apron: Transbot9's All-Tamriel heightmap (CC BY-NC 4.0) cut 1:1 by the old chain (`apron-source-near.npy`),
  joined to the province edge as old 0067 §1 rules: h = map + delta * w(d), delta the province edge minus the
  map at the nearest edge point, w a smoothstep falling from 1 at the border to 0 at APRON_BLEND_M;
- land cover: `terrain/landcover-i16.npy` in the province, `landcover.apron_class` beyond it;
- tint: `terrain/ground-tint.png` (1009^2 RGBA, one pixel per 4 samples), extended beyond the border from the
  nearest edge pixel and faded to white with w(d).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np

from tools.argonia_world import skyrim_units as su

Q = su.QUADS_PER_CELL
N = su.PROVINCE_SAMPLES - 1  # 4032 quads across the province
CX0, CY0 = su.PROVINCE_CELL_SW
PAD = su.APRON_CELLS * Q  # 2176
APRON_BLEND_M = 1200.0  # old 0067 §1's join width
TINT_STEP = 4  # ground-tint.png: one pixel per 4 samples


def data_root() -> Path:
    return Path(os.environ.get("ARGONIA_DATA", str(Path.home() / ".argonia" / "data")))


@dataclass
class Sources:
    """The four inputs as (possibly memory-mapped) arrays; tests pass small synthetic ones."""
    ground: np.ndarray  # (N+1)^2 float32 metres, row 0 north
    apron: np.ndarray | None  # (N+1+2*PAD)^2 float32 metres, or None for a province-only grid
    cover: np.ndarray  # (N+1)^2 int16 class ids
    tint: np.ndarray | None  # (N/4+1)^2 x 4 uint8 RGBA, or None (white)
    pad: int = PAD
    regrade: object = None  # the water's regrade (water_regrade.Regrade), applied by heights()

    @classmethod
    def load(cls, root: Path | None = None, apron: bool = True) -> Sources:
        from tools.argonia_world.terrain import png, water_regrade

        r = root or data_root()
        tint = r / "terrain" / "ground-tint.png"
        return cls(
            ground=np.load(r / "terrain" / "refined-height-f32.npy", mmap_mode="r"),
            apron=np.load(r / "terrain" / "apron-source-near.npy", mmap_mode="r") if apron else None,
            cover=np.load(r / "terrain" / "landcover-i16.npy", mmap_mode="r"),
            tint=png.read(tint) if tint.exists() else None,
            pad=PAD if apron else 0,
            regrade=water_regrade.Regrade.load(PAD if apron else 0),
        )

    @property
    def n(self) -> int:
        return self.ground.shape[0] - 1

    @property
    def size(self) -> int:
        """Samples per side of the whole grid."""
        return self.n + 1 + 2 * self.pad

    # ---- cells --------------------------------------------------------------------------------------------
    @property
    def cell_range(self) -> tuple[int, int, int, int]:
        """(x0, y0, x1, y1) inclusive: every cell of the grid."""
        k = self.pad // Q
        span = self.n // Q
        return CX0 - k, CY0 - k, CX0 + span + k - 1, CY0 + span + k - 1

    def cell_cols(self, cx: int) -> tuple[int, int]:
        c0 = self.pad + (cx - CX0) * Q
        return c0, c0 + Q

    def cell_rows(self, cy: int) -> tuple[int, int]:
        """(north row, south row) of a cell in grid rows."""
        s = self.pad + self.n - (cy - CY0) * Q
        return s - Q, s

    def in_province(self, cx: int, cy: int) -> bool:
        span = self.n // Q
        return CX0 <= cx < CX0 + span and CY0 <= cy < CY0 + span

    # ---- windows ------------------------------------------------------------------------------------------
    def _edge(self, r: np.ndarray, c: np.ndarray):
        """Nearest province sample (row, col in province space) and the distance to it in metres."""
        pr = np.clip(r - self.pad, 0, self.n)
        pc = np.clip(c - self.pad, 0, self.n)
        d = np.hypot((r - self.pad) - pr, (c - self.pad) - pc) * su.PROVINCE_SAMPLE_M
        return pr, pc, d

    @staticmethod
    def _w(d: np.ndarray) -> np.ndarray:
        t = np.clip(d / APRON_BLEND_M, 0.0, 1.0)
        return 1.0 - t * t * (3.0 - 2.0 * t)

    def heights(self, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
        """Ground metres for grid rows [r0, r1) and columns [c0, c1) (clipped by the caller to the grid)."""
        p, n = self.pad, self.n
        out = np.empty((r1 - r0, c1 - c0), dtype=np.float64)
        # the province part
        ir0, ir1 = max(r0, p), min(r1, p + n + 1)
        ic0, ic1 = max(c0, p), min(c1, p + n + 1)
        inside = np.zeros(out.shape, dtype=bool)
        if ir0 < ir1 and ic0 < ic1:
            out[ir0 - r0:ir1 - r0, ic0 - c0:ic1 - c0] = self.ground[ir0 - p:ir1 - p, ic0 - p:ic1 - p]
            inside[ir0 - r0:ir1 - r0, ic0 - c0:ic1 - c0] = True
            if self.regrade is not None:
                self.regrade.apply(out, r0, c0)  # the water's border regrade (water_regrade.py)
        if inside.all():
            return out
        if self.apron is None:
            raise ValueError("window leaves the province but the grid has no apron")
        rr, cc = np.nonzero(~inside)
        rr, cc = rr + r0, cc + c0
        pr, pc, d = self._edge(rr, cc)
        edge = self.ground[pr, pc].astype(np.float64) - self.apron[pr + p, pc + p]
        out[rr - r0, cc - c0] = self.apron[rr, cc] + edge * self._w(d)
        return out

    def classes(self, r0: int, r1: int, c0: int, c1: int, heights: np.ndarray | None = None) -> np.ndarray:
        from tools.argonia_world.terrain.landcover import apron_class

        p, n = self.pad, self.n
        out = np.empty((r1 - r0, c1 - c0), dtype=np.int16)
        ir0, ir1 = max(r0, p), min(r1, p + n + 1)
        ic0, ic1 = max(c0, p), min(c1, p + n + 1)
        inside = np.zeros(out.shape, dtype=bool)
        if ir0 < ir1 and ic0 < ic1:
            out[ir0 - r0:ir1 - r0, ic0 - c0:ic1 - c0] = self.cover[ir0 - p:ir1 - p, ic0 - p:ic1 - p]
            inside[ir0 - r0:ir1 - r0, ic0 - c0:ic1 - c0] = True
        if not inside.all():
            h = heights if heights is not None else self.heights(r0, r1, c0, c1)
            gy, gx = np.gradient(h, su.PROVINCE_SAMPLE_M)
            slope = np.degrees(np.arctan(np.hypot(gx, gy)))
            out[~inside] = apron_class(h, slope)[~inside]
        return out

    def tint_rgb(self, r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
        """The vertex colour (uint8 RGB) for a window: the old ground tint scaled so its bright end is white,
        weighted by its alpha, faded to white beyond the border."""
        shape = (r1 - r0, c1 - c0, 3)
        if self.tint is None:
            return np.full(shape, 255, dtype=np.uint8)
        rr, cc = np.mgrid[r0:r1, c0:c1]
        pr, pc, d = self._edge(rr.ravel(), cc.ravel())
        t = self._tint_at(pr, pc)  # (k, 4) float
        rgb = np.clip(t[:, :3] / self.tint_ref * 255.0, 0, 255)
        a = t[:, 3:4] / 255.0 * self._w(d)[:, None]
        v = 255.0 + (rgb - 255.0) * a
        return np.rint(v).astype(np.uint8).reshape(shape)

    def _tint_at(self, pr: np.ndarray, pc: np.ndarray) -> np.ndarray:
        """Bilinear sample of the tint at province samples."""
        t = self.tint
        fy, fx = pr / TINT_STEP, pc / TINT_STEP
        y0 = np.clip(np.floor(fy).astype(int), 0, t.shape[0] - 2)
        x0 = np.clip(np.floor(fx).astype(int), 0, t.shape[1] - 2)
        wy, wx = (fy - y0)[:, None], (fx - x0)[:, None]
        a = t[y0, x0].astype(np.float64)
        b = t[y0, x0 + 1].astype(np.float64)
        c = t[y0 + 1, x0].astype(np.float64)
        d = t[y0 + 1, x0 + 1].astype(np.float64)
        return (a * (1 - wx) + b * wx) * (1 - wy) + (c * (1 - wx) + d * wx) * wy

    @cached_property
    def tint_ref(self) -> np.ndarray:
        """The 99th percentile of the land tint per channel: that tint maps to white."""
        t = self.tint.reshape(-1, 4)
        land = t[t[:, 3] > 0][:, :3]
        return np.percentile(land, 99, axis=0) if len(land) else np.full(3, 255.0)
