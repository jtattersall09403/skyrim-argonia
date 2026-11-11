"""A world thing's body at walking height: the columns of the navmesh's grid its solid collision blocks over the
world's ground (tools/navmesh/placed.py, solid.py), as the world's own navmesh and a place's are cut round it. The
clearance reads it for the things whose body, not their root, stands in a street or a doorway (clear.across)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

WORLD_DIR = Path(__file__).resolve().parents[3] / "out" / "newworld" / "plugin"


class Bodies:
    """`heights` is the world's ground raster (row 0 north), `frame` the world x and y of its first sample and the
    sample spacing, `resolver` finds a model's collision (tools.navmesh.meshes.Resolver)."""

    def __init__(self, bases: dict, heights: np.ndarray, frame, resolver):
        self.h = np.ascontiguousarray(heights, np.float32)
        self.frame = tuple(float(v) for v in frame)
        self.bases, self.res = bases, resolver
        self._reach: dict[str, float] = {}

    def _tris(self, r: dict):
        model = (self.bases.get(r["base"]) or {}).get("model")
        c = self.res.collision(model) if model else None
        return None if c is None or c.tris is None or not len(c.tris) else c.tris

    def reach(self, r: dict) -> float:
        """How far from its origin the thing's solid collision reaches (0: it has none)."""
        if r["base"] not in self._reach:
            t = self._tris(r)
            self._reach[r["base"]] = 0.0 if t is None else float(np.linalg.norm(t.reshape(-1, 3), axis=1).max())
        return self._reach[r["base"]] * float(r.get("scale") or 1.0)

    def columns(self, r: dict) -> np.ndarray:
        """The plan centres (n, 2) of the columns the thing blocks at walking height."""
        from tools.navmesh import params, placed
        t = self._tris(r)
        if t is None:
            return np.zeros((0, 2))
        x = {"pos": r["pos"], "rot": r.get("rot") or [0.0, 0.0, 0.0], "scale": r.get("scale")}
        runs, _ = placed.blocked_columns(placed.world_tris(t, x), self.h, self.frame)
        if not len(runs):
            return np.zeros((0, 2))
        ij = np.concatenate([np.stack([np.arange(a, b + 1), np.full(b - a + 1, j)], 1) for j, a, b in runs])
        return (ij + 0.5) * params.CELL_SIZE


def load(bases: dict, plugin: Path | None = None) -> Bodies | None:
    """The bodies of the world built here, or None where no world's land stands (a place drafted from bundles alone)."""
    from tools.navmesh import meshes, world
    from tools.navmesh.__main__ import game_data
    plugin = WORLD_DIR if plugin is None else plugin
    if not (plugin / "land" / "manifest.json").exists():
        return None
    land = world.Land.load(plugin)
    was, meshes.PROFILE = meshes.PROFILE, "NewWorld"  # the world's meshes are found by the new world's mod order
    try:
        resolver = meshes.Resolver(game_data())
    finally:
        meshes.PROFILE = was
    return Bodies(bases, land.heights(), (land.grid.origin_x, land.grid.origin_y, world.VERTEX_SPACING_UNITS), resolver)
