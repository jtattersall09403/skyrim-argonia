"""job_guard.sh's game-machine locks are per machine: one machine's job never blocks another's, and a second job
on the same machine queues behind it (or, with GPU_WAIT=0, gives up at once). Runs the real script with HOME in a
temp dir."""
import os
import subprocess
import time
from pathlib import Path

GUARD = Path(__file__).resolve().parents[1] / "job_guard.sh"


def clean_env(home):
    """The environment a test runs the script in: its own spool and none of the caller's job_guard settings (a gate run
    inside a job, or a resumed job, carries the real spool's JOBS_DIR, a lane, a seq, a wait)."""
    e = {k: v for k, v in os.environ.items()
         if k not in ("ARGONIA_PLAY", "ARGONIA_LANE", "JOB_SEQ", "GPU_WAIT", "SLOT_IDLE", "JOB_GUARD_NO_SYSTEMD", "JOB_RESUMED")}
    e.update(HOME=str(home), JOBS_DIR=str(Path(home) / ".argonia" / "jobs"))
    return e


def guard(home, *args, env=None):
    e = clean_env(home)
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


def test_job_survives_its_parent_shell_being_killed(tmp_path):
    """A run whose launching shell gets SIGTERM still finishes and writes its rc (the harness killed setsid jobs)."""
    import signal
    jobs = tmp_path / ".argonia" / "jobs"
    e = clean_env(tmp_path)
    parent = subprocess.Popen(
        ["bash", "-c", f'bash {GUARD} run slow -- bash -c "python3 -c \'import time; time.sleep(3)\'; echo done"; python3 -c "import time; time.sleep(60)"'],
        env=e, start_new_session=True)
    for _ in range(200):
        if (jobs / "slow.pid").exists():
            break
        time.sleep(0.05)
    os.killpg(parent.pid, signal.SIGTERM)
    parent.wait(timeout=30)
    assert guard(tmp_path, "wait", "slow").returncode == 0
    assert (jobs / "slow.rc").read_text().strip() == "0"
    assert "done" in (jobs / "slow.log").read_text()


def test_stop_ends_the_whole_job(tmp_path):
    jobs = tmp_path / ".argonia" / "jobs"
    guard(tmp_path, "run", "stopme", "--", "bash", "-c", "python3 -c 'import time; time.sleep(300)' & wait")
    for _ in range(100):
        if (jobs / "stopme.pid").exists():
            break
        time.sleep(0.05)
    assert "stopped" in guard(tmp_path, "stop", "stopme").stdout
    assert guard(tmp_path, "wait", "stopme").returncode == 1


def done(home, jobs):
    """wait, then drop the pid (a unit gone at once records pid 0, which `kill -0` reads as alive)."""
    assert guard(home, "wait", "j").returncode == 0
    (jobs / "j.pid").unlink()


def test_resumed_run_appends_to_its_log(tmp_path):
    """A boot resume (JOB_RESUMED) keeps the earlier run's lines and marks the resume; a fresh run starts anew."""
    jobs = tmp_path / ".argonia" / "jobs"
    for nosd in ("", "1"):  # the systemd unit's append: mode and the setsid >> fallback
        env = {"JOB_GUARD_NO_SYSTEMD": nosd} if nosd else {}
        assert guard(tmp_path, "run", "j", "--", "echo", "first", env=env).returncode == 0
        done(tmp_path, jobs)
        assert guard(tmp_path, "run", "j", "--", "echo", "second", env={**env, "JOB_RESUMED": "1"}).returncode == 0
        done(tmp_path, jobs)
        lines = (jobs / "j.log").read_text().splitlines()
        assert lines[0] == "first" and lines[1].startswith("== RESUMED ") and lines[2] == "second", lines
        assert guard(tmp_path, "run", "j", "--", "echo", "third", env=env).returncode == 0
        done(tmp_path, jobs)
        assert (jobs / "j.log").read_text().splitlines() == ["third"]


def test_gpu_job_keeps_machine_busy_while_it_runs_only(tmp_path):
    """A --gpu job holding the lock touches the machine's busy flag (run.sh ps) every GPU_KEEPALIVE_S while it runs, so the
    play machine's idle-stop does not stop it under a quiet log (2026-11-07 15:20); nothing touches it once the job ends."""
    fake = tmp_path / "run.sh"
    hits = tmp_path / "hits"
    fake.write_text(f'#!/bin/bash\necho "$@" >> {hits}\n')
    env = {"GPU_KEEPALIVE_RUN": str(fake), "GPU_KEEPALIVE_S": "1"}
    guard(tmp_path, "run", "--gpu", "ka", "--", "bash", "-c", "read -t 4 < /dev/zero; true", env=env)
    assert guard(tmp_path, "wait", "ka").returncode == 0
    n = len(hits.read_text().splitlines())
    assert n >= 2 and "--machine argonia-play ps" in hits.read_text()
    time.sleep(2.5)
    assert len(hits.read_text().splitlines()) == n  # none after the job ended
