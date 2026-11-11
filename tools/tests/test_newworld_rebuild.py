"""The world rebuild's order, stale plan, stop on red and side-by-side run (tools/newworld/rebuild.py), on stub
stages in a tmp tree; the real stage table is judged for its order alone."""
import json
import time

import pytest

from tools.newworld import rebuild as R
from tools.newworld import terrain_needs
from tools.newworld.rebuild import PY, Stage, Tree


# ---- the real table: the order its reads and writes give ---------------------------------------------------------

def test_real_order_is_derived_and_true():
    names = R.order(R.STAGES)
    assert sorted(names) == sorted(s.name for s in R.STAGES)
    at = {n: i for i, n in enumerate(names)}
    for before, after in [("scope", "regions"), ("regions", "terrain"), ("db", "terrain"), ("terrain", "needs"),
                          ("terrain", "water"), ("water", "landcover"), ("water", "db-water"), ("terrain", "land"),
                          ("land", "place"), ("landcover", "place"), ("landcover", "paint"), ("landcover", "cells"),
                          ("cells", "landings"), ("cells", "mist"), ("place", "mist"), ("mist", "map"), ("place", "map"),
                          ("atmosphere", "height-fog"), ("paint", "esm"), ("navmesh", "esm"), ("map", "esm"),
                          ("mist", "esm"), ("atmosphere", "esm"), ("esm", "readback"), ("height-fog", "readback"),
                          ("readback", "upload"), ("tools", "esm"), ("land", "relief")]:
        assert at[before] < at[after], (before, after)


def test_long_stages_wait_for_every_early_check_and_not_for_each_other():
    d = R.deps(R.STAGES)
    for long in ("paint", "navmesh"):
        assert set(R.EARLY_CHECKS) <= set(d[long]), long
    assert "navmesh" not in d["paint"] and "paint" not in d["navmesh"]


def test_every_output_read_has_a_writer_or_is_the_extraction():
    writes = [w for s in R.STAGES for w in s.writes]
    optional = {"out:newworld/lod/logs/coverage.json"}     # the LOD run's own feedback, absent until it has run
    for s in R.STAGES:
        for r in s.reads:
            if r.startswith("out:") and r not in optional:
                path = r.split(":", 1)[1].split("#")[0]
                assert path in R.EXTERNAL or any(R._feeds(w, r) for w in writes), (s.name, r)
            if r.startswith("db:"):
                assert any(R._feeds(w, r) for w in writes), (s.name, r)
        for a, b, how in s.agree:
            assert how in ("eq", "starts") and "#" in a and "#" in b


def test_a_cycle_is_an_error():
    a = Stage("a", "", reads=("out:b.txt",), writes=("out:a.txt",))
    b = Stage("b", "", reads=("out:a.txt",), writes=("out:b.txt",))
    with pytest.raises(ValueError, match="cycle"):
        R.order((a, b))


# ---- stub stages -----------------------------------------------------------------------------------------------------

def cat(src: str, dst: str, mark: str) -> tuple:
    """A stage command: copy out/<src>'s or the source's text to out/<dst>, and count the run in out/<mark>."""
    code = ("import sys,pathlib as p\nsrc,dst,mark=sys.argv[1:4]\n"
            "o=p.Path('out'); o.mkdir(exist_ok=True)\n"
            "t=(o/src).read_text() if (o/src).exists() else p.Path(src).read_text()\n"
            "(o/dst).write_text(t.split('#')[0])\n"
            "(o/mark).open('a').write('x')\n")
    return (PY, "-c", code, src, dst, mark)


def passes_if(path: str) -> tuple:
    return (PY, "-c", "import sys,pathlib as p\nok=p.Path(sys.argv[1]).read_text().strip()=='pass'\n"
                      "print('PASS' if ok else 'FAIL the stub check is red')\nsys.exit(0 if ok else 1)", path)


@pytest.fixture
def tree(tmp_path):
    (tmp_path / "in.txt").write_text("one")
    (tmp_path / "gate.txt").write_text("pass")
    stages = (
        Stage("a", "copies the source", cmds=(cat("in.txt", "a.txt", "a.runs"),), checks=(passes_if("gate.txt"),),
              reads=("src:in.txt", "src:gate.txt"), writes=("out:a.txt",)),
        Stage("b", "copies a", cmds=(cat("a.txt", "b.txt", "b.runs"),), reads=("out:a.txt",), writes=("out:b.txt",)),
        Stage("c", "copies b", cmds=(cat("b.txt", "c.txt", "c.runs"),), reads=("out:b.txt",), writes=("out:c.txt",)),
    )
    return Tree(repo=tmp_path, stages=stages, py=__import__("sys").executable)


