"""L1/L2 (lane 1.15-r6-bridges): a road over a water step crosses on a bridge seated on both banks (infra.seat,
bridge_placements, bridge_errors), and a road keeps out of a site entered from the water (build.around, keep_out)."""
import math

import pytest

from tools.argonia_world import db
from tools.argonia_world.routes import build, infra


def gorge(left: float, right: float, half_gap: float, floor: float = 0.0, centre: float = 0.0):
    return lambda s: floor if abs(s - centre) < half_gap else (left if s < centre else right)


def test_a_level_gorge_seats_the_deck_flush_on_both_banks():
    c, top, banks = infra.seat(gorge(10.0, 10.0, 5.0))
    assert top == 10.0 and banks == (10.0, 10.0)
    assert abs(c) + 5.0 <= infra.BRIDGE_LEN_M / 2 - infra.SEAT_M  # the gap lies inside the two seats


def test_an_off_centre_gorge_moves_the_deck_over_it_and_the_higher_bank_sets_the_top():
    c, top, banks = infra.seat(gorge(12.0, 10.0, 7.0, centre=3.0))  # the gap -4 .. 10 m: a centred deck misses it
    half = infra.BRIDGE_LEN_M / 2 - infra.SEAT_M
    assert c > 0 and c - half <= -4.0 and c + half >= 10.0
    assert top == 12.0 and max(banks) == 12.0 and min(banks) == 10.0  # the lower bank is the terrain's seat


def test_a_line_through_a_disc_goes_round_it_on_the_dry_side_ends_kept():
    pts = [(-100.0, 0.0), (0.0, 0.0), (100.0, 0.0)]
    out = build.around(pts, 0.0, 0.0, 50.0, wet=lambda x, y: y < 0)  # the south (y < 0 here) is water
    assert out[0] == pts[0] and out[-1] == pts[-1]
    assert min(math.hypot(x, y) for x, y in out) >= 50.0 - 1e-6
    assert all(y >= -1e-6 for x, y in out)
    assert build.around(pts, 0.0, 200.0, 50.0) == pts  # a disc the line misses changes nothing
    assert build.around(pts, 100.0, 0.0, 10.0) == pts  # an end inside: kept


@pytest.fixture(scope="module")
def world():
    from tools.argonia_world.place_build import GameGround
    try:
        g = GameGround()
        g.z(1600.0, 3041.0)
        return db.open(), g
    except (FileNotFoundError, OSError) as e:
        pytest.skip(f"no terrain grid: {e}")


def test_the_six_step_crossings_are_bridged_on_their_lines(world):
    w, g = world
    ps = infra.bridge_placements(w, g.z)
    assert len(ps) == 3
    assert sorted(r for p in ps for r in p["routes"]) == sorted(r for _q, _r, rs in infra.BRIDGES.values() for r in rs)
    assert len({r for p in ps for r in p["routes"]}) == 6  # the census's six roads (gideon-stormhold also shares the gideon step)
    for p in ps:
        assert infra.bridge_errors(p, w, g.z) == [], p["id"]
        q = infra.BRIDGES[p["id"].split(".", 1)[1]][0]
        al, ac = infra.lateral(p, q)  # the census's step point lies on the deck, between the seats
        assert abs(al) <= infra.BRIDGE_LEN_M / 2 - infra.SEAT_M and abs(ac) <= infra.BRIDGE_HALF_W_M + 2.5
        assert p["at_m"][2] == pytest.approx(p["deck_m"] - infra.BRIDGE_TOP_M, abs=0.01)


def test_no_road_enters_a_water_entered_site(world):
    w, _g = world
    assert build.site_conflicts(w)["red"] == []
    assert {d[0] for d in build.keep_out_discs(w)} >= {"place.imperial-penal-south.natural-dive-shaft",
                                                         "place.saxhleel-coast.archon-glowgill-byre"}


def test_a_road_into_a_keep_out_disc_is_red(world, monkeypatch):
    w, _g = world
    pid, x, y, r = next(d for d in build.keep_out_discs(w) if d[0].endswith("natural-dive-shaft"))
    monkeypatch.setattr(build, "keep_out_discs", lambda _w: [(pid, x, y, r)])
    real = w.query
    rows = [{"route_id": "route.track.rose-causeway", "x_m": x - 200.0, "y_m": y}, {"route_id": "route.track.rose-causeway", "x_m": x + 200.0, "y_m": y}]
    monkeypatch.setattr(w, "query", lambda q, *a: rows if q.startswith("SELECT route_id, x_m, y_m FROM road_point") else real(q, *a))
    assert [c["road"] for c in build.site_conflicts(w)["red"]] == ["route.track.rose-causeway"]


def test_a_deck_file_sets_the_top_and_the_ends_and_the_census_reads_it(world, tmp_path):
    import json
    w, g = world
    ground = {p["id"]: p for p in infra.bridge_placements(w, g.z, decks=None)}
    gid = ground["bridge.gideon-step"]
    top = gid["deck_m"] + 4.0  # the causeway's corridor, over the pre-causeway ground
    f = tmp_path / "bridge-decks.json"
    c = [gid["at_m"][0] + 1.5, gid["at_m"][1] - 0.5]  # generate's centre (the roads' axis, no seat offset)
    f.write_text(json.dumps([{"id": "bridge.gideon-step", "deck_m": top, "ends_ground_m": [top - 0.4, top],
                              "centre_m": c, "ends_m": [e[:2] for e in gid["ends_m"]], "heading": gid["heading"],
                              "yaw": gid["yaw"]}], indent=1))
    decks = infra.load_decks(f)
    ps = {p["id"]: p for p in infra.bridge_placements(w, g.z, decks)}
    p = ps["bridge.gideon-step"]
    assert p["deck_source"] == "decks-file" and p["deck_m"] == round(top, 2)
    assert p["at_m"] == [round(c[0], 2), round(c[1], 2), round(top - infra.BRIDGE_TOP_M, 2)]
    assert p["yaw"] == gid["yaw"] and p["heading"] == gid["heading"]
    assert ps["bridge.thorn-step"]["deck_source"] == "ground"  # no deck in the file for it: the fallback
    assert infra.bridge_errors(p, w, g.z) == []
    seats = [s for s in infra.seats(w, g.z, decks) if s["bridge"] == "bridge.gideon-step"]
    assert len(seats) == 2 and all(s["z_m"] == round(top, 2) for s in seats)
    assert infra.load_decks(tmp_path / "none.json") is None
