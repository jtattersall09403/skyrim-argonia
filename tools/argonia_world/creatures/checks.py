"""The creatures lane's L1 checks (the brief's Acceptance), over the rows and a planner run.

    classes   every exterior region class has at least MIN_KINDS creature kinds, each with a why
    habitat   every spawn ref stands where every creature it can spawn may stand (medium, depth, slope);
              every den predator where its own rule allows
    no_spawn  no ref within a place's no-spawn radius
    levels    every list's entries sit at the list's band level, and every list's level is its band's
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
    bad = w.query("SELECT l.id, l.level, e.level AS e, b.level AS b FROM creature_list l JOIN danger_band_level b "
                  "USING (band) JOIN creature_list_entry e ON e.list_id = l.id WHERE e.level <> b.level "
                  "OR l.level <> b.level")
    bad += w.query("SELECT id, 0, 0, 0 FROM creature_list WHERE chance_none <> 0")
    return {"lists": len(w.rows("creature_list")), "fail": [r["id"] for r in bad][:10] or None}


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
