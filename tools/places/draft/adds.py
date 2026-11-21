"""Things the agent adds to a place by hand: place.json `draft.add`, one row per thing.

A row: {base, pos: [x, y] outside | [x, y, z] in a room, space? (a room's space id; default the exterior), rot_z?,
scale?, kind?, dz?, on?, walk?, stop?, lock?, name?, need?, map_marker?, room?, pair?, arrival?, why, tier?}. Outside
the thing is seated on the ground (its true footprint, `dz` over the lowest ground under it), or with `on` (a placed
row's id, an added row's minted id included) `dz` over that row's origin, carried with it (moss on a fence, a door on
its building); in a room it stands where `pos` puts it (a room's floor is the source's, so its height is measured off
the floor-standing piece beside it and given). `walk` is a walkway's deck height where its mesh's top is a rail;
`stop` marks the thing a travel stop's handler works at (`rootworm-stop` on a root pool); `lock` is the ref's lock
({level, key, flags}); `name` the name the game shows on looking at it; `need` the story need it meets, by seq;
`map_marker` the name a map marker shows on the world map (the row's base is Skyrim's map marker, 000010). Its id is
minted from its `key` (the first run pins each row its key, so another row added or removed never shifts its id) and its base; `id_base` keeps the id a row was first
minted from when its base is swapped in place (the ids the stories rest on stay). The whole draft adds them; on a drafted place
`draft add <place>` places them again from `draft.add` and touches no other row.

A door with `room` {copy_of: "<source_id>/<cell>", door?: the cell's way out (source ref id), space?: our space id
(default the cell's), whole?: true to copy a cell of several ways out whole (one building; its other ways out
removed), arrival: where one steps out ([x, y] outside, [x, y, z] in a room), drop?: {source ref id: why}
for a piece the room must not have (a container of levelled treasure: decision 0035; a door on to a further room)}
brings that interior of any source we hold as a copied room of ours behind the door, outside or in another room (of
a cell that packs several rooms, the one behind that way out):
the room's `space.json` (marked `added`) and its refs file of our changes only (the way out re-pointed at our door,
any further way out removed, every piece the catalogue judges Nordic replaced by `draft.replace` or removed: decision
0006). A further way into a room is a pair of added doors: one standing in the room, and one outside naming it in
`pair`, with its `arrival`. Once the streets stage has moved a door's arrival onto the walkable network, a rerun
keeps it.
"""
from __future__ import annotations

import copy

from tools.places.draft import geom, interiors, io

FIELDS = ("name", "need", "tier", "lock")


def keys(adds: list[dict]) -> list[str]:
    """The key each `draft.add` row's id is minted from: its own `key`; a row without one takes the smallest unused
    whole number, so the first run gives positions and an added or removed row never shifts another's id."""
    taken = {str(a["key"]) for a in adds if a.get("key") is not None}
    out, n = [], 0
    for a in adds:
        if a.get("key") is not None:
            out.append(str(a["key"]))
            continue
        while str(n) in taken:
            n += 1
        out.append(str(n))
        taken.add(str(n))
    return out


def ident(place_id: str, a: dict, key: str) -> str:
    return io.mint(place_id, "add", key, a.get("id_base") or a["base"])


def pin(place: dict) -> int:
    """Write each keyless `draft.add` row its key, so later runs keep its id. Returns the rows pinned."""
    adds = (place.get("draft") or {}).get("add") or []
    n = 0
    for a, k in zip(adds, keys(adds)):
        if a.get("key") is None:
            a["key"], n = k, n + 1
    return n


