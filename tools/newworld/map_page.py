"""The new world's interactive map (nw-01 step 5): one self-contained page, `out/newworld/map/index.html`, built from
the database and the terrain, for a reader who knows nothing of the map. Published as a Claude Artifact.

Layers: the terrain (hillshade over the heightmap, water at the one water level; the water and land masks when no
terrain is built yet), Project Tamriel's original map for comparison, regions, danger bands per cell, roads, borders,
places (coloured by culture, shaped by kind). Tapping a place or a region opens everything researched about it, in
words: ids and codes are turned into names.

    python3 -m tools.newworld.map_page        # out/newworld/map/index.html
"""
from __future__ import annotations

import base64
import io
import json
from collections import defaultdict

import numpy as np
from PIL import Image

from tools.argonia_world import db
from tools.newworld import frame as f

OUT = f.OUT / "map"
TEMPLATE = f.REPO / "tools" / "newworld" / "map_page.html"
SCALE = 0.5          # image layers at half the map's resolution (1760 x 1420 px): 5.9 m a pixel


def jpeg(img: Image.Image, q: int = 82) -> str:
    b = io.BytesIO()
    img.convert("RGB").save(b, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def png(img: Image.Image) -> str:
    b = io.BytesIO()
    img.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def terrain_image() -> tuple[Image.Image, str]:
    """The terrain layer at map pixels: shaded relief and water depth from the built heightmap, resampled onto the
    map frame; the masks alone when no terrain is built."""
    w, h = int(f.WIDTH_PX * SCALE), int(f.HEIGHT_PX * SCALE)
    tb = f.OUT / "terrain" / "build.json"
    water = np.asarray(Image.open(f.OUT / "raster" / "water.png").convert("L").resize((w, h))) > 127
    foreign = np.asarray(Image.open(f.OUT / "raster" / "foreign.png").convert("L").resize((w, h))) > 127
    if tb.exists():
        b = json.loads(tb.read_text())
        hm = np.load(f.OUT / "terrain" / "heightmap.npy").astype(np.float32)     # game units
        z = hm / f.UNITS_PER_METRE
        level = b["water_level_units"] / f.UNITS_PER_METRE
        # map pixel centres -> world -> heightmap sample
        ys, xs = np.mgrid[0:h, 0:w]
        wx, wy = f.px_to_world((xs + 0.5) / SCALE, (ys + 0.5) / SCALE)
        col = (wx - b["origin_world_x"]) / b["sample_units"]
        row = (b["origin_world_y"] - wy) / b["sample_units"]
        col = np.clip(np.round(col).astype(int), 0, hm.shape[1] - 1)
        row = np.clip(np.round(row).astype(int), 0, hm.shape[0] - 1)
        zz = z[row, col] - level
        gy, gx = np.gradient(zz)
        px_m = 1 / SCALE * f.UNITS_PER_PX / f.UNITS_PER_METRE
        nx, ny = -gx / px_m, -gy / px_m
        shade = np.clip((nx * -0.6 + ny * 0.6 + 1) / np.sqrt(nx * nx + ny * ny + 1), 0, 1.4)
        hi = np.clip(zz / 120, 0, 1)
        land = np.stack([110 + 100 * hi, 128 + 70 * hi, 84 + 90 * hi], -1)
        deep = np.clip(-zz / 25, 0, 1)
        sea = np.stack([92 - 50 * deep, 132 - 60 * deep, 140 - 40 * deep], -1)
        rgb = np.where((zz > 0)[..., None], land * shade[..., None], sea)
        rgb[foreign & (zz > 0)] = rgb[foreign & (zz > 0)] * 0.55 + 70
        return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), "terrain"
    rgb = np.zeros((h, w, 3), np.uint8)
    rgb[~water] = (150, 156, 112)
    rgb[foreign & ~water] = (128, 126, 118)
    rgb[water] = (70, 108, 122)
    return Image.fromarray(rgb), "masks"


