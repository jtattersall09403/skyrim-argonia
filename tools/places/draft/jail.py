"""`draft jail <place_id>`: the crime faction's jail, as Skyrim.esm gives a hold's crime faction one, where the
place keeps a foreign law that jails.

Who holds the place decides (decision 0032; story/lore/topics/labour-and-bondage.md section 2,
story/lore/topics/prisons.md): the Argonian sentence is not a cell but an obligation of work (the Owing), and the
province now punishes with no prisons and no courts; its prisons were foreign foundations. So a place gets a jail
only when its record's holder (`place.held_by`, the clause before "in", "with" or "alongside") names a foreign power
keeping its own law (the Empire and its offices, a Dunmer Great House, the Thalmor), never one it names as "ex-",
"former" or "old"; a native place has none, and its crime row's `law` says why ("native law: the Owing, no cell").

Measured on Skyrim.esm (`ArgoniaPlacesBuild jail`, CrimeFactionRift, CrimeFactionWhiterun, CrimeFactionFalkreath,
CrimeFactionWinterhold): the faction's JAIL is a persistent PrisonMarker (Skyrim.esm 000004, a door-type marker)
standing outside the jail's town door, whose teleport leads to a second PrisonMarker in the jail's cell (beside the
prisoner's bed, 166 to 174 units from it, by a door that locks) and back; WAIT is the same marker (Riften,
Falkreath, Winterhold); STOL and PLCN are an EvidenceChestStolenGoods (0267E7) and an EvidenceChestPlayerInventory
(108D36) in the jail's room, persistent, empty, not respawning, owned by the crime faction (Falkreath, Whiterun's
PLCN); JOUT is BeggarOutfit (028B60). The guards' arrest lines are vanilla's DialogueCrimeGuards quest, which speaks
to any actor that IsGuard and is in GuardDialogueFaction (people.py gives guards both).

The rule, from the place's own things, where the law jails:
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
The stage writes the rows of what it adds (each with its `why`) and place.json's crime row `jail`.
"""
from __future__ import annotations

import math
import re

import numpy as np

from tools.places.draft import interiors, io, overlap

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
FOREIGN = re.compile(r"(?<![-\w])(?<!ex-)(?:Imperial|Empire|Legion|Penitus|Thalmor|Aldmeri|Dominion|Hlaalu|Redoran|Telvanni|"
                     r"Indoril|Dres)\b")
QUALIFIED = re.compile(r"\b(?:ex|former|old)[- ]+(?:\w+[- ])?(?:Imperial|Empire|Legion|Thalmor|Hlaalu|Redoran|Telvanni|Indoril|Dres)", re.I)
NATIVE = "native law: the Owing, no cell"


def law(record: dict) -> tuple[bool, str]:
    """(whether the place keeps a foreign law that jails, the reason in plain words) from its record's holder."""
    held = str(record.get("held_by") or "")
    holder = re.split(r"\b(?:in|with|alongside)\b|;", held, maxsplit=1)[0]
    clean = QUALIFIED.sub("", holder)
    m = FOREIGN.search(clean)
    if m:
        return True, f"foreign law: held by {holder.strip()} ({m.group(0)} law jails)"
    return False, f"{NATIVE} (held by {held or 'nobody named'})"


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
    from tools.places.draft.run import place_record
    jails, why = law(place_record(pid)[0])
    crime["law"] = why
    if not jails:
        crime["jail"] = None
        log(f"draft jail {pid}: {why}: the crime faction fines only")
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
