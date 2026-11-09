"""Hold the build VM awake while a studio tab is open.

Each POST /api/heartbeat touches ~/.argonia/state/studio-heartbeat and, when the job is not already alive, starts
the job_guard job `studio-awake` running this file. While its pid is alive the machine's own idle-stop counts it
as a job and keep-busy.py keeps the CPU above the owner's alarm. The job ends HOLD seconds after the last
heartbeat, so with no tab open the machine falls idle and the alarm stops it about 30 minutes later. It also ends
after MAX_RUN seconds so keep-busy's age limit never ignores it; the next heartbeat starts a fresh one."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
JOB = "studio-awake"
HOLD = int(os.environ.get("STUDIO_HOLD_S", "300"))
MAX_RUN = int(os.environ.get("STUDIO_AWAKE_MAX_S", str(4 * 3600)))


def beat_file() -> Path:
    return Path(os.environ.get("STUDIO_STATE", Path.home() / ".argonia" / "state")) / "studio-heartbeat"


def jobs_dir() -> Path:
    return Path(os.environ.get("JOBS_DIR", Path.home() / ".argonia" / "jobs"))


def job_alive() -> bool:
    try:
        os.kill(int((jobs_dir() / f"{JOB}.pid").read_text().strip()), 0)
        return True
    except (OSError, ValueError):
        return False


def beat() -> dict:
    """Record a heartbeat and make sure the hold job runs. Returns the hold's state."""
    f = beat_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.touch()
    started = False
    if not job_alive():
        subprocess.run([str(ROOT / "tooling" / "job_guard.sh"), "run", JOB, "--", sys.executable, "-I",
                        str(Path(__file__).resolve())], cwd=ROOT, capture_output=True, timeout=60)
        started = True
    return {"held": job_alive(), "started": started, "release_after_s": HOLD}


def main() -> int:
    t0 = time.time()
    while True:
        try:
            age = time.time() - beat_file().stat().st_mtime
        except OSError:
            age = HOLD + 1
        if age > HOLD:
            print(f"last heartbeat {age:.0f} s ago: releasing the machine")
            return 0
        if time.time() - t0 > MAX_RUN:
            print("ran MAX_RUN: ending so the next heartbeat starts a fresh hold")
            return 0
        time.sleep(min(30, HOLD - age + 1))


if __name__ == "__main__":
    sys.exit(main())
