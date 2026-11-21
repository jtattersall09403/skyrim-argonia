"""Two places on one source: the later one owes a `differs` entry for the earlier, and may not take the same part of
the source at the same turn (tools/places/draft/differs.py)."""
import json

from tools.places.draft import differs, plan, wholesale

ROW = {f: f"this place does its own {f} differently here" for f in differs.FIELDS}
OWN = {f: f"the third place keeps {f} for itself" for f in differs.FIELDS}


def _place(root, pid, src="s", laid=None, base=True, pivot=(0, 0), rot=0, diff=None):
    d = root / pid
    d.mkdir(parents=True)
    p = {"place_id": pid, "source_id": src, "fit": {"pivot": list(pivot), "rot_deg": rot}, "draft": {"plan": {}}}
    if base:
        p["wholesale"] = {"offset": 0, **({"laid": laid} if laid else {})}
    if diff is not None:
        p["draft"]["plan"]["differs"] = diff
    (d / "place.json").write_text(json.dumps(p))


def test_a_redraft_mark_names_the_source_the_place_is_next_laid_from(tmp_path):
    _place(tmp_path, "first")
    _place(tmp_path, "second", src="old", base=False)
    pj = tmp_path / "second" / "place.json"
    pj.write_text(json.dumps({**json.loads(pj.read_text()), "redraft": {"source_id": "s", "why": "re-chosen"}}))
    assert differs.owed("second", tmp_path) == ["first"]


def test_the_earlier_place_owes_nothing_and_the_later_owes_an_entry(tmp_path):
    _place(tmp_path, "first")                                   # laid before stamps: the earliest
    _place(tmp_path, "second", base=False)                      # not laid yet
    _place(tmp_path, "first@v2")                                # a variant never counts
    assert differs.owed("first", tmp_path) == [] and differs.faults("first", tmp_path) == []
    assert differs.owed("second", tmp_path) == ["first"]
    assert differs.faults("second", tmp_path) == []             # the checks ask it only once a baseline exists
    assert "write draft.plan.differs" in differs.faults("second", tmp_path, laying=True)[0]


def test_a_thin_or_copied_entry_fails_and_a_full_one_passes(tmp_path):
    _place(tmp_path, "first", diff=[{"place": "x", "takes": "the north quarter round the pond"}])
    _place(tmp_path, "second", laid="2026-11-22T00:00:00Z", pivot=(5000, 0),
           diff=[{"place": "first", **ROW, "takes": "the north quarter round the pond", "adds": "a hut"}])
    got = differs.faults("second", tmp_path)
    assert any("takes: copied" in f for f in got) and any("adds: a sentence" in f for f in got)
    _place(tmp_path, "third", laid="2026-11-23T00:00:00Z", pivot=(-5000, 0), diff=[{"place": "first", **OWN},
                                                                                   {"place": "second", **OWN}])
    assert differs.faults("third", tmp_path) == []


def test_the_same_part_at_the_same_turn_fails_the_later_place_with_numbers(tmp_path):
    _place(tmp_path, "first", pivot=(0, 0), rot=90)
    _place(tmp_path, "second", laid="2026-11-22T00:00:00Z", pivot=(300, 400), rot=100, diff=[{"place": "first", **ROW}])
    got = differs.faults("second", tmp_path)
    assert len(got) == 1 and "500 units apart" in got[0] and "10 degrees" in got[0]
    assert differs.faults("first", tmp_path) == []


def test_the_plan_validates_differs_rows():
    bad = plan.faults({"look": [{"line": "a", "by": "b"}], "differs": [{"place": "", "takes": "x"}]}, [])
    assert any("names no place" in d for _, d in bad) and any("takes" in d for _, d in bad)


def test_draft_wholesale_refuses_until_the_entry_is_written(tmp_path, monkeypatch, capsys):
    _place(tmp_path, "first")
    _place(tmp_path, "second", base=False)

    class St:
        pdir = tmp_path / "second"
    monkeypatch.setattr(wholesale, "Standing", lambda pid: St())
    monkeypatch.setattr(wholesale.io, "PLACES", tmp_path)
    assert wholesale.main(["second", "--offset", "0"]) == 1
    assert "first" in capsys.readouterr().err
