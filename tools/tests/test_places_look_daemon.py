"""The look daemon leaves by itself: idle, its checkout gone, its browser or server dead; and daemons of deleted
checkouts are reaped (look stop, the tidy)."""
import os
import subprocess
import sys
import time
from pathlib import Path

from tools.places.look import daemon


class Browser:
    def __init__(self, up):
        self.up = up

    def is_connected(self):
        return self.up


class Server:
    def __init__(self, rc):
        self.rc = rc

    def poll(self):
        return self.rc


class D:
    def __init__(self, browser=True, server=None):
        self.browser, self.server = Browser(browser), Server(server)


ROOT = Path(__file__).resolve().parents[2]


def test_why_leave():
    now = time.time()
    assert daemon.why_leave(D(), now, now, ROOT) is None
    assert "idle" in daemon.why_leave(D(), now - daemon.IDLE - 1, now, ROOT)
    assert "gone" in daemon.why_leave(D(), now, now, Path("/nonexistent/tree"))
    assert "browser" in daemon.why_leave(D(browser=False), now, now, ROOT)
    assert "server" in daemon.why_leave(D(server=1), now, now, ROOT)


def test_reap_finds_a_daemon_whose_checkout_is_gone(tmp_path):
    """A process named like a look daemon, running in a folder then deleted, is found (and stopped)."""
    d = tmp_path / "gone"
    d.mkdir()
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "tools.places.look.daemon"], cwd=d,
                         start_new_session=True)
    try:
        d.rmdir()
        assert any(str(p.pid) in line for line in daemon.reap(dry=True))
        daemon.reap()
        assert p.wait(10) is not None
    finally:
        if p.poll() is None:
            os.killpg(p.pid, 9)


def test_every_answer_says_which_state_it_drew(monkeypatch):
    monkeypatch.setattr(daemon, "state", lambda place: {"files": "f", "commit": "c", "working_tree": False})

    class P:
        drew, place = {"files": "page"}, "a"
    assert daemon.drew_of(P(), "a") == {"files": "page"}
    assert daemon.drew_of(P(), "b") == {"files": "f", "commit": "c", "working_tree": False, "page": False}
    P.drew = None
    assert daemon.drew_of(P(), "a")["page"] is False
