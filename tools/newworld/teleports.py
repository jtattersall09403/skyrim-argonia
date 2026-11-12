"""Console teleports into the new world: one named cell per place and per walk check, the way Skyrim names its own
exterior cells (`coc Riverwood`), each with a COCMarkerHeading where the player lands.

Why not `cow ArgoniaBlackMarsh X Y`: the plugin's cells run from y -95 to -242, and the owner's
`cow ArgoniaBlackMarsh -8 -148` (Helstrom's cell, measured from its place record: world -32174, -605839) landed in
open sea "miles north, outside the map": exactly where y -148 + 256 = 108 lies, a cell with no LAND (default land
-2048 under the water at 0). Every walk check with y below -128 was affected; those at -128 and above were not. A
named cell is found by its editor id, so `coc` never passes cell numbers through the console.

    python -m tools.newworld.teleports build [--plugin out/newworld/plugin]
        -> <plugin>/map/teleports.json   per place and walk check: coc name, cell, landing x y z and heading
           <plugin>/map/teleports.md     the console list for the owner
    python -m tools.newworld.teleports check [--plugin ...]    every landing on land above water, in its own cell,
        clear of placed objects; exit 1 on any fault
    python -m tools.newworld.teleports landings [--plugin ...] before the plants are placed: every place has dry land
        within reach and every walk check its kind of water (the land, the cells' water and the built places only;
        writes nothing); exit 1 naming the first that has none

`ArgoniaPlugin nwmap apply` (lod.sh map, a world.sh stage) names each cell and places the marker;
`nwmap check` reads both back.

The landing: the heightmap sample nearest the place's centre, inside the place's own cell (the cell holding the
centre), whose height and its eight neighbours' are at least LAND_MIN above the water, gentle (SLOPE_MAX a sample),
and CLEAR from every placed object (a built place's buildings by their footprints, its land patches applied to the
ground: newworld/places/<id>/, the places plugin's own content); when the own cell has none, the nearest such sample in the cells around (named
in the list as a neighbour cell, the place being on water); a place on water with no dry land within SEARCH_CELLS
(a seabed ruin, a wreck at sea) lands on the water's surface above its centre. Two places in one cell share its name (the first by
importance names it). The start cell keeps NewWorld.cs's name, ArgoniaNWStart.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

from tools.newworld.world import units as su

REPO = Path(__file__).resolve().parents[2]
DB = REPO / "newworld/story/data/db"
PLACES = REPO / "newworld/places"  # the built places: their exterior refs and land patches are in the places plugin
WORLD = "ArgoniaBlackMarsh"
START_CELL = "ArgoniaNWStart"  # NewWorld.cs StartCell: the start marker's cell
LAND_MIN = 8.0  # units above the water: one VHGT step
SLOPE_MAX = 32.0  # units of height change per sample (128 units): about 14 degrees
CLEAR = 96.0  # units from any placed object (a trunk, a rock)
SEARCH_CELLS = 3  # rings of neighbour cells searched when the own cell has no landing

# The walk's checks that are not a place: a kind of water (cells.json "water") near an anchor cell, landing on the
# bank of a cell of that kind. The anchors are the walk's cells, in the plugin's grid.
WALK = [
    {"name": "ANWWalkSwamp", "check": "G", "what": "black swamp water in the Banujha Basin", "water": "blackwater-swamp", "near": [-25, -195]},
    {"name": "ANWWalkMarsh", "check": "G", "what": "green marsh water in Okuwun-Rahei", "water": "green-marsh", "near": [55, -168]},
    {"name": "ANWWalkRiver", "check": "G", "what": "a river in the Tulmek Washes", "water": "river-", "near": [15, -207]},
    {"name": "ANWWalkStream", "check": "G", "what": "a stream in the Kotherra mangroves", "water": "stream-", "near": [-55, -163]},
    {"name": "ANWWalkPond", "check": "G", "what": "a pond in Blackwood", "water": "pond", "near": [-73, -130]},
    {"name": "ANWWalkEstuary", "check": "G", "what": "an estuary on the Arnesian coast", "water": "estuary", "near": [56, -115]},
    {"name": "ANWWalkSea", "check": "G", "what": "the open sea, from its shore", "water": "sea", "near": [77, -150]},
    {"name": "ANWWalkHelstromRiver", "check": "Q", "what": "the river south-west of Helstrom", "water": "river-", "near": [-21, -140]},
]

# The ecology walk's spots (nw-03b): a named cell at the exact cell, landing on its dry ground (`water` "" takes any
# cell), each chosen from the region ecology table, the danger band and the landcover (what the cell holds). The
# travel menu's page "spots" lists them (tools/newworld/travel_menu.py).
SPOTS = [
    {"name": "ANWSpotD1CapePercar", "what": "D1, the lowest danger: Cape Percar open coast", "near": [-43, -197]},
    {"name": "ANWSpotD5Murkwood", "what": "D5, the highest danger: Murkwood cypress swamp", "near": [-6, -141]},
    {"name": "ANWSpotFreshWater", "what": "fresh black water creatures: Banujha Basin", "near": [-26, -175]},
    {"name": "ANWSpotSaltWater", "what": "salt water creatures: Aphon Isle coast", "near": [-69, -186]},
    {"name": "ANWSpotCanopy", "what": "under the canopy: Arnesian Jungle", "near": [47, -120]},
    {"name": "ANWSpotOpen", "what": "in the open: Arnesian Jungle grassland", "near": [44, -114]},
    {"name": "ANWSpotDusk", "what": "night insects at dusk: Nushara Bayou reeds", "near": [37, -177]},
    {"name": "ANWSpotHostileNpcs", "what": "a hostile people band: Chixathe Mesa", "near": [17, -133]},
    {"name": "ANWSpotSwampHarvest", "what": "harvestable plants: Ultherus Swamp", "near": [13, -183]},
    {"name": "ANWSpotDry", "what": "a dry region: Aunike Ridge scrub", "near": [-20, -163]},
    {"name": "ANWSpotSeaShore", "what": "a sea shore: Hatandros Bight beach", "near": [61, -133]},
]
for _s in SPOTS:
    WALK.append({**_s, "check": "E", "kind": "spot", "water": ""})


def coc_name(name: str) -> str:
    """'Fort Gysilla' -> 'ANWFortGysilla': letters and digits only, each word capitalised."""
    words = re.findall(r"[A-Za-z0-9]+", name.replace("'", ""))
    return "ANW" + "".join(w[:1].upper() + w[1:] for w in words)


def grid(plugin: Path) -> su.Grid:
    g = json.loads((plugin / "land" / "manifest.json").read_text())["grid"]
    return su.Grid(g["build_id"], g["width"], g["height"], g["origin_x"], g["origin_y"], g["water"])


def _add(acc: dict, x: float, y: float, rad: float) -> None:
    """One keep-out circle, listed in every cell it touches."""
    for cx in range(int((x - rad) // su.CELL_UNITS), int((x + rad) // su.CELL_UNITS) + 1):
        for cy in range(int((y - rad) // su.CELL_UNITS), int((y + rad) // su.CELL_UNITS) + 1):
            acc.setdefault((cx, cy), []).append((x, y, rad))


def refs_by_cell(plugin: Path, places: Path | None = PLACES, world: bool = True) -> dict[tuple[int, int], np.ndarray]:
    """Keep-out circles (x, y, radius) per cell: every placed object of the world (refs/<producer>/cy*.jsonl, CLEAR
    round it) and of each built place's exterior (newworld/places/<id>/spaces/exterior/refs.jsonl, written into
    the places plugin): a building or other seated piece by its footprint's far corner, scaled, plus CLEAR."""
    acc: dict[tuple[int, int], list] = {}
    for f in glob.glob(str(plugin / "refs" / "*" / "cy*.jsonl")) if world else []:
        with open(f) as fh:
            for ln in fh:
                r = json.loads(ln)
                x, y = r.get("x", r.get("pos", [0, 0])[0]), r.get("y", r.get("pos", [0, 0])[1])
                acc.setdefault((int(x // su.CELL_UNITS), int(y // su.CELL_UNITS)), []).append((x, y, CLEAR))
    for f in sorted(glob.glob(str(places / "*" / "spaces" / "exterior" / "refs.jsonl"))) if places else []:
        with open(f) as fh:
            for ln in fh:
                if not ln.strip():
                    continue
                r = json.loads(ln)
                foot = (r.get("seat") or {}).get("foot")
                far = max(math.hypot(a, b) for a in foot[0::2] for b in foot[1::2]) * float(r.get("scale") or 1) if foot else 0.0
                _add(acc, r["pos"][0], r["pos"][1], far + CLEAR)
    return {k: np.asarray(v, float) for k, v in acc.items()}


def ground(plugin: Path, g: su.Grid, places: Path | None = PLACES) -> np.ndarray:
    """The ground as the game will have it: the world's heightmap with each built place's land patches
    (newworld/places/<id>/land.jsonl rows {cell, verts: [[row, col, dz]...]}, row and col from the cell's south-west
    corner as tools/places/seat.py applies them); a vertex shared by two cells is patched once."""
    # the limited heights are VHGT steps (world/land.py): x 8 for the game units every measure here is in
    h = np.asarray(np.load(plugin / "land" / "limited.npy", mmap_mode="r"), np.float32) * su.VHGT_STEP_UNITS
    pat: dict[tuple[int, int], float] = {}
    for f in sorted(glob.glob(str(places / "*" / "land.jsonl"))) if places else []:
        for ln in Path(f).read_text().splitlines():
            if not ln.strip():
                continue
            row = json.loads(ln)
            cx, cy = row["cell"]
            for vr, vc, dz in row["verts"]:
                x, y = (cx * 32 + vc) * su.VERTEX_SPACING_UNITS, (cy * 32 + vr) * su.VERTEX_SPACING_UNITS
                pat[(round((g.origin_y - y) / su.VERTEX_SPACING_UNITS), round((x - g.origin_x) / su.VERTEX_SPACING_UNITS))] = float(dz)
    for (r, c), dz in pat.items():
        if 0 <= r < g.height and 0 <= c < g.width:
            h[r, c] += dz
    return h


def cell_ok(g: su.Grid, h: np.ndarray, refs: dict, cx: int, cy: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The landing samples of one cell: (rows, cols, mask) over its 33 x 33 samples (edges excluded)."""
    r0, r1 = g.cell_rows(cy)
    c0, c1 = g.cell_cols(cx)
    if r0 < 0 or c0 < 0 or r1 >= g.height or c1 >= g.width:
        return np.zeros(0, int), np.zeros(0, int), np.zeros(0, bool)
    # the cell's samples and a ring round them; beyond the built land counts as water
    w = np.full((r1 - r0 + 3, c1 - c0 + 3), -np.inf)
    a0, b0 = max(r0 - 1, 0), max(c0 - 1, 0)
    blk = np.asarray(h[a0:r1 + 2, b0:c1 + 2], np.float64)
    w[a0 - (r0 - 1):a0 - (r0 - 1) + blk.shape[0], b0 - (c0 - 1):b0 - (c0 - 1) + blk.shape[1]] = blk
    core = w[1:-1, 1:-1]
    dry = core >= g.water + LAND_MIN
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            dry &= w[1 + dr:w.shape[0] - 1 + dr, 1 + dc:w.shape[1] - 1 + dc] >= g.water + LAND_MIN
    slope = np.maximum(np.abs(w[2:, 1:-1] - w[:-2, 1:-1]), np.abs(w[1:-1, 2:] - w[1:-1, :-2])) / 2
    ok = dry & (slope < SLOPE_MAX)
    rr, cc = np.mgrid[r0:r1 + 1, c0:c1 + 1]
    pts = refs.get((cx, cy))
    if pts is not None and len(pts):
        x = g.origin_x + cc * su.VERTEX_SPACING_UNITS
        y = g.origin_y - rr * su.VERTEX_SPACING_UNITS
        for i in range(0, len(pts), 512):
            p = pts[i:i + 512]
            ok &= (np.hypot(x[..., None] - p[:, 0], y[..., None] - p[:, 1]) >= p[:, 2]).all(-1)
    # a sample on the cell's own edge belongs to two cells: keep the landing strictly inside this one
    ok[[0, -1], :] = ok[:, [0, -1]] = False
    return rr.ravel(), cc.ravel(), ok.ravel()


def landing(g: su.Grid, h: np.ndarray, refs: dict, x: float, y: float, own: tuple[int, int], want=None) -> dict | None:
    """The landing nearest (x, y): in the own cell first, then ring by ring. `want(cx, cy)` filters cells."""
    col, row = (x - g.origin_x) / su.VERTEX_SPACING_UNITS, (g.origin_y - y) / su.VERTEX_SPACING_UNITS
    for ring in range(SEARCH_CELLS + 1):
        best = None
        for cx in range(own[0] - ring, own[0] + ring + 1):
            for cy in range(own[1] - ring, own[1] + ring + 1):
                if max(abs(cx - own[0]), abs(cy - own[1])) != ring or (want and not want(cx, cy)):
                    continue
                rr, cc, ok = cell_ok(g, h, refs, cx, cy)
                if not ok.any():
                    continue
                d = np.where(ok, np.hypot(rr - row, cc - col), np.inf)
                k = int(np.argmin(d))
                if best is None or d[k] < best[0]:
                    best = (float(d[k]), int(rr[k]), int(cc[k]), cx, cy)
        if best:
            _, r, c, cx, cy = best
            lx, ly = g.origin_x + c * su.VERTEX_SPACING_UNITS, g.origin_y - r * su.VERTEX_SPACING_UNITS
            heading = math.atan2(x - lx, y - ly) if (x, y) != (lx, ly) else 0.0  # face the place's centre
            return {"cell": [cx, cy], "x": lx, "y": ly, "z": float(h[r, c]) + 32.0, "rot_z": round(heading, 5),
                    "ground": float(h[r, c]), "own_cell": [cx, cy] == list(own), "sample": [r, c]}
    return None


def surface(g: su.Grid, x: float, y: float, own: tuple[int, int]) -> dict:
    """A place out at sea or under it with no dry land near (a seabed ruin, a wreck): the water's surface above it."""
    return {"cell": list(own), "x": float(x), "y": float(y), "z": g.water + 32.0, "rot_z": 0.0, "ground": None,
            "own_cell": True, "surface": True}


def build(plugin: Path, built: Path | None = PLACES, write: bool = True, world_refs: bool = True) -> dict:
    """The teleports of the land in `plugin`. `write=False, world_refs=False` is the early proof (`landings`): no
    file is written and the world's placed objects, not yet placed on this land, keep nothing clear."""
    g = grid(plugin)
    h = ground(plugin, g, built)
    man = json.loads((plugin / "land" / "manifest.json").read_text())
    start_cell = tuple(man["marker"]["cell"])
    cells = json.loads((plugin / "cells.json").read_text())["cells"]
    refs = refs_by_cell(plugin, built, world_refs)
    places = [json.loads(ln) for ln in (DB / "place.jsonl").read_text().splitlines() if ln.strip()]
    places.sort(key=lambda p: (-(p.get("importance") or 0), p["id"]))
    names: dict[tuple[int, int], str] = {start_cell: START_CELL}
    taken = {START_CELL}
    out = []

    def name_cell(cell, want):
        c = tuple(cell)
        if c in names:
            return names[c], True
        n, k = want, 2
        while n in taken:
            n, k = f"{want}{k}", k + 1
        names[c] = n
        taken.add(n)
        return n, False

    for p in places:
        own = (int(p["world_x"] // su.CELL_UNITS), int(p["world_y"] // su.CELL_UNITS))
        if not (g.cx0 <= own[0] < g.cx0 + g.cells_x and g.cy_bottom <= own[1] <= g.cy_top):
            raise ValueError(f"{p['id']} lies outside the land grid")
        lnd = landing(g, h, refs, p["world_x"], p["world_y"], own)
        if lnd is None:
            if not p.get("on_water"):
                raise ValueError(f"{p['id']}: no dry landing within {SEARCH_CELLS} cells")
            lnd = surface(g, p["world_x"], p["world_y"], own)
        n, shared = name_cell(lnd["cell"], coc_name(p["name"]))
        out.append({"kind": "place", "id": p["id"], "what": p["name"], "place_cell": list(own), "coc": n,
                    "shared": shared, "on_water": bool(p.get("on_water")), **lnd})
    for w in WALK:
        near = tuple(w["near"])

        def want(cx, cy, kind=w["water"]):
            v = (cells.get(f"{cx},{cy}") or {}).get("water") or ""
            return v.startswith(kind)
        # the walk's cell is the water's own cell; the landing is on a bank in that cell, else the nearest cell of the kind
        lnd = landing(g, h, refs, (near[0] + 0.5) * su.CELL_UNITS, (near[1] + 0.5) * su.CELL_UNITS, near, want)
        if lnd is None:
            raise ValueError(f"{w['name']}: no bank of {w['water']} within {SEARCH_CELLS} cells of {near}")
        n, shared = name_cell(lnd["cell"], w["name"])
        out.append({"kind": w.get("kind", "walk"), "id": w["name"], "check": w["check"], "what": w["what"], "water": w["water"],
                    "place_cell": list(near), "coc": n, "shared": shared, **lnd})
    doc = {"build_id": g.build_id, "world": WORLD, "marker_base": "000032:Skyrim.esm",  # COCMarkerHeading
           "cells": [{"coc": n, "cell": list(c)} for c, n in sorted(names.items(), key=lambda kv: kv[1]) if n != START_CELL],
           "teleports": out}
    if not write:
        return doc
    d = plugin / "map"
    d.mkdir(parents=True, exist_ok=True)
    (d / "teleports.json").write_text(json.dumps(doc, indent=1))
    (d / "teleports.md").write_text(markdown(doc))
    return doc


def markdown(doc: dict) -> str:
    lines = ["| Where | Console |", "|---|---|"]
    for t in doc["teleports"]:
        where = t["what"] + (" (on the water above it: no dry land near)" if t.get("surface") else
                             "" if t["own_cell"] else f" (nearest dry land, cell {t['cell'][0]},{t['cell'][1]})")
        lines.append(f"| {where} | `coc {t['coc']}` |")
    return "\n".join(lines) + "\n"


def check(plugin: Path, built: Path | None = PLACES) -> list[str]:
    """Faults: a landing not above the water (itself and its neighbours), not in its named cell, a place landing
    outside its own cell while its own cell has dry land, a landing inside a placed object's keep-out (a world ref,
    or a built place's building or piece), a name used twice for two cells. The ground is the world's with the built
    places' land patches."""
    g = grid(plugin)
    h = ground(plugin, g, built)
    doc = json.loads((plugin / "map" / "teleports.json").read_text())
    refs = refs_by_cell(plugin, built)
    bad = []
    if doc["build_id"] != g.build_id:
        bad.append(f"teleports.json is of build {doc['build_id']}, the land is {g.build_id}")
    seen: dict[str, tuple] = {}
    for c in doc["cells"]:
        if seen.setdefault(c["coc"], tuple(c["cell"])) != tuple(c["cell"]):
            bad.append(f"{c['coc']} names two cells")
    for t in doc["teleports"]:
        if t.get("surface"):
            near = range(-SEARCH_CELLS, SEARCH_CELLS + 1)
            if t["kind"] != "place" or any(cell_ok(g, h, refs, t["cell"][0] + i, t["cell"][1] + j)[2].any() for i in near for j in near):
                bad.append(f"{t['id']}: on the water's surface though dry land is near")
            continue
        r = round((g.origin_y - t["y"]) / su.VERTEX_SPACING_UNITS)
        c = round((t["x"] - g.origin_x) / su.VERTEX_SPACING_UNITS)
        win = np.asarray(h[r - 1:r + 2, c - 1:c + 2], np.float64)
        if win.min() < g.water + LAND_MIN:
            bad.append(f"{t['id']}: lands at {win.min():.0f} units, not above the water")
        cell = [int(t["x"] // su.CELL_UNITS), int(t["y"] // su.CELL_UNITS)]
        if cell != t["cell"]:
            bad.append(f"{t['id']}: landing in cell {cell}, named cell {t['cell']}")
        if t["z"] < float(h[r, c]):
            bad.append(f"{t['id']}: marker under the ground")
        if t["kind"] == "place" and not t["own_cell"] and cell_ok(g, h, refs, *t["place_cell"])[2].any():
            bad.append(f"{t['id']}: lands outside its own cell {t['place_cell']}, which has dry land")
        pts = refs.get(tuple(cell))
        if pts is not None and len(pts) and (np.hypot(pts[:, 0] - t["x"], pts[:, 1] - t["y"]) < pts[:, 2]).any():
            bad.append(f"{t['id']}: inside a placed object's keep-out (a world ref, or a built place's building)")
    return bad


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "check", "landings"))
    ap.add_argument("--plugin", default=str(REPO / "out/newworld/plugin"))
    a = ap.parse_args(argv)
    plugin = Path(a.plugin)
    if a.cmd == "landings":
        try:
            doc = build(plugin, write=False, world_refs=False)
        except ValueError as e:
            print(f"teleports landings: FAIL {e}")
            return 1
        t = doc["teleports"]
        print(f"teleports landings: {len(t)} found ({sum(x['kind'] == 'walk' for x in t)} walk checks), "
              f"{sum(not x['own_cell'] for x in t)} in a neighbour cell")
        return 0
    if a.cmd == "build":
        doc = build(plugin)
        t = doc["teleports"]
        print(f"teleports: {len(t)} ({sum(x['kind'] == 'place' for x in t)} places, {sum(x['kind'] == 'walk' for x in t)} walk checks), "
              f"{len(doc['cells'])} named cells, {sum(not x['own_cell'] for x in t)} landing in a neighbour cell")
        return 0
    bad = check(plugin)
    n = len(json.loads((plugin / "map" / "teleports.json").read_text())["teleports"])
    print(f"teleports check: {n} landings, {len(bad)} faults")
    for b in bad[:30]:
        print("  FAIL", b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
