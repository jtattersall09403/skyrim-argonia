"""Relief character: how each region's ground reads, measured, and how far apart the regions are.

    python3 -m tools.newworld.terrain_character [terrain dir] [label]
        # measures heightmap.npy there (default out/newworld/terrain) per region, and Skyrim's Tamriel per sample
        # region (out/newworld/terrain_ref/tamriel_h.npy, from terrain_quality refs); writes character.json there

On land only (over 0.5 m above the water and more than 20 m from it, and outside ground held as built for a built
place, terrain_held), per region:
- height above the water p50 and p95, and the span p95 - p5 (metres);
- slope p50 and p90 (degrees, one sample apart) and the share of flats (under 1 degree);
- band roughness at 20, 50, 100, 200, 500 and 1000 m (RMS of a difference of Gaussians a factor two apart) and the
  landform scale: the roughness-weighted mean wavelength, the size of the shapes that make the ground;
- grain: the anisotropy of the slopes (1 - the ratio of the gradient structure tensor's eigenvalues over 200 m;
  0 = no direction, 1 = every slope faces one way: levees, ridges, dune lines);
- skew of the height about its 300 m mean (mounds and knolls on a flat skew positive, ravines and gullies cut into a
  plain skew negative, mesas split two ways).

The distance between two regions is the Euclidean distance of their feature vectors, each feature divided by its
spread over Skyrim's sample regions (SCALE: fixed numbers, so tables from different builds compare). Skyrim's sample
regions (SKYRIM_BOXES, in Skyrim cells) show the contrast Bethesda put between neighbouring regions.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/newworld"
U = 70.0
M = 128.0 / U
BANDS_M = (20, 50, 100, 200, 500, 1000)
# Skyrim's Tamriel, sample regions as (x0, x1, y0, y1) Skyrim cells inclusive, chosen where one character holds
SKYRIM_BOXES = {
    "hjaalmarch-marsh": (-14, -4, 15, 22),      # Morthal's swamp: pools, hummocks, flat
    "whiterun-tundra": (-2, 10, -8, 2),         # the plains round Whiterun: open rolling tundra, rock outcrops
    "the-rift": (26, 42, -26, -14),             # the autumn forest: rolling wooded hills and lakes
    "the-reach": (-40, -26, -8, 8),             # crags, gorges and cliffs
    "pale-snowfield": (8, 20, 14, 24),          # the Pale: snow plain and low ridges
    "north-coast": (20, 36, 22, 30),            # Winterhold's coast: cliffs, ice and shingle
    "eastmarch-springs": (28, 40, 2, 12),       # the volcanic tundra: hot springs, fumaroles, flat with knolls
}
TAMRIEL_X0, TAMRIEL_Y1 = -57, 50          # tamriel_h.npy: 119 x 94 cells, column 0 = cell x -57, row 0 = cell y 50
FEATURES = ("h_p50", "span", "slope_p50", "slope_p90", "flat", "r20", "r100", "r500", "scale", "grain", "skew")
LOGS = {"h_p50", "span", "r20", "r100", "r500", "scale"}       # compared on a log scale (log(1 + v))


def fields(h_m: np.ndarray) -> dict:
    h = h_m.astype(np.float32)
    gy, gx = np.gradient(ndi.gaussian_filter(h, 1.0), M)      # lightly smoothed: LAND's 8-unit steps read as slope
    out = {"slope": np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)}
    for wl in BANDS_M:
        s1 = wl / M / 6
        out[f"b{wl}"] = (ndi.gaussian_filter(h, s1) - ndi.gaussian_filter(h, 2 * s1)).astype(np.float32)
    s = 200.0 / M / 2
    jxx, jyy, jxy = (ndi.gaussian_filter(a, s) for a in (gx * gx, gy * gy, gx * gy))
    tr = jxx + jyy
    det = jxx * jyy - jxy * jxy
    disc = np.sqrt(np.maximum(tr * tr / 4 - det, 0))
    l1, l2 = tr / 2 + disc, np.maximum(tr / 2 - disc, 0)
    out["grain"] = np.where(tr > 1e-6, 1 - l2 / np.maximum(l1, 1e-9), 0).astype(np.float32)
    out["dev"] = (h - ndi.gaussian_filter(h, 300.0 / M / 2)).astype(np.float32)
    return out


def summarise(h_m: np.ndarray, F: dict, mask: np.ndarray) -> dict | None:
    n = int(mask.sum())
    if n < 5000:
        return None
    hv = h_m[mask]
    s = F["slope"][mask]
    r = {"n": n, "km2": round(n * M * M / 1e6, 1),
         "h_p50": float(np.percentile(hv, 50)), "h_p95": float(np.percentile(hv, 95)),
         "span": float(np.percentile(hv, 95) - np.percentile(hv, 5)),
         "slope_p50": float(np.percentile(s, 50)), "slope_p90": float(np.percentile(s, 90)),
         "flat": float((s < 1.0).mean())}
    rms = {wl: float(np.sqrt(np.mean(F[f"b{wl}"][mask] ** 2))) for wl in BANDS_M}
    for wl in (20, 100, 500):
        r[f"r{wl}"] = rms[wl]
    e = np.array([rms[wl] for wl in BANDS_M])
    r["scale"] = float(np.exp((e * np.log(BANDS_M)).sum() / max(e.sum(), 1e-9)))
    r["grain"] = float(F["grain"][mask].mean())
    d = F["dev"][mask]
    sd = d.std()
    r["skew"] = float(((d - d.mean()) ** 3).mean() / max(sd, 1e-6) ** 3) if sd > 0.05 else 0.0
    r["skew"] = float(np.clip(r["skew"], -3, 3))
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}


def vector(r: dict) -> np.ndarray:
    return np.array([np.log1p(max(r[k], 0)) if k in LOGS else r[k] for k in FEATURES])


# the pooled spread (Skyrim's seven sample regions and our land regions on build 20261109T204317Z), fixed
SCALE = (1.4102, 1.2831, 9.3653, 19.1246, 0.2023, 0.2324, 0.5183, 0.7392, 0.1994, 0.0968, 1.3111)


def scale_of(rows: dict) -> np.ndarray:
    if SCALE is not None:
        return np.array(SCALE)
    v = np.array([vector(r) for r in rows.values()])
    return np.maximum(v.std(0), 1e-3)


def distances(rows: dict, scale: np.ndarray) -> dict:
    ids = sorted(rows)
    V = {k: vector(rows[k]) / scale for k in ids}
    return {a: {b: round(float(np.linalg.norm(V[a] - V[b])), 3) for b in ids if b != a} for a in ids}


def land_mask(h_m: np.ndarray, water: np.ndarray | None = None) -> np.ndarray:
    wet = (h_m <= 0) if water is None else water
    land = (h_m > 0.5) & ~wet
    return land & (ndi.distance_transform_edt(~wet) * M > 20)


def skyrim() -> dict:
    H = np.load(OUT / "terrain_ref/tamriel_h.npy")
    Wt = np.load(OUT / "terrain_ref/tamriel_w.npy")
    out = {}
    for name, (x0, x1, y0, y1) in SKYRIM_BOXES.items():
        r0, r1 = (TAMRIEL_Y1 - y1) * 32, (TAMRIEL_Y1 - y0 + 1) * 32
        c0, c1 = (x0 - TAMRIEL_X0) * 32, (x1 - TAMRIEL_X0 + 1) * 32
        h = H[r0 - 64:r1 + 64, c0 - 64:c1 + 64]
        wl = Wt[r0 - 64:r1 + 64, c0 - 64:c1 + 64]
        hole = np.isnan(h)
        h = np.where(hole, np.nanmin(h), h)
        ok = ~np.isnan(wl) & (np.abs(np.nan_to_num(wl)) < 1e5)      # a cell's own water; the rest has none
        wl = np.where(ok, np.nan_to_num(wl), -1e9)
        base = float(np.median(wl[ok])) if ok.any() else float(np.percentile(h[~hole], 1))
        hm = (h - base) / U                               # height above the box's water
        land = land_mask(hm, (h <= wl) | hole)
        inner = np.zeros(h.shape, bool)
        inner[64:-64, 64:-64] = True
        out[name] = summarise(hm, fields(hm), land & inner)
    return out


def region_codes(b: dict, shape) -> tuple[np.ndarray, list]:
    from PIL import Image
    from tools.newworld import frame as f
    from tools.newworld import terrain as T
    cell_region = json.loads((OUT / "cell_region.json").read_text())
    names = sorted(set(cell_region.values()))
    water_px = np.asarray(Image.open(OUT / "raster" / "water.png"))
    rpx = T.region_px(cell_region, names, water_px.shape)
    p0x, p0y = f.world_to_px(b["origin_world_x"], b["origin_world_y"])
    k = 128.0 / f.UNITS_PER_PX
    jx = np.floor(p0x + np.arange(shape[1]) * k).astype(int)
    iy = np.floor(p0y + np.arange(shape[0]) * k).astype(int)
    code = rpx[np.ix_(np.clip(iy, 0, water_px.shape[0] - 1), np.clip(jx, 0, water_px.shape[1] - 1))]
    inside = (((iy >= f.FRAME_PX) & (iy < water_px.shape[0] - f.FRAME_PX))[:, None]
              & ((jx >= f.FRAME_PX) & (jx < water_px.shape[1] - f.FRAME_PX))[None, :])
    return np.where(inside, code, -1), names


def held_mask(b: dict, shape) -> np.ndarray:
    """Ground held as built (terrain_held: built places and their blend): left out of the measure, so builds before
    and after a relief change compare on the ground that may change."""
    from tools.newworld import terrain_held as th
    from tools.newworld import terrain_needs as tn
    grid = tn.grid_of(b)
    out = np.zeros(shape, bool)
    for pid, rec in th.rows().items():
        p = th.patch(pid, rec)
        win = th._window(grid, p)
        if win is not None:
            out[win[0]] |= th.weight(rec, p)[win[1]] > 0
    return out


def ours(tdir: Path) -> dict:
    from tools.argonia_world import db
    sea = {r.id for r in db.open("newworld").rows("region") if r.kind == "sea"}
    b = json.loads((tdir / "build.json").read_text())
    h = np.load(tdir / "heightmap.npy") / U
    code, names = region_codes(b, h.shape)
    F = fields(h)
    land = land_mask(h) & ~held_mask(b, h.shape)
    out = {}
    for k, n in enumerate(names):
        if n in sea:
            continue
        r = summarise(h, F, land & (code == k))
        if r:
            out[n] = r
    return out


def neighbours(cell_region: dict) -> set:
    pairs = set()
    for key, r in cell_region.items():
        x, y = map(int, key.split(","))
        for dx, dy in ((1, 0), (0, 1)):
            o = cell_region.get(f"{x + dx},{y + dy}")
            if o and o != r:
                pairs.add(tuple(sorted((r, o))))
    return pairs


def report(tdir: Path, label: str) -> dict:
    sk = skyrim()
    us = ours(tdir)
    scale = scale_of({**sk, **us})
    cell_region = json.loads((OUT / "cell_region.json").read_text())
    pairs = sorted(p for p in neighbours(cell_region) if p[0] in us and p[1] in us)
    D = distances(us, scale)
    Ds = distances(sk, scale)
    near = {r: min(D[r].values()) for r in us}
    res = {"label": label, "build": json.loads((tdir / "build.json").read_text())["id"],
           "features": FEATURES, "scale": [round(float(s), 4) for s in scale],
           "skyrim": sk, "skyrim_distance": Ds,
           "skyrim_mean_distance": round(float(np.mean([v for d in Ds.values() for v in d.values()])), 3),
           "ours": us, "distance": D,
           "nearest": {r: round(v, 3) for r, v in sorted(near.items())},
           "neighbour_pairs": {f"{a}|{b}": D[a][b] for a, b in pairs},
           "mean_distance": round(float(np.mean([v for d in D.values() for v in d.values()])), 3),
           "mean_nearest": round(float(np.mean(list(near.values()))), 3),
           "mean_neighbour": round(float(np.mean([D[a][b] for a, b in pairs])), 3) if pairs else None}
    (tdir / "character.json").write_text(json.dumps(res, indent=1))
    return res


MIN_NEAREST = 1.0        # every land region at least this far (character distance) from its most alike region
MIN_MEAN_NEAREST = 1.55  # and on average as far as Skyrim's sample regions are from their most alike (1.55)


def verify_rows(rep, land_cells: set) -> None:
    """Read-back rows (tools/newworld/verify.py): regions read differently, the world runs past the picture, built
    places keep their ground. `land_cells`: the plugin's (x, y) Skyrim cells with LAND."""
    from tools.newworld import frame as f
    from tools.newworld import tiles
    tdir = OUT / "terrain"
    cj = tdir / "character.json"
    if not cj.exists():
        rep.fail("relief", "every land region reads differently from its most alike", f"{cj} missing: run "
                 "python -m tools.newworld.terrain_character")
    else:
        c = json.loads(cj.read_text())
        low = {r: v for r, v in c["nearest"].items() if v < MIN_NEAREST}
        rep.row("relief", f"every land region at least {MIN_NEAREST} from its most alike; mean at least "
                f"{MIN_MEAN_NEAREST} (Skyrim's sample regions)", c["mean_nearest"],
                not low and c["mean_nearest"] >= MIN_MEAN_NEAREST, f"too alike: {low}" if low else c["build"])
    xs, ys = f.cell_range()
    k = tiles.BEYOND_CELLS
    want = (2 * (xs.start - k), 2 * (xs.stop + k) - 1, 2 * (ys.start - k), 2 * (ys.stop + k) - 1)
    have = (min(x for x, _ in land_cells), max(x for x, _ in land_cells),
            min(y for _, y in land_cells), max(y for _, y in land_cells)) if land_cells else None
    rep.row("relief", "the world's land reaches past the picture on every side (Skyrim cells x0 x1 y0 y1)", have,
            have is not None and have[0] <= want[0] and have[1] >= want[1] and have[2] <= want[2] and have[3] >= want[3],
            f"wanted at least {want}")
    ch = tdir / "check.json"
    held = json.loads(ch.read_text()).get("held") if ch.exists() else None
    from tools.newworld import terrain_held as th
    rep.row("relief", "built places keep the ground they were seated on (max height difference, units)",
            {p: r.get("max_diff_units") for p, r in (held or {}).items()}, bool(held) and th.ok(held))


if __name__ == "__main__":
    tdir = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "terrain"
    r = report(tdir, sys.argv[2] if len(sys.argv) > 2 else "")
    print(json.dumps({k: r[k] for k in ("build", "skyrim_mean_distance", "mean_distance", "mean_nearest",
                                         "mean_neighbour", "nearest")}, indent=1))
