"""L2 for the pass ledger (owner, 2026-11-03): the reach key, the plan's skip (suffix, independent steps), the force
flag, run_batch skipping a passed journey whole and counting steps, the reader's verdict, and lod.sh's archive skip."""
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools import pass_ledger as pl  # noqa: E402
from tools.tests import test_run_batch as trb  # noqa: E402
from tools.tests.test_run_batch import journeys, no_sleep  # noqa: E402,F401
from tools import run_batch as rb  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    (r / "ui").mkdir(parents=True)
    (r / "skse").mkdir()
    (r / "out").mkdir()
    (r / "ui" / "a.css").write_text("a")
    (r / "skse" / "b.cpp").write_text("b")
    (r / "out" / "Argonia.esm").write_bytes(b"esm1")
    subprocess.run(["git", "init", "-q"], cwd=r, check=True)
    subprocess.run(["git", "add", "."], cwd=r, check=True)
    pl.clear_cache()
    yield r
    pl.clear_cache()


def J(**kw):
    return {"id": "j", "runner": 1, "reach": ["ui/**"], "steps": [{"name": "a"}, {"name": "b"}, {"name": "c"}], **kw}


def test_key_follows_own_reach_only(repo):
    j = J()
    h0 = pl.reach_hash(j, j["steps"][0], repo)
    (repo / "skse" / "b.cpp").write_text("changed")  # outside the reach
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    pl.clear_cache()
    assert pl.reach_hash(j, j["steps"][0], repo) == h0
    (repo / "ui" / "a.css").write_text("changed")  # inside it
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    pl.clear_cache()
    assert pl.reach_hash(j, j["steps"][0], repo) != h0


def test_key_esm_step_reach_and_whole_build(repo):
    j = J(reach=["ui/**", "esm"])
    h0 = pl.reach_hash(j, j["steps"][0], repo)
    (repo / "out" / "Argonia.esm").write_bytes(b"esm2")
    pl.clear_cache()
    assert pl.reach_hash(j, j["steps"][0], repo) != h0
    step = {"name": "a", "reach": ["skse/**"]}
    assert pl.reach_of(j, step) == ["ui/**", "esm", "skse/**"]
    assert pl.reach_of({"id": "x", "steps": []}, step) == list(pl.WHOLE_BUILD)  # no reach: the whole build
    # the step's own definition is in its key
    assert pl.reach_hash(j, {"name": "a", "do": [{"wait": 1}]}, repo) != pl.reach_hash(j, {"name": "a"}, repo)


def passes(j, names, repo, path):
    for n in names:
        s = next(x for x in j["steps"] if x["name"] == n)
        pl.append({"journey": j["id"], "step": n, "reach_hash": pl.reach_hash(j, s, repo), "status": "pass",
                   "time": "T", "still": f"/s/{n}.png", "kept": {"k": n}}, path)


def test_plan_skips_the_passed_suffix_only(repo, tmp_path):
    led = tmp_path / "l.jsonl"
    j = J()
    passes(j, ["a", "c"], repo, led)
    p = pl.plan(j, pl.last_rows(led), repo=repo)
    assert p["run"] == ["a", "b"] and list(p["skip"]) == ["c"]  # a hands state to b: it runs again
    passes(j, ["b"], repo, led)
    assert pl.plan(j, pl.last_rows(led), repo=repo)["run"] == []
    assert len(pl.plan(j, pl.last_rows(led), force=True, repo=repo)["run"]) == 3  # --all


def test_plan_independent_steps_and_needs(repo, tmp_path):
    led = tmp_path / "l.jsonl"
    j = J(independent_steps=True)
    passes(j, ["a", "c"], repo, led)
    assert pl.plan(j, pl.last_rows(led), repo=repo)["run"] == ["b"]
    j["steps"][1]["needs"] = ["a"]
    assert pl.plan(j, pl.last_rows(led), repo=repo)["run"] == ["a", "b"]


def test_a_later_fail_and_reader_rows(repo, tmp_path):
    led = tmp_path / "l.jsonl"
    j = J()
    passes(j, ["a"], repo, led)
    row = pl.last_rows(led)[("j", "a", pl.reach_hash(j, j["steps"][0], repo))]
    pl.append({**row, "status": "fail"}, led)
    assert not pl.passed(pl.last_rows(led), "j", "a", row["reach_hash"])
    with pytest.raises(SystemExit):
        pl.reader_pass("j", "a", led)
    pl.append({**row, "status": "reader"}, led)
    # a reader row's still exists for these inputs: skipped on a rerun (the reader judges the still); its PASS is recorded
    assert pl.passed(pl.last_rows(led), "j", "a", row["reach_hash"])["status"] == "reader"
    pl.reader_pass("j", "a", led)
    assert pl.passed(pl.last_rows(led), "j", "a", row["reach_hash"])["reader"] == "PASS"


