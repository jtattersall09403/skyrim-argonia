"""Rotation on all three axes: turn_rot and tilt_rot (tools/places/xform.py), carried through the edit ops, the
agent's tilt/roll hands, and the plugin's own rotation (tools.navmesh.placed.rotation, which the build uses)."""
import copy
import json
import math
import random
from pathlib import Path

import numpy as np

from tools.navmesh.placed import rotation as plugin_rotation
from tools.places import xform
from tools.places.edits import apply

PLACE = json.loads((Path(__file__).parent / "places_edits" / "place.json").read_text())


def M(rot):
    return np.array(xform.rotation(rot))


def test_turn_of_a_level_piece_only_adds_to_its_heading():
    assert xform.turn_rot([0.0, 0.0, 1.0], 0.5) == [0.0, 0.0, 1.5]


def test_turn_and_tilt_compose_in_the_games_convention():
    rnd = random.Random(7)
    for _ in range(200):
        rot = [rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-3, 3)]
        a = rnd.uniform(-3, 3)
        rz = np.array(xform._rz(-a))
        assert np.allclose(M(xform.turn_rot(rot, a)), rz @ M(rot), atol=1e-9)
        assert np.allclose(M(xform.tilt_rot(rot, 0, a)), M(rot) @ np.array(xform._rx(-a)), atol=1e-9)
        assert np.allclose(M(xform.tilt_rot(rot, 1, a)), M(rot) @ np.array(xform._ry(-a)), atol=1e-9)
        # the studio's matrix and the plugin's are the same matrix (no transposed rotation anywhere)
        assert np.allclose(M(rot), plugin_rotation(*rot), atol=1e-9)


def test_a_tilted_plank_lands_on_both_decks():
    """A scratch scene: a ship's deck at z 420 to the north-east, the dock's at z 300; a 300-unit plank (its top face
    4 units over its origin, its length along its own Y) is turned to face the ship, tilted by the studio's op and
    built: each end lands within 5 cm (3.5 units) of its deck."""
    L, top = 300.0, 4.0
    ship_deck, dock_deck = 420.0, 300.0
    yaw = 0.7                              # faces the ship
    pitch = -math.asin((ship_deck - dock_deck) / L)   # front (+Y, the ship's) end up
    rot = xform.tilt_rot([0.0, 0.0, yaw], 0, pitch)
    mid_z = (ship_deck + dock_deck) / 2 - top * math.cos(pitch)
    files = copy.deepcopy(PLACE)
    plank = {"base": "Skyrim.esm:0A1B2C", "id": "fix.plank", "kind": "static", "layer": "place", "pos": [0.0, 0.0, 0.0],
             "rot": [0.0, 0.0, yaw], "scale": 1.0}
    files["spaces"]["exterior"]["refs"].append(plank)
    before = {k: plank[k] for k in ("pos", "rot", "scale")}
    after = {"pos": [500.0, 600.0, round(mid_z, 3)], "rot": [round(v, 5) for v in rot], "scale": 1.0}
    out = apply(files, [{"n": 1, "op": "ref.move", "space": "exterior", "id": "fix.plank", "before": before, "after": after}])
    row = next(r for r in out["spaces"]["exterior"]["refs"] if r["id"] == "fix.plank")
    R = plugin_rotation(*row["rot"])
    ends = [np.array(row["pos"]) + R @ np.array([0.0, s * L / 2, top]) for s in (1, -1)]
    assert abs(ends[0][2] - ship_deck) < 3.5 and abs(ends[1][2] - dock_deck) < 3.5
    # and it still faces the ship in plan
    d = ends[0] - ends[1]
    assert abs(math.atan2(d[0], d[1]) - yaw) < 1e-3


def test_a_place_without_tilt_reads_unchanged():
    """Ops without tilt give the very rows they gave before: a level turn is the plain sum on Z."""
    files = copy.deepcopy(PLACE)
    r = files["spaces"]["exterior"]["refs"][0]
    before = {"pos": r["pos"], "rot": r["rot"], "scale": 1.0, "seat": r["seat"]}
    after = dict(copy.deepcopy(before), rot=[0, 0, 1.6])
    out = apply(files, [{"n": 1, "op": "ref.move", "space": "exterior", "id": r["id"], "before": before, "after": after}])
    assert json.dumps(next(x for x in out["spaces"]["exterior"]["refs"] if x["id"] == r["id"])["rot"]) == "[0, 0, 1.6]"
