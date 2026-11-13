"""The echo check and the briefs' 'Already said near you' (tools/argonia_world/echoes.py)."""
from types import SimpleNamespace as NS

from tools.argonia_world import echoes
from tools.argonia_world.echoes import Speech

HOLD = "MQ01 stage 10 at lilmoth"


def sp(name, facts=(), texts=(), windows=(HOLD,), key=None, topic="t", source="quest_lines/mq01.json", order=0):
    return Speech(source, key or f"{name}-{topic}", echoes.ident(name), name, topic, list(texts), list(facts),
                  set(windows), order)


def test_words_fold_numbers_and_compass():
    assert echoes.words("Walk twenty-five paces north-north-east") == ["walk", "#", "paces", "~"]


def test_planted_fact_repeat_is_a_cluster():
    items = [sp("Wuleen-Sei", ["fact.mq01.owing-roll"]), sp("Ux-Xeek", ["fact.mq01.owing-roll"])]
    found = echoes.clusters(items)
    assert [(c.kind, c.what, c.speakers) for c in found] == [("fact", "fact.mq01.owing-roll", ["Ux-Xeek", "Wuleen-Sei"])]


def test_planted_clause_repeat_is_a_cluster():
    a = "Every hand in this gang owes months of work to the broker."
    items = [sp("Buys-The-Months", texts=[a]), sp("Ux-Xeek", texts=["Listen. " + a.lower()])]
    found = echoes.clusters(items)
    assert found and all(c.kind == "clause" for c in found)


def test_no_cluster_across_windows_or_for_one_speaker():
    items = [sp("Wuleen-Sei", ["f"]), sp("Ux-Xeek", ["f"], windows=["MQ01 stage 40 at hereguard"]),
             sp("Wuleen-Sei", ["f"], topic="other")]
    assert echoes.clusters(items) == []


def test_glue_and_route_runs_are_not_clauses():
    a = ["Walk about twenty paces south-south-east of here and you are there."]
    b = ["Walk about forty paces south-south-east of here and you are there."]
    assert echoes.shared_clauses(a, b) == []


def test_allow_list_names_fact_and_speakers():
    items = [sp("Azum-Kai", ["fact.dock5.rumours.quest-lq25"]), sp("Counts-Every-Crate", ["fact.dock5.rumours.quest-lq25"])]
    allow = [{"fact": "fact.dock5.rumours.quest-lq25", "speakers": ["Azum-Kai", "Counts-Every-Crate"], "why": "hook"}]
    assert echoes.clusters(items, allow) == []
    assert echoes.clusters(items, [{**allow[0], "speakers": ["Azum-Kai"]}])   # a third teller is not allowed
    assert echoes.clusters(items, [{"fact": "fact.dock5.rumours.quest-lq25"}])  # no why, no allowance


def test_owner_is_first_in_play_order_and_others_leave_it():
    items = [sp("Wuleen-Sei", ["fact.mq01.owing-roll"], order=0), sp("Buys-The-Months", ["fact.mq01.owing-roll"], order=1)]
    assert echoes.owners(items)[(HOLD, "fact.mq01.owing-roll")].name == "Wuleen-Sei"
    brief = "\n".join(echoes.brief_section(items, "Buys-The-Months", {"fact.mq01.owing-roll": "months for food"}))
    assert "Wuleen-Sei" in brief and "you only point to Wuleen-Sei" in brief
    mine = "\n".join(echoes.brief_section(items, "Wuleen-Sei"))
    assert "Facts you leave" not in mine and "Buys-The-Months" in mine


def test_compact_windows():
    assert echoes.compact({"MQ01 stage 40 at x", "MQ01 stage 90 at x", "talk bmv.y"}) == "MQ01 stages 40, 90 at x; talk bmv.y"


class FakeWorld:
    def __init__(self):
        self.t = {
            "bmv_talker": [NS(id=r, settlement="bmv.s") for r in ("A", "B", "C")],
            "talker": [NS(id="A", known_as="Ann"), NS(id="B", known_as="Bo"), NS(id="C", known_as="Cy")],
            "talk_fact": [NS(id="f.owing", claim="A debt is paid in work.", settlement="bmv.s", source="lore:1"),
                          NS(id="f.other", claim="Other.", settlement="bmv.s", source="lore:2")],
            "talker_topic": [NS(talker="A", topic="talk.lore", facts="f.owing"),
                             NS(talker="B", topic="talk.lore", facts="f.other, f.owing"),
                             NS(talker="C", topic="talk.self", facts="")],
        }
        self.saved = False

    def rows(self, table, **where):
        return [r for r in self.t[table] if all(getattr(r, k) == v for k, v in where.items())]

    def upsert(self, table, **cols):
        self.t[table].append(NS(**cols))

    def update(self, table, talker, topic, facts):
        next(r for r in self.t[table] if r.talker == talker and r.topic == topic).facts = facts

    def save(self):
        self.saved = True


def test_assign_keeps_one_holder_and_points_the_rest(monkeypatch):
    monkeypatch.setattr(echoes, "load_allow", lambda *a: [])
    w = FakeWorld()
    plan = echoes.assign(w, "bmv.s", write=True)
    assert plan == ["bmv.s f.owing: Bo (talk.lore) points to Ann"]
    assert w.rows("talker_topic", talker="B")[0].facts == "f.other, f.owing.ask-b"
    ptr = w.rows("talk_fact", id="f.owing.ask-b")[0]
    assert ptr.claim.startswith("Ask Ann about it") and ptr.source.startswith(echoes.POINTER) and w.saved
    assert echoes.assign(w, "bmv.s") == []


def test_one_speaker_twice_across_topics_but_not_across_variants():
    t = ["The roll burnt in the camp's fire and nobody can show what they owe."]
    twice = [sp("Nesh-Deeka", texts=t, key="topic.a#main"), sp("Nesh-Deeka", texts=t, key="topic.b#main")]
    assert [c.kind for c in echoes.clusters(twice)] == ["again"]
    variants = [sp("Nesh-Deeka", texts=t, key="topic.a#x"), sp("Nesh-Deeka", texts=t, key="topic.a#y")]
    assert echoes.clusters(variants) == []


def test_greetings_that_open_alike_are_one_row_per_window():
    g = [sp(n, texts=[x], topic="talk.greet-friend", source="talk_line", windows=["talk bmv.s"])
         for n, x in (("A", "You came back, my friend. Sit."), ("B", "You are back, my friend!"),
                      ("C", "Back again, friend? Good."), ("D", "The water is high today."))]
    found = echoes.clusters(g)
    assert [(c.kind, c.speakers) for c in found] == [("opening", ["A", "B", "C"])]


def test_two_routes_past_one_landmark_are_not_an_echo():
    d = ["Walk east some forty paces until the burnt-out house is on your left, then on to the dock."]
    items = [sp("A", texts=d, topic="talk.directions", source="talk_line"),
             sp("B", texts=d, topic="talk.directions", source="talk_line")]
    assert echoes.clusters(items) == []
