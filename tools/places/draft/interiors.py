"""Interiors: every enterable building brings its interior as a copy of the source space, its doors paired.

A source interior reached by several exterior doors is copied once per door, so each house has its own, unless its
ways out all open into one walkable island (by the room rule below): that is one building with several doors (a front
and a back door, a door on each floor), copied once with every one of its doors paired to the copy. When the
source packs several rooms into one interior cell (one room behind each door), the copy keeps one room: the builder's
room rule (tools.places.build.room_partition: the walkable island reached from its own way out, each ref to the door
island nearest it), so the drafter's beds and stops are exactly what the build keeps. An interior reached only from
another interior is copied once per copy of its parent. A copy brings everything of the source space but its actors
(our people come from people.jsonl), or of a shared cell only its own room; its refs file holds only our changes: its own way out re-pointed at our door, the
other rooms' ways out inside the kept room removed, inner doors at our copies, and every Nordic piece (by the
Nordic review, decision 0006) replaced as the exterior's are, its plane matched for a directional piece, or removed
with a ledger reason.
"""
from __future__ import annotations

import functools
import json
import math
import re
import tempfile
from pathlib import Path

from tools.places.draft import geom
from tools.places.draft.io import Bundle, mint

DIRECTIONAL = {"door", "building", "static", "furniture", "activator"}

BED = re.compile(r"bed(?!side)|bedroll|hammock|sleep", re.I)
DOUBLE = re.compile(r"double|dbl", re.I)


def rooms_of(copy_of: str) -> dict[str, frozenset]:
    """{way-out door ref: the source refs its room keeps} of a shared source cell, read and partitioned exactly as
    the builder does (its source cell from every plugin of the source, then room_partition; both cached by build)."""
    return {k: frozenset(v["refs"]) for k, v in _partition(copy_of).items()}


def on_room_mesh(copy_of: str, room: str, pos) -> bool:
    """Whether a point of a shared source cell stands on its room's walkable mesh (within the build's reach of a
    stop): a bed outside every wall of the cell (a builder's leftover in the void) stands on none."""
    from tools.places import build
    m = _partition(copy_of).get(room, {}).get("mesh") or {}
    V, T = m.get("verts") or [], m.get("tris") or []
    for t in T:
        cx = sum(V[i][0] for i in t) / 3
        cy = sum(V[i][1] for i in t) / 3
        cz = sum(V[i][2] for i in t) / 3
        if math.hypot(cx - pos[0], cy - pos[1]) <= 2 * build.COVER_PLAN and abs(cz - pos[2]) <= build.COVER_Z:
            return True
    return False


@functools.lru_cache(maxsize=None)
def _partition(copy_of: str) -> dict:
    from tools.places import build
    plugin, cell = build.resolve_copy(copy_of)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        got = [c for c in (build.source_cell(p, cell, tmp / "src.json") for p in plugin.split("|")) if c]
        if not got:
            return {}
        refs = list(got[0]["refs"])
        seen = {r["fk"] for r in refs}
        for more in got[1:]:
            refs += [r for r in more["refs"] if r["fk"] not in seen]
        return build.room_partition(copy_of, refs, tmp)["rooms"]


def in_cut(cut: dict | None, pos) -> bool:
    """Whether a source position lies inside a copy's cut (the build's rule: tools.places.build.in_cut)."""
    from tools.places import build
    return build.in_cut(cut, pos)


@functools.lru_cache(maxsize=None)
def _cut_ids(copy_of: str, box: tuple) -> frozenset:
    from tools.places.draft import io
    source_id, cell = copy_of.split("/", 1)
    path = io.BUNDLES / f"src.{source_id}" / "spaces" / cell / "refs.jsonl"
    return frozenset(r["id"] for r in io.read_jsonl(path) if "pos" in r and in_cut({"box": box}, r["pos"]))


def kept(copy_of: str | None, room: str | None, cut: dict | None = None) -> frozenset | None:
    """The source refs a copy keeps (None: the whole space): its room's, and of those only the ones inside its cut."""
    if not copy_of or (not room and not cut):
        return None
    keep = rooms_of(copy_of).get(room, frozenset()) if room else None
    if cut:
        inside = _cut_ids(copy_of, tuple(cut["box"]))
        keep = inside if keep is None else keep & inside
    return keep


