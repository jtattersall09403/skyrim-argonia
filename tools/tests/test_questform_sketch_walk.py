"""The sketch's reach walk (tools/questform/sketch.py, tools/playtest/walk.py): a quest's result is kept until its
sketch, or the sketch of a quest it waits on, or the walker changes; a walk that runs out of time says what it did not
reach and how far it searched; a search kept for more goals answers each set as a search for that set alone."""
from tools.playtest import walk
from tools.playtest import world as W
from tools.questform import sketch
from tools.tests.test_questform_sketch import GOOD

SECOND = '''
```sketch
quest T02 minor "The Second Toll"
start game 0

place hall indoors "Sarel's hall"
place shed indoors "the toll shed"

person giver at hall "Sarel"
thing ledger at shed "the toll ledger"

stage 0 hidden
stage 10 "Sarel wants the toll ledger from the shed."
stage 90 completed "I gave Sarel the toll ledger." do take ledger
stage 95 failed "Sarel is dead."

objective 10 at 10 "Bring Sarel the toll ledger" -> ledger, giver

line job2 giver at 0 ask "More work?" if done T01 90 -> 10 says "the ledger"
line hand2 giver at 10 ask "Here is the ledger." if holds ledger -> 90 says "she reads it"

must-live giver fails 95
```
'''


def walked(monkeypatch) -> list[str]:
    """The quests each later check walks (rather than reads from the cache)."""
    out = []
    reach = walk.reach

    def spy(forms, *a, **k):
        out.extend(sorted(k.get("only") or []))
        return reach(forms, *a, **k)
    monkeypatch.setattr(walk, "reach", spy)
    return out


def check(p, cache):
    faults = sketch.check(p, cache=cache)
    assert {f["rule"] for f in faults} == {"_ok"}, [f["message"] for f in faults]


def test_the_cache_walks_again_only_what_changed(tmp_path, monkeypatch):
    p, cache = tmp_path / "story.md", tmp_path / "cache"
    p.write_text(GOOD + SECOND, encoding="utf-8")
    seen = walked(monkeypatch)
    check(p, cache)
    assert seen == ["T01", "T02"]                            # T02 waits on T01: both walked
    seen.clear()
    check(p, cache)
    assert seen == []                                        # nothing changed: nothing walked
    p.write_text(GOOD + SECOND.replace("she reads it", "she reads it twice"), encoding="utf-8")
    check(p, cache)
    assert seen == ["T02"]                                   # a changed block: that quest alone
    seen.clear()
    p.write_text(GOOD.replace("give-gold 50", "give-gold 60") + SECOND.replace("she reads it", "she reads it twice"),
                 encoding="utf-8")
    check(p, cache)
    assert seen == ["T01", "T02"]                            # a quest waited on changed: it and those after it
    seen.clear()
    sketch.check(p, cache=None)
    assert seen == ["T01", "T02"]                            # no cache: everything walked


def test_a_walk_out_of_time_says_what_it_did_not_reach(tmp_path):
    p = tmp_path / "story.md"
    p.write_text(GOOD, encoding="utf-8")
    faults = sketch.check(p, cache=tmp_path / "cache", time_limit=0)
    late = [f for f in faults if f["rule"] == "reach-time"]
    assert len(late) == 1 and not any(f["rule"] == "_ok" for f in faults)
    msg = late[0]["message"]
    assert "limit of 0 s" in msg and "states searched" in msg and "stage 10 for the able character" in msg
    assert late[0]["line"] == 4 and late[0]["gloss"]         # on the quest's own line, with what it means
    assert not list((tmp_path / "cache").glob("rows-*"))    # a walk cut short is never kept
    text, n = sketch.report(p, faults)
    assert n == 1 and "passes" not in text


def test_a_kept_search_answers_as_a_search_for_those_goals_alone(tmp_path):
    p = tmp_path / "story.md"
    p.write_text(GOOD, encoding="utf-8")
    form, _ = sketch.expand(sketch.read(p)[0])
    form.pop("_errors")

    def game():
        g = walk.game_on({"T01": form}, ["T01"], W.snapshot([form], use_db=False), None, walk.ABLE)
        g.s["gold"] = walk.GOLD
        return g

    def goal(n):
        return lambda st: n in (st["quests"].get("T01") or {}).get("done", [])
    kept = walk.Search(game(), walk._ended("T01"), walk.MAX_STATES, {r["id"] for r in form["refs"]})
    for goals in ({"a": goal(30)}, {"b": goal(10), "c": goal(90)}, {"d": goal(95), "e": goal(20)}):
        g = game()
        alone = walk.search(g, goals, walk._ended("T01"), walk.MAX_STATES, {r["id"] for r in form["refs"]})
        assert kept.answer(goals) == alone
