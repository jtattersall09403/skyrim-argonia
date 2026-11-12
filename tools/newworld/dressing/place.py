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
- Each thing sits on the ground with a random yaw and a scale in SCALE; spawners and effects sit as they are.
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
                    placed.append({"base": base, "x": round(x, 1), "y": round(y, 1), "z": round(max(cv.ground(ry, rx), 0.0), 1),
                                   "rz": round(float(rng.uniform(0, 360)), 1),
                                   "scale": round(float(rng.uniform(*SCALE)), 3), "kind": k, "region": reg,
                                   "cell": [cx, cy], "id": ident})
            for p in placed[:CAP]:
                p["fid"] = f"{fid_of(p['id'], given):06X}"
                lines.append(json.dumps(p, sort_keys=True))
                tally[(p["region"], p["kind"])] += 1
        (d / f"cy{cy:+04d}.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""))
    h = hashlib.sha256()
    for f in sorted(d.glob("cy*.jsonl")):
        h.update(f.name.encode() + f.read_bytes())
    res = {"build_id": man["build_id"], "refs": sum(tally.values()), "shard_sha256": h.hexdigest(),
           "by_region_kind": {f"{r}|{k}": [n, round(expect[(r, k)], 2)] for (r, k), n in sorted(tally.items())},
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
