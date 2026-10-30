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


@pytest.fixture(autouse=True)
def _resume_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(rj, "RESUME", tmp_path / "resume")


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


def test_relaunch_without_the_scene_resumes_where_the_save_left(tmp_path):
    j = journey(tmp_path, [{"name": "relaunch", "do": [{"relaunch": {"save": "ArgoniaSuspend", "scene": False}}]}])
    j["scene"] = "plain-armed"

    class BatFake(RelaunchFake):
        def call(self, cmd, *args, **kw):
            if cmd == "console" and str(args[0]).startswith("bat "):
                self.log.append(("bat",))
            return super().call(cmd, *args, **kw)

    b = BatFake()
    b.resolve_refs = lambda text: text
    rep = rj.Runner(b, tmp_path / "out", stills=False, run_sh="true").run(j, "argoniabase")
    assert rep["passed"], rep
    assert b.log.count(("bat",)) == 1  # the journey's start only
    assert b.log[-2:] == [("launch",), ("load", "ArgoniaSuspend")]  # no bat after the relaunch's load


def test_the_ui_probe_validates():
    here = pathlib.Path(rj.__file__).resolve().parents[1] / "tests" / "journeys"
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


def test_a_kept_value_plus_a_number_bounds_a_change(tmp_path):
    r = rj.Runner(None, tmp_path / "out", stills=False)
    r.kept["hp"] = 100.0
    r.b = type("B", (), {"call": lambda self, *a, **k: {"current": 68.5}})()
    assert r.check({"read": ["av", "Health", "player"], "path": "current", "le": {"kept": "hp", "plus": -31}}, {}) is None
    assert r.check({"read": ["av", "Health", "player"], "path": "current", "ge": {"kept": "hp", "plus": -31}}, {}) is not None


class SaveFake(Fake):
    def __init__(self):
        super().__init__()
        self.deleted, self.loads = [], []

    def call(self, cmd, *args, **kw):
        if cmd == "load":
            self.loads.append(args[0])
        return super().call(cmd, *args)

    def delete_save(self, name):
        self.deleted.append(name)


STEP = lambda n: {"name": n, "expect": [{"console": "player.IsWeaponOut", "contains": ">> 1"}]}


def test_each_passed_step_saves_and_only_the_latest_is_kept(tmp_path):
    j = journey(tmp_path, [STEP("a"), {"name": "b", "owed": "x"}, STEP("c")])
    b = SaveFake()
    rep = rj.Runner(b, tmp_path / "out", stills=False).run(j, "base")
    assert rep["passed"]
    assert [l for l in b.lines if l.startswith("save ")] == ["save argj-t-a", "save argj-t-c"]
    assert b.deleted == ["argj-t-a"]
    state = json.loads((tmp_path / "resume" / "t.json").read_text())
    assert state["latest"] == "argj-t-c" and list(state["saves"]) == ["c"]


def test_from_loads_the_save_before_the_step_with_its_kept_values(tmp_path):
    keep = {"name": "a", "expect": [{"console": "player.IsWeaponOut", "keep": "w"}]}
    j = journey(tmp_path, [keep, STEP("b"), STEP("c")])
    b = SaveFake()
    rj.Runner(b, tmp_path / "out", stills=False).run(j, "base", start=None)
    (tmp_path / "resume" / "t.json").write_text(json.dumps(
        {"latest": "argj-t-a", "saves": {"a": {"save": "argj-t-a", "kept": {"w": "kept!"}}}}))
    b2 = SaveFake()
    r = rj.Runner(b2, tmp_path / "out2", stills=False)
    rep = r.run(j, "base", start="b", only=True)
    assert rep["passed"] and rep["resumed_from"] == "argj-t-a"
    assert b2.loads == ["argj-t-a"] and [s["name"] for s in rep["steps"]] == ["b"]
    assert r.kept == {"w": "kept!"}


def test_from_without_the_save_refuses(tmp_path):
    j = journey(tmp_path, [STEP("a"), STEP("b")])
    with pytest.raises(SystemExit, match="no step save after 'a'"):
        rj.Runner(SaveFake(), tmp_path / "out", stills=False).run(j, "base", start="b")


def test_step_saves_false_saves_nothing(tmp_path):
    j = journey(tmp_path, [STEP("a")], step_saves=False)
    b = SaveFake()
    assert rj.Runner(b, tmp_path / "out", stills=False).run(j, "base")["passed"]
    assert not [l for l in b.lines if l.startswith("save ")]


class LoadFake(Fake):
    """menu events by call count: `menus` is the list returned from the third poll on."""
    def __init__(self, menus):
        super().__init__()
        self.menus, self.polls = menus, 0

    def call(self, cmd, *args):
        if cmd == "events" and args:
            self.polls += 1
            return {"events": [{"seq": i, "data": d} for i, d in enumerate(self.menus if self.polls >= 3 else [])]}
        if cmd == "events":
            return {"last": 7}
        return super().call(cmd, *args)