def shared(refs: list[dict], src: Bundle) -> bool:
    """Whether a source cell must be cut to the room behind its way out: it packs several ways out (rooms of several
    houses), or it has a load door whose partner's cell the source bundle does not hold (a deck or a room reached only
    through a cell we do not copy: nobody could walk to it in the copy)."""
    load = [r for r in refs if r.get("door") and (r["door"].get("to_ref") or r["door"].get("to_space"))]
    return sum(1 for r in load if door_target(r) == "exterior") > 1 or any(door_target(r) not in src.spaces for r in load)


def one_building(copy_of: str, refs: list[dict]) -> bool:
    """Whether a source cell with several ways out to the exterior is one building with several doors: every way out
    opens into the same walkable island of the cell (the room rule's islands)."""
    load = [r for r in refs if r.get("door") and (r["door"].get("to_ref") or r["door"].get("to_space"))]
    outs = [r["id"] for r in load if door_target(r) == "exterior"]
    if len(outs) < 2:
        return False
    rooms = rooms_of(copy_of)
    return len({rooms.get(o) for o in outs}) == 1 and rooms.get(outs[0]) is not None


def door_target(r: dict) -> str | None:
    return (r.get("door") or {}).get("to_space")


def nowhere(r: dict) -> bool:
    """A load door (it names a destination) whose destination's space the source bundle does not hold."""
    d = r.get("door") or {}
    return bool(d.get("to_ref")) and d.get("to_space") is None


def _name(b: dict) -> str:
    return f"{b.get('edid', '')} {b.get('name', '')} {b.get('model', '')}"


def is_bed(b: dict) -> bool:
    return bool(BED.search(_name(b)))


def sleeps(b: dict) -> int:
    return 2 if DOUBLE.search(_name(b)) else 1


def beds_in(space_refs: list[dict], bases: dict, room: str | None = None, copy_of: str | None = None,
            cut: dict | None = None) -> list[dict]:
    """Bed refs of a space (of one room when `room` names its way-out door, and on that room's walkable mesh; inside
    its cut when it has one), each with the sleepers it takes."""
    keep = kept(copy_of, room, cut)
    out = []
    for r in space_refs:
        if r.get("kind") != "furniture" or not is_bed(bases.get(r.get("base")) or {}):
            continue
        if keep is not None and (r["id"] not in keep or (room and not on_room_mesh(copy_of, room, r["pos"]))):
            continue
        out.append({"ref": r["id"], "sleeps": sleeps(bases.get(r.get("base")) or {})})
    return sorted(out, key=lambda b: b["ref"])


def swap(r: dict, bases: dict, rep: dict) -> dict:
    """A ref's replacement set where the original stood: its plane matched to the original's for a directional piece
    (geom.align), else turned by the replacement's own turn."""
    al = geom.align(bases.get(r["base"]) or {}, bases.get(rep["base"]) or {}, rep.get("turn_deg")) \
        if r.get("kind") in DIRECTIONAL else None
    rot = list(r.get("rot") or [0, 0, 0])
    yaw = rot[2]
    rot[2] = round((yaw + math.radians(al["turn_deg"] if al else float(rep.get("turn_deg", 0)))) % (2 * math.pi), 5)
    pos = list(r["pos"])
    out = {"base": rep["base"], "rot": rot}
    if al:
        sx, sy = geom.turn(al["shift_local"], yaw)
        pos = [round(pos[0] + sx, 2), round(pos[1] + sy, 2), pos[2]]
        out["align"] = {"turn_deg": al["turn_deg"], "shift": [round(sx, 1), round(sy, 1)], "of": r["base"]}
    out["pos"] = pos
    return out


def built_room(src_refs: list[dict], keep: frozenset | None, overrides: list[dict]) -> list[dict]:
    """A copied room's refs as the build makes them: the source cell's kept room, each ref as its override row has it,
    less what the rows remove, people aside."""
    ov = {o["src"]: o for o in overrides if o.get("src")}
    out = []
    for r in src_refs:
        if r.get("kind") == "actor" or (keep is not None and r["id"] not in keep):
            continue
        row = ov.get(r["id"])
        if row is None:
            out.append(r)
        elif not row.get("removed"):
            out.append({**r, **{k: v for k, v in row.items() if k in ("base", "pos", "kind", "radius")}})
    return out


