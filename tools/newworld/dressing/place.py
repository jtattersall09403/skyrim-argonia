"""The dressing stage: small signature things, each kind in one or two regions, placed by hyperlocal habitat.

    python -m tools.newworld.dressing.place run   [--out out/newworld/plugin]
    python -m tools.newworld.dressing.place check [--out out/newworld/plugin]

Reads the kinds (newworld/sources/dressing/kinds.json: each kind's regions, bases, habitat, Skyrim sort and rate),
Skyrim's measure of the same sorts (skyrim_measures.json), each cell's region (the database's cell table), the
landcover rasters, the heightmap, the placed flora (refs/flora), the held cells of built places and the map's
teleport landings. Writes `<out>/dressing/`: `cy<+NNN>.jsonl` (one reference a line: base, x, y, z, rz, scale, kind,
region, cell, id, fid) and `manifest.json`; on `check`, `check.json`.

It writes beside `refs/`, not in it: nothing it places is a navmesh obstacle (small or walk-through bases, checked),
so the navmesh and its key never read it. The world writer (NewWorld.cs) reads `dressing/` as plain REFR.

How a cell is dressed (decision 0034: Skyrim's own numbers):
- A kind's rate is its `per100` (references per 100 cells where its habitat holds ground), never above Skyrim's
  outdoor rate for its sort (skyrim_measures.json); the count is a Poisson draw on the cell's habitat share.
- Habitat (place.py HABITATS over the ecology stage's cell view): canopy (under trees), forest (near placed
  understorey), open, rock (rock habitats), slope (dry ground of 15 to 35 degrees), marsh (marsh habitats and
  shallow fresh water edges), reeds (within REED_M of a placed reed or fern, or a marsh habitat), shore (within
  SHORE_M of water). Never on a road (ROAD_M), in a held cell, a landing's cell, or water deeper than its edge.
- Each thing sits on the ground (a floating kind `lift` units above it) with a random yaw and a scale in SCALE; spawners and effects sit as they are.
- A hanging kind (habitat `hang`) hangs from the hang points (hang_points.json) of placed Hist and Hist-grove trees
  near a built place, by its rope's top, never tilted, at the source mod's rate and count per tree (lanterns());
  check_hung judges each one.
Every draw is seeded by the cell and kind, so a rerun writes the same bytes. A reference's id is DRESS_FIRST + its
identity's digest (cell, kind, ordinal) in the `dressing` idspace row, probed on a collision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
LC = REPO / "out/newworld/landcover"
SRC = REPO / "newworld/sources/dressing"
IDENTITY = REPO / "newworld/sources/identity"
PLUGIN = REPO / "out/newworld/plugin"

DRESS_FIRST, DRESS_LAST = 0x0A0000, 0x0FFFFF   # tools/newworld/idspace.py row `dressing`
SAMPLE = 128.0
ROAD_M, SHORE_M, REED_M = 6.0, 12.0, 6.0
SLOPE = (15.0, 35.0)
SCALE = (0.85, 1.15)
NO_SCALE = ("ACTI", "MSTT")                     # spawners and effects stay at their own size
MAX_HALF = 160.0                                # bounds half-extent (units): larger is an obstacle or a far-off shape
CAP = 6                                         # dressing references in one cell
LOD_FLAG = 0x8000                               # STAT "has distant LOD"
TOLERANCE = (0.4, 1.6)                          # placed / expected per kind and region
TREE_CLS = ("canopy_tree", "understorey")       # placed flora a hanging kind hangs from
NEAR_CELLS = 2                                  # a tree this many cells from a built place is near a settlement
BELOW_MIN = 60.0                                # units of air under a hanging thing's bottom
PART_M = 300.0                                  # units: trees standing this close are parts of one tree (a Hist's trunk, crown, glands)
CARRIERS_CAP = 1                                # trees carrying hanging things in one cell
ANCHOR_TOL = 3.5                                # units (5 cm): a hanging thing's anchor from its tree's hang point


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def kinds() -> dict:
    return json.loads((SRC / "kinds.json").read_text())["kinds"]


def fid_of(identity: str, given: set) -> int:
    span = DRESS_LAST - DRESS_FIRST + 1
    i = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "big") % span
    while DRESS_FIRST + i in given:
        i = (i + 1) % span
    given.add(DRESS_FIRST + i)
    return DRESS_FIRST + i


def habitat_mask(cv, hab: str, reeds: np.ndarray) -> np.ndarray:
    from tools.newworld.ecology.place import MARSH, ROCK
    dry = cv.dry & (cv.road > ROAD_M)
    m = {
        "canopy": dry & (cv.canopy >= 120),
        "forest": dry & cv.masks["bush"],
        "open": dry & cv.masks["open"],
        "rock": dry & np.isin(cv.hab, ROCK),
        "slope": dry & (cv.slope >= SLOPE[0]) & (cv.slope < SLOPE[1]),
        "marsh": dry & np.isin(cv.hab, MARSH),
        "reeds": dry & (reeds | np.isin(cv.hab, MARSH)),
        "shore": dry & (cv.shore < SHORE_M),
    }[hab]
    return m[:32, :32]


def reed_near(out: Path) -> dict:
    """(cx, cy) -> [(x, y)] of placed reeds and ferns (refs/flora)."""
    res: dict = {}
    for f in sorted((out / "refs/flora").glob("cy*.jsonl")):
        for line in f.read_text().splitlines():
            if line:
                o = json.loads(line)
                if o.get("cls") in ("reed", "fern"):
                    res.setdefault((math.floor(o["x"] / 4096), math.floor(o["y"] / 4096)), []).append((o["x"], o["y"]))
    return res


def lantern_shape(model: str) -> dict:
    """A hanging thing's anchor (the top of its rope, mesh frame) and its drop below the anchor (units)."""
    from tools.newworld.place.seat import mesh_points
    p = mesh_points(model)
    top = float(p[:, 2].max())
    a = p[p[:, 2] > top - 2.0][:, :2].mean(0)
    return {"anchor": [round(float(a[0]), 1), round(float(a[1]), 1), round(top, 1)], "drop": round(top - float(p[:, 2].min()), 1)}


