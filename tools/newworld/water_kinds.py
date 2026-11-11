"""Water kinds and flow (nw-02 step 5): every water body of the current terrain build classified by its shape, its
place and its region's ecology, never by its level (all water is at 0), then the owner's edits applied last.

Rerunnable on whatever `out/newworld/water_bodies.json` + `out/newworld/terrain/water_bodies.png` the terrain build
last wrote; of each terrain body it reads the map's own kind (`map_kind`), never the owner's kind the terrain laid
over it for the bed. Writes `out/newworld/water_classified.json` (one row per body) and `out/newworld/water_classified.png`
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
3c. The owner's kinds are applied (found by their points), then: a fringe (under 2 ha of stream or river whose
   only water neighbours are marsh or swamp) takes the kind of the marsh or swamp it hangs on; round Helstrom
   (Murkwood) only the main river courses stay river, the narrower arms green marsh; and a stream or river with no
   continuous water surface to the sea is still water. Frame water is sea only where it joins the sea.
4. Flow, along the channel graph. Every running pixel has its distance to its outlet along the water (Dijkstra, the
   sea first; still water is passed through for that distance, so a river leaving a lake runs on toward the sea).
   Water then runs pixel by pixel to the neighbour nearer the outlet, so it follows the channel's centreline, joins
   tributaries into the channel they meet and never reverses mid-channel; it stops where it enters still water
   (still bodies have no flow) and starts again where a channel leaves it. Only an owner-set channel can lack a way
   to the sea (the map's edge is never an outlet): it runs into the still water it touches, else out at its end
   nearest the sea. A
   body's bearing is its flow 32 px downstream of its label point; its downstream body is the first other body that
   walk reaches. Per Skyrim cell the mean flow goes to `out/newworld/water_flow_cells.json` for the plugin's per-cell
   type. The atlas's arrows walk each channel's centreline downstream, so they curve with it. Speed: `still`; `slow` for estuaries, rivers 150 m wide or more, and any running water in a region of
   wetness 0.8 or more; `fast` for streams in rough country (region roughness 4 m or more, or summit 50 m or more);
   else `moderate`.
5. The owner's edits: `newworld/sources/water_paint.json` (strokes that paint a kind and flow over an area,
   splitting the bodies they cross; later strokes win) and `newworld/sources/water_overrides.json` (water_kind_id,
   flows, flow_toward_deg, speed, name; found by `point`, a map pixel inside the body; the body id is the
   fallback). An edit that sets a kind holds the water of the body it was made on (tools/newworld/water_held.py):
   that water is cut out first, as its own body with the owner's kind, before anything else is decided, so the
   edit keeps its water however the rest is cut. Both files are written by tools/newworld/water_overrides_pull.py
   from the atlas's water editor.
6. The checks (`checks`, out/newworld/water_check.json; the run exits 1 when one fails): each kind's bodies and
   area inside the picture against the accepted classification (`newworld/sources/water_accepted.json`), and every
   owner edit on a body of the area recorded with it, with the owner's kind.

    python3 -m tools.newworld.water_kinds            # classify; prints counts
    python3 -m tools.newworld.water_kinds --accept   # and take this classification as the accepted one, after a
                                                     # look, when the kinds were meant to change
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
from tools.newworld import water_held as wh

DB = f.ROOT / "story" / "data" / "db"
SRC = f.ROOT / "sources"
M_PX = f.UNITS_PER_PX / f.UNITS_PER_METRE          # 2.93 m
EIGHT = np.ones((3, 3), bool)
SEA = ("ocean", "shallow-coast", "bay")
RUNNING = ("estuary", "river", "stream")
COAST_M, ENCLOSE_M, ENCLOSED_LAND = 450, 3000, 0.45
RIVER_W_M, SLOW_W_M, LAKE_M2, OPEN_POND_M = 40, 150, 500_000, 120
FRAME_BAND = 2 * f.FRAME_PX + 4               # the ruler band, its rule and the sea margin beyond, in map px
CHANNEL_MIN_M, CHANNEL_ELONG = 100, 8         # a channel: centreline 100 m or more and 8 widths long, or branching
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


def map_kinds(bj: list, raster: np.ndarray) -> dict:
    """raster index -> (kind, why) as the map draws each of the terrain's bodies, before any owner edit. The terrain
    build lays the owner's edits over its own body list (their kinds set the beds) and keeps the map's reading
    beside them (`map_kind`, `map_why`). The shape rules here read the map's reading only: an owner's kind fed back
    in as if drawn would reshape the bodies under the owner's own points (a bit of channel the owner calls a lake
    reads as a still patch and is merged into its river, and the lake edit then lands on the whole river). A body
    list written without the map's reading is read again from the body raster by the terrain's own labelling: each
    body takes the kind that labelling gives its label point (nearly every body must label again as itself)."""
    if all(s.get("map_kind") for s in bj):
        return {s["raster_index"]: (s["map_kind"], s["map_why"]) for s in bj}
    if not any(s.get("overridden") for s in bj):
        return {s["raster_index"]: (s["water_kind_id"], s["why"]) for s in bj}
    from tools.newworld import terrain_relief as tr
    from tools.newworld import terrain_water as tw
    from tools.newworld.terrain import region_px
    regs = jsonl("region")
    names = [r["id"] for r in regs]
    word = {r["id"]: (tr.landform_word(r.get("landform")) or tr.landform_word(r.get("name"))
                      or tr.NAME_GUESS.get(r["id"])) for r in regs}
    cell_region = json.loads((f.OUT / "cell_region.json").read_text())
    again, bodies = tw.label_bodies(raster > 0, region_px(cell_region, names, raster.shape), names,
                                    {r["id"]: r["kind"] for r in regs}, word, M_PX)
    by = {b["raster_index"]: b for b in bodies}
    out, same = {}, 0
    for s in bj:
        b = by[int(again[s["label_py"], s["label_px"]])]
        same += b["id"] == s["id"] and b["area_m2"] == s["area_m2"]
        out[s["raster_index"]] = (b["water_kind_id"], b["why"])
    if same < 0.99 * len(bj):
        raise ValueError(f"only {same} of {len(bj)} water bodies label again as the terrain build labelled them: "
                         "rebuild the terrain so its body list carries the map's reading")
    return out


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
    round still patch is merged back into the channel it lies in, unless it truly opens into still water (120 m
    or more across and three times wider than the channels at it: a pond, or a lake from 0.5 km2). Returns the raster with merged bodies."""
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
            network = channel_shaped(m) or (length / max(width, 1.0) >= 10
                                            and (long_m >= 3000 or ((c in edge or has_lake) and long_m >= 600)))
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
                if 2 * rmax[i] * M_PX >= max(OPEN_POND_M, 3 * ref):
                    k = "lake" if area[i] * M_PX * M_PX >= LAKE_M2 else "pond"
                    byindex[i].update(kind=k, decided=True,
                                      why=f"a channel opens into still water {2 * rmax[i] * M_PX:.0f} m across")
                    continue
                parent[i] = find(max(chans, key=lambda j: area[j]))
    lut = np.arange(n + 1)
    for i in idx.tolist():
        lut[i] = find(i)
    return lut[raster].astype(raster.dtype)


