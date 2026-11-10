"""Interiors: every enterable building brings its interior as a copy of the source space, its doors paired.

A source interior reached by several exterior doors is copied once per door, so each house has its own. When the
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
import math
import re
import tempfile
from pathlib import Path

from tools.places.draft import geom
from tools.places.draft.io import Bundle, mint

DIRECTIONAL = {"door", "building", "static", "furniture", "activator"}

BED = re.compile(r"bed(?!side)|bedroll|hammock|sleep", re.I)
DOUBLE = re.compile(r"double|dbl", re.I)


@functools.lru_cache(maxsize=None)
def rooms_of(copy_of: str) -> dict[str, frozenset]:
    """{way-out door ref: the source refs its room keeps} of a shared source cell, read and partitioned exactly as
    the builder does (its source cell from every plugin of the source, then room_partition; both cached by build)."""
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
        part = build.room_partition(copy_of, refs, tmp)
    return {k: frozenset(v["refs"]) for k, v in part["rooms"].items()}


def kept(copy_of: str | None, room: str | None) -> frozenset | None:
    """The source refs a copy keeps (None: the whole space)."""
    if not room or not copy_of:
        return None
    return rooms_of(copy_of).get(room, frozenset())


def shared(refs: list[dict], src: Bundle) -> bool:
    """Whether a source cell must be cut to the room behind its way out: it packs several ways out (rooms of several
    houses), or it has a load door whose partner's cell the source bundle does not hold (a deck or a room reached only
    through a cell we do not copy: nobody could walk to it in the copy)."""
    load = [r for r in refs if r.get("door") and (r["door"].get("to_ref") or r["door"].get("to_space"))]
    return sum(1 for r in load if door_target(r) == "exterior") > 1 or any(door_target(r) not in src.spaces for r in load)


def door_target(r: dict) -> str | None:
    return (r.get("door") or {}).get("to_space")


def _name(b: dict) -> str:
    return f"{b.get('edid', '')} {b.get('name', '')} {b.get('model', '')}"


def is_bed(b: dict) -> bool:
    return bool(BED.search(_name(b)))


def sleeps(b: dict) -> int:
    return 2 if DOUBLE.search(_name(b)) else 1


def beds_in(space_refs: list[dict], bases: dict, room: str | None = None, copy_of: str | None = None) -> list[dict]:
    """Bed refs of a space (of one room when `room` names its way-out door), each with the sleepers it takes."""
    keep = kept(copy_of, room)
    out = []
    for r in space_refs:
        if r.get("kind") != "furniture" or not is_bed(bases.get(r.get("base")) or {}):
            continue
        if keep is not None and r["id"] not in keep:
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


def shadow_twins(place_id: str, sid: str, src_refs: list[dict], keep: frozenset | None, overrides: list[dict],
                 light_bases: dict | None = None) -> list[dict]:
    """The room's override rows with its shadow casters beyond the engine's limit switched to their no-shadow twin
    base (lights.shadow_plan): one row per switched light, the source ref as it is but for its base."""
    from tools.places.draft import lights
    lb = lights.light_bases() if light_bases is None else light_bases
    ov = [o for o in overrides if not o.get("twin_of")]     # the plan is made afresh from the source's own lights
    switch, _ = lights.shadow_plan(built_room(src_refs, keep, ov), lb)
    by_src = {o.get("src"): o for o in ov}
    for r in src_refs:
        if r["id"] not in switch:
            continue
        row = by_src.get(r["id"])
        if row is None:
            row = {**r, "id": mint(place_id, sid, r["id"]), "src": r["id"], "seat": {"mode": "free"}}
            ov.append(row)
        row["twin_of"], row["base"] = r["base"], switch[r["id"]]
    return ov


def plan(place_id: str, src: Bundle, ext_doors: list[dict], our_door_id: dict[str, str], bases: dict | None = None,
         replace: dict | None = None, ledger: list | None = None) -> dict:
    """{our_space_id: {space_id, copy_of, src_space, door_from, door_back, room, parent, name, overrides}}.

    ext_doors: the source's exterior door refs we placed; our_door_id: source ref id -> our ref id (exterior).
    """
    source_id = src.meta.get("source_id") or src.meta["bundle_id"].removeprefix("src.")
    spaces: dict[str, dict] = {}
    uses: dict[str, int] = {}
    queue: list[tuple[str, str, str, str, tuple]] = []
    for d in sorted(ext_doors, key=lambda r: r["id"]):
        t = door_target(d)
        if t and t in src.spaces and t != "exterior":
            queue.append((t, our_door_id[d["id"]], d["id"], "exterior", (t,)))
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
              "room": back_row["id"] if back_row and shared(refs, src) else None,
              "parent": parent, "name": src.spaces[t].meta.get("name"), "overrides": []}
        spaces[sid] = sp
        keep = kept(sp["copy_of"], sp["room"])
        for r in sorted(refs, key=lambda r: r["id"]):
            t2 = door_target(r)
            rep = (replace or {}).get(r.get("base")) if r.get("kind") != "actor" else None
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
    for sid, sp in spaces.items():
        sp["overrides"] = shadow_twins(place_id, sid, src.spaces[sp["src_space"]].refs,
                                       kept(sp["copy_of"], sp["room"]), sp["overrides"])
    # inner doors point at the copies made of their targets
    for sid, sp in spaces.items():
        for row in sp["overrides"]:
            kids = [k for k, v in spaces.items() if v["door_from"] == row["id"]]
            if kids:
                row["door"] = {**row["door"], "to_space": kids[0], "to_ref": spaces[kids[0]]["door_back"]}
    return spaces
