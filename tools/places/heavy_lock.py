"""Machine-wide lock for the heavy place steps (the ArgoniaPlacesBuild dotnet process, 5 to 7 GB each).

One holder at a time across every worktree: the lock file lives in ~/.argonia/locks. Re-entrant within one
process. The kernel drops the flock when the descriptor closes, so a crash never leaves it held.
"""
from __future__ import annotations

import fcntl
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path

_depth = 0
_fd = None
_mutex = threading.RLock()


def lock_path() -> Path:
    return Path(os.environ.get("ARGONIA_PLACES_LOCK_FILE") or Path.home() / ".argonia" / "locks" / "places-heavy.lock")


@contextmanager
def heavy_lock():
    global _depth, _fd
    if os.environ.get("ARGONIA_PLACES_NO_LOCK") == "1":
        yield
        return
    with _mutex:
        if _depth == 0:
            p = lock_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(p, os.O_RDWR | os.O_CREAT, 0o644)
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    holder = os.pread(fd, 400, 0).decode(errors="replace").strip() or "unknown"
                    print(f"waiting for another place build: {holder}", flush=True)
                    fcntl.flock(fd, fcntl.LOCK_EX)
                os.ftruncate(fd, 0)
                os.pwrite(fd, f"pid {os.getpid()} cwd {os.getcwd()} since {time.strftime('%H:%M:%S')}".encode(), 0)
            except BaseException:
                os.close(fd)
                raise
            _fd = fd
        _depth += 1
        try:
            yield
        finally:
            _depth -= 1
            if _depth == 0:
                os.close(_fd)
                _fd = None