def hang_world(tree: dict, point) -> np.ndarray:
    """A hang point (mesh frame) posed by the placed tree's rotation, scale and final position."""
    from tools.newworld.place.seat import rot_matrix
    return rot_matrix(tree["rx"], tree["ry"], tree["rz"]) @ (np.asarray(point[:3], float) * tree["scale"]) + \
        np.array([tree["x"], tree["y"], tree["z"]], float)


def trees_by_cell(out: Path, bases: dict) -> dict:
    """(cx, cy) -> placed trees (after the edits), each with its bounds' inscribed sphere (the solid core of a tree:
    the bounds' full sphere is mostly the open air under the canopy a lantern hangs in)."""
    from tools.newworld.place.seat import rot_matrix
    obnd = {b["ref"]: b.get("obnd") for b in json.loads((out / "refs/flora/bases.json").read_text())["bases"]}
    res: dict = {}
    for f in sorted((out / "refs/flora").glob("cy*.jsonl")):
        for line in f.read_text().splitlines():
            if not line:
                continue
            o = json.loads(line)
            if o.get("cls") not in TREE_CLS:
                continue
            ob = obnd.get(o["base"]) or [0] * 6
            mid = np.array([(ob[0] + ob[3]) / 2, (ob[1] + ob[4]) / 2, (ob[2] + ob[5]) / 2], float)
            half = np.array([(ob[3] - ob[0]) / 2, (ob[4] - ob[1]) / 2, (ob[5] - ob[2]) / 2], float)
            c = rot_matrix(o["rx"], o["ry"], o["rz"]) @ (mid * o["scale"]) + np.array([o["x"], o["y"], o["z"]])
            t = {k: o[k] for k in ("base", "x", "y", "z", "rx", "ry", "rz", "scale", "id")}
            t["sphere"] = (c, float(half.min()) * o["scale"])
            t["hang"] = bases.get(o["base"], {}).get("points", [])
            res.setdefault((math.floor(o["x"] / 4096), math.floor(o["y"] / 4096)), []).append(t)
    return res


