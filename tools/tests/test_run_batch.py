"""L2 for tools/run_batch.py: a fake bridge; items run in order past a failure, a crash relaunches and the batch goes
on, memory past the threshold relaunches, a chained item skips the save load, an unchanged scene is not re-sent,
and summary.json carries pass/fail, the failing step's reason and the timings."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import run_batch as rb  # noqa: E402
from tools import run_journey as rj  # noqa: E402
from tools.bridge import BridgeError, GameDown  # noqa: E402


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch, tmp_path):
    monkeypatch.setattr(rj.time, "sleep", lambda s: None)
    monkeypatch.setattr(rj, "RESUME", tmp_path / "resume")


class Machine:
    def __init__(self, fake):
        self.f = fake

    def ps(self, script, timeout=120):
        if "Get-Process -Name" in script:
            return "".join(f"LOD {n}\n" for n in getattr(self.f, "lod", []))
        return "MB none" if not self.f.alive else f"MB {self.f.mb}"


class Fake:
    """alive, private MB growing 230 per load; `crash_in` names a journey whose `boom` console line kills the game."""

    def __init__(self, mb=3000):
        self.alive, self.mb, self.loads, self.launches, self.lines = False, mb, 0, 0, []
        self.machine = Machine(self)

    def launch(self, fresh=False):
        self.launches += 1
        self.alive, self.mb = True, 2500
        return {"ping": {}}

    def call(self, cmd, *args, timeout=None):
        if not self.alive:
            raise GameDown("SkyrimSE is not running")
        if cmd == "load":
            self.loads += 1
            self.mb += 230
            return {"loaded": args[0]}
        if cmd == "player":
            return {"pos": {"x": 0.0, "y": 0.0, "z": 0.0}, "dead": False}
        if cmd == "events":
            return {"last": 1, "events": []} if args else {"last": 1}
        if cmd == "console":
            self.lines.append(args[0])
            if args[0] == "boom":
                self.alive = False
                raise GameDown("SkyrimSE is not running; crash log crash-1.log")
            if args[0] == "IsPC1stPerson":
                return {"output": ">> 0.00"}
            return {"output": f"{args[0]} >> 1.00"}
        return {}

    def resolve_refs(self, text):
        return text

    def screenshot(self, out):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"png")
        return out


@pytest.fixture
def journeys(tmp_path, monkeypatch):
    import yaml
    d = tmp_path / "journeys"
    d.mkdir()
    scenes = tmp_path / "scenes"
    scenes.mkdir()
    (scenes / "sc.txt").write_text("coc ARG_HoldingCell\n")
    good = {"name": "ok", "expect": [{"read": ["player"], "path": "dead", "eq": False}]}
    for jid, steps in {"good": [good], "bad": [{"name": "nope", "expect": [{"read": ["player"], "path": "dead", "eq": True,
                                                                            "within": 0}]}],
                       "crash": [{"name": "die", "do": [{"console": "boom"}]}]}.items():
        (d / f"{jid}.yaml").write_text(yaml.safe_dump({"id": jid, "runner": 1, "scene": "sc", "steps": steps}))
    monkeypatch.setattr(rb, "JOURNEYS", d)
    monkeypatch.setattr(rj, "SCENES", scenes)
    puts = []
    monkeypatch.setattr(rj.subprocess, "run", lambda args, **kw: puts.append(args))
    return puts


def run(tmp_path, items, **kw):
    batch = {"id": "t", "items": rb.parse_items(items), "relaunch_mb": kw.pop("mb", 6000), "relaunch_every": kw.pop("every", 0)}
    f = Fake()
    s = rb.Batch(f, batch, tmp_path / "out", stills=False).run()
    return f, s, json.loads((tmp_path / "out" / "summary.json").read_text())


def test_order_past_failure_and_summary(tmp_path, journeys):
    f, s, disk = run(tmp_path, ["good", "bad", "good"])
    assert [i["id"] for i in disk["items"]] == ["good", "bad", "good"]
    assert [i["passed"] for i in disk["items"]] == [True, False, True]
    bad = disk["items"][1]
    assert bad["failed_at"] == "nope" and "wanted eq True" in bad["reason"]
    assert disk["passed"] is False and disk["passed_n"] == 2 and disk["failed"][0].startswith("bad#1: nope")
    assert set(disk["step_classes_s"]) == {"launch", "scene_apply", "steps"}
    assert f.launches == 1  # the game was down at the start: launched once, then never again


def test_crash_relaunches_and_goes_on(tmp_path, journeys):
    f, s, _ = run(tmp_path, ["crash", "good"])
    assert s["items"][0]["crash"] and not s["items"][0]["passed"]
    assert s["items"][1]["passed"] and s["items"][1]["relaunched_before"]
    assert f.launches == 2 and s["launches"][1]["why"] == "the game is not running"


def test_memory_threshold_relaunches(tmp_path, journeys):
    f, s, _ = run(tmp_path, ["good:4"], mb=2900)  # 2500 at launch, +230 a load: past 2900 after two loads
    assert [i["relaunched_before"] for i in s["items"]] == [True, False, True, False]
    assert "private memory" in s["launches"][1]["why"]


def test_relaunch_every_n(tmp_path, journeys):
    f, s, _ = run(tmp_path, ["good:3"], every=2)
    assert f.launches == 2 and s["launches"][1]["why"] == "2 items since the last launch"


def test_chain_skips_the_load_only_after_a_pass(tmp_path, journeys):
    f, s, _ = run(tmp_path, ["good", {"journey": "good", "chain": True}, "bad", {"journey": "good", "chain": True}])
    assert [i["loaded"] for i in s["items"]] == [True, False, True, True]
    assert f.loads == 3


def test_unchanged_scene_is_sent_once(tmp_path, journeys):
    run(tmp_path, ["good:3"])
    assert len(journeys) == 1


def test_scene_item_and_parse(tmp_path, journeys):
    _, s, _ = run(tmp_path, ["scene:sc"])
    assert s["items"][0]["kind"] == "scene" and s["items"][0]["passed"]
    assert rb.parse_items(["croc:2", {"journey": "x", "chain": True}]) == [
        {"kind": "journey", "id": "croc", "runs": 2, "chain": False, "save": None},
        {"kind": "journey", "id": "x", "runs": 1, "chain": True, "save": None}]
    with pytest.raises(SystemExit):
        rb.parse_items([{"journey": "x", "scene": "y"}])
    with pytest.raises(SystemExit):
        rb.parse_items([{"journey": "x", "bogus": 1}])


def test_launch_failing_twice_aborts(tmp_path, journeys):
    batch = {"id": "t", "items": rb.parse_items(["good"]), "relaunch_mb": 6000, "relaunch_every": 0}
    f = Fake()
    f.launch = lambda fresh=False: (_ for _ in ()).throw(BridgeError("no main menu"))
    s = rb.Batch(f, batch, tmp_path / "out", stills=False).run()
    assert "aborted" in s and not s["passed"] and len(s["launches"]) == 2


def test_refuses_while_an_lod_tool_runs(tmp_path, journeys):
    f = Fake()
    f.lod = ["xLODGenx64"]
    s = rb.Batch(f, {"id": "t", "items": rb.parse_items(["good"]), "relaunch_mb": 6000, "relaunch_every": 0},
                 tmp_path / "out", stills=False).run()
    assert "xLODGenx64" in s["aborted"] and s["items"] == [] and f.launches == 0


def test_from_and_only_pick_items(tmp_path, journeys):
    batch = {"id": "t", "items": rb.parse_items(["bad", "good", "crash"]), "relaunch_mb": 6000, "relaunch_every": 0}
    s = rb.Batch(Fake(), batch, tmp_path / "o1", stills=False).run(start="good", only=True)
    assert [i["id"] for i in s["items"]] == ["good"]
    s = rb.Batch(Fake(), batch, tmp_path / "o2", stills=False).run(start="good")
    assert [i["id"] for i in s["items"]] == ["good", "crash"]
    with pytest.raises(SystemExit):
        rb.Batch(Fake(), batch, tmp_path / "o3", stills=False).run(start="nope")


def test_from_a_step_loads_its_step_save(tmp_path, journeys):
    """A failed step leaves the save of the step before it as the journey's latest: --from that step loads it."""
    import yaml
    ok = {"name": "a", "expect": [{"read": ["player"], "path": "dead", "eq": False}]}
    bad = {"name": "b", "expect": [{"read": ["player"], "path": "dead", "eq": True, "within": 0}]}
    (rb.JOURNEYS / "two.yaml").write_text(yaml.safe_dump({"id": "two", "runner": 1, "scene": "sc", "steps": [ok, bad]}))
    batch = {"id": "t", "items": rb.parse_items(["two"]), "relaunch_mb": 6000, "relaunch_every": 0}
    f = Fake()
    s = rb.Batch(f, batch, tmp_path / "o1", stills=False).run()
    assert not s["items"][0]["passed"] and "save argj-two-a" in f.lines
    loads, n = f.loads, len(f.lines)
    s = rb.Batch(f, batch, tmp_path / "o2", stills=False).run(start="two:b", only=True)
    assert s["items"][0]["failed_at"] == "b" and f.loads == loads + 1
    assert "bat sc" not in f.lines[n:]  # the step save, not the scene


