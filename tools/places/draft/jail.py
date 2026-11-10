"""`draft jail <place_id>`: the crime faction's sentence, by the place's law (`place_law` in the database, the one
source of the fact: tools/newworld/place_law.py, docs/design/law.md): a foreign law's jail, as Skyrim.esm gives a
hold's crime faction one; a native law's Owing, the same jail mechanism with no cell; nothing where no one keeps law.

Measured on Skyrim.esm (`ArgoniaPlacesBuild jail`, CrimeFactionRift, CrimeFactionWhiterun, CrimeFactionFalkreath,
CrimeFactionWinterhold): the faction's JAIL is a persistent PrisonMarker (Skyrim.esm 000004, a door-type marker)
standing outside the jail's town door, whose teleport leads to a second PrisonMarker in the jail's cell (beside the
prisoner's bed, 166 to 174 units from it, by a door that locks) and back; WAIT is the same marker (Riften,
Falkreath, Winterhold); STOL and PLCN are an EvidenceChestStolenGoods (0267E7) and an EvidenceChestPlayerInventory
(108D36) in the jail's room, persistent, empty, not respawning, owned by the crime faction (Falkreath, Whiterun's
PLCN); JOUT is BeggarOutfit (028B60). The guards' arrest lines are vanilla's DialogueCrimeGuards quest, which speaks
to any actor that IsGuard and is in GuardDialogueFaction (people.py gives guards both). Its lines
(`ArgoniaPlacesBuild crime`, their compiled fragments read): pay runs the guard's crime faction's
PlayerPayCrimeGold(true, true); "go to jail" runs SendPlayerToJail(true, true), and for CrimeFactionWinterhold its own
line SendPlayerToJail(false, true), the player keeping their belongings; resist runs the guard's
SetPlayerResistingArrest(). No vanilla line sends the player with abRealJail false.

Foreign law, from the place's own things:
  - the jail: a copied interior whose room holds the jail kit (bars, a jail wall, a jail door: bases whose editor id
    says jail or prison); a room's or a cell's name alone never makes it one. None: the faction fines only.
  - the cell the player is put in: a bed of the room by a door that locks (a jail door, or any inner door with a
    lock) within CELL_REACH; else a bed behind the room's bars (the straight way from where one arrives in the room
    to it crosses a piece of the jail kit: bars, a jail wall, a jail door); else, where the room has bars and no bed
    behind them, the point behind the bars most enclosed by them (most kit pieces within KIT_REACH), with a bedroll
    of ours there (vanilla's Bedroll01, as Falkreath's jail), so a sentence can be slept out.
  - the jail marker: beside that bed (MARKER_OFF from it, behind the bars where there are bars), clear of the
    room's things; its teleport leads to the release point and back.
  - the release point (the exterior marker): the arrival outside the jail's town door (`door.arrival`, on the
    town's walkable network), facing away from the door.
  - the evidence chests: in the jail's room, stepped in from where one arrives, clear of its things, owned
    `<place>.crime` (the faction), empty and never respawning (vanilla's bases hold nothing).
Native law, the Owing (the player chooses it from the guard's arrest lines; the engine's jail does the rest: the
time passed by the bounty, the stolen goods taken, the release), outside, with no cell and no bars:
  - the work spot: where the place's labour is done: the landing, where the boat-stop's operator works, else the
    work stop most of its people share; standing on the piece built there (a deck, a walkway), else the ground.
    The jail marker stands there, with a bedroll of ours (Bedroll01) beside it, MARKER_OFF away and clear of the
    place's things: lying down on it serves the sentence, as a prisoner's bed does.
  - the return spot: the faction's exterior marker (JAIL and WAIT): the point of the place's streets nearest the
    work spot that stands RETURN_MIN from it at least, on the piece built there, else the ground; its teleport leads
    to the work spot's marker and back.
  - the stolen goods chest (STOL): out of reach, CHEST_DEPTH under the return spot, owned by the faction, empty and
    never respawning. No player-inventory chest and no jail outfit: the Owing takes nothing of the player's.
The stage writes the rows of what it adds (each with its `why`) and place.json's crime row: `law`, `law_why`, and
`jail` (foreign) or `owing` (native).
"""
from __future__ import annotations