class Raster:
    """Landcover and height samples at a world point."""

    def __init__(self, man: dict, legend: dict):
        self.ox, self.oy = legend["origin_world"]
        self.a = {k: np.load(LC / f"{k}.npy", mmap_mode="r") for k in ("habitat", "flags", "road")}
        self.hm = np.load(man["heightmap"], mmap_mode="r")
        self.grove = legend["habitats"].index("hist_grove")

    def at(self, x: float, y: float) -> dict:
        i = min(max(int(round((x - self.ox) / SAMPLE)), 0), self.hm.shape[1] - 1)
        j = min(max(int(round((self.oy - y) / SAMPLE)), 0), self.hm.shape[0] - 1)
        return {"ground": float(self.hm[j, i]), "water": bool(self.a["flags"][j, i] & 1),
                "road": float(self.a["road"][j, i]) / 10, "grove": int(self.a["habitat"][j, i]) == self.grove}


def near_held(cell: tuple, held: set) -> bool:
    return any((cell[0] + dx, cell[1] + dy) in held for dx in range(-NEAR_CELLS, NEAR_CELLS + 1)
               for dy in range(-NEAR_CELLS, NEAR_CELLS + 1))


def hang_fit(t: dict, hp, shape: dict, rs: Raster, others: list) -> dict | None:
    """The lantern under one hang point, or None: over water, a road or ground too close, or inside a neighbour (a
    tree standing within PART_M of this one is a part of the same tree, as a Hist is built of several pieces)."""
    w = hang_world(t, hp)
    s = rs.at(w[0], w[1])
    bottom = w[2] - shape["drop"]
    if s["water"] or s["road"] < ROAD_M or bottom - max(s["ground"], 0.0) < BELOW_MIN:
        return None
    for u in others:
        if u is t or (u["x"] - t["x"]) ** 2 + (u["y"] - t["y"]) ** 2 < PART_M ** 2:
            continue
        c, r = u["sphere"]
        if np.linalg.norm(w - c) < r or np.linalg.norm(w - np.array([0, 0, shape["drop"]]) - c) < r:
            return None
    return {"w": w, "site": s}


def is_carrier(t: dict, site: dict) -> bool:
    """A tree that carries lanterns: a Hist (its base's editor id names Hist: tree, trunk or gland) or a tree of a Hist grove."""
    return bool(t["hang"]) and ("Hist" in t["base"].split(":", 1)[-1] or site["grove"])


def hang_tree(t: dict, k: int, base_of, rng, shapes: dict, rs: "Raster", others: list) -> list[dict]:
    """Up to k lanterns on one tree, each on its own hang point (drawn in a seeded order), each fitting."""
    out = []
    for hn in rng.permutation(len(t["hang"])):
        if len(out) == k:
            break
        base = base_of(rng)
        rz = float(rng.uniform(0, 360))
        sh = shapes[base]
        f = hang_fit(t, t["hang"][int(hn)], sh, rs, others)
        if f is None:
            continue
        a = math.radians(rz)
        ax, ay = sh["anchor"][0], sh["anchor"][1]
        w = f["w"]
        out.append({"base": base, "x": round(w[0] - (ax * math.cos(a) - ay * math.sin(a)), 2),
                    "y": round(w[1] - (ax * math.sin(a) + ay * math.cos(a)), 2), "z": round(w[2] - sh["anchor"][2], 2),
                    "rz": round(rz, 1), "scale": 1.0, "tree": t["id"], "hang": int(hn)})
    return out


