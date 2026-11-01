"""Where and when creature refs sit: the placement habits of Skyrim.esm's and the Black Marsh mods' creature ACHRs
(1.15 §g.1-2, decision 0034). Prints JSON; the numbers are in the creatures lane report.

    python3 -m tools.argonia_world.vanilla.creature_habits [--json out/creatures/habits.json]

A creature is an NPC_ whose race editor-ID has none of creatures.HUMANOID's words; a levelled base (LVLN, or an NPC_
templated to one) counts through every NPC_ the list can spawn (actors-style resolve). Each plugin and the masters
it leans on are read once into ~/.cache/argonia-vanilla/habits-*.pkl (game-derived, never committed, 0003).

A. Skyrim.esm, Tamriel (vanilla.load's cell data: Skyrim.esm with Update.esm's overrides):
    road      Skyrim has no ROAD record; its roads are painted. A LAND vertex is road when a road LTEX covers it at
              opacity 0.5 or more (the quadrant's base texture counts as opacity 1) and no other ATXT layer is
              stronger. Road LTEX = every LTEX whose editor-ID has "path", "cobble" or "road" (found: LDirtPath01,
              LDirtSnowPath01, LSnowCobble01).
    distance  from the ref to the nearest road vertex in the ref's 3x3 cells (units; none in range = 8,192, the
              reach, counted apart); percentiles over all refs, share within 512 units (~7.3 m)
    schedule  per resolved NPC_ from its PKID packages (its template NPC_'s when it has none): a package is sleep
              when its editor-ID or its template package's has "sleep"; scheduled when PSDT has an hour (hour >= 0;
              the interval is hour .. hour + duration minutes; a sleep package without PSDT is 22:00-06:00). Day is
              06:00-20:00, night the rest. day-only: every non-sleep package is scheduled and inside the day;
              night-only: the same inside the night; mixed: scheduled across both; all-day: any non-sleep package
              runs unscheduled, or the NPC_ has no package. A creature ref takes the commonest class of its NPC_s.
B. Each Black Marsh mod plugin, creature ACHRs in exterior cells of the mod's own worldspaces:
    slope     degrees at the ref, from the 128-unit LAND quad that holds it: the mean of its two edge differences
              along x and along y, then atan of the gradient's length (VHGT)
    tree      distance (units) to the nearest TREE or FLOR ref, or STAT ref whose editor-ID has tree, bush, shrub,
              plant, fern, flora, mangrove, reed, cattail or palm, in the ref's world within 2 cells (none = 8,192)
    schedule  as in A
"""
from __future__ import annotations

import argparse
import json
import pickle
import struct
import time
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from tools.argonia_world.skyrim_units import CELL_UNITS, UNITS_PER_METRE, VERTEX_SPACING_UNITS
from tools.argonia_world.vanilla import load
from tools.argonia_world.vanilla.creatures import HUMANOID

CACHE = Path.home() / ".cache" / "argonia-vanilla"
MODS = Path.home() / ".argonia" / "stack" / "MO2" / "mods"
MOD_PLUGINS = ("King of the Murkmire.esp", "Black Marsh.esm", "Here There Be Monsters - Curse of Cipactli.esp")
KEEP = {b"NPC_", b"RACE", b"PACK", b"LVLN", b"STAT", b"TREE", b"FLOR", b"CELL", b"WRLD"}
NOT_CREATURE = HUMANOID + ("Default", "Naga", "Human", "Elf")
PLANT = ("tree", "bush", "shrub", "plant", "fern", "flora", "mangrove", "reed", "cattail", "palm")
REACH = 2 * CELL_UNITS
ROAD_ALPHA = 0.5
DAY = (6 * 60, 20 * 60)


def _z(b: bytes) -> str:
    return b.split(b"\0", 1)[0].decode("latin1")


