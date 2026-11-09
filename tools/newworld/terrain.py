"""The new world's terrain data: one heightmap at Skyrim's LAND spacing over every in-scope cell, built from the map.

    python3 -m tools.newworld.terrain            # build into out/newworld/terrain/, check, copy to the bucket
    python3 -m tools.newworld.terrain check      # re-check the built outputs
    python3 -m tools.newworld.terrain --no-upload

Inputs: the map's water (`out/newworld/raster/water.png`) and foreign land (`foreign.png`), the region of every
cell (`out/newworld/cell_region.json`), the scope (`out/newworld/scope_cells.json`), the roads
(`out/newworld/roads.json`), and the database `newworld` (region relief, places, place_terrain_need, settlement
tiers, road classes, water kinds).

The recipe:
1. Water level: 0 units for the whole world (BM&V's Black Marsh keeps its water at 0; LAND's base offset is a free
   float, so the level costs nothing; heights then read as height above the water). Every map water pixel lies
   under it and every land pixel above it.
2. Grid: the scope's bounding box plus one Morrowind cell all round, samples every 128 units, north-up, sample (0, 0)
   at the north-west corner (origin in build.json). Heights are float32 game units (70 a metre).
3. Water bodies (terrain_water): every body labelled with a kind and flow guess, then the owner's hand edits from
   `newworld/sources/water_overrides.json` ({"<body id>": {"water_kind_id", "flows", "flow_toward_deg", "name"}},
   read on every build); its kind sets the bed (BED).
4. Relief (terrain_relief): region parameters from the region table, the fallback table where empty.
5. Weathering (terrain_erode): drainage erosion, slope detail and talus on the natural ground, then a buildable
   core for every large built place (town tier and up; radius by tier and slope limit in terrain_erode).
6. Banks and beds (terrain_shape.compose). Then places' needs from `place_terrain_need` (a place with no row takes
   its kind's fallback) in this order: flat pads, rises, sea beds, shore access; then the roads, solved as one
   network and laid; then entrances, each facing down its road when one comes within 60 m, else the best dry and
   open heading, never burying a road's bed. Then LAND's 8-unit rounding and step limit, the map's water guaranteed
   pixel by pixel, and any entrance the rounding spoiled shaped again.
7. Cliff mask: slope over 55 degrees (FreeClimb climbs them; cliff meshes go there later).
8. Outputs in out/newworld/terrain/: heightmap.npy (float32 units), heightmap.png (16-bit, h = offset + scale v),
   cliff.png, water_bodies.png (16-bit body index, map px) with out/newworld/water_bodies.json, roads_terrain.json
   (crossings, cut and fill), places_terrain.json, hillshade.png and crops/, check.json, build.json (the
   terrain_build row and the scale). Then all of it to s3://argonia-private-050977237313/nw/terrain/<stamp>/.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from tools.newworld import frame as f
from tools.newworld import terrain_coast as tc
from tools.newworld import terrain_erode as te
from tools.newworld import terrain_relief as tr
from tools.newworld import terrain_shape as ts
from tools.newworld import terrain_water as tw

OUT = f.OUT / "terrain"
# a trial build writes elsewhere (ARGONIA_TERRAIN_OUT) and leaves the shared outputs and the bucket alone
TRIAL = bool(os.environ.get("ARGONIA_TERRAIN_OUT"))
if TRIAL:
    OUT = f.Path(os.environ["ARGONIA_TERRAIN_OUT"])
BUCKET = "s3://argonia-private-050977237313/nw/terrain"
CLIFF_DEG = 55.0
MAP_HELD = 0.97        # share of map water (land) pixels whose centre reads under (over) the water level
BLOCKS_HELD = 0.99     # share of 4 x 4 pixel blocks whose majority class the heightmap keeps
SEED = 1952
NEED_DEFAULT_R = {"entrance-in-slope": 15.0, "rise": 25.0, "shore-access": 20.0, "seabed": 30.0}
SEABED_DEPTH = {"sunken-ruin": 8.0, "shipwreck": 5.0}
CROPS = {"north-uplands-barsaebica": (1170, 669), "chixathe-mesa": (2318, 866), "helstrom-delta": None,
         "tulmek-washes": (1716, 2268), "aunike-ridge": (1414, 1564)}


def _j(o):
    return o.item() if hasattr(o, "item") else str(o)


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def make_grid(scope) -> ts.Grid:
    c = np.array(scope)
    x0, x1 = c[:, 0].min() - 1, c[:, 0].max() + 1
    y0, y1 = c[:, 1].min() - 1, c[:, 1].max() + 1
    per = f.CELL_UNITS // int(ts.STEP)
    ox, oy = x0 * f.CELL_UNITS, (y1 + 1) * f.CELL_UNITS
    p0x, p0y = f.world_to_px(ox, oy)
    return ts.Grid(rows=(y1 - y0 + 1) * per + 1, cols=(x1 - x0 + 1) * per + 1, p0x=p0x, p0y=p0y,
                   ox=float(ox), oy=float(oy))


def region_px(cell_region: dict, names: list, shape) -> np.ndarray:
    lut = {n: k for k, n in enumerate(names)}
    xs, ys = f.cell_range()
    code = np.full((len(ys), len(xs)), -1, np.int32)
    for key, r in cell_region.items():
        cx, cy = map(int, key.split(","))
        code[ys.stop - 1 - cy, cx - xs.start] = lut[r]
    py, px = np.mgrid[0:shape[0], 0:shape[1]]
    cx = np.floor(((px + 0.5) - f.X0_PX) / f.PX_PER_CELL).astype(int) - xs.start
    cyv = np.floor(-((py + 0.5) - f.Y0_PX) / f.PX_PER_CELL).astype(int)
    return code[np.clip(ys.stop - 1 - cyv, 0, len(ys) - 1), np.clip(cx, 0, len(xs) - 1)]


NEED_ORDER = {"flat-pad": 0, "rise": 1, "seabed": 2, "shore-access": 3, "island": 4, "entrance-in-slope": 5}


def toward_road(plans, grid, i0, j0, fallback):
    """The heading from an entrance to the nearest road within 60 m (Bethesda points a door down its path)."""
    best = None
    for p, _ in plans:
        d = np.hypot(p["i"] - i0, p["j"] - j0) * grid.m
        k = int(np.argmin(d))
        if d[k] < 60 and d[k] > 3 and (best is None or d[k] < best[0]):
            best = (d[k], p["i"][k], p["j"][k])
    if best is None:
        return fallback
    return (math.degrees(math.atan2(best[2] - j0, -(best[1] - i0))) + 360) % 360


def lay_roads(h, water_px, water_s, grid, w):
    """Every road planned, solved as one network (shared node heights), and laid into the ground."""
    grade_of = {c.id: c.grade_max for c in w.rows("road_class")}
    roads_file = f.OUT / "roads.json"
    plans, road_out, edges = [], [], []
    if not roads_file.exists():
        return plans, road_out, grade_of, np.zeros(h.shape, bool)
    for e in json.loads(roads_file.read_text())["edges"]:
        pl = ts.plan_road(h, water_px, grid, e["points"], grade_of[e["class"]], water_s=water_s)
        edges.append((pl, e["class"], e["from"], e["to"]))
        plans.append((pl, e["class"]))
    ts.solve_network(edges, grade_of)
    for e, (pl, c, a, b) in zip(json.loads(roads_file.read_text())["edges"], edges):
        road_out.append({"edge": e["id"], "class": c, "length_m": len(pl["z"]),
                         "max_cut_m": round(float(-pl["cut_m"].min()), 2),
                         "max_fill_m": round(float(pl["cut_m"].max()), 2),
                         "over_max_cut": bool(np.abs(pl["cut_m"]).max() > ts.MAX_CUT_M),
                         "crossings": pl["crossings"]})
    corridor = ts.stamp_roads(h, water_s, grid, plans)
    return plans, road_out, grade_of, corridor


def build(upload: bool = True) -> dict:
    from tools.argonia_world import db
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "crops").mkdir(exist_ok=True)
    w = db.open("newworld")
    water_px = np.asarray(Image.open(f.OUT / "raster" / "water.png")).astype(bool)
    foreign_px = np.asarray(Image.open(f.OUT / "raster" / "foreign.png")).astype(bool)
    cell_region = json.loads((f.OUT / "cell_region.json").read_text())
    scope = json.loads((f.OUT / "scope_cells.json").read_text())
    regions = w.rows("region")
    names = [r.id for r in regions]
    rkind = {r.id: r.kind for r in regions}
    params, psrc = {}, {}
    for r in regions:
        params[r.id], psrc[r.id] = tr.region_params(r)
    for extra in ("foreign", "islet"):
        fl, su, ro, cl, we, ramp, form = tr.FALLBACK[extra]
        params[extra] = {"floor": fl, "summit": su, "rough": ro, "cliff": cl, "wet": we, "ramp": ramp, "form": form}
        psrc[extra] = f"fallback '{extra}'"
    word = {r.id: (tr.landform_word(r.landform) or tr.landform_word(r.name) or tr.NAME_GUESS.get(r.id))
            for r in regions}
    grid = make_grid(scope)
    log("grid", grid.rows, "x", grid.cols)

    # 3. water bodies
    rpx = region_px(cell_region, names, water_px.shape)
    body_r, bodies = tw.label_bodies(water_px, rpx, names, rkind, word, f.UNITS_PER_PX / f.UNITS_PER_METRE)
    tw.flow(body_r, bodies, {k.id: k.flows for k in w.rows("water_kind")})
    ov_file = f.ROOT / "sources" / "water_overrides.json"
    overrides = json.loads(ov_file.read_text()) if ov_file.exists() else {}
    ov_problems = tw.apply_overrides(bodies, overrides, {k.id for k in w.rows("water_kind")})
    log("water bodies", len(bodies))
    Image.fromarray(body_r.astype(np.uint16)).save(OUT / "water_bodies.png")
    (OUT if TRIAL else f.OUT).joinpath("water_bodies.json").write_text(json.dumps(
        [{k: b.get(k) for k in ("id", "water_kind_id", "area_m2", "label_px", "label_py", "flows", "flow_note",
                                "why", "raster_index", "region_id", "flow_deg", "name", "overridden")} for b in bodies], indent=1, default=_j))

    # the smooth coast: the map's shores as smoothed polylines, filled and turned into a signed distance on the
    # samples (terrain_coast.sample_contour)
    sd_m = tc.sample_contour(water_px, grid, SEED)
    rejoined = tc.repair(sd_m, grid, water_px)
    water_s = sd_m < 0
    coast = tc.agreement(water_s, grid, water_px)
    coast["bodies_rejoined"] = rejoined
    log("coast", coast)

    # 4. relief
    C = tr.COARSE
    ci, cj = np.mgrid[0:grid.rows // C + 2, 0:grid.cols // C + 2]
    wx, wy = grid.ox + cj * C * ts.STEP, grid.oy - ci * C * ts.STEP
    cpx, cpy = f.world_to_px(wx, wy)
    H, W = water_px.shape
    inb = (cpx >= 0) & (cpx < W) & (cpy >= 0) & (cpy < H)
    ff = np.zeros(wx.shape)
    ff[inb] = ndi.uniform_filter(foreign_px.astype(np.float32), 5)[cpy[inb].astype(int), cpx[inb].astype(int)]
    ridge_cells = {}
    for rid in names:
        if params[rid]["form"] == "ridge":
            cs = np.array([list(map(int, k.split(","))) for k, v in cell_region.items() if v == rid], float)
            ridge_cells[rid] = (cs + 0.5) * f.CELL_UNITS
    Fc = tr.coarse_fields(wx, wy, cell_region, params, ff, {n for n in names if rkind[n] == "sea"}, ridge_cells)
    sea_c = np.ones(wx.shape, bool)
    kind_arr = np.array(["land"] + [b["water_kind_id"] for b in bodies])
    sea_body = np.isin(kind_arr, ["ocean", "bay"])[body_r]
    sea_c[inb] = sea_body[cpy[inb].astype(int), cpx[inb].astype(int)]
    coast_t = 1 - np.exp(-ndi.distance_transform_edt(~sea_c) * C * ts.STEP / f.UNITS_PER_METRE / 5000.0)
    shape = (grid.rows, grid.cols)
    F = {k: tr.upsample(v, shape, C, order=1) for k, v in Fc.items()}
    coast_full = tr.upsample(coast_t, shape, C, order=1)
    sm = grid.m
    wp = tr.warp_field(shape, sm, SEED + 7)
    n = {k: tr.fbm(shape, sm, tr.SCALES[k], SEED + s_, wp) for s_, k in
         ((8, "swell"), (0, "big"), (1, "mid"), (4, "knoll"), (9, "esc"))}
    n["edge"] = tr.edge_field(shape, sm, SEED, wp)
    del wp
    n.update(small=tr.fbm(shape, sm, tr.SCALES["small"], SEED + 2), amod=tr.fbm(shape, sm, tr.SCALES["amod"], SEED + 5),
             micro=tr.fbm(shape, sm, tr.SCALES["micro"], SEED + 6))
    log("noise and fields")
    relief_m = tr.relief(F, n, coast_full)
    del n
    relief_m = te.weather(relief_m, water_s, F, SEED)
    sym_tier0 = {s.id: s.settlement_tier_id for s in w.rows("symbol")}
    big = [(*(float(v) for v in grid.ij(p.px, p.py)), sym_tier0.get(p.symbol_id)) for p in w.rows("place")
           if sym_tier0.get(p.symbol_id) in te.BUILD_R_M and not p.on_water]
    settled = te.settle_places(relief_m, big, sm)
    log("weathered; large places settled", len(settled))

    # 5. banks and beds
    jx = np.clip(np.floor(grid.p0x + np.arange(grid.cols) * grid.k).astype(int), 0, W - 1)
    iy = np.clip(np.floor(grid.p0y + np.arange(grid.rows) * grid.k).astype(int), 0, H - 1)
    # each sample's bed is the body of its nearest map water pixel (the smooth coast moves banks by a pixel or two)
    near_y, near_x = ndi.distance_transform_edt(~water_px, return_distances=False, return_indices=True)
    bidx = body_r[near_y[np.ix_(iy, jx)], near_x[np.ix_(iy, jx)]]
    del near_y, near_x
    slope_k = np.array([0.0] + [ts.BED[b["water_kind_id"]][0] for b in bodies], np.float32)
    cap_k = np.array([0.0] + [ts.BED[b["water_kind_id"]][1] for b in bodies], np.float32)
    off = ~((grid.p0x + np.arange(grid.cols) * grid.k >= 0) & (grid.p0x + np.arange(grid.cols) * grid.k < W))[None, :] \
        | ~((grid.p0y + np.arange(grid.rows) * grid.k >= 0) & (grid.p0y + np.arange(grid.rows) * grid.k < H))[:, None]
    bed_slope = np.where(off, ts.BED["ocean"][0], slope_k[bidx])
    bed_cap = np.where(off, ts.BED["ocean"][1], cap_k[bidx])
    # a water sample whose own pixel class disagrees (nearest-pixel edge cases) takes stream bed
    bed_slope = np.where(water_s & (bed_slope == 0), 0.12, bed_slope)
    bed_cap = np.where(water_s & (bed_cap == 0), 1.2, bed_cap)
    h, d_land, d_water = ts.compose(water_s, relief_m, F["ramp"], bed_slope, bed_cap, sm, sd_m)
    del relief_m, bed_slope, bed_cap, d_land, d_water
    log("composed")

    # places
    tiers = {t.id: t.footprint_radius_m for t in w.rows("settlement_tier")}
    sym_tier = {s.id: s.settlement_tier_id for s in w.rows("symbol")}
    try:
        need_rows = w.rows("place_terrain_need")
    except Exception:
        need_rows = []
    needs = {}
    for r in need_rows:
        needs.setdefault(r.place_id, []).append((r.terrain_need_id, r.radius_m, r.facing_deg, "table: " + r.why))
    place_out, todo = [], []
    for p in w.rows("place"):
        tier_r = tiers.get(sym_tier.get(p.symbol_id))
        rad = p.footprint_radius_m or tier_r
        lst = needs.get(p.id)
        if lst is None:
            nd = ts.FALLBACK_NEEDS.get(p.place_kind_id)
            if nd == "seabed" and not p.on_water:
                nd = None
            lst = [] if nd is None else [(nd, rad if nd == "flat-pad" and rad else NEED_DEFAULT_R.get(nd, rad or 25.0),
                                          None, f"fallback for kind {p.place_kind_id}")]
        i0, j0 = (float(v) for v in grid.ij(p.px, p.py))
        if not (2 <= i0 < grid.rows - 2 and 2 <= j0 < grid.cols - 2):
            continue
        for nd, r_m, facing, why in lst:
            todo.append((NEED_ORDER.get(nd, 9), p, nd, r_m, facing, why, i0, j0))
    todo.sort(key=lambda t: (t[0], t[1].id))
    entrances = []
    roads_done = False
    corridor = plans = None

    def shape_entrance(rec, i0, j0, facing):
        """Try the road's or table's heading, the best free one, every heading, then nearby spots; keep the first
        whose corridor is dry and open."""
        if facing is None or ts.ray_dry(water_s, grid, i0, j0, facing) < 1:
            facing = toward_road(plans, grid, i0, j0, facing)
        spot = None
        tries = [(i0, j0, pref) for pref in (facing, None, *range(0, 360, 30))]
        tries += [(i0 - r / grid.m * math.cos(math.radians(a)), j0 + r / grid.m * math.sin(math.radians(a)), None)
                  for r in (10, 20, 30) for a in range(0, 360, 45)]
        for ti, tj, pref in tries:   # the road's or table's heading, the best free one, any; then nearby spots
            spot = ts.place_entrance(h, water_s, grid, ti, tj, pref)
            if spot is None:
                continue
            sl = (slice(max(0, int(spot[0]) - 40), int(spot[0]) + 41),
                  slice(max(0, int(spot[1]) - 40), int(spot[1]) + 41))
            before = h[sl].copy()
            ts.entrance(h, water_s, grid, spot[0], spot[1], spot[2], protect=corridor)
            if ts.entrance_ok(h, water_s, None, grid, spot[0], spot[1], spot[2])["open"]:
                break
            h[sl] = before
            spot = None
        if spot is None:
            spot = ts.place_entrance(h, water_s, grid, i0, j0, facing)
            if spot is not None:
                ts.entrance(h, water_s, grid, spot[0], spot[1], spot[2], protect=corridor)
        if spot is None:
            rec["note"] = "no dry corridor within 40 m"
            rec.update(dry=False, open=False)
        else:
            ei, ej, f_deg, moved = spot
            epx, epy = grid.px(ei, ej)
            rec.update(facing_deg=f_deg, table_facing_deg=facing, moved_m=round(moved, 1),
                       entrance_px=[round(float(epx), 1), round(float(epy), 1)])
            entrances.append((rec, ei, ej, f_deg, i0, j0, facing))

    for order, p, nd, r_m, facing, why, i0, j0 in todo:
        if order >= NEED_ORDER["entrance-in-slope"] and not roads_done:
            plans, road_out, grade_of, corridor = lay_roads(h, water_px, water_s, grid, w)
            roads_done = True
        rec = {"place_id": p.id, "need": nd, "radius_m": r_m, "why": why, "px": p.px, "py": p.py}
        if nd == "flat-pad":
            if p.on_water:
                rec["note"] = "on water: stands on stilts, no pad"
            else:
                pad = ts.flat_pad(h, water_s, grid, i0, j0, r_m)
                rec["pad_m"] = None if pad is None else round(pad / ts.U, 2)
        elif nd == "rise":
            ts.rise(h, water_s, grid, i0, j0, r_m)
        elif nd == "shore-access":
            ts.shore_access(h, water_s, grid, i0, j0, r_m)
        elif nd == "seabed":
            ts.seabed(h, water_s, grid, i0, j0, r_m, SEABED_DEPTH.get(p.place_kind_id, 6.0))
        elif nd == "entrance-in-slope":
            shape_entrance(rec, i0, j0, facing)
        place_out.append(rec)
    if not roads_done:
        plans, road_out, grade_of, corridor = lay_roads(h, water_px, water_s, grid, w)
    log("places", len(place_out), "roads", len(plans))

    # LAND format and the water guarantee
    h = ts.quantise(h)
    passes = ts.clamp_steps(h)
    held = ts.hold_water(h, water_s)
    ts.clamp_steps(h)
    fails = []
    log("water held", held, "clamp passes", passes)
    cliff = ts.slope_deg(h) > CLIFF_DEG

    # entrances judged on the finished ground; any spoiled by the rounding or the water guarantee is shaped again
    for _round in range(3):
        redo = [e for e in entrances if not ts.entrance_ok(h, water_s, cliff, grid, e[1], e[2], e[3])["open"]]
        if not redo:
            break
        for e in redo:
            entrances.remove(e)
            shape_entrance(e[0], e[4], e[5], e[6])
        h = ts.quantise(h)
        ts.clamp_steps(h)
        ts.hold_water(h, water_s)
        ts.clamp_steps(h)
        cliff = ts.slope_deg(h) > CLIFF_DEG
        log("entrances reshaped", len(redo))
    for rec, i0, j0, facing, *_ in entrances:
        rec.update(ts.entrance_ok(h, water_s, cliff, grid, i0, j0, facing))

    # outputs
    np.save(OUT / "heightmap.npy", h)
    offset = float(h.min())
    v = np.clip(np.round((h - offset) / ts.QUANT), 0, 65535).astype(np.uint16)
    Image.fromarray(v).save(OUT / "heightmap.png")
    Image.fromarray((cliff * 255).astype(np.uint8)).save(OUT / "cliff.png")
    (OUT / "places_terrain.json").write_text(json.dumps(place_out, indent=1, default=_j))
    (OUT / "roads_terrain.json").write_text(json.dumps(road_out, indent=1, default=_j))
    hillshade(h, water_s, 4).save(OUT / "hillshade.png")
    crops(h, water_s, grid, w)
    chk = check(h, grid, water_px, plans, grade_of, place_out, cliff)
    chk["guarantee_fails_px"] = fails[:200]
    chk["coast"] = coast
    (OUT / "check.json").write_text(json.dumps(chk, indent=1, default=_j))
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sha = hashlib.sha256((OUT / "heightmap.npy").read_bytes()).hexdigest()
    bjson = {"id": stamp, "water_level_units": ts.WATER_LEVEL, "sample_units": ts.STEP, "width": grid.cols,
             "height": grid.rows, "origin_world_x": grid.ox, "origin_world_y": grid.oy,
             "files": f"out/newworld/terrain/ and {BUCKET}/{stamp}/", "sha256": sha,
             "about": ("float32 game units (70 a metre), north-up, row 0 the north edge; heightmap.png is 16-bit: "
                       f"h = {offset} + 8 v units; water bodies at map px; cliffs over {CLIFF_DEG} deg"),
             "png_offset_units": offset, "png_scale_units": ts.QUANT,
             "regions": psrc, "water_overrides": len(overrides), "water_override_problems": ov_problems, "roads_used": bool(plans), "settled_places": settled, "seconds": round(time.time() - t0)}
    (OUT / "build.json").write_text(json.dumps(bjson, indent=1, default=_j))
    log("checks", json.dumps({k: v for k, v in chk.items() if k != "guarantee_fails_px"}, default=_j))
    if upload and not TRIAL:
        subprocess.run(["aws", "s3", "cp", "--recursive", "--quiet", str(OUT), f"{BUCKET}/{stamp}/"], check=True)
        subprocess.run(["aws", "s3", "cp", "--quiet", str(f.OUT / "water_bodies.json"), f"{BUCKET}/{stamp}/"],
                       check=True)
        log("uploaded", f"{BUCKET}/{stamp}/")
    return bjson


def check(h, grid, water_px, plans=None, grade_of=None, places=None, cliff=None) -> dict:
    box = ts.px_box(grid, water_px.shape)
    l, t, r, b = box
    vals, _, _ = ts.pixel_values(h, grid, box)
    wat = water_px[t:b, l:r]
    bad_l = np.argwhere(~wat & (vals <= ts.WATER_LEVEL))
    bad_w = np.argwhere(wat & (vals >= ts.WATER_LEVEL))
    out = {"pixels": int(wat.size), "water_pixels_under": round(1 - len(bad_w) / max(1, wat.sum()), 6),
           "land_pixels_above": round(1 - len(bad_l) / max(1, (~wat).sum()), 6),
           "land_exceptions_px": [(int(x + l), int(y + t)) for y, x in bad_l[:50]],
           "water_exceptions_px": [(int(x + l), int(y + t)) for y, x in bad_w[:50]],
           "land_format": ts.land_format(h)}
    sd = ts.slope_deg(h)
    out["slope_share_over_55"] = round(float((sd > CLIFF_DEG).mean()), 4)
    out["slope_share_over_30"] = round(float((sd > 30).mean()), 4)
    if plans:
        out["roads"] = ts.road_checks(h, grid, plans, grade_of)
    if places:
        ent = [p for p in places if p["need"] == "entrance-in-slope"]
        out["entrances"] = len(ent)
        out["entrances_bad"] = [(p["place_id"], p.get("dry"), p.get("open")) for p in ent
                                if not (p.get("dry") and p.get("open"))]
    return out


def hillshade(h, water_s, stride=1, light=(315, 45)):
    hs = h[::stride, ::stride].astype(np.float32) / ts.U
    gy, gx = np.gradient(hs, ts.STEP / ts.U * stride)
    az, alt = map(math.radians, light)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    sh = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    sh = np.clip(sh, 0, 1)
    tint = np.clip(hs / 150.0, 0, 1)
    rgb = np.stack([0.55 + 0.35 * tint, 0.6 + 0.15 * tint, 0.4 + 0.2 * tint], -1) * sh[..., None] * 255
    wm = water_s[::stride, ::stride]
    depth = np.clip(-hs / 20.0, 0, 1)
    rgb[wm] = np.stack([60 - 30 * depth[wm], 110 - 50 * depth[wm], 170 - 50 * depth[wm]], -1)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def crops(h, water_s, grid, w):
    helstrom = [p for p in w.rows("place") if p.id == "helstrom"]
    half = 600
    for name, at in CROPS.items():
        if at is None and helstrom:
            at = (helstrom[0].px, helstrom[0].py)
        if at is None:
            continue
        i, j = (int(v) for v in grid.ij(*at))
        sl = (slice(max(0, i - half), i + half), slice(max(0, j - half), j + half))
        hillshade(h[sl], water_s[sl], 1).save(OUT / "crops" / f"{name}.png")


def check_built() -> int:
    from tools.argonia_world import db  # noqa: F401
    b = json.loads((OUT / "build.json").read_text())
    h = np.load(OUT / "heightmap.npy")
    sha = hashlib.sha256((OUT / "heightmap.npy").read_bytes()).hexdigest()
    water_px = np.asarray(Image.open(f.OUT / "raster" / "water.png")).astype(bool)
    p0x, p0y = f.world_to_px(b["origin_world_x"], b["origin_world_y"])
    grid = ts.Grid(rows=b["height"], cols=b["width"], p0x=p0x, p0y=p0y, ox=b["origin_world_x"],
                   oy=b["origin_world_y"])
    chk = check(h, grid, water_px)
    old = json.loads((OUT / "check.json").read_text())
    for k in ("roads", "entrances", "entrances_bad", "coast"):
        if k in old:
            chk[k] = old[k]
    chk["sha256_matches"] = sha == b["sha256"]
    print(json.dumps(chk, indent=1, default=_j))
    # the smooth coast moves banks by a pixel or two: the map's water and land are held on 4 px blocks
    ok = (chk["water_pixels_under"] >= MAP_HELD and chk["land_pixels_above"] >= MAP_HELD
          and chk.get("coast", {}).get("blocks4", 0) >= BLOCKS_HELD and chk["land_format"]["ok"]
          and chk["sha256_matches"] and not chk.get("entrances_bad")
          and chk.get("roads", {}).get("grade_over_limit_points", 0) == 0)
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["check"]:
        sys.exit(check_built())
    build(upload="--no-upload" not in sys.argv)
