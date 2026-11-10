"""Walking heights, door facing and the island clean-up: seat.top_at, geom.front / run.face_out, check.stands_inside on
a walkway's deck, walk.cut and walk.rehome."""
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
    def __init__(self, fk, centres):
        self.fk, self.space, self.centres = fk, "exterior", centres

    def tri_at(self, p):
        return next((i for i, c in enumerate(self.centres) if math.dist(c, p[:2]) < 10), -1)


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
                        [{"id": "camp", "pos": [500, 0, 0]}, {"id": "near", "pos": [0, 0, 0]}])
    bed = {"space": "exterior", "ref": "camp", "radius": 128}
    walk.io.write_jsonl(p / "people.jsonl", [
        {"id": "g", "role": "guard", "bed": bed, "home": "exterior", "routine": [{"kind": "sleep", "at": dict(bed)}]},
        {"id": "r", "role": "resident", "bed": {"space": "home", "ref": "B"}, "home": "home"}])
    navs = {"main": _Nav("main", [(0, 0), (50, 0)]), "isl": _Nav("isl", [(500, 0)])}
    comp = {("main", 0): "M", ("main", 1): "M", ("isl", 0): "I"}
    monkeypatch.setattr(C, "components", lambda *_: comp)
    monkeypatch.setattr(C, "door_pairs", lambda *_: {})
    from tools.places.draft import interiors
    monkeypatch.setattr(interiors, "beds_in", lambda refs, *a: [{"ref": "B", "sleeps": 1}])
    n = walk.rehome("p", {"navs": navs}, {}, _Src([]), p, log=lambda *_: None)
    assert n == 1
    ppl = {q["id"]: q for q in walk.io.read_jsonl(p / "people.jsonl")}
    assert set(ppl) == {"g"}                                   # the resident gave up the only bed
    assert ppl["g"]["bed"]["space"] == "home" and ppl["g"]["home"] == "home"
    assert ppl["g"]["routine"][0]["at"]["space"] == "home"
