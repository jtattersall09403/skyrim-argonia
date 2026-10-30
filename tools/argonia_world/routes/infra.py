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


def footprints(w) -> list[tuple[str, float, float, float]]:
    """(place id, x, y, half side) of every exterior build_ref, with the margin a signpost keeps."""
    h = FOOTPRINT_HALF_M + FOOTPRINT_MARGIN_M
    return [(r["place_id"], r["x_m"], r["y_m"], h) for r in w.query(
        "SELECT c.place_id, r.x_m, r.y_m FROM build_ref r JOIN build_cell c ON c.id = r.cell_id "
        "WHERE c.kind = 'exterior' AND coalesce(r.disabled, 0) = 0")]


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
                    "at_m": [x, y, round(max(z_at(x, y), 0.0), 2)], "yaw": round(yaw, 2), "station": s["id"]})
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
    return out


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
        want = max(z_at(x, y), 0.0) if p["kind"] == "landing" else z_at(x, y)
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
    n = {k: sum(1 for p in ps if p["kind"] == k) for k in ("gate", "landing", "signpost", "arm")}
    print(f"infra: {n['gate']} gates, {n['landing']} landings, {n['signpost']} signposts, {n['arm']} arms; "
          f"{len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
