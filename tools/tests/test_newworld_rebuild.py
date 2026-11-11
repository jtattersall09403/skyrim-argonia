"""The world rebuild (tools/newworld/rebuild.py): on stub stages in a tmp tree, its order, stale plan, stop on red,
side-by-side run, its record of a run (running, built, key, proved), its lock and its digests; on the real stage
table, that each stage reads the code and the tables its tool runs on; and the tools' own proofs and keys."""
import ast
import fnmatch
import hashlib
import inspect
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tools.newworld import keyed, terrain_needs
from tools.newworld import rebuild as R
from tools.newworld.rebuild import PY, Stage, Tree

REPO = R.REPO


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


def test_every_output_read_has_a_writer_or_is_the_extraction():
    writes = [w for s in R.STAGES for w in s.writes]
    # a built place's plan and the hollow study's extras: each absent until its tool has run
    optional = {"out:places/shards/*/plan.json", "out:newworld/research/hollow_extra.json"}
    for s in R.STAGES:
        assert not set(s.reads) & set(s.check_reads), s.name
        for r in s.reads + s.check_reads:
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


# ---- the real table: each stage reads what its tool runs on ------------------------------------------------------

def _file(mod: str) -> Path | None:
    for p in (REPO / (mod.replace(".", "/") + ".py"), REPO / mod.replace(".", "/") / "__init__.py"):
        if p.exists():
            return p
    return None


def _imports(p: Path, lazy: bool) -> set[str]:
    """The tools modules a file imports: at module level, or (`lazy`) inside its functions."""
    out: set[str] = set()

    def visit(node, depth):
        for n in ast.iter_child_nodes(node):
            d = depth + isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
            if (d > 0) == lazy:
                if isinstance(n, ast.Import):
                    out.update(a.name for a in n.names)
                elif isinstance(n, ast.ImportFrom) and n.module:
                    out.add(n.module)
                    out.update(f"{n.module}.{a.name}" for a in n.names)
            visit(n, d)
    visit(ast.parse(p.read_text()), 0)
    return {m for m in out if m.startswith("tools.") and _file(m)}


def code_read(mod: str, no_lazy: set[str] = frozenset()) -> set[str]:
    """The files a tool runs on: its module, every module that one imports at module level and so on down (their
    packages with them), and each module one of those imports inside a function."""
    seen: dict[str, Path] = {}
    stack = [mod]
    while stack:
        m = stack.pop()
        if m in seen or not _file(m):
            continue
        seen[m] = _file(m)
        stack += [m.rpartition(".")[0], *_imports(seen[m], lazy=False)]
    files = set(seen.values())
    for p in list(files):
        if str(p.relative_to(REPO)) not in no_lazy:
            files |= {_file(m) for m in _imports(p, lazy=True)}
    return {str(p.relative_to(REPO)) for p in files if p.stat().st_size}


# a file a stage's tool imports and the stage does not read, with the reason; `NO_LAZY`: a file whose imports inside
# functions the stage does not run
NOT_READ = {("place", "tools/newworld/verify.py"): "place calls verify.assets() alone: the laid stack's file listing, read as laid:NewWorld",
            ("terrain", "tools/newworld/rebuild.py"): "the terrain takes from it the list of what its stage reads, each digested itself",
            **{(n, "tools/newworld/keyed.py"): "it ends the tool's key with the build key and changes nothing the tool writes"
               for n in keyed.TOOLS}}
# a table a stage's tool module names in a function the stage does not run
TABLE_NOT_READ = {("atmosphere", "cell"): "atmosphere.py's database rows, which build_db calls",
                  ("atmosphere", "note_aspect"): "atmosphere.py's database rows, which build_db calls"}
NO_LAZY = {("relief", "tools/newworld/verify.py"): "the relief group alone runs: terrain_character and terrain_held, which the stage reads",
           ("place", "tools/newworld/place/__main__.py"): "one import for each of its commands: `run` reaches place.py, `check` checks.py"}


@pytest.mark.parametrize("s", R.STAGES, ids=lambda s: s.name)
def test_each_stage_reads_the_code_its_tool_runs_on(s):
    """A stage goes stale with an edit to any file its commands import; a check's own imports may be check_reads."""
    no_lazy = {f for (n, f) in NO_LAZY if n == s.name}
    for cmds, specs in ((s.cmds, s.reads), (s.checks, s.reads + s.check_reads)):
        globs = [r[4:] for r in specs if r.startswith("src:")]
        files = set().union(*[code_read(m, no_lazy) for c in cmds for m in R.tool_modules(c)]) if cmds else set()
        miss = sorted(f for f in files if not any(fnmatch.fnmatch(f, g) for g in globs) and (s.name, f) not in NOT_READ)
        assert not miss, f"{s.name} does not read {miss}"


@pytest.mark.parametrize("s", R.STAGES, ids=lambda s: s.name)
def test_each_stage_reads_the_tables_its_tool_names(s):
    """Every database table the stage's own tool module names is among the stage's reads (or the stage writes the database)."""
    if any(w.startswith("db:") for w in s.writes):
        return
    read = {r[3:].split("[")[0] for r in s.reads + s.check_reads if r.startswith("db:")}
    for c in s.cmds + s.checks:
        for m in R.tool_modules(c):
            src = _file(m).read_text()
            named = set(re.findall(r"\.rows\(\"(\w+)\"", src)) | set(re.findall(r"\bjsonl\(\"(\w+)\"\)", src)) \
                | set(re.findall(r"DB / \"(\w+)\.jsonl\"", src))
            miss = sorted(t for t in named - read if (s.name, t) not in TABLE_NOT_READ)
            assert not miss, f"{s.name}: {m} names {miss}"


def test_every_source_and_table_a_stage_reads_is_in_the_tree():
    """A read that names nothing digests nothing: each committed file, glob and table column a stage reads exists."""
    tree = Tree()
    made = {w for s in R.STAGES for w in s.writes}
    for s in R.STAGES:
        for r in s.reads + s.check_reads:
            kind, _, rest = r.partition(":")
            if kind == "src" and r not in made:
                assert tree._files(tree.repo, rest), (s.name, r)
            if kind == "db":
                table, _, cols = rest.partition("[")
                p = tree.db / f"{table}.jsonl"
                assert p.exists(), (s.name, r)
                first = next((ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()), None)
                if cols and first:
                    assert {c.strip().lstrip("-") for c in cols.rstrip("]").split(",")} <= set(json.loads(first)), (s.name, r)


