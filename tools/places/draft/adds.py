"""Things the agent adds to a place by hand: place.json `draft.add`, one row per thing.

A row: {base, pos: [x, y] outside | [x, y, z] in a room, space? (a room's space id; default the exterior), rot_z?,
scale?, kind?, dz?, name?, need?, why, tier?}. Outside the thing is seated on the ground (its true footprint, `dz`
over the lowest ground under it); in a room it stands where `pos` puts it (a room's floor is the source's, so its
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
               "seat": {"mode": "ground", "dz": float(a.get("dz", 0.0))} if space == "exterior" else {"mode": "free"},
               "why": a.get("why", "")}
        row.update({f: a[f] for f in FIELDS if a.get(f) is not None})
        if space == "exterior":
            f = geom.foot(row, bases)
            if f:
                row["seat"]["foot"] = f
        if not bases.get(a["base"]):
            row["base_unknown"] = True
        out.append((space, row))
    return out


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