def channel_shaped(m: np.ndarray) -> bool:
    """A body drawn as a channel: its centreline long against its width (a ribbon), or branching (dendritic).
    Only a compact closed blob is still water; a channel runs whether or not the map joins it to the network."""
    from skimage.morphology import skeletonize
    if m.sum() < 30:
        return False
    sk = skeletonize(m)
    # spurs: an irregular blob's skeleton sprouts a twig to every bump of its shore; strip end pixels as many
    # times as the body is wide, so only the trunk and real branches (longer than the width) count
    k8 = EIGHT.astype(np.int8)
    for _ in range(min(60, int(2 * ndi.distance_transform_edt(m).max()))):
        ends = sk & ((ndi.convolve(sk.astype(np.int8), k8, mode="constant") - 1) <= 1)
        if not ends.any():
            break
        sk &= ~ends
    length = float(sk.sum())
    width = float(m.sum()) / max(length, 1.0)
    if length * M_PX < CHANNEL_MIN_M:
        return False
    elong = length / max(width, 1.0)
    if elong >= CHANNEL_ELONG:
        return True
    nb = ndi.convolve(sk.astype(np.int8), k8, mode="constant") - 1
    forks = int(((nb >= 3) & sk).sum())
    return forks >= 4 and elong >= CHANNEL_ELONG / 2


def carve(raster, rows, r, part, kind, why, dist) -> dict | None:
    """Split the pixels `part` (a full-size mask inside body r) off as a new body of `kind`; r keeps the rest."""
    i = r["raster_index"]
    part = part & (raster == i)
    rest = (raster == i) & ~part
    if part.sum() < 20 or rest.sum() < 20:
        if part.sum() >= 20 and not rest.any():
            r["kind"], r["why"] = kind, why
        return None
    k = len(rows) + 1
    raster[part] = k
    out = []
    for m_full, row in ((part, None), (rest, r)):
        sl = ndi.find_objects(m_full.astype(np.int8))[0]
        m = m_full[sl]
        bid, px, py = body_id(m, dist, sl)
        vals = {"area_m2": round(float(m.sum()) * M_PX * M_PX, 1), "label_px": px, "label_py": py,
                "width_m": round(4 * float(dist[sl][m].mean()) * M_PX, 1),
                "open_m": round(2 * float(dist[sl][m].max()) * M_PX, 1)}
        if row is None:
            row = dict(r, id=bid, raster_index=k, kind=kind, why=why, **{x: v for x, v in vals.items()})
            out.append(row)
        else:
            row.update(vals, id=bid)
    rows.append(out[0])
    return out[0]


