"""Water kinds and flow (nw-02 step 5): every water body of the current terrain build classified by its shape, its
place and its region's ecology, never by its level (all water is at 0), then the owner's edits applied last.

Rerunnable on whatever `out/newworld/water_bodies.json` + `out/newworld/terrain/water_bodies.png` the terrain build
last wrote. Writes `out/newworld/water_classified.json` (one row per body) and `out/newworld/water_classified.png`
(16-bit body index, map px; a painted area is its own body), which build_db reads into the `water_body` table.

The recipe:
1. Sea water (the terrain's ocean and bay bodies) is cut again pixel by pixel, so kinds follow the shore and not the
   region cells: `bay` where land covers over 45% of the ground within 3 km, else `shallow-coast` within 450 m of
   land, else `ocean`; pieces under 0.2 km2 take the kind around them.
2. Whole water first. Pieces of water are joined across map gaps of up to ~18 m. A connected piece with no sea in it
   that is not a long through channel (its centreline under 3 km, or under 600 m when it reaches the map edge or a
   lake, or not ten times longer than wide) runs nowhere: it becomes one still body of one kind throughout, a lake
   from 0.5 km2, a pond where it opens 120 m across, else its region's wet character. In a channel network, a round
   still patch the width cut made is merged back into the channel it lies in, unless it truly opens into a lake
   (0.5 km2 and three times wider than the channels at it).
3. Kinds. A channel is a `river` when its mean width is 40 m or more, else a `stream`; `estuary` stays (a channel's
   last ~220 m before the sea). Other still water is a `lake` from 0.5 km2, a `pond` where it opens 120 m across,
   else its region's wet character: `blackwater-swamp` (trees over the water: forest, Hist, cypress, bog, root,
   moss, mangrove, swamp in the region's biome, landform and ecology), `green-marsh` (open reed water: reed, sedge,
   cattail, fen, rice, paddy, bayou, marsh), else `pond`.
4. Flow, along the channel graph. Every running pixel has its distance to its outlet along the water (Dijkstra, the
   sea first; still water is passed through for that distance, so a river leaving a lake runs on toward the sea).
   Water then runs pixel by pixel to the neighbour nearer the outlet, so it follows the channel's centreline, joins
   tributaries into the channel they meet and never reverses mid-channel; it stops where it enters still water
   (still bodies have no flow) and starts again where a channel leaves it. A network with no way to the sea runs to
   the map edge if it reaches it, else into the still water it touches, else out at its end nearest the sea. A
   body's bearing is its flow 32 px downstream of its label point; its downstream body is the first other body that
   walk reaches. Per Skyrim cell the mean flow goes to `out/newworld/water_flow_cells.json` for the plugin's per-cell
   type. Speed: `still`; `slow` for estuaries, rivers 150 m wide or more, and any running water in a region of
   wetness 0.8 or more; `fast` for streams in rough country (region roughness 4 m or more, or summit 50 m or more);
   else `moderate`.
5. The owner's edits, last: `newworld/sources/water_paint.json` (strokes that paint a kind and flow over an area,
   splitting the bodies they cross; later strokes win), then `newworld/sources/water_overrides.json` (water_kind_id,
   flows, flow_toward_deg, speed, name; found by `point`, a map pixel inside the body, so an edit survives a rebuild
   that changes ids; the body id is the fallback). Both are written by tools/newworld/water_overrides_pull.py
   from the atlas's water editor.

    python3 -m tools.newworld.water_kinds            # classify; prints counts
    python3 -m tools.newworld.water_kinds --png      # also a classification picture, out/newworld/water_kinds.png
    python3 -m tools.newworld.water_kinds --chunks   # and the 4 x 4 check: source map beside kinds and flow arrows,
                                                     # out/newworld/water_chunks/r<row>c<col>.png
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
RIVER_W_M, SLOW_W_M, LAKE_M2, OPEN_POND_M = 40, 150, 500_000, 120
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
    share = ndi.zoom(share, k, order=1)
    share = np.pad(share, ((0, max(0, land.shape[0] - share.shape[0])), (0, max(0, land.shape[1] - share.shape[1]))),
                   mode="edge")[:land.shape[0], :land.shape[1]]
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


STILL = ("lake", "pond", "green-marsh", "blackwater-swamp")


def reshape(raster, byindex, painted, water, regions, names, rchar):
    """Step 2a, by whole connected water: a closed piece of water that is not a long through channel is still water
    of one kind throughout (merged into one body); in a channel network a wide stretch that the width cut made a
    round still patch is merged back into the channel it lies in, unless it truly opens into a lake (0.5 km2 or
    more and three times wider than the channels at it). Returns the raster with merged bodies."""
    from skimage.morphology import skeletonize
    comp, _ = ndi.label(bridged(water), EIGHT)
    comp[~water] = 0
    # a body lying in several separate pieces of water is split, one body per piece
    top = int(raster.max()) + 1
    uniq, inv = np.unique(comp.astype(np.int64) * top + raster, return_inverse=True)
    raster = inv.reshape(raster.shape).astype(np.int32)          # land (key 0) stays 0
    old_by, old_paint = dict(byindex), dict(painted)
    byindex.clear()
    painted.clear()
    for new, old in enumerate((uniq % top).tolist()):
        if new and old in old_by:
            byindex[new] = dict(old_by[old], index=new)
        if new and old in old_paint:
            painted[new] = old_paint[old]
    n = int(raster.max())
    idx = np.arange(1, n + 1)
    comp_of = dict(zip(idx.tolist(), ndi.maximum(comp, raster, idx).astype(int).tolist()))
    dist = ndi.distance_transform_edt(water)
    area = dict(zip(idx.tolist(), ndi.sum(np.ones_like(raster), raster, idx).tolist()))
    rmax = dict(zip(idx.tolist(), ndi.maximum(dist, raster, idx).tolist()))
    wmean = dict(zip(idx.tolist(), (4 * ndi.mean(dist, raster, idx) * M_PX).tolist()))
    adj = adjacency(raster)
    edge = set(np.unique(np.concatenate([comp[0], comp[-1], comp[:, 0], comp[:, -1]])).tolist()) - {0}
    parent = {i: i for i in idx.tolist()}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def kind(i):
        b = byindex.get(i)
        return painted[i]["water_kind_id"] if i in painted else (b["kind"] if b else "pond")

    groups: dict = {}
    for i in idx.tolist():
        if area[i]:
            groups.setdefault(comp_of[i], []).append(i)
    cobj = ndi.find_objects(comp)
    for c, members in groups.items():
        if any(kind(i) in SEA for i in members):
            network = True
        else:
            sl = cobj[c - 1]
            m = comp[sl] == c
            a = float(m.sum())
            length = float(skeletonize(m).sum()) or 1.0
            width = a / length
            long_m = length * M_PX
            has_lake = any(kind(i) in STILL and area[i] * M_PX * M_PX >= LAKE_M2 for i in members)
            linear = length / max(width, 1.0) >= 10
            network = linear and (long_m >= 3000 or ((c in edge or has_lake) and long_m >= 600))
            if not network:
                keep = [i for i in members if i not in painted]
                if not keep:
                    continue
                big = max(keep, key=lambda i: area[i])
                rc = np.bincount(regions[sl][m] + 1).argmax() - 1
                ch = rchar.get(names[rc] if rc >= 0 else None) or {"wet": "pond", "name": "the margin"}
                a_m2 = a * M_PX * M_PX
                open_w = 2 * float(dist[sl][m].max()) * M_PX
                k = "lake" if a_m2 >= LAKE_M2 else "pond" if open_w >= OPEN_POND_M else ch["wet"]
                reads = {"blackwater-swamp": "as tree swamp", "green-marsh": "as open reed marsh",
                         "pond": "as dry or firm ground"}[ch["wet"]]
                what = (f"open {k}, {open_w:.0f} m across" if k in ("lake", "pond") and k != ch["wet"]
                        else f"water of {ch['name']}, whose research reads {reads}")
                why = (f"closed water ({a_m2 / 1e4:.1f} ha, {long_m:.0f} m of channel line, {width * M_PX:.0f} m wide) "
                       f"that runs nowhere: still {what}")
                for i in keep:
                    parent[find(i)] = find(big)
                byindex.setdefault(big, {"index": big, "id": None, "src_kind": k})
                byindex[big].update(kind=k, why=why, decided=True)
                continue
        # a network: round still patches cut out of channels go back into their channel
        for _ in range(3):
            for i in members:
                if i in painted or kind(i) not in STILL or find(i) != i:
                    continue
                chans = [j for j in adj.get(i, ()) if kind(find(j)) in RUNNING and find(j) not in painted]
                if not chans:
                    continue
                ref = max(wmean[j] for j in chans)
                if area[i] * M_PX * M_PX >= LAKE_M2 and 2 * rmax[i] * M_PX >= 3 * ref:
                    byindex[i].update(kind="lake", decided=True,
                                      why=f"a channel opens into still water {2 * rmax[i] * M_PX:.0f} m across")
                    continue
                parent[i] = find(max(chans, key=lambda j: area[j]))
    lut = np.arange(n + 1)
    for i in idx.tolist():
        lut[i] = find(i)
    return lut[raster].astype(raster.dtype)


def classify(png: bool = False, chunks: bool = False) -> dict:
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
    painted = {}
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
        lab, n = ndi.label(pm, EIGHT)
        for j in range(1, n + 1):
            i = nxt()
            raster[lab == j] = i
            painted[i] = st
    # the body list from the raster
    byindex = {b["index"]: b for b in bodies}
    raster = reshape(raster, byindex, painted, water, regions, names, rchar)
    dist = ndi.distance_transform_edt(water)
    final = np.zeros_like(raster)
    rows = []
    objs = ndi.find_objects(raster)
    for i, sl in enumerate(objs, 1):
        if sl is None:
            continue
        m0 = raster[sl] == i
        lab, n = m0.astype(np.int32), 1          # pieces were split by connected water in reshape()
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
                   "open_m": round(2 * float(dist[sl][m].max()) * M_PX, 1),
                   "set_by": "derived", "decided": bool(src and src.get("decided"))}
            if i in painted:
                st = painted[i]
                row.update(kind=st["water_kind_id"], why=f"owner painted {st['water_kind_id']}", set_by="owner",
                           paint=st)
            rows.append(row)
    raster = final

    # steps 2 and 3: running and still inland water
    for r in rows:
        if r.pop("decided", False) and r["kind"] not in RUNNING:
            continue
        if r["set_by"] == "owner" or r["kind"] in SEA or r["kind"] == "estuary":
            continue
        ch = rchar.get(r["region_id"]) or {"wet": "pond", "name": "the margin", "swampy": False}
        if r["src_kind"] in ("river", "stream"):
            r["kind"] = "river" if r["width_m"] >= RIVER_W_M else "stream"
            r["why"] = f"a channel {r['width_m']:.0f} m wide on average"
        elif r["area_m2"] >= LAKE_M2:
            r["kind"], r["why"] = "lake", f"open still water of {r['area_m2'] / 1e6:.1f} km2"
        elif r["open_m"] >= OPEN_POND_M:
            r["kind"], r["why"] = "pond", f"open still water {r['open_m']:.0f} m across"
        else:
            r["kind"] = ch["wet"]
            r["why"] = (f"still water ({r['area_m2'] / 1e4:.1f} ha) in {ch['name']}, whose research reads "
                        + {"blackwater-swamp": "as tree swamp", "green-marsh": "as open reed marsh",
                           "pond": "as dry or firm ground"}[ch["wet"]])

    # step 4: flow down the channel graph's distance to its outlet
    kind_of = np.array(["land"] + [r["kind"] for r in rows])
    gmap, outlet = outlet_distance(raster, kind_of)
    nxt = descent(gmap, raster > 0)
    vec = flow_vectors(nxt, raster.shape)
    by_k = {r["raster_index"]: r for r in rows}
    for r in rows:
        r["flows"] = r["kind"] in RUNNING
        r.update(flow_deg=None, downstream_id=None, speed="still", flow_note="still water")
    W = raster.shape[1]
    for r in rows:
        if r["kind"] not in RUNNING or r["set_by"] == "owner":
            continue
        k = r["raster_index"]
        p = r["label_py"] * W + r["label_px"]
        if not np.isfinite(gmap.flat[p]):
            r["flow_note"] = "no outlet on the map; direction left for a hand call"
            continue
        dy, dx = vec[0].flat[p], vec[1].flat[p]
        r["flow_deg"] = round((math.degrees(math.atan2(dx, -dy)) + 360) % 360) if (dx or dy) else None
        q, seen = p, 0                     # walk downstream to the next body
        while raster.flat[q] == k and nxt[q] != q and seen < 20000:
            q, seen = nxt[q], seen + 1
        down = raster.flat[q] if raster.flat[q] != k else 0
        if down == 0:                      # the walk ended in this body: its outlet is the water it touches there
            nb = [raster.flat[q + o] for o in (1, -1, W, -W) if 0 <= q + o < raster.size and raster.flat[q + o] not in (0, k)]
            down = nb[0] if nb else 0
        r["downstream_id"] = by_k[down]["id"] if down else None
        ch = rchar.get(r["region_id"]) or {"swampy": False, "rough": False}
        if r["kind"] == "estuary" or r["width_m"] >= SLOW_W_M or ch["swampy"]:
            r["speed"] = "slow"
        elif r["kind"] == "stream" and ch["rough"]:
            r["speed"] = "fast"
        else:
            r["speed"] = "moderate"
        r["flow_note"] = (f"down its channel, {gmap.flat[p] * M_PX / 1000:.1f} km to "
                          + ("the sea", "the still water it feeds", "the map's edge", "its end nearest the sea")[int(outlet.flat[p])])

    # step 5b: per-body overrides, last
    ovp = SRC / "water_overrides.json"
    ov_raw = json.loads(ovp.read_text()) if ovp.exists() else {}
    ov, unmatched = resolve_overrides(ov_raw, rows, raster)
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
    flow_cells(raster, rows, vec, gmap)
    (f.OUT / "water_arrows.json").write_text(json.dumps(arrow_samples(raster, rows, vec, gmap, 14),
                                                        separators=(",", ":")))
    if png:
        picture(raster, rows)
    if chunks:
        chunk_pictures(raster, rows, vec, gmap)
    return {"bodies": len(rows), "kinds": Counter(r["water_kind_id"] for r in rows),
            "flowing": sum(r["flows"] for r in rows), "speeds": Counter(r["speed"] for r in rows),
            "owner": sum(r["set_by"] == "owner" for r in rows),
            "overrides_without_a_body": unmatched}


def resolve_overrides(ov: dict, rows: list, raster: np.ndarray) -> tuple[dict, list]:
    """Owner edits are keyed by a point inside the body (`point`: [px, py], full map pixels), so they survive a
    terrain rebuild that moves outlines and ids; the body id is the fallback. Returns ({current body id: edit},
    the edits that found no body). Later edits on the same body merge over earlier ones."""
    by_k = {r["raster_index"]: r["id"] for r in rows}
    ids = set(by_k.values())
    out, lost = {}, []
    H, W = raster.shape
    for key, o in ov.items():
        bid = None
        if o.get("point"):
            x, y = int(o["point"][0]), int(o["point"][1])
            for rr in (0, 2, 4, 8, 12):
                win = raster[max(0, y - rr):min(H, y + rr + 1), max(0, x - rr):min(W, x + rr + 1)]
                if (win > 0).any():
                    vals, cnt = np.unique(win[win > 0], return_counts=True)
                    bid = by_k.get(int(vals[cnt.argmax()]))
                    break
        if bid is None and key in ids:
            bid = key
        if bid is None:
            lost.append(key)
            continue
        out.setdefault(bid, {}).update({k: v for k, v in o.items() if k != "point"})
    return out, sorted(lost)


def outlet_distance(raster: np.ndarray, kind_of: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Distance along the water from every water pixel to its outlet, and which outlet (0 sea, 1 still water,
    2 map edge). Sea first; water with no way to the sea runs to the map edge if its network reaches it, else into
    the still water it touches. Sea and still water themselves are outlets (distance 0 at their edge)."""
    sea = np.isin(kind_of, SEA)[raster]
    run = np.isin(kind_of, RUNNING)[raster]
    gap = bridged(raster > 0) & (raster == 0)          # map gaps of a few pixels in a channel are crossed
    raster = np.where(gap, raster.max() + 1, raster)
    run = run | gap
    g = sea_distance(raster, sea)
    outlet = np.zeros(raster.shape, np.int8)
    lost = run & ~np.isfinite(g)
    if lost.any():
        comp, _ = ndi.label(raster > 0, EIGHT)          # raster includes the bridged gaps here
        inc = np.isin(comp, np.unique(comp[lost]))
        edge = np.zeros_like(inc)
        edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
        edge_comps = np.unique(comp[edge & inc & run])
        at_edge = np.isin(comp, edge_comps[edge_comps > 0])
        src = (edge & run & at_edge) | ((raster > 0) & ~run & inc & ~at_edge)
        g2 = sea_distance(np.where(inc, raster, 0), src)
        g[lost] = g2[lost]
        outlet[lost & at_edge] = 2
        outlet[lost & ~at_edge] = 1
        rem = lost & ~np.isfinite(g)       # no edge and no still water: it runs out at its end nearest the sea
        if rem.any():
            rc = np.where(np.isin(comp, np.unique(comp[rem])), comp, 0)
            dsea = ndi.distance_transform_edt(~sea) if sea.any() else np.zeros(sea.shape)
            labs = np.unique(rc[rc > 0])
            mins = dict(zip(labs.tolist(), ndi.minimum(dsea, rc, labs).tolist()))
            lut = np.zeros(int(comp.max()) + 1)
            for c, v in mins.items():
                lut[c] = v
            src3 = (rc > 0) & run & (dsea <= lut[rc] + 2)
            g3 = sea_distance(np.where(rc > 0, raster, 0), src3)
            g[rem] = g3[rem]
            outlet[rem] = 3
    g[~run] = np.inf
    return g, outlet