def runs(tree, name):
    p = tree.out / f"{name}.runs"
    return len(p.read_text()) if p.exists() else 0


def states(tree):
    return {r["stage"]: r["state"] for r in R.plan(tree)}


def test_first_run_then_every_stage_current(tree, capsys):
    assert states(tree) == {"a": "stale", "b": "stale", "c": "stale"}
    assert R.run(tree, check_first=False) == 0
    assert states(tree) == {"a": "current", "b": "current", "c": "current"}
    assert R.run(tree, check_first=False) == 0
    assert [runs(tree, n) for n in "abc"] == [1, 1, 1]
    out = capsys.readouterr().out
    assert "stale: 0 of 3: every stage is current" in out and "stages skipped as current: 3" in out


def test_a_changed_input_makes_its_stage_stale_and_names_it(tree):
    R.run(tree, check_first=False)
    (tree.repo / "in.txt").write_text("two")
    rows = {r["stage"]: r for r in R.plan(tree)}
    assert rows["a"]["state"] == "stale" and "in.txt" in rows["a"]["why"]
    assert rows["b"]["state"] == "follows" and rows["c"]["state"] == "follows"
    assert R.run(tree, check_first=False) == 0
    assert [runs(tree, n) for n in "abc"] == [2, 2, 2]
    assert (tree.out / "c.txt").read_text() == "two"


def test_a_stage_whose_inputs_come_out_unchanged_is_skipped(tree):
    R.run(tree, check_first=False)
    (tree.repo / "in.txt").write_text("one# a comment the stage drops: its output is the same bytes")
    assert R.run(tree, check_first=False) == 0
    assert [runs(tree, n) for n in "abc"] == [2, 1, 1]


def test_a_missing_output_makes_its_stage_stale(tree):
    R.run(tree, check_first=False)
    (tree.out / "b.txt").unlink()
    rows = {r["stage"]: r for r in R.plan(tree)}
    assert rows["a"]["state"] == "current" and rows["b"]["state"] == "stale" and "missing" in rows["b"]["why"]


def test_a_red_check_stops_the_run_there_and_prints_its_line(tree, capsys):
    (tree.repo / "gate.txt").write_text("fail")
    assert R.run(tree, check_first=False) == 1
    out = capsys.readouterr().out
    assert "[a] RED at its check" in out and "FAIL the stub check is red" in out
    assert "not run: b, c" in out
    assert [runs(tree, n) for n in "abc"] == [1, 0, 0]
    assert states(tree)["a"] == "stale"
    doc = json.loads((tree.state / "summary.json").read_text())
    assert doc["red"] == ["a"] and doc["not_run"] == ["b", "c"] and doc["checks_failed"] == ["a: check"]


def test_after_a_red_check_only_what_changed_runs_again(tree):
    (tree.repo / "gate.txt").write_text("fail")
    R.run(tree, check_first=False)
    assert R.run(tree, check_first=False) == 1          # the commands stand; the check alone is repeated
    assert runs(tree, "a") == 1
    (tree.repo / "gate.txt").write_text("pass")         # an input changed: the stage runs again, then the rest
    assert R.run(tree, check_first=False) == 0
    assert [runs(tree, n) for n in "abc"] == [2, 1, 1]


def test_to_runs_only_what_a_stage_needs(tree):
    assert R.run(tree, to="b", check_first=False) == 0
    assert [runs(tree, n) for n in "abc"] == [1, 1, 0]
    assert R.run(tree, to="nothing", check_first=False) == 2


def test_a_worktree_plans_and_never_runs(tree, tmp_path_factory, capsys):
    """A worktree's out/ is hard links to the main tree's files: the run refuses there, preflight or none."""
    import subprocess
    main = tmp_path_factory.mktemp("main")
    wt = tmp_path_factory.mktemp("lanes") / "lane"

    def git(*a, cwd=main):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, check=True, capture_output=True)
    git("init", "-q")
    (main / "in.txt").write_text("one")
    (main / "gate.txt").write_text("pass")
    git("add", "in.txt", "gate.txt")
    git("commit", "-q", "-m", "seed")
    git("worktree", "add", "-q", str(wt))
    lane = Tree(repo=wt, stages=tree.stages, py=tree.py)
    assert states(lane)["a"] == "stale"                       # it plans
    assert R.run(lane, check_first=False) == 2                # and refuses to run
    assert "the main tree is the one writer" in capsys.readouterr().err and not (wt / "out" / "a.txt").exists()
    home = Tree(repo=main, stages=tree.stages, py=tree.py)
    assert R.run(home, check_first=False) == 0 and (main / "out" / "a.txt").exists()


