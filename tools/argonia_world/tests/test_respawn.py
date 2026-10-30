"""L1: who respawns (owner 2026-10-30; docs/research/2026-10-30/respawn-rulings.md). Each actor's class is its
statblock's `respawn`; `onRest` and `untilCleared` become the NPC_ Respawn flag; a clearable place's actors respawn
until the place is cleared (`untilCleared`) or never."""
from __future__ import annotations

import pytest

from tools.argonia_world import checks, db
from tools.argonia_world import combat_records as cr
from tools.argonia_world.place_build import respawns
from tools.argonia_world.tests.test_combat_records import ARCH, FakeAlloc

CROC = "creature-at.imperial-fringe.claywater-station.eco-crocodile"


@pytest.fixture(scope="module")
def w():
    return db.open()


def test_every_placed_enemy_has_a_class(w):
    placed = [r[0] for r in w.query("SELECT DISTINCT npc_id FROM build_ref WHERE npc_id IS NOT NULL")]
    assert placed
    missing = [n for n in placed if w.get("npc_statblock", n) is None]
    assert missing == []


def test_crocodile_never_respawns(w):
    assert w.get("npc_statblock", CROC).respawn == "never"
    assert not respawns(w, CROC)


def test_deserter_respawns_on_rest_by_the_native_flag(w):
    assert w.get("npc_statblock", ARCH).respawn == "onRest"
    npc = next(r for r in cr.archetype_records(FakeAlloc(), w, ARCH) if r["type"] == "NPC_")
    assert npc["flags"] == ["Respawn"]


def test_clearable_places_respawn_until_cleared(w):
    assert checks.respawn_clearable(w) == []
    assert w.values("SELECT count(*) FROM npc_statblock WHERE respawn = 'untilCleared'") == [41]
    sb = w.values("SELECT npc_id FROM npc_statblock WHERE respawn = 'untilCleared' LIMIT 1")[0]
    assert respawns(w, sb)  # the native flag; the cleared LCTN and the roster stop it


def test_respawn_clearable_fails_on_onRest(w):
    """The named check fails an `onRest` actor homed in a clearable place."""
    sql = []
    class W:
        def query(self, q, *a):
            sql.append(q)
            return [("x", "onRest", "place.p")]
    assert checks.respawn_clearable(W()) == ["npc_statblock x: respawn 'onRest' in clearable place.p; must be "
                                             "'untilCleared' or 'never'"]
    assert "NOT IN ('untilCleared', 'never')" in sql[0]
    assert w.values("SELECT count(*) FROM npc_statblock s JOIN npc n ON n.id = s.npc_id JOIN place_build_hostility h "
                    "ON h.place_id = n.home_place_id WHERE h.clearable = 1 AND s.respawn = 'onRest'") == [0]


class _Clearable:
    """The world with the archetype's home place made clearable."""

    def __init__(self, w, clearable):
        self.w, self.clearable = w, clearable

    def get(self, table, key):
        row = self.w.get(table, key)
        if table == "place_build_hostility" and row is not None:
            return row.__class__(**{**row.__dict__, "clearable": self.clearable}) if hasattr(row, "__dict__") else row
        return row

    def __getattr__(self, name):
        return getattr(self.w, name)


def test_clearable_home_zone_never_resets(w):
    """A clearable place's encounter zone carries ECZN Never Resets; any other zone carries no flag."""
    zone = next(r for r in cr.archetype_records(FakeAlloc(), w, ARCH) if r["type"] == "ECZN")
    assert not cr.home_clearable(w, ARCH) and "flags" not in zone
    home = w.get("npc", ARCH).home_place_id
    assert w.get("place_build_hostility", home) is not None
    zone = next(r for r in cr.archetype_records(FakeAlloc(), _Clearable(w, True), ARCH) if r["type"] == "ECZN")
    assert zone["flags"] == ["NeverResets"]


def test_untilCleared_is_reinstated(w):
    rows = {r.id: (bool(r.on_rest), bool(r.until_cleared)) for r in w.rows("core_respawn_class")}
    assert rows == {"never": (False, False), "onRest": (True, False), "untilCleared": (True, True)}
