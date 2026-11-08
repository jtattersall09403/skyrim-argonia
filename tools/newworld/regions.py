"""Each in-scope cell's region, read from Project Tamriel's regions map, which tints whole cells, one colour a region;
an untinted cell (the hatched land inside the northern border, the margin past the province) takes its nearest tinted
cell's region.

The regions map is the base map under a translucent overlay: per channel G = 0.505 B + m, where m is fixed by the
region's colour (the blend factor measured by regressing G on B inside 277 cells). So m = G - 0.505 B is the same
over land and water of any shade, and a cell's signature is its median m. Neighbouring cells whose signatures
differ by less than SAME form one component; components under MIN_CELLS cells join the neighbouring component
whose signature is nearest; each component takes the name of the region label printed inside it, and NAMED_AT
names the few whose label is printed over a neighbour (Topal Bay's label sits on Aphon Isle's cells).

    python3 -m tools.newworld.regions     # out/newworld/cell_region.json and a preview
"""
from __future__ import annotations

import collections
import json

import numpy as np
from PIL import Image

from tools.newworld import frame as f

# Each region as printed on the regions map, with the map pixel at the middle of its label and its kind.
REGIONS = [
    ("barsaebica", "Barsaebica", "BARSAEBICA", 1170, 669, "land"),
    ("valley-of-storms", "Valley of Storms", "VALLEY OF STORMS", 1608, 601, "land"),
    ("arnesian-jungle", "Arnesian Jungle", "ARNESIAN JUNGLE", 2310, 628, "land"),
    ("chixathe-mesa", "Chixathe Mesa", "CHIXATHE MESA", 2318, 866, "land"),
    ("hatandros-bight", "Hatandros Bight", "HATANDROS BIGHT", 2913, 913, "land"),
    ("padomaic-ocean", "Padomaic Ocean", "PADOMAIC OCEAN", 3119, 1042, "sea"),
    ("skeith-isle", "Skeith Isle", "SKEITH ISLE", 3213, 1238, "land"),
    ("blackwood", "Blackwood", "BLACKWOOD", 915, 992, "land"),
    ("murkwood", "Murkwood", "MURKWOOD", 1608, 1121, "land"),
    ("okuwun-rahei", "Okuwun Rahei", "OKUWUN RAHEI", 2591, 1291, "land"),
    ("nha-enasa", "Nha Enasa", "NHA ENASA", 827, 1476, "land"),
    ("kotherra-mangroves", "Kotherra Mangroves", "KOTHERRA MANGROVES", 670, 1510, "land"),
    ("topal-bay", "Topal Bay", "TOPAL BAY", 400, 1696, "sea"),
    ("aphon-isle", "Aphon Isle", "APHON ISLE", 314, 1796, "land"),
    ("aunike-ridge", "Aunike Ridge", "AUNIKE RIDGE", 1414, 1564, "land"),
    ("lake-ulaish", "Lake Ulaish", "LAKE ULAISH", 2010, 1502, "land"),
    ("ultherus-swamp", "Ultherus Swamp", "ULTHERUS SWAMP", 1766, 1819, "land"),
    ("banujha-basin", "Banujha Basin", "BANUJHA BASIN", 1159, 1957, "land"),
    ("nushara-bayou", "Nushara Bayou", "NUSHARA BAYOU", 2488, 1901, "land"),
    ("cape-percar", "Cape Percar", "CAPE PERCAR", 851, 2391, "land"),
    ("tulmek-washes", "Tulmek Washes", "TULMEK WASHES", 1716, 2268, "land"),
    ("althii-archipelago", "Althii Archipelago", "ALTHII ARCHIPELAGO", 2391, 2333, "land"),
    ("benthic-yobesh", "Benthic Yobesh", "BENTHIC YOBESH", 2796, 2424, "sea"),
    ("sea-of-mists", "Sea of Mists", "SEA OF MISTS", 1232, 2635, "sea"),
]


SAME = 14        # sum of channel differences: two neighbouring cells within this share a region
MIN_CELLS = 8    # a component this small is a settlement square drawn over the overlay, not a region
BLEND = 0.505
# components whose label is printed over another region: a cell inside each
NAMED_AT = {"topal-bay": (-38, -99)}


