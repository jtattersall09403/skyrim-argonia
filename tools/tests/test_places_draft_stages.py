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
    for st_ in ("jail", "add", "names"):   # as a whole draft ends
        stages.run(st_, "fx", root / "places", root / "bundles", log=lambda *_: None)
    stages.Standing("fx", root / "places", root / "bundles").write()     # the files as a join leaves them: canonical
    return root


def rows(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


@pytest.mark.parametrize("stage", [s for s in stages.STAGES if s != "streets"])
def test_a_stage_on_a_settled_place_changes_nothing(fx, stage):
    if stage == "ground":       # not part of a whole draft: a place carries its ground by choice; once carried, settled
        stages.run(stage, "fx", fx / "places", fx / "bundles", log=lambda *_: None)
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
    assert "s1" in why and "draft <fit|pieces|ground|seating" in why and "--force" in why
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


def test_a_light_whose_fixture_is_left_out_is_dropped_and_one_whose_fixture_stands_is_kept():
    rows = [{"id": "o.f1", "src": "f1"}, {"id": "o.l1", "src": "l1"}, {"id": "o.l2", "src": "l2"}]
    bound = {"l1": "f1", "l2": "f2"}                              # f2 is left out
    assert [r["id"] for r in lights.orphans(rows, bound)] == ["o.l2"]
    assert lights.orphans(rows[:2], bound) == []


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


def test_one_building_with_several_doors(monkeypatch):
    """A cell whose ways out all open into one walkable island is one building with several doors (copied once); one
    whose ways out open into islands of their own packs several houses' rooms."""
    def door(i, to="exterior"):
        return {"id": i, "kind": "door", "door": {"to_space": to, "to_ref": "x" + i}}
    refs = [door("A"), door("B"), door("C", "cellar"), {"id": "bed", "kind": "furniture"}]
    one = frozenset({"bed", "A", "B"})
    monkeypatch.setattr(interiors, "rooms_of", lambda co: {"A": one, "B": one})
    assert interiors.one_building("s/house", refs)
    monkeypatch.setattr(interiors, "rooms_of", lambda co: {"A": frozenset({"bed", "A"}), "B": frozenset({"B"})})
    assert not interiors.one_building("s/house", refs)
    assert not interiors.one_building("s/house", refs[:1])     # one way out: nothing to decide


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


def test_clearance_takes_a_reused_world_ref_as_the_plant_the_world_has_now(fx):
    p = fx / "places/fx/clear.jsonl"
    rs = rows(p)
    stale = next(r for r in rs if r.get("by") == "draft")
    true_pos = list(stale["pos"])
    stale["pos"] = [true_pos[0] + 500.0, true_pos[1], true_pos[2]]     # the row of a plant an older world had there
    p.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rs))
    counts = stages.run("clearance", "fx", fx / "places", fx / "bundles", log=lambda *_: None)
    assert counts == {"clear.jsonl": {"changed": 1, "added": 0, "removed": 0}}
    assert next(r for r in rows(p) if r["ref"] == stale["ref"])["pos"] == true_pos


def test_add_brings_a_room_of_another_source_behind_an_added_door_and_takes_it_out_again(fx, monkeypatch):
    """A `draft.add` door with `room` copies that source interior as a room of ours, its way out paired with the door
    and the door seated on the building row it names by `on`; a Nordic piece of the room is removed; a rerun changes
    nothing; dropping the rows takes the room out again."""
    from tools.places.draft import io
    monkeypatch.setattr(io, "catalogue_bases", lambda keys, path=None: {k: {"key": k, "nordic": True} for k in keys
                                                                        if k == "T.esm:000007"})
    pj = fx / "places/fx/place.json"
    place = json.loads(pj.read_text())
    before = list(place["draft"].get("add") or [])
    place["draft"]["add"] = before + [
        {"base": "T.esm:000001", "kind": "building", "pos": [40500, 1500], "why": "a hall"},
        {"base": "T.esm:000005", "kind": "door", "pos": [40500, 1240], "on": io.mint("fx", "add", str(len(before)), "T.esm:000001"), "dz": 5.0, "why": "its door",
         "room": {"copy_of": "t.fx/HallInt", "space": "AddedHall", "arrival": [40500, 1100]}},
        {"base": "Skyrim.esm:000010", "kind": "marker", "pos": [40600, 1100], "map_marker": "Hall Landing", "why": "a marker"}]
    pj.write_text(json.dumps(place, indent=1) + "\n")
    stages.run("add", "fx", fx / "places", fx / "bundles", log=lambda *_: None)
    ext = {r["id"]: r for r in rows(fx / "places/fx/spaces/exterior/refs.jsonl")}
    house = ext[io.mint("fx", "add", str(len(before)), "T.esm:000001")]
    door = ext[io.mint("fx", "add", str(len(before) + 1), "T.esm:000005")]
    mark = ext[io.mint("fx", "add", str(len(before) + 2), "Skyrim.esm:000010")]
    assert door["seat"] == {"mode": "on", "on": house["id"], "dz": 5.0} and abs(door["pos"][2] - house["pos"][2] - 5.0) < 1e-3
    assert mark["map_marker"]["Name"] == "Hall Landing" and "persistent" in mark["flags"]
    sj = json.loads((fx / "places/fx/spaces/AddedHall/space.json").read_text())
    assert sj["copy_of"] == "t.fx/HallInt" and sj["door_from"] == door["id"] and sj["added"] and sj["parent"] == "exterior"
    inside = rows(fx / "places/fx/spaces/AddedHall/refs.jsonl")
    back = next(r for r in inside if r.get("src") == "HLD")
    assert door["door"]["to_space"] == "AddedHall" and door["door"]["to_ref"] == back["id"]
    assert back["door"]["to_ref"] == door["id"] and back["door"]["to_pos"][:2] == [40500.0, 1100.0]
    assert sum(1 for r in inside if r.get("removed")) == 8          # the hall's eight Nordic beds
    assert stages.run("add", "fx", fx / "places", fx / "bundles", log=lambda *_: None) == {}
    place["draft"]["add"] = before
    pj.write_text(json.dumps(place, indent=1) + "\n")
    stages.run("add", "fx", fx / "places", fx / "bundles", log=lambda *_: None)
    assert not (fx / "places/fx/spaces/AddedHall").exists()
    assert door["id"] not in {r["id"] for r in rows(fx / "places/fx/spaces/exterior/refs.jsonl")}


