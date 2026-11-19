"""Things the agent adds to a place by hand: place.json `draft.add`, one row per thing.

A row: {base, pos: [x, y] outside | [x, y, z] in a room, space? (a room's space id; default the exterior), rot_z?,
scale?, kind?, dz?, on?, name?, need?, why, tier?}. Outside the thing is seated on the ground (its true footprint, `dz`
over the lowest ground under it), or, with `on` (a placed row's id), on that thing, `dz` over its origin (moss draped
on a fence, carried with it); in a room it stands where `pos` puts it (a room's floor is the source's, so its
height is measured off the floor-standing piece beside it and given). `name` is the name the game shows on looking
at it (a container's: the build makes the container of ours carry it); `need` the story need it meets, by seq. Its
id is minted from its place in the list and its base, so a rerun keeps it. The whole draft adds them; on a drafted
place `draft add <place>` places them again from `draft.add` and touches no other row.
"""
from __future__ import annotations

from tools.places.draft import geom, io

FIELDS = ("name", "need", "tier")


def rows(place_id: str, dec: dict, bases: dict) -> list[dict]:
    """Each `draft.add` row as a place row with its `space`."""
    out = []
    for k, a in enumerate(dec.get("add") or []):
        space = a.get("space") or "exterior"
        z = float(a["pos"][2]) if len(a["pos"]) > 2 else 0.0
        row = {"id": io.mint(place_id, "add", str(k), a["base"]), "base": a["base"], "kind": a.get("kind", "furniture"),
               "pos": [float(a["pos"][0]), float(a["pos"][1]), z], "rot": [0.0, 0.0, float(a.get("rot_z", 0.0))],
               "scale": float(a.get("scale", 1.0)), "layer": "place", "flags": [], "src": None,
               "seat": ({"mode": "on", "on": a["on"], "dz": float(a.get("dz", 0.0))} if a.get("on") else
                        {"mode": "ground", "dz": float(a.get("dz", 0.0))}) if space == "exterior" else {"mode": "free"},
               "why": a.get("why", "")}
        row.update({f: a[f] for f in FIELDS if a.get(f) is not None})
        if space == "exterior" and not a.get("on"):
            f = geom.foot(row, bases)
            if f:
                row["seat"]["foot"] = f
        if not bases.get(a["base"]):
            row["base_unknown"] = True
        out.append((space, row))
    return out


STAND = ("building", "static", "furniture", "container", "activator")
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


def apply(st, log=print) -> None:
    """The `add` stage: every `draft.add` row placed again as `rows` gives it; rows it minted before and no longer
    lists are taken out; nothing else is touched."""
    from tools.places.seat import seat_all
    dec = st.place.get("draft") or {}
    want = rows(st.place_id, dec, st.bases)
    st.bases.update(io.catalogue_bases({r["base"] for _, r in want} - set(st.bases)))
    want = rows(st.place_id, dec, st.bases)
    minted = {io.mint(st.place_id, "add", str(k), b) for k in range(len(dec.get("add") or []) + 64)
              for b in {a["base"] for a in dec.get("add") or []} | {r["base"] for sp in st.files["spaces"].values()
                                                                   for r in sp["refs"] if r.get("why") and not r.get("src")}}
    ids = {r["id"] for _, r in want}
    for sid, sp in st.files["spaces"].items():
        gone = [r["id"] for r in sp["refs"] if r["id"] in minted and r["id"] not in ids]
        if gone:
            sp["refs"] = [r for r in sp["refs"] if r["id"] not in gone]
            log(f"draft add {st.place_id}: {sid}: no longer listed, taken out: {', '.join(gone)}")
    outside = [r for sid, r in want if sid == "exterior"]
    settle(outside, [r for r in st.ext if r["id"] not in ids], st.bases, st.G,
           float((st.place.get("fit") or {}).get("relief_norm", 64.0)), lambda m: log(f"draft add {st.place_id}: {m}"))
    seat_all(outside, st.G)
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
