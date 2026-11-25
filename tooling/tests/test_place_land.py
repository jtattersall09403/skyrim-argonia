"""tooling/place_land.sh: a place lane lands in one job: each place whose built check is stale against the lane's files
is built and checked, consistency confirmed, the lane landed and the main tree levelled; a refused landing goes round
again (rebase, rebuild what is stale, land)."""
import shutil
import subprocess
from pathlib import Path

TOOLING = Path(__file__).resolve().parents[1]


def g(env, cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


def test_builds_what_is_stale_lands_and_goes_round_again_on_a_refusal(tmp_path):
    import os
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
           "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
           "HOME": str(tmp_path / "home"), "JOBS_DIR": str(tmp_path / "jobs"), "JOB_GUARD_NO_SYSTEMD": "1",
           "DISK_FLOOR_GB": "0", "LEVEL_MAIN_INBOX": "true"}
    (tmp_path / "home").mkdir()
    origin, main = tmp_path / "o.git", tmp_path / "main"
    g(env, tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    g(env, tmp_path, "clone", "-q", str(origin), str(main))
    g(env, main, "checkout", "-q", "-B", "main")
    (main / "tooling").mkdir()
    for f in ("place_land.sh", "lane_land.sh", "level_main.sh", "level_main.py", "tidy.py", "job_guard.sh"):
        shutil.copy(TOOLING / f, main / "tooling" / f)
    (main / ".gitignore").write_text("out/\n")
    (main / "newworld/places/p1").mkdir(parents=True)
    (main / "newworld/places/p1/place.json").write_text("{}\n")
    g(env, main, "add", "-A")
    g(env, main, "commit", "-qm", "base")
    g(env, main, "push", "-q", "-u", "origin", "main")
    (main / "out").mkdir()
    wt = main / ".claude/worktrees/p1"
    g(env, main, "worktree", "add", "-q", "-b", "worktree-p1", str(wt), "origin/main")
    (wt / "newworld/places/p1/place.json").write_text('{"moved": 1}\n')
    g(env, wt, "commit", "-qam", "p1 moved")
    log = tmp_path / "built.log"
    gate_once, gate = tmp_path / "gate-refused-once", tmp_path / "gate.sh"
    # the first gate is refused (main moved under the landing); the second passes
    gate.write_text(f"test -e {gate_once} || {{ touch {gate_once}; exit 1; }}\n")
    env |= {"PLACE_LAND_STALE": "echo p1",
            "PLACE_LAND_BUILD": f"echo {{pid}} >> {log} && test -L out",
            "PLACE_LAND_CONSISTENCY": "true",
            "LANE_GATE": f"bash {gate}"}
    r = subprocess.run([str(main / "tooling/place_land.sh"), str(wt)], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "place-land.p1" in r.stdout, r.stdout + r.stderr
    for _ in range(60):
        w = subprocess.run([str(main / "tooling/job_guard.sh"), "wait", "place-land.p1"], capture_output=True,
                           text=True, env=env)
        if w.returncode != 3:
            break
    assert w.returncode == 0, (tmp_path / "jobs/place-land.p1.log").read_text()
    jl = (tmp_path / "jobs/place-land.p1.log").read_text()
    assert log.read_text().split() == ["p1", "p1"] and "going round again" in jl
    assert g(env, origin, "log", "--format=%s", "-1") == "p1 moved"
    assert g(env, main, "rev-parse", "HEAD") == g(env, origin, "rev-parse", "main")
    assert (main / "newworld/places/p1/place.json").read_text() == '{"moved": 1}\n' and not wt.exists()
