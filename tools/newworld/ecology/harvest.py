"""The harvestables of the ecology stage: each region's lore plants bound to real FLOR, TREE and ACTI records, and the
region brought to Skyrim's measured density of them for its habitat classes.

    python -m tools.newworld.ecology.harvest catalogue         # the plugins' harvestable bases -> harvest_bases.json
    python -m tools.newworld.ecology.harvest run   [--out out/newworld/plugin]
    python -m tools.newworld.ecology.harvest check [--out out/newworld/plugin]

Reads harvestables.json (kinds bound to records, the lore map, Skyrim's class pools, the new records), harvest_bases.json
(every FLOR and TREE of the plugins we hold that yields an ingredient, and the Nirnroot activators), the regions'
lore harvestables (regions/*.json), skyrim_measures.json, the landcover rasters and the placed flora. Writes
`<out>/ecology/harvest/`: `cy<+NNN>.jsonl` (one reference a line), `records.json` (the new FLOR and INGR records for
the world writer), `manifest.json` and, on `check`, `check.json`. The flora stage is never touched: nothing is written
under `refs/`, so the navmesh, the LOD plan and the ground stay as they are.

How a region is filled (decision 0034: Skyrim's own numbers):
1. Skyrim's density by class (water 75, shore 460, forest 386, mountain 79, open 12.5 per 100 cells) is the region's
   target: each of its cells counts its class's rate. What the flora stage already placed that yields an ingredient
   counts toward it.
2. Each lore plant of the region (the lore map binds a lore ingredient to a kind, or says it is a creature's drop) is
   given at least LORE_PER_100 per 100 cells (never fewer than LORE_MIN), net of what the flora stage placed of it,
   on the ground the lore row names, spread over the region by the area of that ground in each cell.
3. The rest of the target is Skyrim's variety for the cell's class (the class pools), the region's own lore plants
   twice as likely, spread over the cells that hold ground for a pool, the cells short of their class's rate first.
Every draw is seeded by the region and the cell, so a rerun writes the same bytes. A reference's id is in the ecology
range (idspace row `ecology`), after the actors', probed on a collision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from tools.newworld.ecology import place as P

REPO = P.REPO
SRC = P.SRC
LC = P.LC
CATALOGUE_PLUGINS = ("Skyrim.esm", "Dawnguard.esm", "Dragonborn.esm", "ccBGSSSE001-Fish.esm", "ccBGSSSE037-Curios.esl",
                     "Here There Be Monsters - Curse of Cipactli.esp", "King of the Murkmire.esp",
                     "Tropical Skyrim.esp", "Black Marsh.esm")
EXTRA_BASES = ("Skyrim.esm:TreeFloraNirnroot01", "Skyrim.esm:TreeFloraNirnrootRed01")   # activators that give an ingredient
LORE_PER_100, LORE_MIN = 2, 6          # a lore plant's refs per 100 cells of its region, at least
LORE_WEIGHT = 2.0                      # the region's own lore plants against the class pool's, in the filler
BED_MIN, BED_MAX = 0.5, 10.0           # metres under the water of a bed plant
BANK_M = 6.0
CELL_CAP = 60                          # harvestable references one cell takes from this stage
MIN_GAP = 128.0                        # two placements of this stage keep this far apart, units
CLASSES = ("water", "shore", "forest", "mountain", "open")
FRESH, SALT, BRACKISH = P.FRESH, P.SALT, P.BRACKISH
HABITAT_MASK = {"water-fresh": "bed-fresh", "water-salt": "bed-salt", "water-brackish": "bed-brackish"}   # a lore row's habitat -> mask
FILL_SLACK = 1.15                      # the filler is drawn this much over, for the draws that find no room
BASE_RE = re.compile(r'"base":"([^"]+)"')


def log(*a):
    print(*a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- the sources

def load_data() -> dict:
    d = json.loads((SRC / "harvestables.json").read_text())
    d["catalogue"] = json.loads((SRC / "harvest_bases.json").read_text())
    return d


def region_lore(data: dict) -> dict:
    """region -> [(kind, habitat mask, lore ingredient)] of the lore plants the lore map binds to a kind."""
    res = {}
    for f in sorted((SRC / "regions").glob("*.json")):
        d = json.loads(f.read_text())
        rows, seen = [], set()
        for h in d["harvestables"]:
            m = data["lore"].get(h["ingredient"])
            if m and m.get("kind") and m["kind"] not in seen:
                seen.add(m["kind"])
                k = data["kinds"][m["kind"]]
                rows.append((m["kind"], k.get("mask", HABITAT_MASK.get(h["habitat"], h["habitat"])), h["ingredient"]))
        res[d["region"]] = rows
    return res


def kind_of_base(data: dict) -> dict:
    return {r: k for k, v in data["kinds"].items() for r in v["records"]}


# ---------------------------------------------------------------- the catalogue (game data on this machine)

# ---------------------------------------------------------------- the cells

def mask_of(cv: "P.Cellview", name: str) -> np.ndarray:
    """A habitat's ground in one cell, 32 x 32 samples, from the ecology stage's masks and the bed and bank rules."""
    if name in cv.masks:
        return cv.masks[name][:32, :32]
    wet = cv.water & (cv.depth >= BED_MIN) & (cv.depth <= BED_MAX)
    if name == "bed-fresh":
        m = wet & np.isin(cv.kind, FRESH)
    elif name == "bed-salt":
        m = wet & np.isin(cv.kind, SALT)
    elif name == "bed-brackish":
        m = wet & np.isin(cv.kind, BRACKISH)
    elif name == "bank":
        m = cv.dry & (cv.shore < BANK_M)
    else:
        raise KeyError(name)
    return m[:32, :32]


def cells_of(out: Path, want: set | None = None):
    """Every cell the ecology fills (not a margin, held or landing cell), with its Cellview: (cx, cy, db cell, Cellview);
    only the cells of `want` when given."""
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    if legend["build_id"] != man["build_id"]:
        raise RuntimeError("landcover is another terrain build: rerun landcover")
    g = man["grid"]
    cells = {(c["x"], c["y"]): c for c in P.jsonl("cell")}
    held = P.held_cells(out)
    flora = P.flora_near(out)
    arr = {k: np.load(LC / f"{k}.npy", mmap_mode="r") for k in ("habitat", "kind", "flags", "canopy", "slope", "shore", "road")}
    hm = np.load(man["heightmap"], mmap_mode="r")
    origin = tuple(legend["origin_world"])
    for cy in range(g["cy_top"], g["cy_bottom"] - 1, -1):
        north = (g["cy_top"] - cy) * 32
        rs = slice(north, north + 33)
        sl = {"hm": np.asarray(hm[rs]), "flags": np.asarray(arr["flags"][rs]), "hab": np.asarray(arr["habitat"][rs]),
              "kind": np.asarray(arr["kind"][rs]), "canopy": np.asarray(arr["canopy"][rs]), "slope": np.asarray(arr["slope"][rs]),
              "shore": np.asarray(arr["shore"][rs]), "road": np.asarray(arr["road"][rs])}
        for i in range(g["cells_x"]):
            cx = g["cx0"] + i
            c = cells.get((cx // 2, cy // 2))
            if not c or c.get("margin") or not c.get("danger_band_id") or (cx, cy) in held:
                continue
            if want is not None and (cx, cy) not in want:
                continue
            yield cx, cy, c, P.Cellview(sl, i, legend, flora[(cx, cy)], origin, north)


def existing(out: Path, kind_of: dict, catalogue_refs: set) -> tuple[Counter, Counter]:
    """What the flora stage placed that yields an ingredient: refs per cell, and per (cell, kind)."""
    per_cell, per_kind = Counter(), Counter()
    for f in sorted((out / "refs/flora").glob("cy*.jsonl")):
        for line in f.read_text().splitlines():
            m = BASE_RE.search(line)
            if not m or m.group(1) not in catalogue_refs:
                continue
            o = json.loads(line)
            cell = tuple(o["cell"])
            per_cell[cell] += 1
            k = kind_of.get(m.group(1))
            if k:
                per_kind[(cell, k)] += 1
    return per_cell, per_kind


def place_at(cv: "P.Cellview", mask: np.ndarray, rng, taken: list) -> tuple | None:
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return None
    for _ in range(8):
        k = int(rng.integers(len(ys)))
        ry, rx = min(ys[k] + rng.random(), 31.99), min(xs[k] + rng.random(), 31.99)
        x, y = cv.world(ry, rx)
        if all((x - a) ** 2 + (y - b) ** 2 >= MIN_GAP ** 2 for a, b in taken):
            taken.append((x, y))
            return x, y, round(cv.ground(ry, rx), 1), ry, rx
    return None


def used_ids(d: Path) -> set:
    given = set()
    for f in sorted([*d.glob("cy*.jsonl"), *(d / "critters").glob("cy*.jsonl")]):
        for ln in f.read_text().splitlines():
            m = re.search(r'"fid": ?"([0-9A-Fa-f]+)"', ln)
            if m:
                given.add(int(m.group(1), 16))
    return given


# ---------------------------------------------------------------- run

def build(out: Path) -> dict:
    data = load_data()
    cat = {b["ref"] for b in data["catalogue"]["bases"]}
    kinds = data["kinds"]
    kind_of = kind_of_base(data)
    new_refs = {r for v in kinds.values() for r in v["records"] if r.startswith("new:")}
    meas = json.loads((SRC / "skyrim_measures.json").read_text())
    rate = {k: v / 100 for k, v in meas["harvestable_density"]["refs_per_100_cells_by_class"].items()}
    lore = region_lore(data)
    man = json.loads((out / "land/manifest.json").read_text())
    ed = out / "ecology"
    d = ed / "harvest"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("cy*.jsonl"):
        old.unlink()
    per_cell, per_kind = existing(out, kind_of, cat)
    given = used_ids(ed)
    # pass 1: each cell's class, what stands in it, and the area of every ground a kind may take
    info = {}
    for cx, cy, c, cv in cells_of(out):
        cl = cv.cls()
        need = {name: int(mask_of(cv, name).sum()) for name in {m for pool in data["pools"].values() for _, m, _ in pool} |
                {m for rows in lore.values() for _, m, _ in rows}}
        info[(cx, cy)] = {"reg": c["region_id"], "cl": cl, "have": per_cell.get((cx, cy), 0), "area": need}
    by_reg = defaultdict(list)
    for xy, v in info.items():
        by_reg[v["reg"]].append(xy)
    plan = {}          # (cell) -> [(kind, mask), ...] to place
    report = {}
    for reg, xys in sorted(by_reg.items()):
        rng = np.random.default_rng((0x4A27, int.from_bytes(hashlib.sha256(reg.encode()).digest()[:4], "big")))
        xys.sort()
        n = len(xys)
        target = sum(rate[info[xy]["cl"]] for xy in xys)
        have = sum(info[xy]["have"] for xy in xys)
        rows = lore.get(reg, [])
        quota = {}
        got_lore = Counter()
        for kind, mask, ing in rows:
            have_k = sum(per_kind.get((xy, kind), 0) for xy in xys)
            area = np.array([info[xy]["area"][mask] for xy in xys], float)
            want = max(0, max(LORE_MIN, math.ceil(LORE_PER_100 * n / 100)) - have_k)
            if area.sum() > 0 and want:
                for i, k in enumerate(rng.multinomial(want, area / area.sum())):
                    if k:
                        plan.setdefault(xys[i], []).extend([(kind, mask)] * int(k))
                quota[kind] = want
            got_lore[kind] = have_k
        placed_lore = sum(quota.values())
        # the filler: the rest of the target over the cells that hold ground for a pool, the short cells first
        pool_of = {}
        for xy in xys:
            cl = info[xy]["cl"]
            pool_of[xy] = [(k, m, w * (LORE_WEIGHT if k in {r[0] for r in rows} else 1.0)) for k, m, w in data["pools"][cl] if info[xy]["area"].get(m, 0) > 0]
        short = np.array([max(rate[info[xy]["cl"]] - info[xy]["have"], 0.0) if pool_of[xy] else 0.0 for xy in xys])
        fill = max(0, int(math.ceil((target - have - placed_lore) * FILL_SLACK)))
        if fill and short.sum() == 0:
            short = np.array([1.0 if pool_of[xy] else 0.0 for xy in xys])
        filled = 0
        if fill and short.sum() > 0:
            for i, k in enumerate(rng.multinomial(fill, short / short.sum())):
                xy = xys[i]
                for _ in range(int(k)):
                    pool = pool_of[xy]
                    w = np.array([p[2] for p in pool], float)
                    kd, mk, _ = pool[int(rng.choice(len(pool), p=w / w.sum()))]
                    plan.setdefault(xy, []).append((kd, mk))
                    filled += 1
        report[reg] = {"cells": n, "target": round(target, 1), "flora_have": have, "lore_quota": quota, "filler": filled,
                       "lore_kinds": [r[0] for r in rows], "lore_have": dict(got_lore)}
    # pass 2: the positions
    tally, region_kind = Counter(), defaultdict(Counter)
    lines_of = defaultdict(list)
    for cx, cy, c, cv in cells_of(out, set(plan)):
        reg = c["region_id"]
        rng = np.random.default_rng((0x4A28, cx & 0xFFFF, cy & 0xFFFF))
        taken, ordinal = [], Counter()
        todo = list(plan[(cx, cy)])
        rng.shuffle(todo)
        for kind, mk in todo[:CELL_CAP]:
            pos = place_at(cv, mask_of(cv, mk), rng, taken)
            if not pos:
                continue
            x, y, z, ry, rx = pos
            recs = kinds[kind]["records"]
            base = recs[int(rng.integers(len(recs)))]
            ident = f"h:{cx},{cy}/{kind}/{ordinal[kind]}"
            ordinal[kind] += 1
            lines_of[cy].append(json.dumps({"base": base, "kind": kind, "mask": mk, "region": reg, "cell": [cx, cy], "cls": info[(cx, cy)]["cl"],
                                            "x": round(x, 1), "y": round(y, 1), "z": z, "rz": round(float(rng.uniform(0, 2 * math.pi)), 3),
                                            "scale": round(float(rng.uniform(0.9, 1.1)), 2), "id": ident, "fid": f"{P.fid_of(ident, given):06X}"}, sort_keys=True))
            tally[reg] += 1
            region_kind[reg][kind] += 1
    for cy, lines in lines_of.items():
        (d / f"cy{cy:+04d}.jsonl").write_text("\n".join(lines) + "\n")
    for reg, r in report.items():
        r["placed"] = tally[reg]
        r["by_kind"] = dict(sorted(region_kind[reg].items()))
        r["per_100_cells"] = round(100 * (r["flora_have"] + tally[reg]) / r["cells"], 1)
        r["target_per_100_cells"] = round(100 * r["target"] / r["cells"], 1)
        r["flora_per_100_cells"] = round(100 * r["flora_have"] / r["cells"], 1)
    new = [dict(n) for n in data["new_records"]]
    (d / "records.json").write_text(json.dumps({"build_id": man["build_id"], "records": new}, indent=1))
    h = hashlib.sha256()
    for f in sorted(d.glob("cy*.jsonl")):
        h.update(f.name.encode() + f.read_bytes())
    res = {"build_id": man["build_id"], "refs": int(sum(tally.values())), "regions": report, "shard_sha256": h.hexdigest(),
           "new_records_used": sorted(new_refs)}
    (d / "manifest.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    log(f"harvest: {res['refs']} references added over {len(report)} regions")
    return res


# ---------------------------------------------------------------- check

def check(out: Path) -> int:
    """Every reference on ground of its habitat, in its cell, its id given once in the ecology range, its base a record
    of the catalogue or one of our new records; every region at Skyrim's class density and with its lore plants.
    Writes check.json; exit 1 on a fault."""
    data = load_data()
    d = out / "ecology/harvest"
    res = json.loads((d / "manifest.json").read_text())
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    g = man["grid"]
    cells = {(c["x"], c["y"]): c for c in P.jsonl("cell")}
    held = P.held_cells(out)
    cat = {b["ref"] for b in data["catalogue"]["bases"]}
    kinds = data["kinds"]
    arr = {k: np.load(LC / f"{k}.npy", mmap_mode="r") for k in ("flags", "kind", "slope", "habitat", "canopy", "shore")}
    hm = np.load(man["heightmap"], mmap_mode="r")
    kn = legend["kinds"]
    habs = legend["habitats"]
    faults = []
    actors = set()
    for f in sorted((out / "ecology").glob("cy*.jsonl")):
        for ln in f.read_text().splitlines():
            if ln:
                actors.add(json.loads(ln)["fid"])
    seen_h, n = set(), 0
    by_kind = Counter()
    for f in sorted(d.glob("cy*.jsonl")):
        for line in f.read_text().splitlines():
            if not line:
                continue
            o = json.loads(line)
            n += 1
            by_kind[(o["region"], o["kind"])] += 1
            fid = int(o["fid"], 16)
            if not P.ECO_FIRST <= fid <= P.ECO_LAST or fid in seen_h or o["fid"] in actors:
                faults.append(f"{o['id']}: id {o['fid']} outside the ecology range or given twice")
            seen_h.add(fid)
            cx, cy = o["cell"]
            if (cx, cy) in held:
                faults.append(f"{o['id']}: in a held or landing cell")
            c = cells.get((cx // 2, cy // 2), {})
            if c.get("region_id") != o["region"] or c.get("margin"):
                faults.append(f"{o['id']}: not in a cell of its region")
            if o["base"] not in kinds[o["kind"]]["records"] or (o["base"] not in cat and not o["base"].startswith("new:")):
                faults.append(f"{o['id']}: base {o['base']} is not a record of kind {o['kind']}")
            sy, sx = int((g["origin_y"] - o["y"]) / P.SAMPLE), int((o["x"] - g["origin_x"]) / P.SAMPLE)
            fl, kd = int(arr["flags"][sy, sx]), (kn[arr["kind"][sy, sx]] if arr["kind"][sy, sx] < len(kn) else "")
            wet = bool(fl & 1)
            mk = o["mask"]
            depth = -float(hm[sy, sx]) / 70.0
            if mk.startswith("bed-"):
                ok = {"bed-fresh": FRESH, "bed-salt": SALT, "bed-brackish": BRACKISH}[mk]
                if not wet or kd not in ok or not BED_MIN - 0.3 <= depth <= BED_MAX + 0.3:
                    faults.append(f"{o['id']}: a {mk} plant on {'land' if not wet else kd} at {depth:.1f} m")
            elif wet and not (mk == "marsh" and kd in FRESH):
                faults.append(f"{o['id']}: a land plant ({mk}) in water")
            elif not wet and (fl & 10 or arr["slope"][sy, sx] >= P.MAX_SLOPE):
                faults.append(f"{o['id']}: on a road, a place pad or a slope")
            elif mk == "canopy" and arr["canopy"][sy, sx] < 120:
                faults.append(f"{o['id']}: a canopy plant in the open")
            elif mk == "bank" and arr["shore"][sy, sx] / 10 >= BANK_M + 3:
                faults.append(f"{o['id']}: a bank plant away from water")
            elif mk == "rock" and habs[arr["habitat"][sy, sx]] not in P.ROCK:
                faults.append(f"{o['id']}: a rock plant off the rock")
    # every region: Skyrim's class density, every lore plant
    per = {}
    for reg, r in res["regions"].items():
        short = []
        total = r["flora_have"] + r["placed"]
        if total + 1 < r["target"]:
            faults.append(f"{reg}: {r['per_100_cells']} per 100 cells, under Skyrim's {r['target_per_100_cells']} for its classes")
        for kind in r["lore_kinds"]:
            got = r["lore_have"].get(kind, 0) + by_kind[(reg, kind)]
            if got < LORE_MIN and kind in r["lore_quota"]:
                short.append(kind)
            if got == 0 and kind not in r["lore_quota"] and r["cells"] > 0:
                short.append(kind + " (no ground)")
        if [s for s in short if "no ground" not in s]:
            faults.append(f"{reg}: lore plants under {LORE_MIN}: {short}")
        per[reg] = {"per_100_cells": r["per_100_cells"], "target_per_100_cells": r["target_per_100_cells"], "flora_per_100_cells": r["flora_per_100_cells"],
                    "lore_kinds": r["lore_kinds"], "no_ground": [s for s in short if "no ground" in s]}
    unbound = sorted(i for i in data["lore"] if "kind" not in data["lore"][i] and "drop" not in data["lore"][i])
    if unbound:
        faults.append(f"lore ingredients bound to nothing: {unbound}")
    for kname, k in kinds.items():
        for r in k["records"]:
            if not r.startswith("new:") and r not in cat:
                faults.append(f"kind {kname}: {r} is not in harvest_bases.json")
            if r.startswith("new:") and r[4:] not in {x["edid"] for x in data["new_records"]}:
                faults.append(f"kind {kname}: {r} has no new record")
    doc = {"build_id": res["build_id"], "refs": n, "faults": faults[:50], "fault_count": len(faults), "regions": per}
    (d / "check.json").write_text(json.dumps(doc, indent=1, sort_keys=True))
    print(f"harvest check: {n} references, {len(faults)} faults")
    for x in faults[:20]:
        print("  " + x)
    return 1 if faults else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.newworld.ecology.harvest")
    ap.add_argument("cmd", choices=("catalogue", "run", "check"))
    ap.add_argument("--out", default=str(P.PLUGIN))
    a = ap.parse_args(argv)
    if a.cmd == "catalogue":
        import importlib
        c = importlib.import_module("tools.newworld.ecology.harvest_catalogue").catalogue()
        (SRC / "harvest_bases.json").write_text(json.dumps(c, indent=0) + "\n")
        print(f"{len(c['bases'])} bases, {len(c['ingredients'])} ingredients")
        return 0
    out = Path(a.out)
    if not out.is_absolute():
        out = REPO / out
    if a.cmd == "run":
        build(out)
        return 0
    return check(out)


if __name__ == "__main__":
    sys.exit(main())
