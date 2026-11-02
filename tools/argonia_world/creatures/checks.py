"""The creatures lane's L1 checks (the brief's Acceptance), over the rows and a planner run.

    classes   every exterior region class has at least MIN_KINDS creature kinds, each with a why
    habitat   every spawn ref stands where every creature it can spawn may stand (medium, depth, slope);
              every den predator where its own rule allows
    no_spawn  no ref within a place's no-spawn radius
    levels    every list's level is its band's; chance none 0
    unlevelled decision 0035 over what ArgoniaGen writes (records.document) and the planned refs: no list entry
              above level 1, no zone with min <> max, no template off its band's fixed level, and no list entry or
              den predator naming a mod creature whose record scales or whose death item is levelled (our fixed
              copy instead); the plugin's own bytes are checked again at readback (levelled.check)
    lists     every region class's lists together hold at least MIN_KINDS kinds; no apex kind in a list (dens only)
    density   spawn refs per 100 sampled cells, per vanilla terrain class (vanilla/creatures.py cell_class), at or
              above Skyrim.esm's (VANILLA_PER_100); classes with fewer than DENSITY_MIN_CELLS cells are reported only
    dens      every den marker has its predator within DEN_BESIDE_M (+ one vertex step)
"""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.creatures import place as pl
from tools.argonia_world.creatures import roster

MIN_KINDS = 12
# Skyrim.esm's Tamriel creature refs per 100 cells by terrain class (vanilla/creatures.py, 2026-11-03 run)
VANILLA_PER_100 = {"shore": 105.16, "forest": 95.87, "open": 25.90, "mountain": 20.78, "water": 8.72}
DENSITY_MIN_CELLS = 20


def lists(w) -> dict:
    kinds, bad = {}, []
    for r in w.query("SELECT l.region_class, f.creature_id, c.kind FROM creature_list l JOIN creature_list_entry e "
                     "ON e.list_id = l.id JOIN creature_form f USING (form_key) JOIN creature c ON c.id = f.creature_id"):
        kinds.setdefault(r["region_class"], set()).add(r["creature_id"])
        if r["kind"] == "apex":
            bad.append(f"{r['region_class']}: apex {r['creature_id']} in a list")
    n = {c: len(kinds.get(c, ())) for c in roster.CLASSES}
    bad += [f"{c}: {k} kinds in its lists" for c, k in n.items() if k < MIN_KINDS]
    return {"kinds": n, "fail": sorted(set(bad))[:10] or None}


def terrain_class(h: np.ndarray, level: float, trees: int) -> str:
    """vanilla/creatures.py cell_class on our cell: h metres, level the cell's water, trees its stems."""
    wet = float((h < level).mean())
    if wet > 0.5:
        return "water"
    if wet > 0:
        return "shore"
    if float(h.mean()) * su.UNITS_PER_METRE > 4000:
        return "mountain"
    return "forest" if trees >= 10 else "open"


def density(run: dict, src, cw, cells, stems: dict | None) -> dict:
    """Spawn refs (lists and den predators: Skyrim.esm's count is every creature ACHR) per 100 planned cells."""
    n, refs = {}, {}
    per = {}
    for r in run["refs"]:
        if r["kind"] != "den":
            per[tuple(r["cell"])] = per.get(tuple(r["cell"]), 0) + 1
    cls = run.get("cell_class") or {}
    for cx, cy in cells:
        if (cx, cy) not in cls:
            continue
        r0, r1 = src.cell_rows(cy)
        c0, c1 = src.cell_cols(cx)
        h = src.heights(r0, r1 + 1, c0, c1 + 1)
        lv = cw.level(cx, cy)
        level = lv if lv is not None else cw.nearest_level(cx, cy)
        t = terrain_class(h, level, 0 if stems is None else len(stems.get((cx, cy), ())))
        n[t] = n.get(t, 0) + 1
        refs[t] = refs.get(t, 0) + per.get((cx, cy), 0)
    got = {t: {"cells": n[t], "per_100": round(100 * refs[t] / n[t], 1), "vanilla": VANILLA_PER_100[t]} for t in n}
    bad = [f"{t}: {v['per_100']} per 100 cells < vanilla {v['vanilla']}" for t, v in got.items()
           if v["cells"] >= DENSITY_MIN_CELLS and v["per_100"] < v["vanilla"]]
    return {"by_terrain": got, "fail": bad or None}


