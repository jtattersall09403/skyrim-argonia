"""A room copied with a cut keeps only the part of its source cell inside the cut's box (interiors.kept, build.in_cut)."""
import json

from tools.places import build
from tools.places.draft import interiors, io


def test_cut_keeps_only_the_box(tmp_path, monkeypatch):
    cell = tmp_path / "src.s" / "spaces" / "Hall"
    cell.mkdir(parents=True)
    rows = [{"id": "in", "pos": [100, 100, 0]}, {"id": "edge", "pos": [200, 0, 0]}, {"id": "out", "pos": [900, 100, 0]}]
    (cell / "refs.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    monkeypatch.setattr(io, "BUNDLES", tmp_path)
    interiors._cut_ids.cache_clear()
    cut = {"box": [200, 300, 0, 0]}
    assert interiors.kept("s/Hall", None, cut) == {"in", "edge"}
    assert interiors.kept("s/Hall", None) is None
    assert build.in_cut(cut, [150, 50]) and not build.in_cut(cut, [250, 50]) and build.in_cut(None, [1e9, 0])
    beds = interiors.beds_in([{"id": "in", "kind": "furniture", "base": "b", "pos": [100, 100, 0]},
                              {"id": "out", "kind": "furniture", "base": "b", "pos": [900, 100, 0]}],
                             {"b": {"edid": "BedRoll"}}, None, "s/Hall", cut)
    assert [b["ref"] for b in beds] == ["in"]
    interiors._cut_ids.cache_clear()


def test_work_for_moves_the_working_day():
    from tools.places.draft import people
    folk = [{"id": "a", "name": "Hixee-Ra", "work": {"space": "exterior", "pos": [0, 0]},
             "routine": [{"start": 0, "kind": "sleep", "at": {"space": "h"}},
                         {"start": 8, "kind": "wander", "at": {"space": "exterior", "pos": [0, 0]}},
                         {"start": 20, "kind": "wander", "at": {"space": "exterior", "pos": [0, 0]}}]}]
    spot = {"space": "Hall", "ref": "r", "radius": 256}
    assert people.work_at(folk, {"Hixee-Ra": spot}) == ["a"]
    assert folk[0]["work"] == spot and folk[0]["routine"][1]["at"] == spot
    assert folk[0]["routine"][2]["at"] == {"space": "exterior", "pos": [0, 0]}