def pools_and_mouths(raster, rows, dist) -> None:
    """Step 3b, by local width rather than whole-body shape.
    - A pool in a channel: where the open water is three times or more wider than the channel's own width (the
      median width along its centreline) and 120 m or more across, that part is still water (pond, or lake from
      0.5 km2); the channel runs into it and out again.
    - Water joined to the sea that is wider than a channel and not channel-shaped (a lagoon, a coastal shelf) is
      sea: shallow coast. A lake has no sea connection, or meets it only through a river.
    - Water lying mostly on the map's frame (the ruler band) is sea, never a river mouth.
    - An estuary is a river's mouth: it is kept only where a river meets it, and only within three river widths
      (at most 400 m) of that meeting; the rest of the coastal fringe is still shallow coast."""
    from skimage.morphology import skeletonize
    objs = ndi.find_objects(raster)
    for r in list(rows):
        if r["set_by"] == "owner" or r["kind"] not in ("river", "stream"):
            continue
        sl = objs[r["raster_index"] - 1]
        m = raster[sl] == r["raster_index"]
        d = dist[sl] * m
        sk = skeletonize(m)
        if sk.sum() < 10:
            continue
        ref = float(np.median(d[sk]))
        core = (d >= 1.5 * ref) & (2 * d * M_PX >= max(OPEN_POND_M, 3 * 2 * ref * M_PX))
        if not core.any():
            continue
        lab, n = ndi.label(core, EIGHT)
        dd, (iy, ix) = ndi.distance_transform_edt(~core, return_indices=True)
        pool = m & (dd <= d[iy, ix])
        plab, pn = ndi.label(pool, EIGHT)
        for j in range(1, pn + 1):
            pm = plab == j
            area = pm.sum() * M_PX * M_PX
            if area < 2 * (2 * ref * M_PX) ** 2 * 9:      # several channel widths each way
                continue
            full = np.zeros(raster.shape, bool)
            full[sl] = pm
            k = "lake" if area >= LAKE_M2 else "pond"
            carve(raster, rows, r, full, k,
                  f"a pool in a channel, {2 * float(d[pm].max()) * M_PX:.0f} m across against a "
                  f"{2 * ref * M_PX:.0f} m channel: still water, the channel runs into it and out", dist)
    adj = adjacency(raster)
    by_i = {r["raster_index"]: r for r in rows}
    for r in rows:                     # a whole body that is a pool: twice as open as every channel at it
        if r["set_by"] == "owner" or r["kind"] not in ("river", "stream") or r["area_m2"] < 30_000:
            continue
        nb = [by_i[j] for j in adj.get(r["raster_index"], ())]
        if nb and not any(x["kind"] in SEA + ("estuary", "lake", "pond") for x in nb) and \
                r["open_m"] >= max(OPEN_POND_M, 2 * max(x["width_m"] for x in nb)):
            r["kind"] = "lake" if r["area_m2"] >= LAKE_M2 else "pond"
            r["why"] = (f"open water {r['open_m']:.0f} m across, twice as wide as every channel at it "
                        f"(widest {max(x['width_m'] for x in nb):.0f} m): still, the channels run into it and out")
    fb = np.zeros(raster.shape, bool)
    fb[:FRAME_BAND, :] = fb[-FRAME_BAND:, :] = fb[:, :FRAME_BAND] = fb[:, -FRAME_BAND:] = True
    idx = np.arange(1, len(rows) + 1)
    in_band = ndi.mean(fb, raster, idx)
    for r, v in zip(rows, in_band):          # a channel the frame merely cuts is not sea: only frame water joined to it
        if v >= 0.5 and r["set_by"] != "owner" and r["kind"] not in SEA and \
                any(by_i[j]["kind"] in SEA for j in adj.get(r["raster_index"], ())):
            r["kind"], r["why"] = "shallow-coast", "water lying mostly on the map's frame: sea, never a river mouth"
    for r in rows:
        if r["set_by"] != "owner" and r["kind"] in ("lake", "pond") and \
                any(by_i[j]["kind"] in SEA + ("estuary",) for j in adj.get(r["raster_index"], ())):
            r["kind"] = "bay" if r["area_m2"] >= LAKE_M2 else "shallow-coast"
            r["why"] = "open water joined to the sea or a river mouth, wider than a channel: sea"
    river = np.isin(np.array(["land"] + [r["kind"] for r in rows]), ("river",))[raster]
    for r in list(rows):
        if r["set_by"] == "owner" or r["kind"] != "estuary":
            continue
        i = r["raster_index"]
        m = raster == i
        touch = river & ndi.binary_dilation(m, EIGHT, iterations=2)
        if not touch.any():
            r["kind"], r["why"] = "shallow-coast", "a coastal fringe with no river entering it: still sea"
            continue
        w = float(np.median(2 * dist[touch])) * M_PX
        reach = min(400.0, 3 * w) / M_PX
        far = m & (ndi.distance_transform_edt(~touch) > reach)
        carve(raster, rows, r, far, "shallow-coast",
              "the coastal water beyond a river's mouth: still sea", dist)