def own_lights(src_refs: list[dict], overrides: list[dict]) -> tuple[list[dict], int, int]:
    """The room's override rows with every light on the source's own base: a row that put a light on another base for
    its shadows (`twin_of`) goes back to that base, and is dropped when it then says nothing the source ref does not.
    Returns (rows, restored, dropped)."""
    by_id = {r["id"]: r for r in src_refs}
    out, restored, dropped = [], 0, 0
    for o in overrides:
        if not o.get("twin_of"):
            out.append(o)
            continue
        row = {k: v for k, v in o.items() if k != "twin_of"}
        row["base"] = o["twin_of"]
        r = by_id.get(o.get("src"))
        plain = r is not None and {k: v for k, v in row.items() if k not in ("id", "src", "seat")} == \
            {k: v for k, v in r.items() if k not in ("id", "src")} and row.get("seat") == {"mode": "free"}
        if plain:
            dropped += 1
        else:
            out.append(row)
            restored += 1
    return out, restored, dropped


SITE = re.compile(r"mine|cave|cavern|quarry|crypt|tomb|barrow|ruin|sewer|catacomb|dungeon|grotto|vault|lair", re.I)


def record_text(place_id: str, rec: dict, gives: list[dict]) -> str:
    """What our record says of the place: its row, its promises and the stories' needs, as one lower-case text."""
    try:
        from tools.places import needs as needs_mod
        nd = needs_mod.read(place_id)
    except (FileNotFoundError, OSError, ValueError):
        nd = {}
    return json.dumps([rec, gives, nd], default=str).lower()


