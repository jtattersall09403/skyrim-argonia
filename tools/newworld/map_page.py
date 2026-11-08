"""The new world's interactive map (nw-01 step 5): one self-contained page, `out/newworld/map/index.html`, built from
the database and the terrain, for a reader who knows nothing of the map. Published as a Claude Artifact.

Layers: the terrain (hillshade over the heightmap, water at the one water level; the water and land masks when no
terrain is built yet), Project Tamriel's original map for comparison, regions, danger bands per cell, roads, borders,
places (coloured by culture, shaped by kind). Tapping a place or a region opens everything researched about it, in
words: ids and codes are turned into names.

    python3 -m tools.newworld.map_page        # out/newworld/map/index.html
"""
from __future__ import annotations

import json
from collections import defaultdict

import numpy as np
from PIL import Image

from tools.argonia_world import db
from tools.newworld import frame as f

OUT = f.OUT / "map"
TEMPLATE = f.REPO / "tools" / "newworld" / "map_page.html"
SCALE = 0.5          # image layers at half the map's resolution (1760 x 1420 px): 5.9 m a pixel


def terrain_image(scale: float = SCALE) -> tuple[Image.Image, str]:
    """The terrain layer at map pixels: shaded relief and water depth from the built heightmap, resampled onto the
    map frame; the masks alone when no terrain is built."""
    SCALE = scale  # noqa: N806 (the module default, overridden for the tile pyramid)
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
        col, row = np.round(col).astype(int), np.round(row).astype(int)
        built = (col >= 0) & (col < hm.shape[1]) & (row >= 0) & (row < hm.shape[0])
        col = np.clip(col, 0, hm.shape[1] - 1)
        row = np.clip(row, 0, hm.shape[0] - 1)
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
        # beyond the built heightmap (the map's margins, the north past the terrain's scope) the ground is read
        # from the map's own masks, never stretched from the heightmap's edge
        rgb[~built] = masks_rgb(water, foreign)[~built]
        return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), "terrain"
    return Image.fromarray(masks_rgb(water, foreign)), "masks"


KIND_LABEL = {"ocean": "Open sea", "shallow-coast": "Shallow coast", "bay": "Bay", "estuary": "Estuary",
              "river": "River", "stream": "Stream", "lake": "Lake", "pond": "Pond", "green-marsh": "Green marsh",
              "blackwater-swamp": "Blackwater swamp"}


def water_layer(region_names: dict) -> list:
    """The classified water bodies (tools/newworld/water_kinds.py) for the water editor, indexed by their number in
    the body raster (published beside the page as water_index.png at full resolution, for tapping)."""
    js = f.OUT / "water_classified.json"
    if not js.exists():
        return []
    rows = json.loads(js.read_text())
    by_id = {b["id"]: b["raster_index"] for b in rows}
    out = [None] * (len(rows) + 1)
    for b in rows:
        out[b["raster_index"]] = [b["id"], b["water_kind_id"], int(bool(b["flows"])), b.get("flow_deg"), b["speed"],
                                  round(b["label_px"] * SCALE, 1), round(b["label_py"] * SCALE, 1),
                                  round(b["area_m2"] / 1e4, 2), region_names.get(b.get("region_id"), "the margin"),
                                  b["why"], by_id.get(b.get("downstream_id")), b.get("name"), b.get("set_by"),
                                  b.get("width_m")]
    return out


def masks_rgb(water: np.ndarray, foreign: np.ndarray) -> np.ndarray:
    """Land, foreign land and water from the raster masks alone, flat colours."""
    rgb = np.zeros(water.shape + (3,), np.uint8)
    rgb[~water] = (150, 156, 112)
    rgb[foreign & ~water] = (128, 126, 118)
    rgb[water] = (70, 108, 122)
    return rgb


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


TILE = 512
TERRAIN_SCALE = 1.6        # the heightmap's own resolution: 128 units a sample against 204.8 a map pixel