def classes(w) -> dict:
    n = {}
    for r in w.query("SELECT region_class, COUNT(*) AS k FROM creature_region_class WHERE why <> '' "
                     "GROUP BY region_class"):
        n[r["region_class"]] = r["k"]
    bad = {c: n.get(c, 0) for c in roster.CLASSES if n.get(c, 0) < MIN_KINDS}
    return {"kinds": n, "fail": bad or None}


def levels(w) -> dict:
    bad = w.query("SELECT l.id FROM creature_list l JOIN danger_band_level b USING (band) WHERE l.level <> b.level")
    bad += w.query("SELECT id, 0, 0, 0 FROM creature_list WHERE chance_none <> 0")
    return {"lists": len(w.rows("creature_list")), "fail": [r["id"] for r in bad][:10] or None}


def unlevelled(w, run: dict | None = None) -> dict:
    from tools.argonia_world.creatures import records
    doc = records.document(w)
    order = records.fixed_forms(w)
    fixed = set(order)
    lv = {r["band"]: r["level"] for r in w.query("SELECT band, level FROM danger_band_level")}
    bad = [f"{lst['edid']}: entry {fk} at level {n}" for lst in doc["lists"] for fk, n, _ in lst["entries"] if n != 1]
    bad += [f"{lst['edid']}: names the scaling {fk}" for lst in doc["lists"] for fk, _, _ in lst["entries"]
            if fk in fixed]
    bad += [f"{z['edid']}: min {z['minLevel']} <> max {z['maxLevel']}" for z in doc["zones"]
            if z["minLevel"] != z["maxLevel"]]
    bad += [f"{t['edid']}: level {t['level']}" for t in doc["templates"] if t["level"] not in lv.values()]
    want = {(f, b) for f in fixed for b in lv}
    got = {(a["source"], a["edid"].rsplit("_", 1)[1]) for a in doc["actors"]}
    bad += [f"{f} {b}: no fixed copy" for f, b in sorted(want - got)]
    for r in (run or {}).get("refs", []):
        if r["kind"] == "predator" and records.base_of(r, order)[1] in fixed:
            bad.append(f"den predator {r['base']} at {r['cell']}: the scaling form itself")
    return {"entries": sum(len(lst["entries"]) for lst in doc["lists"]), "fixed_forms": len(fixed),
            "actors": len(doc["actors"]), "fail": bad[:10] or None}


def refs(run: dict, src, cw) -> dict:
    rules, (P, R) = run["rules"], run["places"]
    hs = {}
    bad_h, bad_ns, bad_den = [], [], []
    by_cell = {}
    for r in run["refs"]:
        by_cell.setdefault(tuple(r["cell"]), []).append(r)
    for (cx, cy), rs in by_cell.items():
        r0, r1 = src.cell_rows(cy)
        c0, c1 = src.cell_cols(cx)
        h = src.heights(r0, r1 + 1, c0, c1 + 1)
        lv = cw.level(cx, cy)
        level = lv if lv is not None else cw.nearest_level(cx, cy)
        depth, slope = level - h, pl.slope_deg(h)
        hs[(cx, cy)] = h
        for r in rs:
            i, j = r["i"], r["j"]
            if r["kind"] == "spawn":
                key = (r["class"], r["band"], r["medium"])
                cids = rules.lists[key]
            elif r["kind"] in ("den", "predator"):
                cids = [r["creature"]]
            for c in cids:
                m, rule = rules.medium[c]
                if r["kind"] == "spawn" and m != r["medium"]:
                    bad_h.append((r["base"], c, "medium"))
                if not rule.mask(depth[i:i + 1, j:j + 1], slope[i:i + 1, j:j + 1], m)[0, 0]:
                    bad_h.append((r["base"], c, (cx, cy, i, j), round(float(depth[i, j]), 2)))
            d = np.hypot(P[:, 0] - r["x"], P[:, 1] - r["y"]) / su.UNITS_PER_METRE
            if (d < R).any():
                bad_ns.append((r["base"], (cx, cy), round(float(d.min()), 1)))
        dens = [r for r in rs if r["kind"] == "den"]
        for dn in dens:
            near = [p for p in rs if p["kind"] == "predator" and p["creature"] == dn["creature"]
                    and np.hypot(p["i"] - dn["i"], p["j"] - dn["j"]) * pl.STEP_M <= pl.DEN_BESIDE_M + pl.STEP_M]
            if not near:
                bad_den.append(dn["base"])
    return {"habitat": {"refs": len(run["refs"]), "fail": bad_h[:10] or None},
            "no_spawn": {"fail": bad_ns[:10] or None},
            "dens": {"dens": sum(r["kind"] == "den" for r in run["refs"]), "fail": bad_den[:10] or None}}