def unused_rooms(src: Bundle, ext: list[dict], text: str) -> dict[str, str]:
    """{source exterior door: why} for each door into a site of the source's (a mine, a cave, a crypt: a source cell
    whose name says it is one) that our record never names: the place is drafted to deliver what the record says of
    it, so the source's site goes with its door and the pieces of its mouth (`mouth`)."""
    out = {}
    for d in ext:
        t = door_target(d)
        sp = src.spaces.get(t) if t and t != "exterior" else None
        if sp is None:
            continue
        label = f"{t} {sp.meta.get('name') or ''}"
        m = SITE.search(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", label))
        if m and m.group(0).lower() not in text:
            out[d["id"]] = f"the record has no use for the source's {m.group(0).lower()} ({t}): its door and mouth go"
    return out


MOUTH = 640.0   # units round a dropped site's door within which a group of pieces with no door of its own is its mouth


def mouth(door: dict, clusters, of: dict, by_src: dict) -> set[str]:
    """The source refs that make a dropped site's mouth: the door, and every cluster but the door's own whose middle
    stands within MOUTH of it and that holds no door (the rock face, the cart, the lamp of a mine's entrance)."""
    out = {door["id"]}
    for c in clusters:
        if c.id == of.get(door["id"]):
            continue
        refs = [by_src[i] for i in c.members if i in by_src]
        if not refs or any(r.get("kind") == "door" for r in refs):
            continue
        mx = sum(r["pos"][0] for r in refs) / len(refs)
        my = sum(r["pos"][1] for r in refs) / len(refs)
        if math.dist((mx, my), door["pos"][:2]) <= MOUTH:
            out |= {r["id"] for r in refs}
    return out


def plan(place_id: str, src: Bundle, ext_doors: list[dict], our_door_id: dict[str, str], bases: dict | None = None,
         replace: dict | None = None, ledger: list | None = None) -> dict:
    """{our_space_id: {space_id, copy_of, src_space, door_from, door_back, room, parent, name, overrides}}.

    ext_doors: the source's exterior door refs we placed; our_door_id: source ref id -> our ref id (exterior).
    """
    source_id = src.meta.get("source_id") or src.meta["bundle_id"].removeprefix("src.")
    spaces: dict[str, dict] = {}
    uses: dict[str, int] = {}
    queue: list[tuple[str, str, str, str, tuple]] = []
    by_target: dict[str, list[dict]] = {}
    for d in sorted(ext_doors, key=lambda r: r["id"]):
        t = door_target(d)
        if t and t in src.spaces and t != "exterior":
            by_target.setdefault(t, []).append(d)
    house = {t: len(ds) > 1 and one_building(f"{source_id}/{t}", src.spaces[t].refs) for t, ds in by_target.items()}
    also: dict[str, str] = {}   # a further door of one building: its source ref -> our exterior door
    for t, ds in by_target.items():
        for d in (ds[:1] if house[t] else ds):
            queue.append((t, our_door_id[d["id"]], d["id"], "exterior", (t,)))
        if house[t]:
            also.update({d["id"]: our_door_id[d["id"]] for d in ds[1:]})
    while queue:
        t, our_from, src_from, parent, chain = queue.pop(0)
        uses[t] = uses.get(t, 0) + 1
        sid = t if uses[t] == 1 else f"{t}.{uses[t]}"
        refs = src.spaces[t].refs
        parent_src = "exterior" if parent == "exterior" else spaces[parent]["src_space"]
        back = sorted((r for r in refs if door_target(r) == parent_src),
                      key=lambda r: ((r.get("door") or {}).get("to_ref") != src_from, r["id"]))
        back_row = back[0] if back else None
        sp = {"space_id": sid, "copy_of": f"{source_id}/{t}", "src_space": t, "door_from": our_from,
              "door_back": mint(place_id, sid, back_row["id"]) if back_row else None,
              "room": back_row["id"] if back_row and shared(refs, src) and not house.get(t) else None,
              "parent": parent, "name": src.spaces[t].meta.get("name"), "overrides": []}
        spaces[sid] = sp
        keep = kept(sp["copy_of"], sp["room"])
        for r in sorted(refs, key=lambda r: r["id"]):
            t2 = door_target(r)
            rep = (replace or {}).get(r.get("base")) if r.get("kind") != "actor" else None
            if not t2 and nowhere(r) and (keep is None or r["id"] in keep):
                # a load door whose destination the source bundle does not hold (another place's room of a cell
                # several places share) leads nowhere in our copy: removed
                sp["overrides"].append({"id": mint(place_id, sid, r["id"]), "src": r["id"], "removed": True})
                continue
            if not t2:
                if rep and (keep is None or r["id"] in keep):   # another room's piece is not in this copy
                    sp["overrides"].append({**r, **swap(r, bases, rep), "id": mint(place_id, sid, r["id"]),
                                            "src": r["id"], "seat": {"mode": "free"}})
                    if ledger is not None:
                        ledger.append({"src": r["id"], "space": t, "copy": sid, "status": "replaced", "base": rep["base"]})
                continue
            row = {**r, "id": mint(place_id, sid, r["id"]), "src": r["id"], "seat": {"mode": "free"}}
            if rep:
                row.update(swap(r, bases, rep))
            if r is back_row:
                row["door"] = {**r["door"], "to_space": parent, "to_ref": our_from}
            elif parent == "exterior" and t2 == "exterior" and house.get(t) and (r.get("door") or {}).get("to_ref") in also:
                # another door of the same building: paired with its own door outside
                ext = also[r["door"]["to_ref"]]
                row["door"] = {**r["door"], "to_space": "exterior", "to_ref": ext}
                sp.setdefault("also", []).append([ext, row["id"]])
            elif t2 == "exterior" and sp["room"]:
                # another room's way out (rooms packed in one cell): not this house's; gone if inside the kept room
                if keep is not None and r["id"] not in keep:
                    continue
                row = {"id": row["id"], "src": r["id"], "removed": True}
            elif t2 in src.spaces and t2 != "exterior" and t2 not in chain:
                queue.append((t2, row["id"], r["id"], sid, chain + (t2,)))
            elif not rep:
                continue
            sp["overrides"].append(row)
    # inner doors point at the copies made of their targets
    for sid, sp in spaces.items():
        for row in sp["overrides"]:
            kids = [k for k, v in spaces.items() if v["door_from"] == row["id"]]
            if kids:
                row["door"] = {**row["door"], "to_space": kids[0], "to_ref": spaces[kids[0]]["door_back"]}
    return spaces
