"""The travel infrastructure on the ground (2.W3 §b): the two exit gates and the ferry landings, as placements of
design pieces, written as persistent references in the worldspace's persistent cell.

That cell belongs to the WRLD override of Argonia.esm (regions/api.py). The engine places a persistent reference by
its position, so no exterior CELL of ArgoniaWorld.esm is overridden for these few pieces, and the cell layers stay the
places' (2.W5, old 0140).

- **Gates** stand on their road GATE_INSET_M inside the border, at the route node `exit.*` where the traced road
  meets the edge (routes/build.py; this supersedes terrain/edges.py's provisional gates). Each one is turned across
  the road, facing out of the province. The piece is chosen at review: the old gates were vanilla Whiterun stone, a
  Nordic tell (decision 0012).
- **Landings**: each `ferry-landing` travel_station with a piece, at its position, facing its berth. Root nodes and
  place stations belong to their places (2.W5).

A placement whose piece does not resolve yet (the Black Marsh dependency plugins are not synced to the build VM's
Data) writes no reference. `check` lists those placements, and so does the report.

    python3 -m tools.argonia_world.routes.infra check     every placement, resolved or why not
"""
from __future__ import annotations

import math
import sys

from tools.argonia_world import skyrim_units as su

GATE_INSET_M = 20.0  # terrain/edges.py's inset, kept
GATE_PIECE = "gate-road-closed"  # a design piece name; the kit piece is chosen at review (decision 0012)
CLOSED_MESSAGE = "The road beyond is closed."


def walk_back(pts: list[tuple[float, float]], dist: float) -> tuple[tuple[float, float], float]:
    """The point `dist` metres back from a polyline's end along it, and the heading (degrees clockwise from north,
    north = -y in the province frame) of travel towards the end there."""
    left = dist
    for a, b in zip(reversed(pts[:-1]), reversed(pts[1:])):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L >= left or a == pts[0]:
            t = 1 - min(left / L, 1) if L else 0
            q = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            return q, heading(a, b)
        left -= L
    return pts[-1], heading(pts[-2], pts[-1])


def heading(a, b) -> float:
    """Degrees clockwise from north from a to b, in province metres (x east, y south)."""
    return math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1]))) % 360


def placements(w, z_at) -> list[dict]:
    """Every gate and landing: {id, kind, piece, at_m [x, y south, z], yaw}. ``z_at(x, y)`` gives the ground."""
    out = []
    for e in w.query("SELECT e.route_id, e.to_node_id FROM route_edge e WHERE e.to_node_id LIKE 'exit.%' AND "
                     "e.mode = 'road' ORDER BY e.to_node_id"):
        pts = [(p["x_m"], p["y_m"]) for p in w.query("SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord",
                                                     e["route_id"])]
        (x, y), yaw = walk_back(pts, GATE_INSET_M)
        out.append({"id": "gate." + e["to_node_id"].split(".", 1)[1], "kind": "gate", "piece": GATE_PIECE,
                    "at_m": [round(x, 2), round(y, 2), round(z_at(x, y), 2)], "yaw": round(yaw, 2),
                    "route": e["route_id"], "message": CLOSED_MESSAGE})
    for s in w.query("SELECT * FROM travel_station WHERE kind = 'ferry-landing' AND piece IS NOT NULL ORDER BY id"):
        x, y = s["position_m_x"], s["position_m_y"]
        b = w.query("SELECT position_m_x x, position_m_y y FROM travel_station_berth WHERE travel_station_id = ? "
                    "ORDER BY position_m_x, position_m_y", s["id"])
        yaw = heading((x, y), (b[0]["x"], b[0]["y"])) if b and (b[0]["x"], b[0]["y"]) != (x, y) else 0.0
        out.append({"id": "landing." + s["id"].split(".", 1)[1], "kind": "landing", "piece": s["piece"],
                    "at_m": [x, y, round(max(z_at(x, y), 0.0), 2)], "yaw": round(yaw, 2), "station": s["id"]})
    return out


def edid(pid: str) -> str:
    return "ARG_" + "".join(c if c.isalnum() else "_" for c in pid.title().replace(".", "_"))[:60]


def refs(alloc, w, resolver, z_at) -> tuple[list[dict], list[dict], list[str]]:
    """(the persistent REFRs of every resolved placement, the STATs new meshes need, why each other one writes
    nothing). A piece resolves to one base record or one mesh; a composite piece is a place's business (2.W5)."""
    from tools.argonia_world.intermediate import _pos_exterior, _rot

    out, stats, pending = [], {}, []
    for p in placements(w, z_at):
        res = resolver.resolve(p["piece"])
        if len(res) != 1 or res[0].kind not in ("base", "new-stat"):
            pending.append(f"{p['id']}: piece {p['piece']}: {res[0].why if res else 'no member'}")
            continue
        r = res[0]
        base = r.form_key
        if r.kind == "new-stat":
            base = alloc.form_key(r.edid, "STAT", r.mesh)
            stats[base] = {"type": "STAT", "edid": r.edid, "formKey": base, "model": r.mesh}
        e = edid(p["id"])
        out.append({"formKey": alloc.form_key(e, "REFR", p["id"]), "edid": e, "base": base,
                    "pos": _pos_exterior(p["at_m"]), "rot": _rot(p["yaw"]), "persistent": True})
    return out, list(stats.values()), pending


def main(argv: list[str]) -> int:
    from tools.argonia_world import db
    from tools.argonia_world.pieces import Index, Resolver
    from tools.argonia_world.routes.build import Ground

    w = db.open()
    g = Ground()
    res = Resolver(Index.load())
    for p in placements(w, g.z):
        r = res.resolve(p["piece"])
        ok = len(r) == 1 and r[0].kind in ("base", "new-stat")
        ux, uy = su.province_to_skyrim(p["at_m"][0], p["at_m"][1])
        print(f"{p['id']}: {p['piece']} at {p['at_m']} cell {su.cell_of(ux, uy)} yaw {p['yaw']}: "
              f"{'resolved ' + (r[0].form_key or r[0].mesh) if ok else 'pending (' + (r[0].why if r else 'no member') + ')'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
