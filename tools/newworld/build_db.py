"""Build the new world's database from its sources, whole and deterministically.

Sources (all committed):
- `newworld/sources/key.json` — the map key and the lookups;
- the extraction: `out/newworld/symbols.json` (tools/newworld/consolidate.py), `out/newworld/cell_region.json`
  (regions.py), the rasters (raster.py), and, when built, `out/newworld/roads.json` and `borders.json` (roads.py);
- the research: `newworld/sources/research/cultures.json`, `regions/*.json` and `places/*.json`
  (written by the research passes; each record names the id it fills);
- the danger bands, derived by tools/newworld/danger.py from all of the above.

The tables in `newworld/story/data/db/` are this build's output: rerunning rewrites them whole, so a change is made
in a source and rebuilt, never in a table.

    python3 -m tools.newworld.build_db            # build and check (foreign keys, every place filled)
"""
from __future__ import annotations

import glob
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

from tools.argonia_world import db
from tools.newworld import danger
from tools.newworld import frame as f
from tools.newworld.regions import REGIONS

SRC = f.ROOT / "sources"
RESEARCH = SRC / "research"

# The cultures, by the glyph fill and square tint the map gives their places (measured, tools/newworld/consolidate.py).
# Names and identities come from the research (research/cultures.json); the ids name the colour.
CULTURE_COLOURS = [
    ("forest-green", (15, 79, 17), (119, 139, 97)),
    ("crimson-red", (237, 41, 57), (230, 120, 117)),
    ("rust", (180, 55, 0), (201, 127, 88)),
    ("rose", (255, 142, 151), (239, 171, 164)),
    ("stone-grey", (114, 108, 92), (168, 154, 134)),
    ("pale-green", (172, 225, 175), (197, 212, 176)),
    ("oxblood", (112, 11, 17), (167, 105, 97)),
    ("steel-blue", (123, 152, 196), (173, 176, 186)),
    ("jade", (0, 220, 127), (111, 210, 152)),
    ("plum", (105, 6, 128), (164, 103, 152)),
    ("umber", (67, 45, 45), (145, 122, 111)),
    ("sky-blue", (86, 219, 255), (154, 209, 216)),
    ("lime", (213, 250, 47), (218, 225, 112)),
    ("indigo", (47, 6, 128), (135, 103, 152)),
    ("olive", (94, 107, 0), (158, 156, 110)),
    ("magenta", (207, 37, 213), (215, 118, 195)),
    ("pearl", (233, 234, 236), (155, 148, 154)),
    ("gold", (220, 195, 115), (221, 197, 144)),
]

SHAPE_TIER = {"ringed-octagon": "metropolis", "heptagon": "large-city", "octagon": "large-city",
              "hexagon": "small-city", "pentagon": "town", "square": "village", "concentric-square": "village",
              "triangle": "outpost", "dot": "minor"}
TIER_KIND = {"metropolis": "city", "large-city": "city", "small-city": "city", "town": "town", "village": "village",
             "outpost": "outpost", "minor": "outpost"}
LABEL_KIND = [  # a settlement glyph's label decides its kind before its tier does
    (r"^fort |keep$", "fort"), (r"prison", "prison"), (r"^\[estate\]", "estate"), (r"^\[farm\]", "farm"),
    (r"^\[homestead\]", "homestead"), (r"^\[logging camp\]", "logging-camp"), (r"^\[quarry\]", "quarry"),
    (r"^\[mine\]", "mine"), (r"lighthouse", "lighthouse"), (r"ferry", "ferry"), (r"station$", "station"),
    (r"belvedere", "belvedere"), (r"^\[outpost\]", "outpost"),
]


def hexrgb(c) -> str:
    return "#%02x%02x%02x" % tuple(int(v) for v in c)


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def concentric(s: dict) -> bool:
    t = " ".join(str(s.get(k) or "") for k in ("note", "shape")).lower()
    return any(w in t for w in ("concentric", "ringed", "inner ring", "within square"))