def test_batch_skips_a_passed_journey_and_counts(tmp_path, journeys, monkeypatch):  # noqa: F811
    led = tmp_path / "passes.jsonl"
    f, s, disk = trb.run(tmp_path, ["good", "bad"])
    rows = pl.rows(led)
    assert [(r["journey"], r["status"]) for r in rows] == [("good", "pass"), ("bad", "fail")]
    assert disk["steps_run"] == 2 and disk["steps_skipped"] == 0
    f, s, disk = trb.run(tmp_path, ["good", "bad"])
    good, bad = disk["items"]
    assert good["skipped"].startswith("skipped: passed") and good["passed"] and good["steps_skipped"] == 1
    assert "skipped" not in bad and disk["steps_run"] == 1 and disk["steps_skipped"] == 1
    r = rb.shrink(rb.load_batch(["good", "bad"]), pl.last_rows(led))
    assert r == {"items": 1, "items_all": 2, "steps": 1, "steps_all": 2}
    assert rb.shrink(rb.load_batch(["good"]), pl.last_rows(led))["items"] == 0
    assert rb.shrink(rb.load_batch(["good"]), pl.last_rows(led), force=True)["items"] == 1
    batch = {"id": "t", "items": rb.parse_items(["good"]), "relaunch_mb": 6000, "relaunch_every": 0}
    s = rb.Batch(trb.Fake(), batch, tmp_path / "out2", stills=False, force=True).run()
    assert s["steps_run"] == 1 and "skipped" not in s["items"][0]


def test_runner_skip_restores_kept_and_still(tmp_path, journeys):  # noqa: F811
    from tools import run_journey as rj
    j = {"id": "good", "scene": "sc", "steps": [{"name": "x"}, {"name": "y"}]}
    f = trb.Fake()
    f.launch()
    r = rj.Runner(f, tmp_path / "o", stills=False)
    rep = r.run(j, "s", skip={"x": {"time": "T", "still": "/s/x.png", "run": "/r", "kept": {"k": 1}}})
    assert rep["passed"] and rep["steps"][0]["still"] == "/s/x.png" and rep["steps"][0]["skipped"]
    assert r.kept["k"] == 1 and not rep["steps"][1].get("skipped")


def _lod_skip():
    spec = importlib.util.spec_from_file_location("lod_skip", ROOT / "infra" / "gpu-box" / "lod_skip.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_lod_archive_skip():
    m = _lod_skip()
    meta = {"ContentLength": 99, "Metadata": {"argonia-files": "3", "argonia-bytes": "1536"}}
    assert m.archived(meta, 3, 1536)
    assert not m.archived(meta, 4, 1536) and not m.archived(meta, 3, 2048)
    assert not m.archived(None, 3, 1536)  # no object
    legacy = {"ContentLength": 1536 + 3 * 512 + 20480}
    assert m.archived(legacy, 3, 1536)
    assert not m.archived({"ContentLength": 1000}, 3, 1536)  # a short (torn) upload
    assert not m.archived({"ContentLength": 10 ** 10}, 3, 1536)


def test_lod_skip_cli(capsys, monkeypatch):
    import io
    m = _lod_skip()
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"Metadata": {"argonia-files": "2", "argonia-bytes": "5"}})))
    assert m.main(["2", "5"]) == 0
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert m.main(["2", "5"]) == 1


def test_refresh_keeps_reach_lines(tmp_path, monkeypatch):
    from tools.journeys import __main__ as jm
    monkeypatch.setattr(jm, "JOURNEYS", tmp_path)
    f = tmp_path / "x.yaml"
    f.write_text("# c\nid: x\nreach: [esm]\nrunner: 1\n")
    lines = jm._reach_lines()
    f.write_text("# c\nid: x\nrunner: 1\n")  # a generator rewrote it
    jm._put_reach(lines)
    assert f.read_text() == "# c\nid: x\nreach: [esm]\nrunner: 1\n"


