"""`draft <place_id>`: the source bundle and our ground bundle into the place files (docs/design/place-studio.md).

The agent's own calls (skill place-build) are inputs, read from place.json's `draft` block:
  anchor [x, y]    where the source's middle goes on our land (default: the place record's position)
  rot_deg          the source's turn onto our land (default: searched)
  search           how far round the anchor the global fit looks (units, default 4096)
  replace          {source base key: our base key | {base, turn_deg}}: a Nordic or unsuitable base swapped for one of
                   like size and use (turn_deg when the new model's front faces another way)
  drop             {source ref id: reason}: a source ref left out by judgement
  roles            {role: {space | pos:[x,y]}}: where a service person works, when the default is wrong
  keep_patches     false to forbid land patches (the check then lists what needs one)
  add              [{base, pos:[x, y], rot_z?, kind?, dz?, why}]: something the record promises that the source
                   lacks (a forge, a shrine), placed on our land and seated on the ground
Everything else in the place files is written here, deterministically.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

from tools.places.draft import clear as clearmod
from tools.places.draft import geom, interiors, io, people, seating
from tools.places.draft import paths as paths_mod
from tools.places.draft.geom import LEVELLED
from tools.places.draft.cluster import VEG, decompose
from tools.places.draft.fit import Scorer, global_fit, local_fit, patch_for, patch_verts, relief_norm
from tools.places.draft.fit import _pivot as fit_pivot
from tools.places.draft.paths import PATH_WIDTH, STREET_WIDTH, NavGraph, network, simplify
from tools.places.seat import Ground, foot_box, model_bounds, foot_points, foot_relief, seat_all

UNITS_PER_M = 70.0
STREET_SLOPE_MIN, STREET_SLOPE_MAX = 15.0, 35.0   # degrees: our streets climb no steeper than the source's did
DIRECTIONAL = {"door", "building", "static", "furniture", "activator"}
PATCH_MAX = 105.0          # 1.5 m: the most a patch changes any height point
CLUSTER_NUDGE = [float(v) for v in range(64, 2049, 64)]
NUDGE_STEPS = [64.0, 128.0, 192.0, 256.0, 320.0, 384.0]
PATCH_KINDS = {"building", "static", "furniture", "container", "door", "activator"}
TOOL_FILES = ["run.py", "cluster.py", "fit.py", "seating.py", "paths.py", "clear.py", "interiors.py", "people.py",
              "geom.py", "io.py"]


def tool_key() -> str:
    h = hashlib.sha256()
    here = Path(__file__).parent
    for f in TOOL_FILES + ["../seat.py"]:
        h.update((here / f).read_bytes())
    return h.hexdigest()[:16]


def place_record(place_id: str) -> tuple[dict, list[dict]]:
    from tools.argonia_world import db
    w = db.open("newworld")
    rec = next((dict(vars(r)) if not isinstance(r, dict) else r for r in w.rows("place")
                if (r["id"] if isinstance(r, dict) else r.id) == place_id), None)
    gives = [r if isinstance(r, dict) else dict(vars(r)) for r in w.rows("place_give")]
    gives = [g for g in gives if g.get("place_id") == place_id]
    return rec or {}, gives


def _base_type(b: dict) -> str:
    return str(b.get("type") or "")


def draft(place_id: str, bundles: Path = io.BUNDLES, places: Path = io.PLACES, record: tuple | None = None,
          force: bool = False) -> dict:
    pdir = places / place_id
    pj = pdir / "place.json"
    place = json.loads(pj.read_text())
    dec = place.get("draft") or {}
    src = io.load(f"src.{place['source_id']}", bundles)
    grd = io.load(f"ground.{place_id}", bundles)
    rec, gives = record if record is not None else place_record(place_id)
    key = hashlib.sha256(json.dumps([src.stamp(), grd.stamp(), dec, rec, gives, tool_key()], sort_keys=True,
                                    default=str).encode()).hexdigest()[:16]
    if not force and place.get("draft_key") == key:
        return {"skipped": True, "key": key}
    S = src.ground
    G = Ground.load(grd.path)
    bases = io.place_bases(src, grd, place)
    ext = [r for r in src.exterior.refs]
    by_src = {r["id"]: r for r in ext}
    clusters, of, wild = decompose(ext, bases, S)
    cl_by = {c.id: c for c in clusters}
    sc = Scorer(clusters, S, G)
    anchor = tuple(dec.get("anchor") or (rec.get("world_x", 0.0), rec.get("world_y", 0.0)))
    pivot = fit_pivot(clusters)
    xf = global_fit(sc, pivot, anchor, dec.get("rot_deg"), float(dec.get("search", 4096)))
    fit = local_fit(sc, clusters, xf, {})

    patched_clusters: set[str] = set()

    # --- refs ---
    ledger: list[dict] = []
    replace = {k: (v if isinstance(v, dict) else {"base": v}) for k, v in (dec.get("replace") or {}).items()}
    drop = dec.get("drop") or {}
    our: list[dict] = []
    our_id: dict[str, str] = {}
    for r in sorted(ext, key=lambda r: r["id"]):
        rid = r["id"]
        b = bases.get(r.get("base")) or {}
        if r.get("kind") == "actor":
            continue   # accounted with the people
        why = None
        if rid in drop:
            why = drop[rid]
        elif r.get("kind") == "water":
            why = "the source's water plane; our world's water stands here"
        elif rid in wild:
            why = wild[rid]
        elif rid not in of:
            why = "outside every cluster"
        elif _base_type(b) in LEVELLED:
            why = "levelled (decision 0035)"
        if why is None and b.get("nordic") and r.get("base") not in replace:
            why = "Nordic base (decision 0006); no replacement chosen"
        if why:
            ledger.append({"src": rid, "space": "exterior", "status": "dropped", "why": why})
            continue
        cid = of[rid]
        cx = fit.per[cid]
        seat = seating.infer(r, [by_src[i] for i in cl_by[cid].members], bases, S, False)
        x, y = cx.pt(r["pos"][0], r["pos"][1])
        rot = list(r.get("rot") or [0, 0, 0])
        rot[2] = round(cx.yaw(rot[2]), 5)
        rep = replace.get(r["base"])
        al = None
        if rep:
            al = geom.align(bases.get(r["base"]) or {}, bases.get(rep["base"]) or {}, rep.get("turn_deg")) \
                if r.get("kind") in DIRECTIONAL else None
            orig_yaw = rot[2]
            rot[2] = round((rot[2] + math.radians(al["turn_deg"] if al else float(rep.get("turn_deg", 0))))
                           % (2 * math.pi), 5)
            if al:
                sx, sy = geom.turn(al["shift_local"], orig_yaw)
                x, y = x + sx, y + sy
        row = {"id": io.mint(place_id, "exterior", rid), "base": rep["base"] if rep else r["base"], "kind": r.get("kind"),
               "pos": [round(x, 2), round(y, 2), r["pos"][2]], "rot": rot, "scale": r.get("scale", 1.0),
               "layer": "place", "flags": r.get("flags") or [], "src": rid, "seat": seat, "cluster": cid}
        for k in ("owner", "lock", "door", "linked", "enable_parent", "primitive", "map_marker", "edid"):
            if r.get(k) is not None:
                row[k] = r[k]
        if al:
            row["align"] = {"turn_deg": al["turn_deg"], "shift": [round(sx, 1), round(sy, 1)], "of": r["base"]}
        our_id[rid] = row["id"]
        our.append(row)
        loc = fit.local.get(cid, {})
        moved = abs(loc.get("dx", 0)) + abs(loc.get("dy", 0)) + abs(loc.get("drot_deg", 0)) > 0
        status = "replaced" if r["base"] in replace else ("adapted" if moved or cid in patched_clusters else "placed")
        lrow = {"src": rid, "space": "exterior", "status": status, "as": row["id"], "cluster": cid}
        if status == "replaced":
            lrow["base"] = rep["base"]
        ledger.append(lrow)
    # links to our ids; a supporter or parent left out is let go
    for row in our:
        s = row["seat"]
        if s.get("mode") == "on":
            if s["on"] in our_id:
                s["on"] = our_id[s["on"]]
            else:
                src_r = by_src[row["src"]]
                row["seat"] = seating.infer({**src_r, "kind": "tree"}, [], bases, S, False)   # tree: never `on`
        ep = row.get("enable_parent")
        if ep:
            if ep["ref"] in our_id:
                row["enable_parent"] = {**ep, "ref": our_id[ep["ref"]]}
            elif ep["ref"] in by_src:
                row.pop("enable_parent")     # its parent was left out
        if row.get("linked"):
            row["linked"] = [{**lk, "ref": our_id.get(lk["ref"], lk["ref"])} for lk in row["linked"]
                             if lk.get("ref") in our_id or lk.get("ref") not in by_src]
    # things the place record promises that the source lacks, added by the agent (draft.add)
    for k, a in enumerate(dec.get("add") or []):
        b = bases.get(a["base"]) or {}
        row = {"id": io.mint(place_id, "add", str(k), a["base"]), "base": a["base"], "kind": a.get("kind", "furniture"),
               "pos": [float(a["pos"][0]), float(a["pos"][1]), 0.0], "rot": [0.0, 0.0, float(a.get("rot_z", 0.0))],
               "scale": float(a.get("scale", 1.0)), "layer": "place", "flags": [], "src": None,
               "seat": {"mode": "ground", "dz": float(a.get("dz", 0.0))}, "why": a.get("why", "")}
        f = geom.foot(row, bases)
        if f:
            row["seat"]["foot"] = f
        if not b:
            row["base_unknown"] = True
        our.append(row)
    # --- water and land as our world has them: a thing on the wrong side of the waterline after the fit is
    # nudged to the nearest ground of its kind, or dropped; the land is never turned to water or water to land ---
    gone: dict[str, str] = {}
    lrow_of = {lr.get("as"): lr for lr in ledger if lr["space"] == "exterior"}

    def wrong(row) -> bool:
        if not row.get("src") or row["seat"].get("mode") in ("on", "free", "above") or row.get("kind") not in PATCH_KINDS:
            return False
        r_src = by_src[row["src"]]
        return G.wet(row["pos"][0], row["pos"][1], 16) != S.wet(r_src["pos"][0], r_src["pos"][1], 16)

    # a door never leaves its building: a cluster whose door is on the wrong side moves whole
    by_cluster: dict[str, list[dict]] = {}
    for row in our:
        by_cluster.setdefault(row.get("cluster"), []).append(row)
    for cid, rows in sorted(by_cluster.items(), key=lambda kv: str(kv[0])):
        if not any(r.get("kind") == "door" and wrong(r) for r in rows):
            continue
        best = None
        for d in [0.0] + CLUSTER_NUDGE:
            for k in range(16):
                dx, dy = d * math.cos(k * math.pi / 8), d * math.sin(k * math.pi / 8)
                for r in rows:
                    r["pos"][0] += dx
                    r["pos"][1] += dy
                bad_doors = sum(1 for r in rows if r.get("kind") == "door" and wrong(r))
                n = sum(1 for r in rows if wrong(r))
                for r in rows:
                    r["pos"][0] -= dx
                    r["pos"][1] -= dy
                key = (bad_doors, n, d)
                if best is None or key < best[0]:
                    best = (key, dx, dy)
                if d == 0.0:
                    break
            if best[0][:2] == (0, 0):
                break
        _, dx, dy = best
        for r in rows:
            r["pos"][0], r["pos"][1] = round(r["pos"][0] + dx, 2), round(r["pos"][1] + dy, 2)
            lr = lrow_of[r["id"]]
            if lr["status"] == "placed" and (dx or dy):
                lr["status"] = "adapted"
        fit.local.setdefault(cid, {})["nudge"] = [round(dx, 1), round(dy, 1)]
    for row in sorted(our, key=lambda r: r["id"]):
        if not row.get("src") or row["seat"].get("mode") in ("on", "free", "above") or row.get("kind") not in PATCH_KINDS:
            continue
        r_src = by_src[row["src"]]
        want = S.wet(r_src["pos"][0], r_src["pos"][1], 16)
        x, y = row["pos"][0], row["pos"][1]
        if G.wet(x, y, 16) == want:
            continue
        spot = next(((x + d * math.cos(a), y + d * math.sin(a)) for d in NUDGE_STEPS
                     for a in (k * math.pi / 4 for k in range(8)) if G.wet(x + d * math.cos(a), y + d * math.sin(a), 16) == want
                     and G.has(x + d * math.cos(a), y + d * math.sin(a))), None)
        lr = lrow_of[row["id"]]
        if spot:
            row["pos"][0], row["pos"][1] = round(spot[0], 2), round(spot[1], 2)
            lr["status"] = "adapted" if lr["status"] == "placed" else lr["status"]
            lr["nudge"] = round(geom.dist((x, y), spot), 1)
        else:
            gone[row["id"]] = (f"no {'water' if want else 'dry land'} within {NUDGE_STEPS[-1]:.0f} units of its fitted spot;"
                               " our water and land are kept as they are")
    # what stood on a dropped thing goes with it
    changed = True
    while changed:
        changed = False
        for row in our:
            if row["id"] not in gone and row["seat"].get("on") in gone:
                gone[row["id"]] = "stood on a thing that was dropped"
                changed = True
    for row in our:
        if row["id"] in gone:
            lr = lrow_of[row["id"]]
            lr.update({"status": "dropped", "why": gone[row["id"]]})
            lr.pop("as", None)
    our = [r for r in our if r["id"] not in gone]
    our_id = {k: v for k, v in our_id.items() if v not in gone}
    for row in our:
        if (row.get("enable_parent") or {}).get("ref") in gone:
            row.pop("enable_parent")
        if row.get("linked"):
            row["linked"] = [lk for lk in row["linked"] if lk.get("ref") not in gone]

    # --- land patches, the last resort: only to ease the ground under a building, bounded, never across the
    # waterline ---
    sums: dict[tuple, dict] = {}
    norm = relief_norm(S, ext, bases)
    if dec.get("keep_patches", True):
        for row in sorted((r for r in our if r.get("kind") == "building" and r.get("src")), key=lambda r: r["id"]):
            f = row["seat"].get("foot")
            if not f or row["seat"].get("mode") != "ground":
                continue
            r_src = by_src[row["src"]]
            src_rel = foot_relief(S, r_src["pos"][0], r_src["pos"][1], r_src["rot"][2], f)
            need = patch_for(G, S, r_src, row["pos"][0], row["pos"][1], row["rot"][2], f, row["kind"],
                             src_rel, "relief", row["seat"], norm)
            if not need:
                continue
            target, why = need
            verts = patch_verts(G, row["pos"][0], row["pos"][1], row["rot"][2], f, target, PATCH_MAX)
            if not verts:
                continue
            G.apply_patches([{"cell": list(k), "verts": v} for k, v in verts.items()])
            label = f"{row.get('cluster')} {row['base']}: {why}"
            lr = lrow_of[row["id"]]
            if lr["status"] == "placed":
                lr["status"] = "adapted"
            lr["patch"] = why
            for cell, vs in verts.items():
                c = sums.setdefault(cell, {"verts": {}, "why": []})
                for rr, cc, dz in vs:
                    c["verts"][(rr, cc)] = round(c["verts"].get((rr, cc), 0.0) + dz, 1)
                if label not in c["why"]:
                    c["why"].append(label)
    land = [{"cell": list(cell), "verts": [[k[0], k[1], v] for k, v in sorted(c["verts"].items()) if abs(v) >= 1],
             "why": "; ".join(c["why"]), "by": "draft"} for cell, c in sorted(sums.items())]
    seat_all(our, G)

    # --- interiors ---
    ext_doors = [by_src[r["src"]] for r in our if r.get("door") and r["door"].get("to_space") in src.spaces
                 and r["door"]["to_space"] != "exterior"]
    spaces = interiors.plan(place_id, src, ext_doors, our_id)
    our_by_id = {r["id"]: r for r in our}
    for sid, sp in spaces.items():
        if sp["parent"] == "exterior":
            row = our_by_id[sp["door_from"]]
            row["door"] = {**row["door"], "to_space": sid, "to_ref": sp["door_back"]}
    copies: dict[str, list[str]] = {}
    for sid, sp in spaces.items():
        copies.setdefault(sp["src_space"], []).append(sid)
    for sp_id, sp in sorted(src.spaces.items()):
        if sp_id == "exterior":
            continue
        if sp_id in copies:
            # a copied space is accounted whole: every ref but its actors comes across in each copy
            ledger.append({"src": "*", "space": sp_id, "status": "placed", "as": sorted(copies[sp_id]),
                           "count": sum(1 for r in sp.refs if r.get("kind") != "actor")})
            continue
        for r in sp.refs:
            ledger.append({"src": r["id"], "space": sp_id, "status": "dropped",
                           "why": "its interior is not reached by any placed door"})

    # --- paths ---
    def front(src_door: dict) -> tuple[float, float]:
        """Where one stands outside a door: the source's own arrival marker when the interior has it."""
        t = src_door["door"].get("to_space")
        sp = src.spaces.get(t)
        if sp:
            for r in sp.refs:
                d = r.get("door") or {}
                tp = d.get("to_pos")
                if d.get("to_ref") == src_door["id"] and tp and geom.dist(tp, src_door["pos"]) < 512:
                    return (tp[0], tp[1])
        rz = src_door.get("rot", [0, 0, 0])[2]
        return (src_door["pos"][0] - 128 * math.sin(rz), src_door["pos"][1] - 128 * math.cos(rz))

    our_row_of_src = {r["src"]: r for r in our if r.get("src")}

    def to_ours(src_ref_id: str, p) -> tuple[float, float]:
        """A source point near a placed ref, taken with that ref as it was finally placed (fit, then any nudge)."""
        row = our_row_of_src[src_ref_id]
        xf = fit.per[row["cluster"]]
        m, at = xf.pt(*p), xf.pt(*by_src[src_ref_id]["pos"][:2])
        return (m[0] + row["pos"][0] - at[0], m[1] + row["pos"][1] - at[1])

    nodes_src, nodes_our = {}, {}
    for d in ext_doors:
        f = front(d)
        nodes_src[d["id"]] = f
        nodes_our[d["id"]] = to_ours(d["id"], f)
    landing = next((c for c in clusters if c.kind == "landing"), None)
    if landing:
        # the landing's shore end: from its member nearest the town, walk towards the town until dry land
        cand = [by_src[i] for i in landing.members if by_src[i].get("kind") not in VEG and i in our_row_of_src]
        first = min(cand, key=lambda r: (geom.dist(r["pos"], pivot), r["id"]))
        start = first["pos"]
        d = geom.dist(start, pivot) or 1.0
        ux, uy = (pivot[0] - start[0]) / d, (pivot[1] - start[1]) / d
        land_src = (start[0], start[1])
        for k in range(int(d // 64)):
            p = (start[0] + ux * 64 * k, start[1] + uy * 64 * k)
            if not S.wet(*p):
                land_src = p
                break
        nodes_src["landing"] = land_src
        q = to_ours(first["id"], land_src)
        # on our side too, the shore end stands on dry ground
        q = next(((q[0] + r * math.cos(t), q[1] + r * math.sin(t)) for r in [0.0] + NUDGE_STEPS * 2
                  for t in (k * math.pi / 8 for k in range(16)) if not G.wet(q[0] + r * math.cos(t), q[1] + r * math.sin(t), 16)), q)
        nodes_our["landing"] = q

    # the source's streets: its painted roads, its walkways, its navmesh's preferred paths
    paint = paths_mod.road_points(src.exterior.path)
    paint_grid = {(round(x / 128), round(y / 128)) for x, y in paint}
    walk_src = [r for r in ext if r.get("kind") in ("building", "static") and paths_mod.WALKWAY.search(
        str((bases.get(r["base"]) or {}).get("model", "")))]
    prefer = {(int(x // 128), int(y // 128)) for x, y in paint}
    for r in walk_src:
        for x, y in foot_points(r["pos"][0], r["pos"][1], r["rot"][2], geom.foot(r, bases), 5):
            prefer.add((int(x // 128), int(y // 128)))
    nav = NavGraph(src.exterior.navmesh, prefer)
    edges = network(nodes_src, nav)
    max_slope = max(STREET_SLOPE_MIN, min(STREET_SLOPE_MAX, sorted(
        [paths_mod.route_slope(S, simplify(pts, 32)) for _, _, pts in edges] or [STREET_SLOPE_MIN])[
        int(0.9 * (len(edges) - 1)) if edges else 0] + 5))
    # where our streets may not go: water with no walkway of ours over it, inside a building
    walk_our = [r for r in our if r.get("src") in {w["id"] for w in walk_src}]
    blocked_cells: set = set()
    for r in our:
        f = geom.foot(r, bases)
        if r.get("kind") == "building" and f and r not in walk_our:
            rad = geom.reach(r, bases)
            for i in range(round((r["pos"][0] - rad - 80) / 128), round((r["pos"][0] + rad + 80) / 128) + 1):
                for j in range(round((r["pos"][1] - rad - 80) / 128), round((r["pos"][1] + rad + 80) / 128) + 1):
                    if geom.contains_xy(r, bases, i * 128.0, j * 128.0, 80):
                        blocked_cells.add((i, j))
    walk_cells: set = set()
    for r in walk_our:
        x0, y0, x1, y1 = foot_box(geom.foot(r, bases) or [64.0, 64.0])
        for x, y in foot_points(r["pos"][0], r["pos"][1], r["rot"][2], [x0 - 64, y0 - 64, x1 + 64, y1 + 64], 7):
            walk_cells.add((round(x / 128), round(y / 128)))

    def blocked(x, y) -> bool:
        k = (round(x / 128), round(y / 128))
        return k in blocked_cells or (G.wet(x, y, 8) and k not in walk_cells)
    bridges: list[dict] = []
    walk_base = None
    if walk_src:
        counts: dict[str, int] = {}
        for r in walk_src:
            kb = (replace.get(r["base"]) or {}).get("base", r["base"])
            if not (bases.get(kb) or {}).get("nordic") and geom.foot({"base": kb, "kind": "building"}, bases):
                counts[kb] = counts.get(kb, 0) + 1
        walk_base = max(sorted(counts), key=lambda kb: counts[kb]) if counts else None

    def bridge_over(route, k) -> list[dict]:
        """Walkway pieces end to end over each wet stretch of a route, along it, standing on stilts."""
        if not walk_base:
            return []
        b = model_bounds(bases[walk_base])
        length = max(64.0, b[1][1] - b[0][1] - 16)
        out = []
        for i, (p, q) in enumerate(zip(route, route[1:])):
            seg = geom.dist(p, q)
            n = max(1, int(seg // length) + 1)
            yaw = math.atan2(q[0] - p[0], q[1] - p[1]) % (2 * math.pi)
            for j in range(n):
                x = p[0] + (q[0] - p[0]) * (j + 0.5) / n
                y = p[1] + (q[1] - p[1]) * (j + 0.5) / n
                if not G.wet(x, y, 8):
                    continue
                out.append({"id": io.mint(place_id, "bridge", str(k), str(i), str(j)), "base": walk_base,
                            "kind": "building", "pos": [round(x, 2), round(y, 2), 0.0], "rot": [0.0, 0.0, round(yaw, 5)],
                            "scale": 1.0, "layer": "place", "flags": [], "src": None,
                            "seat": {"mode": "stilts", "dz": 0.0, "foot": geom.foot({"base": walk_base,
                                                                                    "kind": "building"}, bases)},
                            "why": f"carries street {k + 1:02d} over our water, which parts what the source's land joined"})
        return out

    # a door that opens onto the water (on a ship or a pier) is reached over the source's own walkways from the
    # landing, not by a street: its link is laid as the source's line and marked a walkway
    afloat = {n for n, p in nodes_our.items() if n != "landing" and G.wet(p[0], p[1], 16)}
    paths_src, paths_our = [], []
    for k, (a, b, pts) in enumerate(edges):
        if a in afloat or b in afloat:
            line = [nodes_our[a]] + [fit.warp(*p) for p in simplify(pts, 32)[1:-1]] + [nodes_our[b]]
            paths_src.append({"points": [list(p) for p in pts], "width": PATH_WIDTH})
            paths_our.append({"id": f"{place_id}.path.{k + 1:02d}", "kind": "walkway",
                              "points": [[round(p[0], 1), round(p[1], 1)] for p in line], "width": PATH_WIDTH,
                              "style": "boardwalk", "from": a, "to": b, "laid": "the source's walkway, mapped"})
            continue
        street = sum(nav.pref[nav.nearest(p)] for p in pts[1:-1]) * 2 >= max(1, len(pts) - 2) if nav else True
        width = paths_mod.width_from_paint(pts, paint_grid, STREET_WIDTH if street else PATH_WIDTH)
        guide = [nodes_our[a]] + [fit.warp(*p) for p in simplify(pts, 32)[1:-1]] + [nodes_our[b]]
        routed = paths_mod.astar(G, nodes_our[a], nodes_our[b], blocked, max_slope, guide)
        if routed is None:
            # our water parts what the source's land joined: cross it, and carry the street on the source's own
            # walkway pieces (a bridge the place needs that the source lacks, in the source's style)
            routed = paths_mod.astar(G, nodes_our[a], nodes_our[b], lambda x, y: (round(x / 128), round(y / 128))
                                     in blocked_cells, max_slope, guide)
            if routed:
                bridges.extend(bridge_over(routed, k))
        laid = simplify([(round(p[0], 1), round(p[1], 1)) for p in (routed or guide)], 24)
        wet = sum(1 for p in laid if G.wet(*p)) > len(laid) / 2
        paths_src.append({"points": [list(p) for p in pts], "width": width})
        paths_our.append({"id": f"{place_id}.path.{k + 1:02d}", "kind": "street" if street else "path",
                          "points": [list(p) for p in laid], "width": width,
                          "style": "boardwalk" if wet else "dirt", "from": a, "to": b,
                          "laid": "routed on our ground" if routed else "the source's line, mapped"})

    # --- doors: where one arrives outside each door, on our ground, and which way the door opens ---
    our_by_id = {r["id"]: r for r in our}
    needs_look: list[dict] = []
    for sid, sp in sorted(spaces.items()):
        if sp["parent"] != "exterior":
            continue
        ext_door = our_by_id[sp["door_from"]]
        p = nodes_our.get(ext_door["src"])
        back = next((r for r in sp["overrides"] if r["id"] == sp["door_back"]), None)
        if p is None or back is None:
            continue
        # one arrives on dry ground clear of any other building: step out along the way out, then round it
        def clear(q):
            return G.has(*q) and (not G.wet(q[0], q[1], 16) or G.wet(ext_door["pos"][0], ext_door["pos"][1], 16)) \
                and not any(r.get("kind") == "building" and geom.contains_xy(r, bases, q[0], q[1], -32)
                            and not geom.contains_xy(r, bases, ext_door["pos"][0], ext_door["pos"][1], 64) for r in our)
        if not clear(p):
            d0 = math.dist(p, ext_door["pos"][:2]) or 1.0
            ux, uy = (p[0] - ext_door["pos"][0]) / d0, (p[1] - ext_door["pos"][1]) / d0
            cands = [(ext_door["pos"][0] + ux * r_, ext_door["pos"][1] + uy * r_) for r_ in (96.0, 160.0, 224.0, 288.0, 384.0)]
            cands += [(p[0] + r_ * math.sin(t), p[1] + r_ * math.cos(t)) for r_ in (64.0, 128.0, 192.0, 256.0)
                      for t in (k * math.pi / 8 for k in range(16))]
            p = next((q for q in cands if clear(q)), p)
            nodes_our[ext_door["src"]] = p
        h = G.height(*p)
        out_yaw = math.atan2(p[0] - ext_door["pos"][0], p[1] - ext_door["pos"][1]) % (2 * math.pi)
        arrival = [round(p[0], 2), round(p[1], 2), round(h if h is not None else ext_door["pos"][2], 2)]
        back["door"] = {**back["door"], "to_pos": arrival, "to_rot": [0.0, 0.0, round(out_yaw, 5)]}
        ext_door["door"] = {**ext_door["door"], "arrival": arrival}
        if ext_door.get("align"):
            needs_look.append({"door": ext_door["id"], "src": ext_door["src"], "base": ext_door["base"],
                               "space": sid, "at": arrival[:2],
                               "why": "replacement door: its plane is matched to the original's and one arrives on "
                                      "the original's outer side, but which face of the new mesh is its front "
                                      "cannot be read from the geometry; look that the door does not open inward"})

    if bridges:
        our.extend(bridges)
        walk_cells.update((round(r["pos"][0] / 128), round(r["pos"][1] / 128)) for r in bridges)
        seat_all(our, G)

    # --- vegetation clearance ---
    src_buildings = [r for r in ext if r.get("kind") == "building"]
    src_veg = [r for r in ext if r.get("kind") in clearmod.CLEARED_KINDS]
    clearance = clearmod.measure(src_veg, src_buildings, bases, paths_src, list(nodes_src.values()))
    our_buildings = [r for r in our if r.get("kind") == "building"]
    footprints = [r for r in our if geom.foot(r, bases) and r.get("kind") not in VEG]
    world = [r for r in (grd.exterior.refs if grd.exterior else []) if r.get("layer", "world") == "world"]
    clear_rows = clearmod.apply(world, clearance, our_buildings, bases, paths_our, list(nodes_our.values()), footprints)

    # --- people ---
    folk, factions, stations = draft_people(place_id, rec, gives, src, bases, our, spaces, clusters, fit, of,
                                            nodes_our, paths_our, dec, ledger, G)
    seat_all(our, G)

    # --- write ---
    io.write_jsonl(pdir / "spaces" / "exterior" / "refs.jsonl", our)
    for sid, sp in sorted(spaces.items()):
        sdir = pdir / "spaces" / sid
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "space.json").write_text(json.dumps({"space_id": sid, "copy_of": sp["copy_of"], "name": sp["name"],
                                                     "door_from": sp["door_from"], "parent": sp["parent"],
                                                     "room": sp["room"]},
                                                    indent=1) + "\n")
        io.write_jsonl(sdir / "refs.jsonl", sp["overrides"])
    # spaces no longer drafted are removed
    for old in (pdir / "spaces").iterdir():
        if old.is_dir() and old.name != "exterior" and old.name not in spaces:
            for f in old.iterdir():
                f.unlink()
            old.rmdir()
    io.write_jsonl(pdir / "land.jsonl", land)
    io.write_jsonl(pdir / "clear.jsonl", clear_rows)
    io.write_jsonl(pdir / "paths.jsonl", paths_our)
    io.write_jsonl(pdir / "people.jsonl", folk)
    io.write_jsonl(pdir / "ledger.jsonl", sorted(ledger, key=lambda r: (r["space"], r["src"])))
    centre = fit.xf.to
    reach = max((geom.dist(r["pos"], centre) + geom.radius(r, bases) for r in our if r.get("kind") not in VEG),
                default=0.0)
    radius_m = int(math.ceil(reach / UNITS_PER_M / 5.0) * 5)
    counts = {
        "source_refs": len(ledger),
        "placed": sum(1 for r in ledger if r["status"] == "placed"),
        "adapted": sum(1 for r in ledger if r["status"] == "adapted"),
        "replaced": sum(1 for r in ledger if r["status"] == "replaced"),
        "dropped": sum(1 for r in ledger if r["status"] == "dropped"),
        "exterior_refs": len(our), "clusters": len(clusters), "land_patches": len(land), "plants_cleared": len(clear_rows),
        "paths": len(paths_our), "interiors": len(spaces),
        "people": {k: sum(1 for p in folk if p["role"] == k) for k in sorted({p["role"] for p in folk})},
        "beds": sum(b["sleeps"] for sp in spaces.values() for b in interiors.beds_in(
            src.spaces[sp["src_space"]].refs, bases, sp["room"])),
    }
    place.update({
        "fit": {**fit.as_dict(), "clusters_info": [c.as_dict() for c in clusters], "relief_norm": norm,
                "patch_max": PATCH_MAX},
        "clearance": clearance,
        "factions": factions,
        "stations": stations,
        "needs_look": needs_look,
        "ground": {"bundle": f"ground.{place_id}", "sha": G.sha, "stamp": grd.stamp()},
        "source": {"bundle": f"src.{place['source_id']}", "stamp": src.stamp()},
        "radius_m": radius_m,
        "counts": counts,
        "draft_key": key,
    })
    pj.write_text(json.dumps(place, indent=1, ensure_ascii=False) + "\n")
    return counts


def draft_people(place_id, rec, gives, src, bases, our, spaces, clusters, fit, of, nodes_our, paths_our, dec, ledger, G):
    roles_override = dec.get("roles") or {}
    # beds of each copy
    slots: dict[str, list[dict]] = {}
    for sid, sp in sorted(spaces.items()):
        for b in interiors.beds_in(src.spaces[sp["src_space"]].refs, bases, sp["room"]):
            for k in range(b["sleeps"]):
                slots.setdefault(sid, []).append({"space": sid, "ref": b["ref"], "slot": k})
    shared = {sp["src_space"] for sp in spaces.values() if sum(1 for o in spaces.values()
                                                             if o["src_space"] == sp["src_space"]) > 1}
    houses = sorted((sid for sid, sp in spaces.items() if sp["src_space"] in shared
                     or re.search(r"house|home|hut|shack", f"{sid} {sp.get('name') or ''}", re.I)), key=str)
    halls = sorted((sid for sid in spaces if sid not in houses), key=lambda s: (-len(slots.get(s, [])), s))
    free = {sid: list(v) for sid, v in slots.items()}

    def take(sid):
        return free[sid].pop(0) if free.get(sid) else None

    # source actors and the bases they offer
    actors = []
    for sp_id, sp in sorted(src.spaces.items()):
        for r in sp.refs:
            if r.get("kind") == "actor" and r.get("base") in src.npcs:
                actors.append((sp_id, r))
    used_bases: dict[str, int] = {}

    def pick_base(role: str) -> str | None:
        cands = sorted({r["base"] for _, r in actors if people.usable(src.npcs[r["base"]])})
        if not cands:
            return None
        best = max(cands, key=lambda k: (people.role_score(src.npcs[k], role), -used_bases.get(k, 0), k))
        used_bases[best] = used_bases.get(best, 0) + 1
        return best

    centre = fit.xf.to
    town = {"space": "exterior", "pos": [round(centre[0], 1), round(centre[1], 1)], "radius": 1024}
    door_fronts = sorted(nodes_our.items(), key=lambda kv: kv[0])
    building_doors = [(k, v) for k, v in door_fronts if k != "landing"]
    used_fronts: set[str] = set()
    stations_need = sorted({g["give_kind_id"] for g in gives if g["give_kind_id"] in people.STATIONS})
    found: dict[str, list[str]] = {}
    for st in stations_need:
        pat = re.compile(io.STATION_EDID[st], re.I)
        found[st] = sorted(r["id"] for r in our if pat.search(str((bases.get(r["base"]) or {}).get("edid", ""))))
    stations = {"needed": stations_need, "found": found,
                "missing": [s for s in stations_need if not found[s]]}

    folk: list[dict] = []
    taken_names: set[str] = set()
    crime = f"{place_id}.crime"
    factions = [{"id": crime, "kind": "crime", "name": rec.get("name"), "jail": None},
                {"id": f"{place_id}.guard", "kind": "guard", "crime": crime},
                {"id": f"{place_id}.town", "kind": "town", "crime": crime}]
    # the inn: the hall with the most beds that no source trader keeps as a shop
    shops = {sp_id for sp_id, r in actors if people.usable(src.npcs[r["base"]]) and any(
        people.role_score(src.npcs[r["base"]], ro) >= 2 for ro in ("merchant", "smith", "apothecary", "spell-trader"))}
    inn_space = next((h for h in halls if spaces[h]["src_space"] not in shops), halls[0] if halls else None)
    copies_of: dict[str, list[str]] = {}
    for sid_, sp_ in sorted(spaces.items()):
        copies_of.setdefault(sp_["src_space"], []).append(sid_)
    our_by_id = {r["id"]: r for r in our}
    indoor_free = list(halls)

    def work_for(role: str, n: int) -> dict:
        o = roles_override.get(role)
        if o:
            return {"space": o.get("space", "exterior"), **({"pos": o["pos"]} if o.get("pos") else {}), "radius": 512}
        if role == "boatman" and "landing" in nodes_our:
            p = nodes_our["landing"]
            return {"space": "exterior", "pos": [round(p[0], 1), round(p[1], 1)], "radius": 384}
        # where the source's own person of this trade worked (Bethesda places a trader in their shop)
        for sp_id, r in actors:
            n_ = src.npcs[r["base"]]
            if people.usable(n_) and people.role_score(n_, role) >= 2 and sp_id != "exterior" and copies_of.get(sp_id):
                sid = copies_of[sp_id][0]
                if role in people.OUTDOOR_WORK:
                    # a smith works the yard outside the shop's door
                    door = spaces[sid]["door_from"]
                    src_door = next((k for k in nodes_our if our_by_id.get(door, {}).get("src") == k), None)
                    if src_door:
                        p = nodes_our[src_door]
                        return {"space": "exterior", "pos": [round(p[0], 1), round(p[1], 1)], "radius": 384}
                if sid in indoor_free:
                    indoor_free.remove(sid)
                return {"space": sid, "radius": 1024}
        if role in people.INDOOR and indoor_free:
            others = [i for i in indoor_free if i != inn_space] or indoor_free
            sid = inn_space if role == "innkeeper" and inn_space in indoor_free else others[0]
            indoor_free.remove(sid)
            return {"space": sid, "radius": 1024}
        if role == "smith" and stations["found"].get("forge"):
            r = next(x for x in our if x["id"] == stations["found"]["forge"][0])
            return {"space": "exterior", "ref": r["id"], "radius": 512}
        for k, p in building_doors:
            if k not in used_fronts and not G.wet(p[0], p[1], 16):
                used_fronts.add(k)
                return {"space": "exterior", "pos": [round(p[0], 1), round(p[1], 1)], "radius": 384}
        return town

    def bed_for(prefer: list[str]) -> dict | None:
        for sid in prefer:
            s = take(sid)
            if s:
                return s
        return None

    def station_used(ref_id: str, w: dict) -> bool:
        row = next((r for r in our if r["id"] == ref_id), None)
        if row is None or w.get("space", "exterior") != "exterior":
            return False
        c = w.get("pos") or next((r["pos"] for r in our if r["id"] == w.get("ref")), None)
        return c is not None and geom.dist(row["pos"], c) <= w.get("radius", 384) + 256

    services = people.service_people(gives)
    free_houses = list(houses)
    for n, sp in enumerate(services):
        role = sp["role"]
        work = work_for(role, n)
        home = None
        if role == "innkeeper" and work.get("space") in slots:
            home = work["space"]
        elif free_houses:
            home = free_houses.pop(0)
        if role in people.NO_BED:
            bed, home = None, work.get("space") if work.get("space") != "exterior" else home
        else:
            bed = bed_for([home] if home else []) or bed_for(houses + halls)
            home = bed["space"] if bed else home
        pid = io.mint(place_id, "person", role, str(n))
        bed_at = {"space": bed["space"], "ref": bed["ref"], "radius": 128} if bed else town
        eat = {"space": home, "radius": 1024} if home else town
        wander = {"space": inn_space, "radius": 1024} if inn_space and role != "innkeeper" else town
        services_ids = [g["kind"] for g in sp["gives"]]
        fr = [{"faction": crime, "rank": 0}, {"faction": f"{place_id}.town", "rank": 0}]
        if any(k.startswith("trader-") or k == "inn-room" for k in services_ids):
            vid = f"{place_id}.vendor.{n + 1:02d}"
            factions.append({"id": vid, "kind": "vendor", "crime": crime, "hours": list(people.SERVICE_HOURS),
                             "sells": sorted(k for k in services_ids if k.startswith("trader-")), "chest": True,
                             "person": pid})
            fr.append({"faction": vid, "rank": 0})
        folk.append({"id": pid, "name": people.placeholder_name(pid, taken_names), "base_from": pick_base(role),
                     "role": role, "home": home, "bed": bed_at if bed else None, "work": work,
                     "services": sp["gives"], "faction_ranks": fr,
                     "routine": people.routine(role, bed_at, work, eat, wander)})
    # the crafting stations the record promises and the source lacks, by the person who works them, the way
    # Skyrim's towns set them (town-life.md): the smith's yard, the apothecary's lab, the enchanter with the spell
    # trader, the cooking pot at the inn
    added = []
    for st in stations_need:
        role = people.STATION_OWNER.get(st)
        owner = next((p for p in folk if p["role"] == role), None) or next((p for p in folk if p["role"] != "guard"), None)
        if owner is None:
            continue
        w = owner["work"]
        used = [i for i in found[st] if station_used(i, w)]
        if used:
            continue
        b = io.station_base(st)
        if b is None:
            continue
        bases[b["key"]] = b
        k = sum(1 for a in added if a["by"] == owner["id"])
        if w.get("space", "exterior") == "exterior":
            c = w.get("pos") or next(r["pos"] for r in our if r["id"] == w.get("ref"))
            spot = None
            for ring in (224.0, 320.0, 416.0, 512.0, 640.0, 768.0, 1024.0, 1280.0, 1536.0):
                for j in range(12):
                    t = (k * 2 + j) * math.pi / 6
                    q = (c[0] + ring * math.sin(t), c[1] + ring * math.cos(t))
                    if G.has(*q) and not G.wet(q[0], q[1], 16) and not any(
                            r.get("kind") == "building" and geom.contains_xy(r, bases, q[0], q[1], 48) for r in our):
                        spot = (q, t)
                        break
                if spot:
                    break
            if spot is None:
                continue
            (qx, qy), t = spot
            row = {"id": io.mint(place_id, "station", st), "base": b["key"], "kind": "furniture",
                   "pos": [round(qx, 2), round(qy, 2), 0.0], "rot": [0.0, 0.0, round((t + math.pi) % (2 * math.pi), 5)],
                   "scale": 1.0, "layer": "place", "flags": [], "src": None,
                   "seat": {"mode": "ground", "dz": 0.0, **({"foot": geom.foot({"base": b["key"], "kind": "furniture"},
                                                                                bases)} if geom.foot(
                       {"base": b["key"], "kind": "furniture"}, bases) else {})},
                   "why": f"{st}: promised by the place record ({owner['role']}'s work), lacking in the source"}
            our.append(row)
            space = "exterior"
        else:
            space = w["space"]
            sp = spaces[space]
            src_refs = src.spaces[sp["src_space"]].refs
            beds = interiors.beds_in(src_refs, bases, sp["room"])
            anchor_ids = {b_["ref"] for b_ in beds} or {sp.get("room")}
            pts = [r["pos"] for r in src_refs if r["id"] in anchor_ids] or [src_refs[0]["pos"]]
            cx_ = sum(p[0] for p in pts) / len(pts) + 128 * (k + 1)
            cy_ = sum(p[1] for p in pts) / len(pts)
            row = {"id": io.mint(place_id, "station", st), "base": b["key"], "kind": "furniture",
                   "pos": [round(cx_, 2), round(cy_, 2), round(min(p[2] for p in pts), 2)], "rot": [0.0, 0.0, 0.0],
                   "scale": 1.0, "layer": "place", "flags": [], "src": None, "seat": {"mode": "free"},
                   "why": f"{st}: promised by the place record ({owner['role']}'s work), lacking in the source"}
            sp["overrides"].append(row)
        if space == "exterior" and (st == "forge" or not station_used(row["id"], w)):
            # the worker's stop is the station (the forge for a smith; a lab that had to stand further off)
            w.pop("pos", None)
            w["ref"] = row["id"]
        added.append({"station": st, "id": row["id"], "base": b["key"], "space": space, "by": owner["id"]})
        found[st].append(row["id"])
    stations["added"] = added
    stations["missing"] = [s_ for s_ in stations_need if not found[s_]]

    # guards: patrol the streets in two shifts
    # each guard walks streets end to end and back, never cutting across: the day and night guard of a pair share
    # a beat (Whiterun's patrol chains run along its streets, town-life.md)
    beats = [[[round(q[0], 1), round(q[1], 1)] for q in p["points"]] for p in
             sorted(paths_our, key=lambda p: -sum(geom.dist(a, b) for a, b in zip(p["points"], p["points"][1:])))]
    n_guards = people.guard_count(sum(1 for c in clusters if c.kind == "building"))
    for k in range(n_guards):
        shift = "day" if k % 2 == 0 else "night"
        bed = bed_for(halls + houses)
        pid = io.mint(place_id, "person", "guard", str(k))
        beat = beats[(k // 2) % len(beats)] if beats else []
        pts = beat + beat[-2:0:-1]
        work = {"space": "exterior", "pos": pts[0] if pts else town["pos"], "radius": 256}
        bed_at = {"space": bed["space"], "ref": bed["ref"], "radius": 128} if bed else town
        folk.append({"id": pid, "name": people.placeholder_name(pid, taken_names), "base_from": pick_base("guard"),
                     "role": "guard", "shift": shift, "home": bed["space"] if bed else None,
                     "bed": bed_at if bed else None, "work": work, "services": [],
                     "faction_ranks": [{"faction": crime, "rank": 0}, {"faction": f"{place_id}.guard", "rank": 0}],
                     "patrol": {"points": pts, "loop": True},
                     "routine": people.routine("guard", bed_at, work, {"space": bed["space"] if bed else "exterior",
                                                                      "radius": 1024}, town, shift)})
    # residents fill the beds left in the homes
    n = 0
    for sid in houses:
        while free.get(sid):
            bed = take(sid)
            pid = io.mint(place_id, "person", "resident", str(n))
            bed_at = {"space": sid, "ref": bed["ref"], "radius": 128}
            folk.append({"id": pid, "name": people.placeholder_name(pid, taken_names),
                         "base_from": pick_base("resident"), "role": "resident", "home": sid, "bed": bed_at,
                         "work": town, "services": [], "faction_ranks": [{"faction": crime, "rank": 0},
                                                                          {"faction": f"{place_id}.town", "rank": 0}],
                         "routine": people.routine("resident", bed_at, town, {"space": sid, "radius": 1024},
                                                   {"space": inn_space, "radius": 1024} if inn_space else town)})
            n += 1
    # the source's own actors: stand-ins for ours, or left to the town rule
    base_users: dict[str, list[str]] = {}
    for p in folk:
        if p["base_from"]:
            base_users.setdefault(p["base_from"], []).append(p["id"])
    for sp_id, r in actors:
        if r["base"] in base_users:
            ledger.append({"src": r["id"], "space": sp_id, "status": "replaced", "as": base_users[r["base"]]})
        else:
            ledger.append({"src": r["id"], "space": sp_id, "status": "dropped",
                           "why": "people come from the place record's promises, the guards and the beds"})
    return folk, factions, stations
