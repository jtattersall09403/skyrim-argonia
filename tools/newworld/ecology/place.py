"""The ecology stage: the creatures and the roaming hostile people between places, placed by hyperlocal ecology.

    python -m tools.newworld.ecology.place run   [--out out/newworld/plugin]
    python -m tools.newworld.ecology.place check [--out out/newworld/plugin]

Reads the region ecology tables (newworld/sources/ecology/regions/*.json: each kind's size class, hostility,
habitat and group), the binding of each kind to real records (bindings.json, weakest record first), Skyrim's
measures (skyrim_measures.json), each cell's region and danger band (the database's cell table and danger_band),
the landcover rasters (habitat, water kind, canopy, slope, shore, road, flags), the heightmap, the placed flora
(refs/flora: bushes and trees), the held cells of built places (newworld/sources/terrain_held.json) and the map's
teleport landings. Writes `<out>/ecology/`: `cy<+NNN>.jsonl` (one actor a line), `actors.json` (each band actor:
the record it copies, its fixed level and health), `manifest.json` (counts), and on `check` `check.json`.

It writes beside `refs/`, not in it: every producer under `refs/` feeds the navmesh and its key, and an actor is
no obstacle. The world writer (NewWorld.cs) reads `ecology/` as ACHR of our own band copies.

How a cell is filled (decision 0034: Skyrim's own numbers; decision 0035: nothing levelled to the player):
- The cell's class, as Skyrim's measure classed its cells: water (most samples water), shore (some water), mountain
  (rock habitats most), forest (canopy), open. Its creatures per cell are Skyrim's for that class, times the band's
  density (BAND_DENSITY); groups are drawn by Poisson with Skyrim's mean group, sizes from the row's range, larger
  in high bands.
- A group is hostile with the band's share (HOSTILE_SHARE: Skyrim's 0.38 at D2); D0 has none. The kind is drawn
  from the region's rows of that temper whose habitat holds ground in the cell, weighted by the region's
  signature and by the band's weight for the size class (giants from D3).
- Habitat: walkers on dry ground under 35 degrees, never on a road surface or a place pad; marsh kinds on marsh
  habitats; bush kinds within BUSH_M of a placed understorey, fern or reed; canopy kinds under canopy; rock kinds
  on rock habitats; shore kinds on shore habitats or within SHORE_M of water; swimmers in water of their kind
  (fresh, brackish, salt) at least SWIM_DEPTH deep, set mid-depth; insects over water at its surface.
- Hostiles keep HOSTILE_ROAD_M off roads; nothing in a held cell, a teleport landing's cell or the margin.
- The record is chosen by band from the kind's records (weakest first); its band copy has the band's fixed level
  (danger_band.foe_level times the size class's share) and health (BAND_HEALTH).
- Hostile people: the region's lore-backed groups (npc_encounters.json, bound in bindings.json), a roaming group in
  open dry ground with NPC_CHANCE by band, NPC_SIZE members, the band's foe level.
Every draw is seeded by the cell, so a rerun writes the same bytes. A ref's id is ECO_FIRST + its identity's digest
(cell, kind, ordinal) in the ecology range, probed on a collision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
LC = REPO / "out/newworld/landcover"
DB = REPO / "newworld/story/data/db"
SRC = REPO / "newworld/sources/ecology"
HELD = REPO / "newworld/sources/terrain_held.json"
PLUGIN = REPO / "out/newworld/plugin"

ECO_FIRST, ECO_LAST = 0xF00000, 0xFDFFFF   # tools/newworld/idspace.py row `ecology`
SAMPLE = 128.0
BANDS = ("D0", "D1", "D2", "D3", "D4", "D5")
BAND_DENSITY = {"D0": 0.5, "D1": 0.8, "D2": 1.0, "D3": 1.25, "D4": 1.6, "D5": 2.0}
HOSTILE_SHARE = {"D0": 0.0, "D1": 0.15, "D2": 0.38, "D3": 0.5, "D4": 0.65, "D5": 0.8}
BAND_HEALTH = {"D0": 0.6, "D1": 0.8, "D2": 1.0, "D3": 1.4, "D4": 2.0, "D5": 2.8}
SIZE_LEVEL = {"insect": 0.4, "small": 0.6, "game": 0.8, "predator": 1.0, "giant": 1.25, "npc": 1.0}
SIZE_WEIGHT = {  # band -> size class -> weight of a row of that size
    "D0": {"insect": 3, "small": 3, "game": 1, "predator": 0, "giant": 0},
    "D1": {"insect": 3, "small": 3, "game": 2, "predator": 0.5, "giant": 0},
    "D2": {"insect": 2, "small": 2, "game": 2, "predator": 1.5, "giant": 0},
    "D3": {"insect": 1.5, "small": 1.5, "game": 2, "predator": 2, "giant": 0.4},
    "D4": {"insect": 1, "small": 1, "game": 1.5, "predator": 2.5, "giant": 1},
    "D5": {"insect": 1, "small": 1, "game": 1, "predator": 3, "giant": 2}}
CAP = {"D0": 4, "D1": 6, "D2": 8, "D3": 10, "D4": 14, "D5": 18}   # actors in one cell
NPC_CHANCE = {"D0": 0.0, "D1": 0.0, "D2": 0.01, "D3": 0.02, "D4": 0.03, "D5": 0.04}   # a land cell's chance
GEAR_TIER = {"D2": "low", "D3": "mid", "D4": "high", "D5": "high"}   # the band's gear tier of a people's own kit
MIN_LOOKS, MIN_GEAR = 4, 2
NPC_SIZE = {"D2": (2, 3), "D3": (2, 4), "D4": (3, 5), "D5": (4, 6)}
SWIM_DEPTH, BUSH_M, SHORE_M, HOSTILE_ROAD_M, MAX_SLOPE = 1.5, 4.0, 15.0, 30.0, 35.0
SCATTER = 300.0          # a group's members within this of its first, units
FRESH = ("pond", "lake", "river", "stream", "green-marsh", "blackwater-swamp")
SALT = ("ocean", "bay", "shallow-coast")
BRACKISH = ("estuary", "bay", "shallow-coast")
MARSH = ("reed_marsh", "cypress_swamp", "swamp_hummock", "drowned_forest", "mangrove_fringe")
ROCK = ("rocky_outcrop", "cliff_face", "upland_scrub")
SHORE = ("beach_shore", "mangrove_fringe")
OPEN = ("coastal_grassland", "upland_scrub", "dry_hammock", "beach_shore")
BUSHY = ("understorey", "fern", "reed")
TREES = ("canopy_tree", "palm")
TOLERANCE = (0.5, 1.6)   # actors placed / Skyrim's measure for the same cells (band density applied)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def load_sources() -> tuple[dict, dict, dict, dict]:
    """(region -> rows bound to records, bindings, measures, npc encounters)."""
    bind = json.loads((SRC / "bindings.json").read_text())
    rows = {}
    for f in sorted((SRC / "regions").glob("*.json")):
        d = json.loads(f.read_text())
        rows[d["region"]] = [dict(r) for r in d["creatures"] if bind["kinds"].get(r["kind"], {}).get("records")]
    return rows, bind, json.loads((SRC / "skyrim_measures.json").read_text()), json.loads((SRC / "npc_encounters.json").read_text())


def jsonl(name: str) -> list[dict]:
    return [json.loads(l) for l in (DB / f"{name}.jsonl").read_text().splitlines() if l.strip()]


def held_cells(out: Path) -> set:
    held = {tuple(c) for p in json.loads(HELD.read_text())["places"].values() for c in p["cells"]}
    tp = out / "map/teleports.json"
    if tp.exists():
        held |= {tuple(c["cell"]) for c in json.loads(tp.read_text()).get("cells", [])}
    return held


def flora_near(out: Path) -> dict:
    """(cx, cy) -> {"bush": [(x, y)], "tree": [(x, y)]} from the placed flora."""
    res: dict = defaultdict(lambda: {"bush": [], "tree": []})
    for f in sorted((out / "refs/flora").glob("cy*.jsonl")):
        for line in f.read_text().splitlines():
            if not line:
                continue
            o = json.loads(line)
            k = "bush" if o.get("cls") in BUSHY else "tree" if o.get("cls") in TREES else None
            if k:
                res[(math.floor(o["x"] / 4096), math.floor(o["y"] / 4096))][k].append((o["x"], o["y"]))
    return res


def band_level(band: str, size: str, foe: dict) -> int:
    return max(1, int(round(foe[band] * SIZE_LEVEL[size])))


def pick_record(recs: list, band: str, rng) -> str:
    """Weakest records in low bands, strongest in high: a window round the band's share of the list."""
    n = len(recs)
    c = BANDS.index(band) / 5 * (n - 1)
    i = int(np.clip(round(c + rng.uniform(-1, 1)), 0, n - 1))
    return recs[i]


