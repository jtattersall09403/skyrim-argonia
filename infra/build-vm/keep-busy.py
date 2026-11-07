#!/usr/bin/env python3
"""Keep the build VM's CPU above the owner's idle-stop alarm (at or under 3% for 30 minutes) while a job_guard job is
alive, so a long wait (an AWS snapshot, a game-machine job) is never cut off. With no live job it uses no CPU and the
alarm stops the VM as the owner set it. A job alive more than MAX_HOURS no longer counts, so a hung job cannot keep
the VM up for ever. Run by argonia-keep-busy.service; the alarm itself is never touched (owner, 2026-11-07)."""
import os, time
from pathlib import Path

JOBS = Path(os.environ.get("JOBS_DIR", Path.home() / ".argonia/jobs"))
MAX_HOURS = float(os.environ.get("KEEP_BUSY_MAX_HOURS", "6"))
DUTY = 0.3  # busy share of one core: 30% of one of 4 vCPUs is about 7.5% of the machine


def live_job() -> bool:
    now = time.time()
    for pid_file in JOBS.glob("*.pid"):
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
        except (ValueError, OSError):
            continue
        if now - pid_file.stat().st_mtime < MAX_HOURS * 3600:
            return True
    return False


def main() -> None:
    while True:
        if not live_job():
            time.sleep(30)
            continue
        end = time.time() + 30
        while time.time() < end:
            t = time.time() + DUTY
            while time.time() < t:
                pass
            time.sleep(1 - DUTY)


if __name__ == "__main__":
    main()
