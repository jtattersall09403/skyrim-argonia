"""The studio fixtures (0.4 §d, decision 0022 §6, 0.3 §c): the proving ground and the booth, two interior cells that
no load door from the game world leads to (CantTravelFromHere; reached only by `coc ARG_ProvingGround` and the
scenes). Every piece is a base record resolved from a vanilla mesh path (no new art); positions are written in
metres here and converted only by skyrim_units.

Frame: metres from the cell origin, x east, y south (_pos_interior negates it), z up; the arena floor top is z = 0.

The proving ground's stations (each an `ARG_PG_<Station>Marker`, an XMarkerHeading, persistent, so a scene can
`player.moveto` it): Start; WallRock/WallMasonry/WallTimber x Dry/Wet; Ladder; DoorA, DoorB; WaterAnkle,
WaterWaist, WaterSwim, WaterDeep; DuelPlayer, DuelOpponent, DuelFar.

Owed, measured at L4 (nothing here is measured yet): the real width of each wall and floor piece (TILE_M, WALL_PIECE_M
are the planned pitch), the wall pieces' facing, the ladder piece's hatch (the mesh edit of ladders.md is the
install-time patcher's), and the wet state of the walls: there is no placeable wet-surface record, so each "Wet"
wall is the dry piece placed again beside the dry one, marked by its `...WetMarker`; wetness is owed.
"""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su
from tools.argonia_world.formids import Allocator
from tools.argonia_world.intermediate import Layer, _pos_interior, _rot
from tools.argonia_world.pieces import Resolver
from tools.argonia_world.water.layer import type_key

PROVING_GROUND = "ARG_ProvingGround"
BOOTH = "ARG_Booth"
BOOTH_MARKER = "ARG_BoothMarker"

FLOOR = "meshes/dungeons/imperial/clutterkits/impfloormid01.nif"
WALL = {  # climb class -> a simple vanilla piece with collision
    "Rock": "meshes/dungeons/mines/caveepicwall/minecewallstraight01.nif",
    "Masonry": "meshes/architecture/solitude/scastlewall01.nif",
    "Timber": "meshes/architecture/whiterun/wrcitywalls/wrwallstr01stockades01.nif",
}
DOOR = "meshes/dungeons/imperial/door/impwooddoorsingle01.nif"
LADDER = "meshes/dungeons/imperial/door/trapdoorladder01.nif"
BACKDROP = "meshes/architecture/solitude/scastlewall01.nif"

TILE_M = 7.0   # planned floor pitch (unmeasured; see the module note)
WALL_PIECES = 3  # pieces per wall section
WALL_PIECE_M = 2.5  # planned pitch of one wall piece
WALL_Z = 0.0
LADDER_RISE_M = 5.45  # ladders.md: the deck top over the piece's pivot
WATER_LEVEL_M = -0.05  # interior water surface, just under the arena floor top
POOLS = (("Ankle", 0.3), ("Waist", 1.0), ("Swim", 2.0), ("Deep", 4.0))  # name, depth under the water surface
RING_RADIUS_M = 6.0  # the duel ring is ~12 m across
CELL_NAME = {PROVING_GROUND: "Proving Ground", BOOTH: "Booth"}
LIGHT = {"ambient": [200, 200, 200], "directional": [160, 160, 160], "fogNear": [200, 200, 200],
         "fogFar": [200, 200, 200], "fogNearDistance": 20000.0, "fogFarDistance": 40000.0,
         "fogClipDistance": 40000.0, "fogPower": 1.0, "fadeBegin": 4000.0, "fadeEnd": 8000.0}

# station -> (x, y, yaw): the ground's map. Walls stand across the south edge, one section per station.
WALL_Y = 24.0
STATIONS: dict[str, tuple[float, float, float]] = {"Start": (0.0, 0.0, 0.0)}
for _i, _cls in enumerate(WALL):
    for _j, _state in enumerate(("Dry", "Wet")):
        STATIONS[f"Wall{_cls}{_state}"] = (-27.0 + 9.0 * (2 * _i + _j), WALL_Y - 4.0, 180.0)
STATIONS.update({
    "Ladder": (-28.0, 8.0, 90.0),
    "DoorA": (-12.0, -8.0, 0.0), "DoorB": (-4.0, -8.0, 0.0),
    "WaterAnkle": (10.5, -3.5, 270.0), "WaterWaist": (10.5, 3.5, 270.0),  # arena tile centres
    "WaterSwim": (17.5, -3.5, 270.0), "WaterDeep": (17.5, 3.5, 270.0),
    "DuelPlayer": (0.0, -31.0, 0.0), "DuelOpponent": (0.0, -41.0, 180.0), "DuelFar": (0.0, -26.0, 0.0),  # Far: 15 m
})
DUEL_CENTRE = (0.0, -36.0)
GROUND_HALF = 28.0  # the arena floor spans +-28 m


def marker_edid(station: str) -> str:
    return f"ARG_PG_{station}Marker"