def test_the_read_backs_groups_are_all_run_by_some_stage_or_machine():
    """verify's GROUPS is the whole set of its row groups, and the stages' `--only` and `--skip` name every one."""
    from tools.newworld import verify
    sections = set(re.findall(r"@section\(rep, \"([^\"]+)\"", Path(verify.__file__).read_text()))
    assert sections == set(verify.GROUPS)
    args = {flag: set(c[c.index(flag) + 1].split(",")) for s in R.STAGES for c in s.checks if "tools.newworld.verify" in c
            for flag in ("--only", "--skip") if flag in c}
    downstream = set(R.DOWNSTREAM_GROUPS.split(","))
    assert args["--only"] | args["--skip"] <= sections and downstream <= sections
    assert args["--skip"] == downstream | args["--only"]         # the readback runs every group but those two sets
    assert {verify.GROUPS[g] for g in downstream} == {"lod", "deploy", "places"}


def test_no_stage_but_upload_copies_to_the_bucket():
    for s in R.STAGES:
        for c in s.cmds + s.checks:
            if "tools.newworld.terrain" in c:
                assert "--no-upload" in c or c[-1] in ("check", "inputs"), (s.name, c)
            assert not any("upload" in a for a in c if a != "--no-upload") or s.name == "upload", (s.name, c)


def test_the_height_fog_row_is_the_one_left_out_of_the_laid_stack():
    from tools.newworld import atmosphere_cs
    assert R.OWN_ROWS == (atmosphere_cs.ROW,)


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
    return Tree(repo=tmp_path, stages=stages, py=sys.executable)


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


# ---- a stage tool that keeps a key of its own ---------------------------------------------------------------------

OWN_KEY_TOOL = """
import os, sys, pathlib as p
o = p.Path('out'); o.mkdir(exist_ok=True)
key = p.Path('rule.txt').read_text() + (':' + os.environ['NW_STAGE_KEY'] if os.environ.get('NW_STAGE_KEY') else '')
(o / 'tool.env').open('a').write(os.environ.get('NW_STAGE_KEY', '-') + '\\n')
if (o / 'tool.key').exists() and (o / 'tool.key').read_text() == key:
    print('tool current'); sys.exit(0)
if p.Path('die').exists():
    sys.exit(3)
(o / 'tool.txt').write_text(p.Path('rule.txt').read_text() + '+' + p.Path('data.txt').read_text())
(o / 'tool.key').write_text(key)
(o / 'tool.runs').open('a').write('x')
"""


def own_key_tree(tmp_path):
    """One stage whose tool skips on its own key, which covers rule.txt and not data.txt; its check reads look.txt."""
    for n, t in (("rule.txt", "r1"), ("data.txt", "d1"), ("look.txt", "pass")):
        (tmp_path / n).write_text(t)
    s = Stage("t", "", cmds=((PY, "-c", OWN_KEY_TOOL),), checks=(passes_if("look.txt"),), reads=("src:rule.txt", "src:data.txt"),
              check_reads=("src:look.txt",), writes=("out:tool.txt",))
    return Tree(repo=tmp_path, stages=(s,), py=sys.executable)


def test_a_stale_stage_is_rebuilt_whatever_its_tools_own_key_says(tmp_path):
    t = own_key_tree(tmp_path)
    assert R.run(t, check_first=False) == 0
    (t.repo / "data.txt").write_text("d2")                 # read by the stage, outside the tool's own key
    assert R.plan(t)[0]["state"] == "stale"
    assert R.run(t, check_first=False) == 0
    assert (t.out / "tool.txt").read_text() == "r1+d2" and runs(t, "tool") == 2
    assert R.plan(t)[0]["state"] == "current"
    assert R.run(t, force=("t",), check_first=False) == 0 and runs(t, "tool") == 3     # a forced stage is built again


def test_a_stage_with_no_record_is_left_to_its_tools_own_key_and_stamped(tmp_path):
    t = own_key_tree(tmp_path)
    t.out.mkdir()
    (t.out / "tool.txt").write_text("r1+d1")               # built by hand: the tool's own key stands beside it
    (t.out / "tool.key").write_text("r1")
    assert R.run(t, check_first=False) == 0
    assert runs(t, "tool") == 0 and (t.out / "tool.env").read_text() == "-\n" and t.stamp(t.stages[0]).get("key")


def test_a_stopped_run_is_resumed_on_the_same_build_key(tmp_path):
    t = own_key_tree(tmp_path)
    assert R.run(t, check_first=False) == 0
    (t.repo / "data.txt").write_text("d2")
    (t.repo / "die").write_text("")
    assert R.run(t, check_first=False) == 1
    (t.repo / "die").unlink()
    assert R.run(t, check_first=False) == 0
    env = (t.out / "tool.env").read_text().split()
    assert env[0] == "-" and env[1] == env[2] != "-" and (t.out / "tool.txt").read_text() == "r1+d2"


def test_what_the_checks_alone_read_reruns_the_checks_alone(tmp_path):
    t = own_key_tree(tmp_path)
    assert R.run(t, check_first=False) == 0
    (t.repo / "look.txt").write_text("fail")
    row = R.plan(t)[0]
    assert row["state"] == "stale" and "look.txt" in row["why"] and "checks alone" in row["why"]
    assert R.run(t, check_first=False) == 1 and R.plan(t)[0]["state"] == "stale"
    (t.repo / "look.txt").write_text("pass")
    assert R.run(t, check_first=False) == 0
    assert (t.out / "tool.env").read_text().split() == ["-"] and R.plan(t)[0]["state"] == "current"   # the tool never ran again


ADDING_TOOL = """
import pathlib as p
o = p.Path('out'); o.mkdir(exist_ok=True)
word, ids = p.Path('in.txt').read_text(), p.Path('ids.txt')
if word not in ids.read_text().split():
    ids.write_text(ids.read_text() + word + '\\n')          # a new name is added to the registry the stage reads
(o / 'w.txt').write_text(word + '=' + str(ids.read_text().split().index(word)))
(o / 'w.runs').open('a').write('x')
"""


