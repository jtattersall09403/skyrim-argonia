"""The travel infrastructure on the ground (2.W3 §b): the two exit gates, the ferry landings and the signposts, as
placements of design pieces, written as persistent references in the worldspace's persistent cell.

That cell belongs to the WRLD override of Argonia.esm (regions/api.py). The engine places a persistent reference by
its position, so no exterior CELL of ArgoniaWorld.esm is overridden for these few pieces, and the cell layers stay the
places' (2.W5, old 0140). Every z is on the final game ground (place_build.GameGround: the regraded, place-edited
heights the LAND stores), so the L1 check holds each one within GROUND_TOL_M of it.

- **Gates** stand on their road GATE_INSET_M inside the border, at the route node `exit.*` where the traced road
  meets the edge (routes/build.py). Each is turned across the road, facing out of the province. The piece is King of
  the Murkmire's cypress palisade gate; its own record is a Door, so ours is an ACTI on the same mesh, which never
  opens. **The closed road** (lane w3-infra's choice, recorded in its report): activating the gate shows the MESG
  `ARG_Msg_RoadClosed` through a hidden player perk's Activate entry (`ARG_Perk_RoadClosed`, Run Immediately +
  Replace Default, on the keyword `ARG_ClosedGate`), the pattern of the rest and dialogue intercepts and of
  vanilla's barred doors. The player is stopped by the gate's collision and, 20 m on, by the border REGN (the
  engine's own wall at the province edge, 2.W3 §a). A trigger volume was not chosen: it needs two writer features
  we lack (a placed primitive and a script on the trigger's base) and an event script, for a message the border
  wall makes redundant as a barrier.
- **Landings**: each `ferry-landing` travel_station with a piece, at its position, facing its berth.
- **Bridges** (lane 1.15-r6-bridges): where a road crosses a water step (two cells' levels more than STEP_M
  apart, the step's channel under it), no ford can stand, so the road crosses on a bridge, Skyrim's way (0034: its
  road bridges are statics laid across the water with their ends on the banks, Bridge01 42.3 m long, the crown a
  median 5 m over the water and ~3 m over the land at its ends, so the road ramps up to it; probe in the lane
  report). The piece is King of the Murkmire's cypress scaffold bridge (`MurkmirePlatformBridge04`, 17.6 m x
  3.8 m, the widest wooden span of the stack; Stormhold's "long wooden bridges", world/sources/lore/stormhold.md
  43; never a Nordic stone bridge, 0006). The deck is level along the road's line, on the mean line of the roads it
  carries, centred where the earthwork at its two seats is least, its top at the higher bank: the last SEAT_M of each end rests on its bank, and the
  terrain pass holds the corridor there at the deck's top (`seats`, the ask to the road pass).
- **Signposts**: one per `signpost` row: the post at the node, turned to its first arm, and one arm board per
  `signpost_arm`, turned to the arm's bearing. Skyrim has no sign text but the crosshair: each arm is an ACTI of
  ours named with its destination (the place's name, or the exit's city), shown when the player looks at it, the
  way Morrowind's signs read. One ACTI per destination name, shared by every arm that reads it.

Design piece names resolve through DESIGN_PIECES (the asset registry for these few pieces), then pieces.py.

    python3 -m tools.argonia_world.routes.infra check     every placement, resolved and on the ground, or why not
"""
from __future__ import annotations

import math
import re
import sys

from tools.argonia_world import skyrim_units as su

