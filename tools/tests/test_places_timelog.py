"""The place time log: the hook appends and never breaks a command, appends from many processes, the report's sums,
and the handover and the gate leave the file out."""
import json
import os
import subprocess
import sys
import threading
import time
import types

import pytest

from tools.places import handover, timelog
from tooling import gate


@pytest.fixture
def pdir(tmp_path, monkeypatch):
    d = tmp_path / "places"
    (d / "fen").mkdir(parents=True)
    monkeypatch.setenv("ARGONIA_PLACES_DIR", str(d))
    monkeypatch.setenv("JOBS_DIR", str(tmp_path / "nojobs"))
    monkeypatch.setenv("ARGONIA_TIMELOG_DEPTH", "0")
    monkeypatch.setenv("ARGONIA_TIMELOG_TREE", str(tmp_path / "lane"))
    return d


def open_pass(d):
    """What `pass start` leaves: the log exists with an open pass of this worktree."""
    assert timelog.main(["fen", "pass", "start", "an", "ask"]) == 0


def rows(d):
    return [json.loads(x) for x in (d / "fen/timelog.jsonl").read_text().splitlines()]


def test_main_appends_a_row_and_returns_the_verbs_code(pdir, monkeypatch):
    open_pass(pdir)
    from tools.places import __main__ as M
    mod = types.ModuleType("tools.places.zzfake")
    mod.main = lambda argv: (timelog.count("views", 3) or 7)
    monkeypatch.setitem(sys.modules, "tools.places.zzfake", mod)
    assert M.main(["zzfake", "fen", "x"]) == 7
    r = rows(pdir)[-1]
    assert (r["place"], r["verb"], r["rc"], r["depth"], r["counts"]) == ("fen", "zzfake", 7, 0, {"views": 3})
    assert r["secs"] >= 0 and r["end"] >= r["start"]


def test_look_verb_is_classified_and_queue_wait_recorded(pdir, monkeypatch):
    open_pass(pdir)
    jobs = pdir.parent / "jobs"
    jobs.mkdir()
    monkeypatch.setenv("JOBS_DIR", str(jobs))
    (jobs / "j1.cmd").write_bytes(b"python\0-m\0tools.places\0look\0fen\0sink\0")
    os.utime(jobs / "j1.cmd", (time.time() - 40, time.time() - 40))   # asked 40 s ago
    (jobs / "j1.started").write_text("")                              # got the lock now
    st = timelog.begin(["look", "fen", "sink", "post"])
    assert 39 < st["queue"] < 41 and st["job"] == "j1"
    timelog.record(["look", "fen", "sink", "post"], st, 0)
    r = rows(pdir)[-1]
    assert (r["sub"], r["kind"]) == ("sink", "editing") and r["queue"] == st["queue"]
    nested = timelog.begin(['look', 'fen', 'sink'])
    assert nested["queue"] == 0 and nested["depth"] == 1   # a nested verb is depth 1, no second wait


def test_a_read_only_or_missing_log_never_breaks_a_command(pdir, monkeypatch):
    open_pass(pdir)
    p = pdir / "fen/timelog.jsonl"
    p.write_text("")
    p.chmod(0o444)
    if os.geteuid() == 0:   # root ignores modes: make the append fail another way
        def boom(*a, **k):
            raise OSError("read-only")
        monkeypatch.setattr(os, "open", boom)
    timelog.record(["build", "fen"], timelog.begin(), 0)      # no raise
    timelog.record(["build", "nowhere"], timelog.begin(), 0)  # no place: nothing
    assert timelog.main(["fen", "phase", "plan"]) == 0        # says it could not, exits 0