def test_a_stage_that_adds_to_a_file_it_reads_is_current_after_that_run(tmp_path):
    (tmp_path / "in.txt").write_text("one")
    (tmp_path / "ids.txt").write_text("zero\n")
    s = Stage("w", "", cmds=((PY, "-c", ADDING_TOOL),), reads=("src:in.txt", "src:ids.txt"), adds=("src:ids.txt",), writes=("out:w.txt",))
    t = Tree(repo=tmp_path, stages=(s,), py=sys.executable)
    assert R.run(t, check_first=False) == 0 and (tmp_path / "ids.txt").read_text() == "zero\none\n"
    assert R.plan(t)[0]["state"] == "current"                      # the file as the commands left it is what the stage read
    assert R.run(t, check_first=False) == 0 and runs(t, "w") == 1
    (tmp_path / "in.txt").write_text("zero")                       # a known name: nothing is added, the stage runs once
    assert R.run(t, check_first=False) == 0 and runs(t, "w") == 2 and R.plan(t)[0]["state"] == "current"
    (tmp_path / "ids.txt").write_text("one\nzero\n")               # the registry changed by another hand: stale
    assert R.plan(t)[0]["state"] == "stale"
    assert R.run(t, check_first=False) == 0 and (t.out / "w.txt").read_text() == "zero=1"


def test_the_world_files_stage_reads_the_form_id_registry_and_may_add_to_it():
    esm = {s.name: s for s in R.STAGES}["esm"]
    assert R.FORMIDS in esm.reads and esm.adds == (R.FORMIDS,) and "src:tools/ArgoniaPlugin/FormIds.cs" in esm.reads
    assert all(a in s.reads for s in R.STAGES for a in s.adds)


@pytest.mark.parametrize("name", list(keyed.TOOLS))
def test_the_build_key_is_folded_into_each_keyed_tools_own_key(name, monkeypatch):
    import importlib
    mod_name, attr, entry = keyed.TOOLS[name]
    mod = importlib.import_module(mod_name)
    builder = getattr(mod, {"place": "run"}.get(name, "build"))
    assert f"{attr}(" in inspect.getsource(builder)             # the tool's key is made through it, at build time
    monkeypatch.setattr(mod, attr, lambda *a, **k: "own")
    assert keyed.fold(name, None) is importlib.import_module(entry) and getattr(mod, attr)() == "own"
    assert callable(keyed.fold(name, "K7").main) and getattr(mod, attr)() == "own:K7"
    stage = {s.name: s for s in R.STAGES}[name]
    assert stage.cmds[0][1:4] == ("-m", keyed.__name__, name) and stage.proof      # run through the fold; proved by hand


def test_the_keyed_tools_run_as_they_do_by_hand_without_a_build_key(monkeypatch, capsys):
    monkeypatch.delenv("NW_STAGE_KEY", raising=False)
    assert keyed.main(["nothing"]) == 2 and "usage" in capsys.readouterr().err


WORLD_DOTNET = """#!/usr/bin/env bash
case "$*" in
  build*) exit 0 ;;
  *"newworld write"*) echo esm > "${@: -2:1}"; echo x >> "$COUNT" ;;
  *"newworld check"*) printf 'cells 12\\n  PASS in 27.3 s\\n' ;;
esac
"""


def test_the_world_file_is_written_anew_for_a_new_build_key_and_its_check_holds_no_timing(tmp_path):
    repo, home = tmp_path / "repo", tmp_path / "home"
    (repo / "tools/newworld/world").mkdir(parents=True)
    (repo / "tools/newworld/world/world.sh").write_bytes((REPO / "tools/newworld/world/world.sh").read_bytes())
    os.chmod(repo / "tools/newworld/world/world.sh", 0o755)
    (repo / "tools/ArgoniaPlugin").mkdir(parents=True)
    for n in ("NewWorld", "WaterBlend", "ForeignCopy", "FormIds", "NewWorldNavmesh", "NewWorldAtmosphere"):
        (repo / f"tools/ArgoniaPlugin/{n}.cs").write_text(n)
    plug = repo / "out/newworld/plugin"
    for d in ("land", "tex", "refs/flora"):
        (plug / d).mkdir(parents=True)
    (plug / "land/manifest.json").write_text(json.dumps({"key": "B:abc:code", "build_id": "B"}))
    for n in ("tex/manifest.json", "cells.json", "atmosphere.json", "refs/flora/cy+001.jsonl"):
        (plug / n).write_text("{}")
    (home / "bin").mkdir(parents=True)
    (home / "bin/dotnet").write_text(WORLD_DOTNET)
    os.chmod(home / "bin/dotnet", 0o755)
    count = tmp_path / "writes"

    def sh(cmd, key=None):
        env = {"HOME": str(home), "PATH": f"{home / 'bin'}:{os.environ['PATH']}", "COUNT": str(count), "NW_UPLOAD": "0"}
        p = subprocess.run([str(repo / "tools/newworld/world/world.sh"), cmd], env=env | ({"NW_STAGE_KEY": key} if key else {}),
                           capture_output=True, text=True)
        assert p.returncode == 0, p.stderr
        return len(count.read_text().split()) if count.exists() else 0
    assert sh("write") == 1 and sh("write") == 1                   # by hand: its own key
    assert sh("write", "k1") == 2 and sh("write", "k1") == 2       # for the rebuild: written anew, once for a build key
    assert sh("write", "k2") == 3
    assert json.loads((plug / "ArgoniaNewWorld.json").read_text())["key"].startswith("B:abc:code:")
    sh("check")
    assert (plug / "check.txt").read_text() == "cells 12\n  PASS\n"


# ---- the record of a run: running, built, key ----------------------------------------------------------------------

def test_a_red_command_leaves_its_stage_stale_whatever_its_inputs_then_are(tree):
    """The old stamp never stands over outputs a failed command half rewrote."""
    half = (PY, "-c", "import sys,pathlib as p\nt=p.Path('in.txt').read_text()\np.Path('out').mkdir(exist_ok=True)\n"
                      "p.Path('out/a.txt').write_text(t)\nsys.exit(3 if p.Path('die').exists() else 0)")
    t = Tree(repo=tree.repo, stages=(Stage("a", "", cmds=(half,), reads=("src:in.txt",), writes=("out:a.txt",)),), py=tree.py)
    assert R.run(t, check_first=False) == 0
    (t.repo / "in.txt").write_text("two")
    (t.repo / "die").write_text("")
    assert R.run(t, check_first=False) == 1 and (t.out / "a.txt").read_text() == "two"
    (t.repo / "in.txt").write_text("one")                      # the change is taken back: the output is still the failed run's
    (t.repo / "die").unlink()
    row = R.plan(t)[0]
    assert row["state"] == "stale" and "part-way" in row["why"]
    assert R.run(t, check_first=False) == 0 and (t.out / "a.txt").read_text() == "one"


