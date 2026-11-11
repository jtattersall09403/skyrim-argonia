"""The place draft and seating on a synthetic source and ground (tools/tests/places_fixture.py)."""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import places_fixture as F  # noqa: E402

from tools.places import seat  # noqa: E402
from tools.places.draft import check, geom, io, lights, people, render, run  # noqa: E402


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    """The draft over the fixture's own catalogue (the station the record promises is added from it), never the
    tree's out/places/catalogue."""
    root = F.build(tmp_path_factory.mktemp("places"))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(io, "CATALOGUE", F.catalogue(root))
        mp.setattr(io, "_stations", None)
        mp.setattr(lights, "_lights", None)
        counts = run.draft("fx", root / "bundles", root / "places", record=(F.RECORD, F.GIVES))
        yield root, counts


def test_ground_queries(tmp_path):
    root = F.build(tmp_path)
    g = seat.Ground.load(root / "bundles" / "ground.fx")
    for x, y in ((38000.0, 1500.0), (41000.5, -700.25), (36864.0, 0.0)):
        assert g.height(x, y) == pytest.approx(F.our_height(x, y), abs=8.0)
    assert g.wet(42000, 0) and not g.wet(38000, 0)
    assert g.slope(39000, 3000) == pytest.approx(math.degrees(math.atan(0.08)), abs=0.5)
    a = g.at(39000, 3000)
    assert set(a) >= {"ground", "water", "slope", "normal", "sha"} and a["sha"] == "bbb"


def test_seat_rules(tmp_path):
    root = F.build(tmp_path)
    g = seat.Ground.load(root / "bundles" / "ground.fx")
    base = {"id": "a", "pos": [38000.0, 0.0, 999.0], "rot": [0, 0, 0]}
    h = g.height(38000, 0)
    assert seat.seat_z({**base, "seat": {"mode": "above", "dz": 50}}, g) == pytest.approx(h + 50, abs=0.01)
    assert seat.seat_z({**base, "seat": {"mode": "free"}}, g) == 999.0
    w = {**base, "pos": [42000.0, 0.0, 0.0], "seat": {"mode": "water", "dz": -5}}
    assert seat.seat_z(w, g) == pytest.approx(-5)
    sup = {**base, "id": "t", "pos": [38000.0, 0.0, 0.0], "seat": {"mode": "above", "dz": 0}}
    on = {**base, "id": "b", "pos": [38000.0, 0.0, 0.0], "seat": {"mode": "on", "on": "t", "dz": 80}}
    refs = [on, sup]
    seat.seat_all(refs, g)
    assert on["pos"][2] == pytest.approx(sup["pos"][2] + 80)
    footed = {**base, "seat": {"mode": "ground", "dz": 0, "foot": [300, 300]}}
    assert seat.seat_z(footed, g) <= h   # the lowest ground under the footprint


def test_patches_shift_vertices(tmp_path):
    root = F.build(tmp_path)
    g = seat.Ground.load(root / "bundles" / "ground.fx")
    before = g.vertex(9 * 32 + 3, 4)
    g.apply_patches([{"cell": [9, 0], "verts": [[4, 3, 25.0]]}])
    assert g.vertex(9 * 32 + 3, 4) == pytest.approx(before + 25)


def test_draft_passes_its_checks(fx):
    root, counts = fx
    assert check.check("fx", root / "bundles", root / "places", gives=F.GIVES) == []
    assert counts["interiors"] == 4            # three houses share one source interior: three copies, and the hall
    assert counts["people"]["boatman"] == 1 and counts["people"]["guard"] >= 2


def test_fit_turns_the_town_onto_our_river(fx):
    root, _ = fx
    place = json.loads((root / "places" / "fx" / "place.json").read_text())
    # the source's river is to its south; ours is to the east of the anchor: the town turns to face it
    assert 200 <= place["fit"]["rot_deg"] <= 340
    refs = [json.loads(line) for line in (root / "places/fx/spaces/exterior/refs.jsonl").read_text().splitlines()]
    pier = next(r for r in refs if r["src"] == "PIER")
    g = seat.Ground.load(root / "bundles" / "ground.fx")
    assert g.wet(pier["pos"][0], pier["pos"][1])
    assert pier["seat"]["mode"] == "stilts"
    houses = [r for r in refs if r["src"] in ("S0", "S1", "S2", "HALL")]
    assert houses and not any(g.wet(r["pos"][0], r["pos"][1]) for r in houses)


