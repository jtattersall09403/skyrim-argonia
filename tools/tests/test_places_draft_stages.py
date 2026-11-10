"""The draft's stages run alone on standing place files, the whole draft's refusal over the owner's saves, and the
lights' rules (tools/places/draft/stages.py, lights.py)."""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import places_fixture as F  # noqa: E402

from tools.places import check as C  # noqa: E402
from tools.places import draft as D  # noqa: E402
from tools.places.draft import interiors, jail, lights, run, stages  # noqa: E402


@pytest.fixture()
def fx(tmp_path, monkeypatch):
    root = F.build(tmp_path)
    monkeypatch.setattr(run, "place_record", lambda place_id: (F.RECORD, F.GIVES))
    monkeypatch.setattr(jail, "law", lambda place_id: ("native", "Argonian law, no cell: the fixture's elders"))
    run.draft("fx", root / "bundles", root / "places", record=(F.RECORD, F.GIVES))
    stages.run("jail", "fx", root / "places", root / "bundles", log=lambda *_: None)   # as a whole draft ends
    stages.Standing("fx", root / "places", root / "bundles").write()     # the files as a join leaves them: canonical
    return root


def rows(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


@pytest.mark.parametrize("stage", [s for s in stages.STAGES if s != "streets"])
def test_a_stage_on_a_settled_place_changes_nothing(fx, stage):
    before = stages.snapshot(fx / "places/fx")
    counts = stages.run(stage, "fx", fx / "places", fx / "bundles", log=lambda *_: None)
    assert counts == {}, counts
    assert stages.snapshot(fx / "places/fx") == before       # every file byte for byte


def test_fit_puts_back_only_the_row_that_left_its_cluster(fx):
    p = fx / "places/fx/spaces/exterior/refs.jsonl"
    good = p.read_text()
    rs = rows(p)
    moved = next(r for r in rs if r.get("src") == "B0")
    other = next(r["cluster"] for r in rs if r.get("cluster") and r["cluster"] != moved["cluster"])
    moved["cluster"], moved["pos"][0] = other, moved["pos"][0] + 900.0
    p.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rs))
    before = stages.snapshot(fx / "places/fx")
    counts = stages.run("fit", "fx", fx / "places", fx / "bundles", log=lambda *_: None)
    assert counts == {"spaces/exterior/refs.jsonl": {"changed": 1, "added": 0, "removed": 0}}
    after = stages.snapshot(fx / "places/fx")
    assert {k for k in after if after[k] != before[k]} == {"spaces/exterior/refs.jsonl"}
    back = next(r for r in rows(p) if r.get("src") == "B0")
    was = next(r for r in (json.loads(x) for x in good.splitlines()) if r.get("src") == "B0")
    assert back["cluster"] == was["cluster"] and math.dist(back["pos"], was["pos"]) < 0.05
    assert [x for x in p.read_text().splitlines() if '"B0"' not in x] == [x for x in good.splitlines() if '"B0"' not in x]


def test_a_stage_that_writes_outside_what_it_owns_changes_nothing(fx, monkeypatch):
    def rogue(st, log=print):
        st.files["paths"][0]["width"] = 999
    monkeypatch.setitem(stages.RUN, "seating", rogue)
    before = stages.snapshot(fx / "places/fx")
    with pytest.raises(stages.StageError, match="outside what it owns"):
        stages.run("seating", "fx", fx / "places", fx / "bundles")
    assert stages.snapshot(fx / "places/fx") == before


def test_a_row_of_a_finalised_save_is_the_owners(fx):
    p = fx / "places/fx/spaces/exterior/refs.jsonl"
    rs = rows(p)
    moved = next(r for r in rs if r.get("src") == "B0")
    moved["seat"] = {"mode": "above", "dz": 50.0}
    p.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rs))
    (fx / "places/fx/edits").mkdir()
    (fx / "places/fx/edits/s1.json").write_text(json.dumps(
        {"save_id": "s1", "final": True, "ops": [{"op": "ref.move", "id": moved["id"]}]}))
    logs = []
    counts = stages.run("seating", "fx", fx / "places", fx / "bundles", log=logs.append)
    assert counts == {} and any("the owner's" in x for x in logs)
    assert next(r for r in rows(p) if r.get("src") == "B0")["seat"] == {"mode": "above", "dz": 50.0}


def test_a_whole_draft_is_refused_over_the_owners_saves(fx, capsys):
    pdir = fx / "places/fx"
    assert D.refusal("fx", None, fx / "places") is None
    (pdir / "edits").mkdir()
    (pdir / "edits/draft.json").write_text(json.dumps({"save_id": "draft", "ops": []}))
    assert D.refusal("fx", None, fx / "places") is None          # a save not finalised is no edit of record
    (pdir / "edits/s1.json").write_text(json.dumps({"save_id": "s1", "final": True, "ops": []}))
    why = D.refusal("fx", None, fx / "places")
    assert "s1" in why and "draft <fit|pieces|seating" in why and "--force" in why
    assert D.refusal("fx", "", fx / "places") == why             # --force with no reason is still refused
    assert D.refusal("fx", "the ground bundle changed under the whole town", fx / "places") is None


# --- lights ---
BASES = {"L:1": {"edid": "CandleLanternwithCandle01"}, "L:2": {"edid": "SLightCandle"}, "L:3": {"edid": "Crate01"},
         "L:4": {"edid": "01mudwindow"}}


