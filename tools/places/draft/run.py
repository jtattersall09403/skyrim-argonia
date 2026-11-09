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
from tools.places.draft.geom import LEVELLED
from tools.places.draft.cluster import VEG, decompose
from tools.places.draft.fit import Scorer, global_fit, local_fit, patch_for, patch_verts
from tools.places.draft.fit import _pivot as fit_pivot
from tools.places.draft.paths import PATH_WIDTH, STREET_WIDTH, NavGraph, network, simplify
from tools.places.seat import Ground, foot_relief, seat_all

UNITS_PER_M = 70.0
PATCH_ROUNDS = 3
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
    bases = io.place_bases(src, grd, place.get("draft") or {})
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
        if rep:
            rot[2] = round((rot[2] + math.radians(float(rep.get("turn_deg", 0)))) % (2 * math.pi), 5)
        row = {"id": io.mint(place_id, "exterior", rid), "base": rep["base"] if rep else r["base"], "kind": r.get("kind"),
               "pos": [round(x, 2), round(y, 2), r["pos"][2]], "rot": rot, "scale": r.get("scale", 1.0),
               "layer": "place", "flags": r.get("flags") or [], "src": rid, "seat": seat, "cluster": cid}
        for k in ("owner", "lock", "door", "linked", "enable_parent", "primitive", "map_marker", "edid"):
            if r.get(k) is not None:
                row[k] = r[k]
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
    # --- land patches, the last resort: what the fit could not settle, thing by thing ---
    sums: dict[tuple, dict] = {}
    patched: dict[str, str] = {}
    if dec.get("keep_patches", True):
        # water and land first, then the ground under buildings, so a level floor is never undercut after
        cand = [r for r in our if r.get("src") and r["seat"].get("mode") not in ("on", "free")
                and r.get("kind") in PATCH_KINDS]
        one = [(r, "wet") for r in sorted(cand, key=lambda r: r["id"])] + \
              [(r, "relief") for r in sorted(cand, key=lambda r: r["id"]) if r.get("kind") == "building"]
        passes = one * PATCH_ROUNDS     # overlapping patches settle in a few rounds
        for row, which in passes:
            r_src = by_src[row["src"]]
            f = row["seat"].get("foot") or [64.0, 64.0]
            src_rel = foot_relief(S, r_src["pos"][0], r_src["pos"][1], r_src["rot"][2], f) \
                if row.get("kind") == "building" and row["seat"].get("foot") else None
            need = patch_for(G, S, r_src, row["pos"][0], row["pos"][1], row["rot"][2], f, row["kind"],
                             src_rel, which, row["seat"])
            if not need:
                continue
            target, why = need
            verts = patch_verts(G, row["pos"][0], row["pos"][1], row["rot"][2], f, target)
            G.apply_patches([{"cell": list(k), "verts": v} for k, v in verts.items()])
            label = f"{row.get('cluster')} {row['base']}: {why}"
            patched[row["src"]] = why
            for cell, vs in verts.items():
                c = sums.setdefault(cell, {"verts": {}, "why": []})
                for rr, cc, dz in vs:
                    c["verts"][(rr, cc)] = round(c["verts"].get((rr, cc), 0.0) + dz, 1)
                if label not in c["why"]:
                    c["why"].append(label)
    land = [{"cell": list(cell), "verts": [[k[0], k[1], v] for k, v in sorted(c["verts"].items()) if abs(v) >= 1],
             "why": "; ".join(c["why"]), "by": "draft"} for cell, c in sorted(sums.items())]
    for lrow in ledger:
        if lrow["src"] in patched and lrow["status"] == "placed":
            lrow["status"] = "adapted"
            lrow["patch"] = patched[lrow["src"]]
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

    nodes_src, nodes_our = {}, {}
    for d in ext_doors:
        f = front(d)
        nodes_src[d["id"]] = f
        nodes_our[d["id"]] = fit.per[of[d["id"]]].pt(*f)
    landing = next((c for c in clusters if c.kind == "landing"), None)
    if landing:
        # the landing's shore end: from its member nearest the town, walk towards the town until dry land
        cand = [by_src[i] for i in landing.members if by_src[i].get("kind") not in VEG]
        start = min(cand, key=lambda r: (geom.dist(r["pos"], pivot), r["id"]))["pos"]
        d = geom.dist(start, pivot) or 1.0
        ux, uy = (pivot[0] - start[0]) / d, (pivot[1] - start[1]) / d
        land_src = (start[0], start[1])
        for k in range(int(d // 64)):
            p = (start[0] + ux * 64 * k, start[1] + uy * 64 * k)
            if not S.wet(*p):
                land_src = p
                break
        nodes_src["landing"] = land_src
        nodes_our["landing"] = fit.per[landing.id].pt(*land_src)
    nav = NavGraph(src.exterior.navmesh)
    edges = network(nodes_src, nav)
    paths_src, paths_our = [], []
    for k, (a, b, pts) in enumerate(edges):
        width = STREET_WIDTH if any(nav.flags[nav.nearest(p)] & 0x40 for p in pts[1:-1]) or not nav else PATH_WIDTH
        mapped = [nodes_our[a]] + [fit.warp(*p) for p in pts[1:-1]] + [nodes_our[b]]
        mapped = simplify([(round(p[0], 1), round(p[1], 1)) for p in mapped])
        wet = sum(1 for p in mapped if G.wet(*p)) > len(mapped) / 2
        paths_src.append({"points": [list(p) for p in pts], "width": width})
        paths_our.append({"id": f"{place_id}.path.{k + 1:02d}", "kind": "street" if width >= STREET_WIDTH else "path",
                          "points": [list(p) for p in mapped], "width": width,
                          "style": "boardwalk" if wet else "dirt", "from": a, "to": b})

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
                                            nodes_our, paths_our, dec, ledger)

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
        "fit": {**fit.as_dict(), "clusters_info": [c.as_dict() for c in clusters]},
        "clearance": clearance,
        "factions": factions,
        "stations": stations,
        "ground": {"bundle": f"ground.{place_id}", "sha": G.sha, "stamp": grd.stamp()},
        "source": {"bundle": f"src.{place['source_id']}", "stamp": src.stamp()},
        "radius_m": radius_m,
        "counts": counts,
        "draft_key": key,
    })
    pj.write_text(json.dumps(place, indent=1, ensure_ascii=False) + "\n")
    return counts