def lanterns(out: Path, ks: dict, cells: dict, held: set, man: dict, legend: dict) -> tuple[dict, dict]:
    """({cy: hanging lanterns}, {"region|kind": eligible cells}). In each hanging kind's regions, a cell within
    NEAR_CELLS of a built place (never a held cell) is eligible when it holds a carrier (is_carrier) with a hang point
    the longest lantern fits. Of a region's eligible cells, the share the source's rate gives (bound_per100 over the
    mean of per_carrier) carries, chosen by a digest order; one carrier in each takes a count drawn from the source's
    own counts per carrier, one lantern per hang point (as many as fit)."""
    from tools.newworld.dressing.hang_points import load
    hang = {k: v for k, v in ks.items() if v["habitat"] == "hang"}
    if not hang:
        return {}, {}
    trees = trees_by_cell(out, load())
    rs = Raster(man, legend)
    shapes: dict = {}
    res: dict = {}
    pending: dict = {}
    eligible = Counter()
    for (cx, cy), ts in sorted(trees.items()):
        c = cells.get((cx // 2, cy // 2))
        if not c or c.get("margin") or (cx, cy) in held or not near_held((cx, cy), held):
            continue
        reg = c.get("region_id")
        for k, v in sorted(hang.items()):
            if reg not in v["regions"]:
                continue
            for b in v["bases"]:
                if b not in shapes:
                    shapes[b] = lantern_shape(base_facts({b})[b]["mesh"])
            others = [u for dx in (-1, 0, 1) for dy in (-1, 0, 1) for u in trees.get((cx + dx, cy + dy), [])]
            longest = max((shapes[b] for b in v["bases"]), key=lambda sh: sh["drop"])
            carriers = [t for t in ts if is_carrier(t, rs.at(t["x"], t["y"]))
                        and any(hang_fit(t, hp, longest, rs, others) for hp in t["hang"])]
            if not carriers:
                continue
            eligible[(reg, k)] += 1
            pending.setdefault((reg, k), []).append(((cx, cy), carriers, others))
    for (reg, k), sites in sorted(pending.items()):
        v = hang[k]
        per = v["per_carrier"]
        take = round(len(sites) * v["bound_per100"] / 100 / (sum(per) / len(per)))
        sites.sort(key=lambda s: hashlib.sha256(f"{s[0][0]},{s[0][1]}/{k}".encode()).hexdigest())
        for (cx, cy), carriers, others in sorted(sites[:take], key=lambda s: s[0]):
            rng = np.random.default_rng((0xD2E7, cx & 0xFFFF, cy & 0xFFFF, int(hashlib.sha256(k.encode()).hexdigest()[:6], 16)))
            t = carriers[int(rng.integers(len(carriers)))]
            want = int(per[int(rng.integers(len(per)))])
            for o, h in enumerate(hang_tree(t, want, lambda r: v["bases"][int(r.integers(len(v["bases"])))],
                                            rng, shapes, rs, others)):
                h.update({"kind": k, "region": reg, "cell": [cx, cy], "id": f"{cx},{cy}/{k}/{o}"})
                res.setdefault(cy, []).append(h)
    return res, {f"{r}|{k}": n for (r, k), n in sorted(eligible.items())}


def build(out: Path) -> dict:
    from tools.newworld.ecology.place import Cellview, flora_near, held_cells, jsonl
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    if legend["build_id"] != man["build_id"]:
        raise RuntimeError("landcover is another terrain build: rerun landcover")
    g = man["grid"]
    ks = kinds()
    meas = json.loads((SRC / "skyrim_measures.json").read_text())["refs_per_100_cells"]
    by_region: dict = {}
    for k, v in sorted(ks.items()):
        for r in v["regions"]:
            by_region.setdefault(r, []).append(k)
    cells = {(c["x"], c["y"]): c for c in jsonl("cell")}
    held = held_cells(out)
    flora = flora_near(out)
    reeds = reed_near(out)
    arr = {k: np.load(LC / f"{k}.npy", mmap_mode="r") for k in ("habitat", "kind", "flags", "canopy", "slope", "shore", "road")}
    hm = np.load(man["heightmap"], mmap_mode="r")
    origin = tuple(legend["origin_world"])
    d = out / "dressing"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("cy*.jsonl"):
        old.unlink()
    given: set = set()
    tally, expect = Counter(), Counter()
    hung, eligible = lanterns(out, ks, cells, held, man, legend)
    for rk, n in eligible.items():
        r, k = rk.split("|")
        expect[(r, k)] += ks[k]["bound_per100"] / 100 * n
    for cy in range(g["cy_top"], g["cy_bottom"] - 1, -1):
        north = (g["cy_top"] - cy) * 32
        rs = slice(north, north + 33)
        sl = {"hm": np.asarray(hm[rs]), "flags": np.asarray(arr["flags"][rs]), "hab": np.asarray(arr["habitat"][rs]),
              "kind": np.asarray(arr["kind"][rs]), "canopy": np.asarray(arr["canopy"][rs]), "slope": np.asarray(arr["slope"][rs]),
              "shore": np.asarray(arr["shore"][rs]), "road": np.asarray(arr["road"][rs])}
        lines = []
        for i in range(g["cells_x"]):
            cx = g["cx0"] + i
            c = cells.get((cx // 2, cy // 2))
            if not c or c.get("margin") or (cx, cy) in held or c.get("region_id") not in by_region:
                continue
            reg = c["region_id"]
            cv = Cellview(sl, i, legend, flora[(cx, cy)], origin, north)
            rmask = cv._near(reeds.get((cx, cy), []), REED_M)
            placed = []
            for k in by_region[reg]:
                v = ks[k]
                if v["habitat"] == "hang":
                    continue
                m = habitat_mask(cv, v["habitat"], rmask)
                share = float(m.mean())
                if share <= 0:
                    continue
                rate = min(v["per100"], meas[v["sort"]]) / 100 * share
                expect[(reg, k)] += rate
                rng = np.random.default_rng((0xD2E5, cx & 0xFFFF, cy & 0xFFFF, int(hashlib.sha256(k.encode()).hexdigest()[:6], 16)))
                n = int(rng.poisson(rate))
                ys, xs = np.nonzero(m)
                for o in range(n):
                    j = int(rng.integers(len(ys)))
                    ry, rx = ys[j] + rng.random(), xs[j] + rng.random()
                    x, y = cv.world(ry, rx)
                    base = v["bases"][int(rng.integers(len(v["bases"])))]
                    ident = f"{cx},{cy}/{k}/{o}"
                    placed.append({"base": base, "x": round(x, 1), "y": round(y, 1), "z": round(max(cv.ground(ry, rx), 0.0) + v.get("lift", 0), 1),
                                   "rz": round(float(rng.uniform(0, 360)), 1),
                                   "scale": round(float(rng.uniform(*SCALE)), 3), "kind": k, "region": reg,
                                   "cell": [cx, cy], "id": ident})
            for p in placed[:CAP]:
                p["fid"] = f"{fid_of(p['id'], given):06X}"
                lines.append(json.dumps(p, sort_keys=True))
                tally[(p["region"], p["kind"])] += 1
        for p in hung.get(cy, []):
            p["fid"] = f"{fid_of(p['id'], given):06X}"
            lines.append(json.dumps(p, sort_keys=True))
            tally[(p["region"], p["kind"])] += 1
        (d / f"cy{cy:+04d}.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""))
    h = hashlib.sha256()
    for f in sorted(d.glob("cy*.jsonl")):
        h.update(f.name.encode() + f.read_bytes())
    res = {"build_id": man["build_id"], "refs": sum(tally.values()), "shard_sha256": h.hexdigest(),
           "by_region_kind": {f"{r}|{k}": [n, round(expect[(r, k)], 2)] for (r, k), n in sorted(tally.items())},
           "hang_eligible_cells": eligible,
           "expected_only": {f"{r}|{k}": round(e, 2) for (r, k), e in sorted(expect.items()) if (r, k) not in tally}}
    (d / "manifest.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    log(f"dressing: {res['refs']} references in {len(res['by_region_kind'])} region kinds")
    return res


def base_facts(keys: set) -> dict:
    """plugin:edid -> {sig, lod, half, mesh, assets_ok} from the load order's records and the asset resolver."""
    from tools.argonia_world.esm import Plugin
    from tools.newworld.assets_audit import Audit, active_plugins, norm_asset
    from tools.places.assets.resolve import DATA, STACK, Resolver
    audit = Audit(Resolver(), active_plugins(STACK / "MO2/profiles/NewWorld"))
    out: dict = {}
    for plug in sorted({k.split(":", 1)[0] for k in keys}):
        want = {k.split(":", 1)[1] for k in keys if k.startswith(plug + ":")}
        for r in Plugin.read(DATA / plug, {"STAT", "MSTT", "ACTI", "FLOR", "LIGH"}).records():
            if r.edid in want:
                ob = r.sub("OBND")
                half = max(abs(v) for v in struct.unpack_from("<6h", ob)) if ob and len(ob) >= 12 else 0
                mesh = norm_asset(r.zstr("MODL") or "") if r.zstr("MODL") else ""
                tex = audit.nif(mesh) if mesh else None
                ok = tex is not None and all(audit.R.read(norm_asset(t)) is not None for t in tex)
                out[f"{plug}:{r.edid}"] = {"sig": r.sig, "lod": bool(r.sig == "STAT" and r.flags & LOD_FLAG),
                                          "half": half, "mesh": mesh, "assets_ok": ok}
    return out


def neighbours() -> dict:
    adj: dict = {}
    for p in json.loads((IDENTITY / "adjacency.json").read_text())["pairs"]:
        a, b = p.split("|")
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return adj


def check_kinds(ks: dict, facts: dict, adj: dict, land: list[str]) -> list[str]:
    """The catalogue's rules, without a placement: bases real, complete, small, no LOD; each kind in one or two
    regions; every land region with two kinds no neighbour has."""
    faults = []
    for k, v in ks.items():
        if not 1 <= len(v["regions"]) <= 2:
            faults.append(f"{k}: in {len(v['regions'])} regions")
        for b in v["bases"]:
            f = facts.get(b)
            if f is None:
                faults.append(f"{k}: base {b} not in the load order")
                continue
            if not f["assets_ok"]:
                faults.append(f"{k}: base {b} has missing assets ({f['mesh']})")
            if f["lod"]:
                faults.append(f"{k}: base {b} has distant LOD")
            if f["sig"] not in NO_SCALE and f["half"] > MAX_HALF:
                faults.append(f"{k}: base {b} half-extent {f['half']} > {MAX_HALF}")
    for r in land:
        own = [k for k, v in ks.items() if r in v["regions"] and not any(n in v["regions"] for n in adj.get(r, ()))]
        if len(own) < 2:
            faults.append(f"{r}: {len(own)} signature kinds no neighbour has (want 2)")
    return faults


def check_hung(out: Path, ks: dict, man: dict, land_man: dict) -> list[str]:
    """Each hanging thing hangs from its own hang point of a tree that stands after the edits (anchor within
    ANCHOR_TOL), with air, dry ground and no road below it; each carrier holds a count within the source's range,
    CARRIERS_CAP carriers a cell; each kind's lanterns per 100 eligible cells within TOLERANCE of its bound."""
    from tools.newworld.dressing.hang_points import load
    hang = {k for k, v in ks.items() if v["habitat"] == "hang"}
    if not hang:
        return []
    trees = {t["id"]: t for ts in trees_by_cell(out, load()).values() for t in ts}
    rs = Raster(land_man, json.loads((LC / "legend.json").read_text()))
    shapes: dict = {}
    faults, per_tree, per_rk = [], Counter(), Counter()
    carriers: dict = {}
    for f in sorted((out / "dressing").glob("cy*.jsonl")):
        for line in f.read_text().splitlines():
            o = json.loads(line) if line else None
            if not o or o["kind"] not in hang:
                continue
            per_rk[f"{o['region']}|{o['kind']}"] += 1
            t = trees.get(o.get("tree"))
            if t is None or o.get("hang", 99) >= len(t["hang"]):
                faults.append(f"{o['id']}: its tree or hang point is not placed")
                continue
            per_tree[(o["kind"], t["id"], o["hang"])] += 1
            carriers.setdefault(tuple(o["cell"]), set()).add(t["id"])
            if o["base"] not in shapes:
                shapes[o["base"]] = lantern_shape(base_facts({o["base"]})[o["base"]]["mesh"])
            sh = shapes[o["base"]]
            a = math.radians(o["rz"])
            ax, ay, az = sh["anchor"]
            anchor = np.array([o["x"] + ax * math.cos(a) - ay * math.sin(a), o["y"] + ax * math.sin(a) + ay * math.cos(a), o["z"] + az])
            if np.linalg.norm(anchor - hang_world(t, t["hang"][o["hang"]])) > ANCHOR_TOL:
                faults.append(f"{o['id']}: anchor off its tree's hang point")
            if hang_fit(t, t["hang"][o["hang"]], sh, rs, []) is None:
                faults.append(f"{o['id']}: over water or a road, or too little air below")
    faults += [f"{k[1]} hang point {k[2]}: {n} lanterns on one point" for k, n in per_tree.items() if n > 1]
    by_tree = Counter((k, t) for k, t, _ in per_tree)
    for (k, t), n in by_tree.items():
        if n > max(ks[k]["per_carrier"]):
            faults.append(f"{t}: {n} lanterns, over the source's {max(ks[k]['per_carrier'])} a carrier")
    faults += [f"{c}: {len(ts)} carrying trees in one cell" for c, ts in carriers.items() if len(ts) > CARRIERS_CAP]
    for rk, n in per_rk.items():
        cells = man.get("hang_eligible_cells", {}).get(rk, 0)
        bound = ks[rk.split("|")[1]]["bound_per100"]
        if not cells or 100 * n / cells > bound * TOLERANCE[1]:
            faults.append(f"{rk}: {n} in {cells} eligible cells, over {bound} per 100")
    return faults


def check(out: Path) -> int:
    from tools.newworld.world.texture import PROVINCES
    ks = kinds()
    facts = base_facts({b for v in ks.values() for b in v["bases"]})
    land = [r for p in PROVINCES.values() for r in p["regions"]]
    faults = check_kinds(ks, facts, neighbours(), land)
    d = out / "dressing"
    man = json.loads((d / "manifest.json").read_text()) if (d / "manifest.json").exists() else None
    refs = 0
    if man is None:
        faults.append("no dressing output: run the stage")
    else:
        land_man = json.loads((out / "land/manifest.json").read_text())
        if man["build_id"] != land_man["build_id"]:
            faults.append("dressing is another terrain build")
        held = {tuple(c) for c in __import__("tools.newworld.ecology.place", fromlist=["held_cells"]).held_cells(out)}
        seen: set = set()
        for f in sorted(d.glob("cy*.jsonl")):
            for line in f.read_text().splitlines():
                if not line:
                    continue
                o = json.loads(line)
                refs += 1
                fid = int(o["fid"], 16)
                if not DRESS_FIRST <= fid <= DRESS_LAST or fid in seen:
                    faults.append(f"{o['id']}: id {o['fid']} out of range or repeated")
                seen.add(fid)
                if tuple(o["cell"]) in held:
                    faults.append(f"{o['id']}: in a held cell")
                if o["region"] not in ks[o["kind"]]["regions"]:
                    faults.append(f"{o['id']}: kind outside its regions")
        faults += check_hung(out, ks, man, land_man)
        for rk, (n, e) in man["by_region_kind"].items():
            if e >= 5 and not TOLERANCE[0] <= n / e <= TOLERANCE[1]:
                faults.append(f"{rk}: {n} placed against {e} expected")
    res = {"refs": refs, "faults": faults[:200], "fault_count": len(faults), "kinds": len(ks)}
    if d.is_dir():
        (d / "check.json").write_text(json.dumps(res, indent=1))
    print(f"dressing check: {refs} references, {len(ks)} kinds; faults {len(faults)}")
    for f in faults[:40]:
        print("  " + f)
    return 1 if faults else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=("run", "check"))
    ap.add_argument("--out", type=Path, default=PLUGIN)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        build(a.out)
        return 0
    return check(a.out)


if __name__ == "__main__":
    sys.exit(main())