def icon_symbol(s: dict) -> str:
    """The icon's family from the reader's name for it; the look-alike ruin families (named Direnni, Aldmer, Breton
    castle, green or brown by different readers) are told apart by the icon's measured colour: white glow is the
    Ayleid tree, dark timber the stilt hall, olive turf the Lilmothiit dome."""
    name = (s.get("icon") or "").lower()
    label = (s.get("label") or "").lower()
    c = s.get("icon_rgb") or [0, 0, 0]
    if name.startswith("mine") or "pick" in name:
        return "icon.mine"
    if name.startswith("camp"):
        return "icon.camp"
    if name.startswith("cave"):
        return "icon.cave"
    if name.startswith("landmark"):
        return "icon.landmark"
    if name.startswith("shipwreck"):
        return "icon.shipwreck"
    if any(w in name for w in ("spired", "spiky")):
        return "icon.sunken-ruin"
    if any(w in name for w in ("purple", "indigo")) and "brown" not in name:
        return "icon.velothi-ruin"
    if label.startswith("fort ") or label.endswith("keep") or "banner" in name:
        return "icon.imperial-keep"
    if any(w in name for w in ("empire", "yellow tower", "brown tower")):
        return "icon.imperial-ruin"
    if any(w in name for w in ("nord fortress", "breton crypt", "other ruin", "grey castle", "grey keep")):
        return "icon.kothringi-ruin"
    if any(w in name for w in ("white tree", "trident", "glowing", "aldmer", "direnni", "green dom", "breton castle",
                               "brown multi", "dark brown", "stilted", "brown castle")):
        if s.get("glow_share", 0) > 0.12:
            return "icon.ayleid-ruin"
        timber = c[0] > c[1] >= c[2] and c[0] - c[2] > 18 and c[0] < 110
        return "icon.abandoned-village" if timber else "icon.lilmothiit-ruin"
    raise ValueError(f"icon not classified: {s.get('icon')!r} at {s.get('cell')}")


def settlement_symbol(s: dict) -> tuple[str, str]:
    tier = SHAPE_TIER[s["shape"]]
    seat = concentric(s) and tier in ("small-city", "town", "village")
    return (f"settlement.{tier}-seat" if seat else f"settlement.{tier}"), tier


def culture_of(s: dict, settled: list[tuple[np.ndarray, str]]) -> str | None:
    """A settlement glyph's culture: the culture whose fill (or square tint, when measured) is nearest. A minor
    location's dot is too small to carry its colour reliably: it takes a colour only on a tight match, else the
    culture of the nearest larger settlement."""
    fill = np.array(s.get("fill_rgb") or [0, 0, 0])
    tint = np.array(s["tint_rgb"]) if s.get("tint_rgb") else None

    def dist(c):
        d = np.abs(np.array(c[1]) - fill).sum()
        if tint is not None:
            d = min(d, np.abs(np.array(c[2]) - tint).sum() + 40)
        return d
    best = min(CULTURE_COLOURS, key=dist)
    if dist(best) < (40 if s.get("shape") == "dot" else 90):
        return best[0]
    p = np.array([s["px"], s["py"]])
    near = min(settled, key=lambda t: np.hypot(*(t[0] - p))) if settled else None
    return near[1] if near else None


def load_json_dir(pattern: str) -> list[dict]:
    out = []
    for p in sorted(glob.glob(str(pattern))):
        d = json.loads(Path(p).read_text())
        out += d if isinstance(d, list) else d.get("records", [d])
    return out


