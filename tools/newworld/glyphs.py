"""Glyphs found by the pixels, independent of any reader: every solid mark on the base map (settlement glyphs and
icons), so the tile reads can be checked for completeness and their positions snapped to the glyph's true centre.

A glyph pixel differs strongly from the ground around it (a 31 px median of the map, which a glyph of under 25 px
cannot move), is not a road, border or region line (red or navy), and survives an opening that removes the thin
strokes of text. Blobs of 40 to 1600 px are candidates.

    python3 -m tools.newworld.glyphs     # out/newworld/glyphs.json, out/newworld/glyph_crops/<id>.png
"""
from __future__ import annotations

import json

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from tools.newworld import frame as f
from tools.newworld.raster import scope_mask


def detect(a: np.ndarray) -> list[dict]:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    med = np.stack([ndi.median_filter(a[..., k], size=31) for k in range(3)], -1)
    diff = np.abs(a - med).sum(-1)
    lum = a.mean(-1)
    red_line = (r > g + 45) & (r > b + 45) & (lum > 110)
    navy = (b > r + 25) & (lum < 95) & (np.abs(r - g) < 25)
    mark = (diff > 90) & ~red_line & ~navy
    solid = ndi.binary_opening(mark, structure=np.ones((3, 3), bool))
    solid = ndi.binary_closing(solid, structure=np.ones((3, 3), bool))
    solid &= scope_mask(a.shape[:2])
    lab, n = ndi.label(solid)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        area = int((lab[sl] == i).sum())
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if area < 40 or area > 1600 or max(h, w) > 60:
            continue
        cy, cx = ndi.center_of_mass(lab[sl] == i)
        px, py = sl[1].start + cx, sl[0].start + cy
        mean = a[sl][lab[sl] == i].mean(0)
        out.append({"id": len(out), "px": round(px, 1), "py": round(py, 1), "w": w, "h": h, "area": area,
                    "rgb": [int(v) for v in mean], "cell": list(f.px_to_cell(px, py))})
    return out


def main() -> None:
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(np.int16)
    gl = detect(a)
    crops = f.OUT / "glyph_crops"
    crops.mkdir(parents=True, exist_ok=True)
    img = Image.open(f.BASE_MAP).convert("RGB")
    for g in gl:
        x, y = int(g["px"]), int(g["py"])
        img.crop((x - 20, y - 20, x + 20, y + 20)).resize((80, 80), Image.NEAREST).save(crops / f"{g['id']}.png")
    (f.OUT / "glyphs.json").write_text(json.dumps(gl, indent=0))
    print(len(gl), "glyph candidates")


if __name__ == "__main__":
    main()