def draft_people(place_id, rec, gives, src, bases, our, spaces, clusters, fit, of, nodes_our, paths_our, dec, ledger):
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
        pat = re.compile(people.STATION_MATCH[st], re.I)
        found[st] = sorted(r["id"] for r in our if pat.search(str((bases.get(r["base"]) or {}).get("edid", ""))))
    stations = {"needed": stations_need, "found": found,
                "missing": [s for s in stations_need if not found[s]]}

    folk: list[dict] = []
    taken_names: set[str] = set()
    crime = f"{place_id}.crime"
    factions = [{"id": crime, "kind": "crime", "name": rec.get("name"), "jail": None},
                {"id": f"{place_id}.guard", "kind": "guard", "crime": crime},
                {"id": f"{place_id}.town", "kind": "town", "crime": crime}]
    inn_space = halls[0] if halls else None
    indoor_free = list(halls)

    def work_for(role: str, n: int) -> dict:
        o = roles_override.get(role)
        if o:
            return {"space": o.get("space", "exterior"), **({"pos": o["pos"]} if o.get("pos") else {}), "radius": 512}
        if role == "boatman" and "landing" in nodes_our:
            p = nodes_our["landing"]
            return {"space": "exterior", "pos": [round(p[0], 1), round(p[1], 1)], "radius": 384}
        if role in people.INDOOR and indoor_free:
            sid = inn_space if role == "innkeeper" and inn_space in indoor_free else indoor_free[0]
            indoor_free.remove(sid)
            return {"space": sid, "radius": 1024}
        if role == "smith" and stations["found"].get("forge"):
            r = next(x for x in our if x["id"] == stations["found"]["forge"][0])
            return {"space": "exterior", "ref": r["id"], "radius": 512}
        for k, p in building_doors:
            if k not in used_fronts:
                used_fronts.add(k)
                return {"space": "exterior", "pos": [round(p[0], 1), round(p[1], 1)], "radius": 384}
        return town

    def bed_for(prefer: list[str]) -> dict | None:
        for sid in prefer:
            s = take(sid)
            if s:
                return s
        return None

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
    # guards: patrol the streets in two shifts
    patrol_pts = []
    for p in paths_our:
        for q in p["points"]:
            if not patrol_pts or geom.dist(patrol_pts[-1], q) > 256:
                patrol_pts.append([round(q[0], 1), round(q[1], 1)])
    n_guards = people.guard_count(sum(1 for c in clusters if c.kind == "building"))
    for k in range(n_guards):
        shift = "day" if k % 2 == 0 else "night"
        bed = bed_for(halls + houses)
        pid = io.mint(place_id, "person", "guard", str(k))
        pts = patrol_pts[k // 2 % max(1, len(patrol_pts)):] + patrol_pts[:k // 2 % max(1, len(patrol_pts))]
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
