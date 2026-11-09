"""The place draft and seating on a synthetic source and ground (tools/tests/places_fixture.py)."""
import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import places_fixture as F  # noqa: E402

from tools.places import seat  # noqa: E402
from tools.places.draft import check, geom, people, render, run  # noqa: E402


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    root = F.build(tmp_path_factory.mktemp("places"))
    counts = run.draft("fx", root / "bundles", root / "places", record=(F.RECORD, F.GIVES))
    return root, counts


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