def fid_of(identity: str, given: set) -> int:
    span = ECO_LAST - ECO_FIRST + 1
    i = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "big") % span
    while ECO_FIRST + i in given:
        i = (i + 1) % span
    given.add(ECO_FIRST + i)
    return ECO_FIRST + i


class Cellview:
    """One cell's samples (33 x 33, north row first) and its masks by row habitat."""

    def __init__(self, sl: dict, i: int, legend: dict, flora: dict, origin: tuple, north: int):
        sc = slice(i * 32, i * 32 + 33)
        self.h = sl["hm"][:, sc]
        self.water = (sl["flags"][:, sc] & 1) == 1
        self.flags = sl["flags"][:, sc]
        habs, kinds = legend["habitats"], legend["kinds"]
        self.hab = np.array(habs, dtype=object)[sl["hab"][:, sc]]
        self.kind = np.array(kinds + [""] * (256 - len(kinds)), dtype=object)[sl["kind"][:, sc]]
        self.canopy = sl["canopy"][:, sc]
        self.slope = sl["slope"][:, sc]
        self.shore = sl["shore"][:, sc].astype(np.float32) / 10
        self.road = sl["road"][:, sc].astype(np.float32) / 10
        self.depth = np.where(self.water, -self.h / 70.0, 0.0)
        self.ox, self.oy, self.i, self.north = origin[0], origin[1], i, north
        dry = ~self.water & ((self.flags & (2 | 8)) == 0) & (self.slope < MAX_SLOPE)
        self.dry = dry
        self.masks = {
            "any": dry,
            "marsh": dry & np.isin(self.hab, MARSH) | (self.water & (self.depth < 0.6) & np.isin(self.kind, FRESH)),
            "rock": dry & np.isin(self.hab, ROCK),
            "shore": dry & (np.isin(self.hab, SHORE) | (self.shore < SHORE_M)),
            "open": dry & (np.isin(self.hab, OPEN) | (self.canopy < 40)),
            "canopy": dry & (self.canopy >= 120),
            "bush": dry & self._near(flora["bush"], BUSH_M),
            "water-fresh": self.water & np.isin(self.kind, FRESH) & (self.depth >= SWIM_DEPTH),
            "water-salt": self.water & np.isin(self.kind, SALT) & (self.depth >= SWIM_DEPTH),
            "water-brackish": self.water & np.isin(self.kind, BRACKISH) & (self.depth >= SWIM_DEPTH),
        }
        self.surface = {k: self.water & np.isin(self.kind, v) for k, v in
                        (("water-fresh", FRESH), ("water-salt", SALT), ("water-brackish", BRACKISH))}

    def _near(self, pts: list, metres: float) -> np.ndarray:
        m = np.zeros(self.h.shape, bool)
        r = metres * 70 / SAMPLE
        for x, y in pts:
            sx = (x - self.ox) / SAMPLE - self.i * 32
            sy = (self.oy - y) / SAMPLE - self.north
            j0, j1 = max(0, int(sy - r)), min(32, int(sy + r) + 1)
            i0, i1 = max(0, int(sx - r)), min(32, int(sx + r) + 1)
            m[j0:j1 + 1, i0:i1 + 1] = True
        return m

    def cls(self) -> str:
        """The cell's class as Skyrim's measure classed its cells."""
        w = self.water.mean()
        if w > 0.5:
            return "water"
        if w > 0:
            return "shore"
        if np.isin(self.hab, ROCK).mean() > 0.5:
            return "mountain"
        if (self.canopy >= 120).mean() > 0.3:
            return "forest"
        return "open"

    def mask(self, row: dict) -> np.ndarray:
        m = self.masks.get(row["habitat"], self.masks["any"])
        if row["size_class"] == "insect" and row["habitat"].startswith("water"):
            m = self.surface[row["habitat"]]
        return m[:32, :32]

    def world(self, ry: float, rx: float) -> tuple[float, float]:
        return self.ox + (self.i * 32 + rx) * SAMPLE, self.oy - (self.north + ry) * SAMPLE

    def ground(self, ry: float, rx: float) -> float:
        h = self.h
        j, i = min(int(ry), h.shape[0] - 2), min(int(rx), h.shape[1] - 2)
        ay, ax = ry - j, rx - i
        return float((h[j, i] * (1 - ax) + h[j, i + 1] * ax) * (1 - ay) + (h[j + 1, i] * (1 - ax) + h[j + 1, i + 1] * ax) * ay)


