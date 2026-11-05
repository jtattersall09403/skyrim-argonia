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
    assert set(reached) == {"lint", "unit", "world", "roads-census", "edges-census"}
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


def test_pool_heavy_first_and_output_whole_in_part_order():
    import threading
    import time
    steps = ["lint", "unit", "links", "plugin-check", "skse", "world"]
    assert cr.queue_order(steps) == ["unit", "plugin-check", "skse", "lint", "links", "world"]
    started, lock = [], threading.Lock()

    def runner(s):
        with lock:
            started.append(s)
        time.sleep({"unit": 0.3, "plugin-check": 0.2}.get(s, 0.01))
        return (1 if s == "world" else 0), 0.0, f"{s} line1\n{s} line2\n"

    out = []
    res = cr.run_pool(steps, 3, runner, emit=out.append)
    assert started[:3] == ["unit", "plugin-check", "skse"]
    texts = [o for o in out if "line1" in o]
    assert all(t == f"{t.split()[0]} line1\n{t.split()[0]} line2" for t in texts)  # each part whole, one emit
    order = [o.split()[1] for o in out if o.startswith("reach: ")]
    assert order == [s for s in cr.PARTS if s in steps]
    assert res["world"] == 1 and res["unit"] == 0


def test_gate_resumes_by_part(tmp_path):
    """A second gate run with unchanged inputs skips the green parts; a part whose input moved (or that was red) reruns."""
    state = tmp_path / "gate.state"
    ran = []

    def runner(s):
        ran.append(s)
        return (1 if s == "world" else 0), 0.0, ""

    stamps = {"lint": "a1", "unit": "b1", "world": "c1"}
    steps = ["lint", "unit", "world"]
    out = []
    cr.run_pool(steps, 1, cr.resumable(runner, state, lambda s: stamps[s]), emit=out.append)
    assert sorted(ran) == steps
    ran.clear(); out.clear()
    stamps["unit"] = "b2"  # unit's input moved; world was red
    cr.run_pool(steps, 1, cr.resumable(runner, state, lambda s: stamps[s]), emit=out.append)
    assert sorted(ran) == ["unit", "world"]
    assert "gate part lint OK (done earlier for a1)" in out


def test_part_stamp_follows_content(tmp_path, monkeypatch):
    monkeypatch.setattr(cr, "REPO", tmp_path)
    (tmp_path / "docs").mkdir()
    f = tmp_path / "docs" / "a.md"
    f.write_text("x")
    a = cr.part_stamp("links", ["docs/a.md"], set(), "k")
    assert a == cr.part_stamp("links", ["docs/a.md"], set(), "k")
    f.write_text("y")
    assert a != cr.part_stamp("links", ["docs/a.md"], set(), "k")
    assert cr.part_stamp("links", ["docs/a.md"], set(), "k") != cr.part_stamp("links", ["docs/a.md"], set(), "k2")


def test_parts_cover_make_check():
    import re
    mk = (cr.REPO / "Makefile").read_text()
    make_parts = re.search(r"^PARTS := (.+)$", mk, re.M).group(1).split()
    assert sorted(make_parts) == sorted(cr.PARTS)


def test_full_gate_runs_every_part_resumably(tmp_path, monkeypatch):
    """No monolithic fallback: the full run goes part by part, records each green part as it ends, and a rerun after a
    kill skips the parts already green."""
    state = tmp_path / "gate.state"
    ran = []
    monkeypatch.setattr(cr, "full_key", lambda k: k + "|full|H")

    class Killed(Exception):
        pass

    def fake_part(s, targets, paths):
        if s == cr.PARTS[2] and kill:
            raise Killed
        ran.append(s)
        return 0, 0.0, ""

    monkeypatch.setattr(cr, "run_part", fake_part)
    monkeypatch.setattr(cr, "finish", lambda rc, a: rc)
    monkeypatch.setattr(cr, "last_green", lambda: (None, None))
    kill = True
    import pytest
    with pytest.raises(Killed):
        cr.main(["--since", "auto", "--jobs", "1", "--state", str(state)])
    done = {l.split()[0] for l in state.read_text().splitlines()}
    assert done == set(ran) and ran  # each green part recorded as it ended
    first = list(ran)
    ran.clear()
    kill = False
    assert cr.main(["--since", "auto", "--jobs", "1", "--state", str(state)]) == 0
    assert not set(ran) & set(first)
    assert set(ran) | set(first) == set(cr.PARTS)
    assert all("|full|" not in l for l in state.read_text().splitlines())  # stamps are hashes