def test_concurrent_appends_keep_every_row(pdir):
    n0 = 0
    def w(i):
        for j in range(50):
            timelog.append("fen", {"t": "phase", "at": i * 100 + j, "name": "x" * 500})
    ts = [threading.Thread(target=w, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(rows(pdir)) == 400 + n0
    code = ("from tools.places import timelog as t\n"
            "for j in range(30): t.append('fen', {'t': 'phase', 'at': j, 'name': 'y' * 300})")
    procs = [subprocess.Popen([sys.executable, "-c", code], env=os.environ.copy()) for _ in range(4)]
    [p.wait() for p in procs]
    assert len(rows(pdir)) == 520 + n0


def cmd(start, secs, verb, kind, queue=0.0, args="", depth=0, sub=""):
    return {"t": "cmd", "verb": verb, "sub": sub, "kind": kind, "start": start, "end": start + secs, "secs": secs, "rc": 0,
            "queue": queue, "depth": depth, "args": args, "counts": {}}


def test_report_sums_on_a_fixture_stream():
    rows_ = [
        {"t": "pass", "at": 0, "edge": "start", "what": "first draft"},
        {"t": "phase", "at": 0, "name": "site"},
        cmd(10, 20, "look", "looking", sub="at"),                     # gap 0-10 is before the first command
        cmd(130, 5, "look", "editing", sub="sink"),                   # gap 30-130 = 100 s thinking
        {"t": "phase", "at": 200, "name": "tool fix: look.hands"},
        cmd(210, 100, "build", "building", queue=50),                 # asked at 160: a 25 s short gap, queue 50 s
        cmd(215, 99, "check", "checking", depth=1),                   # nested: not counted
        cmd(320, 60, "playwalk", "walking"),                          # full walk; a 10 s short gap before it
        cmd(380, 10, "look", "walking", sub="playwalk", args="--changed"),
        {"t": "pass", "at": 400, "edge": "end", "what": "first draft"},
        {"t": "phase", "at": 400, "name": "waiting on lead"},
        cmd(1000, 5, "check", "checking"),                            # a gap while waiting: away
    ]
    r = timelog.report(rows_)
    assert r["wall"] == 1005 and r["commands"] == 6 and r["builds"] == 1 and r["full_walks"] == 1
    assert r["phases"] == {"site": 200, "tool fix: look.hands": 200, "waiting on lead": 605}
    assert r["tool_fix"] == 200 and r["passes"] == [("first draft", 400)]
    a = r["activity"]
    assert a["looking"] == 20 and a["editing"] == 5 and a["building"] == 100 and a["walking"] == 70
    assert a["waiting in a queue"] == 50 and a["thinking/reading (gaps over 60s)"] == 100
    assert a["away: between passes or waiting on lead"] == 610
    assert r["longest"][0]["verb"] == "build"
    text = timelog.render("fen", r)
    assert "1 builds" in text and "tool fix: look.hands" in text
    assert "| by phase | time | share |" in timelog.render("fen", r, md=True)


def test_handover_wants_phase_markers_once_commands_are_logged(pdir):
    d = pdir / "fen"
    assert handover.timelog_marked(d)[0]
    timelog.append("fen", cmd(1, 2, "build", "building") | {"place": "fen"})
    assert not handover.timelog_marked(d)[0]
    timelog.append("fen", {"t": "phase", "at": 3, "name": "check"})
    assert handover.timelog_marked(d)[0]


def test_report_and_markers_through_main(pdir, capsys):
    assert timelog.main(["fen", "pass", "start", "first", "draft"]) == 0
    assert timelog.main(["fen", "phase", "site", "--note", "n"]) == 0
    assert timelog.main(["fen", "pass", "end", "first", "draft"]) == 0
    assert timelog.main(["fen", "pass", "middle"]) == 2
    assert timelog.main(["fen", "report", "--md"]) == 0
    assert "first draft" in capsys.readouterr().out


def test_handover_and_the_gate_leave_the_log_out(tmp_path):
    root = tmp_path / "repo"
    d = root / "newworld/places/fen"
    d.mkdir(parents=True)
    (d / "place.json").write_text("{}\n")
    for a in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"]):
        subprocess.run(["git", "-C", str(root), *a], check=True)
    t0 = handover.changed_at(root, d)
    (d / "timelog.jsonl").write_text("{}\n")
    os.utime(d / "timelog.jsonl", (t0 + 9000, t0 + 9000))
    assert handover.changed_at(root, d) == t0
    plan = gate.pick(["newworld/places/fen/timelog.jsonl"])
    assert plan.inert == ["newworld/places/fen/timelog.jsonl"] and not plan.stages and not plan.tests


def test_nothing_is_written_outside_an_open_pass_or_from_another_tree(pdir, monkeypatch):
    log = pdir / "fen/timelog.jsonl"
    timelog.record(["build", "fen"], timelog.begin(["build", "fen"]), 0)     # no log, no pass: nothing, no file
    assert not log.exists()
    assert timelog.main(["fen", "phase", "site"]) == 0 and not log.exists()  # a phase needs a pass too
    assert timelog.main(["fen", "pass", "end"]) == 0 and not log.exists()
    open_pass(pdir)
    timelog.main(["fen", "phase", "site"])
    st = {**timelog.begin(["build", "fen"]), "depth": 0}
    timelog.record(["studio", "fen"], st, 0)                                  # the studio is never logged
    timelog.record(["build", "fen"], st, 0)
    r = rows(pdir)
    start = r[0]
    assert start["edge"] == "start" and start["tree"] and "branch" in start and start["id"]
    assert [x["t"] for x in r] == ["pass", "phase", "cmd"] and r[2]["pass"] == start["id"] == r[1]["pass"]
    monkeypatch.setenv("ARGONIA_TIMELOG_TREE", "/elsewhere")                  # another worktree or the main tree
    timelog.record(["check", "fen"], st, 0)
    assert timelog.main(["fen", "phase", "x"]) == 0 and timelog.main(["fen", "pass", "end"]) == 0
    assert len(rows(pdir)) == 3
    monkeypatch.undo()
    monkeypatch.setenv("ARGONIA_PLACES_DIR", str(pdir))
    monkeypatch.setenv("ARGONIA_TIMELOG_TREE", str(pdir.parent / "lane"))
    assert timelog.main(["fen", "pass", "end"]) == 0                          # closed: nothing more is written after it
    timelog.record(["build", "fen"], st, 0)
    assert [x.get("edge") for x in rows(pdir) if x["t"] == "pass"] == ["start", "end"] and len(rows(pdir)) == 4


def test_handover_warns_of_an_open_pass_but_does_not_fail(pdir):
    d = pdir / "fen"
    open_pass(pdir)
    timelog.main(["fen", "phase", "check"])
    ok, line = handover.timelog_marked(d)
    assert ok and "still open" in line and "pass end" in line
