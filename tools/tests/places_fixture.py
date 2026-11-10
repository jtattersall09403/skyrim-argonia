"""A small synthetic source place and ground, in the bundle contract's shapes, for the draft's tests."""
from __future__ import annotations

import json
import math
from array import array
from pathlib import Path

CELL = 4096.0


def _terrain(sdir: Path, cells, hfun, water) -> None:
    sdir.mkdir(parents=True, exist_ok=True)
    raw = array("f")
    meta = []
    for i, (cx, cy) in enumerate(cells):
        for row in range(33):
            for col in range(33):
                raw.append(hfun(cx * CELL + col * 128, cy * CELL + row * 128))
        meta.append({"cell": [cx, cy], "index": i, "water": water})
    (sdir / "terrain.f32").write_bytes(raw.tobytes())
    (sdir / "terrain.json").write_text(json.dumps({"cells": meta}))


def _jsonl(p: Path, rows) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))


BASES = [
    {"key": "T.esm:000001", "edid": "HouseA", "type": "STAT", "bounds": [[-300, -250, -50], [300, 250, 600]]},
    {"key": "T.esm:000002", "edid": "HallA", "type": "STAT", "bounds": [[-500, -400, -50], [500, 400, 800]]},
    {"key": "T.esm:000003", "edid": "DockPier", "type": "STAT", "bounds": [[-150, -400, -300], [150, 400, 20]]},
    {"key": "T.esm:000004", "edid": "Barrel", "type": "CONT", "bounds": [[-20, -20, 0], [20, 20, 60]]},
    {"key": "T.esm:000005", "edid": "DoorLoad", "type": "DOOR", "bounds": [[-60, -10, 0], [60, 10, 200]]},
    {"key": "T.esm:000006", "edid": "TreeSwamp", "type": "TREE", "bounds": [[-100, -100, 0], [100, 100, 900]]},
    {"key": "T.esm:000007", "edid": "BedSingle", "type": "FURN", "bounds": [[-50, -100, 0], [50, 100, 60]]},
    {"key": "T.esm:000008", "edid": "BedDouble", "type": "FURN", "bounds": [[-100, -100, 0], [100, 100, 60]]},
    {"key": "T.esm:000009", "edid": "Table", "type": "FURN", "bounds": [[-80, -50, 0], [80, 50, 80]]},
    {"key": "T.esm:00000A", "edid": "Bowl", "type": "MISC", "bounds": [[-10, -10, 0], [10, 10, 10]]},
    {"key": "T.esm:00000B", "edid": "NordBanner", "type": "STAT", "nordic": True, "bounds": [[-40, -5, 0], [40, 5, 200]]},
    {"key": "T.esm:00000C", "edid": "Fern", "type": "FLOR", "bounds": [[-30, -30, 0], [30, 30, 50]]},
    {"key": "T.esm:00000D", "edid": "Boat", "type": "STAT", "bounds": [[-60, -200, -20], [60, 200, 60]]},
]
for _b in BASES:
    _b["model"] = f"test/{_b['edid'].lower()}.nif"
NPCS = [
    {"key": "T.esm:000100", "edid": "HelstromBoatman", "name": "Boatman", "race": "ArgonianRace", "class": "Boatman"},
    {"key": "T.esm:000101", "edid": "HelstromVillager", "name": "Villager", "race": "ArgonianRace", "class": "Citizen"},
    {"key": "T.esm:000102", "edid": "HelstromSoldier", "name": "Soldier", "race": "ArgonianRace",
     "class": "Soldier", "factions": [{"faction": "GuardFaction", "rank": 0}]},
]
GIVES = [
    {"place_id": "fx", "seq": 0, "give_kind_id": "fishing", "detail": "river fish"},
    {"place_id": "fx", "seq": 1, "give_kind_id": "boat-stop", "detail": "raft-masters at the landing"},
    {"place_id": "fx", "seq": 2, "give_kind_id": "trader-general", "detail": "market trader"},
    {"place_id": "fx", "seq": 3, "give_kind_id": "trader-innkeeper", "detail": "the lodge"},
    {"place_id": "fx", "seq": 4, "give_kind_id": "inn-room", "detail": "the lodge"},
    {"place_id": "fx", "seq": 5, "give_kind_id": "trainer", "detail": "Journeyman Speech (the market trader)"},
    {"place_id": "fx", "seq": 6, "give_kind_id": "forge", "detail": "the smithy"},
]
RECORD = {"id": "fx", "name": "Fixture", "world_x": 40000.0, "world_y": 2000.0}


def src_height(x, y):   # a river along y < 1000, land rising gently northwards
    return -200.0 + 0.08 * y


def our_height(x, y):   # a river along x > 42500 at our anchor (40000, 2000), land rising westwards, a knoll
    k = 300.0 * math.exp(-((x - 38200) ** 2 + (y - 1000) ** 2) / (400.0 ** 2))
    return -200.0 + 0.08 * (42500 - x) + k


