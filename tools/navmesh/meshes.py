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


def plugin_file(name: str, data: Path, stack: Path = STACK) -> Path | None:
    """Where the game loads a plugin from: the game's Data, else the laid stack's mod that carries it (the profile's
    mod order, highest first), as MO2 lays it into Data."""
    if (data / name).exists():
        return data / name
    ml = stack / "profiles" / PROFILE / "modlist.txt"
    if ml.exists():
        for ln in ml.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("+") and (stack / "mods" / ln[1:].strip() / name).is_file():
                return stack / "mods" / ln[1:].strip() / name
    # a place's source mod whose plugin the game never loads (its pieces copied into our places): its plugin lies with
    # its assets in newworld-assets/<mod>, beside the game's Data
    assets = data.parent / "newworld-assets"
    for d in sorted(assets.iterdir()) if assets.is_dir() else []:
        if (d / name).is_file():
            return d / name
    return None


_RESOLVERS: dict = {}


def shared(data: Path) -> "Resolver":
    """One Resolver a run for each game data folder, stack and profile: making one walks every mod's loose meshes."""
    k = (str(data), str(STACK), PROFILE)
    if k not in _RESOLVERS:
        _RESOLVERS[k] = Resolver(data)
    return _RESOLVERS[k]


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
        got = cached_collision(b)
        if got is not None:
            return got
        try:
            c = nif.collision(b)
        except (ValueError, IndexError, KeyError) as e:  # a layout we do not read: counted by the caller
            return nif.Collision(None, None, {f"error:{type(e).__name__}": 1})
        keep = [i for i, layer in enumerate(c.layers) if layer in nif.SOLID_LAYERS]
        out = nif.Collision(c.tris[keep] if len(c.tris) else c.tris, c.layers[keep], c.skipped)
        store_collision(b, out)
        return out


# ---- the solid collision of a mesh, kept on disk by the mesh's bytes and the reader's code ----------------------------
COLLISION_CACHE = Path(os.environ.get("ARGONIA_COLLISION_CACHE") or Path(__file__).resolve().parents[2] / "out" / "places" / "cache" / "collision")


@lru_cache(maxsize=1)
def _reader_key() -> str:
    import hashlib
    h = hashlib.sha256(Path(nif.__file__).read_bytes())   # the reader, and the layers this file keeps of what it reads
    h.update(repr(sorted(nif.SOLID_LAYERS)).encode() + b"|solid-v1")
    return h.hexdigest()[:12]


def _collision_path(b: bytes) -> Path:
    import hashlib
    k = hashlib.sha256(b).hexdigest()
    return COLLISION_CACHE / _reader_key() / k[:2] / f"{k}.npz"


def cached_collision(b: bytes) -> nif.Collision | None:
    """The solid collision read from these bytes before, by this code; None when not kept (or unreadable)."""
    p = _collision_path(b)
    if not p.exists():
        return None
    try:
        import json
        import numpy as np
        z = np.load(p, allow_pickle=False)
        return nif.Collision(z["tris"], z["layers"], json.loads(str(z["skipped"])))
    except Exception:  # noqa: BLE001  a torn or old file: read the mesh again
        return None


def store_collision(b: bytes, c: nif.Collision) -> None:
    import json
    import numpy as np
    if not (isinstance(c.tris, np.ndarray) and isinstance(c.layers, np.ndarray)
            and all(isinstance(k, str) for k in c.skipped)):
        return   # kept only what comes back the same from the file
    p = _collision_path(b)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(f".{os.getpid()}.tmp.npz")
        np.savez(tmp, tris=np.asarray(c.tris), layers=np.asarray(c.layers), skipped=json.dumps(c.skipped))
        os.replace(tmp, p)
    except OSError:
        pass
