"""The look audit's golden scene: a tiny place with known answers, in the real formats, no game asset.

`places/fx_truth/` (committed) are the place files. `make(root)` writes everything else under `root`: the source and
ground bundles (out/places/bundles/src.fx_src, ground.fx_truth), the models as coloured-box GLBs in a mod folder of a
stand-in profile (stack/), served by the studio's own asset route (tools/places/assets: a model that is already a GLB
is served as it is), and a copy of the place files (places/). Every known answer the audit asserts is in TRUTH.

Ground: four cells (0..1, 0..1), 4096 units each. Cell (0,0) is flat at 0; cell (1,0) rises 0.25 a unit eastward;
cell (0,1) holds a hollow made by two land rows that overlap (each -40: -80 where both reach) with our pool in it;
cell (1,1) holds a mound made by two land rows that overlap (+60 and +60)."""
from __future__ import annotations

import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PLACE, SOURCE = "fx_truth", "fx_src"
CELL, N, STEP = 4096.0, 33, 128.0
NO_WATER = 3.4028235e38
CELLS = [(0, 0), (1, 0), (0, 1), (1, 1)]

# model -> [(lo, hi, rgb)], game axes, about the model's origin
MODELS = {
    "gs/house.nif": [([-250, -250, 0], [250, 250, 400], (0.85, 0.75, 0.2))],
    "gs/deck.nif": [([-300, -300, -30], [300, 300, 0], (0.55, 0.35, 0.15))],
    "gs/post.nif": [([-15, -15, 0], [15, 15, 190], (0.4, 0.25, 0.1))],   # ends inside the deck, never flush with its top
    "gs/tree.nif": [([-40, -40, 0], [40, 40, 900], (0.35, 0.2, 0.1)), ([-400, -400, 700], [400, 400, 1500], (0.1, 0.6, 0.15))],
    "gs/wall.nif": [([-500, -20, 0], [500, 20, 450], (0.6, 0.6, 0.62))],
    "gs/water.nif": [([-250, -250, -2], [250, 250, 0], (0.2, 0.45, 0.5))],
    "gs/markers/xmarker.nif": [([-32, -32, 0], [32, 32, 64], (1.0, 0.0, 0.0))],
    "gs/stair.nif": [([i * 60.0 - 150, -60, 0], [i * 60.0 - 90, 60, (i + 1) * 40.0], (0.5, 0.3, 0.2)) for i in range(5)],
    "gs/bridge.nif": [([-500, -80, -20], [500, 80, 0], (0.45, 0.3, 0.15))],
    "gs/leaf.nif": [([-8, -1, -8], [8, 1, 8], (0.2, 0.7, 0.2))],
    "gs/room/floor.nif": [([-400, -400, -10], [400, 400, 0], (0.5, 0.45, 0.4))],
    "gs/room/wall.nif": [([-400, -10, 0], [400, 10, 300], (0.7, 0.68, 0.6))],
    "gs/room/wallhalf.nif": [([-150, -10, 0], [150, 10, 300], (0.7, 0.68, 0.6))],
    "gs/room/door.nif": [([-60, -10, 0], [60, 10, 220], (0.4, 0.2, 0.1))],
}
# kind and model of each base
BASES = {
    "GsHouse": ("building", "gs/house.nif"), "GsDeck": ("static", "gs/deck.nif"), "GsPost": ("static", "gs/post.nif"),
    "GsTree": ("tree", "gs/tree.nif"), "GsWall": ("static", "gs/wall.nif"), "GsPool": ("water", "gs/water.nif"),
    "XMarker": ("marker", "gs/markers/xmarker.nif"), "GsGone": ("static", "gs/gone.nif"),
    "GsStairs01": ("static", "gs/stair.nif"), "GsWoodPlankBridge01": ("static", "gs/bridge.nif"), "GsLeaf": ("clutter", "gs/leaf.nif"),
    "GsRoomFloor": ("static", "gs/room/floor.nif"), "GsRoomWall": ("static", "gs/room/wall.nif"),
    "GsRoomWallHalf": ("static", "gs/room/wallhalf.nif"), "GsRoomDoor": ("door", "gs/room/door.nif"),
}
TYPE = {"building": "STAT", "static": "STAT", "tree": "TREE", "water": "ACTI", "marker": "STAT", "clutter": "MISC", "door": "DOOR"}