DRIVER = """
import sys
sys.path.insert(0, {repo!r})
from tools.newworld import rebuild as R
PY = R.PY
CMD = ("import time,pathlib as p\\no=p.Path('out'); o.mkdir(exist_ok=True)\\n(o/'a.txt').write_text(p.Path('in.txt').read_text())\\n"
       "(o/'a.runs').open('a').write('x')\\nwhile p.Path('slow-cmd').exists(): time.sleep(0.05)")
CHK = ("import time,pathlib as p\\np.Path('out/check.started').write_text('')\\n"
       "while p.Path('slow-check').exists(): time.sleep(0.05)")
STAGES = (R.Stage("a", "", cmds=((PY, "-c", CMD),), checks=((PY, "-c", CHK),), reads=("src:in.txt",), writes=("out:a.txt",)),)
if __name__ == "__main__":
    sys.exit(R.run(R.Tree(repo=sys.argv[1], stages=STAGES, py=sys.executable), check_first=False))
"""


def killed_run(tmp_path, flag: str, until):
    """Start a rebuild of the driver's one stage in its own process group, wait for `until`, and kill the group."""
    import runpy
    drv = tmp_path / "driver.py"
    drv.write_text(DRIVER.format(repo=str(REPO)))
    (tmp_path / flag).write_text("")
    p = subprocess.Popen([sys.executable, str(drv), str(tmp_path)], start_new_session=True, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    t0 = time.time()
    while not until() and time.time() - t0 < 30:
        time.sleep(0.05)
    assert until() and p.poll() is None
    os.killpg(p.pid, signal.SIGKILL)
    p.wait()
    (tmp_path / flag).unlink()
    return Tree(repo=tmp_path, stages=runpy.run_path(str(drv))["STAGES"], py=sys.executable)


def test_a_run_killed_in_a_check_repeats_the_check_alone(tmp_path):
    (tmp_path / "in.txt").write_text("one")
    t = killed_run(tmp_path, "slow-check", lambda: (tmp_path / "out/check.started").exists())
    assert (t.state / "run.pid").exists()                         # the dead run's lock is taken over
    assert R.run(t, check_first=False) == 0
    assert runs(t, "a") == 1 and t.stamp(t.stages[0]).get("key")


def test_a_run_killed_in_a_command_then_its_change_taken_back_is_stale(tmp_path):
    (tmp_path / "in.txt").write_text("one")
    t = Tree(repo=tmp_path, stages=(), py=sys.executable)
    drv_out = tmp_path / "out/a.txt"
    t = killed_run(tmp_path, "slow-cmd", drv_out.exists)        # a first run, killed before its command ended
    assert R.plan(t)[0]["state"] == "stale"
    assert R.run(t, check_first=False) == 0 and R.plan(t)[0]["state"] == "current"
    (tmp_path / "in.txt").write_text("two")
    t = killed_run(tmp_path, "slow-cmd", lambda: drv_out.read_text() == "two")
    (tmp_path / "in.txt").write_text("one")                       # taken back: the old key would match again
    assert R.plan(t)[0]["state"] == "stale"
    assert R.run(t, check_first=False) == 0 and drv_out.read_text() == "one"


# ---- the one-writer lock ---------------------------------------------------------------------------------------------

def test_the_lock_is_taken_before_preflight_and_a_live_rebuild_keeps_it(tree, monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(R, "preflight", lambda t, rows: seen.append((t.state / "run.pid").read_text()) or [])
    assert R.run(tree) == 0 and seen == [str(os.getpid())] and not (tree.state / "run.pid").exists()
    (tree.repo / "in.txt").write_text("two")
    (tree.state / "run.pid").write_text(str(os.getppid()))        # a live process holds it
    assert R.run(tree) == 2 and len(seen) == 1 and runs(tree, "a") == 1
    assert "another rebuild" in capsys.readouterr().err and (tree.state / "run.pid").read_text() == str(os.getppid())


def test_only_one_of_two_takes_the_lock_and_a_dead_ones_is_removed(tmp_path):
    pidf = tmp_path / "state/run.pid"
    assert R.take_lock(pidf) is None and pidf.read_text() == str(os.getpid())
    assert "another rebuild" in R.take_lock(pidf)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    pidf.write_text(str(dead.pid))
    assert R.take_lock(pidf) is None and pidf.read_text() == str(os.getpid())
    assert sorted(p.name for p in pidf.parent.iterdir()) == ["run.pid"]


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
    return Tree(repo=tmp_path, stages=stages, py=sys.executable)


def test_independent_stages_run_side_by_side_and_the_next_waits_for_both(tmp_path):
    t = side_tree(tmp_path)
    assert R.run(t, budget_gb=8.0, check_first=False) == 0
    assert overlap(t, "x", "y") and not overlap(t, "x", "z") and not overlap(t, "y", "z")


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
    t = Tree(repo=tmp_path, stages=stages, py=sys.executable)
    assert R.run(t, budget_gb=8.0, check_first=False) == 1
    assert (t.out / "y.span").exists() and not (t.out / "z.span").exists()
    assert "not run: z" in capsys.readouterr().out
    assert {r["stage"]: r["state"] for r in R.plan(t)} == {"x": "stale", "y": "current", "z": "stale"}


# ---- digests ---------------------------------------------------------------------------------------------------------

def test_a_table_is_read_by_the_columns_a_stage_uses(tmp_path):
    t = Tree(repo=tmp_path, stages=())
    t.db.mkdir(parents=True)
    row = {"id": "p", "px": 1.0, "summary": "a quiet village"}
    (t.db / "place.jsonl").write_text(json.dumps(row) + "\n")
    whole, ground, cols = (t.digest(s) for s in ("db:place", "db:place[-summary]", "db:place[id,px]"))
    (t.db / "place.jsonl").write_text(json.dumps({**row, "summary": "a loud town"}) + "\n")
    assert t.digest("db:place") != whole and t.digest("db:place[-summary]") == ground and t.digest("db:place[id,px]") == cols
    (t.db / "place.jsonl").write_text(json.dumps({**row, "px": 2.0}) + "\n")
    assert t.digest("db:place[-summary]") != ground and t.digest("db:place[id,px]") != cols
    assert t.digest("db:nothing") == "absent" and t.digest("ext:/no/such/file") == "absent"


def test_named_fields_of_a_manifest_are_the_digest_or_are_left_out_of_it(tmp_path):
    t = Tree(repo=tmp_path, stages=())
    (t.out).mkdir()
    (t.out / "m.json").write_text(json.dumps({"key": "k1", "seconds": 3}))
    d, rest = t.digest("out:m.json#key"), t.digest("out:m.json#-seconds")
    (t.out / "m.json").write_text(json.dumps({"key": "k1", "seconds": 9}))
    assert t.digest("out:m.json#key") == d and t.digest("out:m.json#-seconds") == rest
    (t.out / "m.json").write_text(json.dumps({"key": "k2", "seconds": 9}))
    assert t.digest("out:m.json#key") != d and t.digest("out:m.json#-seconds") != rest


def laid(t: Tree, x="h1", fog="f1", order="+a\n"):
    (t.stack / "MO2/profiles/NewWorld").mkdir(parents=True, exist_ok=True)
    (t.stack / "installed-NewWorld.json").write_text(json.dumps({
        "rows": {"a": {}, R.OWN_ROWS[0]: {"v": fog}}, "plugins": ["A.esp"],
        "files": {"meshes\\x.nif": ["a", x], "skse\\fog.json": [R.OWN_ROWS[0], fog]}}))
    (t.stack / "MO2/profiles/NewWorld/modlist.txt").write_text(order)
    return t.digest("laid:NewWorld")


def test_the_laid_stack_is_read_but_for_the_rebuilds_own_row(tmp_path):
    t = Tree(repo=tmp_path, stages=(), stack=tmp_path / "stack")
    assert t.digest("laid:NewWorld") == "absent"
    d = laid(t)
    assert laid(t, fog="f2") == d                                # the height fog the rebuild stages itself
    assert laid(t, x="h2") != d and laid(t, order="+b\n+a\n") != d


def test_the_cache_holds_only_while_the_file_is_untouched_and_a_run_never_trusts_it(tree):
    p = tree.repo / "in.txt"
    d = tree.digest("src:in.txt")
    st = p.stat()
    p.write_text("two")                                          # the same size, and its time put back
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns))
    assert tree.digest("src:in.txt") != d
    assert R.run(tree, check_first=False) == 0 and (tree.out / "a.txt").read_text() == "two"
    p.write_text("six")
    cache = json.loads((tree.state / "digests.json").read_text())
    st = p.stat()
    cache[str(p)] = [st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns, cache[str(p)][4]]     # a cache that lies
    (tree.state / "digests.json").write_text(json.dumps(cache))
    again = Tree(repo=tree.repo, stages=tree.stages, py=tree.py)
    assert R.run(again, check_first=False) == 0 and (tree.out / "c.txt").read_text() == "six"
    (tree.state / "digests.json").write_text("not json")         # nor does a broken one stop a plan
    assert states(Tree(repo=tree.repo, stages=tree.stages, py=tree.py))["a"] == "current"


