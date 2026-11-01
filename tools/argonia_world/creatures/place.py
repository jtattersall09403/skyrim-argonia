"""The spawn planner (1.15 §g.3): Skyrim's own encounter method (spawn refs of levelled lists, in encounter zones,
predators beside dens), placed by rule on the generated ground and the solved cell water.

Measured in Skyrim.esm (vanilla/creatures.py, lane report "The vanilla measurement"): 46% of Tamriel's 4,362
exterior creature refs are levelled lists, the rest single creatures; one ref per occupied cell at the median
(p90 3); refs per 100 cells: shore 105, forest 96, open 26, mountain 21, water 9; every creature list has chance
none 0; 32% of creature refs stand within 60 m of a door (the den beside its mouth).

Per province cell (seeded by the cell, so a cell rebuilds alone and identically):
- **Class and band.** The cell's region class is its land_region's suffix; its band the danger tier of the
  nearest place (D0 counts as D1 outside the place: 74-ecology rule 3).
- **How many.** The band's spawns_per_cell (danger_band_level) is the expectation (x WATER_CELL on a cell more
  than half under water, as vanilla's open water): floor, plus one with probability of the fraction.
- **Where.** Each spawn ref picks a medium weighted by its eligible vertices (water x WATER_WEIGHT: vanilla's water
  cells hold a tenth of a shore cell's refs), then a vertex: water where the depth reaches every entry's
  min_depth_m; shore within shore_above_m above to max_depth_m below the water; land on dry ground; each under the
  medium's steepest slope. Never within a place's no-spawn radius (place_no_spawn by its class).
- **Which list.** lvln.<class>.<band>.<medium>; a medium with no list is not offered.
- **Dens.** A den creature of the class and band has dens_per_100_cells; its den marker stands on an eligible vertex
  of its medium and the creature itself (its first mod form, not a list) beside it, DEN_BESIDE_M away.
- **Zone.** Every ref carries the band's wild encounter zone (eczn.wild.<band>).
"""
from __future__ import annotations

import math
import zlib
from dataclasses import dataclass, field

import numpy as np

from tools.argonia_world import skyrim_units as su

SEED = 0xC4EA
WATER_WEIGHT = 0.1
WATER_CELL = 0.09  # Skyrim.esm: a cell more than half under water holds 8.7 creature refs per 100, a shore cell 105
# The classes whose water is the creatures' home (74-ecology: the delta's mudflats and channels, the river corridor's
# deep reaches): Skyrim's open-water cut (WATER_CELL, WATER_WEIGHT: its lakes and sea hold few creatures) does not
# apply; their water and shore cells take the band's full density (before: tidal-delta 19 refs in 50 cells,
# deep-river-corridor 9 in 45, province run of 2026-11-01).
WATER_CLASSES = frozenset({"tidal-delta", "deep-river-corridor"})
DEN_BESIDE_M = 6.0
# Cover: a vertex with COVER_MIN vegetation stems within COVER_R_M is bush, else open. 3 stems in 8 m (201 m2) is
# 60 % of the stem density of a vanilla forested cell at its p95 (83 stems per 3,422 m2 cell; vegetation/place.py
# VANILLA_P95): where a body can be hidden from the path.
COVER_R_M = 8.0
COVER_MIN = 3
STEP_M = su.VERTEX_SPACING_UNITS / su.UNITS_PER_METRE
U = su.UNITS_PER_METRE


@dataclass(frozen=True)
class Medium:
    """The rule a spawn point's vertex must meet: depth = water level - ground (negative on dry ground)."""
    min_depth: float
    max_depth: float
    above: float
    max_slope: float

    def mask(self, depth: np.ndarray, slope: np.ndarray, kind: str) -> np.ndarray:
        if kind == "water":
            m = depth >= self.min_depth
        elif kind == "shore":
            m = (depth >= -self.above) & (depth <= self.max_depth)
        else:
            m = depth < 0
        return m & (slope <= self.max_slope)