def test_force_runs_a_current_stage(tree):
    R.run(tree, check_first=False)
    assert R.run(tree, force=("b",), check_first=False) == 0
    assert [runs(tree, n) for n in "abc"] == [1, 2, 1]


# ---- side by side ------------------------------------------------------------------------------------------------------

def span(name: str, s: float = 0.6) -> tuple:
    return (PY, "-c", "import sys,time,pathlib as p\no=p.Path('out'); o.mkdir(exist_ok=True)\nt=time.time(); time.sleep(float(sys.argv[2]))\n"
                      "(o/(sys.argv[1]+'.span')).write_text(f'{t} {time.time()}')", name, str(s))


def overlap(tree, a, b):
    (a0, a1), (b0, b1) = (map(float, (tree.out / f"{n}.span").read_text().split()) for n in (a, b))
    return a0 < b1 and b0 < a1


def side_tree(tmp_path, **kw):
    stages = (Stage("x", "", cmds=(span("x"),), writes=("out:x.span",), gb=2.0, **kw.get("x", {})),
              Stage("y", "", cmds=(span("y"),), writes=("out:y.span",), gb=2.0, **kw.get("y", {})),
              Stage("z", "", cmds=(span("z", 0.05),), reads=("out:x.span", "out:y.span"), writes=("out:z.span",)))
    return Tree(repo=tmp_path, stages=stages, py=__import__("sys").executable)


def test_independent_stages_run_side_by_side_and_the_next_waits_for_both(tmp_path):
    t = side_tree(tmp_path)
    t0 = time.time()
    assert R.run(t, budget_gb=8.0, check_first=False) == 0
    assert overlap(t, "x", "y") and not overlap(t, "x", "z") and not overlap(t, "y", "z")
    assert time.time() - t0 < 1.9


def test_memory_budget_and_locks_keep_stages_apart(tmp_path):
    t = side_tree(tmp_path / "budget")
    (tmp_path / "budget").mkdir()
    assert R.run(t, budget_gb=3.0, check_first=False) == 0      # 2 + 2 GB do not fit 3
    assert not overlap(t, "x", "y")
    (tmp_path / "lock").mkdir()
    t = side_tree(tmp_path / "lock", x={"lock": "dotnet"}, y={"lock": "dotnet"})
    assert R.run(t, budget_gb=8.0, check_first=False) == 0
    assert not overlap(t, "x", "y")


def test_a_red_stage_lets_the_running_ones_finish_and_starts_nothing(tmp_path, capsys):
    bad = (PY, "-c", "import sys; print('FAIL x broke'); sys.exit(3)")
    stages = (Stage("x", "", cmds=(bad,), gb=1.0),
              Stage("y", "", cmds=(span("y"),), writes=("out:y.span",), gb=1.0),
              Stage("z", "", cmds=(span("z", 0.05),), reads=("out:y.span",), writes=("out:z.span",)))
    t = Tree(repo=tmp_path, stages=stages, py=__import__("sys").executable)
    assert R.run(t, budget_gb=8.0, check_first=False) == 1
    assert (t.out / "y.span").exists() and not (t.out / "z.span").exists()
    assert "not run: z" in capsys.readouterr().out
    assert {r["stage"]: r["state"] for r in R.plan(t)} == {"x": "stale", "y": "current", "z": "stale"}


# ---- digests, agreement, adopt -----------------------------------------------------------------------------------------

def test_a_table_is_read_by_the_columns_a_stage_uses(tmp_path):
    t = Tree(repo=tmp_path, stages=())
    t.db.mkdir(parents=True)
    row = {"id": "p", "px": 1.0, "summary": "a quiet village"}
    (t.db / "place.jsonl").write_text(json.dumps(row) + "\n")
    whole, ground, cols = (t.digest(s) for s in ("db:place", "db:place[-summary]", "db:place[id,px]"))
    (t.db / "place.jsonl").write_text(json.dumps({**row, "summary": "a loud town"}) + "\n")
    t._cache = None
    assert t.digest("db:place") != whole and t.digest("db:place[-summary]") == ground and t.digest("db:place[id,px]") == cols
    (t.db / "place.jsonl").write_text(json.dumps({**row, "px": 2.0}) + "\n")
    assert t.digest("db:place[-summary]") != ground and t.digest("db:place[id,px]") != cols
    assert t.digest("db:nothing") == "absent" and t.digest("ext:/no/such/file") == "absent"