WET = ("green-marsh", "blackwater-swamp")
FRINGE_M2 = 20_000                 # a fringe network is under 2 ha (measured: the largest on the 2026-11-09 map is 1.5 ha)
HELSTROM_REGIONS = ("murkwood",)   # the Hist forest round Helstrom (region table)
TRIB_SHARE = 0.12                  # Helstrom's streams: the largest 12% of tributary systems stay stream
MAIN_W_M, MAIN_LEN_M = 50, 1500    # Helstrom's main courses: 50 m wide or more along 1.5 km of centreline


def running_networks(rows, adj, ok) -> list:
    """Connected sets of bodies (raster indices) for which ok(row) holds, joined by touching each other."""
    by_i = {r["raster_index"]: r for r in rows}
    todo = {i for i, r in by_i.items() if ok(r)}
    out = []
    while todo:
        st, comp = [todo.pop()], []
        while st:
            k = st.pop()
            comp.append(k)
            for j in adj.get(k, ()):
                if j in todo:
                    todo.discard(j)
                    st.append(j)
        out.append(comp)
    return out


def absorb_fringes(raster, rows) -> int:
    """Step 3c-i. A fringe is a little running network (under 2 ha, joined bodies of stream or river) whose only
    water neighbours are marsh or swamp: the fiddly bits on a swamp's edge. It takes the kind of the largest marsh
    or swamp it touches. A running network that also meets the sea, a lake, a pond or other running water is a real
    channel and stays. Returns how many bodies changed."""
    adj = adjacency(raster)
    by_i = {r["raster_index"]: r for r in rows}
    n = 0
    for comp in running_networks(rows, adj, lambda r: r["kind"] in ("river", "stream") and r["set_by"] != "owner"):
        cs = set(comp)
        nb = {j for k in comp for j in adj.get(k, ()) if j not in cs}
        area = sum(by_i[k]["area_m2"] for k in comp)
        if not nb or area > FRINGE_M2 or any(by_i[j]["kind"] not in WET for j in nb):
            continue
        host = max((by_i[j] for j in nb), key=lambda x: x["area_m2"])
        for k in comp:
            by_i[k]["kind"] = host["kind"]
            by_i[k]["why"] = (f"a fringe of {area / 1e4:.1f} ha of little channels on the edge of {host['id']}, "
                              f"which is its only water: part of that {host['kind']}")
            n += 1
    return n


