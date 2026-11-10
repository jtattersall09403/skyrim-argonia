#!/usr/bin/env python3
"""Write synthetic place-studio bundles (no game assets) in the contract's layout."""

import argparse
import base64
import hashlib
import json
import math
import random
import struct
from pathlib import Path

CELL = 4096.0
N = 33
STEP = CELL / 32
AT = "2026-11-09T12:00:00Z"
LTEX = {  # LTEX key -> (edid, diffuse); the first four are the quadrants' bases and alpha layers
    "Fix.esm:00A001": ("FixGrass01", "textures/landscape/fix_grass.dds"),
    "Fix.esm:00A002": ("FixDirt01", "textures/landscape/fix_dirt.dds"),
    "Fix.esm:00A003": ("FixMud01", "textures/landscape/fix_mud.dds"),
    "Fix.esm:00A004": ("FixRoad01", "textures/landscape/fix_road.dds"),
}
LKEYS = list(LTEX)
QUADS = ["BottomLeft", "BottomRight", "TopLeft", "TopRight"]  # SW, SE, NW, NE
NO_WATER = 3.4028235e38

# kind -> (type, size xyz, keywords, nordic)
SHAPES = {
    "building": ("Static", (800, 600, 500)),
    "tree": ("Tree", (200, 200, 900)),
    "plant": ("Flora", (60, 60, 80)),
    "groundcover": ("Static", (40, 40, 30)),
    "rock": ("Static", (180, 160, 120)),
    "static": ("Static", (300, 300, 200)),
    "clutter": ("MiscItem", (30, 30, 30)),
    "furniture": ("Furniture", (200, 100, 60)),
    "door": ("Door", (130, 20, 220)),
    "light": ("Light", (20, 20, 40)),
    "actor": ("Npc", (40, 40, 180)),
    "container": ("Container", (100, 60, 60)),
}


def jwrite(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1))


def jlines(p, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows))


class Bases:
    def __init__(self):
        self.rows = {}
        self.n = 0x800

    def get(self, name, kind, nordic=False, **extra):
        k = f"Fix.esm:{self.n:06X}" if name not in self.rows else self.rows[name]["key"]
        if name in self.rows:
            return k
        self.n += 1
        typ, size = SHAPES[kind]
        sx, sy, sz = extra.pop("size", size)
        b = {
            "key": k, "edid": name, "type": typ, "name": name.replace("_", " "),
            "model": f"fix/{name.lower()}.nif",
            "bounds": [[-sx / 2, -sy / 2, 0], [sx / 2, sy / 2, sz]],
            "plugin": "Fix.esm", "keywords": [kind, "Fix" + kind.title()], "nordic": nordic, "kind": kind,
        }
        b.update(extra)
        self.rows[name] = b
        return k


def heights(cx, cy, seed, river):
    out = []
    for r in range(N):
        for c in range(N):
            x = cx * CELL + c * STEP
            y = cy * CELL + r * STEP
            h = 300 * math.sin(x / 2500 + seed) * math.cos(y / 3100 - seed) + 120 * math.sin(x / 700 + y / 900)
            if river:
                d = abs(y - (4096 + 600 * math.sin(x / 2000))) if river == "y" else abs(x - 4096)
                h -= 700 * math.exp(-((d / 450) ** 2))
            out.append(h + 400)
    return out


def terrain(sp, cells, seed, river, wtype):
    flat, meta = [], []
    for cx, cy in cells:
        flat += heights(cx, cy, seed, river)
    for i, (cx, cy) in enumerate(cells):
        layers = []
        for q, quad in enumerate(QUADS):
            layers.append({"quad": quad, "layer": -1, "tex": LKEYS[q % 2]})
            for n in range(2):
                a = bytes(int(255 * min(1.0, max(0.0, 0.5 + 0.5 * math.sin((r + c + q + 2 * n) / 3.0))))
                          for r in range(17) for c in range(17))
                layers.append({"quad": quad, "layer": n, "tex": LKEYS[2 + n], "alpha": base64.b64encode(a).decode()})
        vc = bytes(v for r in range(N) for c in range(N) for v in (120 + 40 * ((r + c) % 3), 130 + 30 * (r % 2), 110))
        dry = i == 3
        meta.append({"cell": [cx, cy], "key": f"Fix.esm:{0x100000 + i:06X}", "edid": None, "plugin": "Fix.esm",
                     "water": {"height": NO_WATER if dry else 120.0, "type": f"Fix.esm:{0x3000 + len(wtype):06X}"},
                     "regions": None, "heights_index": i, "layers": layers,
                     "vertex_colours": base64.b64encode(vc).decode()})
    ltex = {k: {"edid": e, "plugin": "Fix.esm", "diffuse": d, "normal": d.replace(".dds", "_n.dds"), "grasses": []}
            for k, (e, d) in LTEX.items()}
    sp.mkdir(parents=True, exist_ok=True)
    (sp / "terrain.f32").write_bytes(struct.pack(f"<{len(flat)}f", *flat))
    jwrite(sp / "terrain.json", {"cells": meta, "ltex": ltex})
    return flat


