"""The world plugin's form ids, one table: every allocator's range in ArgoniaNewWorld.esm, sized for the province.

A local form id is 0x000800..0xFFFFFF. Each allocator owns one range (the references placed by rule own two, either
side of the navmesh's) and gives ids inside it alone; no two ranges overlap. The allocators' own constants
(NewWorld.cs, NewWorldMap.cs, FormIds.cs, atmosphere.py, place.py, edits.py, navmesh/stitch.py and the registry's
blocks in newworld/sources/world_formids.json) are these numbers: tools/tests/test_newworld_idspace.py holds each to
its row.

`faults(plugin)` reads what a build has written (the producers' shards under refs/, the land's grid, the navmesh's
records, the map's markers and teleports, the atmosphere's records) and names every id used twice and every id
outside its allocator's range. The edits stage's check runs it on the shards, and `rebuild.sh preflight` on every
output whose stage is current, so a collision stops the run before the navmesh and the world file are made.

    python3 -m tools.newworld.idspace [--plugin out/newworld/plugin]     the table, and the faults of what is built
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "out/newworld/plugin"
SCOPE = (214, 180)  # the province's grid in cells (the scope stage: the land manifest's cells_x, cells_y)

# (allocator, first, last, how an id is given, the province's count: the grid's by formula, the rest as built 2026-11-11)
RANGES = (
    ("world", 0x000800, 0x000802, "the world, its persistent cell, the start marker (NewWorld.cs)", 3),
    ("region", 0x000880, 0x0008FF, "registry block: one per region", 24),
    ("seeded", 0x000900, 0x00FFFF, "registry: the ids the first world file held, kept as they were (ground, base and water names)", 7265),
    ("ground", 0x010000, 0x01FFFF, "registry block: land textures, their texture sets, grass, registered since", 0),
    ("base", 0x020000, 0x07FFFF, "registry block: placed bases and what they link to, and the travel menu's records, registered since", 0),
    ("atmosphere", 0x080000, 0x080FFF, "by formula from the spec (atmosphere.py BASE: the class sets, reserved; REGION_BASE: a set per region slot)", 817),
    ("travel-give", 0x090000, 0x09000F, "the travel power's give quest, by formula: 0x090000 (NewWorldTravel.cs GiveId; ARG_QF_MQ101.psc NWGiveId)", 1),
    ("music", 0x090100, 0x0901FF, "music records by formula: track slot i 0x090100 + i, its night copy 0x090140 + i, explore type of class j 0x090180 + j (NewWorldMusic.cs)", 29),
    ("dressing", 0x0A0000, 0x0FFFFF, "a small signature thing: a slot by its identity's digest (dressing/place.py fid_of)", 0),
    ("cells", 0x100000, 0x1FFFFF, "cell k of the grid 0x100000 + 2k, its LAND + 1 (NewWorld.cs)", 2 * SCOPE[0] * SCOPE[1]),
    ("placed", 0x200000, 0x5FFFFF, "a reference placed by rule: a slot by its identity's digest (place.py form_ids)", 514240),
    ("navmesh", 0x600000, 0x609677, "the navmesh of grid cell k: 0x600000 + k (navmesh/stitch.py)", SCOPE[0] * SCOPE[1]),
    ("placed-high", 0x609678, 0x6FFFFF, "the same allocator as `placed`, past the navmesh's range", 0),
    ("added", 0x700000, 0x73FFFF, "a thing an edit added: given once by its row, counted (edits.py)", 0),
    ("counted", 0x740000, 0x7FFFFF, "a producer's reference without an id of its own (the mist), counted in shard order (NewWorld.cs)", 21604),
    ("water", 0x800000, 0xEFFFFF, "registry block: water types and their graded blends, registered since", 0),
    ("ecology", 0xF00000, 0xFDFFFF, "an ecology actor: a slot by its identity's digest (ecology/place.py fid_of)", 0),
    ("teleports", 0xFE0000, 0xFEFFFF, "teleport marker k: 0xFE0000 + k (NewWorldMap.cs)", 266),
    ("map-markers", 0xFF0000, 0xFFFFFF, "map marker k: 0xFF0000 + k (NewWorldMap.cs)", 116),
)
SPAN = {name: (lo, hi) for name, lo, hi, _, _ in RANGES}
REGISTRY = ("region", "ground", "base", "water")  # world_formids.json's blocks; `seeded` is its seeded range
PLACED = (SPAN["placed"][0], SPAN["placed-high"][1])  # the rule-placed references' slots run over both, less the hole
HOLE = SPAN["navmesh"]
FID = re.compile(r'"fid":\s*"([0-9A-Fa-f]{6})"')


def size(name: str) -> int:
    lo, hi = SPAN[name]
    return hi - lo + 1


def table_faults() -> list[str]:
    """The table against itself: every range inside the plugin's ids, none reaching into another, each holding the
    province's count, the rule-placed references no more than half their slots (form_ids' own limit)."""
    out = []
    rows = sorted(RANGES, key=lambda r: r[1])
    for name, lo, hi, _, n in rows:
        if not 0x800 <= lo <= hi <= 0xFFFFFF:
            out.append(f"{name}: {lo:06X}..{hi:06X} is not a range of a plugin's own ids")
        if n > hi - lo + 1:
            out.append(f"{name}: the province's {n} do not fit {lo:06X}..{hi:06X}")
    for a, b in zip(rows, rows[1:]):
        if a[2] >= b[1]:
            out.append(f"{a[0]} ({a[1]:06X}..{a[2]:06X}) and {b[0]} ({b[1]:06X}..{b[2]:06X}) overlap")
    if SPAN["navmesh"][1] + 1 != SPAN["placed-high"][0] or SPAN["placed"][1] + 1 != SPAN["navmesh"][0]:
        out.append("the navmesh's range is not the one hole in the rule-placed references' slots")
    return out


def owner_of(i: int) -> str | None:
    for name, lo, hi, _, _ in RANGES:
        if lo <= i <= hi:
            return name
    return None


def shard_ids(d: Path) -> tuple[list[int], int]:
    """One producer's references: the form ids its shard lines carry, and the count of lines without one."""
    given, bare = [], 0
    for f in sorted(Path(d).glob("cy*.jsonl")):
        for ln in f.read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            m = FID.search(ln)
            if m:
                given.append(int(m.group(1), 16))
            else:
                bare += 1
    return given, bare


