"""Each place's law: native, foreign or none, with its reason (docs/design/law.md; the lore in
story/lore/topics/labour-and-bondage.md, "Native law").

- None: a hostile or abandoned place, or one with no people. No one there keeps law; its fight is its answer.
- Foreign: the place is kept by an office inherited from the Empire, which keeps the Imperial cells: the Archwardens
  (the successor administration, which holds the old Imperial forts and posts in its name), or a city governed from
  an Imperial institution still standing (Gideon's Governor's Mansion and courthouse, Archon's East Empire Company
  buildings, Soulrest's ex-Imperial civil office). Its sentence is served in the cell of its own fort, keep or city,
  or else of the same keeper's nearest fort, keep or city.
- Native: every other place where people live. Argonian law has no cell: the sentence is the Owing.

    python3 -m tools.newworld.place_law counts
    python3 -m tools.newworld.place_law list            # every place by law
    python3 -m tools.newworld.place_law check
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter

from tools.argonia_world import db
from tools.newworld import frame as f

LIVED = {"inhabited", "garrisoned"}
FOREIGN = re.compile(r"(?<!no )Archwarden|Governor's Mansion|ex-Imperial|East Empire Company")
CELLS = {"fort", "keep", "prison", "city"}           # kinds whose buildings hold an Imperial cell


def derive(w) -> list[dict]:
    disp = {r.place_id: r.disposition_id for r in w.rows("place_danger")}
    places = w.rows("place")
    rows, law, keeper = [], {}, {}
    for p in places:
        held = p.held_by or ""
        if disp[p.id] in ("hostile", "abandoned") or p.status not in LIVED or not (p.population or 0):
            law[p.id] = ("none", f"no one keeps law: {disp[p.id]}, {p.status or 'unpeopled'}")
        elif m := FOREIGN.search(held):
            law[p.id] = ("foreign", f"kept by an office inherited from the Empire ('{m.group(0)}'): {held}")
            keeper[p.id] = m.group(0)
        else:
            law[p.id] = ("native", f"Argonian law, no cell: {held}")
    jails = [p for p in places if p.id in keeper and p.place_kind_id in CELLS]
    for p in places:
        lid, why = law[p.id]
        jail = None
        if lid == "foreign":
            if p.place_kind_id in CELLS:
                jail, why = p.id, why + f"; its own cell ({p.place_kind_id})"
            else:
                j = min((q for q in jails if keeper[q.id] == keeper[p.id]),
                        key=lambda q: math.hypot(q.world_x - p.world_x, q.world_y - p.world_y))
                jail, why = j.id, why + f"; the cell at {j.name}, the same keeper's nearest {j.place_kind_id}"
        rows.append({"place_id": p.id, "law_id": lid, "jail_place_id": jail, "why": why})
    return rows


def assign(w) -> None:
    w.insert_many("place_law", derive(w))


def problems(w) -> list[str]:
    """Every place has its law; a hostile or abandoned place keeps none; a foreign-law place's jail is a foreign-law
    place with a cell."""
    bad = []
    law = {r.place_id: r for r in w.rows("place_law")}
    disp = {r.place_id: r.disposition_id for r in w.rows("place_danger")}
    kinds = {p.id: p.place_kind_id for p in w.rows("place")}
    for pid in kinds:
        r = law.get(pid)
        if r is None:
            bad.append(f"{pid}: no place_law row")
            continue
        if disp[pid] in ("hostile", "abandoned") and r.law_id != "none":
            bad.append(f"{pid}: {disp[pid]} with {r.law_id} law")
        if r.law_id == "foreign" and (law[r.jail_place_id].law_id != "foreign" or kinds[r.jail_place_id] not in CELLS):
            bad.append(f"{pid}: its jail {r.jail_place_id} is not a foreign-law place with a cell")
        if not r.why.strip():
            bad.append(f"{pid}: no reason")
    return bad


def main(argv: list[str]) -> int:
    w = db.open(f.ROOT)
    rows = w.rows("place_law")
    names = {p.id: p.name for p in w.rows("place")}
    if argv[:1] == ["counts"]:
        print(dict(sorted(Counter(r.law_id for r in rows).items())))
        return 0
    if argv[:1] == ["list"]:
        for lid in ("native", "foreign", "none"):
            sel = sorted(names[r.place_id] for r in rows if r.law_id == lid)
            print(f"{lid} ({len(sel)}): {', '.join(sel)}")
        return 0
    if argv[:1] == ["check"]:
        bad = problems(w)
        print("\n".join(bad) or "law: 0 problems")
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
