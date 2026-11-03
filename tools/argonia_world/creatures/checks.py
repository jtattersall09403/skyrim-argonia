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
    kind_bars every region class holds at least as many wild kinds as the Skyrim.esm biome region nearest its largest
              land region in cells (never below Skyrim's least-varied region of BIOME_MIN_CELLS or more) AND as the
              Black Marsh.esm main worldspace holds over an equal area (its densest window of that many cells, the
              whole worldspace past its size); every D2/D3 land list holds DRY_MIN kinds. The vanilla numbers are
              computed by vanilla/creatures.py --bars and cached in data/creature-kind-bars.json (counts only, 0003).
              Owner #37 (2026-11-03): "at least as many kinds per equivalent-sized region".
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.argonia_world.creatures import roster

# numpy, the units and the planner load inside the functions that need them: kind_bars runs in the world gate's
# named checks (db check), on the system python without numpy

MIN_KINDS = 12
# Skyrim.esm's Tamriel creature refs per 100 cells by terrain class (vanilla/creatures.py, 2026-11-03 run)
VANILLA_PER_100 = {"shore": 105.16, "forest": 95.87, "open": 25.90, "mountain": 20.78, "water": 8.72}
DENSITY_MIN_CELLS = 20
BARS = Path(__file__).resolve().parents[3] / "data" / "creature-kind-bars.json"
BIOME_MIN_CELLS = 600  # a Skyrim biome region the size of a hold's wilderness (the research note's comparable unit)
DRY_MIN = 12  # Skyrim's fewest land species in a biome region (creature-kinds-per-region.md, owner #37)


def our_kinds(w) -> dict[str, dict]:
    """Per region class: the wild kinds a walker can meet (the lists' kinds and the apex kinds at dens), the kinds
    of its D2 and D3 land lists, and its largest land region in cells."""
    out = {c: {"kinds": set(), "dry": {}, "cells": 0} for c in roster.CLASSES}
    for r in w.query("SELECT l.region_class c, l.band b, l.medium m, f.creature_id k FROM creature_list l "
                     "JOIN creature_list_entry e ON e.list_id = l.id JOIN creature_form f USING (form_key)"):
        if r["c"] in out:
            out[r["c"]]["kinds"].add(r["k"])
            if r["m"] == "land" and r["b"] in ("D2", "D3"):
                out[r["c"]]["dry"].setdefault(r["b"], set()).add(r["k"])
    for r in w.query("SELECT rc.region_class c, rc.creature_id k FROM creature_region_class rc JOIN creature c "
                     "ON c.id = rc.creature_id JOIN creature_form f ON f.creature_id = c.id WHERE c.kind = 'apex'"):
        if r["c"] in out:
            out[r["c"]]["kinds"].add(r["k"])
    for r in w.query("SELECT eco_class_id c, MAX(cells) n FROM land_region GROUP BY eco_class_id"):
        if r["c"] in out:
            out[r["c"]]["cells"] = r["n"]
    return out


def bar_for(cells: int, bars: dict) -> tuple[int, str, int, str]:
    """(Skyrim's bar, its region, the mod's bar, its window) for a region of `cells` cells."""
    sk = bars["skyrim"]
    near = min(sk, key=lambda e: (abs(sk[e]["cells"] - cells), -sk[e]["wild_kinds"]))
    floor = min(v["wild_kinds"] for v in sk.values() if v["cells"] >= BIOME_MIN_CELLS)
    main = bars["mod"][bars["mod_main"]]
    if cells >= main["cells"]:
        mod, win = main["wild_kinds"], f"{bars['mod_main']} ({main['cells']} cells)"
    else:
        wins = {int(k): v for k, v in main["window_max"].items()}
        a = min(wins, key=lambda k: (abs(k - cells), -wins[k]))
        mod, win = wins[a], f"{bars['mod_main']} window of {a} cells"
    return max(sk[near]["wild_kinds"], floor), near, mod, win


def kind_bars(w, bars: dict | None = None) -> dict:
    bars = bars or json.loads(BARS.read_text())
    got, bad = {}, []
    for c, v in our_kinds(w).items():
        sky, near, mod, win = bar_for(v["cells"], bars)
        n, dry = len(v["kinds"]), {b: len(k) for b, k in v["dry"].items()}
        got[c] = {"cells": v["cells"], "kinds": n, "skyrim": sky, "skyrim_region": near, "mod": mod, "mod_window": win,
                  "dry": dry}
        if n < sky:
            bad.append(f"{c}: {n} kinds < Skyrim's {sky} ({near}, for {v['cells']} cells)")
        if n < mod:
            bad.append(f"{c}: {n} kinds < Black Marsh.esm's {mod} ({win})")
        bad += [f"{c}: {b} land list {k} kinds < {DRY_MIN}" for b, k in dry.items() if k < DRY_MIN]
        bad += [f"{c}: no {b} land list" for b in ("D2", "D3") if b not in dry]
    return {"classes": got, "fail": bad or None}


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


def terrain_class(h, level: float, trees: int) -> str:
    """vanilla/creatures.py cell_class on our cell: h metres, level the cell's water, trees its stems."""
    from tools.argonia_world import skyrim_units as su
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
    import numpy as np

    from tools.argonia_world import skyrim_units as su
    from tools.argonia_world.creatures import place as pl
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
