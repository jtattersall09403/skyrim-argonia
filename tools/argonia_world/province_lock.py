"""One whole-province job at a time on the build VM (planner, 2026-11-02 22:02: two province generates at 2.6 GB
each beside two plugin builds left 3.6 GB free on a 15 GB machine with no swap; an OOM kill loses both).

    with province_lock("terrain generate"):
        ...

A sample build never needs it. The lock is ~/.argonia/jobs/province.lock; `flock` from the shell takes the same one.
"""
from __future__ import annotations

import contextlib
import fcntl
import os
import time
from pathlib import Path

LOCK = Path(os.environ.get("ARGONIA_PROVINCE_LOCK", Path.home() / ".argonia" / "jobs" / "province.lock"))


@contextlib.contextmanager
def province_lock(label: str, log=print):
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, "a+") as fh:
        t0 = time.time()
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            log(f"province lock held (another whole-province job): {label} waits")
            fcntl.flock(fh, fcntl.LOCK_EX)
            log(f"province lock taken after {time.time() - t0:.0f} s: {label}")
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
