"""The ground-colour check: each land region shows one dominant ground-cover colour and its own flower grasses.

A region's grass set is every grass its grassy materials can carry there: the region's own list for a material,
else its province's, else the material's base list (texture.py's variant rule). Flower grasses are those the grass
census measures with a flower family, on land (the underwater materials are left out) (yellow, violet, blue, white, pink, orange, red). Checks:

1. no flower grass is in more than one region's set;
2. a region with flower grasses holds those of one family only, its identity sheet's ground.family
   (newworld/sources/identity/regions.json); a sheet family with a flower grass in the load order must be met;
   a sheet family no complete grass in the load order carries is listed as unmet (a sourcing gap, not a fault);
3. neighbouring regions (newworld/sources/identity/adjacency.json) differ in the colour they show;
4. the share of palette grass types two neighbours have in common (shared / union, on the materials whose grass a
   province or region chooses) is at most OVERLAP_MAX; the share over all land grass is printed beside it.

    python -m tools.newworld.dressing.ground_colour [--census PATH]

Exit 1 on any failure. Prints the mean and max neighbour overlap."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CENSUS = REPO / "newworld/sources/dressing/grass_census.json"   # committed source (grass_census.py)
IDENTITY = REPO / "newworld/sources/identity"
OVERLAP_MAX = 0.6
# flower grasses that cannot carry a region's colour on land: under water, snow-covered (decision 0006), or incomplete
NOT_FOR_LAND = {"RockGrassSnow01", "SnowGrass01", "SnowGrass01Forest", "SnowGrass01Light", "SnowGrass02",
                "DLC01SoulCairnGrass01", "ALPAGrassViolet01", "ALPAGrassViolet02", "ALPAGrassViolet03"}
UNDERWATER = {"river_bottom", "river_mud", "ocean_floor"}  # grass under water, by water kind, not by region
FLOWER = {"yellow", "violet", "blue", "white", "pink", "orange", "red"}
# sheet family -> census flower family it is met by
COLOUR_FLOWER = {"yellow": "yellow", "violet": "violet", "white": "white", "pink": "pink", "blue": "blue",
                 "orange": "orange", "red": "red", "red-ochre": "red", "rust-brown": "orange", "pale-chalk": "white"}


def _key(g: str) -> str:
    """'King of the Murkmire.esp:ALPAGrassLupin01' -> 'ALPAGrassLupin01' (edids are unique across the census)."""
    return g.split(":", 1)[1]


def region_sets(tex, palette_only: bool = False) -> dict[str, set[str]]:
    """palette_only: only the lists a province or region chooses (texture.PROVINCES and REGIONS grass); the base
    lists (shore, edge and rock tufts) are one list everywhere, by water kind and habitat."""
    out = {}
    varied = {m for p in tex.PROVINCES.values() for m in p["grass"]} | {m for r in tex.REGIONS.values() for m in r["grass"]}
    grassy = [m for m, v in tex.MATERIALS.items() if (v[1] or m in varied) and m not in UNDERWATER]
    if palette_only:
        grassy = [m for m in grassy if m in varied]
    for prov, p in tex.PROVINCES.items():
        for r in p["regions"]:
            own = tex.REGIONS.get(r, {}).get("grass", {})
            s = set()
            for m in grassy:
                lst = own.get(m) or p["grass"].get(m) or ([] if palette_only else tex.MATERIALS[m][1])
                s |= {_key(g) for g in lst}
            out[r] = s
    return out


def neighbours(path: Path = IDENTITY / "adjacency.json") -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for p in json.loads(path.read_text())["pairs"]:
        r, n = p.split("|")
        adj[r].add(n)
        adj[n].add(r)
    return adj


def sheet_colours(path: Path = IDENTITY / "regions.json") -> dict[str, str]:
    d = json.loads(path.read_text())
    rows = d.get("regions", d)
    items = rows.items() if isinstance(rows, dict) else ((x["id"], x) for x in rows)
    return {k: v["ground"]["family"] for k, v in items}


def check(tex, families: dict[str, str], adj: dict[str, set[str]], colour: dict[str, str]) -> dict:
    sets = region_sets(tex)
    pal = region_sets(tex, palette_only=True)
    faults = []
    holders: dict[str, list[str]] = defaultdict(list)
    for r, s in sets.items():
        for g in s:
            if families.get(g) in FLOWER:
                holders[g].append(r)
    for g, rs in sorted(holders.items()):
        if len(rs) > 1:
            faults.append(f"flower grass {g} in {len(rs)} regions: {', '.join(sorted(rs))}")
    offered = {f for f in families.values() if f in FLOWER}
    wet = {_key(g) for m in UNDERWATER if m in tex.MATERIALS for g in tex.MATERIALS[m][1]} | {k for k in families if k.startswith("TBP")}
    shown, unmet = {}, []
    for r, s in sets.items():
        fams = {families[g] for g in s if families.get(g) in FLOWER}
        want = COLOUR_FLOWER.get(colour.get(r, ""))
        if want and want not in fams:
            free = {g for g, f in families.items() if f == want and not holders.get(g) and g not in NOT_FOR_LAND and g not in wet}
            (faults if free and want in offered else unmet).append(
                f"{r}: sheet {colour.get(r)}, no {want} flower grass held")
        if fams and (not want or fams - {want}):
            faults.append(f"{r}: flower families {sorted(fams)} against its sheet colour {colour.get(r)}")
        shown[r] = colour.get(r) if want in fams else "leaf"
    overlaps, overlaps_all = [], []
    for r in sets:
        for n in adj.get(r, ()):
            if n in sets and r < n:
                if shown[r] != "leaf" and shown[r] == shown[n]:
                    faults.append(f"neighbours {r} and {n} both show {shown[r]}")
                o = len(pal[r] & pal[n]) / max(1, len(pal[r] | pal[n]))
                o_all = len(sets[r] & sets[n]) / max(1, len(sets[r] | sets[n]))
                overlaps_all.append(o_all)
                overlaps.append((round(o, 3), r, n))
                if o > OVERLAP_MAX:
                    faults.append(f"neighbours {r} and {n} share {o:.2f} of their grass types (> {OVERLAP_MAX})")
    overlaps.sort(reverse=True)
    mean = sum(o for o, _, _ in overlaps) / max(1, len(overlaps))
    return {"faults": faults, "pairs": len(overlaps), "mean_overlap": round(mean, 3),
            "max_overlap": overlaps[0] if overlaps else None,
            "mean_overlap_all": round(sum(overlaps_all) / max(1, len(overlaps_all)), 3), "shared_flowers": sum(len(v) > 1 for v in holders.values()),
            "unmet": unmet, "shown": shown}


def census_families(path: Path = CENSUS) -> dict[str, str]:
    """The census's family per grass; the census is built first when it is missing."""
    if not path.exists():
        from tools.newworld.dressing import grass_census
        grass_census.main(["--json", str(path)])
    return {g["edid"]: g["family"] for g in json.loads(path.read_text())["grasses"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--census", type=Path, default=CENSUS)
    a = ap.parse_args(argv)
    from tools.newworld.world import texture
    rep = check(texture, census_families(a.census), neighbours(), sheet_colours())
    print(f"ground colour: {rep['pairs']} neighbour pairs, palette overlap mean {rep['mean_overlap']} max {rep['max_overlap']} "
          f"(all land grass {rep['mean_overlap_all']}); "
          f"flower grasses in more than one region {rep['shared_flowers']}; faults {len(rep['faults'])}")
    for u in rep["unmet"]:
        print("  unmet (no complete grass of that colour in the load order): " + u)
    for f in rep["faults"]:
        print("  " + f)
    return 1 if rep["faults"] else 0


if __name__ == "__main__":
    sys.exit(main())
