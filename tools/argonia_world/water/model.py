"""The hydrology graph as the water plan reads it, from the world database (db.py only; decision 0030).

Plain dataclasses, no numpy: the classification and the step plan are pure functions of these rows, so their tests
run on small hand-made graphs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Body:
    id: str
    kind: str
    origin: str
    level_m: float
    area_m2: float
    altitude_band: str
    region: int | None
    deepest: tuple[int, int] | None  # (x, y) full-res sample, y south
    bbox: tuple[int, int, int, int] | None  # x0, y0, x1, y1 inclusive
    caused_by_fall: str | None = None
    realised_by: str | None = None
    lost_at_carve: bool = False


@dataclass(frozen=True)
class Reach:
    id: str
    river: str | None
    kind: str
    surface: str
    water: str  # whitewater | blackwater | clearwater
    width_m: float
    depth_m: float
    length_m: float
    level_from_m: float
    level_to_m: float
    speed_ms: float
    tidal: bool
    body: str | None
    downstream: str | None
    fall_drop_m: float | None
    fall_plunge_body: str | None
    points: tuple[tuple[float, float], ...] = field(default=(), repr=False)  # (east, south) metres


@dataclass(frozen=True)
class Junction:
    id: str
    kind: str
    east_m: float
    south_m: float
    level_m: float
    outflow: str | None


@dataclass
class Graph:
    bodies: dict[str, Body]
    reaches: dict[str, Reach]
    junctions: dict[str, Junction]
    rivers: dict[str, list[str]]  # river id -> reach ids headwater to mouth
    river_water: dict[str, str]
    thresholds: dict


def load(world=None) -> Graph:
    from tools.argonia_world import db
    w = world if world is not None else db.open()
    bodies = {}
    for r in w.rows("hydrology_body"):
        bodies[r.id] = Body(
            r.id, r.kind, r.origin, r.level_m, r.area_m2 or 0.0, r.altitude_band, r.region,
            (r.deepest_x, r.deepest_y) if r.deepest_x is not None else None,
            (r.bbox_x0, r.bbox_y0, r.bbox_x1, r.bbox_y1) if r.bbox_x0 is not None else None,
            r.caused_by_fall_reach_id, r.realised_by, bool(r.lost_at_carve))
    pts: dict[str, list[tuple[float, float]]] = {}
    for p in w.rows("hydrology_reach_point"):
        pts.setdefault(p.reach_id, []).append((p.east_m, p.south_m))
    reaches = {}
    for r in w.rows("hydrology_reach"):
        reaches[r.id] = Reach(
            r.id, r.river_id, r.kind, r.surface, r.water, r.width_m, r.depth_m, r.length_m, r.level_from_m,
            r.level_to_m, r.speed_ms, bool(r.tidal), r.body_id, r.downstream_reach_id, r.fall_drop_m,
            r.fall_plunge_body_id, tuple(pts.get(r.id, ())))
    junctions = {r.id: Junction(r.id, r.kind, r.east_m, r.south_m, r.level_m, r.outflow_reach_id)
                 for r in w.rows("hydrology_junction")}
    rivers: dict[str, list[str]] = {}
    for r in w.rows("hydrology_river_reach"):
        rivers.setdefault(r.river_id, []).append(r.reach_id)
    river_water = {r.id: r.water for r in w.rows("hydrology_river")}
    th = w.get("hydrology_setting", "thresholds")
    return Graph(bodies, reaches, junctions, rivers, river_water, json.loads(th.value) if th else {})
