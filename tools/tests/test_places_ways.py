"""Every walk of a place is clear (tools/places/ways.py): a solid thing in a way's corridor between a step and a
head's height fails, unless a reason says it is meant to stand there; a thing stepped over, walked under or beside the
way passes; a creature's spot on the way fails; a deck the way runs over is walked on, never a blocker."""
from __future__ import annotations

import numpy as np

from tools.places import shape, ways, xform

shape.register("test/ways/crate.nif", np.array(shape.box_tris([-40, -40, 0], [40, 40, 80])).reshape(-1, 3),
               np.arange(36))
shape.register("test/ways/arch.nif", np.array(shape.box_tris([-200, -40, 200], [200, 40, 260])).reshape(-1, 3),
               np.arange(36))
shape.register("test/ways/rug.nif", np.array(shape.box_tris([-60, -60, 0], [60, 60, 8])).reshape(-1, 3), np.arange(36))
shape.register("test/ways/deck.nif", np.array(shape.box_tris([-150, -120, 80], [150, 120, 100])).reshape(-1, 3),
               np.arange(36))


class Flat:
    def height(self, x, y):
        return 0.0

    def water(self, x, y):
        return None


def piece(i, model, x, y, z=0.0, edid=None, kind="static"):
    lo, hi = {"test/ways/crate.nif": ([-40, -40, 0], [40, 40, 80]), "test/ways/arch.nif": ([-200, -40, 200], [200, 40, 260]),
              "test/ways/rug.nif": ([-60, -60, 0], [60, 60, 8]), "test/ways/deck.nif": ([-150, -120, 80], [150, 120, 100])}[model]
    return {"id": i, "base": "t:" + i, "kind": kind, "edid": edid or i, "model": model, "resolved": True,
            "m": xform.matrix([x, y, z], [0, 0, 0], 1.0), "lo": lo, "hi": hi}


def files(refs=(), paths=None, quests=()):
    return {"spaces": {"exterior": {"refs": list(refs)}},
            "paths": paths if paths is not None else [{"id": "p.1", "width": 160, "points": [[0, 0], [2000, 0]]}],
            "quests": list(quests), "people": []}


def ids(bl):
    return sorted(b["id"] for b in bl if not b.get("reason"))


def test_a_crate_in_the_way_fails_beside_it_passes():
    ps = [piece("in", "test/ways/crate.nif", 500, 30), piece("beside", "test/ways/crate.nif", 500, 300)]
    assert ids(ways.blockers(files(), ps, Flat())) == ["in"]


def test_stepped_over_and_walked_under_pass():
    ps = [piece("rug", "test/ways/rug.nif", 700, 0), piece("arch", "test/ways/arch.nif", 900, 0)]
    assert ids(ways.blockers(files(), ps, Flat())) == []


def test_a_deck_the_way_runs_over_is_walked_on():
    deck = piece("deck", "test/ways/deck.nif", 1200, 0, edid="DockDeck01", kind="building")
    deck["model"] = "test/ways/deck.nif"
    # a deck rising 100 over the ground is more than a climb: a way onto it from the ground meets its edge
    assert "deck" in ids(ways.blockers(files(), [deck], Flat()))
    # the walked mesh says the line is on the deck there: the deck is walked on, not in the way
    walked = lambda S: [100.0 if 980 <= q[0] <= 1420 else 0.0 for q in S]   # noqa: E731  (its ramps beyond its ends)
    assert ids(ways.blockers(files(), [deck], Flat(), walked=walked)) == []


def test_a_reason_on_the_ref_or_the_way_lets_it_stand():
    crate = piece("gate", "test/ways/crate.nif", 500, 0)
    ref = {"id": "gate", "blocks_way": "a toll gate meant to stop traffic on the road"}
    assert ids(ways.blockers(files([ref]), [crate], Flat())) == []
    short = {"id": "gate", "blocks_way": "on purpose"}
    assert ids(ways.blockers(files([short]), [crate], Flat())) == ["gate"]
    p = [{"id": "p.1", "width": 160, "points": [[0, 0], [2000, 0]],
          "blocked_by": {"gate": "a barricade the quest clears when the bandits are gone"}}]
    assert ids(ways.blockers(files(paths=p), [crate], Flat())) == []


def test_lights_markers_plants_and_effects_never_block():
    ps = [dict(piece(k, "test/ways/crate.nif", 400 + 100 * n, 0), kind=k) for n, k in enumerate(("light", "marker", "plant"))]
    ps.append(dict(piece("mist", "test/ways/crate.nif", 800, 0), edid="FXMistLow01"))
    ps.append(dict(piece("door", "test/ways/crate.nif", 900, 0), kind="door"))
    assert ids(ways.blockers(files(), ps, Flat())) == []


def test_a_creature_spot_on_the_way_fails():
    q = [{"id": "quest.x/npc.x.mudcrab", "ref": "npc.x.mudcrab", "space": "exterior", "pos": [600, 20, 0]},
         {"id": "quest.x/npc.x.croc", "ref": "npc.x.croc", "space": "exterior", "pos": [600, 600, 0]}]
    f = files(quests=q)
    assert ids(ways.blockers(f, [], Flat(), ways.spots(f))) == ["quest.x/npc.x.mudcrab"]


def test_a_door_way_runs_from_its_arrival_to_the_nearest_walk():
    f = files([{"id": "out.door", "kind": "door", "pos": [500, 900, 0]}])
    f["spaces"]["room"] = {"refs": [{"id": "in.door", "door": {"to_ref": "out.door", "to_pos": [500, 800, 0]}}]}
    w = [w for w in ways.ways(f) if w["id"] == "door out.door"]
    assert w and w[0]["points"] == [[500, 800], [500.0, 0.0]]
    assert ids(ways.blockers(f, [piece("box", "test/ways/crate.nif", 500, 400)], Flat())) == ["box"]
