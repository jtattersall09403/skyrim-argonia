"""tooling/level_main.sh: the main tree (the studio serves it) brought level with origin/main. Stale leftovers (copies
of committed work) are cleared; real unlanded work, the owner's edits folders and his autosave (under out/) are never
touched; a level that real work blocks says which files and exits non-zero with nothing lost; a level put off while a
job runs from the main tree is done by job_guard when that job ends."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

TOOLING = Path(__file__).resolve().parents[1]


def env_for(tmp):
    return {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
            "HOME": str(tmp / "home"), "JOBS_DIR": str(tmp / "home/.argonia/jobs"), "JOB_GUARD_NO_SYSTEMD": "1",
            "DISK_FLOOR_GB": "0", "LEVEL_MAIN_INBOX": f"{sys.executable} {tmp / 'inbox.py'}"}


def g(env, cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


def commit_in(env, clone, files, msg):
    g(env, clone, "pull", "-q", "origin", "main")
    for f, text in files.items():
        p = clone / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    g(env, clone, "add", "-A")
    g(env, clone, "commit", "-qm", msg)
    g(env, clone, "push", "-q", "origin", "HEAD:main")


@pytest.fixture
def scene(tmp_path):
    env = env_for(tmp_path)
    (tmp_path / "home/.argonia/jobs").mkdir(parents=True)
    # the owner inbox stand-in: records each call, answers a post with an issue url
    (tmp_path / "inbox.py").write_text(
        "import sys, json\nopen(sys.argv[0] + '.log', 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "print('https://github.com/x/y/issues/7')\n")
    origin, main, other = tmp_path / "o.git", tmp_path / "main", tmp_path / "other"
    g(env, tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    g(env, tmp_path, "clone", "-q", str(origin), str(main))
    g(env, main, "checkout", "-q", "-B", "main")
    (main / "tooling").mkdir()
    for f in ("level_main.py", "level_main.sh", "tidy.py", "lane_land.sh", "job_guard.sh"):
        shutil.copy(TOOLING / f, main / "tooling" / f)
    files = {".gitignore": "out/\n", "a.txt": "a1\n", "b.txt": "b1\n", "c.txt": "c0\n", "d.txt": "d1\n",
             "newworld/places/p1/place.json": "{\"v\": 1}\n"}
    for f, t in files.items():
        (main / f).parent.mkdir(parents=True, exist_ok=True)
        (main / f).write_text(t)
    g(env, main, "add", "-A")
    g(env, main, "commit", "-qm", "base")
    (main / "c.txt").write_text("c1\n")
    g(env, main, "commit", "-qam", "c1")
    g(env, main, "push", "-q", "-u", "origin", "main")
    g(env, tmp_path, "clone", "-q", str(origin), str(other))
    # what other lanes land meanwhile
    commit_in(env, other, {"a.txt": "a2\n", "n.txt": "new\n", "newworld/places/p1/place.json": "{\"v\": 2}\n"}, "landed")
    return env, main, other, tmp_path


def level(env, main, *args, hook=None):
    e = {**env, **({"LEVEL_MAIN_TEST_HOOK": hook} if hook else {})}
    return subprocess.run([str(main / "tooling/level_main.sh"), "--tree", str(main), *args], capture_output=True,
                          text=True, env=e)


def leftovers(main):
    """(a) an identical copy of what landed, (b) an older committed copy, (c) an untracked identical file,
    (d) real unlanded edits, and the owner's own uncommitted save in a place's edits folder."""
    (main / "a.txt").write_text("a2\n")
    (main / "c.txt").write_text("c0\n")
    (main / "n.txt").write_text("new\n")
    (main / "d.txt").write_text("d1 with real unlanded edits\n")
    (main / "newworld/places/p1/edits").mkdir(parents=True)
    (main / "newworld/places/p1/edits/owner.json").write_text("{\"ops\": [1]}\n")


def test_level_clears_stale_copies_keeps_real_work_and_the_owners_files_and_fast_forwards(scene):
    env, main, other, tmp = scene
    leftovers(main)
    auto = main / "out/places/autosave/p1.json"
    r = level(env, main, hook=f"mkdir -p {auto.parent} && echo '{{\"rev\": 9}}' > {auto}")   # (e) written mid-level
    assert r.returncode == 3, r.stdout + r.stderr
    assert g(env, main, "rev-parse", "HEAD") == g(env, other, "rev-parse", "HEAD")
    assert (main / "a.txt").read_text() == "a2\n" and (main / "c.txt").read_text() == "c1\n"
    assert (main / "n.txt").read_text() == "new\n" and (main / "newworld/places/p1/place.json").read_text() == "{\"v\": 2}\n"
    assert (main / "d.txt").read_text() == "d1 with real unlanded edits\n"
    assert json.loads(auto.read_text()) == {"rev": 9}
    assert (main / "newworld/places/p1/edits/owner.json").read_text() == "{\"ops\": [1]}\n"
    assert "left (real unlanded work): d.txt" in r.stdout and "cleared 3 stale" in r.stdout
    assert g(env, main, "status", "--porcelain") == "M d.txt\n?? newworld/places/p1/edits/".strip()


def test_real_work_in_the_way_is_named_nothing_is_lost_and_the_owner_is_told_once(scene):
    env, main, other, tmp = scene
    commit_in(env, other, {"d.txt": "d2\n"}, "d landed")
    leftovers(main)
    head = g(env, main, "rev-parse", "HEAD")
    r = level(env, main, "--auto")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "in the way: d.txt" in r.stdout and "last written" in r.stdout
    assert g(env, main, "rev-parse", "HEAD") == head
    assert (main / "d.txt").read_text() == "d1 with real unlanded edits\n"
    assert (main / "newworld/places/p1/edits/owner.json").exists()
    calls = [json.loads(x) for x in (tmp / "inbox.py.log").read_text().splitlines()]
    assert calls[0][0] == "--post" and "behind" in (tmp / "home/.argonia/state/agent-wake-pending").read_text()
    assert "p1" in (tmp / "home/.argonia/state/level-main-issue.body").read_text()
    level(env, main, "--auto")   # the same state again: no second post
    assert len((tmp / "inbox.py.log").read_text().splitlines()) == 1
    (main / "d.txt").write_text("d2\n")   # the agent lands or clears it: the next level closes the issue
    r = level(env, main, "--auto")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads((tmp / "inbox.py.log").read_text().splitlines()[-1])[:2] == ["--close", "7"]


def test_report_and_check_change_nothing(scene):
    env, main, other, tmp = scene
    leftovers(main)
    before = g(env, main, "status", "--porcelain")
    r = level(env, main, "--report")
    assert r.returncode == 1 and "would clear 3 stale" in r.stdout and "report only: nothing changed" in r.stdout
    c = level(env, main, "--check")
    assert c.returncode == 1 and "stale: c.txt" in c.stdout
    assert level({**env, "STUDIO_OWNER_SAVE": "1"}, main, "--check").returncode == 0
    assert g(env, main, "status", "--porcelain") == before
    level(env, main)
    (main / "d.txt").write_text("d1\n")
    r = level(env, main, "--report")
    assert r.returncode == 0 and "main tree is level with origin/main" in r.stdout


def test_a_landing_while_a_job_runs_from_the_main_tree_is_levelled_when_the_job_ends(scene):
    env, main, other, tmp = scene
    (main / "a.txt").write_text("a2\n")   # a stale leftover in the way of the fast-forward
    gate = tmp / "release"
    jg = str(main / "tooling/job_guard.sh")
    job = f"import os,time\nwhile not os.path.exists({str(gate)!r}): time.sleep(0.05)"
    subprocess.run([jg, "run", "build", "--", sys.executable, "-c", job], cwd=main, env=env, check=True,
                   capture_output=True)
    wt = main / ".claude/worktrees/x"
    g(env, main, "fetch", "-q")
    g(env, main, "worktree", "add", "-q", "-b", "worktree-x", str(wt), "origin/main")
    (wt / "b.txt").write_text("b from lane x\n")
    g(env, wt, "commit", "-qam", "lane x")
    r = subprocess.run([str(main / "tooling/lane_land.sh"), str(wt)], capture_output=True, text=True,
                       env={**env, "LANE_GATE": "true"})
    assert r.returncode == 0, r.stdout + r.stderr
    assert "job build runs from it" in r.stdout
    assert g(env, main, "rev-parse", "HEAD") != g(env, main, "rev-parse", "origin/main")
    gate.write_text("")
    for _ in range(100):
        if subprocess.run([jg, "wait", "build"], env=env, capture_output=True).returncode != 3:
            break
    end = time.time() + 20
    while time.time() < end and g(env, main, "rev-parse", "HEAD") != g(env, main, "rev-parse", "origin/main"):
        time.sleep(0.1)
    assert g(env, main, "rev-parse", "HEAD") == g(env, main, "rev-parse", "origin/main")
    assert (main / "b.txt").read_text() == "b from lane x\n" and (main / "a.txt").read_text() == "a2\n"
    assert not (tmp / "home/.argonia/jobs/level-pending").exists()
