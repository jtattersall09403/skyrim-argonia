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
    # the built mesh runs onto the deck there (ramps beyond its ends): the deck is walked on, not in the way
    assert ids(ways.blockers(files(), [deck], Flat(), mesh=Mesh(lambda x, y: [100.0] if 980 <= x <= 1420 else [0.0]))) == []


class Mesh:
    """A stand-in built walking mesh: its heights under a point."""
    def __init__(self, f):
        self.f = f

    def heights(self, x, y):
        return self.f(x, y)


def test_a_thing_past_the_meshes_edge_is_the_walks_edge_not_a_blocker():
    # the mesh is 60 wide along the way: a fence 30 off the middle (past the mesh) is its edge; on the mesh it blocks
    fence = piece("fence", "test/ways/crate.nif", 600, 75)
    on = piece("crate", "test/ways/crate.nif", 900, 10)
    mesh = Mesh(lambda x, y: [0.0] if abs(y) <= 30 else [])
    assert ids(ways.blockers(files(), [fence, on], Flat(), mesh=mesh)) == ["crate"]
    assert ids(ways.blockers(files(), [fence, on], Flat())) == ["crate", "fence"]   # without the mesh: the width alone


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


def test_the_time_log_is_not_a_change_the_pictures_miss(tmp_path):
    """The look daemon warns when the place files differ from the committed ones its pictures draw; the time log
    written by every verb during a pass is drawn by nothing, so it never raises the warning."""
    import subprocess
    from tools.places.look.daemon import uncommitted
    pdir = tmp_path / "pl"
    pdir.mkdir()
    (pdir / "place.json").write_text("{}\n")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"], check=True)
    (pdir / "timelog.jsonl").write_text("{}\n")
    assert not uncommitted("pl", tmp_path)
    (pdir / "paths.jsonl").write_text("{}\n")
    assert uncommitted("pl", tmp_path)


def test_the_world_road_as_painted_is_kept_clear_in_the_footprint():
    # the road's track textures show on a band of ground vertices along y = 0 (128-unit vertices), x 0 to 2048
    road = ways.RoadPaint({(i, j): 1.0 for i in range(0, 17) for j in (-1, 0, 1)})
    f = files(paths=[])
    f["place"] = {"fit": {"anchor": [1000, 0]}, "radius_m": 20}
    on = piece("tent", "test/ways/crate.nif", 600, 40)
    off = piece("barrel", "test/ways/crate.nif", 600, 600)
    far = piece("far", "test/ways/crate.nif", 600, 40)
    far["m"] = xform.matrix([9600, 40, 0], [0, 0, 0], 1.0)
    assert ids(ways.blockers(f, [on, off, far], Flat(), road=road)) == ["tent"]
    assert road.at(600, 40) == 1.0 and road.at(600, 600) == 0.0
    allowed = ways.blockers(dict(f, spaces={"exterior": {"refs": [
        {"id": "tent", "blocks_way": "a toll booth the road is meant to pass through here"}]}}), [on], Flat(), road=road)
    assert ids(allowed) == [] and allowed[0]["reason"]


def test_owed_blockers_are_reported_new_ones_fail_and_the_list_only_shrinks(tmp_path):
    import json
    row = {"place": "p", "way": "p.path.01", "id": "p.tent", "edid": "Tent", "at": [0, 0, 0], "since": ways.STAGED}
    late = dict(row, id="p.crate", since="2027-01-01")
    gone = dict(row, id="p.barrel")
    (tmp_path / "ways_owed.jsonl").write_text("".join(json.dumps(r) + "\n" for r in (row, late, gone)))
    found = [{"way": "p.path.01", "id": "p.tent"}, {"way": "p.path.01", "id": "p.crate"},
             {"way": "p.path.01", "id": "p.cart"}]
    fail, owed, bad = ways.split_owed("p", found, tmp_path)
    assert [b["id"] for b in owed] == ["p.tent", "p.crate"] and [b["id"] for b in fail] == ["p.cart"]
    assert any("p.barrel" in x and "names no blocker" in x for x in bad)       # stale: delete it
    assert any("p.crate" in x and "added after" in x for x in bad)            # never added later
    ok, line = ways.handover_line("p", tmp_path)
    assert not ok and "ways FAILS" in line
    (tmp_path / "ways_owed.jsonl").write_text(json.dumps(dict(row, why="the toll tent stands on the road on purpose")) + "\n")
    assert ways.handover_line("p", tmp_path)[0]
    assert ways.handover_line("other", tmp_path) == (True, "ways: nothing owed")
