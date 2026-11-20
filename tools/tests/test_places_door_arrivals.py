"""A door's arrival and its partner door's landing stay one point: an arrival lowered by hand carries its partner
(streets stage), and a door moved by an edit carries both (edits.ref.move)."""
from tools.places import check as C
from tools.places.draft import walk
from tools.places.edits import apply
from tools.tests.test_places_draft_walk import _town


def test_an_arrival_lowered_by_hand_carries_its_partner_doors_landing(tmp_path):
    ctx = _town()
    W = walk.Walkable(ctx, comp=C.components(ctx["navs"], {}))
    p = tmp_path / "p"
    (p / "spaces" / "exterior").mkdir(parents=True)
    (p / "spaces" / "hold").mkdir()
    door = {"id": "d", "kind": "door", "pos": [150.0, -300.0, 0.0], "base": "x", "seat": {"mode": "ground"},
            "door": {"to_space": "hold", "to_ref": "b", "arrival": [150.0, 150.0, 0.0]}}
    walk.io.write_jsonl(p / "spaces" / "exterior" / "refs.jsonl", [door])
    walk.io.write_jsonl(p / "spaces" / "hold" / "refs.jsonl",
                        [{"id": "b", "kind": "door", "door": {"to_ref": "d", "to_pos": [150.0, 150.0, 900.0]}}])
    assert walk.arrivals("p", p, W, {}, log=lambda *_: None) == 1
    a = walk.io.read_jsonl(p / "spaces" / "exterior" / "refs.jsonl")[0]["door"]["arrival"]
    assert walk.io.read_jsonl(p / "spaces" / "hold" / "refs.jsonl")[0]["door"]["to_pos"] == a
    assert walk.arrivals("p", p, W, {}, log=lambda *_: None) == 0


def test_a_door_moved_takes_its_arrival_and_its_partners_landing_with_it():
    files = {"place": {}, "clear": [], "land": [], "paths": [], "people": [],
             "spaces": {"exterior": {"space": None, "refs": [
                 {"id": "d", "kind": "door", "pos": [0.0, 0.0, 100.0], "rot": [0, 0, 0],
                  "door": {"to_space": "hold", "to_ref": "b", "arrival": [10.0, 5.0, 100.0]}}]},
                 "hold": {"space": None, "refs": [
                     {"id": "b", "kind": "door", "pos": [0, 0, 0], "rot": [0, 0, 0],
                      "door": {"to_space": "exterior", "to_ref": "d", "to_pos": [10.0, 5.0, 100.0]}}]}}}
    op = {"n": 1, "op": "ref.move", "space": "exterior", "id": "d", "before": {"pos": [0.0, 0.0, 100.0]},
          "after": {"pos": [0.0, 0.0, 40.0]}}
    out = apply(files, [op])
    assert out["spaces"]["exterior"]["refs"][0]["door"]["arrival"] == [10.0, 5.0, 40.0]
    assert out["spaces"]["hold"]["refs"][0]["door"]["to_pos"] == [10.0, 5.0, 40.0]
