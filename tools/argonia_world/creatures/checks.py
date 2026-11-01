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
    dens      every den marker has its predator within DEN_BESIDE_M (+ one vertex step)
"""
from __future__ import annotations

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.creatures import place as pl
from tools.argonia_world.creatures import roster

MIN_KINDS = 12


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