def helstrom_rivers(raster, rows, regions, names) -> dict:
    """Step 3c-ii, the owner's ruling for the water round Helstrom (Murkwood): only its main river courses stay
    river, the rest of its river water is green marsh, so the region reads as main courses, the streams that feed
    them, and squiggly marsh. Width is measured along each river's centreline (twice the distance to the bank,
    smoothed over ~60 m, a braided reach measured whole with its islands) and given to every pixel from its nearest centreline point; a main course is river 50 m wide
    or more along at least 1.5 km of centreline, and a narrower reach up to 1 km that joins two main
    courses. Then the streams: of the region's tributary systems (connected stream water) the largest 12% by area stay
    stream and the rest become green marsh. A body the owner has set keeps the owner's kind whole."""
    from skimage.morphology import skeletonize
    codes = [names.index(x) for x in HELSTROM_REGIONS if x in names]
    kind_of = np.array(["land"] + [r["kind"] for r in rows])
    riv = (kind_of[raster] == "river") & np.isin(regions, codes)
    if not riv.any():
        return {"river_m2_kept": 0, "river_m2_to_marsh": 0}
    dist = ndi.distance_transform_edt(raster > 0)
    whole = riv | (ndi.binary_closing(riv, EIGHT, iterations=8) & np.isin(regions, codes))   # a braided reach as one
    wd = ndi.distance_transform_edt(whole)
    sk = skeletonize(whole)
    w = np.where(sk, 2 * wd * M_PX, 0.0)
    num, den = ndi.uniform_filter(w, 21), ndi.uniform_filter(sk.astype(float), 21)
    ws = np.where(sk, num / np.maximum(den, 1e-9), 0)
    _, (iy, ix) = ndi.distance_transform_edt(~sk, return_indices=True)
    width = ws[iy, ix]
    main = whole & (width >= MAIN_W_M)
    lab, n = ndi.label(main, EIGHT)
    if n:
        length = ndi.sum(sk & main, lab, np.arange(1, n + 1)) * M_PX
        main &= np.concatenate([[False], length >= MAIN_LEN_M])[lab]
    main &= riv
    # a short narrower reach (up to 1 km of centreline) that joins two main courses (or a main course and river beyond the region) is kept, so the main
    # courses stay one connected system
    lab, n = ndi.label(riv & ~main, EIGHT)
    if n:
        other, _ = ndi.label(main | ((kind_of[raster] == "river") & ~np.isin(regions, codes)), EIGHT)
        for j, sl in enumerate(ndi.find_objects(lab), 1):
            sl2 = tuple(slice(max(0, a.start - 3), a.stop + 3) for a in sl)
            pm = lab[sl2] == j
            touch = np.unique(other[sl2][ndi.binary_dilation(pm, EIGHT, iterations=2)])
            if (touch > 0).sum() >= 2 and float((sk[sl2] & pm).sum()) * M_PX <= 1000:
                main[sl2] |= pm
    narrow = riv & ~main
    kept, moved = float(main.sum()) * M_PX ** 2, float(narrow.sum()) * M_PX ** 2
    by_i = {r["raster_index"]: r for r in rows}
    lab, n = ndi.label(narrow, EIGHT)
    for j, sl in enumerate(ndi.find_objects(lab), 1):
        part = np.zeros(raster.shape, bool)
        part[sl] = lab[sl] == j
        owners = np.unique(raster[part])
        for i in owners.tolist():
            r = by_i.get(i)
            if r is None or r["set_by"] == "owner":   # the owner's kind on a body is final, here as everywhere
                continue
            why = (f"round Helstrom only the main river courses ({MAIN_W_M} m wide or more) stay river: "
                   "a narrower arm, green marsh")
            new = carve(raster, rows, r, part & (raster == i), "green-marsh", why, dist)
            if new is not None:
                new["set_by"] = "derived"
                new.pop("name", None)
                by_i[new["raster_index"]] = new
            elif r["kind"] == "green-marsh":
                r["set_by"] = "derived"
    # the streams: a few principal tributaries stay, the rest is marsh. A tributary is one connected stream system
    # in the region (bodies joined by touching); it is ranked by its area (width x length); the top share by count
    # stays stream, at least one per river system it feeds.
    kind_of = np.array(["land"] + [r["kind"] for r in rows])
    own = np.array([False] + [r["set_by"] == "owner" for r in rows])
    st = (kind_of[raster] == "stream") & np.isin(regions, codes) & ~own[raster]
    lab, n = ndi.label(st, EIGHT)
    s_kept = s_moved = 0
    if n:
        area = ndi.sum(st, lab, np.arange(1, n + 1))
        keep_n = max(1, int(round(TRIB_SHARE * n)))
        keep = set((np.argsort(-area)[:keep_n] + 1).tolist())
        for j, sl in enumerate(ndi.find_objects(lab), 1):
            part = np.zeros(raster.shape, bool)
            part[sl] = lab[sl] == j
            if j in keep:
                s_kept += 1
                continue
            s_moved += 1
            for i in np.unique(raster[part]).tolist():
                r = by_i.get(i)
                if r is None or r["set_by"] == "owner":
                    continue
                new = carve(raster, rows, r, part & (raster == i), "green-marsh",
                            "round Helstrom only a few principal tributaries stay stream: a lesser one, green marsh", dist)
                if new is not None:
                    new["set_by"] = "derived"
                    new.pop("name", None)
                    by_i[new["raster_index"]] = new
    return {"river_m2_kept": round(kept), "river_m2_to_marsh": round(moved), "tributaries": n,
            "tributaries_kept": s_kept, "tributaries_to_marsh": s_moved}


def no_sea_still(raster, rows, rchar) -> int:
    """Step 3c-iii. A stream or river must be joined to the sea by one continuous water surface (still water on the
    way counts; map gaps of ~18 m are bridged). A running body that is not, and that the owner did not set, is
    still water: a lake from 0.5 km2, a pond where it opens 120 m across, else its region's wet character."""
    kind_of = np.array(["land"] + [r["kind"] for r in rows])
    comp, _ = ndi.label(bridged(raster > 0), EIGHT)
    comp[raster == 0] = 0
    sea_comps = np.unique(comp[np.isin(kind_of[raster], SEA)])
    idx = np.arange(1, len(rows) + 1)
    joined = ndi.maximum(np.isin(comp, sea_comps[sea_comps > 0]), raster, idx)
    n = 0
    for r, ok in zip(rows, joined):
        if r["kind"] not in RUNNING or r["set_by"] == "owner" or ok:
            continue
        ch = rchar.get(r["region_id"]) or {"wet": "pond", "name": "the margin"}
        if r["area_m2"] >= LAKE_M2:
            r["kind"] = "lake"
        elif r["open_m"] >= OPEN_POND_M:
            r["kind"] = "pond"
        else:
            r["kind"] = ch["wet"]
        r["why"] = f"a channel with no water surface joining it to the sea, so still: {r['kind']}"
        n += 1
    return n


