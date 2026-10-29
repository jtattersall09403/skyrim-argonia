"""What the chart draws, read from the world database (decision 0030: only through db.py) and the terrain sources
(terrain/grid.py's `Sources`, memory-mapped).

Positions in the database run x east and y SOUTH of the province's north-west corner, in metres (the mirror rule of
tools/argonia_world/intermediate.py); the terrain arrays have row 0 at the north (grid.py). So a chart pixel is
x right and y down with no flip: column = x / PROVINCE_SAMPLE_M, row = y / PROVINCE_SAMPLE_M (checked by
`checks.city_on_land`: all seven cities land on road paint this way, and Thorn lands in the sea mirrored).

    Features.load()       the real world (db.open() + Sources.load(apron=False))
    Features(...)         tests build a small synthetic one
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from tools.argonia_world import skyrim_units as su

# The seven major cities of the sketch (2.W4 §c, 1.2 §e), by place id.
CITIES = (
    "place.imperial-fringe.gideon",
    "place.mercantile-coast.soulrest",
    "place.mercantile-coast.lilmoth",
    "place.imperial-penal-south.blackrose",
    "place.saxhleel-coast.archon",
    "place.dunmer-north.stormhold",
    "place.dunmer-north.thorn",
)
# "Major" thresholds on the hydrology and the road network; the rest is drawn in the revealed layer.
MAJOR_RIVER_STRAHLER = 2  # 20 of the 101 rivers: every river of order 2 or more
MAJOR_ROAD_CLASSES = ("trunk", "road")  # 8 of the 23 legs: the built roads (surface BC_ROAD)
# Land-cover classes (terrain/landcover.py SEED): the sea, and the marsh the sketch hatches.
SEA = (33, 35)  # SEABED_SAND, OCEAN_FLOOR
MARSH = (3, 4, 5, 7, 8, 11, 15)  # SCUM, BLACK_MUD, PUDDLE, MUCK, BC_MUD, MARSH_GRASS, SWAMP_GRASS
FOREST = (10, 12, 19, 20, 21)  # MUD_LEAVES, UNDERGROWTH, JUNGLE, FOREST_FLOOR, LITTER
ROCK = (23, 31, 34, 36, 37)  # BC_ROCK, MOUNTAIN_ROCK, PEBBLES, DIRT_CLIFF, SCREE
# How wooded a cover class reads on the chart (0..1), for the tree crowns and stipple: we have no canopy raster, so
# the forest floors are full wood, peat, moss and scrub half, the grasses a scatter.
CANOPY = {c: 1.0 for c in FOREST} | {9: 0.6, 13: 0.6, 14: 0.6, 18: 0.5, 16: 0.25, 17: 0.25, 11: 0.2, 15: 0.2}


@dataclass
class Line:
    id: str
    pts: np.ndarray  # (n, 2) metres (x east, y south)
    major: bool
    weight: float  # rivers: strahler; roads: 2 trunk, 1.5 road, 1 track, 0.7 path
    cls: str = ""  # roads: the route class (trunk, road, track, footpath, boardwalk, causeway); rivers: ""


@dataclass
class Place:
    id: str
    name: str
    x_m: float
    y_m: float
    kind: str  # classification_class
    magnitude: int  # 0..5 (M5 the cities)
    city: bool


@dataclass
class Features:
    ground: np.ndarray  # (n+1)^2 metres, row 0 north
    cover: np.ndarray  # (n+1)^2 class ids
    sea_level_m: float
    rivers: list[Line]
    roads: list[Line]
    places: list[Place]
    sample_m: float = su.PROVINCE_SAMPLE_M
    cell_samples: int = su.QUADS_PER_CELL
    cell_sw: tuple[int, int] = su.PROVINCE_CELL_SW
    meta: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return self.ground.shape[0] - 1

    @property
    def span_m(self) -> float:
        return self.n * self.sample_m

    @classmethod
    def load(cls) -> Features:
        from tools.argonia_world import db
        from tools.argonia_world.terrain import grid

        w = db.open()
        src = grid.Sources.load(apron=False)
        level = w.values("SELECT level_m FROM hydrology_body WHERE kind = 'ocean'")
        rivers = []
        for r in w.query("SELECT id, strahler FROM hydrology_river ORDER BY id"):
            pts = [(p["east_m"], p["south_m"]) for p in w.query(
                "SELECT p.east_m, p.south_m FROM hydrology_river_reach rr JOIN hydrology_reach_point p "
                "ON p.reach_id = rr.reach_id WHERE rr.river_id = ? ORDER BY rr.ord, p.ord", r["id"])]
            if len(pts) >= 2:
                rivers.append(Line(r["id"], _dedup(pts), r["strahler"] >= MAJOR_RIVER_STRAHLER,
                                   float(r["strahler"])))
        weight = {"trunk": 2.0, "road": 1.5, "track": 1.0, "causeway": 1.0, "boardwalk": 0.8, "footpath": 0.7}
        roads = []
        for r in w.query("SELECT r.id, r.class FROM route r JOIN road d ON d.route_id = r.id ORDER BY r.id"):
            pts = [(p["x_m"], p["y_m"]) for p in w.query(
                "SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r["id"])]
            if len(pts) >= 2:
                roads.append(Line(r["id"], _dedup(pts), r["class"] in MAJOR_ROAD_CLASSES, weight.get(r["class"], 1.0),
                              r["class"]))
        places = []
        for r in w.query("SELECT id, name, classification_class k, classification_magnitude m, position_m_x x, "
                         "position_m_y y FROM place WHERE position_m_x IS NOT NULL ORDER BY id"):
            mag = int(r["m"][1:]) if r["m"] and r["m"][1:].isdigit() else 0
            places.append(Place(r["id"], r["name"], r["x"], r["y"], r["k"] or "lone", mag, r["id"] in CITIES))
        return cls(ground=src.ground, cover=src.cover, sea_level_m=float(level[0]) if level else 0.0,
                   rivers=rivers, roads=roads, places=places,
                   meta={"ground_shape": list(src.ground.shape)})


def _dedup(pts) -> np.ndarray:
    a = np.asarray(pts, dtype=np.float64)
    keep = np.ones(len(a), dtype=bool)
    keep[1:] = np.any(np.diff(a, axis=0) != 0, axis=1)
    return a[keep]
