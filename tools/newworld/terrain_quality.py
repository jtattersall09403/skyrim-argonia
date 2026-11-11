"""Terrain quality: our heightmap measured against Skyrim's Tamriel and BM&V's Black Marsh on the numbers that show
how natural ground looks, and hillshade crops of each side by side.

    python3 -m tools.newworld.terrain_quality refs       # decode the reference LAND once into out/newworld/terrain_ref/
    python3 -m tools.newworld.terrain_quality measure [label]   # measure out/newworld/terrain/heightmap.npy and the refs
                                                         # -> out/newworld/terrain_quality.json (label: before|after)

Every grid here is LAND's own: one sample every 128 units (1.83 m), so the numbers compare like for like.

What is measured, on land only (above the water and more than 10 m from it), split by local relief so a marsh is
compared with flat ground and an upland with hills (relief = 4 x the height spread under a 100 m Gaussian):
- slope p50 / p90 / p99 (degrees, one sample apart);
- band roughness at 20, 100 and 500 m (RMS of the difference of two Gaussians a factor of two apart, metres), and the
  ratios 20/100 and 100/500 (the spectrum's shape: noise-made ground is too smooth at 20 m and too regular across);
- curvature: the spread of the Laplacian of the lightly smoothed ground (1/m), and the share of land that is concave;
- hollows: closed hollows on land deeper than 0.3 m (below their spill height, the water being the outlet): the share
  of land in one, and their number per km2. Water-cut ground drains, so it has few; value noise leaves many;
- flats: the share of land under 0.5 degrees (plateau and terrace artefacts show here, as does bulldozed ground);
- the LAND step: the largest height step between neighbours, against the format's 1016 units.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "out/newworld/terrain_ref"
OUT = ROOT / "out/newworld"
U = 70.0
M = 128.0 / U                     # metres a sample
CLASSES = (("flat", 0, 5), ("low", 5, 20), ("hilly", 20, 60), ("mountain", 60, 1e9))
BANDS_M = (20, 100, 500)
NORTH_STRIP_PX = 80              # map rows above this are left out of our measures (a raster fault was fixed there)
# the references: name -> (height file stem, what it stands for)
REFS = {"skyrim": ("tamriel", "Skyrim.esm + Update.esm, Tamriel"),
        "bm_north": ("005900_Black_Marsh_North.esp", "BM&V Black Marsh North"),
        "bm_south": ("0D6960_Black_Marsh.esm", "BM&V Black Marsh (south)")}


def decode_refs() -> None:
    """Stitch the winning LAND of each reference worldspace into a north-up float32 grid (units) with its water."""
    from tools.argonia_world.bmv_census import DIR, MASTERS, Load
    from tools.bmv_map.build import lands
    REF.mkdir(parents=True, exist_ok=True)

    def stitch(cells):
        xs, ys = [g[0] for g in cells], [g[1] for g in cells]
        x0, y1 = min(xs), max(ys)
        H = np.full(((y1 - min(ys) + 1) * 32, (max(xs) - x0 + 1) * 32), np.nan, np.float32)
        Wt = np.full(H.shape, np.nan, np.float32)
        for (gx, gy), (h, wl) in cells.items():
            r0, c0 = (y1 - gy) * 32, (gx - x0) * 32
            H[r0:r0 + 32, c0:c0 + 32] = h[:32, :32][::-1]
            if wl is not None:
                Wt[r0:r0 + 32, c0:c0 + 32] = wl
        return H, Wt
    worlds = {"tamriel": lands(Load(MASTERS, ("Skyrim.esm", "Update.esm")))["00003C:Skyrim.esm"]}
    bm = lands(Load(DIR))
    worlds["005900_Black_Marsh_North.esp"] = bm["005900:Black Marsh North.esp"]
    worlds["0D6960_Black_Marsh.esm"] = bm["0D6960:Black Marsh.esm"]
    for stem, cells in worlds.items():
        H, Wt = stitch(cells)
        np.save(REF / f"{stem}_h.npy", H)
        np.save(REF / f"{stem}_w.npy", Wt)


def load_ref(stem: str) -> tuple[np.ndarray, np.ndarray]:
    """(heights in metres, holes filled from the nearest LAND, land mask). Land: above its cell's water by 0.3 m and
    more than 100 m from a hole (a cell with no LAND), so the hole's fill never reaches a measure."""
    H = np.load(REF / f"{stem}_h.npy")
    Wt = np.load(REF / f"{stem}_w.npy")
    hole = np.isnan(H)
    near = ndi.distance_transform_edt(hole, return_distances=False, return_indices=True)
    Hf = H[tuple(near)]
    wl = np.where(np.isnan(Wt), -1e9, Wt)
    land = ~hole & (Hf > wl + 0.3 * U) & (ndi.distance_transform_edt(~hole) * M > 100)
    return (Hf / U).astype(np.float32), land


