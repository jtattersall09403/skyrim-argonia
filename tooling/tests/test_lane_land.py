"""tooling/lane_land.sh: a lane lands by rebase, the main tree follows, the worktree and branch go; a dirty lane, a
red gate and a conflict are refused with nothing pushed."""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

TOOLING = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
       "JOBS_DIR": "/nonexistent"}


def g(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True, env=ENV).stdout.strip()


def land(main, wt, gate="true"):
    return subprocess.run([str(main / "tooling/lane_land.sh"), str(wt)], capture_output=True, text=True,
                          env={**ENV, "LANE_GATE": gate, "HOME": str(main.parent)})


@pytest.fixture
def repo(tmp_path):
    origin, main = tmp_path / "o.git", tmp_path / "main"
    g(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    g(tmp_path, "clone", "-q", str(origin), str(main))
    g(main, "checkout", "-q", "-B", "main")
    (main / "tooling").mkdir()
    for f in ("lane_land.sh", "tidy.py"):
        shutil.copy(TOOLING / f, main / "tooling" / f)
    (main / "a.txt").write_text("a\n")
    (main / "b.txt").write_text("b\n")
    g(main, "add", "-A")
    g(main, "commit", "-qm", "base")
    g(main, "push", "-q", "-u", "origin", "main")
    return main


def lane(main, name):
    wt = main / ".claude/worktrees" / name
    g(main, "worktree", "add", "-q", "-b", f"worktree-{name}", str(wt), "origin/main")
    return wt


def other_lane_lands(main, tmp_path, f="b.txt", text="b from another lane\n"):
    c = tmp_path / "c"
    if not c.exists():
        g(tmp_path, "clone", "-q", str(tmp_path / "o.git"), str(c))
    g(c, "pull", "-q")
    (c / f).write_text(text)
    g(c, "commit", "-qam", "another lane")
    g(c, "push", "-q", "origin", "HEAD:main")


def test_lands_by_rebase_and_removes_the_worktree(repo, tmp_path):
    wt = lane(repo, "x")
    (wt / "a.txt").write_text("a from lane x\n")
    g(wt, "commit", "-qam", "lane x")
    other_lane_lands(repo, tmp_path)
    (repo / "notes.txt").write_text("the lead's uncommitted edit\n")
    r = land(repo, wt)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not wt.exists() and "worktree-x" not in g(repo, "branch", "--list")
    assert g(repo, "rev-parse", "HEAD") == g(tmp_path / "o.git", "rev-parse", "main")
    assert (repo / "a.txt").read_text() == "a from lane x\n" and (repo / "b.txt").read_text() == "b from another lane\n"
    assert (repo / "notes.txt").exists()
    assert g(repo, "log", "--format=%s", "-2") == "lane x\nanother lane"


def test_rerun_after_the_push_finishes_the_job(repo, tmp_path):
    """Interrupted between the push and the removal: the second run finds nothing to land and tidies up."""
    wt = lane(repo, "x")
    (wt / "a.txt").write_text("a from lane x\n")
    g(wt, "commit", "-qam", "lane x")
    g(wt, "push", "-q", "origin", "HEAD:main")
    r = land(repo, wt, gate="false")  # the gate is not run again: nothing is left to land
    assert r.returncode == 0, r.stdout + r.stderr
    assert not wt.exists() and (repo / "a.txt").read_text() == "a from lane x\n"


def test_refuses_dirty_red_and_conflicting(repo, tmp_path):
    wt = lane(repo, "x")
    (wt / "a.txt").write_text("a from lane x\n")
    g(wt, "commit", "-qam", "lane x")
    before = g(tmp_path / "o.git", "rev-parse", "main")
    (wt / "scratch.log").write_text("left behind\n")
    r = land(repo, wt)
    assert r.returncode != 0 and "uncommitted or untracked" in r.stderr
    (wt / "scratch.log").unlink()
    r = land(repo, wt, gate="false")
    assert r.returncode != 0 and "gate is red" in r.stderr
    assert g(tmp_path / "o.git", "rev-parse", "main") == before and wt.is_dir()
    other_lane_lands(repo, tmp_path, "a.txt", "a from another lane\n")
    r = land(repo, wt)
    assert r.returncode != 0 and "conflicts" in r.stderr
    assert wt.is_dir() and g(wt, "status", "--porcelain") == "" and (wt / "a.txt").read_text() == "a from lane x\n"
    r = land(repo, repo)
    assert r.returncode != 0 and "main tree" in r.stderr
