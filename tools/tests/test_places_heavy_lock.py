"""The heavy place-build lock: a second process waits while the first holds it, and the lock is re-entrant."""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = ("import sys,time\nfrom tools.places.heavy_lock import heavy_lock\n"
        "with heavy_lock():\n    print('got',flush=True)\n    time.sleep(float(sys.argv[1]))\n")


def _run(lock, secs):
    env = {**os.environ, "ARGONIA_PLACES_LOCK_FILE": str(lock)}
    env.pop("ARGONIA_PLACES_NO_LOCK", None)
    return subprocess.Popen([sys.executable, "-c", CODE, str(secs)], cwd=ROOT, env=env, stdout=subprocess.PIPE, text=True)


def test_second_process_waits(tmp_path):
    lock = tmp_path / "locks" / "x.lock"
    a = _run(lock, 1.5)
    assert a.stdout.readline().strip() == "got"
    t0 = time.time()
    b = _run(lock, 0)
    out = b.communicate(timeout=30)[0]
    assert time.time() - t0 >= 1.0
    assert "waiting for another place build: pid" in out and "got" in out
    a.communicate(timeout=30)


def test_reentrant(tmp_path, monkeypatch):
    monkeypatch.setenv("ARGONIA_PLACES_LOCK_FILE", str(tmp_path / "r.lock"))
    monkeypatch.delenv("ARGONIA_PLACES_NO_LOCK", raising=False)
    from tools.places.heavy_lock import heavy_lock
    with heavy_lock():
        with heavy_lock():
            pass
