"""The quest form compiled from the built quests' records (tools/questform): each rule of compiling that the
walk 6 lanes found broken, proved on the records that broke it, and the rules over a set of forms."""

import pytest

from tools.argonia_world import db
from tools.questform import compile as qc
from tools.questform import rules

BUILT = ["quest.bc.bc01", "quest.bc.bc02", "quest.bc.bc03", "quest.local.lq25", "quest.local.lq30"]
DIVES = "npc.pirate-freeholds.opening-work-camp.n1-2"


@pytest.fixture(scope="module")
def world():
    return db.load()


@pytest.fixture(scope="module")
def forms(world):
    out = {}
    for q in BUILT:
        form, refused = qc.compile_quest(world, q)
        assert refused == [], (q, refused)
        out[q] = form
    return out


def lines_of(form, topic, stage=None):
    return [ln for ln in form["lines"] if ln["id"].startswith(topic + "@")
            and (stage is None or ln["first_stage"] <= stage <= ln["last_stage"])]


def ref(form, rid):
    return next(r for r in form["refs"] if r["id"] == rid)


# -- the built quests fit, alone and as a set ---------------------------------------------------------------------------
def test_the_built_compile_and_pass_with_each_other_and_as_a_set(forms):
    for q, f in forms.items():
        assert rules.check(f, list(forms.values())) == [], q
    assert rules.check_set(list(forms.values())) == []


# -- 9. an ending may change nothing in the world -------------------------------------------------------------------
def test_an_ending_with_no_world_imports():
    from tools.argonia_world.quest_record import export, import_record
    w = db.load()
    q = export(w, "quest.local.lq25")
    q["endings"][-1].pop("world", None)
    assert import_record(w, q) == [] and w.errors() == []


# -- 9. a death that would come late closes with the step it replaces ----------------------------------------------
def trigger(form, tid):
    return next(t for t in form["triggers"] if t["id"] == tid)


# -- a person must live until a stage --------------------------------------------------------------------------------
def _mn03(world, edit=None):
    """MN03's record (its YAML view; its places are not in the database yet): Heem-Jasa's death fails the quest at
    stages 10 to 50 and moves it to 92 from 60."""
    import yaml
    from pathlib import Path
    rec = yaml.safe_load(Path("newworld/story/quests/main/mn03.yaml").read_text(encoding="utf-8"))
    if edit:
        edit({s["id"]: s for s in rec["stages"]})
    real = qc.export
    qc.export = lambda w, q: rec
    try:
        c = qc.Compiler(world, rec["id"])
        try:
            c.compile()
        except Exception:                # the unplaced record may stop the compile after the stage pass
            pass
    finally:
        qc.export = real
    return c


HEEM = "npc.mn.heem-jasa"


def test_a_death_fails_the_quest_until_a_stage_and_moves_it_on_after(world):
    c = _mn03(world)
    assert not [r for r in c.refused if r[0] == "death both ways"]
    assert max(c.must_live_at[HEEM]) == 50 and c.death_moves[HEEM] == {60}
    row = next(m for m in c.windows([{"number": n, "shown": True, "ending": "none"} for n in (10, 20, 30, 40, 50, 60, 70)],
                                    {"stage": 10}, "main") if m["ref"] == HEEM)
    assert row["to"] == 50 and row["fail_stage"] == 96 and row["main_message"]


def _moves_at(n):
    def edit(stages):
        stages[n].setdefault("failForward", []).append({"to": 92, "when": {"not": {"npcAlive": HEEM}}})
    return edit


def test_a_death_that_fails_and_moves_the_quest_at_one_stage_is_refused(world):
    c = _mn03(world, _moves_at(30))
    assert any(r[0] == "death both ways" and HEEM in r[1] for r in c.refused)


def test_the_boundary_the_last_failing_stage_cannot_also_move(world):
    assert any(r[0] == "death both ways" for r in _mn03(world, _moves_at(50)).refused)
    def edit_after(stages):                 # the watch's last stage is 40; 50 and 60 move it on
        stages[50]["failForward"] = [f for f in stages[50]["failForward"] if f["to"] != 96]
        _moves_at(50)(stages)
    c = _mn03(world, edit_after)
    assert not [r for r in c.refused if r[0] == "death both ways"] and max(c.must_live_at[HEEM]) == 40