def parse(path: Path, with_land: bool) -> dict:
    """One walk of a plugin: actor and package records, base-form names, and exterior ACHR/REFR/LAND."""
    blob = path.read_bytes()
    hlen = struct.unpack_from("<I", blob, 4)[0]
    light = bool(struct.unpack_from("<I", blob, 8)[0] & 0x200)
    masters = [_z(b) for s, b in load.subs(blob[24:24 + hlen]) if s == b"MAST"]
    own = path.name.lower()
    names = [m.lower() for m in masters]

    def key(f):
        if light and f >> 24 == 0xFE:
            return (own, f & 0xFFF)
        i = f >> 24
        return (names[i] if i < len(names) else own, f & 0xFFFFFF)

    o = {"name": path.name, "npc": {}, "race": {}, "pack": {}, "lvln": {}, "base": {}, "worlds": {}, "achr": [],
         "refr": [], "land": {}, "key_own": own, "masters": masters}
    cur = {"cell": None}

    def body(i, size, flags):
        b = blob[i + 24:i + 24 + size]
        return zlib.decompress(b[4:]) if flags & 0x40000 else b

    def u32(b):
        return struct.unpack_from("<I", b)[0]

    def walk(i, end, wrld):
        while i < end:
            sig = blob[i:i + 4]
            size = struct.unpack_from("<I", blob, i + 4)[0]
            if sig == b"GRUP":
                label, gtype = struct.unpack_from("<Ii", blob, i + 8)
                if gtype == 0 and blob[i + 8:i + 12] not in KEEP:
                    i += size
                    continue
                walk(i + 24, i + size, key(label) if gtype == 1 else wrld)
                i += size
                continue
            flags, fid = struct.unpack_from("<II", blob, i + 8)
            if sig in KEEP:
                sb = load.subs(body(i, size, flags))
                d = dict(sb)
                edid = _z(d.get(b"EDID", b""))
                k = key(fid)
                if sig == b"NPC_":
                    o["npc"][k] = (edid, key(u32(d[b"RNAM"])) if b"RNAM" in d else None,
                                   key(u32(d[b"TPLT"])) if b"TPLT" in d else None,
                                   [key(u32(b)) for s, b in sb if s == b"PKID"])
                elif sig == b"RACE":
                    o["race"][k] = edid
                elif sig == b"PACK":
                    sch = [struct.unpack_from("<bbbbb3xi", b) for s, b in sb if s == b"PSDT" and len(b) >= 12]
                    pk = d.get(b"PKCU")
                    o["pack"][k] = (edid, [(s[3], s[4], s[5]) for s in sch],
                                    key(u32(pk)) if pk and len(pk) >= 4 else None)
                elif sig == b"LVLN":
                    o["lvln"][k] = [key(struct.unpack_from("<HHIH", b)[2]) for s, b in sb
                                    if s == b"LVLO" and len(b) >= 10]
                elif sig in (b"STAT", b"TREE", b"FLOR"):
                    o["base"][k] = (sig.decode(), edid)
                elif sig == b"WRLD":
                    o["worlds"][k] = edid
                elif sig == b"CELL":
                    cur["cell"] = struct.unpack_from("<ii", d[b"XCLC"]) if b"XCLC" in d else None
            elif wrld is not None and with_land and sig in (b"ACHR", b"REFR", b"LAND"):
                d = dict(load.subs(body(i, size, flags)))
                if sig == b"LAND":
                    if cur["cell"] is not None and b"VHGT" in d:
                        o["land"][(wrld, *cur["cell"])] = load.heights(d[b"VHGT"])
                elif b"NAME" in d and b"DATA" in d:
                    p = struct.unpack("<3f", d[b"DATA"][:12])
                    o["achr" if sig == b"ACHR" else "refr"].append((wrld, p[0], p[1], p[2], key(u32(d[b"NAME"]))))
            elif wrld is not None and sig == b"ACHR":  # a master's creature refs: Skyrim.esm only needs these
                d = dict(load.subs(body(i, size, flags)))
                if b"NAME" in d and b"DATA" in d:
                    p = struct.unpack("<3f", d[b"DATA"][:12])
                    o["achr"].append((wrld, p[0], p[1], p[2], key(u32(d[b"NAME"]))))
            i += 24 + size

    walk(24 + hlen, len(blob), None)
    return o