def local_relief(h_m: np.ndarray) -> np.ndarray:
    s = 100.0 / M
    mu = ndi.gaussian_filter(h_m, s)
    var = np.maximum(ndi.gaussian_filter(h_m * h_m, s) - mu * mu, 0)
    return 4 * np.sqrt(var)


def fields(h_m: np.ndarray, land: np.ndarray) -> dict:
    """Per-sample measures over a whole grid (metres)."""
    h_m = h_m.astype(np.float32)
    gy, gx = np.gradient(h_m, M)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    out = {"slope": slope, "relief": local_relief(h_m)}
    for wl in BANDS_M:
        s1 = wl / M / 6
        out[f"b{wl}"] = ndi.gaussian_filter(h_m, s1) - ndi.gaussian_filter(h_m, 2 * s1)
    hs = ndi.gaussian_filter(h_m, 1.0)
    out["lap"] = ndi.laplace(hs) / (M * M)
    from skimage.morphology import reconstruction
    outlet = ~land
    outlet[0, :] = outlet[-1, :] = outlet[:, 0] = outlet[:, -1] = True
    filled = reconstruction(np.where(outlet, h_m, h_m.max() + 1), h_m, method="erosion")
    hollow = (filled - h_m) > 0.3
    lab, _ = ndi.label(hollow)
    pit = np.zeros(h_m.shape, bool)
    if lab.max():
        deepest = ndi.minimum_position(h_m - filled, lab, np.arange(1, lab.max() + 1))
        pit[tuple(np.array(deepest).T)] = True
    out["pit"] = pit
    out["hollow"] = hollow
    d = ndi.distance_transform_edt(land) * M
    out["core"] = land & (d > 10)
    return out


def summarise(F: dict, mask: np.ndarray) -> dict:
    n = int(mask.sum())
    if n < 20000:
        return {"n": n}
    s = F["slope"][mask]
    r = {"n": n, "km2": round(n * M * M / 1e6, 1),
         "slope_p50": round(float(np.percentile(s, 50)), 2), "slope_p90": round(float(np.percentile(s, 90)), 2),
         "slope_p99": round(float(np.percentile(s, 99)), 2),
         "flat_share": round(float((s < 0.5).mean()), 4)}
    for wl in BANDS_M:
        r[f"rough{wl}_m"] = round(float(np.sqrt(np.mean(F[f"b{wl}"][mask] ** 2))), 3)
    r["ratio_20_100"] = round(r["rough20_m"] / max(r["rough100_m"], 1e-6), 3)
    r["ratio_100_500"] = round(r["rough100_m"] / max(r["rough500_m"], 1e-6), 3)
    lap = F["lap"][mask]
    r["curv_sd"] = round(float(lap.std()), 4)
    r["concave_share"] = round(float((lap > 1e-4).mean()), 3)
    r["hollow_share"] = round(float(F["hollow"][mask].mean()), 4)
    r["pits_per_km2"] = round(float(F["pit"][mask].sum()) / (n * M * M / 1e6), 1)
    return r