import math
import re

import numpy as np

from tools.places.draft import interiors, io, overlap

RETURN_MIN = 384.0      # the return spot stands this far from the work spot at least
CHEST_DEPTH = 2048.0    # the Owing's stolen goods chest stands this far under the return spot
STAND_REACH = 640.0     # a piece reaching down to the ground or the water whose top stands within this above it may be stood on
OWING_WHY = "the {place} crime faction's Owing ({what}): native law's sentence, no cell (draft jail)"
JAIL_WORD = re.compile(r"jail|prison|gaol", re.I)
PRISON_MARKER = "Skyrim.esm:000004"
STOLEN_CHEST = "Skyrim.esm:0267E7"      # EvidenceChestStolenGoods
INVENTORY_CHEST = "Skyrim.esm:108D36"   # EvidenceChestPlayerInventory
BEDROLL = "Skyrim.esm:036ED3"           # Bedroll01 (Falkreath's jail)
CELL_REACH = 384.0      # a bed this near a door that locks is that door's cell (vanilla: 161 to 280)
KIT_REACH = 512.0       # the kit pieces that enclose a point
MARKER_OFF = (128.0, 192.0)   # the jail marker this far from the bed (vanilla: 166 to 174)
GRID = 64.0
BAR_CLEAR = 48.0        # a point behind bars stands this far from them at least
WHY = "the {place} crime faction's jail ({what}): vanilla's hold jail (draft jail)"


def law(place_id: str) -> tuple[str, str]:
    """(law: native, foreign or none; its reason) from the database's `place_law`."""
    from tools.argonia_world import db
    w = db.open("newworld")
    row = next((r for r in w.rows("place_law") if (r["place_id"] if isinstance(r, dict) else r.place_id) == place_id), None)
    if row is None:
        raise ValueError(f"{place_id}: no place_law row in the database: run `python3 -m tools.newworld.build_db`")
    row = row if isinstance(row, dict) else dict(vars(row))
    return row["law_id"], row["why"]


def segs_cross(a, b, c, d) -> bool:
    """Whether segment ab crosses segment cd in plan."""
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (o(a, b, c) * o(a, b, d) < 0) and (o(c, d, a) * o(c, d, b) < 0)


def kit_line(r: dict, bases: dict):
    """A jail kit piece's line in plan: its record box's long axis through the box's middle, in world units."""
    b = overlap.box(r, bases)
    if not b:
        return None
    lo, hi = np.array(b[0], float), np.array(b[1], float)
    mid = (lo + hi) / 2
    if hi[0] - lo[0] >= hi[1] - lo[1]:
        p, q = [lo[0], mid[1], 0.0], [hi[0], mid[1], 0.0]
    else:
        p, q = [mid[0], lo[1], 0.0], [mid[0], hi[1], 0.0]
    from tools.places import build as B
    R = B.rotation(*(r.get("rot") or [0, 0, 0]))
    at = np.asarray(r["pos"], float)
    return tuple((R @ np.array(p) + at)[:2]), tuple((R @ np.array(q) + at)[:2])


def _seg_dist(p, a, b) -> float:
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def find_jail(spaces: dict, src, bases: dict) -> tuple[str, str] | None:
    """(space id, how it was known) of the place's jail interior: the copied room holding the most jail kit (a jail
    door first), or None. A name alone never makes a room a jail."""
    best = None
    for sid, sp in sorted(spaces.items()):
        info = sp.get("space") or {}
        if sid == "exterior" or not info.get("copy_of"):
            continue
        kit = [r for r in room_things(sp, src, bases) if JAIL_WORD.search(str((bases.get(r.get("base")) or {}).get("edid") or ""))]
        doors = sum(1 for r in kit if r.get("kind") == "door")
        if kit and (best is None or (doors, len(kit)) > best[0]):
            best = ((doors, len(kit)), sid, f"its room holds the jail kit ({doors} jail doors, {len(kit) - doors} bars and walls)")
    return (best[1], best[2]) if best else None