def touch(t: Tree, spec: str, n: int) -> None:
    """Change the thing a read names (make it, the first time)."""
    kind, _, rest = spec.partition(":")
    if kind == "laid":
        laid(t, x=f"h{n}")
    elif kind == "db":
        table, _, cols = rest.partition("[")
        names = [c.strip() for c in cols.rstrip("]").split(",")] if cols else ["id"]
        row = {c.lstrip("-"): "same" if c.startswith("-") else f"v{n}" for c in names} | ({"other": f"v{n}"} if cols.startswith("-") else {})
        t.db.mkdir(parents=True, exist_ok=True)
        (t.db / f"{table}.jsonl").write_text(json.dumps(row) + "\n")
    else:
        path, _, fields = rest.partition("#")
        p = (t.repo if kind == "src" else t.out) / path.replace("**/*", "d/x").replace("**/", "d/").replace("*", "x")
        p = p if p.suffix else p / "x.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({f.lstrip("-"): "same" if f.startswith("-") else f"v{n}" for f in fields.split(",")} | {"other": f"v{n}"})
                     if fields else f"v{n}")


def tmp_tree(tmp_path) -> Tree:
    return Tree(repo=tmp_path / "repo", out=tmp_path / "repo/out", stack=tmp_path / "stack", fresh=True)


@pytest.mark.parametrize("s", R.STAGES, ids=lambda s: s.name)
def test_a_change_to_anything_a_stage_reads_changes_its_key(s, tmp_path):
    """Each read of the real table, in a tmp tree: the stage's key moves with it, and its build key with all but
    what its checks alone read. (A file outside the repo is read by its size and time, where it lies.)"""
    t = tmp_tree(tmp_path)
    for i, spec in enumerate(r for r in s.reads + s.check_reads if not r.startswith("ext:")):
        touch(t, spec, 1)
        a = t.inputs(s)
        touch(t, spec, 2)
        b = t.inputs(s)
        assert t.key_of(a) != t.key_of(b), spec
        assert (t.build_key(s, a) != t.build_key(s, b)) == (spec in s.reads), spec


# ---- a stage with no record: its tool's proof ------------------------------------------------------------------------