def test_a_named_field_of_a_manifest_is_the_digest(tmp_path):
    t = Tree(repo=tmp_path, stages=())
    (t.out).mkdir()
    (t.out / "m.json").write_text(json.dumps({"key": "k1", "seconds": 3}))
    d = t.digest("out:m.json#key")
    (t.out / "m.json").write_text(json.dumps({"key": "k1", "seconds": 9}))
    assert t.digest("out:m.json#key") == d


def agree_tree(tmp_path, proof_rc=0):
    w = "import json,sys,pathlib as p\no=p.Path('out'); o.mkdir(exist_ok=True)\n(o/sys.argv[1]).write_text(json.dumps({'build_id': sys.argv[2]}))"
    stages = (Stage("land", "", cmds=((PY, "-c", w, "land.json", "B2"),), writes=("out:land.json",),
                    proof=(PY, "-c", f"import sys; print('land inputs: as built' if not {proof_rc} else 'land inputs: changed'); sys.exit({proof_rc})")),
              Stage("cells", "", cmds=((PY, "-c", w, "cells.json", "B2"),), reads=("out:land.json",), writes=("out:cells.json",),
                    agree=(("out:cells.json#build_id", "out:land.json#build_id", "eq"),)),
              Stage("spec", "", cmds=((PY, "-c", w, "spec.json", "-"),), writes=("out:spec.json",)))
    return Tree(repo=tmp_path, stages=stages, py=__import__("sys").executable)


def test_an_output_of_another_build_is_stale_and_adopt_refuses_it(tmp_path, capsys):
    t = agree_tree(tmp_path)
    t.out.mkdir()
    for name, build in (("land", "B2"), ("cells", "B1"), ("spec", "-")):
        (t.out / f"{name}.json").write_text(json.dumps({"build_id": build}))
    assert R.adopt(t) == 1 and "cells" in capsys.readouterr().out and not (t.state / "land.json").exists()
    (t.out / "cells.json").write_text(json.dumps({"build_id": "B2"}))
    assert R.adopt(t) == 0
    out = capsys.readouterr().out
    assert "left to run  spec: its output carries no proof of its build" in out and "2 of 3 stages stamped" in out
    assert {r["stage"]: r["state"] for r in R.plan(t)} == {"land": "current", "cells": "current", "spec": "stale"}
    (t.out / "cells.json").write_text(json.dumps({"build_id": "B1"}))
    row = R.plan(t)[1]
    assert row["state"] == "stale" and "B1" in row["why"]


def test_adopt_leaves_a_stage_whose_proof_is_red_to_run(tmp_path, capsys):
    t = agree_tree(tmp_path, proof_rc=1)
    t.out.mkdir()
    for name in ("land", "cells", "spec"):
        (t.out / f"{name}.json").write_text(json.dumps({"build_id": "B2"}))
    assert R.adopt(t) == 0
    assert "left to run  land: land inputs: changed" in capsys.readouterr().out
    assert {r["stage"]: r["state"] for r in R.plan(t)} == {"land": "stale", "cells": "follows", "spec": "stale"}
    assert R.run(t, check_first=False) == 0          # land runs; cells' input is the same bytes: skipped
    assert {r["stage"]: r["state"] for r in R.plan(t)} == {"land": "current", "cells": "current", "spec": "current"}


# ---- the checks the rebuild gates on ---------------------------------------------------------------------------------

def test_terrain_needs_fail_only_on_a_failure_not_accepted():
    rows = [{"place_id": "a", "need": "rise", "ok": False, "why": ""}, {"place_id": "b", "need": "flat-pad", "ok": False, "why": ""},
            {"place_id": "c", "need": "island", "ok": True, "why": ""}]
    acc = [{"place_id": "a", "need": "rise", "why": "no land"}, {"place_id": "c", "need": "island", "why": "joined"}]
    new, old, gone = terrain_needs.judge_accepted(rows, acc)
    assert [r["place_id"] for r in new] == ["b"] and [r["place_id"] for r in old] == ["a"] and [a["place_id"] for a in gone] == ["c"]


def test_the_accepted_needs_file_names_place_need_and_reason():
    for a in json.loads((R.REPO / "newworld/sources/terrain_needs_accepted.json").read_text())["accepted"]:
        assert a["place_id"] and a["need"] and len(a["why"]) > 10
