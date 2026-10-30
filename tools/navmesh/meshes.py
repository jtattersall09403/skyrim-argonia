"""Find a base record's mesh (its MODL path) the way the game would, and read its collision (nif.py).

The laid mod stack is on the build VM (infra/gpu-box/stack.py: ~/.argonia/stack/MO2, the same files the game
machine runs): loose files in the profile's mod order (modlist.txt, highest first) win, then the mods' BSAs in that
order, then the game's own BSAs in Data. Nothing is copied: BSAs are read in place by range (bsa.py), and no mesh
leaves the VM or enters the repo (decision 0003).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from tools.navmesh import bsa, nif

STACK = Path(os.environ.get("ARGONIA_STACK") or Path.home() / ".argonia" / "stack") / "MO2"
PROFILE = "Argonia"


class Resolver:
    def __init__(self, data: Path, stack: Path = STACK):
        self.data = data
        order = []
        ml = stack / "profiles" / PROFILE / "modlist.txt"
        if ml.exists():
            order = [ln[1:].strip() for ln in ml.read_text(encoding="utf-8", errors="replace").splitlines()
                     if ln.startswith("+")]
        self.mods = [stack / "mods" / m for m in order if (stack / "mods" / m).is_dir()]
        self._loose: dict[str, tuple[str, Path]] = {}
        for m in reversed(self.mods):  # the highest mod is written last and wins
            for root in (p for p in m.iterdir() if p.is_dir() and p.name.lower() == "meshes"):
                for f in root.rglob("*"):
                    if f.is_file() and f.suffix.lower() == ".nif":
                        self._loose[str(f.relative_to(m)).replace("\\", "/").lower()] = (m.name, f)
        archives = [p for m in self.mods for p in sorted(m.glob("*.bsa"))]
        archives += sorted(p for p in data.glob("*.bsa") if "mesh" in p.name.lower() or "-" not in p.stem)
        self.archives: list[bsa.Archive] = []
        self.names: list[str] = []
        for p in archives:
            try:
                self.archives.append(bsa.Archive(bsa.local(p)))
                self.names.append(p.name)
            except ValueError:
                continue

    def where(self, modl: str) -> str | None:
        key = "meshes/" + modl.replace("\\", "/").lower().lstrip("/")
        if key in self._loose:
            return f"loose:{self._loose[key][0]}"
        for a, n in zip(self.archives, self.names):
            if key in a.files:
                return n
        return None

    @lru_cache(maxsize=None)
    def read(self, modl: str) -> bytes | None:
        key = "meshes/" + modl.replace("\\", "/").lower().lstrip("/")
        if key in self._loose:
            return self._loose[key][1].read_bytes()
        for a in self.archives:
            if key in a.files:
                return a.get(key)
        return None

    @lru_cache(maxsize=None)
    def collision(self, modl: str) -> nif.Collision | None:
        """The mesh's solid collision (nif.SOLID_LAYERS) in mesh units, or None when the mesh is not found or
        cannot be read."""
        b = self.read(modl)
        if b is None:
            return None
        try:
            c = nif.collision(b)
        except (ValueError, IndexError, KeyError) as e:  # a layout we do not read: counted by the caller
            return nif.Collision(None, None, {f"error:{type(e).__name__}": 1})
        keep = [i for i, layer in enumerate(c.layers) if layer in nif.SOLID_LAYERS]
        return nif.Collision(c.tris[keep] if len(c.tris) else c.tris, c.layers[keep], c.skipped)