GATE_INSET_M = 20.0  # terrain/edges.py's inset, kept
GATE_PIECE = "gate-road-closed"
CLOSED_MESSAGE = "The road beyond is closed."
GATE_NAME = "Border Gate"
GATE_VERB = "Open"
ARM_VERB = "To"  # the crosshair reads "To <destination>"
# Design piece -> mesh: the gate is King of the Murkmire's cypress palisade gate; the landing is the Tamriel Rebuilt
# style wooden dock (player-boats-as-horses.md K1, `landing-argonian`); the post and its boards are Claywater's own
# waymark (build_ref p1: the vanilla road-sign post, Black Marsh Vanilla's medium boards; decision 0012 §6).
DESIGN_PIECES = {
    GATE_PIECE: "meshes/argonia/stockades/stockadegate01.nif",
    "landing-argonian": "meshes/argonia/mudhuts/tamu_wooddock01.nif",
    "signpost": "meshes/clutter/signage/roadsigns/roadsignpost.nif",
    "signpost-arm": "meshes/roadsignmedium01r.nif",
}
# The board's arm runs along the mesh's +x (assumed from the vanilla R-board convention: the mod meshes are not on
# the build VM to measure), so an arm at bearing b is yawed b - 90. The s10 still checks that the arms point the way.
ARM_YAW_OFFSET = -90.0
ARM_TOP_M = 2.27  # Claywater's upper board stands 2.27 m up its post (old layout op 141)
ARM_STEP_M = 0.29  # half the old gap between its two boards (2.27 and 1.69 m), so five arms stay on the post
FOOTPRINT_HALF_M = 4.0  # a built ref's footprint is its square this far each way (the mesh bounds are not on this VM)
FOOTPRINT_MARGIN_M = 2.0  # and a signpost keeps this far outside it
SIGN_REACH_M = 120.0  # a place's signpost looks for road paint this near the place's node
GROUND_TOL_M = 0.5  # the ref-heights rule (f6177a7)
KEYWORD = ("ARG_ClosedGate", "hook.closed-gate")
PERK = ("ARG_Perk_RoadClosed", "hook.road-closed")  # ArgoniaCore's EnsurePerks gives it by this world id
FRAGMENT_SCRIPT = "ARG_PRKF_RoadClosed"
MESSAGE = ("ARG_Msg_RoadClosed", "message.road-closed")
GATE_ACTI = ("ARG_ACTI_BorderGate", "infra.border-gate")


# The bridge piece: King of the Murkmire's MurkmirePlatformBridge04 (stockadescaffoldbridge04.nif), its OBND read
# from the plugin (-613, -136, -80, 616, 130, 47) units: long along the mesh's +x, the deck's top 47 u over the origin.
BRIDGE_PIECE = "bridge-cypress-scaffold"
DESIGN_PIECES[BRIDGE_PIECE] = "meshes/argonia/stockades/stockadescaffoldbridge04.nif"
BRIDGE_LEN_M = su.units_to_metres(613 + 616)
BRIDGE_HALF_W_M = su.units_to_metres(136 + 130) / 2
BRIDGE_TOP_M = su.units_to_metres(47)  # the deck's top over the piece's origin
BRIDGE_YAW_OFFSET = -90.0  # the mesh's long axis is its +x: a deck along heading h is yawed h - 90
SEAT_M = 0.3  # each end's last 0.3 m rests on its bank (the lane brief)
SEAT_TOL_M = 0.3  # a bank within this of the deck's top needs no seat from the terrain pass
APPROACH_M = 4.0  # the corridor beyond each end the seat search weighs: the road meets the deck level there
STEP_M = 0.5  # routes/shape.py's step: two cells' levels further apart are a step, never a ford
# The step crossings lane 1.15-r6-roads-dry's census named (34180d72): id -> (the census point (x, y south) m, the
# step's channel, the roads that cross there, widest first: the deck lies along the first one's line).
BRIDGES = {
    "gideon-step": ((1600.0, 3041.0), "reach.878-1669",
                    ("route.road.gideon-soulrest", "route.road.gideon-stormhold")),
    "glenbridge-step": ((1871.0, 2723.0), "reach.1015-1489",
                        ("route.road.gideon-stormhold", "route.road.glenbridge-the-road-nisswo-house",
                         "route.track.north-shadowfen-rootworm-line")),
    "thorn-step": ((5581.0, 1461.0), "reach.3043-787", ("route.road.stormhold-thorn", "route.track.dres-slave-road")),
}


def nearest_on(pts, q) -> tuple[float, tuple[float, float], float]:
    """(distance, the nearest point, the heading there) of a polyline to q."""
    best = None
    for a, b in zip(pts[:-1], pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        if L2 == 0:
            continue
        t = max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / L2))
        p = (a[0] + t * dx, a[1] + t * dy)
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        if best is None or d < best[0]:
            best = (d, p, heading(a, b))
    return best