def navmesh_ids(navi: Path) -> list[int]:
    """The local form ids of the navmesh records a build made (navi.json: the NAVI record, one NVMI a navmesh)."""
    raw = base64.b64decode(json.loads(navi.read_text())["navi"])
    out, p = [], 24
    while p + 6 <= len(raw):
        sig, n = struct.unpack_from("<4sH", raw, p)
        if sig == b"NVMI":
            out.append(struct.unpack_from("<I", raw, p + 6)[0] & 0xFFFFFF)
        p += 6 + n
    return out


def _ids_in(doc, key: str = "formid") -> list[int]:
    """Every local form id a spec names (`formid` values, hex text or a number, at any depth)."""
    out = []
    if isinstance(doc, dict):
        for k, v in doc.items():
            if k == key and isinstance(v, (str, int)):
                out.append(int(v, 16) if isinstance(v, str) else v)
            else:
                out += _ids_in(v, key)
    elif isinstance(doc, list):
        for v in doc:
            out += _ids_in(v, key)
    return out


def faults(plugin: Path | None = None, producers: list[Path] | None = None, skip: frozenset = frozenset(),
           registry: Path | None = None) -> tuple[list[str], dict]:
    """(faults, counts) of what is built under `plugin`. `producers`: the reference shard directories (default every
    directory of plugin/refs). `skip`: parts not to read (their stage runs again first): "refs/<producer>", "grid",
    "navmesh", "map", "atmosphere", "registry". An absent output is not read and not a fault."""
    plugin = Path(plugin or PLUGIN)
    out, counts, held = table_faults(), {}, {}

    def take(ids, who: str, allowed: tuple):
        """Every id of `who` inside one of its own ranges, and held by nothing else."""
        stray, twice = [], []
        for i in ids:
            if not any(SPAN[a][0] <= i <= SPAN[a][1] for a in allowed):
                stray.append(i)
            if i in held:
                twice.append(i)
            else:
                held[i] = who
        if stray:
            names = ", ".join(f"{i:06X} ({owner_of(i) or 'no allocator'}'s)" for i in stray[:4])
            out.append(f"{who}: {len(stray)} ids outside its range ({' and '.join(allowed)}): {names}")
        if twice:
            names = ", ".join(f"{i:06X} (held by {held[i]})" for i in twice[:4])
            out.append(f"{who}: {len(twice)} ids used twice: {names}")

    def span_ids(name: str, n: int, who: str):
        counts[who] = n
        if n > size(name):
            out.append(f"{who}: {n} ids do not fit {name}'s {SPAN[name][0]:06X}..{SPAN[name][1]:06X}")
        take(range(SPAN[name][0], SPAN[name][0] + min(n, size(name))), who, (name,))

    take(range(SPAN["world"][0], SPAN["world"][1] + 1), "the world, its cell and the start marker", ("world",))
    man = plugin / "land/manifest.json"
    if "grid" not in skip and man.exists():
        g = json.loads(man.read_text())["grid"]
        cells = g["cells_x"] * g["cells_y"]
        span_ids("cells", 2 * cells, "cells and their LAND")
        if "navmesh" not in skip:
            counts["navmesh grid"] = cells
            if cells > size("navmesh"):
                out.append(f"navmesh: the grid's {cells} cells do not fit {HOLE[0]:06X}..{HOLE[1]:06X}")
    navi = plugin / "navmesh/navi.json"
    if "navmesh" not in skip and navi.exists():
        ids = navmesh_ids(navi)
        counts["navmesh records"] = len(ids)
        take(ids, "navmesh records", ("navmesh",))
    bare = 0
    dirs = producers if producers is not None else sorted(p for p in (plugin / "refs").glob("*") if p.is_dir())
    for d in dirs:
        if f"refs/{d.name}" in skip:
            continue
        given, b = shard_ids(d)
        counts[f"refs/{d.name}"] = len(given) + b
        take(given, f"references of refs/{d.name}", ("placed", "placed-high", "added"))
        bare += b
    if bare:
        span_ids("counted", bare, "references counted in shard order")
    eco = plugin / "ecology"
    if "ecology" not in skip and eco.is_dir():
        given, _ = shard_ids(eco)
        counts["ecology"] = len(given)
        take(given, "ecology actors", ("ecology",))
    dress = plugin / "dressing"
    if "dressing" not in skip and dress.is_dir():
        given, _ = shard_ids(dress)
        counts["dressing"] = len(given)
        take(given, "dressing references", ("dressing",))
    if "map" not in skip:
        for f, name, key in (("map/teleports.json", "teleports", "teleports"), ("map/markers.json", "map-markers", "markers")):
            p = plugin / f
            if p.exists():
                doc = json.loads(p.read_text())
                rows = doc.get(key, doc) if isinstance(doc, dict) else doc
                span_ids(name, len(rows), name.replace("-", " "))
    atm = plugin / "atmosphere.json"
    if "atmosphere" not in skip and atm.exists():
        ids = _ids_in(json.loads(atm.read_text()))
        counts["atmosphere records"] = len(ids)
        take(ids, "atmosphere records", ("atmosphere",))
    reg = Path(registry or REPO / "newworld/sources/world_formids.json")
    if "registry" not in skip and reg.exists():
        doc = json.loads(reg.read_text())
        n = 0
        for kind, rows in doc["ids"].items():
            n += len(rows)
            take((int(hx, 16) for hx in rows.values()), f"registered {kind} ids", (kind, "seeded"))
        counts["registered names"] = n
    counts["ids"] = len(held)
    return out, counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--plugin", type=Path, default=PLUGIN)
    a = ap.parse_args(argv)
    for name, lo, hi, how, n in RANGES:
        print(f"  {lo:06X}..{hi:06X}  {name:<12} {hi - lo + 1:>9} ids, the province {n:>7}: {how}")
    bad, counts = faults(a.plugin)
    print("built under " + str(a.plugin) + ": " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    for b in bad:
        print("FAIL " + b)
    print("PASS: no id used twice, none outside its allocator's range" if not bad else "FAIL")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