def _clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(rj.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(rj.time, "sleep", lambda s: now.__setitem__(0, now[0] + s))
    return now


def test_wait_load_returns_after_loading_menu_closes(monkeypatch):
    now = _clock(monkeypatch)
    r = rj.Runner.__new__(rj.Runner)
    r.b = LoadFake([{"menu": "Loading Menu", "opening": True}, {"menu": "Loading Menu", "opening": False}])
    r.wait_load(7)
    assert r.b.polls == 3 and 1.5 <= now[0] < 2.5  # two empty polls, the close, then the 1 s fade


def test_wait_load_gives_up_when_no_load_opens(monkeypatch):
    now = _clock(monkeypatch)
    r = rj.Runner.__new__(rj.Runner)
    r.b = LoadFake([])
    r.wait_load(7)
    assert 3.0 <= now[0] < 3.5  # 2 s for a load to appear, then the 1 s fade


class Machine:
    def __init__(self):
        self.cmds = []

    def ps(self, script, timeout=120):
        self.cmds.append(script)
        return "line from " + ("crash" if "crash-" in script else script.split("\\")[-1].split('"')[0])


def test_failure_logs_fetched_only_on_failure(tmp_path):
    fake = Fake()
    fake.machine = Machine()
    got = rj.fetch_failure_logs(fake, tmp_path / "f")
    assert got == ["tail-ArgoniaCore.log", "tail-ArgoniaBridge.log", "tail-Papyrus.0.log"]
    assert all("-Tail 200" in c for c in fake.machine.cmds) and not any("crash-" in c for c in fake.machine.cmds)
    assert (tmp_path / "f" / "tail-Papyrus.0.log").read_text().startswith("line from")
    got = rj.fetch_failure_logs(fake, tmp_path / "c", crash=True)
    assert got[-2:] == ["tail-crash.log", "crash-head.log"] and (tmp_path / "c" / "tail-crash.log").read_text() == "line from crash"
    head = fake.machine.cmds[-1]
    assert "crash-" in head and "-TotalCount 120" in head  # the header and probable call stack, not only the module list


def test_run_report_lists_log_tails_on_failure_only(tmp_path):
    fake = Fake()
    fake.machine = Machine()
    bad = {"name": "bad", "expect": [{"moved": {"gt": 100}}]}
    rep = rj.Runner(fake, tmp_path / "bad").run(journey(tmp_path, [bad]), "base")
    assert not rep["passed"] and "tail-ArgoniaCore.log" in rep["logs"] and (tmp_path / "bad" / "tail-ArgoniaBridge.log").exists()
    fake.machine.cmds.clear()
    rep = rj.Runner(fake, tmp_path / "good").run(journey(tmp_path, [WALK]), "base")
    assert rep["passed"] and "logs" not in rep and not fake.machine.cmds


class TalkFake(Fake):
    """The crosshair shows `ref` from the `shows_after`-th read (None: never)."""
    def __init__(self, shows_after=None, heading=90.0):
        super().__init__()
        self.shows_after, self.heading, self.reads, self.keys = shows_after, heading, 0, []

    def call(self, cmd, *args):
        if cmd == "player":
            return {"pos": {"x": 0.0, "y": 0.0, "z": 0.0}, "heading_deg": self.heading}
        if cmd == "crosshair":
            self.reads += 1
            hit = self.shows_after is not None and self.reads >= self.shows_after
            return {"ref": {"id": "FE00180C", "editor_id": ""} if hit else {"id": "00000014", "editor_id": "Player"}}
        if cmd == "input":
            self.keys.append(args)
            return {"ms": 120}
        return super().call(cmd, *args)

    def resolve_refs(self, text):
        return text.replace("ARG_Ref_Livia", '"FE00180C"')


def test_talk_sets_the_npc_before_the_player_and_presses_e_once_the_crosshair_shows_it(monkeypatch):
    _clock(monkeypatch)
    b = TalkFake(shows_after=3, heading=90.0)
    rj.Runner(b, pathlib.Path("/nonexistent")).act({"talk": "ARG_Ref_Livia"})
    assert "ARG_Ref_Livia.moveto player 110 0 0" in b.lines and "ARG_Ref_Livia.setangle z 270" in b.lines
    assert b.reads == 3 and b.keys == [("key", "E", 120)]


def test_talk_fails_clearly_when_the_crosshair_never_shows_the_npc(monkeypatch, tmp_path):
    _clock(monkeypatch)
    b = TalkFake(shows_after=None)
    rep = rj.Runner(b, tmp_path / "o").run(journey(tmp_path, [{"name": "hi", "do": [{"talk": "ARG_Ref_Livia"}]}]), "base")
    assert not rep["passed"] and "crosshair never showed it" in rep["steps"][0]["reason"] and "Player" in rep["steps"][0]["reason"]
    assert b.keys == []


def test_a_save_load_waits_for_the_load_to_settle_before_the_scene(monkeypatch):
    now = _clock(monkeypatch)
    r = rj.Runner(LoadFake([{"menu": "Loading Menu", "opening": True}, {"menu": "Loading Menu", "opening": False}]),
                  pathlib.Path("/nonexistent"))
    r.apply_scene(None, "base")
    assert r.b.polls >= 3 and now[0] >= 1.5  # the close seen, then the settle


def test_wait_load_waits_out_a_fade_after_the_load(monkeypatch):
    now = _clock(monkeypatch)
    r = rj.Runner.__new__(rj.Runner)
    r.b = LoadFake([{"menu": "Loading Menu", "opening": True}, {"menu": "Loading Menu", "opening": False},
                    {"menu": "Fader Menu", "opening": True}])
    r.wait_load(7, cap=5)
    assert now[0] >= 5  # the fade never closed: held to the cap, never acting under it