def test_an_added_room_has_a_second_way_in_by_a_pair_of_added_doors(fx):
    """A door standing in an added room and a door outside naming it in `pair` lead into each other; the outer one
    carries its lock and is laid a path to the street."""
    from tools.places.draft import io
    pj = fx / "places/fx/place.json"
    place = json.loads(pj.read_text())
    n = len(place["draft"].get("add") or [])
    house = io.mint("fx", "add", str(n), "T.esm:000001")
    inner = io.mint("fx", "add", str(n + 2), "T.esm:000005")
    place["draft"]["add"] = (place["draft"].get("add") or []) + [
        {"base": "T.esm:000001", "kind": "building", "pos": [40500, 1500], "why": "a hall"},
        {"base": "T.esm:000005", "kind": "door", "pos": [40500, 1240], "on": house, "why": "its front door",
         "room": {"copy_of": "t.fx/HallInt", "space": "AddedHall", "arrival": [40500, 1100]}},
        {"base": "T.esm:000005", "kind": "door", "space": "AddedHall", "pos": [0, 600, 0], "rot_z": 0.0, "why": "back"},
        {"base": "T.esm:000005", "kind": "door", "pos": [40500, 1760], "on": house, "rot_z": 3.1416, "pair": inner,
         "arrival": [40500, 1900], "lock": {"level": "Expert", "key": None, "flags": "0"}, "why": "its back door"}]
    pj.write_text(json.dumps(place, indent=1) + "\n")
    stages.run("add", "fx", fx / "places", fx / "bundles", log=lambda *_: None)
    ext = {r["id"]: r for r in rows(fx / "places/fx/spaces/exterior/refs.jsonl")}
    back = ext[io.mint("fx", "add", str(n + 3), "T.esm:000005")]
    inside = {r["id"]: r for r in rows(fx / "places/fx/spaces/AddedHall/refs.jsonl")}[inner]
    assert back["door"]["to_space"] == "AddedHall" and back["door"]["to_ref"] == inner
    assert inside["door"]["to_space"] == "exterior" and inside["door"]["to_ref"] == back["id"]
    assert inside["door"]["to_pos"][:2] == [40500.0, 1900.0] and back["lock"]["level"] == "Expert"
    assert any(p.get("from") == back["id"] for p in rows(fx / "places/fx/paths.jsonl"))
    assert stages.run("add", "fx", fx / "places", fx / "bundles", log=lambda *_: None) == {}


def test_a_stop_handler_works_at_the_stops_own_thing():
    """The handler of a stop works at the `draft.add` row marked with that stop, work hours and all."""
    from tools.places.draft import io, people
    place = {"draft": {"add": [{"base": "b:pool", "pos": [0, 0], "stop": "rootworm-stop"}]}}
    spot = io.mint("p", "add", "0", "b:pool")
    folk = [{"id": "p.tender", "services": [{"kind": "rootworm-stop"}], "work": {"space": "exterior", "pos": [1, 2]},
             "routine": [{"kind": "work", "at": {"space": "exterior", "pos": [1, 2]}}]}, {"id": "p.other", "services": []}]
    assert people.spots_of("p", place) == {"rootworm-stop": spot}
    assert people.stop_spots(folk, people.spots_of("p", place)) == ["p.tender"]
    assert folk[0]["work"]["ref"] == spot and folk[0]["routine"][0]["at"]["ref"] == spot
    assert people.stop_spots(folk, people.spots_of("p", place)) == []


def test_an_added_row_swapped_in_place_keeps_its_id():
    """A `draft.add` row whose base is swapped keeps the id it was minted with (`id_base`): the stories rest on it."""
    from tools.places.draft import adds, io, people
    first = io.mint("p", "add", "0", "b:puddle")
    place = {"draft": {"add": [{"base": "b:sap", "id_base": "b:puddle", "pos": [0, 0], "stop": "rootworm-stop"}]}}
    bases = {"b:sap": {"key": "b:sap", "edid": "Pool", "kind": "activator", "bounds": [[-10, -10, 0], [10, 10, 1]]}}
    (_, row), = adds.rows("p", place["draft"], bases)
    assert row["id"] == first and row["base"] == "b:sap"
    assert people.spots_of("p", place) == {"rootworm-stop": first}