def room_things(sp: dict, src, bases: dict) -> list[dict]:
    """The copied room's refs as the build makes them, with the rows the place adds to it."""
    info = sp["space"]
    src_sp = src.spaces.get(info["copy_of"].split("/", 1)[1])
    keep = interiors.kept(info["copy_of"], info.get("room"))
    built = interiors.built_room(src_sp.refs if src_sp else [], keep, sp["refs"])
    return built + [o for o in sp["refs"] if not o.get("src") and not o.get("removed")]


def _clear(p, things: list[dict], bases: dict, pad: float = 16.0) -> bool:
    """A point clear of the room's things by the build's rule (its shell and walls hold the room)."""
    return not any(t.get("kind") in overlap.SOLID - {"building", "static"} and math.dist(t["pos"][:2], p[:2]) < 1024
                   and overlap.inside(p, t, bases, z=False, pad=pad) for t in things)


def plan_jail(place_id: str, sid: str, things: list[dict], bases: dict, into) -> dict:
    """The cell, the marker and the chests' places for the jail room `sid`: {bed: ref or None, bed_row: an added
    bedroll or None, marker: [x, y, z], chests: [[x, y, z], [x, y, z]], door: the cell's locking door or None,
    how: why this cell}. Raises ValueError when the room has neither a bed nor bars."""
    name = lambda r: str((bases.get(r.get("base")) or {}).get("edid") or "")  # noqa: E731
    kit = [r for r in things if JAIL_WORD.search(name(r)) and r.get("kind") in ("static", "door", "building", "activator")]
    lines = [ln for ln in (kit_line(r, bases) for r in kit) if ln]
    beds = sorted((r for r in things if r.get("kind") == "furniture" and interiors.is_bed(bases.get(r.get("base")) or {})),
                  key=lambda r: str(r.get("src") or r["id"]))
    locking = [r for r in things if r.get("kind") == "door" and not interiors.door_target(r) and not r.get("door")
               and (r.get("lock") or JAIL_WORD.search(name(r)))]
    into = into or (things[0]["pos"] if things else [0.0, 0.0, 0.0])

    def behind(p) -> bool:
        return any(segs_cross(into[:2], p[:2], a, b) for a, b in lines)

    bed, door, how, bed_row = None, None, "", None
    pairs = sorted(((math.dist(b["pos"][:2], d["pos"][:2]), str(b.get("src") or b["id"]), b, d)
                    for b in beds for d in locking if math.dist(b["pos"][:2], d["pos"][:2]) <= CELL_REACH), key=lambda t: t[:2])
    if pairs:
        _, _, bed, door = pairs[0]
        how = f"a bed by a door that locks ({name(door)})"
    elif lines and [b for b in beds if behind(b["pos"])]:
        cx = np.mean([r["pos"] for r in kit], axis=0)
        bed = min((b for b in beds if behind(b["pos"])), key=lambda b: (math.dist(b["pos"][:2], cx[:2]), str(b.get("src") or b["id"])))
        how = "a bed behind the room's bars"
    elif lines:
        floor = min(r["pos"][2] for r in kit)
        xs = [v for a, b in lines for v in (a[0], b[0])]
        ys = [v for a, b in lines for v in (a[1], b[1])]
        mids = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in lines]
        cx = (sum(m[0] for m in mids) / len(mids), sum(m[1] for m in mids) / len(mids))
        best = None
        for gx in np.arange(math.floor((min(xs) - 256) / GRID) * GRID, max(xs) + 256 + 1, GRID):
            for gy in np.arange(math.floor((min(ys) - 256) / GRID) * GRID, max(ys) + 256 + 1, GRID):
                p = [float(gx), float(gy), float(floor)]
                if not behind(p) or any(_seg_dist(p, a, b) < BAR_CLEAR for a, b in lines) or not _clear(p, things, bases, 48.0):
                    continue
                key = (-sum(1 for m in mids if math.dist(m, p[:2]) <= KIT_REACH), math.dist(p[:2], cx), p[0], p[1])
                if best is None or key < best[0]:
                    best = (key, p)
        if best is None:
            raise ValueError(f"{sid}: no floor behind the room's bars clear of its things")
        bed_row = {"id": io.mint(place_id, "jail", sid, "bed"), "base": BEDROLL, "kind": "furniture",
                   "pos": [round(v, 2) for v in best[1]], "rot": [0.0, 0.0, 0.0], "scale": 1.0, "layer": "place",
                   "flags": [], "src": None, "seat": {"mode": "free"},
                   "why": WHY.format(place=place_id, what="the prisoner's bed: the room's bars hold no bed")}
        bed = bed_row
        how = "behind the room's bars, most enclosed by them (no bed there: a bedroll of ours)"
    elif beds:
        bed = max(beds, key=lambda b: (math.dist(b["pos"][:2], into[:2]), str(b.get("src") or b["id"])))
        how = "the bed farthest from the way in (the room has no bars and no door that locks)"
    else:
        raise ValueError(f"{sid}: the jail room holds neither a bed nor bars to keep a prisoner")
    # the marker beside the bed, behind the bars where there are bars, clear of the room's things
    marker = None
    for r_ in MARKER_OFF:
        for j in range(16):
            a = j * math.pi / 8
            p = [bed["pos"][0] + r_ * math.cos(a), bed["pos"][1] + r_ * math.sin(a), bed["pos"][2]]
            if (not lines or behind(p)) and all(_seg_dist(p, a_, b_) >= BAR_CLEAR for a_, b_ in lines) and _clear(p, things, bases):
                marker = [round(v, 2) for v in p]
                break
        if marker:
            break
    if marker is None:
        raise ValueError(f"{sid}: no floor beside the jail's bed clear of the room's things")
    # the evidence chests: stepped in from where one arrives, clear of the room's things and of each other
    chests = []
    d_ = math.dist(into[:2], marker[:2]) or 1.0
    ux, uy = (marker[0] - into[0]) / d_, (marker[1] - into[1]) / d_
    for k in range(2):
        x0, y0 = into[0] + ux * 192.0 - uy * (96.0 if k else -96.0), into[1] + uy * 192.0 + ux * (96.0 if k else -96.0)
        for dx, dy in [(0.0, 0.0)] + list(overlap.SHIFTS):
            p = [x0 + dx, y0 + dy, float(into[2])]
            if _clear(p, things, bases) and all(math.dist(p[:2], c[:2]) >= 96 for c in chests) and (not lines or not behind(p)):
                chests.append([round(v, 2) for v in p])
                break
    if len(chests) < 2:
        raise ValueError(f"{sid}: no floor by the way in for the evidence chests")
    return {"bed": bed, "bed_row": bed_row, "marker": marker, "chests": chests, "door": door, "how": how}


