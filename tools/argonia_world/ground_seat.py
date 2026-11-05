"""The ground-side helpers of place building: the game ground at a point, a cell's water level, the dock deck height.
Kept free of place_build's placement code so terrain/patches.py and routes/infra.py import this, and an edit of
place_build.py does not re-key the ground stage (lane claywater-reseat)."""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su

# A dock's origin stands DOCK_DECK_M over the water (Skyrim.esm's DockStRSol01/02 refs, the kit of our DockStRent02:
# origin over their cell's XCLW p50 0.76-0.88 m, n 5; lane 1.15-r4-claywater); see place_build.water_seat.
DOCK_DECK_M = 0.85


def water_level(world, x_m: float, y_m: float) -> float | None:
    """The level of the cell's water at a province point (cell_water), None for a dry cell."""
    cache = getattr(world, "_cell_water", None)
    if cache is None:
        cache = world._cell_water = {(r["cx"], r["cy"]): r["level_m"]
                                     for r in world.query("SELECT cx, cy, level_m FROM cell_water")}
    ux, uy = su.province_to_skyrim(x_m, y_m)
    return cache.get(su.cell_of(ux, uy))


class GameGround:
    """The final game ground at province metres (x east, y south): bilinear over `build.game_heights_m` with every
    layer applied (the river regrade and the place ground edits), the numbers the LAND stores, so a reference
    with no explicit z stands on the ground the player sees, not on the frozen 2.W1 array."""

    def __init__(self, src=None):
        from tools.argonia_world.terrain.grid import Sources
        self.src = src if src is not None else Sources.load()
        self._cache: dict[tuple[int, int], object] = {}

    def _block(self, br: int, bc: int):
        from tools.argonia_world.terrain import build as tb
        b = self._cache.get((br, bc))
        if b is None:  # 33 x 33 samples with a shared edge, so a bilinear 2x2 is inside
            p = self.src.pad
            b = tb.game_heights_m(self.src, p + br * 32, p + br * 32 + 33, p + bc * 32, p + bc * 32 + 33)
            self._cache[(br, bc)] = b
        return b

    def z(self, x: float, y: float) -> float:
        n = self.src.n
        c = min(max(x / su.PROVINCE_SAMPLE_M, 0), n - 1e-6)
        r = min(max(y / su.PROVINCE_SAMPLE_M, 0), n - 1e-6)
        c0, r0 = int(c), int(r)
        fc, fr = c - c0, r - r0
        h = self._block(r0 // 32, c0 // 32)
        i, j = r0 % 32, c0 % 32
        a, b, cc, d = (float(h[i, j]), float(h[i, j + 1]), float(h[i + 1, j]), float(h[i + 1, j + 1]))
        return (a * (1 - fc) + b * fc) * (1 - fr) + (cc * (1 - fc) + d * fc) * fr