def build() -> db.World:
    key = json.loads((SRC / "key.json").read_text())
    syms = json.loads((f.OUT / "symbols.json").read_text())
    cell_region = {tuple(map(int, k.split(","))): v for k, v in json.loads((f.OUT / "cell_region.json").read_text()).items()}
    water = np.asarray(Image.open(f.OUT / "raster" / "water.png").convert("L")) > 127

    root = f.ROOT
    dbdir = root / "story" / "data" / "db"
    dbdir.mkdir(parents=True, exist_ok=True)
    for p in dbdir.glob("*.jsonl"):
        p.unlink()
    w = db.open(root, cache=False)

    for table in ("statement_tier", "settlement_tier", "place_kind", "symbol", "road_class", "danger_band",
                  "terrain_need", "note_aspect", "water_kind"):
        w.insert_many(table, key[table])

    sources: dict[str, dict] = {}

    def source(kind: str, title: str, locator: str | None = None, url: str | None = None) -> str:
        sid = slug(f"{kind}-{locator or title}")[:80]
        sources.setdefault(sid, {"id": sid, "kind": kind, "title": title, "locator": locator, "url": url})
        return sid

    source("map", "Project Tamriel: Black Marsh map", "newworld/sources/maps/PT3-map-Black_Marsh.png",
           "https://en.uesp.net/wiki/File:PT3-map-Black_Marsh.png")

    w.insert_many("map_source", [
        {"id": "pt3-black-marsh", "title": "Project Tamriel: Black Marsh (created March 2022)",
         "file": "newworld/sources/maps/PT3-map-Black_Marsh.png",
         "url": "https://en.uesp.net/wiki/File:PT3-map-Black_Marsh.png", "licence": "Public domain",
         "width_px": f.WIDTH_PX, "height_px": f.HEIGHT_PX,
         "about": "Places, roads, water, borders and the cell grid with its rulers."},
        {"id": "pt3-black-marsh-regions", "title": "Project Tamriel: Black Marsh regions",
         "file": "newworld/sources/maps/PT3-map-Black_Marsh_Regions.png",
         "url": "https://en.uesp.net/wiki/File:PT3-map-Black_Marsh_Regions.png", "licence": "Public domain",
         "width_px": f.WIDTH_PX, "height_px": f.HEIGHT_PX,
         "about": "The same map with each region's cells tinted one colour and its name printed."},
        {"id": "pt3-key-hammerfell-high-rock", "title": "Project Tamriel: key of the Hammerfell and High Rock map",
         "file": "newworld/sources/maps/PT3-key-Hammerfell-High-Rock.png",
         "url": "https://en.uesp.net/wiki/Category:Project_Tamriel-Map_Images", "licence": "Public domain",
         "width_px": 590, "height_px": 868,
         "about": "The icon key and settlement tiers the Black Marsh map shares."},
    ])
    w.insert("map_frame", id="pt3", px_per_cell=f.PX_PER_CELL, cell_x0_px=f.X0_PX, cell_y0_px=f.Y0_PX,
             cell_units=f.CELL_UNITS, units_per_metre=f.UNITS_PER_METRE,
             about="Grid lines every 40 px from the image edge; the rulers print the absolute value of negative "
                   "coordinates. One map cell is one Morrowind cell (8192 units, two Skyrim cells a side); one "
                   "pixel is 204.8 units, 2.93 m.")

    # research
    cultures_r = {r["id"]: r for r in load_json_dir(RESEARCH / "cultures.json")}
    regions_r = {r["id"]: r for r in load_json_dir(RESEARCH / "regions" / "*.json")}
    places_r = {r["id"]: r for r in load_json_dir(RESEARCH / "places" / "*.json")}

    for cid, fill, tint in CULTURE_COLOURS:
        r = cultures_r.get(cid, {})
        w.insert("culture", id=cid, name=r.get("name", f"({cid} culture, unresearched)"), tint_hex=hexrgb(tint),
                 glyph_hex=hexrgb(fill), people=r.get("people", "unresearched"), about=r.get("about", "unresearched"),
                 why=r.get("why", "unresearched"), statement_tier_id=r.get("statement_tier_id", "EXTRAPOLATED"))

    # regions
    g = np.asarray(Image.open(f.REGION_MAP).convert("RGB")).astype(int)
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(int)
    by_region = defaultdict(list)
    for c, r in cell_region.items():
        by_region[r].append(c)
    region_cols = ("summary", "landform", "elevation_floor_m", "elevation_summit_m", "roughness_m", "cliff_share",
                   "wetness", "biome", "climate", "culture_id", "danger_band_id", "statement_tier_id")
    for rid, name, label, px, py, kind in REGIONS:
        cols = []
        for c in by_region[rid]:
            l, t, rr, b = f.cell_px_box(*c)
            A, G = a[t:b, l:rr], g[t:b, l:rr]
            plain = (np.abs(A - (216, 193, 177)).sum(-1) < 20)
            if plain.any():
                cols.append(np.median(G[plain], 0))
        if not cols:
            for c in by_region[rid]:
                l, t, rr, b = f.cell_px_box(*c)
                cols.append(np.median(g[t:b, l:rr].reshape(-1, 3), 0))
        r = regions_r.get(rid, {})
        w.insert("region", id=rid, name=name, map_label=label, kind=kind, map_hex=hexrgb(np.median(cols, 0)),
                 label_px=px, label_py=py, **{k: r.get(k) for k in region_cols})
        write_notes(w, "region", rid, r, source)

    # cells (their danger bands are set by danger.py once places and roads are in)
    for (x, y), rid in sorted(cell_region.items()):
        l, t, rr, b = f.cell_px_box(x, y)
        land = 1.0 - float(water[max(t, 0):b, max(l, 0):rr].mean())
        w.insert("cell", x=x, y=y, region_id=rid, land_share=round(land, 3))

    # places
    rows, seen = [], Counter()
    settled = []
    for s in syms:
        if s.get("glyph") == "settlement" and s.get("shape") != "dot":
            c = culture_of(s, [])
            settled.append((np.array([s["px"], s["py"]]), c))
    for s in syms:
        label = s.get("label")
        if s.get("glyph") == "settlement":
            sym, tier = settlement_symbol(s)
            kind = next((k for pat, k in LABEL_KIND if label and re.search(pat, label.lower())), TIER_KIND[tier])
            if kind == "outpost" and tier == "outpost" and label and not label.startswith("["):
                kind = "hamlet"
            culture = culture_of(s, settled)
        else:
            sym = icon_symbol(s)
            kind = next(k["place_kind_id"] for k in key["symbol"] if k["id"] == sym)
            if sym == "icon.camp" and label and any(w_ in label.lower() for w_ in ("pirate", "smuggler")):
                kind = "outlaw-camp"
            if sym == "icon.landmark" and label == "[Peak]":
                kind = "peak"
            culture = None
        cx, cy = f.px_to_cell(s["px"], s["py"])
        named = label and not label.startswith("[")
        base = slug(label) if named else f"{kind}-{cx}-{cy}".replace("--", "-m")
        seen[base] += 1
        pid = base if seen[base] == 1 else f"{base}-{seen[base]}"
        wx, wy = f.px_to_world(s["px"], s["py"])
        rows.append({"id": pid, "s": s, "sym": sym, "kind": kind, "culture": culture, "cell": (cx, cy),
                     "label": label, "named": named, "world": (wx, wy)})
    place_cols = ("status", "held_by", "population", "footprint_radius_m", "siting", "danger_band_id", "importance",
                  "summary", "lore_page", "statement_tier_id")
    for p in rows:
        s, r = p["s"], places_r.get(p["id"], {})
        cx, cy = p["cell"]
        region = cell_region.get((cx, cy)) or nearest_region(cell_region, cx, cy)
        name = r.get("name") or (title(p["label"]) if p["named"] else
                                 f"Unnamed {next(k['label'] for k in key['place_kind'] if k['id'] == p['kind']).lower()}")
        x, y = int(round(s["px"])), int(round(s["py"]))
        w.insert("place", id=p["id"], name=name, map_label=p["label"], symbol_id=p["sym"],
                 place_kind_id=r.get("place_kind_id", p["kind"]), culture_id=r.get("culture_id", p["culture"]),
                 region_id=region, cell_x=cx, cell_y=cy, px=s["px"], py=s["py"], world_x=round(p["world"][0], 1),
                 world_y=round(p["world"][1], 1), on_water=bool(water[y, x]), read_sure=bool(s.get("sure", True)),
                 **{k: r.get(k) for k in place_cols})
        for al in r.get("aliases", []):
            src = al.get("source")
            w.insert("place_alias", place_id=p["id"], alias=al["alias"],
                     source_id=source(src["kind"], src["title"], src.get("locator"), src.get("url")) if src else None)
        write_notes(w, "place", p["id"], r, source)
        for need in r.get("terrain_needs", []):
            w.insert("place_terrain_need", place_id=p["id"], terrain_need_id=need["id"], radius_m=need["radius_m"],
                     facing_deg=need.get("facing_deg"), why=need["why"])

    roads_and_borders(w)
    danger.assign(w)
    w.insert_many("source", sorted(sources.values(), key=lambda r: r["id"]))
    w.save()
    return w


