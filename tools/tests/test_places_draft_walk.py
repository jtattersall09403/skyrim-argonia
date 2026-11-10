"""Walking heights, door facing and the island clean-up: seat.top_at, geom.front / run.face_out, check.stands_inside on
a walkway's deck, walk.cut and walk.rehome, and streets and patrols on the built walkable network (walk.Walkable, walk.mend)."""
import json
import math

import numpy as np

from tools.places import check as C
from tools.places.draft import geom, walk
from tools.places.draft.run import face_out
from tools.places.seat import top_at

# a door leaf 40 thick standing 150 in front of (-x of) its origin, as BM&V's in-place hut doors are modelled
DOOR = {"bounds": [[-170, -100, 0], [-130, 100, 200]]}
LEAF = {"bounds": [[-20, -100, 0], [20, 100, 200]]}


def test_top_at_takes_the_highest_upward_face_over_the_point():
    deck = [[[-50, -50, 0], [50, -50, 0], [0, 50, 0]]]
    rail = [[[-50, -50, 60], [50, -50, 60], [0, 50, 60]]]
    wall = [[[-50, 0, 0], [50, 0, 0], [0, 0, 90]]]
    assert top_at(np.array(deck + wall), 0, 0) == 0.0
    assert top_at(np.array(deck + rail), 0, 0) == 60.0
    assert top_at(np.array(deck), 500, 500) is None


def test_front_is_the_face_away_from_the_origin_and_none_on_the_leaf():
    assert geom.front(DOOR) == (-1.0, 0.0)
    assert geom.front(LEAF) is None


def test_face_out_turns_a_door_whose_front_faces_in_about_its_leaf():
    rot = [0.0, 0.0, 0.0]
    # the arrival is on +x of the leaf (x = -150): the front (-x) faces in, so the door turns half round
    x, y = face_out(rot, 0.0, 0.0, DOOR, (100.0, 0.0))
    assert math.isclose(rot[2], math.pi, abs_tol=1e-4)
    leaf = (x + geom.turn([-150.0, 0.0], rot[2])[0], y)
    assert math.isclose(leaf[0], -150.0, abs_tol=0.5)       # the leaf stays where it stood
    rot2 = [0.0, 0.0, 0.0]
    assert face_out(rot2, 0.0, 0.0, DOOR, (-400.0, 0.0)) == (0.0, 0.0) and rot2[2] == 0.0


def test_one_stands_on_a_walkways_deck_not_in_it():
    dock = {"pos": [0, 0, 0], "rot": [0, 0, 0], "scale": 1.0, "bounds": [-160, -250, -430, 160, 250, 70]}
    assert C.stands_inside(dock, [0, 0, 1])                   # under the rail tops: inside by the record box
    assert not C.stands_inside({**dock, "walk": 0.0}, [0, 0, 1])   # on the deck
    assert C.stands_inside({**dock, "walk": 0.0}, [0, 0, -100])    # under the deck


def _place(tmp, people):
    p = tmp / "p"
    (p / "spaces" / "exterior").mkdir(parents=True)
    (p / "spaces" / "hold").mkdir()
    (p / "spaces" / "hold" / "space.json").write_text(json.dumps({"space_id": "hold", "parent": "exterior",
                                                                    "door_from": "d1", "copy_of": "s/hold"}))
    (p / "people.jsonl").write_text("".join(json.dumps(x) + "\n" for x in people))
    (p / "ledger.jsonl").write_text(json.dumps({"src": "S:1", "space": "exterior", "status": "placed"}) + "\n")
    rows = [{"id": "d1", "src": "S:1", "kind": "door", "door": {"to_space": "hold"}}, {"id": "x", "kind": "static"}]
    return p, rows


def test_cut_leaves_out_an_unreachable_room_nobody_uses(tmp_path):
    p, rows = _place(tmp_path, [])
    assert walk.cut("p", ["d1"], rows, p, log=lambda *_: None) == 1
    assert not (p / "spaces" / "hold").exists()
    assert [r["id"] for r in walk.io.read_jsonl(p / "spaces" / "exterior" / "refs.jsonl")] == ["x"]
    led = walk.io.read_jsonl(p / "ledger.jsonl")
    assert {(r["src"], r["status"]) for r in led} == {("S:1", "dropped"), ("*", "dropped")}


