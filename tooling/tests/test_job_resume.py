"""1.15: job_guard's spool survives an interrupt and job_resume.sh relaunches the queue in order. Runs the real
scripts against a temp spool (JOBS_DIR), never ~/.argonia/jobs; the interrupt is simulated by stopping every job's
unit (what a reboot does to them) before a result is written."""
import os
import subprocess
import time
from pathlib import Path

TOOLING = Path(__file__).resolve().parents[1]
GUARD, RESUME = TOOLING / "job_guard.sh", TOOLING / "job_resume.sh"


def env_for(tmp, extra=None):
    e = {k: v for k, v in os.environ.items()
         if k not in ("ARGONIA_PLAY", "ARGONIA_LANE", "JOB_SEQ", "GPU_WAIT", "SLOT_IDLE", "JOB_GUARD_NO_SYSTEMD")}
    e.update(HOME=str(tmp), JOBS_DIR=str(tmp / "jobs"))
    e.update(extra or {})
    return e


def guard(tmp, *args, extra=None, cwd=None):
    return subprocess.run(["bash", str(GUARD), *args], env=env_for(tmp, extra), cwd=cwd,
                          capture_output=True, text=True, timeout=300)


def until(pred, n=300):
    for _ in range(n):
        if pred():
            return True
        time.sleep(0.05)
    return pred()


def interrupt(jobs: Path):
    """What a reboot does: every job's unit (or process group) dies before its result is written."""
    units = [u.read_text().strip() for u in jobs.glob("*.unit")]
    for sig in ("SIGSTOP", "SIGKILL"):  # freeze all first, so no job runs into a lock another's death frees
        subprocess.run(["systemctl", "--user", "kill", f"--signal={sig}", *units], capture_output=True)


def test_spool_write(tmp_path):
    jobs = tmp_path / "jobs"
    guard(tmp_path, "run", "a", "--", "printf", "%s|", "one two", "x", extra={"ARGONIA_LANE": "L"}, cwd=tmp_path)
    guard(tmp_path, "run", "--gpu=argonia-play-9", "b", "--", "true")
    assert guard(tmp_path, "wait", "a").returncode == 0 and guard(tmp_path, "wait", "b").returncode == 0
    assert (jobs / "a.cmd").read_bytes() == b"printf\0%s|\0one two\0x\0"
    assert (jobs / "a.cwd").read_text().strip() == str(tmp_path)
    envs = (jobs / "a.env").read_bytes().split(b"\0")
    assert b"ARGONIA_LANE=L" in envs and any(v.startswith(b"PATH=") for v in envs)
    assert int((jobs / "b.seq").read_text()) == int((jobs / "a.seq").read_text()) + 1
    assert (jobs / "b.gpu").read_text().strip() == "argonia-play-9" and not (jobs / "a.gpu").exists()
    assert (jobs / "a.state").read_text().strip() == "done" and (jobs / "b.state").read_text().strip() == "done"