def write_notes(w: db.World, kind: str, rid: str, r: dict, source) -> None:
    for n in r.get("notes", []):
        w.insert(f"{kind}_note", **{f"{kind}_id": rid}, aspect_id=n["aspect"], text=n["text"],
                 statement_tier_id=n["tier"])
        for s in n.get("sources", []):
            sid = source(s["kind"], s["title"], s.get("locator"), s.get("url"))
            key = (rid, n["aspect"], sid)
            if key in _note_sources:
                continue
            _note_sources.add(key)
            w.insert(f"{kind}_note_source", **{f"{kind}_id": rid}, aspect_id=n["aspect"], source_id=sid,
                     locator=s.get("section"))


_note_sources: set = set()


def title(label: str) -> str:
    return label if label != label.upper() else "-".join(p.capitalize() for p in label.split("-")).title() \
        if " " in label else "-".join(p.capitalize() for p in label.lower().split("-"))


def nearest_region(cell_region: dict, cx: int, cy: int) -> str:
    return min(cell_region.items(), key=lambda kv: math.dist(kv[0], (cx, cy)))[1]


def roads_and_borders(w: db.World) -> None:
    """Roads and borders from roads.py's output, when it has been built."""
    rp, bp = f.OUT / "roads.json", f.OUT / "borders.json"
    if not rp.exists():
        return
    water = np.asarray(Image.open(f.OUT / "raster" / "water.png").convert("L")) > 127
    rd = json.loads(rp.read_text())
    places = {(round(r.px), round(r.py)): r.id for r in w.rows("place")}
    syms = json.loads((f.OUT / "symbols.json").read_text())
    for n in rd["nodes"]:
        pid = None
        if n.get("place_index") is not None:
            s = syms[n["place_index"]]
            pid = places.get((round(s["px"]), round(s["py"])))
        wx, wy = f.px_to_world(n["px"], n["py"])
        w.insert("road_node", id=str(n["id"]), kind=n["kind"] if pid or n["kind"] != "place" else "end",
                 place_id=pid, px=n["px"], py=n["py"], world_x=round(wx, 1), world_y=round(wy, 1))
    for e in rd["edges"]:
        pts = e["points"]
        length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) * f.UNITS_PER_PX / f.UNITS_PER_METRE
        wet = [bool(water[min(max(int(round(y)), 0), f.HEIGHT_PX - 1), min(max(int(round(x)), 0), f.WIDTH_PX - 1)])
               for x, y in pts]
        wet_m = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1) if wet[i] and wet[i + 1]) \
            * f.UNITS_PER_PX / f.UNITS_PER_METRE
        w.insert("road", id=str(e["id"]), road_class_id=e["class"], from_node_id=str(e["from"]),
                 to_node_id=str(e["to"]), length_m=round(length, 1), crosses_water_m=round(wet_m, 1))
        for i, (x, y) in enumerate(pts):
            wx, wy = f.px_to_world(x, y)
            w.insert("road_vertex", road_id=str(e["id"]), seq=i, px=round(x, 2), py=round(y, 2),
                     world_x=round(wx, 1), world_y=round(wy, 1), on_water=wet[i])
    if bp.exists():
        bd = json.loads(bp.read_text())
        w.insert("border", id="province", kind="province", about="The province border: the map's thick red dash-dot line.")
        w.insert("border", id="regions", kind="region", about="The region borders: the map's navy dash-dot lines.")
        for bid, parts in (("province", bd.get("province", [])), ("regions", bd.get("region", []))):
            for k, part in enumerate(parts):
                for i, (x, y) in enumerate(part):
                    wx, wy = f.px_to_world(x, y)
                    w.insert("border_vertex", border_id=bid, part=k, seq=i, px=round(x, 2), py=round(y, 2),
                             world_x=round(wx, 1), world_y=round(wy, 1))


def main() -> None:
    w = build()
    n = {t: len(w.rows(t)) for t in ("region", "cell", "place", "culture", "symbol", "road", "road_vertex",
                                     "place_note", "region_note")}
    print(n)
    unfilled = [p.id for p in w.rows("place") if not p.summary]
    print(len(unfilled), "places without research yet")


if __name__ == "__main__":
    main()
