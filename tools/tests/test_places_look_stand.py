"""Where the look tool lets a camera stand, by a piece's mesh rather than its box (tools/places/look/capture.py: a
tree's trunk at the eye's height, a rock's column), the survey's time budget, and `look stop` ending a busy daemon
with its process group."""
import os
import subprocess
import sys
import time

import numpy as np

from tools.places import shape, xform
from tools.places.look import capture


def _mesh(name, *boxes):
    tris = np.concatenate([shape.box_tris(lo, hi) for lo, hi in boxes])
    shape.register(name, tris.reshape(-1, 3), np.arange(len(tris) * 3).reshape(-1, 3))


def _piece(pid, pos, lo, hi, kind, edid, model):
    return {"id": pid, "base": "B:" + pid, "kind": kind, "edid": edid, "model": model, "resolved": True,
            "m": xform.matrix(list(pos), [0, 0, 0], 1.0), "lo": list(lo), "hi": list(hi)}


def test_a_trunk_is_where_the_trees_wood_is_at_the_eyes_height(monkeypatch):
    monkeypatch.setattr(shape, "REAL", False)
    # a leaning tree: its trunk at its origin, its crown far off to one side, so its box's middle is open ground
    _mesh("m/leaning.nif", ([-40, -40, 0], [40, 40, 600]), ([300, -300, 600], [1500, 300, 1400]))
    tree = _piece("t", (0, 0, 0), (-40, -300, 0), (1500, 300, 1400), "tree", "Leaning", "m/leaning.nif")
    assert "trunk" in capture.camera_inside([0, 0, 160], [tree], 0.0)
    assert capture.camera_inside([600, 0, 160], [tree], 0.0) is None      # the box's middle: open ground under the crown
    assert "crown" in capture.camera_inside([600, 0, 1000], [tree], 0.0)


def test_a_hollow_trunk_is_solid_and_roots_under_the_eye_are_not():
    shape.register("m/hollow.nif", *_ring(300, 0, 500))
    _mesh("m/rooty.nif", ([-40, -40, 0], [40, 40, 900]), ([-800, -800, 0], [800, 800, 30]))
    capture._TRUNKS.clear()
    hollow = _piece("h", (0, 0, 0), (-300, -300, 0), (300, 300, 2000), "tree", "Hollow", "m/hollow.nif")
    rooty = _piece("r", (0, 0, 0), (-800, -800, 0), (800, 800, 2000), "tree", "Rooty", "m/rooty.nif")
    assert "trunk" in capture.camera_inside([0, 0, 160], [hollow], 0.0)    # inside the ring of bark
    assert capture.camera_inside([500, 0, 160], [rooty], 0.0) is None     # over its roots, beside its trunk


def _ring(r, z0, z1, n=24):
    V, T = [], []
    for k in range(n):
        a = 2 * np.pi * k / n
        V += [[r * np.cos(a), r * np.sin(a), z0], [r * np.cos(a), r * np.sin(a), z1]]
    for k in range(n):
        i, j = 2 * k, 2 * ((k + 1) % n)
        T += [[i, j, i + 1], [j, j + 1, i + 1]]
    return V, T


def test_a_mound_holds_a_camera_only_inside_its_stone():
    # a grassy mound: a low hump in the middle of a wide box, as a landscape piece's box reaches far round it
    _mesh("m/mound.nif", ([-150, -150, 0], [150, 150, 120]))
    mound = _piece("k", (0, 0, 0), (-900, -900, 0), (900, 900, 120), "rock", "Mound", "m/mound.nif")
    assert "inside" in capture.camera_inside([0, 0, 60], [mound], 0.0)
    assert capture.camera_inside([600, 0, 60], [mound], 0.0) is None      # in its box, over open ground


def test_a_box_stand_in_keeps_the_box_rules(monkeypatch):
    monkeypatch.setattr(shape, "REAL", False)
    rock = _piece("b", (0, 0, 0), (-900, -900, 0), (900, 900, 120), "rock", "Boulder", "m/unregistered-rock.nif")
    assert "inside" in capture.camera_inside([600, 0, 60], [rock], 0.0)


def test_look_stop_kills_a_busy_daemon_and_its_group(tmp_path, monkeypatch):
    import tools.places.look as look
    monkeypatch.setattr(look, "PIDF", tmp_path / "daemon.pid")
    monkeypatch.setattr(look, "SOCK", tmp_path / "daemon.sock")
    # a stand-in daemon in a session of its own, with a child (its browser), ignoring SIGTERM as a busy loop might not
    p = subprocess.Popen([sys.executable, "-c", "import signal, subprocess, sys, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                          "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)']); time.sleep(600)"],
                         start_new_session=True)
    time.sleep(0.5)
    (tmp_path / "daemon.pid").write_text(str(p.pid))
    (tmp_path / "daemon.sock").write_text("")
    look.kill_daemon(grace=0.5)
    assert p.wait(5) is not None
    assert not (tmp_path / "daemon.pid").exists() and not (tmp_path / "daemon.sock").exists()
    try:
        os.killpg(p.pid, 0)
        alive = True
    except OSError:
        alive = False
    assert not alive


def test_a_survey_sheet_spends_no_more_than_its_budget():
    from tools.places.look import survey

    class Page:
        calls = 0

        def evaluate(self, js, arg):
            Page.calls += 1
            time.sleep(0.3)
            raise AssertionError("no tile is drawn once the budget is spent")

    class D:
        page = Page()

        def open(self, place): pass
        def sync(self, strokes): pass
        def go(self, space): pass

    th = {"name": "huge", "lo": [0, 0, 0], "hi": [100, 100, 100], "pieces": []}
    sc = type("Sc", (), {"ground_under": lambda self, lo, hi: 0.0})()
    orig = survey._cam
    survey._cam = lambda *a, **k: {"w": survey.TW, "h": survey.TH}
    try:
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            got = survey.sheet(D(), "p", [], sc, th, set(), Path(d), budget=0.0)
    finally:
        survey._cam = orig
    assert Page.calls == 0 and got["failed"] == got["tiles"]