def proof_tree(tmp_path, gate=None):
    """`land` keeps its own key beside its output (key.txt = the source's text) and proves it; `cells` names the
    build it stands on but has no proof; `spec` has neither."""
    w = "import json,sys,pathlib as p\no=p.Path('out'); o.mkdir(exist_ok=True)\n(o/sys.argv[1]).write_text(json.dumps({'build_id': sys.argv[2]}))"
    land = ("import pathlib as p\no=p.Path('out'); o.mkdir(exist_ok=True)\n(o/'land.json').write_text('{\"build_id\": \"B2\"}')\n"
            "(o/'land.key').write_text(p.Path('rule.txt').read_text())\n(o/'land.runs').open('a').write('x')")
    proof = ("import sys,pathlib as p\nk=p.Path('out/land.key')\nok=k.exists() and k.read_text()==p.Path('rule.txt').read_text()\n"
             "print('land: its key is today\\'s' if ok else 'land: its key is not today\\'s'); sys.exit(0 if ok else 1)")
    (tmp_path / "rule.txt").write_text("rule 1")
    (tmp_path / "wide.txt").write_text("read by the stage, outside its tool's key")
    stages = (Stage("land", "", cmds=((PY, "-c", land),), checks=(passes_if(gate),) if gate else (),
                    reads=("src:rule.txt", "src:wide.txt"), writes=("out:land.json",), proof=(PY, "-c", proof)),
              Stage("cells", "", cmds=((PY, "-c", w, "cells.json", "B2"),), reads=("out:land.json",), writes=("out:cells.json",),
                    agree=(("out:cells.json#build_id", "out:land.json#build_id", "eq"),)),
              Stage("spec", "", cmds=((PY, "-c", w, "spec.json", "-"),), writes=("out:spec.json",)))
    return Tree(repo=tmp_path, stages=stages, py=sys.executable)


def by_hand(t, key="rule 1"):
    """Outputs the stage tools wrote outside the rebuild: no stamps."""
    t.out.mkdir(exist_ok=True)
    for name in ("land", "cells", "spec"):
        (t.out / f"{name}.json").write_text(json.dumps({"build_id": "B2"}))
    (t.out / "land.key").write_text(key)


def test_a_stage_with_no_record_is_proved_only_by_its_own_tool(tmp_path):
    t = proof_tree(tmp_path)
    by_hand(t)
    rows = {r["stage"]: r for r in R.plan(t)}
    assert rows["land"]["state"] == "proved" and "by its own record" in rows["land"]["why"]
    # agreeing build ids are no proof, and neither is an output that merely exists
    assert rows["cells"]["state"] == "stale" and "no proof" in rows["cells"]["why"]
    assert rows["spec"]["state"] == "stale"
    assert not (t.state / "land.json").exists()                  # the plan records nothing


def test_a_proof_that_fails_leaves_the_stage_stale_with_the_tools_line(tmp_path):
    t = proof_tree(tmp_path)
    by_hand(t, key="rule 0")
    row = R.plan(t)[0]
    assert row["state"] == "stale" and "its key is not today's" in row["why"]


def test_the_run_marks_what_it_saw_proved_and_stamps_only_what_it_made(tmp_path, capsys):
    t = proof_tree(tmp_path)
    by_hand(t)
    assert R.run(t, check_first=False) == 0
    assert not (t.out / "land.runs").exists()                    # proved: not run, and not stamped as built
    land = t.stamp(t.by_name["land"])
    assert land.get("proved") and not land.get("key") and t.stamp(t.by_name["cells"]).get("key") and t.stamp(t.by_name["spec"]).get("key")
    assert "stages proved by their own record, their checks run: 1 (land)" in capsys.readouterr().out
    assert {r["stage"]: r["state"] for r in R.plan(t)} == {"land": "current", "cells": "current", "spec": "current"}
    (t.repo / "wide.txt").write_text("changed")                  # outside the tool's own key: the mark holds everything read
    row = R.plan(t)[0]
    assert row["state"] == "stale" and "wide.txt" in row["why"]
    assert R.run(t, check_first=False) == 0
    assert (t.out / "land.runs").read_text() == "x" and t.stamp(t.by_name["land"]).get("key")
    assert {r["stage"]: r["state"] for r in R.plan(t)} == {"land": "current", "cells": "current", "spec": "current"}


def test_a_proved_stages_checks_run_and_a_red_one_stops_the_run_unmarked(tmp_path, capsys):
    (tmp_path / "gate.txt").write_text("fail")
    t = proof_tree(tmp_path, gate="gate.txt")
    by_hand(t)
    assert R.run(t, check_first=False) == 1
    assert "[land] RED at its check" in capsys.readouterr().out
    assert not t.stamp(t.by_name["land"]) and not (t.out / "land.runs").exists() and not t.stamp(t.by_name["cells"])
    (tmp_path / "gate.txt").write_text("pass")
    assert R.run(t, check_first=False) == 0
    assert t.stamp(t.by_name["land"]).get("proved") and not (t.out / "land.runs").exists()
    assert R.plan(t)[0]["state"] == "current"


def test_an_output_of_another_build_is_stale_whatever_its_stamp(tmp_path):
    t = proof_tree(tmp_path)
    assert R.run(t, check_first=False) == 0
    (t.out / "cells.json").write_text(json.dumps({"build_id": "B1"}))
    row = R.plan(t)[1]
    assert row["state"] == "stale" and "B1" in row["why"]


def test_the_world_file_has_no_proof_of_its_own():
    """Its key holds neither the map data nor its check: with no record it runs, and `write` skips on its key."""
    esm = {s.name: s for s in R.STAGES}["esm"]
    assert not esm.proof and esm.cmds[0][-1] == "write"
    p = subprocess.run([str(REPO / "tools/newworld/world/world.sh"), "current"], capture_output=True, text=True)
    assert p.returncode == 2 and "usage" in p.stderr


def test_the_cells_tool_ends_with_its_own_record_and_proves_it(tmp_path, monkeypatch):
    """One water cell, built whole: cells.json and the key beside it, which `--current` then finds today's."""
    import numpy as np

    from tools.newworld import water_kinds
    from tools.newworld.world import cells
    lcd, out, db = tmp_path / "landcover", tmp_path / "plugin", tmp_path / "db"
    for d in (lcd, out / "land", db):
        d.mkdir(parents=True)
    monkeypatch.setattr(cells, "LC", lcd)
    monkeypatch.setattr(cells.f, "OUT", tmp_path)
    monkeypatch.setattr(cells.lc, "DB", db)
    monkeypatch.setattr(cells.lc, "jsonl", lambda t: [{"id": "r", "name": "R", "wetness": 0.5}])
    monkeypatch.setattr(water_kinds, "region_character", lambda: {})
    (out / "land/manifest.json").write_text(json.dumps({"key": "k", "build_id": "B", "grid": {"cy_top": 0, "cy_bottom": 0, "cx0": 0, "cells_x": 1}}))
    (lcd / "legend.json").write_text(json.dumps({"build_id": "B", "kinds": ["lake"], "regions": ["r"]}))
    (lcd / "key.txt").write_text("B:lc")
    for n, v in (("region", 0), ("kind", 0), ("flags", 1)):
        np.save(lcd / f"{n}.npy", np.full((33, 33), v, np.uint8))
    (tmp_path / "water_flow_cells.json").write_text("[]")
    for n in ("region", "region_note"):
        (db / f"{n}.jsonl").write_text("")
    assert cells.main(["--current", "--out", str(out)]) == 1
    assert cells.main(["--out", str(out)]) == 0 and json.loads((out / "cells.json").read_text())["cells"]["0,0"]["water"]
    assert cells.main(["--current", "--out", str(out)]) == 0
    (tmp_path / "water_flow_cells.json").write_text("[ ]")
    assert cells.main(["--current", "--out", str(out)]) == 1