def test_seating_measured_not_copied(fx):
    root, _ = fx
    refs = {r["src"]: r for r in (json.loads(line) for line in
                                  (root / "places/fx/spaces/exterior/refs.jsonl").read_text().splitlines())}
    assert refs["BWL"]["seat"]["mode"] == "on" and refs["BWL"]["seat"]["on"] == refs["TBL"]["id"]
    assert refs["S0"]["seat"]["mode"] == "ground" and refs["S0"]["seat"]["dz"] == pytest.approx(-20 + 0.08 * 250, abs=1)
    # (sunk 20 at its origin on a slope of 0.08: level with the lowest ground under its 500-deep footprint)
    assert refs["NB"]["base"] == "T.esm:000004"     # the Nordic banner replaced by the agent's choice


def test_ledger_accounts_for_every_source_ref(fx):
    root, _ = fx
    ledger = [json.loads(line) for line in (root / "places/fx/ledger.jsonl").read_text().splitlines()]
    srcs = {(r["space"], r["src"]) for r in ledger}
    assert ("exterior", "TR0") in srcs and ("HouseInt", "*") in srcs
    assert all(r.get("why") for r in ledger if r["status"] == "dropped")


def test_reseat_is_idempotent(fx, monkeypatch):
    root, _ = fx
    seat.reseat_place("fx", root / "bundles", root / "places")
    p = root / "places/fx/spaces/exterior/refs.jsonl"
    first = p.read_text()
    assert seat.reseat_place("fx", root / "bundles", root / "places") == 0
    assert p.read_text() == first


def test_draft_is_deterministic(fx, tmp_path):
    root, _ = fx
    other = F.build(tmp_path)
    run.draft("fx", other / "bundles", other / "places", record=(F.RECORD, F.GIVES))
    for name in ("spaces/exterior/refs.jsonl", "people.jsonl", "paths.jsonl", "clear.jsonl", "ledger.jsonl"):
        assert (root / "places/fx" / name).read_text() == (other / "places/fx" / name).read_text(), name


def test_check_catches_a_floating_ref(fx, tmp_path):
    root, _ = fx
    import shutil
    copy = tmp_path / "c"
    shutil.copytree(root, copy)
    p = copy / "places/fx/spaces/exterior/refs.jsonl"
    rows = [json.loads(line) for line in p.read_text().splitlines()]
    rows[0]["pos"][2] += 300
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    (copy / "places/fx/people.jsonl").write_text("")
    bad = check.check("fx", copy / "bundles", copy / "places", gives=F.GIVES)
    assert any("not seated" in b for b in bad) and any("nobody giving it" in b for b in bad)


def test_service_people_merge_trainers_and_rooms():
    ps = people.service_people(F.GIVES)
    roles = sorted(p["role"] for p in ps)
    assert roles == ["boatman", "innkeeper", "merchant"]
    trader = next(p for p in ps if p["role"] == "merchant")
    assert {g["kind"] for g in trader["gives"]} == {"trader-general", "trainer"}


def test_render_writes_pngs(fx):
    root, _ = fx
    out = render.render("fx", root / "bundles", root / "places", out=root / "renders")
    assert all(p.exists() and p.stat().st_size > 1000 for p in out)


def test_xf_compose():
    xf = geom.Xf((0, 0), (10, 0), 0.0).then(5, 0, math.pi / 2, (10, 0))
    x, y = xf.pt(1, 0)
    assert (round(x, 6), round(y, 6)) == (15.0, -1.0)


def test_check_refuses_a_large_or_waterline_patch(fx, tmp_path):
    root, _ = fx
    import shutil
    copy = tmp_path / "c"
    shutil.copytree(root, copy)
    # cell (10, 0) holds our river's edge at x = 40000 (col 24): lift a wet point across the waterline, far past the bound
    (copy / "places/fx/land.jsonl").write_text(json.dumps({"cell": [10, 0], "verts": [[4, 30, 400.0]], "why": "t"}) + "\n")
    bad = check.check("fx", copy / "bundles", copy / "places", gives=F.GIVES)
    assert any("bound" in b for b in bad) and any("waterline" in b for b in bad)


def test_innkeeper_keeps_the_inn_all_night(fx):
    root, _ = fx
    folk = [json.loads(line) for line in (root / "places/fx/people.jsonl").read_text().splitlines()]
    inn = next(p for p in folk if p["role"] == "innkeeper")
    assert inn["bed"] is None and [s["hours"] for s in inn["routine"]] == [24]


