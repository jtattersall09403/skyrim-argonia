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
            if args[0] == "nosuch":
                raise BridgeError("console: Script command \"nosuch\" not found")
            return {"output": f"{args[0]} >> 1.00\n"}
        if cmd == "load":
            return {"loaded": args[0]}
        if cmd == "quests":
            return {"total": 3, "running": [{"id": "10000805", "editor_id": "ARG_StartQuest", "plugin": "Argonia.esm"},
                                            {"id": "10000900", "editor_id": "ARG_Q_LF83", "plugin": "Argonia.esm"},
                                            {"id": "0001A2B3", "editor_id": "WIGreeting", "plugin": "Skyrim.esm"}]}
        if cmd == "music":
            return {"current": {"id": "0001B0D2", "editor_id": "MUSExploreTundra", "name": ""}, "queue": []}
        if cmd == "global":
            return {"value": 0}
        return {}

    def resolve_refs(self, text):
        return text

    def running_quests(self):
        return self.call("quests")["running"]

    def music(self):
        return self.call("music")

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


def test_an_owed_step_is_listed_not_run_and_the_journey_goes_on(tmp_path):
    camp = {"name": "camp", "owed": "the rest fragment's Papyrus (#15)", "do": [{"console": "nosuch"}],
            "expect": [{"moved": {"gt": 100}, "within": 0}]}
    fake = Fake()
    rep = rj.Runner(fake, tmp_path / "out").run(journey(tmp_path, [camp, WALK]), "base")
    assert rep["passed"] and [s["name"] for s in rep["steps"]] == ["walk"] and "nosuch" not in fake.lines
    assert rep["owed"] == [{"n": 1, "name": "camp", "why": "the rest fragment's Papyrus (#15)"}]
    with pytest.raises(SystemExit, match="owed"):
        journey(tmp_path, [{"name": "camp", "owed": ""}])


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


def test_music_against_the_allowed_types(tmp_path):
    exp = {"music": {"allowed": ["ARG_MusicSilence"]}, "within": 0}
    rep = rj.Runner(Fake(), tmp_path / "out").run(journey(tmp_path, [{"name": "m", "expect": [exp]}]), "b")
    assert "MUSExploreTundra plays" in rep["steps"][0]["reason"]


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