def apply(st, log=print) -> None:
    """The stage: the jail's rows and place.json's crime row `jail` (None where the place has no jail)."""
    pid = st.place_id
    spaces = st.files["spaces"]
    crime = next((f for f in st.place.get("factions") or [] if f.get("kind") == "crime"), None)
    if crime is None:
        log(f"draft jail {pid}: place.json has no crime faction row")
        return
    mine = {r["id"] for sp in spaces.values() for r in sp["refs"] if str(r.get("why") or "").endswith("(draft jail)")}
    for sp in spaces.values():  # this stage's own rows are made again from the rule
        sp["refs"] = [r for r in sp["refs"] if r["id"] not in mine]
    kind, why = law(pid)
    crime.update({"law": kind, "law_why": why, "jail": None, "owing": None})
    if kind == "native":
        owing(st, crime, log)
        return
    if kind != "foreign":
        log(f"draft jail {pid}: {why}: no sentence")
        return
    found = find_jail(spaces, st.src, st.bases)
    if found is None:
        crime["jail"] = None
        log(f"draft jail {pid}: no jail interior: the crime faction fines only")
        return
    sid, known = found
    sp = spaces[sid]
    door_from = next((r for r in spaces["exterior"]["refs"] if r["id"] == sp["space"].get("door_from")), None)
    if door_from is None or not (door_from.get("door") or {}).get("arrival"):
        raise ValueError(f"{sid}: the jail's town door {sp['space'].get('door_from')} has no arrival outside: run `draft streets {pid}`")
    into = (door_from["door"] or {}).get("to_pos")
    for b in (STOLEN_CHEST, INVENTORY_CHEST, PRISON_MARKER, BEDROLL):
        st.bases.setdefault(b, {"key": b, "edid": "", "bounds": None})
    got = plan_jail(pid, sid, room_things(sp, st.src, st.bases), st.bases, into)
    release = [round(float(v), 2) for v in door_from["door"]["arrival"][:3]]
    back = next((r for r in sp["refs"] if (r.get("door") or {}).get("to_ref") == door_from["id"]), None)
    out_rot = [0.0, 0.0, round(float(((back or {}).get("door") or {}).get("to_rot", [0, 0, 0])[2]), 5)]
    ext_id, in_id = io.mint(pid, "jail", "exterior"), io.mint(pid, "jail", sid, "marker")
    rows_in = [] if got["bed_row"] is None else [got["bed_row"]]
    rows_in.append({"id": in_id, "base": PRISON_MARKER, "kind": "marker", "pos": got["marker"], "rot": [0.0, 0.0, 0.0],
                    "scale": 1.0, "layer": "place", "flags": ["persistent"], "src": None, "seat": {"mode": "free"},
                    "door": {"to_space": "exterior", "to_ref": ext_id, "to_pos": release, "to_rot": out_rot},
                    "why": WHY.format(place=pid, what="the jail marker: where an arrest puts the player")})
    for k, (key, what) in enumerate(((STOLEN_CHEST, "stolen goods"), (INVENTORY_CHEST, "player inventory"))):
        rows_in.append({"id": io.mint(pid, "jail", sid, key), "base": key, "kind": "container", "pos": got["chests"][k],
                        "rot": [0.0, 0.0, 0.0], "scale": 1.0, "layer": "place", "flags": ["persistent"], "src": None,
                        "seat": {"mode": "free"}, "owner": f"{pid}.crime",
                        "why": WHY.format(place=pid, what=f"the {what} evidence chest")})
    sp["refs"] += rows_in
    spaces["exterior"]["refs"].append(
        {"id": ext_id, "base": PRISON_MARKER, "kind": "marker", "pos": release, "rot": out_rot, "scale": 1.0, "layer": "place",
         "flags": ["persistent"], "src": None, "seat": {"mode": "free"},
         "door": {"to_space": sid, "to_ref": in_id, "to_pos": got["marker"], "to_rot": [0.0, 0.0, 0.0]},
         "why": WHY.format(place=pid, what="the release point outside the jail's town door")})
    bed = got["bed"]
    crime["jail"] = {"space": sid, "known": known, "cell": got["how"], "bed": bed["id"] if got["bed_row"] else bed.get("src") or bed["id"],
                     "door": (got["door"] or {}).get("src") or (got["door"] or {}).get("id"),
                     "marker": in_id, "exterior": ext_id, "stolen": rows_in[-2]["id"], "inventory": rows_in[-1]["id"]}
    log(f"draft jail {pid}: {sid} ({known}); cell: {got['how']}; marker at {[round(v) for v in got['marker']]}, "
        f"release at {[round(v) for v in release]}")