@pytest.mark.parametrize("name", ["world-panel", "sky-ab"])
def test_panel_and_sky_reach_ignores_other_journeys_and_follows_placement(name, tmp_path):
    """The 00:41 rerun ran 21 steps, 0 skipped, after a sky-ab bound edit: with no `reach:` every journey edit moved
    every key. Their own reach: an unrelated journey's edit leaves the keys; a placement (ESM) change moves them."""
    import yaml
    j = yaml.safe_load((ROOT / "tests" / "journeys" / f"{name}.yaml").read_text())
    assert "esm" not in j["reach"] and "records: Weathers" in j["reach"] and "tests/journeys/**" not in j["reach"]
    r = tmp_path / "repo"
    (r / "plugin" / "Argonia" / "Weathers").mkdir(parents=True)
    (r / "plugin" / "Argonia" / "Weathers" / "w.yaml").write_text("sky: 1\n")
    (r / "tests" / "journeys").mkdir(parents=True)
    (r / "tests" / "scenes").mkdir(parents=True)
    (r / "data").mkdir()
    (r / "out").mkdir()
    (r / "tests" / "journeys" / "other.yaml").write_text("id: other\n")
    (r / "tests" / "scenes" / "world-panel.txt").write_text("player.moveto X\n")
    (r / "data" / "dependencies.json").write_text("{}")
    (r / "out" / "ArgoniaWorld.esm").write_bytes(b"refs1")
    subprocess.run(["git", "init", "-q"], cwd=r, check=True)
    subprocess.run(["git", "add", "."], cwd=r, check=True)
    pl.clear_cache()
    keys = lambda: [pl.reach_hash(j, s, r) for s in j["steps"]]  # noqa: E731
    k0 = keys()
    (r / "tests" / "journeys" / "other.yaml").write_text("id: other\nsteps: []\n")
    subprocess.run(["git", "add", "."], cwd=r, check=True)
    pl.clear_cache()
    assert keys() == k0
    (r / "out" / "ArgoniaWorld.esm").write_bytes(b"refs2")   # a placement change elsewhere: the ESM is not in reach
    pl.clear_cache()
    assert keys() == k0
    (r / "plugin" / "Argonia" / "Weathers" / "w.yaml").write_text("sky: 2\n")   # a weather record the stops judge
    pl.clear_cache()
    assert all(a != b for a, b in zip(keys(), k0))
    pl.clear_cache()


def _plugin(tmp_path):
    r = tmp_path / "rec"
    pa = r / "plugin" / "Argonia"
    ws = pa / "Worldspaces" / "WS - 000800_X.esm"
    for rel, txt in (("Weathers/a.yaml", "w: 1\n"), ("Weathers/b.yaml", "w: 2\n"), ("ImageSpaces/i.yaml", "i: 1\n"),
                     ("Worldspaces/WS - 000800_X.esm/RecordData.yaml",
                      "EditorID: WS\nTopCell:\n  Persistent:\n  - FormKey: 1\n    EditorID: Ref_A\n    Position: 1, 2, 3\n"
                      "  - FormKey: 2\n    EditorID: Ref_B\n    Position: 4, 5, 6\n"),
                     ("Worldspaces/WS - 000800_X.esm/-1, 0/-2, 0/0A_X.esm/RecordData.yaml", "Grid:\n  Point: -9, 27\n"),
                     ("Worldspaces/WS - 000800_X.esm/-1, 0/-2, 1/0B_X.esm/RecordData.yaml", "Grid:\n  Point: 3, 4\n")):
        (pa / rel).parent.mkdir(parents=True, exist_ok=True)
        (pa / rel).write_text(txt)
    pl.clear_cache()
    return r, pa, ws


def test_a_records_spec_hashes_only_its_files(tmp_path):
    r, pa, _ = _plugin(tmp_path)
    j = {"id": "x", "reach": ["records: Weathers", "records: ImageSpaces"]}
    h = lambda: pl.reach_hash(j, {"name": "s"}, r)  # noqa: E731
    h0 = h()
    (pa / "Climates").mkdir()
    (pa / "Climates" / "c.yaml").write_text("c\n")   # another folder: not reached
    (pa / "Statics").mkdir()
    (pa / "Statics" / "s.yaml").write_text("s\n")
    pl.clear_cache()
    assert h() == h0
    (pa / "Weathers" / "b.yaml").write_text("w: 3\n")
    pl.clear_cache()
    assert h() != h0
    # the ESM is not read by a records-only reach
    (r / "out").mkdir()
    (r / "out" / "ArgoniaWorld.esm").write_bytes(b"x")
    h1 = h()
    (r / "out" / "ArgoniaWorld.esm").write_bytes(b"y")
    pl.clear_cache()
    assert h() == h1