def test_a_light_is_bound_to_the_nearest_fixture_within_reach():
    refs = [{"id": "lantern", "base": "L:1", "kind": "clutter", "pos": [0, 0, 100]},
            {"id": "crate", "base": "L:3", "kind": "container", "pos": [10, 0, 100]},
            {"id": "window", "base": "L:4", "kind": "static", "pos": [1000, 0, 100]},
            {"id": "glow", "base": "L:2", "kind": "light", "pos": [30, 0, 110]},
            {"id": "pane", "base": "L:2", "kind": "light", "pos": [1000, 100, 100]},
            {"id": "alone", "base": "L:2", "kind": "light", "pos": [5000, 0, 100]}]
    assert lights.fixtures(refs, BASES) == {"glow": "lantern", "pane": "window"}


def test_a_light_follows_its_fixture_and_the_check_sees_one_that_does_not():
    src = {"f": {"id": "f", "pos": [0.0, 0.0, 100.0]}, "l": {"id": "l", "pos": [20.0, 0.0, 130.0]}}
    ours = [{"id": "o.f", "src": "f", "cluster": "b1", "pos": [500.0, 500.0, 40.0]},
            {"id": "o.l", "src": "l", "cluster": "s9", "pos": [900.0, 100.0, 300.0], "seat": {"mode": "above"}}]
    turn = lambda cid: math.pi / 2      # noqa: E731
    assert len(lights.off_fixture(ours, src, {"l": "f"}, turn)) == 1
    assert lights.follow(ours, src, {"l": "f"}, turn) == 1
    assert ours[1]["pos"][:2] == [500.0, 480.0]                   # the offset turned a quarter clockwise
    ours[1]["pos"][2] = 40.0 + lights.seat(src["l"], src["f"])["dz"]
    assert lights.off_fixture(ours, src, {"l": "f"}, turn) == []
    assert lights.off_fixture(ours[1:], src, {"l": "f"}, turn)    # its fixture left out


def test_an_added_forge_carries_its_fire_light_and_a_smelter_none():
    ext = [{"id": "p.forge", "pos": [100.0, 100.0, 10.0], "rot": [0, 0, 0.0]}, {"id": "p.smelter", "pos": [0, 0, 0], "rot": [0, 0, 0]}]
    stn = {"added": [{"station": "forge", "id": "p.forge", "space": "exterior"},
                     {"station": "smelter", "id": "p.smelter", "space": "exterior"}]}
    got = lights.station_lights("p", ext, stn)
    assert [(r["base"], r["seat"]["on"], r["pos"]) for r in got] == [(lights.FORGE_LIGHT, "p.forge", [84.0, 267.0, 94.0])]


def test_a_copied_rooms_lights_go_back_to_the_sources_own_bases():
    src = [{"id": "w0", "kind": "static", "pos": [0, 0, 0]},
           {"id": "l0", "kind": "light", "base": "S:1", "pos": [0.0, 0, 0], "rot": [0, 0, 0], "src": "X.esm"},
           {"id": "l1", "kind": "light", "base": "S:1", "pos": [100.0, 0, 0], "rot": [0, 0, 0], "src": "X.esm"}]
    ov = [{"id": "x", "src": "w0", "removed": True},
          {**src[1], "id": "p.l0", "src": "l0", "seat": {"mode": "free"}, "base": "S:2", "twin_of": "S:1"},
          {**src[2], "id": "p.l1", "src": "l1", "seat": {"mode": "free"}, "base": "S:2", "twin_of": "S:1",
           "pos": [150.0, 0, 0]}]
    rows, back, gone = interiors.own_lights(src, ov)
    assert (back, gone) == (1, 1)                                 # the plain twin row goes; the moved one keeps its move
    assert rows == [ov[0], {**src[2], "id": "p.l1", "src": "l1", "seat": {"mode": "free"}, "pos": [150.0, 0, 0]}]
    assert interiors.own_lights(src, rows) == (rows, 0, 0)       # run again on its own output: the same rows


# --- the build's checks ---
def test_a_source_places_own_piece_is_not_judged_nordic_and_an_added_one_is():
    import test_places_check as T
    c = T.ctx()
    c["dump"]["refs"][0].update(model="meshes/architecture/whiterun/wrhouse01.nif", base_type="STAT")
    c["plan"]["refs"][0]["base"] = "Skyrim.esm:0AAAAA"
    c["nordic_review"] = {}
    c["source_bases"] = {"Skyrim.esm:0AAAAA"}
    assert not C.check_nordic(c)
    c["source_bases"] = set()
    assert C.check_nordic(c)


def test_people_re_reads_a_service_from_the_record_and_changes_that_row_alone(fx):
    """A service left from an older record (a dead kind, old words) is re-read from the record's promise at its seq
    by the people stage: that person's row changes and nothing else; the services check sees the stale row."""
    from tools.places.draft import people
    p = fx / "places/fx/people.jsonl"
    folk = rows(p)
    boat = next(r for r in folk if any(s["seq"] == 1 for s in r.get("services") or []))
    good = [dict(s) for s in boat["services"]]
    boat["services"] = [{"seq": 1, "kind": "carriage-or-boat", "detail": "raft-boatman to Truowa and Julo"}]
    p.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in folk))
    stale = C.service_rows({"folk": rows(p), "gives": F.GIVES, "routes": {}})
    assert any("carriage-or-boat" in b for b in stale) and any("raft-boatman" in b for b in stale), stale
    counts = stages.run("people", "fx", fx / "places", fx / "bundles", log=lambda *_: None)
    assert counts == {"people.jsonl": {"changed": 1, "added": 0, "removed": 0}}, counts
    again = next(r for r in rows(p) if r["id"] == boat["id"])
    assert again["services"] == good and good[0]["kind"] == "boat-stop" and good[0]["destinations"] == []
    assert C.service_rows({"folk": rows(p), "gives": F.GIVES, "routes": {}}) == []
    assert people.refresh_services(rows(p), F.GIVES, {}) == []      # settled: nothing more to change
