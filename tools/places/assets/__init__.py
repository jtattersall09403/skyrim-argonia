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


def _key(data: bytes, version: int) -> str:
    return hashlib.sha256(data + f"|v{version}".encode()).hexdigest()


def mesh_info(model: str, level: int = 0, bounds=None) -> dict:
    k = norm(model, "meshes")
    raw = resolver().read(k)
    if raw is None:
        key = _key(("missing:" + k + json.dumps(bounds)).encode(), _mesh.VERSION)
    else:
        key = _key(raw, _mesh.VERSION)
    glb = cache.path("mesh", key, f"l{level}.glb")
    side = glb.with_suffix(".json")
    if glb.exists() and side.exists():
        cache.touch(glb)
        return json.loads(side.read_text()) | {"glb": str(glb)}
    with cache.lock(key):
        if glb.exists() and side.exists():
            return json.loads(side.read_text()) | {"glb": str(glb)}
        if raw is None:
            data, meta = _mesh.placeholder(bounds, "not found in the NewWorld profile (no loose file, no archive)")
        else:
            try:
                data, meta = _mesh.build(_mesh.dump(raw, cache.root()), level)
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
    raw = resolver().read(k)
    if raw is None:
        return None
    size = _tex.clamp_size(size)
    if keep_alpha is None:
        stem = k.rsplit(".", 1)[0]
        keep_alpha = not (stem.endswith("_n") or stem.endswith("_msn"))
    key = _key(raw, 1)
    out = cache.path("tex", key, f"{size}{'' if keep_alpha else 'o'}.webp")
    side = out.with_suffix(".json")
    if out.exists() and side.exists():
        cache.touch(out)
        return json.loads(side.read_text()) | {"webp": str(out)}
    with cache.lock(key):
        if not (out.exists() and side.exists()):
            data, meta = _tex.to_webp(raw, size, keep_alpha)
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
    out = cache.path("thumb", key, f"{size}.webp")
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