class CoreFake(Fake):
    """Fake with ArgoniaCore reads: a vastei that grows on each pad, a pile string, and soak measures."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.vastei, self.teleports, self.queue, self.cosave = 0, [], iter([3, 4, 3]), iter([2000, 2210, 2210, 2210])

    def call(self, cmd, *args):
        if cmd == "core":
            if args[0] == "GetVastei":
                return {"native": "GetVastei", "value": self.vastei}
            if args[0] == "PileState":
                return {"native": "PileState", "value": "10.50 -20.25 3.00 0000003C 120"}
        if cmd == "teleport":
            self.teleports.append(args)
            return {}
        if cmd == "frametime":
            return {"p50_ms": 15.0, "p99_ms": 20.0}
        return super().call(cmd, *args)

    def pad(self, seq):
        self.vastei += 5
        return super().pad(seq)

    def papyrus_queue(self):
        return {"stacks": next(self.queue, 3)}

    def save_bytes(self, name):
        return {"ess": 1, "skse": next(self.cosave, 2210)}


def test_kept_values_compare_later_and_fill_an_action(tmp_path):
    j = journey(tmp_path, [
        {"name": "before", "expect": [{"read": ["core", "GetVastei"], "path": "value", "keep": "v0"}]},
        {"name": "earn", "do": [{"pad": "RB:120"}], "expect": [{"read": ["core", "GetVastei"], "path": "value",
                                                                 "gt": {"kept": "v0"}}]},
        {"name": "pile", "expect": [{"read": ["core", "PileState"], "path": "value", "ne": "", "keep": "pile"}]},
        {"name": "go", "do": [{"teleport": "pos {pile.0} {pile.1} {pile.2}"}]}])
    b = CoreFake()
    rep = rj.Runner(b, tmp_path / "out", stills=False).run(j, "argoniabase")
    assert rep["passed"], rep
    assert b.teleports == [("pos", "10.50", "-20.25", "3.00")]


def test_a_kept_comparison_fails_with_its_reason(tmp_path):
    j = journey(tmp_path, [
        {"name": "before", "expect": [{"read": ["core", "GetVastei"], "path": "value", "keep": "v0"}]},
        {"name": "no-input", "expect": [{"read": ["core", "GetVastei"], "path": "value", "gt": {"kept": "v0"}}]}])
    rep = rj.Runner(CoreFake(), tmp_path / "out", stills=False).run(j, "argoniabase")
    assert rep["failed_at"] == "no-input" and "wanted gt 0" in rep["steps"][1]["reason"]


def test_dry_validates_scene_and_kept_order(tmp_path, monkeypatch):
    import yaml
    monkeypatch.setattr(rj, "SCENES", tmp_path)
    (tmp_path / "s.txt").write_text("set gamehour to 10\r\n")
    good = tmp_path / "good.yaml"
    good.write_text(yaml.safe_dump({"id": "good", "runner": 1, "scene": "s", "steps": [
        {"name": "a", "expect": [{"read": ["core", "PileState"], "path": "value", "keep": "pile"}]},
        {"name": "b", "do": [{"teleport": "pos {pile.0} {pile.1} {pile.2}"}]}]}))
    assert "2 steps" in rj.dry(good)
    early = tmp_path / "early.yaml"
    early.write_text(yaml.safe_dump({"id": "early", "runner": 1, "scene": "s", "steps": [
        {"name": "b", "do": [{"teleport": "pos {pile.0} 0 0"}]}]}))
    with pytest.raises(SystemExit, match="before it is kept"):
        rj.dry(early)
    noscene = tmp_path / "noscene.yaml"
    noscene.write_text(yaml.safe_dump({"id": "n", "runner": 1, "scene": "missing", "steps": [{"name": "a"}]}))
    with pytest.raises(SystemExit, match="no scene"):
        rj.dry(noscene)
    soak = tmp_path / "soak.yaml"
    soak.write_text(yaml.safe_dump({"id": "soak", "runner": 1, "soak": {"journey": "good", "minutes": 1}}))
    assert "soak of good" in rj.dry(soak)
    soak.write_text(yaml.safe_dump({"id": "soak", "runner": 1, "soak": {"journey": "good", "bars": {"fps": 1}}}))
    with pytest.raises(SystemExit, match="unknown soak bars"):
        rj.dry(soak)


def test_the_real_first_place_and_soak_validate():
    here = pathlib.Path(rj.__file__).resolve().parents[1] / "tests" / "journeys"
    assert "ok" in rj.dry(here / "first-place.yaml")
    assert "soak of first-place" in rj.dry(here / "soak.yaml")


def test_soak_loops_measures_and_judges(tmp_path):
    import yaml
    (tmp_path / "inner.yaml").write_text(yaml.safe_dump({"id": "inner", "runner": 1, "steps": [{"name": "a"}]}))
    j = {"id": "soak", "runner": 1, "soak": {"journey": "inner", "minutes": 1, "frames": 10}}
    ticks = iter([0, 10, 20, 30, 100])  # three loops inside the minute, then the clock runs out
    v = rj.soak(CoreFake(), j, tmp_path, tmp_path / "out", "argoniabase", clock=lambda: next(ticks))
    assert v["passed"], v["reasons"]
    assert [x["papyrus"]["stacks"] for x in v["loops"]] == [3, 4, 3]
    assert (tmp_path / "out" / "soak.json").is_file()


def test_judge_soak_names_every_reason():
    bars = rj.SOAK_BARS
    loops = [{"n": 1, "passed": True, "papyrus": {"stacks": 3}, "save_bytes": {"skse": 2000}, "frames": {"p50_ms": 15}},
             {"n": 2, "passed": True, "papyrus": {"stacks": 30}, "save_bytes": {"skse": 2200}, "frames": {"p50_ms": 15}},
             {"n": 3, "passed": False, "failed_at": "die", "papyrus": {"stacks": 31}, "save_bytes": {"skse": 4000},
              "frames": {"p50_ms": 25, "p99_ms": 40}},
             {"n": 4, "passed": False, "failed_at": "game down", "crash": "crash-1.log"}]
    why = " | ".join(rj.judge_soak(loops, bars))
    for part in ("game went down", "failed at die", "queue grew 3 -> 31", "co-save after the first loop", "p50 25"):
        assert part in why, why


class RelaunchFake(Fake):
    """Fake with the machine's side: a game that goes down on qqq (or hangs), health, and launch."""
    def __init__(self, hang=False, drop_reply=False):
        super().__init__()
        self.alive, self.hang, self.drop_reply, self.log = True, hang, drop_reply, []

    def call(self, cmd, *args, **kw):
        if cmd in ("load", "console") and (cmd == "load" or args[0] == "qqq"):
            self.log.append((cmd, args[0]))
        if cmd == "console" and args[0] == "qqq":
            self.alive = self.hang
            if self.drop_reply:
                raise GameDown("the bridge closed the connection without a reply (is the game running?)")
        return super().call(cmd, *args)

    def health(self):
        self.log.append(("health", self.alive))
        return {"alive": self.alive}

    def launch(self):
        self.log.append(("launch",))
        self.alive = True
        return {"ping": {"pong": True}}


