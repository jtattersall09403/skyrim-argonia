"""A place's plan (`draft.plan`, one shape held by tools/places/draft/plan.py): every row delivered, a gives row for
each promise of the record, a verdict on each major source structure and standing cluster, and a dropped structure
dropped piece by piece."""
from tools.places.draft import plan

GIVES = [{"kind": "trader-general"}, {"kind": "cooking-pot"}]
STRUCT = {"walls": {"refs": ["w1", "w2"]}, "harbour": {"refs": ["d1"]}}
FULL = {"look": [{"line": "pale stilt houses", "by": "the source's thatch houses"}],
        "gives": [{"kind": "trader-general", "by": "the market hut"}, {"kind": "cooking-pot", "by": "an added pot"}],
        "structures": [{"structure": "walls", "what": "the town wall", "verdict": "dropped", "why": "no wall"},
                       {"structure": "harbour", "what": "the jetty", "verdict": "kept", "why": "on the stream"},
                       {"cluster": "s01,s02", "what": "houses", "verdict": "kept", "why": "the record's houses"},
                       {"cluster": "s09", "what": "a trap field", "verdict": "dropped", "why": "a friendly camp"}]}


def causes(bad):
    return {c for c, _ in bad}


def test_a_whole_plan_has_no_faults():
    assert plan.faults(FULL, GIVES, STRUCT, {"w1": "x", "w2": "x"}, {"s01", "s02"}) == []


def test_each_fault_is_named():
    part = {"look": [{"line": "x", "by": ""}], "gives": FULL["gives"][1:], "structures": FULL["structures"][:1] +
            FULL["structures"][3:] + [{"what": "a hall"}]}
    bad = plan.faults(part, GIVES, STRUCT, {"w1": "x"}, {"s01", "s09"})
    text = " | ".join(d for _, d in bad)
    assert causes(bad) == {plan.UNDELIVERED, plan.NO_GIVE, plan.NO_VERDICT, plan.STANDS}
    assert "trader-general" in text and "harbour" in text and "cluster s01" in text and "cluster s09" in text
    assert "walls is dropped but 1" in text


def test_no_plan_or_another_shape_is_missing():
    for p in (None, {}, [{"thing": "x", "by": "y"}]):
        assert causes(plan.faults(p, GIVES)) == {plan.MISSING}
