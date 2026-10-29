"""job_guard.sh's game-machine locks are per machine: one machine's job never blocks another's, and a second job
on the same machine is refused. Runs the real script with HOME in a temp dir."""
import os
import subprocess
import time
from pathlib import Path

GUARD = Path(__file__).resolve().parents[1] / "job_guard.sh"


def guard(home, *args, env=None):
    e = dict(os.environ, HOME=str(home))
    e.pop("ARGONIA_PLAY", None)
    e.update(env or {})
    return subprocess.run(["bash", str(GUARD), *args], env=e, capture_output=True, text=True, timeout=300)


def held(lock: Path) -> bool:
    return lock.exists() and subprocess.run(["flock", "-n", str(lock), "true"]).returncode != 0


def test_locks_are_per_machine(tmp_path):
    jobs = tmp_path / ".argonia" / "jobs"
    fifo = tmp_path / "release"
    os.mkfifo(fifo)
    assert guard(tmp_path, "run", "--gpu=argonia-play-2", "hold", "--", "bash", "-c", f"read l < {fifo}").returncode == 0
    lock2 = jobs / "gpu-argonia-play-2.lock"
    for _ in range(100):
        if held(lock2):
            break
        time.sleep(0.05)
    assert held(lock2)

    # Same machine: refused (the job dies without a result).
    guard(tmp_path, "run", "--gpu=argonia-play-2", "same", "--", "true")
    assert guard(tmp_path, "wait", "same").returncode == 1
    assert not (jobs / "same.rc").exists()

    # Other machines: run, each with ARGONIA_PLAY set to its machine; bare --gpu is argonia-play on gpu.lock.
    for name, flag, machine in (("p1", "--gpu", "argonia-play"), ("p3", "--gpu=argonia-play-3", "argonia-play-3")):
        guard(tmp_path, "run", flag, name, "--", "bash", "-c", 'echo "machine=$ARGONIA_PLAY"')
        assert guard(tmp_path, "wait", name).returncode == 0
        assert f"machine={machine}" in (jobs / f"{name}.log").read_text()
    assert (jobs / "gpu.lock").exists() and (jobs / "gpu-argonia-play-3.lock").exists()

    # Bare --gpu follows ARGONIA_PLAY, so it shares play-2's lock.
    guard(tmp_path, "run", "--gpu", "env2", "--", "true", env={"ARGONIA_PLAY": "argonia-play-2"})
    assert guard(tmp_path, "wait", "env2").returncode == 1

    with open(fifo, "w") as f:
        f.write("go\n")
    assert guard(tmp_path, "wait", "hold").returncode == 0


def test_unknown_machine_refused(tmp_path):
    r = guard(tmp_path, "run", "--gpu=somebox", "x", "--", "true")
    assert r.returncode == 2 and "no such game machine" in r.stderr