def z_for(cv: Cellview, row: dict, ry: float, rx: float) -> float:
    g = cv.ground(ry, rx)
    if row["habitat"].startswith("water"):
        return 60.0 if row["size_class"] == "insect" else round(g / 2, 1)   # over the surface, or mid-depth
    return round(max(g, 0.0) + 16, 1)


def build(out: Path) -> dict:
    man = json.loads((out / "land/manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    if legend["build_id"] != man["build_id"]:
        raise RuntimeError("landcover is another terrain build: rerun landcover")
    g = man["grid"]
    rows, bind, meas, enc = load_sources()
    per100 = meas["creature_density"]["refs_per_100_cells_by_class"]
    foe = {r["id"]: r["foe_level"] for r in jsonl("danger_band")}
    cells = {(c["x"], c["y"]): c for c in jsonl("cell")}
    held = held_cells(out)
    flora = flora_near(out)
    groups = {}
    for reg, e in enc["regions"].items():
        groups[reg] = [b for gr in e.get("groups", []) if gr.get("support") != "none"
                       for b in [bind.get("npc_groups", {}).get(f"{reg}|{gr['group']}")] if b and b.get("records")]
    arr = {k: np.load(LC / f"{k}.npy", mmap_mode="r") for k in ("habitat", "kind", "flags", "canopy", "slope", "shore", "road")}
    hm = np.load(man["heightmap"], mmap_mode="r")
    origin = tuple(legend["origin_world"])
    d = out / "ecology"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("cy*.jsonl"):
        old.unlink()
    given: set = set()
    actors: dict = {}
    tally = Counter()
    expect = Counter()
    for cy in range(g["cy_top"], g["cy_bottom"] - 1, -1):
        north = (g["cy_top"] - cy) * 32
        rs = slice(north, north + 33)
        sl = {"hm": np.asarray(hm[rs]), "flags": np.asarray(arr["flags"][rs]), "hab": np.asarray(arr["habitat"][rs]),
              "kind": np.asarray(arr["kind"][rs]), "canopy": np.asarray(arr["canopy"][rs]), "slope": np.asarray(arr["slope"][rs]),
              "shore": np.asarray(arr["shore"][rs]), "road": np.asarray(arr["road"][rs])}
        lines = []
        for i in range(g["cells_x"]):
            cx = g["cx0"] + i
            c = cells.get((cx // 2, cy // 2))   # the database cell is a map (Morrowind) cell, two Skyrim cells a side
            if not c or c.get("margin") or not c.get("danger_band_id") or (cx, cy) in held:
                continue
            band, reg = c["danger_band_id"], c["region_id"]
            rng = np.random.default_rng((0xEC0, cx & 0xFFFF, cy & 0xFFFF))
            cv = Cellview(sl, i, legend, flora[(cx, cy)], origin, north)
            cl = cv.cls()
            rate = per100[cl] / 100 * BAND_DENSITY[band]
            expect[(reg, band, cl)] += rate
            placed = []
            target = int(rng.poisson(rate))     # Skyrim's creatures for the class; groups are drawn until it is met
            for _ in range(4 * target):
                if len(placed) >= target:
                    break
                hostile = rng.random() < HOSTILE_SHARE[band]
                cand, wts = [], []
                for r in rows.get(reg, []):
                    if (r["hostility"] == "hostile") != hostile:
                        continue
                    w = SIZE_WEIGHT[band][r["size_class"]] * (2 if r.get("signature") else 1)
                    if w > 0 and cv.mask(r).any():
                        cand.append(r)
                        wts.append(w)
                if not cand:
                    continue
                r = cand[int(rng.choice(len(cand), p=np.array(wts) / sum(wts)))]
                lo, hi = r["group"]
                n = min(int(lo + round((hi - lo) * rng.beta(1 + BANDS.index(band) / 2, 2))), target - len(placed))
                placed += spot(cv, r, n, band, hostile, rng, cx, cy, kind=r["kind"], size=r["size_class"],
                               rec=pick_record(bind["kinds"][r["kind"]]["records"], band, rng))
            if groups.get(reg) and band in NPC_SIZE and rng.random() < NPC_CHANCE[band]:
                gb = groups[reg][int(rng.integers(len(groups[reg])))]
                lo, hi = NPC_SIZE[band]
                row = {"habitat": "open", "size_class": "npc"}
                kind = "npc:" + re.sub(r"[^a-z]+", "-", gb.get("race", "people").lower()).strip("-")
                looks = gb.get("looks") or gb["records"]
                tier = gb.get("gear", {}).get(GEAR_TIER[band]) or []
                for _ in range(int(rng.integers(lo, hi + 1))):
                    look = looks[int(rng.integers(len(looks)))]          # a flat draw: any face of the people
                    g = int(rng.integers(len(tier))) if tier else -1      # a flat draw from the band's gear tier
                    placed += spot(cv, row, 1, band, True, rng, cx, cy, kind=kind, size="npc",
                                   rec=look + (f"~{GEAR_TIER[band]}{g}" if g >= 0 else ""), people=True,
                                   gear=tier[g] if g >= 0 else None)
            ordinal = Counter()
            for p in placed[:CAP[band]]:
                ident = f"{cx},{cy}/{p['kind']}/{ordinal[p['kind']]}"
                ordinal[p["kind"]] += 1
                name = f"{p.pop('rec')}@{band}"
                lvl = band_level(band, p["size"], foe)
                gear = p.pop("gear", None)
                actors[name] = {"name": name, "src": name.rsplit("@", 1)[0].split("~")[0], "band": band, "level": lvl,
                                "health_mult": BAND_HEALTH[band], "kind": p["kind"]}
                if gear:
                    actors[name]["gear"] = gear
                p.update(actor=name, region=reg, band=band, cell=[cx, cy], cls=cl, id=ident, fid=f"{fid_of(ident, given):06X}")
                lines.append(json.dumps(p, sort_keys=True))
                tally[(reg, band, p["kind"], p["hostile"], cl)] += 1
        (d / f"cy{cy:+04d}.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""))
    (d / "actors.json").write_text(json.dumps({"build_id": man["build_id"], "actors": sorted(actors.values(), key=lambda a: a["name"])}, indent=1))
    res = summary(tally, expect, man["build_id"])
    h = hashlib.sha256()
    for f in sorted(d.glob("cy*.jsonl")):
        h.update(f.name.encode() + f.read_bytes())
    res["shard_sha256"] = h.hexdigest()
    (d / "manifest.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    log(f"ecology: {res['refs']} actors, {len(actors)} band actors; by band {res['by_band']}")
    return res


def spot(cv: Cellview, row: dict, n: int, band: str, hostile: bool, rng, cx: int, cy: int, *, kind: str, size: str,
         rec: str, people: bool = False, gear: dict | None = None) -> list[dict]:
    """n members of one group on the row's ground in the cell, the first at a random sample of its mask."""
    m = cv.mask(row).copy()
    if hostile:
        m &= cv.road[:32, :32] >= HOSTILE_ROAD_M
    ys, xs = np.nonzero(m)
    if not len(ys):
        return []
    k = int(rng.integers(len(ys)))
    y0, x0 = ys[k] + rng.random(), xs[k] + rng.random()
    out = []
    for j in range(max(1, n)):
        for _ in range(6):
            ry = float(np.clip(y0 + (rng.uniform(-1, 1) * SCATTER / SAMPLE if j else 0), 0, 31.99))
            rx = float(np.clip(x0 + (rng.uniform(-1, 1) * SCATTER / SAMPLE if j else 0), 0, 31.99))
            if m[int(ry), int(rx)]:
                x, y = cv.world(ry, rx)
                out.append({"rec": rec, "gear": gear, "kind": kind, "size": size, "hostile": hostile, "people": people,
                            "hab": row["habitat"], "x": round(x, 1), "y": round(y, 1), "z": z_for(cv, row, ry, rx),
                            "rz": round(float(rng.uniform(0, 2 * math.pi)), 3)})
                break
    return out


def summary(tally: Counter, expect: Counter, build_id: str) -> dict:
    by_band, by_region, by_kind, by_cls, hostile = Counter(), Counter(), Counter(), Counter(), Counter()
    kinds = defaultdict(set)
    for (reg, band, kind, h, cl), n in tally.items():
        by_band[band] += n
        by_region[reg] += n
        by_kind[kind] += n
        by_cls[cl] += 0 if kind.startswith("npc:") else n
        hostile[band] += n if h else 0
        kinds[reg].add(kind)
    exp_cls = Counter()
    for (reg, band, cl), e in expect.items():
        exp_cls[cl] += e
    return {"build_id": build_id, "refs": int(sum(tally.values())), "by_band": dict(sorted(by_band.items())),
            "hostile_by_band": dict(sorted(hostile.items())), "by_region": dict(sorted(by_region.items())),
            "by_kind": dict(sorted(by_kind.items())), "by_class": dict(sorted(by_cls.items())),
            "expected_by_class": {k: round(v, 1) for k, v in sorted(exp_cls.items())},
            "kinds_by_region": {k: sorted(v) for k, v in sorted(kinds.items())}}


def check(out: Path) -> int:
    """Every actor on valid ground or water for its kind, in its cell's band caps, outside held cells, its id in the
    ecology range and given once; the band actors' levels as their band's; regions told apart; density against
    Skyrim's measure. Writes check.json; exit 1 on a fault."""
    d = out / "ecology"
    man = json.loads((out / "land/manifest.json").read_text())
    res = json.loads((d / "manifest.json").read_text())
    legend = json.loads((LC / "legend.json").read_text())
    g = man["grid"]
    foe = {r["id"]: r["foe_level"] for r in jsonl("danger_band")}
    cells = {(c["x"], c["y"]): c for c in jsonl("cell")}
    held = held_cells(out)
    acts = {a["name"]: a for a in json.loads((d / "actors.json").read_text())["actors"]}
    arr = {k: np.load(LC / f"{k}.npy", mmap_mode="r") for k in ("flags", "kind", "slope")}
    kinds = legend["kinds"]
    faults, seen, per_cell = [], set(), Counter()
    n = 0
    for f in sorted(d.glob("cy*.jsonl")):
        for line in f.read_text().splitlines():
            if not line:
                continue
            o = json.loads(line)
            n += 1
            cx, cy = o["cell"]
            per_cell[(cx, cy)] += 1
            fid = int(o["fid"], 16)
            if not ECO_FIRST <= fid <= ECO_LAST or fid in seen:
                faults.append(f"{o['id']}: id {o['fid']} outside the ecology range or given twice")
            seen.add(fid)
            if (cx, cy) in held:
                faults.append(f"{o['id']}: in a held or landing cell")
            c = cells.get((cx // 2, cy // 2), {})
            if c.get("danger_band_id") != o["band"]:
                faults.append(f"{o['id']}: band {o['band']} is not its cell's {c.get('danger_band_id')}")
            if o["hostile"] and o["band"] == "D0":
                faults.append(f"{o['id']}: hostile in D0")
            a = acts.get(o["actor"])
            if not a or a["level"] != band_level(o["band"], o["size"], foe):
                faults.append(f"{o['id']}: its actor's level is not its band's")
            sy, sx = int((g["origin_y"] - o["y"]) / SAMPLE), int((o["x"] - g["origin_x"]) / SAMPLE)
            wet = bool(arr["flags"][sy, sx] & 1)
            fl = int(arr["flags"][sy, sx])
            if o["hab"].startswith("water"):
                k = kinds[arr["kind"][sy, sx]] if arr["kind"][sy, sx] < len(kinds) else ""
                ok = {"water-fresh": FRESH, "water-salt": SALT, "water-brackish": BRACKISH}[o["hab"]]
                if not wet or k not in ok:
                    faults.append(f"{o['id']}: a swimmer of {o['hab']} on {'land' if not wet else k}")
            elif o["hab"] != "marsh" and (wet or fl & 10 or arr["slope"][sy, sx] >= MAX_SLOPE):
                faults.append(f"{o['id']}: a walker on water, a road, a place pad or a slope")
    for (cx, cy), k in per_cell.items():
        b = cells.get((cx // 2, cy // 2), {}).get("danger_band_id")
        if b and k > CAP[b]:
            faults.append(f"cell {cx},{cy}: {k} actors over the cap {CAP[b]} of {b}")
    kr = {r: set(k for k in v if not k.startswith("npc:")) for r, v in res["kinds_by_region"].items()}
    jac = {f"{a}~{b}": round(len(kr[a] & kr[b]) / len(kr[a] | kr[b]), 2) for a in kr for b in kr if a < b and kr[a] | kr[b]}
    worst = max(jac.values(), default=0.0)
    if worst > 0.5:
        faults.append(f"regions too alike: {max(jac, key=jac.get)} share {worst} of their kinds")
    bind = json.loads((SRC / "bindings.json").read_text())
    variety = {}
    for gk, gb in bind.get("npc_groups", {}).items():
        if not gb.get("records"):
            continue
        looks = gb.get("looks") or gb["records"]
        tiers = gb.get("gear", {})
        mean = {t: (sum(e["value"] for e in tiers[t]) / len(tiers[t]) if tiers.get(t) else None) for t in ("low", "mid", "high")}
        variety[gk] = {"looks": len(set(looks)), "gear": {t: len(tiers.get(t, [])) for t in ("low", "mid", "high")}, "mean_value": mean}
        if len(set(looks)) < MIN_LOOKS:
            faults.append(f"{gk}: {len(set(looks))} looks, fewer than {MIN_LOOKS}")
        if not gb.get("gear_note"):
            if any(len(tiers.get(t, [])) < MIN_GEAR for t in ("low", "mid", "high")):
                faults.append(f"{gk}: a gear tier with fewer than {MIN_GEAR} sets")
            elif not mean["low"] < mean["mid"] < mean["high"]:
                faults.append(f"{gk}: mean gear value does not rise with the band {mean}")
    worn = defaultdict(list)
    for a in acts.values():
        if a.get("gear"):
            worn[a["band"]].append(a["gear"]["value"])
    worn_mean = {b: round(sum(v) / len(v)) for b, v in sorted(worn.items())}
    density = {}
    for cl, e in res["expected_by_class"].items():
        got = res["by_class"].get(cl, 0)
        density[cl] = {"expected": e, "placed": got, "ratio": round(got / e, 2) if e else None}
        if e >= 20 and not TOLERANCE[0] <= got / e <= TOLERANCE[1]:
            faults.append(f"density of {cl}: {got} placed against {e} by Skyrim's measure, outside {TOLERANCE}")
    out_doc = {"build_id": res["build_id"], "refs": n, "faults": faults[:50], "fault_count": len(faults),
               "max_region_overlap": worst, "density": density, "people_variety": variety, "gear_value_by_band": worn_mean, "by_band": res["by_band"]}
    (d / "check.json").write_text(json.dumps(out_doc, indent=1, sort_keys=True))
    print(f"ecology check: {n} actors, {len(faults)} faults; worst region overlap {worst}; density {density}")
    for x in faults[:20]:
        print("  " + x)
    return 1 if faults else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="tools.newworld.ecology.place")
    ap.add_argument("cmd", choices=("run", "check"))
    ap.add_argument("--out", default=str(PLUGIN))
    a = ap.parse_args(argv)
    out = Path(a.out)
    if not out.is_absolute():
        out = REPO / out
    if a.cmd == "run":
        build(out)
        return 0
    return check(out)


if __name__ == "__main__":
    sys.exit(main())