def seat(z_along, length: float = BRIDGE_LEN_M, reach: float = BRIDGE_LEN_M / 2 - 1.0, step: float = 0.25):
    """The deck's offset along the road from the crossing, its top and its two banks: ``z_along(s)`` is the ground
    s metres along the road's line. Each end's seat (SEAT_M in from the end) and APPROACH_M beyond it should stand
    at the deck's top (the higher seat's bank, so no bank is cut under a deck end); the offset (the crossing kept
    on the deck, within `reach`) is the one with the least earthwork there. -> (offset, top, (bank a, bank b))."""
    half = length / 2 - SEAT_M
    best = None
    for k in range(-int(reach / step), int(reach / step) + 1):
        c = k * step
        a, b = z_along(c - half), z_along(c + half)
        top = max(a, b)
        work = sum(abs(z_along(c - half - j) - top) + abs(z_along(c + half + j) - top)
                   for j in range(int(APPROACH_M) + 1))
        key = (round(work, 3), abs(c))
        if best is None or key < best[0]:
            best = (key, c, top, (a, b))
    return best[1], best[2], best[3]


def bridge_placements(w, z_at) -> list[dict]:
    """Every BRIDGES piece: on its first road's line at the census point, along that road, seated (seat()); its two
    ends' positions and banks, and the lift each bank needs to meet the deck."""
    out = []
    for bid, (q, reach, routes) in sorted(BRIDGES.items()):
        lines = {r: [(p["x_m"], p["y_m"]) for p in w.query(
            "SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r)] for r in routes}
        if any(len(v) < 2 for v in lines.values()):
            continue  # a road not traced: nothing to bridge
        near = [nearest_on(lines[r], q) for r in routes]
        x, y, hd = axis(near)
        ux, uy = math.sin(math.radians(hd)), -math.cos(math.radians(hd))
        c, top, banks = seat(lambda s: z_at(x + ux * s, y + uy * s))
        cx, cy = x + ux * c, y + uy * c
        half = BRIDGE_LEN_M / 2
        ends = [[round(cx - ux * half, 2), round(cy - uy * half, 2), round(top, 2)],
                [round(cx + ux * half, 2), round(cy + uy * half, 2), round(top, 2)]]
        out.append({"id": f"bridge.{bid}", "kind": "bridge", "piece": BRIDGE_PIECE,
                    "at_m": [round(cx, 2), round(cy, 2), round(top - BRIDGE_TOP_M, 2)],
                    "yaw": round((hd + BRIDGE_YAW_OFFSET) % 360, 2), "heading": round(hd, 2), "deck_m": round(top, 2),
                    "ends_m": ends, "banks_m": [round(b, 2) for b in banks],
                    "lift_m": [round(top - b, 2) for b in banks], "routes": list(routes), "reach": reach,
                    "crossing_m": [round(x, 2), round(y, 2)]})
    return out


def axis(near) -> tuple[float, float, float]:
    """The deck's centre line through several roads' crossings: their mean point, and the first road's heading
    turned by the others' mean deviation (each taken either way along, so a road traced the other way counts)."""
    h0 = near[0][2]
    dev = [((n[2] - h0 + 90) % 180) - 90 for n in near]
    return (sum(n[1][0] for n in near) / len(near), sum(n[1][1] for n in near) / len(near),
            (h0 + sum(dev) / len(dev)) % 360)


def lateral(p: dict, pt) -> tuple[float, float]:
    """(along, across) metres of a point from a bridge's centre in its deck's frame."""
    ux, uy = math.sin(math.radians(p["heading"])), -math.cos(math.radians(p["heading"]))
    dx, dy = pt[0] - p["at_m"][0], pt[1] - p["at_m"][1]
    return dx * ux + dy * uy, -dx * uy + dy * ux


def seats(w, z_at) -> list[dict]:
    """The ask to the terrain's road pass (the lane may not edit terrain/generate.py or routes/shape.py): at each
    bridge end, the corridor held at the deck's top from SEAT_M under the deck out to APPROACH_M beyond it, the
    deck's width plus the road's shoulder wide, then eased into the road's own profile at GRADE_MAX; between the two
    seats the channel is left to the water (the deck stands over it)."""
    out = []
    for p in bridge_placements(w, z_at):
        for k, e in enumerate(p["ends_m"]):
            out.append({"bridge": p["id"], "end": k, "at_m": e[:2], "z_m": p["deck_m"], "heading": p["heading"],
                        "from_m": -SEAT_M, "to_m": APPROACH_M, "half_width_m": round(BRIDGE_HALF_W_M + 2.0, 2),
                        "lift_m": p["lift_m"][k]})
    return out


def census_bridges(w, z_at) -> list[dict]:
    """The census's `bridges` entry (routes/shape.py wet_main, the planner's edit): per crossing, the bridge form,
    its roads and its ends' bank heights against the deck."""
    from tools.argonia_world.pieces import Index, Resolver
    r, _ = _mesh(Resolver(Index.load()), BRIDGE_PIECE)
    form = r.form_key if r is not None else None
    return [{"id": p["id"], "form": form, "routes": p["routes"], "at_m": p["at_m"][:2], "deck_m": p["deck_m"],
             "banks_m": p["banks_m"], "seated": all(abs(x) <= SEAT_TOL_M for x in p["lift_m"])}
            for p in bridge_placements(w, z_at)]


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


def slug(s: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[^0-9A-Za-z]+", s) if p)


def arm_texts(w) -> dict[tuple[str, int], str]:
    """(signpost id, ord) -> what the arm reads: the destination place's name, else the node's (an exit's city)."""
    return {(r["signpost_id"], r["ord"]): re.sub(r"^The ", "the ", r["text"]) for r in w.query(
        "SELECT a.signpost_id, a.ord, coalesce(p.name, n.name) text FROM signpost_arm a "
        "JOIN route_node n ON n.id = a.to_node_id LEFT JOIN place p ON p.id = n.place_id ORDER BY 1, 2")}


from tools.argonia_world.vegetation.build import PROBE_PLACE  # noqa: E402 - markers clear nothing


def footprints(w) -> list[tuple[str, float, float, float]]:
    """(place id, x, y, half side) of every exterior build_ref, with the margin a signpost keeps."""
    h = FOOTPRINT_HALF_M + FOOTPRINT_MARGIN_M
    return [(r["place_id"], r["x_m"], r["y_m"], h) for r in w.query(
        "SELECT c.place_id, r.x_m, r.y_m FROM build_ref r JOIN build_cell c ON c.id = r.cell_id "
        "WHERE c.kind = 'exterior' AND coalesce(r.disabled, 0) = 0 AND c.place_id <> ?", PROBE_PLACE)]


def in_footprint(x: float, y: float, fps, place_id: str | None = None) -> bool:
    return any((place_id is None or f[0] == place_id) and abs(x - f[1]) <= f[3] and abs(y - f[2]) <= f[3] for f in fps)


def road_edge_site(w, node: dict, fps) -> tuple[float, float, float]:
    """(x, y, yaw) of a place node's signpost: the road-paint edge sample (a road's centreline offset by half its flat
    width, every metre along it) nearest the node that is outside every footprint of the place, turned to face the
    road's centreline. The node itself when no road paint lies within SIGN_REACH_M."""
    nx, ny = node["x_m"], node["y_m"]
    best = None
    for r in w.query("SELECT route_id, flat_width_m FROM road ORDER BY route_id"):
        pts = [(p["x_m"], p["y_m"]) for p in w.query(
            "SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r["route_id"])]
        half = r["flat_width_m"] / 2
        for a, b in zip(pts[:-1], pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L == 0:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            for k in range(int(L) + 1):
                cx, cy = a[0] + ux * k, a[1] + uy * k
                if math.hypot(cx - nx, cy - ny) > SIGN_REACH_M:
                    continue
                for side in (1, -1):
                    ex, ey = cx - uy * half * side, cy + ux * half * side
                    if in_footprint(ex, ey, fps, node["place_id"]):
                        continue
                    d = math.hypot(ex - nx, ey - ny)
                    if best is None or d < best[0]:
                        best = (d, ex, ey, cx, cy)
    if best is None:
        return nx, ny, None
    _, ex, ey, cx, cy = best
    return round(ex, 2), round(ey, 2), round(heading((ex, ey), (cx, cy)), 2)


def landing_z(w, z_at, x: float, y: float) -> float:
    """A landing's deck on its cell's water (place_build.seated_z: Skyrim's dock kit over XCLW), not on the bed: the
    old max(ground, 0 m) held only at the sea, so every inland landing stood on the river bed (owner play test 3,
    finding 31)."""
    from tools.argonia_world.place_build import DOCK_DECK_M, water_level
    lv = water_level(w, x, y)
    g = z_at(x, y)
    return max(g, 0.0) if lv is None else max(g, lv) + DOCK_DECK_M


def placements(w, z_at) -> list[dict]:
    """Every gate, landing, signpost and arm: {id, kind, piece, at_m [x, y south, z], yaw, ...}. ``z_at(x, y)`` gives
    the final ground."""
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
                    "at_m": [x, y, round(landing_z(w, z_at, x, y), 2)], "yaw": round(yaw, 2), "station": s["id"]})
    texts = arm_texts(w)
    fps = footprints(w)
    for s in w.query("SELECT s.*, n.kind node_kind, n.place_id FROM signpost s JOIN route_node n ON n.id = s.node_id "
                     "ORDER BY s.id"):
        x, y, yaw = s["x_m"], s["y_m"], s["yaw_deg"]
        if s["node_kind"] == "place":  # off the place's centre, where a built place may stand
            x, y, face = road_edge_site(w, {"x_m": x, "y_m": y, "place_id": s["place_id"]}, fps)
            yaw = yaw if face is None else face
        z = round(z_at(x, y), 2)
        out.append({"id": s["id"], "kind": "signpost", "piece": "signpost", "at_m": [x, y, z],
                    "yaw": round(yaw, 2), "signpost": s["id"]})
        for a in w.query("SELECT * FROM signpost_arm WHERE signpost_id = ? ORDER BY ord", s["id"]):
            k = a["ord"]
            out.append({"id": f"{s['id']}.arm{k}", "kind": "arm", "piece": "signpost-arm",
                        "at_m": [x, y, round(z + ARM_TOP_M - ARM_STEP_M * k, 2)],
                        "yaw": round((a["bearing_deg"] + ARM_YAW_OFFSET) % 360, 2), "signpost": s["id"],
                        "text": texts.get((s["id"], k), ""), "bearing": a["bearing_deg"]})
    return out + bridge_placements(w, z_at)


def edid(p: dict) -> str:
    """A placement's reference EditorID: ARG_Ref_Gate<Road>, ARG_Ref_Landing<Station>, ARG_Ref_Sign<Node>[Arm<k>]."""
    pid = p["id"]
    if p["kind"] in ("signpost", "arm"):
        node = p["signpost"].split(".", 1)[1]
        node = node.split(".", 1)[1] if node.startswith(("place.", "road.", "track.")) else node
        s = "ARG_Ref_Sign" + slug(node) + (f"Arm{pid.rsplit('arm', 1)[1]}" if p["kind"] == "arm" else "")
    else:
        s = "ARG_Ref_" + slug(pid)
    return s[:su.EDITOR_ID_MAX]


def arm_edid(text: str) -> str:
    return ("ARG_ACTI_SignArm" + slug(text))[:su.EDITOR_ID_MAX]


def gate_records(alloc, model: str) -> list[dict]:
    """The closed road: the keyword, the gate ACTI, the message and the hidden perk that shows it on activation."""
    fk = alloc.form_key
    kw = fk(KEYWORD[0], "KYWD", KEYWORD[1])
    msg = fk(MESSAGE[0], "MESG", MESSAGE[1])
    return [
        {"type": "KYWD", "edid": KEYWORD[0], "formKey": kw},
        {"type": "MESG", "edid": MESSAGE[0], "formKey": msg, "text": CLOSED_MESSAGE, "messageBox": False},
        {"type": "ACTI", "edid": GATE_ACTI[0], "formKey": fk(GATE_ACTI[0], "ACTI", GATE_ACTI[1]), "name": GATE_NAME,
         "model": model, "keywords": [kw], "activateTextOverride": GATE_VERB},
        {"type": "PERK", "edid": PERK[0], "formKey": fk(PERK[0], "PERK", PERK[1]), "hidden": True, "playable": False,
         "trait": False, "level": 0, "ranks": 1, "name": "", "description": "",
         "effects": [{"entryPoint": "Activate", "function": "AddActivateChoice", "rank": 0, "priority": 0,
                      "tabCount": 2,
                      "conditions": [{"tab": 1, "function": "HasKeyword", "keyword": kw, "op": "EqualTo", "value": 1}],
                      "buttonLabel": GATE_VERB, "flags": ["RunImmediately", "ReplaceDefault"], "fragment": 0}],
         "fragments": {"script": FRAGMENT_SCRIPT, "entries": [{"index": 0, "name": "Fragment_0"}],
                       "properties": [{"name": "RoadClosed", "object": msg}]}},
    ]


def _mesh(resolver, piece: str):
    """(the resolution, why not) of a design piece through DESIGN_PIECES and the resolver."""
    from tools.argonia_world.pieces import Resolver
    res = Resolver(resolver.index, {**resolver.registry, **DESIGN_PIECES}, resolver.composites).resolve(piece)
    if len(res) != 1 or res[0].kind not in ("base", "new-stat"):
        return None, res[0].why if res else "no member"
    return res[0], ""


def refs(alloc, w, resolver, z_at) -> tuple[list[dict], list[dict], list[str]]:
    """(the persistent REFRs of every resolved placement, the base records they need, why each other one writes
    nothing). A gate and an arm are ACTIs of ours on their piece's mesh; a landing and a post place their piece's
    base record (or a new STAT of ours on a mesh with none)."""
    from tools.argonia_world.intermediate import _pos_exterior, _rot

    out, bases, pending = [], {}, []
    for p in placements(w, z_at):
        r, why = _mesh(resolver, p["piece"])
        if r is None:
            pending.append(f"{p['id']}: piece {p['piece']}: {why}")
            continue
        model = r.mesh[len("meshes/"):]
        if p["kind"] == "gate":
            if GATE_ACTI[0] not in bases:
                for rec in gate_records(alloc, model):
                    bases[rec["edid"]] = rec
            base = bases[GATE_ACTI[0]]["formKey"]
        elif p["kind"] == "arm":
            if not p["text"]:
                pending.append(f"{p['id']}: the arm has no text")
                continue
            e = arm_edid(p["text"])
            if e not in bases:
                bases[e] = {"type": "ACTI", "edid": e, "formKey": alloc.form_key(e, "ACTI", "infra.sign-arm." + p["text"]),
                            "name": p["text"], "model": model, "activateTextOverride": ARM_VERB}
            base = bases[e]["formKey"]
        elif r.kind == "base":
            base = r.form_key
        else:
            base = alloc.form_key(r.edid, "STAT", r.mesh)
            bases[r.edid] = {"type": "STAT", "edid": r.edid, "formKey": base, "model": model}
        e = edid(p)
        out.append({"formKey": alloc.form_key(e, "REFR", p["id"]), "edid": e, "base": base,
                    "pos": _pos_exterior(p["at_m"]), "rot": _rot(p["yaw"]), "persistent": True})
    return out, list(bases.values()), pending


def check(w, resolver, z_at) -> list[str]:
    """L1: every planned gate, landing, signpost and arm resolves; each gate, landing and post stands within
    GROUND_TOL_M of the final ground (a landing on the water when the ground is under it); every signpost has two
    or more arms and every arm has text."""
    errs = []
    ps = placements(w, z_at)
    for p in ps:
        r, why = _mesh(resolver, p["piece"])
        if r is None:
            errs.append(f"{p['id']}: piece {p['piece']} does not resolve ({why})")
        x, y, z = p["at_m"]
        if p["kind"] == "arm":
            if not p["text"].strip():
                errs.append(f"{p['id']}: the arm has no text")
            continue
        if p["kind"] == "bridge":
            errs += bridge_errors(p, w, z_at)
            continue
        want = landing_z(w, z_at, x, y) if p["kind"] == "landing" else z_at(x, y)
        if abs(z - want) > GROUND_TOL_M:
            errs.append(f"{p['id']}: z {z} m is {z - want:+.2f} m off the final ground")
    fps = footprints(w)
    for p in ps:
        if p["kind"] == "signpost" and in_footprint(p["at_m"][0], p["at_m"][1], fps):
            errs.append(f"{p['id']}: the post stands inside a built ref's footprint")
    arms: dict[str, int] = {}
    for p in ps:
        if p["kind"] == "arm":
            arms[p["signpost"]] = arms.get(p["signpost"], 0) + 1
    for s in w.values("SELECT id FROM signpost"):
        if arms.get(s, 0) < 2:
            errs.append(f"{s}: {arms.get(s, 0)} arms")
    kinds = {k: sum(1 for p in ps if p["kind"] == k) for k in ("gate", "landing", "signpost", "arm")}
    if kinds["gate"] != len(w.values("SELECT id FROM route_node WHERE kind = 'exit'")):
        errs.append(f"{kinds['gate']} gates for the exit nodes")
    return errs


def bridge_errors(p: dict, w, z_at) -> list[str]:
    """L1 for one bridge: every road it carries crosses the deck inside its width (the road line at the crossing,
    within BRIDGE_HALF_W_M across the deck's axis, inside its length), the deck's top at the higher bank, and the
    channel under it below the deck (it spans water). The banks' lift is the terrain's seat, not an error here."""
    errs = []
    for r in p["routes"]:
        pts = [(q["x_m"], q["y_m"]) for q in w.query("SELECT x_m, y_m FROM road_point WHERE route_id = ? ORDER BY ord", r)]
        _, q, _ = nearest_on(pts, p["crossing_m"])
        al, ac = lateral(p, q)
        if abs(ac) > BRIDGE_HALF_W_M or abs(al) > BRIDGE_LEN_M / 2 - SEAT_M:
            errs.append(f"{p['id']}: {r} crosses {ac:+.1f} m across, {al:+.1f} m along the deck")
    if abs(p["deck_m"] - max(p["banks_m"])) > 0.01 or min(p["lift_m"]) < -0.01:
        errs.append(f"{p['id']}: deck {p['deck_m']} m not at the higher bank {p['banks_m']}")
    under = min(z_at(p["at_m"][0] + (e[0] - p["at_m"][0]) * t, p["at_m"][1] + (e[1] - p["at_m"][1]) * t)
                for e in p["ends_m"] for t in (0.0, 0.25, 0.5, 0.75))
    if under >= p["deck_m"] - BRIDGE_TOP_M:
        errs.append(f"{p['id']}: no gap under the deck (lowest ground {under:.2f} m)")
    return errs


def main(argv: list[str]) -> int:
    from tools.argonia_world import db
    from tools.argonia_world.pieces import Index, Resolver
    from tools.argonia_world.place_build import GameGround

    w = db.open()
    g = GameGround()
    res = Resolver(Index.load())
    ps = placements(w, g.z)
    for p in ps:
        if p["kind"] == "arm":
            continue
        r, why = _mesh(res, p["piece"])
        ux, uy = su.province_to_skyrim(p["at_m"][0], p["at_m"][1])
        print(f"{p['id']}: {p['piece']} at {p['at_m']} cell {su.cell_of(ux, uy)} yaw {p['yaw']}: "
              f"{'resolved ' + (r.form_key or r.mesh) if r else 'pending (' + why + ')'}")
    errs = check(w, res, g.z)
    for e in errs:
        print("infra:", e)
    for p in ps:
        if p["kind"] == "bridge":
            print(f"{p['id']}: deck {p['deck_m']} m, banks {p['banks_m']}, lift {p['lift_m']}, ends {p['ends_m']}")
    n = {k: sum(1 for p in ps if p["kind"] == k) for k in ("gate", "landing", "signpost", "arm", "bridge")}
    print(f"infra: {n['gate']} gates, {n['landing']} landings, {n['signpost']} signposts, {n['arm']} arms, "
          f"{n['bridge']} bridges; {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
