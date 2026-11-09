"""Convert everything bundles use, in parallel, so the studio opens fast; report what could not convert.

Per bundle (out/places/bundles/<id>/): every base's model (bounds kept for a placeholder), the grass models of its
terrain's land textures; level 0 of every mesh and level 1 of every tree, plant, ground cover and any mesh over the
light threshold; then every texture those meshes name, the diffuse at the requested size and the normal map at half.
The land textures follow (land.py). The report, out/places/assets/reports/warm-<ids>.json, lists each placeholder
mesh and each missing texture with its reason and the bases that use it, the counts, bytes and seconds."""
from __future__ import annotations

import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tools.places.assets import cache, nifglb

LIGHT_KINDS = {"tree", "plant", "groundcover"}


def bundle_dir(b: str) -> Path:
    p = Path(b)
    return p if p.is_dir() else cache.root().parent / "bundles" / b


def wanted(dirs: list[Path]) -> dict[str, dict]:
    """model -> {bounds, kinds, keys}"""
    out: dict[str, dict] = {}
    for d in dirs:
        for line in (d / "bases.jsonl").read_text(encoding="utf-8").splitlines():
            b = json.loads(line)
            if not b.get("model"):
                continue
            e = out.setdefault(b["model"].lower(), {"bounds": b.get("bounds"), "kinds": set(), "keys": []})
            e["kinds"].add(b.get("kind") or "other")
            e["keys"].append(b["key"])
        for t in d.glob("spaces/*/terrain.json"):
            for lt in json.loads(t.read_text(encoding="utf-8")).get("ltex", {}).values():
                for g in lt.get("grasses") or []:
                    if g.get("model"):
                        e = out.setdefault(g["model"].lower(), {"bounds": None, "kinds": set(), "keys": []})
                        e["kinds"].add("groundcover")
                        e["keys"].append(g["key"])
    return out


def _mesh(args):
    model, bounds, light = args
    os.nice(5)
    import tools.places.assets as A
    t = time.time()
    infos = [A.mesh_info(model, 0, bounds)]
    if light or infos[0]["tris"] > nifglb.LIGHT_TRIS:
        infos.append(A.mesh_info(model, 1, bounds))
    return model, infos, time.time() - t


def _tex(args):
    path, size = args
    os.nice(5)
    import tools.places.assets as A
    try:
        i = A.tex_info(path, size)
        return path, i, None if i else "not in the NewWorld profile"
    except Exception as e:
        return path, None, f"{type(e).__name__}: {e}"[:200]


def run(bundles: list[str], jobs: int = 3, size: int = 512) -> dict:
    t0 = time.time()
    dirs = [bundle_dir(b) for b in bundles]
    want = wanted(dirs)
    meshes, placeholders, users = {}, [], {}
    with ProcessPoolExecutor(jobs) as ex:
        for model, infos, _ in ex.map(_mesh, [(m, e["bounds"], bool(e["kinds"] & LIGHT_KINDS)) for m, e in sorted(want.items())], chunksize=4):
            meshes[model] = infos
            if infos[0].get("placeholder"):
                placeholders.append({"model": model, "why": infos[0]["why"], "bases": want[model]["keys"][:5]})
            for i in infos:
                for tx in i.get("textures", []):
                    users.setdefault(tx, set()).add(model)
        texs = sorted(users)
        jobs_t = [(p, size // 2 if p.rsplit(".", 1)[0].endswith(("_n", "_msn")) else size) for p in texs]
        tex_res = list(ex.map(_tex, jobs_t, chunksize=8))
    missing = [{"path": p, "why": why, "used_by": sorted(users[p])[:5]} for p, i, why in tex_res if not i]
    from tools.places.assets import land
    ls = land.run()["summary"]
    mesh_bytes = sum(i["bytes"] for infos in meshes.values() for i in infos)
    tex_bytes = sum(i["bytes"] for _, i, _ in tex_res if i)
    tris = {m: [i["tris"] for i in infos] for m, infos in meshes.items()}
    summary = {"bundles": bundles, "models": len(want), "converted": len(want) - len(placeholders),
               "placeholders": len(placeholders), "glb_files": sum(len(v) for v in meshes.values()),
               "simplified": sum(1 for v in meshes.values() if len(v) > 1 and v[1]["tris"] < v[0]["tris"]),
               "tris_level0": sum(v[0] for v in tris.values()), "textures": len(texs), "textures_missing": len(missing),
               "land_textures": ls["land_textures"], "land_written": ls["written"],
               "bytes": {"meshes": mesh_bytes, "textures": tex_bytes, "land": ls["bytes"]}, "seconds": round(time.time() - t0, 1)}
    rep = {"summary": summary, "placeholders": placeholders, "textures_missing": missing, "land_missing": ls["missing"],
           "heaviest": sorted(({"model": m, "tris": t} for m, t in tris.items()), key=lambda r: -r["tris"][0])[:20]}
    d = cache.root() / "reports"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"warm-{'+'.join(Path(b).name for b in bundles)}.json").write_text(json.dumps(rep, indent=1))
    return rep
