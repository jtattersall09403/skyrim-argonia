"""tooling/check_reach.py: a docs-only change runs the docs checks, a water-only one the water tests and the world
step, an unmapped path the whole gate."""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location("check_reach", pathlib.Path(__file__).resolve().parents[1] / "check_reach.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


def test_docs_only_runs_only_docs_checks():
    reached, targets, why, _ = cr.plan(["docs/research/2026-11-04/lane-x.md", "docs/PROGRESS.md"])
    assert why is None
    assert set(reached) == {"links", "records"}
    assert not targets


def test_water_only_runs_water_tests_and_world():
    reached, targets, why, _ = cr.plan(["tools/argonia_world/water/solve.py"])
    assert why is None
    assert set(reached) == {"lint", "unit", "world", "roads-census"}
    assert "plugin-check" not in reached
    assert targets and all("water" in t or "argonia_world" in t for t in targets)
    assert not any(t.startswith("tooling") for t in targets)


def test_unmapped_path_runs_everything():
    reached, targets, why, _ = cr.plan(["some/new/thing.xyz"])
    assert why and "unmapped" in why and not reached


def test_makefile_runs_everything():
    assert cr.plan(["Makefile"])[2]


def test_claude_md_reaches_budget():
    assert "budget" in cr.plan(["CLAUDE.md"])[0]


def test_unit_all_for_shared_units_module():
    assert cr.plan(["tools/argonia_world/skyrim_units.py"])[1] == {"__all__"}
