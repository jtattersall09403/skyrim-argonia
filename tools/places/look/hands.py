"""The hands' own rules beyond a move: the decks of a structure and their height over the ground (what `move` and
`sink` report), a duplicate's own seat and reason, and one flight of steps laid from a deck or a door down to the
ground the way the streets stage lays them (tools/places/draft/walk.py: the place's own steps pieces first, then
its decks' kit; hung square off the deck's edge, its top tread at the deck's height, its foot where a tread meets
the ground). Numbers only; verbs.py turns them into ops."""
from __future__ import annotations

import copy
import math

from tools.places.look import geom


def _walk():
    from tools.places.draft import walk
    return walk


UNIT_KINDS = ("house", "walkway", "bridge", "dock", "small", "boat", "thing", "added")


def units_of(sc):
    """The place's units (tools/places/units.py) as the scene stands, read once per scene."""
    if getattr(sc, "_units", None) is None:
        from tools.places import units
        sc._units = units.Place(sc.place_id, scene=sc)
    return sc._units


def thing(sc, name: str, piece: bool = False) -> dict:
    """What a hand acts on: a unit by its id (house.<room>, walkway.03, ...) as its own pieces, else the scene's thing.
    A house's body is never moved without its deck: a thing holding a body but not all of its unit's decks is refused
    unless `piece` (the agent means that one piece)."""
    head = name.split(".", 1)[0].lower()
    if sc.space == "exterior" and head in UNIT_KINDS:
        pl = units_of(sc)
        u = pl.unit(name)
        ids = [i for v in u["pieces"].values() for i in v if i in sc.by_id]
        return sc._of(u["id"], "unit", [sc.by_id[i] for i in ids])
    th = sc.resolve(name)
    if piece or sc.space != "exterior":
        return th
    got = {p["id"] for p in th["pieces"]}
    for u in units_of(sc).units:
        body, deck = set(u["pieces"].get("body", [])), set(u["pieces"].get("deck", []))
        if u["kind"] == "house" and body & got and deck - got:
            raise ValueError(f"{name} holds the body of {u['id']} but not its deck: a house moves with its platform. "
                             f"Act on the unit ({u['id']}) or give --piece to move that piece alone")
    return th


def decks(sc, rows: list[dict]) -> list[tuple[dict, float, tuple]]:
    """The deck pieces among rows (floors, platforms, planks: a level walked top): [(row, deck height, own rect)]."""
    try:
        return _walk().decks([r for r in rows if r.get("pos")], sc.bases)
    except Exception:  # noqa: BLE001  a model whose collision cannot be read is no deck the tool can measure
        return []


