"""`draft render <place_id>`: top-down PNGs of the source and our draft side by side, at one scale.

Hillshaded ground, water, footprints (buildings filled, other things as dots by kind), paths, cleared plants (red
crosses), land patches (magenta squares), people's work spots (circles by role) and guard patrols; each cluster's
id at its centre on both sides, so the two views link. Written to out/places/renders/<place_id>/.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from tools.places.draft import geom, io
from tools.places.seat import STEP, Ground, foot_points

OUT = io.ROOT / "out" / "places" / "renders"
PX = 1000
KIND_COLOUR = {"building": (150, 95, 60), "static": (120, 120, 120), "clutter": (230, 200, 90), "light": (255, 240, 0),
               "furniture": (170, 120, 200), "door": (255, 255, 255), "container": (200, 140, 40),
               "tree": (20, 110, 30), "plant": (60, 160, 60), "rock": (90, 90, 90), "marker": (120, 140, 200)}
ROLE_COLOUR = {"guard": (220, 30, 30), "resident": (255, 255, 255), "boatman": (0, 200, 255), "carter": (200, 150, 0)}


def _canvas(g: Ground, centre, half: float):
    img = Image.new("RGB", (PX, PX), (0, 0, 0))
    px = img.load()
    scale = PX / (2 * half)
    step = max(1, int(PX / 250))
    for j in range(0, PX, step):
        for i in range(0, PX, step):
            x = centre[0] - half + (i + 0.5) / scale
            y = centre[1] + half - (j + 0.5) / scale
            h = g.height(x, y)
            if h is None:
                col = (30, 30, 30)
            else:
                nx, ny, nz = g.normal(x, y, STEP)
                shade = max(0.25, min(1.0, 0.5 + 0.6 * (-nx * 0.6 + ny * 0.6 + nz * 0.5)))
                w = g.water(x, y)
                if w is not None and h < w:
                    d = min(1.0, (w - h) / 512)
                    col = (int(40 - 20 * d), int(90 - 30 * d), int(150 - 20 * d))
                else:
                    base = (110, 120, 80)
                    col = tuple(int(c * shade) for c in base)
            for dj in range(step):
                for di in range(step):
                    if i + di < PX and j + dj < PX:
                        px[i + di, j + dj] = col

    def to(p):
        return ((p[0] - centre[0] + half) * scale, (centre[1] + half - p[1]) * scale)
    return img, ImageDraw.Draw(img), to, scale


def _refs(d, to, refs, bases, scale):
    for r in sorted(refs, key=lambda r: r.get("kind") != "building"):
        col = KIND_COLOUR.get(r.get("kind"), (180, 180, 180))
        f = geom.foot(r, bases)
        if f and r.get("kind") not in ("tree", "plant", "rock"):
            pts = foot_points(r["pos"][0], r["pos"][1], r["rot"][2], f, 2)
            quad = [pts[0], pts[1], pts[3], pts[2]]
            d.polygon([to(p) for p in quad], fill=col if r.get("kind") == "building" else None, outline=col)
        else:
            x, y = to(r["pos"])
            rad = 2 if r.get("kind") != "tree" else 3
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col)


def render(place_id: str, bundles: Path = io.BUNDLES, places: Path = io.PLACES, out: Path = OUT) -> list[Path]:
    pdir = places / place_id
    place = json.loads((pdir / "place.json").read_text())
    src = io.load(f"src.{place['source_id']}", bundles)
    grd = io.load(f"ground.{place_id}", bundles)
    bases = io.place_bases(src, grd, place)
    G = Ground.load(grd.path)
    G.apply_patches(io.read_jsonl(pdir / "land.jsonl"))
    refs = io.read_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl")
    fit = place["fit"]
    half = max(2048.0, place.get("radius_m", 100) * 70 * 1.25)
    out_dir = out / place_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # source
    piv = fit["pivot"]
    simg, sd, sto, sscale = _canvas(src.ground, piv, half)
    _refs(sd, sto, [r for r in src.exterior.refs if r.get("kind") != "actor"], bases, sscale)
    for c in fit.get("clusters_info", []):
        x, y = sto(c["centre"])
        sd.text((x + 4, y - 6), c["id"], fill=(255, 255, 255))
    sd.text((8, 8), f"source {place['source_id']}", fill=(255, 255, 255))

    # ours
    oimg, od, oto, oscale = _canvas(G, fit["anchor"], half)
    for p in io.read_jsonl(pdir / "paths.jsonl"):
        w = max(3, int(p["width"] * oscale))
        od.line([oto(q) for q in p["points"]], fill=(150, 100, 50) if p.get("kind") == "walkway" else (255, 170, 40),
                width=w)
    for p in io.read_jsonl(pdir / "land.jsonl"):
        cx, cy = p["cell"]
        big = max((abs(v[2]) for v in p["verts"]), default=0)
        half = max(2, 64 * oscale)
        for row, col, _ in p["verts"]:
            x, y = oto(((cx * 32 + col) * STEP, (cy * 32 + row) * STEP))
            od.rectangle([x - half, y - half, x + half, y + half], fill=(255, 0, 255))
        if p["verts"]:
            row, col, _ = p["verts"][0]
            x, y = oto(((cx * 32 + col) * STEP, (cy * 32 + row) * STEP))
            od.text((x + 6, y - 14), f"patch {len(p['verts'])} pts, max {big / 70:.1f} m", fill=(255, 0, 255))
    for c in io.read_jsonl(pdir / "clear.jsonl"):
        x, y = oto(c["pos"])
        od.line([x - 3, y - 3, x + 3, y + 3], fill=(255, 40, 40))
        od.line([x - 3, y + 3, x + 3, y - 3], fill=(255, 40, 40))
    for r in grd.exterior.refs if grd.exterior else []:
        if r.get("kind") == "tree":
            x, y = oto(r["pos"])
            od.point((x, y), fill=(10, 70, 20))
    _refs(od, oto, refs, bases, oscale)
    by_id = {r["id"]: r for r in refs}
    for p in io.read_jsonl(pdir / "people.jsonl"):
        col = ROLE_COLOUR.get(p["role"], (255, 160, 0))
        w = p.get("work") or {}
        pos = w.get("pos") or (by_id.get(w.get("ref"), {}).get("pos") if w.get("ref") else None)
        if p.get("patrol"):
            od.line([oto(q) for q in p["patrol"]["points"]], fill=col, width=1)
        if pos and w.get("space") == "exterior":
            x, y = oto(pos)
            od.ellipse([x - 6, y - 6, x + 6, y + 6], outline=col, width=2)
    for cid, c in fit["clusters"].items():
        info = next((i for i in fit.get("clusters_info", []) if i["id"] == cid), None)
        if info:
            xf = geom.Xf(c["pivot"], c["to"], c["rot"])
            x, y = oto(xf.pt(*info["centre"]))
            od.text((x + 4, y - 6), cid, fill=(255, 255, 255))
    od.text((8, 8), f"draft {place_id}  rot {fit['rot_deg']} deg  cost {fit['cost']}", fill=(255, 255, 255))
    od.text((8, 22), f"scale: {2 * half / 70:.0f} m across", fill=(255, 255, 255))

    both = Image.new("RGB", (2 * PX + 10, PX), (0, 0, 0))
    both.paste(simg, (0, 0))
    both.paste(oimg, (PX + 10, 0))
    paths = [out_dir / "side-by-side.png", out_dir / "draft.png", out_dir / "source.png"]
    both.save(paths[0])
    oimg.save(paths[1])
    simg.save(paths[2])
    return paths


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python -m tools.places draft render <place_id>")
        return 2
    for p in render(argv[0]):
        print(p)
    return 0