def follow(place: dict, ops: list) -> list[str]:
    """A hand's stroke on an added thing written into its `draft.add` row, so the stage places it where the hand put
    it: a move sets `pos` (and the room's height), `rot_z`, `scale` and `dz` (its seat's); a drop marks the row
    `dropped`; adding it back clears that. Pins the keys first. Returns the ids followed."""
    adds = (place.get("draft") or {}).get("add") or []
    if not adds:
        return []
    pin(place)
    by = {ident(place["place_id"], a, str(a["key"])): a for a in adds}
    done = []
    for op in ops:
        a = by.get(op.get("id") or (op.get("ref") or {}).get("id"))
        if a is None:
            continue
        if op["op"] == "ref.move":
            after = op.get("after") or {}
            room = (a.get("space") or "exterior") != "exterior"
            if after.get("pos"):
                x, y, z = (float(v) for v in after["pos"][:3])
                a["pos"] = [round(x, 2), round(y, 2)] + ([round(z, 2)] if room else [])
            if after.get("rot"):
                a["rot_z"] = round(float(after["rot"][2]), 5)
            if after.get("scale") is not None:
                a["scale"] = after["scale"]
            if not room and (after.get("seat") or {}).get("dz") is not None:
                a["dz"] = round(float(after["seat"]["dz"]), 2)
        elif op["op"] == "ref.remove":
            a["dropped"] = True
        elif op["op"] == "ref.add":
            a.pop("dropped", None)
        done.append(op.get("id") or op["ref"]["id"])
    return done


def rows(place_id: str, dec: dict, bases: dict) -> list[tuple[str, dict]]:
    """Each `draft.add` row as a place row with its `space`; a row a hand dropped (`dropped`) places nothing."""
    out = []
    adds = dec.get("add") or []
    for k, a in zip(keys(adds), adds):
        if a.get("dropped"):
            continue
        space = a.get("space") or "exterior"
        z = float(a["pos"][2]) if len(a["pos"]) > 2 else 0.0
        if space != "exterior":
            seat = {"mode": "free"}
        elif a.get("on"):
            seat = {"mode": "on", "on": a["on"], "dz": float(a.get("dz", 0.0))}
            if a.get("within"):   # it also rests in another thing (a ship's steps carried by its hull)
                seat["carrier"] = a["within"]
        else:
            seat = {"mode": "ground", "dz": float(a.get("dz", 0.0))}
            if a.get("within"):   # on the ground inside a shelter (a bedroll in a tent, a bed in a hut): it rests in it
                seat["carrier"] = a["within"]
        row = {"id": ident(place_id, a, k), "base": a["base"], "kind": a.get("kind", "furniture"),
               "pos": [float(a["pos"][0]), float(a["pos"][1]), z], "rot": [0.0, 0.0, float(a.get("rot_z", 0.0))],
               "scale": float(a.get("scale", 1.0)), "layer": "place", "flags": [], "src": None,
               "seat": seat, "why": a.get("why", "")}
        row.update({f: a[f] for f in FIELDS if a.get(f) is not None})
        if a.get("map_marker"):
            row["map_marker"] = {"$type": "MapMarker", "Flags": "Visible", "Name": a["map_marker"]}
        if a.get("map_marker") or a.get("room"):
            row["flags"] = ["persistent"]
        if seat["mode"] == "ground":
            f = geom.foot(row, bases)
            if f:
                row["seat"]["foot"] = f
        w = a.get("walk", geom.walk(bases.get(a["base"]) or {}))    # `walk`: the deck's height where its mesh's top is a rail
        if w is not None:      # one stands on a walkway's deck (its mesh's top surface), as on the source's own
            row["walk"] = w
        if not bases.get(a["base"]):
            row["base_unknown"] = True
        out.append((space, row))
    return out


STAND = ("building", "furniture", "container")   # what people walk into, sleep in or open; a fence or a tree stands in a creek bed
SEEK, SEEK_STEP = 1536.0, 64.0     # how far round its spot a thing is moved to find ground to stand on, in steps


def ground_ok(row: dict, G, norm: float) -> bool:
    """A thing seated on the ground has ground under the whole of its footprint: the ground under it rises no more
    than `norm` (the slope the source's builders built on) and none of it is under water."""
    from tools.places.seat import foot_points
    f = (row.get("seat") or {}).get("foot")
    if not f:
        return True
    hs = []
    for px, py in foot_points(row["pos"][0], row["pos"][1], row["rot"][2], f, 5):
        h = G.height(px, py)
        if h is None:
            return False
        w = G.water(px, py)
        if w is not None and w > h:
            return False
        hs.append(h)
    return max(hs) - min(hs) <= norm


