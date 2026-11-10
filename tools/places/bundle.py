"""Read and write place bundles (docs/design/place-studio.md, "Bundles"). Other lanes import this to load a bundle:

    from tools.places.bundle import Bundle
    b = Bundle("src.bmv.helstrom")            # or a path to the bundle directory
    b.meta, b.bases[key], b.npcs[key], b.space_ids
    ext = b.space("exterior")
    ext.info, ext.refs, ext.navmeshes, ext.terrain.height_at(x, y), ext.terrain.water_at(x, y)

Files are read lazily and cached; nothing here needs the game or Mutagen.
"""
from __future__ import annotations

import array
import gzip
import hashlib
import json
import math
import os
import shutil
import threading
from functools import cached_property
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUNDLES = REPO / "out" / "places" / "bundles"
CELL = 4096.0
V = 33
STEP = CELL / (V - 1)


def bundle_dir(bundle_id_or_path: str | os.PathLike) -> Path:
    p = Path(bundle_id_or_path)
    return p if p.is_dir() and (p / "bundle.json").exists() else BUNDLES / str(bundle_id_or_path)


# ---- jsonl --------------------------------------------------------------------------------------------------------

def _open(path: Path, mode: str):
    return gzip.open(path, mode + "t", encoding="utf-8") if path.suffix == ".gz" else open(path, mode, encoding="utf-8")


def read_jsonl(path: str | os.PathLike) -> list[dict]:
    """Rows of a .jsonl (or .jsonl.gz) file; an absent file is no rows."""
    p = Path(path)
    if not p.exists() and Path(str(p) + ".gz").exists():
        p = Path(str(p) + ".gz")
    if not p.exists():
        return []
    with _open(p, "r") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: str | os.PathLike, rows) -> int:
    """Write rows one per line (gzip when the name ends .gz); returns the count."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with _open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
            n += 1
    return n


def write_json(path: str | os.PathLike, obj) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


# ---- stamps -------------------------------------------------------------------------------------------------------

_SHA_CACHE = REPO / "out" / "places" / "cache" / "sha256.json"


def sha256_file(path: str | os.PathLike) -> str:
    """sha256 of a file, cached by (path, size, mtime) so a rerun does not rehash a 285 MB plugin."""
    p = Path(path).resolve()
    st = p.stat()
    key = f"{p}|{st.st_size}|{st.st_mtime_ns}"
    try:
        cache = json.loads(_SHA_CACHE.read_text())
    except (OSError, ValueError):
        cache = {}
    if key in cache:
        return cache[key]
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    cache = {k: v for k, v in cache.items() if not k.startswith(f"{p}|")}
    cache[key] = h.hexdigest()
    _SHA_CACHE.parent.mkdir(parents=True, exist_ok=True)
    # a file of this writer's own: two processes (or threads) hashing at once both land, the later one whole
    tmp = _SHA_CACHE.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(cache, indent=0))
    tmp.replace(_SHA_CACHE)
    return cache[key]


def stamp_key(inputs: dict[str, str], tool: str, params) -> str:
    """The key of a stamp: the inputs' hashes, the tool's own hash and the parameters, as one sha256."""
    blob = json.dumps({"inputs": inputs, "tool": tool, "params": params}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def publish(tmp: Path, final: Path) -> None:
    """Replace a bundle directory with a fully written one in one rename (an interrupted run leaves the old one)."""
    old = final.with_name(final.name + ".old")
    if old.exists():
        shutil.rmtree(old)
    if final.exists():
        final.rename(old)
    tmp.rename(final)
    if old.exists():
        shutil.rmtree(old)


# ---- the reader ---------------------------------------------------------------------------------------------------

class Terrain:
    """An exterior's land: 33x33 heights per cell (world Z, rows south to north), water, texture layers."""

    def __init__(self, d: Path):
        self.dir = d
        t = json.loads((d / "terrain.json").read_text())
        self.ltex = t.get("ltex", {})
        self.cells = {tuple(c["cell"]): c for c in t["cells"]}
        self._f32 = None
        self._cell: dict[tuple[int, int], array.array | None] = {}

    def heights(self, cx: int, cy: int):
        """The cell's 1089 heights as an array('f'), row-major south to north, west to east; None without land.
        Cut out of the file once per cell (height_at asks for every point it is given); read it, never write it."""
        try:
            return self._cell[(cx, cy)]
        except KeyError:
            pass
        c = self.cells.get((cx, cy))
        h = None
        if c is not None and c.get("heights_index") is not None:
            if self._f32 is None:
                self._f32 = array.array("f")
                self._f32.frombytes((self.dir / "terrain.f32").read_bytes())
            i = c["heights_index"] * V * V
            h = self._f32[i:i + V * V]
        self._cell[(cx, cy)] = h
        return h

    def height_at(self, x: float, y: float) -> float | None:
        """Land height at a world point, bilinear between the four vertices round it (the engine's quads split into
        triangles; bilinear is within a unit or two of it on any slope that matters for seating)."""
        cx, cy = math.floor(x / CELL), math.floor(y / CELL)
        h = self.heights(cx, cy)
        if h is None:
            return None
        fx, fy = (x - cx * CELL) / STEP, (y - cy * CELL) / STEP
        c0, r0 = min(int(fx), V - 2), min(int(fy), V - 2)
        tx, ty = fx - c0, fy - r0
        a, b = h[r0 * V + c0], h[r0 * V + c0 + 1]
        c, d = h[(r0 + 1) * V + c0], h[(r0 + 1) * V + c0 + 1]
        return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty

    def normal_at(self, x: float, y: float) -> list[float] | None:
        """Unit normal of the land at a point, from the heights a vertex step either side."""
        hs = [self.height_at(x + dx, y + dy) for dx, dy in ((-STEP, 0), (STEP, 0), (0, -STEP), (0, STEP))]
        if any(v is None for v in hs):
            return None
        gx, gy = (hs[1] - hs[0]) / (2 * STEP), (hs[3] - hs[2]) / (2 * STEP)
        n = math.sqrt(gx * gx + gy * gy + 1)
        return [-gx / n, -gy / n, 1 / n]

    def water_at(self, x: float, y: float) -> dict | None:
        """{height, type} of the cell's water at a point, or None when the cell has none."""
        c = self.cells.get((math.floor(x / CELL), math.floor(y / CELL)))
        return c.get("water") if c else None


