"""Beyond the map: the land and sea past the source map's edge, so the world does not stop where the picture does.

The source map (3521 x 2841 px) ends in a ruler band (frame.FRAME_PX) on every edge. The world reaches BEYOND_CELLS
map cells past the picture (tiles.BEYOND_CELLS: unplayable border scenery, like Skyrim's land past its mountains and
its sea to the north). What lies there is the map's own edge carried on outward, so each neighbour continues as the
map shows it: Cyrodiil (Blackwood and the Nibenay) on the west and north-west, Morrowind (the Deshaan) on the north,
the open sea on the east, south and south-west (the map's edge there is sea).

    water_ext, foreign_ext, pad = extend(water_px, foreign_px)

`water_ext` and `foreign_ext` are the map's rasters padded by `pad` px on every side: the picture's inside kept
pixel for pixel; the ruler band and everything past it read from the last true map pixels inward of the band,
carried outward and blurred more the further out they go (BLUR_PX: a 3 px river ends a few px past the edge, a
coast simplifies into a broad shore), with a little warped noise on the threshold (NOISE) so the new coasts wander.
Land past the map is foreign land (it takes the `foreign` relief row: modest generic hills).
A grid reads them with its origin shifted by `pad` (shifted(grid, pad)).
"""
from __future__ import annotations

import dataclasses

import numpy as np
from scipy import ndimage as ndi

from tools.newworld import frame as f

PAD_PX = 400                      # covers BEYOND_CELLS (8) + the grid's own cell + the band, at 40 px a cell
INSET_PX = 2 * f.FRAME_PX + 4     # the ruler band and the map's own frame strip inside it (as water_kinds.FRAME_BAND)
BLUR_PX = (1.0, 0.35)             # sigma = a + b * distance past the edge (px)
NOISE = (600.0 / (204.8 / 70.0), 0.12)   # threshold noise: wavelength (px, about 600 m) and amplitude (land share)
SEED = 4242


def interior_box(shape) -> tuple[int, int, int, int]:
    """(top, bottom, left, right) of the map's true pixels: the picture less its ruler band."""
    H, W = shape
    return INSET_PX, H - INSET_PX, INSET_PX, W - INSET_PX


def _carry(a: np.ndarray, pad: int) -> tuple[np.ndarray, np.ndarray]:
    """`a`'s interior carried outward to the padded size, blurred by distance past the interior box; and that
    distance (px)."""
    t, b, l, r = interior_box(a.shape)
    inner = a[t:b, l:r].astype(np.float32)
    ext = np.pad(inner, ((pad + t, pad + a.shape[0] - b), (pad + l, pad + a.shape[1] - r)), mode="edge")
    I, J = np.ogrid[0:ext.shape[0], 0:ext.shape[1]]
    di = np.maximum(np.maximum((pad + t) - I, I - (pad + b - 1)), 0)
    dj = np.maximum(np.maximum((pad + l) - J, J - (pad + r - 1)), 0)
    dist = np.hypot(di, dj).astype(np.float32)
    sig = BLUR_PX[0] + BLUR_PX[1] * dist
    levels = (1, 2, 4, 8, 16, 32, 64, 128)
    out = np.zeros(ext.shape, np.float32)
    lo = None
    for k, s in enumerate(levels):
        cur = ndi.gaussian_filter(ext, s, mode="nearest")
        if lo is None:
            out[sig <= s] = cur[sig <= s]
        else:
            sel = (sig > levels[k - 1]) & (sig <= s)
            w = (sig[sel] - levels[k - 1]) / (s - levels[k - 1])
            out[sel] = (1 - w) * lo[sel] + w * cur[sel]
        lo = cur
    out[sig > levels[-1]] = lo[sig > levels[-1]]
    return out, dist


def extend(water_px: np.ndarray, foreign_px: np.ndarray, pad: int = PAD_PX) -> tuple[np.ndarray, np.ndarray, int]:
    from tools.newworld.terrain_relief import noise
    land, dist = _carry(~water_px.astype(bool), pad)
    n = noise(land.shape, NOISE[0], SEED)
    beyond = dist > 0
    land_b = (land + NOISE[1] * np.clip(dist / 20.0, 0, 1) * n) > 0.5
    water_ext = np.ones(land.shape, bool)
    water_ext[pad:pad + water_px.shape[0], pad:pad + water_px.shape[1]] = water_px
    water_ext[beyond] = ~land_b[beyond]
    del land, n
    fr, _ = _carry(foreign_px.astype(bool), pad)
    foreign_ext = np.zeros(water_ext.shape, bool)
    foreign_ext[pad:pad + foreign_px.shape[0], pad:pad + foreign_px.shape[1]] = foreign_px
    # past the edge every land pixel is a neighbour's land; in the ruler band it is foreign where the map's edge was
    foreign_ext[beyond] = ~water_ext[beyond]
    band = beyond.copy()
    band[:pad, :] = band[-pad:, :] = band[:, :pad] = band[:, -pad:] = False
    foreign_ext[band] = (fr[band] > 0.5) & ~water_ext[band]
    return water_ext, foreign_ext, pad


def shifted(grid, pad: int):
    """The same grid read against the padded rasters."""
    return dataclasses.replace(grid, p0x=grid.p0x + pad, p0y=grid.p0y + pad)


def corrected(water_ext: np.ndarray, pad: int, shape) -> np.ndarray:
    """The picture's own extent of the padded raster: the map with its ruler band read as what lies there."""
    return water_ext[pad:pad + shape[0], pad:pad + shape[1]]