# --- the Owing (native law) ---
WALKABLE = {"building", "static", "furniture"}


def stand(x: float, y: float, things: list[dict], bases: dict, ground) -> tuple[float, dict | None]:
    """Where one stands at (x, y): on the top of a piece built there that reaches down to the ground or the water and
    stands no more than STAND_REACH above it (a deck on its piles, a walkway), the highest; else on the ground (or the
    water's surface, where it is higher). Returns (the height, the piece stood on or None)."""
    g = ground.height(x, y)
    if g is None:
        raise ValueError(f"{x:.0f}, {y:.0f} is off the ground the place reaches")
    w = ground.water(x, y)
    low = max(g, w) if w is not None else g
    tops = []
    for t in things:
        if t.get("kind") not in WALKABLE or math.dist(t["pos"][:2], (x, y)) > 2048 or not overlap.inside([x, y, 0.0], t, bases, z=False):
            continue
        b = overlap.box(t, bases)
        top, bottom = t["pos"][2] + b[1][2], t["pos"][2] + b[0][2]
        if bottom <= low + 64.0 and low < top <= low + STAND_REACH:
            tops.append((top, t["id"], t))
    if not tops:
        return round(low, 2), None
    top, _, piece = max(tops, key=lambda v: (v[0], v[1]))
    return round(top, 2), piece