class Space:
    def __init__(self, d: Path):
        self.dir = d
        self.id = d.name

    @cached_property
    def info(self) -> dict:
        return json.loads((self.dir / "space.json").read_text())

    @cached_property
    def refs(self) -> list[dict]:
        return read_jsonl(self.dir / "refs.jsonl")

    @cached_property
    def navmeshes(self) -> list[dict]:
        return read_jsonl(self.dir / "navmesh.jsonl")

    @cached_property
    def terrain(self) -> Terrain | None:
        return Terrain(self.dir) if (self.dir / "terrain.json").exists() else None


class Bundle:
    def __init__(self, bundle_id_or_path: str | os.PathLike):
        self.dir = bundle_dir(bundle_id_or_path)
        if not (self.dir / "bundle.json").exists():
            raise FileNotFoundError(f"no bundle at {self.dir} (run: python -m tools.places extract ...)")
        self.meta = json.loads((self.dir / "bundle.json").read_text())
        self.id = self.meta["bundle_id"]
        self._spaces: dict[str, Space] = {}

    @property
    def space_ids(self) -> list[str]:
        return list(self.meta.get("spaces", []))

    def space(self, space_id: str) -> Space:
        if space_id not in self._spaces:
            d = self.dir / "spaces" / space_id
            if not d.is_dir():
                raise KeyError(f"{self.id} has no space {space_id!r}")
            self._spaces[space_id] = Space(d)
        return self._spaces[space_id]

    @cached_property
    def bases(self) -> dict[str, dict]:
        return {r["key"]: r for r in read_jsonl(self.dir / "bases.jsonl")}

    @cached_property
    def npcs(self) -> dict[str, dict]:
        return {r["key"]: r for r in read_jsonl(self.dir / "npcs.jsonl")}

    @property
    def stamp(self) -> dict:
        return self.meta.get("stamp", {})