def read(name: str, with_land: bool) -> dict:
    f = CACHE / f"habits-{name}-{int(with_land)}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    p = load.data_dir() / name
    if not p.exists():
        p = next(MODS.glob(f"*/{name}"))
    o = parse(p, with_land)
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_bytes(pickle.dumps(o, protocol=5))
    return o


class World:
    """A plugin and the masters it leans on, merged by (plugin, local id)."""

    def __init__(self, main: str, with_land: bool):
        self.parts: dict[str, dict] = {}
        self.add(main, with_land)
        self.npc, self.race, self.pack, self.lvln, self.base = {}, {}, {}, {}, {}
        for p in self.parts.values():
            for a in ("npc", "race", "pack", "lvln", "base"):
                getattr(self, a).update(p[a])

    def add(self, name, with_land):
        if name in self.parts:
            return
        try:
            o = read(name, with_land)
        except StopIteration:
            return
        self.parts[name] = o
        for m in o["masters"]:
            self.add(m, False)


def is_creature(w: World, k) -> bool:
    n = w.npc.get(k)
    r = w.race.get(n[1], "") if n and n[1] else ""
    return bool(r) and not any(h.lower() in r.lower() for h in NOT_CREATURE)


def resolve(w: World, k, depth=0) -> list:
    if depth > 6:
        return []
    if k in w.lvln:
        return [n for e in w.lvln[k] for n in resolve(w, e, depth + 1)]
    n = w.npc.get(k)
    if n is None:
        return []
    if n[2] is not None and n[2] in w.lvln:
        return resolve(w, n[2], depth + 1)
    return [k]


def _sleep(w: World, k) -> bool:
    e, _, t = w.pack.get(k, ("", [], None))
    return "sleep" in e.lower() or (t is not None and "sleep" in w.pack.get(t, ("",))[0].lower())


def _intervals(w: World, k) -> list[tuple[int, int]]:
    """(start, end) minutes from midnight; end may pass 1440."""
    sch = w.pack.get(k, ("", [], None))[1]
    out = [(h * 60 + m, h * 60 + m + max(du, 1)) for h, m, du in sch if h >= 0]
    return out or ([(22 * 60, 30 * 60)] if _sleep(w, k) else [])


def _span_class(span: tuple[int, int]) -> str:
    s, e = span
    mins = [x % 1440 for x in range(s, min(e, s + 1440), 15)] or [s % 1440]
    inday = sum(DAY[0] <= x < DAY[1] for x in mins) / len(mins)
    return "day" if inday >= 0.999 else "night" if inday <= 0.001 else "mixed"


def schedule_class(w: World, k) -> dict:
    n = w.npc[k]
    pk = n[3] or (w.npc[n[2]][3] if n[2] in w.npc else [])
    parts, free = [], False
    for p in pk:
        if _sleep(w, p):
            continue
        iv = _intervals(w, p)
        free |= not iv
        parts += [_span_class(s) for s in iv]
    cls = "all-day" if free or not parts else "day-only" if set(parts) == {"day"} else \
        "night-only" if set(parts) == {"night"} else "mixed"
    return {"cls": cls, "sleep": any(_sleep(w, p) for p in pk), "scheduled": bool(parts), "packages": len(pk)}