def braid_smooth(raster, rows, vec, sigma: float = 40.0):
    """In a braided reach (a running body that splits round islands) every braid flows the reach's way: the flow
    is averaged over the reach, so no braid runs back against its neighbours."""
    objs = ndi.find_objects(raster)
    for r in rows:
        if r["kind"] not in RUNNING:
            continue
        sl = objs[r["raster_index"] - 1]
        if sl is None:
            continue
        m = raster[sl] == r["raster_index"]
        holes = ndi.binary_fill_holes(m) & ~m
        if ndi.label(holes)[1] < 2:
            continue
        wsum = ndi.gaussian_filter(m.astype(np.float32), sigma) + 1e-6
        for c in (0, 1):
            v = vec[c][sl]
            n = np.hypot(vec[0][sl], vec[1][sl]) + 1e-6
            sm = ndi.gaussian_filter(np.where(m, v / n, 0).astype(np.float32), sigma) / wsum
            v[m] = (sm * 32)[m]


def classify(png: bool = False, chunks: bool = False, accept: bool = False) -> dict:
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
    drawn = map_kinds(bj, raster)
    bodies = []
    for s in bj:
        i = s["raster_index"]
        sl = objs[i - 1]
        if sl is None:
            continue
        m = raster[sl] == i
        reg_codes = regions[sl][m]
        rc = np.bincount(reg_codes + 1).argmax() - 1
        kind, why = drawn[i]
        bodies.append({"index": i, "id": s["id"], "sl": sl, "src_kind": kind, "kind": kind,
                       "src_why": why, "why": why, "area_m2": s["area_m2"], "px": s["label_px"],
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
    # step 5a, held: the water each of the owner's kind edits was made on is cut out whole (water_held), so the
    # edit holds over that water however the rest is cut round it; a painted stroke over it still wins
    ovp = SRC / "water_overrides.json"
    ov_raw = json.loads(ovp.read_text()) if ovp.exists() else {}
    held, held_kind = wh.load(raster.shape), wh.kinds(ov_raw)
    taken = np.isin(raster, list(painted))
    for k, sl in enumerate(ndi.find_objects(held), 1):
        if sl is None or k not in held_kind:
            continue
        m = (held[sl] == k) & water[sl] & ~taken[sl]
        if m.any():
            i = nxt()
            raster[sl][m] = i
            painted[i] = {"water_kind_id": held_kind[k], "held": k}
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
            if i in painted and painted[i].get("held"):
                row.update(kind=painted[i]["water_kind_id"], why="owner set the kind", set_by="owner")
            elif i in painted:
                st = painted[i]
                row.update(kind=st["water_kind_id"], why=f"owner painted {st['water_kind_id']}", set_by="owner",
                           paint=st)
            rows.append(row)
    raster = final

    # steps 2 and 3: running and still inland water
    objs_final = ndi.find_objects(raster)
    for r in rows:
        if r.pop("decided", False) and r["kind"] not in RUNNING:
            continue
        if r["set_by"] == "owner" or r["kind"] in SEA or r["kind"] == "estuary":
            continue
        ch = rchar.get(r["region_id"]) or {"wet": "pond", "name": "the margin", "swampy": False}
        sl = objs_final[r["raster_index"] - 1]
        shaped = channel_shaped(raster[sl] == r["raster_index"])
        if r["src_kind"] in ("river", "stream") and not shaped and r["open_m"] >= OPEN_POND_M:
            r["kind"] = "lake" if r["area_m2"] >= LAKE_M2 else "pond"
            r["why"] = f"drawn in a channel network but open and compact, {r['open_m']:.0f} m across: still water"
        elif r["src_kind"] in ("river", "stream") or shaped:
            r["kind"] = "river" if r["width_m"] >= RIVER_W_M else "stream"
            r["why"] = (f"a channel {r['width_m']:.0f} m wide on average"
                        + ("; channel-shaped (long or branching), so running whether or not the map joins it"
                           if shaped and r["src_kind"] not in ("river", "stream") else ""))
        elif r["area_m2"] >= LAKE_M2:
            r["kind"], r["why"] = "lake", f"open still water of {r['area_m2'] / 1e6:.1f} km2"
        elif r["open_m"] >= OPEN_POND_M:
            r["kind"], r["why"] = "pond", f"open still water {r['open_m']:.0f} m across"
        else:
            r["kind"] = ch["wet"]
            r["why"] = (f"still water ({r['area_m2'] / 1e4:.1f} ha) in {ch['name']}, whose research reads "
                        + {"blackwater-swamp": "as tree swamp", "green-marsh": "as open reed marsh",
                           "pond": "as dry or firm ground"}[ch["wet"]])

    # step 3b: pools in channels, lagoons, the frame and river mouths
    pools_and_mouths(raster, rows, ndi.distance_transform_edt(raster > 0))

    # step 3c: the owner's kinds first, then fringes, Helstrom's rivers and the sea test (see their docstrings)
    ov, _ = resolve_overrides(ov_raw, rows, raster)
    for r in rows:
        o = ov.get(r["id"])
        if o and o.get("water_kind_id"):
            r["kind"], r["why"], r["set_by"] = o["water_kind_id"], "owner set the kind", "owner"
    stats = {"fringe_bits": absorb_fringes(raster, rows)}
    stats["helstrom"] = helstrom_rivers(raster, rows, regions, names)
    stats["still_for_no_sea"] = no_sea_still(raster, rows, rchar)
    ov, _ = resolve_overrides(ov_raw, rows, raster)

    # step 4: flow down the channel graph's distance to its outlet
    kind_of = np.array(["land"] + [r["kind"] for r in rows])
    gmap, outlet = outlet_distance(raster, kind_of)
    flowing = np.isin(kind_of, RUNNING)[raster]
    stats["flow_px_to_sea"] = f"{int((flowing & (outlet == 0) & np.isfinite(gmap)).sum())}/{int(flowing.sum())}"
    nxt = descent(gmap, raster > 0)
    vec = flow_vectors(nxt, raster.shape)
    braid_smooth(raster, rows, vec)
    by_k = {r["raster_index"]: r for r in rows}
    for r in rows:
        r["flows"] = r["kind"] in RUNNING
        r.update(flow_deg=None, downstream_id=None, speed="still", flow_note="still water")
    W = raster.shape[1]
    for r in rows:
        if r["kind"] not in RUNNING or (r["id"] in ov and ov[r["id"]].get("flow_toward_deg") is not None):
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

    # step 5b: per-body overrides, last (ids found again by the owner's points: carving may rename a body)
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
    seen: set = set()
    for r in rows:                     # ids are unique: a carved body whose label point repeats takes a suffix
        base, n = r["id"], 1
        while r["id"] in seen:
            n += 1
            r["id"] = f"{base}-{n}"
        seen.add(r["id"])
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
    stats["check"] = checks(raster, rows, ov_raw, accept)
    (f.OUT / "water_check.json").write_text(json.dumps(stats["check"], indent=1))
    return {"bodies": len(rows), "kinds": Counter(r["water_kind_id"] for r in rows),
            "flowing": sum(r["flows"] for r in rows), "speeds": Counter(r["speed"] for r in rows),
            "owner": sum(r["set_by"] == "owner" for r in rows),
            "overrides_without_a_body": unmatched, **stats}


ACCEPTED = SRC / "water_accepted.json"
KIND_TOL, KIND_FLOOR_M2, KIND_FLOOR_N = 0.02, 20_000, 3    # a kind may move 2% (or 2 ha, or 3 bodies) from the accepted
WATERLINE_TOL = 0.001                                      # the water pixels inside the picture: the same waterline


def measure(raster: np.ndarray, rows: list) -> dict:
    """What the accepted record keeps of a classification: inside the picture (the map less its frame band, where
    the water is the map's own and not the carried-on edge) the water pixels and, per kind, the bodies whose label
    point lies there and the area."""
    inner = np.zeros(raster.shape, bool)
    inner[FRAME_BAND:-FRAME_BAND, FRAME_BAND:-FRAME_BAND] = True
    names = sorted(COLOURS)
    code = np.array([0] + [names.index(r["water_kind_id"]) + 1 for r in rows])
    px = np.bincount(code[raster][inner], minlength=len(names) + 1)
    n = Counter(r["water_kind_id"] for r in rows if inner[r["label_py"], r["label_px"]])
    return {"water_px": int(px[1:].sum()),
            "kinds": {k: {"bodies": n.get(k, 0), "area_m2": round(float(px[j + 1]) * M_PX * M_PX)}
                      for j, k in enumerate(names)}}


def checks(raster: np.ndarray, rows: list, ov_raw: dict, accept: bool = False) -> dict:
    """The two checks a rebuild must pass (the result is also out/newworld/water_check.json, which verify reads).
    - kinds: each kind's bodies and area inside the picture against the accepted classification
      (newworld/sources/water_accepted.json), failing past KIND_TOL unless the waterline itself moved (then the
      comparison means nothing and the new classification is looked at and accepted afresh, `--accept`).
    - edits: every owner edit on the body its point finds, that body's area against the area recorded when the edit
      was made and its kind against the edit's (water_held.check)."""
    now = measure(raster, rows)
    tb = f.OUT / "terrain" / "build.json"
    now["terrain_build"] = json.loads(tb.read_text())["id"] if tb.exists() else None
    if accept or not ACCEPTED.exists():
        ACCEPTED.write_text(json.dumps(now, indent=1) + "\n")
    was = json.loads(ACCEPTED.read_text())
    moved = abs(now["water_px"] - was["water_px"]) > WATERLINE_TOL * was["water_px"]
    off = []
    for k, a in was["kinds"].items():
        b = now["kinds"].get(k, {"bodies": 0, "area_m2": 0})
        if abs(b["area_m2"] - a["area_m2"]) > max(KIND_TOL * a["area_m2"], KIND_FLOOR_M2) or \
                abs(b["bodies"] - a["bodies"]) > max(KIND_TOL * a["bodies"], KIND_FLOOR_N):
            off.append({"kind": k, "bodies": b["bodies"], "accepted_bodies": a["bodies"],
                        "area_m2": b["area_m2"], "accepted_area_m2": a["area_m2"]})
    edits = wh.check(ov_raw, raster, rows)
    return {"accepted_build": was.get("terrain_build"), "terrain_build": now["terrain_build"],
            "waterline_moved": bool(moved), "kinds_off": off, "edits": edits,
            "ok": bool((moved or not off) and not edits["off"] and not edits["lost"] and not edits["no_record"])}


def resolve_overrides(ov: dict, rows: list, raster: np.ndarray) -> tuple[dict, list]:
    """Owner edits are keyed by a point inside the body (`point`: [px, py], full map pixels), so they survive a
    terrain rebuild that moves outlines and ids; the body id is the fallback. Returns ({current body id: edit},
    the edits that found no body). Edits on the same body merge in the order the owner made them (`at`), the
    latest winning."""
    by_k = {r["raster_index"]: r["id"] for r in rows}
    ids = set(by_k.values())
    out, lost = {}, []
    H, W = raster.shape
    for key, o in sorted(ov.items(), key=lambda kv: str(kv[1].get("at", ""))):
        bid = None
        pt = o.get("point") or ([int(v) for v in re.findall(r"\d+", key)[:2]] if re.fullmatch(r"wb-\d+-\d+(-\d+)?", key) else None)
        if pt:
            x, y = int(pt[0]), int(pt[1])
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
        out.setdefault(bid, {}).update({k: v for k, v in o.items() if k not in ("point", "at")})
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
        at_edge = np.isin(comp, edge_comps[edge_comps > 0]) & False     # the map's edge is not the sea: never an outlet
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


def arrow_samples(raster, rows, vec, gmap, step: int = 22, steps: int = 26) -> list:
    """Flow arrows that follow each channel's curve: from one centreline point per step x step px, the path walks
    the centreline (skeleton) downstream, each step to the neighbour nearest the outlet along the water, for up to
    `steps` px, never leaving its body. One row per arrow: [x, y, bearing at the head, body index, x0, y0, x1, y1,
    ...] (x, y the tail; the polyline's last point is the head)."""
    from skimage.morphology import skeletonize
    run = np.isin(np.array(["land"] + [r.get("water_kind_id", r.get("kind")) for r in rows]), RUNNING)[raster]
    skel = skeletonize(run & np.isfinite(gmap))
    H, W = raster.shape
    ys, xs = np.nonzero(skel)
    _, first = np.unique((ys // step) * 100000 + xs // step, return_index=True)
    out = []
    for y, x in zip(ys[first].tolist(), xs[first].tolist()):
        k = int(raster[y, x])
        pts = [(x, y)]
        cy, cx = y, x
        for _ in range(steps):
            best = None
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = cy + dy, cx + dx
                    if (dy or dx) and 0 <= ny < H and 0 <= nx < W and skel[ny, nx] and raster[ny, nx] == k \
                            and gmap[ny, nx] < gmap[cy, cx] and (best is None or gmap[ny, nx] < gmap[best]):
                        best = (ny, nx)
            if best is None:
                break
            cy, cx = best
            pts.append((cx, cy))
        if len(pts) < 8:
            continue
        pts = pts[::3] + ([pts[-1]] if (len(pts) - 1) % 3 else [])
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        deg = round((math.degrees(math.atan2(bx - ax, -(by - ay))) + 360) % 360)
        out.append([x, y, deg, k] + [c for p in pts for c in p])
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
    for x, y, deg, _k, *pts in arrow_samples(raster, rows, vec, gmap):
        ux, uy = math.sin(math.radians(deg)), -math.cos(math.radians(deg))
        ex, ey = pts[-2], pts[-1]
        d.line(pts, fill=(230, 20, 20), width=2, joint="curve")
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
    result = classify(png="--png" in sys.argv, chunks="--chunks" in sys.argv, accept="--accept" in sys.argv)
    print(json.dumps(result, indent=1, default=dict))
    if not result["check"]["ok"]:
        sys.exit("water_kinds: the classification moved from the accepted one, or an owner edit is off its water "
                 "(out/newworld/water_check.json); look, then `--accept` if it is right")