def pyramid(img: Image.Image, native: float, name: str, q: int = 80) -> dict:
    """A tile pyramid of `img` (map pixels x `native`): 512 px WebP tiles at native, native/2, ... down to a level
    that fits in two tiles; out/newworld/map/tiles/<name>/<level>/<col>_<row>.webp. Returns the level table the page
    reads (scale = image px per page unit, the page working at SCALE map px a unit)."""
    levels, cur, z = [], img, 0
    while True:
        levels.append(cur)
        if max(cur.size) <= 2 * TILE:
            break
        cur = cur.resize((max(1, cur.width // 2), max(1, cur.height // 2)), Image.LANCZOS)
    levels.reverse()
    meta = []
    for z, im in enumerate(levels):
        d = OUT / "tiles" / name / str(z)
        d.mkdir(parents=True, exist_ok=True)
        cols, rows = -(-im.width // TILE), -(-im.height // TILE)
        for c in range(cols):
            for r in range(rows):
                im.crop((c * TILE, r * TILE, min(im.width, (c + 1) * TILE), min(im.height, (r + 1) * TILE))) \
                    .save(d / f"{c}_{r}.webp", "WEBP", quality=q, method=5)
        sc = native / (2 ** (len(levels) - 1 - z)) / SCALE
        meta.append({"z": z, "s": round(sc, 6), "c": cols, "r": rows, "w": im.width, "h": im.height})
    return {"name": name, "tile": TILE, "levels": meta}


def water_shapes(rows: list) -> dict:
    """Every water body's outline traced from the full-resolution body raster (sub-pixel, lightly smoothed), in page
    units, so the water stays crisp at any zoom: {raster index: [ring, ...]} with each ring a flat [x, y, ...]."""
    from skimage.measure import approximate_polygon, find_contours
    from scipy import ndimage as ndi
    r = np.asarray(Image.open(f.OUT / "water_classified.png")).astype(np.int32)
    out = {}
    for k, sl in enumerate(ndi.find_objects(r), 1):
        if sl is None:
            continue
        y0, x0 = max(sl[0].start - 2, 0), max(sl[1].start - 2, 0)
        m = (r[y0:sl[0].stop + 2, x0:sl[1].stop + 2] == k).astype(np.float32)
        m = ndi.gaussian_filter(m, 1.2)
        rings = []
        for c in find_contours(m, 0.5):
            c = approximate_polygon(c, 0.25)
            if len(c) < 3:
                continue
            xy = np.empty(2 * len(c))
            xy[0::2] = (c[:, 1] + x0 + 0.5) * SCALE
            xy[1::2] = (c[:, 0] + y0 + 0.5) * SCALE
            rings.append(np.round(xy, 2).tolist())
        if rings:
            out[k] = rings
    return out


def main() -> None:
    import shutil
    Image.MAX_IMAGE_PIXELS = None
    w = db.open(f.ROOT, cache=False)
    if (OUT / "tiles").exists():
        shutil.rmtree(OUT / "tiles")
    terr, kind = terrain_image(TERRAIN_SCALE)
    tiles = {"terrain": pyramid(terr, TERRAIN_SCALE, "terrain")}
    pt = Image.open(f.BASE_MAP).convert("RGB")
    tiles["pt"] = pyramid(pt, 1.0, "pt", 78)
    d = data(w)
    d["terrainKind"] = kind
    d["size"] = [int(f.WIDTH_PX * SCALE), int(f.HEIGHT_PX * SCALE)]
    d["tiles"] = tiles
    html = TEMPLATE.read_text()
    wb = water_layer(d["regionNames"])
    d["water"] = {"bodies": wb, "kinds": KIND_LABEL, "scale": SCALE}
    OUT.mkdir(parents=True, exist_ok=True)
    if wb:
        rows = json.loads((f.OUT / "water_classified.json").read_text())
        (OUT / "water_shapes.json").write_text(json.dumps(water_shapes(rows), separators=(",", ":")))
        r = np.asarray(Image.open(f.OUT / "water_classified.png")).astype(np.int32)
        rgb = np.zeros(r.shape + (3,), np.uint8)
        rgb[..., 0], rgb[..., 1] = r % 256, r // 256          # body number = red + 256 * green, for tapping
        Image.fromarray(rgb).save(OUT / "water_index_rgb.png", optimize=True)
        arrows = json.loads((f.OUT / "water_arrows.json").read_text()) if (f.OUT / "water_arrows.json").exists() else []
        (OUT / "water_arrows.json").write_text(json.dumps(
            [[round(x * SCALE, 1), round(y * SCALE, 1), deg, k] for x, y, deg, k in arrows], separators=(",", ":")))
    html = html.replace("/*__DATA__*/null", json.dumps(d, separators=(",", ":")))
    (OUT / "index.html").write_text(html)
    files = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file() and p.name != "index.html")
    print(f"{OUT / 'index.html'}: {len(html) / 1e6:.1f} MB; terrain layer from {kind}; {len(files)} supporting files")


if __name__ == "__main__":
    main()
