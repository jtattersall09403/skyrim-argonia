"""Relief character: how each region's ground reads, measured, and how far apart the regions are.

    python3 -m tools.newworld.terrain_character [terrain dir] [label]
        # measures heightmap.npy there (default out/newworld/terrain) per region, and Skyrim's Tamriel per sample
        # region (out/newworld/terrain_ref/tamriel_h.npy, from terrain_quality refs); writes character.json there

On land only (over 0.5 m above the water and more than 20 m from it, and outside ground held as built for a built
place, terrain_held), per region. Four numbers say how much relief there is:
- h_p50: the median height above the water, and span: the height range p95 - p5 (metres);
- slope_p90 (degrees, one sample apart);
- r100: the roughness at 100 m (RMS of a difference of Gaussians a factor two apart, metres).
Nine say what shape it has, whatever its size (two regions of one landform at two amplitudes differ only in the four
above; two landforms of one amplitude differ here):
- flat: the share of ground under 1 degree;
- step: log of slope p90 over slope p50 (benches, mesas and scarps are flats with a few steep risers: high; rolling
  ground: low);
- scale: the roughness-weighted mean wavelength over 20 to 1000 m, the size of the shapes that make the ground;
- fine and broad: log of the roughness at 20 m and at 500 m over that at 100 m (the spectrum's shape: hummocks and
  rills against swells);
- grain: the anisotropy of the slopes (1 - the ratio of the gradient structure tensor's eigenvalues over 200 m;
  0 = no direction, 1 = every slope faces one way: parallel ridges, scarps facing one way);
- line: how linear the shapes are where they stand, whatever way they run (|k1| - |k2| over |k1| + |k2| of the
  50 m band's curvatures, weighted by curvature: ridges, rings, ravines and beach lines near 1, domes and kettles
  near 0);
- skew: of the 100 m band (mounds standing on a flat skew positive, ravines and kettles cut into a plain negative);
- kurt: log of the 100 m band's kurtosis over a Gaussian's (a few strong shapes on calm ground: high; ground busy
  everywhere: low).

The distance between two regions is the Euclidean distance of their feature vectors, each feature divided by its
spread (SCALE: fixed numbers, so tables from different builds compare). Skyrim's sample regions (SKYRIM_BOXES, in
Skyrim cells) show the contrast Bethesda put between regions, and SKYRIM_NEIGHBOURS which of them adjoin: our
neighbouring regions should differ at least as much as Skyrim's do.
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
HALO = 256            # samples round a region's box: the widest band reads this far
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
# the sample regions whose holds share a border on Skyrim's map
SKYRIM_NEIGHBOURS = (("hjaalmarch-marsh", "the-reach"), ("hjaalmarch-marsh", "whiterun-tundra"),
                     ("hjaalmarch-marsh", "pale-snowfield"), ("whiterun-tundra", "the-reach"),
                     ("whiterun-tundra", "pale-snowfield"), ("whiterun-tundra", "eastmarch-springs"),
                     ("whiterun-tundra", "the-rift"), ("pale-snowfield", "north-coast"),
                     ("pale-snowfield", "eastmarch-springs"), ("north-coast", "eastmarch-springs"),
                     ("eastmarch-springs", "the-rift"))
TAMRIEL_X0, TAMRIEL_Y1 = -57, 50          # tamriel_h.npy: 119 x 94 cells, column 0 = cell x -57, row 0 = cell y 50
AMOUNT = ("h_p50", "span", "slope_p90", "r100")
SHAPE = ("flat", "step", "scale", "fine", "broad", "grain", "line", "skew", "kurt")
FEATURES = AMOUNT + SHAPE
LOGS = {"h_p50", "span", "r100", "scale"}       # compared on a log scale (log(1 + v))
FLOOR_M = 0.02                                  # roughness under this is no shape (LAND's step is 0.11 m)


def measure(h_m: np.ndarray, mask: np.ndarray) -> dict | None:
    """The features of the ground `h_m` (metres above the water) over `mask`; None under 5000 samples."""
    n = int(mask.sum())
    if n < 5000:
        return None
    h = h_m.astype(np.float32)
    gy, gx = np.gradient(ndi.gaussian_filter(h, 1.0), M)      # lightly smoothed: LAND's 8-unit steps read as slope
    s = np.degrees(np.arctan(np.hypot(gx, gy)))[mask]
    hv = h[mask]
    p50, p90 = float(np.percentile(s, 50)), float(np.percentile(s, 90))
    r = {"n": n, "km2": round(n * M * M / 1e6, 1),
         "h_p50": float(np.percentile(hv, 50)), "span": float(np.percentile(hv, 95) - np.percentile(hv, 5)),
         "slope_p50": p50, "slope_p90": p90, "flat": float((s < 1.0).mean()),
         "step": float(np.log((p90 + 0.5) / (p50 + 0.5)))}
    sg = 200.0 / M / 2
    jxx, jyy, jxy = (ndi.gaussian_filter(a, sg) for a in (gx * gx, gy * gy, gx * gy))
    del gx, gy
    tr = jxx + jyy
    disc = np.sqrt(np.maximum(tr * tr / 4 - (jxx * jyy - jxy * jxy), 0))
    r["grain"] = float(np.where(tr > 1e-6, 1 - np.maximum(tr / 2 - disc, 0) / np.maximum(tr / 2 + disc, 1e-9), 0)[mask]
                       .mean())
    del jxx, jyy, jxy, tr, disc
    rms = {}
    for wl in BANDS_M:
        s1 = wl / M / 6
        b = ndi.gaussian_filter(h, s1) - ndi.gaussian_filter(h, 2 * s1)
        d = b[mask]
        rms[wl] = float(np.sqrt(np.mean(d ** 2)))
        if wl == 100:
            sd = float(d.std())
            z = (d - d.mean()) / max(sd, 1e-6)
            calm = sd < FLOOR_M
            r["skew"] = 0.0 if calm else float(np.clip((z ** 3).mean(), -3, 3))
            r["kurt"] = 0.0 if calm else float(np.clip(np.log((z ** 4).mean() / 3.0), -1, 3))
        if wl == 50:
            byy, byx = np.gradient(np.gradient(b, M, axis=0), M)
            bxx = np.gradient(np.gradient(b, M, axis=1), M, axis=1)
            t = bxx + byy
            dc = np.sqrt(np.maximum(t * t / 4 - (bxx * byy - byx * byx), 0))
            k1, k2 = np.abs(t / 2 + dc)[mask], np.abs(t / 2 - dc)[mask]
            r["line"] = float(np.abs(k1 - k2).sum() / max(float((k1 + k2).sum()), 1e-9)) if rms[50] >= FLOOR_M else 0.5
            del byy, byx, bxx, t, dc
    r["r20"], r["r100"], r["r500"] = rms[20], rms[100], rms[500]
    e = np.array([rms[wl] for wl in BANDS_M])
    r["scale"] = float(np.exp((e * np.log(BANDS_M)).sum() / max(e.sum(), 1e-9)))
    r["fine"] = float(np.log((rms[20] + FLOOR_M) / (rms[100] + FLOOR_M)))
    r["broad"] = float(np.log((rms[500] + FLOOR_M) / (rms[100] + FLOOR_M)))
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}


def vector(r: dict) -> np.ndarray:
    return np.array([np.log1p(max(r[k], 0)) if k in LOGS else r[k] for k in FEATURES])


# the pooled spread of each feature (Skyrim's seven sample regions and our land regions on build 20261109T204317Z),
# fixed so tables from different builds compare; `line` barely varied there (0.045: neither had linear landforms), so
# it takes grain's spread, the other 0-to-1 measure of direction
SCALE = (1.4075, 1.274, 19.0779, 0.517, 0.2023, 0.2794, 0.2134, 0.2854, 0.4165, 0.0999, 0.0999, 1.3264, 0.7399)


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
    H = np.load(OUT / "terrain_ref/tamriel_h.npy", mmap_mode="r")
    Wt = np.load(OUT / "terrain_ref/tamriel_w.npy", mmap_mode="r")
    out = {}
    for name, (x0, x1, y0, y1) in SKYRIM_BOXES.items():
        r0, r1 = (TAMRIEL_Y1 - y1) * 32, (TAMRIEL_Y1 - y0 + 1) * 32
        c0, c1 = (x0 - TAMRIEL_X0) * 32, (x1 - TAMRIEL_X0 + 1) * 32
        a0, b0 = max(r0 - HALO, 0), max(c0 - HALO, 0)
        h = np.array(H[a0:r1 + HALO, b0:c1 + HALO])
        wl = np.array(Wt[a0:r1 + HALO, b0:c1 + HALO])
        hole = np.isnan(h)
        h = np.where(hole, np.nanmin(h), h)
        ok = ~np.isnan(wl) & (np.abs(np.nan_to_num(wl)) < 1e5)      # a cell's own water; the rest has none
        wl = np.where(ok, np.nan_to_num(wl), -1e9)
        box = np.zeros(h.shape, bool)
        box[r0 - a0:r1 - a0, c0 - b0:c1 - b0] = True
        okb = ok & box
        base = float(np.median(wl[okb])) if okb.any() else float(np.percentile(h[box & ~hole], 1))
        hm = (h - base) / U                               # height above the box's water
        out[name] = measure(hm, land_mask(hm, (h <= wl) | hole) & box)
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
    """Every land region measured on its own window of the heightmap (its box and HALO round it)."""
    from tools.argonia_world import db
    sea = {r.id for r in db.open("newworld").rows("region") if r.kind == "sea"}
    b = json.loads((tdir / "build.json").read_text())
    H = np.load(tdir / "heightmap.npy", mmap_mode="r")
    code, names = region_codes(b, H.shape)
    held = held_mask(b, H.shape)
    out = {}
    for k, n in enumerate(names):
        if n in sea:
            continue
        on = code == k
        rows, cols = np.flatnonzero(on.any(1)), np.flatnonzero(on.any(0))
        if not rows.size:
            continue
        sl = (slice(max(int(rows[0]) - HALO, 0), int(rows[-1]) + 1 + HALO),
              slice(max(int(cols[0]) - HALO, 0), int(cols[-1]) + 1 + HALO))
        h = np.array(H[sl], np.float32) / U
        r = measure(h, land_mask(h) & on[sl] & ~held[sl])
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
    near_s = {r: min(Ds[r].values()) for r in sk}
    nb_s = {f"{a}|{b}": Ds[a][b] for a, b in SKYRIM_NEIGHBOURS}
    nb = {f"{a}|{b}": D[a][b] for a, b in pairs}
    res = {"label": label, "build": json.loads((tdir / "build.json").read_text())["id"],
           "features": FEATURES, "scale": [round(float(s), 4) for s in scale],
           "skyrim": sk, "skyrim_distance": Ds,
           "skyrim_mean_distance": round(float(np.mean([v for d in Ds.values() for v in d.values()])), 3),
           "skyrim_nearest": {r: round(v, 3) for r, v in sorted(near_s.items())},
           "skyrim_mean_nearest": round(float(np.mean(list(near_s.values()))), 3),
           "skyrim_neighbour_pairs": nb_s,
           "skyrim_min_neighbour": round(min(nb_s.values()), 3),
           "skyrim_mean_neighbour": round(float(np.mean(list(nb_s.values()))), 3),
           "ours": us, "distance": D,
           "nearest": {r: round(v, 3) for r, v in sorted(near.items())},
           "nearest_to": {r: min(D[r], key=D[r].get) for r in sorted(us)},
           "neighbour_pairs": nb,
           "mean_distance": round(float(np.mean([v for d in D.values() for v in d.values()])), 3),
           "mean_nearest": round(float(np.mean(list(near.values()))), 3),
           "min_neighbour": round(min(nb.values()), 3) if nb else None,
           "mean_neighbour": round(float(np.mean(list(nb.values()))), 3) if nb else None}
    (tdir / "character.json").write_text(json.dumps(res, indent=1))
    return res


def judge(c: dict) -> dict:
    """What character.json must show: every neighbouring pair of regions at least as far apart as Skyrim's closest
    neighbouring pair and on average as far as Skyrim's neighbours; no region nearer its most alike than Skyrim's
    most alike pair of sample regions."""
    close = {p: v for p, v in c["neighbour_pairs"].items() if v < c["skyrim_min_neighbour"]}
    alike = {r: v for r, v in c["nearest"].items() if v < min(c["skyrim_nearest"].values())}
    return {"neighbours_too_alike": close, "regions_too_alike": alike,
            "ok": not close and not alike and c["mean_neighbour"] >= c["skyrim_mean_neighbour"]}


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
        j = judge(c)
        built = json.loads((tdir / "build.json").read_text())["id"]
        rep.row("relief", "character.json measures the terrain build in place", c["build"], c["build"] == built,
                f"terrain build {built}")
        rep.row("relief", "neighbouring regions differ at least as much as Skyrim's neighbouring regions (smallest, "
                f"mean; Skyrim {c['skyrim_min_neighbour']}, {c['skyrim_mean_neighbour']})",
                [c["min_neighbour"], c["mean_neighbour"]], j["ok"],
                f"too alike: {j['neighbours_too_alike'] or j['regions_too_alike']}" if not j["ok"] else c["build"])
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
    print(json.dumps({k: r[k] for k in ("build", "skyrim_mean_nearest", "skyrim_min_neighbour",
                                         "skyrim_mean_neighbour", "mean_distance", "mean_nearest", "min_neighbour",
                                         "mean_neighbour", "nearest")} | {"judge": judge(r)}, indent=1))