def test_cut_keeps_a_room_someone_lives_in(tmp_path):
    p, rows = _place(tmp_path, [{"id": "a", "home": "hold"}])
    assert walk.cut("p", ["d1"], rows, p, log=lambda *_: None) == 0
    assert (p / "spaces" / "hold").exists()


class _Nav:
    """A flat mesh of 100-unit squares (two triangles each) at the given (column, row) cells, neighbours over shared
    edges, as the build's navmesh is read."""

    def __init__(self, fk, cells, z=0.0):
        self.fk, self.space, self.links, self.doors = fk, "exterior", [], []
        verts, vid, tris = [], {}, []

        def v(x, y):
            if (x, y) not in vid:
                vid[(x, y)] = len(verts)
                verts.append([x * 100.0, y * 100.0, z])
            return vid[(x, y)]
        for cx, cy in cells:
            a, b, c, d = v(cx, cy), v(cx + 1, cy), v(cx + 1, cy + 1), v(cx, cy + 1)
            tris += [[a, b, c], [a, c, d]]
        self.verts, self.tri = np.asarray(verts, float), np.asarray(tris, int)
        edge_of = {}
        for i, t in enumerate(tris):
            for k in range(3):
                edge_of.setdefault(frozenset((t[k], t[(k + 1) % 3])), []).append(i)
        self.edge = np.full((len(tris), 3), -1, int)
        for i, t in enumerate(tris):
            for k in range(3):
                self.edge[i][k] = next((o for o in edge_of[frozenset((t[k], t[(k + 1) % 3]))] if o != i), -1)
        self.flags = np.zeros(len(tris), int)


def _town():
    """A street's ground 10 squares long and 3 wide with a hole cut across its lower two rows (a big static's
    collision), and a small island apart."""
    cells = [(x, y) for x in range(10) for y in range(3) if not (4 <= x < 6 and y < 2)]
    return {"navs": {"main": _Nav("main", cells), "isl": _Nav("isl", [(20, 0)])}}


def test_walkable_finds_the_main_network_and_not_holes_or_islands():
    ctx = _town()
    W = walk.Walkable(ctx, comp=C.components(ctx["navs"], {}))
    assert W.on((50, 50)) and W.on((500, 250))
    assert not W.on((500, 50))                 # in the hole
    assert not W.on((2050, 50))                # on the island
    assert not W.on((50, 50, 900))             # a point far above the mesh is another level


def test_mend_relays_a_stretch_off_the_network_along_the_mesh_and_patrols_follow():
    ctx = _town()
    W = walk.Walkable(ctx, comp=C.components(ctx["navs"], {}))
    street = {"id": "s", "points": [[50.0, 50.0], [950.0, 50.0]]}
    assert walk.off_network([street], [], W)[0]
    assert walk.mend(street, W) == 1
    assert walk.off_network([street], [], W)[0] == []
    assert street["points"][0] == [50.0, 50.0] and street["points"][-1] == [950.0, 50.0]
    assert max(q[1] for q in street["points"]) >= 200 - walk.ON_TOL      # it goes round by the top row
    from tools.places.draft import people
    beat = people.beats([{"points": [[50, 50], [500, 50], [950, 50]]}])
    assert people.patrol(beat, 0, W.on) == [[50, 50], [950, 50]]    # the point in the hole is left out
    assert people.patrol(people.beats([street]), 0, W.on)[0] == [50.0, 50.0]


def test_mend_leaves_a_street_with_no_way_on_the_mesh():
    ctx = _town()
    W = walk.Walkable(ctx, comp=C.components(ctx["navs"], {}))
    street = {"id": "s", "points": [[50.0, 50.0], [2050.0, 50.0]]}
    assert walk.mend(street, W) is None and street["points"] == [[50.0, 50.0], [2050.0, 50.0]]