def h_at(flat, cells, x, y):
    cx, cy = int(x // CELL), int(y // CELL)
    if [cx, cy] not in [list(c) for c in cells]:
        return 400.0
    off = [list(c) for c in cells].index([cx, cy]) * N * N
    fx, fy = (x - cx * CELL) / STEP, (y - cy * CELL) / STEP
    c0, r0 = min(int(fx), 31), min(int(fy), 31)
    tx, ty = fx - c0, fy - r0
    g = lambda r, c: flat[off + r * N + c]  # noqa: E731
    return (g(r0, c0) * (1 - tx) + g(r0, c0 + 1) * tx) * (1 - ty) + (g(r0 + 1, c0) * (1 - tx) + g(r0 + 1, c0 + 1) * tx) * ty


def space_json(sid, typ, cells, name=None):
    return {"space_id": sid, "type": typ, "name": name or sid, "cells": cells,
            "water": {"default_height": 120.0, "type": "river"} if typ == "exterior" else {},
            "light": {"ambient": [90, 90, 90]} if typ == "interior" else {}, "owner": None}


def bundle_json(bid, kind, title, anchor, cells, spaces, extra=None):
    b = {"bundle_id": bid, "kind": kind, "title": title, "plugins": ["Fix.esm"], "worldspace": "FixWorld",
         "anchor": anchor, "cells": cells, "spaces": spaces,
         "stamp": {"key": hashlib.sha256(bid.encode()).hexdigest()[:16], "inputs": {}, "tool": "make_fixture", "at": AT}}
    b.update(extra or {})
    return b


def interiors(bases, rng, prefix, door_back_to):
    """Return {space_id: refs} for two houses; door_back_to[space]=(ext_ref_id, ext_pos)."""
    out = {}
    for i, sid in enumerate(["FixHouse01", "FixHouse02"]):
        refs = []
        p = f"{prefix}{sid}"
        refs.append(ref(f"{p}.door", bases.get("Fix_Door", "door", door={"teleport": True}), "door",
                        [0, -300, 0], [0, 0, 0], layer="place",
                        door={"to_space": "exterior", "to_ref": door_back_to[sid][0],
                              "to_pos": door_back_to[sid][1], "to_rot": [0, 0, 0]}))
        refs.append(ref(f"{p}.bed", bases.get("Fix_Bed", "furniture", furniture={"markers": [{"type": "sleep", "pos": [0, 0, 40]}]}),
                        "furniture", [150, 100, 0], [0, 0, 1.0]))
        refs.append(ref(f"{p}.chest", bases.get("Fix_Chest", "container", container={}), "container", [-150, -100, 0], [0, 0, 0]))
        refs.append(ref(f"{p}.table", bases.get("Fix_Table", "furniture"), "furniture", [-100, 100, 0], [0, 0, 0]))
        for j in range(4):
            refs.append(ref(f"{p}.c{j}", bases.get(f"Fix_Cup{j % 2}", "clutter"), "clutter",
                            [-100 + rng.randint(-40, 40), 100 + rng.randint(-40, 40), 80], [0, 0, rng.random() * 6]))
        refs.append(ref(f"{p}.l", bases.get("Fix_Lamp", "light", light={"radius": 512, "colour": [255, 200, 120]}), "light",
                        [0, 0, 250], [0, 0, 0]))
        out[sid] = refs
    return out


def ref(rid, base, kind, pos, rot, scale=1.0, layer="place", **kw):
    r = {"id": rid, "base": base, "kind": kind, "pos": [round(v, 2) for v in pos],
         "rot": [round(v, 4) for v in rot], "scale": scale, "layer": layer, "flags": []}
    r.update(kw)
    r.setdefault("edid", None)
    r.setdefault("cell", None)
    if "door" in r:
        r["door"].setdefault("flags", "0")
    return r


def source_refs(bases, rng, cells, pfx, nbuild, nenter):
    """Village refs around the middle of `cells`; returns (refs, door_back)."""
    x0 = min(c[0] for c in cells) * CELL
    y0 = min(c[1] for c in cells) * CELL
    refs, back = [], {}
    names = ["Fix_Hall", "Fix_Smithy", "Fix_HouseA", "Fix_HouseB", "Fix_Barn", "Fix_Shrine"]
    for i in range(nbuild):
        nm = names[i % len(names)]
        x, y = x0 + 2000 + (i % 3) * 1500, y0 + 2200 + (i // 3) * 1700
        nordic = nm == "Fix_Shrine"
        b = bases.get(nm, "building", nordic=nordic, keywords=["building", "FixBuilding"] + (["NordicRuin"] if nordic else []))
        rid = f"{pfx}.b{i}"
        refs.append(ref(rid, b, "building", [x, y, 380], [0, 0, rng.random() * 6.28]))
        if i < nenter:
            sid = ["FixHouse01", "FixHouse02"][i]
            dp = [x, y - 420, 380]
            refs.append(ref(f"{pfx}.d{i}", bases.get("Fix_Door", "door", door={"teleport": True}), "door", dp, [0, 0, 0],
                            door={"to_space": sid, "to_ref": f"{pfx}{sid}.door", "to_pos": [0, -300, 0], "to_rot": [0, 0, 0]}))
            back[sid] = (f"{pfx}.d{i}", dp)
    for i in range(10):
        refs.append(ref(f"{pfx}.s{i}", bases.get(f"Fix_Wall{i % 3}", "static", nordic=(i == 3)), "static",
                        [x0 + 1200 + rng.random() * 2800, y0 + 1500 + rng.random() * 2800, 380], [0, 0, rng.random() * 6.28]))
    for i in range(12):
        refs.append(ref(f"{pfx}.c{i}", bases.get(f"Fix_Crate{i % 3}", "clutter"), "clutter",
                        [x0 + 1500 + rng.random() * 2500, y0 + 1500 + rng.random() * 2500, 380], [0, 0, rng.random() * 6.28]))
    for i in range(8):
        refs.append(ref(f"{pfx}.l{i}", bases.get("Fix_Torch", "light", light={"radius": 600, "colour": [255, 180, 90]}), "light",
                        [x0 + 1500 + rng.random() * 2500, y0 + 1500 + rng.random() * 2500, 480], [0, 0, 0]))
    npcs = []
    for i in range(2):
        nb = f"Fix.esm:{0x2000 + i:06X}"
        npcs.append({"key": nb, "edid": f"FixActor{i}", "name": ["Ada", "Bram"][i], "race": "FixRace", "sex": i,
                     "template": None, "class": "Citizen", "factions": [{"faction": "FixVillage", "rank": 0}],
                     "voice": "FixVoice", "outfit": "FixOutfit", "services": {}, "packages": []})
        ab = bases.get(f"Fix_Actor{i}", "actor")
        refs.append(ref(f"{pfx}.a{i}", ab, "actor", [x0 + 2500 + i * 300, y0 + 2000, 380], [0, 0, 0], npc=nb))
    return refs, back, npcs


def write_bundle(root, bid, kind, title, anchor, cells, ext_refs, int_refs, bases, flat_args, npcs=(), extra=None):
    d = root / bid
    for r in ext_refs:
        if r.get("cell") is None:
            r["cell"] = [int(r["pos"][0] // CELL), int(r["pos"][1] // CELL)]
        r.setdefault("src", "Fix.esm")
    for rs in int_refs.values():
        for r in rs:
            r.setdefault("src", "Fix.esm")
    sids = ["exterior"] + sorted(int_refs)
    seed, river, wtype = flat_args
    flat = terrain(d / "spaces" / "exterior", cells, seed, river, wtype)
    jwrite(d / "spaces/exterior/space.json", space_json("exterior", "exterior", cells))
    jlines(d / "spaces/exterior/refs.jsonl", ext_refs)
    jlines(d / "spaces/exterior/navmesh.jsonl", [])
    for sid, refs in int_refs.items():
        jwrite(d / "spaces" / sid / "space.json", space_json(sid, "interior", [], sid))
        jlines(d / "spaces" / sid / "refs.jsonl", refs)
        jlines(d / "spaces" / sid / "navmesh.jsonl", [])
    used = {r["base"] for r in ext_refs} | {r["base"] for rs in int_refs.values() for r in rs}
    jlines(d / "bases.jsonl", [b for b in bases.rows.values() if b["key"] in used])
    jlines(d / "npcs.jsonl", list(npcs))
    jwrite(d / "bundle.json", bundle_json(bid, kind, title, anchor, cells, sids, extra))
    return flat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=str(Path(__file__).parent / "fixture-out"))
    ap.add_argument("--big", action="store_true", help="ground at real-data scale: 31 x 31 cells, 37,000 world refs")
    args = ap.parse_args()
    out = Path(args.out)
    rng = random.Random(7)
    root = out / "bundles"

    side = 31 if args.big else 2
    gcells = [[x, y] for y in range(side) for x in range(side)]
    scells = [[10, 10], [11, 10], [10, 11], [11, 11]]
    sb = Bases()
    srefs, back, snpcs = source_refs(sb, rng, scells, "src", 6, 2)
    sint = interiors(sb, rng, "src", back)
    write_bundle(root, "src.fix.village", "source", "Fix village", [10 * CELL, 10 * CELL, 0], scells, srefs, sint, sb,
                 (2.0, "y", "river"), snpcs)

    # ground: world layer
    gb = Bases()
    grefs = []
    kinds = [("tree", 90, "Fix_Pine"), ("tree", 40, "Fix_Oak"), ("plant", 70, "Fix_Fern"), ("groundcover", 60, "Fix_Moss"),
             ("rock", 40, "Fix_Boulder")]
    gcells_t = [tuple(c) for c in gcells]
    heights_all = []
    for cx, cy in gcells_t:
        heights_all += heights(cx, cy, 1.0, "y")
    n = 0
    mult = 120 if args.big else 1
    for kind, cnt, nm in kinds:
        base = gb.get(nm, kind)
        for _ in range(cnt * mult):
            x, y = rng.random() * side * CELL, rng.random() * side * CELL
            grefs.append(ref(f"g{n}", base, kind, [x, y, h_at(heights_all, gcells, x, y)], [0, 0, rng.random() * 6.28],
                             0.8 + rng.random() * 0.5, layer="world"))
            n += 1
    gsha = hashlib.sha256(b"fixture-ground").hexdigest()
    write_bundle(root, "ground.fixplace", "ground", "Fixture place ground", [0, 0, 0], gcells, grefs, {}, gb,
                 (1.0, "y", "river"), (), {"esm": {"file": "Fix.esm", "sha256": gsha},
                  "stamp": {"key": gsha[:16], "inputs": {"Fix.esm": gsha}, "tool": "make_fixture", "at": AT, "sha": gsha}})
    # rewrite stamp (extra replaced whole dict above; fine) and flat for later use
    flat = heights_all

    # fit: source middle -> ground middle, rotated 0.3 rad
    rot, scale = 0.3, 1.0
    sc = (10 * CELL + 4096, 10 * CELL + 4096)
    gc = (4096, 4096)
    cr, sr = math.cos(rot), math.sin(rot)
    dx = gc[0] - scale * (cr * sc[0] - sr * sc[1])
    dy = gc[1] - scale * (sr * sc[0] + cr * sc[1])
    fit = {"dx": dx, "dy": dy, "dz": 0.0, "rot": rot, "scale": scale}

    def xf(p):
        return [scale * (cr * p[0] - sr * p[1]) + dx, scale * (sr * p[0] + cr * p[1]) + dy]

    # draft: same layout seated on ground, base keys equal to source bases (keys are unique per fixture bundle set)
    drefs = []
    for r in srefs:
        x, y = xf(r["pos"])
        z = h_at(flat, gcells, x, y)
        nr = dict(r)
        nr.update(id=r["id"].replace("src", "fixplace", 1), pos=[round(x, 2), round(y, 2), round(z, 2)],
                  rot=[r["rot"][0], r["rot"][1], r["rot"][2] + rot], layer="place",
                  seat={"mode": "ground", "dz": 0}, src=r["id"], cell=[int(x // CELL), int(y // CELL)])
        if "door" in r:
            nr["door"] = dict(r["door"], to_ref=r["door"]["to_ref"].replace("src", "fixplace", 1))
        drefs.append(nr)
    dint = {}
    for sid, rs in sint.items():
        dint[sid] = []
        for r in rs:
            nr = dict(r, id=r["id"].replace("src", "fixplace", 1), src=r["id"])
            if "door" in r:
                tr = r["door"]["to_ref"].replace("src", "fixplace", 1)
                nr["door"] = dict(r["door"], to_ref=tr)
                if r["door"]["to_space"] == "exterior":
                    nd = next(x for x in drefs if x["src"] == r["door"]["to_ref"])
                    nr["door"]["to_pos"] = nd["pos"]
            dint[sid].append(nr)
    dnpcs = list(snpcs)
    dd = root / "draft.fixplace"
    write_bundle(root, "draft.fixplace", "draft", "Fixture place draft", [0, 0, 0], gcells, drefs, dint, sb,
                 (1.0, "y", "river"), dnpcs, {"stamp": {"key": hashlib.sha256(b"draft" + gsha.encode()).hexdigest()[:16],
                                           "inputs": {"ground": gsha}, "tool": "make_fixture", "at": AT}})
    bed = {sid: next(r for r in rs if r["id"].endswith(".bed")) for sid, rs in dint.items()}
    stop = lambda s, h, k, at: {"start": s, "hours": h, "kind": k, "at": at}  # noqa: E731
    hp = drefs[0]["pos"]
    people = [
        {"id": "fixplace.p1", "name": "Ada Fixwright", "base_from": "Fix.esm:002000", "role": "smith",
         "home": "FixHouse01", "bed": {"space": "FixHouse01", "ref": bed["FixHouse01"]["id"]},
         "work": {"space": "exterior", "pos": hp, "radius": 300}, "services": [{"kind": "vendor", "detail": "Sells smithing goods"}],
         "faction_ranks": [{"faction": "FixVillage", "rank": 1}],
         "routine": [stop(6, 2, "sandbox", {"space": "FixHouse01", "pos": [0, 0, 0], "radius": 200}),
                     stop(8, 8, "work", {"space": "exterior", "pos": hp, "radius": 300}),
                     stop(17, 2, "eat", {"space": "FixHouse01", "ref": "fixplace.FixHouse01.table", "radius": 150}),
                     stop(22, 8, "sleep", {"space": "FixHouse01", "ref": bed["FixHouse01"]["id"], "radius": 50})]},
        {"id": "fixplace.p2", "name": "Bram Fixguard", "base_from": "Fix.esm:002001", "role": "guard",
         "home": "FixHouse02", "bed": {"space": "FixHouse02", "ref": bed["FixHouse02"]["id"]},
         "work": {"space": "exterior", "pos": [hp[0] + 800, hp[1], hp[2]], "radius": 200}, "services": [],
         "faction_ranks": [{"faction": "FixVillage", "rank": 2}],
         "routine": [stop(6, 12, "work", {"space": "exterior", "pos": hp, "radius": 400}),
                     stop(18, 2, "eat", {"space": "FixHouse02", "ref": "fixplace.FixHouse02.table", "radius": 150}),
                     stop(22, 8, "sleep", {"space": "FixHouse02", "ref": bed["FixHouse02"]["id"], "radius": 50})],
         "patrol": {"points": [[hp[0] + 200 * k, hp[1] + 300 * (k % 2)] for k in range(4)], "loop": True}},
    ]
    jlines(dd / "people.jsonl", people)
    jlines(dd / "paths.jsonl", [{"id": "fixplace.path1", "kind": "street",
                                 "points": [[2000, 2000], [3000, 2600], [4200, 3000], [5200, 4200]], "width": 200, "style": "fix_path"},
                                {"id": "fixplace.walk1", "kind": "walkway", "points": [[2400, 4600], [3400, 4800]], "width": 160,
                                 "style": "boardwalk"}])
    jlines(dd / "clear.jsonl", [{"base": gb.rows["Fix_Fern"]["key"], "pos": [grefs[200]["pos"][0], grefs[200]["pos"][1], 0], "by": "draft",
                                 "why": "street", "ref": grefs[200]["id"]}])
    jlines(dd / "land.jsonl", [{"cell": [0, 0], "verts": [[16, 16, 60.0], [16, 17, 40.0]], "textures": None, "why": "level the smithy"}])

    # hamlet: tiny source
    hb = Bases()
    hrefs = []
    for i in range(5):
        hrefs.append(ref(f"hm.r{i}", hb.get(f"Fix_Hut{i % 2}", "building"), "building",
                         [20 * CELL + 800 * i + 600, 20 * CELL + 1000, 300], [0, 0, 0]))
    write_bundle(root, "src.fix.hamlet", "source", "Fix hamlet", [20 * CELL, 20 * CELL, 0], [[20, 20]], hrefs, {}, hb,
                 (3.0, None, "lake"))

    jwrite(out / "place.json", {"place_id": "fixplace", "title": "Fixture place", "source_id": "fix.village",
                                "similar": ["fix.hamlet"], "fit": fit})
    print(f"fixture written to {out}")


if __name__ == "__main__":
    main()