# ---- the terrain's proof, and the build that keeps its id -----------------------------------------------------------

@pytest.fixture
def terrain(tmp_path, monkeypatch):
    from tools.newworld import terrain as T
    t = tmp_tree(tmp_path)
    reads = tuple(r for r in t.by_name["terrain"].reads if not r.startswith("ext:"))
    monkeypatch.setattr(T, "_reads", lambda: (t, reads))
    monkeypatch.setattr(T, "OUT", tmp_path / "terrain")
    T.OUT.mkdir()
    (T.OUT / "heightmap.npy").write_bytes(b"heights")
    sha = hashlib.sha256(b"heights").hexdigest()
    (T.OUT / "build.json").write_text(json.dumps({"id": "B1", "sha256": sha}))
    for r in reads:
        touch(t, r, 0)
    T.record_inputs("B1", sha, T.input_digests())
    return T, t, reads, sha


def test_the_terrains_proof_fails_on_a_change_to_anything_its_stage_reads(terrain):
    T, t, reads, sha = terrain
    assert T.unproven() == [] and T.inputs_changed() == []
    assert len(reads) >= 20 and {"out:newworld/raster/water.png", "out:newworld/roads.json", "src:tools/newworld/terrain_*.py"} <= set(reads)
    for r in reads:
        touch(t, r, 1)
        assert T.unproven() == [r.split(":", 1)[1]], r
        touch(t, r, 0)
    assert T.unproven() == []


def test_the_terrains_proof_fails_on_a_heightmap_or_a_record_not_the_builds(terrain):
    T, t, reads, sha = terrain
    (T.OUT / "heightmap.npy").write_bytes(b"other heights")
    assert T.unproven() == ["heightmap.npy (not the build's own)"]
    (T.OUT / "heightmap.npy").write_bytes(b"heights")
    T.record_inputs("B0", sha, T.input_digests())
    assert "no record of this build's inputs" in T.unproven()[0]
    (T.OUT / "inputs.json").unlink()
    assert "no record of this build's inputs" in T.unproven()[0]


def test_a_build_whose_heightmap_is_the_standing_builds_keeps_its_id_and_record():
    from tools.newworld import terrain as T
    old = {"id": "B1", "files": "bucket/B1/", "sha256": "s1", "held": {"p": 1}, "seconds": 500, "peak_rss_mb": 5000, "inputs": {"a": 1}}
    new = {"id": "B2", "files": "bucket/B2/", "sha256": "s1", "held": {"p": 1}, "seconds": 531, "peak_rss_mb": 5100}
    assert T.settle(old, new) is None                                    # the record stands, bytes and time
    assert T.settle(old, {**new, "held": {"p": 2}}) == {**new, "id": "B1", "files": "bucket/B1/", "held": {"p": 2}}
    assert T.settle(old, {**new, "sha256": "s2"})["id"] == "B2" and T.settle(None, new)["id"] == "B2"


def test_the_terrains_upload_is_its_own_command(tmp_path):
    from tools.newworld import terrain as T
    from tools.newworld import terrain_upload
    p = subprocess.run([sys.executable, "-m", "tools.newworld.terrain_upload"], cwd=REPO, env=dict(os.environ, NW_UPLOAD="0"),
                       capture_output=True, text=True)
    assert p.returncode == 0 and "upload skipped" in p.stdout
    assert T.BUCKET == terrain_upload.BUCKET and "terrain_upload.upload()" in inspect.getsource(T.build)


# ---- the navmesh was fed the placed objects ---------------------------------------------------------------------------

def nav(tmp_path, tris, fed):
    from tools.newworld.world import navobjects
    d = tmp_path / "plugin" / "navmesh"
    d.mkdir(parents=True, exist_ok=True)
    (d / "check.json").write_text(json.dumps({"objects": tris}))
    (d / "build.json").write_text(json.dumps({} if fed is None else {"placed": {"objects": fed}}))
    return navobjects, tmp_path / "plugin"


def test_a_navmesh_no_placed_object_reached_is_red(tmp_path):
    N, p = nav(tmp_path, 0, None)
    r = N.rows(p, tmp_path, count=lambda refs, data: None)
    assert [ok for _, _, ok, _ in r] == [False, False] and "owed by the navmesh tool" in r[1][3]


def test_the_fed_count_must_be_the_collidable_refs(tmp_path):
    N, p = nav(tmp_path, 5000, 120)
    assert [ok for _, _, ok, _ in N.rows(p, tmp_path, count=lambda refs, data: 120)] == [True, True]
    assert [ok for _, _, ok, _ in N.rows(p, tmp_path, count=lambda refs, data: 150)] == [True, False]
    assert [ok for _, _, ok, _ in N.rows(p, tmp_path, count=lambda refs, data: None)] == [True, False]


# ---- the checks the rebuild gates on ---------------------------------------------------------------------------------

def test_terrain_needs_fail_only_on_a_failure_not_accepted():
    rows = [{"place_id": "a", "need": "rise", "ok": False, "why": "lift 0.4 m"}, {"place_id": "b", "need": "flat-pad", "ok": False, "why": ""},
            {"place_id": "c", "need": "island", "ok": True, "why": ""}]
    acc = [{"place_id": "a", "need": "rise", "reason": "lift # m", "bound": 0.4, "why": "no land"},
           {"place_id": "c", "need": "island", "reason": "islet # m#, joined to the mainland", "why": "joined"}]
    new, old, gone = terrain_needs.judge_accepted(rows, acc)
    assert [r["place_id"] for r in new] == ["b"] and [r["place_id"] for r in old] == ["a"] and [a["place_id"] for a in gone] == ["c"]


