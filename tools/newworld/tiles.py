"""Reading tiles of the base map: 10 x 10 cell blocks with one cell of overlap, upscaled 2x, each framed by rulers
that print every cell's true coordinate (negative signs included), so a reader names a symbol's cell without
counting. Only blocks that touch the province (a cell the regions map tints) are cut.

    python3 -m tools.newworld.tiles         # out/newworld/tiles/tile_<x0>_<y0>.png and tiles.json, and the scope
    python3 -m tools.newworld.tiles scope   # only the scope: scope_cells.json (province + margin), margin_cells.json
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

from tools.newworld import frame as f

BLOCK = 10
PAD = 1        # overlap in cells on every side
SCALE = 2
RULER = 44     # px of ruler on the upscaled tile


MARGIN = 4     # cells of neighbouring land and sea kept all round the province as border scenery


def tinted_cells() -> set[tuple[int, int]]:
    """Cells the regions map tints: the province and its seas (the regions map differs from the base map there)."""
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(int)
    g = np.asarray(Image.open(f.REGION_MAP).convert("RGB")).astype(int)
    d = np.abs(g - a).sum(-1) > 15
    return _cells_where(d)


def hatched_cells() -> set[tuple[int, int]]:
    """Cells mostly of the hatched province land along the northern border (alternating grey and tan stripes inside
    the province border, which the regions map leaves untinted)."""
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    water = (b > r + 8) & (g - r >= 10) & (g - r <= 45) & (b - g >= -2) & (b - g <= 28)
    grey = ((np.abs(r - b) <= 24) & (np.abs(r - g) < 14) & (r > 150) & ~water).astype(np.float32)
    mean = ndi.uniform_filter(grey, size=15)
    mix = (mean > 0.2) & (mean < 0.8)
    return _cells_where(ndi.binary_opening(mix, np.ones((7, 7), bool)) & ~water)


def _cells_where(d: np.ndarray) -> set[tuple[int, int]]:
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


HATCH_MIN_CELLS = 20   # a hatched patch smaller than this is grey-and-tan coast elsewhere on the border, not the strip


def province_cells() -> set[tuple[int, int]]:
    """The province: its tinted cells and the hatched land inside its northern border. The hatched cells are kept
    in patches of HATCH_MIN_CELLS or more; then every cell within two of a kept one that is closed in by province
    (a river through the strip, a gap the 50% rule missed) joins, by a 2-cell closing limited to that band."""
    tin = tinted_cells()
    xs, ys = f.cell_range()
    shape = (len(ys), len(xs))

    def grid(cells):
        g = np.zeros(shape, bool)
        for cx, cy in cells:
            g[ys.stop - 1 - cy, cx - xs.start] = True
        return g
    hat = grid(hatched_cells() - tin)
    lab, n = ndi.label(hat, np.ones((3, 3), bool))
    sizes = ndi.sum(hat, lab, np.arange(1, n + 1))
    hat = np.isin(lab, np.flatnonzero(sizes >= HATCH_MIN_CELLS) + 1)
    prov = grid(tin) | hat
    near = ndi.binary_dilation(hat, np.ones((5, 5), bool))
    closed = ndi.binary_closing(np.pad(prov, 3), np.ones((5, 5), bool))[3:-3, 3:-3]
    prov |= closed & near
    prov = ndi.binary_fill_holes(prov) & (prov | near)
    return {(int(xs.start + j), int(ys.stop - 1 - i)) for i, j in zip(*np.nonzero(prov))}


def margin_cells(province: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """MARGIN cells of neighbouring land and sea all round the province (Chebyshev distance), on the map: border
    scenery past the walkable edge, as Skyrim keeps beyond its own."""
    xs, ys = f.cell_range()
    out = set()
    for cx, cy in province:
        for dx in range(-MARGIN, MARGIN + 1):
            for dy in range(-MARGIN, MARGIN + 1):
                c = (cx + dx, cy + dy)
                if c not in province and c[0] in xs and c[1] in ys:
                    out.add(c)
    return out


def scope_cells() -> set[tuple[int, int]]:
    """Every cell the world is built over: the province and its margin."""
    p = province_cells()
    return p | margin_cells(p)


def write_scope() -> None:
    """out/newworld/scope_cells.json (province and margin) and margin_cells.json (the margin alone)."""
    p = province_cells()
    m = margin_cells(p)
    (f.OUT / "scope_cells.json").write_text(json.dumps(sorted(p | m)))
    (f.OUT / "margin_cells.json").write_text(json.dumps(sorted(m)))
    print(len(p), "province cells,", len(m), "margin cells")


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
    cells = province_cells()
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
    write_scope()
    print(len(tiles), "tiles")


if __name__ == "__main__":
    import sys
    write_scope() if sys.argv[1:2] == ["scope"] else main()