def data(w: db.World) -> dict:
    kinds = {k.id: k for k in w.rows("place_kind")}
    tiers = {t.id: t for t in w.rows("statement_tier")}
    aspects = {a.id: a.about for a in w.rows("note_aspect")}
    bands = {b.id: b for b in w.rows("danger_band")}
    sources = {s.id: s for s in w.rows("source")}
    cultures = {c.id: c for c in w.rows("culture")}
    regions = {r.id: r for r in w.rows("region")}
    symbols = {s.id: s for s in w.rows("symbol")}
    needs = {n.id: n.about for n in w.rows("terrain_need")}

    def notes(table: str, key: str, rid: str) -> list:
        out = []
        srcs = defaultdict(list)
        for s in w.rows(f"{table}_note_source", **{key: rid}):
            src = sources[s.source_id]
            srcs[s.aspect_id].append({"t": src.title, "u": src.url, "k": src.kind, "s": s.locator})
        order = list(aspects)
        for n in sorted(w.rows(f"{table}_note", **{key: rid}), key=lambda n: order.index(n.aspect_id)):
            out.append({"a": n.aspect_id.capitalize(), "t": n.text, "tier": n.statement_tier_id,
                        "src": srcs.get(n.aspect_id, [])})
        return out

    def band(b):
        return f"{b} · {bands[b].label}" if b else None

    places = []
    for p in w.rows("place"):
        places.append({
            "id": p.id, "n": p.name, "label": p.map_label, "x": round(p.px * SCALE, 1), "y": round(p.py * SCALE, 1),
            "kind": kinds[p.place_kind_id].label, "fam": kinds[p.place_kind_id].family, "kid": p.place_kind_id,
            "sym": symbols[p.symbol_id].label, "symid": p.symbol_id,
            "cul": p.culture_id, "reg": p.region_id, "cell": [p.cell_x, p.cell_y],
            "skyrim_cell": [int(p.world_x // f.SKYRIM_CELL_UNITS), int(p.world_y // f.SKYRIM_CELL_UNITS)],
            "world": [round(p.world_x), round(p.world_y)], "water": p.on_water, "sure": p.read_sure,
            "status": p.status, "held": p.held_by, "pop": p.population, "radius": p.footprint_radius_m,
            "siting": p.siting, "band": band(p.danger_band_id), "bandid": p.danger_band_id, "imp": p.importance,
            "sum": p.summary, "lore": p.lore_page, "tier": p.statement_tier_id,
            "alias": [a.alias for a in w.rows("place_alias", place_id=p.id)],
            "needs": [{"n": needs[t.terrain_need_id], "r": t.radius_m, "why": t.why}
                      for t in w.rows("place_terrain_need", place_id=p.id)],
            "notes": notes("place", "place_id", p.id),
        })
    regs = []
    for r in w.rows("region"):
        regs.append({"id": r.id, "n": r.name, "kind": r.kind, "hex": r.map_hex, "x": r.label_px * SCALE,
                     "y": r.label_py * SCALE, "sum": r.summary, "landform": r.landform,
                     "elev": [r.elevation_floor_m, r.elevation_summit_m], "biome": r.biome, "climate": r.climate,
                     "cul": r.culture_id, "band": band(r.danger_band_id), "tier": r.statement_tier_id,
                     "notes": notes("region", "region_id", r.id)})
    cells = [[c.x, c.y, c.region_id, c.danger_band_id, round(c.land_share, 2), c.danger_why]
             for c in w.rows("cell")]
    roads = []
    for r in w.rows("road"):
        pts = [(v.px * SCALE, v.py * SCALE) for v in w.rows("road_vertex", road_id=r.id)]
        roads.append({"c": r.road_class_id, "p": [round(v, 1) for xy in simplify(pts, 0.6) for v in xy],
                      "len": r.length_m})
    borders = defaultdict(list)
    for v in w.rows("border_vertex"):
        borders[(v.border_id, v.part)].append((v.px * SCALE, v.py * SCALE))
    bl = [{"k": k[0], "p": [round(v, 1) for xy in simplify(pts, 0.8) for v in xy]} for k, pts in borders.items()]
    frame = {"x0": f.X0_PX * SCALE, "y0": f.Y0_PX * SCALE, "cell": f.PX_PER_CELL * SCALE}
    return {
        "places": places, "regions": regs, "cells": cells, "roads": roads, "borders": bl, "frame": frame,
        "cultures": {c.id: {"n": c.name, "hex": c.glyph_hex, "tint": c.tint_hex, "people": c.people,
                            "about": c.about, "why": c.why, "tier": c.statement_tier_id} for c in cultures.values()},
        "bands": {b.id: {"label": b.label, "about": b.about, "level": b.foe_level} for b in bands.values()},
        "tiers": {t.id: t.about for t in tiers.values()},
        "kinds": {k.id: {"label": k.label, "about": k.about, "fam": k.family} for k in kinds.values()},
        "symbols": [{"id": s.id, "label": s.label, "glyph": s.glyph, "pt": s.pt_key_name, "meaning": s.meaning,
                     "why": s.why, "tier": s.statement_tier_id} for s in symbols.values()],
        "regionNames": {r.id: r.name for r in regions.values()},
    }


def simplify(pts: list, tol: float) -> list:
    """Douglas-Peucker."""
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0]), np.array(pts[-1])
    ab = b - a
    n = np.hypot(*ab) or 1e-9
    d = [abs(ab[0] * (p[1] - a[1]) - ab[1] * (p[0] - a[0])) / n for p in pts[1:-1]]
    i = int(np.argmax(d))
    if d[i] > tol:
        return simplify(pts[:i + 2], tol)[:-1] + simplify(pts[i + 1:], tol)
    return [pts[0], pts[-1]]


def main() -> None:
    w = db.open(f.ROOT, cache=False)
    terr, kind = terrain_image()
    pt = Image.open(f.BASE_MAP).convert("RGB").resize(terr.size, Image.LANCZOS)
    d = data(w)
    d["terrainKind"] = kind
    d["size"] = list(terr.size)
    html = TEMPLATE.read_text()
    html = html.replace("/*__DATA__*/null", json.dumps(d, separators=(",", ":")))
    html = html.replace("__TERRAIN__", jpeg(terr)).replace("__PTMAP__", jpeg(pt, 78))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(html)
    print(f"{OUT / 'index.html'}: {len(html) / 1e6:.1f} MB; terrain layer from {kind}")


if __name__ == "__main__":
    main()