def stand_z(x: float, y: float, things: list[dict], bases: dict, ground) -> float:
    return stand(x, y, things, bases, ground)[0]


def seat_on(pos: list[float], things: list[dict], bases: dict, ground) -> dict:
    """A row's seat where it stands: `on` the piece under it (it rests on the deck), else free."""
    z, piece = stand(pos[0], pos[1], things, bases, ground)
    return {"mode": "on", "on": piece["id"], "dz": round(z - piece["pos"][2], 2)} if piece and abs(z - pos[2]) < 0.01 else {"mode": "free"}


def work_spot(people: list[dict]) -> tuple[tuple[float, float], str]:
    """Where the place's labour is done: the landing (the boat-stop operator's work stop), else the exterior work
    stop most of its people share."""
    for p in sorted(people, key=lambda p: p["id"]):
        w = p.get("work") or {}
        if any(s.get("kind") == "boat-stop" for s in p.get("services") or []) and w.get("space", "exterior") == "exterior" and w.get("pos"):
            return (float(w["pos"][0]), float(w["pos"][1])), "the landing, where the boatman works: loading and hauling"
    count: dict[tuple, int] = {}
    for p in people:
        w = p.get("work") or {}
        if w.get("space", "exterior") == "exterior" and w.get("pos"):
            k = (round(float(w["pos"][0]), 1), round(float(w["pos"][1]), 1))
            count[k] = count.get(k, 0) + 1
    if not count:
        raise ValueError("no one of the place works outside: the Owing has no work spot")
    k, n = max(sorted(count.items()), key=lambda kv: kv[1])
    return k, f"the work stop {n} of the place's people share"


