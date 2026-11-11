"""Water bodies: every connected stretch of the map's water, with a default kind and, for running water, a flow guess.

How the map's water (`out/newworld/raster/water.png`, one pixel 2.93 m) is cut into bodies:
1. Width. Each water pixel's local width is read by erosion and regrowth on the distance to land: a pixel is
   `open` when it lies in a disc of radius 25 px (73 m) that is all water (water at least ~150 m across), `channel`
   when in a disc of radius 4 px (width at least ~23 m), else `narrow`.
2. Open water. Its connected parts are cut again by region. Open water in a sea region, or joined to such water,
   is sea; so is open water touching the map edge when the water it belongs to (channels included) reaches a sea
   region. Open water that merely reaches the map edge is not: the land past the edge is a neighbour's, and a lake
   the edge cuts is still a lake (marked `edge_cut`: the terrain's inland rise counts it with the sea past the
   edge). Sea is `ocean` in a region named Ocean or Sea or in the Benthic Yobesh, `bay` in a
   region named Bay and wherever sea water lies inside a land region. Open water joined to no sea is `lake`
   (under 0.05 km2 it is a `pond`).
3. Channels and narrow water. Connected channel pixels are a `river`; where a channel meets sea water, its last
   ~220 m (75 px) is an `estuary`, its tidal reach, one body per mouth (pieces within 12 px join); connected narrow pixels are a `stream`. A narrow or channel part that touches no other water and is
   compact is a `pond`.
4. Swamps. In a tree swamp region (swamp, wood) a pond or small lake (under 2 km2) is `blackwater-swamp`; in an open
   wet region (bayou, mangroves, basin, marsh) it is `green-marsh`.
5. Slivers under 40 px join the body they touch most.
6. Ids. A body's label point is its most interior pixel (farthest from land; the first in raster order on a tie);
   its id is `wb-<px>-<py>` of that point, so a rebuild from the same map gives the same ids. Every body records
   `why` for its kind. The owner's kinds are laid on by the water they hold (`hold`), never by id.
7. Flow. Running water (river, stream, estuary) is given a direction toward the sea: the distance from the sea
   along the water network (Dijkstra over water pixels, sources the pixels touching ocean or bay) falls toward the
   mouth, and the terrain rises inland by construction, so the guess runs from the body's farthest pixel to its
   nearest. A body with no water path to the sea flows toward the still water it touches, else is left for a hand
   call.
"""
from __future__ import annotations

import math

import numpy as np
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

OPEN_R, CHANNEL_R = 25, 4
ESTUARY_PX = 75     # ~220 m tidal reach
SLIVER_PX = 40
POND_M2 = 50_000
SWAMP_LAKE_M2 = 2_000_000
EIGHT = np.ones((3, 3), bool)
TREE_SWAMP = {"swamp", "wood"}
OPEN_WET = {"bayou", "mangroves", "basin", "marsh"}


def widths(water: np.ndarray, radius: int) -> np.ndarray:
    """Water pixels inside a disc of `radius` px that is all water."""
    d = ndi.distance_transform_edt(water)
    core = d >= radius
    if not core.any():
        return np.zeros_like(water)
    return water & (ndi.distance_transform_edt(~core) <= radius)


