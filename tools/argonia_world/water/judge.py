"""The water check's three placement rules (lane 1.15-r4-water, owner play test 3 findings 19 and 20), pure
functions over the emitted stream (`out/water/cells.jsonl`, `records.json`), the solve and the written ground, so a
synthetic cell tests them (tests/test_judge.py) and `water check` runs them on the province:

1. pieces: every rapids or falls piece stands on a step between two cells whose levels differ, its base no more
   than BED_TOL_U over the bed the terrain graded there (deeper is water under it) (the line on the edge at the upper water, the foot pieces where the
   bed meets the lower water) and facing down the step (the skirt, as Skyrim.esm lays it, up it);
2. no hovering surface: along every edge where a water cell meets a dry cell, or a lower water outside a step's
   channel, the ground stands within BED_TOL_U under the level or above it; and every channel crossing (where the
   upper sheet ends over the lower cell's bed) is covered by a rapids line;
3. still and flowing: a body's cell (lake, pond, pool, tarn, marsh, lagoon, backswamp) takes a still type, a
   river's own cell a flowing one (layer.TYPES, measured);
4. types: every water cell has one of our types, and each type copies the record the game draws (the load order's
   winner, layer.winners), never a record a later plugin overrides (round 5).

Ground: the province grid (4033 x 4033, row 0 north, metres); world units map to it by skyrim_units.
"""
from __future__ import annotations

import math

import numpy as np

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.water import steps as stp

UPM = su.UNITS_PER_METRE
Q = su.QUADS_PER_CELL
X0, Y0 = su.PROVINCE_CELL_SW
NB = stp.OUT