def key(edid: str) -> str:
    return f"GsTruth.esm:{0x800 + sorted(BASES).index(edid):06X}"


def box_of(model: str) -> list:
    bs = MODELS.get(model)
    if not bs:
        return [[-32, -32, 0], [32, 32, 64]]
    return [np.min([b[0] for b in bs], 0).tolist(), np.max([b[1] for b in bs], 0).tolist()]


def glb_boxes(boxes) -> bytes:
    from tools.places.assets.glb import Builder
    g = Builder()
    for k, (lo, hi, rgb) in enumerate(boxes):
        lo, hi = np.array(lo, np.float32), np.array(hi, np.float32)
        c = np.array([[x, y, z] for z in (0, 1) for y in (0, 1) for x in (0, 1)], np.float32)
        P = lo + c * (hi - lo)
        I = np.array([0, 2, 1, 1, 2, 3, 4, 5, 6, 5, 7, 6, 0, 1, 4, 1, 5, 4, 2, 6, 3, 3, 6, 7, 0, 4, 2, 2, 4, 6, 1, 3, 5, 3, 7, 5], np.uint32)
        # flat-shaded faces: each triangle its own corners, so the light reads every face apart
        T = P[I.reshape(-1, 3)]
        nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        V, Nn = T.reshape(-1, 3), np.repeat(nrm, 3, axis=0)
        mat = g.material({"name": f"fx{k}", "pbrMetallicRoughness": {"baseColorFactor": [*rgb, 1.0], "metallicFactor": 0.0,
                                                                   "roughnessFactor": 0.9}, "doubleSided": True})
        g.node(f"box{k}", None, [{"attributes": {"POSITION": g.accessor(V, "VEC3", minmax=True), "NORMAL": g.accessor(Nn, "VEC3")},
                                  "indices": g.accessor(np.arange(len(V), dtype=np.uint32), "SCALAR"), "material": mat, "mode": 4}])
    return g.glb()


def ground_heights(cx: int, cy: int) -> list[float]:
    """The ground bundle's heights (before land rows), row-major south to north."""
    out = []
    for r in range(N):
        for c in range(N):
            out.append(c * STEP * 0.25 if (cx, cy) == (1, 0) else 0.0)
    return out


def jl(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


def jw(p: Path, o) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, indent=1))


def bundle_json(bid: str, kind: str, spaces: list[str]) -> dict:
    return {"bundle_id": bid, "kind": kind, "title": bid, "plugins": ["GsTruth.esm"], "worldspace": "GsWorld",
            "anchor": [0, 0, 0], "cells": [list(c) for c in CELLS], "spaces": spaces, "source_id": SOURCE,
            "stamp": {"key": f"fx-{bid}-1", "inputs": {"GsTruth.esm": "fx1"}, "tool": "look_truth fixture", "at": "2026-11-21T00:00:00Z"}}


