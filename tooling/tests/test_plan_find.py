"""plan_find: one search over every place the plan lives, grouped by layer (a temporary tree stands in for the repo)."""
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def tree(tmp_path, monkeypatch):
    (tmp_path / "docs/decisions").mkdir(parents=True)
    (tmp_path / "newworld/story/data/db").mkdir(parents=True)
    (tmp_path / "story/design/quests/lines").mkdir(parents=True)
    (tmp_path / "docs/owner-rulings.md").write_text("- spellmaking, later\n- nothing here\n")
    (tmp_path / "docs/decisions/0012-x.md").write_text("The Shout key carries Hist communion powers.\n")
    (tmp_path / "newworld/story/data/db/place_give.jsonl").write_text(
        json.dumps({"place_id": "helstrom", "give_kind_id": "trader-spells", "detail": "tree-minder's healer: tomes"}) + "\n")
    (tmp_path / "newworld/story/data/db/cell.jsonl").write_text('{"id": "spell"}\n')
    (tmp_path / "story/design/quests/lines/a.md").write_text("She teaches a spell.\nShe sells a tome of a spell.\n")
    monkeypatch.setenv("PLAN_FIND_ROOT", str(tmp_path))
    import plan_find
    return importlib.reload(plan_find)


def test_a_topic_is_found_in_every_layer_that_holds_it(tmp_path, monkeypatch, capsys):
    pf = tree(tmp_path, monkeypatch)
    assert pf.main(["spell", "communion"]) == 0
    out = capsys.readouterr().out
    assert "== rulings: 1 lines in 1 files" in out and "spellmaking" in out
    assert "== decisions: 1 lines" in out and "communion powers" in out
    # a database row shows its ids and its prose; the bulk geometry tables are never searched
    assert "helstrom trader-spells: tree-minder's healer: tomes" in out and "cell.jsonl" not in out
    assert "== story: 2 lines in 1 files" in out and "== lore: 0 lines" in out


def test_all_words_one_layer_and_the_map(tmp_path, monkeypatch, capsys):
    pf = tree(tmp_path, monkeypatch)
    pf.main(["--all", "--layer", "story", "tome", "spell"])
    out = capsys.readouterr().out
    assert "== story: 1 lines" in out and "== records" not in out
    assert pf.main(["--map"]) == 0
    assert "not searched: the built game" in capsys.readouterr().out
    assert pf.main(["zzzz"]) == 0 and "try synonyms" in capsys.readouterr().out