@dataclass
class Rules:
    lists: dict[tuple[str, str, str], list[str]]  # (class, band, medium) -> entry creature ids
    list_ids: dict[tuple[str, str, str], str]
    medium: dict[str, tuple[str, Medium]]  # creature -> (medium kind, rule)
    first_form: dict[str, str]
    dens: dict[tuple[str, str], list[tuple[str, float]]]  # (class, band) -> [(creature, dens per 100 cells)]
    spawns: dict[str, float]  # band -> per cell
    hostile: dict[str, bool] = field(default_factory=dict)  # creature -> hostile (74-ecology's hostility column)

    def ambush(self, key) -> bool:
        """A list whose entries are mostly hostile waits in cover (74-ecology: the crocodile ambushes from the bank,
        the death hopper from under the surface, the giant snake from its reedbed coil); the rest stand in the open."""
        cs = self.lists[key]
        return sum(self.hostile.get(c, False) for c in cs) * 2 > len(cs)

    def list_medium(self, key) -> Medium:
        """The strictest rule over a list's entries (every entry's habitat must allow the point)."""
        rs = [self.medium[c][1] for c in self.lists[key]]
        return Medium(max(r.min_depth for r in rs), min(r.max_depth for r in rs), min(r.above for r in rs),
                      min(r.max_slope for r in rs))


def load_rules(w) -> Rules:
    lists, ids = {}, {}
    for r in w.query("SELECT l.id, l.region_class, l.band, l.medium, f.creature_id FROM creature_list l "
                     "JOIN creature_list_entry e ON e.list_id = l.id JOIN creature_form f USING (form_key)"):
        k = (r["region_class"], r["band"], r["medium"])
        ids[k] = r["id"]
        if r["creature_id"] not in lists.setdefault(k, []):
            lists[k].append(r["creature_id"])
    med, dens = {}, {}
    bands = {}
    for r in w.query("SELECT creature_id, value FROM creature_band"):
        bands.setdefault(r["creature_id"], []).append(r["value"])
    for r in w.query("SELECT * FROM creature_spawn_rule"):
        med[r["creature_id"]] = (r["medium"], Medium(r["min_depth_m"], r["max_depth_m"], r["shore_above_m"],
                                                     r["max_slope_deg"]))
    for r in w.query("SELECT s.creature_id, s.dens_per_100_cells, c.region_class FROM creature_spawn_rule s "
                     "JOIN creature_region_class c USING (creature_id) WHERE s.den = 1"):
        for b in bands.get(r["creature_id"], []):
            dens.setdefault((r["region_class"], b), []).append((r["creature_id"], r["dens_per_100_cells"]))
    first = {}
    for r in w.query("SELECT creature_id, form_key FROM creature_form ORDER BY rowid"):
        first.setdefault(r["creature_id"], r["form_key"])
    spawns = {r["band"]: r["spawns_per_cell"] for r in w.query("SELECT * FROM danger_band_level")}
    hostile = {r["id"]: r["hostility"] == "hostile" for r in w.query("SELECT id, hostility FROM creature")}
    return Rules(lists, ids, med, first, dens, spawns, hostile)


def slope_deg(h: np.ndarray) -> np.ndarray:
    gy, gx = np.gradient(h, STEP_M)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def rng_for(cx: int, cy: int) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(f"{SEED}:{cx}:{cy}".encode()))


def _count(rng, e: float) -> int:
    return int(math.floor(e)) + int(rng.random() < e - math.floor(e))


