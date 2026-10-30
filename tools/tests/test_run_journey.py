"""L2 for tools/run_journey.py (0.3 §d): a fake bridge; a passing journey, a failing step with its reason and still,
a crash, the three-identical-failures stop and a draft refused."""
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from tools import run_journey as rj  # noqa: E402
from tools.bridge import BridgeError, GameDown  # noqa: E402


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(rj.time, "sleep", lambda s: None)


class Fake:
    def __init__(self, crash_on=None):
        self.x, self.crash_on, self.lines = 0.0, crash_on, []

    def call(self, cmd, *args):
        if cmd == self.crash_on:
            raise GameDown("SkyrimSE is not running; crash log crash-1.log")
        if cmd == "player":
            return {"pos": {"x": self.x, "y": 0.0, "z": 0.0}}
        if cmd == "events":
            return {"last": 7, "events": [{"seq": 8, "data": {"tag": "TKDR_DodgeStart"}}]} if args else {"last": 7}
        if cmd == "console":
            self.lines.append(args[0])
            if args[0] == "IsPC1stPerson":
                return {"output": "IsPC1stPerson >> 0.00\n"}
            if args[0] == "sq":
                return {"output": "ARG_StartQuest 10\nWIGreeting 0\n"}
            if args[0] == "nosuch":
                raise BridgeError("console: Script command \"nosuch\" not found")
            return {"output": f"{args[0]} >> 1.00\n"}
        if cmd == "load":
            return {"loaded": args[0]}
        if cmd == "global":
            return {"value": 0}
        return {}

    def pad(self, seq):
        self.x += 200.0
        return {"ms": 100}

    def screenshot(self, out):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b"png")
        return out


def journey(tmp_path, steps, **kw):
    import yaml
    p = tmp_path / "j.yaml"
    p.write_text(yaml.safe_dump({"id": "t", "runner": 1, "steps": steps, **kw}))
    return rj.load_journey(p)


WALK = {"name": "walk", "do": [{"pad": "LY=1:500"}], "expect": [{"moved": {"gt": 100}}, {"event": {"kind": "anim", "match": "dodgestart"}}]}


def test_pass_keeps_a_still_per_step(tmp_path):
    j = journey(tmp_path, [WALK, {"name": "draw", "expect": [{"console": "player.IsWeaponOut", "contains": ">> 1"}]}])
    rep = rj.Runner(Fake(), tmp_path / "out").run(j, "base")
    assert rep["passed"] and [s["passed"] for s in rep["steps"]] == [True, True]
    assert (tmp_path / "out" / "01-walk.png").exists() and (tmp_path / "out" / "02-draw.png").exists()


def test_broken_step_fails_readably_with_its_still(tmp_path):
    bad = {"name": "stand", "expect": [{"moved": {"gt": 100}, "within": 0}]}
    rep = rj.Runner(Fake(), tmp_path / "out").run(journey(tmp_path, [bad, WALK]), "base")
    assert not rep["passed"] and rep["failed_at"] == "stand" and len(rep["steps"]) == 1
    f = json.loads((tmp_path / "out" / "failure.json").read_text())
    assert f["reason"] == "moved 0 units on the ground, wanted gt 100" and f["still"].endswith("01-stand.png")


def test_refused_action_is_the_reason(tmp_path):
    rep = rj.Runner(Fake(), tmp_path / "out").run(journey(tmp_path, [{"name": "c", "do": [{"console": "nosuch"}]}]), "b")
    assert "not found" in rep["steps"][0]["reason"]


def test_crash_is_a_failure(tmp_path):
    rep = rj.Runner(Fake(crash_on="player"), tmp_path / "out").run(journey(tmp_path, [WALK]), "base")
    assert not rep["passed"] and "crash-1.log" in rep["crash"]


def test_quests_running_against_the_allowed_list(tmp_path):
    exp = {"quests_running": {"allowed": "data/quarantine/allowed-quests.json"}, "within": 0}
    rep = rj.Runner(Fake(), tmp_path / "out").run(journey(tmp_path, [{"name": "q", "expect": [exp]}]), "b")
    assert rep["steps"][0]["reason"].startswith("1 quests running") and "WIGreeting" in rep["steps"][0]["reason"]


def test_three_identical_failures_stop(tmp_path, monkeypatch):
    runs = []
    bad = {"name": "stand", "expect": [{"moved": {"gt": 100}, "within": 0}]}
    p = tmp_path / "j.yaml"
    import yaml
    p.write_text(yaml.safe_dump({"id": "t", "runner": 1, "steps": [bad]}))
    monkeypatch.setattr(rj, "Bridge", Fake)
    monkeypatch.setattr(rj, "REPO", tmp_path)
    orig = rj.Runner.run
    monkeypatch.setattr(rj.Runner, "run", lambda self, j, s: runs.append(1) or orig(self, j, s))
    assert rj.main([str(p), "--runs", "5", "--no-stills"]) == 1
    assert len(runs) == 3


def test_draft_is_refused(tmp_path):
    p = tmp_path / "d.yaml"
    p.write_text("id: d\nstatus: draft\nsteps: []\n")
    with pytest.raises(SystemExit):
        rj.load_journey(p)
