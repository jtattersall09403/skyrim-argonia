"""L2: every branch of a quest's stage graph walked against its record (1.4; 2.12 §a), including the dead-NPC
fail-forward (old 0138). Each walked quest's every successor and fail-forward is driven by a state that satisfies
it, and the stage's rule (fail-forwards first, then successors, in record order) must take it."""
import pytest

from tools.argonia_world import db, quest_record as Q, stage_walk as S

LF83 = "quest.local.lf83"


@pytest.fixture(scope="module")
def w():
    world = db.open()
    yield world
    world.con.rollback()


def test_lf83_every_branch(w):
    r = S.walk(w, LF83)
    assert r.errors == []
    walked = {(a, b) for a, b, _, _ in r.edges}
    # the main path, the two other settlements, the deadline and each keeper's death, from every working stage
    for a in (10, 20, 30):
        assert {(a, 90), (a, 92), (a, 93), (a, 41)} <= walked
    assert {(10, 20), (20, 30), (30, 40), (30, 42)} <= walked
    assert {40, 41, 42, 90, 92, 93} <= r.reached


def test_lf83_death_overrides_progress(w):
    q = Q.export(w, LF83)
    st = {s["id"]: s for s in q["stages"]}[30]
    objectives = {(LF83, o["id"]): o["completeWhen"] for s in q["stages"] for o in s.get("objectives") or []}
    s = S.State(flags={"flag.lf83.one-charge-station": True, "flag.lf83.one-charge-landing": True},
                dead={"npc.imperial-fringe.claywater-station.landing-s-poler"})
    assert S.step(st, s, objectives) == 93
    s.dead = set()
    assert S.step(st, s, objectives) == 40


def _broken(w, mutate):
    """Walk a mutated copy of LF83's record (nothing written)."""
    q = Q.export(w, LF83)
    mutate(q)
    return S.walk_record(q).errors


def test_walk_fails_without_a_death_fail_forward(w):
    def drop(q):
        st = {s["id"]: s for s in q["stages"]}[10]   # its objective names the poler
        st["failForward"] = [e for e in st["failForward"] if e["to"] != 93]
    errs = _broken(w, drop)
    assert any("landing-s-poler but has no fail-forward" in e for e in errs)


def test_walk_fails_on_a_shadowed_edge(w):
    def shadow(q):
        st = {s["id"]: s for s in q["stages"]}[30]
        # an always-true successor ahead of the settlement makes 40 unreachable from 30
        st["successors"].insert(0, {"to": 41, "when": {"npcAlive": "npc.imperial-fringe.claywater-station.n1-3"}})
    errs = _broken(w, shadow)
    assert any("30 -> 40" in e and "takes 41" in e for e in errs)