def test_relaunch_quits_launches_and_loads_the_journeys_save(tmp_path):
    j = journey(tmp_path, [{"name": "pan", "do": [{"console": "x"}]}, {"name": "relaunch", "do": [{"relaunch": True}]},
                           {"name": "remembered", "do": [{"console": "y"}]}])
    b = RelaunchFake(drop_reply=True)  # the game went down before it answered: the quit, not a failure
    rep = rj.Runner(b, tmp_path / "out", stills=False).run(j, "argoniabase")
    assert rep["passed"], rep
    assert b.log == [("load", "argoniabase"), ("console", "qqq"), ("health", False), ("launch",), ("load", "argoniabase")]
    assert rep["calls"][-1] == {"call": ["relaunch", "argoniabase"],
                                "result": {"quit_clean": True, "save": "argoniabase", "ping": {"pong": True}}}


def test_relaunch_to_a_named_save_after_a_hung_quit(tmp_path, monkeypatch):
    monkeypatch.setattr(rj, "QUIT_WAIT_S", 3)
    j = journey(tmp_path, [{"name": "relaunch", "do": [{"relaunch": "studio-a"}]}])
    b = RelaunchFake(hang=True)
    rep = rj.Runner(b, tmp_path / "out", stills=False).run(j, "argoniabase")
    assert rep["passed"], rep
    assert b.log[-3:] == [("health", True), ("launch",), ("load", "studio-a")]  # launch kills what the quit left
    assert rep["calls"][-1]["result"]["quit_clean"] is False


def test_the_ui_probe_validates_with_its_relaunch():
    here = pathlib.Path(rj.__file__).resolve().parents[1] / "tests" / "journeys"
    j = rj.load_journey(here / "ui-probe.yaml")
    steps = {s["name"]: s for s in j["steps"]}
    assert steps["relaunch"]["do"] == [{"relaunch": True}] and "owed" not in steps["relaunch"]
    assert "owed" not in steps["remembered"]
    assert "ok" in rj.dry(here / "ui-probe.yaml")


def test_event_absent_and_log_since_the_step(tmp_path):
    class LogFake(Fake):
        def __init__(self):
            super().__init__()
            self.log = ["old line"]
            self.machine = self

        def ps(self, script, timeout=120):
            return "\n".join(self.log)

        def call(self, cmd, *args):
            if cmd == "console" and args[0] == "quit-now":
                self.log.append("saves: ArgoniaSuspend written (quit)")
            return super().call(cmd, *args)
    j = journey(tmp_path, [
        {"name": "stays", "expect": [{"event": {"kind": "menu", "match": "nomenu", "absent": True}}]},
        {"name": "quit", "do": [{"console": "quit-now"}],
         "expect": [{"log": {"name": "ArgoniaCore", "contains": "ArgoniaSuspend written (quit)"}}]},
        {"name": "again", "expect": [{"log": {"name": "ArgoniaCore", "contains": "ArgoniaSuspend written"}, "within": 0}]},
        {"name": "closed", "expect": [{"event": {"kind": "anim", "match": "dodgestart", "absent": True}}]}])
    rep = rj.Runner(LogFake(), tmp_path / "out", stills=False).run(j, "base")
    assert [s["passed"] for s in rep["steps"]] == [True, True, False]  # an old line is not new; the run stops there
    assert "no line with" in rep["steps"][2]["reason"]
