"""The studio's browser suites declare their reach whole (tools/places/studio/web/test/reach.py), so the gate can run
them test by test: every test declares what it reaches, every name in a reach exists, and every module of the page is
in the core or in some test's reach."""
import ast
import runpy
from fnmatch import fnmatchcase
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
R = runpy.run_path(str(REPO / "tools/places/studio/web/test/reach.py"))
WEB = REPO / R["DIR"]


def _tests(f: str) -> set[str]:
    tree = ast.parse((WEB / f).read_text())
    return {n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test")}


def test_every_browser_test_declares_its_reach_and_no_reach_names_a_missing_test():
    declared = {k for k in R["REACH"]}
    actual = {f"{f}::{t}" for f in R["FILES"] for t in _tests(f)}
    assert actual - declared == set(), "tests without a declared reach"
    assert declared - actual == set(), "a reach for a test that does not exist"


def test_every_suite_file_exists_and_every_named_file_exists():
    for f in R["FILES"]:
        assert (WEB / f).is_file(), f
    for node, files in R["REACH"].items():
        for f in files:
            assert (WEB / f).is_file(), (node, f)
            assert not any(fnmatchcase(f, g) for g in R["CORE"]), f"{node}: {f} is core, which every test reaches"


def test_every_page_module_is_core_or_reached_by_a_test():
    reached = {f for files in R["REACH"].values() for f in files}
    for p in sorted((WEB / "js").glob("*.js")):
        rel = p.relative_to(WEB).as_posix()
        assert rel in reached or any(fnmatchcase(rel, g) for g in R["CORE"]), f"{rel}: no browser test reaches it"
