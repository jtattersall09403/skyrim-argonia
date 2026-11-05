"""infra/gpu-box/jobs/chain.sh runs in its own worktree of the launch commit: a lane's uncommitted edit is invisible,
out/ is the main tree's, the sha is kept for a resume and dropped on a good end; CHAIN_DRY prints tree and sha."""
import os
import pathlib
import shutil
import subprocess

REPO = pathlib.Path(__file__).resolve().parents[2]


def git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def setup(tmp):
    src = tmp / "repo"
    jobs = src / "infra" / "gpu-box" / "jobs"
    jobs.mkdir(parents=True)
    shutil.copy(REPO / "infra/gpu-box/jobs/chain.sh", jobs / "chain.sh")
    seen = tmp / "seen.log"
    for name, rel in (("prebatch", "jobs/r5_prebatch.sh"), ("round", "round.sh"), ("run", "run.sh")):
        p = src / "infra" / "gpu-box" / rel
        p.write_text(f'#!/usr/bin/env bash\necho "{name} $PWD $(cat lane.txt) $(readlink out)" >>{seen}\n')
        p.chmod(0o755)
    (src / "tooling").mkdir()
    (src / "tooling" / "round_retro.py").write_text(f'import sys; open("{seen}", "a").write("retro " + sys.argv[-1] + "\\n")\n')
    (src / "lane.txt").write_text("committed\n")
    (src / ".gitignore").write_text("out/\n")
    (src / "out").mkdir()
    git(src, "init", "-q", "-b", "main")
    git(src, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    git(src, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c")
    return src, seen


def chain(tmp, src, **env):
    # the gate itself runs inside a chain: nothing the chain exports may leak in (CHAIN_IN_TREE skipped the tree step)
    e = {k: v for k, v in os.environ.items() if not k.startswith("CHAIN_") and k != "ARGONIA_REPO"}
    e.update(HOME=str(tmp / "home"), **env)
    return subprocess.run(["bash", str(src / "infra/gpu-box/jobs/chain.sh"), "b.yaml", "rec.md"], cwd=src, env=e,
                          capture_output=True, text=True)


def test_lane_edit_invisible_and_out_shared(tmp_path):
    src, seen = setup(tmp_path)
    (src / "lane.txt").write_text("lane live edit\n")  # uncommitted, made before the chain starts
    r = chain(tmp_path, src)
    assert r.returncode == 0, r.stdout + r.stderr
    tree = tmp_path / "home" / ".argonia" / "round" / "tree"
    lines = seen.read_text().splitlines()
    pre = [x for x in lines if x.startswith("prebatch")][0]
    assert pre == f"prebatch {tree} committed {src}/out"
    assert f"retro {src}/rec.md" in lines  # the record is appended in the main tree
    assert (src / "lane.txt").read_text() == "lane live edit\n"  # the lanes' tree untouched
    assert git(tree, "status", "--porcelain") == ""  # the out link is excluded
    assert not (tmp_path / "home/.argonia/round/chain.b.sha").exists()  # a good end drops the resume key


def test_dry_prints_tree_and_sha(tmp_path):
    src, _ = setup(tmp_path)
    r = chain(tmp_path, src, CHAIN_DRY="1")
    assert r.returncode == 0, r.stderr
    sha = git(src, "rev-parse", "HEAD")
    assert f"CHAIN tree {tmp_path}/home/.argonia/round/tree sha {sha}" in r.stdout
    assert "would run on:" in r.stdout and not (tmp_path / "home/.argonia/round/tree").exists()


def bare_origin(tmp, src):
    o = tmp / "origin.git"
    git(tmp, "init", "-q", "--bare", "-b", "main", str(o))
    git(src, "remote", "add", "origin", str(o))
    git(src, "push", "-q", "origin", "main")
    other = tmp / "other"
    git(tmp, "clone", "-q", str(o), str(other))
    (other / "lane.txt").write_text("pushed by a lane\n")
    git(other, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qam", "lane")
    git(other, "push", "-q", "origin", "main")
    return git(other, "rev-parse", "HEAD")


def test_ff_to_origin_and_tree_at_that_sha(tmp_path):
    src, seen = setup(tmp_path)
    new = bare_origin(tmp_path, src)
    r = chain(tmp_path, src)
    assert r.returncode == 0, r.stdout + r.stderr
    assert git(src, "rev-parse", "HEAD") == new
    assert f"prebatch {tmp_path}/home/.argonia/round/tree pushed by a lane" in seen.read_text()


def test_dirty_tree_behind_origin_refused(tmp_path):
    src, seen = setup(tmp_path)
    old = git(src, "rev-parse", "HEAD")
    bare_origin(tmp_path, src)
    (src / "lane.txt").write_text("dirty\n")
    r = chain(tmp_path, src)
    assert r.returncode == 2 and "planner reconciles" in r.stdout
    assert git(src, "rev-parse", "HEAD") == old and not seen.exists()


def test_prebatch_sync_leaves_pinned_tree_alone(tmp_path):
    src, _ = setup(tmp_path)
    old = git(src, "rev-parse", "HEAD")
    new = bare_origin(tmp_path, src)
    assert new != old
    text = (REPO / "infra/gpu-box/jobs/r5_prebatch.sh").read_text()
    sync = text.split("# PREBATCH-SYNC begin\n")[1].split("# PREBATCH-SYNC end")[0]
    wt = tmp_path / "wt"
    git(src, "worktree", "add", "-q", "--detach", str(wt), old)
    e = {k: v for k, v in os.environ.items() if not k.startswith("CHAIN_")}
    for env in ({}, {"CHAIN_IN_TREE": "1"}):  # detached alone is enough; the flag too
        r = subprocess.run(["bash", "-c", sync], cwd=wt, env={**e, **env}, capture_output=True, text=True)
        assert r.returncode == 0 and "pinned at" in r.stdout, r.stdout + r.stderr
        assert git(wt, "rev-parse", "HEAD") == old
