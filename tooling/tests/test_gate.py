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


def test_story_markdown_runs_the_explorer_consistency_and_story_tests_only():
    p = gate.pick(["story/design/owner-bar.md"])
    assert not p.full
    assert p.stages == {"storyexplorer", "consistency"}  # the consistency checker reads the story pages too
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
    assert gate.pick(["tooling/gate_map.toml"]).full     # no base map to compare with
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


def test_records_quests_story_drafts_and_the_checker_run_the_consistency_stage():
    for path in ("newworld/story/data/db/place.jsonl", "newworld/sources/research/places/west.json",
                 "newworld/story/quests/main/mn01.yaml", "story/design/quests/lines/main-plot.md",
                 "newworld/places/helstrom/place.json", "story/data/db/faction.jsonl",
                 "tools/newworld/consistency.py", "tools/newworld/record_check.py"):
        p = gate.pick([path])
        assert "consistency" in p.stages, path
        assert p.full or "tools/tests/test_newworld_consistency.py" in p.tests, path


MAP_TEXT = (REPO / "tooling" / "gate_map.toml").read_text()
NEW_RULE = '\n[[rule]]\nglobs = ["tools/zzz/*"]\ntests = ["tooling/tests/test_gate.py"]\n'


def _pick_map(new_text, tmp_path):
    m = tmp_path / "map.toml"
    m.write_text(new_text)
    return gate.pick(["tooling/gate_map.toml"], mapfile=m, base_map=MAP_TEXT)


def test_a_map_edit_adding_one_entry_runs_that_entrys_tests_not_everything(tmp_path):
    p = _pick_map(MAP_TEXT + NEW_RULE, tmp_path)
    assert not p.full and p.tests == {"tooling/tests/test_gate.py"} and not p.stages
    assert "tools/zzz/*" in gate.summary(p, 100)


def test_a_map_edit_to_the_full_list_a_stage_or_named_direct_runs_everything(tmp_path):
    assert _pick_map(MAP_TEXT.replace("full = [", 'full = [\n  "extra.txt",'), tmp_path).full
    assert _pick_map(MAP_TEXT.replace('atlas = "tools.newworld.atlas_state"', 'atlas = "tools.newworld.map_page"'), tmp_path).full
    assert _pick_map(MAP_TEXT.replace("named_direct = [", 'named_direct = ["x/y.py", '), tmp_path).full


def test_a_removed_entry_runs_the_tests_it_named_if_they_still_exist(tmp_path):
    base = MAP_TEXT + '\n[[rule]]\nglobs = ["tools/zzz/*"]\nstages = ["skse"]\ntests = ["tooling/tests/test_gate.py", "tooling/tests/gone.py"]\n'
    m = tmp_path / "map.toml"
    m.write_text(MAP_TEXT)
    p = gate.pick(["tooling/gate_map.toml"], mapfile=m, base_map=base)
    assert not p.full and p.tests == {"tooling/tests/test_gate.py"} and p.stages == {"skse"}


def test_a_map_edit_merges_with_the_other_changed_files(tmp_path):
    m = tmp_path / "map.toml"
    m.write_text(MAP_TEXT + NEW_RULE)
    p = gate.pick(["tooling/gate_map.toml", "docs/PLAN.md"], mapfile=m, base_map=MAP_TEXT)
    assert not p.full and "tooling/tests/test_gate.py" in p.tests and "storyexplorer" in p.stages


def test_the_gate_code_still_runs_everything_with_a_map_edit():
    assert gate.pick(["tooling/gate_map.toml", "tooling/gate.py"], base_map=MAP_TEXT).full


def test_a_full_run_is_refused_without_a_deploy_or_a_phase_close(capsys):
    assert gate.main(["run", "--all"]) == 2
    assert gate.main(["run", "--all", "--why", "landing"]) == 2
    assert "only for a deploy or a phase's close" in capsys.readouterr().err
    import subprocess
    r = subprocess.run(["make", "-s", "full-why", "WHY=landing"], cwd=REPO, capture_output=True, text=True)
    assert r.returncode != 0 and "GATE_BASE=origin/main" in r.stderr
    assert subprocess.run(["make", "-s", "full-why", "WHY=phase-close"], cwd=REPO).returncode == 0


def test_a_full_run_the_change_forces_names_the_file_that_forced_it():
    line = gate.summary(gate.pick(["Makefile"]), 10)
    assert line.startswith("gate: FULL") and "Makefile" in line and "expected only when such a file changes" in line