def signatures(cells) -> dict:
    a = np.asarray(Image.open(f.BASE_MAP).convert("RGB")).astype(float)
    g = np.asarray(Image.open(f.REGION_MAP).convert("RGB")).astype(float)
    out = {}
    for c in cells:
        l, t, r, b = f.cell_px_box(*c)
        m = (g[t + 3:b - 3, l + 3:r - 3] - BLEND * a[t + 3:b - 3, l + 3:r - 3]).reshape(-1, 3)
        out[c] = np.median(m, 0)
    return out


def assign() -> tuple[dict, dict]:
    from tools.newworld.tiles import tinted_cells
    scope = [tuple(c) for c in json.loads((f.OUT / "scope_cells.json").read_text())]
    cells = sorted(tinted_cells() & set(scope))
    sig = signatures(cells)
    nbrs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    comp: dict = {}
    members: dict = collections.defaultdict(list)
    for seed in cells:
        if seed in comp:
            continue
        k = len(members)
        comp[seed] = k
        stack = [seed]
        while stack:
            c = stack.pop()
            members[k].append(c)
            for dx, dy in nbrs:
                n = (c[0] + dx, c[1] + dy)
                if n in sig and n not in comp and np.abs(sig[n] - sig[c]).sum() < SAME:
                    comp[n] = k
                    stack.append(n)
    mean = {k: np.median([sig[c] for c in v], 0) for k, v in members.items()}
    big = {k for k, v in members.items() if len(v) >= MIN_CELLS}
    loose = [c for k, v in members.items() if k not in big for c in v]
    names = {}
    for rid, _, _, px, py, _ in REGIONS:
        at = NAMED_AT.get(rid, f.px_to_cell(px, py))
        if at in comp and rid not in names.values():
            names.setdefault(comp[at], rid)
    unnamed = [(len(v), min(v), max(v), [round(x) for x in mean[k]]) for k, v in members.items()
               if k in big and k not in names]
    if unnamed:
        raise SystemExit(f"components without a region label: {unnamed[:10]} (name one with NAMED_AT)")
    reg = {c: names[k] for c, k in comp.items() if k in big}
    # cells of the small components (settlement squares drawn over the overlay) take their neighbours' majority
    while loose:
        left = []
        for c in loose:
            nb = [reg[(c[0] + dx, c[1] + dy)] for dx, dy in nbrs if (c[0] + dx, c[1] + dy) in reg]
            if nb:
                reg[c] = collections.Counter(nb).most_common(1)[0][0]
            else:
                left.append(c)
        if len(left) == len(loose):
            break
        loose = left
    # the untinted cells (the hatched land inside the northern border, and the margin past the province's edge)
    # take the region of the nearest tinted cell, so each region runs on to the border and beyond it
    rest = [c for c in scope if c not in reg]
    if rest:
        from scipy.spatial import cKDTree
        known = list(reg)
        _, k = cKDTree(np.array(known)).query(np.array(rest))
        for c, i in zip(rest, k):
            reg[c] = reg[known[i]]
    return reg, sig


def main() -> None:
    reg, _ = assign()
    (f.OUT / "cell_region.json").write_text(json.dumps({f"{x},{y}": r for (x, y), r in sorted(reg.items())}))
    cnt = collections.Counter(reg.values())
    print(len(reg), "cells;", len(cnt), "regions:", dict(sorted(cnt.items())))
    # preview: each region a flat colour with its id, over the base map
    img = Image.open(f.BASE_MAP).convert("RGB")
    over = Image.new("RGB", img.size, (0, 0, 0))
    rng = np.random.default_rng(7)
    cols = {r[0]: tuple(int(v) for v in rng.integers(40, 255, 3)) for r in REGIONS}
    from PIL import ImageDraw
    d = ImageDraw.Draw(over)
    for (x, y), r in reg.items():
        d.rectangle(f.cell_px_box(x, y), fill=cols[r])
    out = Image.blend(img, over, 0.55)
    d = ImageDraw.Draw(out)
    for rid, name, _, px, py, _ in REGIONS:
        d.text((px - 40, py), name, fill=(0, 0, 0))
    out.resize((1200, 968)).save(f.OUT / "regions_preview.png")


if __name__ == "__main__":
    main()
