"""Look-loop renders of the placed refs (nw-02 step 8), into out/newworld/place_renders/ (never git):

    world.png            every ref as a dot coloured by class over the hillshade (1 px = 4 samples, 7.3 m)
    region-<id>.png      each region's box, 1 px = 1 sample (1.83 m): refs as discs of their crown/footprint
                         reach coloured by family (hue from the family name), so variety reads as colour mix
    crop-<n>.png         close canopy crops (150 m) at 4 px a sample: discs by reach, trunks marked
    slice-<n>.png        side profiles: the terrain line through a ref (both triangulations), the mesh's OBND box
                         at its pivot, and the pivot and the trunk-base line the sink rule sets
    sheet.json           what each file shows
"""
from __future__ import annotations

import colorsys
import hashlib
import json
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw

from tools.newworld.place import place as P
from tools.newworld.place.checks import load

OUT = P.OUT / "place_renders"
CLS_COL = {"canopy_tree": (20, 110, 30), "palm": (120, 170, 40), "understorey": (70, 150, 70), "fern": (100, 200, 100),
           "herb": (220, 200, 60), "reed": (190, 220, 120), "mushroom": (200, 120, 200), "log": (130, 90, 50),
           "boulder": (150, 150, 150), "cliff": (90, 80, 70), "water_plant": (40, 200, 200),
           "seabed_plant": (20, 140, 200), "seabed_rock": (60, 90, 130)}


def col(r):
    if r["cls"].startswith("road_"):
        return (230, 40, 40)
    return CLS_COL.get(r["cls"], (255, 0, 255))


def fam_col(fam: str):
    h = int(hashlib.md5(fam.encode()).hexdigest()[:6], 16) / 0xFFFFFF
    return tuple(int(255 * c) for c in colorsys.hsv_to_rgb(h, 0.75, 0.95))


