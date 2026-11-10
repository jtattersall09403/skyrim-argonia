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
from tools.places.draft import interiors, lights, run, stages  # noqa: E402


@pytest.fixture()
def fx(tmp_path, monkeypatch):
    root = F.build(tmp_path)
    monkeypatch.setattr(run, "place_record", lambda place_id: (F.RECORD, F.GIVES))
    run.draft("fx", root / "bundles", root / "places", record=(F.RECORD, F.GIVES))
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


LB = {"S:1": {"key": "S:1", "edid": "DBFireLight01", "plugin": "S", "light": {"radius": 256, "colour": "a", "flags": "Dynamic, ShadowOmnidirectional"}},
      "S:2": {"key": "S:2", "edid": "DBFireLight01NS", "plugin": "S", "light": {"radius": 256, "colour": "b", "flags": "Dynamic"}},
      "S:3": {"key": "S:3", "edid": "CandleLight01_Flicker", "plugin": "S", "light": {"radius": 256, "colour": "c", "flags": "ShadowOmnidirectional"}},
      "S:4": {"key": "S:4", "edid": "CandleLight01NS", "plugin": "S", "light": {"radius": 256, "colour": "c", "flags": "Flicker"}},
      "S:5": {"key": "S:5", "edid": "InnCandleShadow", "plugin": "S", "light": {"radius": 300, "colour": "d", "flags": "ShadowSpotlight"}},
      "S:6": {"key": "S:6", "edid": "InnCandle", "plugin": "S", "light": {"radius": 300, "colour": "d", "flags": ""}},
      "S:7": {"key": "S:7", "edid": "OddShadowCaster", "plugin": "S", "light": {"radius": 77, "colour": "z", "flags": "ShadowHemisphere"}}}


def test_a_shadow_casters_twin_is_found_as_skyrim_names_them():
    assert [lights.twin(k, LB) for k in ("S:1", "S:3", "S:5", "S:7", "S:2")] == ["S:2", "S:4", "S:6", None, None]


def room(n, base="S:1"):
    walls = [{"id": "w0", "kind": "static", "pos": [0, 0, 0]}, {"id": "w1", "kind": "static", "pos": [1000, 0, 0]}]
    return walls + [{"id": f"l{i}", "kind": "light", "base": base, "pos": [100.0 * i, 0, 0]} for i in range(n)]


def test_a_room_keeps_four_shadow_casters_by_rule():
    assert lights.shadow_plan(room(4), LB) == ({}, [])
    r = room(7)
    r[2 + 6]["radius"] = 900.0                                   # the largest radius keeps its shadow
    switch, bad = lights.shadow_plan(r, LB)
    assert bad == [] and set(switch.values()) == {"S:2"}
    assert sorted({f"l{i}" for i in range(7)} - set(switch)) == ["l3", "l4", "l5", "l6"]   # l6, then nearest x=500
    switch, bad = lights.shadow_plan(room(6, "S:7"), LB)         # no twin in the load order: said, not hidden
    assert switch == {} and len(bad) == 2


def test_a_copied_room_over_the_limit_gets_twin_rows():
    src = room(6)
    ov = interiors.shadow_twins("p", "house", src, None, [{"id": "x", "src": "w0", "removed": True}], LB)
    twins = [o for o in ov if o.get("twin_of")]
    assert len(twins) == 2 and all(o["base"] == "S:2" and o["twin_of"] == "S:1" and o["seat"] == {"mode": "free"} for o in twins)
    again = interiors.shadow_twins("p", "house", src, None, ov, LB)
    assert again == ov                                            # run again on its own output: the same rows
    built = interiors.built_room(src, None, ov)
    assert sum(1 for r in built if lights.casts(LB.get(r.get("base")))) == 4 and all(r["id"] != "w0" for r in built)


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


def test_a_room_with_five_shadow_casters_fails_shadows():
    import test_places_check as T
    assert C.check_shadows(T.broken("shadows"))
    assert not C.check_shadows({**T.ctx(), "light_bases": LB})
