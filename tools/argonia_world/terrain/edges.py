"""The closed playable edge (2.W1 §b), the native way: one border region (REGN, BorderRegion flag) whose polygon
is the province's outline, so the engine itself stops the player there; and the two canon exit roads end at a
gate just inside it, where a "the road beyond is closed" activator speaks (the gate piece and the activator are
placed by 2.W3 with the road; this is their plan).

The gate positions come from the road's last place on our side, carried straight to the border: the Tear road
leaves north from Tear Road Stage, the Blackwood Road west from Gideon (both canon exits, `route` rows
`route.road.thorn-tear-road` and `route.road.gideon-blackwood-road`). They are provisional until 2.W3 lays the
roads' solved geometry, which moves each gate to where its road meets the border.
"""
from __future__ import annotations

from tools.argonia_world import skyrim_units as su

GATE_INSET_M = 20.0  # a gate stands this far inside the border on its road
EXITS = (
    # route id, the place the road last passes on our side, the border it leaves by
    ("route.road.thorn-tear-road", "place.dunmer-north.tear-road-stage", "north"),
    ("route.road.gideon-blackwood-road", "place.imperial-fringe.gideon", "west"),
)
CLOSED_MESSAGE = "The road beyond is closed."


def border_polygon() -> list[list[float]]:
    """The province outline in Skyrim units, counter-clockwise from the south-west corner."""
    x0, y0 = su.PROVINCE_CELL_SW
    span = su.PROVINCE_CELLS * su.CELL_UNITS
    ax, ay = x0 * su.CELL_UNITS, y0 * su.CELL_UNITS
    return [[float(ax), float(ay)], [float(ax + span), float(ay)], [float(ax + span), float(ay + span)],
            [float(ax), float(ay + span)]]


def gates(world) -> list[dict]:
    """The exit gates' planned positions, from the database's place rows."""
    side_m = (su.PROVINCE_SAMPLES - 1) * su.PROVINCE_SAMPLE_M
    out = []
    for route_id, place_id, side in EXITS:
        p = world.get("place", place_id)
        r = world.get("route", route_id)
        if p is None or r is None or p.position_m_x is None:
            raise KeyError(f"exit {route_id}: no route or placed {place_id} in the database")
        x, y = p.position_m_x, p.position_m_y
        if side == "north":
            y = GATE_INSET_M
        elif side == "south":
            y = side_m - GATE_INSET_M
        elif side == "west":
            x = GATE_INSET_M
        else:
            x = side_m - GATE_INSET_M
        ux, uy = su.province_to_skyrim(x, y)
        out.append({"route": route_id, "road": r.name, "from": place_id, "side": side,
                    "atM": [round(x, 2), round(y, 2)], "pos": [su.rounded(ux, 2), su.rounded(uy, 2)],
                    "cell": list(su.cell_of(ux, uy)), "message": CLOSED_MESSAGE,
                    "provisional": "until 2.W3 lays the road's solved geometry"})
    return out