def hillshade(h):
    gy, gx = np.gradient(h.astype(np.float32), 128.0)
    shade = np.clip(0.6 + (-gx - gy) * 0.6, 0.15, 1.0)
    base = np.where(h[..., None] < 0, np.array([40, 60, 90]) * shade[..., None], np.array([150, 140, 120]) * shade[..., None])
    return base.astype(np.uint8)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    W = P.World(); Pa = P.Palette(W)
    refs = load()
    bases = {b["key"]: b for b in json.loads((P.REFS / "bases.json").read_text())["bases"]}
    sheet = {}
    # world
    k = 4
    hs = hillshade(np.asarray(W.h[::k, ::k]))
    img = Image.fromarray(hs); d = ImageDraw.Draw(img)
    for r in refs:
        rr, cc = W.rc(r["x"], r["y"])
        d.point((cc / k, rr / k), fill=col(r))
    img.save(OUT / "world.png"); sheet["world.png"] = "all refs, colour by class, red = road dressing"
    # regions
    regs = W.legend["regions"]
    by_reg = defaultdict(list)
    rg = W.at("region", np.array([r["x"] for r in refs]), np.array([r["y"] for r in refs]))
    for r, g in zip(refs, rg):
        by_reg[regs[g]].append(r)
    for name, rs in sorted(by_reg.items()):
        if len(rs) < 200:
            continue
        rows = np.array([W.rc(r["x"], r["y"]) for r in rs])
        # the densest 600 x 600 sample window of the region
        h2, _, _ = np.histogram2d(rows[:, 0], rows[:, 1], bins=[np.arange(0, W.H + 300, 300), np.arange(0, W.W + 300, 300)])
        i, j = np.unravel_index(h2.argmax(), h2.shape)
        r0, c0 = max(0, i * 300 - 150), max(0, j * 300 - 150)
        win = np.asarray(W.h[r0:r0 + 600, c0:c0 + 600])
        img = Image.fromarray(hillshade(win)); d = ImageDraw.Draw(img)
        for r in rs:
            rr, cc = W.rc(r["x"], r["y"])
            rr -= r0; cc -= c0
            if 0 <= rr < 600 and 0 <= cc < 600:
                b = bases[r["key"]]; ob = b["obnd"]
                rad = max(1.0, max(abs(ob[0]), abs(ob[1]), ob[3], ob[4]) * r["scale"] / 128 * 0.5)
                fam = Pa.base[r["db"]]["flora_family_id"] if r["db"] in Pa.base else r["cls"]
                d.ellipse((cc - rad, rr - rad, cc + rad, rr + rad), outline=fam_col(fam))
        img.save(OUT / f"region-{name}.png")
        sheet[f"region-{name}.png"] = f"{name}: densest 1.1 km window, discs = half reach, colour = family"
    # canopy crops: the 6 cells with the most trees
    trees = [r for r in refs if r["cls"] in ("canopy_tree", "palm")]
    cnt = defaultdict(int)
    for r in trees:
        cnt[tuple(r["cell"])] += 1
    for n, (cell, _) in enumerate(sorted(cnt.items(), key=lambda t: -t[1])[:6]):
        cx, cy = cell
        x0, y1 = cx * P.CELL - 1000, (cy + 1) * P.CELL + 1000
        r0, c0 = int((W.oy - y1) / 128), int((x0 - W.ox) / 128)
        s = 4
        win = np.asarray(W.h[r0:r0 + 48, c0:c0 + 48])
        img = Image.fromarray(hillshade(win)).resize((48 * s, 48 * s), Image.NEAREST); d = ImageDraw.Draw(img)
        for r in refs:
            rr, cc = W.rc(r["x"], r["y"]); rr -= r0; cc -= c0
            if 0 <= rr < 48 and 0 <= cc < 48:
                ob = bases[r["key"]]["obnd"]
                rad = max(1.5, max(abs(ob[0]), abs(ob[1]), ob[3], ob[4]) * r["scale"] / 128 * s * 0.5)
                d.ellipse((cc * s - rad, rr * s - rad, cc * s + rad, rr * s + rad), outline=col(r))
                d.point((cc * s, rr * s), fill=(0, 0, 0))
        img.save(OUT / f"crop-{n}.png"); sheet[f"crop-{n}.png"] = f"cell {cell}, 88 m window, colour by class"
    # side slices: 3 trees, 3 cliffs, 2 boulders on the steepest ground
    pick = []
    for c, m in (("canopy_tree", 3), ("cliff", 3), ("boulder", 2), ("palm", 1)):
        rs = [r for r in refs if r["cls"] == c]
        rs.sort(key=lambda r: -float(W.at("slope", r["x"], r["y"])))
        pick += rs[:m]
    for n, r in enumerate(pick):
        b = bases[r["key"]]; ob = b["obnd"]; sc = r["scale"]
        span = max(600.0, (ob[3] - ob[0]) * sc * 1.6)
        xs = np.linspace(r["x"] - span, r["x"] + span, 400)
        ys = np.full_like(xs, r["y"])
        t1, t2 = W.tri_grounds(xs, ys)
        zlo = min(t1.min(), t2.min(), r["z"] + ob[2] * sc) - 100
        zhi = max(t1.max(), r["z"] + ob[5] * sc) + 100
        Wd, Ht = 800, 600
        img = Image.new("RGB", (Wd, Ht), (245, 245, 240)); d = ImageDraw.Draw(img)
        sx = lambda x: (x - xs[0]) / (xs[-1] - xs[0]) * Wd
        sz = lambda z: Ht - (z - zlo) / (zhi - zlo) * Ht
        d.line([(sx(x), sz(z)) for x, z in zip(xs, t1)], fill=(120, 80, 30), width=2)
        d.line([(sx(x), sz(z)) for x, z in zip(xs, t2)], fill=(200, 140, 60), width=1)
        d.rectangle((sx(r["x"] + ob[0] * sc), sz(r["z"] + ob[5] * sc), sx(r["x"] + ob[3] * sc), sz(r["z"] + ob[2] * sc)), outline=col(r), width=2)
        d.line((sx(r["x"]) - 30, sz(r["z"]), sx(r["x"]) + 30, sz(r["z"])), fill=(255, 0, 0), width=2)
        g = float(W.ground(r["x"], r["y"]))
        d.line((sx(r["x"]) - 30, sz(g), sx(r["x"]) + 30, sz(g)), fill=(0, 0, 255), width=1)
        d.text((8, 8), f"{r['db']} {r['cls']} scale {sc:.2f}; pivot (red) {(g - r['z']) / 70:.2f} m under the ground (blue); "
                       f"box = OBND x scale; brown = terrain (both diagonals); 1 px = {(xs[-1]-xs[0])/Wd/70:.2f} m", fill=(0, 0, 0))
        img.save(OUT / f"slice-{n}.png"); sheet[f"slice-{n}.png"] = f"{r['db']} at {r['pos']}"
    (OUT / "sheet.json").write_text(json.dumps(sheet, indent=1))
    print(f"render: {len(sheet)} images in {OUT}")
