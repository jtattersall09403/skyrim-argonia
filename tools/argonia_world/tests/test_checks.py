"""The named checks (checks.py) each refuse the violation they name, on the real world with one bad row added;
the world-reads check refuses a tool that names a world/ path."""
import pytest

from tools.argonia_world import check_world_reads, checks, db


@pytest.fixture(scope="module")
def world():
    return db.open()


@pytest.fixture
def w(world):
    yield world
    world.con.rollback()


def test_real_world_is_green(world):
    assert checks.run(world) == []


def test_lock_owner(w):
    w.update("lock", "lock.bog-iron-workings.container-iron-stock", owner_kind="faction", owner_id="npc.nobody")
    assert any("has no row in faction" in e for e in checks.run(w, ["lock-owner"]))


def test_journal_grounding(w):
    w.insert("journal_entry_grounding", journal_entry_id="text.journal.bc05.10", ord=99, value="fact.nowhere")
    assert checks.run(w, ["journal-grounding"]) == [
        "[journal-grounding] journal_entry text.journal.bc05.10: groundedIn 'fact.nowhere' is neither a fact nor a "
        "promise"]


def test_quest_topic(w):
    w.insert("quest_essential_topic", quest_id="quest.bc.bc01", ord=99, value="topic.nowhere")
    errs = checks.run(w, ["quest-topic"])
    assert errs and "essential topic 'topic.nowhere'" in errs[0]


def test_term_arity(w):
    w.insert("condition_arg", condition_id="quest_fail_forward:quest.bc.bc05|0|0:when.0.0", ord=9, value="extra")
    w.insert("action_arg", list_id="dialogue_line:pool.bog-iron-deep-end.start:on_delivered", ord=0, arg_ord=9,
             value="extra")
    errs = checks.run(w, ["term-arity"])
    assert any("npcAlive takes 1-1 argument(s), has 2" in e for e in errs)
    assert any("action dialogue_line:pool.bog-iron-deep-end.start:on_delivered[0]" in e for e in errs)


def test_save_refuses_a_failing_check(w):
    w.insert("journal_entry_grounding", journal_entry_id="text.journal.bc05.10", ord=99, value="fact.nowhere")
    with pytest.raises(db.LoadError):
        w.save()


@pytest.mark.parametrize("shape,want", [("none", (0, 0)), ("flag `id`, `bool`", (1, 2)),
                                        ("item `id` *or* slot `id` + tag `id`", (1, 2)),
                                        ("month `id` (a, b), optional day `int`", (1, 2)),
                                        ("quest `id`, `op`, stage `int`", (3, 3))])
def test_arity(shape, want):
    assert checks.arity(shape) == want


def test_world_reads(tmp_path):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "ok.py").write_text("from tools.argonia_world import db\n")
    assert check_world_reads.scan(tmp_path) == []
    w_ = "wor" + "ld"     # built, so this test is not itself a hit
    (tmp_path / "tools" / "bad.py").write_text(f'p = REPO / "{w_}" / "sources" / "x.json"\nq = "{w_}/db/npc.jsonl"\n')
    (tmp_path / "tools" / "ok.md").write_text(f"read the lore (`../{w_}/sources/lore/`) and tools/argonia_{w_}/db.py\n")
    assert [h.split(":")[1] for h in check_world_reads.scan(tmp_path)] == ["1", "2"]