def deck_heights(sc, rows: list[dict], dx: float = 0.0, dy: float = 0.0, dz: float = 0.0) -> list[dict]:
    """Each deck piece's walked top over the ground under its middle, as it stands (`seated` z) and after a move of
    dx, dy, dz: [{id, edid, over, after}]."""
    out = []
    seated = {r["id"]: r for r in sc.refs.values()} if hasattr(sc, "refs") else {}
    w = _walk()
    for r, top, rect in decks(sc, [seated.get(r["id"], r) for r in rows]):
        cx, cy = w.to_world(r, (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
        g0, g1 = sc.ground.height(cx, cy), sc.ground.height(cx + dx, cy + dy)
        out.append({"id": r["id"], "edid": (sc.bases.get(r["base"]) or {}).get("edid"),
                    "over": None if g0 is None else round(top - g0, 1),
                    "after": None if g1 is None else round(top + dz - g1, 1)})
    return out


def own_seat(sc, r: dict, nr: dict, group: set[str]) -> tuple[dict, float]:
    """A copy's own seat where it stands, and its height there: a seat on the ground (ground, above, stilts, water,
    clear) is the original's rule, measured afresh at the copy's spot; a piece the original stood on that is not
    copied is never the copy's: it goes on what is under it at the height it comes to, else on the ground at the
    original's height over its own ground. A room's copies keep their height (free)."""
    from tools.places.seat import reference_z
    z0 = (sc.refs.get(r["id"]) or r)["pos"][2]
    s = copy.deepcopy(r.get("seat") or {"mode": "free"})
    if sc.space != "exterior" or s.get("mode", "free") == "free":
        return {"mode": "free"}, z0
    rz, foot = (r.get("rot") or [0, 0, 0])[2], s.get("foot")
    g0 = reference_z(sc.ground, "ground", r["pos"][0], r["pos"][1], rz, foot)
    g1 = reference_z(sc.ground, "ground", nr["pos"][0], nr["pos"][1], rz, foot)
    over = z0 - g0 if g0 is not None else 0.0
    if s["mode"] != "on":
        base = reference_z(sc.ground, s["mode"], nr["pos"][0], nr["pos"][1], rz, foot)
        return s, (base + float(s.get("dz", 0.0))) if base is not None else z0
    z = (g1 + over) if g1 is not None else z0
    others = [p for p in sc.pieces if p["id"] not in group]
    sup = geom.support_under(others, nr["pos"][0], nr["pos"][1], z, geom.FLOAT_TOL)
    if sup and sup in sc.refs:
        return {"mode": "on", "on": sup, "dz": round(z - sc.refs[sup]["pos"][2], 3)}, z
    return {"mode": "ground", "dz": round(over, 3)} | ({"foot": foot} if foot else {}), z


def duplicate_rows(sc, rows: list[dict], dx: float, dy: float, why: str, new_id) -> list[dict]:
    """The copies of rows moved by dx, dy: each its own id, its own reason, seated where it stands (a copy seated on
    another copied piece goes on that piece's copy)."""
    ids = {r["id"]: new_id(i) for i, r in enumerate(rows)}
    out = []
    for r in rows:
        nr = {k: v for k, v in copy.deepcopy(r).items() if k not in ("src", "why", "why_tier", "tier", "need", "door")}
        nr["id"] = ids[r["id"]]
        nr["pos"] = [round(r["pos"][0] + dx, 3), round(r["pos"][1] + dy, 3), r["pos"][2]]
        on = (r.get("seat") or {}).get("on")
        if on in ids:   # on another copied piece: on that piece's copy, as the original stands on the original
            nr["seat"] = dict(r["seat"], on=ids[on])
        else:
            nr["seat"], z = own_seat(sc, r, nr, set(ids) | set(ids.values()))
            nr["pos"][2] = round(z, 3)
        nr["why"] = why
        nr["tier"] = "AGENT_INVENTED"
        out.append(nr)
    return out


def steps_bases(sc) -> list[str]:
    """The steps pieces a flight may be laid with: the place's own (commonest first), then its decks' kit."""
    from collections import Counter
    w = _walk()
    rows = list(sc.refs.values())
    got = Counter(r["base"] for r in rows if w.is_steps(r, sc.bases))
    out = sorted(got, key=lambda b: (-got[b], b))
    try:
        for k, b in w.kit_steps({r["base"] for r, _, _ in w.decks(rows, sc.bases)}, sc.bases).items():
            sc.bases.setdefault(k, b)
            if k not in out:
                out.append(k)
    except Exception:  # noqa: BLE001  no catalogue: the place's own steps only
        pass
    return out


def edge_toward(sc, d: dict, rect: tuple, to_xy) -> tuple[tuple, tuple]:
    """The middle of the deck's edge facing a point, and the unit plan direction off it (square to the edge)."""
    w = _walk()
    x0, y0, x1, y1 = rect
    best = None
    for mx, my, ox, oy in (((x0 + x1) / 2, y1, 0, 1), ((x0 + x1) / 2, y0, 0, -1), (x1, (y0 + y1) / 2, 1, 0),
                           (x0, (y0 + y1) / 2, -1, 0)):
        a = w.to_world(d, mx, my)
        far = w.to_world(d, mx + ox, my + oy)
        o = (far[0] - a[0], far[1] - a[1])
        n = math.hypot(*o)
        o = (o[0] / n, o[1] / n)
        dist = math.dist(a, to_xy[:2])
        toward = (to_xy[0] - a[0]) * o[0] + (to_xy[1] - a[1]) * o[1]
        if toward > 0 and (best is None or dist < best[0]):
            best = (dist, a, o)
    if best is None:
        raise ValueError("no edge of that deck faces the point")
    return best[1], best[2]


def lay_steps(sc, deck_row: dict, to_xy, new_id: str, why: str) -> dict:
    """One flight from a deck piece's edge facing to_xy down to the ground: the first steps piece (steps_bases order)
    whose foot meets the ground the bank buries least of; hung on the deck (seat `on`), its foot resting where a
    tread meets the ground. Returns {row, top, foot, base, tried}; raises when no piece of the kit comes down."""
    w = _walk()
    base = sc.bases.get(deck_row["base"]) or {}
    dr = w.deck_rect(base)
    if dr is None:
        raise ValueError(f"{deck_row['id']} has no level deck to hang steps from")
    dz = deck_row["pos"][2] + dr[0] * float(deck_row.get("scale") or 1.0)
    a, o = edge_toward(sc, deck_row, dr[1], to_xy)
    tried, cand = [], []
    for sb in steps_bases(sc):
        fl = w.flight(sc.bases.get(sb) or {})
        if fl is None:
            continue
        pos, rot, seat = w.hang(fl, deck_row, dz, a, o)
        landed, buried = w.landing(fl, pos[2], a, o, sc.ground)
        tried.append({"base": sb, "edid": (sc.bases.get(sb) or {}).get("edid"), "lands": landed is not None})
        if landed is None:
            continue
        cand.append((round(buried / w.BURY), math.dist(landed[:2], to_xy[:2]), sb, pos, rot, seat, landed))
    if not cand:
        raise ValueError(f"no steps piece of the place's kit comes down to the ground from that edge: {tried}")
    cand.sort(key=lambda t: t[:2])
    _, _, sb, pos, rot, seat, landed = cand[0]
    row = {"id": new_id, "base": sb, "kind": "building", "pos": pos, "rot": rot, "scale": 1.0, "layer": "place",
           "flags": [], "src": None, "seat": seat, "why": why, "tier": "AGENT_INVENTED"}
    return {"row": row, "top": [round(a[0]), round(a[1]), round(dz)], "foot": [round(float(v)) for v in landed],
            "base": sb, "edid": (sc.bases.get(sb) or {}).get("edid"), "tried": tried}


def deck_of(sc, th, near_xy) -> dict:
    """The deck piece a flight leaves from: of a thing's deck pieces the one nearest the point; for a door, the deck
    under where one comes out of it."""
    rows = [sc.refs[p["id"]] for p in th["pieces"] if p["id"] in sc.refs]
    if th["kind"] == "door":
        p = th["pieces"][0]
        at = (p.get("door") or {}).get("arrival") or [p["m"][0][3], p["m"][1][3], p["m"][2][3]]
        sup = geom.support_under(sc.pieces, at[0], at[1], at[2] + 8, 64)
        if not sup:
            raise ValueError("no deck where one comes out of that door: name the deck")
        rows = [sc.refs[sup]]
    ds = decks(sc, rows)
    if not ds:
        raise ValueError(f"{th['name']} has no deck piece to lay steps from")
    w = _walk()
    return min(ds, key=lambda t: math.dist(w.to_world(t[0], (t[2][0] + t[2][2]) / 2, (t[2][1] + t[2][3]) / 2), near_xy[:2]))[0]
