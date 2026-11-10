"""A model or texture path to its bytes exactly as the game finds it in the NewWorld profile.

Loose files win over archives. The loose winner of each path is the NewWorld profile's install record
(`~/.argonia/stack/installed-NewWorld.json`: data path -> [mod, sha256], written by infra/gpu-box/stack.ps1 in the
profile's mod order, so Tropical Skyrim's file wins over vanilla wherever it has one); a mod's files live in
`~/.argonia/stack/MO2/mods/<mod>` or, for the new world's asset-only mods, `~/games/skyrimse/newworld-assets/<mod>`.
Archives come next: each profile mod's BSAs in the profile's priority (modlist.txt lists the highest first), then
the game's own `Data/*.bsa`. Paths are matched case-insensitively, as the game does."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path

HOME = Path.home()
STACK = Path(os.environ.get("ARGONIA_STACK", HOME / ".argonia" / "stack"))
DATA = Path(os.environ.get("ARGONIA_DATA", HOME / "games" / "skyrimse" / "Data"))
ASSET_MODS = Path(os.environ.get("ARGONIA_NW_ASSETS", HOME / "games" / "skyrimse" / "newworld-assets"))
PROFILE = "NewWorld"


def norm(path: str, root: str) -> str:
    """Data-relative, lower case, backslashes; `root` ('meshes' or 'textures') prefixed when missing."""
    p = path.strip().replace("/", "\\").lower().lstrip("\\")
    if p.startswith("data\\"):
        p = p[5:]
    return p if p.startswith(root + "\\") else f"{root}\\{p}"


def _decompress(arc, key: str) -> bytes:
    import zlib
    foff, size, comp = arc.files[key]
    data = arc.read(foff, size)
    if arc.flags & 0x100:
        data = data[1 + data[0]:]
    if not comp:
        return data
    body = data[4:]
    if arc.version == 105:
        try:
            import lz4.frame
            return lz4.frame.decompress(body)
        except ImportError:
            from tools.navmesh.bsa import lz4_frame
            return lz4_frame(body)
    return zlib.decompress(body)


class Resolver:
    """read(path) -> bytes or None; where(path) -> 'mod:<id>' | 'bsa:<archive>' | None."""

    def __init__(self, stack: Path = STACK, data: Path = DATA, asset_mods: Path = ASSET_MODS, profile: str = PROFILE):
        self.stack, self.data, self.asset_mods = stack, data, asset_mods
        rec = stack / f"installed-{profile}.json"
        self.loose: dict[str, str] = {k: v[0] for k, v in json.loads(rec.read_text())["files"].items()} if rec.exists() else {}
        ml = stack / "MO2" / "profiles" / profile / "modlist.txt"
        self.order = [ln[1:].strip() for ln in ml.read_text(errors="replace").splitlines() if ln.startswith("+")] if ml.exists() else []
        self._dirs: dict[Path, dict[str, str]] = {}
        self._arcs = None
        self._lock = threading.Lock()

    # ---- loose files
    def _ls(self, d: Path) -> dict[str, str]:
        if d not in self._dirs:
            try:
                self._dirs[d] = {n.lower(): n for n in os.listdir(d)}
            except OSError:
                self._dirs[d] = {}
        return self._dirs[d]

    def _find(self, root: Path, key: str) -> Path | None:
        p = root
        for part in key.split("\\"):
            n = self._ls(p).get(part)
            if n is None:
                return None
            p = p / n
        return p if p.is_file() else None

    def loose_file(self, key: str) -> Path | None:
        mod = self.loose.get(key)
        if mod:
            for root in (self.stack / "MO2" / "mods" / mod, self.asset_mods / mod):
                f = self._find(root, key)
                if f:
                    return f
        return None

    # ---- archives
    def archives(self):
        with self._lock:
            if self._arcs is None:
                from tools.navmesh import bsa
                mods = self.stack / "MO2" / "mods"
                paths = [p for m in self.order for p in sorted((mods / m).glob("*.bsa"))] + sorted(self.data.glob("*.bsa"))
                arcs = []
                for p in paths:
                    try:
                        arcs.append((p.name, bsa.Archive(bsa.local(p))))
                    except (ValueError, OSError):
                        continue
                self._arcs = arcs
        return self._arcs

    def ident(self, key: str) -> tuple | None:
        """What a path resolves to, without reading it: the loose winner's file, size and time, else the archive
        entry that holds it; None when nothing does. Equal idents mean equal bytes."""
        f = self.loose_file(key)
        if f:
            st = f.stat()
            return ("loose", str(f), st.st_size, st.st_mtime_ns)
        k = key.replace("\\", "/")
        for name, arc in self.archives():
            if k in arc.files:
                return ("bsa", name, *arc.files[k])
        return None

    def where(self, key: str) -> str | None:
        if self.loose_file(key):
            return f"mod:{self.loose[key]}"
        k = key.replace("\\", "/")
        for name, arc in self.archives():
            if k in arc.files:
                return f"bsa:{name}"
        return None

    def read(self, key: str) -> bytes | None:
        f = self.loose_file(key)
        if f:
            return f.read_bytes()
        k = key.replace("\\", "/")
        for _, arc in self.archives():
            if k in arc.files:
                return _decompress(arc, k)
        return None


_default: Resolver | None = None
_dlock = threading.Lock()


def default() -> Resolver:
    global _default
    with _dlock:
        if _default is None:
            _default = Resolver()
        return _default