def test_owed_status_and_write_owed(tmp_path, journeys):
    import yaml
    d = rb.JOURNEYS
    (d / "draft.yaml").write_text("id: draft\nstatus: draft\n")
    (d / "fixture.yaml").write_text(yaml.safe_dump({"id": "fixture", "runner": 1, "must_fail": True, "steps": []}))
    (d / "quit.yaml").write_text(yaml.safe_dump({"id": "quit", "runner": 1, "batch_last": True, "steps": [{"name": "q"}]}))
    (d / "re.yaml").write_text(yaml.safe_dump({"id": "re", "runner": 1, "steps": [{"name": "r", "do": [{"relaunch": True}]}]}))
    out = tmp_path / "hist"
    for stamp, items in {"20261029T1": [("good", False), ("bad", True)], "20261030T1": [("good", True), ("bad", False)]}.items():
        p = out / "batch" / "g" / stamp
        p.mkdir(parents=True)
        (p / "summary.json").write_text(json.dumps({"items": [{"kind": "journey", "id": i, "passed": ok} for i, ok in items]}))
    rows = {r["id"]: r for r in rb.owed(d, out)}
    assert "fixture" not in rows
    assert rows["draft"]["status"] == "draft" and rows["good"]["status"] == "passed"
    assert rows["bad"]["status"] == "failed" and rows["crash"]["status"] == "never"
    ids = rb.write_owed(tmp_path / "b.yaml", d, out)
    assert ids == ["bad", "crash", "quit", "re"]
    b = rb.load_batch([str(tmp_path / "b.yaml")])
    assert [i["id"] for i in b["items"]] == ids
