"""tooling/gate.py: the scoped gate picks what a change reaches, and falls back to everything when unsure."""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("gate", REPO / "tooling" / "gate.py")
gate = importlib.util.module_from_spec(_spec)
sys.modules["gate"] = gate
_spec.loader.exec_module(gate)

STORY = {"tools/tests/test_newworld_story_explorer.py", "tools/tests/test_newworld_plot_check.py",
         "tools/tests/test_places_needs.py", "tools/tests/test_newworld_story_digest.py"}


def test_story_markdown_runs_the_explorer_and_story_tests_only():
    p = gate.pick(["story/design/owner-bar.md"])
    assert not p.full
    assert p.stages == {"storyexplorer"}
    assert STORY <= p.tests
    assert len(p.tests) < 15
    assert "tooling/tests/test_job_guard.py" not in p.tests


def test_docs_markdown_is_scoped():
    p = gate.pick(["docs/PLAN.md"])
    assert not p.full and p.stages == {"storyexplorer"} and STORY <= p.tests


def test_skse_change_runs_the_skse_check_alone():
    p = gate.pick(["skse/ArgoniaDodgeBuffer/core/buffer.h"])
    assert not p.full and p.stages == {"skse"} and p.tests <= {"tooling/tests/test_gate.py"}


def test_unknown_path_runs_everything():
    p = gate.pick(["somewhere/new.txt"])
    assert p.full and "matches no rule" in p.reason


def test_map_or_gate_change_runs_everything():
    assert gate.pick(["tooling/gate_map.toml"]).full
    assert gate.pick(["tooling/gate.py"]).full
    assert gate.pick(["tools/tests/conftest.py"]).full


def test_module_change_runs_the_tests_that_import_it():
    p = gate.pick(["tools/newworld/story_explorer.py"])
    assert not p.full
    assert "tools/tests/test_newworld_story_explorer.py" in p.tests
    assert "storyexplorer" in p.stages


def test_quest_data_runs_the_quest_stages():
    p = gate.pick(["story/data/quest_lines/mq01.json"])
    assert {"adaptation", "questtext", "questform", "reach"} <= p.stages


def test_picker_error_runs_everything(monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("broken map")
    monkeypatch.setattr(gate, "pick", boom)
    assert gate.main(["plan", "docs/PLAN.md"]) == 0
    assert "FULL" in capsys.readouterr().out


def test_bad_map_entry_errors(tmp_path):
    m = tmp_path / "map.toml"
    m.write_text('full = []\n[[rule]]\nglobs = ["docs/*"]\ntests = ["tools/tests/no_such_test.py"]\n')
    try:
        gate.pick(["docs/x.md"], mapfile=m)
    except FileNotFoundError:
        return
    raise AssertionError("a missing test in the map must raise (and so run everything)")


def test_import_closure_follows_relative_imports_and_path_chains(tmp_path):
    (tmp_path / "tools" / "pkg").mkdir(parents=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "tools" / "__init__.py").write_text("")
    (tmp_path / "tools" / "pkg" / "__init__.py").write_text("")
    (tmp_path / "tools" / "pkg" / "a.py").write_text("from . import b\n")
    (tmp_path / "tools" / "pkg" / "b.py").write_text('X = ROOT / "data" / "things"\n')
    files, named = gate.Index(tmp_path).closure(tmp_path / "tools" / "pkg" / "a.py")
    assert "tools/pkg/b.py" in files and "data/things" in named


def test_every_mapped_stage_is_a_stage_with_a_make_target():
    import re
    import tomllib
    m = tomllib.loads((REPO / "tooling" / "gate_map.toml").read_text())
    named = set(m.get("stages", {}))
    for rule in m.get("rule", []):
        named |= set(rule.get("stages", []))
    makefile = (REPO / "Makefile").read_text()
    targets = set(re.findall(r"^([A-Za-z0-9_-]+):", makefile, re.M))
    check_all = re.search(r"^check-all:(.*)$", makefile, re.M).group(1).split()
    for s in named:
        assert s in gate.STAGES, s
        assert s == "skse" or s in targets, s
        assert s == "skse" or s in check_all, s
