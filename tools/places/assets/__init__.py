"""Meshes and textures for the studio's browser, converted on demand and cached; land textures; the catalogue.

API (lane V's server calls these for GET /api/asset/mesh and /api/asset/tex):
    mesh(model, level=0, bounds=None) -> Path to a GLB      (always a file: a placeholder box when it cannot convert)
    mesh_info(model, level=0, bounds=None) -> dict          (tris, shapes, textures, bounds, placeholder, why, glb)
    tex(path, size=512) -> Path to a WebP, or None when the profile has no such texture
    thumb(model) -> Path to a 256-pixel WebP picture of the mesh (search results)
    land_table() -> Path to land/land.json (land textures for the terrain splat)

CLI: python -m tools.places assets <verb> ...
    mesh <model> [--level N]      convert one mesh, print the GLB path and its facts
    tex <path> [--size N]         convert one texture
    warm <bundle_id|dir> ...      convert everything bundles use, in parallel; writes a report
    land                          every land texture to WebP, and out/places/assets/land/land.json
    catalogue                     out/places/catalogue/bases.jsonl across every source we hold
    render <model> <png>          an off-screen picture of a converted mesh (the proof)
    evict [--cap-mb N]            apply the cache cap now
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.places.assets import cache
from tools.places.assets import nifglb as _mesh
from tools.places.assets import dds as _tex
from tools.places.assets.resolve import default as resolver
from tools.places.assets.resolve import norm


RETRY = "retry"   # in the name of a placeholder that stands in for one call only (the conversion is tried again)


def _key(data: bytes, version: int) -> str:
    return hashlib.sha256(data + f"|v{version}".encode()).hexdigest()


_hashed: dict[tuple[str, int], tuple[tuple, str]] = {}   # (data path, version) -> (what it resolved to, its key)


def _source(k: str, version: int) -> tuple[str | None, bytes | None]:
    """A data path's cache key and, when they had to be read to make it, its bytes; (None, None) when the profile
    has no such file. The key is the hash of the source's bytes; it is worked out once per source file as it
    stands (the resolver's `ident`), so a request for something already converted reads no source at all."""
    r = resolver()
    ident = r.ident(k) if hasattr(r, "ident") else None
    hit = _hashed.get((k, version))
    if ident is not None and hit and hit[0] == ident:
        return hit[1], None
    raw = r.read(k)
    if raw is None:
        return None, None
    key = _key(raw, version)
    if ident is not None:
        _hashed[(k, version)] = (ident, key)
    return key, raw


def mesh_info(model: str, level: int = 0, bounds=None) -> dict:
    k = norm(model, "meshes")
    key, raw = _source(k, _mesh.VERSION)
    found = key is not None
    if not found:
        key = _key(("missing:" + k + json.dumps(bounds)).encode(), _mesh.VERSION)
    glb = cache.path("mesh", key, f"l{level}.glb")
    side = glb.with_suffix(".json")
    if glb.exists() and side.exists():
        cache.touch(glb)
        return json.loads(side.read_text()) | {"glb": str(glb)}
    with cache.lock(key):
        if glb.exists() and side.exists():
            return json.loads(side.read_text()) | {"glb": str(glb)}
        if not found:
            data, meta = _mesh.placeholder(bounds, "not found in the NewWorld profile (no loose file, no archive)")
        else:
            try:
                raw = resolver().read(k) if raw is None else raw
                data, meta = _mesh.build(_mesh.dump(raw, cache.root()), level)
            except _mesh.NotNow as e:  # not the mesh's fault: a placeholder for now, under a name no later call reads
                data, meta = _mesh.placeholder(bounds, str(e))
                meta["retry"] = True
                glb = cache.path("mesh", key, f"l{level}.{RETRY}.glb")
                side = glb.with_suffix(".json")
            except Exception as e:  # any reader failure becomes a listed placeholder, never a crash
                data, meta = _mesh.placeholder(bounds, f"{type(e).__name__}: {e}"[:300])
        meta = meta | {"model": k, "source": resolver().where(k), "bytes": len(data)}
        cache.write(side, json.dumps(meta).encode())
        cache.write(glb, data)
    return meta | {"glb": str(glb)}


def mesh(model: str, level: int = 0, bounds=None) -> Path:
    return Path(mesh_info(model, level, bounds)["glb"])


def tex_info(path: str, size: int = 512, keep_alpha: bool | None = None) -> dict | None:
    k = norm(path, "textures")
    key, raw = _source(k, 1)
    if key is None:
        return None
    size = _tex.clamp_size(size)
    if keep_alpha is None:
        stem = k.rsplit(".", 1)[0]
        keep_alpha = not (stem.endswith("_n") or stem.endswith("_msn"))
    out = cache.path("tex", key, f"{size}{'' if keep_alpha else 'o'}.webp")
    side = out.with_suffix(".json")
    if out.exists() and side.exists():
        cache.touch(out)
        return json.loads(side.read_text()) | {"webp": str(out)}
    with cache.lock(key):
        if not (out.exists() and side.exists()):
            data, meta = _tex.to_webp(resolver().read(k) if raw is None else raw, size, keep_alpha)
            meta |= {"path": k, "bytes": len(data)}
            cache.write(side, json.dumps(meta).encode())
            cache.write(out, data)
        else:
            meta = json.loads(side.read_text())
    return meta | {"webp": str(out)}


def tex(path: str, size: int = 512) -> Path | None:
    i = tex_info(path, size)
    return Path(i["webp"]) if i else None


def thumb(model: str, size: int = 256) -> Path:
    info = mesh_info(model, 1)
    key = Path(info["glb"]).name.split(".")[0]
    out = cache.path("thumb", key, f"{size}{'.' + RETRY if info.get('retry') else ''}.webp")
    if out.exists():
        cache.touch(out)
        return out
    with cache.lock(key):
        if not out.exists():
            from tools.places.assets import render
            import io
            buf = io.BytesIO()
            render.render(Path(info["glb"]).read_bytes(), size).save(buf, "WEBP", quality=80)
            cache.write(out, buf.getvalue())
    return out


def land_table() -> Path | None:
    p = cache.root() / "land" / "land.json"
    return p if p.exists() else None


def main(argv: list[str]) -> int:
    from tools.places.assets.cli import main as cli
    return cli(argv)
