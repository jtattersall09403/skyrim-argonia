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


# -- the talk that drives stage 30 (the lines, first match in id order, as the topic store answers) --------------

LIVIA = "npc.imperial-fringe.claywater-station.well-keeper"
SIGNS = "npc.imperial-fringe.claywater-station.landing-s-poler"
TAKES = "npc.imperial-fringe.claywater-station.n1-3"
CROC = "creature-at.imperial-fringe.claywater-station.eco-crocodile"


def _lines(w, speaker):
    from tools.argonia_world import lines as L
    return sorted(L.export(w, speaker)["lines"], key=lambda ln: ln["id"])


def _answer(lines, topic, s, objectives):
    """The line the speaker gives: the first conditioned line that holds, in id order, then a plain one."""
    mine = [ln for ln in lines if ln.get("topic") == topic]
    for ln in [x for x in mine if x.get("available")] + [x for x in mine if not x.get("available")]:
        if not ln.get("available") or S.holds(ln["available"], s, objectives):
            return ln
    return None


def _deliver(ln, speaker, s):
    s.heard.add((ln["topic"], speaker))
    for a in ln.get("onDelivered") or []:
        (verb, args), = a.items()
        args = args if isinstance(args, list) else [args]
        if verb == "setFlag":
            s.flags[args[0]] = args[1] if len(args) > 1 else True
        elif verb == "takeItem":
            s.items[args[0]] = s.items.get(args[0], 0) - (args[1] if len(args) > 1 else 1)
        elif verb == "takeGold":
            s.gold -= args[0]
        elif verb == "giveItem":
            s.items[args[0]] = s.items.get(args[0], 0) + (args[1] if len(args) > 1 else 1)


@pytest.fixture(scope="module")
def talk(w):
    q = Q.export(w, LF83)
    objectives = {(LF83, o["id"]): o["completeWhen"] for s in q["stages"] for o in s.get("objectives") or []}
    stages = {s["id"]: s for s in q["stages"]}
    return objectives, stages, {p: _lines(w, p) for p in (LIVIA, SIGNS, TAKES)}


def _stage30(speechcraft):
    # the yearly mending found by the crack (no talk with Signs about the clay), the basket back, the croc dead
    return S.State(flags={"flag.lf83.crack-seen": True}, items={"item.lf83.clay-basket": 1}, dead={CROC},
                   stages={LF83: 30}, skills={"speechcraft": speechcraft})


def test_lf83_persuasion_route_reaches_the_settlement(talk):
    objectives, stages, lines = talk
    s = _stage30(30)
    s.flags["flag.lf83.crack-seen"] = False
    s.flags["flag.lf83.tub-seen"] = True          # the mortar tub alone: no evidence Signs accepts
    said = []
    for who in (SIGNS, SIGNS, LIVIA, LIVIA):
        ln = _answer(lines[who], "topic.lf83-one-charge", s, objectives)
        said.append(ln["id"].rsplit(".", 1)[-1])
        _deliver(ln, who, s)
    assert said == ["argued", "agrees", "argued", "agree"]
    assert s.flags["flag.lf83.poler-persuaded"] and s.flags["flag.lf83.livia-persuaded"]
    assert s.items["item.lf83.clay-basket"] == 0
    assert S.step(stages[30], s, objectives) == 40


def test_lf83_no_persuasion_below_speechcraft_30(talk):
    objectives, stages, lines = talk
    s = _stage30(29)
    s.flags["flag.lf83.crack-seen"] = False
    s.flags["flag.lf83.tub-seen"] = True
    assert _answer(lines[SIGNS], "topic.lf83-one-charge", s, objectives)["id"].endswith(".no-seal")
    assert _answer(lines[LIVIA], "topic.lf83-one-charge", s, objectives)["id"].endswith(".open-stone")


def test_lf83_livia_persuaded_still_needs_the_landing(talk):
    objectives, stages, lines = talk
    s = _stage30(30)
    s.flags["flag.lf83.livia-persuaded"] = True    # her stone objection answered; the landing has promised nothing
    assert _answer(lines[LIVIA], "topic.lf83-one-charge", s, objectives)["id"].endswith(".open-half")


def test_lf83_pay_choice_once(talk):
    objectives, stages, lines = talk
    for who, gold, flag in ((SIGNS, 1, "flag.lf83.ford-paid"), (LIVIA, 2, "flag.lf83.stop-paid")):
        s = S.State(stages={LF83: 10}, gold=gold)
        first = _answer(lines[who], "topic.claywater-two-charges", s, objectives)
        assert not first["id"].endswith(".pay")              # the side is heard before anything is paid
        _deliver(first, who, s)
        pay = _answer(lines[who], "topic.claywater-two-charges", s, objectives)
        assert pay["id"].endswith(".pay")                     # asked again with the money: paid
        _deliver(pay, who, s)
        assert s.gold == 0 and s.flags[flag]
        s.gold = gold
        assert not _answer(lines[who], "topic.claywater-two-charges", s, objectives)["id"].endswith(".pay")


@pytest.mark.parametrize("who, endings, topics", [
    (LIVIA, (40, 41, 42, 90, 93), ("claywater-two-charges", "claywater-landing-terms", "lf83-cracked-well",
                                   "lf83-one-charge", "lf83-stop-charge")),
    (SIGNS, (40, 41, 42, 90, 92), ("claywater-two-charges", "claywater-landing-terms", "lf83-clay-bend",
                                   "lf83-one-charge", "lf83-ford-charge")),
    (TAKES, (40, 41, 42, 90, 92, 93), ("claywater-two-charges", "lf83-cracked-well", "lf83-clay-bend")),
])
def test_lf83_quest_topics_answer_after_every_ending(talk, who, endings, topics):
    objectives, stages, lines = talk
    for end in endings:
        for alive in (True, False):
            s = S.State(stages={LF83: end}, dead=set() if alive and end != 40 else {CROC})
            for t in topics:
                ln = _answer(lines[who], f"topic.{t}", s, objectives)
                assert ln is not None, (who, end, t)
                assert not ln.get("onDelivered"), (who, end, t, ln["id"])
                assert any(f"{t.split('-', 1)[1]}.{k}" in ln["id"] for k in ("after", "stage-4", "stage-9")), \
                    (who, end, t, ln["id"])
