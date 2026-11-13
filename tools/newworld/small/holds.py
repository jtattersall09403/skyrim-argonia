"""What the small world's block holds, read from the real build it is cut from: one row for each thing a stage has a
rule for. A world that changes under the block fails a row here, and the block is chosen again (`best`), once.

    python3 -m tools.newworld.small holds [--from <out/newworld>]
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

from tools.newworld import small

DB = small.REPO / "newworld/story/data/db"
STILL = ("pond", "green-marsh", "blackwater-swamp", "lake")


def _jsonl(p: Path) -> list:
    return [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()]


def _cell(x: float, y: float) -> tuple[int, int]:
    return int(x // 4096), int(y // 4096)


def facts(src: Path, block=small.BLOCK) -> dict:
    """The block's counts in the real build `src` (an out/newworld folder)."""
    x0, y0, nx, ny = block
    cells = json.loads((src / "plugin/cells.json").read_text())["cells"]
    plan = {b["source"]: b for b in json.loads((src / "plugin/map/lodplan.json").read_text())["bases"]}
    base = {b["ref"]: b for b in json.loads((src / "plugin/refs/flora/bases.json").read_text())["bases"]}
    region, water, t = collections.Counter(), collections.Counter(), collections.Counter()
    for x in range(x0, x0 + nx):
        for y in range(y0, y0 + ny):
            v = cells.get(f"{x},{y}") or {}
            region[v.get("region")] += 1
            if "water" in v:
                w = v["water"].split("@")[0]       # a region's variant (<kind>[-<heading>]@<region>) counts as its kind
                water[w.split("-")[0] if w.split("-")[-1].isdigit() else w] += 1
    lodmodels = set()
    for y in range(y0, y0 + ny):
        f = src / f"plugin/refs/flora/cy{y:+04d}.jsonl"
        for r in (_jsonl(f) if f.exists() else []):
            if not small.in_block(*r["cell"], block):
                continue
            p, b = plan.get(r["base"]), base.get(r["base"])
            if r["cls"].startswith("road_"):
                t["dressing"] += 1
            if not p:
                continue
            t[p["mech"]] += 1
            if p["mech"] == "tree" and p["sig"] == "STAT":
                t["static_tree"] += 1
            if p["mech"] == "tree" and b and p["plugin"] == small.REAL_ESM and b.get("copied"):
                t["repaired_copy"] += 1          # our copy of another plugin's tree: a billboard of its own
            if p["mech"] == "lodmodel":
                lodmodels.add(p["edid"])
    flow = sum(small.in_block(*r["cell"], block) for r in json.loads((src / "water_flow_cells.json").read_text()))
    road = {_cell(v["world_x"], v["world_y"]) for v in _jsonl(DB / "road_vertex.jsonl")}
    junctions = sum(n["kind"] == "junction" and small.in_block(*_cell(n["world_x"], n["world_y"]), block) for n in _jsonl(DB / "road_node.jsonl"))
    places = [p["id"] for p in _jsonl(DB / "place.jsonl") if p.get("world_x") is not None and small.in_block(*_cell(p["world_x"], p["world_y"]), block)]
    shore = {p["place_id"] for p in json.loads((src / "terrain/places_terrain.json").read_text()) if p["need"] in ("shore-access", "island")}
    return {"regions": {k: n for k, n in region.items() if k and n >= 30}, "water": dict(water), "flow_cells": flow,
            "still_cells": sum(water[k] for k in STILL), "dry_cells": nx * ny - sum(water.values()),
            "tree": t["tree"], "static_tree": t["static_tree"], "repaired_copy": t["repaired_copy"], "object": t["object"],
            "own": t["own"], "lodmodel_bases": sorted(lodmodels), "dressing": t["dressing"],
            "lodmodel_planned": sum(v["mech"] == "lodmodel" for v in plan.values()),
            "road_cells": sum(small.in_block(*c, block) for c in road), "junctions": junctions,
            "places": places, "places_at_water": sorted(set(places) & shore)}


ROWS = (
    ("two regions or more, 30 cells each: a seam between regions", lambda f: len(f["regions"]) >= 2),
    ("still water and flowing water: a seam between water kinds", lambda f: f["still_cells"] >= 8 and f["flow_cells"] >= 6),
    ("dry land for forest and upland (60 cells)", lambda f: f["dry_cells"] >= 60),
    ("trees planned for a billboard", lambda f: f["tree"] >= 500),
    ("static trees flagged for tree LOD", lambda f: f["static_tree"] >= 50),
    ("our copies of other plugins' trees, each with a billboard of its own", lambda f: f["repaired_copy"] >= 20),
    ("rocks matched by a full-model rule", lambda f: f["object"] >= 5),
    ("cliffs and trims with LOD models of their own", lambda f: f["own"] >= 20),
    ("a base drawn from a derived LOD model, when the province plans one", lambda f: len(f["lodmodel_bases"]) >= min(1, f["lodmodel_planned"])),
    ("a road, its dressing and a junction", lambda f: f["road_cells"] >= 10 and f["dressing"] >= 5 and f["junctions"] >= 1),
    ("a place whose pad is at the water", lambda f: bool(f["places_at_water"])),
)


def check(src: Path, root: Path) -> int:
    f = facts(src)
    bad = 0
    for what, ok in ROWS:
        good = ok(f)
        bad += not good
        print(f"  {'PASS' if good else 'FAIL'} the block holds {what}")
    print("  " + json.dumps(f, sort_keys=True))
    (root / "holds.json").write_text(json.dumps(f, indent=1, sort_keys=True))
    if bad:
        print(f"FAIL: the world changed under block {small.BLOCK}: choose it again (tools/newworld/small/holds.py)")
    return 1 if bad else 0
