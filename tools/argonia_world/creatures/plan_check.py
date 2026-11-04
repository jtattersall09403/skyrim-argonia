"""plan-check (lane 1.15-r6-creatures): does the province plan put enough kinds round each creatures-kinds stand?

For each region-class stop of tests/journeys/creatures-kinds.yaml: the spawn refs of the whole-province plan within the
read's radius (two cells, 8192 units) of the stand, the distinct kinds of that class their lists can yield (plus the
predators at dens), the expected number of distinct kinds the engine draws (one entry per spawn ref, uniform over the
list's entries: every entry level 1, chance none 0) and the chance of at least KINDS_N, the spawn points within
KINDS_REACH_M of the stand and whether the stand's eye line to its subject is clear. Exit 0 only when every stop has at
least KINDS_N kinds possible and expected, a spawn point within reach and a clear eye line. A live count below the
expected one is then the engine's spawning, not the plan.
"""
from __future__ import annotations

import math
import re

import numpy as np

from tools.argonia_world import skyrim_units as su

KINDS_N, RADIUS_U, REACH_M = 4, 2 * su.CELL_UNITS, 90.0
STOP = re.compile(r"- name: (\S+)\n(?:  #.*\n)*?  # subject: (-?\d+) (-?\d+) (-?\d+)\n(?:.*\n)*?"
                  r"  - console: player.setpos x (-?\d+)\n  - console: player.setpos y (-?\d+)")


def stops(text: str) -> list[dict]:
    return [{"name": m[1], "subj": (float(m[2]), float(m[3]), float(m[4])), "x": float(m[5]), "y": float(m[6])}
            for m in STOP.finditer(text)]


def kinds_near(refs: list[dict], entries: dict, cls: str, own: set, x: float, y: float, trials: int = 4000,
               seed: int = 1) -> dict:
    """The plan's kinds of class `cls` (its kinds `own`) round (x, y): possible, expected distinct, P(>= KINDS_N)."""
    sp = [r for r in refs if r["kind"] == "spawn" and math.hypot(r["x"] - x, r["y"] - y) < RADIUS_U]
    pred = {r["creature"] for r in refs if r["kind"] == "predator" and math.hypot(r["x"] - x, r["y"] - y) < RADIUS_U} & own
    possible = (set().union(*[set(entries[r["base"]]) for r in sp]) & own) | pred
    expected = len(pred)
    for k in possible - pred:
        expected += 1 - math.prod(1 - entries[r["base"]].count(k) / len(entries[r["base"]]) for r in sp)
    rng = np.random.default_rng(seed)
    lists = [entries[r["base"]] for r in sp]
    hits = sum(len(({e[int(rng.integers(len(e)))] for e in lists} & own) | pred) >= KINDS_N for _ in range(trials))
    return {"spawns": len(sp), "own_spawns": sum(r["class"] == cls for r in sp), "possible": len(possible),
            "expected": round(expected, 2), "p_ge": round(hits / trials, 3)}


def run(refs: list[dict], w, b, text: str) -> list[dict]:
    """One row per region-class stop; `fail` lists why it falls short."""
    from tools.journeys import frame
    entries: dict[str, list[str]] = {}
    for r in w.query("SELECT e.list_id, f.creature_id FROM creature_list_entry e JOIN creature_form f USING (form_key)"):
        entries.setdefault(r["list_id"], []).append(r["creature_id"])
    own: dict[str, set] = {}
    for r in w.query("SELECT creature_id, region_class FROM creature_region_class"):
        own.setdefault(r["region_class"], set()).add(r["creature_id"])
    xy = np.array([(r["x"], r["y"]) for r in refs if r["kind"] == "spawn"]).reshape(-1, 2)
    out = []
    for s in stops(text):
        if s["name"] not in own:
            continue
        k = kinds_near(refs, entries, s["name"], own[s["name"]], s["x"], s["y"])
        k["within_reach"] = int((np.hypot(xy[:, 0] - s["x"], xy[:, 1] - s["y"]) < REACH_M * su.UNITS_PER_METRE).sum())
        k["clear"] = bool(frame(b, s["x"], s["y"], s["subj"])["clear"]) if b is not None else None
        k["fail"] = [w_ for w_, bad in ((f"{k['possible']} kinds possible", k["possible"] < KINDS_N),
                                        (f"{k['expected']} kinds expected", k["expected"] < KINDS_N),
                                        (f"no spawn point within {REACH_M:.0f} m", not k["within_reach"]),
                                        ("eye line not clear", k["clear"] is False)) if bad]
        out.append({"class": s["name"], **k})
    return out