def test_restore_order_and_finished_not_rerun(tmp_path):
    jobs, order = tmp_path / "jobs", tmp_path / "order"
    hold, nhold = tmp_path / "hold", tmp_path / "nhold"
    os.mkfifo(hold)
    os.mkfifo(nhold)
    m = "--gpu=argonia-play-9"
    guard(tmp_path, "run", "done1", "--", "bash", "-c", f"echo done1 >> {order}")
    assert guard(tmp_path, "wait", "done1").returncode == 0
    guard(tmp_path, "run", m, "run1", "--", "bash", "-c", f"echo run1 >> {order}; read l < {hold}")
    assert until(lambda: order.exists() and "run1" in order.read_text())
    guard(tmp_path, "run", m, "q2", "--", "bash", "-c", f"echo q2 >> {order}")
    guard(tmp_path, "run", m, "q3", "--", "bash", "-c", f'echo "q3 $ARGONIA_LANE $PWD" >> {order}',
          extra={"ARGONIA_LANE": "lane-x"}, cwd=tmp_path)
    guard(tmp_path, "run", "n4", "--", "bash", "-c", f"echo n4 >> {order}; read l < {nhold}")
    assert until(lambda: "n4" in order.read_text())
    assert until(lambda: "queued (" in guard(tmp_path, "status", "q3").stdout)

    interrupt(jobs)
    assert until(lambda: all(guard(tmp_path, "status", n).stdout.strip().endswith("dead")
                             for n in ("run1", "q2", "q3", "n4")))
    assert [(jobs / f"{n}.state").read_text().strip() for n in ("run1", "q2", "q3", "n4")] == \
        ["running", "queued", "queued", "running"]
    order.write_text("")
    # a job whose wrapper wrote a signal rc as the reboot's SIGTERM landed is still the interrupt's: relaunched
    (jobs / "n4.rc").write_text("143\n")

    r = subprocess.run(["bash", str(RESUME)], env=env_for(tmp_path, {"RESUME_BOOT_ID": "test-boot"}),
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    mark = (jobs / "RESUMED-test-boot").read_text()
    relaunched = [ln.split()[1] for ln in mark.splitlines() if ln.startswith("relaunched")]
    assert relaunched == ["run1", "q2", "q3", "n4"], mark
    # a second run in the same boot does nothing
    assert "already resumed" in subprocess.run(["bash", str(RESUME)], env=env_for(tmp_path, {"RESUME_BOOT_ID": "test-boot"}),
                                               capture_output=True, text=True).stdout

    assert until(lambda: "run1" in order.read_text() and "n4" in order.read_text())
    with open(hold, "w") as f:
        f.write("go\n")
    with open(nhold, "w") as f:
        f.write("go\n")
    for n in ("run1", "q2", "q3", "n4"):
        assert guard(tmp_path, "wait", n).returncode == 0, n
    lines = order.read_text().splitlines()
    gpu_lines = [ln.split()[0] for ln in lines if ln.split()[0] in ("run1", "q2", "q3")]
    assert gpu_lines == ["run1", "q2", "q3"]
    assert f"q3 lane-x {tmp_path}" in lines
    assert "done1" not in lines  # finished before the interrupt: not rerun


def test_old_boot_pid_is_not_running(tmp_path):
    """A pid file from another boot (pid reused by an unrelated live process) does not block a run; one from this boot does."""
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    (jobs / "j.pid").write_text(f"{os.getpid()}\n")  # a live pid, as a reused one would be
    (jobs / "j.boot").write_text("some-other-boot-id\n")
    assert guard(tmp_path, "run", "j", "--", "true").returncode == 0
    assert guard(tmp_path, "wait", "j").returncode == 0
    assert (jobs / "j.boot").read_text() == Path("/proc/sys/kernel/random/boot_id").read_text()
    (jobs / "k.pid").write_text(f"{os.getpid()}\n")
    (jobs / "k.boot").write_text(Path("/proc/sys/kernel/random/boot_id").read_text())
    r = guard(tmp_path, "run", "k", "--", "true")
    assert r.returncode == 2 and "already running" in r.stderr


def test_resume_relaunches_over_old_boot_pid(tmp_path):
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    out = tmp_path / "ran"
    (jobs / "j.cmd").write_bytes(f"touch\0{out}\0".encode())
    (jobs / "j.state").write_text("running\n")
    (jobs / "j.seq").write_text("1\n")
    (jobs / "j.cwd").write_text(f"{tmp_path}\n")
    (jobs / "j.pid").write_text(f"{os.getpid()}\n")
    (jobs / "j.boot").write_text("old-boot\n")
    r = subprocess.run(["bash", str(RESUME)], env=env_for(tmp_path, {"RESUME_BOOT_ID": "newboot"}),
                       capture_output=True, text=True, timeout=300)
    assert "relaunched j" in r.stdout and "FAILED" not in r.stdout, r.stdout
    assert until(out.exists)
