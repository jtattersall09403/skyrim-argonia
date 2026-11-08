"""The base map's ground, read pixel by pixel: water, the province's land, foreign land (the grey beyond the
border), and the hatched land along the northern border. Written to `out/newworld/raster/` as PNG masks at the
map's resolution (40 px a cell, 5.85 m a pixel), with a preview.

How a pixel is read:
- plain ground: water is the only colour family with blue above red (base water ~ (128,160,176), land ~ (216,192,176),
  foreign land ~ (176,176,160));
- a culture square (the shaded square behind a settlement) is a constant tint over land and water alike, which keeps
  land about 50 brighter in red than water under it: each square is split by its own threshold (Otsu) on
  s = 0.94 r + 0.34 g, the direction from base water to base land;
- marks drawn over the ground (labels, icons, glyphs, roads, borders, the grid's highlighted bands are ground) are
  removed and take the class of the nearest ground pixel; so does the whole disc of every settlement glyph (from
  out/newworld/symbols.json when it exists), whose fill and rings are no ground at all.

    python3 -m tools.newworld.raster      # water.png, foreign.png, hatched.png, preview.png
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from tools.newworld import frame as f

RASTER = f.OUT / "raster"


def load() -> np.ndarray:
    return np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(np.int16)


def marks(a: np.ndarray) -> np.ndarray:
    """Pixels drawn over the ground: text, glyph outlines, icons, red lines (roads, the border), navy lines."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = (r + g + b) / 3
    dark_text = (lum < 110) & (np.abs(r - b) < 30) & (np.abs(r - g) < 30)
    white = lum > 238
    red_line = (r > g + 45) & (r > b + 45)
    navy = (b > r + 25) & (lum < 95)
    saturated = (a.max(-1) - a.min(-1)) > 110
    lines = ndi.binary_dilation(red_line | navy, iterations=1)   # their anti-aliased fringes too
    return dark_text | white | lines | saturated


def otsu(v: np.ndarray) -> tuple[float, float]:
    """Threshold and the separation of the two classes' means (0 when one class is empty)."""
    hist, edges = np.histogram(v, bins=64)
    mids = (edges[:-1] + edges[1:]) / 2
    best, thr, sep = -1.0, float(v.mean()), 0.0
    w_all, m_all = hist.sum(), (hist * mids).sum()
    w0 = m0 = 0.0
    for i in range(63):
        w0 += hist[i]
        m0 += hist[i] * mids[i]
        w1 = w_all - w0
        if w0 == 0 or w1 == 0:
            continue
        mu0, mu1 = m0 / w0, (m_all - m0) / w1
        between = w0 * w1 * (mu0 - mu1) ** 2
        if between > best:
            best, thr, sep = between, (edges[i + 1]), abs(mu1 - mu0)
    return thr, sep


def scope_mask(shape) -> np.ndarray:
    """Pixels of the cells the regions map tints (the province and its seas)."""
    from tools.newworld.tiles import scope_cells
    m = np.zeros(shape, bool)
    for cx, cy in scope_cells():
        l, t, r, b = f.cell_px_box(cx, cy)
        m[max(t, 0):b, max(l, 0):r] = True
    return m