def label_bodies(water: np.ndarray, region_code: np.ndarray, region_names: list, region_kind: dict,
                 region_word: dict, m_per_px: float) -> tuple[np.ndarray, list]:
    """water: bool map; region_code: int per pixel (index into region_names, -1 none). Returns (raster of body
    index 1..n, 0 land) and the body list (dicts without flow)."""
    px_m2 = m_per_px * m_per_px
    dist = ndi.distance_transform_edt(water)
    open_ = widths(water, OPEN_R)
    chan = widths(water, CHANNEL_R) & ~open_
    narrow = water & ~open_ & ~chan
    edge = np.zeros_like(water)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    is_sea_reg = np.zeros(len(region_names) + 1, bool)
    for k, n in enumerate(region_names):
        is_sea_reg[k] = region_kind.get(n) == "sea"
    sea_px = is_sea_reg[region_code] & (region_code >= 0)

    out = np.zeros(water.shape, np.int32)
    bodies: list[dict] = []
    kinds: list[str] = []
    whys: list[str] = []

    def add(mask, kind, why, sl=None):
        if sl is None:
            out[mask] = len(kinds) + 1
        else:
            out[sl][mask] = len(kinds) + 1
        kinds.append(kind)
        whys.append(why)

    lab, n = ndi.label(open_, EIGHT)
    sea_open = np.zeros_like(water)
    edge_cut = np.zeros_like(water)                      # open inland water the map's edge cuts
    if n:
        idx = np.arange(1, n + 1)
        joined, _ = ndi.label(water, EIGHT)              # the edge counts only for water that reaches a sea region
        at_edge = ndi.maximum(edge, lab, idx).astype(bool)
        edge = edge & np.isin(joined, np.unique(joined[sea_px & water]))
        touches_sea = ndi.maximum(sea_px | edge, lab, idx).astype(bool)
        area = ndi.sum(np.ones_like(water), lab, idx)
        for k, sl in zip(idx, ndi.find_objects(lab)):
            m = lab[sl] == k
            if touches_sea[k - 1]:
                sea_open[sl] |= m
                regs = np.unique(region_code[sl][m])
                for r in regs:
                    mr = m & (region_code[sl] == r)
                    name = region_names[r] if r >= 0 else ""
                    word = name.lower()
                    if r >= 0 and is_sea_reg[r] and ("bay" in word):
                        add(mr, "bay", f"open sea water in {name}, a region named as a bay", sl)
                    elif r >= 0 and is_sea_reg[r]:
                        add(mr, "ocean", f"open sea water in the sea region {name}", sl)
                    elif r < 0:
                        add(mr, "ocean", "open sea water at the map's edge", sl)
                    else:
                        add(mr, "bay", f"sea water reaching into the land region {name}", sl)
            else:
                a = area[k - 1] * px_m2
                kind = "pond" if a < POND_M2 else "lake"
                add(m, kind, f"open water ({a / 1e6:.2f} km2) joined to no sea", sl)
                if at_edge[k - 1]:
                    edge_cut[sl] |= m
    near_sea = np.zeros_like(water)
    if sea_open.any():
        near_sea = ndi.distance_transform_edt(~sea_open) <= ESTUARY_PX
        clab, cn = ndi.label(chan, EIGHT)
        mouth = np.unique(clab[ndi.binary_dilation(sea_open, EIGHT, iterations=2) & chan])
        near_sea &= np.isin(clab, mouth[mouth > 0])
    for mask, kind, why in ((chan & near_sea, "estuary", "a river's mouth: the last ~220 m of a channel that meets the sea"),
                            (chan & ~near_sea, "river", "a channel over ~23 m wide"),
                            (narrow, "stream", "a channel under ~23 m wide")):
        if kind == "estuary":                         # one body per mouth: pieces split by width changes join
            lab, n = ndi.label(ndi.binary_dilation(mask, EIGHT, iterations=6), EIGHT)
            lab = np.where(mask, lab, 0)
        else:
            lab, n = ndi.label(mask, EIGHT)
        for k, sl in enumerate(ndi.find_objects(lab), 1):
            if sl is None:
                continue
            add(lab[sl] == k, kind, why, sl)

    # slivers join the neighbour they touch most
    ids = np.arange(1, len(kinds) + 1)
    area = ndi.sum(np.ones_like(water), out, ids)
    small = set(ids[area < SLIVER_PX].tolist())
    if small:
        smask = np.isin(out, list(small))
        big = (out > 0) & ~smask
        _, (ii, jj) = ndi.distance_transform_edt(~big, return_indices=True)
        out[smask] = out[ii[smask], jj[smask]]

    # isolated compact water is a pond; swamp water takes its swamp kind
    whole, _ = ndi.label(water, EIGHT)
    whole_size = np.bincount(whole.ravel())
    ids = [k for k in range(1, len(kinds) + 1) if k not in small]
    objs = ndi.find_objects(out)
    final = np.zeros_like(out)
    for new, k in enumerate(ids, 1):
        sl = objs[k - 1]
        m = out[sl] == k
        a = m.sum() * px_m2
        kind, why = kinds[k - 1], whys[k - 1]
        wl = whole[sl][m]
        alone = whole_size[wl[0]] == m.sum() if kind in ("stream", "river") else False
        if alone:
            hh, ww = m.shape
            if a < POND_M2 or max(hh, ww) < 3 * min(hh, ww):
                kind, why = "pond", f"still water ({a:.0f} m2) touching no other water"
        r = np.bincount(region_code[sl][m] + 1).argmax() - 1
        rname = region_names[r] if r >= 0 else ""
        word = region_word.get(rname)
        if kind in ("pond", "lake") and a < SWAMP_LAKE_M2 and word in TREE_SWAMP:
            kind, why = "blackwater-swamp", f"still water under the trees of {rname} ({word})"
        elif kind in ("pond", "lake") and a < SWAMP_LAKE_M2 and word in OPEN_WET:
            kind, why = "green-marsh", f"shallow open water in {rname} ({word})"
        dm = np.where(m, dist[sl], -1)
        li = int(np.argmax(dm))
        ly, lx = np.unravel_index(li, m.shape)
        lpx, lpy = int(lx + sl[1].start), int(ly + sl[0].start)
        final[sl][m] = new
        bodies.append({"id": f"wb-{lpx}-{lpy}", "raster_index": new, "water_kind_id": kind,
                       "area_m2": round(float(a), 1), "label_px": lpx, "label_py": lpy,
                       "region_id": rname or None, "why": why, "edge_cut": bool(edge_cut[sl][m].any())})
    return final, bodies


