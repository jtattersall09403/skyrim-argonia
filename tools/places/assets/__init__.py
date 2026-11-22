"""Meshes and textures for the studio's browser, converted on demand and cached; land textures; the catalogue.

API (lane V's server calls these for GET /api/asset/mesh and /api/asset/tex):
    mesh(model, level=0, bounds=None, alt=None) -> Path to a GLB   (always a file: a placeholder box when it cannot
                                                   convert; `alt` a base key: the model as its alternate textures draw it)
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


def swap_of(base_key: str | None) -> list[dict] | None:
    """A base's alternate textures (the catalogue's alt_tex, with our plugin's replacements: own_bases.alt_tex) as the
    converter applies them: [{shape, index,
    textures: {diffuse, normal} or None}] in a fixed order; None when the base swaps nothing."""
    if not base_key:
        return None
    from tools.places import draft_bundle, own_bases
    alt = own_bases.alt_tex(base_key, (draft_bundle.catalogue().get(base_key) or {}).get("alt_tex"))
    if not alt:
        return None
    return sorted(({"shape": a.get("shape") or "", "index": a.get("index"),
                    "textures": ({"diffuse": a["textures"].get("diffuse"), "normal": a["textures"].get("normal")}
                                 if a.get("textures") else None)} for a in alt), key=lambda a: (a["shape"], a["index"] or 0))


def mesh_info(model: str, level: int = 0, bounds=None, alt: str | None = None) -> dict:
    """`alt`: a base key whose alternate textures (swap_of) make its own variant of the model, kept under the swap's
    identity (the model's bytes and the swap), so bases sharing a model and a swap share one file and bases sharing
    a model with different swaps never collide."""
    k = norm(model, "meshes")
    key, raw = _source(k, _mesh.VERSION)
    found = key is not None
    swap = swap_of(alt)
    if not found:
        key = _key(("missing:" + k + json.dumps(bounds)).encode(), _mesh.VERSION)
    elif swap:
        key = _key((key + f"|swap{_mesh.SWAP_VERSION}:" + json.dumps(swap, sort_keys=True)).encode(), _mesh.VERSION)
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
                data, meta = _glb_as_is(raw) if raw[:4] == b"glTF" else _mesh.build(_mesh.dump(raw, cache.root()), level, swap)
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


def _glb_as_is(raw: bytes) -> tuple[bytes, dict]:
    """A model file that is already a GLB (the look audit's golden scene, tools/tests/fixtures/look_truth) is served
    as it is; its facts from its own accessors."""
    from tools.places.assets import glb
    j, _ = glb.read(raw)
    pos = [j["accessors"][p["attributes"]["POSITION"]] for m in j.get("meshes", []) for p in m["primitives"]]
    tris = sum(j["accessors"][p["indices"]]["count"] // 3 for m in j.get("meshes", []) for p in m["primitives"] if "indices" in p)
    lo = [min(a["min"][i] for a in pos) for i in range(3)] if pos else [-32] * 3
    hi = [max(a["max"][i] for a in pos) for i in range(3)] if pos else [32] * 3
    return raw, {"level": 0, "tris": tris, "tris_full": tris, "shapes": len(pos), "textures": [], "placeholder": False,
                 "bounds": [lo, hi]}


def mesh(model: str, level: int = 0, bounds=None, alt: str | None = None) -> Path:
    return Path(mesh_info(model, level, bounds, alt)["glb"])


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
    """The land texture table, brought level first with every land texture the bundles list (land.ensure)."""
    from tools.places.assets import land
    land.ensure()
    p = cache.root() / "land" / "land.json"
    return p if p.exists() else None


def main(argv: list[str]) -> int:
    from tools.places.assets.cli import main as cli
    return cli(argv)