def test_patches_never_fill_water(fx):
    root, _ = fx
    land = [json.loads(line) for line in (root / "places/fx/land.jsonl").read_text().splitlines()]
    assert all(abs(v[2]) <= 105 for p in land for v in p["verts"])


def test_nordic_review_outranks_the_folder_rule(tmp_path):
    from tools.places.draft import io as dio
    p = tmp_path / "review.jsonl"
    p.write_text('{"base": "A:1", "verdict": "neutral", "why": "leaves"}\n'
                 '{"base": "A:2", "verdict": "nordic", "why": "planter", "replace": {"base": "K:9"}}\n')
    rv = dio.nordic_review(p)
    assert not dio.is_nordic("A:1", {"nordic": True}, rv)
    assert dio.is_nordic("A:2", {"nordic": False}, rv)
    assert dio.is_nordic("A:3", {"nordic": True}, rv)        # unreviewed: the folder rule stands
    # the place's own replacements stand alone: the review replaces nothing, and a Nordic replacement is refused
    refused = []
    rep = dio.replacements({"replace": {"A:5": "K:5", "A:1": "K:1"}}, {"K:1": {"nordic": True}}, refused)
    assert rep == {"A:5": {"base": "K:5"}}
    assert refused == ["replace A:1 -> refused: the replacement is a Nordic piece (decision 0006)"]


def test_a_replacement_keeps_the_walking_top():
    from tools.places.draft import io as dio
    steps = {"edid": "DockStepsDown02", "bounds": [[-258, -150, -508], [257, 157, 190]]}
    flat = {"edid": "DLC2RRDockStr02", "bounds": [[-158, -269, -440], [153, 287, 74]]}
    steps2 = {"edid": "OtherSteps", "bounds": [[-200, -150, -480], [200, 150, 180]]}
    bases = {"A:7": steps, "K:7": flat, "K:8": steps2}
    refused = []
    assert dio.replacements({"replace": {"A:7": "K:7"}}, bases, refused) == {}
    assert refused and "walking top" in refused[0]
    assert dio.replacements({"replace": {"A:7": "K:8"}}, bases) == {"A:7": {"base": "K:8"}}
    assert dio.keeps_function({"edid": "Lamp", "bounds": [[0, 0, 0], [1, 1, 300]]}, {"bounds": [[0, 0, 0], [1, 1, 10]]})


def test_arrival_inside_a_body_but_not_on_top_of_it():
    from tools.places.draft import geom
    bases = {"B:1": {"key": "B:1", "bounds": [[-100, -100, 0], [100, 100, 300]], "model": "x/house.nif"}}
    house = {"base": "B:1", "kind": "building", "pos": [0, 0, 0], "rot": [0, 0, 0], "scale": 1}
    assert geom.stands_in(house, bases, (10, 10, 0))
    assert not geom.stands_in(house, bases, (95, 0, 0))       # outside the 0.8 share in plan
    assert not geom.stands_in(house, bases, (10, 10, 300))     # standing on its top
    road = {"base": "R:1", "kind": "static", "pos": [0, 0, 0], "rot": [0, 0, 0], "scale": 1}
    bases["R:1"] = {"key": "R:1", "bounds": [[-200, -200, -40], [200, 200, 20]], "model": "x/road.nif"}
    assert geom.stand_height(0, 0, 0.0, [road], bases) == 20     # one steps onto a low road


def test_plant_inside_a_placed_thing_is_cleared():
    from tools.places.draft import clear
    bases = {"B:1": {"key": "B:1", "bounds": [[-100, -100, 0], [100, 100, 300]], "model": "x/rock.nif"}}
    rock = {"id": "r", "base": "B:1", "kind": "rock", "pos": [0, 0, 0], "rot": [0, 0, 0], "scale": 1}
    inside = {"id": "p1", "base": "T:1", "kind": "tree", "pos": [90, 0, 10]}
    outside = {"id": "p2", "base": "T:1", "kind": "tree", "pos": [150, 0, 10]}
    assert clear.inside_placed(inside, [rock], bases)
    assert clear.stray([inside, outside], set(), [rock], bases, []) == ["world plant p1 (T:1) stands in r"]
    assert clear.stray([inside], {"p1"}, [rock], bases, []) == []