def vertex_xy(cx: int, cy: int, i: np.ndarray, j: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Skyrim units of vertex (row i from the north, column j from the west) of cell (cx, cy)."""
    x = cx * su.CELL_UNITS + j * su.VERTEX_SPACING_UNITS
    y = cy * su.CELL_UNITS + (su.QUADS_PER_CELL - i) * su.VERTEX_SPACING_UNITS
    return x, y


def cover_counts(cx: int, cy: int, stems: np.ndarray | None) -> np.ndarray | None:
    """Stems (n x 2 units, the cell's vegetation refs) within COVER_R_M of each of the cell's 33 x 33 vertices."""
    if stems is None:
        return None
    ii, jj = np.mgrid[0:su.QUADS_PER_CELL + 1, 0:su.QUADS_PER_CELL + 1]
    x, y = vertex_xy(cx, cy, ii, jj)
    if not len(stems):
        return np.zeros(ii.shape, int)
    d2 = (x[..., None] - stems[:, 0]) ** 2 + (y[..., None] - stems[:, 1]) ** 2
    return (d2 < (COVER_R_M * U) ** 2).sum(-1)


def plan_cell(cx: int, cy: int, h: np.ndarray, level: float, cls: str, band: str, rules: Rules,
              blocked: np.ndarray | None = None, cover: np.ndarray | None = None) -> list[dict]:
    """The spawn refs of one cell. h: 33 x 33 ground metres (row 0 north); level: the cell's water (its own, or
    the nearest water's level on a dry cell); blocked: vertices inside a no-spawn radius."""
    rng = rng_for(cx, cy)
    depth = level - h
    slope = slope_deg(h)
    free = ~blocked if blocked is not None else np.ones(h.shape, bool)
    zone = f"eczn.wild.{band}"
    out = []
    masks = {}
    for m in ("water", "shore", "land"):
        k = (cls, band, m)
        if k in rules.lists:
            masks[m] = rules.list_medium(k).mask(depth, slope, m) & free
    wet = cls in WATER_CLASSES
    weights = {m: v.sum() * (WATER_WEIGHT if m == "water" and not wet else 1.0) for m, v in masks.items()}
    tot = sum(weights.values())

    def put(kind, base, m, mask, extra=None, near=None):
        ii, jj = np.nonzero(mask)
        if near is not None:
            d = np.hypot(ii - near[0], jj - near[1]) * STEP_M
            ok = (d > 0) & (d <= DEN_BESIDE_M + STEP_M)
            if not ok.any():
                return None
            ii, jj = ii[ok], jj[ok]
        if not len(ii):
            return None
        p = int(rng.integers(len(ii)))
        i, j = int(ii[p]), int(jj[p])
        x, y = vertex_xy(cx, cy, i, j)
        z = float(h[i, j]) if m != "water" else float(level - min(depth[i, j], 2.0) / 2)
        r = {"cell": [cx, cy], "kind": kind, "base": base, "medium": m, "zone": zone, "band": band, "class": cls,
             "i": i, "j": j, "x": float(x), "y": float(y), "z": round(z * U, 1), "rz": round(float(rng.random()) * 6.2832, 3)}
        r.update(extra or {})
        out.append(r)
        return r

    if tot > 0:
        ms = list(weights)
        pr = np.array([weights[m] for m in ms], float) / tot
        e = rules.spawns[band] * (WATER_CELL if (depth > 0).mean() > 0.5 and not wet else 1.0)
        for _ in range(_count(rng, e)):
            m = ms[int(rng.choice(len(ms), p=pr))]
            mask = masks[m]
            tag = {}
            if cover is not None:  # bush or open by the vegetation; a hostile list waits in the bush (an ambush point)
                amb = rules.ambush((cls, band, m))
                pick = mask & ((cover >= COVER_MIN) if amb else (cover < COVER_MIN))
                if pick.any():
                    mask = pick
                    tag = {"cover": "bush" if amb else "open", "ambush": amb}
            put("spawn", rules.list_ids[(cls, band, m)], m, mask, tag)
    for cid, per100 in rules.dens.get((cls, band), []):
        if rng.random() >= per100 / 100.0:
            continue
        m, rule = rules.medium[cid]
        mask = rule.mask(depth, slope, m) & free
        den = put("den", f"den.{cid}", m, mask, {"creature": cid})
        if den is not None and put("predator", rules.first_form[cid], m, mask, {"creature": cid},
                                   near=(den["i"], den["j"])) is None:
            out.remove(den)  # a den with no room for its predator beside it is no den
    return out
