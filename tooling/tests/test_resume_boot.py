"""The build machine's boot (infra/build-vm/resume.sh --dry): a start by the studio's address never resumes an agent;
the resume it was owed waits for the next start that is not the studio's. Runs against a temporary HOME with the
studio tag given by STUDIO_TAG, so it never asks AWS or GitHub."""
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

RESUME = Path(__file__).resolve().parents[2] / "infra" / "build-vm" / "resume.sh"


def boot_utc(minutes_before: float) -> str:
    up = subprocess.run(["uptime", "-s"], capture_output=True, text=True, check=True).stdout.strip()
    boot = dt.datetime.fromisoformat(up).astimezone(dt.timezone.utc)
    return (boot - dt.timedelta(minutes=minutes_before)).strftime("%Y-%m-%dT%H:%M:%SZ")


def dry(home: Path, tag: str, marker=False, owed=False) -> dict:
    state = home / ".argonia" / "state"
    state.mkdir(parents=True, exist_ok=True)
    for d in (".local/bin", ".claude/projects", ".argonia/jobs"):
        (home / d).mkdir(parents=True, exist_ok=True)
    gh = home / ".local" / "bin" / "gh"
    gh.write_text("#!/bin/sh\nexit 0\n")
    gh.chmod(0o755)
    for f, on in (("clean-stop", marker), ("resume-owed", owed)):
        p = state / f
        if on:
            p.write_text(json.dumps({"at": "2026-11-13T09:00:00Z", "reason": "test"}) + "\n")
        else:
            p.unlink(missing_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "JOBS_DIR"} | {"HOME": str(home), "STUDIO_TAG": tag}
    out = subprocess.run(["bash", str(RESUME), "--dry"], env=env, capture_output=True, text=True, timeout=120).stdout
    return dict(line.split(": ", 1) for line in out.splitlines() if line.startswith(("start: ", "mode: ")))


def test_a_studio_start_never_resumes(tmp_path):
    # no marker and no sign of an idle stop: work was live, so an agent start resumes it
    assert dry(tmp_path, "") == {"start": "agent", "mode": "resume"}
    # the same boot started by the studio's address: Claude waits at its prompt
    assert dry(tmp_path, boot_utc(0.5)) == {"start": "studio", "mode": "idle"}
    # a tag from an earlier start is not this boot's
    assert dry(tmp_path, boot_utc(120)) == {"start": "agent", "mode": "resume"}
    assert dry(tmp_path, "None") == {"start": "agent", "mode": "resume"}


def test_the_owed_resume_waits_for_an_agent_start(tmp_path):
    assert dry(tmp_path, boot_utc(1), marker=True, owed=True) == {"start": "studio", "mode": "idle"}
    assert dry(tmp_path, "", marker=True, owed=True) == {"start": "agent", "mode": "resume"}
    assert dry(tmp_path, "", marker=True) == {"start": "agent", "mode": "idle"}