def build(root: Path) -> Path:
    b = root / "bundles"
    # --- source ---
    s = b / "src.t.fx"
    (s).mkdir(parents=True, exist_ok=True)
    (s / "bundle.json").write_text(json.dumps({"bundle_id": "src.t.fx", "kind": "source", "source_id": "t.fx",
                                               "stamp": {"inputs": {"T.esm": "aaa"}}}))
    _jsonl(s / "bases.jsonl", BASES)
    _jsonl(s / "npcs.jsonl", NPCS)
    ext = s / "spaces" / "exterior"
    _terrain(ext, [(0, 0), (1, 0), (0, 1), (1, 1), (0, -1), (1, -1)], src_height, 0.0)
    (ext / "space.json").write_text(json.dumps({"space_id": "exterior", "type": "exterior", "water": {"default_height": 0.0}}))

    def z(x, y, dz=0.0):
        return src_height(x, y) + dz

    refs = []
    houses = [(2000, 4000), (3000, 4000), (4000, 4000)]
    for k, (x, y) in enumerate(houses):
        refs.append({"id": f"S{k}", "base": "T.esm:000001", "kind": "building", "pos": [x, y, z(x, y, -20)], "rot": [0, 0, 0], "scale": 1.0})
        refs.append({"id": f"D{k}", "base": "T.esm:000005", "kind": "door", "pos": [x, y - 260, z(x, y - 260)], "rot": [0, 0, 0], "scale": 1.0,
                     "door": {"to_space": "HouseInt", "to_ref": "HD0"}})
        refs.append({"id": f"B{k}", "base": "T.esm:000004", "kind": "container", "pos": [x + 350, y, z(x + 350, y)], "rot": [0, 0, 0], "scale": 1.0})
    hx, hy = 3000, 5600
    refs.append({"id": "HALL", "base": "T.esm:000002", "kind": "building", "pos": [hx, hy, z(hx, hy, -30)], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "DH", "base": "T.esm:000005", "kind": "door", "pos": [hx, hy - 410, z(hx, hy - 410)], "rot": [0, 0, 0], "scale": 1.0,
                 "door": {"to_space": "HallInt", "to_ref": "HLD"}})
    refs.append({"id": "TBL", "base": "T.esm:000009", "kind": "furniture", "pos": [hx + 700, hy, z(hx + 700, hy)], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "BWL", "base": "T.esm:00000A", "kind": "clutter", "pos": [hx + 700, hy, z(hx + 700, hy) + 80], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "NB", "base": "T.esm:00000B", "kind": "static", "pos": [hx - 600, hy, z(hx - 600, hy)], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "PIER", "base": "T.esm:000003", "kind": "building", "pos": [3000, 2200, 10.0], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "BOAT", "base": "T.esm:00000D", "kind": "static", "pos": [3400, 2000, 0.0], "rot": [0, 0, 0], "scale": 1.0})
    for k in range(30):
        x, y = 500 + (k * 1373) % 7000, 1500 + (k * 911) % 6000
        refs.append({"id": f"TR{k}", "base": "T.esm:000006", "kind": "tree", "pos": [x, y, z(x, y)], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "FERN", "base": "T.esm:00000C", "kind": "plant", "pos": [2200, 4400, z(2200, 4400)], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "A0", "base": "T.esm:000100", "kind": "actor", "pos": [3000, 900, z(3000, 900)], "rot": [0, 0, 0], "scale": 1.0})
    refs.append({"id": "A1", "base": "T.esm:000102", "kind": "actor", "pos": [3000, 3000, z(3000, 3000)], "rot": [0, 0, 0], "scale": 1.0})
    _jsonl(ext / "refs.jsonl", refs)
    for sid, beds, door, back, out in (("HouseInt", [("T.esm:000008", "HB0"), ("T.esm:000007", "HB1")], "HD0", "D0",
                                        [2000, 3610, 0]),
                                       ("HallInt", [("T.esm:000007", f"LB{i}") for i in range(8)], "HLD", "DH",
                                        [hx, hy - 540, 0])):
        d = s / "spaces" / sid
        d.mkdir(parents=True, exist_ok=True)
        (d / "space.json").write_text(json.dumps({"space_id": sid, "type": "interior", "name": sid}))
        rows = [{"id": door, "base": "T.esm:000005", "kind": "door", "pos": [0, 0, 0], "rot": [0, 0, 0], "scale": 1.0,
                 "door": {"to_space": "exterior", "to_ref": back, "to_pos": out}}]
        rows += [{"id": rid, "base": bk, "kind": "furniture", "pos": [100 * i, 200, 0], "rot": [0, 0, 0], "scale": 1.0}
                 for i, (bk, rid) in enumerate(beds)]
        rows.append({"id": f"{sid}A", "base": "T.esm:000101", "kind": "actor", "pos": [0, 100, 0], "rot": [0, 0, 0], "scale": 1.0})
        _jsonl(d / "refs.jsonl", rows)
    # --- ground ---
    g = b / "ground.fx"
    g.mkdir(parents=True, exist_ok=True)
    (g / "bundle.json").write_text(json.dumps({"bundle_id": "ground.fx", "kind": "ground",
                                               "stamp": {"inputs": {"ArgoniaNewWorld.esm": "bbb"}}}))
    gext = g / "spaces" / "exterior"
    _terrain(gext, [(cx, cy) for cx in range(8, 12) for cy in range(-2, 3)], our_height, 0.0)
    (gext / "space.json").write_text(json.dumps({"space_id": "exterior", "type": "exterior", "water": {"default_height": 0.0}}))
    world = []
    for k in range(400):
        x, y = 36000 + (k * 733) % 8000, -2000 + (k * 1291) % 8000
        world.append({"id": f"W{k}", "base": "T.esm:000006" if k % 3 else "T.esm:00000C", "kind": "tree" if k % 3 else "plant",
                      "layer": "world", "pos": [x, y, our_height(x, y)], "rot": [0, 0, 0], "scale": 1.0})
    _jsonl(gext / "refs.jsonl", world)
    _jsonl(g / "bases.jsonl", [])
    # --- place ---
    p = root / "places" / "fx"
    p.mkdir(parents=True, exist_ok=True)
    (p / "place.json").write_text(json.dumps({"place_id": "fx", "source_id": "t.fx", "similar": [],
                                              "draft": {"replace": {"T.esm:00000B": "T.esm:000004"}}}))
    return root