def schedule_report(w: World, bases) -> dict:
    memo, ref_cls, seen = {}, Counter(), {}
    for b in bases:
        kids = [x for x in resolve(w, b) if is_creature(w, x)]
        for x in kids:
            memo.setdefault(x, schedule_class(w, x))
        if kids:
            ref_cls[Counter(memo[x]["cls"] for x in kids).most_common(1)[0][0]] += 1
            seen.update({x: memo[x] for x in kids})
    return {"refs_by_class": dict(ref_cls), "npcs": len(seen),
            "npcs_by_class": dict(Counter(v["cls"] for v in seen.values())),
            "npcs_with_sleep_package": sum(v["sleep"] for v in seen.values()),
            "npcs_with_scheduled_package": sum(v["scheduled"] for v in seen.values()),
            "npcs_without_packages": sum(v["packages"] == 0 for v in seen.values())}


def pct(v) -> list:
    return [round(float(np.percentile(v, p)), 1) for p in (10, 50, 90)] if len(v) else []


def nearest(q: np.ndarray, pts: np.ndarray, reach: float = REACH) -> np.ndarray:
    """Distance from each query xy to the nearest pts xy among the 3x3 cells round it; `reach` when none."""
    out = np.full(len(q), float(reach))
    if not len(pts):
        return out
    pc = np.floor(pts / CELL_UNITS).astype(np.int64)
    order = np.lexsort((pc[:, 1], pc[:, 0]))
    pts, pc = pts[order], pc[order]
    ck = pc[:, 0] * 100003 + pc[:, 1]
    qc = np.floor(q / CELL_UNITS).astype(np.int64)
    for cx, cy in {tuple(c) for c in qc}:
        idx = np.where((qc[:, 0] == cx) & (qc[:, 1] == cy))[0]
        lo = [np.arange(*np.searchsorted(ck, [(cx + dx) * 100003 + cy + dy, (cx + dx) * 100003 + cy + dy + 1]))
              for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
        lo = np.concatenate(lo).astype(np.int64)
        if len(lo):
            d = np.sqrt(((q[idx, None, :] - pts[lo][None, :, :]) ** 2).sum(2)).min(1)
            out[idx] = np.minimum(d, reach)
    return out


def slope_deg(h: np.ndarray, x: float, y: float, cx: int, cy: int) -> float:
    u, v = (x - cx * CELL_UNITS) / VERTEX_SPACING_UNITS, (y - cy * CELL_UNITS) / VERTEX_SPACING_UNITS
    i, j = min(max(int(v), 0), 31), min(max(int(u), 0), 31)
    q = h[i:i + 2, j:j + 2].astype(np.float64)  # [row y][col x]
    gx = ((q[0, 1] - q[0, 0]) + (q[1, 1] - q[1, 0])) / 2 / VERTEX_SPACING_UNITS
    gy = ((q[1, 0] - q[0, 0]) + (q[1, 1] - q[0, 1])) / 2 / VERTEX_SPACING_UNITS
    return float(np.degrees(np.arctan(np.hypot(gx, gy))))


def road_vertices(t: dict) -> tuple[np.ndarray, list[str]]:
    road = {f: v[1] for f, v in t["forms"].items()
            if v[0] == "LTEX" and any(s in v[1].lower() for s in ("path", "cobble", "road"))}
    pts = []
    for (cx, cy), c in t["cells"].items():
        if c["h"] is None:
            continue
        rd = np.zeros((33, 33), np.float32)  # strongest road opacity
        ot = np.zeros((33, 33), np.float32)  # strongest other opacity
        for q in range(4):  # quadrant 0 SW, 1 SE, 2 NW, 3 NE, each 17x17 vertices
            r0, c0 = (q // 2) * 16, (q % 2) * 16
            (rd if c["btxt"][q] in road else ot)[r0:r0 + 17, c0:c0 + 17] = 1.0
        for quad, _, ltex, alpha in c["atxt"]:
            r0, c0 = (quad // 2) * 16, (quad % 2) * 16
            sl = (slice(r0, r0 + 17), slice(c0, c0 + 17))
            a = np.asarray(alpha, np.float32).reshape(17, 17)
            tgt = rd if ltex in road else ot
            tgt[sl] = np.maximum(tgt[sl], a)
        ii, jj = np.nonzero((rd >= ROAD_ALPHA) & (rd >= ot))
        if len(ii):
            pts.append(np.stack([cx * CELL_UNITS + jj * VERTEX_SPACING_UNITS,
                                 cy * CELL_UNITS + ii * VERTEX_SPACING_UNITS], 1).astype(np.float64))
    return (np.concatenate(pts) if pts else np.zeros((0, 2))), sorted(set(road.values()))


def measure_vanilla() -> dict:
    t = load.tamriel()
    w = World("Skyrim.esm", True)
    tam = ("skyrim.esm", load.TAMRIEL)
    rows = [a for a in w.parts["Skyrim.esm"]["achr"]
            if a[0] == tam and any(is_creature(w, x) for x in resolve(w, a[4]))]
    pts, road_names = road_vertices(t)
    d = nearest(np.array([(a[1], a[2]) for a in rows], np.float64), pts)
    return {
        "creature_refs": len(rows),
        "road_ltex_used": road_names, "road_vertices": int(len(pts)),
        "road_m_p10_50_90": [round(x / UNITS_PER_METRE, 1) for x in pct(d)],
        "road_units_p10_50_90": pct(d),
        "within_512_units_of_road": round(float((d <= 512).mean()), 4),
        "no_road_within_3x3_cells": int((d >= REACH).sum()),
        "schedule": schedule_report(w, [a[4] for a in rows]),
    }


def measure_mod(name: str) -> dict:
    w = World(name, True)
    o = w.parts[name]
    mine = {k for k in o["worlds"] if k[0] == o["key_own"]}
    rows = [a for a in o["achr"] if a[0] in mine and any(is_creature(w, x) for x in resolve(w, a[4]))]
    if not rows:
        return {"n_refs": 0, "worlds": sorted(o["worlds"][k] for k in mine)}
    trees: dict = defaultdict(list)
    for r in o["refr"]:
        b = w.base.get(r[4])
        if r[0] in mine and b and (b[0] in ("TREE", "FLOR") or (b[0] == "STAT" and any(p in b[1].lower() for p in PLANT))):
            trees[r[0]].append((r[1], r[2]))
    sl, td = [], []
    for wk in mine:
        rs = [a for a in rows if a[0] == wk]
        if not rs:
            continue
        td.extend(nearest(np.array([(a[1], a[2]) for a in rs], np.float64),
                          np.array(trees.get(wk, []), np.float64).reshape(-1, 2)))
        for a in rs:
            cx, cy = int(a[1] // CELL_UNITS), int(a[2] // CELL_UNITS)
            h = o["land"].get((wk, cx, cy))
            if h is not None:
                sl.append(slope_deg(h, a[1], a[2], cx, cy))
    td = np.array(td)
    return {
        "n_refs": len(rows), "worlds": sorted(o["worlds"][k] for k in mine), "refs_with_land": len(sl),
        "slope_deg_p50_p90_max": [round(float(np.percentile(sl, 50)), 1), round(float(np.percentile(sl, 90)), 1),
                                  round(float(np.max(sl)), 1)] if sl else [],
        "tree_refs_in_worlds": sum(len(v) for v in trees.values()),
        "tree_units_p10_50_90": pct(td), "tree_m_p10_50_90": [round(x / UNITS_PER_METRE, 1) for x in pct(td)],
        "no_tree_within_2_cells": int((td >= REACH).sum()),
        "schedule": schedule_report(w, [a[4] for a in rows]),
    }


def measure() -> dict:
    return {"A_skyrim_tamriel": measure_vanilla(), "B_mods": {n: measure_mod(n) for n in MOD_PLUGINS}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    t0 = time.time()
    m = measure()
    m["seconds"] = round(time.time() - t0, 1)
    txt = json.dumps(m, indent=1, default=str)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(txt + "\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
