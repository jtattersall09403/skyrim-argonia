"""A place's plan (`draft.plan`) has a line for each promise of its record and a verdict on each major source
structure; a structure it drops is dropped piece by piece (tools/places/draft/plan.py)."""
from tools.places.draft import plan

GIVES = [{"kind": "trader-general"}, {"kind": "cooking-pot"}]
STRUCT = {"walls": {"kept": False, "refs": ["w1", "w2"]}, "harbour": {"kept": True, "refs": ["d1"]}}
FULL = [{"thing": "a general trader at the jetty market", "by": "the market hut", "gives": "trader-general"},
        {"thing": "a cooking pot at the fish racks", "by": "an added pot", "gives": "cooking-pot"},
        {"thing": "the town wall", "by": "dropped", "structure": "walls", "kept": False},
        {"thing": "the jetty", "by": "the source's docks", "structure": "harbour", "kept": True}]


def test_a_whole_plan_has_no_faults():
    assert plan.faults(FULL, GIVES, STRUCT, {"w1": "x", "w2": "x"}) == []


def test_a_missing_promise_a_missing_verdict_and_a_half_dropped_structure_are_named():
    bad = plan.faults(FULL[1:3], GIVES, STRUCT, {"w1": "x"})
    assert any("trader-general has no line" in b for b in bad)
    assert any("harbour" in b and "no verdict" in b for b in bad)
    assert any("walls is dropped but 1" in b for b in bad)
    assert plan.faults([{"thing": "x"}], [], {}, {}) == ["plan line 0: a line names the thing and what delivers it"]
