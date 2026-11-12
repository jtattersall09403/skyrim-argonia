"""Skyrim's own density of small found things outdoors (decision 0034), the dressing stage's density bound.

Counts the placed references in Skyrim.esm's Tamriel exterior cells whose base's editor id names one of the sorts
the dressing places (bones, mushrooms, nests and eggs, insect spawners, ambient effects, mounds, shells and kelp),
per 100 cells holding any reference. Writes newworld/sources/dressing/skyrim_measures.json.

    python -m tools.newworld.dressing.measure"""
from __future__ import annotations

import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "newworld/sources/dressing/skyrim_measures.json"
TAMRIEL = 0x3C
SORTS = {
    "bones": r"bone|skull|skeleton|carcass",
    "fungi": r"mushroom|fung",
    "nests_eggs": r"nest|egg",
    "insects": r"critterspawn|firefly|dragonfl|moth",
    "ambient_fx": r"^fxamb|mist|steam|petal|dust",
    "mounds": r"mound",
    "shore_wrack": r"shell|carapace|kelp|coral|driftwood",
}


def main() -> int:
    from tools.argonia_world.esm import Plugin
    from tools.places.assets.resolve import DATA
    p = Plugin.read(DATA / "Skyrim.esm", {"STAT", "MSTT", "ACTI", "FLOR", "WRLD"})
    sort_of = {}
    for r in p.records():
        if r.sig in ("STAT", "MSTT", "ACTI", "FLOR") and r.edid:
            for s, rx in SORTS.items():
                if re.search(rx, r.edid, re.I):
                    sort_of[r.formid] = s
                    break
    cells: set = set()
    count: Counter = Counter()
    for r in p.records("REFR"):
        if not any(g == 1 and lbl == TAMRIEL for g, lbl in r.parents):
            continue
        cell = next((lbl for g, lbl in reversed(r.parents) if g in (8, 9)), None)   # the cell children group
        cells.add(cell)
        name = r.sub("NAME")
        if name and len(name) >= 4:
            s = sort_of.get(struct.unpack_from("<I", name)[0])
            if s:
                count[s] += 1
    n = max(1, len(cells))
    res = {"about": __doc__.split("\n")[0], "cells_with_refs": len(cells),
           "refs_per_100_cells": {s: round(100 * count[s] / n, 2) for s in SORTS}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
