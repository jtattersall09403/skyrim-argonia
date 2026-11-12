"""Roster check (nw-03b): is each region's creature roster broad, distinct and truly modelled?

The exit test of the creature loop (docs/design/ecology.md, "The roster test"). For every region:

  a. each size class holds at least its floor of kinds (FLOORS; tiny counts the region's critter kinds);
  b. a benign and a hostile kind in each class of TEMPERED (defensive counts as hostile: it fights back);
  c. at least SIGNATURES kinds no bordering region has, and no two regions sharing more than OVERLAP of their kinds
     (Jaccard, as the ecology stage's own check);
  d. each water kind of the region (fresh, brackish, salt; WATER_MIN_M2 of it) has a swimmer of its own;
  e. every kind bound to a true model: records, or a critter base; never dropped, never a `why` that says nearest
     fit or stand-in;
and province-wide (f): distinct actor kinds placed at least SKYRIM_KINDS, the creature races Skyrim.esm places in
Tamriel (measured: tools/newworld/ecology/measure.py's resolution over every ACHR, 38).

    python3 -m tools.newworld.ecology.roster_check          # prints the failures; exit 1 on any
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path("newworld/sources/ecology")
CELL_REGION = Path("out/newworld/cell_region.json")
WATER = Path("out/newworld/water_classified.json")

CLASSES = ("insect", "small", "game", "predator", "giant")
FLOORS = {"land": {"insect": 2, "small": 3, "game": 2, "predator": 3, "giant": 1},
          "sea": {"insect": 1, "small": 3, "game": 1, "predator": 2, "giant": 1}}
TEMPERED = ("insect", "small", "game")
SIGNATURES = 4
OVERLAP = 0.5
SKYRIM_KINDS = 38
WATER_MIN_M2 = 20000.0
BORDER_MIN = 3
FRESH = ("pond", "lake", "river", "stream", "green-marsh", "blackwater-swamp")
SALT = ("ocean", "bay", "shallow-coast")
BRACKISH = ("estuary", "bay", "shallow-coast")
NEAR = re.compile(r"\bnearest\b|stand-?in", re.I)


def true_model(kind: str, bind: dict) -> str | None:
    """None when the kind is bound to a true model, else why not."""
    if kind in bind.get("critter_kinds", {}):
        return None
    b = bind["kinds"].get(kind)
    if b is None:
        return "unbound"
    if not b.get("records"):
        return "dropped"
    if NEAR.search(b.get("why", "")):
        return "nearest fit"
    return None


def neighbours(cell_region: dict[str, str], border_min: int = BORDER_MIN) -> dict[str, set[str]]:
    border = defaultdict(int)
    for key, r in cell_region.items():
        x, y = map(int, key.split(","))
        for o in (f"{x + 1},{y}", f"{x},{y + 1}"):
            s = cell_region.get(o)
            if s and s != r:
                border[tuple(sorted((r, s)))] += 1
    out = defaultdict(set)
    for (a, b), n in border.items():
        if n >= border_min:
            out[a].add(b)
            out[b].add(a)
    return out


def water_kinds(bodies: list[dict]) -> dict[str, set[str]]:
    area = defaultdict(lambda: defaultdict(float))
    for w in bodies:
        if w.get("region_id"):
            area[w["region_id"]][w.get("water_kind_id")] += w.get("area_m2", 0.0)
    out = {}
    for r, kinds in area.items():
        out[r] = {hab for hab, ks in (("water-fresh", FRESH), ("water-salt", SALT), ("water-brackish", BRACKISH))
                  if sum(a for k, a in kinds.items() if k in ks) >= WATER_MIN_M2}
    return out


def check(regions: dict[str, dict], sea: set[str], bind: dict, nbr: dict[str, set[str]],
          water: dict[str, set[str]]) -> tuple[list[str], dict]:
    fails: list[str] = []
    kinds = {r: {c["kind"] for c in d["creatures"]} for r, d in regions.items()}
    for r, d in sorted(regions.items()):
        rows = d["creatures"]
        floor = FLOORS["sea" if r in sea else "land"]
        for cls in CLASSES:
            got = [c for c in rows if c["size_class"] == cls]
            if len(got) < floor[cls]:
                fails.append(f"{r}: a {cls} {len(got)} < {floor[cls]}")
            if cls in TEMPERED and r not in sea:
                temp = {"benign" if c["hostility"] == "benign" else "hostile" for c in got}
                for t in ("benign", "hostile"):
                    if t not in temp:
                        fails.append(f"{r}: b {cls} has no {t} kind")
        own = kinds[r] - set().union(*(kinds.get(n, set()) for n in nbr.get(r, ())))
        if len(own) < SIGNATURES:
            fails.append(f"{r}: c {len(own)} kinds no neighbour has < {SIGNATURES}")
        for hab in sorted(water.get(r, ())):
            if not any(c["habitat"] == hab for c in rows):
                fails.append(f"{r}: d no swimmer of {hab}")
        for c in rows:
            why = true_model(c["kind"], bind)
            if why:
                fails.append(f"{r}: e {c['kind']} {why}")
    names = sorted(regions)
    worst = (0.0, "")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            j = len(kinds[a] & kinds[b]) / max(1, len(kinds[a] | kinds[b]))
            if j > worst[0]:
                worst = (round(j, 3), f"{a}/{b}")
            if j > OVERLAP:
                fails.append(f"{a}/{b}: c overlap {j:.2f} > {OVERLAP}")
    actors = {k for ks in kinds.values() for k in ks
              if k not in bind.get("critter_kinds", {}) and bind["kinds"].get(k, {}).get("records")}
    if len(actors) < SKYRIM_KINDS:
        fails.append(f"province: f {len(actors)} actor kinds < Skyrim's {SKYRIM_KINDS}")
    return fails, {"actor_kinds": len(actors), "all_kinds": len(set().union(*kinds.values())),
                   "worst_overlap": worst}


def load() -> tuple:
    regions = {p.stem: json.loads(p.read_text()) for p in sorted((SRC / "regions").glob("*.json"))}
    sea = set()
    for line in Path("newworld/story/data/db/region.jsonl").read_text().splitlines():
        d = json.loads(line)
        if d.get("kind") == "sea":
            sea.add(d["id"])
    bind = json.loads((SRC / "bindings.json").read_text())
    nbr = neighbours(json.loads(CELL_REGION.read_text())) if CELL_REGION.exists() else {}
    water = water_kinds(json.loads(WATER.read_text())) if WATER.exists() else {}
    return regions, sea, bind, nbr, water


def main(argv: list[str] | None = None) -> int:  # no arguments: it reads the sources (the small world passes none it needs)
    fails, stats = check(*load())
    for f in fails:
        print(f)
    print(f"roster check: {len(fails)} failures; {stats}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