def make(root: Path) -> dict:
    """Write the scene under root; returns the env a look daemon on it needs."""
    root = Path(root)
    out = root / "out" / "places"
    bd = out / "bundles"
    # models: a mod folder of a stand-in NewWorld profile
    files = {}
    for m, boxes in MODELS.items():
        p = root / "stack" / "MO2" / "mods" / "gs" / "meshes" / m
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(glb_boxes(boxes))
        files["meshes\\" + m.replace("/", "\\")] = ["gs", "0"]
    jw(root / "stack" / "installed-NewWorld.json", {"files": files})
    (root / "data").mkdir(exist_ok=True)
    bases = [{"key": key(e), "edid": e, "type": TYPE[k], "kind": k, "name": None, "model": m, "bounds": box_of(m),
              "plugin": "GsTruth.esm", "keywords": [], "nordic": False} | ({"water": {"shallow": [61, 111, 120]}} if k == "water" else {})
             for e, (k, m) in sorted(BASES.items())]
    # the source: an empty exterior and the room cell
    s = bd / f"src.{SOURCE}"
    jl(s / "bases.jsonl", bases)
    jl(s / "npcs.jsonl", [])
    _terrain(s / "spaces" / "exterior")
    jw(s / "spaces" / "exterior" / "space.json", {"space_id": "exterior", "type": "exterior", "name": "exterior",
                                                   "cells": [list(c) for c in CELLS], "water": {}})
    jl(s / "spaces" / "exterior" / "refs.jsonl", [])
    jl(s / "spaces" / "exterior" / "navmesh.jsonl", [])
    jw(s / "spaces" / "RoomCell" / "space.json", {"space_id": "RoomCell", "type": "interior", "name": "Fx Room", "cells": [],
                                                   "water": {}, "light": {}})
    jl(s / "spaces" / "RoomCell" / "refs.jsonl", ROOM)
    jl(s / "spaces" / "RoomCell" / "navmesh.jsonl", [])
    jw(s / "bundle.json", bundle_json(f"src.{SOURCE}", "source", ["exterior", "RoomCell"]))
    g = bd / f"ground.{PLACE}"
    jl(g / "bases.jsonl", [])
    jl(g / "npcs.jsonl", [])
    _terrain(g / "spaces" / "exterior")
    jw(g / "spaces" / "exterior" / "space.json", {"space_id": "exterior", "type": "exterior", "name": "exterior",
                                                   "cells": [list(c) for c in CELLS], "water": {}})
    jl(g / "spaces" / "exterior" / "refs.jsonl", [])
    jl(g / "spaces" / "exterior" / "navmesh.jsonl", [])
    jw(g / "bundle.json", bundle_json(f"ground.{PLACE}", "ground", ["exterior"]))
    jw(out / "footprints.json", {})
    places = root / "places"
    shutil.rmtree(places, ignore_errors=True)
    shutil.copytree(HERE / "places", places)
    return {"PLACES_OUT": str(out), "PLACES_DIR": str(places), "ARGONIA_STACK": str(root / "stack"),
            "ARGONIA_DATA": str(root / "data"), "ARGONIA_NW_ASSETS": str(root / "data"),
            "PLACES_CATALOGUE": str(out / "catalogue" / "bases.jsonl")}


def _terrain(sp: Path) -> None:
    flat, meta = [], []
    for i, (cx, cy) in enumerate(CELLS):
        flat += ground_heights(cx, cy)
        meta.append({"cell": [cx, cy], "key": f"GsTruth.esm:{0x100000 + i:06X}", "edid": None, "plugin": "GsTruth.esm",
                     "water": {"height": NO_WATER}, "regions": None, "heights_index": i, "layers": []})
    sp.mkdir(parents=True, exist_ok=True)
    (sp / "terrain.f32").write_bytes(struct.pack(f"<{len(flat)}f", *flat))
    jw(sp / "terrain.json", {"cells": meta, "ltex": {}})


# ---------- the place files (written once into places/; committed) ----------
def ref(rid, edid, pos, rot=(0, 0, 0), seat="free", **kw):
    return {"id": f"{PLACE}.{rid}", "base": key(edid), "kind": BASES[edid][0], "pos": list(pos), "rot": list(rot),
            "scale": 1.0, "layer": "place", "cluster": kw.pop("cluster", None), "seat": {"mode": seat, "dz": 0.0}, **kw}