def street_points(paths: list[dict], step: float = 64.0):
    """Every point along the place's streets, `step` apart."""
    for p in paths:
        pts = p.get("points") or []
        for a, b in zip(pts, pts[1:]):
            d = math.dist(a[:2], b[:2])
            for i in range(max(1, int(d // step))):
                t = i * step / d if d else 0.0
                yield (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if pts:
            yield tuple(pts[-1][:2])


def plan_owing(place_id: str, things: list[dict], people: list[dict], paths: list[dict], bases: dict, ground) -> dict:
    """The Owing's spots: {work: [x, y, z], work_how, back: [x, y, z], bed: [x, y, z], chest: [x, y, z]}."""
    (wx, wy), how = work_spot(people)
    work = [round(wx, 2), round(wy, 2), stand_z(wx, wy, things, bases, ground)]
    cand = sorted((math.dist(p, (wx, wy)), p) for p in street_points(paths) if math.dist(p, (wx, wy)) >= RETURN_MIN)
    if not cand:
        raise ValueError(f"{place_id}: no street stands {RETURN_MIN:.0f} units from the work spot: lay the streets first")
    bx, by = cand[0][1]
    back = [round(bx, 2), round(by, 2), stand_z(bx, by, things, bases, ground)]
    bed = None
    for r_ in MARKER_OFF:
        for j in range(16):
            a = j * math.pi / 8
            x, y = wx + r_ * math.cos(a), wy + r_ * math.sin(a)
            try:
                z = stand_z(x, y, things, bases, ground)
            except ValueError:
                continue
            if abs(z - work[2]) <= 16.0 and _clear([x, y, z], things, bases):
                bed = [round(x, 2), round(y, 2), z]
                break
        if bed:
            break
    if bed is None:
        raise ValueError(f"{place_id}: no floor beside the Owing's work spot clear of the place's things for its bedroll")
    return {"work": work, "work_how": how, "back": back, "bed": bed,
            "chest": [back[0], back[1], round(back[2] - CHEST_DEPTH, 2)]}


def owing(st, crime: dict, log=print) -> None:
    """The Owing's rows outside and the crime row's `owing`."""
    pid = st.place_id
    ext = st.files["spaces"]["exterior"]["refs"]
    for b in (STOLEN_CHEST, PRISON_MARKER, BEDROLL):
        st.bases.setdefault(b, {"key": b, "edid": "", "bounds": None})
    got = plan_owing(pid, [r for r in ext if not r.get("removed")], st.files["people"], st.files.get("paths") or [], st.bases, st.G)
    back_id, work_id = io.mint(pid, "owing", "return"), io.mint(pid, "owing", "work")
    bed_id, chest_id = io.mint(pid, "owing", "bed"), io.mint(pid, "owing", STOLEN_CHEST)
    face = round(math.atan2(got["back"][0] - got["work"][0], got["back"][1] - got["work"][1]) % (2 * math.pi), 5)
    things = [r for r in ext if not r.get("removed")]
    row = lambda i, base, kind, pos, what, **kw: {"id": i, "base": base, "kind": kind, "pos": pos, "rot": [0.0, 0.0, kw.pop("rz", 0.0)],  # noqa: E731
                                                   "scale": 1.0, "layer": "place", "flags": ["persistent"], "src": None,
                                                   "seat": seat_on(pos, things, st.bases, st.G) if kind != "container" else {"mode": "free"},
                                                   **kw, "why": OWING_WHY.format(place=pid, what=what)}
    ext += [
        row(back_id, PRISON_MARKER, "marker", got["back"], "the return spot: where the player stands when the sentence ends",
            rz=face, door={"to_space": "exterior", "to_ref": work_id, "to_pos": got["work"], "to_rot": [0.0, 0.0, 0.0]}),
        row(work_id, PRISON_MARKER, "marker", got["work"], f"the work spot: {got['work_how']}",
            door={"to_space": "exterior", "to_ref": back_id, "to_pos": got["back"], "to_rot": [0.0, 0.0, face]}),
        row(bed_id, BEDROLL, "furniture", got["bed"], "the worker's mat: lying down on it serves the sentence"),
        row(chest_id, STOLEN_CHEST, "container", got["chest"], "the stolen goods chest, out of reach", owner=f"{pid}.crime"),
    ]
    from tools.places.seat import seat_all
    seat_all(ext, st.G)   # each row rests on its deck as the seating stage has it
    crime["owing"] = {"work": work_id, "return": back_id, "bed": bed_id, "stolen": chest_id, "work_at": got["work_how"]}
    log(f"draft jail {pid}: the Owing: work at {[round(v) for v in got['work']]} ({got['work_how']}), "
        f"return at {[round(v) for v in got['back']]}")