def settle(rows: list[dict], others: list[dict], bases: dict, G, norm: float, log=print) -> int:
    """Each added thing seated on the ground stands where the ground carries its whole footprint: one whose spot
    does not (a slope, a bank's edge, water under part of it) is moved to the nearest spot within SEEK that does,
    clear of every other solid, keeping its turn. Returns the things moved."""
    from tools.places.draft import overlap
    moved = 0
    for r in rows:
        if r.get("kind") not in STAND or (r.get("seat") or {}).get("mode") != "ground" or ground_ok(r, G, norm):
            continue
        x0, y0 = r["pos"][:2]
        inner = [o for o in rows if o is not r and overlap.inside(o["pos"], r, bases, z=False)]   # what it holds
        near = [o for o in others + rows if o is not r and o not in inner and o.get("kind") in overlap.SOLID
                and abs(o["pos"][0] - x0) < SEEK + 2048 and abs(o["pos"][1] - y0) < SEEK + 2048]
        spots = sorted(((dx * SEEK_STEP, dy * SEEK_STEP) for dx in range(-int(SEEK // SEEK_STEP), int(SEEK // SEEK_STEP) + 1)
                        for dy in range(-int(SEEK // SEEK_STEP), int(SEEK // SEEK_STEP) + 1)),
                       key=lambda d: (d[0] ** 2 + d[1] ** 2, d))
        for dx, dy in spots[1:]:
            if dx * dx + dy * dy > SEEK * SEEK:
                break
            cand = {**r, "pos": [x0 + dx, y0 + dy, r["pos"][2]]}
            if not ground_ok(cand, G, norm):
                continue
            from tools.places.seat import seat_z
            cand["pos"][2] = seat_z(cand, G)
            if overlap.hits(cand, near, bases):
                continue
            r["pos"] = [round(cand["pos"][0], 2), round(cand["pos"][1], 2), cand["pos"][2]]
            for o in inner:      # what stands inside it goes with it
                o["pos"] = [round(o["pos"][0] + dx, 2), round(o["pos"][1] + dy, 2), o["pos"][2]]
            moved += 1
            log(f"add: {r['id']} moved {(dx * dx + dy * dy) ** 0.5:.0f} units onto ground that carries it")
            break
        else:
            log(f"add: {r['id']}: no ground within {SEEK:.0f} units carries its footprint")
    return moved


def room(place_id: str, door: dict, spec: dict, src, replace: dict, nordic: set, G,
         arrival: list | None = None, parent: str = "exterior") -> tuple[str, dict, list[dict]]:
    """The copied room a door of ours leads into: (space id, space.json, refs of our changes). Sets the door's own
    `door`: into the room, and its `arrival` outside (`arrival` when the streets stage has placed it, else the row's).
    `spec`: copy_of, door (the way out), space, arrival, drop ({source ref: why}), strip ({base editor id: why}: every
    ref of that base goes), whole, and cut ({"box": [x1, y1, x2, y2]}: only the part of the source cell inside the
    box is copied, its way out any load door inside it; the build meshes the cut room's navmesh from what it keeps)."""
    cell = spec["copy_of"].split("/", 1)[1]
    sp = src.spaces.get(cell)
    if sp is None:
        raise ValueError(f"draft.add {door['id']}: room {spec['copy_of']}: the source bundle has no space {cell}")
    sid = spec.get("space") or cell
    ways = sorted((r for r in sp.refs if (r.get("door") or {}).get("to_space") == "exterior"), key=lambda r: r["id"])
    cut = spec.get("cut")
    # a cut copy's way out may be any load door inside the cut (one wing of a hall entered by its own door)
    loads = ways if not cut else sorted((r for r in sp.refs if (r.get("door") or {}).get("to_space")
                                         and interiors.in_cut(cut, r["pos"])), key=lambda r: r["id"])
    back = next((r for r in loads if r["id"] == spec.get("door")), None) if spec.get("door") else (loads[0] if loads else None)
    if back is None:
        raise ValueError(f"draft.add {door['id']}: room {spec['copy_of']} has no way out {spec.get('door') or ''}")
    # a cell that packs several rooms (one behind each way out) is copied as the one room behind this way out; a
    # building whose ways out all open into one walkable island (a front and an upper door) is copied whole
    part = back["id"] if (len(ways) > 1 and not spec.get("whole") and interiors.shared(sp.refs, src)
                          and not interiors.one_building(spec["copy_of"], sp.refs)) else None   # one building: copied whole
    keep = interiors.kept(spec["copy_of"], part, cut)
    inner = [r["id"] for r in sp.refs if (r.get("door") or {}).get("to_space") not in (None, "exterior")
             and r is not back and r["id"] not in (spec.get("drop") or {}) and (keep is None or r["id"] in keep)]
    if inner:
        raise ValueError(f"draft.add {door['id']}: room {spec['copy_of']} leads on into further rooms ({inner[:3]})")
    if arrival is None and parent != "exterior":     # inside a room: where one steps out is given whole
        arrival = [float(v) for v in spec["arrival"][:3]]
    elif arrival is None:
        ax, ay = (float(v) for v in spec["arrival"][:2])
        h = G.height(ax, ay)
        arrival = [round(ax, 2), round(ay, 2), round(h if h is not None else door["pos"][2], 2)]
    back_id = io.mint(place_id, sid, back["id"])
    into = next(((r["door"].get("to_pos"), r["door"].get("to_rot")) for s_ in src.spaces.values() for r in s_.refs
                 if (r.get("door") or {}).get("to_ref") == back["id"]), (None, None))
    door["door"] = {"to_space": sid, "to_ref": back_id, "to_pos": list(into[0] or back["pos"]),
                    "to_rot": list(into[1] or back.get("rot") or [0, 0, 0]), "flags": "0", "arrival": list(arrival)}
    out = [{**back, "id": back_id, "src": back["id"], "seat": {"mode": "free"},
            "door": {**back["door"], "to_space": parent, "to_ref": door["id"], "to_pos": list(arrival),
                     "to_rot": [0.0, 0.0, door["rot"][2]]}}]
    for r in sorted(sp.refs, key=lambda r: r["id"]):
        if r is back or r.get("kind") == "actor" or (keep is not None and r["id"] not in keep):
            continue
        rid = io.mint(place_id, sid, r["id"])
        if ((r.get("door") or {}).get("to_space") is not None or r["id"] in (spec.get("drop") or {})
                or (src.bases.get(r.get("base")) or {}).get("edid") in (spec.get("strip") or {})):
            out.append({"id": rid, "src": r["id"], "removed": True})       # one way in: this door's; or the agent's drop
        elif r.get("base") in replace:
            out.append({**r, **interiors.swap(r, {}, replace[r["base"]]), "id": rid, "src": r["id"], "seat": {"mode": "free"}})
        elif r.get("base") in nordic:
            out.append({"id": rid, "src": r["id"], "removed": True})       # a Nordic piece we would add (0006)
    info = {"space_id": sid, "copy_of": spec["copy_of"], "name": sp.meta.get("name"), "door_from": door["id"],
            "parent": parent, "room": part, "added": True}
    if cut:
        info["cut"] = cut
    return sid, info, out


def pair(st, want: list[tuple[str, dict]], adds: list[dict], standing: dict) -> None:
    """A further way into a room: an added door with `pair` (the id of an added door standing in that room) and
    `arrival` ([x, y] where one steps out) leads into the room by that inner door, and the inner door out by it. The
    inner door's arrival is a step in front of it (its local -Y), facing away from it."""
    import math
    by = {r["id"]: (sid, r) for sid, r in want}
    for (sid, r), a in zip(want, adds):
        if not a.get("pair"):
            continue
        if a["pair"] not in by or by[a["pair"]][0] == sid:
            raise ValueError(f"draft.add {r['id']}: pair {a['pair']} is not an added door in another space")
        isid, inner = by[a["pair"]]
        moved = ((standing.get(r["id"]) or {}).get("door") or {}).get("arrival")
        if moved is None:
            ax, ay = (float(v) for v in a["arrival"][:2])
            h = st.G.height(ax, ay) if sid == "exterior" else None
            moved = [round(ax, 2), round(ay, 2), round(h if h is not None else r["pos"][2], 2)]
        rz = inner["rot"][2]
        front = [round(inner["pos"][0] - 128.0 * math.sin(rz), 2), round(inner["pos"][1] - 128.0 * math.cos(rz), 2),
                 inner["pos"][2]]
        r["door"] = {"to_space": isid, "to_ref": inner["id"], "to_pos": front,
                     "to_rot": [0.0, 0.0, round((rz + math.pi) % (2 * math.pi), 5)], "flags": "0", "arrival": list(moved)}
        inner["door"] = {"to_space": sid, "to_ref": r["id"], "to_pos": list(moved), "to_rot": [0.0, 0.0, r["rot"][2]],
                         "flags": "0"}
        for x in (r, inner):
            x["flags"] = ["persistent"]


SPUR = ".path.add."      # an added door's path: `<place>.path.add.<door id's tail>`


def spurs(st, doors: list[dict], log=print) -> None:
    """Each added door is reached by a path: a spur from its arrival to the nearest point of the place's other paths
    (`from` the door's id, `to` that path's), so the town's network runs to it; spurs of doors no longer listed go."""
    import math
    paths = st.files["paths"]
    mine = {f"{st.place_id}{SPUR}{d['id'].rsplit('.', 1)[-1]}": d for d in doors}
    st.files["paths"] = paths = [p for p in paths if SPUR not in p["id"] or p["id"] in mine]
    others = [p for p in paths if SPUR not in p["id"]]
    for pid, d in sorted(mine.items()):
        a = d["door"]["arrival"][:2]
        near = min(((math.dist(a, q[:2]), q[:2], p["id"]) for p in others for q in p["points"]), default=None)
        if near is None:
            continue
        row = {"id": pid, "kind": "path", "points": [[round(a[0], 1), round(a[1], 1)], [round(near[1][0], 1), round(near[1][1], 1)]],
               "width": 128.0, "style": "dirt", "from": d["id"], "to": near[2], "laid": "a spur from an added door to the nearest street"}
        have = next((i for i, p in enumerate(paths) if p["id"] == pid), None)
        if have is None:
            paths.append(row)
            log(f"draft add {st.place_id}: path {pid} from door {d['id']} to {near[2]} ({near[0]:.0f} units)")
        elif paths[have]["from"] != d["id"] or paths[have]["to"] != near[2]:
            paths[have] = row


def room_nordic(keys: set[str], bases: dict[str, dict], review: dict[str, dict]) -> set[str]:
    """The bases of a copied room that are taken out as Nordic: by the Nordic review's looked-at verdict where there
    is one (a stone house's shell looked at and judged neutral stays), else by the catalogue's folder rule."""
    return {k for k in keys if k in bases and io.is_nordic(k, bases[k], review)}


def apply(st, log=print) -> None:
    """The `add` stage: every `draft.add` row placed again as `rows` gives it, and every room a row brings copied
    again; rows and rooms it made before and no longer lists are taken out; nothing else is touched."""
    from tools.places.seat import seat_all
    dec = st.place.get("draft") or {}
    pin(st.place)                       # each row's id from its own key, before any row is placed
    adds = [a for a in dec.get("add") or [] if not a.get("dropped")]
    want = rows(st.place_id, dec, st.bases)
    st.bases.update(io.catalogue_bases({r["base"] for _, r in want} - set(st.bases)))
    want = rows(st.place_id, dec, st.bases)
    every = dec.get("add") or []
    minted = {io.mint(st.place_id, "add", k, b) for k in {str(a["key"]) for a in every} | set(map(str, range(len(every) + 64)))
              for b in {a["base"] for a in every} | {a["id_base"] for a in every if a.get("id_base")} | {r["base"] for sp in st.files["spaces"].values()
                                                    for r in sp["refs"] if r.get("why") and not r.get("src")}}
    ids = {r["id"] for _, r in want}
    for sid, sp in st.files["spaces"].items():
        gone = [r["id"] for r in sp["refs"] if r["id"] in minted and r["id"] not in ids]
        if gone:
            sp["refs"] = [r for r in sp["refs"] if r["id"] not in gone]
            log(f"draft add {st.place_id}: {sid}: no longer listed, taken out: {', '.join(gone)}")
    # the rooms the rows bring
    rooms: dict[str, tuple[dict, list[dict]]] = {}
    srcs: dict[str, object] = {}
    replace = io.replacements(dec, st.bases)
    review = io.nordic_review()
    standing = {r["id"]: r for r in st.files["spaces"]["exterior"]["refs"]}
    for (sid, r), a in zip(want, adds):
        if not a.get("room"):
            continue
        source_id, cell = a["room"]["copy_of"].split("/", 1)
        if source_id not in srcs:
            srcs[source_id] = st.src if source_id == st.place.get("source_id") else io.load(f"src.{source_id}", st.bundles)
        src = srcs[source_id]
        keys = {x["base"] for x in (src.spaces[cell].refs if cell in src.spaces else [])}
        nordic = room_nordic(keys, io.catalogue_bases(keys), review)
        moved = ((standing.get(r["id"]) or {}).get("door") or {}).get("arrival")
        rid, info, refs = room(st.place_id, r, a["room"], src, replace, nordic, st.G, moved, sid)
        have = (st.files["spaces"].get(rid) or {}).get("space")
        if (have is not None and not have.get("added")) or rid in rooms:
            raise ValueError(f"draft.add {r['id']}: room {rid} is already a space of the place: give the room a `space`")
        rooms[rid] = (info, refs)
    for sid in [s for s, sp in st.files["spaces"].items() if (sp.get("space") or {}).get("added") and s not in rooms]:
        del st.files["spaces"][sid]
        log(f"draft add {st.place_id}: room {sid}: no longer listed, taken out")
    for sid, (info, refs) in rooms.items():
        sp = st.files["spaces"].get(sid)
        if sp is None or sp.get("space") is None:
            st.files["spaces"][sid] = {"space": info, "refs": refs}
            log(f"draft add {st.place_id}: room {sid} copied from {info['copy_of']} behind {info['door_from']}")
            continue
        info = {**info, "name": sp["space"].get("name") or info["name"]}     # its name is the names stage's
        refs = sorted(refs + [x for x in sp["refs"] if not x.get("src")], key=lambda x: x["id"])   # what is added in it stays
        if info != sp["space"] or refs != sorted(sp["refs"], key=lambda x: x["id"]):
            sp["space"], sp["refs"] = info, refs
            log(f"draft add {st.place_id}: room {sid} copied again")
    pair(st, want, adds, standing)
    spurs(st, [r for sid, r in want if sid == "exterior" and (r.get("door") or {}).get("arrival")], log)
    outside = [r for sid, r in want if sid == "exterior"]
    settle(outside, [r for r in st.ext if r["id"] not in ids], st.bases, st.G,
           float((st.place.get("fit") or {}).get("relief_norm", 64.0)), lambda m: log(f"draft add {st.place_id}: {m}"))
    held = {r["seat"]["on"] for r in outside if r["seat"].get("on")} - ids     # what our things stand on, as it stands
    seat_all(outside + [copy.deepcopy(r) for r in st.ext if r["id"] in held], st.G)
    for sid, r in want:
        sp = st.files["spaces"].get(sid)
        if sp is None:
            raise ValueError(f"draft.add: {r['id']}: no space {sid} in the place")
        have = next((i for i, x in enumerate(sp["refs"]) if x["id"] == r["id"]), None)
        if have is None:
            sp["refs"].append(r)
            log(f"draft add {st.place_id}: {sid}: {r['id']} {r['base']} added ({r.get('why', '')[:80]})")
        elif sp["refs"][have] != r:
            sp["refs"][have] = r
            log(f"draft add {st.place_id}: {sid}: {r['id']} placed again")
