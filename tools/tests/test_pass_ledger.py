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
    assert "esm" in j["reach"] and "tests/journeys/**" not in j["reach"]
    r = tmp_path / "repo"
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
    (r / "out" / "ArgoniaWorld.esm").write_bytes(b"refs2")   # a placement change
    pl.clear_cache()
    assert all(a != b for a, b in zip(keys(), k0))
    pl.clear_cache()


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