def test_an_accepted_need_that_fails_for_another_reason_or_worse_is_new():
    acc = [{"place_id": "p", "need": "flat-pad", "reason": "slope p90 # deg", "bound": 13.4, "why": "the pad holds the rise"}]

    def judged(why):
        new, old, _ = terrain_needs.judge_accepted([{"place_id": "p", "need": "flat-pad", "ok": False, "why": why}], acc)
        return "new" if new else "accepted"
    assert judged("slope p90 13.4 deg") == "accepted" and judged("slope p90 9.0 deg") == "accepted"
    assert judged("slope p90 13.5 deg") == "new"                          # far worse, or a little: past what was accepted
    assert judged("no room behind the bank (12% of the pad)") == "new"    # another reason
    assert judged("no land in the footprint") == "new"
    lift = [{"place_id": "p", "need": "rise", "reason": "lift # m", "bound": 1.2, "why": "the map gives no more"}]
    low = [{"place_id": "p", "need": "rise", "ok": False, "why": "lift 0.3 m"}]
    assert terrain_needs.judge_accepted(low, lift)[0] == low              # a smaller lift is the worse one


def test_the_accepted_needs_file_names_place_need_reason_bound_and_why():
    words = Path(terrain_needs.__file__).read_text()
    for a in json.loads((R.REPO / "newworld/sources/terrain_needs_accepted.json").read_text())["accepted"]:
        assert a["place_id"] and a["need"] and len(a["why"]) > 10
        assert (a["reason"] in terrain_needs.WORSE) == isinstance(a.get("bound"), float), a
        assert a["reason"].split("#")[0].split("(")[0].strip() in words, a      # a reason the judge gives
        assert terrain_needs.reason(a["reason"].replace("#", "7"))[0] == a["reason"], a


def test_an_empty_table_keeps_its_empty_file(tmp_path):
    """build_db starts from no table files: a table with no rows is written as its empty file, never left out."""
    from tools.argonia_world import db
    from tools.newworld import build_db
    (tmp_path / "story/data").mkdir(parents=True)
    (tmp_path / "story/data/schema.sql").write_text("CREATE TABLE a (id TEXT PRIMARY KEY);\nCREATE TABLE b (id TEXT PRIMARY KEY);\n")
    w = db.open(tmp_path, cache=False)
    w.insert("a", id="x")
    assert build_db.save_whole(w) == ["a", "b"]
    d = tmp_path / "story/data/db"
    assert (d / "a.jsonl").read_text().strip() == '{"id":"x"}' and (d / "b.jsonl").exists() and (d / "b.jsonl").read_text() == ""


# ---- settled: the world file cannot change under a long job that reads it -----------------------------------------

def test_src_patterns_match_within_a_name_and_across_folders():
    m = lambda pat, f: bool(R._src_re(pat).match(f))  # noqa: E731
    assert m("tools/newworld/*.py", "tools/newworld/verify.py") and not m("tools/newworld/*.py", "tools/newworld/small/__init__.py")
    assert m("tools/ArgoniaPlugin/**/*.cs", "tools/ArgoniaPlugin/NewWorld.cs") and m("tools/ArgoniaPlugin/**/*.cs", "tools/ArgoniaPlugin/a/b/C.cs")
    assert m("newworld/places/*/land.jsonl", "newworld/places/helstrom/land.jsonl")
    assert m("newworld/sources/flora/**/*", "newworld/sources/flora/sets/a.json") and not m("in.txt", "in.txt.bak")
    srcs = R.world_sources()
    hit = lambda f: any(p.match(f) for p in srcs)  # noqa: E731
    assert hit("tools/ArgoniaPlugin/NewWorldMap.cs") and hit("newworld/sources/world_formids.json") and hit("mods/dependencies.json")
    assert not hit("docs/PLAN.md") and not hit(".claude/skills/world-build/SKILL.md") and not hit("tooling/tidy.py")


def test_settled_names_a_tree_behind_a_stale_stage_and_a_lane_on_the_sources(tree, tmp_path_factory):
    main, origin = tree.repo, tmp_path_factory.mktemp("origin") / "o.git"

    def git(*a, cwd=main):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=cwd, check=True, capture_output=True)
    git("init", "-q", "--bare", "-b", "main", str(origin))
    git("init", "-q", "-b", "main")
    (main / "notes.md").write_text("n")
    (main / ".gitignore").write_text("out/\n")
    git("add", "in.txt", "gate.txt", "notes.md", ".gitignore")
    git("commit", "-q", "-m", "seed")
    git("remote", "add", "origin", str(origin))
    git("push", "-q", "-u", "origin", "main")
    assert any("the rebuild is owed for a, b, c" in w for w in R.unsettled(tree))      # nothing built yet
    assert R.run(tree, check_first=False) == 0
    assert R.unsettled(tree) == []
    # a lane that changes only what no stage reads leaves it settled; one that changes a source does not
    lanes = tmp_path_factory.mktemp("lanes")
    git("worktree", "add", "-q", "-b", "worktree-docs", str(lanes / "docs"), "origin/main")
    (lanes / "docs" / "notes.md").write_text("more")
    assert R.unsettled(tree) == []
    git("worktree", "add", "-q", "-b", "worktree-rule", str(lanes / "rule"), "origin/main")
    (lanes / "rule" / "in.txt").write_text("two")                                       # uncommitted is enough
    assert [w for w in R.unsettled(tree) if w.startswith("lane rule: in.txt changes")] and len(R.unsettled(tree)) == 1
    git("commit", "-q", "-am", "rule", cwd=lanes / "rule")
    assert len(R.unsettled(tree)) == 1
    # the lane lands: the main tree is behind until it is level, then the rebuild is owed, then it is settled
    git("push", "-q", "origin", "HEAD:main", cwd=lanes / "rule")
    assert any("1 commits behind origin/main" in w for w in R.unsettled(tree))
    git("merge", "-q", "--ff-only", "origin/main")
    assert any("the rebuild is owed for a" in w for w in R.unsettled(tree))
    assert R.run(tree, check_first=False) == 0
    assert R.unsettled(tree) == []
    # from a worktree it is never settled: the world file is the main tree's
    assert "the world file is the main tree's" in R.unsettled(Tree(repo=lanes / "docs", stages=tree.stages, py=sys.executable))[0]
