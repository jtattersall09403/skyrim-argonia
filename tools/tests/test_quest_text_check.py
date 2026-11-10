from tools.argonia_world import quest_text_check as q

Q = "quest.main.mq01"
ALLOW = {"rhetorical": [], "gives_ok": [], "retired": {Q: ["Hereguard", "shore path"]},
         "roles": {Q: {"the boat captain": "Sells-Dear"}}}


def it(kind, text, key="k", info=None, quest=Q):
    return q.Item(quest, key, kind, text, info or {})


def test_e1():
    assert q.e1([it("objective", "Go.", info={})])
    assert q.e1([it("objective", "Go.", info={"target": "  "})])
    assert not q.e1([it("objective", "Go.", info={"target": "none"})])
    assert not q.e1([it("objective", "Go.", info={"hidden": True})])


def test_e2():
    ok = "Hulm-Tei keeps the book. I'm to take it."
    assert not q.e2([it("journal", ok)])
    assert q.e2([it("journal", "Hulm-Tei keeps the book.")])
    assert q.e2([it("journal", "I'm to go. I am to wait.")])
    assert q.e2([it("journal", "I'm to go. " + "word " * 60)])
    assert not q.e2([it("ending", "It is done.")])


def test_e3():
    assert q.e3([it("spoken", "Who are you?")], ALLOW)
    assert q.e3([it("spoken", "Well. Tell me what you saw.")], ALLOW)
    assert not q.e3([it("spoken", "Who are you?", info={"replies": ["a"]})], ALLOW)
    allow = dict(ALLOW, rhetorical=[{"key": "k", "text": "Who are", "why": "x"}])
    assert not q.e3([it("spoken", "Who are you?")], allow)
    assert not q.e3([it("spoken", "I tell you plainly.")], ALLOW)


def test_e8():
    assert q.e8([it("journal", "Walk the Shore Path north.")], ALLOW)
    assert not q.e8([it("journal", "Walk the shorepath north.")], ALLOW)
    assert not q.e8([it("journal", "Hereguard.", quest="quest.other")], ALLOW)


def test_e9():
    sexes = {"Never-Sold": "female", "Hulm-Tei": "male"}
    bad = q.e9([it("spoken", "Never-Sold waits. He keeps the book.")], sexes)
    assert bad and all(h.warn for h in bad)
    two = q.e9([it("spoken", "Never-Sold asked Hulm-Tei. She waits.")], sexes)
    assert [h for h in two if h.warn]
    assert not q.e9([it("spoken", "Never-Sold waits. She keeps the book.")], sexes)


def test_e10():
    assert q.e10([it("prompt", "the boat")])
    assert q.e10([it("prompt", "Helstrom")])
    assert q.e10([it("prompt", "Tell me about the boat")])
    assert q.e10([it("prompt", "who is she?")])
    for ok in ("Why am I here?", "(Say nothing.)", "Put down the name I carry."):
        assert not q.e10([it("prompt", ok)])


def test_e16():
    assert q.e16([it("journal", "I'm to find the boat captain.")], ALLOW)
    assert not q.e16([it("journal", "I'm to find the boat captain, Sells-Dear.")], ALLOW)
    assert not q.e16([it("spoken", "The boat captain waits.")], ALLOW)


def test_e17():
    h = q.e17([it("spoken", "He left four hours ago.")])
    assert h and h[0].warn
    assert not q.e17([it("spoken", "He left.")])


def test_e18():
    assert q.e18([it("spoken", "Here is the key.")], ALLOW)
    assert not q.e18([it("spoken", "Here is the key.", info={"gives": ["key"]})], ALLOW)
    assert not q.e18([it("spoken", "Take the key.")], ALLOW)
    allow = dict(ALLOW, gives_ok=[{"key": "k", "why": "x"}])
    assert not q.e18([it("spoken", "Take this.")], allow)


def test_loaders(tmp_path):
    import json
    (tmp_path / "db").mkdir()
    (tmp_path / "quest_lines").mkdir()
    (tmp_path / "db" / "quest.jsonl").write_text(json.dumps({"id": Q, "code": "MQ01"}) + "\n")
    (tmp_path / "db" / "quest_stage.jsonl").write_text(
        json.dumps({"quest_id": Q, "ord": 0, "id": 10, "journal_text": "I'm to go."}) + "\n")
    (tmp_path / "db" / "quest_objective.jsonl").write_text(
        json.dumps({"quest_id": Q, "stages_ord": 0, "id": "a", "objective_text": "Go."}) + "\n")
    (tmp_path / "quest_lines" / "mq01.json").write_text(json.dumps(
        {"topic.x": {"speaker": "s", "infos": [{"prompt": "Why?", "lines": ["Here is a thing."], "gives": ["x"]}]}}))
    items = q.load(tmp_path)
    assert {i.kind for i in items} == {"prompt", "spoken", "journal", "objective"}
    assert q.e1(items) and not q.e18(items, ALLOW) and not q.e2(items)
