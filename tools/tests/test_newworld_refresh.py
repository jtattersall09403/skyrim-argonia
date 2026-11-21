"""tools/newworld/refresh: the tables, then the story digest, then the story explorer, in that order; idempotent
(nothing runs when nothing changed) and a dry run writes nothing. The steps' tools are stood in for."""
import json

from tools.newworld import refresh as R
from tools.newworld import story_digest as sd
from tools.newworld import story_explorer as se
from tools.newworld import atlas_state as at


def world(tmp_path, monkeypatch):
    root = tmp_path
    (root / R.DB).mkdir(parents=True)
    (root / R.DB / "place.jsonl").write_text('{"id": "a", "population": 10}\n')
    (root / R.WEALTH).parent.mkdir(parents=True)
    (root / R.WEALTH).write_text('{"places": []}\n')
    src = root / "newworld/sources/people/a.json"
    src.parent.mkdir(parents=True)
    src.write_text('{"people": []}\n')
    digest_out = root / "story/design/world"
    calls = []
    monkeypatch.setattr("tools.newworld.rebuild.DB_SOURCES", ("src:newworld/sources/**/*.json",))

    def run(*args, root):
        calls.append(args[0] + (" " + args[1] if len(args) > 1 else ""))
        if args[0] == "tools.newworld.build_db":   # the tables follow the source
            (root / R.DB / "place.jsonl").write_text(json.dumps({"id": "a", "src": src.read_text()}) + "\n")
        if args[:2] == ("tools.newworld.wealth", "derive"):
            (root / R.WEALTH).write_text(json.dumps({"places": [len(src.read_text())]}) + "\n")
    monkeypatch.setattr(R, "_run", run)

    def gen(out, today=None):
        calls.append(f"digest {'temp' if out != digest_out else 'write'}")
        out.mkdir(parents=True, exist_ok=True)
        (out / "places.md").write_text(f"# Places ({today or '2026-11-21'})\n" + (root / R.DB / "place.jsonl").read_text())
    monkeypatch.setattr(sd, "generate", gen)
    monkeypatch.setattr(sd, "OUT", digest_out)
    monkeypatch.setattr(sd, "REPO", root)
    state = {"explorer": "story explorer behind"}
    monkeypatch.setattr(se, "check", lambda r: state["explorer"])
    monkeypatch.setattr(se, "generate", lambda r: calls.append("explorer build"))
    monkeypatch.setattr(at, "check", lambda r: None)
    return root, src, calls, state


def test_the_chain_runs_in_order_then_is_idempotent(tmp_path, monkeypatch):
    root, src, calls, state = world(tmp_path, monkeypatch)
    said = []
    got = R.refresh(root, say=said.append)
    assert calls == ["tools.newworld.build_db", "tools.newworld.wealth derive", "tools.newworld.stockdb load",
                     "digest temp", "digest write", "explorer build"]
    assert got["changed"] == ["newworld/sources/stock/place_wealth.json", "newworld/story/data/db/place.jsonl"]
    assert got["digest"] == ["story/design/world/places.md"]
    assert any("story explorer: NEEDS REPUBLISHING" in s for s in said) and said[-1].startswith("commit by path:")
    # nothing changed: no table build, the digest only compared, nothing to commit
    calls.clear()
    state["explorer"] = None
    said.clear()
    got = R.refresh(root, say=said.append)
    assert calls == ["digest temp"] and not got["tables_stale"] and got["digest"] == []
    assert "tables: current" in said and "story explorer: published page current" in said
    # a source changes: the chain runs again
    src.write_text('{"people": [{"id": "a.p1"}]}\n')
    calls.clear()
    R.refresh(root, say=lambda s: None)
    assert calls[0] == "tools.newworld.build_db" and "digest write" in calls


def test_a_dry_run_writes_nothing(tmp_path, monkeypatch):
    root, src, calls, state = world(tmp_path, monkeypatch)
    said = []
    got = R.refresh(root, dry=True, say=said.append)
    assert got["tables_stale"] and calls == ["digest temp"] and not (root / R.STAMP).exists()
    assert said[0] == "tables: stale" and not any(s.startswith("commit by path") for s in said)
