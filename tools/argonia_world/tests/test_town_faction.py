"""L1 (lane w3-infra): every placed person of a built place is in its town's crime faction, which tracks crime with
the Owing's rates (place_build.town_faction). Claywater is one town of two halves (culture.settlement.claywater-station)."""
import pytest

from tools.argonia_world import db, place_build
from tools.argonia_world.formids import Allocator


@pytest.fixture(scope="module")
def built():
    w = db.open()
    alloc = Allocator(w)
    ctx = place_build._Ctx(alloc, w, None, None)
    out = {}
    for pid in place_build.built_places(w):
        fk = place_build.town_faction(ctx, w, pid)
        people = [r for r in w.rows("build_ref") if r.npc_id and w.get("npc", r.npc_id).kind != "creature"
                  and w.get("build_cell", r.cell_id).place_id == pid]
        out[pid] = (fk, people)
    return ctx, out


def test_every_place_with_people_has_a_crime_faction(built):
    _, out = built
    assert out
    bad = [pid for pid, (fk, people) in out.items() if people and not fk]
    assert not bad, bad


def test_the_crime_faction_tracks_crime_with_the_owing_rates(built):
    ctx, _ = built
    facts = [r for r in ctx.records.values() if r["type"] == "FACT"]
    assert facts
    for f in facts:
        assert "TrackCrime" in f["flags"] and "HiddenFromPC" in f["flags"]
        assert f["crime"]["murder"] > f["crime"]["assault"] > 0 and f["crime"]["stealMult"] > 0


def test_claywater_is_one_town():
    w = db.open()
    seats = w.query("SELECT faction_ref FROM place_faction_presence WHERE place_id = 'place.imperial-fringe.claywater-station' "
                    "AND role = 'seat'")
    assert [r["faction_ref"] for r in seats] == ["faction.claywater-station"]