def ground_at(g: np.ndarray, x: float, y: float) -> float:
    c = int(round((x - X0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS))
    r = g.shape[0] - 1 - int(round((y - Y0 * su.CELL_UNITS) / su.VERTEX_SPACING_UNITS))
    return float(g[min(max(r, 0), g.shape[0] - 1), min(max(c, 0), g.shape[1] - 1)])


def _edge(g: np.ndarray, cx: int, cy: int, e: str) -> np.ndarray:
    """The edge's 33 ground samples, west->east (n, s) or south->north (e, w)."""
    r = (g.shape[0] - 1) - (cy - Y0 + 1) * Q
    c = (cx - X0) * Q
    if e == "n":
        return g[r, c:c + Q + 1]
    if e == "s":
        return g[r + Q, c:c + Q + 1]
    col = c + (Q if e == "e" else 0)
    return g[r:r + Q + 1, col][::-1]


def _yaw_off(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def pieces(steps, levels: dict, refs: list[tuple[str, tuple, float]], g: np.ndarray | None) -> list[str]:
    """Rule 1. `refs`: (kind or None for a base no chain uses, pos units, yaw deg)."""
    bad = []
    chained = [s for s in steps if s.chain != "closed"]
    for s in chained:
        dx, dy = NB[s.edge]
        lo = levels.get((s.cx + dx, s.cy + dy))
        up = levels.get((s.cx, s.cy))
        if lo is None or up is None or up - lo < 0.05 or abs(lo - s.lower_m) > 0.01:
            bad.append(f"step ({s.cx},{s.cy}) {s.edge}: not between two water cells whose levels differ")
    pts = np.array([stp.edge_point(s) for s in chained]) if chained else np.zeros((0, 2))
    for kind, pos, yaw in refs:
        if not len(pts):
            bad.append(f"{kind} at {pos[:2]}: no step")
            continue
        i = int(np.argmin(np.hypot(pts[:, 0] - pos[0], pts[:, 1] - pos[1])))
        s = chained[i]
        where = f"{kind} on step ({s.cx},{s.cy}) {s.edge}"
        if kind is None or kind not in stp.CHAINS[s.chain]:
            bad.append(f"{where}: a piece the step's chain does not take")
            continue
        foot = kind in stp.AT_FOOT
        want_xy = stp.foot_point(s) if foot else stp.edge_point(s)
        if math.hypot(pos[0] - want_xy[0], pos[1] - want_xy[1]) > su.VERTEX_SPACING_UNITS / 2:
            bad.append(f"{where}: off its place on the step")
        water = (s.lower_m if foot else s.upper_m) * UPM
        if abs(pos[2] - water) > stp.BED_TOL_U:
            bad.append(f"{where}: {pos[2] - water:+.0f} u off its water")
        if g is not None:
            bed = water - (stp.FOOT_BED_M if foot else stp.STEP_BED_M) * UPM
            gz = ground_at(g, pos[0], pos[1]) * UPM
            if gz - bed > stp.BED_TOL_U:  # deeper is water under the piece; higher buries it in a bank
                bad.append(f"{where}: the bed under it is {gz - bed:+.0f} u over the graded bed (buried)")
        want = (stp.YAW[s.edge] + (180.0 if kind in stp.FACE_UP else 0.0)) % 360
        if _yaw_off(yaw, want) > 45.0:
            bad.append(f"{where}: faces {_yaw_off(yaw, want):.0f} deg off {'up' if kind in stp.FACE_UP else 'down'} the step")
    lines = {(s.cx, s.cy, s.edge) for s in chained if g is None or not buried(s, 1.0, g)}  # a buried step reads as a bank
    covered = set()
    for kind, pos, _ in refs:
        if kind == "rapids" and len(pts):
            i = int(np.argmin(np.hypot(pts[:, 0] - pos[0], pts[:, 1] - pos[1])))
            covered.add((chained[i].cx, chained[i].cy, chained[i].edge))
    for k in sorted(lines - covered):
        bad.append(f"step ({k[0]},{k[1]}) {k[2]}: the upper sheet's end over the channel has no rapids line (hovering surface)")
    return bad


def seat(steps, refs: list[tuple[str, tuple, float, float]]) -> tuple[dict[str, int], list[str]]:
    """The seat rule (r6 water-steps): every chained piece against its own step by rule: its origin neither over the
    upper reach's water nor under the lower's, not facing uphill, and its OBND's foot (scaled) at or under the lower
    water (no hanging sheet edge). `refs`: (kind, pos units, yaw deg, scale). Returns counts per rule and the reds."""
    chained = [s for s in steps if s.chain != "closed"]
    n = {"pieces": 0, "above upper": 0, "below lower": 0, "uphill": 0, "hanging": 0}
    bad = []
    if not chained:
        return n, [f"{k} at {p[:2]}: no step" for k, p, _, _ in refs]
    pts = np.array([stp.foot_point(s) for s in chained] + [stp.edge_point(s) for s in chained])
    for kind, pos, yaw, scale in refs:
        n["pieces"] += 1
        i = int(np.argmin(np.hypot(pts[:, 0] - pos[0], pts[:, 1] - pos[1]))) % len(chained)
        s = chained[i]
        up, lo = s.upper_m * UPM, s.lower_m * UPM
        where = f"{kind} on step ({s.cx},{s.cy}) {s.edge}"
        z0 = stp.OBND_Z.get(kind, (0, 0))[0] * scale
        for rule, hit in (("above upper", pos[2] > up + stp.BED_TOL_U), ("below lower", pos[2] < lo - stp.BED_TOL_U),
                          ("hanging", pos[2] + z0 > lo + stp.BED_TOL_U + 0.5)):
            if hit:
                n[rule] += 1
                bad.append(f"{where}: {rule} ({pos[2]:.0f} u, foot {pos[2] + z0:.0f} u, waters {up:.0f}/{lo:.0f} u)")
        want = (stp.YAW[s.edge] + (180.0 if kind in stp.FACE_UP else 0.0)) % 360
        if _yaw_off(yaw, want) > 90.0:
            n["uphill"] += 1
            bad.append(f"{where}: faces uphill ({_yaw_off(yaw, want):.0f} deg off)")
    return n, bad


def hovering(levels: dict, steps, g: np.ndarray, in_province) -> list[str]:
    """Rule 2's ground half: no ground more than BED_TOL_U under a level along an edge where its sheet ends."""
    chan = {(s.cx, s.cy, s.edge): (s.cross_lo, s.cross_hi) for s in steps if s.chain != "closed"}
    bad = []
    for (cx, cy), lv in levels.items():
        for e, (dx, dy) in NB.items():
            o = (cx + dx, cy + dy)
            if not in_province(*o):
                continue
            ol = levels.get(o)
            if ol is not None and lv - ol <= 0.05:
                continue
            line = np.asarray(_edge(g, cx, cy, e), np.float64)
            if (cx, cy, e) in chan:
                a, b = chan[(cx, cy, e)]
                keep = np.ones(Q + 1, bool)
                keep[a:b + 1] = False
                line = line[keep]
            if len(line) and (lv - line.min()) * UPM > stp.BED_TOL_U:
                bad.append(f"cell ({cx},{cy}) {e}: the sheet ends {(lv - line.min()) * UPM:.0f} u over the ground "
                           f"beside {'a dry cell' if ol is None else 'lower water'}")
    return bad


def still_flow(cells: list[tuple[int, int, str | None, str | None, str]], flow: dict[str, bool]) -> list[str]:
    """Rule 3. `cells`: (cx, cy, body_id, reach_id, emitted type key); `flow`: type key -> the type flows."""
    bad = []
    for cx, cy, body, reach, key in cells:
        want = not body and bool(reach)
        if flow.get(key) is not want:
            bad.append(f"cell ({cx},{cy}) {'still body ' + body if body else 'river ' + str(reach)}: type {key} "
                       f"{'is unknown' if key not in flow else 'flows' if flow[key] else 'is still'}")
    return bad


def types(cells: list[tuple[int, int, str | None, str | None, str]], recs: list[dict],
          winners: dict | None) -> tuple[dict[str, int], list[str]]:
    """Rule 4 (round 5): the cells per type (edid -> count), and a red for a water cell with no type, or a type whose
    template is not the load order's winner for its editor id (`winners`: layer.winners; None skips that part)."""
    by_key = {r["formKey"]: r for r in recs}
    counts: dict[str, int] = {r["edid"]: 0 for r in recs}
    bad = []
    for cx, cy, _, _, key in cells:
        if key not in by_key:
            bad.append(f"cell ({cx},{cy}): type {key} is no WATR of ours")
            continue
        counts[by_key[key]["edid"]] += 1
    for r in recs:
        plugin, edid = r["template"].split(":", 1)
        if winners is not None and (edid not in winners or winners[edid][0] != plugin):
            bad.append(f"{r['edid']} copies {r['template']}, the game draws {winners.get(edid, ('nothing',))[0]}'s")
    return counts, bad


def buried(s, width_m: float, g: np.ndarray) -> bool:
    """A step whose ground stands over the graded bed at any of its pieces (the terrain kept no channel there):
    the emit lays no chain on it, and the edge reads as a closed bank."""
    for p in stp.place(s, width_m):
        foot = p["kind"] in stp.AT_FOOT
        bed = ((s.lower_m - stp.FOOT_BED_M) if foot else (s.upper_m - stp.STEP_BED_M)) * UPM
        if ground_at(g, p["pos"][0], p["pos"][1]) * UPM - bed > stp.BED_TOL_U:
            return True
    return False
