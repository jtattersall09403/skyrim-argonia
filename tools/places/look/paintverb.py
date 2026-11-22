"""`look <place> paint ...`: an agent's ground paint, one paint.add op per call (a stroke of the session, undone by
`undo`, written by `commit`), by the rule of tools/places/paint.py.

    paint textures [--near x,y]                 the palette: land textures the world and the source use, most used first
    paint <texture> --circle x,y,r              a dab: everything within r
    paint <texture> --polygon x,y;x,y;x,y...    an area, its edge feathered over --size * --softness
    paint <texture> --stroke x,y;x,y;...        a stroke of radius --size along the points (x,y,pressure allowed)
    paint --erase (--circle|--polygon|--stroke) ...   takes earlier paint away: the world's own paint shows again
    options: --brush soft|hard|scatter (soft) --size u (256) --softness 0..1 --strength 0..1 (1) --seed n
             --why "<why>" (required)

A texture is named by its key (plugin:formid), its editor id, or a word of its editor id or file that names one
texture of the palette (`silt`, `river_mud`)."""
from __future__ import annotations

import json
import random
from collections import Counter

from tools.places import paint

FLAGS = {"circle": True, "polygon": True, "stroke": True, "brush": True, "size": True, "softness": True,
         "strength": True, "seed": True, "why": True, "erase": False, "near": True}


def palette(place_id: str, files: dict, out) -> list[dict]:
    """The land textures the place may paint: those of its ground's cells and of its source's, most used first (the
    nearest the place's anchor first among equals). [{key, edid, diffuse, name, used}]"""
    got: dict = {}
    count: Counter = Counter()
    for bid in (f"ground.{place_id}", f"src.{files['place'].get('source_id')}"):
        f = out / "bundles" / bid / "spaces" / "exterior" / "terrain.json"
        if not f.exists():
            continue
        t = json.loads(f.read_text())
        for k, v in (t.get("ltex") or {}).items():
            got.setdefault(k, v)
        for c in t.get("cells") or []:
            for la in c.get("layers") or []:
                if la.get("tex"):
                    count[la["tex"]] += 1
    return [{"key": k, "edid": v.get("edid"), "diffuse": v.get("diffuse"), "name": plain(v.get("edid") or v.get("diffuse") or k),
             "used": count[k]} for k, v in sorted(got.items(), key=lambda kv: (-count[kv[0]], kv[0]))]


def plain(s: str) -> str:
    """A land texture's plain name: `ANW_Ground_river_mud~coast` -> `river mud (coast)`."""
    s = str(s or "").replace("ANW_Ground_", "").rsplit("/", 1)[-1].replace(".dds", "")
    base, _, var = s.partition("~")
    name = base.replace("_", " ").strip()
    return f"{name} ({var.replace('-', ' ')})" if var else name


def resolve(word: str, pal: list[dict]) -> str:
    if ":" in word:
        return word
    w = word.lower()
    exact = [t for t in pal if (t["edid"] or "").lower() in (w, "anw_ground_" + w)]
    if len(exact) == 1:
        return exact[0]["key"]
    hits = [t for t in pal if w in (t["edid"] or "").lower() or w in (t["diffuse"] or "").lower() or w in t["name"]]
    if len({t["key"] for t in hits}) == 1:
        return hits[0]["key"]
    if not hits:
        raise ValueError(f"paint: no land texture of the palette is named {word!r} (`paint textures` lists them)")
    raise ValueError(f"paint: {word!r} names {len(hits)} textures: " + ", ".join(f"{t['edid'] or t['key']}" for t in hits[:12]))


def _pts(s: str) -> list[list[float]]:
    return [[float(v) for v in p.split(",")] for p in s.split(";") if p.strip()]


def run(sc, args: list[str], out) -> list[dict] | dict:
    """The paint verb: the palette (a dict to print) or one stroke's ops."""
    from tools.places.look.verbs import _opts
    pos, o = _opts(args, FLAGS)
    pal = palette(sc.place_id, sc.files, out)
    if pos[:1] == ["textures"]:
        return {"textures": [{k: t[k] for k in ("key", "name", "edid", "used")} for t in pal]}
    why = str(o.get("why") or "").strip()
    if not why:
        raise ValueError('paint needs --why "<why>"')
    row: dict = {"id": paint.next_id(sc.files.get("paint") or []), "brush": o.get("brush", "soft"), "by": "agent", "why": why}
    if o.get("erase"):
        row["erase"] = True
    else:
        if not pos:
            raise ValueError("paint <texture> (--circle x,y,r | --polygon x,y;x,y;... | --stroke x,y;x,y;...) --why ...")
        row["texture"] = resolve(pos[0], pal)
    for k in ("size", "softness", "strength"):
        if k in o:
            row[k] = float(o[k])
    if row["brush"] == "scatter":
        row["seed"] = int(o.get("seed", random.randrange(1 << 16)))
    if "circle" in o:
        x, y, r = (float(v) for v in o["circle"].split(","))
        row["size"], row["points"] = r, [[x, y, 1.0]]
    elif "polygon" in o:
        row["polygon"] = [p[:2] for p in _pts(o["polygon"])]
        row.setdefault("size", 256.0)
    elif "stroke" in o:
        row["points"] = [p[:3] if len(p) > 2 else p[:2] + [1.0] for p in _pts(o["stroke"])]
        row.setdefault("size", 256.0)
    else:
        raise ValueError("paint: give --circle x,y,r, --polygon x,y;x,y;... or --stroke x,y;x,y;...")
    row.setdefault("size", 256.0)
    paint.check_row(row)
    return [{"op": "paint.add", "paint": row, "call": "fault", "note": why}]
