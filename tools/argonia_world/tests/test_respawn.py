"""L1: who respawns (owner 2026-10-30; docs/research/2026-10-30/respawn-rulings.md). Each actor's class is its
statblock's `respawn`; `onRest` becomes the NPC_ Respawn flag; a clearable place's actors never respawn."""
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


def test_clearable_places_never_respawn(w):
    assert checks.respawn_clearable(w) == []
    assert w.values("SELECT count(*) FROM npc_statblock WHERE respawn = 'untilCleared'") == [0]
