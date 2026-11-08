"""Reading tiles of the base map: 10 x 10 cell blocks with one cell of overlap, upscaled 2x, each framed by rulers
that print every cell's true coordinate (negative signs included), so a reader names a symbol's cell without
counting. Only blocks that touch the province (a cell the regions map tints) are cut.

    python3 -m tools.newworld.tiles     # out/newworld/tiles/tile_<x0>_<y0>.png and tiles.json
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tools.newworld import frame as f

BLOCK = 10
PAD = 1        # overlap in cells on every side
SCALE = 2
RULER = 44     # px of ruler on the upscaled tile


def scope_cells() -> set[tuple[int, int]]:
    """Cells the regions map tints: the province and its seas (the regions map differs from the base map there)."""
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(int)
    g = np.asarray(Image.open(f.REGION_MAP).convert("RGB")).astype(int)
    d = np.abs(g - a).sum(-1) > 15
    xs, ys = f.cell_range()
    out = set()
    for cx in xs:
        for cy in ys:
            l, t, r, b = f.cell_px_box(cx, cy)
            l, t, r, b = max(l, 0), max(t, 0), min(r, f.WIDTH_PX), min(b, f.HEIGHT_PX)
            if r - l < 20 or b - t < 20:
                continue
            if d[t:b, l:r].mean() > 0.5:
                out.add((cx, cy))
    return out


def font(size: int):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def cut(img: Image.Image, x0: int, y0: int) -> Image.Image:
    """The tile whose block's south-west cell is (x0, y0), padded by PAD cells, with rulers."""
    cxs = range(x0 - PAD, x0 + BLOCK + PAD)
    cys = range(y0 + BLOCK + PAD - 1, y0 - PAD - 1, -1)   # north to south
    l, t, _, _ = f.cell_px_box(cxs[0], cys[0])
    _, _, r, b = f.cell_px_box(cxs[-1], cys[-1])
    crop = img.crop((l, t, r, b)).resize(((r - l) * SCALE, (b - t) * SCALE), Image.LANCZOS)
    w, h = crop.size
    out = Image.new("RGB", (w + 2 * RULER, h + 2 * RULER), (255, 255, 255))
    out.paste(crop, (RULER, RULER))
    d = ImageDraw.Draw(out)
    fn = font(15)
    c = f.PX_PER_CELL * SCALE
    for i, cx in enumerate(cxs):
        x = RULER + i * c + c // 2
        for y in (RULER // 2, h + RULER + RULER // 2):
            d.text((x, y), str(cx), fill=(200, 0, 0) if PAD <= i < PAD + BLOCK else (150, 150, 150), font=fn, anchor="mm")
    for j, cy in enumerate(cys):
        y = RULER + j * c + c // 2
        for x in (RULER // 2, w + RULER + RULER // 2):
            d.text((x, y), str(cy), fill=(0, 0, 200) if PAD <= j < PAD + BLOCK else (150, 150, 150), font=fn, anchor="mm")
    return out


def main() -> None:
    cells = scope_cells()
    img = Image.open(f.BASE_MAP).convert("RGB")
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    outdir = f.OUT / "tiles"
    outdir.mkdir(parents=True, exist_ok=True)
    tiles = []
    for x0 in range(min(xs) - (min(xs) % BLOCK), max(xs) + 1, BLOCK):
        for y0 in range(min(ys) - (min(ys) % BLOCK), max(ys) + 1, BLOCK):
            block = {(x, y) for x in range(x0, x0 + BLOCK) for y in range(y0, y0 + BLOCK)}
            if not block & cells:
                continue
            name = f"tile_{x0}_{y0}"
            cut(img, x0, y0).save(outdir / f"{name}.png")
            tiles.append({"tile": name, "x0": x0, "y0": y0, "x1": x0 + BLOCK - 1, "y1": y0 + BLOCK - 1,
                          "scope_cells": len(block & cells)})
    (outdir / "tiles.json").write_text(json.dumps(tiles, indent=1))
    (f.OUT / "scope_cells.json").write_text(json.dumps(sorted(cells)))
    print(len(cells), "scope cells;", len(tiles), "tiles")


if __name__ == "__main__":
    main()