def classify(a: np.ndarray) -> dict[str, np.ndarray]:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mk = marks(a)
    scope = scope_mask(a.shape[:2])
    # base water's hue: green 10-45 above red, blue 0-28 above green (any culture tint breaks one of these)
    water = (b > r + 8) & (g - r >= 10) & (g - r <= 45) & (b - g >= -2) & (b - g <= 28)
    # foreign (grey) ground lies only beyond the province's cells; inside them a grey pixel is a glyph's fill
    grey = (np.abs(r - b) <= 24) & (np.abs(r - g) < 14) & (r > 150) & ~water
    mk = mk | (grey & scope)
    grey &= ~scope
    tan = (r > b + 25) & (r > 185)
    plain = water | grey | tan
    # culture squares: big blobs of tinted ground (neither plain ground nor marks), opened to drop thin strokes
    tinted = ~plain & ~mk
    sq = ndi.binary_opening(tinted, structure=np.ones((9, 9), bool))
    sq = ndi.binary_closing(sq, structure=np.ones((5, 5), bool))
    lab, n = ndi.label(sq)
    s = 0.94 * r + 0.34 * g
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        if sl is None:
            continue
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if h < 25 or w < 25:
            continue
        # the glyph sits at the square's centre: its fill is neither land nor water, so leave it out of the split
        yy, xx = np.mgrid[0:h, 0:w]
        core = (np.abs(yy - h / 2) < 0.3 * h) & (np.abs(xx - w / 2) < 0.3 * w)
        mk[sl] |= (lab[sl] == i) & core
        inside = (lab[sl] == i) & ~mk[sl]
        vals = s[sl][inside]
        if vals.size < 50:
            continue
        thr, sep = otsu(vals)
        share = float((vals < thr).mean())
        sub_water = water[sl]
        if sep >= 30 and 0.08 <= share <= 0.92:   # two real classes, not a sliver of anti-aliasing
            sub_water[inside] = s[sl][inside] < thr
        else:   # one class only: the ring around the square decides
            big = (slice(max(sl[0].start - 4, 0), sl[0].stop + 4), slice(max(sl[1].start - 4, 0), sl[1].stop + 4))
            ring = ndi.binary_dilation(lab[big] == i, iterations=3) & ~(lab[big] == i) & ~mk[big]
            sub_water[inside] = water[big][ring].mean() > 0.5 if ring.any() else False
        # water inside a square always enters from outside it (a river, the coast): a blob that never reaches the
        # square's edge is a shading artefact of the split, so it is land
        blobs, nb = ndi.label(sub_water & (lab[sl] == i))
        if nb:
            edge = set(np.unique(np.concatenate([blobs[0], blobs[-1], blobs[:, 0], blobs[:, -1]]))) - {0}
            for b in set(range(1, nb + 1)) - edge:
                sub_water[blobs == b] = False
        water[sl] = sub_water
        tan[sl] = np.where(inside, ~sub_water, tan[sl])
        plain[sl] |= inside
    known = (plain | sq) & ~mk
    # a settlement glyph's own disc carries no ground: clear it, so it takes the ground round it (a river under a
    # glyph carries straight through from both sides)
    syms = f.OUT / "symbols.json"
    if syms.exists():
        import json
        for g in json.loads(syms.read_text()):
            if g.get("glyph") != "settlement":
                continue
            rad = max(8, int(g.get("glyph_px") or 16) // 2 + 3)
            x, y = int(round(g["px"])), int(round(g["py"]))
            yy, xx = np.ogrid[-rad:rad + 1, -rad:rad + 1]
            disc = xx * xx + yy * yy <= rad * rad
            sl = (slice(y - rad, y + rad + 1), slice(x - rad, x + rad + 1))
            if known[sl].shape == disc.shape:
                known[sl] &= ~disc
    cls = np.zeros(a.shape[:2], np.uint8)        # 0 unknown, 1 water, 2 province land, 3 foreign land
    cls[known & water] = 1
    cls[known & ~water & ~grey] = 2
    cls[known & grey] = 3
    # unknown pixels take the class of the nearest known pixel
    idx = ndi.distance_transform_edt(cls == 0, return_distances=False, return_indices=True)
    filled = cls == 0
    cls = cls[idx[0], idx[1]]
    # the fill copies the nearest ground, so beside a river it can draw streaks of water into a glyph or label:
    # a small water blob made mostly of filled pixels (the map never showed it) is land
    blobs, nb = ndi.label(cls == 1)
    if nb:
        size = ndi.sum(np.ones_like(blobs), blobs, index=np.arange(1, nb + 1))
        fill_share = ndi.mean(filled, blobs, index=np.arange(1, nb + 1))
        bad = np.flatnonzero((size < 600) & (fill_share > 0.6)) + 1
        cls[np.isin(blobs, bad)] = 2
    hatched = hatch_mask(a, cls) & ~scope
    return {"water": cls == 1, "land": cls == 2, "foreign": cls == 3, "hatched": hatched}


def hatch_mask(a: np.ndarray, cls: np.ndarray) -> np.ndarray:
    """The diagonal hatching (alternating grey and tan stripes) along the northern border: land where both colours
    mix within a short window."""
    land = cls != 1
    grey = (cls == 3).astype(np.float32)
    mean = ndi.uniform_filter(grey, size=15)
    return land & (mean > 0.2) & (mean < 0.8) & ndi.binary_opening((mean > 0.2) & (mean < 0.8), np.ones((7, 7), bool))


def main() -> None:
    RASTER.mkdir(parents=True, exist_ok=True)
    m = classify(load())
    for k, v in m.items():
        Image.fromarray((v * 255).astype(np.uint8)).convert("1").save(RASTER / f"{k}.png")
    prev = np.zeros(m["water"].shape + (3,), np.uint8)
    prev[m["water"]] = (60, 110, 200)
    prev[m["land"]] = (220, 190, 150)
    prev[m["foreign"]] = (120, 120, 120)
    prev[m["hatched"]] = (170, 120, 120)
    Image.fromarray(prev).save(RASTER / "preview.png")
    print({k: round(float(v.mean()), 4) for k, v in m.items()})


if __name__ == "__main__":
    main()