class _Build:
    def __init__(self, alloc: Allocator, resolver: Resolver):
        self.alloc, self.resolver = alloc, resolver
        self.records: list[dict] = []
        self.refs: list[dict] = []
        self._bases: dict[str, str] = {}

    def base(self, mesh: str) -> str:
        if mesh in self._bases:
            return self._bases[mesh]
        res = self.resolver.resolve(mesh)
        if len(res) != 1 or res[0].kind == "unresolved":
            raise ValueError(f"fixture piece {mesh}: {res[0].why if res else 'no member'}")
        r = res[0]
        key = r.form_key
        if r.kind == "new-stat":
            key = self.alloc.form_key(r.edid, "STAT", r.mesh)
            self.records.append({"type": "STAT", "edid": r.edid, "formKey": key, "model": r.mesh})
        self._bases[mesh] = key
        return key

    def place(self, edid: str, mesh: str, at_m, yaw: float = 0.0, **extra) -> dict:
        ref = {"edid": edid, "formKey": self.alloc.form_key(edid, "REFR"), "base": self.base(mesh),
               "pos": _pos_interior(at_m), "rot": _rot(yaw), **extra}
        self.refs.append(ref)
        return ref

    def marker(self, edid: str, x: float, y: float, yaw: float, z: float = 0.0) -> dict:
        ref = {"edid": edid, "formKey": self.alloc.form_key(edid, "REFR"), "base": su.ENGINE_MARKER_HEADING,
               "pos": _pos_interior((x, y, z)), "rot": _rot(yaw), "persistent": True}
        self.refs.append(ref)
        return ref


def _tiles(centre, half_x, half_y):
    nx, ny = round(2 * half_x / TILE_M), round(2 * half_y / TILE_M)
    for i in range(nx):
        for j in range(ny):
            yield centre[0] - half_x + (i + 0.5) * TILE_M, centre[1] - half_y + (j + 0.5) * TILE_M


def _in_pool(x, y):
    return 10.0 < x < 19.0 and -7.0 < y < 7.0


def _in_ring(x, y):
    return (x - DUEL_CENTRE[0]) ** 2 + (y - DUEL_CENTRE[1]) ** 2 <= (RING_RADIUS_M + TILE_M / 2) ** 2


def _cell(b: _Build, edid: str, flags, extra=None) -> dict:
    return {"type": "CELL", "edid": edid, "formKey": b.alloc.form_key(edid, "CELL"), "name": CELL_NAME[edid],
            "flags": flags, "lighting": dict(LIGHT), "refs": b.refs, **(extra or {})}


def proving_ground(alloc: Allocator, resolver: Resolver) -> list[dict]:
    b = _Build(alloc, resolver)
    n = 0
    # The arena floor, with the water pools left open; the ring's floor extends north of the arena.
    for x, y in [*_tiles((0, 0), GROUND_HALF, GROUND_HALF), *_tiles((0, -42.0), 14.0, 14.0)]:
        if _in_pool(x, y) or (y < -GROUND_HALF and not _in_ring(x, y)):
            continue
        b.place(f"ARG_PG_Floor{n:03d}", FLOOR, (x, y, 0.0))
        n += 1
    for name, depth in POOLS:  # each pool's floor under the water: depth below WATER_LEVEL_M
        sx, sy, _ = STATIONS[f"Water{name}"]
        b.place(f"ARG_PG_Pool{name}Floor", FLOOR, (sx, sy, WATER_LEVEL_M - depth))
    # Walls: WALL_PIECES pieces per section, one section per class and state.
    for cls, mesh in WALL.items():
        for state in ("Dry", "Wet"):
            sx, sy, yaw = STATIONS[f"Wall{cls}{state}"]
            for k in range(WALL_PIECES):
                off = (k - (WALL_PIECES - 1) / 2) * WALL_PIECE_M
                b.place(f"ARG_PG_Wall{cls}{state}{k}", mesh, (sx + off, WALL_Y, WALL_Z), yaw)
    # The ladder and the deck at its top.
    lx, ly, lyaw = STATIONS["Ladder"]
    b.place("ARG_PG_Ladder", LADDER, (lx, ly, 0.0), lyaw)
    for k in range(2):
        b.place(f"ARG_PG_LadderDeck{k}", FLOOR, (lx - TILE_M * (k + 0.5), ly, LADDER_RISE_M))
    # Doors, each teleporting to a marker in front of its partner.
    ax, ay, _ = STATIONS["DoorA"]
    bx, by, _ = STATIONS["DoorB"]
    ka, kb = alloc.form_key("ARG_PG_DoorA", "REFR"), alloc.form_key("ARG_PG_DoorB", "REFR")
    for edid, (x, y), (px, py), partner in (("ARG_PG_DoorA", (ax, ay), (bx, by), kb),
                                            ("ARG_PG_DoorB", (bx, by), (ax, ay), ka)):
        b.place(edid, DOOR, (x, y, 0.0), 0.0,
                teleport={"door": partner, "pos": _pos_interior((px, py + 1.5, 0.0)), "rot": _rot(180.0)})
    for station, (x, y, yaw) in STATIONS.items():
        b.marker(marker_edid(station), x, y, yaw)
    water = type_key("fresh")
    cell = _cell(b, PROVING_GROUND, ["IsInteriorCell", "CantTravelFromHere", "HasWater"],
                 {"water": water, "waterHeight": su.rounded(su.metres_to_units(WATER_LEVEL_M), 2)})
    return [*b.records, cell]


def booth(alloc: Allocator, resolver: Resolver) -> list[dict]:
    b = _Build(alloc, resolver)
    for i, (x, y) in enumerate(_tiles((0, 0), TILE_M, TILE_M)):
        b.place(f"ARG_Booth_Floor{i}", FLOOR, (x, y, 0.0))
    for k in range(3):
        b.place(f"ARG_Booth_Backdrop{k}", BACKDROP, ((k - 1) * WALL_PIECE_M, TILE_M, 0.0), 180.0)
    b.marker(BOOTH_MARKER, 0.0, 0.0, 0.0)
    return [*b.records, _cell(b, BOOTH, ["IsInteriorCell", "CantTravelFromHere"])]


def layer(alloc: Allocator, resolver: Resolver) -> Layer:
    return Layer("place:fixtures", [*proving_ground(alloc, resolver), *booth(alloc, resolver)])
