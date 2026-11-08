"""Water kinds and flow (nw-02 step 5): every water body of the current terrain build classified by its shape, its
place and its region's ecology, never by its level (all water is at 0), then the owner's edits applied last.

Rerunnable on whatever `out/newworld/water_bodies.json` + `out/newworld/terrain/water_bodies.png` the terrain build
last wrote. Writes `out/newworld/water_classified.json` (one row per body) and `out/newworld/water_classified.png`
(16-bit body index, map px; a painted area is its own body), which build_db reads into the `water_body` table.

The recipe:
1. Sea water (the terrain's ocean and bay bodies) is cut again pixel by pixel, so kinds follow the shore and not the
   region cells: `bay` where land covers over 45% of the ground within 3 km, else `shallow-coast` within 450 m of
   land, else `ocean`; pieces under 0.2 km2 take the kind around them.
2. Running water. `estuary` stays (a channel's last ~220 m before the sea). A channel is a `river` when its mean
   width is 40 m or more, else a `stream`. Channel water with no water path to the sea and no lake to feed is read
   by its region: in a swamp region it is still swamp water of that region's kind, elsewhere a stream that runs
   downhill on the built terrain.
3. Still inland water: open water of 0.5 km2 or more is a `lake`; smaller still water takes its region's wet character:
   `blackwater-swamp` (trees over the water: forest, Hist, cypress, bog, root, moss in the region's biome, landform
   and ecology), `green-marsh` (open reed water: reed, sedge, cattail, fen, rice, paddy, bayou), else `pond`.
4. Flow. Every water pixel has its distance to the open sea along the water (Dijkstra). A running body flows from its
   farthest pixel toward its nearest; its downstream body is the neighbour that holds the lowest distance it
   touches; a body without a sea path runs into the lake it touches, else downhill on the terrain.
   Speed: `still`; `slow` for estuaries, rivers 150 m wide or more, and any running water in a region of wetness
   0.8 or more (swamp, bayou, basin); `fast` for streams in rough country (region roughness 4 m or more, or summit
   50 m or more); else `moderate`.
5. The owner's edits, last: `newworld/sources/water_paint.json` (strokes that paint a kind and flow over an area,
   splitting the bodies they cross; later strokes win), then `newworld/sources/water_overrides.json` (per body id:
   water_kind_id, flows, flow_toward_deg, speed, name). Both are written by tools/newworld/water_overrides_pull.py
   from the atlas's water editor.

    python3 -m tools.newworld.water_kinds            # classify; prints counts
    python3 -m tools.newworld.water_kinds --png      # also a classification picture, out/newworld/water_kinds.png
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

from tools.newworld import frame as f

DB = f.ROOT / "story" / "data" / "db"
SRC = f.ROOT / "sources"
M_PX = f.UNITS_PER_PX / f.UNITS_PER_METRE          # 2.93 m
EIGHT = np.ones((3, 3), bool)
SEA = ("ocean", "shallow-coast", "bay")
RUNNING = ("estuary", "river", "stream")
COAST_M, ENCLOSE_M, ENCLOSED_LAND = 450, 3000, 0.45
RIVER_W_M, SLOW_W_M, LAKE_M2 = 40, 150, 500_000
TREE_WORDS = {"forest", "hist", "cypress", "bog", "root", "roots", "moss", "mosses", "jungle", "trees", "wood", "mangrove", "mangroves", "swamp"}
REED_WORDS = {"reed", "reeds", "sedge", "cattail", "cattails", "fen", "rice", "saltrice", "paddy", "paddies", "bayou",
              "marsh", "lilies", "flats"}
SPEEDS = ("still", "slow", "moderate", "fast")
COLOURS = {"ocean": (31, 64, 122), "shallow-coast": (72, 140, 190), "bay": (52, 104, 160), "estuary": (150, 110, 200),
           "river": (40, 170, 230), "stream": (120, 220, 250), "lake": (20, 120, 140), "pond": (110, 190, 160),
           "green-marsh": (110, 170, 60), "blackwater-swamp": (70, 50, 30)}


def jsonl(name: str) -> list:
    p = DB / f"{name}.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def region_character() -> dict:
    """region id -> {'wet': blackwater-swamp | green-marsh | pond, 'swampy': bool, 'rough': bool, 'wetness': float,
    'name', 'why'}, read from the region research (biome, landform, ecology and look notes)."""
    notes: dict = {}
    for n in jsonl("region_note"):
        if n["aspect_id"] in ("ecology", "look", "landscape"):
            notes.setdefault(n["region_id"], []).append(n["text"])
    out = {}
    for r in jsonl("region"):
        text = " ".join([r.get("biome") or "", r.get("landform") or "", *notes.get(r["id"], [])]).lower()
        words = re.findall(r"[a-z]+", text)
        tree = sum(w in TREE_WORDS for w in words)
        reed = sum(w in REED_WORDS for w in words)
        wetness = float(r.get("wetness") or 0)
        if r["kind"] == "sea":
            wet = "pond"
        elif wetness < 0.6 and tree + reed < 4:
            wet = "pond"
        elif tree > reed:
            wet = "blackwater-swamp"
        else:
            wet = "green-marsh"
        out[r["id"]] = {"name": r["name"], "wet": wet, "wetness": wetness, "swampy": wetness >= 0.8,
                        "rough": (r.get("roughness_m") or 0) >= 4 or (r.get("elevation_summit_m") or 0) >= 50,
                        "why": f"{r['name']}: wetness {wetness:g}, {tree} tree words, {reed} reed words "
                               f"in its biome, landform and ecology"}
    return out


def region_raster(shape) -> tuple[np.ndarray, list]:
    from tools.newworld.terrain import region_px          # the terrain build's own cell -> pixel reading
    cell_region = json.loads((f.OUT / "cell_region.json").read_text())
    names = sorted(set(cell_region.values()))
    return region_px(cell_region, names, shape), names


def heights_px(shape):
    """The built heightmap sampled at map pixels (metres), or None."""
    tb = f.OUT / "terrain" / "build.json"
    if not tb.exists():
        return None
    b = json.loads(tb.read_text())
    hm = np.load(f.OUT / "terrain" / "heightmap.npy", mmap_mode="r")
    ys, xs = np.mgrid[0:shape[0]:4, 0:shape[1]:4]
    wx, wy = f.px_to_world(xs + 0.5, ys + 0.5)
    col = np.clip(np.round((wx - b["origin_world_x"]) / b["sample_units"]).astype(int), 0, hm.shape[1] - 1)
    row = np.clip(np.round((b["origin_world_y"] - wy) / b["sample_units"]).astype(int), 0, hm.shape[0] - 1)
    small = np.asarray(hm[row, col], np.float32) / f.UNITS_PER_METRE
    return np.kron(small, np.ones((4, 4), np.float32))[:shape[0], :shape[1]]


def body_id(mask: np.ndarray, dist: np.ndarray, sl) -> tuple[str, int, int]:
    dm = np.where(mask, dist[sl], -1)
    ly, lx = np.unravel_index(int(np.argmax(dm)), mask.shape)
    px, py = int(lx + sl[1].start), int(ly + sl[0].start)
    return f"wb-{px}-{py}", px, py


def split_sea(raster, bodies, land, nxt):
    """Step 1: all sea water is cut again by pixel, so the kinds follow the shore and not the region cells."""
    sea_idx = [b["index"] for b in bodies if b["kind"] in ("ocean", "bay")]
    sea = np.isin(raster, sea_idx)
    coast = ndi.distance_transform_edt(~land) <= COAST_M / M_PX
    k = 8
    small = land[::k, ::k].astype(np.float32)
    r = int(ENCLOSE_M / M_PX / k)
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disc = (xx * xx + yy * yy <= r * r).astype(np.float32)
    from scipy.signal import fftconvolve
    share = fftconvolve(np.pad(small, r, mode="edge"), disc / disc.sum(), mode="same")[r:-r, r:-r]
    share = np.kron(share, np.ones((k, k), np.float32))[:land.shape[0], :land.shape[1]]
    cls = np.zeros(raster.shape, np.int8)                 # 1 ocean, 2 shallow-coast, 3 bay
    cls[sea] = 1
    cls[sea & coast] = 2
    cls[sea & (share > ENCLOSED_LAND)] = 3
    # pieces under 0.2 km2 take the class around them
    for c in (1, 2, 3):
        lab, n = ndi.label(cls == c, EIGHT)
        if not n:
            continue
        sizes = np.bincount(lab.ravel())
        tiny = (lab > 0) & (sizes[lab] < 200_000 / (M_PX * M_PX))
        keep = sea & ~tiny & (cls != c)
        if tiny.any() and keep.any():
            _, (ii, jj) = ndi.distance_transform_edt(~keep, return_indices=True)
            cls[tiny] = cls[ii[tiny], jj[tiny]]
    out = [b for b in bodies if b["kind"] not in ("ocean", "bay")]
    raster[sea] = 0
    names = {1: ("ocean", f"open sea more than {COAST_M} m from land, with land on under {ENCLOSED_LAND:.0%} "
                          "of the ground within 3 km"),
             2: ("shallow-coast", f"the sea within {COAST_M} m of land"),
             3: ("bay", f"sea water with land on over {ENCLOSED_LAND:.0%} of the ground within 3 km")}
    for c, (kind, why) in names.items():
        lab, n = ndi.label(cls == c, EIGHT)
        for j, sl in enumerate(ndi.find_objects(lab), 1):
            if sl is None:
                continue
            i = nxt()
            raster[sl][lab[sl] == j] = i
            out.append({"index": i, "id": None, "kind": kind, "src_kind": kind, "why": why, "src_why": why})
    return out


def classify(png: bool = False) -> dict:
    bj = json.loads((f.OUT / "water_bodies.json").read_text())
    raster = np.asarray(Image.open(f.OUT / "terrain" / "water_bodies.png")).astype(np.int32)
    water = raster > 0
    land = ~water
    regions, names = region_raster(raster.shape)
    rchar = region_character()
    dist = ndi.distance_transform_edt(water)
    counter = [int(raster.max())]

    def nxt():
        counter[0] += 1
        return counter[0]

    objs = ndi.find_objects(raster)
    bodies = []
    for s in bj:
        i = s["raster_index"]
        sl = objs[i - 1]
        if sl is None:
            continue
        m = raster[sl] == i
        reg_codes = regions[sl][m]
        rc = np.bincount(reg_codes + 1).argmax() - 1
        bodies.append({"index": i, "id": s["id"], "sl": sl, "src_kind": s["water_kind_id"], "kind": s["water_kind_id"],
                       "src_why": s["why"], "why": s["why"], "area_m2": s["area_m2"], "px": s["label_px"],
                       "py": s["label_py"], "region": names[rc] if rc >= 0 else None})
    bodies = split_sea(raster, bodies, land, nxt)

    # step 5a: paint strokes split bodies before the rest is decided, so a painted area is its own body
    paint = json.loads((SRC / "water_paint.json").read_text()) if (SRC / "water_paint.json").exists() else []
    painted, cut = {}, set()
    for st in paint:
        pm = np.zeros(raster.shape, bool)
        rr = max(1, int(st.get("radius_px", 20)))
        for x, y in st["points"]:
            x0, x1, y0, y1 = max(0, int(x) - rr), min(raster.shape[1], int(x) + rr + 1), \
                max(0, int(y) - rr), min(raster.shape[0], int(y) + rr + 1)
            yy, xx = np.mgrid[y0:y1, x0:x1]
            pm[y0:y1, x0:x1] |= (xx - x) ** 2 + (yy - y) ** 2 <= rr * rr
        pm &= water
        if not pm.any():
            continue
        cut |= set(np.unique(raster[pm]).tolist())
        lab, n = ndi.label(pm, EIGHT)
        for j in range(1, n + 1):
            i = nxt()
            raster[lab == j] = i
            painted[i] = st
    # rebuild the body list from the raster (painted pieces; bodies cut in two by a stroke split into parts)
    byindex = {b["index"]: b for b in bodies}
    dist = ndi.distance_transform_edt(water)
    final = np.zeros_like(raster)
    rows = []
    objs = ndi.find_objects(raster)
    for i, sl in enumerate(objs, 1):
        if sl is None:
            continue
        m0 = raster[sl] == i
        lab, n = ndi.label(m0, EIGHT) if i in cut else (m0.astype(np.int32), 1)
        for j in range(1, n + 1):
            m = lab == j
            if m.sum() < 20 and n > 1:
                continue
            k = len(rows) + 1
            final[sl][m] = k
            bid, px, py = body_id(m, dist, sl)
            src = byindex.get(i)
            reg_codes = regions[sl][m]
            rc = np.bincount(reg_codes + 1).argmax() - 1
            row = {"id": bid, "raster_index": k, "area_m2": round(float(m.sum()) * M_PX * M_PX, 1),
                   "label_px": px, "label_py": py, "region_id": names[rc] if rc >= 0 else None,
                   "kind": src["kind"] if src else "pond", "src_kind": src["src_kind"] if src else "pond",
                   "why": src["why"] if src else "", "width_m": round(4 * float(dist[sl][m].mean()) * M_PX, 1),
                   "set_by": "derived"}
            if i in painted:
                st = painted[i]
                row.update(kind=st["water_kind_id"], why=f"owner painted {st['water_kind_id']}", set_by="owner",
                           paint=st)
            rows.append(row)
    raster = final

    # steps 2 and 3: running and still inland water
    for r in rows:
        if r["set_by"] == "owner" or r["kind"] in SEA or r["kind"] == "estuary":
            continue
        ch = rchar.get(r["region_id"]) or {"wet": "pond", "name": "the margin", "swampy": False}
        if r["src_kind"] in ("river", "stream"):
            r["kind"] = "river" if r["width_m"] >= RIVER_W_M else "stream"
            r["why"] = f"a channel {r['width_m']:.0f} m wide on average"
        elif r["area_m2"] >= LAKE_M2:
            r["kind"], r["why"] = "lake", f"open still water of {r['area_m2'] / 1e6:.1f} km2"
        else:
            r["kind"] = ch["wet"]
            r["why"] = (f"still water ({r['area_m2'] / 1e4:.1f} ha) in {ch['name']}, whose research reads "
                        + {"blackwater-swamp": "as tree swamp", "green-marsh": "as open reed marsh",
                           "pond": "as dry or firm ground"}[ch["wet"]])

    # step 4: distance to the open sea along the water
    kind_of = np.array(["land"] + [r["kind"] for r in rows])
    seam = np.isin(kind_of, SEA)[raster]
    gmap = sea_distance(raster, seam)
    adj = adjacency(raster)
    hts = heights_px(raster.shape)
    objs = ndi.find_objects(raster)
    by_k = {r["raster_index"]: r for r in rows}
    gfin = np.where(np.isfinite(gmap), gmap, 1e12)
    gmin = dict(zip(range(1, len(rows) + 1), ndi.minimum(gfin, raster, np.arange(1, len(rows) + 1)).tolist()))
    for r in rows:
        r["flows"] = r["kind"] in RUNNING
        r.update(flow_deg=None, downstream_id=None, speed="still", flow_note="still water")
    for r in rows:
        if r["kind"] not in RUNNING or r["set_by"] == "owner":
            continue
        k, sl = r["raster_index"], objs[r["raster_index"] - 1]
        m = raster[sl] == k
        gv = np.where(m, gmap[sl], np.nan)
        fin = np.isfinite(gv)
        ch = rchar.get(r["region_id"]) or {"swampy": False, "rough": False, "wet": "pond", "name": "the margin"}
        if fin.any():
            hi = np.unravel_index(np.nanargmax(np.where(fin, gv, np.nan)), m.shape)
            lo = np.unravel_index(np.nanargmin(np.where(fin, gv, np.nan)), m.shape)
            lowest = min(adj.get(k, ()), key=lambda n: (by_k[n]["kind"] not in SEA, gmin[n]), default=None)
            note = f"toward the sea, {np.nanmin(gv) * M_PX / 1000:.1f} km on along the water"
        else:
            lakes = [n for n in adj.get(k, ()) if by_k[n]["kind"] in ("lake", "pond", "green-marsh",
                                                                       "blackwater-swamp")]
            if ch["swampy"] and not lakes:
                r.update(kind=ch["wet"] if ch["wet"] != "pond" else "green-marsh", flows=False,
                         why=f"channel water with no way to the sea in {ch['name']}, a swamp: still swamp water")
                continue
            if lakes:
                lowest = max(lakes, key=lambda n: by_k[n]["area_m2"])
                ys, xs = np.nonzero(m)
                ly, lx = by_k[lowest]["label_py"] - sl[0].start, by_k[lowest]["label_px"] - sl[1].start
                d = (ys - ly) ** 2 + (xs - lx) ** 2
                hi, lo = (ys[d.argmax()], xs[d.argmax()]), (ys[d.argmin()], xs[d.argmin()])
                note = f"into {by_k[lowest]['kind']} {by_k[lowest]['id']} (no way to the sea on the map)"
            elif hts is not None:
                hv = np.where(m, hts[sl], np.nan)
                hi = np.unravel_index(np.nanargmax(hv), m.shape)
                lo = np.unravel_index(np.nanargmin(hv), m.shape)
                lowest, note = None, "downhill on the built terrain (no way to the sea on the map)"
            else:
                r["flow_note"] = "direction left for a hand call"
                continue
        dx, dy = lo[1] - hi[1], lo[0] - hi[0]
        r["flow_deg"] = round((math.degrees(math.atan2(dx, -dy)) + 360) % 360) if (dx or dy) else None
        r["downstream_id"] = by_k[lowest]["id"] if lowest else None
        if r["kind"] == "estuary" or r["width_m"] >= SLOW_W_M or ch["swampy"]:
            r["speed"] = "slow"
        elif r["kind"] == "stream" and ch["rough"]:
            r["speed"] = "fast"
        else:
            r["speed"] = "moderate"
        r["flow_note"] = note

    # step 5b: per-body overrides, last
    ovp = SRC / "water_overrides.json"
    ov = json.loads(ovp.read_text()) if ovp.exists() else {}
    for r in rows:
        if r.get("paint"):
            st = r.pop("paint")
            r["flows"] = bool(st.get("flows", r["kind"] in RUNNING))
            r["flow_deg"] = st.get("flow_toward_deg")
            r["speed"] = st.get("speed") or ("moderate" if r["flows"] else "still")
            r["flow_note"] = "owner painted"
        o = ov.get(r["id"])
        if not o:
            continue
        r["set_by"] = "owner"
        if o.get("water_kind_id"):
            r["kind"], r["why"] = o["water_kind_id"], "owner set the kind"
        if "flows" in o:
            r["flows"] = bool(o["flows"])
            if not r["flows"]:
                r.update(speed="still", flow_deg=None, downstream_id=None, flow_note="owner: still")
        if o.get("flow_toward_deg") is not None:
            r["flow_deg"], r["flow_note"] = round(float(o["flow_toward_deg"])) % 360, "owner drew the direction"
        if o.get("speed") in SPEEDS:
            r["speed"] = o["speed"]
        elif r["flows"] and r["speed"] == "still":
            r["speed"] = "moderate"
        if o.get("name"):
            r["name"] = o["name"]
    for r in rows:
        r.pop("src_kind", None)
        r["water_kind_id"] = r.pop("kind")
        r.setdefault("name", None)
    Image.fromarray(raster.astype(np.uint16)).save(f.OUT / "water_classified.png")
    (f.OUT / "water_classified.json").write_text(json.dumps(rows, indent=1, default=float))
    if png:
        picture(raster, rows)
    return {"bodies": len(rows), "kinds": Counter(r["water_kind_id"] for r in rows),
            "flowing": sum(r["flows"] for r in rows), "speeds": Counter(r["speed"] for r in rows),
            "owner": sum(r["set_by"] == "owner" for r in rows),
            "overrides_without_a_body": sorted(set(ov) - {r["id"] for r in rows})}


def sea_distance(raster: np.ndarray, sea: np.ndarray) -> np.ndarray:
    run = (raster > 0) & ~sea
    n = int(run.sum())
    node = np.full(raster.shape, -1, np.int64)
    node[run] = np.arange(n)
    H, W = raster.shape
    rows, cols, wts = [], [], []
    for dy, dx, w in ((0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))):
        a = node[:H - dy, max(0, -dx):W - max(0, dx)]
        b = node[dy:, max(0, dx):W - max(0, -dx)]
        ok = (a >= 0) & (b >= 0)
        rows.append(a[ok]), cols.append(b[ok]), wts.append(np.full(ok.sum(), w))
    gmap = np.full(raster.shape, np.inf)
    src = run & ndi.binary_dilation(sea, EIGHT)
    if n and src.any():
        r, c = np.concatenate(rows + cols), np.concatenate(cols + rows)
        g = coo_matrix((np.concatenate(wts + wts), (r, c)), shape=(n, n)).tocsr()
        gmap[run] = dijkstra(g, directed=False, indices=node[src], min_only=True)
    return gmap


def adjacency(raster: np.ndarray) -> dict:
    adj: dict = {}
    for a, b in ((raster[:, :-1], raster[:, 1:]), (raster[:-1, :], raster[1:, :]),
                 (raster[:-1, :-1], raster[1:, 1:]), (raster[:-1, 1:], raster[1:, :-1])):
        ok = (a > 0) & (b > 0) & (a != b)
        for x, y in set(zip(a[ok].tolist(), b[ok].tolist())):
            adj.setdefault(x, set()).add(y)
            adj.setdefault(y, set()).add(x)
    return adj


def picture(raster: np.ndarray, rows: list) -> None:
    lut = np.zeros((len(rows) + 1, 3), np.uint8)
    lut[0] = (226, 214, 186)
    for r in rows:
        lut[r["raster_index"]] = COLOURS.get(r["water_kind_id"], (255, 0, 255))
    img = Image.fromarray(lut[raster])
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for r in rows:
        if r["flows"] and r["flow_deg"] is not None and r["area_m2"] > 30000:
            a = math.radians(r["flow_deg"])
            x, y = r["label_px"], r["label_py"]
            ex, ey = x + 18 * math.sin(a), y - 18 * math.cos(a)
            d.line((x, y, ex, ey), fill=(200, 20, 20), width=2)
            d.ellipse((ex - 3, ey - 3, ex + 3, ey + 3), fill=(200, 20, 20))
    y = 10
    for k, c in COLOURS.items():
        d.rectangle((10, y, 40, y + 20), fill=c, outline=(0, 0, 0))
        d.text((46, y + 4), k, fill=(0, 0, 0))
        y += 26
    img.save(f.OUT / "water_kinds.png")


if __name__ == "__main__":
    print(json.dumps(classify(png="--png" in sys.argv), indent=1, default=dict))
