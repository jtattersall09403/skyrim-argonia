"""The awake hold ends HOLD seconds after the last heartbeat (tools/places/studio/awake.py)."""
import os
import time

from tools.places.studio import awake


def test_hold_releases_after_last_beat(tmp_path, monkeypatch):
    monkeypatch.setenv("STUDIO_STATE", str(tmp_path))
    f = awake.beat_file()
    f.touch()
    old = time.time() - awake.HOLD - 5
    os.utime(f, (old, old))
    t = time.time()
    assert awake.main() == 0 and time.time() - t < 2


def test_no_job_means_not_alive(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBS_DIR", str(tmp_path))
    assert awake.job_alive() is False
    (tmp_path / "studio-awake.pid").write_text("999999999")
    assert awake.job_alive() is False
    (tmp_path / "studio-awake.pid").write_text(str(os.getpid()))
    assert awake.job_alive() is True
