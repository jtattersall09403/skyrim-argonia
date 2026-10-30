"""L1: a creature's den marker (place_build: the marker it owns is its sandbox centre). Claywater's crocodile dens on
the clay-cut bank by LF83's scour pool, so the fight is on foot (game-8: its 20 m sandbox around the cut's lip was
42% under water, it swam, and the player's blows never landed). The navmesh side is measured in the lane report
(docs/research/2026-10-30/lane-fixes-1.md): the den on our navmesh, the bank's path to it, the circle dry."""
import math

from tools.argonia_world import db

CROC = "creature-at.imperial-fringe.claywater-station.eco-crocodile"
POOL_DEPTH_M = 2.5  # LF83: a scour pool of 2.5 m or more
WATER_M = 32.84     # the water plan's surface there (build_ground's row)


def _den(w, npc_id):
    dens = [r for r in w.rows("build_ref") if r.owner_npc_id == npc_id and not r.npc_id]
    assert len(dens) <= 1, f"{npc_id}: {len(dens)} den markers"
    return dens[0] if dens else None


def test_every_den_marker_is_persistent_and_in_its_creatures_cell():
    w = db.open()
    for p in w.rows("build_person"):
        if w.get("npc", p.npc_id).kind != "creature":  # a person's owned references are their beds
            continue
        den = _den(w, p.npc_id)
        actor = next((r for r in w.rows("build_ref") if r.npc_id == p.npc_id), None)
        if den is None or actor is None:
            continue
        assert den.persistent, f"{den.id}: a package target must be persistent"
        assert den.cell_id == actor.cell_id


def test_claywater_crocodile_dens_on_the_bank_out_of_the_pool():
    w = db.open()
    p = w.get("build_person", CROC)
    den = _den(w, CROC)
    assert den is not None, "the crocodile has no den marker"
    pool = w.get("build_ground", "ground.claywater-station.scour-pool")
    assert WATER_M - pool.floor_m >= POOL_DEPTH_M  # the pool stays deep
    assert 0 < p.sandbox_radius_m <= 20.0           # LF83: territory 20 m at most
    d = math.hypot(den.x_m - pool.x_m, den.y_m - pool.y_m)
    # the sandbox circle stays more than 2 m outside the pool's flat floor (the old den, the cut's lip 6.5 m from the
    # pool's centre with a 20 m circle, failed this)
    assert d - p.sandbox_radius_m > pool.flat_radius_m + 2.0, d
    raft = w.get("build_ref", "ref.claywater-station.raft")  # the ford stays outside the territory
    assert math.hypot(den.x_m - raft.x_m, den.y_m - raft.y_m) > p.sandbox_radius_m
    actor = next(r for r in w.rows("build_ref") if r.npc_id == CROC)
    assert math.hypot(actor.x_m - den.x_m, actor.y_m - den.y_m) <= p.sandbox_radius_m


def _creature(flags, **extra):
    from tools.argonia_world import place_build as pb
    return [{"type": "NPC_", "edid": "ARG_Npc_C", "templateFlags": flags, **extra}]


def test_creature_without_templated_ai_carries_an_attack_radius():
    from tools.argonia_world import place_build as pb
    pb.check_creatures(_creature(pb.CREATURE_TEMPLATE_FLAGS, **pb.CREATURE_AI))
    assert pb.CREATURE_AI["aggro"]["attack"] > 0 and "AIData" not in pb.CREATURE_TEMPLATE_FLAGS


def test_old_flags_fail_on_purpose():  # the old flags (AIData templated) left the record with no radius of its own
    import pytest
    from tools.argonia_world import place_build as pb
    old = [f for f in pb.CREATURE_TEMPLATE_FLAGS] + ["AIData"]
    with pytest.raises(ValueError, match="no attack radius"):
        pb.check_creatures(_creature(old))
