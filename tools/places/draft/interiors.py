"""Interiors: every enterable building brings its interior as a copy of the source space, its doors paired.

A source interior reached by several exterior doors is copied once per door, so each house has its own. When the
source packs several rooms into one interior cell (one room behind each door), the copy's own room is the part of
the cell nearer its own way out than any other; the copy's beds and people are that room's. An interior reached
only from another interior is copied once per copy of its parent. A copy brings everything of the source space but
its actors (our people come from people.jsonl); its refs file holds only our changes: every door that leads out
re-pointed at our door for it, and inner doors at our copies.
"""
from __future__ import annotations

import math
import re

from tools.places.draft.io import Bundle, mint

BED = re.compile(r"bed(?!side)|bedroll|hammock|sleep", re.I)
DOUBLE = re.compile(r"double|dbl", re.I)


def door_target(r: dict) -> str | None:
    return (r.get("door") or {}).get("to_space")


def beds_in(space_refs: list[dict], bases: dict, room: str | None = None) -> list[dict]:
    """Bed refs of a space (of one room when `room` names its way-out door), each with the sleepers it takes."""
    exits = [r for r in space_refs if door_target(r) == "exterior"] if room else []
    out = []
    for r in space_refs:
        b = bases.get(r.get("base")) or {}
        if r.get("kind") != "furniture":
            continue
        name = f"{b.get('edid', '')} {b.get('name', '')} {b.get('model', '')}"
        if not BED.search(name):
            continue
        if exits and len(exits) > 1:
            near = min(exits, key=lambda d: (math.dist(d["pos"], r["pos"]), d["id"]))
            if near["id"] != room:
                continue
        out.append({"ref": r["id"], "sleeps": 2 if DOUBLE.search(name) else 1})
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
        for r in sorted(refs, key=lambda r: r["id"]):
            t2 = door_target(r)
            if not t2:
                continue
            row = {**r, "id": mint(place_id, sid, r["id"]), "src": r["id"], "seat": {"mode": "free"}}
            if r is back_row:
                row["door"] = {**r["door"], "to_space": parent, "to_ref": our_from}
            elif t2 == "exterior" and r["door"].get("to_ref") in our_door_id:
                # another room's way out (rooms packed in one cell): to our door for that room
                row["door"] = {**r["door"], "to_ref": our_door_id[r["door"]["to_ref"]]}
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
