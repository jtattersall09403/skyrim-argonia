"""Off-game read of the ground paint as the game shows it: edges, roads, swathes, regional variety, and crops.

    python3 -m tools.newworld.world.texcheck [--out out/newworld/plugin] [--crops name:cx,cy,ncx,ncy ...] [--overview]

Reads `<out>/tex/` shards (texture.py; its materials.json names each material's diffuse, grass and road role) and the
landcover (land/water, road distance, region). Every metric is taken on the ENGINE VIEW: a quadrant shows its alpha
layers added, each with its opacity as its weight, and its base with what is left (1 - their sum, none if they pass
1: then the vertex shows brighter than any of its textures), and only its first six textures (the landscape shader's
six slots, roadpaint.py); a layer past the sixth is not shown. Weights interpolate linearly over
each land triangle (the quad split along its SE-NW diagonal), so a step between two neighbouring vertices, the
diagonal included, is a visible edge whose shape is the triangle's.
Writes `<out>/tex/check.json` and, with --crops, `<out>/crops/tex_*.png` rendered per triangle from the diffuse
textures the NewWorld profile resolves (6 repeats per cell edge); `tex_overview.png` (1 px per 4 vertices).

A step is the change of a weight between two vertices that share a triangle edge, per vertex spacing (1.83 m): the
diagonal's, which is 1.41 spacings long, is divided by 1.41.

Rows (PASS limits; the measured references are in docs/research/nw-02-walk5-ground.md):
  layers: no quadrant over six textures; seams: a vertex shared by quadrants reads the same from each (<= 3/255).
  overbright: a vertex's alpha opacities sum past 1.05 at most 1.8% of land vertices, p99 <= 1.13 (Skyrim.esm, 3,000
    LAND sampled; BM&V never past 1.00): past 1 the engine adds more than one whole texture, a lit square that ends
    hard at the quadrant's edge, near and in the far land built from it.
  edges: per material, the step between neighbouring vertices: p99 <= 0.41 (BM&V), max <= 0.75.
  roads (vertices within a road's reach), against Skyrim.esm's road ground under its straight road pieces in six
    holds: the road weight's step p99 <= 0.31 (the steepest metre of any hold's mean ramp: Whiterun, 0.17 a metre)
    and max <= 0.41; the join, the step of one road material where the road holds >= half the vertex, max <= 0.41
    (both: no harder than the hardest hundredth of BM&V's ground steps, the edges limit); the spine (within 1.5 m of
    a road centre line, clear of the ramp by which a road runs out toward water): at most 2.8% of its vertices under
    0.6 road weight (Whiterun, Skyrim's worst hold) and none under 0.4, at most 1.8% carrying more than 0.1
    grass-bearing ground (Hjaalmarch, Skyrim's worst hold); across the road's walked surface (to 0.45 m inside its edge,
    3 m from a major spine and 1.55 m from a minor, where the rule holds the road at 0.97 or more) no vertex carries
    over 0.1 grass-bearing ground (grass grows by its ground's weight: at 0.1 or
    less a tuft here and there, as on Skyrim's spines, whose grass-bearing share is 0.1 or less at 98.2% or more of
    their vertices in every hold); no road quadrant over the cap. Skyrim's own road steps
    are harder than these (p90 1.0 in every hold: a hard brush under a road mesh), so the step limits are taken from
    its mean ramp and from BM&V's painted ground: what a road with no mesh over it must show.
  swathes: per land region, the distance from a vertex to the nearest change of its dominant texture (run) p90 <= 12 m
    and p99 <= 35 m, of its dominant grass list p90 <= 80 m and p99 <= 140 m (Skyrim.esm's five holds: texture p90
    2.6 to 10.7, p99 7.5 to 33.7; grass p90 15 to 77, p99 44 to 135); no material over 0.40 of any land 1 km window.
  variety: textures per land quadrant mean >= 2.5; regional similarity = weighted Jaccard of two land regions' ground
    material shares and of their grass shares (reported, with each region's nearest neighbour).
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from tools.newworld.world import roadpaint as rp
from tools.newworld.world import texture as tx

REPO = tx.REPO
SLOTS = 6  # textures a quadrant can show
Q = tx.Q
# the old build's materials.json named no diffuse: these are its paths
OLD_DIFFUSE = {
    "forest_floor": "Landscape\\PineForest03.dds", "moss": "TEXTUREPACK\\landscape\\tundramoss01.dds",
    "wet_rock_moss": "TEXTUREPACK\\landscape\\grass\\rocksgrasswater01.dds", "swamp_mud": "TEXTUREPACK\\landscape\\rivermud.dds",
    "mud_reeds": "argonia\\landscape\\rivermud.dds", "marsh_grass": "argonia\\landscape\\CTQ_Grass_Lush01.dds",
    "rainforest": "argonia\\landscape\\CTQ_Undergrowth_01.dds", "rainforest_low": "argonia\\landscape\\CTQ_JungleGrass01_d.dds",
    "dirt_grass": "TEXTUREPACK\\landscape\\fielddirtgrass01.dds", "dark_grass_rocks": "landscape\\darklandgrassrocks.dds",
    "meadow": "Landscape\\FieldGrass02.dds", "sand": "landscape\\sand\\Sand03.dds",
    "wet_sand": "_ResourcePack\\Landscape\\SandWet01_d.dds", "rock": "landscape\\Apel_lh_rock_02.dds",
    "rock2": "vvardenfell\\rm\\rm_rock02.dds", "rock_grass": "Landscape\\TundraRocks01.dds", "dirt_road": "dirtroad01.dds",
    "road_skirt": "Landscape\\Dirt02.dds", "marsh_mud": "_ResourcePack\\Landscape\\MarshMud02_d.dds",
    "riverbed_edge": "Landscape\\RiverbedEdge.dds", "river_bottom": "Landscape\\RiverBottom.dds",
    "river_mud": "Landscape\\RiverMud.dds", "beach": "Landscape\\CoastBeach01.dds",
    "ocean_floor": "Landscape\\CoastOceanFloor01.dds", "dirt_slopes": "Landscape\\FrozenMarshDirtSlopes01.dds",
    "silt": "argonia\\landscape\\dirt02.dds",
}
OLD_ROAD = {"dirt_road", "road_skirt"}
LIMITS = {"step_p99": 0.41, "step_max": 0.75, "seam_max": 3 / 255 + 1e-6, "road_step_p99": 0.31, "road_step_max": 0.41,
          "road_join_max": 0.41, "surface_grass_max": 0.1, "over_share": 0.018, "over_p99": 1.13, "road_spine_min": 0.4, "road_spine_low_share": 0.028, "road_spine_grassy_share": 0.018, "run_tex_p90": 12.0, "run_tex_p99": 35.0, "run_grass_p90": 80.0,
          "run_grass_p99": 140.0, "swathe_1km": 0.40, "textures_per_quadrant": 2.5}
SEA_REGIONS = {"benthic-yobesh", "padomaic-ocean", "sea-of-mists", "topal-bay"}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def read_rows(out: Path):
    man = json.loads((out / "tex/manifest.json").read_text())
    g = json.loads((out / "land/manifest.json").read_text())["grid"]
    return man, g


def materials(out: Path) -> list[dict]:
    mats = json.loads((out / "tex/materials.json").read_text())
    for m in mats:
        m.setdefault("diffuse", OLD_DIFFUSE.get(m["id"]))
        m.setdefault("road", m["id"] in OLD_ROAD)
    return mats


def decode_row(data: bytes, maxl: int, nm: int, slots: int | None = SLOTS):
    """All quadrants of one shard -> (dense weights [nq, 289, nm] as the engine shows them, layer counts [nq], weight
    the engine cannot show [nq, 289], dense of the dropped layers [nq, 289, nm])."""
    qb = 1 + maxl + (maxl - 1) * Q * Q
    a = np.frombuffer(data, np.uint8).reshape(-1, qb)
    n = a[:, 0].astype(int)
    mats = a[:, 1:1 + maxl].astype(int)
    alph = a[:, 1 + maxl:].reshape(-1, maxl - 1, Q * Q).astype(np.float32) / 255
    nq = a.shape[0]

    def stack(limit):
        W = np.zeros((nq, maxl, Q * Q), np.float32)
        for k in range(1, maxl):
            W[:, k] = alph[:, k - 1] * (k < np.minimum(n, limit))[:, None]
        W[:, 0] = np.clip(1 - W[:, 1:].sum(1), 0, 1)
        return W

    full = stack(maxl)
    eng = stack(slots or maxl)
    dense = np.zeros((nq, Q * Q, nm), np.float32)
    lost = np.zeros((nq, Q * Q, nm), np.float32)
    qi = np.arange(nq)
    for k in range(maxl):
        ok = k < n
        mk = np.where(ok, mats[:, k], 0)
        np.add.at(dense, (qi[ok][:, None], np.arange(Q * Q)[None], mk[ok][:, None]), eng[ok, k])
        if slots and k >= slots:
            np.add.at(lost, (qi[ok][:, None], np.arange(Q * Q)[None], mk[ok][:, None]), full[ok, k])
    shown_loss = 0.5 * np.abs(full_dense(full, mats, n, nm) - dense).sum(-1)
    return dense, n, shown_loss, lost


def full_dense(W, mats, n, nm):
    nq, maxl = mats.shape
    d = np.zeros((nq, Q * Q, nm), np.float32)
    qi = np.arange(nq)
    for k in range(maxl):
        ok = k < n
        np.add.at(d, (qi[ok][:, None], np.arange(Q * Q)[None], np.where(ok, mats[:, k], 0)[ok][:, None]), W[ok, k])
    return d


def steps(g: np.ndarray) -> np.ndarray:
    """g [..., 17, 17, k] -> the steps between every pair of vertices that share a triangle edge, per vertex spacing:
    x, y and the SE-NW diagonal of each quad ((r, c+1) to (r+1, c), y from the south; 1.41 spacings long, so divided
    by 1.41), stacked [..., pairs, k]."""
    dx = g[..., :, 1:, :] - g[..., :, :-1, :]
    dy = g[..., 1:, :, :] - g[..., :-1, :, :]
    dd = (g[..., 1:, :-1, :] - g[..., :-1, 1:, :]) / np.sqrt(2).astype(g.dtype)
    sh = g.shape[:-3]
    return np.concatenate([dx.reshape(*sh, -1, g.shape[-1]), dy.reshape(*sh, -1, g.shape[-1]),
                           dd.reshape(*sh, -1, g.shape[-1])], -2)


def pair_any(m: np.ndarray) -> np.ndarray:
    """m [..., 17, 17] bool -> per triangle-edge pair (as steps orders them): either end."""
    a = m[..., :, 1:] | m[..., :, :-1]
    b = m[..., 1:, :] | m[..., :-1, :]
    c = m[..., 1:, :-1] | m[..., :-1, 1:]
    sh = m.shape[:-2]
    return np.concatenate([a.reshape(*sh, -1), b.reshape(*sh, -1), c.reshape(*sh, -1)], -1)


def pair_both(m):
    a = m[..., :, 1:] & m[..., :, :-1]
    b = m[..., 1:, :] & m[..., :-1, :]
    c = m[..., 1:, :-1] & m[..., :-1, 1:]
    sh = m.shape[:-2]
    return np.concatenate([a.reshape(*sh, -1), b.reshape(*sh, -1), c.reshape(*sh, -1)], -1)


def pct(h: np.ndarray, q: float) -> float:
    if h.sum() == 0:
        return 0.0
    return float(np.searchsorted(np.cumsum(h) / h.sum(), q) / 100)


def check(out: Path, rows: list[int] | None = None) -> dict:
    man, g = read_rows(out)
    mats = materials(out)
    nm = len(mats)
    maxl = int(man.get("max_layers", 7))
    lc = tx.LC
    flags = np.load(lc / "flags.npy", mmap_mode="r")
    roadd = np.load(lc / "road.npy", mmap_mode="r")
    roadc = np.load(lc / "roadcls.npy", mmap_mode="r")
    regv = np.load(lc / "region.npy", mmap_mode="r")
    shorev = np.load(lc / "shore.npy", mmap_mode="r")
    legend = json.loads((lc / "legend.json").read_text())
    regions = legend["regions"]
    nreg = len(regions) + 1
    road_m = np.array([m["road"] for m in mats])
    grass_key = {}
    gid = np.array([grass_key.setdefault(tuple(sorted(m["grass"])), len(grass_key)) for m in mats])
    nx = g["cells_x"]
    shards = man["shards"]
    if rows is not None:
        shards = [s for s in shards if int(s[2:-4]) in rows]
    H = (g["cy_top"] - g["cy_bottom"] + 1) * 32 + 1
    dom = np.full((H, nx * 32 + 1), 255, np.uint8)
    dgr = np.full((H, nx * 32 + 1), 65535, np.uint16)
    hist = np.zeros(102, np.int64)
    rhist = np.zeros(102, np.int64)
    maxstep, max_at = 0.0, None
    rmax, rmax_at, jmax, jmax_at = 0.0, None, 0.0, None
    spine_min, spine_at, spine_low, spine_grass, spine_n, spine_grassy = 1.0, None, 0, 0.0, 0, 0
    surf_grass, surf_at, surf_n = 0.0, None, 0
    grassy = np.array([bool(m["grass"]) for m in mats])
    seam_max, seam_at = 0.0, None
    ohist = np.zeros(301, np.int64)
    over_max, over_at = 0.0, None
    over_cap = road_cap = 0
    lost_max = 0.0
    road_lost_max, road_lost_at = 0.0, None
    nlayers, ntex_land = [], []
    reg_w = np.zeros((nreg, nm), np.float64)
    cell_w = {}
    prev, prev_cy = None, None
    for k, name in enumerate(shards):
        cy = int(name[2:-4])
        data = (out / "tex" / name).read_bytes()
        north = (g["cy_top"] - cy) * 32
        dense, n, loss, lost = decode_row(data, maxl, nm)
        D = dense.reshape(nx, 4, Q, Q, nm)
        # landcover at each quadrant's vertices (y from the south)
        fl = np.asarray(flags[north:north + 33])[::-1]
        rd = np.asarray(roadd[north:north + 33], np.float32)[::-1] / 10
        rc = np.asarray(roadc[north:north + 33])[::-1]
        rg = np.asarray(regv[north:north + 33])[::-1]
        sh = np.asarray(shorev[north:north + 33], np.float32)[::-1] / 10

        def quads(a):
            out_ = np.zeros((nx, 4, Q, Q) + a.shape[2:], a.dtype)
            for q in range(4):
                qy, qx = divmod(q, 2)
                for i in range(nx):
                    out_[i, q] = a[qy * 16:qy * 16 + Q, i * 32 + qx * 16:i * 32 + qx * 16 + Q]
            return out_
        land = quads((fl & 1) == 0)
        rdq, rcq, rgq, shq = quads(rd), quads(rc), quads(rg), quads(sh)
        reach = np.where(rcq == 1, rp.HALF_M["major"] + rp.reach_m(1.0), rp.HALF_M["minor"] + rp.reach_m(rp.SCALE["minor"]))
        roadv = (rcq > 0) & (rdq < reach) & land
        spine = (rcq > 0) & (rdq < 1.5) & land & (shq >= tx.ROAD_WATER[1])
        surface = (rcq > 0) & (rdq < np.where(rcq == 1, rp.HALF_M["major"], rp.HALF_M["minor"]) + rp.PULL_E[0]) & land & (shq >= tx.ROAD_WATER[1])
        # overbright: the shown weights' sum past 1 on land
        tot = D.sum(-1)
        ohist += np.bincount(np.minimum((tot[land] * 100).astype(int), 300), minlength=301)
        if land.any() and float(tot[land].max()) > over_max:
            i, q = np.unravel_index(np.argmax(np.where(land, tot, 0).max((2, 3))), (nx, 4))
            over_max, over_at = float(tot[land].max()), [g["cx0"] + int(i), cy, int(q)]
        # layers
        nlayers += n.tolist()
        oc = n > SLOTS
        over_cap += int(oc.sum())
        lost_max = max(lost_max, float(loss.max()))
        lq = lost.reshape(nx, 4, Q, Q, nm)[..., road_m].sum(-1)
        rq = roadv.any((2, 3)) & oc.reshape(nx, 4)
        if rq.any():
            road_cap += int((rq & (lq.max((2, 3)) > 0.05)).sum())
            v = float(np.where(roadv, lq, 0).max())
            if v > road_lost_max:
                i, q = np.unravel_index(np.argmax(np.where(roadv, lq, 0).max((2, 3))), (nx, 4))
                road_lost_max, road_lost_at = v, [g["cx0"] + int(i), cy, int(q)]
        # edges (all materials, pairs where either side has weight)
        st = np.abs(steps(D))
        s = st[st > 0]
        hist += np.bincount(np.minimum((s * 100).astype(int), 101), minlength=102)
        mx = float(st.max())
        if mx > maxstep:
            i, q = np.unravel_index(np.argmax(st.reshape(nx, 4, -1).max(-1)), (nx, 4))
            maxstep, max_at = mx, [g["cx0"] + int(i), cy, int(q)]
        # roads
        R = D[..., road_m].sum(-1)
        if roadv.any():
            rs = np.abs(steps(R[..., None]))[..., 0]
            pm = pair_any(roadv)
            sv = rs[pm]
            rhist += np.bincount(np.minimum((sv * 100).astype(int), 101), minlength=102)
            v = float(sv.max()) if sv.size else 0.0
            if v > rmax:
                i, q = np.unravel_index(np.argmax(np.where(pm, rs, 0).max(-1)), (nx, 4))
                rmax, rmax_at = v, [g["cx0"] + int(i), cy, int(q)]
            js = np.abs(steps(D[..., road_m]))
            pb = pair_both((R >= 0.5) & roadv)
            jv = np.where(pb[..., None], js, 0).max(-1)
            v = float(jv.max())
            if v > jmax:
                i, q = np.unravel_index(np.argmax(jv.max(-1)), (nx, 4))
                jmax, jmax_at = v, [g["cx0"] + int(i), cy, int(q)]
            if surface.any():
                G = np.where(surface, D[..., grassy].sum(-1), 0)
                surf_n += int(surface.sum())
                if float(G.max()) > surf_grass:
                    i, q = np.unravel_index(np.argmax(G.max((2, 3))), (nx, 4))
                    surf_grass, surf_at = float(G.max()), [g["cx0"] + int(i), cy, int(q)]
            if spine.any():
                gv = D[..., grassy].sum(-1)[spine]
                spine_grass = max(spine_grass, float(gv.max()))
                sv = R[spine]
                spine_low += int((sv < 0.6).sum())
                spine_n += int(sv.size)
                spine_grassy += int((gv > 0.1).sum())
                v = float(sv.min())
                if v < spine_min:
                    i, q = np.unravel_index(np.argmin(np.where(spine, R, 9).min((2, 3))), (nx, 4))
                    spine_min, spine_at = v, [g["cx0"] + int(i), cy, int(q)]
        # seams inside the row and with the row to the north
        bl, br, tl, tr = D[:, 0], D[:, 1], D[:, 2], D[:, 3]
        pairs = [(bl[:, :, 16], br[:, :, 0]), (tl[:, :, 16], tr[:, :, 0]), (bl[:, 16], tl[:, 0]), (br[:, 16], tr[:, 0]),
                 (br[:-1, :, 16], bl[1:, :, 0]), (tr[:-1, :, 16], tl[1:, :, 0])]
        if prev is not None and prev_cy == cy + 1:
            pairs += [(prev[:, 0, 0], tl[:, 16]), (prev[:, 1, 0], tr[:, 16])]
        for a_, b_ in pairs:
            d = np.abs(a_ - b_).max(-1)
            if d.size and float(d.max()) > seam_max:
                seam_max = float(d.max())
                seam_at = [g["cx0"] + int(np.unravel_index(np.argmax(d), d.shape)[0]), cy]
        prev, prev_cy = D, cy
        # dominant texture and grass list, region shares, textures per land quadrant
        dm_ = np.argmax(D, -1).astype(np.uint8)
        for q in range(4):
            qy, qx = divmod(q, 2)
            r0 = north + 32 - qy * 16 - 16  # y from the south -> rows from the north
            for i in range(nx):
                blk = dm_[i, q][::-1]
                dom[r0:r0 + Q, i * 32 + qx * 16:i * 32 + qx * 16 + Q] = blk
        lw = land[..., None] * D
        ntex_land += ((lw.max((2, 3)) >= 0.02).sum(-1)[land.any((2, 3))]).tolist()
        for m in range(nm):
            reg_w[:, m] += np.bincount(rgq[land].ravel().astype(int), weights=D[..., m][land].ravel(), minlength=nreg)[:nreg]
        cw = lw.sum((1, 2, 3))
        cl = land.sum((1, 2, 3))
        for i in range(nx):
            cell_w[(g["cx0"] + i, cy)] = (cw[i], cl[i])
        if k % 20 == 0:
            log(f"  check row {cy}")
    dgr = np.where(dom == 255, 65535, gid[np.minimum(dom, nm - 1)]).astype(np.uint16)
    res = {"engine_slots": SLOTS, "max_layers_written": maxl,
           "layers_hist": np.bincount(nlayers, minlength=maxl + 1).tolist(),
           "quadrants_over_cap": over_cap, "cap_lost_weight_max": round(lost_max, 3),
           "step_p90": pct(hist, 0.90), "step_p99": pct(hist, 0.99), "step_max": round(maxstep, 3), "step_max_at": max_at,
           "seam_max": round(seam_max, 4), "seam_at": seam_at,
           "over_share": round(float(ohist[105:].sum() / max(ohist.sum(), 1)), 4), "over_p99": pct(ohist, 0.99),
           "over_max": round(over_max, 3), "over_at": over_at,
           "road_step_p99": pct(rhist, 0.99), "road_step_max": round(rmax, 3), "road_step_max_at": rmax_at,
           "road_join_max": round(jmax, 3), "road_join_at": jmax_at,
           "road_spine_min": round(spine_min, 3), "road_spine_at": spine_at, "road_spine_vertices_low": spine_low,
           "road_spine_grass_max": round(spine_grass, 3), "road_spine_vertices": spine_n,
           "road_spine_low_share": round(spine_low / max(spine_n, 1), 4),
           "road_spine_grassy_share": round(spine_grassy / max(spine_n, 1), 4),
           "road_surface_grass_max": round(surf_grass, 3), "road_surface_grass_at": surf_at, "road_surface_vertices": surf_n,
           "road_quadrants_over_cap": road_cap, "road_weight_hidden_by_cap_max": round(road_lost_max, 3),
           "road_hidden_at": road_lost_at,
           "layers_per_quadrant_mean": round(float(np.mean(nlayers)), 2),
           "textures_per_land_quadrant_mean": round(float(np.mean(ntex_land)), 2) if ntex_land else 0.0}
    res.update(swathe(dom, dgr, regv, flags, regions, g, rows))
    res.update(window_1km(cell_w, mats, g))
    res.update(similarity(reg_w, regions, mats))
    L = LIMITS
    fails = []
    for key, lim, ok in (("quadrants_over_cap", 0, res["quadrants_over_cap"] == 0),
                         ("step_p99", L["step_p99"], res["step_p99"] <= L["step_p99"]),
                         ("step_max", L["step_max"], res["step_max"] <= L["step_max"]),
                         ("seam_max", L["seam_max"], res["seam_max"] <= L["seam_max"]),
                         ("over_share", L["over_share"], res["over_share"] <= L["over_share"]),
                         ("over_p99", L["over_p99"], res["over_p99"] <= L["over_p99"]),
                         ("road_step_p99", L["road_step_p99"], res["road_step_p99"] <= L["road_step_p99"]),
                         ("road_step_max", L["road_step_max"], res["road_step_max"] <= L["road_step_max"]),
                         ("road_join_max", L["road_join_max"], res["road_join_max"] <= L["road_join_max"]),
                         ("road_spine_min", L["road_spine_min"], res["road_spine_min"] >= L["road_spine_min"]),
                         ("road_spine_low_share", L["road_spine_low_share"], res["road_spine_low_share"] <= L["road_spine_low_share"]),
                         ("road_spine_grassy_share", L["road_spine_grassy_share"], res["road_spine_grassy_share"] <= L["road_spine_grassy_share"]),
                         ("road_surface_grass_max", L["surface_grass_max"], res["road_surface_grass_max"] <= L["surface_grass_max"]),
                         ("road_quadrants_over_cap", 0, res["road_quadrants_over_cap"] == 0),
                         ("run_tex_p90_worst", L["run_tex_p90"], res["run_tex_p90_worst"] <= L["run_tex_p90"]),
                         ("run_tex_p99_worst", L["run_tex_p99"], res["run_tex_p99_worst"] <= L["run_tex_p99"]),
                         ("run_grass_p90_worst", L["run_grass_p90"], res["run_grass_p90_worst"] <= L["run_grass_p90"]),
                         ("run_grass_p99_worst", L["run_grass_p99"], res["run_grass_p99_worst"] <= L["run_grass_p99"]),
                         ("swathe_max_1km_land", L["swathe_1km"], res["swathe_max_1km_land"] <= L["swathe_1km"]),
                         ("textures_per_land_quadrant_mean", L["textures_per_quadrant"],
                          res["textures_per_land_quadrant_mean"] >= L["textures_per_quadrant"])):
        if not ok:
            fails.append(f"{key} {res[key]} (limit {lim})")
    res["fails"] = fails
    res["pass"] = not fails
    (out / "tex/check.json").write_text(json.dumps(res, indent=1, default=float))
    return res


def swathe(dom, dgr, regv, flags, regions, g, rows) -> dict:
    """Per land region: how far one dominant texture / grass list runs from each vertex (m to the nearest change)."""
    H = dom.shape[0]
    have = dom != 255
    land = np.zeros_like(have)
    land[:] = (np.asarray(flags[:H, :dom.shape[1]]) & 1) == 0
    reg = np.asarray(regv[:H, :dom.shape[1]])
    out = {"runs": {}}
    for nm_, a in (("tex", dom), ("grass", dgr)):
        chg = np.zeros(a.shape, bool)
        d = a[:, 1:] != a[:, :-1]
        chg[:, 1:] |= d
        chg[:, :-1] |= d
        d = a[1:] != a[:-1]
        chg[1:] |= d
        chg[:-1] |= d
        chg |= ~have
        dist = ndi.distance_transform_edt(~chg).astype(np.float32) * rp.VERTEX_M
        # a run cut by the sample's edge is not measured (the band's first and last 40 vertices)
        ok = have & land
        if rows is not None:
            ok &= ndi.binary_erosion(have, np.ones((3, 3), bool), iterations=40)
        for ri, rn in enumerate(regions):
            if rn in SEA_REGIONS:
                continue
            m = ok & (reg == ri)
            if m.sum() < 2000:
                continue
            v = dist[m]
            r = out["runs"].setdefault(rn, {})
            r[f"{nm_}_p50"] = round(float(np.percentile(v, 50)), 1)
            r[f"{nm_}_p90"] = round(float(np.percentile(v, 90)), 1)
            r[f"{nm_}_p99"] = round(float(np.percentile(v, 99)), 1)
            r[f"{nm_}_max"] = round(float(v.max()), 1)
    for nm_ in ("tex", "grass"):
        for p in ("p90", "p99"):
            vals = [(r[f"{nm_}_{p}"], rn) for rn, r in out["runs"].items() if f"{nm_}_{p}" in r]
            out[f"run_{nm_}_{p}_worst"] = max(vals)[0] if vals else 0.0
            out[f"run_{nm_}_{p}_worst_region"] = max(vals)[1] if vals else None
    return out


def window_1km(cell_w, mats, g) -> dict:
    """The largest share one material holds of any 1 km of land (17 x 17 cells, land >= 50%)."""
    from scipy.ndimage import uniform_filter
    if not cell_w:
        return {"swathe_max_1km_land": 0.0}
    xs = [k[0] for k in cell_w]
    ys = [k[1] for k in cell_w]
    x0, y0 = min(xs), min(ys)
    W_, H_ = max(xs) - x0 + 1, max(ys) - y0 + 1
    nm = len(mats)
    cw = np.zeros((H_, W_, nm))
    cl = np.zeros((H_, W_))
    for (x, y), (w, l) in cell_w.items():
        cw[y - y0, x - x0] = w
        cl[y - y0, x - x0] = l
    lw = uniform_filter(cl, 17, mode="constant")
    full = uniform_filter(np.ones_like(cl), 17, mode="constant")
    mask = (lw >= 0.5 * 4 * Q * Q) & (full > 0.999)
    share = np.stack([uniform_filter(cw[..., m], 17, mode="constant") for m in range(nm)], -1) / np.maximum(lw[..., None], 1e-9)
    win = share[mask]
    if not win.size:
        return {"swathe_max_1km_land": 0.0}
    j = np.unravel_index(np.argmax(np.where(mask[..., None], share, 0)), share.shape)
    tot = cw.sum((0, 1))
    land = cl.sum()
    table = {m["id"]: round(float(tot[k] / max(land, 1)), 4) for k, m in enumerate(mats)}
    gras = sum(v for m, v in zip(mats, table.values()) if m["grass"])
    return {"swathe_max_1km_land": round(float(win.max()), 3), "swathe_material": mats[j[2]]["id"],
            "swathe_at_cell": [int(x0 + j[1]), int(y0 + j[0])], "gras_share_of_land": round(gras, 3),
            "share_of_land": dict(sorted(table.items(), key=lambda x: -x[1]))}


def wjaccard(a, b) -> float:
    a = a / max(a.sum(), 1e-12)
    b = b / max(b.sum(), 1e-12)
    return float(np.minimum(a, b).sum() / max(np.maximum(a, b).sum(), 1e-12))


def similarity(reg_w, regions, mats) -> dict:
    """Weighted Jaccard between land regions: of their ground materials' shares (by texture: variants of one diffuse
    count as one) and of their grass (each material's share split over its grass list)."""
    diff = {}
    tex_ix = np.array([diff.setdefault((m.get("diffuse") or m["id"]).lower(), len(diff)) for m in mats])
    gl = {}
    for m in mats:
        for gr in m["grass"]:
            gl.setdefault(gr, len(gl))
    T = np.zeros((reg_w.shape[0], len(diff)))
    G = np.zeros((reg_w.shape[0], max(len(gl), 1)))
    for k, m in enumerate(mats):
        T[:, tex_ix[k]] += reg_w[:, k]
        for gr in m["grass"]:
            G[:, gl[gr]] += reg_w[:, k] / len(m["grass"])
    names = [(i, r) for i, r in enumerate(regions) if r not in SEA_REGIONS and reg_w[i].sum() > 1e4]
    out = {}
    for label, A in (("ground", T), ("grass", G)):
        tab = {}
        for i, a in names:
            best = max(((wjaccard(A[i], A[j]), b) for j, b in names if j != i), default=(0.0, None))
            tab[a] = {"nearest": best[1], "jaccard": round(best[0], 3)}
        vals = [wjaccard(A[i], A[j]) for x, (i, _) in enumerate(names) for (j, _) in names[x + 1:]]
        out[f"similarity_{label}"] = {"max": round(max(vals), 3) if vals else 0.0,
                                      "mean": round(float(np.mean(vals)), 3) if vals else 0.0, "by_region": tab}
    return out


# --- rendering ----------------------------------------------------------------------------------------------------

class Tex:
    """Each material's diffuse as the NewWorld profile resolves it (Tropical Skyrim's loose files over vanilla's)."""

    def __init__(self, mats):
        self.mats = mats
        self.cache = {}
        from tools.places.assets.resolve import default, norm
        self.R, self.norm = default(), norm

    def get(self, k: int) -> np.ndarray:
        if k in self.cache:
            return self.cache[k]
        rel = self.mats[k].get("diffuse")
        b = self.R.read(self.norm(rel, "textures")) if rel else None
        if b is None:
            a = np.zeros((256, 256, 3), np.float32) + np.array((255, 0, 255), np.float32)
        else:
            a = np.asarray(Image.open(io.BytesIO(b)).convert("RGB").resize((256, 256)), np.float32)
        self.cache[k] = a
        return a


def tri_weights(qw: np.ndarray, ppv: int) -> np.ndarray:
    """One quadrant's [17, 17, n] vertex weights (y from the south) -> [16 ppv, 16 ppv, n] pixels (y from the south),
    linear over each triangle of the quad split along its SE-NW diagonal."""
    n = 16 * ppv
    f = (np.arange(n) + 0.5) / ppv
    fy, fx = np.meshgrid(f, f, indexing="ij")
    r, c = np.minimum(fy.astype(int), 15), np.minimum(fx.astype(int), 15)
    ty, tx_ = fy - r, fx - c
    v00, v01, v10, v11 = qw[r, c], qw[r, c + 1], qw[r + 1, c], qw[r + 1, c + 1]
    lo = (tx_ + ty <= 1)[..., None]
    a = v00 + (v01 - v00) * tx_[..., None] + (v10 - v00) * ty[..., None]
    b = v11 + (v10 - v11) * (1 - tx_[..., None]) + (v01 - v11) * (1 - ty[..., None])
    return np.where(lo, a, b)


def composite(out: Path, cx0: int, cy0: int, ncx: int, ncy: int, ppv: int = 8) -> np.ndarray:
    """RGB of cells [cx0, cx0+ncx) x [cy0, cy0+ncy) as the game shows them: six slots, per-triangle blends."""
    man, g = read_rows(out)
    mats = materials(out)
    nm = len(mats)
    T = Tex(mats)
    P = 32 * ppv
    img = np.zeros((ncy * P, ncx * P, 3), np.float32)
    rep = 256 * 6 / P
    yy, xx = np.mgrid[0:16 * ppv, 0:16 * ppv]
    for cy in range(cy0, cy0 + ncy):
        data = (out / "tex" / f"cy{cy:+04d}.bin").read_bytes()
        dense, *_ = decode_row(data, int(man.get("max_layers", 7)), nm)
        D = dense.reshape(g["cells_x"], 4, Q, Q, nm)
        for cx in range(cx0, cx0 + ncx):
            for q in range(4):
                qy, qx = divmod(q, 2)
                qw = D[cx - g["cx0"], q]
                used = np.nonzero(qw.max((0, 1)) > 1e-3)[0]
                pw = tri_weights(qw[..., used], ppv)[::-1]  # north up
                y0 = (cy0 + ncy - 1 - cy) * P + (1 - qy) * 16 * ppv
                x0 = (cx - cx0) * P + qx * 16 * ppv
                u = (((x0 + xx) * rep) % 256).astype(int)
                v = (((y0 + yy) * rep) % 256).astype(int)
                acc = np.zeros((16 * ppv, 16 * ppv, 3), np.float32)
                for j, m in enumerate(used):
                    acc += pw[..., j:j + 1] * T.get(int(m))[v, u]
                img[y0:y0 + 16 * ppv, x0:x0 + 16 * ppv] = acc
    return np.clip(img, 0, 255).astype(np.uint8)


def overview(out: Path, step: int = 4) -> None:
    man, g = read_rows(out)
    mats = materials(out)
    T = Tex(mats)
    mean = np.stack([T.get(k).reshape(-1, 3).mean(0) for k in range(len(mats))])
    rows = []
    for name in man["shards"]:
        data = (out / "tex" / name).read_bytes()
        dense, *_ = decode_row(data, int(man.get("max_layers", 7)), len(mats))
        D = dense.reshape(g["cells_x"], 4, Q, Q, len(mats))
        band = np.zeros((32 // step, g["cells_x"] * 32 // step, 3), np.float32)
        for i in range(g["cells_x"]):
            for q in range(4):
                qy, qx = divmod(q, 2)
                c = (D[i, q] @ mean)[:16:step, :16:step]
                band[(1 - qy) * 16 // step:(2 - qy) * 16 // step, (i * 32 + qx * 16) // step:(i * 32 + qx * 16 + 16) // step] = c[::-1]
        rows.append(band)
    Image.fromarray(np.clip(np.concatenate(rows), 0, 255).astype(np.uint8)).save(out / "crops/tex_overview.png")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "out/newworld/plugin")
    ap.add_argument("--crops", nargs="*", help="name:cx,cy,ncx,ncy ...")
    ap.add_argument("--overview", action="store_true")
    ap.add_argument("--no-metrics", action="store_true")
    ap.add_argument("--rows", help="lo:hi cell rows (a sample painted with texture.py --rows)")
    a = ap.parse_args(argv)
    (a.out / "crops").mkdir(parents=True, exist_ok=True)
    ok = True
    rows = None
    if a.rows:
        lo, hi = map(int, a.rows.split(":"))
        rows = list(range(lo, hi + 1))
    if not a.no_metrics:
        r = check(a.out, rows)
        print(json.dumps({k: v for k, v in r.items() if k not in ("share_of_land",)}, indent=1, default=float))
        print("texcheck", "PASS" if r["pass"] else "FAIL: " + "; ".join(r["fails"]))
        ok = r["pass"]
    for spec in a.crops or []:
        name, box = spec.split(":")
        cx, cy, nx, ny = map(int, box.split(","))
        Image.fromarray(composite(a.out, cx, cy, nx, ny)).save(a.out / f"crops/tex_{name}.png")
    if a.overview:
        overview(a.out)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