def test_a_cell_spec_follows_the_cell_folder_and_its_shard_line(tmp_path):
    import gzip
    r, pa, ws = _plugin(tmp_path)
    land = r / "out" / "terrain" / "land"
    land.mkdir(parents=True)

    def shard(v):
        with gzip.open(land / "cy+027.jsonl.gz", "wb") as f:
            f.write(json.dumps({"cell": "A", "vhgt": v, "x": -9, "y": 27}).encode() + b"\n")
            f.write(json.dumps({"cell": "B", "vhgt": 0, "x": 50, "y": 27}).encode() + b"\n")
    shard("a")
    j = {"id": "x", "reach": ["records: cell -9,27"]}
    h = lambda: pl.reach_hash(j, {"name": "s"}, r)  # noqa: E731
    h0 = h()
    (ws / "-1, 0" / "-2, 1" / "0B_X.esm" / "RecordData.yaml").write_text("Grid:\n  Point: 3, 4\nchanged: 1\n")   # another cell
    (pa / "Weathers" / "a.yaml").write_text("w: 9\n")
    pl.clear_cache()
    assert h() == h0
    (ws / "-1, 0" / "-2, 0" / "0A_X.esm").mkdir(exist_ok=True)
    (ws / "-1, 0" / "-2, 0" / "0A_X.esm" / "Temporary.yaml").write_text("ref: 1\n")   # a ref placed in the cell
    pl.clear_cache()
    h1 = h()
    assert h1 != h0
    shard("b")   # the cell's own LAND line
    pl.clear_cache()
    h2 = h()
    assert h2 != h1
    with gzip.open(land / "cy+027.jsonl.gz", "ab") as f:   # a neighbour's line in the same shard: not this cell
        f.write(json.dumps({"cell": "C", "vhgt": 1, "x": -8, "y": 27}).encode() + b"\n")
    pl.clear_cache()
    assert h() == h2
    j = {"id": "x", "reach": ["records: cell -9,27 r1"]}   # the ring takes the neighbour in
    pl.clear_cache()
    h3 = h()
    with gzip.open(land / "cy+027.jsonl.gz", "ab") as f:
        f.write(json.dumps({"cell": "D", "vhgt": 2, "x": -8, "y": 27}).encode() + b"\n")
    pl.clear_cache()
    assert h() != h3


def test_wrld_spec_leaves_out_persistent_refs_and_ref_spec_is_one_of_them(tmp_path):
    r, pa, ws = _plugin(tmp_path)
    f = ws / "RecordData.yaml"
    hs = lambda *specs: pl.reach_hash({"id": "x", "reach": [*("records: " + s for s in specs)]}, {"name": "s"}, r)  # noqa: E731
    w0, a0, b0 = hs("wrld"), hs("ref Ref_A"), hs("ref Ref_B")
    f.write_text(f.read_text().replace("4, 5, 6", "4, 5, 7"))   # ref B moved
    pl.clear_cache()
    assert (hs("wrld"), hs("ref Ref_A")) == (w0, a0) and hs("ref Ref_B") != b0
    f.write_text(f.read_text().replace("EditorID: WS", "EditorID: WS2"))   # the record itself
    pl.clear_cache()
    assert hs("wrld") != w0


def test_lint_accepts_records_specs_and_rejects_bad_ones():
    from tools import journey_lint as jl
    assert jl.reach(["records: Weathers", "records: wrld", "records: cell -9,27 r1", "records: ref A_b"], "") == []
    assert jl.reach(["records: cell nine"], "")


def test_a_setup_step_is_never_skipped(repo, tmp_path):
    led = tmp_path / "l.jsonl"
    for extra in ({}, {"independent_steps": True}):
        j = J(**extra)
        j["steps"][0]["setup"] = True
        passes(j, ["a", "b", "c"], repo, led)
        assert pl.plan(j, pl.last_rows(led), repo=repo)["run"] == []  # nothing else runs: no setup alone
        j2 = J(**extra)
        j2["steps"][0]["setup"] = True
        j2["steps"][2]["do"] = [{"wait": 1}]  # c changed: its key moved
        p = pl.plan(j2, pl.last_rows(led), repo=repo)
        assert p["run"][0] == "a" and "a" not in p["skip"] and "c" in p["run"]
        if not extra:
            assert p["run"] == ["a", "b", "c"]
