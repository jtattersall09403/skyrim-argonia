"""The chart's tile pyramid for the view (1.12 look 1: sharp when zoomed in, smooth to pan).

The view draws only the tiles it shows, from the level whose pixels are nearest one to one on the screen, so a close
zoom reads the largest render and the whole province the smallest. Two flattened layers per level, from the render's
own composites (tools/chart/__main__.py `flatten`): `sketch` (base and ink: the land not yet explored) and `full`
(base, revealed and ink: the explored land, masked per cell by the view). Made at install from the player's own
render (decision 0014), as the layers are; nothing here is committed.

    tiles(sources, out) -> {"tile": TILE, "levels": [1024, 2048, ...]}
        sources: {layer: largest render path}, e.g. {"sketch": out/chart/sketch-<master>.png, "full": ...}
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

TILE = 512          # tile side in pixels (a pixel count, not a Skyrim unit)
SMALLEST = 1024     # the whole province at zoom 1 on a 1080p sheet needs about this many pixels


def levels_for(top: int) -> list[int]:
    """The pyramid's level sides from SMALLEST up to the largest render, doubling."""
    out, s = [], SMALLEST
    while s <= top:
        out.append(s)
        s *= 2
    return out


def tiles(sources: dict[str, Path], out: Path) -> dict:
    Image.MAX_IMAGE_PIXELS = None   # our own largest render (twice the master)
    tops = {}
    for layer, src in sources.items():
        stamp = out / layer / ".source"
        key = f"{src.resolve()} {src.stat().st_mtime_ns}"
        im = Image.open(src).convert("RGB")
        tops[layer] = im.width
        if stamp.exists() and stamp.read_text() == key:
            continue
        for s in levels_for(im.width):
            lv = im if s == im.width else im.resize((s, s), Image.LANCZOS)
            d = out / layer / str(s)
            d.mkdir(parents=True, exist_ok=True)
            for ty in range(0, s, TILE):
                for tx in range(0, s, TILE):
                    lv.crop((tx, ty, tx + TILE, ty + TILE)).save(d / f"{tx // TILE}-{ty // TILE}.png", compress_level=6)
        stamp.write_text(key)
    top = min(tops.values())
    return {"tile": TILE, "levels": levels_for(top)}
