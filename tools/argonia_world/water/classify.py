"""Water classes and their placement rules (2.W2 §a): every body, reach and spring of the hydrology graph -> one of
sea, lagoon, lake, pond, river, rapids, falls, spring, a water type (WATR) and the rule that places it.

Water types: four of ours, salt against fresh (old 60-water-traversal §40's classes; the look is tuned in game with
Community Shaders, decision 0026 §4):
  sea        the open sea and the worldspace default water (salt)
  brackish   lagoons, tidal reaches, the tidal-delta mudflats (salt-fresh mix)
  fresh      clear and white water: clearwater and whitewater rivers, lakes, tarns, ponds, pools
  black      blackwater rivers and the marsh family (tannin-dark, still)

Placement rules (how plan.py realises a class):
  default    the worldspace default water at 0 (sea; any body whose level is sea level)
  level      the body's level as a cell water height where the cell's water is one level, else placed planes
  stepped    a river's planes stepped along its grade, a vanilla rapids/falls piece at each step
  falls      no plane: the vanilla waterfall kit at the lip and mist at the plunge (old 0064)
  source     a spring: the headwater of a stepped river; no record of its own (its reach's first step starts here)
"""
from __future__ import annotations

from dataclasses import dataclass

from tools.argonia_world.water.model import Body, Graph, Junction, Reach

CLASSES = ("sea", "lagoon", "lake", "pond", "river", "rapids", "falls", "spring")
WATER_TYPES = ("sea", "brackish", "fresh", "black")
MARSH = {"marsh-fringe", "marsh-deep", "swamp", "backswamp", "mudflat"}
SEA_LEVEL_M = 0.005  # a level within this of 0 is the sea's level: the default water realises it


@dataclass(frozen=True)
class Rule:
    id: str
    cls: str
    rule: str
    water: str
    why: str


def body_rule(b: Body, lake_min_m2: float = 10000.0) -> Rule:
    sea_level = abs(b.level_m) <= SEA_LEVEL_M
    if b.kind == "ocean":
        return Rule(b.id, "sea", "default", "sea", "the open sea: the worldspace default water at 0")
    if b.kind == "lagoon":
        return Rule(b.id, "lagoon", "default" if sea_level else "level", "brackish", "brackish sea-level water")
    if b.kind in ("lake-lowland", "tarn-upland"):
        return Rule(b.id, "lake", "default" if sea_level else "level", "fresh", b.kind)
    if b.kind in ("pond", "pool", "plunge-pool"):
        return Rule(b.id, "pond", "default" if sea_level else "level", "fresh", b.kind)
    if b.kind in MARSH:
        cls = "lake" if b.area_m2 >= lake_min_m2 else "pond"
        water = "brackish" if b.kind == "mudflat" or b.altitude_band == "tidal" else "black"
        return Rule(b.id, cls, "default" if sea_level else "level", water, f"{b.kind} ({b.area_m2:.0f} m2)")
    raise ValueError(f"{b.id}: unknown body kind {b.kind!r}")


def reach_water(r: Reach) -> str:
    if r.tidal:
        return "brackish"
    return "black" if r.water == "blackwater" else "fresh"


def reach_rule(r: Reach) -> Rule:
    w = reach_water(r)
    if r.kind == "vertical-fall":
        return Rule(r.id, "falls", "falls", w, f"a {r.fall_drop_m or 0:.1f} m fall: the vanilla waterfall kit")
    if r.kind == "horizontal-backwater":
        return Rule(r.id, "river", "body", w, f"inside {r.body}: the body's water carries it")
    if r.kind in ("sloped-rapid", "sloped-chute"):
        return Rule(r.id, "rapids", "stepped", w, r.kind)
    if r.kind == "horizontal-tidal":
        return Rule(r.id, "river", "default", "brackish", "tidal: at sea level")
    return Rule(r.id, "river", "stepped", w, r.kind)


def spring_rule(j: Junction) -> Rule:
    return Rule(j.id, "spring", "source", "fresh", f"the headwater of {j.outflow}")


def classify(g: Graph) -> dict[str, list[Rule]]:
    lake_min = g.thresholds.get("lakeMinM2", 10000.0)
    return {
        "bodies": [body_rule(b, lake_min) for b in g.bodies.values()],
        "reaches": [reach_rule(r) for r in g.reaches.values()],
        "springs": [spring_rule(j) for j in g.junctions.values() if j.kind == "source"],
    }
