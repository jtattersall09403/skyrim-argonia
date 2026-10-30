"""job_guard.sh's game-machine locks are per machine: one machine's job never blocks another's, and a second job
on the same machine queues behind it (or, with GPU_WAIT=0, gives up at once). Runs the real script with HOME in a
temp dir."""
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
    for _ in range(300):  # up to 15 s: a loaded VM under make -j starts the job slowly
        if held(lock2):
            break
        time.sleep(0.05)
    assert held(lock2)

    # Same machine with GPU_WAIT=0: gives up at once, with a failed result.
    guard(tmp_path, "run", "--gpu=argonia-play-2", "same", "--", "true", env={"GPU_WAIT": "0"})
    assert guard(tmp_path, "wait", "same").returncode == 1
    # Same machine by default: queued behind the holder, and runs once it is released (checked at the end).
    guard(tmp_path, "run", "--gpu=argonia-play-2", "queued", "--", "true")
    for _ in range(100):
        if "queued (" in guard(tmp_path, "status", "queued").stdout:
            break
        time.sleep(0.05)
    assert "queued (" in guard(tmp_path, "status", "queued").stdout

    # Other machines: run, each with ARGONIA_PLAY set to its machine; bare --gpu is argonia-play on gpu.lock.
    for name, flag, machine in (("p1", "--gpu", "argonia-play"), ("p3", "--gpu=argonia-play-3", "argonia-play-3")):
        guard(tmp_path, "run", flag, name, "--", "bash", "-c", 'echo "machine=$ARGONIA_PLAY"')
        assert guard(tmp_path, "wait", name).returncode == 0
        assert f"machine={machine}" in (jobs / f"{name}.log").read_text()
    assert (jobs / "gpu.lock").exists() and (jobs / "gpu-argonia-play-3.lock").exists()

    # Bare --gpu follows ARGONIA_PLAY, so it shares play-2's lock.
    guard(tmp_path, "run", "--gpu", "env2", "--", "true", env={"ARGONIA_PLAY": "argonia-play-2", "GPU_WAIT": "0"})
    assert guard(tmp_path, "wait", "env2").returncode == 1

    with open(fifo, "w") as f:
        f.write("go\n")
    assert guard(tmp_path, "wait", "hold").returncode == 0
    assert guard(tmp_path, "wait", "queued").returncode == 0


def test_unknown_machine_refused(tmp_path):
    r = guard(tmp_path, "run", "--gpu=somebox", "x", "--", "true")
    assert r.returncode == 2 and "no such game machine" in r.stderr


def test_slot_reservation(tmp_path):
    jobs = tmp_path / ".argonia" / "jobs"
    lane_a, lane_b = {"ARGONIA_LANE": "a", "GPU_WAIT": "0"}, {"ARGONIA_LANE": "b", "GPU_WAIT": "0"}
    assert guard(tmp_path, "reserve", "--gpu", "a", "--minutes", "5").returncode == 0
    assert (jobs / "gpu.lock.slot").read_text().split()[0] == "a"
    assert "slot gpu: a until" in guard(tmp_path, "status").stdout
    assert guard(tmp_path, "reserve", "--gpu", "b").returncode == 1  # held by another lane
    assert guard(tmp_path, "reserve", "--gpu", "a").returncode == 0  # renewal

    # Own slot passes; another lane queues (gives up with GPU_WAIT=0); no lane ignores slots.
    guard(tmp_path, "run", "--gpu", "own", "--", "true", env=lane_a)
    assert guard(tmp_path, "wait", "own").returncode == 0
    guard(tmp_path, "run", "--gpu", "other", "--", "true", env=lane_b)
    assert guard(tmp_path, "wait", "other").returncode == 1
    assert "queued behind slot of a until" in (jobs / "other.log").read_text()

    # An expired slot is ignored.
    (jobs / "gpu.lock.slot").write_text(f"a {int(time.time()) - 10}\n")
    guard(tmp_path, "run", "--gpu", "late", "--", "true", env=lane_b)
    assert guard(tmp_path, "wait", "late").returncode == 0

    # Release frees it; only the owner may release.
    assert guard(tmp_path, "reserve", "--gpu", "a").returncode == 0
    assert guard(tmp_path, "release", "--gpu", "b").returncode == 1
    assert guard(tmp_path, "release", "--gpu", "a").returncode == 0
    assert not (jobs / "gpu.lock.slot").exists()
    guard(tmp_path, "run", "--gpu", "free", "--", "true", env=lane_b)
    assert guard(tmp_path, "wait", "free").returncode == 0


def test_idle_slot_yields(tmp_path):
    jobs = tmp_path / ".argonia" / "jobs"
    a, b = {"ARGONIA_LANE": "a", "GPU_WAIT": "0", "SLOT_IDLE": "100"}, {"ARGONIA_LANE": "b", "GPU_WAIT": "0", "SLOT_IDLE": "100"}
    assert guard(tmp_path, "reserve", "--gpu", "a", "--minutes", "5").returncode == 0
    guard(tmp_path, "run", "--gpu", "own", "--", "true", env=a)  # own lane runs straight through
    assert guard(tmp_path, "wait", "own").returncode == 0
    assert (jobs / "own.lane").read_text().strip() == "a"
    guard(tmp_path, "run", "--gpu", "early", "--", "true", env=b)  # a ended moments ago: still blocks
    assert guard(tmp_path, "wait", "early").returncode == 1
    old = time.time() - 200  # backdate a's activity past SLOT_IDLE
    for f in (jobs / "own.rc", jobs / "gpu.lock.slot"):
        os.utime(f, (old, old))
    assert "(idle 3m, yielding)" in guard(tmp_path, "status", env=a).stdout
    guard(tmp_path, "run", "--gpu", "late", "--", "true", env=b)
    assert guard(tmp_path, "wait", "late").returncode == 0


def test_busy_slot_holder_blocks(tmp_path):
    a, b = {"ARGONIA_LANE": "a", "SLOT_IDLE": "1", "GPU_WAIT": "0"}, {"ARGONIA_LANE": "b", "SLOT_IDLE": "1", "GPU_WAIT": "0"}
    assert guard(tmp_path, "reserve", "--gpu", "a", "--minutes", "5").returncode == 0
    guard(tmp_path, "run", "--gpu", "long", "--", "sleep", "6", env=a)
    time.sleep(3)  # a's job still running past SLOT_IDLE: the slot blocks
    assert "yielding" not in guard(tmp_path, "status", env=a).stdout
    guard(tmp_path, "run", "--gpu", "other", "--", "true", env=b)
    assert guard(tmp_path, "wait", "other").returncode == 1
    assert guard(tmp_path, "wait", "long").returncode == 0