class _Src:
    def __init__(self, beds):
        self.spaces = {"home": type("S", (), {"refs": beds})()}


def test_rehome_moves_a_sleeper_off_the_network_into_a_home_bed(tmp_path, monkeypatch):
    p = tmp_path / "p"
    (p / "spaces" / "exterior").mkdir(parents=True)
    (p / "spaces" / "home").mkdir()
    (p / "spaces" / "home" / "space.json").write_text(json.dumps({"space_id": "home", "parent": "exterior",
                                                                    "copy_of": "s/home"}))
    walk.io.write_jsonl(p / "spaces" / "exterior" / "refs.jsonl",
                        [{"id": "camp", "pos": [550, 50, 0]}, {"id": "near", "pos": [50, 50, 0]}])
    bed = {"space": "exterior", "ref": "camp", "radius": 128}
    walk.io.write_jsonl(p / "people.jsonl", [
        {"id": "g", "role": "guard", "bed": bed, "home": "exterior", "routine": [{"kind": "sleep", "at": dict(bed)}]},
        {"id": "r", "role": "resident", "bed": {"space": "home", "ref": "B"}, "home": "home"}])
    navs = {"main": _Nav("main", [(0, 0), (1, 0), (0, 1), (1, 1)]), "isl": _Nav("isl", [(5, 0)])}
    from tools.places.draft import interiors
    monkeypatch.setattr(interiors, "beds_in", lambda refs, *a: [{"ref": "B", "sleeps": 1}])
    W = walk.Walkable({"navs": navs}, comp=C.components(navs, {}))
    n = walk.rehome("p", W, {}, _Src([]), p, log=lambda *_: None)
    assert n == 1
    ppl = {q["id"]: q for q in walk.io.read_jsonl(p / "people.jsonl")}
    assert set(ppl) == {"g"}                                   # the resident gave up the only bed
    assert ppl["g"]["bed"]["space"] == "home" and ppl["g"]["home"] == "home"
    assert ppl["g"]["routine"][0]["at"]["space"] == "home"


def test_arrivals_puts_a_door_arrival_off_the_mesh_on_it_in_front_of_its_door(tmp_path):
    ctx = _town()
    W = walk.Walkable(ctx, comp=C.components(ctx["navs"], {}))
    p = tmp_path / "p"
    (p / "spaces" / "exterior").mkdir(parents=True)
    (p / "spaces" / "hold").mkdir()
    door = {"id": "d", "kind": "door", "pos": [150.0, -300.0, 0.0], "base": "x", "seat": {"mode": "ground"},
            "door": {"to_space": "hold", "to_ref": "b", "arrival": [150.0, -150.0, 0.0]}}
    walk.io.write_jsonl(p / "spaces" / "exterior" / "refs.jsonl", [door])
    walk.io.write_jsonl(p / "spaces" / "hold" / "refs.jsonl",
                        [{"id": "b", "kind": "door", "door": {"to_ref": "d", "to_pos": [150.0, -150.0, 0.0]}}])
    assert walk.arrivals("p", p, W, {}, log=lambda *_: None) == 1
    a = walk.io.read_jsonl(p / "spaces" / "exterior" / "refs.jsonl")[0]["door"]["arrival"]
    assert W.on(a) and a[1] > -150.0
    assert walk.io.read_jsonl(p / "spaces" / "hold" / "refs.jsonl")[0]["door"]["to_pos"] == a
    assert walk.arrivals("p", p, W, {}, log=lambda *_: None) == 0


def test_a_base_taking_its_stats_from_a_template_we_cannot_see_is_levelled():
    from tools.places.draft import people
    merchant = {"edid": "ArgMerchant", "race_edid": "ArgonianRace", "template": "Skyrim.esm:03DECB", "template_flags": "Stats"}
    assert not people.usable(merchant, {})
    assert people.usable(merchant, {"Skyrim.esm:03DECB": {"edid": "ArgTrader", "race_edid": "ArgonianRace"}})
    assert people.usable({**merchant, "template_flags": ""}, {})
