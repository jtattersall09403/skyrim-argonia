"""`look <place> measure`: the place's measurement table, numbers and no images. The structures' own numbers (each
house's floor, the ground under it, its deck and the gap between, its doors, its steps; each dock, walkway and
bridge with its joins and ends) are the units' (tools/places/units.py table) and nothing is measured twice; this adds
what the units do not give: each house's eaves over the ground, each tree's root collar against the ground, and each
loose piece's lowest point over what is under it. Heights in game units (70 = 1 m)."""
from __future__ import annotations

import numpy as np

from tools.places.look import capture, geom

EAVES_MIN = 150.0    # a house's eaves this little over the ground: a person cannot pass under, it reads as buried
EAVES_SHARE = 0.45   # a house body's eaves taken this share of its height under its top (an estimate from the box)
COLLAR_MAX = 60.0    # a tree's root collar this far under the ground: buried
COLLAR_FLOAT = 120.0  # a tree's feet this far over the ground with nothing under them: floating
LOOSE_TOL = geom.FLOAT_TOL


def eaves(body: dict, ground) -> dict:
    """A house body's eaves over the ground under it: the box top less EAVES_SHARE of its height, over the highest
    ground under its footprint (an estimate: the box knows no roof line)."""
    lo, hi = geom.aabb(body)
    g = [ground.height(x, y) for x, y, _ in geom.bottom_points(body, 4)]
    g = [v for v in g if v is not None]
    if not g:
        return {"eaves_over_ground": None}
    e = float(hi[2]) - EAVES_SHARE * float(hi[2] - lo[2])
    return {"eaves_over_ground": round(e - max(g)), "flag": e - max(g) < EAVES_MIN}


def collar(tree: dict, ground) -> dict | None:
    """A tree's root collar (its origin, where the trunk meets its roots) against the ground there."""
    m = np.asarray(tree["m"], float)
    x, y, z = m[0][3], m[1][3], m[2][3]
    g = ground.height(x, y)
    if g is None:
        return None
    return {"collar_over_ground": round(float(z - g)), "flag": z - g < -COLLAR_MAX}


def tree_floats(tree: dict, sc) -> bool:
    """A tree whose feet stand over the ground with nothing holding them: the rock it grew on sunk or pruned, or a
    source bank that our ground lies under."""
    if "hanging" in str(tree.get("edid") or "").lower():   # moss hangs from what is over it
        return False
    boxes = {q["id"]: geom.aabb(q) for q in sc.everything()}
    r = geom.probe_piece(tree, sc.ground, sc.everything(), boxes)
    low = r.get("lowest_over_ground")
    return low is not None and low > COLLAR_FLOAT and not r.get("held_by")


def table(sc, pl, units_text: str) -> str:
    """The units' table, then eaves, collars and loose pieces, each flagged where it fails its rule."""
    out = [units_text, "", f"eaves over the ground (estimate: box top less {EAVES_SHARE:.0%} of its height; "
           f"flag under {EAVES_MIN:.0f})", f"{'house':34} {'eaves':>6} flag"]
    for un in pl.units:
        if un["kind"] != "house":
            continue
        for bid in un["pieces"].get("body", []):
            p = sc.by_id.get(bid)
            if p is None:
                continue
            e = eaves(p, sc.ground)
            out.append(f"{un['id'][:34]:34} {e['eaves_over_ground'] if e['eaves_over_ground'] is not None else '-':>6} "
                       f"{'EAVES LOW' if e.get('flag') else 'ok'}")
    out += ["", f"trees: root collar against the ground (flag more than {COLLAR_MAX:.0f} under, or feet more than "
            f"{COLLAR_FLOAT:.0f} over with nothing under them)",
            f"{'tree':40} {'collar':>7} flag"]
    in_unit = {pid for un in pl.units if un["kind"] != "thing" for ids in un["pieces"].values() for pid in ids}
    for p in sc.pieces:
        if p.get("kind") != "tree" or not p.get("model"):
            continue
        c = collar(p, sc.ground)
        if c is None:
            continue
        word = "COLLAR BURIED" if c["flag"] else "ok"
        if c["collar_over_ground"] > COLLAR_FLOAT and tree_floats(p, sc):
            word = "COLLAR FLOATS"
        out.append(f"{(p.get('edid') or '')[:24] + ' ' + p['id'][-14:]:40} {c['collar_over_ground']:>7} {word}")
    out += ["", f"loose pieces (not in a unit): lowest point over what is under it, shown when over {LOOSE_TOL:.0f} "
            "or buried", f"{'piece':48} {'lowest':>7} held by / fault"]
    faults = {f["id"]: f["fault"] for f in sc.faults()}
    boxes = {q["id"]: geom.aabb(q) for q in sc.everything()}
    for p in sc.pieces:
        if p["id"] in in_unit or p.get("kind") in ("tree", "light", "marker", "groundcover") or capture.helper_kind(p):
            continue
        if not p.get("model"):
            continue
        r = geom.probe_piece(p, sc.ground, sc.everything(), boxes)
        low = r.get("lowest_over_ground")
        if low is None or (abs(low) <= LOOSE_TOL and p["id"] not in faults):
            continue
        out.append(f"{(p.get('edid') or '')[:30] + ' ' + p['id'][-16:]:48} {low:>7.0f} "
                   f"{faults.get(p['id'], 'held by ' + ','.join(str(h)[-8:] for h in (r.get('held_by') or [])[:2]) or 'nothing')}")
    return "\n".join(out) + "\n"


def run(sc, place: str) -> dict:
    from tools.places import units
    pl = units.Place(place, scene=sc)
    _rows, text = units.table(pl)
    t = table(sc, pl, text)
    return {"text": t, "flags": sum(1 for ln in t.splitlines() if any(w in ln for w in (
        "EAVES LOW", "COLLAR BURIED", "COLLAR FLOATS", "flags", "floor under", "through", "mismatched", "unsupported", "not reaching")))}
