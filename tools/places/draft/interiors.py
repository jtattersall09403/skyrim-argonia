"""Interiors: every enterable building brings its interior as a copy of the source space, its doors paired.

A source interior reached by several exterior doors is copied once per door, so each house has its own. When the
source packs several rooms into one interior cell (one room behind each door), the copy keeps one room: the builder's
room rule (tools.places.build.room_partition: the walkable island reached from its own way out, each ref to the door
island nearest it), so the drafter's beds and stops are exactly what the build keeps. An interior reached only from
another interior is copied once per copy of its parent. A copy brings everything of the source space but its actors
(our people come from people.jsonl), or of a shared cell only its own room; its refs file holds only our changes: its own way out re-pointed at our door, the
other rooms' ways out inside the kept room removed, and inner doors at our copies.
"""
from __future__ import annotations

import functools
import re
import tempfile
from pathlib import Path

from tools.places.draft.io import Bundle, mint

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


def plan(place_id: str, src: Bundle, ext_doors: list[dict], our_door_id: dict[str, str]) -> dict:
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
              "room": back_row["id"] if back_row and sum(1 for r in refs if door_target(r) == "exterior") > 1 else None,
              "parent": parent, "name": src.spaces[t].meta.get("name"), "overrides": []}
        spaces[sid] = sp
        keep = kept(sp["copy_of"], sp["room"])
        for r in sorted(refs, key=lambda r: r["id"]):
            t2 = door_target(r)
            if not t2:
                continue
            row = {**r, "id": mint(place_id, sid, r["id"]), "src": r["id"], "seat": {"mode": "free"}}
            if r is back_row:
                row["door"] = {**r["door"], "to_space": parent, "to_ref": our_from}
            elif t2 == "exterior" and sp["room"]:
                # another room's way out (rooms packed in one cell): not this house's; gone if inside the kept room
                if keep is not None and r["id"] not in keep:
                    continue
                row = {"id": row["id"], "src": r["id"], "removed": True}
            elif t2 in src.spaces and t2 != "exterior" and t2 not in chain:
                queue.append((t2, row["id"], r["id"], sid, chain + (t2,)))
            else:
                continue
            sp["overrides"].append(row)
    # inner doors point at the copies made of their targets
    for sid, sp in spaces.items():
        for row in sp["overrides"]:
            kids = [k for k, v in spaces.items() if v["door_from"] == row["id"]]
            if kids:
                row["door"] = {**row["door"], "to_space": kids[0], "to_ref": spaces[kids[0]]["door_back"]}
    return spaces