EXTERIOR = [
    ref("house", "GsHouse", (1000, 1000, 200), cluster="s01"),
    ref("deck", "GsDeck", (1000, 1000, 200), cluster="s01"),
    *[ref(f"post{i}", "GsPost", (1000 + dx, 1000 + dy, 0), cluster="s01") for i, (dx, dy) in
      enumerate(((-280, -280), (280, -280), (-280, 280), (280, 280)))],
    ref("stair", "GsStairs01", (550, 1000, 0), cluster="s01"),
    ref("tree", "GsTree", (2600, 1000, 0), cluster="s02"),
    ref("wall", "GsWall", (1000, 1800, 0), cluster="s03"),
    ref("marker", "XMarker", (1800, 600, 0), cluster="s04"),
    ref("gone", "GsGone", (1800, 1400, 0), cluster="s04"),
    ref("bridge", "GsWoodPlankBridge01", (2600, 2600, 120), cluster="s05"),
    ref("pool", "GsPool", (1408, 4096 + 1408, -60), cluster="s06"),
    ref("door", "GsRoomDoor", (3200, 600, 0), cluster="s07", door={"to_space": "fx_room"}),
    ref("leaf", "GsLeaf", (1000, 300, 160), cluster="s08"),
]
ROOM = [  # the source room cell: a floor, three walls, the west wall a door and a gap onto the void
    {"id": "GsTruth.esm:R01", "base": key("GsRoomFloor"), "kind": "static", "pos": [0, 0, 0], "rot": [0, 0, 0], "scale": 1.0},
    {"id": "GsTruth.esm:R02", "base": key("GsRoomWall"), "kind": "static", "pos": [0, 400, 0], "rot": [0, 0, 0], "scale": 1.0},
    {"id": "GsTruth.esm:R03", "base": key("GsRoomWall"), "kind": "static", "pos": [0, -400, 0], "rot": [0, 0, 0], "scale": 1.0},
    {"id": "GsTruth.esm:R04", "base": key("GsRoomWall"), "kind": "static", "pos": [400, 0, 0], "rot": [0, 0, 1.5707963], "scale": 1.0},
    {"id": "GsTruth.esm:R05", "base": key("GsRoomWallHalf"), "kind": "static", "pos": [-400, 250, 0], "rot": [0, 0, 1.5707963], "scale": 1.0},
    {"id": "GsTruth.esm:R06", "base": key("GsRoomDoor"), "kind": "door", "pos": [-400, -250, 0], "rot": [0, 0, 1.5707963], "scale": 1.0,
     "door": {"to_space": "exterior"}},
]
LAND = [  # two overlapping rows in one cell each: they add
    {"cell": [0, 1], "verts": [[r, c, -40.0] for r in range(8, 13) for c in range(8, 13)], "why": "fixture: hollow, first row"},
    {"cell": [0, 1], "verts": [[r, c, -40.0] for r in range(10, 15) for c in range(10, 15)], "why": "fixture: hollow, second row"},
    {"cell": [1, 1], "verts": [[r, c, 60.0] for r in range(10, 17) for c in range(10, 17)], "why": "fixture: mound, first row"},
    {"cell": [1, 1], "verts": [[r, c, 60.0] for r in range(13, 20) for c in range(13, 20)], "why": "fixture: mound, second row"},
]


def write_places(d: Path = HERE / "places" / PLACE) -> None:
    shutil.rmtree(d, ignore_errors=True)
    jw(d / "place.json", {"place_id": PLACE, "source_id": SOURCE, "title": "Fx Truth", "similar": []})
    jl(d / "spaces" / "exterior" / "refs.jsonl", EXTERIOR)
    jw(d / "spaces" / "fx_room" / "space.json", {"copy_of": f"{SOURCE}/RoomCell", "name": "Fx Room", "parent": "exterior",
                                                  "door_from": f"{PLACE}.door"})
    jl(d / "spaces" / "fx_room" / "refs.jsonl", [])
    jl(d / "land.jsonl", LAND)
    for f in ("people", "paths", "clear", "quests"):
        jl(d / f"{f}.jsonl", [])


if __name__ == "__main__":
    sys.path.insert(0, str(REPO))
    if sys.argv[1:] == ["--write-places"]:
        write_places()
    else:
        print(json.dumps(make(Path(sys.argv[1]))))
