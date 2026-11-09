"""Land textures for the studio's terrain splat: out/places/assets/land/.

Every land texture the bundles' terrains use (each bundle's terrain.json `ltex` map) and every land texture record
of the catalogue's sources (out/places/catalogue/ltex.jsonl), its diffuse as WebP at LAND_SIZE without alpha (a
land texture's alpha is specular, not cut-out), named by the record key (`Skyrim.esm_013876.webp`), and
land.json: {key: {edid, plugin, diffuse, file, avg, w, h}}, `file` relative to land/, `avg` the average colour
(the splat's colour at a distance and while a texture loads). A key whose diffuse the profile lacks gets
`file: null` and its reason; the front end draws it in a neutral colour."""
from __future__ import annotations

import json
import os
from pathlib import Path

from tools.places.assets import cache, dds
from tools.places.assets.resolve import default, norm

LAND_SIZE = 512


def bundles_dir() -> Path:
    return cache.root().parent / "bundles"


def gather() -> dict[str, dict]:
    out: dict[str, dict] = {}
    cat = cache.root().parent / "catalogue" / "ltex.jsonl"
    if cat.exists():
        for line in cat.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            out[r["key"]] = {"edid": r.get("edid"), "plugin": r.get("plugin"), "diffuse": r.get("diffuse")}
    for t in bundles_dir().glob("*/spaces/*/terrain.json"):
        for k, r in json.loads(t.read_text(encoding="utf-8")).get("ltex", {}).items():
            out[k] = {"edid": r.get("edid"), "plugin": r.get("plugin"), "diffuse": r.get("diffuse")}
    return out


def run() -> dict:
    d = cache.root() / "land"
    d.mkdir(parents=True, exist_ok=True)
    r = default()
    table, missing = {}, []
    for k, row in sorted(gather().items()):
        e = dict(row)
        name = k.replace(":", "_").replace(" ", "_") + ".webp"
        raw = r.read(norm(row["diffuse"], "textures")) if row.get("diffuse") else None
        if raw is None:
            e |= {"file": None, "why": "no diffuse in the record" if not row.get("diffuse") else "diffuse not in the NewWorld profile"}
            missing.append(k)
        else:
            try:
                data, meta = dds.to_webp(raw, LAND_SIZE, keep_alpha=False)
                tmp = d / f".{name}.tmp"
                tmp.write_bytes(data)
                os.replace(tmp, d / name)
                e |= {"file": name, "avg": meta["avg"], "w": meta["w"], "h": meta["h"]}
            except Exception as ex:
                e |= {"file": None, "why": f"{type(ex).__name__}: {ex}"[:200]}
                missing.append(k)
        table[k] = e
    (d / "land.json").write_text(json.dumps(table, indent=0))
    total = sum(p.stat().st_size for p in d.glob("*.webp"))
    return {"table": table, "summary": {"land_textures": len(table), "written": len(table) - len(missing),
                                        "missing": [{"key": k, "why": table[k]["why"], "diffuse": table[k].get("diffuse")} for k in missing],
                                        "bytes": total}}