def flow(raster: np.ndarray, bodies: list, flows_kind: dict) -> None:
    """Set `flows` and `flow_note` on each body in place (see the module recipe, step 7)."""
    kind_of = np.array(["land"] + [b["water_kind_id"] for b in bodies])
    sea = np.isin(kind_of, ["ocean", "bay"])[raster]
    run = (raster > 0) & ~sea
    n_nodes = int(run.sum())
    node = np.full(raster.shape, -1, np.int64)
    node[run] = np.arange(n_nodes)
    rows, cols, wts = [], [], []
    H, W = raster.shape
    for dy, dx, w in ((0, 1, 1.0), (1, 0, 1.0), (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2))):
        a = node[:H - dy, max(0, -dx):W - max(0, dx)]
        b = node[dy:, max(0, dx):W - max(0, -dx)]
        ok = (a >= 0) & (b >= 0)
        rows.append(a[ok])
        cols.append(b[ok])
        wts.append(np.full(ok.sum(), w))
    touch_sea = run & ndi.binary_dilation(sea, EIGHT)
    g = np.full(n_nodes, np.inf)
    if n_nodes and touch_sea.any():
        r = np.concatenate(rows + cols)
        c = np.concatenate(cols + rows)
        graph = coo_matrix((np.concatenate(wts + wts), (r, c)), shape=(n_nodes, n_nodes)).tocsr()
        g = dijkstra(graph, directed=False, indices=node[touch_sea], min_only=True)
    gmap = np.full(raster.shape, np.inf)
    gmap[run] = g
    objs = ndi.find_objects(raster)
    for b in bodies:
        k = b["raster_index"]
        runs = bool(flows_kind.get(b["water_kind_id"], False))
        b["flows"] = runs
        if not runs:
            b["flow_note"] = "still water"
            continue
        sl = objs[k - 1]
        m = raster[sl] == k
        gv = np.where(m, gmap[sl], np.nan)
        finite = np.isfinite(gv)
        if not finite.any():
            b["flow_note"] = "no water path to the sea on the map; direction left for a hand call"
            continue
        hi = np.unravel_index(np.nanargmax(np.where(finite, gv, np.nan)), m.shape)
        lo = np.unravel_index(np.nanargmin(np.where(finite, gv, np.nan)), m.shape)
        dx, dy = lo[1] - hi[1], lo[0] - hi[0]
        bearing = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
        b["flow_deg"] = round(bearing)
        b["flow_note"] = (f"guess: flows toward {round(bearing)} deg (0 north, clockwise) from px "
                          f"({hi[1] + sl[1].start},{hi[0] + sl[0].start}) to ({lo[1] + sl[1].start},"
                          f"{lo[0] + sl[0].start}); the sea {np.nanmin(gv) * 2.93 / 1000:.1f} km on along the water")


def hold(raster: np.ndarray, bodies: list, held: np.ndarray, held_kind: dict) -> list:
    """The owner's water in the terrain's bodies, so each takes its kind's bed. `held` is the owner's held water
    (tools/newworld/water_held.py: map px, k the k-th held body) and `held_kind` its kind per k. Where held water
    covers a whole body, the body takes the owner's kind; where it covers part of one of another kind, that part is
    cut off as a body of its own (appended; both parts are labelled again). No body under SLIVER_PX is made, the
    smallest the labelling keeps: a smaller held part is left to its body, and a body left with less is taken whole. `raster` and `bodies` change in place.
    The map's own reading of every body stays in `map_kind`. Returns the held bodies that lie on no water."""
    by_i = {b["raster_index"]: b for b in bodies}
    objs = ndi.find_objects(raster)
    npx = np.bincount(raster.ravel(), minlength=len(bodies) + 1).tolist()
    dist = ndi.distance_transform_edt(raster > 0)
    px_m2 = bodies[0]["area_m2"] / max(npx[bodies[0]["raster_index"]], 1) if bodies else 0.0

    def label(b: dict, sl) -> None:
        m = raster[sl] == b["raster_index"]
        ly, lx = np.unravel_index(int(np.argmax(np.where(m, dist[sl], -1))), m.shape)
        b["label_px"], b["label_py"] = int(lx + sl[1].start), int(ly + sl[0].start)
        b["id"] = f"wb-{b['label_px']}-{b['label_py']}"
        b["area_m2"] = round(float(m.sum()) * px_m2, 1)

    lost = []
    slices = ndi.find_objects(held)
    for k in sorted(held_kind):
        sl = slices[k - 1] if 0 < k <= len(slices) else None
        m = (held[sl] == k) & (raster[sl] > 0) if sl is not None else np.zeros((0, 0), bool)
        if not m.any():
            lost.append(f"held water {k} ({held_kind[k]}) lies on no water")
            continue
        for i in np.unique(raster[sl][m]).tolist():
            b = by_i[i]
            if b["water_kind_id"] == held_kind[k]:
                continue
            part = m & (raster[sl] == i)
            n = int(part.sum())
            if n < SLIVER_PX and npx[i] - n >= SLIVER_PX:  # a sliver of held water on a body: no body of its own
                continue
            if npx[i] - n >= SLIVER_PX:                   # part of the body: cut it off as its own
                new = dict(b, raster_index=len(bodies) + 1)
                raster[sl][part] = new["raster_index"]
                npx[i] -= n
                npx.append(n)
                bodies.append(new)
                by_i[new["raster_index"]] = new
                label(new, sl)
                label(b, objs[i - 1])
                b = new
            b["water_kind_id"], b["why"], b["overridden"] = held_kind[k], "owner set the kind", True
    return lost
