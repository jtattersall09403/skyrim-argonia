"""tooling/gate.py: the scoped gate picks what a change reaches, and falls back to everything when unsure."""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("gate", REPO / "tooling" / "gate.py")
gate = importlib.util.module_from_spec(_spec)
sys.modules["gate"] = gate
_spec.loader.exec_module(gate)

def _pl(place, rel):
    """A path in a place's folder, built so that this file does not itself name the folder (and so is not picked by
    every change to that place's files)."""
    return "newworld/places/%s/%s" % (place, rel)


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


def test_an_edits_only_change_picks_only_the_validity_check():
    for path in (_pl("jal-veesa", "edits/save-1.json"), _pl("jal-veesa", "edits/notes.jsonl"),
                 _pl("jal-veesa@pipeline", "edits/save-2.json")):
        p = gate.pick([path])
        assert not p.full and p.stages == {"editsvalid"} and p.tests == set(), path
        assert p.inert == [path]


def test_edits_beside_place_files_are_picked_as_the_place_files_are():
    p = gate.pick([_pl("jal-veesa", "edits/save-1.json"), _pl("jal-veesa", "place.json")])
    assert "consistency" in p.stages and "editsvalid" in p.stages and p.tests
    assert p.inert == [_pl("jal-veesa", "edits/save-1.json")]
    assert "consistency" in gate.pick([_pl("jal-veesa", "place.json")]).stages


QUEST_STAGES = {"questform", "reach", "questtext", "storyexplorer"}
TOOL_TESTS = {"tools/tests/test_playtest.py", "tools/tests/test_questform.py", "tools/tests/test_places_studio.py",
              "tools/tests/test_places_truth.py", "tools/tests/test_newworld_story_explorer.py"}


def test_one_places_refs_or_place_json_runs_its_data_checks_not_the_tools_or_the_quest_stages():
    for path in (_pl("jal-veesa", "spaces/exterior/refs.jsonl"), _pl("jal-veesa", "place.json"),
                 _pl("jal-veesa", "people.jsonl"), _pl("jal-veesa", "formids.json")):
        p = gate.pick([path])
        assert not p.full and p.stages == {"consistency"}, path
        assert "tools/tests/test_newworld_consistency.py" in p.tests, path
        assert not (p.tests & TOOL_TESTS) and len(p.tests) < 15, (path, sorted(p.tests))


def test_a_place_file_the_quest_compiler_or_the_explorer_reads_runs_the_quest_stages():
    for path in (_pl("jal-veesa", "quests.jsonl"), _pl("jal-veesa", "ledger.jsonl")):
        p = gate.pick([path])
        assert not p.full and QUEST_STAGES | {"consistency"} == p.stages, path


def test_a_tree_root_file_and_a_place_the_code_names_still_pick_by_name():
    assert "tools/tests/test_places_truth.py" in gate.pick(["newworld/places/formid_blocks.json"]).tests
    assert "tools/tests/test_places_look.py" in gate.pick([_pl("jal-veesa", "place.json")]).tests


def test_a_place_skills_text_runs_nothing_but_the_dialogue_skill_still_runs_its_lints():
    p = gate.pick([".claude/skills/place-people/SKILL.md", ".claude/skills/place-lessons/SKILL.md"])
    assert not p.full and not p.tests and not p.stages
    d = gate.pick([".claude/skills/dialogue-write/SKILL.md"])
    assert "tooling/tests/test_dialogue_lint_place_rules.py" in d.tests


def test_edits_run_only_their_own_validity_check_with_a_skill_beside_them(monkeypatch):
    seen = []
    monkeypatch.setattr(gate.subprocess, "run", lambda cmd, **k: seen.append(cmd) or type("R", (), {"returncode": 0})())
    monkeypatch.setattr(gate, "_make", lambda t: 0)
    plan = gate.pick([_pl("jal-veesa", "edits/s.json"), ".claude/skills/place-people/SKILL.md"])
    assert gate.run(plan, []) == 0
    assert seen[-1][-1] == _pl("jal-veesa", "edits/s.json") and ".claude" not in " ".join(seen[-1])


def test_a_rules_not_globs_leave_those_paths_to_a_more_exact_rule():
    rule = {"globs": ["newworld/*"], "not": ["newworld/places/*/*"]}
    assert not gate._rule_hit("newworld/places/a/place.json", rule)
    assert gate._rule_hit("newworld/places/formid_blocks.json", rule)