def measure(h_m: np.ndarray, land: np.ndarray, extra_masks: dict | None = None) -> dict:
    F = fields(h_m, land)
    core = F["core"]
    out = {"all": summarise(F, core)}
    for name, lo, hi in CLASSES:
        out[name] = summarise(F, core & (F["relief"] >= lo) & (F["relief"] < hi))
    for name, m in (extra_masks or {}).items():
        out[name] = summarise(F, core & m)
    return out


def land_step(h_units: np.ndarray) -> float:
    return float(max(np.abs(np.diff(h_units, axis=0)).max(), np.abs(np.diff(h_units, axis=1)).max()))


def ours(path: Path | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(metres, land, units). The map's northern strip (map rows above NORTH_STRIP_PX) is left out of the land."""
    from tools.newworld import frame as f
    h = np.load(path or OUT / "terrain/heightmap.npy")
    b = json.loads((OUT / "terrain/build.json").read_text())
    p0y = f.world_to_px(b["origin_world_x"], b["origin_world_y"])[1]
    land = h > 0.25 * U
    land[: max(0, int(np.ceil((NORTH_STRIP_PX - p0y) / (128.0 / 204.8))))] = False
    return h / U, land, h


def region_masks(shape) -> dict:
    """Our marsh-form and upland-form ground (by the region relief table), for region-matched comparisons."""
    from tools.newworld import frame as f
    from tools.newworld import terrain as T
    from tools.newworld import terrain_relief as tr
    from tools.argonia_world import db
    b = json.loads((OUT / "terrain/build.json").read_text())
    w = db.open("newworld")
    names = [r.id for r in w.rows("region")]
    form = {r.id: tr.region_params(r)[0]["form"] for r in w.rows("region")}
    summit = {r.id: tr.region_params(r)[0]["summit"] for r in w.rows("region")}
    cell_region = json.loads((f.OUT / "cell_region.json").read_text())
    water_px = np.asarray(Image.open(f.OUT / "raster" / "water.png"))
    rpx = T.region_px(cell_region, names, water_px.shape)
    p0x, p0y = f.world_to_px(b["origin_world_x"], b["origin_world_y"])
    k = 128.0 / 204.8
    jx = np.floor(p0x + np.arange(shape[1]) * k).astype(int)
    iy = np.floor(p0y + np.arange(shape[0]) * k).astype(int)
    # ground past the picture (and in its ruler band) is no region's: it is counted in neither class
    inside = (((iy >= f.FRAME_PX) & (iy < water_px.shape[0] - f.FRAME_PX))[:, None]
              & ((jx >= f.FRAME_PX) & (jx < water_px.shape[1] - f.FRAME_PX))[None, :])
    code = np.where(inside, rpx[np.ix_(np.clip(iy, 0, water_px.shape[0] - 1),
                                       np.clip(jx, 0, water_px.shape[1] - 1))], -1)
    low = np.array([form[n] == "low" or summit[n] <= 26 for n in names] + [False])
    high = np.array([form[n] != "low" and summit[n] >= 45 for n in names] + [False])
    return {"our_marsh": low[code], "our_upland": high[code]}


def run_measure(label: str) -> dict:
    res_file = OUT / "terrain_quality.json"
    res = json.loads(res_file.read_text()) if res_file.exists() else {}
    for name, (stem, about) in REFS.items():
        if name in res:
            continue
        h, land = load_ref(stem)
        res[name] = {"about": about, **measure(h, land), "land_step_units": None}
    h_m, land, hu = ours()
    res[f"ours_{label}"] = {"about": f"out/newworld/terrain/heightmap.npy ({label})",
                            **measure(h_m, land, region_masks(h_m.shape)), "land_step_units": land_step(hu)}
    res_file.write_text(json.dumps(res, indent=1))
    return res


def hillshade_m(h_m: np.ndarray, water: np.ndarray | None = None, z: float = 1.0) -> Image.Image:
    gy, gx = np.gradient(h_m * z, M)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az, alt = np.radians(315), np.radians(45)
    sh = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
    g = (40 + 215 * sh).astype(np.uint8)
    rgb = np.stack([g, g, g], -1)
    if water is not None:
        rgb[water] = (70, 110, 150)
    return Image.fromarray(rgb)


def preservation() -> dict:
    """What the weathering must not move, read from the built outputs: the map's water and land exact (check.json),
    every shore at 0.3 m (land samples beside water, one sample inland of the 0.3 m shoreline), pads level (the
    height spread p10 to p90 over each pad's inner half radius, where roads and entrances may still cross), roads graded and troughed, entrances open, LAND's
    step limit."""
    from tools.newworld import terrain_shape as ts
    T = OUT / "terrain"
    chk = json.loads((T / "check.json").read_text())
    h = np.load(T / "heightmap.npy")
    water = h < 0
    shore = ~water & ndi.binary_dilation(water)
    sh = h[shore] / U
    b = json.loads((T / "build.json").read_text())
    from tools.newworld import frame as f
    p0x, p0y = f.world_to_px(b["origin_world_x"], b["origin_world_y"])
    k = 128.0 / 204.8
    pads = []
    for p in json.loads((T / "places_terrain.json").read_text()):
        if p.get("pad_m") is None:
            continue
        i, j = (p["py"] - p0y) / k, (p["px"] - p0x) / k
        r = p["radius_m"] * 0.5 / M
        sl = (slice(max(0, int(i - r)), int(i + r) + 1), slice(max(0, int(j - r)), int(j + r) + 1))
        ii, jj = np.mgrid[sl]
        inside = (np.hypot(ii - i, jj - j) <= r) & (h[sl] > 0)
        if inside.any():
            v = h[sl][inside] / U
            pads.append(float(np.percentile(v, 90) - np.percentile(v, 10)))
    out = {"water_pixels_under": chk["water_pixels_under"], "land_pixels_above": chk["land_pixels_above"],
           "shore_land_m_p5_p50_p95": [round(float(np.percentile(sh, q)), 2) for q in (5, 50, 95)],
           "shore_samples": int(shore.sum()),
           "pads": len(pads), "pad_spread_m_p50_p90": [round(float(np.percentile(pads, 50)), 2),
                                                      round(float(np.percentile(pads, 90)), 2)] if pads else None,
           "roads": chk.get("roads"), "entrances": chk.get("entrances"), "entrances_bad": chk.get("entrances_bad"),
           "land_step_max_units": land_step(h), "land_format_ok": chk["land_format"]["ok"],
           "freeboard_m": ts.FREEBOARD / U}
    return out


KEYS = ("km2", "slope_p50", "slope_p90", "slope_p99", "flat_share", "rough20_m", "rough100_m", "rough500_m",
        "ratio_20_100", "ratio_100_500", "curv_sd", "concave_share", "hollow_share", "pits_per_km2")


def table(res: dict) -> str:
    """The measures as a markdown table, one row per side and relief class."""
    lines = ["| side | class | " + " | ".join(KEYS) + " |", "|---" * (len(KEYS) + 2) + "|"]
    for side, r in res.items():
        for c in ("all", "flat", "low", "hilly", "mountain", "our_marsh", "our_upland"):
            if "km2" in r.get(c, {}):
                lines.append(f"| {side} | {c} | " + " | ".join(str(r[c][k]) for k in KEYS) + " |")
    return "\n".join(lines)


# crops: name -> (map px of the centre, reference stem, reference sample (row, col) of the centre)
CROPS = {"marsh-tulmek-washes": ((1716, 2268), "005900_Black_Marsh_North.esp", None),
         "upland-aunike-ridge": ((1414, 1564), "tamriel", None),
         "upland-chixathe-mesa": ((2318, 866), "tamriel", None),
         "city-helstrom": (None, "tamriel", None),
         "seam-north-stormhold": ((2050, 360), "tamriel", None)}   # across the old scope line
HALF = 300                     # samples each side: 1.1 km crops


def _ref_centre(stem: str, kind: str) -> tuple[int, int]:
    """The reference crop's centre: the window of most land whose relief matches the kind (marsh: flat, upland:
    hilly), chosen once on a coarse search."""
    h, land = load_ref(stem)
    rel = local_relief(h)[::8, ::8]
    ok = ndi.uniform_filter(land[::8, ::8].astype(np.float32), 2 * HALF // 8) > 0.9
    want = (rel < 6) if kind == "marsh" else (rel > 25) & (rel < 70)
    score = ndi.uniform_filter((want & ok).astype(np.float32), 2 * HALF // 8)
    i, j = np.unravel_index(np.argmax(score), score.shape)
    return int(i * 8), int(j * 8)


def render_crops(sides: dict[str, tuple[Path, Path]], out_dir: Path) -> list[Path]:
    """Hillshade crops side by side: each of our sides (name -> (heightmap.npy, build.json)) at the same world
    spot, then the reference. Returns the written paths."""
    from tools.newworld import frame as f
    from tools.argonia_world import db
    out_dir.mkdir(parents=True, exist_ok=True)
    w = db.open("newworld")
    hel = [p for p in w.rows("place") if p.id == "helstrom"]
    paths = []
    for name, (at, stem, rc) in CROPS.items():
        at = at or (hel[0].px, hel[0].py)
        wx, wy = f.px_to_world(*at) if hasattr(f, "px_to_world") else _px_world(f, at)
        panels = []
        for side, (hp, bp) in sides.items():
            b = json.loads(Path(bp).read_text())
            h = np.load(hp, mmap_mode="r")
            i = int(round((b["origin_world_y"] - wy) / 128.0))
            j = int(round((wx - b["origin_world_x"]) / 128.0))
            crop = np.array(h[max(0, i - HALF):i + HALF, max(0, j - HALF):j + HALF]) / U
            panels.append((side, hillshade_m(crop, crop <= 0)))
        rh, rland = load_ref(stem)
        i, j = rc or _ref_centre(stem, name.split("-")[0])
        crop = rh[max(0, i - HALF):i + HALF, max(0, j - HALF):j + HALF]
        wl = ~rland[max(0, i - HALF):i + HALF, max(0, j - HALF):j + HALF]
        panels.append((REFS_BY_STEM.get(stem, stem), hillshade_m(crop, wl)))
        W = sum(p.width for _, p in panels) + 10 * (len(panels) - 1)
        img = Image.new("RGB", (W, max(p.height for _, p in panels) + 20), (255, 255, 255))
        from PIL import ImageDraw
        d = ImageDraw.Draw(img)
        x = 0
        for label, p in panels:
            img.paste(p, (x, 20))
            d.text((x + 4, 4), label, fill=(0, 0, 0))
            x += p.width + 10
        path = out_dir / f"{name}.png"
        img.save(path)
        paths.append(path)
    return paths


REFS_BY_STEM = {stem: name for name, (stem, _) in REFS.items()}


def _px_world(f, at):
    return (at[0] - f.X0_PX) * f.UNITS_PER_PX, -(at[1] - f.Y0_PX) * f.UNITS_PER_PX


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "measure"
    if cmd == "refs":
        decode_refs()
    elif cmd == "crops":
        # crops <name>=<heightmap.npy>:<build.json> ...
        sides = {a.split("=")[0]: tuple(a.split("=")[1].split(":")) for a in sys.argv[2:]}
        for p in render_crops(sides, OUT / "terrain_quality"):
            print(p)
    elif cmd == "preserve":
        r = preservation()
        (OUT / "terrain_quality_preserve.json").write_text(json.dumps(r, indent=1))
        print(json.dumps(r, indent=1))
    elif cmd == "table":
        print(table(json.loads((OUT / "terrain_quality.json").read_text())))
    else:
        r = run_measure(sys.argv[2] if len(sys.argv) > 2 else "before")
        print(table(r))