def bridged(water: np.ndarray, px: int = 3) -> np.ndarray:
    """Water with gaps of up to 2 * px pixels (~18 m) closed: a channel the map's drawing broke still joins."""
    return water | ndi.binary_closing(water, EIGHT, iterations=px)


def descent(g: np.ndarray, water: np.ndarray) -> np.ndarray:
    """For each pixel (flat index) the neighbour one step downstream (itself at an outlet or off the network)."""
    H, W = g.shape
    gp = np.pad(np.where(np.isfinite(g), g, np.inf), 1, constant_values=np.inf)
    best = gp[1:-1, 1:-1].copy()
    nxt = np.arange(H * W).reshape(H, W)
    base = nxt.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not (dy or dx):
                continue
            cand = gp[1 + dy:H + 1 + dy, 1 + dx:W + 1 + dx]
            better = cand < best
            best = np.where(better, cand, best)
            nxt = np.where(better, base + dy * W + dx, nxt)
    return nxt.ravel()


def flow_vectors(nxt: np.ndarray, shape, steps_log2: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """Where each pixel's water is 2**steps_log2 steps downstream, as (dy, dx): the flow along the channel."""
    far = nxt.copy()
    for _ in range(steps_log2):
        far = far[far]
    H, W = shape
    i = np.arange(H * W)
    return ((far // W) - (i // W)).reshape(shape).astype(np.float32), ((far % W) - (i % W)).reshape(shape).astype(np.float32)


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


def flow_cells(raster, rows, vec, gmap) -> None:
    """Per Skyrim cell (20 map px), the running water in it and its mean flow along the channels:
    out/newworld/water_flow_cells.json, for the world plugin's per-cell water type (a baked flow direction)."""
    by_k = {r["raster_index"]: r for r in rows}
    run = np.isin(np.array(["land"] + [r["water_kind_id"] if "water_kind_id" in r else r["kind"] for r in rows]),
                  RUNNING)[raster] & np.isfinite(gmap)
    n = int(round(f.SKYRIM_CELL_UNITS / f.UNITS_PER_PX))
    out = []
    H, W = raster.shape
    for y0 in range(0, H, n):
        for x0 in range(0, W, n):
            m = run[y0:y0 + n, x0:x0 + n]
            if m.sum() < 8:
                continue
            dy, dx = vec[0][y0:y0 + n, x0:x0 + n][m], vec[1][y0:y0 + n, x0:x0 + n][m]
            ln = np.hypot(dx, dy) + 1e-6
            ux, uy = float((dx / ln).mean()), float((dy / ln).mean())
            k = int(np.bincount(raster[y0:y0 + n, x0:x0 + n][m]).argmax())
            wx, wy = f.px_to_world(x0 + n / 2, y0 + n / 2)
            out.append({"cell": [int(wx // f.SKYRIM_CELL_UNITS), int(wy // f.SKYRIM_CELL_UNITS)], "body_id": by_k[k]["id"],
                        "share": round(float(m.mean()), 2),
                        "flow_deg": round((math.degrees(math.atan2(ux, -uy)) + 360) % 360) if abs(ux) + abs(uy) > .2 else None})
    (f.OUT / "water_flow_cells.json").write_text(json.dumps(out))


def arrow_samples(raster, rows, vec, gmap, step: int = 22) -> list:
    """Flow arrows along every running channel's centreline, one per step x step px: [x, y, bearing, body index]."""
    from skimage.morphology import skeletonize
    run = np.isin(np.array(["land"] + [r.get("water_kind_id", r.get("kind")) for r in rows]), RUNNING)[raster]
    skel = skeletonize(run & np.isfinite(gmap))
    ys, xs = np.nonzero(skel)
    _, first = np.unique((ys // step) * 100000 + xs // step, return_index=True)
    out = []
    for y, x in zip(ys[first].tolist(), xs[first].tolist()):
        dy, dx = float(vec[0][y, x]), float(vec[1][y, x])
        if math.hypot(dx, dy) >= 1:
            out.append([x, y, round((math.degrees(math.atan2(dx, -dy)) + 360) % 360), int(raster[y, x])])
    return out


def chunk_pictures(raster, rows, vec, gmap, grid: int = 4) -> None:
    """The visual check: a grid x grid split of the map, each chunk the source map beside the classification laid
    over it with flow arrows along every channel's centreline: out/newworld/water_chunks/r<row>c<col>.png."""
    from PIL import ImageDraw
    Image.MAX_IMAGE_PIXELS = None
    src = Image.open(f.BASE_MAP).convert("RGB")
    lut = np.zeros((len(rows) + 1, 3), np.uint8)
    for r in rows:
        lut[r["raster_index"]] = COLOURS.get(r.get("water_kind_id", r.get("kind")), (255, 0, 255))
    over = np.asarray(src).copy()
    wm = raster > 0
    over[wm] = (0.25 * over[wm] + 0.75 * lut[raster][wm]).astype(np.uint8)
    img = Image.fromarray(over)
    d = ImageDraw.Draw(img)
    for x, y, deg, _k in arrow_samples(raster, rows, vec, gmap):
        ux, uy = math.sin(math.radians(deg)), -math.cos(math.radians(deg))
        ex, ey = x + 6 * ux, y + 6 * uy
        d.line((x - 7 * ux, y - 7 * uy, ex, ey), fill=(230, 20, 20), width=2)
        d.polygon([(ex + 5 * ux, ey + 5 * uy), (ex - 2 * ux - 4 * uy, ey - 2 * uy + 4 * ux),
                   (ex - 2 * ux + 4 * uy, ey - 2 * uy - 4 * ux)], fill=(230, 20, 20))
    out = f.OUT / "water_chunks"
    out.mkdir(exist_ok=True)
    H, W = raster.shape
    for i in range(grid):
        for j in range(grid):
            box = (j * W // grid, i * H // grid, (j + 1) * W // grid, (i + 1) * H // grid)
            a, b = src.crop(box), img.crop(box)
            pair = Image.new("RGB", (a.width * 2 + 6, a.height), (255, 255, 255))
            pair.paste(a, (0, 0))
            pair.paste(b, (a.width + 6, 0))
            pair.save(out / f"r{i}c{j}.png")


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
    print(json.dumps(classify(png="--png" in sys.argv, chunks="--chunks" in sys.argv), indent=1, default=dict))
