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


def _ancestors() -> set[int]:
    pids, pid = set(), os.getpid()
    while pid > 1:
        pids.add(pid)
        try:
            with open(f"/proc/{pid}/stat") as fh:
                pid = int(fh.read().rsplit(")", 1)[1].split()[1])
        except OSError:
            break
    return pids


def held_by_ancestor() -> bool:
    """True when a process above us already holds the lock (a job wrapped in `flock province.lock` whose command
    then calls generate(): the same lock taken twice in one process tree deadlocked a plugin check for 26 min,
    2026-11-02). /proc/locks lists every flock with its holder's pid and the file's inode."""
    try:
        ino = os.stat(LOCK).st_ino
        with open("/proc/locks") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return False
    anc = _ancestors()
    for line in lines:
        f = line.split()
        if len(f) >= 6 and f[1] == "FLOCK" and f[5].split(":")[-1] == str(ino) and int(f[4]) in anc and int(f[4]) != os.getpid():
            return True
    return False


@contextlib.contextmanager
def province_lock(label: str, log=print):
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if held_by_ancestor():
        yield
        return
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
